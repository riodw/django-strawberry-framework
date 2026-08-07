# Spec: Optimizer & Reverse-Relation Resolution

## Purpose
This parent spec records the optimizer architecture and the shipped foundation slices for relation resolution, root-gated query planning, nested prefetch chains, [`only()`][glossary-only-projection] projection, and `get_queryset`-aware `Prefetch` downgrade.

It records that behavior at a high level only: the detailed O4 design and implementation record belongs to `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`; keep detailed O4 rationale there rather than duplicating it here. The same rule governs the rest of the optimizer family — `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`, `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`, and `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` each own the surface they added. Where one of them changed how one of the slices below behaves, this spec states the behavior that holds and names the spec that owns it; it does not restate that spec's rules.

Deliberation for this spec lives in its companion [rationale file][spec-002-rationale]: why the optimizer became its own document, why the O4 record was split out, why generated relation resolvers survive the optimizer, the questions this spec left open, and every claim it once made and no longer makes. Read the spec for what holds; read that file for why it holds.

## Problem statement
Two concrete problems in relation resolution define this subsystem:

- Reverse relations exposed by [`DjangoType`][glossary-djangotype] need generated resolvers because Strawberry's default resolver returns a Django `RelatedManager`, which is not directly iterable.
- Query planning needs to run from the operation root so the optimizer can inspect the GraphQL selection tree before relation resolvers evaluate model attributes.

These problems share one seam: how the framework gets from Strawberry field resolution to the underlying Django model relation.

Why they were lifted out of `spec-001-django_types-0_0_1.md` is in the [rationale file][spec-002-rationale].

## Architecture decision
The chosen architecture is a root-gated selection-tree walk plus generated relation resolvers.

The optimizer's schema-middleware entry point is Strawberry's `SchemaExtension.resolve` hook, gated by `info.path.prev is None`. A root resolver's return value is normalized first (`django_strawberry_framework/utils/querysets.py::normalize_query_source`): a Django `Manager` is coerced to a `QuerySet`, and every other non-`QuerySet` value passes through unchanged, as do all non-root resolvers. A queryset the consumer has already evaluated also passes through unchanged, because the plan is applied to a clone and cloning an evaluated queryset would silently re-run the consumer's SQL (`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`). What survives that gate is planned once, then the resulting `OptimizationPlan` is applied to that queryset.

`resolve` is not the only caller of that plan-and-apply tail. `DjangoConnectionField` invokes it directly through `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.apply_to`, because Strawberry's connection slicing hides the pre-slice queryset from schema middleware. One plan-application implementation, two entry points; the connection path is `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`'s.

Generated relation resolvers are required independently of the optimizer: they must return correct results when the optimizer is disabled and when a relation is not already loaded. They also host the B2/B3 runtime sentinels used by later optimizer behavior. Why the optimizer does not subsume them is in the [rationale file][spec-002-rationale].

## Shipped slices
### O1 — Custom relation resolvers
One generated resolver is attached per relation field during type finalization: `django_strawberry_framework/types/finalizer.py::finalize_django_types` calls `django_strawberry_framework/types/resolvers.py::_attach_relation_resolvers` in its Phase 2 window, before Strawberry freezes the class. A relation the consumer assigned its own resolver to is skipped, so a consumer-declared resolver always wins over the generated one; the skip set is `DjangoTypeDefinition.consumer_assigned_relation_fields`.

Forward FK / OneToOne resolvers return the related attribute, except where B2 FK-id elision substitutes a stub carrying only the target's identifier. Reverse FK / M2M resolvers return a materialized list so Strawberry receives an iterable, row-bounded by the request resource policy (`docs/SPECS/spec-047-resource_policy-0_0_14.md`). Reverse OneToOne resolvers collapse missing related rows to `None`.

### O2 — Selection-tree walker
`plan_optimizations(selected_fields, model, info=None, *, runtime_prefixes=None, source_type=None)` in `django_strawberry_framework/optimizer/walker.py` walks Strawberry selections, maps Django relation fields through the registered type's `DjangoTypeDefinition.field_map` (resolved by `django_strawberry_framework/optimizer/walker.py::_resolve_field_map`), handles fragments/directives/aliases, and produces an `OptimizationPlan`.

### O3 — Root-gated optimizer hook
`DjangoOptimizerExtension.resolve` gates optimization to root resolvers, traces graphql-core return types back to registered `DjangoType` models, calls the walker, stashes the plan and its companion sentinels on the request context under the optimizer's own key vocabulary (`django_strawberry_framework/optimizer/_context.py`), and applies the plan to the root queryset. That stash is both the introspection surface and the hand-off the generated relation resolvers read, so [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] owns its per-execution lifetime.

### O4 — Nested prefetch chains
The walker descends across queryset boundaries and emits nested `Prefetch` objects with optimized child querysets. Same-query recursion handles nested `select_related` paths. Resolver sentinels use branch-sensitive resolver keys derived from GraphQL runtime response paths so aliases and sibling branches do not leak B2/B3 state across each other. A nested Relay connection selection is not a plain `Prefetch`: it is planned and fetched through the connection optimizer's own seam (`docs/SPECS/spec-033-connection_optimizer-0_0_9.md`).

### O5 — `only()` projection
The walker records selected scalar columns and required FK connector columns in `OptimizationPlan.only_fields`. `OptimizationPlan.apply()` calls `QuerySet.only()` when the plan carries projected fields. Column projection is a `QUERY`-operation behavior only: under a mutation or subscription the walker records no projected fields, so the returned queryset keeps `select_related` / `prefetch_related` and carries no column deferral (`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`).

### O6 — `get_queryset` + `Prefetch` downgrade
When a target `DjangoType` has a custom `get_queryset`, the planner avoids `select_related` for that relation and emits a `Prefetch` with the target queryset instead. The planner does not invoke that `get_queryset` itself: the call runs through the package's shared visibility boundary (`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`), which is what hands the planner a framework-owned queryset to compose over (`docs/SPECS/spec-045-visibility_boundary-0_0_14.md`). These plans are marked uncacheable because they may depend on request context.

## Coordination with `spec-001-django_types-0_0_1.md`
`spec-001-django_types-0_0_1.md` Slices 4–6 are superseded by this optimizer spec family. The type-system pieces still belong in `spec-001-django_types-0_0_1.md`; the optimizer consumes them here.

The `_is_default_get_queryset` sentinel and `has_custom_get_queryset` introspection helper remain part of the type-system surface, stamped on the class at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`. O6 consumes that surface when choosing between `select_related` and `Prefetch`.

The `TypeRegistry` model/type reverse lookup remains shared by both halves.

## Visibility status
O1 through O6 have shipped. The optimizer is public via [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], exported from `django_strawberry_framework.__init__`.

## References
graphene-django relation resolver wrap: the three relation converters registered on `graphene_django/converter.py::convert_django_field` - `::convert_onetoone_field_to_djangomodel`, `::convert_field_to_list_or_connection`, and `::convert_field_to_djangomodel`.

graphene-django-optimizer top-level walk: `https://github.com/tfoxy/graphene-django-optimizer`.

strawberry-graphql-django field result resolver: `https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/fields/field.py`.

strawberry-graphql-django optimizer extension: `https://strawberry.rocks/docs/django/guide/optimizer` and the source under `strawberry_django/optimizer.py`.

The visibility-leak / `Prefetch` downgrade discussion: issue #572 and PR #583 on `strawberry-graphql/strawberry-django`.

## Implementation checklist
- [x] O1 — Custom resolvers for relation fields
- [x] O2 — Selection-tree walker
- [x] O3 — Root-gated resolve hook
- [x] O4 — Nested prefetch chains
- [x] O5 — `only()` projection
- [x] O6 — `get_queryset` + `Prefetch` downgrade

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-only-projection]: ../GLOSSARY.md#only-projection

<!-- docs/SPECS/ -->
[spec-002-rationale]: appx/spec-002-optimizer-0_0_2-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
