# Spec: Optimizer & Reverse-Relation Resolution

## Purpose
This parent spec records the optimizer architecture and the shipped foundation slices for relation resolution, root-gated query planning, `only()` projection, and `get_queryset`-aware `Prefetch` downgrade.

O4 has been extracted out of this document. The O4 implementation source of truth is `docs/spec-optimizer_nested_prefetch_chains.md`. Keep all O4 design, pseudocode, insertion points, and test planning there rather than duplicating them here.

## Problem statement
`spec-django_types.md` predicted that the optimizer half of its scope would eventually warrant its own document; running the early DjangoType slice tests confirmed it. Two concrete failures pushed the optimizer story into its own subsystem:

- Reverse relations exposed by `DjangoType` need generated resolvers because Strawberry's default resolver returns a Django `RelatedManager`, which is not directly iterable.
- Query planning needs to run from the operation root so the optimizer can inspect the GraphQL selection tree before relation resolvers evaluate model attributes.

These problems share one seam: how the framework gets from Strawberry field resolution to the underlying Django model relation.

## Current state
The foundation optimizer architecture has shipped:

- O1 — Custom resolvers for relation fields.
- O2 — Selection-tree walker in `django_strawberry_framework/optimizer/walker.py`.
- O3 — Root-gated optimizer hook in `DjangoOptimizerExtension`.
- O5 — `only()` projection.
- O6 — `get_queryset` + `Prefetch` downgrade.

`DjangoOptimizerExtension` is exported from `django_strawberry_framework.__init__`, root optimizer plans are stashed on context for introspection, and the extension is covered by the optimizer test suite.

The only remaining O-slice from this parent spec is O4, which now lives in `docs/spec-optimizer_nested_prefetch_chains.md`.

## Architecture decision
The chosen architecture is a root-gated selection-tree walk plus generated relation resolvers.

The optimizer runs from Strawberry's `SchemaExtension.resolve` hook, gated by `info.path.prev is None`. Root resolvers returning a Django `QuerySet` are planned once, then the resulting `OptimizationPlan` is applied to that queryset. Non-root resolvers and non-`QuerySet` values pass through unchanged.

Generated relation resolvers remain necessary even with the optimizer because they provide correct behavior when the optimizer is disabled or when a relation is not already loaded. They also host the B2/B3 runtime sentinels used by later optimizer behavior.

## Shipped slices
### O1 — Custom relation resolvers
`DjangoType.__init_subclass__` attaches one resolver per relation field. Forward FK / OneToOne resolvers return the related attribute. Reverse FK / M2M resolvers return `list(manager.all())` when needed so Strawberry receives an iterable. Reverse OneToOne resolvers collapse missing related rows to `None`.

### O2 — Selection-tree walker
`plan_optimizations(selected_fields, model, info=None)` walks Strawberry selections, maps Django relation fields through `_optimizer_field_map`, handles fragments/directives/aliases, and produces an `OptimizationPlan`.

### O3 — Root-gated optimizer hook
`DjangoOptimizerExtension.resolve` gates optimization to root resolvers, traces graphql-core return types back to registered `DjangoType` models, calls the walker, stashes the plan on context, and applies the plan to the root queryset.

### O5 — `only()` projection
The walker records selected scalar columns and required FK connector columns in `OptimizationPlan.only_fields`. `OptimizationPlan.apply()` calls `QuerySet.only()` when the plan carries projected fields.

### O6 — `get_queryset` + `Prefetch` downgrade
When a target `DjangoType` has a custom `get_queryset`, the planner avoids `select_related` for that relation and emits a `Prefetch` with the target queryset instead. These plans are marked uncacheable because they may depend on request context.

## O4 extraction
O4 is not specified here anymore. Use `docs/spec-optimizer_nested_prefetch_chains.md` as the only O4 implementation plan. When O4 ships, update this file only to mark O4 as shipped and keep the detailed implementation record in the extracted spec.

## Coordination with `spec-django_types.md`
`spec-django_types.md` Slices 4–6 are superseded by this optimizer spec family. The type-system pieces still belong in `spec-django_types.md`; the optimizer consumes them here.

The `_is_default_get_queryset` sentinel and `has_custom_get_queryset` introspection helper remain part of the type-system surface. O6 consumes that surface when choosing between `select_related` and `Prefetch`.

The `TypeRegistry` model/type reverse lookup remains shared by both halves.

## Visibility status
O1, O2, O3, O5, and O6 have shipped. The optimizer is public via `DjangoOptimizerExtension`.

O4 remains open and is tracked exclusively in `docs/spec-optimizer_nested_prefetch_chains.md`.

## Open questions
Custom resolver opt-out: consumers should eventually be able to override generated relation resolvers with their own resolver. The generated resolver should only fire when no consumer-declared resolver exists for that field.

`only()` opt-out per consumer field: strawberry-graphql-django ships `disable_optimization=True` on individual fields. A similar flag should be considered in a future optimizer-control spec.

## References
graphene-django relation resolver wrap: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py:308-471`.

graphene-django-optimizer top-level walk: `https://github.com/tfoxy/graphene-django-optimizer`.

strawberry-graphql-django field result resolver: `https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/fields/field.py`.

strawberry-graphql-django optimizer extension: `https://strawberry.rocks/docs/django/guide/optimizer` and the source under `strawberry_django/optimizer.py`.

The visibility-leak / `Prefetch` downgrade discussion that motivated bundling the optimizer with `spec-django_types.md` originally: issue #572 and PR #583 on `strawberry-graphql/strawberry-django`.

## Implementation checklist
- [x] O1 — Custom resolvers for relation fields
- [x] O2 — Selection-tree walker
- [x] O3 — Root-gated resolve hook
- [ ] O4 — See `docs/spec-optimizer_nested_prefetch_chains.md`
- [x] O5 — `only()` projection
- [x] O6 — `get_queryset` + `Prefetch` downgrade
