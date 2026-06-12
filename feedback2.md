# Optimizer Improvement Review

Scope: this file now tracks only the optimizer-improvement findings that still
look actionable after the completed implementation slices. Items that landed
already, did not survive review, or are only generic profiling/observability
ideas have been removed.

## Remaining Findings

### 1. Split structural plan caching from request-time queryset hydration

Status: valid, high-value remaining work.

The optimizer still disables plan caching when a planned prefetch embeds a
request-scoped queryset. The two relevant paths are:

- `django_strawberry_framework/optimizer/walker.py::_plan_prefetch_relation`
  marks the whole plan uncacheable when the target type has a custom
  `get_queryset`, because the generated `Prefetch` contains a queryset built
  with the current `info`.
- `django_strawberry_framework/optimizer/walker.py::_apply_hint` marks the
  whole plan uncacheable for `OptimizerHint.prefetch(obj)` for the same reason:
  the consumer-supplied queryset may close over request state.

That is correct for live queryset safety, but it throws away the stable
structural plan: lookup paths, selected child fields, resolver keys, and
projection metadata are the same for identical query shapes across requests.

Target behavior: cache a frozen structural template for the query shape, then
hydrate dynamic `Prefetch` querysets from the current request at apply time.
Live querysets built from `info.context` must never be stored in the shared
plan cache.

Existing temporary probe:

- `tests/optimizer/temp-tests/test_optimizer_improvement_acceptance.py::test_dynamic_child_queryset_keeps_structural_plan_cache_entry`

Implementation direction:

1. Represent dynamic prefetches in the cached plan as structural specs, not
   constructed `Prefetch` objects with live querysets.
2. At request time, materialize those specs into `Prefetch` objects using the
   current `info`, including custom `get_queryset` hooks and hinted prefetch
   querysets.
3. Preserve the current correctness rule: request-scoped querysets are rebuilt
   once per request, even when the structural plan is a cache hit.
4. Keep finalized plan metadata immutable and deterministic; any hydrated plan
   should be a derived request-local plan, not a mutation of the cached
   template.

### 2. Remove the duplicate child-selection pass in FK-id elision

Status: valid hot-path cleanup.

`django_strawberry_framework/optimizer/walker.py::_plan_select_relation` calls
`_selected_scalar_names` to decide whether a forward FK / OneToOne id-only
selection can be elided. That helper reruns directive filtering, alias merging,
`snake_case`, and field-map resolution for the child selection set. If elision
does not apply, the walker then normalizes the same child selections again
during recursive planning.

Target behavior: classify a relation's child selections once, then reuse that
classification for both FK-id elision and recursive traversal.

Implementation direction: introduce a small normalized child-selection result
for relation planning, carrying at least:

- included/merged child field selections,
- scalar Django field names when the child set is scalar-only,
- an unsafe marker when any selected child cannot be resolved to a scalar field.

Use that result in `_plan_select_relation` before deciding whether to recurse.
The existing behavior must remain fail-closed: unknown fields, relation fields,
or directive states that cannot be proven scalar-only must prevent FK-id
elision.

### 3. Precompute GraphQL-name field lookups on type definitions

Status: valid, lower priority unless paired with walker normalization work.

The walker still resolves every selected field by calling `snake_case(sel.name)`
and probing the definition's Django-name `field_map`. This is small per field,
but it is on the cache-miss walk for every selected node. A definition-level
lookup keyed by emitted GraphQL field name would remove repeated string
conversion and make the walker depend on the same naming source as schema
generation.

Implementation direction: add a finalized, definition-owned map from GraphQL
selection names to `FieldMeta`, built with the same naming rules used when
fields are emitted. The change should not guess at naming policy independently
from Strawberry or the package's schema-generation path. If that shared source
is not available yet, do not add an approximate map.

This pairs naturally with finding 2: once child selections are normalized once,
that normalized result can use the precomputed GraphQL-name map instead of
calling `snake_case` throughout the walk.

## Suggested Order

1. Implement the structural-template / request-hydration split for dynamic
   prefetch querysets, and make the remaining temp probe pass.
2. Remove the `_selected_scalar_names` duplicate pass by normalizing relation
   child selections once.
3. Add a GraphQL-name field lookup map only if it can share the exact schema
   naming source; otherwise leave it out until that dependency is explicit.

Run the remaining temp probe explicitly while working on the structural-cache
split:

```bash
uv run pytest tests/optimizer/temp-tests/test_optimizer_improvement_acceptance.py::test_dynamic_child_queryset_keeps_structural_plan_cache_entry
```
