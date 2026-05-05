# django-strawberry-framework Kanban

Last refreshed: 2026-05-05

This board summarizes what is shipped, what has recently landed, and what remains to finish based on the current code, tests, and specs. It is intentionally written as a project-management view: each card has a status, priority, scope, and a practical definition of done.

## Snapshot

### Shipped foundation

- Layer 1 shared infrastructure is in place: `conf.py`, `exceptions.py`, `registry.py`, `utils/strings.py`, `utils/typing.py`, `py.typed`.
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
- Several DjangoType contract gaps remain:
  - definition-order independence / `registry.lazy_ref`
  - multiple `DjangoType`s per model / `Meta.primary`
  - stable consumer override semantics
  - `Meta.interfaces` / Relay interface wiring
  - deferred scalar conversions: `BigIntegerField`, `ArrayField`, `JSONField`, `HStoreField`
  - real M2M fixture/test coverage
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

- Some old spec text still describes O4 as pending. Treat source/tests as truth and clean docs under READY-007.
- `tests/types/test_base.py` still has a skipped O6 placeholder that is now stale. Track that under READY-006.

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

- `docs/README.md` describes shipped Layer 1 and Layer 2.
- `docs/spec-optimizer.md` checklist marks O1-O6 complete.
- `docs/spec-optimizer_beyond.md` checklist marks B1-B8 complete.

Evidence:

- `docs/README.md`
- `docs/spec-optimizer.md`
- `docs/spec-optimizer_beyond.md`

Notes:

- This is not fully clean. Several docs still contain stale sections or old target trees. Track cleanup under READY-007.

## Ready

### READY-001 — Definition-order independence for relation conversion

Priority: high

Status: ready to spec/implement

Current behavior:

- `convert_relation()` requires the target `DjangoType` to be registered before the source type is declared.
- `registry.lazy_ref()` still raises `NotImplementedError`.

Why it matters:

- Real projects often have cyclic or cross-module model graphs.
- Requiring strict declaration order is brittle and un-DRF-like.

Likely implementation options:

- string annotations rewritten after all sibling types register
- `Annotated["TargetType", strawberry.lazy("module.path")]` for cross-module references
- registry-tracked pending relation records plus a `finalize_types()` pass

Definition of done:

- Pick and document one strategy.
- Implement `registry.lazy_ref()` or replace it with the chosen mechanism.
- `convert_relation()` no longer raises for target types declared later when the schema can resolve them.
- Unskip or replace `test_forward_reference_resolves_when_target_defined_later`.
- Add cross-module and same-module tests.

Files likely touched:

- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/base.py`
- `tests/types/test_base.py`
- `tests/test_registry.py`

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

### READY-003 — Consumer override semantics

Priority: high

Status: ready for design, not implementation-by-assumption

Current behavior:

- `DjangoType.__init_subclass__` merges consumer annotations over synthesized annotations.
- Strawberry later rewrites class annotation/field metadata, so the override is not a reliable public contract.
- `test_consumer_annotation_overrides_synthesized` remains skipped.

Why it matters:

- Consumers need a stable way to customize generated fields without abandoning `DjangoType`.
- The package should not claim annotations override generated fields until it is true end-to-end.

Open design choices:

- Use Strawberry field customization APIs.
- Add explicit `Meta.field_overrides`.
- Support annotation overrides by controlling the timing of Strawberry finalization.

Definition of done:

- New spec, probably `docs/spec-consumer_overrides.md`.
- Clear supported override forms:
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
- `docs/spec-django_type_contract.md`

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
- Decide `AutoField` / `BigAutoField` / `SmallAutoField` mapping for Relay types.
- Implement and test `relay.Node` integration.
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

Status: ready

Current issues:

- `tests/types/test_base.py` still has a skipped placeholder named `test_optimizer_downgrades_to_prefetch_when_target_has_custom_get_queryset`, but O6 is implemented and covered in optimizer tests.
- `tests/types/test_base.py` still has skipped placeholders for M2M and forward-reference independence; those are valid, but should be named and grouped as future work rather than stale slice leftovers.
- `docs/alpha-review-feedback.md` contains historical findings for cache-key bugs that are already fixed in source.

Definition of done:

- Remove or rewrite the stale O6 skipped test.
- Keep valid future skips for M2M and `lazy_ref`, but make their skip reasons current and concise.
- Decide whether `docs/alpha-review-feedback.md` remains a historical review artifact or gets an “implemented” status note.
- Run formatting/lint.

Files likely touched:

- `tests/types/test_base.py`
- `docs/alpha-review-feedback.md`

### READY-007 — Documentation drift sweep

Priority: medium

Status: ready

Current issues:

- `docs/spec-django_types.md` still contains old “current state” language and historical implementation-slice text.
- `docs/spec-optimizer_nested_prefetch_chains.md` is now mostly a shipped design record but still reads as a pending implementation spec in many places.
- `docs/README.md` current tree still has a stale optimizer comment in the folder layout section that does not fully reflect O1-O6 and B1-B8.
- `docs/spec-public_surface.md` contains historical 0.0.3 decisions that may no longer match the current top-level exports.

Definition of done:

- Preserve historical design rationale, but clearly label shipped vs historical sections.
- Make `docs/README.md`, `docs/TREE.md`, and spec status sections agree with source.
- Avoid changing `CHANGELOG.md` unless explicitly requested.
- Do not remove useful design context; prefer “Status now” callouts over destructive rewrites.

Files likely touched:

- `docs/README.md`
- `docs/TREE.md`
- `docs/spec-django_types.md`
- `docs/spec-optimizer_nested_prefetch_chains.md`
- `docs/spec-public_surface.md`
- `docs/alpha-review-feedback.md`

### READY-008 — Version and release alignment

Priority: medium

Status: ready when preparing a release

Current behavior:

- `pyproject.toml` version is `0.0.2`.
- `django_strawberry_framework/__init__.py` version is `0.0.2`.
- Specs mention “0.0.3” as shipped/in flight in places.

Definition of done:

- Decide the next release version.
- Bump `pyproject.toml` and `django_strawberry_framework/__init__.py` together.
- Confirm README/spec language matches the chosen release.
- Only update `CHANGELOG.md` if explicitly requested.

Files likely touched:

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
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
- Support simple fields and relation paths.
- Define interaction with filters and connection field.

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
- Decide result type naming and grouping semantics.
- Validate generated queryset aggregation paths.

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

Definition of done:

- Add `docs/spec-permissions.md`.
- Implement `django_strawberry_framework/permissions.py` or a `permissions/` package if the surface grows.
- Add `tests/test_permissions.py`.
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

Status: blocked on fixture/model choice

Current behavior:

- Relation conversion and optimizer paths include M2M branches.
- Fakeshop has no M2M model field, so dedicated M2M tests remain skipped.

Options:

- Add a small unmanaged synthetic model pair in tests.
- Add a real M2M relation to fakeshop if it benefits the example domain.
- Use Django auth `User.groups` only if it produces clear package-level tests without leaking example-app concerns.

Definition of done:

- Unskip/replace M2M placeholder tests.
- Cover relation conversion, resolver behavior, and optimizer prefetch behavior for M2M.

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
- Future names must follow `docs/spec-public_surface.md` rules.

Definition of done for each future public symbol:

- Implementation shipped end-to-end.
- Tests pin consumer-visible behavior.
- Docs mark it shipped.
- API name is stable enough for alpha.
- Top-level `__all__` and subpackage exports are updated together.

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

1. READY-006 — clean stale test/doc placeholders.
2. READY-007 — sweep spec and README drift.
3. READY-001 — definition-order independence.
4. READY-002 — multiple types per model / `Meta.primary`.
5. READY-003 — consumer override semantics.
6. READY-004 — Relay / `Meta.interfaces`.
7. READY-005 — deferred scalar conversions.
8. BACKLOG-004 — real M2M coverage.

Use this sequence if the goal is to make `DjangoType` feel solid before expanding the public API.

### Sequence B — Ship visible Layer 3 value sooner

1. READY-006 — clean stale test/doc placeholders.
2. NEXT-001 — `FieldSet`.
3. NEXT-002 — filters.
4. NEXT-003 — orders.
5. NEXT-004 — aggregates.
6. NEXT-005 — `DjangoConnectionField`.
7. NEXT-006 — permissions.
8. BACKLOG-005 — activate fakeshop schema.

Use this sequence if the goal is to demonstrate the DRF-shaped API surface quickly.

### Recommended hybrid

1. READY-006 — remove stale noise first.
2. READY-007 — bring docs into alignment so future planning starts from truth.
3. READY-001 — fix `lazy_ref`; it reduces friction across almost every future subsystem.
4. NEXT-001 — implement `FieldSet` as the smallest Layer 3 slice.
5. NEXT-002 and NEXT-003 — filters and orders.
6. READY-002 — introduce `Meta.primary` before connection/permissions need multiple type variants.
7. NEXT-005 and NEXT-006 — connection field and permissions.
8. BACKLOG-005 — activate the real fakeshop GraphQL schema.

## Release readiness checklist

Before a release:

- `pyproject.toml` and `django_strawberry_framework/__init__.py` versions match.
- README status matches actual top-level exports.
- `docs/README.md`, `docs/TREE.md`, and relevant specs agree on shipped/planned state.
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
