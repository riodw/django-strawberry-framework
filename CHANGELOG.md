# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Versioning

This project follows a milestone-style cadence during pre-`1.0.0`:

- **Alpha (`0.0.x`)** — each patch ships a coherent feature group on the road to `0.1.0`. Public surface is still in flight; breaking changes can land in any patch. Strict [Semantic Versioning](https://semver.org/spec/v2.0.0.html) does **not** apply here.
- **`0.1.0` (beta release)** — feature parity with `graphene-django` (`⚛️`) and `strawberry-graphql-django` (`🍓`) is complete. Alpha → beta cut-over. Tracked by `TODO-BETA-035-0.1.0` in [`KANBAN.md`](KANBAN.md).
- **Beta (`0.1.x`)** — each patch ships a Layer-3 capability (`FieldSet`, `search_fields`, aggregations, choice-enum naming, fakeshop activation, migration guides) on the road to `1.0.0`. Public surface stabilizes; breaking changes are discouraged but not forbidden.
- **`1.0.0` (stable release)** — full `django-graphene-filters` depth on top of parity. Beta → stable cut-over; **API freeze**. Tracked by `TODO-STABLE-044-1.0.0` in [`KANBAN.md`](KANBAN.md).
- **Stable (`1.x.y`)** — strict [Semantic Versioning](https://semver.org/spec/v2.0.0.html) applies from this point forward: breaking changes require a MAJOR bump, additive changes require a MINOR bump, and bug-fix-only releases get a PATCH bump.

See [`KANBAN.md`](KANBAN.md) for the per-card sequencing and the version scope of each patch.

## [Unreleased]
### Added
- `BigInt` public scalar export — JSON-safe, decimal-string-serialized, with a strict regex parser (`^(0|-?[1-9][0-9]*)$`) and a strict serializer that rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`. See [`BigInt` scalar](docs/FEATURES.md#bigint-scalar). Tracked as `DONE-013-0.0.6` in [`KANBAN.md`](KANBAN.md).
- `JSONField → strawberry.scalars.JSON` mapping in `SCALAR_MAP`.
- `HStoreField → strawberry.scalars.JSON` mapping via a sentinel-guarded branch in `convert_scalar` (soft-registered, only when `django.contrib.postgres.fields` imports successfully).
- PostgreSQL `ArrayField` recursion through `field.base_field` via a sentinel-guarded branch in `convert_scalar`. Nested `ArrayField` and outer `choices` on `ArrayField` / `HStoreField` are rejected with `ConfigurationError`.
- `Meta.primary` boolean flag. Multiple `DjangoType` subclasses per Django model. Registry surface: `primary_for`, `types_for`, `models_with_multiple_types`. Tracked as `DONE-014-0.0.6` in [`KANBAN.md`](KANBAN.md).
- `TypeRegistry.unregister(type_cls)` public helper. Removes all traces of a type from the registry: types list, model index, primary slot, definition, and pending relations sourced from the type. Honours `_check_mutable`; no-op for unregistered types. Test fixtures that previously poked the registry's private maps to drop a registration now go through this helper.
- Annotation-only scalar field overrides on `DjangoType`. Writing `description: int` (or any other class-level scalar annotation that shadows a Django scalar column selected via [`Meta.fields`](FEATURES.md#metafields)) is now a stable public contract — the consumer's annotation wins over the auto-synthesized one and survives `finalize_django_types()` / `strawberry.type(...)` decoration. Mirrors the annotation-only relation-override path that has shipped since `0.0.4` (`DONE-006-0.0.4`).
- `DjangoTypeDefinition.consumer_annotated_scalar_fields: frozenset[str]` — introspection surface for the new override path; symmetric with the existing `consumer_annotated_relation_fields`, `consumer_assigned_relation_fields`, and `consumer_assigned_scalar_fields` sets.
- `ConfigurationError` raised at `DjangoType.__init_subclass__` time when a consumer authors an `id` annotation on a `Meta.interfaces = (relay.Node,)`-shaped type that is not a `relay.NodeID[...]`-marked annotation. Points at `strawberry.relay.NodeID[<pk_type>]` as the supported escape hatch. Replaces the downstream Strawberry-side `ValueError` ("Interface field Node.id expects type ID! but ...") that surfaced only at `strawberry.Schema(...)` construction. Narrow guard: `id: relay.NodeID[int]` is accepted in direct, stringified / PEP 563 / `from __future__ import annotations`, and mixed (directly-resolved `id` alongside other unresolved annotations on the same class) forms; non-`id` consumer scalar overrides on Relay-Node-shaped types (including custom-named primary keys like `code: str` on `models.CharField(primary_key=True)`) are accepted; inherited `id` annotations on a Relay-Node-shaped subclass also pass through at class-creation time (the guard does not walk the MRO) and are silently handled by `_build_annotations`'s pk-suppression branch — Strawberry applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()` falls back to `"pk"`, so schema construction succeeds. Detection uses `typing.get_type_hints(cls, include_extras=True)` with a fail-soft fallback for unresolved forward references that distinguishes "id itself failed to resolve" (accept only when the raw string matches the token-shaped regex `(?:^|\.)NodeID\[`, so prefixed-substring lookalikes like `"NotNodeID[int]"` are rejected) from "id is directly resolved but another annotation failed" (inspect the resolved object via `_has_node_id_marker`). The fail-soft accept window for unresolved NodeID-shaped strings is package-level guard suppression only — Strawberry's downstream resolution against `cls`'s module globals still applies.

### Changed
- Consolidated field metadata onto `DjangoTypeDefinition` as the single source of truth. Three reader sites in `types/` (`_record_pending_relation`, `resolved_relation_annotation`, `_make_relation_resolver`) now read `FieldMeta` from `DjangoTypeDefinition.field_map` instead of re-deriving relation shape via `relation_kind(field)` + raw `getattr(field, ...)`. The optimizer reads `FieldMeta` from `registry.get_definition(type_cls)` at all four former mirror-reader sites (`walker._resolve_field_map`, `walker._walk_selections`, `extension._collect_schema_reachable_types`, `extension.check_schema`); the legacy `cls._optimizer_field_map` / `cls._optimizer_hints` class-attribute mirrors are retired. Internal refactor only — no public surface or consumer-visible behavior change. Tracked as `DONE-012-0.0.6` in [`KANBAN.md`](KANBAN.md).
- `PositiveBigIntegerField` mapping switched from `int` to [`BigInt`](docs/FEATURES.md#bigint-scalar). Breaking wire-format change: `PositiveBigIntegerField` values are now serialized as decimal strings on the wire (not JSON integers) to survive GraphQL's signed 32-bit `Int` boundary. Consumers using the existing 32-bit `int` shape must update wire-format expectations.
- `registry.register` now returns `bool` (whether state was added; was `None`). `registry.register` and `registry.register_with_definition` gained a keyword-only `primary: bool = False` parameter. `registry.get(model)` semantics: returns the primary if declared; the single type if only one is registered; `None` if multiple types are registered with no primary. Tracked as `DONE-014-0.0.6` in [`KANBAN.md`](KANBAN.md).
- `registry.iter_types()` now yields once per registered type — a model with multiple types appears multiple times. Consumers iterating to drive a per-model action should explicitly dedupe by model, or use `models_with_multiple_types()` + `types_for(model)` for an explicit grouping.
- `_build_annotations` (`types/base.py`) always defers **auto-synthesized** relation annotations to `PendingRelationAnnotation` + the registry's pending list; the eager-bind shortcut is removed. Consumer-authored relation fields (annotation overrides and assigned `strawberry.field`) continue to skip synthesis entirely — the existing `if field.name in consumer_authored_fields: continue` short-circuit is preserved.
- optimizer plan cache key includes the resolver's origin Strawberry type alongside the model. Primary-return and secondary-return resolvers on the same model produce distinct cache entries.
- Annotation-only and assigned scalar field overrides bypass `convert_scalar` validations and side effects for the overridden field — unsupported-field-type rejection, grouped-choices rejection, `ArrayField` shape rejection, `null=True` widening, and choice-enum registration are skipped. The consumer's annotation is authoritative. `Meta.exclude` and annotation override are now parallel consumer recourses for unsupported scalar fields.
- `id = <StrawberryField>` assignment on a `Meta.interfaces = (relay.Node,)`-shaped `DjangoType` now raises `ConfigurationError` at `__init_subclass__` time. Previously consumers could write `@strawberry.field def id(self) -> relay.GlobalID: ...` (or `id = strawberry.field(description="…")`) and the resulting schema would build because the assigned-field type matched `Node.id: ID!`; this card uniformly rejects assigned `id` overrides on Relay-Node-shaped types for consistency with the annotation-side guard. The supported alternatives are `@classmethod resolve_id` (custom id resolver), `id: relay.NodeID[<pk_type>]` (custom id annotation), and a **resolver-backed sibling field** for the field-level GraphQL metadata use case (declare a separate field with a resolver — e.g., `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — carrying the metadata AND a value source; the Relay-supplied `id` stays undecorated). Field-level metadata on the Relay-supplied `id` field is not configurable in `0.0.6`; the resolver-backed sibling-field is the documented alternative. **Note**: a metadata-only sibling like `display_id: ID = strawberry.field(description="…")` without a resolver would build but fail at query time because Strawberry's default resolver looks up `display_id` as an attribute on the returned Django model instance and does not find it.

### Notes
- The internal `BigInt` scalar definition uses `strawberry.scalar(NewType, ...)`, which Strawberry deprecates in favor of `StrawberryConfig.scalar_map`. The deprecation warning is suppressed at the definition site so the package import remains clean. Migration to a `scalar_map`-based design is tracked as a follow-up and will be a real public-API change for consumers using `BigInt` directly.

## [0.0.5] - 2026-05-15
### Added
- Relay Node interface support: `Meta.interfaces` accepted for any Strawberry interface (Relay `Node` or `@strawberry.interface`-decorated classes).
- Default `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes` classmethods injected on every `DjangoType` whose `Meta.interfaces` declares `relay.Node`; consumer-declared overrides are preserved via Strawberry's `__func__` identity test (matches `strawberry-django`).
- Automatic synthesized `id: int!` suppression when `relay.Node` is in `Meta.interfaces` (including consumer subclasses of `relay.Node`); the Relay-supplied `id: GlobalID!` from the interface is used instead. The Django primary key remains selected as a connector column for the optimizer.
- `is_type_of` injection is unconditional for every `DjangoType` (Relay-declared or not); consumer-declared `is_type_of` is preserved.
- Models whose primary key is a Django 5.2+ `CompositePrimaryKey` raise `ConfigurationError` at finalization; declare an explicit `id: relay.NodeID[...]` annotation or remove `relay.Node` from `Meta.interfaces` to remediate.
- Both sync and async paths for `_resolve_node_default` / `_resolve_nodes_default`; `_resolve_id_attr_default` and `_resolve_id_default` are sync.
- `is_many_side_relation_kind` and `unwrap_graphql_type` utility helpers consolidated in `django_strawberry_framework.utils` so optimizer, walker, and type-conversion call sites share a single source of truth for relation cardinality and graphql-core type unwrapping.

### Changed
- `Meta.interfaces` promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`.
- Optimizer schema audit (`check_schema`) now descends into GraphQL union member types so `DjangoType`s reachable only through a union participate in the missing-target audit.
- `get_context_value` tolerates non-dict mapping contexts and `AttributeError` from `__getitem__` so `strawberry-graphql-django`'s attribute-bridging context and `__slots__`-backed mappings read correctly.

### Fixed
- `_check_n1` now receives the real `relation_kind` of the field being resolved (including `reverse_many_to_one`) instead of a hardcoded `"many"` / `"forward"`, so reverse-FK resolvers exercise the many-side N+1 check path consistently.
- `_ensure_connector_only_fields` now injects the forward FK column for reverse one-to-one prefetches so Django can bind each child row back to its parent without a lazy load.
- Optimizer walker now projects a `NodeID`-targeted relation via the FK `attname` (e.g. `user_id`) instead of the relation name (`user`), so `.only(...)` does not drag the related row back through a deferred load.
- `FieldMeta.nullable` is now forced to `False` for many-side cardinalities (`many_to_many`, `one_to_many`, `reverse_many_to_one`). Django's `ForeignObjectRel` inherits `null = True` as a class-level default, which caused reverse FK and M2M fields to be annotated as `list[T] | None` instead of `list[T]`, corrupting the schema.
- GraphQL-reserved enum member names (`true` / `false` / `null`) and introspection-prefixed (`__`) sanitizations from Django `choices` values now produce schema-valid Strawberry enums.
- Relay `_resolve_nodes_default` / `_resolve_nodes_async` materialize the input `node_ids` once so one-shot iterables (generators, `map`, etc.) survive both the IN-filter and the order-preserving key pass.
- Walker `_prefetch_hint_for_path` now rebases type-relative nested lookups onto the full path while preserving queryset and `to_attr`, and rejects mismatched lookups that do not target the hinted relation.
- Optimizer `stash_on_context` now handles frozen dict subclasses and `AttributeError` from `__getitem__` so the plan cache survives immutable mapping contexts.

### Removed
- Removed the dead `PendingRelation` hashability probe; `TypeRegistry.discard_pending()` removes pending records by identity rather than via a hash set.

## [0.0.4] - 2026-05-08
### Added
- `finalize_django_types()` public API and `DjangoTypeDefinition` metadata layer for definition-order-independent relation finalization before Strawberry schema construction.
- Relation finalization support for FK, reverse FK, OneToOne, reverse OneToOne, and M2M fields, including cyclic graphs and target types declared in either order.
- Fail-loud relation diagnostics that name unresolved targets, unsupported relation fields, and duplicate registry/choice-enum collisions instead of surfacing later as vague runtime errors.
- Relation-field override support that preserves consumer annotations, `strawberry.field` resolvers, and generated resolvers where appropriate.
- A restructured `examples/fakeshop` project with a real API-testing app, migrations, schema examples, and query tests for validating the package against Django behavior.

### Changed
- `DjangoType` subclass creation now collects model metadata and pending relations only; Strawberry decoration and generated relation resolver attachment happen during finalization.
- Optimizer metadata now lives on `DjangoTypeDefinition`, with compatibility mirrors retained on generated classes.
- Optimizer internals were hardened around context propagation, cache-key generation, field-map resolution, relation-kind classification, prefetch typing, lazy-load detection, and aliased selections with divergent arguments.
- Settings reload now mutates the existing singleton instance in place, and `registry.clear()` resets definitions, pending relations, finalized state, and class-mutation residue.
- User-facing docs were consolidated into code-first onboarding, a current feature catalog, architecture notes, testing guidance, and review/inspection documentation.
- Tests were expanded across settings, registry lifecycle, choice conversion, relation resolution, definition-order cycles, generic foreign keys, optimizer hints, plans, walker behavior, and the fakeshop example.

### Fixed
- `OptimizerHint` now rejects conflicting flag combinations, and `Meta.optimizer_hints` keys must refer to selected fields.
- Choice enum conversion now raises `ConfigurationError` for name collisions that would otherwise silently lose values.
- Unsupported relation fields such as `GenericForeignKey` now raise `ConfigurationError` during annotation building with guidance to exclude or override the field.
- Relation cache checks now handle single-valued and synthetic Django relation objects more reliably.

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

See [`docs/README.md`](docs/README.md) for the architecture and [`KANBAN.md`](KANBAN.md) for per-release sequencing. The Versioning section at the top of this file describes the alpha → beta → stable milestone cadence.
