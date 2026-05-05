# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.3] - 2026-05-05

### Added
- **Layer 2 optimizer milestone.** `DjangoOptimizerExtension` is now effective end-to-end with the root-gated O3 optimizer hook, O4 nested prefetch chains and same-query recursion, O5 `only()` projection, and O6 custom `get_queryset` downgrade to `Prefetch`.
- **B1 — AST-cached plans.** Plan cache keyed on selected operation AST, directive variables, model, and root runtime path, with fragment-spread directive coverage, multi-operation document correctness, bounded-size storage, and public `cache_info()`.
- **B2 — FK-id elision.** Forward foreign-key relations selected only for `id` can be satisfied from the local `*_id` column when safe.
- **B3 — N+1 detection.** `DjangoOptimizerExtension(strictness="warn"|"raise")` with alias-safe field-name comparison and lazy-load checks.
- **B4 — `Meta.optimizer_hints`.** `OptimizerHint` typed wrapper (`SKIP`, `.select_related()`, `.prefetch_related()`, `.prefetch(obj)`) with build-time validation.
- **B5 — Plan introspection.** `OptimizationPlan` stashed on `info.context.dst_optimizer_plan` after every optimization pass.
- **B6 — Schema-build-time audit.** Optimizer validation walks registered Django types and reports invalid hints before request execution.
- **B7 — Precomputed field metadata.** `FieldMeta` frozen dataclass built at `DjangoType` class-creation time; walker reads cached maps instead of `_meta.get_fields()` per request.
- **B8 — Queryset diffing.** Consumer-applied `select_related`, `prefetch_related`, and `Prefetch` lookups are reconciled so optimizer plans do not duplicate them.
- `OptimizerHint` re-exported from top-level `__init__.py`.
- `registry.iter_types()` public iterator.
- Resolver signature changed to `(root, info: Info)` for B3 N+1 detection.

## [0.0.2] - 2026-04-30
### Added
- `DjangoType` Meta-class-driven adapter generating Strawberry types from Django models, with scalar / relation / choice converters, `TypeRegistry`, and a `get_queryset` hook.
- `DjangoOptimizerExtension` Strawberry schema extension for N+1 prevention (per-resolver depth-1; the top-level selection-tree walker is tracked in `docs/spec-optimizer.md`).
- Cardinality-aware relation resolvers attached at `DjangoType.__init_subclass__` so reverse FK / M2M fields return iterables instead of Django `RelatedManager`s.

Pre-alpha; the public API is unstable until `0.1.0`. See `docs/README.md` for the architecture and roadmap.
