# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- Consolidated completed design-doc content into the user-facing docs, added code-first onboarding, and archived the completed spec files.

## [0.0.4] - 2026-05-07
### Added
- `finalize_django_types()` public API for resolving pending Django relations after all `DjangoType` modules are imported and before Strawberry schema construction.
- Definition-order-independent relation finalization for FK, reverse FK, OneToOne, reverse OneToOne, and M2M fields, including cyclic graphs declared in either order.
- `DjangoTypeDefinition` as the canonical per-type metadata object for selected fields, optimizer metadata, lifecycle state, and future subsystem slots.
- Fail-loud unresolved-target diagnostics that name each source model, field, and missing target model during finalization.
- Relation-field override contract: consumer annotations are preserved, and consumer-assigned Strawberry fields/resolvers are not clobbered by generated relation resolvers.
- Registry lifecycle coverage for idempotent finalization, post-finalization registration errors, phase-1 retry behavior, and class-mutation residue after `registry.clear()`.

### Changed
- `DjangoType` subclass creation now collects metadata and pending relations only; Strawberry type finalization and relation resolver attachment happen in `finalize_django_types()`.
- Optimizer metadata now lives on `DjangoTypeDefinition`, with `_optimizer_field_map`, `_optimizer_hints`, and `_is_default_get_queryset` mirrored on classes for compatibility.
- `registry.clear()` now resets definitions, pending relations, and finalized state in addition to type/model/enum maps.
- `DjangoType` now raises `ConfigurationError` at class-creation time when a selected relation field has no concrete target model, such as `GenericForeignKey`; previously this surfaced later as an `AttributeError` during `finalize_django_types()`. Use `Meta.exclude` or an explicit annotation/resolver for these fields.

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
