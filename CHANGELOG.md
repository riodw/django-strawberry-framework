# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.2] - 2026-04-30
### Added
- `DjangoType` Meta-class-driven adapter generating Strawberry types from Django models, with scalar / relation / choice converters, `TypeRegistry`, and a `get_queryset` hook.
- `DjangoOptimizerExtension` Strawberry schema extension for N+1 prevention (per-resolver depth-1; the top-level selection-tree walker is tracked in `docs/spec-optimizer.md`).
- Cardinality-aware relation resolvers attached at `DjangoType.__init_subclass__` so reverse FK / M2M fields return iterables instead of Django `RelatedManager`s.

Pre-alpha; the public API is unstable until `0.1.0`. See `docs/README.md` for the architecture and roadmap.
