# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- Consolidated completed design-doc content into the user-facing docs, added code-first onboarding, and archived the completed spec files.

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
