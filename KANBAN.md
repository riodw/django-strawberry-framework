# django-strawberry-framework Kanban

Last refreshed: 2026-05-21

This board summarizes what is shipped, what has recently landed, and what remains to finish based on the current code, tests, docs, and release-readiness notes. It is intentionally written as a project-management view: each card has a status, priority, scope, and a practical definition of done.

## Card ID format

Every card uses the form `<STATUS>[-<MILESTONE>]-NNN-X.Y.Z`:

- `<STATUS>` — the column the card lives in: `TODO` (committed to a milestone, not yet active), `WIP` (actively being worked), `BLOCKED` (waiting on a dependency), or `DONE` (shipped). Updated when the card moves between columns.
- `<MILESTONE>` *(optional)* — the development phase the card lives in while it's still pre-shipping: `ALPHA` (pre-`0.1.0`), `BETA` (post-`0.1.0` / pre-`1.0.0`), or `STABLE` (post-`1.0.0`). Used on `TODO`, `WIP`, and `BLOCKED` cards. The two release cards themselves are tagged with the phase they usher in: `TODO-BETA-036-0.1.0` is the alpha → beta cut-over and `TODO-STABLE-045-1.0.0` is the beta → stable cut-over. **Dropped when the card ships** — `DONE` cards use the bare `DONE-NNN-X.Y.Z` form (no milestone segment). The card's version tag (`X.Y.Z`) already encodes which phase the shipment belongs to, and the bare form keeps the shipped-card cluster compact and uniform across the package's history.
- `NNN` — a 3-digit sequence number indicating the order the card was completed (`DONE` cards) or is planned to be completed (every other card, ordered by planned ship version, ties broken by intra-version dependency order). **Unlike status, milestone, and version, this number is not stable** — it is recomputed whenever a card's position in the shipping sequence changes (reordered, new card inserted between two existing cards, version-tag bumped). Use the card title, not the NNN, when referencing a card from long-lived documents.
- `X.Y.Z` — the package version the card shipped in (Done cards) or is planned to ship in (everything else). Alpha cards span `0.0.6` through `0.0.12` leading up to `0.1.0`; Beta cards span `0.1.1` through `0.1.6` leading up to `1.0.0`. The `0.1.0` and `1.0.0` tags are reserved for the two release cards themselves. Anything beyond `1.0.0` lives in [`BACKLOG.md`](BACKLOG.md), not here.

For install, local development, testing, and the canonical documentation map, start from [`README.md`](README.md).

## Snapshot

### Shipped foundation

- Layer 1 shared infrastructure is in place: `conf.py`, `exceptions.py`, `registry.py`, `utils/relations.py`, `utils/strings.py`, `utils/typing.py`, `py.typed`.
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
- 0.0.5 shipped after this foundation slice and is recorded separately as `DONE-011-0.0.5`.
- 0.0.6 shipped as the patch closing the foundation phase: `DONE-012-0.0.6` (`FieldMeta` consolidation), `DONE-013-0.0.6` (deferred scalar conversions), `DONE-014-0.0.6` (multiple `DjangoType`s per model with `Meta.primary`), and `DONE-015-0.0.6` (consumer override semantics for scalar fields).
- Test suite structure has caught up with the package shape:
  - `tests/optimizer/` covers `extension.py`, `walker.py`, `plans.py`, `hints.py`, `field_meta.py`, and `definition_order.py`.
  - `tests/types/` covers `base.py`, `converters.py`, `resolvers.py`, `definition_order.py`, and `definition_order_schema.py`.
  - `tests/test_registry.py` covers idempotency / phase-1 atomicity / phase-2/3 partial-mutation / pending-set cleanup / class-mutation residue.
  - `tests/utils/` covers utility modules.
  - The full suite runs through `uv run pytest`, including package tests, example-project tests, and live `/graphql/` HTTP tests, with 100% package coverage.

### In progress

- `0.0.7` is the active patch. Five WIP cards were opened together so the small parity-driven slices land in one release; four have shipped (`DONE-016-0.0.7` `DjangoListField`, `DONE-017-0.0.7` `apps.py` and Django app config, `DONE-018-0.0.7` schema-export management command, and `DONE-019-0.0.7` multi-database cooperation contract). The remaining card — `WIP-ALPHA-020-0.0.7` (warning-free scalar registration via `StrawberryConfig.scalar_map`) — is still queued. Full card detail lives under the `## In progress` board column below; `DONE-016-0.0.7`, `DONE-017-0.0.7`, `DONE-018-0.0.7`, and `DONE-019-0.0.7` are in the `## Done` column. The last `0.0.7` card to ship owns the version bump from `0.0.6` per Decision 10 of `docs/SPECS/spec-016-list_field-0_0_7.md`.
- Strategic differentiation roadmap (post-`0.0.6`) captured in [`BACKLOG.md`](BACKLOG.md): items neither `graphene-django` nor `strawberry-graphql-django` ship cleanly that should land on the roadmap once parity items are shipped.

### Still not implemented

- Layer 3 public subsystems are still planned only:
  - `filters/`
  - `orders/`
  - `aggregates/`
  - `fieldset.py`
  - `connection.py`
  - `permissions.py`
  - `utils/queryset.py`
- Layer 3 still needs the original goal-level contract: declarative filtering, ordering, aggregation, and permission rules configured through `Meta`, composable with each other, and introspectable from one type definition.
- Several DjangoType contract gaps remain:
  - stable choice-enum naming override, because the first `DjangoType` to read a choice field currently wins the enum name
- Optimizer follow-up ideas remain outside the shipped B1-B8 surface:
  - model-property / cached-property optimization hints
  - connection-aware planning for Relay-style nested connection selections (new card `TODO-ALPHA-025-0.0.9`)
- Test/example hygiene items surfaced by the foundation slice review have moved into the testing-shift docs and backlog: package-level override tests intentionally pin Strawberry internals while HTTP tests pin the consumer-visible override contract ([`BACKLOG.md`](BACKLOG.md) item 38).
- The library GraphQL schema is real and wired into the project schema; the product-catalog Layer 3 aspirational schema block remains commented until those subsystems ship.

## Board columns

## In progress

### WIP-ALPHA-020-0.0.7 — Warning-free scalar registration via `StrawberryConfig.scalar_map`

Priority: medium

Severity: low (the suppressed warning in `0.0.6` is a workaround, not a runtime bug)

Status: ready for design

Predecessors: `DONE-013-0.0.6` (introduced the suppression debt); `docs/SPECS/spec-013-deferred_scalars-0_0_6.md` revision 7 (Decision 1, Decision 6, Risks).

Why it matters:

- `0.0.6` ships `BigInt` defined via `strawberry.scalar(NewType("BigInt", int), ...)`, which Strawberry deprecates in favor of `StrawberryConfig.scalar_map`. The deprecation warning is suppressed at the definition site in `django_strawberry_framework/scalars.py` so it doesn't escape to consumers — but the suppression is a workaround, not a fix.
- The right design defines `BigInt` (and any future package-defined scalars) on Strawberry's recommended path and has consumers merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`. This card pays down the debt, removes the suppression filter, and establishes the public-API pattern for any future package-defined scalar (planned: `Upload` for file / image fields in `TODO-ALPHA-027`; possibly more).
- Removes the `0.0.6` `Notes` line from `CHANGELOG.md` about suppressed deprecation; closes the architectural debt explicitly.

Recommended architectural direction (pinned here so the spec doesn't re-litigate the helper shape):

- **Helper API shape: factory function.** Expose `strawberry_config(extra_scalar_map=None) -> StrawberryConfig` returning a composed `StrawberryConfig` pre-populated with the package's scalar map. Note: `extra_extensions=` deliberately omitted — Strawberry extensions go to `strawberry.Schema(..., extensions=[...])`, not into `StrawberryConfig`. If the follow-up reveals a need to compose extensions too, that's a separate helper (returning a schema-construction bundle, not a `StrawberryConfig`). Consumer usage:

  ```python
  from django_strawberry_framework import strawberry_config, DjangoOptimizerExtension
  import strawberry

  schema = strawberry.Schema(
      query=Query,
      config=strawberry_config(),
      extensions=[DjangoOptimizerExtension()],
  )
  ```

  Rationale: explicit (consumer sees what they're getting); composable (factory accepts `extra_scalar_map=...` for consumer additions, merges instead of overwriting); forward-extensible (new package scalars / future config needs slot into the factory without API breaks); doesn't shadow Strawberry's `Schema` symbol.

  Alternatives considered (and recommended against): a static `SCALAR_MAP` constant (pushes `StrawberryConfig(...)` boilerplate onto every consumer); a `dst.Schema(...)` wrapper (shadows upstream symbol; hides composition).

- **`BigInt` symbol stays usable as a direct annotation.** `category: BigInt` in `DjangoType` and `@strawberry.field` annotations works as today. Internally, `BigInt` is a bare `NewType("BigInt", int)`; the `strawberry_config(...)` factory registers `BigInt → ScalarDefinition(...)` in its `scalar_map`. The wire format, parser, and serializer logic are preserved verbatim from `0.0.6`.

- **Single-line consumer migration.** Consumers upgrading from `0.0.6` add `config=strawberry_config()` to their existing `strawberry.Schema(...)` call. No annotation changes. No re-import.

- **Recommended posture: hard break in alpha.** Suggested default — no deprecation window — consumers using `BigInt` directly in `0.0.6` who don't add `config=strawberry_config()` will see Strawberry schema-construction fail with `Unexpected type '...BigInt'`. Matches the `PositiveBigIntegerField` precedent in `0.0.6`'s Changed entry. Long deprecation windows are appropriate at `1.0.0`, not during alpha — but the follow-up spec author can revisit after surveying real `0.0.6` consumer adoption of `BigInt`.

- **Composition story.** Factory accepts `extra_scalar_map` to merge with consumer-defined scalars without losing the package's defaults. Conflict resolution: explicit error if a key collides between package defaults and consumer extras, instructing the consumer to override the package default via a separate API (TBD in the spec).

- **Forward compatibility for future package scalars.** When `Upload` (TODO-ALPHA-027) and any future package scalars ship, they slot into the factory's internal scalar map without API changes. Consumers' existing `strawberry_config()` calls continue to work; new scalars become usable immediately.

Definition of done:

- New spec: `docs/spec-scalar_map_helper.md` settling the helper API shape, composition story (including conflict resolution between package defaults and consumer extras), and the migration guide.
- `django_strawberry_framework/scalars.py` — `BigInt` redefined as a bare `NewType` (or per the spec's final decision); strict parser and serializer preserved; suppression filter removed.
- New `django_strawberry_framework/config.py` (or wherever the helper lives — TBD by spec; follows `docs/TREE.md` mirror rule) exposing the factory.
- `django_strawberry_framework/__init__.py` updated: re-export the helper (`strawberry_config`); `BigInt` stays in `__all__` (consistent with the recommended "BigInt as a direct annotation" usage pattern above).
- `tests/base/test_init.py` — pinned `__all__` assertion updated.
- New test file mirroring the helper's source location (e.g., `tests/test_config.py`).
- `tests/test_scalars.py` updated: the `test_package_import_does_not_emit_strawberry_deprecation_warning` test continues to pass (no suppression needed because the deprecation is no longer triggered at all).
- `docs/README.md` quickstart updated to show the new schema-construction pattern; replaces every `strawberry.Schema(query=Query, ...)` example with `strawberry.Schema(query=Query, config=strawberry_config(), ...)`.
- `GOAL.md` schema-setup section updated.
- `examples/fakeshop/config/schema.py` updated to use the helper.
- `examples/fakeshop/apps/library/schema.py` (and any other example schemas) audited for direct `BigInt` usage — no change should be needed if they only use it indirectly via Django field-to-scalar mapping.
- `docs/GLOSSARY.md` updated: `BigInt scalar` entry covers the new construction pattern; new entry for the helper symbol; `Public exports` updated; `Quick start` and `Schema setup` walk-throughs (if present) updated.
- `CHANGELOG.md`:
  - `Changed`: "Public-API migration — `BigInt` now requires `config=strawberry_config()` in `strawberry.Schema(...)`. Single-line change for consumers using `BigInt` directly."
  - `Removed`: "Internal `warnings.catch_warnings()` suppression in `scalars.py` (no longer needed)."
  - Remove the `0.0.6` `Notes` line about suppressed deprecation.
- Migration note in `CHANGELOG.md` and the spec: explicit before/after code blocks.
- Archive the spec to `docs/SPECS/spec-scalar_map_helper.md`.

Files likely touched (subject to the follow-up spec settling final locations):

- `docs/spec-scalar_map_helper.md` (new)
- `django_strawberry_framework/scalars.py`
- `django_strawberry_framework/config.py` (new — or wherever the spec decides)
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `tests/test_config.py` (new)
- `tests/test_scalars.py`
- `docs/README.md`
- `docs/GLOSSARY.md`
- `docs/TREE.md` (if the new module location requires it)
- `GOAL.md`
- `examples/fakeshop/config/schema.py`
- `KANBAN.md` (move to Done; rewrite body)
- `CHANGELOG.md`

Open design questions for the spec (not blocking; spec author decides):

- Helper module name: `config.py`, `schema.py`, or kept as a top-level export in `__init__.py`?
- Conflict resolution when consumer's `extra_scalar_map` collides with package defaults: hard error, override with warning, or silent override?
- Deprecation-window details: should the recommended hard-break (matching `PositiveBigIntegerField` in `0.0.6`) be revisited after surveying real `0.0.6` consumer adoption? If softened to a one-release `DeprecationWarning` from the package, what does the warning shape look like?
- Helper module location: top-level export in `__init__.py`, or `django_strawberry_framework/config.py` (new module)?
- Helper signature beyond `extra_scalar_map=`: nothing more, or a small set of curated optional parameters? (Note: `extra_extensions=` does not fit here — extensions are passed to `strawberry.Schema(..., extensions=[...])`, not into `StrawberryConfig`. If extension composition becomes a need, it requires a separate helper returning a schema-construction bundle, not a `StrawberryConfig`.)

## To Do - Alpha (0.1.0)

Cards required to reach feature parity with both upstreams (`⚛️ graphene-django` and `🍓 strawberry-graphql-django`). Each card targets its own `0.0.x` patch within the road to **0.1.0**. The final card in this column is the `0.1.0` release itself (cleanup, verification, alpha → beta cut-over). Cards in NNN order = planned ship order; dependency and parallelism notes live on each card.

### TODO-ALPHA-021-0.0.8 — Filtering subsystem

Priority: high for package positioning (⚛️&🍓 parity-required)

Severity: **major**

Status: planned

Scope:

- `Filter`
- `FilterSet`
- filterset factory
- GraphQL argument factory
- input type/data adapters
- `Meta.filterset_class` promotion out of `DEFERRED_META_KEYS`

Verified upstream filter primitives (graphene-django parity floor):

- `array_filter.py` — `ArrayFilter(TypedFilter)`, `ArrayFilterMethod(FilterMethod)`
- `range_filter.py` — `RangeFilter(TypedFilter)`, `RangeField(Field)`
- `list_filter.py` — `ListFilter(TypedFilter)`, `ListFilterMethod(FilterMethod)`
- `typed_filter.py` — `TypedFilter(Filter)` (base class for the four above)
- `global_id_filter.py` — `GlobalIDFilter(Filter)`, `GlobalIDMultipleChoiceFilter(MultipleChoiceFilter)`

All sourced from `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/filters/`. Our implementation should ship equivalents for each (DRF-style class declarations on the filterset rather than graphene-style filter-class subclassing where it matters); the global-ID filter in particular is required for Relay-aware filtering against `relay.Node` types shipped in `DONE-011-0.0.5`.

`strawberry-graphql-django` covers the same surface through `filters.py` (single-file decorator-driven implementation) — verified at `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/filters.py`.

Foundation-slice seam:

- `DjangoTypeDefinition.filterset_class` is the slot the collection phase will populate; the BFS argument factory (analogous to `FilterArgumentsFactory` in the Graphene reference) reads it during finalizer phase 3.
- The pending-relation registry's record-now-resolve-at-finalization pattern reuses cleanly for lazy related-filter class references; a `LazyRelatedClassMixin` equivalent should reuse the same fail-loud error format ("Cannot finalize ... no registered ...") that the model-relation finalizer already produces.
- The relation-override contract pinned in 0.0.4 is what allows filter sidecars to reference relation fields by name without the framework clobbering consumer annotations or resolvers.

Lazy-resolution pipeline (borrowed from `django-graphene-filters`):

The four cooperating files in the Graphene reference (`filters.py`, `filterset.py`, `filterset_factories.py`, `filter_arguments_factory.py`) implement a six-layer lazy-resolution pipeline that handles circular `RelatedFilter` references across modules. **Five of six layers are library-agnostic Python and port verbatim**; only Layer 5 (the cycle-safe forward reference in the GraphQL schema build) is Strawberry-adapted.

1. **Lazy class references in `RelatedFilter`** — port verbatim from `filters.py:BaseRelatedFilter`. `RelatedFilter` accepts target as class, absolute import path string (`"myapp.filters.ManagerFilter"`), or unqualified name (`"ManagerFilter"`). `_filterset` stores it unresolved; the `.filterset` property triggers resolution.
2. **Module-fallback resolution** — port verbatim from `mixins.py:LazyRelatedClassMixin.resolve_lazy_class`. Two-step resolution: try as absolute path via `django.utils.module_loading.import_string`; on `ImportError`, retry with `bound_class.__module__` prefix. Handles circular-import scenarios in the same module.
3. **Metaclass discovery, deferred expansion** — port pattern from `filterset.py:FilterSetMetaclass`. Metaclass collects `BaseRelatedFilter` declarations into `cls.related_filters`, calls `f.bind_filterset(new_class)` so the module-fallback resolver knows the owning module, and **does not** expand. Expansion is deferred to `get_filters()`.
4. **Cycle-safe expansion + cache** — port verbatim from `filterset.py:AdvancedFilterSet.get_filters`. `cls.__dict__["_expanded_filters"]` cache plus `cls.__dict__["_is_expanding_filters"]` recursion guard. Two-condition cache write: `"related_filters" in cls.__dict__` AND no string `_filterset` remaining on any related filter. This is what breaks `A → B → A` cycles cleanly.
5. **BFS schema build with deferred references — Strawberry-adapted.** BFS algorithm in `filter_arguments_factory.py:FilterArgumentsFactory._ensure_built` ports verbatim; only the cycle-safe forward reference changes. Graphene's `graphene.InputField(lambda tn=target_name: input_object_types[tn])` becomes `strawberry.lazy("django_strawberry_framework.filters._registry.{TargetFilterSet}InputType")` (or an `Annotated[..., strawberry.lazy(...)]` annotation, whichever Strawberry's filter-input-class generator emits). The `lambda:` and `strawberry.lazy()` are exact conceptual twins — both defer the type reference until schema walk.
6. **Memoized dynamic FilterSet generation** — port verbatim from `filterset_factories.py:_dynamic_filterset_cache`. Cache keyed by `(model, fields, extra_meta)` for connection fields declared without an explicit `filterset_class`; prevents duplicate-`__name__` collisions when two connection fields target the same model.

Synchronization point: every layer runs inside `finalize_django_types()` phase 2.5 — the same seam that already wires `Meta.interfaces = (relay.Node,)` per `DONE-011-0.0.5`. For each `DjangoType` with `Meta.filterset_class`:

- validate the class is a `FilterSet`
- call `filterset_cls.get_filters()` to trigger Layer 4 expansion (resolves lazy refs, expands related filters with cycle guards)
- call `FilterArgumentsFactory(filterset_cls).arguments` to trigger Layer 5 BFS (builds every reachable `strawberry.input` type)
- register the resulting input types in a per-package filter-input-type registry

By phase 3, when `strawberry.type(cls, ...)` runs on the `DjangoType`, every referenced filter input type already exists. **No consumer-facing `strawberry.lazy()` calls needed** — the laziness is internal to the filter-input-type generator, mirroring how `django-graphene-filters` hides its lambdas inside `FilterArgumentsFactory`.

Verbatim ports beyond the six layers (also library-agnostic):

- `FilterArgumentsFactory.filterset_to_trees` / `try_add_sequence` / `sequence_to_tree` — per-lookup tree-building algorithm
- `AdvancedFilterSet._apply_related_queryset_constraints` — explicit queryset as security/scope boundary that can't be bypassed via nested filters
- `AdvancedFilterSet.check_permissions` — recursion through `RelatedFilter`s into child filtersets' `check_*_permission` methods
- `LOOKUP_PREFIXES` map for `construct_search` (`^` → `istartswith`, `=` → `iexact`, `@` → `search`, `$` → `iregex`)
- Recursion-protected `_get_fields` (with `visited: set[type]`)

Strawberry-adapted bits:

- `_build_class_type` emits a `strawberry.input`-decorated class instead of `type(name, (graphene.InputObjectType,), fields)`
- `_build_logic_fields` (`and` / `or` / `not`) uses self-referential `strawberry.lazy(...)` instead of `graphene.List(lambda: ...)`
- `_build_input_fields` lambda ref to target filterset's root type → `strawberry.lazy("...module.path...")`
- `GrapheneFilterSetMixin.FILTER_DEFAULTS` (FK/PK → `GlobalIDFilter`) → our own `FILTER_DEFAULTS` mapping FK/PK to a `strawberry.relay.GlobalID`-aware primitive (the global-ID filter in the upstream-primitives list above)
- `graphene_django.forms.converter.convert_form_field` → our own form-field → Strawberry-input converter; pairs with `TODO-ALPHA-028` (Form-based mutations), which builds the same converter for the mutation surface

Dropped (Graphene-specific, no Strawberry equivalent needed):

- `setup_filterset` wrapper avoidance — Strawberry's eager annotation resolution doesn't have the "Graphene{X}Filter" wrapping problem that motivated this in the reference
- `replace_csv_filters` — Strawberry's typed input handles `list[T]` natively without comma-separated-string workarounds

Reference symbols in the Graphene checkout (`/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/`): `filters.py:BaseRelatedFilter`, `mixins.py:LazyRelatedClassMixin`, `filterset.py:FilterSetMetaclass` + `AdvancedFilterSet.get_filters`, `filter_arguments_factory.py:FilterArgumentsFactory`, `filterset_factories.py:get_filterset_class` + `_dynamic_filterset_cache`.

Definition of done:

- Add `docs/spec-filters.md`.
- Add `django_strawberry_framework/filters/`.
- Add mirrored `tests/filters/`.
- Promote `Meta.filterset_class` only when filters are applied end-to-end from `DjangoType` / connection fields.
- Keep filter declarations composable with ordering, aggregation, permissions, and optimizer planning.
- Expose enough introspection for one type definition to show what filter surface it supports.
- Use fakeshop flows where practical, but package tests belong under `tests/filters/`.
- Validate Django ORM query generation for N+1 opportunities when filters traverse relations.
- Decide whether the input-type factory's namespace shares the `TypeRegistry` or has its own (interacts with `DONE-014-0.0.6` and the `Meta.primary` design).

Dependencies:

- Field selection semantics may affect filter argument generation.
- `utils/queryset.py` may become useful here.

### TODO-ALPHA-022-0.0.8 — Ordering subsystem

Priority: high after filters

Parity: 🍓 required (strawberry-graphql-django ships `strawberry_django.order`; graphene-django via `django-filter`-style ordering — sister card to TODO-ALPHA-021 Filtering).

Status: planned

Scope:

- `Order`
- `OrderSet`
- GraphQL argument factory
- `Meta.orderset_class` promotion

Foundation-slice seam:

- `DjangoTypeDefinition.orderset_class` is the populated slot.
- Lazy related-order class references reuse the same record-now-resolve-at-finalization pattern as model relations (`PendingRelation` → analogous `PendingRelatedClass` shape).

Lazy-resolution pipeline:

Reuses the six-layer lazy-resolution architecture spec'd in detail under `TODO-ALPHA-021-0.0.8` (Filtering subsystem). The same `LazyRelatedClassMixin`, metaclass-discovery + deferred-expansion pattern, cycle-safe `get_orders()` cache + recursion guard, BFS schema build, and `_dynamic_orderset_cache` memoization all port verbatim, with `RelatedOrder` substituted for `RelatedFilter` and `OrderSet` for `FilterSet`. The Strawberry adaptation is identical: Graphene's `lambda tn=...: input_object_types[tn]` forward references become `strawberry.lazy("django_strawberry_framework.orders._registry.{TargetOrderSet}InputType")` (or `Annotated[..., strawberry.lazy(...)]`). Synchronization runs inside `finalize_django_types()` phase 2.5 alongside filter resolution; the two subsystems share the same finalizer pass.

Reference symbols in the Graphene checkout: `django_graphene_filters/orders.py`, `orderset.py`, `order_arguments_factory.py` — mirror images of the filter trio with the same lazy-resolution shape.

Definition of done:

- Add `docs/spec-orders.md`.
- Add `django_strawberry_framework/orders/`.
- Add mirrored `tests/orders/`.
- Promote `Meta.orderset_class` only when ordering is applied end-to-end.
- Support simple fields and relation paths.
- Define interaction with filters and connection field.
- Keep ordering declarations introspectable from the owning type/query surface.

### TODO-ALPHA-023-0.0.9 — `DjangoConnectionField`

Priority: high once filters/orders/fieldset are stable

Parity: ⚛️&🍓 required (both upstreams ship Relay-shaped connection fields).

Status: planned

Scope:

- Relay-style connection field
- composition of filtering, ordering, aggregation, field selection, and optimizer behavior

Foundation-slice seam:

- `finalize_django_types()` is the single architectural entry point that `DjangoConnectionField(DjangoType)` (and `DjangoNodeField`) will auto-trigger as their wrapper. Spec note: `docs/spec-foundation.md:65` already calls this out as a later-phase wrapper around the same finalizer.
- An auto-trigger wrapper must respect the single-threaded-setup window from `docs/spec-foundation.md:63`: either be constrained to schema-construction time, or acquire a real lock around the finalizer.
- Connection-aware optimizer planning is its own follow-up slice (`TODO-ALPHA-025-0.0.9`); the foundation slice did not exercise nested connection prefetch shapes.

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

### TODO-ALPHA-025-0.0.9 — Connection-aware optimizer planning

Priority: medium (gated on `TODO-ALPHA-023-0.0.9` / Relay decisions)

Parity: 🍓 required (strawberry-graphql-django's optimizer plans connection selections natively; graphene-django has only rudimentary connection-aware optimization — 🍓 required, ⚛️ parity-adjacent).

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

### TODO-ALPHA-026-0.0.10 — Permissions subsystem

Priority: high for the fakeshop example and real usage

Parity: ⚛️ required (django-graphene-filters ships rich cascade + per-field permissions; strawberry-graphql-django has a weaker per-field permission story — ⚛️ required, 🍓 parity-adjacent).

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

### TODO-ALPHA-027-0.0.11 — Mutations + auto-generated Input types

Priority: high (🍓 parity-required)

Severity: **major**

Status: needs spec — no on-board predecessor

Why it matters:

- Mutations are the single largest unscoped gap against `strawberry-graphql-django`. Consumers migrating from strawberry-graphql-django will notice the missing write side immediately.
- `strawberry-django` exposes `create`, `update`, `delete`, custom mutations, and auto-generated `Input` / `PartialInput` types per model. These compose with permissions and the optimizer.

Verified in upstream:

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/mutations/` — `mutations.py` (create/update/delete classes), `fields.py` (`DjangoMutationField`), `resolvers.py` (sync/async write resolvers), `types.py` (input-type generation).

Definition of done:

- Add `docs/spec-mutations.md`.
- Implement `django_strawberry_framework/mutations/` (sets, fields, resolvers, input-type generation) on the DRF-style Meta surface (`Meta.input_class`, `Meta.partial_input_class`, etc.).
- Auto-generated input types respect the relation-override contract pinned in `DONE-006-0.0.4`.
- Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `TODO-ALPHA-028-0.0.11`, `TODO-ALPHA-029-0.0.11`, and `TODO-ALPHA-030-0.0.11`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings).
- Tests under `tests/mutations/`.
- Live HTTP coverage under `examples/fakeshop/test_query/` exercising the products write surface.

Dependencies:

- `DONE-014-0.0.6` (`Meta.primary`) — explicit primary type drives mutation target resolution.
- `TODO-ALPHA-026-0.0.10` (permissions) — write mutations need to compose with `apply_cascade_permissions`.

Files likely touched:

- `django_strawberry_framework/mutations/` (new)
- `django_strawberry_framework/types/base.py`
- `tests/mutations/` (new)
- `examples/fakeshop/apps/products/schema.py`

### TODO-ALPHA-028-0.0.11 — Upload scalar and file / image field mapping

Priority: medium (🍓 parity-required)

Severity: **medium**

Status: planned; pairs with `TODO-ALPHA-027-0.0.11` for the write side

Why it matters:

- `strawberry-graphql-django` maps `FileField` / `ImageField` to `Upload` on the input side and to `DjangoFileType` / `DjangoImageType` (with `name` / `path` / `size` / `url`) on the output side. Without it, every consumer that touches user uploads has to hand-roll the mapping.

Verified in upstream:

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py` — output mappings `files.FileField: DjangoFileType`, `files.ImageField: DjangoImageType`; input mappings `files.FileField: Upload`, `files.ImageField: Upload`.

Definition of done:

- Scalar conversion in `types/converters.py` returns `DjangoFileType` / `DjangoImageType` (or local equivalents) for `FileField` / `ImageField`.
- Mutation input-type generation (`TODO-ALPHA-027-0.0.11`) maps the same fields to Strawberry's `Upload` scalar.
- Synthetic-model tests cover both read and write paths.
- `docs/GLOSSARY.md` documents the conversion table change.

Files likely touched:

- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/mutations/` (input mapping)
- `tests/types/test_converters.py`

### TODO-ALPHA-029-0.0.11 — Form-based mutations (Django Forms / ModelForms)

Priority: high (⚛️ parity-required)

Severity: **major**

Status: needs spec — no on-board predecessor

Why it matters:

- `graphene-django` ships `DjangoFormMutation` and `DjangoModelFormMutation`: mutation classes that consume a Django `Form` / `ModelForm` and translate field validation + `cleaned_data` into a GraphQL mutation surface. Many graphene-django consumers rely on this as their write-side abstraction because it reuses validation they already have.
- Without an equivalent, graphene-django migrants must rewrite every form-backed mutation against the lower-level mutation surface from `TODO-ALPHA-027-0.0.11`.

Verified in upstream:

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/mutation.py` — `BaseDjangoFormMutation`, `DjangoFormMutationOptions`, `DjangoFormMutation`, `DjangoModelDjangoFormMutationOptions`, `DjangoModelFormMutation`, plus `fields_for_form(form, only_fields, exclude_fields)` helper.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/converter.py` — `convert_form_field` registry mapping Django form fields → GraphQL types.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/types.py` — `ErrorType` envelope shape.

Definition of done:

- Add `docs/spec-form_mutations.md`.
- Implement `django_strawberry_framework/forms/` on the DRF-style Meta surface (`Meta.form_class`, `Meta.return_field_name`, etc.) rather than graphene's `MutationOptions` pattern.
- Form-field → Strawberry input mapping lives in `forms/converter.py` and reuses the scalar conversion registry where field types overlap.
- Validation errors surface through the shared `errors: list[FieldError]` envelope defined in `TODO-ALPHA-027-0.0.11`, populated from `form.errors`.
- Tests under `tests/forms/`.
- Live HTTP coverage under `examples/fakeshop/test_query/` exercising both a plain `Form` mutation and a `ModelForm` mutation.

Dependencies:

- `TODO-ALPHA-027-0.0.11` — general mutation infrastructure (input-type generation, mutation-field plumbing) is the foundation form mutations attach to.

Files likely touched:

- `django_strawberry_framework/forms/` (new)
- `tests/forms/` (new)
- `examples/fakeshop/apps/products/schema.py`

### TODO-ALPHA-030-0.0.11 — DRF serializer mutations (`SerializerMutation`)

Priority: high (⚛️ parity-required)

Severity: **major**

Status: needs spec — no on-board predecessor

Why it matters:

- `graphene-django` ships `SerializerMutation`, which builds a mutation from a DRF `Serializer` / `ModelSerializer`. This is the highest-leverage write-side feature for DRF migrants — they already have serializers defined and want to reuse them in GraphQL.
- [`GOAL.md`](GOAL.md) explicitly names DRF as a target migration source ("keep the public API familiar to Django, DRF, and django-filter users"). Shipping `SerializerMutation` is on-mission, not just a parity item.

Verified in upstream:

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/mutation.py` — `SerializerMutationOptions` carrying `lookup_field`, `model_class`, `model_operations=["create", "update"]`, `serializer_class`, `optional_fields`; `SerializerMutation` class; `fields_for_serializer(serializer, only_fields, exclude_fields, is_input=False, convert_choices_to_enum=True, lookup_field=None, optional_fields=())` helper.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/serializer_converter.py` — DRF-field → GraphQL-type registry; same module covers input and output via `is_input` flag.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/types.py` — shared `ErrorType` envelope.

Definition of done:

- Add `docs/spec-serializer_mutations.md`.
- Implement `django_strawberry_framework/rest_framework/` exposing `SerializerMutation` (final name pinned during implementation) on the DRF-style Meta surface: `Meta.serializer_class`, `Meta.lookup_field`, `Meta.model_operations`, `Meta.optional_fields`.
- Serializer-field → Strawberry input mapping lives in `rest_framework/serializer_converter.py`, dual-purposed for inputs and outputs (mirroring graphene's `is_input=True` flag).
- `rest_framework` is a soft dependency: package import must succeed without DRF installed; the helper raises `ImportError` with an install hint when actually called.
- Validation errors surface through the shared `errors: list[FieldError]` envelope from `TODO-ALPHA-027-0.0.11`, populated from `serializer.errors`.
- Tests under `tests/rest_framework/`.
- Live HTTP coverage under `examples/fakeshop/test_query/` exercising a `ModelSerializer` mutation.

Dependencies:

- `TODO-ALPHA-027-0.0.11` — general mutation infrastructure (including the shared `errors` envelope).

Files likely touched:

- `django_strawberry_framework/rest_framework/` (new)
- `tests/rest_framework/` (new)
- `examples/fakeshop/apps/products/schema.py`

### TODO-ALPHA-031-0.0.11 — Auth mutations (login / logout / register)

Priority: medium (🍓 parity-required)

Severity: **medium**

Status: planned; depends on `TODO-ALPHA-027-0.0.11`

Why it matters:

- `strawberry-graphql-django` ships a small auth-mutations module so consumers don't have to hand-wire the most common Django auth flows. Natural follow-on once general mutations land.

Verified in upstream:

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/auth/` — `mutations.py` (login / logout / register), `queries.py` (`current_user`), `utils.py`.

Definition of done:

- Implement `django_strawberry_framework/auth/` with `login_mutation`, `logout_mutation`, `register_mutation`, and a `current_user` query helper, each composable with the existing permissions surface.
- Mirrored tests under `tests/auth/`.
- Documented as opt-in: consumers must import explicitly; auth mutations are not injected into every schema.

### TODO-ALPHA-032-0.0.12 — Channels ASGI router (migration aid)

Priority: low (🍓 parity-required; small slice; explicit migration aid)

Severity: **low**

Status: planned

Why it matters:

- `strawberry-graphql-django` ships a small `routers.py` that builds a `ProtocolTypeRouter` over `GraphQLHTTPConsumer` and `GraphQLWSConsumer` for consumers using Channels. The module is ~30 lines but is the single import that makes ASGI / WebSocket migration painless.
- Shipping a functionally-equivalent helper lets strawberry-graphql-django migrants update one import line in their ASGI entrypoint. This card exists primarily to reduce migration friction, not to expand the API surface.

Verified in upstream:

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/routers.py` — `AuthGraphQLProtocolTypeRouter` wrapping `ProtocolTypeRouter`, `URLRouter`, `AllowedHostsOriginValidator`, `AuthMiddlewareStack`, plus `GraphQLHTTPConsumer` / `GraphQLWSConsumer`.

Architectural posture:

- The router helper must use a **distinctly-ours symbol name** (working name: `DjangoGraphQLProtocolRouter`) so the module is unambiguously ours and does not impersonate the upstream API. This respects the [`GOAL.md`](GOAL.md) non-goal "a thin wrapper around `strawberry-graphql-django`".
- Migration ergonomics are preserved by the upstream-equivalent mapping in the migration guide (`TODO-BETA-044-0.1.6`), not by copying the symbol name. A migrant changes one import line: `from strawberry_django.routers import AuthGraphQLProtocolTypeRouter` → `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`.

Definition of done:

- Implement `django_strawberry_framework/routers.py` exposing `DjangoGraphQLProtocolRouter` (final name pinned during implementation).
- `channels` is a soft dependency: top-level package import must not fail if `channels` is not installed. The helper wraps `channels` imports lazily and raises `ImportError` with an install hint when it is actually called.
- Tests under `tests/test_routers.py` exercise both the channels-present and channels-absent paths.
- Migration guide (`TODO-BETA-044-0.1.6`) gains a one-row entry in its "symbol equivalents" table mapping `AuthGraphQLProtocolTypeRouter` → `DjangoGraphQLProtocolRouter`, so the symbol rename is documented in one canonical location.

### TODO-ALPHA-033-0.0.12 — Debug-toolbar middleware

Priority: low (🍓 parity-adjacent; developer experience)

Severity: **low**

Status: planned

Why it matters:

- `strawberry-graphql-django` ships a `middlewares/debug_toolbar.py` so `django-debug-toolbar`'s SQL panel captures queries triggered by GraphQL resolvers. Without it, developers can't see the SQL hit by their queries during a `/graphql/` request.

Verified in upstream:

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/middlewares/debug_toolbar.py`.

Definition of done:

- Implement `django_strawberry_framework/middleware/debug_toolbar.py` exposing a middleware class that lets `django-debug-toolbar` capture SQL through the Strawberry view.
- `debug_toolbar` is a soft dependency.
- In-process test against a fakeshop request that emits SQL.

### TODO-ALPHA-034-0.0.12 — Test client helper

Priority: low (⚛️&🍓 parity-adjacent; developer experience)

Severity: **low**

Status: planned

Why it matters:

- `strawberry-graphql-django` ships `strawberry_django.test.client.TestClient`, a thin wrapper around `django.test.Client` that posts GraphQL requests with the right content type, parses the response, and exposes `.query(...)` / `.mutate(...)`.
- `graphene-django` ships `graphene_django.utils.testing` with `GraphQLTestCase` / `graphql_query` helpers covering the same need.
- The fakeshop live tests already do this by hand; centralizing the pattern is a small win for consumers and keeps our HTTP tests crisp.

Verified in upstream:

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/test/client.py` — `TestClient`, `AsyncTestClient`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/utils/testing.py` — `GraphQLTestCase`, `graphql_query`.

Definition of done:

- Implement `django_strawberry_framework/test/client.py` with `TestClient` / `AsyncTestClient` plus a `GraphQLTestCase` subclass for the unittest crowd.
- Live HTTP tests under `examples/fakeshop/test_query/` switch to the helper.
- Tests under `tests/test/test_client.py`.

### TODO-ALPHA-035-0.0.12 — Response-extensions debug middleware

Priority: low (⚛️ parity-adjacent; developer experience)

Severity: **low**

Status: planned; distinct from `TODO-ALPHA-033-0.0.12` (Django debug toolbar)

Why it matters:

- `graphene-django` ships a debug subsystem that exposes the executed SQL queries and raised exceptions for each GraphQL request via a `DjangoDebug` object. This is different from `TODO-ALPHA-033-0.0.12` (django-debug-toolbar SQL panel UI): graphene's mechanism is **inside the GraphQL response**, so frontend clients and Apollo DevTools can read it without the toolbar. Both mechanisms are useful and not mutually exclusive.
- A Strawberry-native equivalent is a small `SchemaExtension` that captures SQL through `django.db.connection.queries` and attaches the result to the response's `extensions` map.

Verified in upstream:

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/middleware.py` — `DjangoDebugContext`, `DjangoDebugMiddleware` (wraps cursors, captures exceptions, resolves the `_debug` object on result).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/types.py` — `class DjangoDebug(ObjectType)` with `sql: List(DjangoDebugSQL)` and `exceptions: List(DjangoDebugException)`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/sql/tracking.py` and `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/exception/formating.py` — cursor wrapping and exception serialization.

Definition of done:

- Implement `django_strawberry_framework/extensions/debug.py` as a Strawberry `SchemaExtension` that captures SQL and exceptions and attaches them to the response `extensions` map (key: `debug`).
- Off by default; opt-in via the extensions list passed to `strawberry.Schema(...)`.
- Tests under `tests/extensions/test_debug.py` against a fakeshop request that emits SQL.
- Documented as the response-side counterpart to `TODO-ALPHA-033-0.0.12`.

Files likely touched:

- `django_strawberry_framework/extensions/` (new)
- `tests/extensions/` (new)

### TODO-BETA-036-0.1.0 — Beta release (cleanup, verification, alpha → beta)

Priority: high — release card

Severity: **major** (release-blocking)

Status: planned; this is the final card in the Alpha queue and gates the alpha → beta milestone

Why it matters:

- This card is the formal cut-over from alpha (`0.0.x`) to beta (`0.1.0`). When every other Alpha card is in `DONE`, this card is the only thing left between the current state and the beta release. It exists to make the milestone explicit and to give the cleanup / verification work a place to live.
- Without a dedicated release card, the alpha → beta transition becomes an unstructured handful of doc tweaks and version bumps spread across the last few patches. Tracking it explicitly forces the parity audit and the full test pass to happen on a single named slice.

Definition of done:

- Every other Alpha card (`ALPHA-013-0.0.6` through `ALPHA-035-0.0.12` plus `ALPHA-024-0.0.9`) is in `DONE`.
- Full test pass under each supported `(Python, Django, Strawberry)` combination.
- Coverage stays at 100% for the package source tree.
- Version bumped to `0.1.0` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock`.
- `CHANGELOG.md` `[Unreleased]` block promoted to `## [0.1.0] - YYYY-MM-DD` with a one-paragraph release summary plus the cumulative Added / Changed / Fixed / Removed sections covering `0.0.6` through `0.0.12`.
- `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, and `docs/TREE.md` cross-checked against the actual shipped surface; "shipped" / "planned" status markers updated.
- Audit pass against the parity findings: every ⚛️ and 🍓 card from the two upstream audits is either `DONE` or explicitly deferred with a recorded reason.
- Tag the release in git and publish to PyPI.

Files likely touched:

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`

## To Do - Beta (1.0.0)

Cards that complete the django-graphene-filters Layer-3 richness on top of parity (`fields_class`, `aggregate_class`, `search_fields`, plus pre-stable cleanup). Each card targets its own `0.1.x` patch within the road to **1.0.0**. The final card in this column is the `1.0.0` release itself (API freeze, cleanup, verification, beta → stable cut-over). Cards in NNN order = planned ship order.

### TODO-BETA-037-0.1.1 — `FieldSet`

Priority: high for Layer 3

Status: needs spec or implementation slice

Why first:

- `FieldSet` is the smallest Layer 3 surface and can define field-selection semantics used by `DjangoConnectionField`.
- It bridges the existing `DjangoType.Meta.fields` behavior and future connection/query APIs.

Foundation-slice seam:

- `DjangoTypeDefinition.fields_class` is the forward-reserved slot the collection phase will populate.
- `Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (see also [`BACKLOG.md`](BACKLOG.md) item 38 for the `DjangoModelField` custom Strawberry field class that field-level permissions will likely require).

Definition of done:

- Add `docs/spec-fieldset.md`.
- Implement `django_strawberry_framework/fieldset.py`.
- Add `tests/test_fieldset.py`.
- Keep the API Meta-class-driven.
- Do not top-level export until the public-surface rules are satisfied.

### TODO-BETA-038-0.1.2 — `Meta.search_fields` support

Priority: high for django-graphene-filters parity

Severity: **medium**

Status: planned; gated on `TODO-ALPHA-021-0.0.8` (Filtering) and `TODO-ALPHA-023-0.0.9` (DjangoConnectionField)

Why it matters:

- `Meta.search_fields` is one of the five django-graphene-filters Layer-3 Meta keys explicitly listed in [`GOAL.md`](GOAL.md) alongside `filterset_class`, `orderset_class`, `aggregate_class`, and `fields_class`. Without it the package cannot claim full DGF parity at 1.0.0.
- Currently `search_fields` is in `DEFERRED_META_KEYS` and rejected at validation time. `TODO-BETA-042-0.1.5` (Fakeshop schema activation) explicitly carries a note to "move or defer `search_fields` before uncommenting" because of this gap.

Verified reference shape:

- `django-graphene-filters` exposes `Meta.search_fields = ("name", "description", "category__name")` — a tuple of model-field paths. The connection field gains a single `search: String` argument that fans out across the listed fields as an OR'd `icontains` filter, traversing relations through Django's standard ORM lookup syntax.

Definition of done:

- Add `docs/spec-search_fields.md`.
- Search-fields argument generation lives in `django_strawberry_framework/filters/` and reuses the same DRF-style Meta surface and argument-factory machinery as `filterset_class`.
- Single `search: String` argument surfaces on `DjangoConnectionField` consumers and produces an OR'd `icontains` queryset filter across every declared field path.
- Promote `Meta.search_fields` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the pipeline applies it end-to-end (per `BLOCKED-BETA-040-0.1.3`).
- Tests under `tests/filters/test_search_fields.py` covering single-field, relation-path, and combined-with-filterset cases.
- Live HTTP coverage under `examples/fakeshop/test_query/` exercising a search across at least one relation path.

Dependencies:

- `TODO-ALPHA-021-0.0.8` (Filtering subsystem) — the argument factory is shared.
- `TODO-ALPHA-023-0.0.9` (`DjangoConnectionField`) — the `search: String` argument surfaces on connection fields.

Files likely touched:

- `django_strawberry_framework/filters/` (search support)
- `django_strawberry_framework/types/base.py` (Meta validation; promote key)
- `tests/filters/test_search_fields.py` (new)
- `examples/fakeshop/apps/products/schema.py` (activation)

### TODO-BETA-039-0.1.3 — Aggregation subsystem

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

Lazy-resolution pipeline:

Reuses the six-layer lazy-resolution architecture spec'd in detail under `TODO-ALPHA-021-0.0.8` (Filtering subsystem). Same `LazyRelatedClassMixin`, metaclass-discovery + deferred-expansion pattern, cycle-safe `get_aggregates()` cache + recursion guard, BFS schema build, and `_dynamic_aggregateset_cache` memoization — with `RelatedAggregate` substituted for `RelatedFilter` and `AggregateSet` for `FilterSet`.

One key difference from Filtering / Ordering: aggregates emit **output types** (`strawberry.type`-decorated), not input types. The Strawberry adaptation in Layer 5 (the BFS schema build) accordingly uses `strawberry.lazy("django_strawberry_framework.aggregates._registry.{TargetAggregateSet}OutputType")` for forward references between aggregate output types. The `compute` / `acompute` split from `AdvancedAggregateSet` runs *after* the type graph is built — the sync/async dispatch happens at resolver-invocation time, not at finalize time.

Synchronization runs inside `finalize_django_types()` phase 2.5 alongside filters and orders; all three subsystems share the same finalizer pass, with `aggregate_class` resolution coming last so it can reference filter-input types when an aggregate is filtered before computation.

Reference symbols in the Graphene checkout: `django_graphene_filters/aggregateset.py`, `aggregate_types.py`, `aggregate_arguments_factory.py` — same lazy-resolution shape as the filter trio, swapped for output-type emission.

Definition of done:

- Add `docs/spec-aggregates.md`.
- Add `django_strawberry_framework/aggregates/`.
- Add mirrored `tests/aggregates/`.
- Promote `Meta.aggregate_class` only when aggregation is applied end-to-end.
- Decide result type naming and grouping semantics.
- Validate generated queryset aggregation paths.
- Keep aggregation declarations composable with filters, ordering, and connection field behavior.

### TODO-BETA-041-0.1.4 — Stable choice enum naming override

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

### TODO-BETA-042-0.1.5 — Fakeshop GraphQL schema activation

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

### TODO-BETA-044-0.1.6 — Migration and adoption guides

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
- README and `GLOSSARY.md` link to the migration docs.
- Guides distinguish shipped migration steps from planned Layer 3 migration targets.

Files likely touched:

- future migration docs under `docs/`
- `docs/README.md`
- `docs/GLOSSARY.md`


### TODO-STABLE-045-1.0.0 — Stable release (API freeze, cleanup, verification, beta → stable)

Priority: critical — release card

Severity: **major** (release-blocking; API freeze starts here)

Status: planned; this is the final card in the Beta queue and gates the beta → stable milestone

Why it matters:

- `1.0.0` is the API freeze. After this card lands, every public symbol — `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `finalize_django_types`, `DjangoConnectionField`, `DjangoListField`, mutation classes, filter / order / aggregate / fieldset surfaces, and the Meta key vocabulary — is bound by strict SemVer. Breaking changes from this point forward require a major bump.
- The release card is where we audit, finalize, and commit to that contract. Without a dedicated card, "1.0 is stable" becomes a soft promise spread across N patches; making it a single card means the audit happens before the version tag goes out.

Definition of done:

- Every other Beta card (`TODO-BETA-037-0.1.1` through `TODO-BETA-044-0.1.6` plus `BLOCKED-BETA-040-0.1.3` and `BLOCKED-BETA-043-0.1.5`) is in `DONE`.
- API surface audit: top-level `__all__` confirmed stable; every public symbol documented; no `# experimental` markers in shipped code; no `_private` symbols accidentally referenced from docs.
- SemVer policy committed in CHANGELOG header: every release after `1.0.0` follows MAJOR / MINOR / PATCH rules strictly; pre-`0.1.0` deprecation shims removed entirely.
- Full async + sync coverage matrix validated; no `sync_to_async` workarounds remain on any resolver path.
- Security review: input-validation surfaces (mutations, filters, GlobalID decoding) audited for injection / authorization gaps.
- Version bumped to `1.0.0` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock`.
- `CHANGELOG.md` `[Unreleased]` block promoted to `## [1.0.0] - YYYY-MM-DD`. Release summary mentions the parity story (graphene-django + strawberry-graphql-django), the django-graphene-filters depth, and the SemVer policy switch.
- Final pass through `BACKLOG.md` to mark differentiators that landed and refresh the post-1.0 roadmap.
- Tag, publish to PyPI, write the 1.0 announcement.

Files likely touched:

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`
- `BACKLOG.md`

## Blocked

### BLOCKED-ALPHA-024-0.0.9 — Full Relay story (Node + Connection + Root + validation)

Priority: high

Parity: ⚛️&🍓 required (both upstreams ship full Relay Node + Connection + Root field surfaces).

Severity: **major** — Relay is the canonical GraphQL identity + pagination spec; the foundation shipped in `DONE-011-0.0.5` only becomes useful end-to-end when paired with this card's Connection + Root + validation surface.

Status: blocked on `TODO-ALPHA-023-0.0.9` (`DjangoConnectionField`). When the connection field lands, this card unblocks and ships in the same release. The post-`1.0.0` "Relay magic" differentiators (type-rename GlobalID migrations, polymorphic connections, stable cursors, refetchable containers, permission-aware cursor decoding) live separately in [`BACKLOG.md`](BACKLOG.md) item 39 — they extend this story rather than block it.

This is the umbrella spec for the **complete Relay surface at `0.0.9`** — Node foundation + Connection + Root entry points + schema validation + test helpers. The Node half shipped in `DONE-011-0.0.5`; the Connection half is its own implementation slice (`TODO-ALPHA-023-0.0.9`); this card carries the connective tissue that ties them together into one end-to-end Relay story.

Resolved blockers (shipped in `DONE-011-0.0.5`):

- ~~`Meta.interfaces` design~~ — `Meta.interfaces` accepted end-to-end for any Strawberry interface; `(relay.Node,)` activates the Node foundation.
- ~~`GlobalID` mapping decision~~ — Strawberry-supplied `id: GlobalID!` from the Relay interface replaces the synthesized `id: int!`; Django primary key remains projected as a connector column for the optimizer (Decision 2 of [`docs/SPECS/spec-011-relay_interfaces-0_0_5.md`](docs/SPECS/spec-011-relay_interfaces-0_0_5.md)).
- ~~Default `resolve_*` injection~~ — `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes` defaults injected when `relay.Node` is in `Meta.interfaces`; consumer overrides preserved via Strawberry's `__func__` identity test.
- ~~`is_type_of` injection~~ — Unconditional on every `DjangoType`; consumer-declared `is_type_of` preserved.
- ~~`CompositePrimaryKey` rejection~~ — Django 5.2+ composite-pk models raise `ConfigurationError` at finalization with the documented escape hatch (`id: relay.NodeID[...]` annotation).

Remaining work (unblocks when `TODO-ALPHA-023-0.0.9` lands):

#### Goal 1: Root Node entry points

Schema-level entry points for *"give me any Node by GlobalID"* — required by Relay clients (Apollo, Relay Compiler) for refetch and cache reconciliation. Two fields:

- `node(id: GlobalID!): Node` — single-object refetch. Decodes the GlobalID, dispatches to the type's `resolve_node`, returns the resolved object. Returns `null` if the GlobalID decodes to a type/ID the requesting user can't see (respects `get_queryset`).
- `nodes(ids: [GlobalID!]!): [Node]!` — batch refetch. Decodes each GlobalID, dispatches per-type to `resolve_nodes` (batched), returns results in input order. Missing IDs become `null` entries (preserves positional correspondence).

Both ship as `DjangoNodeField` / `DjangoNodesField` re-exports in the package public surface. Consumers attach them to their root `Query` type by declaration:

```python path=null start=null
@strawberry.type
class Query:
    node:  Node           = DjangoNodeField()
    nodes: list[Node]     = DjangoNodesField()
```

Both fields cooperate with `TODO-ALPHA-025-0.0.9` (connection-aware optimizer) so the per-type `get_queryset` is applied at decode time, not after-the-fact filtering — a Relay-client refetch on a hidden row returns `null` cheaply, not a hidden row that the post-filter would have removed.

#### Goal 2: Relation-as-Connection upgrade

The shipped foundation exposes reverse-FK and M2M relations as `list[T]`. For Relay-compatible schemas, those relations need a *Connection* counterpart so clients can paginate inside a parent object's relation set. Two paths:

- **Implicit upgrade** (default): every `DjangoType` whose `Meta.interfaces` includes `relay.Node` automatically exposes its reverse-FK and M2M relations as Connections in addition to the existing `list[T]` shape. Field names follow a stable convention (`itemsConnection: ItemConnection` alongside `items: list[Item]`).
- **Explicit-only**: consumers who want only Connections (or only lists) on a relation declare `Meta.relation_shapes = {"items": "connection"}` (or `"list"`, or `"both"` — `"both"` is the default for Relay types).

The Connection counterpart inherits the parent's `get_queryset` (so a reverse-FK Connection over `category.items` filters the items by the parent category AND by the type's `get_queryset` policy) and integrates with filters (`TODO-ALPHA-021-0.0.8`) and orders (`TODO-ALPHA-022-0.0.8`) when declared on the related `DjangoType`.

#### Goal 3: Cursor pagination math

The `DjangoConnectionField` implementation (`TODO-ALPHA-023-0.0.9`) carries the actual cursor algorithm; this card pins the **contracts** the connection field must satisfy:

- **Cursor format**: opaque base64-encoded payload by default (`b64("offset:N")`). Documented as opaque — clients must not parse it. `Meta.cursor_field` for stable column-based cursors is **out of scope** for this card; lives in BETTER item 39 sub-feature 3.
- **Required arguments**: `first: Int`, `after: String`, `last: Int`, `before: String`. Backward pagination (`last`/`before`) is required by the Relay spec.
- **`pageInfo`**: emits the four standard fields (`hasNextPage`, `hasPreviousPage`, `startCursor`, `endCursor`) with correct semantics — including the spec-mandated *"the connection MUST resolve `hasNextPage` correctly even when the consumer didn't request it"* invariant.
- **Edge cases**: `first: 0` returns empty edges + `pageInfo`. `first: N` with N > remaining rows returns the actual remainder. `after` cursor for a row that no longer exists falls through to the next existing row (no error). Both `first` and `last` in the same query is rejected with a typed error.
- **`totalCount`**: an opt-in field on every Connection (`Meta.connection = {"total_count": True}`). When selected, runs `qs.count()` on the *unpaginated* queryset (post-filter, pre-slice). Documented as the canonical Relay-compatible total-count surface.

#### Goal 4: Filter / Order integration

A Connection without filters is half a feature. The connection field accepts:

- `filter: <Type>FilterInput` — generated from `Meta.filterset_class` (composes with `TODO-ALPHA-021-0.0.8`)
- `orderBy: [<Type>OrderInput!]` — generated from `Meta.orderset_class` (composes with `TODO-ALPHA-022-0.0.8`)
- `search: String` — generated from `Meta.search_fields` (composes with `TODO-BETA-038-0.1.2` — note: search is `1.0.0` scope, ships after `0.1.0`; until then, search arg is absent)

The cursor algorithm runs *after* filter + order are applied, so cursors are stable across the filtered+ordered queryset. Changing `orderBy` between paginated requests is **documented as invalidating cursors** (consumers should treat order change as a fresh pagination cycle, not a continuation).

#### Goal 5: Permission integration

Relay refetch over `node(id:)` is a privacy hot spot — clients can construct any GlobalID and ask the server to resolve it. The Node entry points MUST:

- decode the GlobalID server-side (never trust the client's claim of which type the ID belongs to)
- dispatch to the resolved type's `resolve_node` (which honors `cls.get_queryset(qs, info)`)
- return `null` for rows the user can't see (not an error — the Relay spec requires `null`, not an exception)
- never reveal *existence* of hidden rows through error timing or status codes

Composes with `TODO-ALPHA-026-0.0.10` (Permissions subsystem). Permission-aware cursor decoding (cursors minted under one user's privileges shouldn't reveal rows under another's) is **out of scope** for this card — lives in BETTER item 39 sub-feature 6.

#### Goal 6: Schema-validation diagnostics

Targeted `ConfigurationError` messages when consumers misuse the Relay vocabulary:

- `relay.GlobalID`, `relay.NodeID[...]`, `relay.Connection`, `relay.ListConnection`, `relay.Edge`, `relay.PageInfo` in `Meta.interfaces` → rejected with a message naming the helper and explaining it's a scalar / annotation / field-type rather than an interface.
- Non-Strawberry-interface classes in `Meta.interfaces` → rejected at validation with the offending class name.
- `Meta.connection = {...}` declared on a type that doesn't include `relay.Node` in `Meta.interfaces` → rejected with a message suggesting either remove the `connection` key or add `relay.Node` to interfaces.
- A `DjangoNodeField()` query field on a schema with **no** `DjangoType`s declaring `relay.Node` → rejected at finalization with *"node lookup configured but no Node types registered."*

#### Goal 7: Test helpers

Basic helpers for HTTP-test fixtures, in a new `django_strawberry_framework.test.relay` submodule:

```python path=null start=null
from django_strawberry_framework.test.relay import global_id_for, decode_global_id

item_gid = global_id_for(ItemType, item.id)
response = client.query("{ node(id: $id) { ... on Item { name } } }", variables={"id": item_gid})

# decode_global_id(item_gid) → ("Item", "42") for assertions
```

Advanced helpers (cursor encoding for paginated test fixtures, polymorphic-connection fixture generation) are **out of scope** for this card; deferred to BETTER item 39's test-helper sub-section.

#### Goal 8: Fakeshop activation

The library app already has live `/graphql/` acceptance tests for the Node foundation (DONE-011); the product-catalog aspirational schema in `examples/fakeshop/apps/products/schema.py` activates as part of `TODO-BETA-042-0.1.5` (Fakeshop activation) but ITS **Relay surface** lights up here:

- `node(id:)` and `nodes(ids:)` resolve real product / category / item / entry GlobalIDs
- Reverse-FK and M2M relations on those types expose their Connection counterparts
- Live HTTP tests under `examples/fakeshop/test_query/` exercise the full Relay query shape (refetch, paginated connection, cursor round-trip, `totalCount`)

The fakeshop activation itself depends on Layer-3 subsystems (filters, orders, aggregates, fieldsets, search) so the *full* Relay-shaped schema lights up at `1.0.0`. This card delivers the **mechanics** that activation depends on.

#### Out-of-scope (lives in `BACKLOG.md` item 39)

Explicitly *not* in this card; they're post-`1.0.0` Relay-magic differentiators:

- Type-rename GlobalID migrations (Django-migrations-style history that lets old-format IDs decode alongside new)
- Polymorphic connections (`Connection[Interface]` with auto-dispatched concrete types per edge)
- `Meta.cursor_field` for stable cursors keyed on a deterministic column
- Auto-upgrade reverse FK / M2M to Connection based on a row-count threshold
- Refetchable container schema metadata for `useRefetchableFragment`
- Permission-aware cursor decoding (cursor decode re-runs `get_queryset` so privileged cursors don't leak)

These all build on `BLOCKED-ALPHA-023`'s mechanics. Shipping `BLOCKED-ALPHA-023` first means BETTER item 39 becomes incremental enhancement, not foundational work.

#### Dependencies

- `TODO-ALPHA-023-0.0.9` (`DjangoConnectionField`) — **hard dependency**; this card unblocks when 023 lands.
- `TODO-ALPHA-021-0.0.8` (Filtering subsystem) — soft dependency for the filter argument on Connections.
- `TODO-ALPHA-022-0.0.8` (Ordering subsystem) — soft dependency for the orderBy argument on Connections.
- `TODO-ALPHA-025-0.0.9` (Connection-aware optimizer planning) — ships in parallel; the Node entry points and the relation-as-Connection upgrade both rely on the walker recognizing `edges { node { ... } }`.
- `TODO-ALPHA-026-0.0.10` (Permissions subsystem) — soft dependency; the Node entry points respect `get_queryset` immediately and integrate with declared permissions when 023 lands.

#### Definition of done

- New spec: `docs/spec-relay_connection.md` covering all eight goals above with worked examples and decision rationale.
- `DjangoNodeField` and `DjangoNodesField` exported from the package public surface; both wired through the registry's GlobalID decode path and the per-type `get_queryset`.
- Reverse-FK and M2M relations on `relay.Node`-implementing types expose their Connection counterparts; `Meta.relation_shapes` opt-out documented.
- Cursor pagination math passes the Relay-spec test suite for `first`/`after`/`last`/`before`/`pageInfo` edge cases.
- `Meta.connection = {"total_count": True}` adds a `totalCount` field that runs `qs.count()` on the unpaginated post-filter queryset.
- Filter / order arguments accepted on Connection fields when the corresponding `*_class` is declared on the type.
- Permission-aware Node lookup: `node(id:)` returns `null` for hidden rows; no existence leak via error timing.
- Six schema-validation diagnostics from Goal 6 raise `ConfigurationError` with the documented messages.
- `django_strawberry_framework.test.relay` module exposes `global_id_for(type_cls, id)` and `decode_global_id(gid)`.
- The fakeshop `library` HTTP test suite gains Relay-shaped queries (refetch, paginated connection, cursor round-trip, `totalCount`). Fakeshop `products` activation lights up the full Relay surface as part of `TODO-BETA-042-0.1.5`.
- 100% coverage across the new code paths; tests pin both happy paths and every validation failure.

#### Files likely touched

- `django_strawberry_framework/connection.py` — main implementation (shipped as part of `TODO-ALPHA-023-0.0.9`)
- `django_strawberry_framework/relay.py` (new) — `DjangoNodeField`, `DjangoNodesField`, GlobalID decode dispatch
- `django_strawberry_framework/types/base.py` — `Meta.connection` / `Meta.relation_shapes` validation
- `django_strawberry_framework/types/finalizer.py` — auto-upgrade reverse-FK / M2M to Connection
- `django_strawberry_framework/test/relay.py` (new) — test helpers
- `tests/test_relay_node_field.py`, `tests/test_relay_connection.py` (new)
- `examples/fakeshop/test_query/test_library_api.py` — Relay-shape HTTP tests
- `examples/fakeshop/apps/products/schema.py` — Relay surface activation (lit up at fakeshop activation time)
- `docs/spec-relay_connection.md` (new)
- `docs/GLOSSARY.md` — Relay surface description

#### Unblocks

- Relay node refetch from Apollo / Relay Compiler clients (the *"Relay just works"* end state for `1.0.0`)
- Fakeshop product-catalog Relay activation (Goal 8)
- Per-type `useFragment` / `useRefetchableFragment` patterns (mechanics; the schema-side `@refetchable` directive support lives in BETTER item 39 sub-feature 5)
- Every BETTER item 39 sub-feature builds on this card's mechanics

### BLOCKED-BETA-040-0.1.3 — Layer 3 Meta key promotion

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

### BLOCKED-BETA-043-0.1.5 — Product-catalog Layer 3 HTTP GraphQL tests

Blocked by:

- activating the product-catalog fakeshop GraphQL schema
- connection/query fields and other Layer 3 public surfaces

Current state:

- The library app already has live `/graphql/` acceptance tests under `examples/fakeshop/test_query/`.
- Future product-catalog HTTP tests should use the same placement and schema-reload pattern.
- In-process `schema.execute_sync` tests still go under `examples/fakeshop/tests/`.

## Done

### DONE-001-0.0.1 — DjangoType core foundation

Parity: ⚛️&🍓 required (`DjangoObjectType` is the namesake primitive graphene-django ships; `@strawberry_django.type` is the strawberry-graphql-django equivalent).

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

Parity: 🍓 required (strawberry-graphql-django ships a heavy optimizer extension; graphene-django has only `select_related_field` — 🍓 required, ⚛️ parity-adjacent).

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

- Shipped behavior is consolidated into `docs/GLOSSARY.md`; source/tests are the truth for optimizer behavior.

### DONE-003-0.0.3 — Optimizer beyond slices B1-B8

Parity: 🍓 required (continuation of DONE-002's optimizer lineage; ⚛️ parity-adjacent).

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
- `docs/GLOSSARY.md` describes shipped, planned, deferred, and alpha-constrained capabilities.
- `docs/TREE.md` preserves detailed package/test tree responsibilities.

Evidence:

- `docs/README.md`
- `docs/GLOSSARY.md`
- `docs/TREE.md`

Notes:

- User-facing docs avoid internal slice shorthand; maintainer docs can still use it where useful.

### DONE-005-0.0.4 — 0.0.4 onboarding docs and spec consolidation

Priority: completed docs cleanup

Scope:

- Root `README.md` is the canonical documentation map and operational entry point.
- `docs/README.md` is code-first: quickstart, three-minute path, optimizer behavior, and status.
- `docs/GLOSSARY.md` is the capability catalog with value-led optimizer language and comparison table.
- `docs/TREE.md` is the detailed layout/test-tree reference.
- `CHANGELOG.md` is condensed and no longer relies on design-doc pointers for release context.
- Completed design-doc content is folded into durable docs, while remaining specs preserve design history and follow-up work.

Evidence:

- `README.md`
- `docs/README.md`
- `docs/GLOSSARY.md`
- `docs/TREE.md`
- `CHANGELOG.md`

Notes:

- Future in-flight design docs use the `docs/spec-<NNN>-<topic>-<0_0_X>.md` convention (NNN matches the KANBAN card number; see `docs/builder/BUILD.md` "Spec filename pattern"), then get folded into durable docs when shipped.

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
- Documentation sweep: `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, `TODAY.md`, and `CHANGELOG.md`.
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
- Kept the remaining scalar override skip documented as a separate scalar-field concern under `DONE-015-0.0.6`.

Evidence:

- `tests/types/test_definition_order.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_definition_order.py`
- `DONE-015-0.0.6`

### DONE-008-0.0.4 — 0.0.4 version and release alignment

Priority: completed release alignment

Status: complete.

Scope:

- Package metadata, runtime version, lockfile, tests, and changelog now agree on `0.0.4`.
- The changelog entry is condensed for the alpha release and covers the actual commit range through 2026-05-08.

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

Parity: ⚛️&🍓 required (both upstreams ship Relay Node interfaces and Node foundation; this card shipped our 🍓-shaped Relay Node integration).

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
- `docs/GLOSSARY.md`
- `docs/README.md`
- `TODAY.md`
- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`

Notes:

- Borrowed patterns from `strawberry-django` (spec "Borrowing posture", Decision 3). The override discriminator triad stays distinct across the three injection sites: `__dict__` membership for `is_type_of`, tuple membership for id suppression, `__func__` identity for the four `resolve_*` defaults.
- `Meta.interfaces` is the first `0.0.4`-reserved `DjangoTypeDefinition` slot that ships end-to-end through finalizer phase 2.5; subsequent Layer 3 subsystems plug into the same architectural seam.

### DONE-012-0.0.6 — `FieldMeta` single-source-of-truth consolidation and mirror retirement

Priority: completed metadata-architecture cleanup (will release with `0.0.6`)

Status: complete; in main, pending the `0.0.6` release.

Why it mattered:

- Three reader sites were re-deriving relation shape via `relation_kind(field)` + raw `getattr(field, ...)` instead of reading the `FieldMeta` already on `DjangoTypeDefinition.field_map` — duplicating logic and creating drift surface for any future relation-flag addition.
- `DjangoType.__init_subclass__` was writing legacy class-attribute mirrors (`cls._optimizer_field_map`, `cls._optimizer_hints`) that survived `registry.clear()`, then four optimizer sites read those mirrors instead of the canonical `DjangoTypeDefinition`. Two parallel sources of field metadata with no enforced consistency.

Scope:

- **SSoT consolidation.** Three reader sites now read `FieldMeta` from the canonical source on `DjangoTypeDefinition.field_map`:
  - `django_strawberry_framework/types/base.py:_record_pending_relation`
  - `django_strawberry_framework/types/converters.py:resolved_relation_annotation`
  - `django_strawberry_framework/types/resolvers.py:_make_relation_resolver`
- **Mirror retirement.** `DjangoType.__init_subclass__` no longer writes the legacy class-attribute mirrors. The optimizer reads from `registry.get_definition(type_cls)` directly at all four former reader sites:
  - `optimizer/walker.py:_resolve_field_map`
  - `optimizer/walker.py:_walk_selections` (hints read)
  - `optimizer/extension.py:_collect_schema_reachable_types`
  - `optimizer/extension.py:check_schema`
- All `TODO(spec-fieldmeta-*)` source anchors removed.
- 100% package coverage maintained; no consumer-visible API change.

Evidence:

- Commit `de35a62` (`refactor(types,optimizer): consolidate metadata onto DjangoTypeDefinition`).
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/extension.py`
- `CHANGELOG.md` (under `[Unreleased] → Changed`)

Notes:

- Originally tracked as `BACKLOG.md` item 35 ("`FieldMeta` single-source-of-truth consolidation and mirror retirement"). Promoted to a DONE card and removed from `BACKLOG.md` when the work shipped — per `BACKLOG.md`'s "graduate into a `KANBAN.md` card when scheduled" workflow. This is the first `BACKLOG.md` item to graduate; the precedent for shipped items: strike-through with SHIPPED status is fine while the item awaits a release; once a release is imminent, move the item to a `KANBAN.md` `DONE` card and delete it from `BACKLOG.md` so the strategic-differentiation file doesn't keep pointing at completed architecture debt.
- The consolidation eliminates ~7 sites of duplicated relation-shape logic and removes legacy class-attribute residue that previously survived `registry.clear()`. Single source of truth for field metadata reduces drift surface whenever Django adds a new relation flag or changes a descriptor attribute.
- Internal refactor only; no `Meta` key changes, no public surface changes, no consumer-visible behavior changes. Existing tests pass without modification.

### DONE-013-0.0.6 — Deferred scalar conversions

Parity: ⚛️&🍓 required (both upstreams ship scalar conversion for `BigIntegerField`, `JSONField`, `HStoreField`, `ArrayField`, etc.).

Slice-by-slice scope (per `docs/SPECS/spec-013-deferred_scalars-0_0_6.md`):

- Public `BigInt` scalar (`django_strawberry_framework/scalars.py`, `NewType`-based) with the Strawberry class-direct-to-`scalar()` `DeprecationWarning` suppressed at the definition site so consumers see no warning at import time.
- Strict `BigInt` parser via regex `^(0|-?[1-9][0-9]*)$` — rejects `bool`, `float`, empty / whitespace-padded strings, non-decimal strings, underscores, plus signs, leading zeroes, `-0`, and Unicode digits.
- Strict `BigInt` serializer — rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`.
- `BigIntegerField → BigInt` and `PositiveBigIntegerField → BigInt` in `SCALAR_MAP`. `BigAutoField` preserved as `int` (no override recourse at the time of DONE-013; annotation-override recourse now available via `DONE-015-0.0.6`).
- `JSONField → strawberry.scalars.JSON` in `SCALAR_MAP`.
- `ArrayField` and `HStoreField` mapped via sentinel-guarded branches in `convert_scalar`. `HStoreField` not added to `SCALAR_MAP`.
- `ArrayField` rejects nested arrays and outer `choices` with `ConfigurationError`.
- `SCALAR_MAP`'s declared value type widened from `dict[type[models.Field], type]` to `dict[type[models.Field], Any]`.
- `BigInt` added to `django_strawberry_framework.__all__`; `tests/base/test_init.py`'s pinned `__all__` and `__version__` assertions updated.
- Atomic version-bump quintet: `pyproject.toml`, `__init__.py`, `tests/base/test_init.py`, `docs/GLOSSARY.md` package-version line, `uv.lock`.
- 100% coverage via `tests/test_scalars.py` (new flat file) and `tests/types/test_converters.py` (extended). Includes a `test_package_import_does_not_emit_strawberry_deprecation_warning` guard so future regressions to the suppression are explicit.
- Docs: `docs/GLOSSARY.md`, `docs/README.md`, `README.md`, `docs/TREE.md`, `TODAY.md`, `CHANGELOG.md`.

Design notes carried into `0.0.6`:

- The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` is suppressed at the definition site (tight `warnings.catch_warnings()` filter). The package import surface is therefore clean. Migration to a `StrawberryConfig.scalar_map`-based design is roadmapped as `WIP-ALPHA-020-0.0.7` — that path is a real public-API change (consumers using `BigInt` directly will merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`), not an internal-only refactor.

### DONE-014-0.0.6 — Multiple DjangoTypes per model with `Meta.primary`

Parity: 🍓 parity-adjacent (strawberry-graphql-django has an implicit primary-type concept via `is_type_of`; graphene-django does not ship this primitive — adjacent rather than required on either side).

Slice-by-slice scope (per `docs/spec-014-meta_primary-0_0_6.md`):

- Registry stores multiple types per model (`_types: dict[Model, list[Type]]`).
- New `Meta.primary: bool` flag (default `False`); validated in `_validate_meta`.
- `registry.register(..., *, primary: bool = False) -> bool` and
  `registry.register_with_definition(..., *, primary=...)` accept the flag.
  `register()` now returns `bool` indicating whether state was added; drives
  snapshot-restore rollback in `register_with_definition`.
- New registry surface: `primary_for(model)`, `types_for(model)`,
  `models_with_multiple_types()`.
- `registry.get(model)` returns the primary if declared, else the single
  registered type, else `None`. Multiple types with no primary is an
  ambiguous-pending state that the finalizer audits.
- `finalize_django_types()` runs `audit_primary_ambiguity()` first: any
  model with `>=2` registered types and no primary raises
  `ConfigurationError` naming the model and every registered class plus an
  actionable fix sentence.
- Two primary types for the same model: rejected at registration time
  with message `"<class> is already declared primary as <existing>"`.
- Relation conversion in `types/base.py` defers all **auto-synthesized**
  relation annotations to `finalize_django_types()` (eager-bind shortcut
  removed; eliminates the secondary-registered-before-source-before-
  primary import-order trap). The existing `consumer_authored_fields`
  short-circuit is preserved, so direct relation annotations (`category:
  AdminCategoryType`) and assigned `strawberry.field` resolvers continue
  to bypass synthesis entirely and may target a secondary `DjangoType`.
  `types/converters.py` and `types/finalizer.py` resolve auto-synthesized
  relations to the primary at finalize time.
- Optimizer planning threads the resolved origin Strawberry type from
  `optimizer/extension.py` through `plan_optimizations` to the walker's
  root `_resolve_field_map(model, source_type=origin)` call. Root planning
  uses the resolver's actual return type; nested relation steps continue
  to use `registry.get(related_model)` (the primary). Plan cache key
  includes the origin type so primary-return and secondary-return
  resolvers on the same model do not share a cached plan.
- Schema audit (`optimizer/extension.py`) iterates every reachable
  registered type via `registry.iter_types()` and dedupes warning
  collection. Secondary types whose relation fields the primary does not
  expose are still audited; identical-string duplicate warnings from
  overlapping field maps are collapsed.
- `model_for_type` continues to work for any registered type so
  secondary-type resolvers stay planable.
- `DjangoTypeDefinition` gains `primary: bool = False`.
- 100% coverage across `tests/test_registry.py`, `tests/types/test_base.py`,
  `tests/test_registry.py` / `tests/types/test_definition_order.py`
  (the existing finalize-test hosts), `tests/types/test_converters.py`
  (the existing relation-conversion host), and `tests/optimizer/`.

Design notes carried into `0.0.6`:

- Single-type-no-primary stays backward compatible: `registry.get(model)`
  still returns the lone type without requiring an explicit `primary` flag.
- `Meta.primary` is a per-class declaration, not a registry-level
  `set_primary(Model, Type)` mutation — keeps the contract immutable
  after `__init_subclass__` runs.
- Already-shipped consumer relation overrides (direct annotation
  `category: AdminItemType` and assigned `category = strawberry.field(...)`)
  stay in scope and are preserved by this card via the existing
  `consumer_authored_fields` short-circuit — they may legitimately
  target a secondary `DjangoType` after `Meta.primary` ships. A NEW
  declarative override API (e.g., `Meta.field_types = {...}`) is the
  `DONE-015-0.0.6 — Consumer override semantics` design space and
  is out of scope here.

### DONE-015-0.0.6 — Consumer override semantics (scalar fields)

Parity: ⚛️&🍓 required (both upstreams support consumer-authored scalar field overrides on model-backed types).

Slice-by-slice scope (per `docs/SPECS/spec-015-consumer_overrides_scalar-0_0_6.md`):

- `DjangoType.__init_subclass__` collected `consumer_annotated_scalar_fields`
  parallel to `consumer_annotated_relation_fields`. Annotation-only scalar
  overrides (e.g., `description: int` shadowing an auto-synthesized `str`)
  are added to the unified `consumer_authored_fields` frozenset and skip
  auto-synthesis in `_build_annotations`'s scalar branch via the existing
  `if field.name in consumer_authored_fields: continue` short-circuit.
- `DjangoTypeDefinition` gained `consumer_annotated_scalar_fields: frozenset[str]`.
- The previously-skipped `test_consumer_annotation_overrides_synthesized`
  landed as `test_annotation_only_scalar_field_override_wins_over_synthesized`
  in `tests/types/test_definition_order.py` alongside the three relation
  overrides and the assigned-scalar override. The four-corner matrix
  (relation × annotation, relation × assigned, scalar × annotation,
  scalar × assigned) is symmetric and complete.
- End-to-end test pinned the override surviving `strawberry.type(...)`
  decoration and showing up in the GraphQL schema with the consumer's type
  (unwrapped through `NON_NULL` for non-nullable Django columns).
- **Consumer annotation overrides are authoritative.** `_build_annotations`'s
  scalar short-circuit bypasses every `convert_scalar` validation and side
  effect for an overridden field: unsupported-field-type rejection,
  grouped-choices rejection, `ArrayField` nested-array / outer-`choices`
  rejection, `null=True` widening, and choice-enum registration into the
  shared `(model, field_name)` cache. The contract matches the existing
  relation-annotation override path (which also bypasses `convert_relation`
  entirely) and treats annotation override as the consumer's escape from
  auto-conversion. `Meta.exclude` and annotation override are now parallel
  recourses for unsupported scalar fields. Cross-type cache behavior was
  pinned by an explicit test: two `DjangoType`s on the same `choices=`
  column where one overrides and one does not get the fresh enum from
  the non-overriding type alone (the overriding type's GraphQL surface
  uses the consumer's annotation; the cache is populated only by the
  non-overriding type's `convert_scalar` call).
- **`relay.Node` `id` collision rejected at type-creation time.** A consumer
  who writes `id: <T>` (where `<T>` is not `relay.NodeID[...]`) or assigns
  any `id = <StrawberryField>` on a `DjangoType` with
  `Meta.interfaces = (relay.Node,)` now raises `ConfigurationError` from
  `__init_subclass__`. The annotation-side error points at
  `relay.NodeID[<pk_type>]` and `GlobalID`; the assigned-side error
  points at `relay.NodeID[<pk_type>]`, `@classmethod resolve_id`, and a
  **resolver-backed sibling-field workaround** (e.g.,
  `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`
  for the field-level GraphQL metadata use case — the rev4 M1 ban on
  `id = <StrawberryField>` on Relay-Node-shaped types eliminated the
  only path for attaching `description`/`deprecation_reason`/
  `directives` to the Relay-supplied `id` field; rev6 M1 documented
  the sibling-field workaround and rev7 M2 corrected the example
  from the metadata-only `display_id: ID = strawberry.field(description="…")`
  shape — which would build but fail at query time because Strawberry's
  default resolver looks up `display_id` as an attribute on the
  returned Django model instance — to the resolver-backed form that
  carries the metadata AND defines a value source). Without the guard
  the consumer would have seen a Strawberry-side `ValueError` only at
  `strawberry.Schema(...)` construction, which obscured the source.
  The guard is narrow: it fires only when the consumer authored an
  `id` entry on a Relay-Node-shaped type AND the annotation is not a
  `relay.NodeID[...]`-marked annotation. Detection uses
  `typing.get_type_hints(cls, include_extras=True)` so direct, PEP
  563 / `from __future__ import annotations`, and explicit-string
  forms are all resolved against the consumer's module globals; the
  fail-soft branch covers two sub-cases — id-itself-failed-to-
  resolve (rev7 H1: accept only when the raw string matches the
  token-shaped regex `(?:^|\.)NodeID\[`, so prefixed-substring
  lookalikes like `"NotNodeID[int]"` are rejected) and id-resolved-
  but-sibling-failed (rev6 H1: fall back to `_has_node_id_marker(raw)`
  on the already-resolved object so directly-resolved `id:
  relay.NodeID[int]` alongside a forward-referenced relation
  annotation is accepted). The fail-soft accept window for unresolved
  NodeID-shaped strings is package-level suppression only; Strawberry's
  downstream schema construction also resolves the string and may
  still error if the consumer's module globals don't expose `relay`
  (rev7 H1). `id: relay.NodeID[int]` and `id: "relay.NodeID[int]"`
  (the documented escape hatch in direct and stringified forms, with
  `relay` importable at module scope) are accepted end-to-end; non-
  `id` consumer scalar overrides (e.g., `description: int`, or `code:
  str` on a model with `code` as pk) pass through unchanged;
  **inherited `id` annotations on a subclass slip past the guard at
  class-creation time and are silently handled by `_build_annotations`'s
  pk-suppression branch** (rev6 L1 + rev7 M1: the guard does not
  walk the MRO, but pk-suppression strips the synthesized `id`
  annotation for any Relay-Node-shaped type and the post-merge
  reassignment leaves the child without an `id` key; Strawberry
  applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()`
  falls back to `"pk"` — schema construction succeeds).
- No new public API. No `Meta.field_overrides = {...}`-style key. Opt-out
  / removal continues to go through `Meta.exclude`. Field description /
  deprecation / default continues to go through the assigned
  `strawberry.field(...)` path that shipped in `0.0.5`.
- 100% coverage was reached across `tests/types/test_definition_order.py`
  (the override-contract host, where the core + Relay-collision +
  cross-type-cache tests live) and `tests/types/test_converters.py`
  (the converter test host, where the nested-`ArrayField` bypass test
  lives by default per the rev6 L3 placement decision).

Design notes carried into `0.0.6`:

- The four `consumer_*_fields` sets on `DjangoTypeDefinition`
  (`consumer_annotated_relation_fields`, `consumer_assigned_relation_fields`,
  `consumer_annotated_scalar_fields`, `consumer_assigned_scalar_fields`) are
  the introspection surface. The unified `consumer_authored_fields` is the
  single short-circuit input for `_build_annotations`.
- Resolver / metadata overrides for scalars stay on the assigned
  `strawberry.field(...)` path — the consumer writes
  `description = strawberry.field(resolver=..., description="...", deprecation_reason=...)`
  and `_consumer_assigned_fields` already routes it through the
  `consumer_assigned_scalar_fields` short-circuit. Field-level GraphQL
  metadata on the Relay-supplied `id` field is **not** configurable in
  `0.0.6` (the rev4 M1 / rev6 M1 / rev7 M2 assigned-`id` ban applies
  uniformly); the documented workaround is a **resolver-backed sibling
  field** (`@strawberry.field(description="…") def display_id(self) ->
  strawberry.ID: return str(self.pk)`) carrying both the metadata and
  a value source.
- Type-annotation overrides are the consumer's responsibility for runtime
  correctness. `description: int` against a `CharField` will surface a
  Strawberry-side serialization error at query time if the database returns
  a non-integer value; the package does not pre-check annotation/field-type
  compatibility (out of scope for this card).

### DONE-016-0.0.7 — `DjangoListField` (non-Relay list)

Parity: ⚛️ required (graphene-django ships `DjangoListField`; strawberry-graphql-django has no non-Relay list-field primitive).

Shipped the `DjangoListField` factory function in `django_strawberry_framework/list_field.py` as a one-line `field: list[T] = DjangoListField(TargetType)` shape for root Query fields. The default resolver pulls `target_type.__django_strawberry_definition__.model._default_manager.all()` and applies `cls.get_queryset(...)` in both sync and async contexts; a consumer-supplied `resolver=` overrides the default body and any `Manager`/`QuerySet` return value receives `target_type.get_queryset(qs, info)` (graphene-django parity per rev2 H1 of `docs/SPECS/spec-016-list_field-0_0_7.md`), with `Manager → QuerySet` coercion handled by the field wrapper before `get_queryset` runs. Async consumer resolvers are detected at construction time via `inspect.iscoroutinefunction` and routed through an `async def` wrapper. Outer-list nullability is driven by the consumer's class-attribute annotation (`list[T]` → `[T!]!`, `list[T] | None` → `[T!]`). Optimizer cooperation rides the existing root-gated `info.path.prev is None` planning hook (`optimizer/extension.py:553`).

Added a new `all_library_branches_via_list_field` root field via `DjangoListField` to the library example schema. This is an intentional **card-text departure** from the original "Live HTTP coverage replacing one of the hand-rolled `all_library_*` resolvers" wording, per [Decision 9](docs/SPECS/spec-016-list_field-0_0_7.md) "Card-text departure" (rev4 H3): the add-only posture keeps `all_library_branches`'s `order_by("id")` intact so the existing live HTTP determinism tests stay green; no existing `all_library_*` resolver was replaced. A new live HTTP test `test_library_branches_via_djangolistfield_optimized_nested_selection` in `examples/fakeshop/test_query/test_library_api.py` pins the response shape and the optimizer's `prefetch_related("shelves")` plan via `CaptureQueriesContext`.

Validation tests in `tests/test_list_field.py` cover: non-class targets, non-`DjangoType` subclasses, unregistered types, non-callable `resolver=`, default-resolver shape, sync coroutine rejection in `get_queryset`, sync + async `get_queryset` paths, sync + async consumer-resolver `QuerySet` returns receiving `get_queryset`, sync + async Python `list` pass-through, nullable-outer / non-nullable-outer rendering, root-position optimizer planning, FK-id elision, and `Meta.primary` interaction (explicit primary + explicit secondary). The version bump from `0.0.6` is deferred to the last `0.0.7` card to ship per Decision 10 of the spec; this card leaves `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion at `0.0.6`.

Files touched: `django_strawberry_framework/list_field.py` (new), `django_strawberry_framework/__init__.py`, `tests/test_list_field.py` (new), `tests/base/test_init.py`, `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`, plus the Slice 5 doc sweep across `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `GOAL.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md`.

Spec: `docs/SPECS/spec-016-list_field-0_0_7.md`. Build plan: `docs/builder/build-016-list_field-0_0_7.md`.

### DONE-017-0.0.7 — `apps.py` and Django app config

Parity: ⚛️&🍓 required (both upstreams ship `apps.py` with an `AppConfig` for `INSTALLED_APPS`-driven discovery).

Shipped `django_strawberry_framework/apps.py` containing `DjangoStrawberryFrameworkConfig(AppConfig)` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`; no `ready()` body in `0.0.7` (deferred to the card that needs one). Consumers list `"django_strawberry_framework"` in `INSTALLED_APPS`; Django's implicit single-AppConfig discovery resolves the explicit class, and Django's check / signal hooks now resolve through the package's AppConfig.

Borrowed the behavioral shape from `strawberry_django/apps.py` verbatim (two class-level attributes, `name` then `verbose_name`); the module docstring (required by ruff's `D100`) and class docstring (required by ruff's `D101`) are additive, forced by this repo's stricter pydocstyle gate. `DjangoStrawberryFrameworkConfig` is NOT re-exported from `django_strawberry_framework/__init__.py` — Django's app loader resolves it through its dotted module path, and consumers reach it via `INSTALLED_APPS`, not via the package's import surface.

Package-internal tests at `tests/test_apps.py` cover the four positive contracts (importability from `django_strawberry_framework.apps`, `django.apps.AppConfig` subclass, `name` / `verbose_name` attribute values, and Django registry pickup via `django.apps.apps.get_app_config("django_strawberry_framework")`) plus one consolidated negative-shape test (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) that iterates `{"ready", "label", "default_auto_field", "default"}` and asserts each is absent from `DjangoStrawberryFrameworkConfig.__dict__` — pinning the "no extra behavioral AppConfig attributes" discipline across Decisions 2 / 4 / 5 / 8 of the spec. The existing live `/graphql/` HTTP tests at `examples/fakeshop/test_query/test_library_api.py` continue to pass unmodified — `examples/fakeshop/config/settings.py:48`'s `"django_strawberry_framework"` `INSTALLED_APPS` entry now resolves to the explicit AppConfig without any consumer-side change.

The version bump from `0.0.6` stays deferred to the last `0.0.7` card to ship per Decision 10 of `docs/SPECS/spec-016-list_field-0_0_7.md`; this card leaves `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, and `tests/base/test_init.py`'s version assertion at `0.0.6`. No new public exports; `__all__` is unchanged.

Files touched: `django_strawberry_framework/apps.py` (new), `tests/test_apps.py` (new), plus the Slice 3 doc sweep across `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md`.

Spec: `docs/SPECS/spec-017-apps-0_0_7.md`. Build plan: `docs/builder/build-017-apps-0_0_7.md`.

### DONE-018-0.0.7 — Schema export management command

Parity: 🍓 required (strawberry-graphql-django ships `manage.py export_schema` verbatim; graphene-django ships a different `graphql_schema` command — parity-adjacent only, deliberately not borrowed per Decision 6 of `docs/SPECS/spec-018-export_schema-0_0_7.md`).

Shipped `django_strawberry_framework/management/commands/export_schema.py` containing `Command(BaseCommand)` with positional `schema` (dotted path, default symbol name `"schema"`) and optional `--path`; SDL output via `strawberry.printer.print_schema`; `CommandError` for unimportable dotted path, non-`strawberry.Schema` resolved symbol, and missing positional argument. Package-internal tests at `tests/management/test_export_schema.py`; live fakeshop coverage in `examples/fakeshop/tests/test_commands.py`.

Borrowed the command shape verbatim from `strawberry_django/management/commands/export_schema.py` (positional `schema`, optional `--path`, `(ImportError, AttributeError)` → `CommandError` wrap, `isinstance(schema_symbol, strawberry.Schema)` guard, SDL via `strawberry.printer.print_schema`); the module / class / method docstrings (forced by ruff's `D100` / `D101` / `D102`) and the `parser: CommandParser` / `-> None` annotations (forced by `ANN001` / `ANN201`) are additive divergences from the upstream's annotation-free shape. `Command` is NOT re-exported from `django_strawberry_framework/__init__.py` — Django's `INSTALLED_APPS`-driven command-discovery resolves the class through `management/commands/`, not through the package's import surface.

Package-internal tests at `tests/management/test_export_schema.py` cover seven contracts (rev2 M1) — happy stdout, happy `--path`, `ImportError` half of the import-failure wrapper, `AttributeError` half of the wrapper, non-`Schema` resolved symbol, missing positional argument (via `CommandParser.error()` on `called_from_command_line=False`), and the `default_symbol_name="schema"` fallback. Every test goes through `django.core.management.call_command(...)` (NOT direct `Command().handle(...)`) so the missing-positional branch exercises the argparse layer; per-test `monkeypatch.setitem(sys.modules, "test_module", module)` keeps the seven tests order-independent. Live fakeshop coverage in `examples/fakeshop/tests/test_commands.py::test_export_schema_command_against_fakeshop_schema` runs `call_command("export_schema", "config.schema", "--path", str(tmp_path / "schema.graphql"))` against the real `strawberry.Schema(query=..., extensions=[DjangoOptimizerExtension()])` and asserts the produced SDL contains `"type BranchType"` from the library app.

The version bump from `0.0.6` stays deferred to the last `0.0.7` card to ship per Decision 10 of `docs/SPECS/spec-016-list_field-0_0_7.md` / Decision 9 of `docs/SPECS/spec-018-export_schema-0_0_7.md`; this card leaves `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, and `tests/base/test_init.py`'s version assertion at `0.0.6`. No new public exports; `__all__` is unchanged.

Files touched: `django_strawberry_framework/management/__init__.py` (new), `django_strawberry_framework/management/commands/__init__.py` (new), `django_strawberry_framework/management/commands/export_schema.py` (new), `tests/management/__init__.py` (new), `tests/management/test_export_schema.py` (new), `examples/fakeshop/tests/test_commands.py`, plus the Slice 3 doc sweep across `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md`.

Spec: `docs/SPECS/spec-018-export_schema-0_0_7.md`. Build plan: `docs/builder/build-018-export_schema-0_0_7.md`.

### DONE-019-0.0.7 — Multi-database cooperation contract

Parity: ⚛️&🍓 parity-adjacent (multi-database is a Django capability neither upstream specifies a contract around; pinning ours smooths the migrant story from both, but is not a primitive either upstream ships).

Pinned the package's multi-database cooperation contract — `router.db_for_read` on FK-id elision stubs (parent row forwarded as the `instance=` hint when present), explicit `.using(alias)` `_db` preservation through [`OptimizationPlan.apply`](django_strawberry_framework/optimizer/plans.py), consumer-provided [`OptimizerHint.prefetch(Prefetch(queryset=…))`](docs/GLOSSARY.md#optimizerhint) round-trip with `_db` intact, and strictness-mode's connection-agnostic shape under non-default aliases. Tests in [`tests/types/test_resolvers.py`](tests/types/test_resolvers.py) (five resolver-level tests against `_build_fk_id_stub` and `_check_n1` — four FK-id elision branches plus the strictness connection-agnostic shape; FK-id tests hermetic via mocked router) and [`tests/optimizer/test_multi_db.py`](tests/optimizer/test_multi_db.py) (two optimizer-plan-level tests against `OptimizationPlan.apply` and `OptimizerHint.prefetch` round-trip) and [`examples/fakeshop/test_query/test_multi_db.py`](examples/fakeshop/test_query/test_multi_db.py) (live `/graphql/` HTTP under `FAKESHOP_SHARDED=1` with `@pytest.mark.django_db(databases=...)` and full `Branch → Shelf → Book` seeding). [`docs/GLOSSARY.md#multi-database-cooperation`](docs/GLOSSARY.md#multi-database-cooperation) flipped from `planned for 0.0.7` to `shipped (0.0.7)` with a four-axis entry body; [`docs/README.md`](docs/README.md) `### Sharded mode (multi-DB)` carries a one-line forward-pointer. Spec: [`docs/spec-019-multi_db-0_0_7.md`](docs/spec-019-multi_db-0_0_7.md). Zero production code change; the cooperation already existed in [`django_strawberry_framework/types/resolvers.py:82`](django_strawberry_framework/types/resolvers.py). [`BACKLOG.md`](BACKLOG.md) item 41 owns first-class sharding-aware planning post-`1.0.0` (including threading the parent queryset's `_db` into generated child `Prefetch` querysets, which this card explicitly leaves to that future card).

Build plan: [`docs/builder/build-019-multi_db-0_0_7.md`](docs/builder/build-019-multi_db-0_0_7.md).

## Release readiness checklist

Before a release:

- `pyproject.toml` and `django_strawberry_framework/__init__.py` versions match.
- README status matches actual top-level exports.
- `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, and any active design docs agree on shipped/planned state.
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
- Strategic differentiation candidates (features neither `graphene-django` nor `strawberry-graphql-django` ship cleanly) live in [`BACKLOG.md`](BACKLOG.md). When a `BACKLOG.md` item is scheduled, promote it to a `TODO-NNN-X.Y.Z` or `TODO-NNN-X.Y.Z` card here and cross-reference back.
