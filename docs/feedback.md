# Performance deep-dive — `django_strawberry_framework` vs `strawberry_django`

Comparison pass. Subject: per-request / per-row runtime efficiency of our shipped
read path against the reference package
`~/projects/strawberry-django-main/strawberry_django`. The original mandate was
narrow: find places where we **already ship the feature** but compute it more slowly
than the reference, and that are **not already carded** (KANBAN.md, `spec-035`
optimizer-hardening, `spec-033` connection-optimizer). This verified revision keeps
that framing but corrects two classifications: H2 is a real cache-hit hot-path bug,
but TODO-035 already owns it through the "plan-cache hit path gains zero allocations"
acceptance line; B1 is likewise already named in `spec-033` as a deferred root
`totalCount` micro-optimization. Pure feature gaps and the already-carded items (G1
`_result_cache` guard, G2 operation gating, G3 fragment narrowing, windowed nested-
prefetch pagination, nested `totalCount` window reuse, annotate hints, prefetch
merging, GFK/polymorphic, `disabled()`) are out of scope as new findings.

No `pytest` run this pass (`AGENTS.md`: only when explicitly asked). Every claim
below was read in both trees; OUR anchors are symbol-qualified (`path::Symbol
#"substring"`), reference anchors are cited by `path:line` (external package).
Each finding states explicitly whether it is a fresh uncarded item, already owned
by a card/spec, or a watch-only note. None of the proposed speedups changes wire
output, GlobalID opacity, the visibility cascade, or any `check_<field>_permission`
gate — they remove work, not behavior.

**Verdict.** We hold real architectural advantages the reference lacks (global LRU
plan cache, FK-id elision, strictness N+1 detection, class-creation-time
`FieldMeta` precompute). But on two fresh shared hot paths, plus one TODO-035-owned
cache-hit path, we leave measurable time on the table:

1. **MAJOR — every many-side relation field clones a `QuerySet` and copies the
   prefetched result list, per parent row.** (`types/resolvers.py`)
2. **MAJOR, already TODO-035-owned — the optimizer converts the whole AST to
   Strawberry selection objects on every request and then throws the result away
   on a plan-cache hit.**
   (`optimizer/extension.py`)
3. **MAJOR — the filter/order permission pass walks and re-classifies the entire
   input twice per nesting level when one pass yields both halves.**
   (`utils/permissions.py`)

One further MAJOR-class candidate (the hand-rolled selection-collection triple walk
vs graphql-core's `collect_subfields`), one Low/watch item already documented in the
registry review (GlobalID decode `O(types)` per id), one borderline item already
noted as uncarded backlog in `spec-033` (root `totalCount` fires a second `COUNT`),
and a batch of minor allocation/memoization wins follow.

## Resolution (2026-06-15 implementation pass)

Implemented the fresh, uncarded, behavior-neutral wins and reconciled the rest
against their owning cards:

- **Fixed (CODE):** **H1** (`many_resolver` reads `_prefetched_objects_cache`
  directly, no manager clone / list copy), **H3** (`run_active_input_permission_checks`
  now does ONE `iter_active_fields` pass via `active_permission_targets`; the two
  walkers are thin wrappers over it), **L2** (`_LOGIC_WIRE_BY_PYTHON_ATTR` +
  `_NORMALIZE_TRAVERSAL` hoisted to module scope), **L3** (`forward_resolver`
  computes the `info.path`/resolver-key once and only when an FK-id-elision or N+1
  check needs it), **L4** (`snake_case` memoized), **L5** (`_check_method_name`
  memoized).
- **Withdrawn:** **L1** — `feedback2.md`'s "No Action" supersedes it (see L1 below).
- **Deferred to owning cards (not touched this pass):** **H2** (TODO-035 owns the
  zero-allocation plan-cache-hit path), **H5** (must land with/after G3's `spec-035`
  selection-normalization rewrite — fixing now double-churns it), **H4** (watch-only,
  profile-triggered), **B1** (maintainer carding call), and the `_result_cache`
  guard (carded under G1 / `spec-035`).

The descriptions below are the original findings, retained for provenance.

## Findings

### H1 — `many_resolver` clones a `QuerySet` + copies the prefetched result list on every parent row — MAJOR — fix: CODE

**OUR anchor:** `django_strawberry_framework/types/resolvers.py::_make_relation_resolver`
— the `many_resolver` closure, `#"return list(getattr(root, accessor_name).all())"`.
**Reference:** `strawberry_django/resolvers.py:240` (`resolve_base_manager`), wired at
`strawberry_django/fields/field.py:282` / `:297`.

Our generated many-side resolver (M2M, reverse FK) is unconditionally
`list(getattr(root, accessor_name).all())`. On the **prefetched path** — the normal
optimized path, since the optimizer prefetches these relations — Django already stores
the relation under `_prefetched_objects_cache[...]` (in the probed Django version, as a
materialized `QuerySet` whose `_result_cache` points at the prefetched list).
`RelatedManager.all()` still constructs a fresh `QuerySet` wrapper over that cache, and
our `list(...)` then copies the materialized result list for output. That is one
`QuerySet` allocation **plus one redundant full list copy per many-side relation field,
per parent row** — and a connection page multiplies it by
`page_size × (#many-relations selected)`.
The docstring at `_make_relation_resolver #"manager.all() is prefetch-aware"` shows the
team already knows `.all()` is prefetch-aware; the cost is the construction + copy it
hides, not a DB hit.

The reference reads the cache **directly** — `result_instance._prefetched_objects_cache[manager.prefetch_cache_name]`
(ManyRelated) or `[remote_field.cache_name]` (reverse FK) — returning Django's
already-materialized cache object with zero manager-clone construction, and only falls
back to `manager.all()` on a genuine cache miss.

#### Apply

In `many_resolver`, probe the prefetch cache first (the in-module `_will_lazy_load_many`
already inspects `_prefetched_objects_cache`, so the accessor→cache-key mapping is at
hand) and return the cached result directly; fall through to
`list(getattr(root, accessor_name).all())` only on a miss.

```diff
 def many_resolver(root: Any, info: Info) -> Any:
     _check_n1(info, root, field_name, parent_type, kind=kind, accessor_name=accessor_name)
-    return list(getattr(root, accessor_name).all())
+    cache = getattr(root, "_prefetched_objects_cache", None)
+    if cache is not None:
+        cached = cache.get(_prefetch_cache_key(field))   # M2M cache name / reverse-FK cache name
+        if cached is not None:
+            result_cache = getattr(cached, "_result_cache", None)
+            return result_cache if result_cache is not None else cached
+    return list(getattr(root, accessor_name).all())
```

Resolve `_prefetch_cache_key(field)` once at resolver-build time (it is a property of
the relation descriptor, not of the row), mirroring `resolve_base_manager`'s
`prefetch_cache_name` / `remote_field.cache_name` split with the `5.1+ cache_name` vs
`get_cache_name()` fallback. **Behavior is identical** — same rows, same order; the
returned value is the prefetched result list when Django stores a materialized
`QuerySet`, or the cache object itself when Django stores a list-like value. The
fallback stays the current manager path.

**Confirmations.** (a) Shared feature: both packages resolve many-side relations from a
generated relation resolver; this package materializes a list, while the reference
returns Django's cached/manager iterable. (b) Grepped KANBAN /
`spec-033` / `spec-035`: `resolve_base_manager` / `_prefetched_objects_cache` for the
**list-relation** resolver is not carded. `spec-033 #"re-running the pipeline over
prefetched rows is rejected"` concerns the **connection windowed-prefetch fallback**, a
different mechanism — not the plain `many_resolver`.

### H2 — Plan-cache hits still pay the full AST→Strawberry conversion, then discard it — MAJOR, already TODO-035-owned — fix: CODE under TODO-035

**OUR anchor:** `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.apply_to`
(or the method owning `#"selections = ast_to_converted_selections(info, info.field_nodes)"`),
feeding `_get_or_build_plan`.
**Reference:** no plan cache exists upstream; the structural contrast is the early-out at
`strawberry_django/optimizer.py:1628` (`if is_optimized(qs) or qs._result_cache is not None: return qs`)
which short-circuits *before* selection work.

In `apply_to` we call `ast_to_converted_selections(info, info.field_nodes)` and
`selection_extractor(...)` **unconditionally**, then pass the result into
`_get_or_build_plan`. But `_get_or_build_plan` first computes the cache key
(`_build_cache_key`, from `print_ast` + variables — `#"cache_key = self._build_cache_key(info, target_model, origin)"`)
and on a **cache hit returns the cached plan immediately** (`#"if cached_plan is not None:"`),
never touching `node_selections`. So **every cache-hit request** pays the full recursive
AST conversion — Strawberry dataclass allocation per node plus `convert_arguments` /
`convert_directives` per node — for a result that is dropped on the floor. The plan
cache (B1) exists precisely to make hot queries cheap, yet the single most expensive
pre-plan step runs on every hit.

#### Apply

Reorder so the cache key is built and the cache consulted **before** converting
selections; convert (the input to `plan_optimizations`) only on a miss. The cache key
derives from `info.operation` / `print_ast` / variables and does **not** depend on the
converted selections, so the reorder is behavior-neutral — identical plan on a hit, only
the dead conversion removed.

```diff
-selections = ast_to_converted_selections(info, info.field_nodes)
-node_selections = selection_extractor(selections, info)
-plan = self._get_or_build_plan(node_selections, target_model, info, target_type)
+def _build_selections():
+    selections = ast_to_converted_selections(info, info.field_nodes)
+    return selection_extractor(selections, info)
+# _get_or_build_plan calls _build_selections() only inside the cache-miss branch
+plan = self._get_or_build_plan(_build_selections, target_model, info, target_type)
```

(Thread a thunk, or split `_get_or_build_plan` into `key → lookup → (miss) convert+build`.)
This directly advances TODO-035's own stated acceptance line that the cache-hit path
"gains zero allocations," which today it does not.

**Confirmations.** (a) Shared feature: both the AST conversion and (ours-only) the plan
cache ship today. (b) Grepped KANBAN / `spec-035`: the earlier "uncarded" claim was
incorrect. TODO-035 explicitly owns this outcome through its zero-allocation
plan-cache-hit acceptance line, even though it does not spell this exact thunking shape.

### H3 — Filter/Order permission pass walks + re-classifies the whole input twice per level — MAJOR — fix: CODE

**OUR anchor:** `django_strawberry_framework/utils/permissions.py::run_active_input_permission_checks`
— `#"for field_path in cls._active_permission_field_paths(input_value):"` immediately
followed by `#"for field_name, related_obj, child_input in cls._iter_active_related_branches(input_value):"`.
The two wrappers are `active_permission_field_paths` (keeps `LEAF`) and
`active_related_branches` (keeps `RELATED`), each of which independently runs
`iter_active_fields(cls, input_value, config)` (`utils/input_values.py::iter_active_fields`).
**Reference:** `strawberry_django/ordering.py:127` (`process_order`, single
`for f in OrderSequence.sorted(...)` pass) and `strawberry_django/filters.py:197`
(`process_filters`, single `for f in sorted(...)` pass). This is a traversal-shape
comparison, not a one-for-one permission-feature comparison; upstream does not carry
our active-input permission gate.

`run_active_input_permission_checks` traverses the same input dataclass **twice per
nesting level**: `_active_permission_field_paths` runs the full `iter_active_fields`
classifier and keeps only `LEAF` records; `_iter_active_related_branches` runs the full
classifier *again* and keeps only `RELATED` records. The classifier already emits `LEAF`,
`RELATED`, **and** `LOGIC` in a single pass — the two callers just discard the kinds
they don't want. Each pass also rebuilds a `SetInputTraversal` config object. On the
filter side the same input is then walked a **third** time by `_normalize_input` (see
L2). The reference's analogous filter/order traversal does its own field processing in
one pass.

#### Apply

Run `iter_active_fields` **once** with a config that is the superset of both current
configs (`field_specs` + `logic_keys` populated), then partition the yielded
`ActiveField` records by `.kind` into the leaf-path loop and the related-branch loop:

```python
config = SetInputTraversal(field_specs=field_specs, related_attr=related_attr,
                           logic_keys=logic_keys, unset_sentinel=..., handle_top_level_list=...)
leaves, branches = [], []
for f in iter_active_fields(cls, input_value, config):
    if f.kind == LEAF:     leaves.append(...)
    elif f.kind == RELATED: branches.append(...)
```

Caveat to verify when fusing: `active_related_branches` currently passes
`field_specs={}` and no `logic_keys`, while `active_permission_field_paths` passes both.
`RELATED` classification keys off `related_attr` membership and is independent of
`field_specs`/`logic_keys`, so the superset config must yield byte-identical `RELATED`
records — pin that with the existing permission tests. Dedup is per-class and
order-independent (the code documents this at `#"the per-class _fired dedup ... are all
order-independent"`), so the fused order is safe. This removes one full input traversal
+ re-classification per recursion level on every filtered/ordered request.

**Confirmations.** (a) Shipped feature: active-input per-field + per-branch permission
dispatch ships in both our `FilterSet` and `OrderSet` paths. The upstream reference is
only evidence that the analogous filter/order traversal can be organized as one pass.
(b) Grepped KANBAN / specs:
`run_active_input_permission_checks` / `iter_active_fields` single-pass fusion is not
carded (the only carded perf surface is the optimizer, `spec-035`).

### H4 — GlobalID type-name decode is `O(types)` per id instead of a keyed lookup — LOW / watch-only — fix: defer until trigger

**OUR anchor:** `django_strawberry_framework/registry.py::TypeRegistry.definition_for_graphql_name`
— `#"for type_cls, definition in self.iter_definitions()"`, called from
`types/relay.py::decode_global_id` (`#"definition_for_graphql_name"`).
**Reference:** `strawberry_django/relay/utils.py:223` (`resolve_model_node`) resolves the
source type directly, with no per-id type scan. This is not directly comparable:
upstream is handed a model/type source at this point, while this package also supports
type-name GlobalID strategies that must invert `definition.graphql_type_name`.

`definition_for_graphql_name` builds a list comprehension over **every registered
definition**, calling `implements_relay_node(type_cls)` (an `issubclass` check) on each,
**on every call**. `decode_global_id` calls it once per id under the `type` / `type+model`
GlobalID strategies, and `relay.py::DjangoNodesField._resolve` decodes per id
(`#"_decode_or_graphql_error(raw_id) for raw_id in ids"`), so a batch
`nodes(ids: [...])` request under the `type` strategy is **`O(ids × types)`**. (The
default `model` strategy uses `apps.get_model` + a dict `registry.get` and is unaffected
— this bites only the non-default type-name strategies.)

#### Apply

Do not promote this as an immediate CODE fix unless profiling shows node-decode latency
dominated by the scan under a large Relay-Node catalog. If that trigger fires, build a
`graphql_type_name → definition` index **once** at `mark_finalized()`. The registry is
immutable post-finalize (`_check_mutable` enforces it; `related_target_for` already gates
its cache on `is_finalized()`), so detect the ambiguity collision once at build (raising
the same `ConfigurationError` with the same `colliding` message) and turn each decode
into a single dict lookup. Same misses, same ambiguity errors, same routing.

**Confirmations.** (a) Shipped feature: this package's type-name GlobalID decode resolves
to a registered type; the upstream reference is an alternate node-resolution shape, not
the same type-name inversion feature. (b) Grepped KANBAN / spec-031 / spec-032: no
implementation card owns the index. But the registry review already records this as a
Low, profile-triggered note
(`docs/review/rev-registry.md #"Linear scan in definition_for_graphql_name"`) and
explicitly rejects adding mutable registry state before the large-catalog trigger. The
previous "MAJOR" / fresh-uncarded classification was overstated.

### H5 — Hand-rolled selection collection triple-walks the tree instead of using `collect_subfields` — MAJOR (highest payoff, largest change) — fix: CODE

**OUR anchor:** `optimizer/selections.py::ast_to_converted_selections` →
`optimizer/selections.py::included_field_selections` (`#"return included fields with
fragment bodies inlined"`) → `optimizer/walker.py` `#"_merge_aliased_selections(_included_field_selections(selections))"`.
**Reference:** `strawberry_django/optimizer.py:1305` (`_get_selections`) →
`strawberry_django/utils/gql_compat.py:21` (`get_sub_field_selections`).

For every plan build we do graphql-core's job in pure Python, and we walk the same tree
**three times**: (1) `ast_to_converted_selections` recursively builds Strawberry
`SelectedField` / `FragmentSpread` / `InlineFragment` dataclasses (per-node
`convert_arguments` / `convert_directives`); (2) `_included_field_selections` re-walks to
evaluate `@skip`/`@include` and inline fragment bodies; (3) `_merge_aliased_selections`
re-walks to group by response key (with a per-node `snake_case` — see L4).

graphql-core ships `collect_sub_fields` (3.2) / `collect_subfields` (3.3) — the exact
routine the executor uses — which does fragment inlining, `@skip`/`@include` evaluation,
and grouping-by-response-key **in one optimized pass**, returning
`dict[response_key, list[FieldNode]]`. The reference calls it directly. Collapsing our
three passes onto it is the largest change here but the biggest structural win, and it
honors fragment type-conditions identically (relevant to the in-flight G3 narrowing,
which becomes a predicate over the collected groups rather than a fourth walk).

> **Sequencing note:** G3 (`spec-035`) rewrites this same
> `included_field_selections` / `_included_field_selections` seam for *correctness*.
> Land H5 **after** G3 (or fold H5 into G3's rewrite) to avoid double-churning the
> selection-normalization code — the WIP card already warns against concurrent walker
> churn there.

Correction to the original wording: this is not a drop-in replacement. Our
`ast_to_converted_selections` also works around Strawberry's anonymous-inline-fragment
conversion crash and seeds `Info.selected_fields` for connection paths through
`prime_selected_fields`; those contracts must survive any `collect_subfields` rewrite.
Treat H5 as a larger adapter replacement that preserves the anonymous-fragment,
connection-direct-child, response-key-argument, and G3 type-condition semantics — not as
simply swapping one helper call.

**Confirmations.** (a) Shared feature: fragment inlining + directive filtering + alias
merging is exactly what `included_field_selections` + `_merge_aliased_selections` do.
(b) Grepped KANBAN / `spec-035`: no mention of `collect_sub_fields` /
`get_sub_field_selections`; G3 is a correctness narrowing predicate, not a perf rewrite
of how selections are collected.

### B1 — Root-connection `totalCount` fires a second `COUNT` query instead of folding it into the rows query — MAJOR, but flagged as already-noted-uncarded-backlog — fix: CODE (maintainer call)

**OUR anchor:** `django_strawberry_framework/connection.py::_attach_count_sync`
(`#"nodes.count()"`) and `_attach_count_async` (`#"await nodes.acount()"`), reached from
the generated `<TypeName>Connection.resolve_connection` in `_build_total_count_connection`.
**Reference:** `strawberry_django/relay/list_connection.py:129` (partition-less
`Window(Count(1))` annotation on the optimized root queryset), consumed at `:67`
(`total_count` reads it off the first edge's node).

When a **root** connection selects `totalCount`, we issue **two SQL statements**: the
sliced rows query (via Strawberry's `ListConnection.resolve_connection`) **and** a
separate `SELECT COUNT(*)` on the pre-slice `nodes` queryset. Upstream issues **one**:
for an optimized root queryset it annotates `Window(Count(1), partition_by=None)` so
every returned row already carries the total, and reads it off `edges[0].node`. Our
window machinery (`optimizer/plans.py::apply_window_pagination`) is `partition_by`-based
and emitted only for **nested** prefetch connections; the root path has no window-fold
equivalent.

**Apply (if pursued):** when the resolver source is a single optimized `QuerySet` and
`totalCount` is selected, annotate the partition-less count window on `nodes` before
delegating to `super().resolve_connection`, and read it from the first materialized
edge's node; fall back to `.count()`/`.acount()` on zero rows (no row to read) or when
`DISTINCT` is present (upstream guards both). The M1 `Int!`/non-queryset guard
(`_guard_total_count_countable`) is untouched; result is byte-identical.

> **Provenance flag (honesty):** unlike H1–H5, this one is **already named** in
> `spec-033 #"BACKLOG-worthy, not cut-blocking"` / `#"no card yet"` as a deferred
> post-`0.0.9` micro-optimization for the **root** path (the carded `DONE-033` window
> work is nested-only). It is **not in KANBAN.md**, so it technically clears the bar, but
> it is not a fresh discovery — it is a known, deliberately-deferred idea. Surfacing it
> here for completeness; whether to promote it to a card is a maintainer call.

## Minor findings (batch — allocation / memoization, all behavior-neutral)

- **L1 — WITHDRAWN (superseded by `feedback2.md` "No Action").** This originally
  proposed an `@lru_cache` over the registry-less fallback branch of
  `optimizer/walker.py::_resolve_field_map`
  (`#"{f.name: f for f in model._meta.get_fields()}"`). The `feedback2.md`
  verification pass reaches the opposite, better-reasoned conclusion and the two are
  now reconciled in its favor: (1) the fallback fires only when `registry.get(model)`
  misses, but a relation is only *selectable* in GraphQL when its target has a
  registered `DjangoType`, so the B7 `definition.field_map` precompute already covers
  the real per-request traffic — the fallback is an edge case, not a per-row loop;
  (2) the cache would couple to `registry.clear()` invalidation for near-zero benefit.
  **No code.** The narrow caches on genuinely-immutable metadata
  (`permissions.py::_cascadable_edges`, `orders/sets.py::_path_traverses_to_many`,
  and now `utils/strings.py::snake_case`) remain the correct boundary.

- **L2 — `_normalize_input` rebuilds `dict(_LOGIC_KEYS)` + a `SetInputTraversal` per
  call.** `filters/sets.py::FilterSet._normalize_input` (`#"logic_lookup = dict(_LOGIC_KEYS)"`).
  `_LOGIC_KEYS` is a frozen module constant; the dict and the config are identical every
  call, and `_normalize_input` runs once per `apply_*`, again via `_run_permission_checks`,
  and once per nested `_q_for_branch` sibling. Reference uses a module-level
  `lookup_name_conversion_map` (`strawberry_django/filters.py:109`). Fix: hoist
  `_LOGIC_WIRE_BY_PYTHON_ATTR = dict(_LOGIC_KEYS)` to module scope (our
  `_FORM_KEY_BY_PYTHON_ATTR` already is — this one was left inline) and make the
  filter-normalize `SetInputTraversal` a module singleton. Uncarded.

- **L3 — forward-relation resolver walks `info.path` twice per row.**
  `types/resolvers.py::_make_relation_resolver` `forward_resolver`
  (`#"if field_meta.attname is not None and _is_fk_id_elided"`): `_is_fk_id_elided` walks
  `info.path` → builds the runtime-path tuple → joins the resolver-key string, and then
  (common case, elision off) `_check_n1` recomputes the **identical** walk + key from
  scratch when the optimizer sentinels are present. Important correction: `_check_n1`
  already returns before walking when `DST_OPTIMIZER_PLANNED` is absent; the unconditional
  empty-sentinel work is on `_is_fk_id_elided`, which computes the key even when the
  FK-id-elision set is empty. Fix: short-circuit `_is_fk_id_elided` before the path walk
  when the elision set is empty, and compute `runtime_path_from_info(info)` +
  `resolver_key(...)` once in `forward_resolver` when both FK-id-elision and strictness
  checks need it (thread via an optional precomputed-key param).
  Behavior-neutral; uncarded (spec-003 defines the helpers, not this redundancy).

- **L4 — per-selection `snake_case` recomputed char-by-char, uncached.**
  `optimizer/walker.py` (`#"snake_case(sel.name)"`, repeated in `_merge_aliased_selections`
  and `_selected_scalar_names`); impl `utils/strings.py::snake_case`. Called once per
  selection per walk over a tiny fixed vocabulary that repeats every request. Reference
  avoids the reverse-conversion entirely (matches on the precomputed GraphQL name via
  `name_converter`, reads `field.django_name`). Fix: `@functools.lru_cache` on
  `snake_case`, or carry the resolved Django name on `FieldMeta` so it is precomputed
  once at class-creation. Smallest win; trivially safe. Uncarded. (Naturally folds into
  H5 if that lands.)

- **L5 — `invoke_permission_method` re-derives the `check_*` method-name string per
  field per request.** `utils/permissions.py::invoke_permission_method`
  (`#"method_name = f\"check_{field_path.replace('__', '_')}_permission\""`). The
  `field_path → method_name` transform is request-independent; only the bound-instance
  `getattr`/`callable` probe must stay per-request. Reference memoizes its per-field
  introspection (`strawberry_django/filters.py:140`,
  `@lru_cache _function_allow_passing_info`). Fix: `lru_cache` the pure string transform
  (bounded by declared field paths). The reference example is an analogous
  per-field-introspection cache, not a matching permission hook. Smallest of the batch;
  uncarded.

## Checked and explicitly rejected (not findings)

- **LIMIT/OFFSET slicing & over-fetch-by-1 for `hasNextPage`** — identical; both delegate
  to Strawberry's `ListConnection.resolve_connection` (`SliceMetadata.overfetch = end + 1`).
- **ListConnection cursor encode/decode** — identical (both build edges via
  `Edge.resolve_edge` over an integer-offset cursor). Upstream's richer
  `DjangoCursorConnection` tuple/JSON cursor is a **different connection type we don't
  implement** — a feature gap, not a slower shared path (out of scope by rule 1).
- **`should_resolve_list_connection_edges`** (skip edge materialization when only
  `totalCount` selected) — upstream applies it only in `DjangoCursorConnection`
  (`cursor_connection.py:396`), not the `DjangoListConnection` we mirror; not a shared-gap.
- **`_q_for_branch` per-branch `deepcopy(base_filters)`** — per-request, but it is a
  documented django-filter `BaseFilterSet.__init__` cost (M-filters-6, "profile before
  optimizing"), bounded by `_MAX_LOGIC_DEPTH`, reaching into django-filter copy semantics
  — out of bounds for a behavior-neutral speedup.
- **`get_filters` / `_expand_related_filter` deepcopy** — runs at class-finalize and is
  cached in `_expanded_filters` / `base_filters`, not per-request.
- **`diff_plan_for_queryset` prefetch reconciliation** — could not establish it as slower
  than upstream's `PrefetchInspector.merge` (the merge path is itself an explicit
  non-goal / consumer-wins safety stance, spec-004 B8).
- **Plan cache itself, `print_ast` cost, `_path_traverses_to_many`** — OUR-only
  advantages with no shared counterpart, or already `@lru_cache`'d.

## Net

Two clean, verified, uncarded MAJOR wins (**H1** many-resolver clone/list copy and
**H3** double input walk), one verified MAJOR that is already TODO-035-owned (**H2**
cache-hit conversion discard), one larger MAJOR-class candidate (**H5**
`collect_subfields`, with the adapter caveats above), one Low/watch item already
documented in registry review (**H4** GlobalID `O(types)` decode), one borderline
already-noted-backlog item (**B1** root `totalCount`), and five minor
allocation/memoization wins (**L1–L5**). The intended fixes are behavior-preserving:
same rows, same ids, same gates, same SQL semantics — they delete redundant work, not
authorization or visibility logic. Recommended order for **new** work by payoff-to-risk:
**H1** → **H3** → **L2/L4/L5** (trivial) → **L1/L3** (small invalidation/threading care)
→ **H5** (fold into G3 or land after it) → **B1** (maintainer call on carding). **H2**
should be handled inside TODO-035 rather than counted as a separate new card.
