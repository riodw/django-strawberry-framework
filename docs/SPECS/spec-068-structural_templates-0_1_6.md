# Spec: Structural optimization templates and nested sidecar batching

Planned for `0.1.6` (card `TODO-BETA-068-0.1.6`, created 2026-08-08 seated
immediately ahead of the optimizer-explain card `TODO-BETA-069-0.1.6`; every
card from that seat onward shifted up by one, and so did the post-`0.1.5`
patch versions). **The explain card shares this patch version, lands
last, and owns the `0.1.6` version cut, so this spec defers every
release-state artifact to it**
([Decision 1](#decision-1--seat-this-card-before-explain-joint-cut-at-016)).

The second of two graph foundation cards, sibling to the graph substrate
([`spec-058`][spec-058]). Where card `058` ships the shared planning
*vocabulary* (`GraphPathPlan`, `PredicatePlan`, `EdgeScope`,
`FieldDependencyPlan`, `RowIdentityProof`, the operation-scoped dependency
memo), this card ships the optimizer *architecture* that consumes it — four
pillars, each closing a measured production gap from the five-root
schedule-calendar audit that drove both cards (the failing shape and its
fakeshop recreation: [`docs/multi-root-graph-recreation.md`][recreation]):

1. **The structural/bound plan split.** An immutable, cross-request-cacheable
   `StructuralOptimizationTemplate` (relative paths, field dependency graph,
   visibility *binding slots*, nested argument slots, row-identity proof
   recipe) is bound per request into a `BoundOptimizationPlan` (absolute
   resolver paths, database alias, visibility querysets, concrete `Prefetch`
   objects, normalized argument values). `OptimizationPlan` survives as the
   final ORM directive bag, produced by binding
   ([Decision 2](#decision-2--structuralbound-split-no-request-value-in-any-structural-object)).
2. **Root-subtree structural cache keys.** The [plan cache][glossary-plan-cache]
   stops keying sibling roots by the whole operation's printed AST and keys
   each root subtree by its own normalized fingerprint; unrelated sibling
   variation, response aliasing, and re-embedding stop invalidating unchanged
   subtrees
   ([Decision 3](#decision-3--root-subtree-fingerprints-replace-whole-operation-cache-keys)).
3. **Nested sidecar batching.** Filtered, ordered, and search-bearing nested
   connections stop falling back to per-parent execution: one normalization
   pass per argument-distinct response key, windowed or lateral-paged by the
   parent join key, with query counts independent of parent count
   ([Decision 7](#decision-7--nested-sidecar-normalization-and-per-alias-batching)).
4. **The operation plan map and row-identity enforcement.** Optimizer
   introspection state stops being last-wins: every root publishes an explain
   entry under an immutable root execution identity, deterministic under
   async completion order
   ([Decision 6](#decision-6--operation-plan-map-replaces-last-wins-introspection)),
   and window planning refuses child shapes whose row identity is not proven
   by construction
   ([Decision 8](#decision-8--row-identity-proof-enforcement-never-an-automatic-distinct)).

Status: **PLANNED — no slice built yet; card created (`TODO-BETA-068-0.1.6`).**
Five slices: Slice 1 (**template/bound core** — the frozen dataclasses, the
subtree fingerprint builder, the binding pipeline, package tests proving
bind-equivalence with today's plans), Slice 2 (**cache rekey + rebasing +
plan map** — `_build_cache_key` moves to subtree fingerprints, response
paths rebase at bind time, the operation plan map publishes alongside the
retained legacy key), Slice 3 (**sidecar batching** — the normalization
pipeline, batched filtered/ordered nested connections, per-alias plans, the
request-bound sidecar cache), Slice 4 (**row-identity enforcement + live
fakeshop activation** — proof grades, strict/non-strict arms, the live
R1/R7/R8/R10 matrix and the R3 filtered-arm equalities), Slice 5 (**card-local
docs + card wrap — version and release marketing deferred to the explain
card's joint cut**).

This card consumes — and is gated on — card `058` landing first: `EdgeScope`
supplies the visibility-scoped child base queryset the sidecar pipeline
normalizes, `RowIdentityProof` is the vocabulary the window gate enforces,
`FieldDependencyPlan` feeds the template's dependency graph, and the
operation memo is the request-local tier the template binding reuses.
Card `058`'s spec explicitly "prepares the structural/bound split the
sibling card ships" ([`spec-058`][spec-058] Decision 8 posture); this card
is that sibling.

Permission caveat: [`AGENTS.md`][agents] prohibits `CHANGELOG.md` edits
without explicit permission. This card does not touch `CHANGELOG.md`; the
explain card's joint-cut slice must carry the maintainer's explicit grant.

---

## Key glossary references

Every project-specific symbol below is anchored in
[`docs/GLOSSARY.md`][glossary]; the companion
[`spec-068-structural_templates-0_1_6-terms.csv`][templates-terms]
is the audit ledger. Load-bearing entries:

- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the
  owner of the plan cache, the walk, and the context publication this card
  restructures.
- [Plan cache][glossary-plan-cache] — the whole-operation-keyed store this
  card re-keys by root subtree.
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]
  — the nested planning layer that gains sidecar batching.
- [`DjangoConnectionField`][glossary-djangoconnectionfield] — where the
  per-parent fallback currently lives and where batched sidecar results
  attach.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] —
  the request-bound value that currently poisons plan cacheability and
  becomes a binding slot.
- [Strictness mode][glossary-strictness-mode] — strict targets raise on
  unproven row identity; strictness keys publish only after successful
  binding.
- [`Meta.filterset_class`][glossary-metafilterset_class] /
  [`Meta.orderset_class`][glossary-metaorderset_class] — the declared
  surfaces the sidecar pipeline applies exactly once per batch.
- [Joint version cut][glossary-joint-version-cut] — why Slice 5 does NOT
  bump the version.

Substrate vocabulary (`EdgeScope`, `RowIdentityProof`, `FieldDependencyPlan`,
`GraphPathPlan`, the operation memo) is defined by [`spec-058`][spec-058];
its glossary entries fold in with that card's shipping slice.

## Slice checklist

- [ ] **Slice 1 — template/bound core.** `StructuralOptimizationTemplate` and
  `BoundOptimizationPlan` as frozen dataclasses in a new
  `optimizer/templates.py`; the normalized root-subtree fingerprint builder
  (exact owning type identity, root field/return type identity, normalized
  subtree selection, only the directive/pagination slots referenced inside
  the subtree, strategy/static schema configuration); the binding pipeline
  producing today's `OptimizationPlan` from a template plus request inputs;
  package tests proving a bound plan is directive-for-directive equivalent
  to a directly-walked plan across the existing optimizer test corpus
  shapes. No behavior change ships in this slice.
- [ ] **Slice 2 — cache rekey, response-path rebasing, operation plan map.**
  `optimizer/extension.py::DjangoOptimizerExtension._build_cache_key` moves
  to the subtree fingerprint; templates store relative paths and binding
  rebases them to absolute response paths (aliases and re-embedding hit the
  same template); `_publish_plan_to_context` publishes the operation plan
  map keyed by root execution identity while the legacy
  `DST_OPTIMIZER_PLAN` last-wins key is retained for the explain card to
  retire ([Decision 6](#decision-6--operation-plan-map-replaces-last-wins-introspection)).
- [ ] **Slice 3 — nested sidecar batching.** The eight-step sidecar
  normalization in a new `optimizer/sidecar.py`
  ([Decision 7](#decision-7--nested-sidecar-normalization-and-per-alias-batching));
  `optimizer/nested_planner.py::_divergent_key_windows` plans
  argument-bearing response keys instead of abandoning them;
  `connection.py::_build_relation_connection_resolver` consumes the batched
  per-parent result attribute; the request-bound sidecar plan cache
  (relation identity, normalized sidecar arguments, viewer/edge-scope key,
  database alias, target type, response-key-independent child selection);
  per-alias batching.
- [ ] **Slice 4 — row-identity enforcement + live activation.**
  `optimizer/nested_fetch.py::unwindowable_child_queryset_reason` composes
  with the `RowIdentityProof` grades
  ([Decision 8](#decision-8--row-identity-proof-enforcement-never-an-automatic-distinct));
  strict targets raise a targeted unproven-row-identity error, non-strict
  targets fall back visibly, no automatic `DISTINCT`; the live fakeshop
  matrix under `examples/fakeshop/test_query/` — R1 five-root cache
  isolation, R7 ordered nested batching, R8 gate arms, R10 plan-map
  completeness, and the R3 filtered-connection arm promoted from
  characterized to asserted-equal query counts.
- [ ] **Slice 5 — card-local docs + card wrap.** Regenerate `docs/TREE.md`
  for the new modules, update
  `examples/fakeshop/test_query/README.md` suite descriptions, move the
  glossary DB entries to a precise intermediate status and regenerate
  `docs/GLOSSARY.md`, audit that the explain card's amendment obligation
  (consume the plan map, retire the legacy key) is recorded on that card,
  flip the card + regenerate the board. Leave README shipped-surface
  wording, GOAL/TODAY release status, `CHANGELOG.md`, and the version
  quintet untouched — all owned by the explain card's `0.1.6` joint cut.

## Problem statement

One production dashboard operation selects five model-backed connection
roots whose subtrees traverse overlapping relation paths under per-viewer
visibility. Against that shape the current optimizer architecture has four
measured gaps, and every one is an architecture decision that freezes at the
`1.0.0` API surface if the explain card, the adversarial suite, and the
stable audit are allowed to build on today's internals:

1. **Whole-operation cache keys churn sibling plans.** Five roots across 32
   combinations of five binary directive/pagination choices can occupy 160
   entries of a 256-cap cache that evicts a quarter when full; toggling one
   root's `@include` variable invalidates every sibling's plan.
2. **Request-bound visibility poisons cacheability.** One
   `get_queryset`-bearing child type marks the entire parent plan
   `cacheable = False`, so the most security-sensitive types are exactly the
   ones that replan on every request.
3. **Filtered/ordered nested connections execute per parent.** One hundred
   parents with a filtered child connection issue one hundred (or, with
   `totalCount`, two hundred) child statements.
4. **Introspection is last-wins and windows are unproven.** A five-root
   operation exposes only the last-published plan — under async resolution,
   *which* plan survives depends on completion order — and the window-safety
   gate cannot detect a consumer join that multiplies child rows, corrupting
   `totalCount`, page boundaries, and next-page flags.

## Current state

- `optimizer/extension.py::DjangoOptimizerExtension._build_cache_key` keys
  plans by the selected operation's printed AST plus reachable fragments,
  relevant directive/nested-pagination variable values from the whole
  operation, target model, root response path, and origin type. Safe but
  whole-operation-coarse: aliasing a root or embedding the same subtree in a
  larger document produces a different key.
- `optimizer/walker.py::_plan_prefetch_relation` detects a target type with
  custom `get_queryset`, builds the child queryset *during the walk*, embeds
  it in a `Prefetch`, and stamps the plan `cacheable = False` — necessary
  under the current representation, since a queryset built from
  `info.context` must never enter a cross-request cache.
- `optimizer/nested_planner.py::_divergent_key_windows` classifies `filter:`
  / `orderBy:` as sidecar arguments and leaves those response keys
  unplanned; `connection.py::_build_relation_connection_resolver` then runs
  the ordinary connection pipeline against each parent's relation manager
  (`parents × page` queries, plus `parents × count` when `totalCount` is
  selected). [`spec-058`][spec-058] deliberately pinned this arm as
  *characterized, not required equal* and assigned closing it here.
- `optimizer/extension.py::DjangoOptimizerExtension._publish_plan_to_context`
  unions correctness sentinel sets so nested plans coexist, but stores
  `DST_OPTIMIZER_PLAN` (`optimizer/_context.py`) as last-wins introspection
  data.
- `optimizer/nested_fetch.py::unwindowable_child_queryset_reason` rejects a
  fixed shape list (sliced, `select_for_update`, combined, `distinct`,
  values querysets) but passes a custom queryset carrying an unexplained
  to-many join — e.g. `Issue.objects.filter(periodical__issues__embargoed=False)`
  emits one row per qualifying sibling and still windows. [`spec-058`][spec-058]
  Slice 2 lands this *characterization baseline*; enforcement is this card.

## Goals

- Cross-request structural reuse that survives sibling variation, response
  aliasing, and re-embedding — with request binding (visibility, arguments,
  alias, database) applied per execution.
- Visibility-bearing types cacheable at the structural tier: the template
  carries the *instruction* to bind a visibility factory, never a queryset.
- Constant child query counts for filtered/ordered/search-bearing nested
  connections, independent of parent count; argument-divergent aliases each
  cost one batched query.
- Complete, deterministic per-operation introspection: every root appears
  exactly once regardless of completion order; shared dependencies report
  one compute with hit counts and redacted keys.
- Window planning that refuses unproven row-multiplying child shapes in
  strict mode and falls back visibly — never silently — in non-strict mode.
- Sync and async agree on all of the above.

## Non-goals

- **No new consumer surface.** No new Meta keys, no new arguments, no new
  public API. Every object this card ships is internal optimizer
  vocabulary; the consumer-visible effect is query counts, cache behavior,
  and explain completeness.
- **No explain rendering.** The operation plan map is the *data*; rendering
  it is the explain card (`TODO-BETA-069-0.1.6`), which is
  amended to consume the map and retire the legacy context key.
- **No document-level parse/validation cache.** The BACKLOG
  operation-document cache is complementary (byte-identical repeats), not a
  substitute (sibling invalidation inside one changing document); the two
  layers must share epoch-keying discipline, tracked there.
- **No `DISTINCT` semantics change.** The gate refuses or falls back; it
  never rewrites a consumer multiset.

## Architectural decisions

### Decision 1 — Seat this card before explain; joint cut at `0.1.6`

The hard constraints are a floor and a ceiling: after card `058` (this card
consumes its vocabulary) and before the explain card (whose design assumes
the single context plan this card deletes and which must render the plan
map). Within that window the card seats at `068`, immediately ahead of
explain — the tightest satisfying seat, matching the audit's proposed order,
and the smallest renumber (every card from that seat onward shifted up by
one).
The three independent `0.1.4`/`0.1.5` cards (enums, fakeshop activation,
product HTTP) neither feed nor consume this work and ship ahead of it
unchanged.

Two non-Done cards then share `0.1.6`: this card and explain
(`TODO-BETA-069-0.1.6`). Explain renders what this card publishes — natural
joint-cut partners. Explain lands last, so per the
[joint version cut][glossary-joint-version-cut] rule the explain card's
final slice owns the version quintet, `CHANGELOG.md`, and all release-state
prose; this spec's Slice 5 ships none of it. The former `0.1.6`/`0.1.7`
patches shift to `0.1.7`/`0.1.8`.

### Decision 2 — Structural/bound split; no request value in any structural object

Two objects, one boundary:

```text
StructuralOptimizationTemplate      cacheable across requests
    relative response paths
    field dependency graph
    visibility binding slots
    nested argument slots
    row-identity proof recipe

BoundOptimizationPlan               request-local
    absolute resolver paths
    database alias
    visibility querysets
    contextual Prefetch objects
    normalized argument values
```

`OptimizationPlan` remains the final ORM directive bag consumed by the
execution layer, but it is *produced by binding* a template rather than
walked fresh. Both new objects are frozen dataclasses, extending
[`spec-058`][spec-058]'s posture verbatim: **no request value — user,
tenant, queryset, database alias, or argument value — is storable in any
structural object.** The invariant is enforced structurally (the template's
slots hold factories and slot descriptors, not values) and tested
adversarially (attempting to construct a template around a bound queryset
raises).

**Rejected:** keeping `cacheable = False` and adding a second cache tier
keyed by viewer — it multiplies entries by viewer cardinality and still
replans per viewer; the binding slot costs one bind per request against a
shared template.

### Decision 3 — Root-subtree fingerprints replace whole-operation cache keys

A template is keyed by exactly:

- exact owning GraphQL type identity (object identity, not name —
  [`spec-058`][spec-058]'s exact-owner rule);
- root field / return type identity;
- normalized root-subtree selection fingerprint;
- only the directive and nested-pagination slots referenced *inside* that
  subtree;
- strategy/static schema configuration.

Explicitly excluded from the key: unrelated operation text, unrelated
variables, the root response alias, request-bound visibility, the database
alias. The store keys on registry/schema epoch like every cross-request
cache in the package; capacity and eviction policy are measured in Slice 2
against the existing 256-cap/evict-quarter behavior and pinned then (open
question below).

### Decision 4 — Visibility becomes a binding slot

`_plan_prefetch_relation`'s walk-time queryset construction moves to bind
time. The structural relation template records the relation lookup, exact
target type, child structural template, projection, and subtree-relative
strictness identities; the binding stage calls the target's `get_queryset`
factory with the live `info`, applies the contextual edge scope
(`EdgeScope`, from card `058`), and materializes the concrete `Prefetch`.
A visibility-bearing relation template is therefore cross-request cacheable.
One request-bound child recipe is reused across identical
relation/argument/scope keys within the request (the operation memo is the
request-local tier).

### Decision 5 — Response paths rebase at bind time; strictness keys publish after attachment

Templates store subtree-relative paths. Binding rebases them to absolute
response paths under the actual alias, so aliased and re-embedded subtrees
share one template (R1's aliasing arm). Strictness resolver keys and
planned-edge markers publish **only after successful binding and
attachment**: planning failure stays visible — an edge is never marked
planned and then resolved lazily.

### Decision 6 — Operation plan map replaces last-wins introspection

`_publish_plan_to_context` publishes a map keyed by an immutable root
execution identity and rendered by response path. Each entry carries: root
field/type/model; structural template fingerprint; structural hit/miss;
request-binding identity without secret values; select/prefetch/computed
dependencies; direct and correlated predicate branches; contextual edge
scopes; nested strategy and sidecar plan; row-identity proof; fallback
reasons; estimated query families; strictness keys; database alias; and
whether count and page share a statement. Shared operation dependencies
appear once with redacted keys and hit/miss counts. The map is complete and
deterministic under any async completion order.

The legacy `DST_OPTIMIZER_PLAN` last-wins key is **retained unchanged**
through this card — consumers exist in `types/resolvers.py` and tests — and
retiring it is the explain card's recorded amendment. This card changes the
data, not the readers.

### Decision 7 — Nested sidecar normalization and per-alias batching

One normalization per argument-distinct nested response key:

1. start from the visibility- and edge-scoped child base queryset;
2. apply the target FilterSet once;
3. apply the target OrderSet once;
4. append deterministic ordering;
5. prove one SQL row per child identity (Decision 8);
6. partition by the parent join key;
7. window or lateral-page each parent;
8. attach one result list per parent under a response-key-specific
   `to_attr`.

The request-bound sidecar plan caches by relation identity, normalized
sidecar arguments, viewer/edge-scope key, database alias, target type, and
response-key-independent structural child selection. Two aliases with
different arguments cost two batched child queries — never `parents × 2`.
Target statement counts: one batched page/count query, or a constant three
total where the backend/strategy requires separate count and page
statements — in all cases independent of parent count. This closes the R3
filtered-connection arm [`spec-058`][spec-058] pinned as characterized-only.

### Decision 8 — Row-identity proof enforcement; never an automatic `DISTINCT`

`RowIdentityProof` (vocabulary from card `058`, baseline from its Slice 2)
becomes the window gate. Proof is **by construction**, composed from
framework-generated query-shape operations:

```text
PROVEN_BASE
PROVEN_CORRELATED_EXISTS
PROVEN_PARENT_PK_SUBQUERY
PROVEN_TO_ONE_JOIN
UNPROVEN_CONSUMER_SHAPE
KNOWN_MULTIPLYING
```

Plain model base querysets, `select_related`, framework correlated `EXISTS`,
and framework parent-PK subqueries stay proven; an unexplained consumer join
across a multiplying path is unproven; consumer `DISTINCT` stays
unwindowable under the existing semantic contract. Strict mode refuses to
window an unproven shape with a targeted unproven-row-identity error;
non-strict mode uses the existing per-parent fallback with the reason
reported through strictness and the plan map. The framework never injects
`DISTINCT` to launder an unproven shape — that would silently change a
consumer multiset. Consumer querysets that bypass framework shaping remain
unproven; reverse-engineering Django alias maps to certify them is
explicitly rejected.

### Decision 9 — Pluggable nested-fetch strategies must consume the pipeline

The nested-fetch strategy boundary stays pluggable, but every strategy —
including the BACKLOG candidates (SQLite correlated-JSON, backward keyset,
MTI-aware lateral) — must consume the sidecar normalization and the
`RowIdentityProof` gate rather than self-certifying child row identity. A
strategy that self-certifies would reopen the window-safety hole in a new
backend. This is a contract on the strategy interface, asserted by a
package test that a strategy cannot receive an unproven shape in strict
mode.

### Decision 10 — Internal vocabulary only; the consumer surface is unchanged

Nothing here is shipped API. The consumer-facing declaration surface remains
Meta keys and sidecar `Set` classes as card `058` pins it; this card adds no
key, no argument, and no decorator. The observable contract is behavioral:
query counts, cache hit rates, explain completeness, and strict-mode errors.

## Implementation plan

Slices as checklisted above. New modules: `optimizer/templates.py`
(structural/bound objects, fingerprint builder, binding pipeline) and
`optimizer/sidecar.py` (normalization + batching); both consume
`django_strawberry_framework/graph/` (card `058`) and neither is imported by
it. Changed seams: `optimizer/extension.py` (`_build_cache_key`,
`_publish_plan_to_context`), `optimizer/walker.py`
(`_plan_prefetch_relation`), `optimizer/nested_planner.py`
(`_divergent_key_windows`), `optimizer/nested_fetch.py`
(`unwindowable_child_queryset_reason`), `connection.py`
(`_build_relation_connection_resolver`). Slice 1 is behavior-neutral by
design so the equivalence corpus can gate everything after it.

## Test plan

This card owns the four reproductions [`spec-058`][spec-058]'s R-index
assigns to the sibling, plus the R3 arm it defers here. Per the live-first
mandate everything reachable from a real GraphQL query is covered live under
`examples/fakeshop/test_query/`; package tests under `tests/` keep pure
plan/fingerprint construction, SQL-shape assertions, raise paths, and
interleavings a real query cannot produce.

| # | Reproduction | Core assertion |
| --- | --- | --- |
| R1 | Five-root structural cache isolation | Each root produces one plan-map entry; a selection or argument change invalidates only its own subtree; aliasing a root needs no new template; a repeat request hits every template; rebased paths are correct under aliases |
| R3 (filtered arm) | Filtered nested connection batching | The per-parent fallback counts pinned as *characterized* by card `058` become asserted equalities: query count identical for 1 and 100 parents with a `filter:` argument |
| R7 | Ordered nested connection batching | Parent count does not change child query count; per-parent windows and `totalCount`; cursors replay; argument-divergent aliases batch separately; strictness reports no planned edge on fallback; the plan map reports the sidecar normalization and strategy |
| R8 | Row-identity window gate | Strict targets raise a targeted unproven-row-identity error on the multiplying-join shape; non-strict targets fall back visibly; no automatic `DISTINCT`; correlated `EXISTS` restores a proven window plan; duplicate child identities never enter row numbering or partition counts |
| R10 | Operation plan-map completeness | Every root appears exactly once regardless of async completion order; shared dependencies appear once with one compute and N-1 hits; fallback reasons attach to the right response key; scope values are redacted |

Fixtures are the existing fakeshop surfaces: the five-root dashboard
operation (categories/items/properties/entries/periodicals) for R1/R10,
`PeriodicalType.issuesConnection` + `IssueOrder` (seeded 1 and 100
periodicals × 5 issues) for R3/R7, and the multiplying
`periodical__issues__embargoed=False` Issue queryset for R8. Query-count
assertions are exact per-backend equalities pinned from a measured baseline,
never inequalities. Async arms run with delays that reverse root completion
order. The no-extension schema and `OptimizerHint.SKIP` arms are pinned
unchanged.

## Doc updates

- `docs/TREE.md` regenerates for the new modules (Slice 5).
- Glossary DB: `StructuralOptimizationTemplate`, `BoundOptimizationPlan`,
  the operation plan map, and the sidecar normalization enter at a precise
  intermediate status; final shipped-release status belongs to the explain
  card's joint cut.
- `examples/fakeshop/test_query/README.md` suite descriptions extend for
  the new live coverage.
- The explain card's amendment (consume the plan map; retire
  `DST_OPTIMIZER_PLAN`) and the adversarial card's amendment (attack the
  template store, the binding boundary, and the proof gate) are recorded on
  those cards at this card's creation, mirroring card `058`'s
  amendment-at-creation rule.

## Risks and open questions

- **Template-store capacity and eviction.** The 256-cap/evict-quarter
  numbers belong to the current whole-operation cache; per-subtree entries
  are smaller and more numerous. Slice 2 measures before pinning a policy.
- **Count/page statement sharing.** Whether `totalCount` and the page share
  one statement is today a per-backend/strategy detail; the plan map reports
  it, and the R7 equality budget (one vs a constant three statements) is
  pinned per backend from the measured baseline, not assumed.
- **Fingerprint normalization completeness.** A slot the fingerprint misses
  (a directive or pagination variable that *is* referenced in the subtree
  but not keyed) is a correctness bug, not a performance bug. Slice 1's
  equivalence corpus plus an adversarial arm in the `072` suite guard it;
  under-keying fails closed to a walk, never to a wrong
  reuse — the bind stage revalidates referenced slots against the template.
- **`FieldDependencyPlan` vocabulary breadth.** The template's dependency
  graph consumes whatever vocabulary has shipped by then (`058` ships the
  narrow form; `059` expands it). Binding treats unknown dependency kinds
  as bind-time walks, so the template layer does not gate on `059`'s
  expansion.
- **Legacy-key window.** Between this card and the explain card, the plan
  map and `DST_OPTIMIZER_PLAN` coexist; the legacy key stays last-wins and
  documented as such. The window is one card wide by seating (Decision 1).

## Out of scope (explicitly tracked elsewhere)

- **Explain rendering over the plan map** — the explain card
  (`TODO-BETA-069-0.1.6`) owns the surface and the legacy-key
  retirement.
- **Adversarial attack suite** — the adversarial card (`TODO-BETA-072-0.1.8`),
  amended to attack the template store, binding boundary, and proof gate.
- **Document-level parse/validation/plan cache** — BACKLOG
  (`operation_document_and_plan_cache`); complementary layer, shared
  epoch-keying discipline recorded there.
- **New nested-fetch strategies** (SQLite correlated-JSON, backward keyset,
  MTI-aware lateral) — BACKLOG; each must consume this card's pipeline
  (Decision 9).
- **Optional PostgreSQL repeatable-read snapshot policy** — non-gating,
  unscheduled (card `058`'s R11 disposition).
- **All originating-consumer work** — owned and tracked by that repository.

## Definition of done

- [ ] `StructuralOptimizationTemplate` / `BoundOptimizationPlan` ship frozen;
  no request value storable in any structural object; the adversarial
  construction test raises.
- [ ] The plan cache keys by root-subtree fingerprint; the R1 matrix is
  green live (isolation, aliasing, re-embedding, full-hit repeat).
- [ ] Visibility-bearing relation templates are cross-request cacheable;
  `get_queryset` binds per request; one bound child recipe per
  relation/argument/scope key per request.
- [ ] Filtered/ordered/search-bearing nested connections batch with query
  counts independent of parent count; per-alias batching proven; the R3
  filtered arm asserts equalities.
- [ ] Strict mode refuses unproven window shapes with a targeted error;
  non-strict falls back visibly; no code path injects `DISTINCT`.
- [ ] The operation plan map is complete and deterministic under reversed
  async completion order; the legacy key still serves existing readers.
- [ ] Sync and async agree across every arm; the no-extension and SKIP arms
  are unchanged.
- [ ] Slice 5 docs land; release-state artifacts are untouched and owned by
  the explain card's `0.1.6` joint cut.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-joint-version-cut]: ../GLOSSARY.md#joint-version-cut
[glossary-metafilterset_class]: ../GLOSSARY.md#metafilterset_class
[glossary-metaorderset_class]: ../GLOSSARY.md#metaorderset_class
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[recreation]: ../multi-root-graph-recreation.md

<!-- docs/SPECS/ -->
[spec-058]: spec-058-graph_substrate-0_1_1.md
[templates-terms]: spec-068-structural_templates-0_1_6-terms.csv

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
