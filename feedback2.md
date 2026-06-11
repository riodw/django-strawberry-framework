# Optimizer Improvement Review

Scope: reviewed the claims in the original optimizer deep-review note against
the current live code in `django_strawberry_framework/optimizer/`,
`django_strawberry_framework/connection.py`, and the existing optimizer /
connection tests. I added temporary acceptance probes under
`tests/optimizer/temp-tests/`. I did not run pytest.

## Developer-Facing Findings

### 1. Connection-aware planning is the highest-value optimizer gap

Status: valid and high priority.

The connection hook is wired:
`django_strawberry_framework/connection.py::_finalize_queryset` calls
`django_strawberry_framework/optimizer/extension.py::apply_connection_optimization`,
which delegates to `DjangoOptimizerExtension.apply_to` when the optimizer
extension is active. The missing piece is still the walker shape: the generic
root walker sees the connection wrapper selections instead of treating
`edges -> node -> ...` as the node selection set. As a result, connection node
queries publish an empty plan where the equivalent list field would use
`select_related`, `prefetch_related`, and `only`.

Temporary tests added:

- `tests/optimizer/temp-tests/test_optimizer_improvement_acceptance.py::test_connection_edges_node_forward_fk_selection_builds_node_plan`
- `tests/optimizer/temp-tests/test_optimizer_improvement_acceptance.py::test_connection_edges_node_many_relation_selection_builds_prefetch_plan`

Target behavior: a `DjangoConnectionField(ItemType)` query selecting
`edges { node { category { id name } } }` should plan the same node queryset as
the list-field selection: `select_related("category")` plus the required
projection fields. A `DjangoConnectionField(CategoryType)` query selecting
`edges { node { items { name } } }` should produce a prefetch plan for `items`.

Implementation direction: add a connection-aware selection extractor that walks
only node selections under `edges.node`, ignores connection metadata
(`pageInfo`, `cursor`, `totalCount`), then feeds the existing
`plan_optimizations(..., source_type=target_type)` path with the node-level
selection list. Keep the existing connection field pipeline order: visibility,
filter, order, deterministic pk tiebreaker, optimizer, slicing.

Second-pass refinement: make the extractor a shared helper rather than a
connection-only fork. The list path can keep using the current
`django_strawberry_framework/optimizer/extension.py::_root_child_selections`
shape, while the connection path unwraps `edges -> node -> children`; both
should feed one normalized node-selection list into the walker. This matters for
root `DjangoConnectionField` and for synthesized relation connection fields
from `django_strawberry_framework/types/finalizer.py::_synthesize_relation_connections`.
The extractor must explicitly ignore `totalCount`, `pageInfo`, `cursor`, and
connection wrapper fields. Longer term, identical node selections reached via a
list field and a connection field should be eligible to share a structural plan
template after wrapper extraction.

### 2. Plan-cache eviction should be LRU, not FIFO

Status: valid and useful.

`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._get_or_build_plan`
evicts the oldest quarter when the cache is full, but cache hits do not promote
recency. Under a diverse GraphQL workload, repeatedly used plans can still age
out just because they were inserted early.

Temporary test added:

- `tests/optimizer/temp-tests/test_optimizer_improvement_acceptance.py::test_plan_cache_hit_promotes_entry_before_eviction`

Target behavior: after a cache hit on the oldest entry, the next insertion
should keep that hot entry and evict the next least-recently-used entry.

Implementation direction: use `collections.OrderedDict` or an equivalent
move-to-end-on-hit policy. Keep the quarter-sweep amortization if desired, but
sweep from the least-recently-used side.

### 3. Request-scoped child querysets should not disable all structural caching

Status: valid, larger refactor.

Current behavior is conservative: if a nested relation target has a custom
`get_queryset`, the generated `Prefetch` embeds a request-scoped queryset and
the entire plan becomes uncacheable. That protects correctness, but it also
throws away the structural part of the plan even though the selected paths and
projection fields are stable across requests.

Temporary test added:

- `tests/optimizer/temp-tests/test_optimizer_improvement_acceptance.py::test_dynamic_child_queryset_keeps_structural_plan_cache_entry`

Target behavior: the structural plan should cache across identical query
shapes, while dynamic child querysets are hydrated per request. The test asserts
that the hook still runs once per request, but the optimizer records one miss
and one hit across two identical executions.

Implementation direction: split the cached plan into a frozen structural
template and a request-time hydration step for dynamic `Prefetch` querysets.
Do not cache live queryset objects that close over `info.context`.

Second-pass refinement: apply the same split to
`OptimizerHint.prefetch(obj)`. Today
`django_strawberry_framework/optimizer/walker.py::_apply_hint` marks the whole
plan uncacheable when a consumer-supplied `Prefetch` is present, for the same
correctness reason as custom `get_queryset`: the queryset can close over
request state. The structural template should keep the lookup path and metadata
cacheable while hydrating the hinted queryset per request.

### 4. Publish-time strictness metadata should be precomputed

Status: valid, small-to-medium optimization.

`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._publish_plan_to_context`
copies `plan.fk_id_elisions` and `plan.planned_resolver_keys` into fresh sets on
every publish, and under strictness it also recomputes `lookup_paths(plan)`.
That is cheap for small plans but repeats on every cache hit and every root
field. Finalized plans can carry `frozenset` variants for elisions and planned
resolver keys, plus a precomputed `lookup_paths` frozenset. Resolver membership
checks already only need `key in collection`, so frozenset works.

Implementation direction: extend `OptimizationPlan.finalize` to publish
immutable membership sets and lookup paths, then stash those references directly
when possible. Keep the tuple fields for existing introspection and deterministic
plan shape unless the public contract is intentionally changed.

## Valid Claims Without New Temp Tests

Set-backed plan construction is worth doing after connection planning. The
current `append_unique` / `append_unique_many` helpers in
`django_strawberry_framework/optimizer/plans.py` do linear membership checks.
That is a real cache-miss CPU cost for wide or deeply nested selections, but it
is better validated with a microbenchmark or profiler than a normal assertion
test. Preserve deterministic tuple output from
`OptimizationPlan.finalize`.

Finalize-time relation hints are also worth considering. The walker repeatedly
asks type-level questions while relation metadata is otherwise precomputed.
One important correction from the second pass: custom `get_queryset` is already
stamped on `DjangoTypeDefinition.has_custom_get_queryset` at class creation, so
that part is not remaining MRO work. The useful remaining stamps are narrower:
`FieldMeta.fk_id_elision_eligible`, `FieldMeta.target_pk_name`,
`FieldMeta.default_traversal_kind`, optional post-finalize
`FieldMeta.resolved_target_type`, and a
`DjangoTypeDefinition.has_custom_id_resolver_for(pk_name)` cache to replace
`django_strawberry_framework/optimizer/walker.py::_has_custom_id_resolver`'s
per-walk MRO scan.

Walker-frame reuse is worth doing with the builder refactor. Today
`django_strawberry_framework/optimizer/walker.py::_walk_selections` resolves
`(type_cls, field_map)` at every recursive level through registry lookups.
Threading a small frame object containing `type_cls`, definition, field map,
optimizer hints, and any precomputed name map would remove repeated registry
and dict lookups on deep selection trees. Where a finalized definition exists,
`DjangoTypeDefinition.related_target_for(field_name)` can also replace the
separate `registry.get(django_field.related_model)` target lookup on registered
relations.

The FK-id elision branch has a duplicated child-selection pass. In
`django_strawberry_framework/optimizer/walker.py::_plan_select_relation`,
`_selected_scalar_names` reruns directive filtering, alias merging,
`snake_case`, and related field-map resolution for every forward-FK elision
candidate. Inline classification of child selections during the main relation
walk would avoid that second normalization pass and should land alongside the
set-backed builder work.

Precomputing a GraphQL-name-to-field map is a reasonable follow-up. The walker
currently calls `snake_case(sel.name)` per selection. A definition-level map
from GraphQL response field names to `FieldMeta`, built with the same naming
rules as schema generation, would remove string conversion from the hot walk.
This should be done carefully so custom naming and schema config cannot drift
from Strawberry's emitted names.

`append_prefetch_unique` can move from a list scan to a lookup-path dict if
profiling shows wide prefetch plans. This is lower impact than the `only_fields`
/ resolver-key dedupe because most plans have few top-level prefetches.

Directive-variable-name collection can be memoized per operation in the same
execution-local memo used for printed AST strings. Existing tests already cover
cache-key correctness for directive variables, so this is a performance-only
change.

`OptimizerHint.SKIP` and explicit `OptimizerHint.prefetch(obj)` are useful
consumer performance knobs. `SKIP` avoids planning a relation branch entirely;
`prefetch(obj)` can intentionally replace recursive child planning with a
consumer-owned queryset. This belongs in consumer-facing optimizer guidance more
than in code changes, except for the structural-cache split noted above.

## Claims I Would Not Prioritize As Optimizer Work

The multi-root single context slot is worth keeping in mind, but I did not find
a current failing path to justify making it a top optimizer task. Existing cache
keys are separated by runtime root path, and current synchronous execution
resolves nested fields under the active root plan before the next root publish
matters. If future async or parallel root execution changes that assumption,
stash cumulative branch-keyed sets rather than one overwrite-only set.

The `@skip` / `@include` planner-vs-runtime suspicion is already covered by the
normal optimizer suite. `DjangoOptimizerExtension._build_cache_key` includes
only relevant directive variable values, and the walker evaluates converted
selection directives. No new temp test added.

Aliased selections with different arguments are a future-risk note, not a
current optimizer defect. The current walker intentionally ignores field
arguments for ORM planning. Revisit only when argument-sensitive relation
planning lands.

The `select_related(True)` interaction is already documented as a conservative
consumer-cooperation tradeoff. It may add explicit paths after a wildcard, but
it is not a clear correctness or high-value performance issue.

The scalar `only_fields` / `db_column` concern does not look valid as stated.
Django `QuerySet.only()` accepts model field names and relation attnames, not
raw database column names, so using the GraphQL/Django field name for normal
scalars is the right abstraction. FK and Relay-id attname cases are already
handled separately.

The lazy local import of `convert_selections` is too small to prioritize unless
profiling shows it matters. The import is cached after first use, and connection
planning, cache policy, and walker data structures are better use of optimizer
engineering time.

Interface and inline-fragment over-planning is real but should be treated as a
design problem, not a quick optimizer patch. The current fragment inliner does
not narrow by runtime concrete type, so interface-heavy documents can over-plan
relations selected only for some concrete types. Correct fixes either plan per
concrete type, accept a safe over-fetch, or introduce a more complex union of
structural templates. Revisit this with connection-aware planning once
interface-shaped connection queries are in scope.

Read-side resolver micro-optimizations, such as returning an existing
`_prefetched_objects_cache[field_name]` list without `list(...)`, caching pieces
of resolver-key construction, or generating strictness-free relation resolvers
when strictness is off, are profile-gated. They may matter for very large
result sets, but the database-level plan gaps and cache work above should land
first.

`django_strawberry_framework/optimizer/extension.py::_optimizer_active` appears
to be test-observed but not used by production code. Removing it, or making it a
real guard, is cleanup rather than a meaningful optimizer win.

Plan-cache observability is a useful later addition: eviction counters and
debug-only timing buckets for cache-key build, walker, diff, and apply phases
would make the LRU and structural-cache changes measurable in staging. This
should stay optional and off by default.

## Suggested Order

1. Implement connection-aware node selection walking and make the two connection
   temp tests pass. Build it around a shared node-selection extractor.
2. Switch plan-cache eviction to LRU and make the LRU temp test pass.
3. Move walker construction to set-backed/dict-backed builders while preserving
   deterministic finalized tuples; include walker-frame reuse and remove the
   `_selected_scalar_names` duplicate pass.
4. Stamp the remaining relation-planning booleans at type/finalize time.
5. Precompute finalized-plan frozensets and lookup paths for publish-time
   strictness metadata.
6. Split structural plan caching from request-time dynamic queryset hydration
   and make the structural-cache temp test pass.
7. Consider directive-walk memoization, GraphQL-name maps, prefetch lookup-path
   dicts, resolver micro-opts, and observability after profiling the larger
   changes.

Run the temp probes explicitly when working on this batch:

```bash
uv run pytest tests/optimizer/temp-tests
```
