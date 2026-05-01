# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **B1 — AST-cached plans.** Plan cache keyed on `(document_hash, directive_vars, target_model)` with directive-variable extraction (including named fragment resolution), bounded-size dict, and public `cache_info()` method.
- **B5 — Plan introspection.** `OptimizationPlan` stashed on `info.context.dst_optimizer_plan` after every optimization pass.
- **B7 — Precomputed field metadata.** `FieldMeta` frozen dataclass built at `DjangoType` class-creation time; walker reads cached map instead of `_meta.get_fields()` per request.
- **B3 — N+1 detection.** `DjangoOptimizerExtension(strictness="warn"|"raise")` with alias-safe field-name comparison and lazy-load check.
- **B4 — `Meta.optimizer_hints`.** `OptimizerHint` typed wrapper (`SKIP`, `.select_related()`, `.prefetch_related()`, `.prefetch(obj)`) with build-time validation.
- **O5 — `only()` projection.** Optimizer plans now collect selected scalar columns, include FK columns for `select_related` traversals, and apply `QuerySet.only()` before relation optimization.
- `OptimizerHint` re-exported from top-level `__init__.py`.
- `registry.iter_types()` public iterator.
- Resolver signature changed to `(root, info: Info)` for B3 N+1 detection.

## [0.0.2] - 2026-04-30
### Added
- `DjangoType` Meta-class-driven adapter generating Strawberry types from Django models, with scalar / relation / choice converters, `TypeRegistry`, and a `get_queryset` hook.
- `DjangoOptimizerExtension` Strawberry schema extension for N+1 prevention (per-resolver depth-1; the top-level selection-tree walker is tracked in `docs/spec-optimizer.md`).
- Cardinality-aware relation resolvers attached at `DjangoType.__init_subclass__` so reverse FK / M2M fields return iterables instead of Django `RelatedManager`s.

Pre-alpha; the public API is unstable until `0.1.0`. See `docs/README.md` for the architecture and roadmap.
