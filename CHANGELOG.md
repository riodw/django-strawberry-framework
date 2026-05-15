# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.5] - 2026-05-15
### Added
- Relay Node interface support: `Meta.interfaces` accepted for any Strawberry interface (Relay `Node` or `@strawberry.interface`-decorated classes).
- Default `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes` classmethods injected on every `DjangoType` whose `Meta.interfaces` declares `relay.Node`; consumer-declared overrides are preserved via Strawberry's `__func__` identity test (matches `strawberry-django`).
- Automatic synthesized `id: int!` suppression when `relay.Node` is in `Meta.interfaces` (including consumer subclasses of `relay.Node`); the Relay-supplied `id: GlobalID!` from the interface is used instead. The Django primary key remains selected as a connector column for the optimizer.
- `is_type_of` injection is unconditional for every `DjangoType` (Relay-declared or not); consumer-declared `is_type_of` is preserved.
- Models whose primary key is a Django 5.2+ `CompositePrimaryKey` raise `ConfigurationError` at finalization; declare an explicit `id: relay.NodeID[...]` annotation or remove `relay.Node` from `Meta.interfaces` to remediate.
- Both sync and async paths for `_resolve_node_default` / `_resolve_nodes_default`; `_resolve_id_attr_default` and `_resolve_id_default` are sync.
- `is_many_side_relation_kind` and `unwrap_graphql_type` utility helpers consolidated in `django_strawberry_framework.utils` so optimizer, walker, and type-conversion call sites share a single source of truth for relation cardinality and graphql-core type unwrapping.

### Changed
- `Meta.interfaces` promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`.
- Optimizer schema audit (`check_schema`) now descends into GraphQL union member types so `DjangoType`s reachable only through a union participate in the missing-target audit.
- `get_context_value` tolerates non-dict mapping contexts and `AttributeError` from `__getitem__` so `strawberry-graphql-django`'s attribute-bridging context and `__slots__`-backed mappings read correctly.

### Fixed
- `_check_n1` now receives the real `relation_kind` of the field being resolved (including `reverse_many_to_one`) instead of a hardcoded `"many"` / `"forward"`, so reverse-FK resolvers exercise the many-side N+1 check path consistently.
- `_ensure_connector_only_fields` now injects the forward FK column for reverse one-to-one prefetches so Django can bind each child row back to its parent without a lazy load.
- Optimizer walker now projects a `NodeID`-targeted relation via the FK `attname` (e.g. `user_id`) instead of the relation name (`user`), so `.only(...)` does not drag the related row back through a deferred load.
- GraphQL-reserved enum member names (`true` / `false` / `null`) and introspection-prefixed (`__`) sanitizations from Django `choices` values now produce schema-valid Strawberry enums.
- Relay `_resolve_nodes_default` / `_resolve_nodes_async` materialize the input `node_ids` once so one-shot iterables (generators, `map`, etc.) survive both the IN-filter and the order-preserving key pass.
- Walker `_prefetch_hint_for_path` now rebases type-relative nested lookups onto the full path while preserving queryset and `to_attr`, and rejects mismatched lookups that do not target the hinted relation.

### Removed
- Removed the dead `PendingRelation` hashability probe; `TypeRegistry.discard_pending()` removes pending records by identity rather than via a hash set.

## [0.0.4] - 2026-05-08
### Added
- `finalize_django_types()` public API and `DjangoTypeDefinition` metadata layer for definition-order-independent relation finalization before Strawberry schema construction.
- Relation finalization support for FK, reverse FK, OneToOne, reverse OneToOne, and M2M fields, including cyclic graphs and target types declared in either order.
- Fail-loud relation diagnostics that name unresolved targets, unsupported relation fields, and duplicate registry/choice-enum collisions instead of surfacing later as vague runtime errors.
- Relation-field override support that preserves consumer annotations, `strawberry.field` resolvers, and generated resolvers where appropriate.
- A restructured `examples/fakeshop` project with a real API-testing app, migrations, schema examples, and query tests for validating the package against Django behavior.

### Changed
- `DjangoType` subclass creation now collects model metadata and pending relations only; Strawberry decoration and generated relation resolver attachment happen during finalization.
- Optimizer metadata now lives on `DjangoTypeDefinition`, with compatibility mirrors retained on generated classes.
- Optimizer internals were hardened around context propagation, cache-key generation, field-map resolution, relation-kind classification, prefetch typing, lazy-load detection, and aliased selections with divergent arguments.
- Settings reload now mutates the existing singleton instance in place, and `registry.clear()` resets definitions, pending relations, finalized state, and class-mutation residue.
- User-facing docs were consolidated into code-first onboarding, a current feature catalog, architecture notes, testing guidance, and review/inspection documentation.
- Tests were expanded across settings, registry lifecycle, choice conversion, relation resolution, definition-order cycles, generic foreign keys, optimizer hints, plans, walker behavior, and the fakeshop example.

### Fixed
- `OptimizerHint` now rejects conflicting flag combinations, and `Meta.optimizer_hints` keys must refer to selected fields.
- Choice enum conversion now raises `ConfigurationError` for name collisions that would otherwise silently lose values.
- Unsupported relation fields such as `GenericForeignKey` now raise `ConfigurationError` during annotation building with guidance to exclude or override the field.
- Relation cache checks now handle single-valued and synthetic Django relation objects more reliably.

### Removed
- Removed the unused `TypeRegistry.lazy_ref` placeholder in favor of the package-owned pending-relation registry.

## [0.0.3] - 2026-05-05
### Added
- `DjangoOptimizerExtension` is now effective end-to-end for root `QuerySet` resolvers: selection-tree planning, `select_related`, nested `Prefetch` chains, same-query recursion, `only()` projection, and `get_queryset`-aware `Prefetch` downgrade.
- Optimizer performance and safety features: AST plan cache, FK-id elision, strictness modes, plan introspection, schema audit, precomputed field metadata, and queryset diffing against consumer-applied `select_related`, `prefetch_related`, and `Prefetch` lookups.
- `Meta.optimizer_hints` with the `OptimizerHint` typed wrapper (`SKIP`, `.select_related()`, `.prefetch_related()`, `.prefetch(obj)`) and build-time validation.
- `OptimizerHint` re-exported from top-level `__init__.py`.
- `registry.iter_types()` public iterator.
- Resolver signature changed to `(root, info: Info)` for B3 N+1 detection.

## [0.0.2] - 2026-04-30
### Added
- `DjangoType` Meta-class-driven adapter generating Strawberry types from Django models, with scalar / relation / choice converters, `TypeRegistry`, and a `get_queryset` hook.
- Early `DjangoOptimizerExtension` Strawberry schema extension for depth-1 N+1 prevention.
- Cardinality-aware relation resolvers attached at `DjangoType.__init_subclass__` so reverse FK / M2M fields return iterables instead of Django `RelatedManager`s.

Pre-alpha; the public API is unstable until `0.1.0`. See `docs/README.md` for the architecture and roadmap.
