# django-strawberry-framework Kanban

Last refreshed: 2026-05-15

This board summarizes what is shipped, what has recently landed, and what remains to finish based on the current code, tests, docs, and release-readiness notes. It is intentionally written as a project-management view: each card has a status, priority, scope, and a practical definition of done.

## Card ID format

Every card uses the form `<STATUS>-NNN-X.Y.Z`:

- `<STATUS>` — the column the card lives in: `DONE`, `READY`, `NEXT`, `BACKLOG`, or `BLOCKED`. Updated when the card moves between columns.
- `NNN` — a monotonic, never-reused 3-digit sequence number indicating the order the card entered the board. Stays fixed across column moves and version-tag changes.
- `X.Y.Z` — the package version the card shipped in (Done cards) or is planned to ship in (everything else). `0.0.x` is the placeholder version for cards not yet pinned to a specific patch release (long-tail backlog, ongoing rules, blocked items waiting on their dependency).

For install, local development, testing, and the canonical documentation map, start from [`README.md`](README.md).

## Snapshot

### Shipped foundation

- Layer 1 shared infrastructure is in place: `conf.py`, `exceptions.py`, `registry.py`, `utils/strings.py`, `utils/typing.py`, `py.typed`.
- The package builds directly on `strawberry-graphql` and does not depend on `strawberry-graphql-django`; that dependency boundary is intentional so this package controls its DRF-shaped API surface end-to-end.
- `DjangoType` is usable today for model-backed Strawberry types:
  - Meta validation for `model`, `fields`, `exclude`, `name`, `description`, `optimizer_hints`, and `interfaces`.
  - Deferred Meta keys are rejected loudly: `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`.
  - Scalar conversion, relation conversion, choice-enum generation, generated relation resolvers, and `get_queryset` sentinel detection are implemented.
- `DjangoOptimizerExtension` is usable today:
  - O1 through O6 are implemented: relation resolvers, root-gated planning, nested prefetch chains, `only()` projection, and `get_queryset`-aware `Prefetch` downgrade.
  - B1 through B8 are implemented: AST plan cache, FK-id elision, strictness mode, optimizer hints, context plan stashing, schema audit, precomputed field metadata, and queryset diffing.
  - Recent cache-key review findings are implemented in source: fragment-spread directives are collected and multi-operation documents hash the selected operation AST.
- 0.0.4 foundation slice has shipped (card `DONE-006-0.0.4`):
  - `DjangoTypeDefinition` is the canonical per-type metadata object stashed at `cls.__django_strawberry_definition__`, with forward-reserved slots (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`) ready for Layer 3 to populate.
  - `finalize_django_types()` resolves pending relations, attaches generated relation resolvers, and runs `strawberry.type(cls, ...)` for every collected type. Re-exported from `django_strawberry_framework` and `django_strawberry_framework.types`.
  - Pending-relation registry (`PendingRelation`, `add_pending_relation`, `iter_pending_relations`, `discard_pending`, `is_finalized`, `mark_finalized`, extended `clear`) supports definition-order-independent FK / reverse FK / forward + reverse OneToOne / forward + reverse M2M / multi-cycle graphs.
  - Manual relation override contract (`consumer_annotated_relation_fields` vs `consumer_assigned_relation_fields`): annotation-only overrides keep the generated relation resolver; `strawberry.field(resolver=...)` / `@strawberry.field` overrides suppress it.
  - Fail-loud unresolved-target finalization error names source model, source field, and target model.
  - OneToOne / M2M cardinality coverage now uses the real `library` example app; the old `tests.fixtures.apps.TestsCardinalityConfig` fixture app has been removed.
  - Package version is `0.0.5`.
- Test suite structure has caught up with the package shape:
  - `tests/optimizer/` covers `extension.py`, `walker.py`, `plans.py`, `hints.py`, `field_meta.py`, and `definition_order.py`.
  - `tests/types/` covers `base.py`, `converters.py`, `resolvers.py`, `definition_order.py`, and `definition_order_schema.py`.
  - `tests/test_registry.py` covers idempotency / phase-1 atomicity / phase-2/3 partial-mutation / pending-set cleanup / class-mutation residue.
  - `tests/utils/` covers utility modules.
  - The full suite runs through `uv run pytest`, including package tests, example-project tests, and live `/graphql/` HTTP tests, with 100% package coverage.

### In progress

- No slice is currently active. The `0.0.5` Relay Node slice shipped as `DONE-011-0.0.5`.
- Strategic differentiation roadmap (post-`0.0.5`) captured in [`BETTER.md`](BETTER.md): items neither `graphene-django` nor `strawberry-graphql-django` ship cleanly that should land on the roadmap once parity items are shipped.

### Still not implemented

- Layer 3 public subsystems are still planned only:
  - `filters/`
  - `orders/`
  - `aggregates/`
  - `fieldset.py`
  - `connection.py`
  - `permissions.py`
  - `apps.py`
  - `management/commands/export_schema.py`
  - `utils/queryset.py`
- Layer 3 still needs the original goal-level contract: declarative filtering, ordering, aggregation, and permission rules configured through `Meta`, composable with each other, and introspectable from one type definition.
- `Meta.interfaces` and Relay Node wiring shipped in `0.0.5` (`DONE-011-0.0.5`); the foundation seam (finalizer phase 2.5, before `strawberry.type(cls)`, with the slot already on `DjangoTypeDefinition`) is the insertion point now applied.
- Several DjangoType contract gaps remain:
  - multiple `DjangoType`s per model / `Meta.primary`
  - stable consumer override semantics for **scalar** fields (the foundation slice pinned the contract for relation fields only)
  - stable choice-enum naming override, because the first `DjangoType` to read a choice field currently wins the enum name
  - deferred scalar conversions: `BigIntegerField`, `ArrayField`, `JSONField`, `HStoreField`
- Optimizer follow-up ideas remain outside the shipped B1-B8 surface:
  - model-property / cached-property optimization hints
  - connection-aware planning for Relay-style nested connection selections (new card `BACKLOG-030-0.0.9`)
- Test/example hygiene items surfaced by the foundation slice review have moved into the testing-shift docs and backlog: package-level override tests intentionally pin Strawberry internals while HTTP tests pin the consumer-visible override contract (`BACKLOG-029-0.0.x`).
- The library GraphQL schema is real and wired into the project schema; the product-catalog Layer 3 aspirational schema block remains commented until those subsystems ship.

## Board columns

## Done

### DONE-001-0.0.1 — DjangoType core foundation

Priority: completed foundation

Scope:

- `DjangoType` base class
- Meta validation
- scalar conversion
- relation conversion
- choice enums
- type registry
- relation resolvers
- `get_queryset` hook and `has_custom_get_queryset`

Evidence:

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `tests/types/test_base.py`
- `tests/types/test_converters.py`
- `tests/types/test_resolvers.py`

Notes:

- The public shape is intentionally narrow and explicit.
- Deferred Meta keys are rejected, not silently accepted.
- Definition-order independence is now covered by `DONE-006-0.0.4`.

### DONE-002-0.0.2 — Optimizer O1-O6 foundation

Priority: completed foundation

Scope:

- generated relation resolvers
- selection-tree walker
- root-gated optimizer extension
- nested `Prefetch` chains
- same-query `select_related` recursion
- `only()` projection
- custom `get_queryset` downgrade to `Prefetch`

Evidence:

- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/plans.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_walker.py`
- `tests/optimizer/test_plans.py`

Notes:

- Shipped behavior is consolidated into `docs/FEATURES.md`; source/tests are the truth for optimizer behavior.

### DONE-003-0.0.3 — Optimizer beyond slices B1-B8

Priority: completed optimizer polish/performance layer

Scope:

- B1: plan cache keyed by selected operation AST, directive variables, model, and root runtime path
- B2: forward-FK-id elision
- B3: strictness mode (`off`, `warn`, `raise`)
- B4: `Meta.optimizer_hints` with `OptimizerHint`
- B5: plan introspection via context
- B6: schema-build-time audit
- B7: precomputed optimizer field metadata
- B8: queryset diffing against consumer-applied `select_related`, `prefetch_related`, and `Prefetch`

Evidence:

- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/hints.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/plans.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_hints.py`
- `tests/optimizer/test_field_meta.py`
- `tests/optimizer/test_plans.py`

Notes:

- B8 went beyond the initial simple exact-match diff and now handles subtree-aware prefetch reconciliation.
- Fragment-spread directive and multi-operation cache-key bugs have been fixed in source; the old `alpha-review-feedback.md` entries are now historical.

### DONE-004-0.0.3 — Documentation/status positioning for shipped Layer 2

Priority: completed enough for current alpha

Scope:

- `docs/README.md` gives a quickstart, package positioning, optimizer value, and status.
- `docs/FEATURES.md` describes shipped, planned, deferred, and alpha-constrained capabilities.
- `docs/TREE.md` preserves detailed package/test tree responsibilities.

Evidence:

- `docs/README.md`
- `docs/FEATURES.md`
- `docs/TREE.md`

Notes:

- User-facing docs avoid internal slice shorthand; maintainer docs can still use it where useful.

### DONE-005-0.0.4 — 0.0.4 onboarding docs and spec consolidation

Priority: completed docs cleanup

Scope:

- Root `README.md` is the canonical documentation map and operational entry point.
- `docs/README.md` is code-first: quickstart, three-minute path, optimizer behavior, and status.
- `docs/FEATURES.md` is the capability catalog with value-led optimizer language and comparison table.
- `docs/TREE.md` is the detailed layout/test-tree reference.
- `CHANGELOG.md` is condensed and no longer relies on design-doc pointers for release context.
- Completed design-doc content is folded into durable docs, while remaining specs preserve design history and follow-up work.

Evidence:

- `README.md`
- `docs/README.md`
- `docs/FEATURES.md`
- `docs/TREE.md`
- `CHANGELOG.md`

Notes:

- Future in-flight design docs still use the `docs/spec-<topic>.md` convention, then get folded into durable docs when shipped.

### DONE-006-0.0.4 — 0.0.4 foundation slice (definition-order independence)

Priority: completed Layer 2 foundation

Status: complete.

Scope:

- `DjangoTypeDefinition` dataclass with forward-reserved slots for every Layer 3 subsystem.
- `PendingRelation` and pending-relation registry API (`add_pending_relation`, `iter_pending_relations`, `discard_pending`, `is_finalized`, `mark_finalized`, extended `clear`).
- `finalize_django_types()` three-phase finalizer (resolve pending → attach resolvers → `strawberry.type(cls)`), with phase-1 failure-atomicity and named-source-model error format.
- Manual relation override contract: split `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields` so annotation-only overrides keep the generated resolver while assigned-field / decorator overrides suppress it. Class-attribute shadowing of relation fields raises `ConfigurationError`.
- `PendingRelationAnnotation` sentinel with metaclass `__repr__` that surfaces a useful `TypeError` body if `strawberry.Schema(...)` is constructed before finalization.
- MRO-aware `_detect_custom_get_queryset` so abstract bases without `Meta` still flip the `has_custom_get_queryset` sentinel for downstream concrete subclasses.
- Real cardinality coverage through the `library` example app (`Patron`, `MembershipCard`, `Genre`, `Book`, `Shelf`, `Branch`, `Loan`) instead of test-only fixture models.
- Dedicated test files: `tests/types/test_definition_order.py`, `tests/types/test_definition_order_schema.py`, `tests/optimizer/test_definition_order.py`, plus `tests/test_registry.py` extensions for idempotency / phase-1 atomicity / phase-2/3 partial-mutation contract / pending-set cleanup / class-mutation residue.
- Documentation sweep: `README.md`, `docs/README.md`, `docs/FEATURES.md`, `TODAY.md`, and `CHANGELOG.md`.
- Version bump to `0.0.4` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `uv.lock`.
- Deletion of `TypeRegistry.lazy_ref`; unsupported and unresolved relations now fail with explicit `ConfigurationError` messages at annotation-building or finalization time.

Evidence:

- `django_strawberry_framework/types/definition.py`
- `django_strawberry_framework/types/relations.py`
- `django_strawberry_framework/types/finalizer.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/registry.py`
- `tests/types/test_definition_order.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_definition_order.py`
- `tests/test_registry.py`
- `examples/fakeshop/apps/library/models.py`
- `examples/fakeshop/apps/library/schema.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `CHANGELOG.md`
- `docs/spec-foundation.md`
- `docs/feedback.md`

Notes:

- The forward-reserved slots on `DjangoTypeDefinition` are the architectural seam where the cookbook-shaped Layer 3 subsystems plug in (each subsystem moves its `Meta` key out of `DEFERRED_META_KEYS`, populates the matching slot in collection, and consumes it during finalization or in `DjangoConnectionField`).
- The pending-resolution pattern (record at class creation, resolve at finalization, fail loud on missing target with named source model / field / target) generalizes directly to lazy related class references for `RelatedFilter`, `RelatedOrder`, and `RelatedAggregate`.
- The previous foundation-slice in-progress cards have been retired; this card is their successor in Done.

### DONE-007-0.0.4 — Stale placeholder cleanup

Priority: completed testing/doc cleanup

Status: complete.

Scope:

- Replaced stale M2M and forward-reference skips with definition-order tests.
- Kept the remaining scalar override skip documented as a separate scalar-field concern under `READY-013-0.0.10`.

Evidence:

- `tests/types/test_definition_order.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_definition_order.py`
- `READY-013-0.0.10`

### DONE-008-0.0.4 — 0.0.4 version and release alignment

Priority: completed release alignment

Status: complete.

Scope:

- Package metadata, runtime version, lockfile, tests, and changelog now agree on `0.0.4`.
- The changelog entry is condensed for the pre-alpha release and covers the actual commit range through 2026-05-08.

Evidence:

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`

### DONE-009-0.0.4 — Real M2M coverage

Priority: completed testing-shift hygiene

Status: complete.

Scope:

- Replaced test-only M2M/cardinality fixtures with real managed models in the `library` example app.
- Added package-level and HTTP-level coverage for M2M traversal and optimizer planning.

Evidence:

- `examples/fakeshop/apps/library/models.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `tests/types/test_definition_order.py`
- `tests/optimizer/test_definition_order.py`

### DONE-010-0.0.4 — Move test fixture out of example settings

Priority: completed testing-shift hygiene

Status: complete.

Scope:

- Removed `tests.fixtures.apps.TestsCardinalityConfig` from the example project.
- Removed the old unmanaged cardinality fixture files under `tests/fixtures/`.
- Package tests that need OneToOne / M2M / cardinality coverage now use real models from `examples/fakeshop/apps/library/`.

Evidence:

- `examples/fakeshop/config/settings.py`
- `examples/fakeshop/apps/library/models.py`
- `docs/spec-testing_shift.md`
- `AGENTS.md`
- `docs/TREE.md`

### DONE-011-0.0.5 — 0.0.5 Relay interfaces and Node foundation

Priority: completed Relay Node foundation

Status: complete.

Scope:

- `Meta.interfaces` accepted end-to-end for any Strawberry interface.
- Four Relay node resolver defaults injected when `relay.Node` is declared (canonical order: `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes`); consumer-declared overrides are preserved via Strawberry's `__func__` identity test.
- Automatic synthesized `id: int!` suppression when `relay.Node` is in `Meta.interfaces`; the Relay-supplied `id: GlobalID!` is used instead.
- `is_type_of` injection is unconditional for every `DjangoType` (Relay-declared or not); consumer-declared `is_type_of` is preserved.
- Models whose primary key is a Django 5.2+ `CompositePrimaryKey` raise `ConfigurationError` at finalization; declare an explicit `id: relay.NodeID[...]` annotation or remove `relay.Node` from `Meta.interfaces` to remediate.
- Both sync and async paths for `_resolve_node_default` / `_resolve_nodes_default`; async `get_queryset` hooks are awaited on the async branch and rejected with `ConfigurationError` on the sync branch.
- `Meta.interfaces` promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`.
- Package version bumped to `0.0.5` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock`.

Evidence:

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/relay.py`
- `django_strawberry_framework/types/finalizer.py`
- `tests/types/test_relay_interfaces.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_relay_id_projection.py`
- `tests/test_registry.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `examples/fakeshop/apps/library/schema.py` (`GenreType` declares `Meta.interfaces = (relay.Node,)`)
- `CHANGELOG.md`
- `docs/FEATURES.md`
- `docs/README.md`
- `TODAY.md`
- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`

Notes:

- Borrowed patterns from `strawberry-django` (spec "Borrowing posture", Decision 3). The override discriminator triad stays distinct across the three injection sites: `__dict__` membership for `is_type_of`, tuple membership for id suppression, `__func__` identity for the four `resolve_*` defaults.
- `Meta.interfaces` is the first `0.0.4`-reserved `DjangoTypeDefinition` slot that ships end-to-end through finalizer phase 2.5; subsequent Layer 3 subsystems plug into the same architectural seam.

## In progress

_No slice in progress._

## Ready

### READY-012-0.0.7 — Multiple DjangoTypes per model with `Meta.primary`

Priority: high

Status: ready for a dedicated spec

Current behavior:

- `TypeRegistry.register()` enforces one type per model.
- Registering a second type for the same model raises `ConfigurationError`.

Why it matters:

- DRF-style usage commonly needs public/admin/list/detail variants for the same model.
- Relation conversion and optimizer reverse lookup need an explicit primary type instead of import-order behavior.

Recommended direction:

- Introduce `Meta.primary`.
- Allow multiple types per model only when ambiguity is resolved.
- Exactly one primary type should drive relation conversion and optimizer model/type reverse lookup.

Definition of done:

- New spec, probably `docs/spec-meta_primary.md`.
- Registry stores multiple types per model plus one primary.
- Ambiguity rules are explicit:
  - one type only: allowed without `primary`
  - multiple types, exactly one primary: allowed
  - multiple primaries: error
  - multiple non-primary types with no primary: error
- Relation conversion, schema audit, and optimizer target lookup use the primary type consistently.
- Tests cover all registration and relation-routing cases.

Files likely touched:

- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/optimizer/extension.py`
- `tests/test_registry.py`
- `tests/types/test_base.py`

### READY-013-0.0.10 — Consumer override semantics (scalar fields)

Priority: high

Status: ready for design, not implementation-by-assumption

Note: the foundation slice (`DONE-006-0.0.4`) pins the consumer-override contract for **relation fields only** (`DjangoTypeDefinition.consumer_annotated_relations`, finalizer skip). This card now covers the remaining scalar-field override semantics.

Current behavior:

- `DjangoType.__init_subclass__` merges consumer annotations over synthesized annotations for both scalar and relation fields, but only the relation-field path is part of the stable 0.0.4 contract.
- Strawberry later rewrites class annotation/field metadata for scalars, so the scalar override is not a reliable public contract.
- `test_consumer_annotation_overrides_synthesized` remains skipped.

Why it matters:

- Consumers need a stable way to customize generated scalar fields without abandoning `DjangoType`.
- The package should not claim scalar-annotation overrides survive end-to-end until they actually do.

Open design choices:

- Use Strawberry field customization APIs.
- Add explicit `Meta.field_overrides`.
- Support annotation overrides by controlling the timing of Strawberry finalization (the foundation slice already moves Strawberry finalization into `finalize_django_types()`, which makes this design cheaper to land later).

Definition of done:

- New spec, probably `docs/spec-consumer_overrides.md`.
- Clear supported override forms for scalars:
  - type annotation override
  - resolver override
  - field description/deprecation/default metadata
  - opt-out/removal behavior
- The skipped override test is either unskipped and passes or replaced with the accepted explicit mechanism.
- README and contract docs describe the supported path.

Files likely touched:

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/resolvers.py`
- `tests/types/test_base.py`

### READY-014-0.0.6 — Deferred scalar conversions

Priority: medium

Status: ready when fixture/model coverage is added

Current behavior:

- Implemented scalar coverage is broad but excludes:
  - plain `BigIntegerField` with custom `BigInt`
  - `ArrayField`
  - `JSONField`
  - `HStoreField`

Why it matters:

- These are expected model-field conversions in the original `DjangoType` spec.
- `JSONField` is common in modern Django projects.

Definition of done:

- Add `BigInt` scalar with string serialization and `int` parsing.
- Add `JSONField` mapping to Strawberry JSON.
- Add `HStoreField` where available.
- Add `ArrayField` recursion through `field.base_field`.
- Use synthetic unmanaged test models where fakeshop does not naturally exercise the fields.
- Keep coverage at 100%.

Files likely touched:

- `django_strawberry_framework/types/converters.py`
- `tests/types/test_converters.py`


## Next up

### NEXT-015-0.0.6 — `FieldSet`

Priority: high for Layer 3

Status: needs spec or implementation slice

Why first:

- `FieldSet` is the smallest Layer 3 surface and can define field-selection semantics used by `DjangoConnectionField`.
- It bridges the existing `DjangoType.Meta.fields` behavior and future connection/query APIs.

Foundation-slice seam:

- `DjangoTypeDefinition.fields_class` is the forward-reserved slot the collection phase will populate.
- `Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (see also `BACKLOG-029-0.0.x` for the `DjangoModelField` custom Strawberry field class that field-level permissions will likely require).

Definition of done:

- Add `docs/spec-fieldset.md`.
- Implement `django_strawberry_framework/fieldset.py`.
- Add `tests/test_fieldset.py`.
- Keep the API Meta-class-driven.
- Do not top-level export until the public-surface rules are satisfied.

### NEXT-016-0.0.8 — Filtering subsystem

Priority: high for package positioning

Status: planned

Scope:

- `Filter`
- `FilterSet`
- filterset factory
- GraphQL argument factory
- input type/data adapters
- `Meta.filterset_class` promotion out of `DEFERRED_META_KEYS`

Foundation-slice seam:

- `DjangoTypeDefinition.filterset_class` is the slot the collection phase will populate; the BFS argument factory (analogous to `FilterArgumentsFactory` in the Graphene reference) reads it during finalizer phase 3.
- The pending-relation registry's record-now-resolve-at-finalization pattern reuses cleanly for lazy related-filter class references; a `LazyRelatedClassMixin` equivalent should reuse the same fail-loud error format ("Cannot finalize ... no registered ...") that the model-relation finalizer already produces.
- The relation-override contract pinned in 0.0.4 is what allows filter sidecars to reference relation fields by name without the framework clobbering consumer annotations or resolvers.

Definition of done:

- Add `docs/spec-filters.md`.
- Add `django_strawberry_framework/filters/`.
- Add mirrored `tests/filters/`.
- Promote `Meta.filterset_class` only when filters are applied end-to-end from `DjangoType` / connection fields.
- Keep filter declarations composable with ordering, aggregation, permissions, and optimizer planning.
- Expose enough introspection for one type definition to show what filter surface it supports.
- Use fakeshop flows where practical, but package tests belong under `tests/filters/`.
- Validate Django ORM query generation for N+1 opportunities when filters traverse relations.
- Decide whether the input-type factory's namespace shares the `TypeRegistry` or has its own (interacts with `READY-012-0.0.7` and the `Meta.primary` design).

Dependencies:

- Field selection semantics may affect filter argument generation.
- `utils/queryset.py` may become useful here.

### NEXT-017-0.0.8 — Ordering subsystem

Priority: high after filters

Status: planned

Scope:

- `Order`
- `OrderSet`
- GraphQL argument factory
- `Meta.orderset_class` promotion

Foundation-slice seam:

- `DjangoTypeDefinition.orderset_class` is the populated slot.
- Lazy related-order class references reuse the same record-now-resolve-at-finalization pattern as model relations (`PendingRelation` → analogous `PendingRelatedClass` shape).

Definition of done:

- Add `docs/spec-orders.md`.
- Add `django_strawberry_framework/orders/`.
- Add mirrored `tests/orders/`.
- Promote `Meta.orderset_class` only when ordering is applied end-to-end.
- Support simple fields and relation paths.
- Define interaction with filters and connection field.
- Keep ordering declarations introspectable from the owning type/query surface.

### NEXT-018-0.0.11 — Aggregation subsystem

Priority: medium-high

Status: planned

Scope:

- `Sum`, `Count`, `Avg`, `Min`, `Max`, `GroupBy`
- `AggregateSet`
- GraphQL argument/result factories
- `Meta.aggregate_class` promotion

Foundation-slice seam:

- `DjangoTypeDefinition.aggregate_class` is the populated slot.
- The cookbook reference (`AdvancedAggregateSet.compute` / `acompute`) splits sync and async paths; this lines up with the existing async-resolver support in the optimizer.
- Selection-set-aware aggregate computation will reuse the optimizer plan-cache infrastructure, since the aggregate output type's selected fields drive which annotations are computed.

Definition of done:

- Add `docs/spec-aggregates.md`.
- Add `django_strawberry_framework/aggregates/`.
- Add mirrored `tests/aggregates/`.
- Promote `Meta.aggregate_class` only when aggregation is applied end-to-end.
- Decide result type naming and grouping semantics.
- Validate generated queryset aggregation paths.
- Keep aggregation declarations composable with filters, ordering, and connection field behavior.

### NEXT-019-0.0.9 — `DjangoConnectionField`

Priority: high once filters/orders/fieldset are stable

Status: planned

Scope:

- Relay-style connection field
- composition of filtering, ordering, aggregation, field selection, and optimizer behavior

Foundation-slice seam:

- `finalize_django_types()` is the single architectural entry point that `DjangoConnectionField(DjangoType)` (and `DjangoNodeField`) will auto-trigger as their wrapper. Spec note: `docs/spec-foundation.md:65` already calls this out as a later-phase wrapper around the same finalizer.
- An auto-trigger wrapper must respect the single-threaded-setup window from `docs/spec-foundation.md:63`: either be constrained to schema-construction time, or acquire a real lock around the finalizer.
- Connection-aware optimizer planning is its own follow-up slice (`BACKLOG-030-0.0.9`); the foundation slice did not exercise nested connection prefetch shapes.

Definition of done:

- Add `docs/spec-connection.md`.
- Implement `django_strawberry_framework/connection.py`.
- Add `tests/test_connection.py`.
- Decide whether full Relay support belongs here or a separate `relay/` subpackage.
- Promote `DjangoConnectionField` only when end-to-end schema usage is tested.

Dependencies:

- `FieldSet`
- `FilterSet`
- `OrderSet`
- Relay/interface decisions

### NEXT-020-0.0.9 — Permissions subsystem

Priority: high for the fakeshop example and real usage

Status: planned

Scope:

- `apply_cascade_permissions`
- per-field permission hooks declared via `Meta`
- integration with optimizer `Prefetch` downgrade
- composable permission rules that remain visible from the owning type/query surface

Foundation-slice seam:

- `apply_cascade_permissions(cls, queryset, info)` walks the model graph at call time; `registry.iter_definitions()` (shipped in 0.0.4) is the public iterator that walk uses to find each owner type's `get_queryset`.
- `_attach_relation_resolvers` already accepts a `skip_field_names` set so consumer-authored fields are not clobbered; field-level permission hooks (`fields_class`) extend the same skip-set semantics.

Definition of done:

- Add `docs/spec-permissions.md`.
- Implement `django_strawberry_framework/permissions.py` or a `permissions/` package if the surface grows.
- Add `tests/test_permissions.py`.
- Define the `Meta` surface for per-field permissions and promote keys only when applied end-to-end.
- Use real fakeshop permission users through `services.create_users(1)` in example tests where the system-under-test is the example project.
- Check all permission-related ORM paths for N+1 behavior.

Dependencies:

- `DjangoType.get_queryset`
- optimizer `Prefetch` downgrade
- future `DjangoConnectionField`

## Backlog

### BACKLOG-021-0.0.x — `apps.py` and Django app config

Priority: medium

Status: planned

Definition of done:

- Add `django_strawberry_framework/apps.py`.
- Add `tests/test_apps.py`.
- Do not add settings placeholders unless a shipped feature consumes them.

### BACKLOG-022-0.0.x — Schema export management command

Priority: medium

Status: planned

Definition of done:

- Add `django_strawberry_framework/management/commands/export_schema.py`.
- Add `tests/management/test_export_schema.py`.
- Test through `django.core.management.call_command`, not direct `handle()` calls.

### BACKLOG-023-0.0.x — `utils/queryset.py`

Priority: medium

Status: planned

Potential scope:

- queryset introspection helpers
- prefetch-cache awareness helpers
- reusable utilities currently embedded in optimizer/resolver modules if they become cross-subsystem needs

Definition of done:

- Add only when at least one shipped feature needs it.
- Add mirrored `tests/utils/test_queryset.py`.


### BACKLOG-024-0.1.0 — Fakeshop GraphQL schema activation

Priority: medium

Status: blocked on Layer 3 and Relay decisions

Current behavior:

- `examples/fakeshop/apps/products/schema.py` exposes a placeholder `hello` field for the product catalog.
- The aspirational schema block depends on `DjangoConnectionField`, Relay interfaces, filters, orders, aggregates, fieldsets, and permissions.

Definition of done:

- Uncomment only the portions whose dependencies have shipped.
- Keep unshipped subsystem lines commented until their specs land.
- Move or defer `search_fields` before uncommenting because it is currently a rejected Meta key.
- Add in-process schema tests under `examples/fakeshop/tests/`.
- Add live `/graphql/` tests under `examples/fakeshop/test_query/` only when testing the HTTP endpoint.

### BACKLOG-025-0.0.x — Public surface promotion discipline

Priority: medium

Status: ongoing

Current behavior:

- Top-level exports currently include `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `finalize_django_types`, `auto`, and `__version__`.
- Future names must follow the public-surface promotion discipline in this card.
- README/TREE language should use the public-surface status vocabulary: `shipped`, `partial`, `experimental`, `planned`, `in flight`, `deferred`, and `aspirational`.

Definition of done for each future public symbol:

- Implementation shipped end-to-end.
- Tests pin consumer-visible behavior.
- Docs mark it shipped.
- API name is stable enough for alpha.
- Top-level `__all__` and subpackage exports are updated together.
- README/TREE status markers match the symbol's actual implementation state.

### BACKLOG-026-0.0.12 — Stable choice enum naming override

Priority: low-medium

Status: planned

Current behavior:

- Choice fields generate Strawberry enums and cache them by `(model, field_name)`.
- The first `DjangoType` to read a choice column wins the generated enum's GraphQL name.
- This is deterministic for a fixed import order but still makes schema naming dependent on which type imports first.

Potential scope:

- Add a stable override surface such as `Meta.choice_enum_names = {"status": "ItemStatusEnum"}`.
- Decide whether this belongs in the consumer-overrides spec or a small choice-enum follow-up spec.
- Preserve enum reuse by `(model, field_name)` while making the published schema name explicit when consumers need it.

Definition of done:

- New or amended spec documents the override key and ambiguity behavior.
- `_validate_meta` accepts the key only when the pipeline applies it end-to-end.
- `convert_choices_to_enum()` uses the explicit name when provided.
- Tests cover explicit naming, cache reuse, duplicate/conflicting names, and default first-reader behavior.

Files likely touched:

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/registry.py`
- `tests/types/test_converters.py`

### BACKLOG-027-0.0.13 — Model-property optimization hints

Priority: low-medium

Status: deferred

Current behavior:

- The optimizer plans Django model fields and relation fields.
- `Meta.optimizer_hints` controls relation planning only.
- Model properties and cached properties are not part of the optimizer contract.

Potential scope:

- Evaluate `model_property` / `cached_model_property` style hints after the core optimizer has real-world use.
- Decide whether property hints belong in `Meta.optimizer_hints`, a separate `Meta.property_hints`, or field customization.
- Define how property dependencies declare the Django columns or relations they require.

Definition of done:

- New spec defines supported property hint syntax and interaction with `only()`, `select_related`, and `prefetch_related`.
- Implementation lets computed fields declare required columns/relations without broadening every query.
- Tests cover plain properties, cached properties, relation-dependent properties, and failure modes.

Files likely touched:

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/plans.py`
- `tests/optimizer/`

### BACKLOG-028-0.0.x — Migration and adoption guides

Priority: medium

Status: planned

Current behavior:

- The package is intentionally shaped for teams coming from `django-filter`, DRF, `graphene-django`, and `strawberry-graphql-django`.
- The feature docs explain the positioning, but there are no dedicated migration guides yet.

Potential scope:

- Add a `graphene-django` migration guide covering `DjangoObjectType` to `DjangoType`, enum/field conversion differences, query optimizations, and Relay caveats.
- Add a `strawberry-graphql-django` migration guide covering decorator-to-`Meta` translation, optimizer differences, `get_queryset`, and optimizer hints.
- Add concise notes for DRF / django-filter users mapping serializers/filtersets/orders into the planned Layer 3 surfaces.

Definition of done:

- New docs are added for the two major migration paths.
- README and `FEATURES.md` link to the migration docs.
- Guides distinguish shipped migration steps from planned Layer 3 migration targets.

Files likely touched:

- future migration docs under `docs/`
- `docs/README.md`
- `docs/FEATURES.md`


### BACKLOG-029-0.0.x — Layered manual relation override tests

Priority: low

Status: partially addressed by the testing-shift follow-up

Current behavior:

- Package tests in `tests/types/test_definition_order.py` intentionally inspect Strawberry internals (`field.base_resolver.wrapped_func.*`) to pin resolver-attachment details and fail early if Strawberry changes the underlying field shape.
- The live HTTP suite in `examples/fakeshop/test_query/test_library_api.py` now also proves the consumer-visible contract: a consumer-authored relation resolver on the real `library` schema shapes `/graphql/` response data.
- This is the chosen policy for now: package tests pin internal wiring; HTTP tests pin observable behavior.

Potential scope:

- If Strawberry internals churn becomes noisy, introduce a single named helper (production or test-only) that centralizes the `StrawberryField.base_resolver` access and documents the coupling.
- Keep at least one HTTP assertion for consumer-authored relation override behavior so the public contract does not depend only on internals.
- Revisit when the deferred `DjangoModelField` custom Strawberry field class lands; production code may need a stable resolver-introspection helper then.

Definition of done:

- Override coverage remains layered: internal attachment details are pinned in package tests, and consumer-visible override behavior is pinned through schema/HTTP response data.
- Any future direct Strawberry-internal access is centralized or documented at the helper site.

Files likely touched:

- `tests/types/test_definition_order.py`
- `examples/fakeshop/test_query/test_library_api.py`
- possibly a helper in `django_strawberry_framework/types/resolvers.py` if production code needs it

### BACKLOG-031-0.0.6 — FieldMeta SSoT consolidation

Priority: low

Status: planned

Current behavior:

- `FieldMeta` (`django_strawberry_framework/optimizer/field_meta.py`) is the canonical relation-shape single source of truth: cardinality flags, `attname`, `related_model`, FK target columns.
- Three sites still re-derive relation shape via `relation_kind(field)` + raw `getattr(field, ...)` instead of reading the `FieldMeta` already on `DjangoTypeDefinition.field_map`:
  - `django_strawberry_framework/types/base.py:_record_pending_relation` — anchored with `TODO(spec-fieldmeta-ssot)`.
  - `django_strawberry_framework/types/converters.py:resolved_relation_annotation` — anchored with `TODO(spec-fieldmeta-ssot)`.
  - `django_strawberry_framework/types/resolvers.py:_make_relation_resolver` — anchored with `TODO(spec-fieldmeta-ssot)`.
- The `optimizer/field_meta.py` module docstring enumerates the three reader sites as cross-references back to `FieldMeta`.

Why it matters:

- Three shape-derivation paths can drift when Django adds a relation flag or when reverse-relation descriptor attributes change.
- Routing every reader through one `FieldMeta` instance removes the raw Django-private `getattr` calls from production code and shrinks the drift surface to one place.

Definition of done:

- Each anchored site reads its `FieldMeta` from `DjangoTypeDefinition.field_map` (keyed by `field.name` / `snake_case(field.name)`) instead of recomputing.
- The three `TODO(spec-fieldmeta-ssot)` anchors are removed in the same change.
- The `optimizer/field_meta.py` module docstring paragraph listing the three reader sites is trimmed accordingly.
- Tests cover all current cardinalities (forward FK, OneToOne, reverse OneToOne, reverse FK, M2M) so the three readers still produce identical annotations / pending-relation records / resolvers.
- Coverage stays at 100%; no new public surface.

Files likely touched:

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `tests/types/`

### BACKLOG-032-0.0.6 — FieldMeta mirror retirement

Priority: low

Status: planned

Current behavior:

- `DjangoType.__init_subclass__` writes legacy class-attribute mirrors (`cls._optimizer_field_map`, `cls._optimizer_hints`) in addition to populating the canonical `DjangoTypeDefinition.field_map` / `optimizer_hints`. The writer is at `django_strawberry_framework/types/base.py:137`, anchored with `TODO(spec-fieldmeta-mirror-retirement)`.
- The optimizer still reads the legacy mirrors at four sites:
  - `django_strawberry_framework/optimizer/walker.py:_resolve_field_map` — anchored with `TODO(spec-fieldmeta-mirror-retirement)`.
  - `django_strawberry_framework/optimizer/walker.py:_walk_selections` (hints read) — anchored with `TODO(spec-fieldmeta-mirror-retirement)`.
  - `django_strawberry_framework/optimizer/extension.py:_collect_schema_reachable_types` — anchored with `TODO(spec-fieldmeta-mirror-retirement)`.
  - `django_strawberry_framework/optimizer/extension.py:check_schema` — anchored with `TODO(spec-fieldmeta-mirror-retirement)`.
- The `optimizer/field_meta.py` module docstring documents the mirror and cross-references this card.

Why it matters:

- The mirror is dead weight after the foundation slice put `DjangoTypeDefinition` on the canonical metadata path; the optimizer should reach the same data through `registry.get_definition(type_cls)` so there is one source of truth and no compatibility shim.
- Removing the mirror also removes a class-attribute residue that survives `registry.clear()`, which today is documented as a non-issue for tests that recreate classes but is still extra surface.

Definition of done:

- All four reader sites read `field_map` / `optimizer_hints` from `registry.get_definition(type_cls)` (or accept a missing definition gracefully where the walker tolerates an unregistered model today).
- The mirror writer at `django_strawberry_framework/types/base.py` is removed in the same change.
- The five `TODO(spec-fieldmeta-mirror-retirement)` anchors are deleted.
- The `optimizer/field_meta.py` module docstring paragraph documenting the mirror is removed.
- Coverage stays at 100% with the existing optimizer/fakeshop tests; no new public surface.

Files likely touched:

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `tests/optimizer/`

### BACKLOG-030-0.0.9 — Connection-aware optimizer planning

Priority: medium (gated on `NEXT-019-0.0.9` / Relay decisions)

Status: planned

Current behavior:

- The optimizer's plan cache, `select_related` / `prefetch_related` planning, FK-id elision, and queryset diffing are all proven for direct selection trees and nested non-Relay relation paths.
- Relay-style nested connection selections (`{ allObjects { edges { node { values { edges { node { value } } } } } } }`, mirroring the cookbook recipes shape) have not been exercised against the optimizer.
- The cookbook reference `AdvancedDjangoFilterConnectionField` does its own argument and queryset construction; the Strawberry equivalent will need the optimizer to recognize Relay edge/node wrappers in its selection walk.

Potential scope:

- Selection-tree walker awareness of Relay `edges { node { ... } }` pattern.
- Connection-pagination-aware queryset planning (`Prefetch` downgrade for `connection { edges { node } }`, `total_count` aggregate cooperation, slice-aware projections).
- Plan-cache key hygiene for paginated selections (skip pagination args that do not affect selection shape, hash the ones that do).
- Strictness-mode interaction with connection paths so unplanned nested connection access still surfaces as N+1.

Definition of done:

- New spec, probably `docs/spec-connection_optimizer.md` (or folded into `docs/spec-connection.md`).
- Walker recognizes connection edge/node shapes without reaching into `DjangoConnectionField` internals.
- Tests cover the cookbook-equivalent nested-connection shape against fakeshop or the cardinality fixture.
- No regression on the existing B1-B8 plan-cache and queryset-diff coverage.

Files likely touched:

- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/optimizer/extension.py`
- future `django_strawberry_framework/connection.py`
- mirrored optimizer tests

## Blocked / Deferred

### BLOCKED-033-0.0.9 — Full Relay story

Resolved blockers (Node half shipped in `DONE-011-0.0.5`, `0.0.5`):

- ~~`Meta.interfaces` design~~ — shipped as `DONE-011-0.0.5`.
- ~~`GlobalID` mapping decision~~ — shipped as `DONE-011-0.0.5` (Decision 2 of [`docs/spec-relay_interfaces.md`](docs/spec-relay_interfaces.md)).

Remaining blocker (Connection half still blocked):

- `DjangoConnectionField` design (pending; `NEXT-019-0.0.9`)

Unblocks:

- Relay node queries (shipped via `DONE-011-0.0.5`).
- fakeshop aspirational schema activation (Connection half still blocked).
- connection field public surface (Connection half still blocked).

### BLOCKED-034-0.0.x — Layer 3 Meta key promotion

Blocked by:

- each Layer 3 subsystem implementation

Affected keys:

- `filterset_class`
- `orderset_class`
- `aggregate_class`
- `fields_class`
- `search_fields`

Rule:

- Do not move a key from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` until the pipeline applies it end-to-end.

### BLOCKED-035-0.1.0 — Product-catalog Layer 3 HTTP GraphQL tests

Blocked by:

- activating the product-catalog fakeshop GraphQL schema
- connection/query fields and other Layer 3 public surfaces

Current state:

- The library app already has live `/graphql/` acceptance tests under `examples/fakeshop/test_query/`.
- Future product-catalog HTTP tests should use the same placement and schema-reload pattern.
- In-process `schema.execute_sync` tests still go under `examples/fakeshop/tests/`.

## Suggested sequencing

### Sequence A — Stabilize Layer 2 before Layer 3

1. READY-012-0.0.7 — multiple types per model / `Meta.primary`.
2. READY-013-0.0.10 — consumer override semantics (scalar fields).
3. ~~Relay / `Meta.interfaces`~~ — shipped as `DONE-011-0.0.5`.
4. READY-014-0.0.6 — deferred scalar conversions.
5. BACKLOG-026-0.0.12 — stable choice enum naming override.
6. BACKLOG-027-0.0.13 — model-property optimization hints.

Use this sequence if the goal is to make `DjangoType` feel solid before expanding the public API.

### Sequence B — Ship visible Layer 3 value sooner

1. NEXT-015-0.0.6 — `FieldSet`.
2. NEXT-016-0.0.8 — filters.
3. NEXT-017-0.0.8 — orders.
4. NEXT-018-0.0.11 — aggregates.
5. NEXT-019-0.0.9 — `DjangoConnectionField` (interacts with `BACKLOG-030-0.0.9` for connection-aware optimizer planning).
6. NEXT-020-0.0.9 — permissions.
7. BACKLOG-024-0.1.0 — activate fakeshop schema.

Use this sequence if the goal is to demonstrate the DRF-shaped API surface quickly.

### Recommended hybrid (current direction)

1. **Next** — `NEXT-015-0.0.6` `FieldSet`. Smallest Layer 3 slice.
2. NEXT-016-0.0.8 and NEXT-017-0.0.8 — filters and orders. Both reuse the pending-resolution pattern from the foundation slice for lazy related-class references.
3. READY-012-0.0.7 — introduce `Meta.primary` before connection/permissions need multiple type variants (also interacts with the filter input-type factory namespace decision in `NEXT-016-0.0.8`).
4. NEXT-019-0.0.9 and NEXT-020-0.0.9 — connection field and permissions. `BACKLOG-030-0.0.9` runs alongside `NEXT-019-0.0.9` to keep the optimizer aware of Relay-shaped selections.
5. NEXT-018-0.0.11 — aggregates.
6. READY-013-0.0.10 — finalize scalar-field consumer override semantics once the relation contract has bedded in.
7. BACKLOG-026-0.0.12 — add stable choice enum naming if schema import-order friction appears in real use.
8. BACKLOG-027-0.0.13 — add model-property optimization hints if computed fields start broadening queries.
9. BACKLOG-029-0.0.x — keep the layered override-test policy healthy as Strawberry internals and future custom field classes evolve.
10. BACKLOG-024-0.1.0 — activate the real product-catalog fakeshop GraphQL schema.


## Release readiness checklist

Before a release:

- `pyproject.toml` and `django_strawberry_framework/__init__.py` versions match.
- README status matches actual top-level exports.
- `docs/README.md`, `docs/FEATURES.md`, `docs/TREE.md`, and any active design docs agree on shipped/planned state.
- No stale skipped tests refer to already-shipped slices.
- New source modules have mirrored tests in the correct tree.
- `uv run ruff format .` passes.
- `uv run ruff check --fix .` passes.
- `uv run pytest` passes with 100% package coverage when explicitly run for release validation.

## Notes for Kanban maintenance

- Treat this file as a living operational board, not a spec.
- When a card moves to Done, update the evidence and remove stale blocker language.
- When a future spec creates a new subsystem, add it here as a card with a definition of done.
- Keep `CHANGELOG.md` out of routine updates unless explicitly requested.
- Strategic differentiation candidates (features neither `graphene-django` nor `strawberry-graphql-django` ship cleanly) live in [`BETTER.md`](BETTER.md). When a `BETTER.md` item is scheduled, promote it to a `NEXT-NNN-X.Y.Z` or `READY-NNN-X.Y.Z` card here and cross-reference back.
