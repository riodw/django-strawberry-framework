# Parity review — `django-strawberry-framework` vs. `django-graphene-filters`

Scope: not a single-spec review. This checks whether the package is on track to
recreate the **feature set** of the released, feature-complete reference
`django-graphene-filters` (DGF) `1.0.0`, per `GOAL.md` ("Working reference"),
on the custom Strawberry foundation. ALPHA — many cards are still unbuilt; that
is expected and not flagged here. Below are only points that **contradict** the
stated goal of recreating DGF's feature set.

Last triaged at `0.0.11` (2026-06-22).

## Verdict

On track. Every public symbol in DGF's `__all__`
(`django_graphene_filters/__init__.py`) is either shipped or has a dedicated
beta card:

| DGF public surface | This package | Status |
| --- | --- | --- |
| `AdvancedFilterSet`, `RelatedFilter` / `BaseRelatedFilter` | `FilterSet`, `RelatedFilter` (collapsed to one symbol, spec-027 D2) | shipped `DONE-027-0.0.8` |
| `AdvancedOrderSet`, `RelatedOrder` / `BaseRelatedOrder` | `OrderSet`, `RelatedOrder` | shipped `DONE-028-0.0.8` |
| `AdvancedDjangoFilterConnectionField` | `DjangoConnectionField` | shipped `DONE-030-0.0.9` |
| `apply_cascade_permissions` | `apply_cascade_permissions` + async `aapply_cascade_permissions` | shipped `DONE-034-0.0.10` |
| `AdvancedDjangoObjectType` | `DjangoType` | shipped; node-sentinel redaction is an opt-in tier planned for `TODO-BETA-051-0.1.4` |
| `AdvancedFieldSet` | `FieldSet` (`Meta.fields_class`) | planned `TODO-BETA-046-0.1.1` |
| `Meta.search_fields` (basic OR'd `icontains`) | `search_fields` | planned `TODO-BETA-047-0.1.2` |
| `AnnotatedFilter`, `SearchQueryFilter`, `SearchRankFilter`, `TrigramFilter` (+ input types) | same names | planned `TODO-BETA-048-0.1.2` |
| `AdvancedAggregateSet`, `RelatedAggregate` | `AggregateSet`, `RelatedAggregate` (`Meta.aggregate_class`) | planned `TODO-BETA-049-0.1.3` |

The architecture also reproduces DGF's *enabling* properties named in `GOAL.md`:
declarative `Meta` sidecars, lazy related-class references, generated types with
stable class-derived names, layered/cascade permissions, sync+async paths, and
Relay-node output. Plus net-new value DGF lacks (selection-aware N+1 optimizer,
mutations, `Upload`/file-image, model-anchored GlobalID). No DGF public capability
is silently missing from the roadmap.

## Resolved since the last review

- **[P2] Node-sentinel redaction (`isRedacted`) — now carded.** The prior review
  flagged this as the one public DGF behavior with no equivalent and no card
  (DGF's `AdvancedDjangoObjectType` exposes `is_redacted` + a `pk=0` `get_node`
  sentinel chain that masks a hidden non-null FK target in place instead of
  dropping the row). It is now tracked as an explicit per-`DjangoType` opt-in —
  `TODO-BETA-051-0.1.4` (`Meta.redaction_mode`) — recreating that surface for
  verbatim DGF ports while keeping row-narrowing (`apply_cascade_permissions`,
  spec-034 Decision 6) the default. The `FieldSet` non-goal note (`TODO-BETA-046`)
  cross-references it. Closed — no top-level parity gap remains.

## Open findings

### [P3] DGF's configurable filter/logic key namespace is not reproduced

DGF lets the schema author rename the filter-tree keys via settings:
`DJANGO_GRAPHENE_FILTERS = {"FILTER_KEY": ..., "AND_KEY": ..., "OR_KEY": ...,
"NOT_KEY": ...}` (`django_graphene_filters/conf.py:13-16`, defaults
`filter`/`and`/`or`/`not`).

This package hardcodes the GraphQL names: `_LOGIC_KEYS = (("and_", "and"),
("or_", "or"), ("not_", "not"))` (`django_strawberry_framework/filters/inputs.py:131`),
and the settings namespace `DJANGO_STRAWBERRY_FRAMEWORK` carries only
`APPLY_UPSTREAM_PATCHES` (`conf.py`). There is no way to rename the operator keys
or the `filter` argument. Still un-carded as of `0.0.11` — no `FILTER_KEY` /
logic-key entry exists in `KANBAN.md` or `BACKLOG.md`.

Low severity and possibly intentional (fixed names are simpler and arguably
better). It is a settings-level capability, not an `__all__` symbol, so it does
**not** break the verdict above — but it is a real DGF capability with no analogue
and no home. Needs a conscious owner decision: either add it to a beta card's
scope, or record it as an accepted, out-of-parity simplification — **recommended**:
fixed key names are the simpler, safer default; note the exception in `GOAL.md` /
the filters spec / `BACKLOG.md` so it stops surfacing as an open finding.

## Notes / parity watch items (not yet actionable — for the beta specs)

- **Aggregation config surface (`TODO-BETA-049`).** DGF's aggregate subsystem
  ships tunable safety limits and an async opt-in as settings: `AGGREGATE_MAX_VALUES`,
  `AGGREGATE_MAX_UNIQUES`, `ASYNC_AGGREGATES` (`django_graphene_filters/conf.py`).
  The card captures the `compute`/`acompute` split and stat surface but not these
  config knobs — confirm they're in scope when `spec-aggregates` is authored, or
  consciously drop them.
- **Postgres FTS search shortcuts (`TODO-BETA-048`).** Verify whether DGF's
  prefix-shortcut search operators (e.g. `^ = @ $`) are part of the surface being
  ported, or intentionally left out; the card describes the
  `SearchQuery`/`SearchRank`/`Trigram` classes but not the shortcut syntax.

These are reminders for spec time, not gaps to fix now.

## Performance — concurrency / scatter-gather opportunities

Net-new value, **not** a DGF-parity item (DGF has no concurrency story); captured here because
it was investigated against current `0.0.11` code. Nothing below is a bug — these are design
seams, ranked by whether they survive re-grounding. Assume large tables (~1M rows each) and a
backend that actually parallelizes.

**Hard constraints that shape every item.**

- The package has **zero** query concurrency today, and that is partly deliberate:
  `django_strawberry_framework/relay.py::DjangoNodesField` explicitly chooses *sequential awaits,
  not `asyncio.gather`*, citing Django async-ORM connection safety. Parallelism only pays for
  **genuinely independent** queries on **separate connections** — never naive fan-out over one
  shared connection/cursor.
- Each thread worker opens a thread-local connection and must close it (`close_old_connections`)
  on exit; N workers × concurrent requests exhausts the DB `max_connections` fast, so any pool is
  **small and bounded** (≈2–3), **not** `max_workers=NUM_CORES` — *except* the independent-DB shard
  case, where core-scaling is correct.
- The inspiration snippet's `chunk_size = ceil(count / NUM_CORES)` PK-range partition is a win
  **only** when the reduction runs in Python (mode / uniques / percentile / `Counter`); it is never
  a win for a SQL-native aggregate (`Count`/`Sum`/`Min`/`Max`/`Avg`), which adds round-trips and
  loses index efficiency.
- The example project runs on **SQLite** (both default and `FAKESHOP_SHARDED` modes), which
  serializes — no gain shows there. Any benchmark must run on Postgres/MySQL, and the
  100%-coverage suite cannot prove the speedup under the default runner.

**Re-grounded against `0.0.11`:**

- **Closed — nested `<field>Connection` `totalCount` ∥ page.** The `0.0.9` connection-aware
  optimizer folds `Count(1) OVER` + `RowNumber() OVER` into a single windowed-`Prefetch` query
  (`django_strawberry_framework/optimizer/plans.py::apply_window_pagination`); there is no separate
  count to parallelize. This was a candidate in the original deep-dive and is now obsolete.
- **Valid, package-owned — root connection `totalCount` ∥ page slice.** When `Meta.connection`
  opts into `totalCount`, the count runs serially *after* the slice via `count()` / `acount()` on
  the same filtered queryset (`django_strawberry_framework/connection.py::_attach_count_sync` /
  `::_attach_count_async`). The two are independent and the package fully owns the resolver — the
  smallest standalone win, but marginal unless the count rivals the page cost, and only on a
  parallelizing backend.
- **Valid, design-time (unbuilt) — `AggregateSet` per-stat + Python-reduction fan-out
  (`TODO-BETA-049-0.1.3`).** Independent stats that can't fold into one `.aggregate()` (mode /
  uniques / percentile / the `Counter`-based custom `compute_*` shown in `GOAL.md`) are each their
  own scan, and the PK-range partition applies to the Python reduction. **DB-native stats must stay
  single-query.** `acompute` already implies the async seam — build the gather seam into the card,
  don't retrofit.
- **Valid, textbook fit (parked) — multi-shard compose.** Independent DBs / connections → zero GIL
  contention, no shared-connection hazard; the item already specifies per-shard count/sum/min/max
  compose. The one place `max_workers=NUM_CORES` is literally correct. (`BACKLOG`
  `sharding_aware_optimizer`, item 41 — parked, not scheduled.)
- **Valid, design-time — matrix / BI measures + pivot.** Heaviest aggregation surface (10M-row,
  percentile, pivot); both per-measure fan-out and chunked-partition reduction apply. Design the
  matrix executor with a parallel reduce from the start. (`BACKLOG` `matrix_dimensions_and_measures`,
  item 32.)
- **Valid but architecturally invasive — parallel independent top-level `prefetch_related`.** The
  window optimizer removed the nested-*connection* serial-prefetch surface, but plain to-many list /
  M2M siblings still issue N serial `WHERE parent_id IN (...)` scans inside Django's
  `prefetch_related_objects`. `django_strawberry_framework/optimizer/plans.py::OptimizationPlan.apply`
  returns a **lazy** queryset; Strawberry/Django owns materialization. Parallelizing means the
  package takes over materialization in the resolvers it controls — per the root-cause rule, **not**
  monkeypatching `prefetch_related_objects`. High risk; defer behind a benchmark.

**Cross-cutting choke point.** Every async path wraps its sync body in
`sync_to_async(..., thread_sensitive=True)` — `django_strawberry_framework/filters/sets.py::FilterSet.apply_async`,
`django_strawberry_framework/orders/sets.py::OrderSet.apply_async`,
`django_strawberry_framework/permissions.py::aapply_cascade_permissions`, and (new in `0.0.11`)
`django_strawberry_framework/mutations/resolvers.py::run_pipeline_async` — which serializes them onto
one asgiref worker. That is a deliberate connection / consumer-hook safety choice, not a bug, but it
is the constraint any future async scatter-gather (the `acompute` seam above) must design around: the
gather must run genuinely independent units on their own connections, never re-enter the shared
sensitive thread.

**Ruled out (on the record):** a single root list query
(`django_strawberry_framework/list_field.py`) — nothing to split; `resolve_nodes` in
`django_strawberry_framework/relay.py` — already one `pk__in` per type, optimal within one DB (don't
parallelize the single-DB case); `FilterSet` / `OrderSet` `apply_*` — queryset builders, no fan-out;
`0.0.11` mutations — single-row, single-transaction, no bulk / per-id loops;
`finalize_django_types()` — CPU/GIL-bound and contractually single-threaded; DB-native aggregates —
let SQL do it.

**Where it pays to invest:** the `AggregateSet` (`0.1.3`) gather seam — a sync bounded-pool plus the
async `acompute` path — designed once and reused by the matrix and shard cards. Fold this note into
`spec-aggregates` when it is authored (same as the watch-items above); do not retrofit concurrency
onto shipped code without a Postgres benchmark.
