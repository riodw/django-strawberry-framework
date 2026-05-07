# django-strawberry-framework Kanban

Last refreshed: 2026-05-07

This board summarizes what is shipped, what has recently landed, and what remains to finish based on the current code, tests, docs, and release-readiness notes. It is intentionally written as a project-management view: each card has a status, priority, scope, and a practical definition of done.

For install, local development, testing, and the canonical documentation map, start from [`README.md`](README.md).

## Snapshot

### Shipped foundation

- Layer 1 shared infrastructure is in place: `conf.py`, `exceptions.py`, `registry.py`, `utils/strings.py`, `utils/typing.py`, `py.typed`.
- The package builds directly on `strawberry-graphql` and does not depend on `strawberry-graphql-django`; that dependency boundary is intentional so this package controls its DRF-shaped API surface end-to-end.
- `DjangoType` is usable today for model-backed Strawberry types:
  - Meta validation for `model`, `fields`, `exclude`, `name`, `description`, and `optimizer_hints`.
  - Deferred Meta keys are rejected loudly: `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`.
  - Scalar conversion, relation conversion, choice-enum generation, generated relation resolvers, and `get_queryset` sentinel detection are implemented.
- `DjangoOptimizerExtension` is usable today:
  - O1 through O6 are implemented: relation resolvers, root-gated planning, nested prefetch chains, `only()` projection, and `get_queryset`-aware `Prefetch` downgrade.
  - B1 through B8 are implemented: AST plan cache, FK-id elision, strictness mode, optimizer hints, context plan stashing, schema audit, precomputed field metadata, and queryset diffing.
  - Recent cache-key review findings are implemented in source: fragment-spread directives are collected and multi-operation documents hash the selected operation AST.
- 0.0.4 foundation slice has shipped (card `DONE-006`):
  - `DjangoTypeDefinition` is the canonical per-type metadata object stashed at `cls.__django_strawberry_definition__`, with forward-reserved slots (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`) ready for Layer 3 to populate.
  - `finalize_django_types()` resolves pending relations, attaches generated relation resolvers, and runs `strawberry.type(cls, ...)` for every collected type. Re-exported from `django_strawberry_framework` and `django_strawberry_framework.types`.
  - Pending-relation registry (`PendingRelation`, `add_pending_relation`, `iter_pending_relations`, `discard_pending`, `is_finalized`, `mark_finalized`, extended `clear`) supports definition-order-independent FK / reverse FK / forward + reverse OneToOne / forward + reverse M2M / multi-cycle graphs.
  - Manual relation override contract (`consumer_annotated_relation_fields` vs `consumer_assigned_relation_fields`): annotation-only overrides keep the generated relation resolver; `strawberry.field(resolver=...)` / `@strawberry.field` overrides suppress it.
  - Fail-loud unresolved-target finalization error names source model, source field, and target model.
  - OneToOne / M2M cardinality fixture lives at `tests/fixtures/cardinality_models.py` (registered via the `tests.fixtures.apps.TestsCardinalityConfig` Django app).
  - Package version is `0.0.4`.
- Test suite structure has caught up with the package shape:
  - `tests/optimizer/` covers `extension.py`, `walker.py`, `plans.py`, `hints.py`, `field_meta.py`, and `definition_order.py`.
  - `tests/types/` covers `base.py`, `converters.py`, `resolvers.py`, `definition_order.py`, and `definition_order_schema.py`.
  - `tests/test_registry.py` covers idempotency / phase-1 atomicity / phase-2/3 partial-mutation / pending-set cleanup / class-mutation residue.
  - `tests/utils/` covers utility modules.
  - 326 passed, 1 skipped, 0 failed under `uv run pytest tests --no-cov -q`.

### In progress

- No active 0.0.4 foundation tasks. The final release-polish feedback has been applied; optional follow-ups remain tracked in the backlog.

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
- Several DjangoType contract gaps remain:
  - multiple `DjangoType`s per model / `Meta.primary`
  - stable consumer override semantics for **scalar** fields (the foundation slice pinned the contract for relation fields only)
  - stable choice-enum naming override, because the first `DjangoType` to read a choice field currently wins the enum name
  - `Meta.interfaces` / Relay interface wiring (insertion point: finalizer phase 3, before `strawberry.type(cls)`; the slot is already on `DjangoTypeDefinition`)
  - deferred scalar conversions: `BigIntegerField`, `ArrayField`, `JSONField`, `HStoreField`
- Optimizer follow-up ideas remain outside the shipped B1-B8 surface:
  - model-property / cached-property optimization hints
  - connection-aware planning for Relay-style nested connection selections (new card `BACKLOG-012`)
- Test/example hygiene items surfaced by the foundation slice review:
  - durable override-test pattern that does not couple to Strawberry's `StrawberryField.base_resolver.wrapped_func` shape (`BACKLOG-011`)
  - move the cardinality fixture's `INSTALLED_APPS` line out of the example project's production-shaped settings (`BACKLOG-010`)
- The fakeshop GraphQL schema is still a placeholder; the aspirational schema block remains commented.

## Board columns

## Done

### DONE-001 — DjangoType core foundation

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
- Definition-order independence is not part of this completed card; see READY-001.

### DONE-002 — Optimizer O1-O6 foundation

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

### DONE-003 — Optimizer beyond slices B1-B8

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

### DONE-004 — Documentation/status positioning for shipped Layer 2

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

### DONE-005 — 0.0.4 onboarding docs and completed-spec archive

Priority: completed docs cleanup

Scope:

- Root `README.md` is the canonical documentation map and operational entry point.
- `docs/README.md` is code-first: quickstart, three-minute path, optimizer behavior, and status.
- `docs/FEATURES.md` is the capability catalog with value-led optimizer language and comparison table.
- `docs/TREE.md` is the detailed layout/test-tree reference.
- `CHANGELOG.md` is condensed and no longer points at archived design docs.
- Completed design docs are removed after shipped behavior is folded into docs and future work is preserved here.

Evidence:

- `README.md`
- `docs/README.md`
- `docs/FEATURES.md`
- `docs/TREE.md`
- `CHANGELOG.md`

Notes:

- Future in-flight design docs still use the `docs/spec-<topic>.md` convention, then get folded into durable docs and archived when shipped.

### DONE-006 — 0.0.4 foundation slice (definition-order independence)

Priority: completed Layer 2 foundation

Status: complete.

Scope:

- `DjangoTypeDefinition` dataclass with forward-reserved slots for every Layer 3 subsystem.
- `PendingRelation` and pending-relation registry API (`add_pending_relation`, `iter_pending_relations`, `discard_pending`, `is_finalized`, `mark_finalized`, extended `clear`).
- `finalize_django_types()` three-phase finalizer (resolve pending → attach resolvers → `strawberry.type(cls)`), with phase-1 failure-atomicity and named-source-model error format.
- Manual relation override contract: split `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields` so annotation-only overrides keep the generated resolver while assigned-field / decorator overrides suppress it. Class-attribute shadowing of relation fields raises `ConfigurationError`.
- `PendingRelationAnnotation` sentinel with metaclass `__repr__` that surfaces a useful `TypeError` body if `strawberry.Schema(...)` is constructed before finalization.
- MRO-aware `_detect_custom_get_queryset` so abstract bases without `Meta` still flip the `has_custom_get_queryset` sentinel for downstream concrete subclasses.
- Cardinality fixture under `tests/fixtures/cardinality_models.py` (`User`, `Profile(OneToOneField)`, `Author`, `Tag`, `Book(ForeignKey, M2M)`).
- Dedicated test files: `tests/types/test_definition_order.py`, `tests/types/test_definition_order_schema.py`, `tests/optimizer/test_definition_order.py`, plus `tests/test_registry.py` extensions for idempotency / phase-1 atomicity / phase-2/3 partial-mutation contract / pending-set cleanup / class-mutation residue.
- Documentation sweep: `README.md`, `docs/README.md`, `docs/FEATURES.md`, `TODAY.md`, and `CHANGELOG.md`.
- Version bump to `0.0.4` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `uv.lock`.
- Deletion of `TypeRegistry.lazy_ref`; removal of the eager `convert_relation` `ConfigurationError` (failure moved into the finalizer).

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
- `tests/fixtures/cardinality_models.py`
- `CHANGELOG.md`
- `docs/spec-foundation.md`
- `docs/feedback.md`

Notes:

- The forward-reserved slots on `DjangoTypeDefinition` are the architectural seam where the cookbook-shaped Layer 3 subsystems plug in (each subsystem moves its `Meta` key out of `DEFERRED_META_KEYS`, populates the matching slot in collection, and consumes it during finalization or in `DjangoConnectionField`).
- The pending-resolution pattern (record at class creation, resolve at finalization, fail loud on missing target with named source model / field / target) generalizes directly to lazy related class references for `RelatedFilter`, `RelatedOrder`, and `RelatedAggregate`.
- The previous foundation-slice in-progress cards have been retired; this card is their successor in Done.

## In progress
No active cards.

## Ready

### READY-002 — Multiple DjangoTypes per model with `Meta.primary`

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

### READY-003 — Consumer override semantics (scalar fields)

Priority: high

Status: ready for design, not implementation-by-assumption

Note: the foundation slice (`DONE-006`) pins the consumer-override contract for **relation fields only** (`DjangoTypeDefinition.consumer_annotated_relations`, finalizer skip). This card now covers the remaining scalar-field override semantics.

Current behavior:

- `DjangoType.__init_subclass__` merges consumer annotations over synthesized annotations for both scalar and relation fields, but only the relation-field path will be a stable contract after the foundation slice ships.
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

### READY-004 — Relay and `Meta.interfaces`

Priority: medium-high

Status: blocked on relay design

Current behavior:

- `Meta.interfaces` is rejected as a deferred key.
- Consumers can subclass Strawberry interfaces directly, but the Meta key is not wired.
- Primary keys map to `int`, not Relay `GlobalID`.

Why it matters:

- The aspirational fakeshop schema uses `relay.Node`.
- `DjangoConnectionField` will need a coherent Relay story.

Definition of done:

- New Relay/interface spec.
- Decide whether `Meta.interfaces` injects bases before `strawberry.type`.
- Decide whether `AutoField` / `BigAutoField` / `SmallAutoField` mapping for Relay types is automatic, tied to `Meta.interfaces`, or controlled by a `MAP_AUTO_ID_AS_GLOBAL_ID`-style setting.
- Implement and test `relay.Node` integration.
- Define how Relay interfaces interact with future connection fields and any future polymorphic-interface story.
- Move `interfaces` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when it is applied end-to-end.

Files likely touched:

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- future `django_strawberry_framework/connection.py`
- `tests/types/test_base.py`
- future connection/relay tests

### READY-005 — Deferred scalar conversions

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

### READY-006 — Test/doc cleanup for stale placeholders

Priority: completed

Status: closed by `DONE-006`. The M2M and forward-reference skips were replaced by `tests/types/test_definition_order.py`, `tests/types/test_definition_order_schema.py`, and `tests/optimizer/test_definition_order.py`. The remaining skipped scalar-override test (`test_consumer_annotation_overrides_synthesized`) is documented as a separate scalar-field concern under `READY-003`.

Note: this card is retained for traceability and will be moved to Done in the next Kanban refresh.

### READY-007 — Version and release alignment

Priority: completed

Status: closed by `DONE-006`. The version bump and `[0.0.4]` changelog entry are both complete.

Current behavior:

- `pyproject.toml` version is `0.0.4`.
- `django_strawberry_framework/__init__.py` version is `0.0.4`.
- `tests/base/test_init.py` asserts `"0.0.4"`.
- `uv.lock` is synced.
- `KANBAN.md` `RELEASE-002` (this card) and `docs/review/REVIEW.md` reference `0.0.4` / `0_0_4`.

Note: the bullet list above is preserved for the historical record.

## Next up

### NEXT-001 — `FieldSet`

Priority: high for Layer 3

Status: needs spec or implementation slice

Why first:

- `FieldSet` is the smallest Layer 3 surface and can define field-selection semantics used by `DjangoConnectionField`.
- It bridges the existing `DjangoType.Meta.fields` behavior and future connection/query APIs.

Foundation-slice seam:

- `DjangoTypeDefinition.fields_class` is the forward-reserved slot the collection phase will populate.
- `Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (see also `BACKLOG-011` for the `DjangoModelField` custom Strawberry field class that field-level permissions will likely require).

Definition of done:

- Add `docs/spec-fieldset.md`.
- Implement `django_strawberry_framework/fieldset.py`.
- Add `tests/test_fieldset.py`.
- Keep the API Meta-class-driven.
- Do not top-level export until the public-surface rules are satisfied.

### NEXT-002 — Filtering subsystem

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
- Decide whether the input-type factory's namespace shares the `TypeRegistry` or has its own (interacts with `READY-002` and the `Meta.primary` design).

Dependencies:

- Field selection semantics may affect filter argument generation.
- `utils/queryset.py` may become useful here.

### NEXT-003 — Ordering subsystem

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

### NEXT-004 — Aggregation subsystem

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

### NEXT-005 — `DjangoConnectionField`

Priority: high once filters/orders/fieldset are stable

Status: planned

Scope:

- Relay-style connection field
- composition of filtering, ordering, aggregation, field selection, and optimizer behavior

Foundation-slice seam:

- `finalize_django_types()` is the single architectural entry point that `DjangoConnectionField(DjangoType)` (and `DjangoNodeField`) will auto-trigger as their wrapper. Spec note: `docs/spec-foundation.md:65` already calls this out as a later-phase wrapper around the same finalizer.
- An auto-trigger wrapper must respect the single-threaded-setup window from `docs/spec-foundation.md:63`: either be constrained to schema-construction time, or acquire a real lock around the finalizer.
- Connection-aware optimizer planning is its own follow-up slice (`BACKLOG-012`); the foundation slice did not exercise nested connection prefetch shapes.

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

### NEXT-006 — Permissions subsystem

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

### BACKLOG-001 — `apps.py` and Django app config

Priority: medium

Status: planned

Definition of done:

- Add `django_strawberry_framework/apps.py`.
- Add `tests/test_apps.py`.
- Do not add settings placeholders unless a shipped feature consumes them.

### BACKLOG-002 — Schema export management command

Priority: medium

Status: planned

Definition of done:

- Add `django_strawberry_framework/management/commands/export_schema.py`.
- Add `tests/management/test_export_schema.py`.
- Test through `django.core.management.call_command`, not direct `handle()` calls.

### BACKLOG-003 — `utils/queryset.py`

Priority: medium

Status: planned

Potential scope:

- queryset introspection helpers
- prefetch-cache awareness helpers
- reusable utilities currently embedded in optimizer/resolver modules if they become cross-subsystem needs

Definition of done:

- Add only when at least one shipped feature needs it.
- Add mirrored `tests/utils/test_queryset.py`.

### BACKLOG-004 — Real M2M coverage

Priority: completed

Status: closed by `DONE-006` (cardinality fixture under `tests/fixtures/cardinality_models.py`).

Evidence:

- `tests/fixtures/cardinality_models.py` (`Author`, `Tag`, `Book` with FK + M2M relations; `User`, `Profile` with OneToOne).
- `tests/types/test_definition_order.py::test_many_to_many_forward_and_reverse_relations_resolve` covers forward and reverse M2M.
- `tests/optimizer/test_definition_order.py::test_plan_relation_decisions_match_cardinality_after_finalization` covers the optimizer's M2M planning decision.
- `tests/types/test_definition_order_schema.py::test_m2m_schema_shape_builds_without_database_tables` pins the schema shape for unmanaged M2M.

Note: this card is retained for traceability and will be moved to Done in the next Kanban refresh.

### BACKLOG-005 — Fakeshop GraphQL schema activation

Priority: medium

Status: blocked on Layer 3 and Relay decisions

Current behavior:

- `examples/fakeshop/fakeshop/products/schema.py` exposes a placeholder `hello` field.
- The aspirational schema block depends on `DjangoConnectionField`, Relay interfaces, filters, orders, aggregates, fieldsets, and permissions.

Definition of done:

- Uncomment only the portions whose dependencies have shipped.
- Keep unshipped subsystem lines commented until their specs land.
- Move or defer `search_fields` before uncommenting because it is currently a rejected Meta key.
- Add in-process schema tests under `examples/fakeshop/tests/`.
- Add live `/graphql/` tests under `examples/fakeshop/test_query/` only when testing the HTTP endpoint.

### BACKLOG-006 — Public surface promotion discipline

Priority: medium

Status: ongoing

Current behavior:

- Top-level exports currently include `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `auto`, and `__version__`.
- Future names must follow the public-surface promotion discipline in this card.
- README/TREE language should use the public-surface status vocabulary: `shipped`, `partial`, `experimental`, `planned`, `in flight`, `deferred`, and `aspirational`.

Definition of done for each future public symbol:

- Implementation shipped end-to-end.
- Tests pin consumer-visible behavior.
- Docs mark it shipped.
- API name is stable enough for alpha.
- Top-level `__all__` and subpackage exports are updated together.
- README/TREE status markers match the symbol's actual implementation state.

### BACKLOG-007 — Stable choice enum naming override

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

### BACKLOG-008 — Model-property optimization hints

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

### BACKLOG-009 — Migration and adoption guides

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

### BACKLOG-010 — Move test fixture out of example settings

Priority: low-medium

Status: planned (surfaced as N-2 in the round-4 foundation review)

Current behavior:

- `tests/fixtures/apps.py` is registered as a Django app via `examples/fakeshop/fakeshop/settings.py:51-52` (`"tests.fixtures.apps.TestsCardinalityConfig"`).
- The mechanism is required because the cardinality fixture's reverse-relation discovery (M2M, OneToOne) needs Django's app registry to know about the fixture models.
- The example project's production-shaped settings now reference test code, which is a layering concern: a downstream consumer copying `settings.py` as a starting point inherits a phantom `tests.fixtures` app reference.
- This deviates from `docs/spec-foundation.md:476` ("No `tests/conftest.py` and no `apps.get_app_config(...)` mutation by default"); the chosen mechanism is technically distinct from `apps.get_app_config(...)` mutation but has the same practical effect.

Potential scope:

- Move the fixture's `INSTALLED_APPS` registration into a test-scoped settings file (`examples/fakeshop/fakeshop/settings_test.py` or a `pytest.ini`-controlled `DJANGO_SETTINGS_MODULE` override).
- Or, leave it in place but add a load-bearing comment in `settings.py` explaining the line is test-scoped.
- Either way, update `docs/spec-foundation.md` to acknowledge the chosen mechanism.

Definition of done:

- The example project's production-shaped settings either no longer reference `tests.fixtures`, or carry a comment explaining why they do.
- `docs/spec-foundation.md` reflects the chosen approach (no silent drift between spec and code).
- Tests still pass without touching `apps.get_app_config(...)` from test code.

Files likely touched:

- `examples/fakeshop/fakeshop/settings.py` (or new `settings_test.py`)
- `pytest.ini` if a settings override is added
- `docs/spec-foundation.md`
- `tests/fixtures/apps.py` (only if relocation requires it)

### BACKLOG-011 — Durable override-test pattern (avoid Strawberry-internal coupling)

Priority: low

Status: planned (surfaced as N-3 in the round-4 foundation review)

Current behavior:

- `tests/types/test_definition_order.py` asserts that override resolvers wire correctly by reading `field.base_resolver.wrapped_func.__name__` and `field.base_resolver.wrapped_func.__qualname__`.
- These attribute paths are Strawberry-internal (`StrawberryField.base_resolver`); a Strawberry minor release that renames or wraps them breaks three tests at once with `AttributeError` rather than a useful assertion message.
- The decorator-override test at `test_decorator_relation_field_override_routes_schema_query_through_consumer_resolver` already routes a real schema query through the consumer's resolver, demonstrating the more durable pattern.

Potential scope:

- Promote the annotation-only and assigned-field override tests to schema-level (construct a `strawberry.Schema(query=Query)`, run a query, observe the resolver's side effect).
- Or, add a stable internal helper (e.g., `_resolver_callable_for_field(field)`) that hides the Strawberry-internal attribute path and gets used from both production code and tests.
- This becomes important when `BACKLOG-011`'s deferred `DjangoModelField` custom Strawberry field class lands (rich-schema spec layer 4); production code will need a stable helper too.

Definition of done:

- Override tests no longer reach into `field.base_resolver.wrapped_func.*` directly, or do so through a single named helper that documents the coupling.
- Tests still pin both directions of the manual relation-override contract (annotation-only keeps the generated resolver; assigned-field / decorator suppresses it).

Files likely touched:

- `tests/types/test_definition_order.py`
- possibly a new helper in `django_strawberry_framework/types/resolvers.py` or a test-only helper module

### BACKLOG-012 — Connection-aware optimizer planning

Priority: medium (gated on `NEXT-005` / Relay decisions)

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

### BLOCKED-001 — Full Relay story

Blocked by:

- `Meta.interfaces` design
- `GlobalID` mapping decision
- `DjangoConnectionField` design

Unblocks:

- fakeshop aspirational schema activation
- Relay node queries
- connection field public surface

### BLOCKED-002 — Layer 3 Meta key promotion

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

### BLOCKED-003 — Example HTTP GraphQL tests

Blocked by:

- real fakeshop GraphQL schema
- connection/query fields

Test placement:

- Live `/graphql/` tests go under `examples/fakeshop/test_query/`.
- In-process `schema.execute_sync` tests go under `examples/fakeshop/tests/`.

## Suggested sequencing

### Sequence A — Stabilize Layer 2 before Layer 3

1. READY-002 — multiple types per model / `Meta.primary`.
2. READY-003 — consumer override semantics (scalar fields).
3. READY-004 — Relay / `Meta.interfaces`.
4. READY-005 — deferred scalar conversions.
5. BACKLOG-007 — stable choice enum naming override.
6. BACKLOG-008 — model-property optimization hints.

Use this sequence if the goal is to make `DjangoType` feel solid before expanding the public API.

### Sequence B — Ship visible Layer 3 value sooner

1. NEXT-001 — `FieldSet`.
2. NEXT-002 — filters.
3. NEXT-003 — orders.
4. NEXT-004 — aggregates.
5. NEXT-005 — `DjangoConnectionField` (interacts with `BACKLOG-012` for connection-aware optimizer planning).
6. NEXT-006 — permissions.
7. BACKLOG-005 — activate fakeshop schema.

Use this sequence if the goal is to demonstrate the DRF-shaped API surface quickly.

### Recommended hybrid (current direction)

1. READY-004 — Relay / `Meta.interfaces`. The forward-reserved slot already exists on `DjangoTypeDefinition` and the finalizer's phase-3 insertion point is ready; this is the cheapest cookbook-shaped feature to land first.
2. NEXT-001 — `FieldSet`. Smallest Layer 3 slice.
3. NEXT-002 and NEXT-003 — filters and orders. Both reuse the pending-resolution pattern from the foundation slice for lazy related-class references.
4. READY-002 — introduce `Meta.primary` before connection/permissions need multiple type variants (also interacts with the filter input-type factory namespace decision in `NEXT-002`).
5. NEXT-005 and NEXT-006 — connection field and permissions. `BACKLOG-012` runs alongside `NEXT-005` to keep the optimizer aware of Relay-shaped selections.
6. NEXT-004 — aggregates.
7. READY-003 — finalize scalar-field consumer override semantics once the relation contract has bedded in.
8. BACKLOG-007 — add stable choice enum naming if schema import-order friction appears in real use.
9. BACKLOG-008 — add model-property optimization hints if computed fields start broadening queries.
10. BACKLOG-010 — relocate the test fixture out of the example settings (or annotate it).
11. BACKLOG-011 — durable override-test pattern; aligns naturally with the rich-schema-spec layer 4 `DjangoModelField` work.
12. BACKLOG-005 — activate the real fakeshop GraphQL schema.

`READY-006` (stale-placeholder cleanup) and `BACKLOG-004` (M2M coverage) are closed by `DONE-006`; both will be moved to Done at the next Kanban refresh.

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
