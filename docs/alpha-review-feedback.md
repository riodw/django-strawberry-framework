Additional Findings

A. Plan cache key collides across root fields with the same target model

Priority: P1 (likely pre-existing, but newly load-bearing under O4)

DjangoOptimizerExtension._build_cache_key returns:
python
return (doc_hash, relevant_vars, target_model)

Two root fields in the same operation that return the same model — e.g. { allCategories { items { id } } featured: someOtherCategoryRoot { name } } — produce the same (doc_hash, relevant_vars, target_model) tuple, so the second resolver pulls the first root's plan out of the cache and applies it to a queryset whose actual selections are different. Before O4 this was a smaller problem (depth-1 plans were mostly additive). With nested Prefetch objects now embedding child querysets and only() projections, applying the wrong plan can either over- or under-fetch.

The cache key also doesn't account for which root field within the operation is being optimized. A robust key would include something like the AST path of the resolved root field (e.g. info.path.key) or info.field_name, in addition to the model.

Relevant code:
•  django_strawberry_framework/optimizer/extension.py:420-452 (_build_cache_key)

B. _get_relation_field_name in resolvers.py is now dead code

Priority: P3
django_strawberry_framework/types/resolvers.py (37-41)
def _get_relation_field_name(info: Any) -> str:
    """Return the Django field name for the current resolver.
    ...
    """
    return snake_case(getattr(info, "field_name", "") or "")

Nothing in resolvers.py (or anywhere else after the resolver-key migration) calls it. Either delete it or wire it into _runtime_path_from_info if you want to keep a fallback for missing info.path.

C. plans.py module docstring still says "three bags" but lists 5+ fields

Priority: P3
django_strawberry_framework/optimizer/plans.py (1-9)
"""``OptimizationPlan`` — the shape the walker emits and the extension consumes.

The plan is a simple data class carrying three bags:

- ``select_related``: ...
- ``prefetch_related``: ...
- ``only_fields``: ...
- ``fk_id_elisions``: ...
"""

The class now also carries planned_resolver_keys and cacheable. Update "three bags" and add the new fields to the docstring listing.

D. Test gap: test_plan_merges_aliased_selections doesn't assert per-alias resolver keys

Priority: P3
tests/optimizer/test_walker.py (318-328)
def test_plan_merges_aliased_selections():
    """Aliased selections for the same relation produce one plan entry."""
    plan = plan_optimizations(
        [
            _sel("items", selections=[_sel("id")], alias="first"),
            _sel("items", selections=[_sel("name")], alias="second"),
        ],
        Category,
    )
    prefetch = _prefetch_entry(plan)
    assert prefetch.prefetch_to == "items"

The test only verifies that the merge happened and produced a single Prefetch. It doesn't assert that planned_resolver_keys contains both items@first and items@second — which is the actual contract _response_keys exists to support. Add:
python
assert plan.planned_resolver_keys == ["items@first", "items@second"]

E. _merge_aliased_selections overwrites directives and arguments from the second occurrence

Priority: P3

The SimpleNamespace is built from the first occurrence; directives and arguments from the second alias are dropped:
django_strawberry_framework/optimizer/walker.py (405-412)
else:
    merged = SimpleNamespace(
        name=sel.name,
        alias=getattr(sel, "alias", None),
        directives=getattr(sel, "directives", None) or {},
        arguments=getattr(sel, "arguments", None) or {},
        ...
    )

In practice this is fine because _should_include already filtered both inputs before merge and arguments aren't consulted by the walker. But if you ever extend the walker to look at arguments (e.g. for a future filter-aware optimization), it will silently see only the first alias's arguments. Worth a comment noting the limitation.

F. _plan_prefetch_relation falls back to a string lookup but spec recommends always-Prefetch

Priority: P3 (re-flagged from previous review)

I noticed this hasn't been addressed yet:
django_strawberry_framework/optimizer/walker.py (253-255)
if child_plan.is_empty and not has_custom_get_queryset:
    _append_unique(plan.prefetch_related, full_path)
    return

Spec says: "Prefer Prefetch for uniformity with B8 diffing." Switching to always-Prefetch would cost one extra Prefetch(full_path) allocation per trivial prefetch but would simplify B8 diffing and lookup_paths consumers (no need to handle the isinstance(entry, str) branch).

Overall

The fixes addressed the higher-priority items cleanly. The A finding (cache-key collision) is the most concerning — it's likely a latent bug that O4 makes worse because plans are now larger and more selection-dependent. B, C, D, E are housekeeping. F is a forward-looking recommendation, not a bug.