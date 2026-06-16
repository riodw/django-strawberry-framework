# Performance Review 2

> **Verification pass (2026-06-15).** Every claim below was re-checked against live
> source. All anchors resolve, the fix-check (H1–H5, B1) is accurate, and the two
> cache `maxsize` values (`_cascadable_edges` 1024, `_path_traverses_to_many` 2048)
> match. `_build_cache_key`'s per-execution `print_ast` memoization
> (`_printed_ast_cache`) is real, so the "AST/key memoization" claim holds. The
> scratch-probe *outputs* (query counts, timings, `CacheInfo`) were not re-executed
> this pass; the source behavior each probe asserts was verified by reading. Two
> reconciliation notes were added inline (Finding 1 placement; the "No Action"
> finding vs `feedback.md` L1) — see the **[corrected]** tags.

## `feedback.md` Fix Check

Current `docs/feedback.md` is a performance deep-dive, and its package findings are
**not** fixed in the current package code.

- H1 is still present: `django_strawberry_framework/types/resolvers.py::_make_relation_resolver` still returns `list(getattr(root, accessor_name).all())` in `many_resolver`.
- H2 is still present: `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.apply_to` still calls `ast_to_converted_selections(...)` before `_get_or_build_plan(...)`, so cache hits still pay conversion cost.
- H3 is still present: `django_strawberry_framework/utils/permissions.py::run_active_input_permission_checks` still calls `_active_permission_field_paths(...)` and `_iter_active_related_branches(...)` as two independent traversals.
- H4 is still present: `django_strawberry_framework/registry.py::TypeRegistry.definition_for_graphql_name` still scans `iter_definitions()` per decode.
- H5 is still present: optimizer selection handling still routes through `ast_to_converted_selections(...)`, `included_field_selections(...)`, and `_merge_aliased_selections(...)` rather than a single graphql-core subfield collection pass.
- B1 is still present: `django_strawberry_framework/connection.py::_attach_count_sync` still calls `nodes.count()` for selected root `totalCount`.

The earlier spec-034 cookbook-review items are fixed in the package/spec:

- `docs/SPECS/spec-034-permissions-0_0_10.md #"required parity (helper-level; the consumer `view_<model>` branch intentionally diverges"` is present.
- `docs/SPECS/spec-034-permissions-0_0_10.md #"Consumer-recipe divergence (cookbook `view_<model>`)."` is present.
- `examples/fakeshop/apps/products/schema.py #"TODO-BETA-046-0.1.1"` and `examples/fakeshop/apps/products/schema.py #"TODO-BETA-052-0.1.5"` are present.
- No stale `TODO-BETA-038`, `TODO-BETA-039`, `TODO-BETA-040`, or `TODO-BETA-051` references remain in `examples/fakeshop/apps/products/schema.py`.

## Findings

### Confirm - Already-Carded `_result_cache` Guard Still Missing

`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize` normalizes a resolver result and sends every `QuerySet` into `DjangoOptimizerExtension.apply_to`. `apply_to` then builds/applies an optimizer plan without checking whether the queryset already has `_result_cache` populated.

Upstream explicitly avoids this in `strawberry_django/optimizer.py::optimize #"if is_optimized(qs) or qs._result_cache is not None"`: already-evaluated querysets are returned unchanged so the resolver's cached rows are not thrown away.

Current `docs/feedback.md` excludes this as already carded under G1 / `spec-035`, so
this is not a new uncarded finding. It is still worth recording here because the
scratch probe confirms the package behavior is still present.

Scratch verification against fakeshop:

```text
resolver_cache_populated True
query_count 2
sql 1 SELECT "library_branch"."id", "library_branch"."name", "library_branch"."city"
sql 2 SELECT "library_branch"."id", "library_branch"."name"
```

The second query is produced by the optimizer applying `.only(...)` to an already-evaluated queryset clone. This is a pure performance regression for resolvers that intentionally materialize once and return the queryset object. It can also discard consumer-side queryset cache/prefetch work that the resolver deliberately established before returning.

Recommended root-cause fix for the G1 / `spec-035` implementation: add an
evaluated-queryset bypass in `DjangoOptimizerExtension.apply_to`, before selection
conversion and plan-cache lookup:

```python
if getattr(queryset, "_result_cache", None) is not None:
    return queryset
```

`apply_to` is the right central seam because both middleware optimization and `DjangoConnectionField`'s `apply_connection_optimization` route through it. Do not move this earlier than visibility/filter/order processing in connection/list pipelines; security scoping must still run. The bypass should only skip the optimizer's projection/prefetch plan over a queryset that is already evaluated.

**[corrected] Placement vs the G1 card's `_optimize` anchor.** The `spec-035` G1
checklist anchors the guard in `DjangoOptimizerExtension._optimize`, explicitly
*after* the manager→`.all()` coercion (a `Manager` coercion always yields a fresh
unevaluated `QuerySet`, so the guard must not pre-empt it). Putting the guard at the
top of `apply_to` instead — as recommended above — is consistent with that
constraint, not in conflict with it: `_optimize` coerces the manager *before* it
calls `apply_to` (`extension.py::_optimize #"return self.apply_to(resolved.origin, resolved.model, result, info)"`),
and a bare `Manager` has no `_result_cache` attribute, so `getattr(queryset,
"_result_cache", None)` is `None` and the guard naturally skips it. The `apply_to`
seam is in fact the broader choice because it also covers the
`apply_connection_optimization` path (`extension.py #"return optimizer.apply_to("`),
which `_optimize` does not. Implementers should pick one seam; `apply_to` is
preferred for that coverage, provided the manager-coercion ordering is preserved on
the `_optimize` path.

Coverage should follow the repo rule: if practical, pin this through a real fakeshop GraphQL query in `examples/fakeshop/test_query/`; otherwise use the narrowest package test that exercises `DjangoOptimizerExtension.apply_to` with an evaluated queryset. Do not use mocks for the queryset behavior.

### Keep - Static Metadata Caches Are Correct

The current package now has the two performance caches that matter on static metadata:

- `django_strawberry_framework/permissions.py::_cascadable_edges`
- `django_strawberry_framework/orders/sets.py::_path_traverses_to_many`

Scratch verification:

```text
cascade_empty_same_sql True
cascade_cache CacheInfo(hits=2, misses=2, maxsize=1024, currsize=2)
order_cache CacheInfo(hits=1, misses=1, maxsize=2048, currsize=1)
cascade_cached_10000 0.002707
cascade_cold_10000 0.014772
order_cached_10000 0.000727
order_cold_10000 0.007974
```

These are safe because they cache immutable Django model metadata, not request state, users, permission decisions, querysets, or `Prefetch` objects. Keep this boundary strict.

### Keep - Plan Cache Is Ahead of Upstream, With the Right Security Boundary

Upstream caches model-field inspection in `strawberry_django/utils/inspect.py::get_model_fields`, but its optimizer still rebuilds `OptimizerStore` state for each optimization call. This package has a bounded operation plan cache in `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._get_or_build_plan`, plus per-execution AST/key memoization in `django_strawberry_framework/optimizer/extension.py::_build_cache_key`.

Scratch verification:

```text
cacheable scalar query:
run 1 cache CacheInfo(hits=0, misses=1, size=1)
run 2 cache CacheInfo(hits=1, misses=1, size=1)
run 3 cache CacheInfo(hits=2, misses=1, size=1)

custom-visibility relation query:
run 1 cache CacheInfo(hits=0, misses=1, size=0)
run 2 cache CacheInfo(hits=0, misses=2, size=0)
```

That second shape is correct: plans embedding target `get_queryset` visibility querysets are not cacheable. Do not trade this away for hit rate. Caching user-scoped `QuerySet`s, target visibility outputs, or consumer `Prefetch` objects would be a security bug.

### No Action - Do Not Copy Upstream's Broad Model-Fields Cache

Upstream's `get_model_fields` cache is useful for its architecture, but the hot path here is already different: `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.field_map` is built once at `DjangoType` class construction and consumed by `django_strawberry_framework/optimizer/walker.py::_resolve_field_map`.

Adding a second broad process-wide cache over `model._meta.get_fields()` would duplicate state, increase invalidation surface around `registry.clear()`, and provide little benefit on the registered-type path. The narrow caches above are the better fit.

**[corrected] Direct conflict with `feedback.md` L1 — this finding supersedes it.**
The current `feedback.md` L1 proposes the *opposite*: a narrow `@lru_cache` over the
**registry-less fallback** branch of `_resolve_field_map`
(`walker.py::_resolve_field_map #"{f.name: f for f in model._meta.get_fields()}"`),
ranked as a minor win. The two cannot both stand, and **No Action is the
better-reasoned position** for two verified reasons. (1) The fallback branch is
rarely on a hot path: it fires only when `registry.get(model)` returns `None` for the
walked model, but a relation is only *selectable* in GraphQL when its target has a
registered `DjangoType` — so the registered `definition.field_map` precompute (B7)
covers the real per-request traffic, and the fallback is an edge case, not a per-row
loop. (2) `feedback.md` L1 itself concedes the cache "must invalidate on
`registry.clear()`" — that invalidation coupling is exactly the maintenance surface
this finding declines to add for a near-zero benefit. Net: `feedback.md` L1 should be
**withdrawn / downgraded to No Action** so the two reviews agree; the narrow caches
on genuinely-immutable metadata (`_cascadable_edges`, `_path_traverses_to_many`)
remain the correct boundary.

### Watch - Filter Logical Branch Instantiation Cost

`django_strawberry_framework/filters/sets.py::FilterSet._q_for_branch` correctly builds a sibling `FilterSet` per logical branch so django-filter's form validation, per-instance filter copies, related-visibility constraints, and recursive `and`/`or`/`not` behavior stay isolated. The cost scales with `branches * filter_count` because django-filter deep-copies `base_filters` during instance construction.

Do not optimize this with a shortcut. A real improvement would need a production abstraction that preserves django-filter's per-instance mutation semantics while avoiding repeated deep copies. Until profiling shows this path hot, keep the existing correctness-first design.

## TODO-BETA-046 Guidance

For the FieldSet work, follow the same performance boundary:

- Reuse `DjangoTypeDefinition.field_map` and static metadata caches where possible.
- Prefer class/finalization-time expansion over per-request introspection.
- Do not cache request/user/queryset-dependent authorization results globally.
- Keep the public consumer surface `Meta`-driven; do not introduce stacked Strawberry decorators for consumer-facing classes.
