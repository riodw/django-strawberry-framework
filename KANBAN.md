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
- Test suite structure has caught up with the package shape:
  - `tests/optimizer/` covers `extension.py`, `walker.py`, `plans.py`, `hints.py`, and `field_meta.py`.
  - `tests/types/` covers `base.py`, `converters.py`, and `resolvers.py`.
  - `tests/utils/` covers utility modules.

### In progress

- **0.0.4 foundation slice — definition-order independence.** Implementation contract: [`docs/spec-foundation.md`](docs/spec-foundation.md). This is the current focus for the next release. The slice introduces `DjangoTypeDefinition`, the pending-relation registry, `finalize_django_types()`, the OneToOne / M2M cardinality fixture, the post-finalization registration guard, and the relation-field manual-annotation contract. It also deletes `registry.lazy_ref`, removes the eager `convert_relation` raise, and bumps the package version to `0.0.4`. Card: `IN-PROGRESS-001`.

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
  - stable consumer override semantics for **scalar** fields (the foundation slice pins the contract for relation fields only)
  - stable choice-enum naming override, because the first `DjangoType` to read a choice field currently wins the enum name
  - `Meta.interfaces` / Relay interface wiring
  - deferred scalar conversions: `BigIntegerField`, `ArrayField`, `JSONField`, `HStoreField`
- Optimizer follow-up ideas remain outside the shipped B1-B8 surface:
  - model-property / cached-property optimization hints
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

Note: the foundation slice (`IN-PROGRESS-001`) pins the consumer-override contract for **relation fields only** (`DjangoTypeDefinition.consumer_annotated_relations`, finalizer skip). This card now covers the remaining scalar-field override semantics.

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

Priority: medium

Status: ready (most of this lands as a side effect of `IN-PROGRESS-001`)

Current issues:

- `tests/types/test_base.py` still has skipped placeholders for M2M and forward-reference independence. Both are removed by the foundation slice: the M2M skip is replaced by the new cardinality fixture, and the forward-reference skip is replaced by the new `tests/types/test_definition_order.py` cycle tests.
- `docs/alpha-review-feedback.md` is now the 0.0.4 consolidation checklist, not a historical cache-key bug review.

Definition of done:

- After the foundation slice merges, audit `tests/types/test_base.py` for any remaining stale skip reasons and update them.
- Keep `docs/alpha-review-feedback.md` focused on the current 0.0.4 consolidation pass until the archive work is done.
- Run formatting/lint.

Files likely touched:

- `tests/types/test_base.py`
- `docs/alpha-review-feedback.md`

### READY-007 — Version and release alignment

Priority: medium

Status: handled inside `IN-PROGRESS-001` — the next release is `0.0.4` and the bump ships with the foundation slice.

Current behavior:

- `pyproject.toml` version is `0.0.3`.
- `django_strawberry_framework/__init__.py` version is `0.0.3`.
- The next release is `0.0.4`, gated by the foundation slice.

Definition of done:

- Bump `pyproject.toml` and `django_strawberry_framework/__init__.py` to `0.0.4` as part of `IN-PROGRESS-001` (phased step 12 of `spec-foundation.md`).
- Confirm README/Kanban/docs language matches `0.0.4` (this Kanban already does).
- Add a `CHANGELOG.md` entry for `0.0.4` summarizing the new `finalize_django_types()` public API and the definition-order independence behavior.

Files likely touched:

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `CHANGELOG.md`
- docs status text as needed

## Next up

### NEXT-001 — `FieldSet`

Priority: high for Layer 3

Status: needs spec or implementation slice

Why first:

- `FieldSet` is the smallest Layer 3 surface and can define field-selection semantics used by `DjangoConnectionField`.
- It bridges the existing `DjangoType.Meta.fields` behavior and future connection/query APIs.

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

Definition of done:

- Add `docs/spec-filters.md`.
- Add `django_strawberry_framework/filters/`.
- Add mirrored `tests/filters/`.
- Promote `Meta.filterset_class` only when filters are applied end-to-end from `DjangoType` / connection fields.
- Keep filter declarations composable with ordering, aggregation, permissions, and optimizer planning.
- Expose enough introspection for one type definition to show what filter surface it supports.
- Use fakeshop flows where practical, but package tests belong under `tests/filters/`.
- Validate Django ORM query generation for N+1 opportunities when filters traverse relations.

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

Priority: medium

Status: closed by `IN-PROGRESS-001` (cardinality fixture under `tests/fixtures/cardinality_models.py`).

Current behavior:

- Relation conversion and optimizer paths include M2M branches.
- Fakeshop has no M2M model field; the foundation slice introduces unmanaged synthetic `Author` / `Tag` / `Book` models for in-package tests rather than expanding fakeshop.

Definition of done:

- Unskip/replace M2M placeholder tests — done by the foundation slice's cyclic acceptance tests and optimizer regression tests.
- Cover relation conversion, resolver behavior, and optimizer prefetch behavior for M2M — covered by `tests/types/test_definition_order.py` and `tests/optimizer/test_definition_order.py`.

Note: this card is retained for traceability and will be moved to Done once the foundation slice merges.

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

1. **IN-PROGRESS-001** — 0.0.4 foundation slice (definition-order independence). **Current focus.**
2. READY-002 — multiple types per model / `Meta.primary`.
3. READY-003 — consumer override semantics (scalar fields).
4. READY-004 — Relay / `Meta.interfaces`.
5. READY-005 — deferred scalar conversions.
6. BACKLOG-007 — stable choice enum naming override.
7. BACKLOG-008 — model-property optimization hints.

Use this sequence if the goal is to make `DjangoType` feel solid before expanding the public API.

### Sequence B — Ship visible Layer 3 value sooner

1. **IN-PROGRESS-001** — 0.0.4 foundation slice. Layer 3 cannot land safely without finalized concrete relation metadata.
2. NEXT-001 — `FieldSet`.
3. NEXT-002 — filters.
4. NEXT-003 — orders.
5. NEXT-004 — aggregates.
6. NEXT-005 — `DjangoConnectionField`.
7. NEXT-006 — permissions.
8. BACKLOG-005 — activate fakeshop schema.

Use this sequence if the goal is to demonstrate the DRF-shaped API surface quickly.

### Recommended hybrid (current direction)

1. **IN-PROGRESS-001** — 0.0.4 foundation slice (definition-order independence + finalization lifecycle). Reduces friction across every future subsystem.
2. NEXT-001 — implement `FieldSet` as the smallest Layer 3 slice.
3. NEXT-002 and NEXT-003 — filters and orders.
4. READY-002 — introduce `Meta.primary` before connection/permissions need multiple type variants.
5. NEXT-005 and NEXT-006 — connection field and permissions.
6. READY-003 — finalize scalar-field consumer override semantics once the relation contract has bedded in.
7. BACKLOG-007 — add stable choice enum naming if schema import-order friction appears in real use.
8. BACKLOG-008 — add model-property optimization hints if computed fields start broadening queries.
9. BACKLOG-005 — activate the real fakeshop GraphQL schema.

READY-006 (stale-placeholder cleanup) runs as a side effect of IN-PROGRESS-001, not as a standalone step.

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
