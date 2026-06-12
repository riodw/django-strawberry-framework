# Package source change attribution

Generated from `/private/tmp/package-history.json` produced by `scripts/list_package_python_changes_by_commit.py`.

This is conservative: broad maintenance commits are not forced into a spec card merely because they occurred near a spec build.


## Cards with no confident core-package attribution

No standalone `django_strawberry_framework/**/*.py` implementation commits were confidently attributable to these current KANBAN cards from the package manifest alone: `DONE-007-0.0.4`, `DONE-008-0.0.4`, `DONE-009-0.0.4`, `DONE-011-0.0.4`, `DONE-012-0.0.4`, `DONE-014-0.0.4`, `DONE-023-0.0.7`, `DONE-026-0.0.7`, and `WIP-ALPHA-033-0.0.9`. Some are design/doc/test/example cards; some may be bundled into mixed commits already attributed to neighboring implementation cards.

## Adjacent hardening not counted as card implementation

The post-`DONE-032` connection/optimizer hardening pass (`7b40d644` through `08da9664`) is deliberately left unattributed to `WIP-ALPHA-033-0.0.9`: `docs/spec-033-connection_optimizer-0_0_9.md` says those commits made the card premise stale and that spec-033 does not re-ship that root-connection planning work. A downstream reviewer may still want to cite them as prerequisite context for spec-033.

## DONE-001-0.0.1 DjangoType core foundation

Commits: 2428cd8f, 084b4643, 77b8fe7f
Unique package files: 7

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/conf.py`
- `django_strawberry_framework/converters.py`
- `django_strawberry_framework/exceptions.py`
- `django_strawberry_framework/optimizer.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/types.py`

Commit detail:
- `2428cd8f` 2026-04-29 - chore: initial project skeleton (v0.0.1)
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/conf.py`
- `084b4643` 2026-04-29 - ready to start first spec;
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/converters.py`
  - `django_strawberry_framework/exceptions.py`
  - `django_strawberry_framework/optimizer.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types.py`
- `77b8fe7f` 2026-04-30 - DjangoTypes done; Prep for spec-optimizer.md;
  - `django_strawberry_framework/converters.py`
  - `django_strawberry_framework/optimizer.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types.py`

## DONE-002-0.0.2 Optimizer O1-O6 foundation

Commits: 70c7bff2, 2893ccb8, bd7e7011, 32b7e033, dae186a1, f18c1fed
Unique package files: 12

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/optimizer/__init__.py`
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/types/__init__.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/utils/__init__.py`
- `django_strawberry_framework/utils/strings.py`
- `django_strawberry_framework/utils/typing.py`

Commit detail:
- `70c7bff2` 2026-04-30 - Version 0.0.2 finished; Refactor to fix best structure;
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/converters.py`
- `2893ccb8` 2026-04-30 - Version 0.0.2 finished; Refactor to fix best structure;
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/optimizer/__init__.py`
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/types/__init__.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/converters.py`
  - `django_strawberry_framework/types/resolvers.py`
  - `django_strawberry_framework/utils/__init__.py`
  - `django_strawberry_framework/utils/strings.py`
  - `django_strawberry_framework/utils/typing.py`
- `bd7e7011` 2026-04-30 - Refactor optimizer scaffolding and introduce selection-tree walker
  - `django_strawberry_framework/optimizer/__init__.py`
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/plans.py`
  - `django_strawberry_framework/optimizer/walker.py`
- `32b7e033` 2026-04-30 - Refactor DjangoOptimizerExtension to implement O3 optimizations, including root-field gating and type-tracing for querysets. Update tests to cover new functionality and ensure async parity with aresolvers.
  - `django_strawberry_framework/optimizer/extension.py`
- `dae186a1` 2026-04-30 - Update README and documentation for optimizer improvements; enhance DjangoOptimizerExtension with caching and relation path checks
  - `django_strawberry_framework/optimizer/__init__.py`
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/resolvers.py`
- `f18c1fed` 2026-04-30 - Refactor optimizer extension and walker for improved caching and relation handling
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/resolvers.py`

## DONE-003-0.0.2 Optimizer O4 nested prefetch chains

Commits: 8e17fd6e, 4b7d7703, 6d6cc621
Unique package files: 6

Files:
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/hints.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/types/resolvers.py`

Commit detail:
- `8e17fd6e` 2026-05-01 - Enhance optimizer with nested prefetch chain support
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/hints.py`
  - `django_strawberry_framework/optimizer/plans.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/resolvers.py`
- `4b7d7703` 2026-05-01 - feat: enhance optimizer with nested prefetch and resolver key support
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/field_meta.py`
  - `django_strawberry_framework/optimizer/hints.py`
  - `django_strawberry_framework/optimizer/plans.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/resolvers.py`
- `6d6cc621` 2026-05-01 - Refactor optimizer for nested prefetch chains and FK-id elision
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/plans.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/resolvers.py`

## DONE-004-0.0.3 Optimizer beyond slices B1-B8

Commits: 394418d2, 06ec75f0, bfb14107, 440b5b32, c4a17bc7, 5d92272f, 411b2187, ee469cbb, b4b9221e
Unique package files: 9

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/hints.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/resolvers.py`

Commit detail:
- `394418d2` 2026-04-30 - feat(optimizer): implement field metadata caching and optimizer hints
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/field_meta.py`
  - `django_strawberry_framework/optimizer/hints.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/resolvers.py`
- `06ec75f0` 2026-05-01 - B6.05 Done;
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/plans.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/resolvers.py`
- `bfb14107` 2026-05-01 - feat(optimizer): implement Prefetch downgrade for custom get_queryset in relation planning
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/plans.py`
  - `django_strawberry_framework/optimizer/walker.py`
- `440b5b32` 2026-05-01 - feat(optimizer): implement forward-FK-id elision for id-only selections
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/field_meta.py`
  - `django_strawberry_framework/optimizer/plans.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/resolvers.py`
- `c4a17bc7` 2026-05-01 - feat(optimizer): enhance caching mechanism for root fields and update plan structure
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/plans.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/resolvers.py`
- `5d92272f` 2026-05-04 - feat(optimizer): implement queryset diffing to avoid duplicating consumer-applied select_related and prefetch_related lookups
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/plans.py`
- `411b2187` 2026-05-04 - feat(optimizer): enhance plan reconciliation to support consumer prefetch and select_related optimizations
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/plans.py`
- `ee469cbb` 2026-05-04 - feat(optimizer): implement absorption logic for consumer prefetch entries in optimizer
  - `django_strawberry_framework/optimizer/plans.py`
- `b4b9221e` 2026-05-05 - feat(optimizer): enhance directive handling in _walk_directives and optimize plan-cache key generation
  - `django_strawberry_framework/optimizer/extension.py`

## DONE-005-0.0.3 DjangoType contract and boundary

Commits: f5d03652, b5c12f41
Unique package files: 2
Note: Low confidence: commit subjects are generic 0.0.3 spec-prep, but changed only DjangoType/converter contract files before optimizer-beyond work.

Files:
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`

Commit detail:
- `f5d03652` 2026-04-30 - Start specs for 0.0.3;
  - `django_strawberry_framework/types/base.py`
- `b5c12f41` 2026-04-30 - Specs finished;
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/converters.py`

## DONE-006-0.0.3 Documentation/status positioning for shipped Layer 2

Commits: 2c5bfaae, 83c25963
Unique package files: 8
Note: Low confidence: package changes are release/public-surface/doc-consolidation spillover, not feature implementation.

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/hints.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`

Commit detail:
- `2c5bfaae` 2026-05-05 - Release 0.0.3
  - `django_strawberry_framework/__init__.py`
- `83c25963` 2026-05-05 - Finish consolidation of specs and doc files;
  - `django_strawberry_framework/optimizer/field_meta.py`
  - `django_strawberry_framework/optimizer/hints.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/converters.py`
  - `django_strawberry_framework/types/resolvers.py`

## DONE-010-0.0.4 foundation slice

Commits: 0be61b6c, 27d62919, 78d23895, 118f71a1, 1d9ca597
Unique package files: 12

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/types/__init__.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/definition.py`
- `django_strawberry_framework/types/finalizer.py`
- `django_strawberry_framework/types/relations.py`
- `django_strawberry_framework/types/resolvers.py`

Commit detail:
- `0be61b6c` 2026-05-06 - feat: prepare for spec-foundation 0.0.4 implementation; add TODOs for new features and refactoring
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/field_meta.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/__init__.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/converters.py`
  - `django_strawberry_framework/types/resolvers.py`
- `27d62919` 2026-05-07 - Start spec-foundation : Slice 0-6
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/__init__.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/converters.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
  - `django_strawberry_framework/types/relations.py`
  - `django_strawberry_framework/types/resolvers.py`
- `78d23895` 2026-05-07 - IMplement feedback - enhance relation handling and finalization process in DjangoType
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/converters.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
  - `django_strawberry_framework/types/relations.py`
  - `django_strawberry_framework/types/resolvers.py`
- `118f71a1` 2026-05-07 - Complete spec-foundation.md - Slices 7-12 (v0.0.4)
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/optimizer/field_meta.py`
  - `django_strawberry_framework/registry.py`
- `1d9ca597` 2026-05-07 - Finished spec-foundation.md
  - `django_strawberry_framework/types/relations.py`

## DONE-013-0.0.4 Real M2M coverage / relation hardening

Commits: 02f7190e, d592ac3a
Unique package files: 3
Note: Medium confidence: relation lazy-load and unsupported-relation fixes match real relation/M2M hardening, but subjects do not name the current card.

Files:
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/resolvers.py`

Commit detail:
- `02f7190e` 2026-05-08 - fix: Enhance lazy loading check for Django relations to support single-valued and synthetic objects
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/resolvers.py`
- `d592ac3a` 2026-05-08 - fix: Improve error handling for unsupported relations in annotation building
  - `django_strawberry_framework/types/base.py`

## DONE-015-0.0.5 Relay interfaces and Node foundation

Commits: 32dea521, b14232fa, bdc9ca1a, 4cfe14be, e6907fa8, e836d72e, 01efc102, 9e70ae39, f56f5f21, b686ae4f, 77122cd5, 13778027, c733ef2a, 9f0d99f8, 2ec8d04a, d3829b25, 9d01054b, 9eaeb8ad, 1d581f2d, 6db241c6, 7df1c382, d9e40091
Unique package files: 20

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/conf.py`
- `django_strawberry_framework/optimizer/_context.py`
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/hints.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/types/__init__.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/definition.py`
- `django_strawberry_framework/types/finalizer.py`
- `django_strawberry_framework/types/relations.py`
- `django_strawberry_framework/types/relay.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/utils/__init__.py`
- `django_strawberry_framework/utils/relations.py`
- `django_strawberry_framework/utils/typing.py`

Commit detail:
- `32dea521` 2026-05-11 - Prep for 0.0.5 Code; relay interfaces refinements
  - `django_strawberry_framework/types/base.py`
- `b14232fa` 2026-05-13 - slice 1 done;
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
- `bdc9ca1a` 2026-05-13 - Slice 2 done;
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/relay.py`
- `4cfe14be` 2026-05-13 - slice 3 done;
  - `django_strawberry_framework/types/base.py`
- `e6907fa8` 2026-05-13 - Finish slice 4;
  - `django_strawberry_framework/types/finalizer.py`
  - `django_strawberry_framework/types/relay.py`
  - `django_strawberry_framework/types/resolvers.py`
- `e836d72e` 2026-05-13 - Finish docs/spec-relay_interfaces.md;
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/types/base.py`
- `01efc102` 2026-05-13 - Enhance Relay interface handling and resolve_id signatures
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/finalizer.py`
  - `django_strawberry_framework/types/relay.py`
- `9e70ae39` 2026-05-13 - More fixes;
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/__init__.py`
  - `django_strawberry_framework/types/relay.py`
- `f56f5f21` 2026-05-13 - Final feedback;
  - `django_strawberry_framework/optimizer/field_meta.py`
- `b686ae4f` 2026-05-13 - Start processing 0.0.5 REVIEW;
  - `django_strawberry_framework/conf.py`
  - `django_strawberry_framework/optimizer/_context.py`
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/field_meta.py`
  - `django_strawberry_framework/registry.py`
- `77122cd5` 2026-05-13 - Fix Relay node handling for custom primary keys and improve composite PK error handling
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/relay.py`
- `13778027` 2026-05-14 - Continue code review;
  - `django_strawberry_framework/optimizer/hints.py`
  - `django_strawberry_framework/optimizer/plans.py`
  - `django_strawberry_framework/optimizer/walker.py`
- `c733ef2a` 2026-05-14 - Force FieldMeta.nullable=False for many-side cardinalities
  - `django_strawberry_framework/optimizer/field_meta.py`
  - `django_strawberry_framework/types/base.py`
- `9f0d99f8` 2026-05-14 - Project Relay id_attr in walker for custom and relation primary keys
  - `django_strawberry_framework/optimizer/walker.py`
- `2ec8d04a` 2026-05-14 - Suppress synthesized id for ``relay.Node`` subclasses + rename ``pk_name``
  - `django_strawberry_framework/types/base.py`
- `d3829b25` 2026-05-14 - Sanitize GraphQL-reserved enum member names + harden Meta validation tests
  - `django_strawberry_framework/types/converters.py`
- `9d01054b` 2026-05-15 - Drop obsolete PendingRelation hashability probe
  - `django_strawberry_framework/types/relations.py`
- `9eaeb8ad` 2026-05-15 - Materialize Relay node_ids once for filter and ordering
  - `django_strawberry_framework/types/relay.py`
- `1d581f2d` 2026-05-15 - Harden optimizer schema audit and context helpers
  - `django_strawberry_framework/optimizer/_context.py`
  - `django_strawberry_framework/optimizer/extension.py`
- `6db241c6` 2026-05-15 - Extract is_many_side_relation_kind and unwrap_graphql_type helpers
  - `django_strawberry_framework/utils/__init__.py`
  - `django_strawberry_framework/utils/relations.py`
  - `django_strawberry_framework/utils/typing.py`
- `7df1c382` 2026-05-15 - Optimizer: migrate to shared helpers; fix reverse O2O connector and NodeID attname
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/walker.py`
- `d9e40091` 2026-05-15 - Types: use is_many_side_relation_kind; propagate real kind through _check_n1
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/converters.py`
  - `django_strawberry_framework/types/resolvers.py`

## DONE-016-0.0.6 FieldMeta consolidation

Commits: de35a622
Unique package files: 6

Files:
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`

Commit detail:
- `de35a622` 2026-05-15 - refactor(types,optimizer): consolidate metadata onto DjangoTypeDefinition
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/field_meta.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/converters.py`
  - `django_strawberry_framework/types/resolvers.py`

## DONE-017-0.0.6 Deferred scalar conversions

Commits: df13b644
Unique package files: 3

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/scalars.py`
- `django_strawberry_framework/types/converters.py`

Commit detail:
- `df13b644` 2026-05-17 - Finish docs/spec-013-deferred_scalars-0_0_6.md;
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/scalars.py`
  - `django_strawberry_framework/types/converters.py`

## DONE-018-0.0.6 Meta.primary

Commits: 307f358c, 8cec18a3, 13d8dac5, b70c0360, 1fb42b04
Unique package files: 6

Files:
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/definition.py`
- `django_strawberry_framework/types/finalizer.py`

Commit detail:
- `307f358c` 2026-05-18 - Ready to start spec-014
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
- `8cec18a3` 2026-05-18 - Finish docs/spec-014-meta_primary-0_0_6.md
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
- `13d8dac5` 2026-05-18 - Apply feedback;
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/finalizer.py`
- `b70c0360` 2026-05-19 - Add public helpers for managing primary types in TypeRegistry
  - `django_strawberry_framework/registry.py`
- `1fb42b04` 2026-05-19 - Refactor TypeRegistry public helper for unregistering types
  - `django_strawberry_framework/registry.py`

## DONE-019-0.0.6 Consumer override semantics

Commits: 630c4c3e, 42d57e45, a357c68c
Unique package files: 2
Note: Conservative: excludes the broad review/bug-hunt commits immediately after it unless they are later judged card-owned.

Files:
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/definition.py`

Commit detail:
- `630c4c3e` 2026-05-19 - Add TODO comments, reprocess spec pass 7
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
- `42d57e45` 2026-05-19 - last spec pass, ready to BUILD
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
- `a357c68c` 2026-05-19 - Finish docs/spec-015-consumer_overrides_scalar-0_0_6.md
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`

## DONE-020-0.0.7 DjangoListField

Commits: 6adbe630, 7e8632f6, f2aba83c, cfacd48b, b972cd84
Unique package files: 3

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/apps.py`
- `django_strawberry_framework/list_field.py`

Commit detail:
- `6adbe630` 2026-05-20 - Ready for docs/spec-016-list_field-0_0_7.md
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/list_field.py`
- `7e8632f6` 2026-05-20 - Start docs/spec-016-list_field-0_0_7.md
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/list_field.py`
- `f2aba83c` 2026-05-21 - feat: add _is_async_callable function to check for async callables in DjangoListField
  - `django_strawberry_framework/list_field.py`
- `cfacd48b` 2026-05-21 - docs: fixes for High findings and clarify async-callable detection
  - `django_strawberry_framework/list_field.py`
- `b972cd84` 2026-05-21 - Final revision pass
  - `django_strawberry_framework/apps.py`

## DONE-021-0.0.7 apps.py and Django AppConfig

Commits: dfa035b4
Unique package files: 1

Files:
- `django_strawberry_framework/apps.py`

Commit detail:
- `dfa035b4` 2026-05-21 - Done docs/spec-017-apps-0_0_7.md;
  - `django_strawberry_framework/apps.py`

## DONE-022-0.0.7 export_schema management command

Commits: d35385c2, d780726f, f6238256, 9e11eb30
Unique package files: 4

Files:
- `django_strawberry_framework/management/__init__.py`
- `django_strawberry_framework/management/commands/__init__.py`
- `django_strawberry_framework/management/commands/export_schema.py`
- `django_strawberry_framework/scalars.py`

Commit detail:
- `d35385c2` 2026-05-22 - Add TODO comments
  - `django_strawberry_framework/management/__init__.py`
  - `django_strawberry_framework/management/commands/__init__.py`
  - `django_strawberry_framework/management/commands/export_schema.py`
- `d780726f` 2026-05-22 - Finish docs/builder/build-018-export_schema-0_0_7.md
  - `django_strawberry_framework/management/__init__.py`
  - `django_strawberry_framework/management/commands/__init__.py`
  - `django_strawberry_framework/management/commands/export_schema.py`
  - `django_strawberry_framework/scalars.py`
- `f6238256` 2026-05-22 - Improve error handling when writing schema to path in export_schema command
  - `django_strawberry_framework/management/commands/export_schema.py`
- `9e11eb30` 2026-05-22 - Refactor export_schema command argument handling and improve user feedback
  - `django_strawberry_framework/management/commands/export_schema.py`

## DONE-024-0.0.7 Django Trac #37064 hardening + safe_wrap_connection_method

Commits: 300e2811, 893465a5, 61973f8d, 7014125a, 744fd28d
Unique package files: 4

Files:
- `django_strawberry_framework/_django_patches.py`
- `django_strawberry_framework/apps.py`
- `django_strawberry_framework/test/__init__.py`
- `django_strawberry_framework/test/_wrap.py`

Commit detail:
- `300e2811` 2026-05-23 - Ship Django Trac #37064 fix as package-level AppConfig.ready() patch
  - `django_strawberry_framework/_django_patches.py`
  - `django_strawberry_framework/apps.py`
- `893465a5` 2026-05-23 - Document django-debug-toolbar precedent and defense-in-depth framing in _django_patches
  - `django_strawberry_framework/_django_patches.py`
- `61973f8d` 2026-05-23 - Ship safe_wrap_connection_method consumer helper as wrap-time mirror of Trac #37064 patch
  - `django_strawberry_framework/_django_patches.py`
  - `django_strawberry_framework/test/__init__.py`
  - `django_strawberry_framework/test/_wrap.py`
- `7014125a` 2026-05-26 - Harden Trac #37064 patch: SimpleTestCase retarget + defensive imports + callable guard
  - `django_strawberry_framework/_django_patches.py`
  - `django_strawberry_framework/apps.py`
  - `django_strawberry_framework/test/_wrap.py`
- `744fd28d` 2026-05-26 - Tighten Trac #37064 patch: log-once sentinel + accurate non-callable example
  - `django_strawberry_framework/_django_patches.py`
  - `django_strawberry_framework/test/_wrap.py`

## DONE-025-0.0.7 scalar_map helper

Commits: b1a6d01f
Unique package files: 2

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/scalars.py`

Commit detail:
- `b1a6d01f` 2026-05-27 - Finish docs/spec-020-scalar_map_helper-0_0_7.md;
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/scalars.py`

## DONE-027-0.0.8 Filtering subsystem

Commits: 7e6a7fc4, 1694bd2e, 74608b0b, 44d407ca, 28a8d6c2, 222c5341, cbf550ac, 97ea13e6, fd390356, a6c26222, 0190597c, 8021a00e, 3279625b, 8af1347d, 19471729, 9b826d93, bae0e24b, 8584cf87, fdeb4fbd, 73d71e51, 5b2788f8, ebe593c5, 3171382f, 6b95ede9
Unique package files: 19
Note: Includes filter-specific review and polish commits; excludes global style/tooling-only commits in the same window.

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/conf.py`
- `django_strawberry_framework/exceptions.py`
- `django_strawberry_framework/filters/__init__.py`
- `django_strawberry_framework/filters/base.py`
- `django_strawberry_framework/filters/factories.py`
- `django_strawberry_framework/filters/inputs.py`
- `django_strawberry_framework/filters/sets.py`
- `django_strawberry_framework/list_field.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/scalars.py`
- `django_strawberry_framework/sets_mixins.py`
- `django_strawberry_framework/types/__init__.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/definition.py`
- `django_strawberry_framework/types/finalizer.py`
- `django_strawberry_framework/types/relay.py`

Commit detail:
- `7e6a7fc4` 2026-05-28 - Add TODO comments
  - `django_strawberry_framework/filters/__init__.py`
  - `django_strawberry_framework/filters/base.py`
  - `django_strawberry_framework/filters/factories.py`
  - `django_strawberry_framework/filters/inputs.py`
  - `django_strawberry_framework/filters/sets.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
  - `django_strawberry_framework/types/relay.py`
- `1694bd2e` 2026-05-30 - Finish build-021-filters-0_0_8
  - `django_strawberry_framework/filters/__init__.py`
  - `django_strawberry_framework/filters/base.py`
  - `django_strawberry_framework/filters/factories.py`
  - `django_strawberry_framework/filters/inputs.py`
  - `django_strawberry_framework/filters/sets.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
- `74608b0b` 2026-05-30 - Start DRY out
  - `django_strawberry_framework/filters/sets.py`
  - `django_strawberry_framework/types/relay.py`
- `44d407ca` 2026-05-30 - Refactor filterset input normalization and error handling
  - `django_strawberry_framework/filters/sets.py`
  - `django_strawberry_framework/types/finalizer.py`
- `28a8d6c2` 2026-05-30 - Fix lookup_token grouping bug when field name is in LOOKUP_NAME_MAP
  - `django_strawberry_framework/filters/inputs.py`
- `222c5341` 2026-05-30 - Address round-2 review findings in filters and types
  - `django_strawberry_framework/filters/base.py`
  - `django_strawberry_framework/filters/factories.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
  - `django_strawberry_framework/types/relay.py`
- `cbf550ac` 2026-05-30 - Address round-3 review findings: UNSET in operator bags, SyncMisuseError loop, related-target cache
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/filters/inputs.py`
  - `django_strawberry_framework/filters/sets.py`
  - `django_strawberry_framework/types/__init__.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/relay.py`
- `97ea13e6` 2026-05-30 - Address round-4 review findings: permission dedup, depth guard, cache-key pins
  - `django_strawberry_framework/filters/sets.py`
  - `django_strawberry_framework/types/relay.py`
- `fd390356` 2026-05-30 - Address round-5 review findings: cross-branch dedup, overridable depth cap
  - `django_strawberry_framework/filters/sets.py`
- `a6c26222` 2026-05-30 - Address docs/feedback.md review: filters correctness fixes + tests
  - `django_strawberry_framework/conf.py`
  - `django_strawberry_framework/filters/factories.py`
  - `django_strawberry_framework/filters/inputs.py`
  - `django_strawberry_framework/filters/sets.py`
- `0190597c` 2026-05-30 - Address docs/feedback.md review: filters correctness fixes + per-field __all__
  - `django_strawberry_framework/filters/base.py`
  - `django_strawberry_framework/filters/inputs.py`
  - `django_strawberry_framework/filters/sets.py`
  - `django_strawberry_framework/types/finalizer.py`
- `8021a00e` 2026-05-30 - filters: memoize _lookups_for_field + extract shared set-mixins
  - `django_strawberry_framework/filters/base.py`
  - `django_strawberry_framework/filters/inputs.py`
  - `django_strawberry_framework/filters/sets.py`
  - `django_strawberry_framework/sets_mixins.py`
- `3279625b` 2026-05-30 - filters: add HIDE_FLAT_FILTERS to toggle flat relation-traversal input fields
  - `django_strawberry_framework/filters/inputs.py`
- `8af1347d` 2026-05-30 - filters: unwrap enum members structurally via isinstance(enum.Enum)
  - `django_strawberry_framework/filters/inputs.py`
- `19471729` 2026-05-30 - filters: correct generated filter input types (spec-021 H1/H2)
  - `django_strawberry_framework/filters/inputs.py`
  - `django_strawberry_framework/filters/sets.py`
  - `django_strawberry_framework/types/converters.py`
- `9b826d93` 2026-05-30 - filters: re-apply RelatedFilter constraints inside logical branches
  - `django_strawberry_framework/filters/sets.py`
- `bae0e24b` 2026-05-30 - types: reject a filterset bound to an unrelated owner model at finalize
  - `django_strawberry_framework/types/finalizer.py`
- `8584cf87` 2026-05-30 - docs: document review-flagged contracts and known edge cases
  - `django_strawberry_framework/filters/__init__.py`
  - `django_strawberry_framework/filters/base.py`
  - `django_strawberry_framework/filters/inputs.py`
  - `django_strawberry_framework/filters/sets.py`
  - `django_strawberry_framework/optimizer/walker.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/finalizer.py`
- `fdeb4fbd` 2026-05-30 - filters: enforce no-subclass on FilterArgumentsFactory, split namespace cleanup
  - `django_strawberry_framework/filters/factories.py`
  - `django_strawberry_framework/filters/inputs.py`
  - `django_strawberry_framework/filters/sets.py`
- `73d71e51` 2026-05-30 - types: surface the underlying error when finalize re-wraps an expansion failure
  - `django_strawberry_framework/types/finalizer.py`
- `5b2788f8` 2026-06-01 - framework: filter polish, RelatedFilter lookups removal, type_name_for guard
  - `django_strawberry_framework/exceptions.py`
  - `django_strawberry_framework/filters/base.py`
  - `django_strawberry_framework/filters/factories.py`
  - `django_strawberry_framework/filters/inputs.py`
  - `django_strawberry_framework/list_field.py`
  - `django_strawberry_framework/scalars.py`
  - `django_strawberry_framework/sets_mixins.py`
- `ebe593c5` 2026-06-01 - framework: filter cycle polish — guard hoist, partial-range, apply_async safety
  - `django_strawberry_framework/filters/__init__.py`
  - `django_strawberry_framework/filters/base.py`
  - `django_strawberry_framework/filters/factories.py`
  - `django_strawberry_framework/filters/inputs.py`
  - `django_strawberry_framework/filters/sets.py`
- `3171382f` 2026-06-01 - framework: drop final Slice-2 tense-rot in filters/factories.py docstring
  - `django_strawberry_framework/filters/factories.py`
- `6b95ede9` 2026-06-02 - filters: DRY landings — _iter_input_items / _iter_visibility_steps; pin third logic-depth site
  - `django_strawberry_framework/filters/sets.py`

## DONE-028-0.0.8 Ordering subsystem

Commits: f3a07775, b8fbd74d, 3fe4c92a, 01e8ce23
Unique package files: 10

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/orders/__init__.py`
- `django_strawberry_framework/orders/base.py`
- `django_strawberry_framework/orders/factories.py`
- `django_strawberry_framework/orders/inputs.py`
- `django_strawberry_framework/orders/sets.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/definition.py`
- `django_strawberry_framework/types/finalizer.py`

Commit detail:
- `f3a07775` 2026-06-01 - docs: stage spec-028 orders-0.0.8 subsystem prep
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/orders/__init__.py`
  - `django_strawberry_framework/orders/base.py`
  - `django_strawberry_framework/orders/factories.py`
  - `django_strawberry_framework/orders/inputs.py`
  - `django_strawberry_framework/orders/sets.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
- `b8fbd74d` 2026-06-01 - orders: ship Slices 1-3 of spec-028 — foundation, factories, finalizer binding
  - `django_strawberry_framework/orders/__init__.py`
  - `django_strawberry_framework/orders/base.py`
  - `django_strawberry_framework/orders/factories.py`
  - `django_strawberry_framework/orders/inputs.py`
  - `django_strawberry_framework/orders/sets.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
- `3fe4c92a` 2026-06-02 - orders: pass-2 B1 coverage closure — 19 tests; spec/builder corrected; feedback rewritten
  - `django_strawberry_framework/orders/base.py`
  - `django_strawberry_framework/orders/sets.py`
  - `django_strawberry_framework/types/base.py`
- `01e8ce23` 2026-06-03 - orders: gate-green round-2 — card-owned + filter-async + glossary seed idempotency; gate now GREEN
  - `django_strawberry_framework/orders/__init__.py`

## DONE-029-0.0.9 DjangoType consumer-DX cleanup

Commits: 138b1c1d, 2d1f2963, 513b2690, 47a3c75f, 2bb41372
Unique package files: 4

Files:
- `django_strawberry_framework/management/commands/inspect_django_type.py`
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`

Commit detail:
- `138b1c1d` 2026-06-05 - Add TODO comments;
  - `django_strawberry_framework/management/commands/inspect_django_type.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/converters.py`
- `2d1f2963` 2026-06-05 - Finish spec-029-consumer_dx_cleanup-0_0_9.md
  - `django_strawberry_framework/management/commands/inspect_django_type.py`
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/converters.py`
- `513b2690` 2026-06-05 - Fix spec-029 review feedback: kanban fixtures, coverage gap, inspect polish
  - `django_strawberry_framework/management/commands/inspect_django_type.py`
- `47a3c75f` 2026-06-05 - Enhance inspect_django_type command: add support for consumer-authored fields and improve GraphQL type resolution
  - `django_strawberry_framework/management/commands/inspect_django_type.py`
- `2bb41372` 2026-06-06 - Fix inspect_django_type command: handle consumer-authored fields and improve error reporting for unresolved forward references
  - `django_strawberry_framework/management/commands/inspect_django_type.py`

## DONE-030-0.0.9 DjangoConnectionField

Commits: 89798607, 9704e25a, ab17f96a
Unique package files: 9

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/connection.py`
- `django_strawberry_framework/list_field.py`
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/orders/inputs.py`
- `django_strawberry_framework/orders/sets.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/definition.py`

Commit detail:
- `89798607` 2026-06-08 - Finish spec-030-connection_field-0_0_9.md
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/connection.py`
  - `django_strawberry_framework/list_field.py`
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
- `9704e25a` 2026-06-09 - Refactor connection validation to use precomputed relay shape check and improve documentation clarity
  - `django_strawberry_framework/connection.py`
  - `django_strawberry_framework/types/base.py`
- `ab17f96a` 2026-06-09 - Fix cursor stability, to-many ordering multiplication, and totalCount scope (spec-030 review round)
  - `django_strawberry_framework/connection.py`
  - `django_strawberry_framework/list_field.py`
  - `django_strawberry_framework/optimizer/extension.py`
  - `django_strawberry_framework/orders/inputs.py`
  - `django_strawberry_framework/orders/sets.py`
  - `django_strawberry_framework/registry.py`

## DONE-031-0.0.9 Django-model-based GlobalID encoding

Commits: a6063fff, 9b0c1050, a305ee46, 162019ff, bf138a57, 356e6709, 9ca3d6de
Unique package files: 9
Note: Includes spec-031 review commits; broad lint/ASCII sweeps in the same day are excluded.

Files:
- `django_strawberry_framework/filters/base.py`
- `django_strawberry_framework/filters/inputs.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/definition.py`
- `django_strawberry_framework/types/finalizer.py`
- `django_strawberry_framework/types/relay.py`
- `django_strawberry_framework/utils/typing.py`

Commit detail:
- `a6063fff` 2026-06-09 - Add TODO comments
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
  - `django_strawberry_framework/types/relay.py`
- `9b0c1050` 2026-06-10 - Finish build-031-globalid_encoding-0_0_9.md
  - `django_strawberry_framework/filters/base.py`
  - `django_strawberry_framework/filters/inputs.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
  - `django_strawberry_framework/types/relay.py`
- `a305ee46` 2026-06-10 - Refine GlobalID encoder validation to ensure synchronous callables only
  - `django_strawberry_framework/types/base.py`
- `162019ff` 2026-06-10 - Add validation for async GlobalID encoders and enhance tests for callable checks
  - `django_strawberry_framework/types/base.py`
- `bf138a57` 2026-06-10 - Implement depth limits for GraphQL path and type unwrapping to prevent infinite loops
  - `django_strawberry_framework/optimizer/plans.py`
  - `django_strawberry_framework/utils/typing.py`
- `356e6709` 2026-06-10 - Refactor feedback.md: comprehensive review of GlobalID encoding implementation, addressing spec-031 compliance and various identified issues
  - `django_strawberry_framework/filters/base.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
  - `django_strawberry_framework/types/relay.py`
- `9ca3d6de` 2026-06-10 - Refactor GlobalID encoding documentation and implementation: update feedback.md with verification results, revise spec-031 to reflect changes in override detection and routing audit, and enhance clarity in filter docstrings by replacing raw line references with unique pinpoints.
  - `django_strawberry_framework/filters/base.py`
  - `django_strawberry_framework/registry.py`

## DONE-032-0.0.9 Full Relay story

Commits: 3b8173dc, 70b919f9, 8a860e9a, 6148d3f1, f8ca5a08
Unique package files: 9
Note: Excludes the later root-connection optimizer hardening pass; that pass is referenced by spec-033 but was not WIP-033 implementation.

Files:
- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/connection.py`
- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/relay.py`
- `django_strawberry_framework/testing/__init__.py`
- `django_strawberry_framework/testing/relay.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/definition.py`
- `django_strawberry_framework/types/finalizer.py`

Commit detail:
- `3b8173dc` 2026-06-10 - Add TODO comments for spec-032-full_relay-0_0_9.md
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/connection.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/relay.py`
  - `django_strawberry_framework/testing/__init__.py`
  - `django_strawberry_framework/testing/relay.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
- `70b919f9` 2026-06-11 - Enhance test documentation for error handling in GraphQL queries
  - `django_strawberry_framework/relay.py`
- `8a860e9a` 2026-06-11 - Finish docs/spec-032-full_relay-0_0_9.md
  - `django_strawberry_framework/__init__.py`
  - `django_strawberry_framework/connection.py`
  - `django_strawberry_framework/registry.py`
  - `django_strawberry_framework/relay.py`
  - `django_strawberry_framework/testing/__init__.py`
  - `django_strawberry_framework/testing/relay.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/definition.py`
  - `django_strawberry_framework/types/finalizer.py`
- `6148d3f1` 2026-06-11 - fix: resolve spec-032 implementation edge cases and finalizer recovery bugs
  - `django_strawberry_framework/relay.py`
  - `django_strawberry_framework/testing/relay.py`
  - `django_strawberry_framework/types/base.py`
  - `django_strawberry_framework/types/finalizer.py`
- `f8ca5a08` 2026-06-11 - fix: complete spec-032 full relay implementation and resolve edge cases
  - `django_strawberry_framework/connection.py`
  - `django_strawberry_framework/relay.py`

## Not attributed to a spec card yet

These touched `django_strawberry_framework/**/*.py` but look like maintenance, release, global style, docstring, review-infrastructure, prototype, or ambiguous inter-card work.

- `ac50dd32` 2026-04-30 - Ready for improvements over strawberry-graphql-django optimization query;
  Files: `django_strawberry_framework/optimizer/extension.py`
- `3fac089d` 2026-05-06 - Refactor logging setup and improve module documentation for optimizer and types
  Files: `django_strawberry_framework/__init__.py`, `django_strawberry_framework/optimizer/__init__.py`, `django_strawberry_framework/types/__init__.py`
- `f8f8b8a0` 2026-05-06 - Fix reload_settings to mutate existing Settings instance and update documentation
  Files: `django_strawberry_framework/conf.py`
- `55614d67` 2026-05-06 - Enhance TypeRegistry with error handling for duplicate registrations and update documentation for thread-safety and usage guidelines
  Files: `django_strawberry_framework/registry.py`
- `3bf8a877` 2026-05-06 - Refactor optimizer extension: enhance context handling and improve cache key mechanism
  Files: `django_strawberry_framework/optimizer/extension.py`
- `47cecb7e` 2026-05-06 - Refactor FieldMeta: tighten related_model typing and enhance from_django_field docstring
  Files: `django_strawberry_framework/optimizer/field_meta.py`
- `4d446687` 2026-05-06 - Add validation to OptimizerHint: reject conflicting flag combinations in __post_init__ and tighten prefetch_obj typing
  Files: `django_strawberry_framework/optimizer/hints.py`
- `603e1c60` 2026-05-06 - Enhance OptimizationPlan: tighten prefetch_related typing and document cache invariants
  Files: `django_strawberry_framework/optimizer/plans.py`
- `f785840a` 2026-05-06 - Refactor walker: centralize field-map resolution, enhance hint handling, and add tests for default dispatch behavior
  Files: `django_strawberry_framework/optimizer/walker.py`
- `7a71ad04` 2026-05-06 - Add validation for optimizer_hints to ensure keys are in selected fields and update tests
  Files: `django_strawberry_framework/types/base.py`
- `1f306793` 2026-05-06 - Add collision detection in convert_choices_to_enum to prevent silent data loss and raise ConfigurationError
  Files: `django_strawberry_framework/types/converters.py`
- `1f6878fa` 2026-05-06 - Refactor logger import in resolvers.py to use framework-wide singleton and remove duplicate string literal
  Files: `django_strawberry_framework/types/resolvers.py`
- `45970e64` 2026-05-06 - Refactor settings handling to mutate singleton instance in place and update related tests; add context helpers for optimizer-resolver interaction; enhance error handling in choice enum conversion; improve logging for aliased selections with divergent arguments.
  Files: `django_strawberry_framework/conf.py`, `django_strawberry_framework/optimizer/_context.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/plans.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/utils/typing.py`
- `46688189` 2026-05-06 - DRY OUT CODE - Add relation kind utility and refactor context usage in optimizer and resolvers
  Files: `django_strawberry_framework/optimizer/_context.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/utils/relations.py`
- `3982978d` 2026-05-08 - feat: Add content-versioned Node types with response-extensions gossip
  Files: `django_strawberry_framework/__init__.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/types/__init__.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/resolvers.py`
- `250b04f2` 2026-05-11 - fix(conf): refresh settings singleton in place on Django changes
  Files: `django_strawberry_framework/conf.py`
- `9296ccf3` 2026-05-11 - fix(api): pin package logger and public API surface
  Files: `django_strawberry_framework/__init__.py`, `django_strawberry_framework/optimizer/__init__.py`
- `194f0992` 2026-05-11 - fix(types): harden type collection and registry guarantees
  Files: `django_strawberry_framework/registry.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/relations.py`, `django_strawberry_framework/types/resolvers.py`
- `89fdfdf9` 2026-05-11 - refactor(utils): name forward and reverse relation shapes
  Files: `django_strawberry_framework/utils/__init__.py`, `django_strawberry_framework/utils/relations.py`
- `c7447e23` 2026-05-11 - fix(optimizer): finalize plans and centralize metadata validation
  Files: `django_strawberry_framework/optimizer/_context.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/field_meta.py`, `django_strawberry_framework/optimizer/hints.py`, `django_strawberry_framework/optimizer/plans.py`, `django_strawberry_framework/optimizer/walker.py`
- `2701fe92` 2026-05-14 - Enhance error handling in stash_on_context for frozen dict subclasses and improve test coverage
  Files: `django_strawberry_framework/optimizer/_context.py`
- `d0da5f1f` 2026-05-15 - Align converter docstrings with MRO walk and GraphQL-safe sanitization
  Files: `django_strawberry_framework/types/converters.py`
- `9a0d9ec7` 2026-05-19 - Simplify id hint check in _id_annotation_is_relay_node_id function
  Files: `django_strawberry_framework/types/base.py`
- `f83bb71b` 2026-05-20 - Run REVIEW.md;
  Files: `django_strawberry_framework/conf.py`, `django_strawberry_framework/optimizer/_context.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/field_meta.py`, `django_strawberry_framework/optimizer/plans.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/registry.py`, `django_strawberry_framework/types/__init__.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/relations.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/utils/__init__.py`, `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/utils/typing.py`
- `0411e242` 2026-05-20 - refactor: centralize model lookup with _model_for function
  Files: `django_strawberry_framework/types/relay.py`
- `21212a19` 2026-05-20 - End Bug Hunt
  Files: `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/registry.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/utils/typing.py`
- `d6cac863` 2026-05-20 - refactor: improve error messages in OptimizerHint and validate meta fields
  Files: `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/converters.py`
- `2bcd7f96` 2026-05-21 - refactor: simplify _id_annotation_is_relay_node_id function for clarity and consistency - this fixes a coverage difference on Python3.10
  Files: `django_strawberry_framework/types/base.py`
- `5f0ffa5b` 2026-05-23 - Bump version to 0.0.7 and update changelog, README, GLOSSARY, and tests to reflect new version
  Files: `django_strawberry_framework/__init__.py`
- `f274b2a4` 2026-05-26 - Apply REVIEW 0.0.7 source/test corrections across 11 modules
  Files: `django_strawberry_framework/conf.py`, `django_strawberry_framework/list_field.py`, `django_strawberry_framework/management/commands/export_schema.py`, `django_strawberry_framework/optimizer/__init__.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/registry.py`, `django_strawberry_framework/scalars.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/resolvers.py`
- `3ed0bb84` 2026-05-26 - Convert path:NN line refs to symbol-qualified path::Symbol form
  Files: `django_strawberry_framework/list_field.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/resolvers.py`
- `df547235` 2026-05-27 - Replace line-NN references repo-wide with symbol-qualified paths
  Files: `django_strawberry_framework/list_field.py`, `django_strawberry_framework/optimizer/__init__.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/resolvers.py`
- `13543c24` 2026-05-30 - style: apply trailing-comma layout and line-length 100 across the repo
  Files: `django_strawberry_framework/conf.py`, `django_strawberry_framework/filters/base.py`, `django_strawberry_framework/filters/factories.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/field_meta.py`, `django_strawberry_framework/optimizer/hints.py`, `django_strawberry_framework/optimizer/plans.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/registry.py`, `django_strawberry_framework/types/__init__.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/utils/relations.py`
- `f9064a01` 2026-05-30 - tooling: correct trailing-comma gate detection
  Files: `django_strawberry_framework/exceptions.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/types/__init__.py`, `django_strawberry_framework/types/relay.py`
- `78b69d76` 2026-06-01 - docs: archive prior specs to docs/SPECS/ and renumber per Step 8 pass
  Files: `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/list_field.py`, `django_strawberry_framework/types/relay.py`
- `4f2b4c6b` 2026-06-01 - refactor: rename test subpackage to testing
  Files: `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/testing/__init__.py`, `django_strawberry_framework/testing/_wrap.py`
- `171a9bc1` 2026-06-01 - release: bump to 0.0.8, retire joint-cut convention
  Files: `django_strawberry_framework/__init__.py`
- `1043d5cd` 2026-06-01 - optimizer: review-cycle fixes — _apply_hint mutation safety, FK-id elision ordering, plan-cache origin discrimination
  Files: `django_strawberry_framework/optimizer/_context.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/field_meta.py`, `django_strawberry_framework/optimizer/hints.py`, `django_strawberry_framework/optimizer/plans.py`, `django_strawberry_framework/optimizer/walker.py`
- `a9cf0c77` 2026-06-01 - types: review-cycle polish — converters docstring tightening; capture rev-types artifacts
  Files: `django_strawberry_framework/types/converters.py`
- `6c453fa9` 2026-06-01 - management + testing: review-cycle polish and capture rev artifacts
  Files: `django_strawberry_framework/management/commands/export_schema.py`, `django_strawberry_framework/testing/_wrap.py`
- `92ca9aa4` 2026-06-02 - types: review-cycle fixes — _from_field_shape DRY landing, SyncMisuseError, citation rebinds
  Files: `django_strawberry_framework/optimizer/field_meta.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/relations.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/resolvers.py`
- `4b4f8d4f` 2026-06-02 - utils: review-cycle polish; capture rev-utils artifacts
  Files: `django_strawberry_framework/utils/relations.py`
- `d0811aba` 2026-06-02 - types: DRY landing — collapse registry.primary_for-or-get chain to registry.get
  Files: `django_strawberry_framework/types/definition.py`
- `11a4df6b` 2026-06-06 - Fix line-length configuration in Ruff settings to align with project standards
  Files: `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/management/commands/inspect_django_type.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/orders/inputs.py`, `django_strawberry_framework/orders/sets.py`
- `0bb2f0e7` 2026-06-10 - Enable warnings-as-errors and add ruff B/ASYNC lint groups
  Files: `django_strawberry_framework/list_field.py`, `django_strawberry_framework/types/base.py`
- `cd9c2ab5` 2026-06-10 - Expand ruff lint coverage (RUF/PERF/ARG/...) and fix what it surfaced
  Files: `django_strawberry_framework/connection.py`, `django_strawberry_framework/filters/base.py`, `django_strawberry_framework/filters/factories.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/list_field.py`, `django_strawberry_framework/optimizer/hints.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/orders/__init__.py`, `django_strawberry_framework/orders/factories.py`, `django_strawberry_framework/orders/inputs.py`, `django_strawberry_framework/scalars.py`, `django_strawberry_framework/sets_mixins.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/relay.py`
- `e6389922` 2026-06-10 - Make all .py source ASCII (emoji excepted) and enforce it
  Files: `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/apps.py`, `django_strawberry_framework/conf.py`, `django_strawberry_framework/connection.py`, `django_strawberry_framework/exceptions.py`, `django_strawberry_framework/filters/base.py`, `django_strawberry_framework/filters/factories.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/list_field.py`, `django_strawberry_framework/management/commands/export_schema.py`, `django_strawberry_framework/management/commands/inspect_django_type.py`, `django_strawberry_framework/optimizer/__init__.py`, `django_strawberry_framework/optimizer/_context.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/field_meta.py`, `django_strawberry_framework/optimizer/hints.py`, `django_strawberry_framework/optimizer/plans.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/orders/base.py`, `django_strawberry_framework/orders/inputs.py`, `django_strawberry_framework/orders/sets.py`, `django_strawberry_framework/registry.py`, `django_strawberry_framework/scalars.py`, `django_strawberry_framework/testing/__init__.py`, `django_strawberry_framework/testing/_wrap.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/utils/__init__.py`, `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/utils/typing.py`
- `7b40d644` 2026-06-11 - feat: implement connection-aware selection extraction and optimize planning for edges.node queries
  Files: `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/walker.py`
- `e0cb6fb1` 2026-06-11 - refactor: replace dict with OrderedDict for plan cache to enable LRU eviction
  Files: `django_strawberry_framework/optimizer/extension.py`
- `57711032` 2026-06-11 - feat: enhance OptimizationPlan with finalized metadata for improved context publishing
  Files: `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/plans.py`
- `53745e31` 2026-06-11 - test: add tests for _IndexedList usage in OptimizationPlan default fields
  Files: `django_strawberry_framework/optimizer/plans.py`
- `4ca3fc29` 2026-06-11 - feat: enhance relation target resolution by utilizing definition metadata in the optimizer
  Files: `django_strawberry_framework/optimizer/walker.py`
- `1637c8e1` 2026-06-11 - feat: add target_pk_name and fk_id_elision_eligible to FieldMeta for enhanced relation handling
  Files: `django_strawberry_framework/optimizer/field_meta.py`, `django_strawberry_framework/optimizer/walker.py`
- `04db843e` 2026-06-11 - feat: implement memoization for custom id resolver checks in DjangoTypeDefinition
  Files: `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/types/definition.py`
- `a095b89f` 2026-06-11 - Refactor optimizer for improved handling of primary keys and connection fields
  Files: `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/field_meta.py`, `django_strawberry_framework/optimizer/plans.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/types/definition.py`
- `54b3fb05` 2026-06-11 - feat: enhance error handling for unregistered RelatedFilter targets and improve related branch visibility checks
  Files: `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/types/finalizer.py`
- `30a0ba39` 2026-06-12 - feat: implement instance accessor for reverse relations and enhance connection type cache eviction
  Files: `django_strawberry_framework/registry.py`, `django_strawberry_framework/relay.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/utils/relations.py`
- `08da9664` 2026-06-12 - feat: enhance relation handling by introducing accessor_name for reverse relations and optimizing prefetch lookups
  Files: `django_strawberry_framework/optimizer/field_meta.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/utils/relations.py`
- `5aa7bb27` 2026-06-12 - Add file package descriptions;
  Files: `django_strawberry_framework/__init__.py`, `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/apps.py`, `django_strawberry_framework/conf.py`, `django_strawberry_framework/connection.py`, `django_strawberry_framework/filters/__init__.py`, `django_strawberry_framework/filters/base.py`, `django_strawberry_framework/filters/factories.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/management/__init__.py`, `django_strawberry_framework/management/commands/__init__.py`, `django_strawberry_framework/optimizer/__init__.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/orders/__init__.py`, `django_strawberry_framework/orders/base.py`, `django_strawberry_framework/orders/factories.py`, `django_strawberry_framework/orders/sets.py`, `django_strawberry_framework/scalars.py`, `django_strawberry_framework/testing/__init__.py`, `django_strawberry_framework/testing/_wrap.py`, `django_strawberry_framework/types/__init__.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/utils/__init__.py`, `django_strawberry_framework/utils/strings.py`

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
