# Spec: Optimizer & Reverse-Relation Resolution

## Problem statement

`spec-django_types.md` predicted that the optimizer half of its scope would eventually warrant its own document; running Slice 4's tests confirmed it. Two concrete failures push the optimizer story into its own subsystem.

The first failure is correctness, not performance. When a `DjangoType` exposes a reverse relation (`Category.items` -> `list[ItemType]`), Strawberry's default resolver does `getattr(category, "items")`, gets back a Django `RelatedManager`, and raises `Expected Iterable, but did not find one for field 'CategoryType.items'`. A `RelatedManager` is not directly iterable; the consumer code has to call `manager.all()`. Until the framework supplies a custom resolver for relation fields, every reverse relation in a generated GraphQL type is broken at the schema level, irrespective of any optimizer.

The second failure is performance. Slice 4's optimizer hooks per-resolver via Strawberry's `resolve` / `aresolve` extension hooks. It optimizes only the queryset returned by *that* resolver. For a query like `{ allCategories { items { entries { value } } } }` it would (if reverse rels worked) call `prefetch_related("items")` on the top-level Category queryset, but it cannot emit `prefetch_related("items__entries")` because by the time the Item-level resolver fires the parent queryset is already evaluated. Depth >1 N+1 returns. strawberry-graphql-django solved this by hooking earlier in Strawberry's lifecycle and walking the entire selection tree once. Our current architecture cannot.

These two problems are coupled: the resolver work and the optimizer work share a single seam (how relations are read off a model instance during GraphQL field resolution), and any clean fix has to address both at once.

## Current state

`docs/spec-django_types.md` Slice 4 shipped:

- `DjangoOptimizerExtension` as a Strawberry `SchemaExtension` with `resolve` / `aresolve` hooks.
- `_optimize` returns the result unchanged for non-`QuerySet` returns.
- `_unwrap_return_type` and `_plan` walk `info.selected_fields[0].selections` and dispatch by cardinality flags into a `select_related` list and a `prefetch_related` list.
- `registry.model_for_type(type_cls)` reverse-lookup helper.

Slice O1 has shipped (custom relation resolvers in `DjangoType.__init_subclass__`); the iterability error is fixed across forward FK / OneToOne / reverse FK / OneToOne / M2M. See `tests/test_django_types.py` "Slice O1" section for the integration tests and the three direct unit tests of `_make_relation_resolver`.

Slice 4's tests in `tests/test_optimizer.py`:

- `test_optimizer_applies_select_related_for_forward_fk` — still `@pytest.mark.skip(reason="spec-optimizer.md O3")`. Iterability is no longer the blocker; the remaining one is type-tracing — see "Slice-4 type-tracing limitation" below.
- `test_optimizer_applies_prefetch_related_for_reverse_fk` — still `@pytest.mark.skip(reason="spec-optimizer.md O3")`. Same type-tracing limitation.
- `test_optimizer_combines_select_related_and_prefetch_related` — still `@pytest.mark.skip(reason="spec-optimizer.md O3 + O4")`. Same type-tracing limitation, plus the depth-2 chain that needs O3's top-level walker.
- `test_optimizer_skips_when_no_relations_selected` — passing (but for the wrong reason — see below).
- `test_optimizer_passes_through_non_queryset` — passing.
- `test_optimizer_passes_through_unregistered_return_type` — passing.
- All direct unit tests of `_unwrap_return_type` / `_plan` / `_snake_case` / `aresolve` — passing.

Slice-4 type-tracing limitation: at the per-resolver `resolve` / `aresolve` hooks, `info.return_type` is graphql-core's wrapper shape — `GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLObjectType('ItemType'))))` — not the consumer's `list[ItemType]` annotation. `_unwrap_return_type` only peels one layer (`getattr(rt, "of_type", None)`) and returns the inner `GraphQLList` wrapper, so `registry.model_for_type(...)` always yields `None` and `_optimize` exits early before applying any `select_related` / `prefetch_related`. The "passing" Slice-4 tests pass because they short-circuit on this `None` (no relations selected, or non-`QuerySet` returns) — not because the planner ever fires. O3's `on_executing_start` hook receives the Python annotation directly and side-steps this; no separate fix is needed before O3 lands.

Slice 5 (`only()` projection) and Slice 6 (`plan_relation` + `Prefetch` downgrade) inside `spec-django_types.md` are still TODO. They are now this spec's scope.

graphene-django's reverse-relation resolution is a custom `Field.wrap_resolve` per FK / M2M (see `converter.py:308-471`). graphene-django does not ship an optimizer — it relies on `graphene-django-optimizer` which uses the same selection-tree-walk approach as strawberry-graphql-django.

strawberry-graphql-django's reverse-relation resolution lives in `StrawberryDjangoField.get_result` (`strawberry_django/fields/field.py`). The branch that matters: when the Django attribute is a `ReverseManyToOneDescriptor`, it calls `getattr(source, attname)` and trusts the manager-as-queryset shape because the optimizer has already replaced the manager with a prefetched queryset. When the optimizer is off, it falls back to a `manager.all()` call inside `django_getattr`. The optimizer itself, in `strawberry_django/optimizer.py`, hooks `on_executing_start` and walks the entire `info.selected_fields` tree once, building nested `Prefetch` chains.

## Goal

Make reverse relations resolve correctly in every `DjangoType` and make the optimizer effective at arbitrary nesting depth. Specifically:

- A query like `{ allCategories { items { name } } }` returns 2 SQL queries with the optimizer enabled, and 1 + N when disabled (correct results either way).
- A query like `{ allCategories { items { entries { value } } } }` returns 3 SQL queries with the optimizer enabled, and 1 + N + N*M when disabled.
- Forward-FK joins still collapse via `select_related`.
- The `get_queryset` + `Prefetch` downgrade rule from `spec-django_types.md` lands on the new architecture.
- `only()` column projection lands once the new architecture is in place.

## Non-goals

This spec does not cover filtering, ordering, aggregations, permissions beyond the existing `get_queryset` hook, mutations, polymorphic interfaces, or the relay connection field. Those belong to later specs that build on this one.

## Two architectural options

The reverse-relation correctness fix and the nested-prefetch fix are not independent — they both turn on how the framework gets between Strawberry and the Django model instance during field resolution. Two coherent shapes are on the table.

### Option A: per-field custom resolvers, optimizer stays per-resolver

Generate a `strawberry_field`-equivalent per relation field on every `DjangoType`. The resolver for a reverse rel calls `manager.all()`; the resolver for a forward FK / M2M is the same shape. The optimizer keeps its current per-resolver `resolve` / `aresolve` hooks but also gains the ability to plan nested optimizations because each level's resolver can read its own selection set and apply `select_related` / `prefetch_related` to its own queryset return.

This is closer to graphene-django's wrap-resolve-per-field model.

Trade-offs.

- Pro: the resolver layer is straightforward — one resolver per relation, mechanical to generate from the existing `convert_relation` output.
- Pro: per-resolver optimization is local; each level of the selection tree is optimized when its resolver runs.
- Con: nested prefetch is genuinely hard. By the time the inner resolver fires, the outer queryset is already evaluated; you cannot retroactively `prefetch_related("items__entries")` from the items level. The best you can do is per-level prefetches, which on `M*N` rows still issues `M+1` queries instead of `2`. graphene-django-optimizer does not solve this; it falls back to a top-level walk.
- Con: every relation field carries a resolver — a small but not free cost on every request.

### Option B: top-level selection-tree walk, custom resolvers only where the optimizer cannot reach

Hook the optimizer earlier — `on_executing_start` instead of per-resolver `resolve`. At the start of execution, walk `info.selected_fields` once, build a nested-prefetch plan (`prefetch_related("items__entries")`), and apply it to the top-level queryset. Reverse-rel fields still need a custom resolver because Strawberry's default resolver chokes on `RelatedManager`, but the resolver is now a one-line `getattr(source, attname)` that trusts the optimizer has already replaced the manager with a prefetched queryset (and falls back to `manager.all()` if no optimizer is in play).

This is exactly strawberry-graphql-django's architecture.

Trade-offs.

- Pro: nested prefetches work to arbitrary depth in a single `prefetch_related` call.
- Pro: matches the upstream design that has been battle-tested at scale.
- Pro: keeps the resolver layer tiny — one line per relation field.
- Con: the selection-tree walk is the most complex piece of code in the package. It needs a recursive walker that handles fragments, inline fragments, aliases, conditional `@skip` / `@include` directives, and union types.
- Con: the optimizer becomes more "magic" — the queryset it returns has an opaque internal Prefetch chain that consumers have to debug via Django's query log if anything is off.
- Con: the `Prefetch` downgrade rule from `spec-django_types.md` becomes more involved, because `Prefetch` objects nest along with `prefetch_related` chains and need to be assembled top-down.

### Recommendation

**Option B.** The reasons are concentrated in the trade-off table:

- Option A cannot deliver the nested-prefetch goal stated above; depth >1 stays N+1 by construction. That alone disqualifies it for a foundation that any consumer would actually want to ship.
- Option B is more upfront work but its complexity is bounded — there's a single recursive walker and a single resolver shape, both modeled directly on strawberry-graphql-django which has solved this before us. We are not exploring novel architecture; we are translating known-good behavior into our DRF-shaped `Meta` API.
- Option B's per-relation resolver is also where the existing `convert_relation` output gets used, so we tie the type-system half and the optimizer half together at exactly one seam (the registered relation list per `DjangoType`), which is the cleanest possible interface.

The rest of the spec assumes Option B unless explicitly noted.

## Proposed implementation slices

Each slice ships with tests in the same change. The existing failing tests in `tests/test_optimizer.py` get unskipped slice-by-slice as their behavior comes online.

Slice O1 — Custom resolvers for relation fields. Generate one resolver per relation field at `DjangoType` finalization time. Insertion point: `DjangoType.__init_subclass__`, after `registry.register(...)` and before the `strawberry.type(cls)` call, so the synthesized resolvers are attached to the class when Strawberry processes it. (The TODO anchor for this slice already sits at that location in `django_strawberry_framework/types.py`.) Forward FK / OneToOne resolver: `getattr(source, attname)` (the cached value if the optimizer has set it, else triggers Django's lazy load). M2M resolver: `list(getattr(source, attname).all())` if not prefetched. Reverse FK / OneToOne resolver: same `manager.all()` shape with prefetch-cache awareness. After this slice, `{ allCategories { items { name } } }` returns correct results in 26 SQL queries (1 + 25). The optimizer is still off-architecture and not invoked.

Slice O2 — Selection-tree walker. New module `optimizer/walker.py`. A pure function `plan_optimizations(selected_fields, model) -> OptimizationPlan` that receives the pre-peeled selection list (typically `info.selected_fields[0].selections` — the caller in O3 owns that peel) and walks it recursively, mapping each relation selection to a `Prefetch` chain and each scalar selection to an `only()` column. Taking `selected_fields` instead of `info` keeps the walker a pure function with no Strawberry dependency, which is why the synthetic-`info` test harness works without standing up a schema.

Three load-bearing details the walker must get right (strawberry-graphql-django's `optimizer.py` is the reference; expect to spend most of O2's complexity budget here):

- **Fragments.** Named fragments (`...FragmentName`) and inline fragments (`... on TypeName`) both contain selections that count toward the plan. The walker must descend into `selection.selections` recursively for any fragment node and treat its children as if they were direct children of the parent. Fragment spreads referencing the same fragment from different selection sites must merge cleanly without double-prefetching.
- **Aliases.** A query like `{ first: items(...) { id } second: items(...) { name } }` issues two selections both bound to the Django field `items`, just under different GraphQL aliases. The walker must normalize on the underlying field name (`selection.name`), not the alias, when looking up the Django field via `model._meta`. Aliases that resolve to the same field name need their selection sets merged before planning.
- **`@skip` / `@include` directives.** A selection with `@skip(if: true)` or `@include(if: false)` is omitted from execution, so it should be omitted from the plan. The directive arguments are typically constant booleans at this stage (variables are already resolved), so evaluation is a literal check; if a future change exposes unresolved variables here, treat them as "selected" to avoid silently dropping prefetches the consumer needed.

These three cases are why a synthetic-`info` test harness matters: each one has a tight, isolated test case that exercises the walker without standing up a Strawberry schema. Mirror strawberry-graphql-django's selection-walking utilities (e.g. `get_sub_field_selections`) rather than reinventing the dispatch.

Slice O3 — Top-level optimizer hook. Replace `resolve` / `aresolve` with `on_executing_start`. Detect the root resolver's queryset return, run the planner from O2 against it, replace the resolver's return with the optimized queryset. The slice unskips and passes the three currently-skipped optimizer tests (`test_optimizer_applies_select_related_for_forward_fk`, `test_optimizer_applies_prefetch_related_for_reverse_fk`, `test_optimizer_combines_select_related_and_prefetch_related`).

Slice O4 — Nested prefetch end-to-end. Extend the planner to emit `prefetch_related("items__entries")` style chains. Add tests that assert query counts at depths 2 and 3 (`category > items > entries` and `entry > item > category`).

Slice O5 — `only()` projection. Extend the planner to emit the `only()` column list, including the FK columns required to materialize `select_related` joins (per `spec-django_types.md`'s "only() and FK columns" section). Tests use `qs.query.deferred_loading` to confirm the column projection.

Slice O6 — `get_queryset` + `Prefetch` downgrade. The planner consults `target_type.has_custom_get_queryset()` and, when true, emits a `Prefetch(queryset=target_type.get_queryset(target.objects.all(), info))` instead of a `select_related`. The `_is_default_get_queryset` sentinel from `spec-django_types.md` lights up here. The end-to-end visibility-leak test in `tests/test_django_types.py` (currently `@pytest.mark.skip`) gets unskipped.

## Coordination with `spec-django_types.md`

`spec-django_types.md` Slices 4-6 are superseded by this spec's O1-O6. The DjangoType spec's `## Suggested implementation slices` section should be edited to mark Slices 4-6 as "moved to spec-optimizer.md" and the `## Scope creep into the N+1 problem` section's third paragraph (the one that justified bundling) should be revisited — the bundle didn't survive contact with implementation.

The three optimizer tests blocked by the architectural shift (`test_optimizer_applies_select_related_for_forward_fk`, `test_optimizer_applies_prefetch_related_for_reverse_fk`, `test_optimizer_combines_select_related_and_prefetch_related`) live in `tests/optimizer/test_extension.py` and carry `@pytest.mark.skip` markers citing `spec-optimizer.md O3`. O1 has shipped, but O3 still gates them because the per-resolver hook can't trace types through graphql-core's wrappers. They unskip in O3 once the top-level hook is in place. The remaining `tests/optimizer/test_extension.py` cases (`_plan` unit tests, `aresolve`, the no-relations / pass-through cases, the synthetic-info cardinality dispatch and `select_related` / `prefetch_related` application) keep passing throughout the rebuild and gate against regressions in the legacy code path until O3 retires it. The `unwrap_return_type` and `snake_case` helpers that used to live on `DjangoOptimizerExtension` moved to `django_strawberry_framework.utils` in 0.0.2 and have their own unit tests in `tests/utils/`.

The `_is_default_get_queryset` sentinel and `has_custom_get_queryset` introspection helper still belong in `spec-django_types.md` — they are part of the type-system surface that the optimizer consumes. The Slice 6 wiring of `__init_subclass__` ("flip the sentinel when the subclass declares get_queryset") moves to this spec's O6 because the consumer of the sentinel is now here.

The `model_for_type` reverse-lookup on `TypeRegistry` stays where it is. Both halves use it.

## Visibility status (alpha)

Per `docs/spec-public_surface.md`, `DjangoOptimizerExtension` does not currently meet the top-level re-export rules: the per-resolver dispatch is shipped (Slice 4) and Slice O1's relation resolvers are shipped, but the type-tracing limitation through graphql-core's wrappers means the optimizer is not effective end-to-end. Three of the optimizer's tests in `tests/optimizer/test_extension.py` are `@pytest.mark.skip` pending O3 for that reason.

**Decision for 0.0.3.** Drop `DjangoOptimizerExtension` from `django_strawberry_framework/__init__.py`'s `__all__`. Power users and tests still import via:

```
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
```

The class returns to the top-level `__all__` when O3 (the `on_executing_start` hook) lands and the three currently-skipped optimizer tests unskip and pass. That promotion is part of the O3 slice's definition of done — the `__init__.py` change ships in the same commit as the hook flip.

This is the visibility-discipline pattern from `docs/spec-public_surface.md`: a Layer-2 subsystem stays subpackage-only until its core hook is effective. The optimizer's status marker in `docs/README.md` is `partial` until O3 ships, then `shipped`.

## Open questions

Hooking point: `on_executing_start` is the analog of strawberry-graphql-django's choice, but Strawberry's extension API has been rearranged in recent releases. Confirm at O3 implementation time that the `info` object available at `on_executing_start` carries the `selected_fields` we need. If not, the next-best hook is `resolve` on the root type only, gated by `info.path.prev is None`.

Async resolver compatibility: Strawberry calls `resolve` for sync resolvers and `aresolve` for async; the optimizer's planner is sync (querysets are lazy regardless). Keep the planner as a pure sync function and call it from both hooks; the queryset's actual evaluation happens later in whichever async / sync context Strawberry chose.

Custom resolver opt-out: should consumers be able to override the auto-generated relation resolver with their own `@strawberry_django.field` decorator? Recommendation: yes, eventually — the auto-generated resolver only fires when no consumer-declared resolver exists for that name. Defer until O1 implementation surfaces a concrete need.

`only()` opt-out per consumer field: strawberry-graphql-django ships `disable_optimization=True` on individual fields. We should plan for the same flag, on `Meta.optimizer_overrides` or a per-field marker, but defer the API decision until O5.

## References

graphene-django relation resolver wrap (forward FK / M2M / reverse): `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py:308-471`.

graphene-django-optimizer top-level walk: `https://github.com/tfoxy/graphene-django-optimizer` (no local checkout; reference upstream when implementing O2).

strawberry-graphql-django field result resolver: `https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/fields/field.py` — see `StrawberryDjangoField.get_result`.

strawberry-graphql-django optimizer extension: `https://strawberry.rocks/docs/django/guide/optimizer` and the source under `strawberry_django/optimizer.py` in the same repository.

The visibility-leak / `Prefetch` downgrade discussion that motivated bundling the optimizer with `spec-django_types.md` originally: issue #572 and PR #583 on `strawberry-graphql/strawberry-django`.
