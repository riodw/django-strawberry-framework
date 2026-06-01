# django-strawberry-framework Kanban

Last refreshed: 2026-05-28

This board summarizes what is shipped, what has recently landed, and what remains to finish based on the current code, tests, docs, and release-readiness notes. It is intentionally written as a project-management view: each card has a status, priority, scope, and a practical definition of done.

## Card ID format

Every card uses the form `<STATUS>[-<MILESTONE>]-NNN-X.Y.Z`:

- `<STATUS>` — the card workflow state: `BACKLOG` (unscheduled investigation / strategic-differentiation candidate), `TODO` (committed to a milestone, not yet active), `WIP` (actively being worked), or `DONE` (shipped). Updated when the card moves between workflow states. Blocking is not part of the workflow status; blocked cards render a derived `blocked` badge from unfinished `blocked_by` references and stay in their normal planning column.
- `<MILESTONE>` *(optional)* — the development phase the card lives in while it's still pre-shipping: `ALPHA` (pre-`0.1.0`), `BETA` (post-`0.1.0` / pre-`1.0.0`), or `STABLE` (post-`1.0.0`). Used on `BACKLOG`, `TODO`, and `WIP` cards. The two release cards themselves are tagged with the phase they usher in: `TODO-BETA-043-0.1.0` is the alpha → beta cut-over and `TODO-STABLE-053-1.0.0` is the beta → stable cut-over. **Dropped when the card ships** — `DONE` cards use the bare `DONE-NNN-X.Y.Z` form (no milestone segment). The card's version tag (`X.Y.Z`) already encodes which phase the shipment belongs to, and the bare form keeps the shipped-card cluster compact and uniform across the package's history.
- `NNN` — a 3-digit sequence number indicating the order the card was completed (`DONE` cards) or is being tracked (everything else; scheduled cards are ordered by planned ship version, and backlog cards sort after the scheduled board). **Unlike status, milestone, and version, this number is not stable** — it is recomputed whenever a card's position in the shipping sequence changes (reordered, new card inserted between two existing cards, version-tag bumped). Use the card title, not the NNN, when referencing a card from long-lived documents.
- `X.Y.Z` — the package version the card shipped in (`DONE` cards), is planned to ship in (scheduled cards), or is provisionally bucketed under (`BACKLOG` cards). Alpha cards span `0.0.6` through `0.0.12` leading up to `0.1.0`; Beta cards span `0.1.1` through `0.1.6` leading up to `1.0.0`. The `0.1.0` and `1.0.0` tags are reserved for the two release cards themselves. Backlog cards may use post-`1.0.0` buckets as ordering placeholders; they stay unscheduled until promoted to `TODO`.

For install, local development, testing, and the canonical documentation map, start from [`README.md`][readme].

## Relative size

Every card carries a `Relative size:` estimate on a five-point
T-shirt scale **anchored to the shipped Filtering subsystem (`DONE-027-0.0.8`) =
XL** — the largest card the package has shipped (a 1,290-line spec plus a full
six-layer lazy-resolution pipeline). The size is a planning estimate of build
effort, not a commitment:

- **XS** — trivial / mechanical; ≲½ day; one small module or a bookkeeping edit; no spec.
- **S** — small; ~1 day; one module + tests; light or no spec.
- **M** — moderate; a few days; multi-file, a real spec, a handful of design decisions.
- **L** — large subsystem; ~a week; new subpackage, full spec, broad integration.
- **XL** — very large subsystem at `DONE-027-0.0.8` scale.

On `DONE` cards the size is a retrospective estimate of the build effort the
card represented; their `Priority` and `Severity` tags are likewise best-effort
retrospective values (neither was tracked while the work was active). Cards in
the To-Do-Alpha column and the Done column carry the full tag block (`Priority`
/ `Parity` / `Severity` / `Status` / `Relative size`), with any explanatory text
demoted to a bullet under its label.

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
- 0.0.4 foundation slice has shipped (card `DONE-010-0.0.4`):
  - `DjangoTypeDefinition` is the canonical per-type metadata object stashed at `cls.__django_strawberry_definition__`, with forward-reserved slots (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`) ready for Layer 3 to populate.
  - `finalize_django_types()` resolves pending relations, attaches generated relation resolvers, and runs `strawberry.type(cls, ...)` for every collected type. Re-exported from `django_strawberry_framework` and `django_strawberry_framework.types`.
  - Pending-relation registry (`PendingRelation`, `add_pending_relation`, `iter_pending_relations`, `discard_pending`, `is_finalized`, `mark_finalized`, extended `clear`) supports definition-order-independent FK / reverse FK / forward + reverse OneToOne / forward + reverse M2M / multi-cycle graphs.
  - Manual relation override contract (`consumer_annotated_relation_fields` vs `consumer_assigned_relation_fields`): annotation-only overrides keep the generated relation resolver; `strawberry.field(resolver=...)` / `@strawberry.field` overrides suppress it.
  - Fail-loud unresolved-target finalization error names source model, source field, and target model.
  - OneToOne / M2M cardinality coverage now uses the real `library` example app; the old `tests.fixtures.apps.TestsCardinalityConfig` fixture app has been removed.
- 0.0.5 shipped after this foundation slice and is recorded separately as `DONE-015-0.0.5`.
- 0.0.6 shipped as the patch closing the foundation phase: `DONE-016-0.0.6` (`FieldMeta` consolidation), `DONE-017-0.0.6` (deferred scalar conversions), `DONE-018-0.0.6` (multiple `DjangoType`s per model with `Meta.primary`), and `DONE-019-0.0.6` (consumer override semantics for scalar fields).
- Test suite structure has caught up with the package shape:
  - `tests/optimizer/` covers `extension.py`, `walker.py`, `plans.py`, `hints.py`, `field_meta.py`, and `definition_order.py`.
  - `tests/types/` covers `base.py`, `converters.py`, `resolvers.py`, `definition_order.py`, and `definition_order_schema.py`.
  - `tests/test_registry.py` covers idempotency / phase-1 atomicity / phase-2/3 partial-mutation / pending-set cleanup / class-mutation residue.
  - `tests/utils/` covers utility modules.
  - The full suite runs through `uv run pytest`, including package tests, example-project tests, and live `/graphql/` HTTP tests, with 100% package coverage.

### In progress

- `0.0.7` shipped 2026-05-27 with seven cards: `DONE-020-0.0.7` (`DjangoListField`), `DONE-021-0.0.7` (`apps.py` and Django app config), `DONE-022-0.0.7` (schema-export management command), `DONE-023-0.0.7` (multi-database cooperation contract), `DONE-024-0.0.7` (Django Trac #37064 hardening + `safe_wrap_connection_method` consumer helper), `DONE-025-0.0.7` (warning-free scalar registration via `StrawberryConfig.scalar_map`), and `DONE-026-0.0.7` (scalar conversion end-to-end coverage in the fakeshop example with the new `apps.scalars` app plus a `BigIntegerField` on `apps.library.Patron`). Full card detail lives under the `## Done` board column below. Tag: `0.0.7` at commit `72f6cd9`.
- `0.0.8` is the active patch. `WIP-ALPHA-028-0.0.8` (Ordering subsystem) is the only card currently in progress for this patch; the Filtering subsystem shipped as `DONE-027-0.0.8`. Blocked future cards stay in their normal planning columns with derived `blocked` badges, outside the active in-progress column. The last `0.0.8` card to ship owns the version bump from `0.0.7` per Decision 10 of `docs/SPECS/spec-020-list_field-0_0_7.md`.
- Strategic differentiation roadmap (post-`0.0.6`) captured in [`BACKLOG.md`][backlog]: items neither `graphene-django` nor `strawberry-graphql-django` ship cleanly that should land on the roadmap once parity items are shipped.

### Still not implemented

- Layer 3 public subsystems are still planned only:
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
  - connection-aware planning for Relay-style nested connection selections (new card `TODO-ALPHA-030-0.0.9`)
- Test/example hygiene items surfaced by the foundation slice review have moved into the testing-shift docs and backlog: package-level override tests intentionally pin Strawberry internals while HTTP tests pin the consumer-visible override contract ([`BACKLOG.md`][backlog] item 38).
- The library GraphQL schema is real and wired into the project schema; the product-catalog Layer 3 aspirational schema block remains commented until those subsystems ship.

## Board columns

## WIP / DONE spec map

| Card | Spec file |
| --- | --- |
| `WIP-ALPHA-028-0.0.8` — Ordering subsystem | [spec-028-orders-0_0_8.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-028-orders-0_0_8.md) |
| `DONE-027-0.0.8` — Filtering subsystem | [spec-027-filters-0_0_8.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-027-filters-0_0_8.md) |
| `DONE-026-0.0.7` — Scalar conversion end-to-end coverage in the fakeshop example | [spec-026-scalar_conversion_fakeshop-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md) |
| `DONE-025-0.0.7` — Warning-free scalar registration via `StrawberryConfig.scalar_map` | [spec-025-scalar_map_helper-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-025-scalar_map_helper-0_0_7.md) |
| `DONE-024-0.0.7` — Django Trac #37064 hardening + `safe_wrap_connection_method` | [spec-024-django_trac_37064_hardening-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md) |
| `DONE-023-0.0.7` — Multi-database cooperation contract | [spec-023-multi_db-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-023-multi_db-0_0_7.md) |
| `DONE-022-0.0.7` — Schema export management command | [spec-022-export_schema-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-022-export_schema-0_0_7.md) |
| `DONE-021-0.0.7` — `apps.py` and Django app config | [spec-021-apps-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-021-apps-0_0_7.md) |
| `DONE-020-0.0.7` — `DjangoListField` (non-Relay list) | [spec-020-list_field-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-020-list_field-0_0_7.md) |
| `DONE-019-0.0.6` — Consumer override semantics (scalar fields) | [spec-019-consumer_overrides_scalar-0_0_6.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md) |
| `DONE-018-0.0.6` — Multiple DjangoTypes per model with `Meta.primary` | [spec-018-meta_primary-0_0_6.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-018-meta_primary-0_0_6.md) |
| `DONE-017-0.0.6` — Deferred scalar conversions | [spec-017-deferred_scalars-0_0_6.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-017-deferred_scalars-0_0_6.md) |
| `DONE-016-0.0.6` — `FieldMeta` single-source-of-truth consolidation and mirror retirement | [spec-016-fieldmeta_consolidation-0_0_6.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md) |
| `DONE-015-0.0.5` — 0.0.5 Relay interfaces and Node foundation | [spec-015-relay_interfaces-0_0_5.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-015-relay_interfaces-0_0_5.md) |
| `DONE-014-0.0.4` — Move test fixture out of example settings | [spec-014-testing_shift-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-014-testing_shift-0_0_4.md) |
| `DONE-013-0.0.4` — Real M2M coverage | [spec-013-real_m2m_coverage-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md) |
| `DONE-012-0.0.4` — 0.0.4 version and release alignment | [spec-012-version_release_alignment-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-012-version_release_alignment-0_0_4.md) |
| `DONE-011-0.0.4` — Stale placeholder cleanup | [spec-011-stale_placeholder_cleanup-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md) |
| `DONE-010-0.0.4` — 0.0.4 foundation slice (definition-order independence) | [spec-010-foundation-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-010-foundation-0_0_4.md) |
| `DONE-009-0.0.4` — Rich schema architecture | [spec-009-rich_schema_architecture-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md) |
| `DONE-008-0.0.4` — Definition-order independence design | [spec-008-definition_order_independence-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-008-definition_order_independence-0_0_4.md) |
| `DONE-007-0.0.4` — 0.0.4 onboarding docs and spec consolidation | [spec-007-onboarding_docs_spec_consolidation-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md) |
| `DONE-006-0.0.3` — Documentation/status positioning for shipped Layer 2 | [spec-006-public_surface-0_0_3.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-006-public_surface-0_0_3.md) |
| `DONE-005-0.0.3` — DjangoType contract and boundary | [spec-005-django_type_contract-0_0_3.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-005-django_type_contract-0_0_3.md) |
| `DONE-004-0.0.3` — Optimizer beyond slices B1-B8 | [spec-004-optimizer_beyond-0_0_3.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-004-optimizer_beyond-0_0_3.md) |
| `DONE-003-0.0.2` — Optimizer O4 nested prefetch chains | [spec-003-optimizer_nested_prefetch_chains-0_0_2.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md) |
| `DONE-002-0.0.2` — Optimizer O1-O6 foundation | [spec-002-optimizer-0_0_2.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-002-optimizer-0_0_2.md) |
| `DONE-001-0.0.1` — DjangoType core foundation | [spec-001-django_types-0_0_1.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-001-django_types-0_0_1.md) |

## In progress

The only active WIP card is `WIP-ALPHA-028-0.0.8 — Ordering subsystem`, and it is in the `0.0.8` patch. The Filtering subsystem shipped as `DONE-027-0.0.8`; blocked cards stay in their normal planning column with a derived `blocked` badge, and future cards stay outside the in-progress column.

<a id="ordering_subsystem"></a>
### [WIP-ALPHA-028-0.0.8 — Ordering subsystem](https://riodw.github.io/django-strawberry-framework/#ordering_subsystem)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: In progress
- Relative size: L
- Labels: `filters`, `graphql-api`, `layer-3`, `ordering`, `public-api`
- Spec: [spec-028-orders-0_0_8.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-028-orders-0_0_8.md)

#### Planning note

planned

#### Scope

- `Order`
- `OrderSet`
- GraphQL argument factory
- `Meta.orderset_class` promotion

#### Definition of done

- [ ] Add `docs/spec-orders.md`.
- [ ] Add `django_strawberry_framework/orders/`.
- [ ] Add mirrored `tests/orders/`.
- [ ] Promote `Meta.orderset_class` only when ordering is applied end-to-end.
- [ ] Support simple fields and relation paths.
- [ ] Define interaction with filters and connection field.
- [ ] Keep ordering declarations introspectable from the owning type/query surface.

#### Foundation-slice seam

- `DjangoTypeDefinition.orderset_class` is the populated slot.
- Lazy related-order class references reuse the same record-now-resolve-at-finalization pattern as model relations (`PendingRelation` → analogous `PendingRelatedClass` shape).

#### Verified in upstream

- `ordering.py::Ordering` — public `Ordering` enum: `ASC`, `DESC`, `ASC_NULLS_FIRST`, `ASC_NULLS_LAST`, `DESC_NULLS_FIRST`, `DESC_NULLS_LAST`.
- `ordering.py::OrderSequence` — per-field sequence descriptor used to order ties when multiple fields participate.
- `ordering.py::process_order` / `::process_ordering` / `::process_ordering_default` / `::apply_ordering` — the runtime pipeline that compiles an order-input value into queryset `order_by()` arguments and applies them.
- `ordering.py::StrawberryDjangoFieldOrdering` — field-base subclass that injects the `order: <T>OrderInput` and `ordering: list[<T>OrderInput]` arguments on a Django-backed field.
- `ordering.py::order_type` — current consumer-facing `@strawberry_django.order_type(Model)` decorator (public API).
- `ordering.py::order` — legacy decorator alias marked `@deprecated("strawberry_django.order is deprecated in favor of strawberry_django.order_type.")`; do not claim parity with this symbol.
- `ordering.py::ORDER_ARG` (`= "order"`) and `ordering.py::ORDERING_ARG` (`= "ordering"`) — module-level constants for the singular one-of and list GraphQL argument names.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField #"order_by"` — connection field accepts an `order_by` argument that composes through `django_filters.OrderingFilter` declared on the FilterSet. Graphene has no separate ordering primitive; ⚛️ parity is met by the filter subsystem (`DONE-027-0.0.8`) rather than this card.

#### Other

- second-largest `0.0.8` card. A leaner mirror of `DONE-027-0.0.8`: five of the six lazy-resolution layers carry over, no operator-bag/lookup surface, 🍓-only parity. New `orders/` subpackage + `docs/spec-orders.md` + mirrored tests. Layer 6 (dynamic OrderSet generation) has no cookbook counterpart — the one genuinely fresh design decision.
- **Layers 1-2** (lazy class refs + module-fallback resolution): port from `mixins.py::LazyRelatedClassMixin` and `orders.py::BaseRelatedOrder`. Same shape as the filter side; `RelatedOrder` substituted for `RelatedFilter`.
- **Layer 3** (metaclass discovery, deferred expansion): port from `orderset.py::OrderSetMetaclass`. Leaner than the filter side's `FilterSetMetaclass`; the discover-and-bind pattern is the same.
- **Layer 4** (cycle-safe expansion + cache): the cookbook's orderset uses `orderset.py::AdvancedOrderSet.get_fields` (and `::get_flat_orders` for the prefix-walked output) — **not** `get_filters()` or `get_orders()`. Earlier card revisions referenced a `get_orders()` method that does not exist in the cookbook. The cycle-safe expansion pattern carries over but the method names and cache-key shape are spelled differently from the filter side.
- **Layer 5** (BFS schema build with deferred references — Strawberry-adapted): port from `order_arguments_factory.py::OrderArgumentsFactory._ensure_built`. Graphene's `lambda tn=...: input_object_types[tn]` forward references become `strawberry.lazy("django_strawberry_framework.orders._registry.{TargetOrderSet}InputType")` (or `Annotated[..., strawberry.lazy(...)]`).
- **Layer 6** (memoized dynamic OrderSet generation): **no cookbook counterpart**. The cookbook ships no `orderset_factories.py` and no `_dynamic_orderset_cache` — only the filter side has the dynamic-factory mechanism. Our ordering subsystem must either design Layer 6 fresh (mirroring the filter side's `filterset_factories.py::_dynamic_filterset_cache`) or skip the dynamic-ordering-for-connection-field case and require explicit `orderset_class` declarations on every consumer. **Pin this decision in the spec.**
- `orders.py::BaseRelatedOrder`, `orders.py::RelatedOrder`
- `orderset.py::OrderSetMetaclass`, `orderset.py::AdvancedOrderSet` (with `::get_fields`, `::get_flat_orders`, `::apply_distinct`, `::check_permissions`, `::_apply_distinct_postgres`, `::_apply_distinct_emulated`)
- `order_arguments_factory.py::OrderArgumentsFactory`, `order_arguments_factory.py::OrderDirection`

#### Card references

- Related via Card item: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField #"order_by"` — connection field accepts an `order_by` argument that composes through `django_filters.OrderingFilter` declared on the FilterSet. Graphene has no separate ordering primitive; ⚛️ parity is met by the filter subsystem (`DONE-027-0.0.8`) rather than this card. -> `DONE-027-0.0.8` — Filtering subsystem
- Related via Card item: second-largest `0.0.8` card. A leaner mirror of `DONE-027-0.0.8`: five of the six lazy-resolution layers carry over, no operator-bag/lookup surface, 🍓-only parity. New `orders/` subpackage + `docs/spec-orders.md` + mirrored tests. Layer 6 (dynamic OrderSet generation) has no cookbook counterpart — the one genuinely fresh design decision. -> `DONE-027-0.0.8` — Filtering subsystem

## To Do - Alpha (0.1.0)

Cards required to reach feature parity with both upstreams (`⚛️ graphene-django` and `🍓 strawberry-graphql-django`). Each card targets its own `0.0.x` patch within the road to **0.1.0**. The final card in this column is the `0.1.0` release itself (cleanup, verification, alpha → beta cut-over). Cards in NNN order = planned ship order; dependency and parallelism notes live on each card.

<a id="djangotype_consumer_dx_cleanup_pass"></a>
### [TODO-ALPHA-029-0.0.9 — `DjangoType` consumer-DX cleanup pass](https://riodw.github.io/django-strawberry-framework/#djangotype_consumer_dx_cleanup_pass)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Planned
- Relative size: S-M
- Labels: `cleanup`, `developer-tools`, `public-api`, `types`

#### Planning note

planned; three independent slices that ship in any order. Card body counts as complete when all three slices land; if the schedule forces Slice 3 to defer, the slice carves off as its own follow-up card without disrupting Slices 1 + 2.

#### Dependencies

- `TODO-ALPHA-030-0.0.9` — `DjangoConnectionField`

#### Scope

- **Slice 1** — Strawberry `extensions=[instance]` factory-callable migration. Mechanical sweep of every `strawberry.Schema(query=…, extensions=[DjangoOptimizerExtension()])` site, replacing the deprecated instance form with `extensions=[DjangoOptimizerExtension]` (class) or `extensions=[lambda: DjangoOptimizerExtension()]` (factory callable). Strawberry deprecated the instance form upstream; future releases will remove it. Affects `tests/optimizer/test_relay_id_projection.py`, `tests/test_list_field.py`, `tests/types/test_generic_foreign_key.py`, `examples/fakeshop/config/schema.py`, plus the schema-construction snippet in `docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, and `TODAY.md`. ~30 min mechanical. No spec.
- **Slice 2** — `manage.py inspect_django_type <TypeName>` diagnostic command. New Django management command at `django_strawberry_framework/management/commands/inspect_django_type.py` walking a `DjangoType.__django_strawberry_definition__` and printing per-field: Django field name → Django field type → resolved GraphQL scalar/type → nullability → which `SCALAR_MAP` row (or relation converter) fired. Mirrors Django's `inspectdb` conceptually but scoped to the framework's type-definition surface. Tests via `examples/fakeshop/tests/test_commands.py::call_command("inspect_django_type", "PatronType", ...)`. Sub-1-day. Light spec or none.
- **Slice 3** — `Meta.nullable_overrides` GraphQL-layer nullability override. New public `Meta` key (and possibly a companion `Meta.required_overrides`) letting consumers decouple the GraphQL type's nullability from the underlying Django column without an `AlterField` migration or a custom resolver. Implemented inside `django_strawberry_framework/types/base.py` and `django_strawberry_framework/types/converters.py`'s scalar-resolution path. Tests in `tests/types/test_converters.py` (override + collision cases) plus a live HTTP test on the library or scalars app demonstrating the override flipping the GraphQL type's nullability without touching the model column. **Requires spec**: `docs/spec-021-nullable_overrides-0_0_8.md` — open design decisions include dict-of-name vs tuple-set per direction, interaction with `Meta.exclude`, error behavior when both override sets name the same field, choice-field interaction, and FK / reverse-FK interaction.

#### Definition of done

- [ ] **Slice 1**: every `extensions=[DjangoOptimizerExtension()]` instance form replaced with the factory-callable equivalent in tests, examples, and consumer-facing docs. `uv run pytest` shows zero `DeprecationWarning` about Strawberry extension instances. CHANGELOG entry under `## [0.0.8]` `### Changed`.
- [ ] **Slice 2**: `django_strawberry_framework/management/commands/inspect_django_type.py` ships with module + class docstring, `add_arguments` taking a positional `type_dotted_path`, and `handle` printing the resolved field table. Tests via `examples/fakeshop/tests/test_commands.py` using `call_command`. `docs/GLOSSARY.md` adds an entry; `docs/TREE.md` lists the new module under `management/commands/`. CHANGELOG entry under `## [0.0.8]` `### Added`.
- [ ] **Slice 3**: `docs/spec-021-nullable_overrides-0_0_8.md` written and reviewed; `Meta.nullable_overrides` (and `Meta.required_overrides` if the spec confirms it) implemented; tests cover override-applies, override-rejects-unknown-field, override-collides-with-other-direction error, and override-on-choice-field. `docs/GLOSSARY.md` adds an entry; live HTTP test in `examples/fakeshop/test_query/` demonstrates the override flipping nullability for a real model field. CHANGELOG entry under `## [0.0.8]` `### Added`.

#### Foundation-slice seam

- Slice 1 has no foundation interaction; it's a sweep across already-shipped surfaces.
- Slice 2 reads `DjangoTypeDefinition` populated by `finalize_django_types()`; the command is a strict consumer of the existing introspection surface.
- Slice 3 plugs into `DjangoType._build_annotations` (the converter loop in `django_strawberry_framework/types/base.py`) and the scalar-resolution path in `django_strawberry_framework/types/converters.py`. No finalizer changes — overrides apply at type-construction time, before finalization.

#### Dependencies

- None blocking. Slice 1 should land before any new schema-construction surfaces ship in `TODO-ALPHA-030-0.0.9` and onward, so consumers copy from a current pattern rather than a deprecated one.

#### Other

- three independent slices: Slice 1 `extensions=` factory-form sweep (XS, ~30 min, no spec), Slice 2 `inspect_django_type` command (S, sub-1-day), Slice 3 `Meta.nullable_overrides` (M, needs spec, deferrable to `0.0.9`). Smallest of the three `0.0.8` cards.
- **Slice 1**: defensive — both upstreams already use the factory-callable form in their consumer docs. Strawberry's removal runway is multiple releases, but landing the migration in 0.0.8 keeps the package's surface aligned with the upstream recommendation.
- **Slice 2**: differentiating — neither `graphene-django` nor `strawberry-graphql-django` ships an equivalent `manage.py inspect_*` diagnostic for their type definitions. Consumers currently introspect by hand against the GraphQL schema after construction. This command moves that diagnostic to the type-definition layer, before schema construction.
- **Slice 3**: ⚛️&🍓 required — `strawberry_django.field(required=True/False)` allows per-field GraphQL nullability override against the Django column's native nullability. `graphene_django` allows the same via `DjangoObjectType.Meta.fields` plus per-field overrides on the type class. This card surfaces the same capability through a single `Meta`-key dict that the rest of the package's `Meta`-shaped API already prefers.

#### Card references

- Dependency via Dependencies section: None blocking. Slice 1 should land before any new schema-construction surfaces ship in `TODO-ALPHA-030-0.0.9` and onward, so consumers copy from a current pattern rather than a deprecated one. -> `TODO-ALPHA-030-0.0.9` — `DjangoConnectionField`

<a id="djangoconnectionfield"></a>
### [TODO-ALPHA-030-0.0.9 — `DjangoConnectionField`](https://riodw.github.io/django-strawberry-framework/#djangoconnectionfield)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Planned
- Relative size: L
- Labels: `connections`, `filters`, `optimizer`, `ordering`, `public-api`, `relay`

#### Planning note

planned

#### Dependencies

- `DONE-027-0.0.8` — Filtering subsystem
- `WIP-ALPHA-028-0.0.8` — Ordering subsystem
- `TODO-BETA-044-0.1.1` — `FieldSet`

#### Scope

- Relay-style connection field
- composition of filtering, ordering, aggregation, field selection, and optimizer behavior

#### Definition of done

- [ ] Add `docs/spec-connection.md`.
- [ ] Implement `django_strawberry_framework/connection.py`.
- [ ] Add `tests/test_connection.py`.
- [ ] Decide whether full Relay support belongs here or a separate `relay/` subpackage.
- [ ] Promote `DjangoConnectionField` only when end-to-end schema usage is tested.

#### Foundation-slice seam

- `finalize_django_types()` is the single architectural entry point that `DjangoConnectionField(DjangoType)` (and `DjangoNodeField`) will auto-trigger as their wrapper.
- An auto-trigger wrapper must respect the single-threaded-setup window: either be constrained to schema-construction time, or acquire a real lock around the finalizer.
- Connection-aware optimizer planning is its own follow-up slice (`TODO-ALPHA-032-0.0.9`); the foundation slice did not exercise nested connection prefetch shapes.

#### Dependencies

- `FilterSet` (`DONE-027-0.0.8`)
- `OrderSet` (`WIP-ALPHA-028-0.0.8`)
- Relay/interface decisions
- `FieldSet` — **deferred to `TODO-BETA-044-0.1.1`** (post-Alpha); field-selection composition is layered on after the connection field ships, not a 0.0.9 blocker.

#### Other

- once filters/orders are stable. FieldSet integration is deferred to `TODO-BETA-044-0.1.1` — `DjangoConnectionField` ships against the Layer-2 surface in 0.0.9 and gains field-selection composition when FieldSet lands.
- both upstreams ship Relay-shaped connection fields.
- the central read-side primitive — the Relay surface and all Layer-3 arguments compose through it.
- central Relay-shaped connection field plus cursor-pagination math; the integration point that filters / orders / aggregation / field-selection / optimizer all compose through. New `connection.py` + `docs/spec-connection.md` + tests.

#### Card references

- Dependency via Dependencies section: `FilterSet` (`DONE-027-0.0.8`) -> `DONE-027-0.0.8` — Filtering subsystem
- Dependency via Dependencies section: `OrderSet` (`WIP-ALPHA-028-0.0.8`) -> `WIP-ALPHA-028-0.0.8` — Ordering subsystem
- Dependency via Dependencies section: `FieldSet` — **deferred to `TODO-BETA-044-0.1.1`** (post-Alpha); field-selection composition is layered on after the connection field ships, not a 0.0.9 blocker. -> `TODO-BETA-044-0.1.1` — `FieldSet`
- Related via Card item: Connection-aware optimizer planning is its own follow-up slice (`TODO-ALPHA-032-0.0.9`); the foundation slice did not exercise nested connection prefetch shapes. -> `TODO-ALPHA-032-0.0.9` — Connection-aware optimizer planning
- Related via Card item: once filters/orders are stable. FieldSet integration is deferred to `TODO-BETA-044-0.1.1` — `DjangoConnectionField` ships against the Layer-2 surface in 0.0.9 and gains field-selection composition when FieldSet lands. -> `TODO-BETA-044-0.1.1` — `FieldSet`

<a id="full_relay_story_node_connection_root_validation"></a>
### [TODO-ALPHA-031-0.0.9 — Full Relay story (Node + Connection + Root + validation)](https://riodw.github.io/django-strawberry-framework/#full_relay_story_node_connection_root_validation)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Planned
- Relative size: L-XL
- Labels: `connections`, `graphql-api`, `permissions`, `public-api`, `relay`

#### Planning note

blocked on `TODO-ALPHA-030-0.0.9` (`DjangoConnectionField`). When the connection field lands, this card unblocks and ships in the same release. The post-`1.0.0` "Relay magic" differentiators (type-rename GlobalID migrations, polymorphic connections, stable cursors, refetchable containers, permission-aware cursor decoding) live separately in [`BACKLOG.md`][backlog] item 39 — they extend this story rather than block it.

#### Dependencies

- `TODO-ALPHA-030-0.0.9` — `DjangoConnectionField`

#### Other

- eight-goal umbrella for the complete Relay surface (Root `node`/`nodes` fields, relation-as-Connection upgrade, cursor contracts, permission integration, schema-validation diagnostics, test helpers, fakeshop activation). New `relay.py` + `test/relay.py` + finalizer changes + spec. Cursor mechanics overlap with 024; this card is the connective tissue tying it all together.
- ~~`Meta.interfaces` design~~ — `Meta.interfaces` accepted end-to-end for any Strawberry interface; `(relay.Node,)` activates the Node foundation.
- ~~`GlobalID` mapping decision~~ — Strawberry-supplied `id: GlobalID!` from the Relay interface replaces the synthesized `id: int!`; Django primary key remains projected as a connector column for the optimizer (Decision 2 of [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-011]).
- ~~Default `resolve_*` injection~~ — `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes` defaults injected when `relay.Node` is in `Meta.interfaces`; consumer overrides preserved via Strawberry's `__func__` identity test.
- ~~`is_type_of` injection~~ — Unconditional on every `DjangoType`; consumer-declared `is_type_of` preserved.
- ~~`CompositePrimaryKey` rejection~~ — Django 5.2+ composite-pk models raise `ConfigurationError` at finalization with the documented escape hatch (`id: relay.NodeID[...]` annotation).
- `node(id: GlobalID!): Node` — single-object refetch. Decodes the GlobalID, dispatches to the type's `resolve_node`, returns the resolved object. Returns `null` if the GlobalID decodes to a type/ID the requesting user can't see (respects `get_queryset`).
- `nodes(ids: [GlobalID!]!): [Node]!` — batch refetch. Decodes each GlobalID, dispatches per-type to `resolve_nodes` (batched), returns results in input order. Missing IDs become `null` entries (preserves positional correspondence).
- **Implicit upgrade** (default): every `DjangoType` whose `Meta.interfaces` includes `relay.Node` automatically exposes its reverse-FK and M2M relations as Connections in addition to the existing `list[T]` shape. Field names follow a stable convention (`itemsConnection: ItemConnection` alongside `items: list[Item]`).
- **Explicit-only**: consumers who want only Connections (or only lists) on a relation declare `Meta.relation_shapes = {"items": "connection"}` (or `"list"`, or `"both"` — `"both"` is the default for Relay types).
- **Cursor format**: opaque base64-encoded payload by default (`b64("offset:N")`). Documented as opaque — clients must not parse it. `Meta.cursor_field` for stable column-based cursors is **out of scope** for this card; lives in BETTER item 39 sub-feature 3.
- **Required arguments**: `first: Int`, `after: String`, `last: Int`, `before: String`. Backward pagination (`last`/`before`) is required by the Relay spec.
- **`pageInfo`**: emits the four standard fields (`hasNextPage`, `hasPreviousPage`, `startCursor`, `endCursor`) with correct semantics — including the spec-mandated *"the connection MUST resolve `hasNextPage` correctly even when the consumer didn't request it"* invariant.
- **Edge cases**: `first: 0` returns empty edges + `pageInfo`. `first: N` with N > remaining rows returns the actual remainder. `after` cursor for a row that no longer exists falls through to the next existing row (no error). Both `first` and `last` in the same query is rejected with a typed error.
- **`totalCount`**: an opt-in field on every Connection (`Meta.connection = {"total_count": True}`). When selected, runs `qs.count()` on the *unpaginated* queryset (post-filter, pre-slice). Documented as the canonical Relay-compatible total-count surface.
- `filter: <Type>FilterInput` — generated from `Meta.filterset_class` (composes with `DONE-027-0.0.8`)
- `orderBy: [<Type>OrderInput!]` — generated from `Meta.orderset_class` (composes with `WIP-ALPHA-028-0.0.8`)
- `search: String` — generated from `Meta.search_fields` (composes with `TODO-BETA-045-0.1.2` — note: search is `1.0.0` scope, ships after `0.1.0`; until then, search arg is absent)
- decode the GlobalID server-side (never trust the client's claim of which type the ID belongs to)
- dispatch to the resolved type's `resolve_node` (which honors `cls.get_queryset(qs, info)`)
- return `null` for rows the user can't see (not an error — the Relay spec requires `null`, not an exception)
- never reveal *existence* of hidden rows through error timing or status codes
- `relay.GlobalID`, `relay.NodeID[...]`, `relay.Connection`, `relay.ListConnection`, `relay.Edge`, `relay.PageInfo` in `Meta.interfaces` → rejected with a message naming the helper and explaining it's a scalar / annotation / field-type rather than an interface.
- Non-Strawberry-interface classes in `Meta.interfaces` → rejected at validation with the offending class name.
- `Meta.connection = {...}` declared on a type that doesn't include `relay.Node` in `Meta.interfaces` → rejected with a message suggesting either remove the `connection` key or add `relay.Node` to interfaces.
- A `DjangoNodeField()` query field on a schema with **no** `DjangoType`s declaring `relay.Node` → rejected at finalization with *"node lookup configured but no Node types registered."*
- `node(id:)` and `nodes(ids:)` resolve real product / category / item / entry GlobalIDs
- Reverse-FK and M2M relations on those types expose their Connection counterparts
- Live HTTP tests under `examples/fakeshop/test_query/` exercise the full Relay query shape (refetch, paginated connection, cursor round-trip, `totalCount`)
- Type-rename GlobalID migrations (Django-migrations-style history that lets old-format IDs decode alongside new)
- Polymorphic connections (`Connection[Interface]` with auto-dispatched concrete types per edge)
- `Meta.cursor_field` for stable cursors keyed on a deterministic column
- Auto-upgrade reverse FK / M2M to Connection based on a row-count threshold
- Refetchable container schema metadata for `useRefetchableFragment`
- Permission-aware cursor decoding (cursor decode re-runs `get_queryset` so privileged cursors don't leak)
- `TODO-ALPHA-030-0.0.9` (`DjangoConnectionField`) — **hard dependency**; this card unblocks when 026 lands.
- `DONE-027-0.0.8` (Filtering subsystem) — soft dependency for the filter argument on Connections.
- `WIP-ALPHA-028-0.0.8` (Ordering subsystem) — soft dependency for the orderBy argument on Connections.
- `TODO-ALPHA-032-0.0.9` (Connection-aware optimizer planning) — ships in parallel; the Node entry points and the relation-as-Connection upgrade both rely on the walker recognizing `edges { node { ... } }`.
- `TODO-ALPHA-033-0.0.10` (Permissions subsystem) — soft dependency; the Node entry points respect `get_queryset` immediately and integrate with declared permissions when 029 lands.
- New spec: `docs/spec-relay_connection.md` covering all eight goals above with worked examples and decision rationale.
- `DjangoNodeField` and `DjangoNodesField` exported from the package public surface; both wired through the registry's GlobalID decode path and the per-type `get_queryset`.
- Reverse-FK and M2M relations on `relay.Node`-implementing types expose their Connection counterparts; `Meta.relation_shapes` opt-out documented.
- Cursor pagination math passes the Relay-spec test suite for `first`/`after`/`last`/`before`/`pageInfo` edge cases.
- `Meta.connection = {"total_count": True}` adds a `totalCount` field that runs `qs.count()` on the unpaginated post-filter queryset.
- Filter / order arguments accepted on Connection fields when the corresponding `*_class` is declared on the type.
- Permission-aware Node lookup: `node(id:)` returns `null` for hidden rows; no existence leak via error timing.
- Six schema-validation diagnostics from Goal 6 raise `ConfigurationError` with the documented messages.
- `django_strawberry_framework.test.relay` module exposes `global_id_for(type_cls, id)` and `decode_global_id(gid)`.
- The fakeshop `library` HTTP test suite gains Relay-shaped queries (refetch, paginated connection, cursor round-trip, `totalCount`). Fakeshop `products` activation lights up the full Relay surface as part of `TODO-BETA-049-0.1.5`.
- 100% coverage across the new code paths; tests pin both happy paths and every validation failure.
- `django_strawberry_framework/connection.py` — main implementation (shipped as part of `TODO-ALPHA-030-0.0.9`)
- `django_strawberry_framework/relay.py` (new) — `DjangoNodeField`, `DjangoNodesField`, GlobalID decode dispatch
- `django_strawberry_framework/types/base.py` — `Meta.connection` / `Meta.relation_shapes` validation
- `django_strawberry_framework/types/finalizer.py` — auto-upgrade reverse-FK / M2M to Connection
- `django_strawberry_framework/test/relay.py` (new) — test helpers
- `tests/test_relay_node_field.py`, `tests/test_relay_connection.py` (new)
- `examples/fakeshop/test_query/test_library_api.py` — Relay-shape HTTP tests
- `examples/fakeshop/apps/products/schema.py` — Relay surface activation (lit up at fakeshop activation time)
- `docs/spec-relay_connection.md` (new)
- `docs/GLOSSARY.md` — Relay surface description
- Relay node refetch from Apollo / Relay Compiler clients (the *"Relay just works"* end state for `1.0.0`)
- Fakeshop product-catalog Relay activation (Goal 8)
- Per-type `useFragment` / `useRefetchableFragment` patterns (mechanics; the schema-side `@refetchable` directive support lives in BETTER item 39 sub-feature 5)
- Every BETTER item 39 sub-feature builds on this card's mechanics

#### Card references

- Blocked by via Planning note: blocked on `TODO-ALPHA-030-0.0.9` (`DjangoConnectionField`). When the connection field lands, this card unblocks and ships in the same release. The post-`1.0.0` "Relay magic" differentiators (type-rename GlobalID migrations, polymorphic connections, stable cursors, refetchable containers, permission-aware cursor decoding) live separately in [`BACKLOG.md`][backlog] item 39 — they extend this story rather than block it. -> `TODO-ALPHA-030-0.0.9` — `DjangoConnectionField`
- Related via Card item: `filter: <Type>FilterInput` — generated from `Meta.filterset_class` (composes with `DONE-027-0.0.8`) -> `DONE-027-0.0.8` — Filtering subsystem
- Related via Card item: `orderBy: [<Type>OrderInput!]` — generated from `Meta.orderset_class` (composes with `WIP-ALPHA-028-0.0.8`) -> `WIP-ALPHA-028-0.0.8` — Ordering subsystem
- Related via Card item: `search: String` — generated from `Meta.search_fields` (composes with `TODO-BETA-045-0.1.2` — note: search is `1.0.0` scope, ships after `0.1.0`; until then, search arg is absent) -> `TODO-BETA-045-0.1.2` — `Meta.search_fields` support
- Related via Card item: `TODO-ALPHA-030-0.0.9` (`DjangoConnectionField`) — **hard dependency**; this card unblocks when 026 lands. -> `TODO-ALPHA-030-0.0.9` — `DjangoConnectionField`
- Related via Card item: `DONE-027-0.0.8` (Filtering subsystem) — soft dependency for the filter argument on Connections. -> `DONE-027-0.0.8` — Filtering subsystem
- Related via Card item: `WIP-ALPHA-028-0.0.8` (Ordering subsystem) — soft dependency for the orderBy argument on Connections. -> `WIP-ALPHA-028-0.0.8` — Ordering subsystem
- Related via Card item: `TODO-ALPHA-032-0.0.9` (Connection-aware optimizer planning) — ships in parallel; the Node entry points and the relation-as-Connection upgrade both rely on the walker recognizing `edges { node { ... } }`. -> `TODO-ALPHA-032-0.0.9` — Connection-aware optimizer planning
- Related via Card item: `TODO-ALPHA-033-0.0.10` (Permissions subsystem) — soft dependency; the Node entry points respect `get_queryset` immediately and integrate with declared permissions when 029 lands. -> `TODO-ALPHA-033-0.0.10` — Permissions subsystem
- Related via Card item: The fakeshop `library` HTTP test suite gains Relay-shaped queries (refetch, paginated connection, cursor round-trip, `totalCount`). Fakeshop `products` activation lights up the full Relay surface as part of `TODO-BETA-049-0.1.5`. -> `TODO-BETA-049-0.1.5` — Fakeshop GraphQL schema activation
- Related via Card item: `django_strawberry_framework/connection.py` — main implementation (shipped as part of `TODO-ALPHA-030-0.0.9`) -> `TODO-ALPHA-030-0.0.9` — `DjangoConnectionField`

<a id="connection_aware_optimizer_planning"></a>
### [TODO-ALPHA-032-0.0.9 — Connection-aware optimizer planning](https://riodw.github.io/django-strawberry-framework/#connection_aware_optimizer_planning)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Planned
- Relative size: M
- Labels: `connections`, `optimizer`, `query-planning`, `relay`

#### Planning note

planned

#### Definition of done

- [ ] New spec, probably `docs/spec-connection_optimizer.md` (or folded into `docs/spec-connection.md`).
- [ ] Walker recognizes connection edge/node shapes without reaching into `DjangoConnectionField` internals.
- [ ] Tests cover the cookbook-equivalent nested-connection shape against fakeshop or the cardinality fixture.
- [ ] No regression on the existing B1-B8 plan-cache and queryset-diff coverage.

#### Files likely touched

- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/optimizer/extension.py`
- future `django_strawberry_framework/connection.py`
- mirrored optimizer tests

#### Other

- gated on `TODO-ALPHA-030-0.0.9` / Relay decisions.
- strawberry-graphql-django plans connection selections natively; graphene-django has only rudimentary connection-aware optimization (⚛️ parity-adjacent).
- bounded optimizer extension: teach the selection-walker to recognize Relay `edges { node }` and plan paginated selections. No new subpackage; touches `walker.py` / `plans.py` / `extension.py` + mirrored tests.
- The optimizer's plan cache, `select_related` / `prefetch_related` planning, FK-id elision, and queryset diffing are all proven for direct selection trees and nested non-Relay relation paths.
- Relay-style nested connection selections (`{ allObjects { edges { node { values { edges { node { value } } } } } } }`, mirroring the cookbook recipes shape) have not been exercised against the optimizer.
- The cookbook reference `AdvancedDjangoFilterConnectionField` does its own argument and queryset construction; the Strawberry equivalent will need the optimizer to recognize Relay edge/node wrappers in its selection walk.
- Selection-tree walker awareness of Relay `edges { node { ... } }` pattern.
- Connection-pagination-aware queryset planning (`Prefetch` downgrade for `connection { edges { node } }`, `total_count` aggregate cooperation, slice-aware projections).
- Plan-cache key hygiene for paginated selections (skip pagination args that do not affect selection shape, hash the ones that do).
- Strictness-mode interaction with connection paths so unplanned nested connection access still surfaces as N+1.

#### Card references

- Related via Card item: gated on `TODO-ALPHA-030-0.0.9` / Relay decisions. -> `TODO-ALPHA-030-0.0.9` — `DjangoConnectionField`

<a id="permissions_subsystem"></a>
### [TODO-ALPHA-033-0.0.10 — Permissions subsystem](https://riodw.github.io/django-strawberry-framework/#permissions_subsystem)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Severity: Major
- Status: Planned
- Relative size: L
- Labels: `optimizer`, `permissions`, `public-api`, `security`

#### Planning note

planned

#### Dependencies

- `TODO-ALPHA-030-0.0.9` — `DjangoConnectionField`

#### Scope

- `apply_cascade_permissions`
- per-field permission hooks declared via `Meta`
- integration with optimizer `Prefetch` downgrade
- composable permission rules that remain visible from the owning type/query surface

#### Definition of done

- [ ] Add `docs/spec-permissions.md`.
- [ ] Implement `django_strawberry_framework/permissions.py` or a `permissions/` package if the surface grows.
- [ ] Add `tests/test_permissions.py`.
- [ ] Define the `Meta` surface for per-field permissions and promote keys only when applied end-to-end.
- [ ] Use real fakeshop permission users through `services.create_users(1)` in example tests where the system-under-test is the example project.
- [ ] Check all permission-related ORM paths for N+1 behavior.

#### Foundation-slice seam

- `apply_cascade_permissions(cls, queryset, info)` walks the model graph at call time; `registry.iter_definitions()` (shipped in 0.0.4) is the public iterator that walk uses to find each owner type's `get_queryset`.
- `_attach_relation_resolvers` already accepts a `skip_field_names` set so consumer-authored fields are not clobbered; field-level permission hooks (`fields_class`) extend the same skip-set semantics.

#### Dependencies

- `DjangoType.get_queryset`
- optimizer `Prefetch` downgrade
- future `DjangoConnectionField`

#### Other

- for the fakeshop example and real usage.
- django-graphene-filters ships rich cascade + per-field permissions; strawberry-graphql-django's per-field story is weaker (🍓 parity-adjacent).
- permissions/visibility is security-relevant and blocks the fakeshop real-usage story.
- full subsystem: `apply_cascade_permissions`, per-field `Meta` permission hooks, and optimizer `Prefetch`-downgrade integration. New `permissions.py` (or package) + `docs/spec-permissions.md` + tests.
- Each node type writes visibility ONCE in `get_queryset`
- `apply_cascade_permissions(node_class, queryset, info, fields=None)`
- **Cycle detection** via a `ContextVar` "seen" set (`:16`, `:61-69`) — correct for
- **Single-column FK / O2O only**: skip relations without a `column` attribute, so
- **Multi-DB / sharding**: the target visibility subquery is pinned to the caller's
- **Nullable FK rows preserved** (a NULL FK references no hidden target) (`:103-105`).
- Optional `fields=` to cascade only specific FK names (`:82-84`).
- The contract is proven across depth in
- `test_permissions_nested.py::test_not_authenticated_cascade_permissions` — an
- `test_permissions.py` — root cascade counts (`cascade_public_count` = public rows
- `test_permissions_nested.py::test_view_object_user_object_type_id_consistency` —
- `test_permissions_async.py`, `test_permissions_combos.py`,
- Upstream's `check_<field>_permission(info)` lives on `AdvancedFieldSet`
- `AggregateSet` carries its own `check_<field>_permission` /
- A per-field **filter-denial** gate (raise to block *filtering by* a field) exists in
- EXISTS: per-active-`RelatedFilter`-branch `get_queryset` scoping
- EXISTS (registry seam): walk owner types via `registry.iter_definitions()` to find
- MISSING: the parent-queryset FK cascade itself — a framework
- RECONCILE: the framework currently ships a per-field FILTER-denial gate
- `apply_cascade_permissions(cls, queryset, info)` with sync AND async variants
- Port the four upstream invariants verbatim with a test each: ContextVar cycle guard;
- Hidden-FK semantics reached via selection: upstream sentinels with a real id —
- Per-field permission hooks via `Meta` (Scope) — pin whether they live on the FieldSet
- Optimizer `Prefetch`-downgrade integration (Scope): a cascaded relation must downgrade
- Composability: permission rules stay visible from the owning type/query surface (Scope).
- **Double-fire + ordering of related-branch gates** (Medium). `apply_sync` /
- **`check_permissions` back-compat shim regresses the per-lookup gate-name bug**
- **`_normalize_input` recomputed 3x per `apply`** (Low / perf).
- Does `check_<field>_permission(self, request)` (filter-denial) survive, deprecate, or
- Hidden-FK semantics: exclude row vs null field vs sentinel — and the cross-depth id
- Cascade performance: subquery-per-FK vs a single annotated pass; N+1 under nested
- M2M / reverse-relation visibility (upstream's cascade skips M2M) — in scope here or

#### Card references

- Dependency via Dependencies section: future `DjangoConnectionField` -> `TODO-ALPHA-030-0.0.9` — `DjangoConnectionField`

<a id="mutations_auto_generated_input_types"></a>
### [TODO-ALPHA-034-0.0.11 — Mutations + auto-generated Input types](https://riodw.github.io/django-strawberry-framework/#mutations_auto_generated_input_types)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Planned
- Relative size: XL
- Labels: `graphql-api`, `mutations`, `permissions`, `public-api`

#### Planning note

needs spec

#### Dependencies

- `DONE-018-0.0.6` — Multiple DjangoTypes per model with `Meta.primary`
- `TODO-ALPHA-033-0.0.10` — Permissions subsystem

#### Definition of done

- [ ] Add `docs/spec-mutations.md`.
- [ ] Implement `django_strawberry_framework/mutations/` (sets, fields, resolvers, input-type generation) on the DRF-style Meta surface (`Meta.input_class`, `Meta.partial_input_class`, etc.).
- [ ] Auto-generated input types respect the relation-override contract pinned in `DONE-010-0.0.4`.
- [ ] Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `TODO-ALPHA-035-0.0.11`, `TODO-ALPHA-036-0.0.11`, and `TODO-ALPHA-037-0.0.11`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings).
- [ ] Tests under `tests/mutations/`.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` exercising the products write surface.

#### Files likely touched

- `django_strawberry_framework/mutations/` (new)
- `django_strawberry_framework/types/base.py`
- `tests/mutations/` (new)
- `examples/fakeshop/apps/products/schema.py`

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/mutations/` — `mutations.py` (create/update/delete classes), `fields.py` (`DjangoMutationField`), `resolvers.py` (sync/async write resolvers), `types.py` (input-type generation).

#### Why it matters

- Mutations are the single largest unscoped gap against `strawberry-graphql-django`. Consumers migrating from strawberry-graphql-django will notice the missing write side immediately.
- `strawberry-django` exposes `create`, `update`, `delete`, custom mutations, and auto-generated `Input` / `PartialInput` types per model. These compose with permissions and the optimizer.

#### Dependencies

- `DONE-018-0.0.6` (`Meta.primary`) — explicit primary type drives mutation target resolution.
- `TODO-ALPHA-033-0.0.10` (permissions) — write mutations need to compose with `apply_cascade_permissions`.

#### Other

- mutations are the single largest unscoped gap vs strawberry-graphql-django (create / update / delete + auto-generated Input / PartialInput types).
- no on-board predecessor.
- `DONE-027-0.0.8`-scale. The single largest unscoped gap versus strawberry-graphql-django. New `mutations/` subpackage (sets / fields / resolvers / input-type generation) + spec + tests + live HTTP, plus the shared `errors: list[FieldError]` envelope reused by 031 / 032 / 033.

#### Card references

- Dependency via Dependencies section: `DONE-018-0.0.6` (`Meta.primary`) — explicit primary type drives mutation target resolution. -> `DONE-018-0.0.6` — Multiple DjangoTypes per model with `Meta.primary`
- Dependency via Dependencies section: `TODO-ALPHA-033-0.0.10` (permissions) — write mutations need to compose with `apply_cascade_permissions`. -> `TODO-ALPHA-033-0.0.10` — Permissions subsystem
- Related via Card item: Auto-generated input types respect the relation-override contract pinned in `DONE-010-0.0.4`. -> `DONE-010-0.0.4` — 0.0.4 foundation slice (definition-order independence)
- Related via Card item: Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `TODO-ALPHA-035-0.0.11`, `TODO-ALPHA-036-0.0.11`, and `TODO-ALPHA-037-0.0.11`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings). -> `TODO-ALPHA-035-0.0.11` — Upload scalar and file / image field mapping
- Related via Card item: Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `TODO-ALPHA-035-0.0.11`, `TODO-ALPHA-036-0.0.11`, and `TODO-ALPHA-037-0.0.11`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings). -> `TODO-ALPHA-036-0.0.11` — Form-based mutations (Django Forms / ModelForms)
- Related via Card item: Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; reused unchanged by `TODO-ALPHA-035-0.0.11`, `TODO-ALPHA-036-0.0.11`, and `TODO-ALPHA-037-0.0.11`. Shape mirrors graphene-django's `ErrorType` (field name + list of message strings). -> `TODO-ALPHA-037-0.0.11` — DRF serializer mutations (`SerializerMutation`)
- Related via Card item: `DONE-027-0.0.8`-scale. The single largest unscoped gap versus strawberry-graphql-django. New `mutations/` subpackage (sets / fields / resolvers / input-type generation) + spec + tests + live HTTP, plus the shared `errors: list[FieldError]` envelope reused by 031 / 032 / 033. -> `DONE-027-0.0.8` — Filtering subsystem

<a id="upload_scalar_and_file_image_field_mapping"></a>
### [TODO-ALPHA-035-0.0.11 — Upload scalar and file / image field mapping](https://riodw.github.io/django-strawberry-framework/#upload_scalar_and_file_image_field_mapping)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Planned
- Relative size: S
- Labels: `converters`, `mutations`, `scalars`, `uploads`

#### Planning note

planned

#### Definition of done

- [ ] Scalar conversion in `types/converters.py` returns `DjangoFileType` / `DjangoImageType` (or local equivalents) for `FileField` / `ImageField`.
- [ ] Mutation input-type generation (`TODO-ALPHA-034-0.0.11`) maps the same fields to Strawberry's `Upload` scalar.
- [ ] Synthetic-model tests cover both read and write paths.
- [ ] `docs/GLOSSARY.md` documents the conversion table change.

#### Files likely touched

- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/mutations/` (input mapping)
- `tests/types/test_converters.py`

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/fields/types.py` — output mappings `files.FileField: DjangoFileType`, `files.ImageField: DjangoImageType`; input mappings `files.FileField: Upload`, `files.ImageField: Upload`.

#### Why it matters

- `strawberry-graphql-django` maps `FileField` / `ImageField` to `Upload` on the input side and to `DjangoFileType` / `DjangoImageType` (with `name` / `path` / `size` / `url`) on the output side. Without it, every consumer that touches user uploads has to hand-roll the mapping.

#### Other

- strawberry-graphql-django maps `FileField` / `ImageField` to `Upload` (input) and file/image output types.
- pairs with `TODO-ALPHA-034-0.0.11` for the write side.
- bounded converter-table addition: `FileField` / `ImageField` → file/image output types on read, `Upload` on the input side. Touches `converters.py` + mutation input mapping + tests. Pairs with 028.

#### Card references

- Related via Card item: Mutation input-type generation (`TODO-ALPHA-034-0.0.11`) maps the same fields to Strawberry's `Upload` scalar. -> `TODO-ALPHA-034-0.0.11` — Mutations + auto-generated Input types
- Related via Card item: pairs with `TODO-ALPHA-034-0.0.11` for the write side. -> `TODO-ALPHA-034-0.0.11` — Mutations + auto-generated Input types

<a id="form_based_mutations_django_forms_modelforms"></a>
### [TODO-ALPHA-036-0.0.11 — Form-based mutations (Django Forms / ModelForms)](https://riodw.github.io/django-strawberry-framework/#form_based_mutations_django_forms_modelforms)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Severity: Major
- Status: Planned
- Relative size: L
- Labels: `forms`, `mutations`, `public-api`

#### Planning note

needs spec

#### Dependencies

- `TODO-ALPHA-034-0.0.11` — Mutations + auto-generated Input types

#### Definition of done

- [ ] Add `docs/spec-form_mutations.md`.
- [ ] Implement `django_strawberry_framework/forms/` on the DRF-style Meta surface (`Meta.form_class`, `Meta.return_field_name`, etc.) rather than graphene's `MutationOptions` pattern.
- [ ] Form-field → Strawberry input mapping lives in `forms/converter.py` and reuses the scalar conversion registry where field types overlap.
- [ ] Validation errors surface through the shared `errors: list[FieldError]` envelope defined in `TODO-ALPHA-034-0.0.11`, populated from `form.errors`.
- [ ] Tests under `tests/forms/`.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` exercising both a plain `Form` mutation and a `ModelForm` mutation.

#### Files likely touched

- `django_strawberry_framework/forms/` (new)
- `tests/forms/` (new)
- `examples/fakeshop/apps/products/schema.py`

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/mutation.py` — `BaseDjangoFormMutation`, `DjangoFormMutationOptions`, `DjangoFormMutation`, `DjangoModelDjangoFormMutationOptions`, `DjangoModelFormMutation`, plus `fields_for_form(form, only_fields, exclude_fields)` helper.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/converter.py` — `convert_form_field` registry mapping Django form fields → GraphQL types.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/types.py` — `ErrorType` envelope shape.

#### Why it matters

- `graphene-django` ships `DjangoFormMutation` and `DjangoModelFormMutation`: mutation classes that consume a Django `Form` / `ModelForm` and translate field validation + `cleaned_data` into a GraphQL mutation surface. Many graphene-django consumers rely on this as their write-side abstraction because it reuses validation they already have.
- Without an equivalent, graphene-django migrants must rewrite every form-backed mutation against the lower-level mutation surface from `TODO-ALPHA-034-0.0.11`.

#### Dependencies

- `TODO-ALPHA-034-0.0.11` — general mutation infrastructure (input-type generation, mutation-field plumbing) is the foundation form mutations attach to.

#### Other

- graphene-django ships `DjangoFormMutation` / `DjangoModelFormMutation`.
- no on-board predecessor.
- new `forms/` subpackage (form-field converter + `Form`/`ModelForm` mutation classes) on the DRF-style Meta surface; reuses 028's mutation infra + shared error envelope. Spec + tests + live HTTP.

#### Card references

- Dependency via Dependencies section: `TODO-ALPHA-034-0.0.11` — general mutation infrastructure (input-type generation, mutation-field plumbing) is the foundation form mutations attach to. -> `TODO-ALPHA-034-0.0.11` — Mutations + auto-generated Input types
- Related via Card item: Validation errors surface through the shared `errors: list[FieldError]` envelope defined in `TODO-ALPHA-034-0.0.11`, populated from `form.errors`. -> `TODO-ALPHA-034-0.0.11` — Mutations + auto-generated Input types
- Related via Card item: Without an equivalent, graphene-django migrants must rewrite every form-backed mutation against the lower-level mutation surface from `TODO-ALPHA-034-0.0.11`. -> `TODO-ALPHA-034-0.0.11` — Mutations + auto-generated Input types

<a id="drf_serializer_mutations_serializermutation"></a>
### [TODO-ALPHA-037-0.0.11 — DRF serializer mutations (`SerializerMutation`)](https://riodw.github.io/django-strawberry-framework/#drf_serializer_mutations_serializermutation)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Severity: Major
- Status: Planned
- Relative size: L
- Labels: `mutations`, `public-api`, `serializers`

#### Planning note

needs spec

#### Dependencies

- `TODO-ALPHA-034-0.0.11` — Mutations + auto-generated Input types

#### Definition of done

- [ ] Add `docs/spec-serializer_mutations.md`.
- [ ] Implement `django_strawberry_framework/rest_framework/` exposing `SerializerMutation` (final name pinned during implementation) on the DRF-style Meta surface: `Meta.serializer_class`, `Meta.lookup_field`, `Meta.model_operations`, `Meta.optional_fields`.
- [ ] Serializer-field → Strawberry input mapping lives in `rest_framework/serializer_converter.py`, dual-purposed for inputs and outputs (mirroring graphene's `is_input=True` flag).
- [ ] `rest_framework` is a soft dependency: package import must succeed without DRF installed; the helper raises `ImportError` with an install hint when actually called.
- [ ] Validation errors surface through the shared `errors: list[FieldError]` envelope from `TODO-ALPHA-034-0.0.11`, populated from `serializer.errors`.
- [ ] Tests under `tests/rest_framework/`.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` exercising a `ModelSerializer` mutation.

#### Files likely touched

- `django_strawberry_framework/rest_framework/` (new)
- `tests/rest_framework/` (new)
- `examples/fakeshop/apps/products/schema.py`

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/mutation.py` — `SerializerMutationOptions` carrying `lookup_field`, `model_class`, `model_operations=["create", "update"]`, `serializer_class`, `optional_fields`; `SerializerMutation` class; `fields_for_serializer(serializer, only_fields, exclude_fields, is_input=False, convert_choices_to_enum=True, lookup_field=None, optional_fields=())` helper.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/serializer_converter.py` — DRF-field → GraphQL-type registry; same module covers input and output via `is_input` flag.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/rest_framework/types.py` — shared `ErrorType` envelope.

#### Why it matters

- `graphene-django` ships `SerializerMutation`, which builds a mutation from a DRF `Serializer` / `ModelSerializer`. This is the highest-leverage write-side feature for DRF migrants — they already have serializers defined and want to reuse them in GraphQL.
- [`GOAL.md`][goal] explicitly names DRF as a target migration source ("keep the public API familiar to Django, DRF, and django-filter users"). Shipping `SerializerMutation` is on-mission, not just a parity item.

#### Dependencies

- `TODO-ALPHA-034-0.0.11` — general mutation infrastructure (including the shared `errors` envelope).

#### Other

- graphene-django ships `SerializerMutation`; the highest-leverage write-side feature for DRF migrants.
- no on-board predecessor.
- new `rest_framework/` subpackage (serializer converter dual-purposed for inputs + outputs, plus `SerializerMutation`); soft DRF dependency. Reuses 028's infra + error envelope. Spec + tests + live HTTP.

#### Card references

- Dependency via Dependencies section: `TODO-ALPHA-034-0.0.11` — general mutation infrastructure (including the shared `errors` envelope). -> `TODO-ALPHA-034-0.0.11` — Mutations + auto-generated Input types
- Related via Card item: Validation errors surface through the shared `errors: list[FieldError]` envelope from `TODO-ALPHA-034-0.0.11`, populated from `serializer.errors`. -> `TODO-ALPHA-034-0.0.11` — Mutations + auto-generated Input types

<a id="auth_mutations_login_logout_register"></a>
### [TODO-ALPHA-038-0.0.11 — Auth mutations (login / logout / register)](https://riodw.github.io/django-strawberry-framework/#auth_mutations_login_logout_register)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Planned
- Relative size: M
- Labels: `auth`, `mutations`, `public-api`

#### Planning note

planned

#### Definition of done

- [ ] Implement `django_strawberry_framework/auth/` with `login_mutation`, `logout_mutation`, `register_mutation`, and a `current_user` query helper, each composable with the existing permissions surface.
- [ ] Mirrored tests under `tests/auth/`.
- [ ] Documented as opt-in: consumers must import explicitly; auth mutations are not injected into every schema.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/auth/` — `mutations.py` (login / logout / register), `queries.py` (`current_user`), `utils.py`.

#### Why it matters

- `strawberry-graphql-django` ships a small auth-mutations module so consumers don't have to hand-wire the most common Django auth flows. Natural follow-on once general mutations land.

#### Other

- strawberry-graphql-django ships a small auth-mutations module.
- depends on `TODO-ALPHA-034-0.0.11`.
- new `auth/` module (`login` / `logout` / `register` + `current_user` query helper) composing with permissions; builds on 028's mutation infra. Mirrored tests; opt-in import.

#### Card references

- Related via Card item: depends on `TODO-ALPHA-034-0.0.11`. -> `TODO-ALPHA-034-0.0.11` — Mutations + auto-generated Input types

<a id="channels_asgi_router_migration_aid"></a>
### [TODO-ALPHA-039-0.0.12 — Channels ASGI router (migration aid)](https://riodw.github.io/django-strawberry-framework/#channels_asgi_router_migration_aid)

- Priority: Low
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Low
- Status: Planned
- Relative size: S
- Labels: `asgi`, `channels`, `django-integration`

#### Planning note

planned

#### Definition of done

- [ ] Implement `django_strawberry_framework/routers.py` exposing `DjangoGraphQLProtocolRouter` (final name pinned during implementation).
- [ ] `channels` is a soft dependency: top-level package import must not fail if `channels` is not installed. The helper wraps `channels` imports lazily and raises `ImportError` with an install hint when it is actually called.
- [ ] Tests under `tests/test_routers.py` exercise both the channels-present and channels-absent paths.
- [ ] Migration guide (`TODO-BETA-051-0.1.6`) gains a one-row entry in its "symbol equivalents" table mapping `AuthGraphQLProtocolTypeRouter` → `DjangoGraphQLProtocolRouter`, so the symbol rename is documented in one canonical location.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/routers.py` — `AuthGraphQLProtocolTypeRouter` wrapping `ProtocolTypeRouter`, `URLRouter`, `AllowedHostsOriginValidator`, `AuthMiddlewareStack`, plus `GraphQLHTTPConsumer` / `GraphQLWSConsumer`.

#### Architectural posture

- The router helper must use a **distinctly-ours symbol name** (working name: `DjangoGraphQLProtocolRouter`) so the module is unambiguously ours and does not impersonate the upstream API. This respects the [`GOAL.md`][goal] non-goal "a thin wrapper around `strawberry-graphql-django`".
- Migration ergonomics are preserved by the upstream-equivalent mapping in the migration guide (`TODO-BETA-051-0.1.6`), not by copying the symbol name. A migrant changes one import line: `from strawberry_django.routers import AuthGraphQLProtocolTypeRouter` → `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`.

#### Why it matters

- `strawberry-graphql-django` ships a small `routers.py` that builds a `ProtocolTypeRouter` over `GraphQLHTTPConsumer` and `GraphQLWSConsumer` for consumers using Channels. The module is ~30 lines but is the single import that makes ASGI / WebSocket migration painless.
- Shipping a functionally-equivalent helper lets strawberry-graphql-django migrants update one import line in their ASGI entrypoint. This card exists primarily to reduce migration friction, not to expand the API surface.

#### Other

- small slice; explicit migration aid.
- strawberry-graphql-django ships a Channels `ProtocolTypeRouter` helper; graphene-django ships none.
- small `routers.py` (~30 lines) with a soft `channels` dependency; tests for both channels-present and channels-absent paths. Pure migration-aid card.

#### Card references

- Related via Card item: Migration guide (`TODO-BETA-051-0.1.6`) gains a one-row entry in its "symbol equivalents" table mapping `AuthGraphQLProtocolTypeRouter` → `DjangoGraphQLProtocolRouter`, so the symbol rename is documented in one canonical location. -> `TODO-BETA-051-0.1.6` — Migration and adoption guides
- Related via Card item: Migration ergonomics are preserved by the upstream-equivalent mapping in the migration guide (`TODO-BETA-051-0.1.6`), not by copying the symbol name. A migrant changes one import line: `from strawberry_django.routers import AuthGraphQLProtocolTypeRouter` → `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`. -> `TODO-BETA-051-0.1.6` — Migration and adoption guides

<a id="debug_toolbar_middleware"></a>
### [TODO-ALPHA-040-0.0.12 — Debug-toolbar middleware](https://riodw.github.io/django-strawberry-framework/#debug_toolbar_middleware)

- Priority: Low
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Low
- Status: Planned
- Relative size: M
- Labels: `debugging`, `django-integration`, `middleware`

#### Planning note

planned

#### Definition of done

- [ ] Implement `django_strawberry_framework/middleware/debug_toolbar.py` exposing a `DebugToolbarMiddleware` that **subclasses** `debug_toolbar.middleware.DebugToolbarMiddleware` and overrides `process_view` + `_postprocess` for the two injection paths above.
- [ ] Ship the matching template asset at `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`; the middleware renders it via `render_to_string(...)` into HTML responses for the GraphiQL view.
- [ ] Introspection-query skip behavior preserved (no payload injection when `operationName == "IntrospectionQuery"`).
- [ ] `debug_toolbar` is a soft dependency: top-level package import must succeed without `django-debug-toolbar` installed; the middleware module raises `ImportError` with an install hint when actually imported.
- [ ] In-process test against a fakeshop request that emits SQL, covering both the GraphiQL HTML path and the JSON operation path.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/middlewares/debug_toolbar.py` — `DebugToolbarMiddleware` (subclasses upstream `debug_toolbar.middleware.DebugToolbarMiddleware`); module-level `_get_payload` helper; `_HTML_TYPES` constant for content-type sniffing.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html` — HTML snippet rendered into the GraphiQL response; ships as a template asset alongside the Python module.

#### Architectural posture

- **Not a from-scratch middleware**: strawberry-django **subclasses** `debug_toolbar.middleware.DebugToolbarMiddleware` and overrides `process_view` (to tag GraphiQL requests) and `_postprocess` (to inject the toolbar payload into the response). Our equivalent follows the same subclass-and-override shape; we do not re-implement the panel-rendering logic that `django-debug-toolbar` already owns.
- **GraphiQL-view detection**: strawberry-django tags `request._is_graphiql = bool(view and issubclass(view, BaseView))` where `BaseView` is `strawberry.django.views.BaseView`. Our equivalent uses the same `issubclass` check against whichever view class the package settles on (working name `DjangoGraphQLView`; pinned during implementation).
- **Two output paths, not one**:
- **HTML response** (the GraphiQL page itself): the middleware appends a rendered toolbar template to the response body and refreshes `Content-Length`.
- **JSON response** (a `/graphql/` operation result): the middleware parses the body, injects a `debugToolbar` key carrying per-panel `title` / `subtitle` metadata plus the toolbar's `requestId`, and re-encodes via `DjangoJSONEncoder`.
- **Introspection-query skip**: payload injection is suppressed when `operationName == "IntrospectionQuery"` so IDEs (Apollo Sandbox, etc.) that poll introspection on every keystroke don't flood their request history. Carry this behavior over.

#### Why it matters

- `strawberry-graphql-django` ships a `middlewares/debug_toolbar.py` so `django-debug-toolbar`'s SQL panel captures queries triggered by GraphQL resolvers. Without it, developers can't see the SQL hit by their queries during a `/graphql/` request.
- `graphene-django` ships **no** equivalent; this card is strawberry-graphql-django parity only.

#### Other

- developer experience.
- strawberry-graphql-django ships a debug-toolbar middleware; graphene-django ships none.
- subclass django-debug-toolbar's middleware with two injection paths (GraphiQL HTML + `/graphql/` JSON), a template asset, introspection-skip behavior, and a soft dependency. Single module + tests.

<a id="test_client_helper"></a>
### [TODO-ALPHA-041-0.0.12 — Test client helper](https://riodw.github.io/django-strawberry-framework/#test_client_helper)

- Priority: Low
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Low
- Status: Planned
- Relative size: M
- Labels: `graphql-api`, `test-client`, `tests`, `uploads`

#### Planning note

planned

#### Dependencies

- `TODO-ALPHA-035-0.0.11` — Upload scalar and file / image field mapping

#### Definition of done

- [ ] Implement `django_strawberry_framework/test/client.py` exposing `TestClient` / `AsyncTestClient` (per the inheritance shape pinned above) plus a `GraphQLTestMixin` and two concrete `(Mixin, TestCase)` / `(Mixin, TransactionTestCase)` combinations for the unittest crowd.
- [ ] Mixin carries `assertResponseNoErrors` / `assertResponseHasErrors` helpers (or the equivalent named for the chosen `.query()` return type).
- [ ] Project-wide endpoint settings key (working name `GRAPHQL_TESTING_ENDPOINT`, final name pinned during implementation) under `DJANGO_STRAWBERRY_FRAMEWORK`, with constructor / per-call override.
- [ ] Multipart file-upload support on `request()` so consumers can drive `Upload`-scalar mutations from the same helper once `TODO-ALPHA-035-0.0.11` ships.
- [ ] Live HTTP tests under `examples/fakeshop/test_query/` switch to the helper.
- [ ] Tests under `tests/test/test_client.py`.

#### Verified in upstream

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/test/client.py` — `TestClient` (subclasses Strawberry's `strawberry.test.BaseGraphQLTestClient`), `AsyncTestClient` (subclasses `TestClient`, takes an `AsyncClient`, overrides `.query()` and `.login()`). The `.query()` / `.mutate()` API surface lives on the upstream `BaseGraphQLTestClient`; strawberry-django adds Django-specific `request()`, `login()`, and the async `query()` override. `request()` switches to `format="multipart"` when `files=` is provided.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/utils/testing.py` — module-level `graphql_query` function; `GraphQLTestMixin` (the reusable mixin carrying `.query(...)`, `assertResponseNoErrors`, `assertResponseHasErrors`); `GraphQLTestCase` (`(GraphQLTestMixin, TestCase)`); `GraphQLTransactionTestCase` (`(GraphQLTestMixin, TransactionTestCase)`).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/settings.py #"TESTING_ENDPOINT"` — graphene reads `TESTING_ENDPOINT` (default `/graphql`) from its own settings dict so the testing helper has a project-wide override knob.

#### Architectural posture

- **Mixin-first shape** (graphene-django convention): the reusable piece is `GraphQLTestMixin`; the concrete `GraphQLTestCase` / `GraphQLTransactionTestCase` are two-line `(Mixin, TestCase)` / `(Mixin, TransactionTestCase)` combinations so consumers with their own custom TestCase base can compose the mixin in directly. Our equivalent follows the same mixin-first shape rather than only shipping the concrete subclasses.
- **`.query()` return type — decide before writing the spec**: strawberry-django returns a typed `Response` dataclass (`data` / `errors` / `extensions`); graphene-django's `GraphQLTestMixin.query` returns a raw Django `HttpResponse` paired with `assertResponseNoErrors` / `assertResponseHasErrors` helpers that parse the body. The two flavors are not interchangeable — pick one and pin it (the typed-dataclass shape is the more DRF-shaped choice and composes better with future typed-error work).
- **Async**: strawberry-django's `AsyncTestClient` subclasses `TestClient` (not `BaseGraphQLTestClient` directly), takes a `django.test.client.AsyncClient`, and only overrides `.query()` + `.login()`. The sync `request()` is reused via `cast("Awaitable", ...)`. Our equivalent ports the same inheritance shape (or picks a flatter alternative explicitly in the spec).
- **Endpoint resolution**: project-wide default reads from `DJANGO_STRAWBERRY_FRAMEWORK["GRAPHQL_TESTING_ENDPOINT"]` (mirrors graphene's `TESTING_ENDPOINT` knob; final settings-key name pinned during implementation), with a per-instance / per-call override identical to strawberry-django's `path` constructor argument and graphene-django's `graphql_url` per-call argument.
- **File-upload coupling**: strawberry-django's `request()` switches to `format="multipart"` when `files=` is provided. Our helper must do the same so live HTTP tests for `TODO-ALPHA-035-0.0.11` (Upload scalar) can exercise multipart uploads through the helper rather than dropping back to raw `client.post(...)` calls.
- **Strawberry base-class reuse — decide before writing the spec**: subclass `strawberry.test.BaseGraphQLTestClient` (less code, couples our `.query()` / `.mutate()` shape to upstream Strawberry's choices) vs. roll our own base (more code, full control over the public surface). The strawberry-django decision was to subclass; the package's DRF-first stance argues for considering the from-scratch alternative.

#### Why it matters

- `strawberry-graphql-django` ships `strawberry_django.test.client.TestClient`, a thin wrapper around `django.test.Client` that posts GraphQL requests with the right content type, parses the response, and exposes `.query(...)` / `.mutate(...)`.
- `graphene-django` ships `graphene_django.utils.testing` with `GraphQLTestMixin` / `GraphQLTestCase` / `GraphQLTransactionTestCase` / `graphql_query` helpers covering the same need.
- The fakeshop live tests already do this by hand; centralizing the pattern is a small win for consumers and keeps our HTTP tests crisp.

#### Dependencies

- `TODO-ALPHA-035-0.0.11` (Upload scalar) — the file-upload helper path lights up once Upload-scalar inputs exist; the helper itself ships without it but gains a tested path here.

#### Other

- developer experience.
- both upstreams ship a GraphQL test client / mixin.
- `test/client.py` (sync + async `TestClient`, a `GraphQLTestMixin`, two `(Mixin, TestCase)` combos), endpoint setting, multipart-upload support; several design decisions to pin; switch the fakeshop tests over.

#### Card references

- Dependency via Dependencies section: `TODO-ALPHA-035-0.0.11` (Upload scalar) — the file-upload helper path lights up once Upload-scalar inputs exist; the helper itself ships without it but gains a tested path here. -> `TODO-ALPHA-035-0.0.11` — Upload scalar and file / image field mapping
- Related via Card item: Multipart file-upload support on `request()` so consumers can drive `Upload`-scalar mutations from the same helper once `TODO-ALPHA-035-0.0.11` ships. -> `TODO-ALPHA-035-0.0.11` — Upload scalar and file / image field mapping
- Related via Card item: **File-upload coupling**: strawberry-django's `request()` switches to `format="multipart"` when `files=` is provided. Our helper must do the same so live HTTP tests for `TODO-ALPHA-035-0.0.11` (Upload scalar) can exercise multipart uploads through the helper rather than dropping back to raw `client.post(...)` calls. -> `TODO-ALPHA-035-0.0.11` — Upload scalar and file / image field mapping

<a id="response_extensions_debug_middleware"></a>
### [TODO-ALPHA-042-0.0.12 — Response-extensions debug middleware](https://riodw.github.io/django-strawberry-framework/#response_extensions_debug_middleware)

- Priority: Low
- Parity: ⚛️ graphene-django (Required)
- Severity: Low
- Status: Planned
- Relative size: M
- Labels: `debugging`, `graphql-api`, `middleware`

#### Planning note

planned

#### Definition of done

- [ ] Implement `django_strawberry_framework/extensions/debug.py` as a Strawberry `SchemaExtension` that captures SQL and exceptions for the in-flight operation and attaches them to the response `extensions` map (key: `debug`).
- [ ] Pin the **exposure mechanism** (response-`extensions` map vs. schema-level `_debug` field) and the **fidelity choice** (cursor-wrap port vs. `connection.queries`) in the spec; default both to the simpler choice (response-`extensions` map + `connection.queries`) unless the spec authoring round chooses otherwise.
- [ ] Output shape mirrors graphene's `DjangoDebugSQL` / `DjangoDebugException` field names where the chosen fidelity supports them; document any shape narrowing (e.g., omitted Postgres-specific fields) explicitly.
- [ ] Off by default; opt-in via the extensions list passed to `strawberry.Schema(...)`.
- [ ] Tests under `tests/extensions/test_debug.py` against a fakeshop request that emits SQL.
- [ ] Documented as the response-side counterpart to `TODO-ALPHA-040-0.0.12`.

#### Files likely touched

- `django_strawberry_framework/extensions/` (new)
- `tests/extensions/` (new)

#### Verified in upstream

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/__init__.py` — exports `DjangoDebugMiddleware`, `DjangoDebug`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/middleware.py` — `DjangoDebugContext` (lifecycle around cursor wrapping, exception capture, accumulated debug object), `DjangoDebugMiddleware` (Graphene `resolve` middleware — see Architectural posture; wraps each field resolution and returns the accumulated debug object when the field's return type matches `DjangoDebug`).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/types.py` — `class DjangoDebug(ObjectType)` with `sql: List(DjangoDebugSQL)` and `exceptions: List(DjangoDebugException)`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/sql/types.py` — `DjangoDebugSQL` shape: `vendor`, `alias`, `sql`, `duration`, `raw_sql`, `params`, `start_time`, `stop_time`, `is_slow`, `is_select`, plus Postgres-specific `trans_id`, `trans_status`, `iso_level`, `encoding`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/exception/types.py` — `DjangoDebugException` shape: `exc_type`, `message`, `stack`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/sql/tracking.py` — thread-local cursor wrapping (`wrap_cursor`, `unwrap_cursor`, `NormalCursorWrapper`, `ExceptionCursorWrapper`, `ThreadLocalState`).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/exception/formating.py` — `wrap_exception` (serializes `exc_type`, `message`, `stack`).

#### Architectural posture

- **"Middleware" is overloaded here**: graphene-django's `DjangoDebugMiddleware` is a **Graphene field-resolver middleware** (a callable invoked around each `resolve(root, info, **args)`), not a Django request/response middleware. The card title says "middleware" because that's what the graphene side calls the same idea; our Strawberry-native shape is a `SchemaExtension` (operation-scoped), not a Django middleware. The file name `middleware.py` is preserved on the graphene side for parity with their naming; ours lives under `extensions/`.
- **Exposure mechanism — pick one before writing the spec**:
- graphene-django: **schema-level**. Consumers add a `_debug: DjangoDebug` field to their query and selectively pull `{ _debug { sql { duration } } }`. Pay-for-what-you-select.
- Card's proposed Strawberry-native shape: **response-extensions-level**. Always emit the whole map under `extensions["debug"]` when the extension is enabled, or skip it entirely.
- Both end up "in the GraphQL response," but the graphene shape gives consumers per-query selectivity at the cost of needing a schema field. The Strawberry-extension shape is simpler to wire and skips schema surface entirely.
- **Fidelity tradeoff — pick one before writing the spec**:
- **Port graphene's cursor wrapping** (`sql/tracking.py`): wraps `connection.cursor` per-thread so the wrapper sees `start_time` before `execute()` and computes precise `duration`, captures Postgres-specific `iso_level` / `encoding`, surfaces `is_slow` / `is_select` flags. Higher fidelity; requires thread-local state management and `enable_instrumentation` / `disable_instrumentation` lifecycle hooks tied to the extension's operation begin / end.
- **Use `django.db.connection.queries`**: the SchemaExtension reads `connection.queries` at operation end and emits a smaller shape. Lower fidelity (relies on Django's existing logging — no Postgres-specific data, less precise timing). Trivially threadsafe; no cursor wrapping to manage.
- **Thread-local state** (if porting the cursor wrap): `sql/tracking.py::ThreadLocalState` plus `enable_instrumentation` / `disable_instrumentation` are the lifecycle hooks. The SchemaExtension's `on_operation` (or equivalent) wraps `wrap_cursor` for the request and `unwrap_cursor` on teardown. Exception capture wires through the corresponding execution hooks similarly.

#### Why it matters

- `graphene-django` ships a debug subsystem that exposes the executed SQL queries and raised exceptions for each GraphQL request via a `DjangoDebug` object. This is different from `TODO-ALPHA-040-0.0.12` (django-debug-toolbar SQL panel UI): graphene's mechanism is **inside the GraphQL response**, so frontend clients and Apollo DevTools can read it without the toolbar. Both mechanisms are useful and not mutually exclusive.
- A Strawberry-native equivalent is a small `SchemaExtension` that captures SQL (through `django.db.connection.queries` or via a port of graphene's cursor-wrap mechanism — see Architectural posture) and exceptions and attaches the result to the response's `extensions` map.
- `strawberry-graphql-django` ships **no** equivalent (no file references `connection.queries` and no `*debug*` module exists outside the toolbar middleware tracked by `TODO-ALPHA-040-0.0.12`); this card is graphene-django parity only.

#### Other

- developer experience.
- graphene-django ships an in-response `DjangoDebug` SQL/exception subsystem; strawberry-graphql-django ships none.
- distinct from `TODO-ALPHA-040-0.0.12` (Django debug toolbar).
- a Strawberry `SchemaExtension` that captures SQL + exceptions into `extensions['debug']`; one design choice between porting graphene's cursor-wrap and reading `connection.queries`. Single extension module + tests.

#### Card references

- Related via Card item: Documented as the response-side counterpart to `TODO-ALPHA-040-0.0.12`. -> `TODO-ALPHA-040-0.0.12` — Debug-toolbar middleware
- Related via Card item: `graphene-django` ships a debug subsystem that exposes the executed SQL queries and raised exceptions for each GraphQL request via a `DjangoDebug` object. This is different from `TODO-ALPHA-040-0.0.12` (django-debug-toolbar SQL panel UI): graphene's mechanism is **inside the GraphQL response**, so frontend clients and Apollo DevTools can read it without the toolbar. Both mechanisms are useful and not mutually exclusive. -> `TODO-ALPHA-040-0.0.12` — Debug-toolbar middleware
- Related via Card item: `strawberry-graphql-django` ships **no** equivalent (no file references `connection.queries` and no `*debug*` module exists outside the toolbar middleware tracked by `TODO-ALPHA-040-0.0.12`); this card is graphene-django parity only. -> `TODO-ALPHA-040-0.0.12` — Debug-toolbar middleware
- Related via Card item: distinct from `TODO-ALPHA-040-0.0.12` (Django debug toolbar). -> `TODO-ALPHA-040-0.0.12` — Debug-toolbar middleware

## To Do - Beta (1.0.0)

Cards that complete the django-graphene-filters Layer-3 richness on top of parity (`fields_class`, `aggregate_class`, `search_fields`, plus pre-stable cleanup). Each card targets its own `0.1.x` patch within the road to **1.0.0**. The final card in this column is the `1.0.0` release itself (API freeze, cleanup, verification, beta → stable cut-over). Cards in NNN order = planned ship order.

<a id="beta_release_cleanup_verification_alpha_beta"></a>
### [TODO-BETA-043-0.1.0 — Beta release (cleanup, verification, alpha → beta)](https://riodw.github.io/django-strawberry-framework/#beta_release_cleanup_verification_alpha_beta)

- Priority: High
- Severity: Major
- Status: Planned
- Relative size: M
- Labels: `cleanup`, `release`, `tests`

#### Planning note

planned

#### Definition of done

- [ ] Every other Alpha card (`ALPHA-013-0.0.6` through `ALPHA-035-0.0.12` plus `ALPHA-024-0.0.9`) is in `DONE`.
- [ ] Full test pass under each supported `(Python, Django, Strawberry)` combination.
- [ ] Coverage stays at 100% for the package source tree.
- [ ] Version bumped to `0.1.0` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock`.
- [ ] `CHANGELOG.md` `[Unreleased]` block promoted to `## [0.1.0] - YYYY-MM-DD` with a one-paragraph release summary plus the cumulative Added / Changed / Fixed / Removed sections covering `0.0.6` through `0.0.12`.
- [ ] `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, and `docs/TREE.md` cross-checked against the actual shipped surface; "shipped" / "planned" status markers updated.
- [ ] Audit pass against the parity findings: every ⚛️ and 🍓 card from the two upstream audits is either `DONE` or explicitly deferred with a recorded reason.
- [ ] Tag the release in git and publish to PyPI.

#### Files likely touched

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`

#### Why it matters

- This card is the formal cut-over from alpha (`0.0.x`) to beta (`0.1.0`). When every other Alpha card is in `DONE`, this card is the only thing left between the current state and the beta release. It exists to make the milestone explicit and to give the cleanup / verification work a place to live.
- Without a dedicated release card, the alpha → beta transition becomes an unstructured handful of doc tweaks and version bumps spread across the last few patches. Tracking it explicitly forces the parity audit and the full test pass to happen on a single named slice.

#### Other

- release card.
- release / verification card — gates the alpha → beta cut; not an upstream-parity feature.
- release-blocking.
- final card in the Alpha queue; gates the alpha → beta milestone.
- release / verification card, no new subsystem: full `(Python, Django, Strawberry)` matrix pass, 100% coverage, version bump to `0.1.0`, CHANGELOG promotion, doc status cross-check, parity audit, tag + publish.

<a id="fieldset"></a>
### [TODO-BETA-044-0.1.1 — `FieldSet`](https://riodw.github.io/django-strawberry-framework/#fieldset)

- Priority: High
- Severity: Medium
- Status: Needs spec
- Relative size: M
- Labels: `fieldsets`, `layer-3`, `public-api`

#### Planning note

needs spec or implementation slice

#### Definition of done

- [ ] Add `docs/spec-fieldset.md`.
- [ ] Implement `django_strawberry_framework/fieldset.py`.
- [ ] Add `tests/test_fieldset.py`.
- [ ] Keep the API Meta-class-driven.
- [ ] Do not top-level export until the public-surface rules are satisfied.

#### Foundation-slice seam

- `DjangoTypeDefinition.fields_class` is the forward-reserved slot the collection phase will populate.
- `Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (see also [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` custom Strawberry field class that field-level permissions will likely require).

#### Why it matters

- `FieldSet` is the smallest Layer 3 surface and can define field-selection semantics used by `DjangoConnectionField`.
- It bridges the existing `DjangoType.Meta.fields` behavior and future connection/query APIs.

#### Other

- the smallest Layer-3 subsystem: `fieldset.py` + `docs/spec-fieldset.md` + tests; defines field-selection semantics the connection field consumes. Meta-driven.

<a id="metasearch_fields_support"></a>
### [TODO-BETA-045-0.1.2 — `Meta.search_fields` support](https://riodw.github.io/django-strawberry-framework/#metasearch_fields_support)

- Priority: High
- Severity: Medium
- Status: Planned
- Relative size: M
- Labels: `connections`, `filters`, `public-api`, `search`

#### Planning note

planned; gated on `DONE-027-0.0.8` (Filtering) and `TODO-ALPHA-030-0.0.9` (DjangoConnectionField)

#### Dependencies

- `DONE-027-0.0.8` — Filtering subsystem
- `TODO-ALPHA-030-0.0.9` — `DjangoConnectionField`

#### Definition of done

- [ ] Add `docs/spec-search_fields.md`.
- [ ] Search-fields argument generation lives in `django_strawberry_framework/filters/` and reuses the same DRF-style Meta surface and argument-factory machinery as `filterset_class`.
- [ ] Single `search: String` argument surfaces on `DjangoConnectionField` consumers and produces an OR'd `icontains` queryset filter across every declared field path.
- [ ] Promote `Meta.search_fields` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the pipeline applies it end-to-end (per `TODO-BETA-047-0.1.3`).
- [ ] Tests under `tests/filters/test_search_fields.py` covering single-field, relation-path, and combined-with-filterset cases.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` exercising a search across at least one relation path.

#### Files likely touched

- `django_strawberry_framework/filters/` (search support)
- `django_strawberry_framework/types/base.py` (Meta validation; promote key)
- `tests/filters/test_search_fields.py` (new)
- `examples/fakeshop/apps/products/schema.py` (activation)

#### Why it matters

- `Meta.search_fields` is one of the five django-graphene-filters Layer-3 Meta keys explicitly listed in [`GOAL.md`][goal] alongside `filterset_class`, `orderset_class`, `aggregate_class`, and `fields_class`. Without it the package cannot claim full DGF parity at 1.0.0.
- Currently `search_fields` is in `DEFERRED_META_KEYS` and rejected at validation time. `TODO-BETA-049-0.1.5` (Fakeshop schema activation) explicitly carries a note to "move or defer `search_fields` before uncommenting" because of this gap.

#### Dependencies

- `DONE-027-0.0.8` (Filtering subsystem) — the argument factory is shared.
- `TODO-ALPHA-030-0.0.9` (`DjangoConnectionField`) — the `search: String` argument surfaces on connection fields.

#### Other

- a single `search: String` argument fanning out as an OR'd `icontains` across declared field paths; reuses `DONE-027-0.0.8`'s argument-factory machinery. Spec + tests + live HTTP + Meta-key promotion.
- `django-graphene-filters` exposes `Meta.search_fields = ("name", "description", "category__name")` — a tuple of model-field paths. The connection field gains a single `search: String` argument that fans out across the listed fields as an OR'd `icontains` filter, traversing relations through Django's standard ORM lookup syntax.

#### Card references

- Dependency via Dependencies section: `DONE-027-0.0.8` (Filtering subsystem) — the argument factory is shared. -> `DONE-027-0.0.8` — Filtering subsystem
- Dependency via Dependencies section: `TODO-ALPHA-030-0.0.9` (`DjangoConnectionField`) — the `search: String` argument surfaces on connection fields. -> `TODO-ALPHA-030-0.0.9` — `DjangoConnectionField`
- Dependency via Planning note: planned; gated on `DONE-027-0.0.8` (Filtering) and `TODO-ALPHA-030-0.0.9` (DjangoConnectionField) -> `DONE-027-0.0.8` — Filtering subsystem
- Dependency via Planning note: planned; gated on `DONE-027-0.0.8` (Filtering) and `TODO-ALPHA-030-0.0.9` (DjangoConnectionField) -> `TODO-ALPHA-030-0.0.9` — `DjangoConnectionField`
- Related via Card item: Promote `Meta.search_fields` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the pipeline applies it end-to-end (per `TODO-BETA-047-0.1.3`). -> `TODO-BETA-047-0.1.3` — Layer 3 Meta key promotion
- Related via Card item: Currently `search_fields` is in `DEFERRED_META_KEYS` and rejected at validation time. `TODO-BETA-049-0.1.5` (Fakeshop schema activation) explicitly carries a note to "move or defer `search_fields` before uncommenting" because of this gap. -> `TODO-BETA-049-0.1.5` — Fakeshop GraphQL schema activation
- Related via Card item: a single `search: String` argument fanning out as an OR'd `icontains` across declared field paths; reuses `DONE-027-0.0.8`'s argument-factory machinery. Spec + tests + live HTTP + Meta-key promotion. -> `DONE-027-0.0.8` — Filtering subsystem

<a id="aggregation_subsystem"></a>
### [TODO-BETA-046-0.1.3 — Aggregation subsystem](https://riodw.github.io/django-strawberry-framework/#aggregation_subsystem)

- Priority: Medium-high
- Severity: Major
- Status: Planned
- Relative size: L
- Labels: `aggregations`, `filters`, `layer-3`, `public-api`

#### Planning note

planned

#### Scope

- `Sum`, `Count`, `Avg`, `Min`, `Max`, `GroupBy`
- `AggregateSet`
- GraphQL argument/result factories
- `Meta.aggregate_class` promotion

#### Definition of done

- [ ] Add `docs/spec-aggregates.md`.
- [ ] Add `django_strawberry_framework/aggregates/`.
- [ ] Add mirrored `tests/aggregates/`.
- [ ] Promote `Meta.aggregate_class` only when aggregation is applied end-to-end.
- [ ] Decide result type naming and grouping semantics.
- [ ] Validate generated queryset aggregation paths.
- [ ] Keep aggregation declarations composable with filters, ordering, and connection field behavior.

#### Foundation-slice seam

- `DjangoTypeDefinition.aggregate_class` is the populated slot.
- The cookbook reference (`AdvancedAggregateSet.compute` / `acompute`) splits sync and async paths; this lines up with the existing async-resolver support in the optimizer.
- Selection-set-aware aggregate computation will reuse the optimizer plan-cache infrastructure, since the aggregate output type's selected fields drive which annotations are computed.

#### Other

- full subsystem, parallel to Ordering: reuses `DONE-027-0.0.8`'s six-layer architecture but emits `strawberry.type` output types (not input) and adds the sync/async `compute` / `acompute` split. New `aggregates/` subpackage + `docs/spec-aggregates.md` + tests.

#### Card references

- Related via Card item: full subsystem, parallel to Ordering: reuses `DONE-027-0.0.8`'s six-layer architecture but emits `strawberry.type` output types (not input) and adds the sync/async `compute` / `acompute` split. New `aggregates/` subpackage + `docs/spec-aggregates.md` + tests. -> `DONE-027-0.0.8` — Filtering subsystem

<a id="layer_3_meta_key_promotion"></a>
### [TODO-BETA-047-0.1.3 — Layer 3 Meta key promotion](https://riodw.github.io/django-strawberry-framework/#layer_3_meta_key_promotion)

- Priority: Low
- Severity: Low
- Status: Planned
- Relative size: XS
- Labels: `cleanup`, `layer-3`, `public-api`

#### Other

- each Layer 3 subsystem implementation
- `filterset_class`
- `orderset_class`
- `aggregate_class`
- `fields_class`
- `search_fields`
- Do not move a key from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` until the pipeline applies it end-to-end.
- mechanical bookkeeping: move keys from `DEFERRED_META_KEYS` → `ALLOWED_META_KEYS` as each subsystem lands end-to-end. The real work lives in the subsystem cards, not here.

<a id="stable_choice_enum_naming_override"></a>
### [TODO-BETA-048-0.1.4 — Stable choice enum naming override](https://riodw.github.io/django-strawberry-framework/#stable_choice_enum_naming_override)

- Priority: Low-medium
- Severity: Medium
- Status: Planned
- Relative size: S
- Labels: `choice-enums`, `public-api`, `schema`, `stable-api`

#### Planning note

planned

#### Definition of done

- [ ] New or amended spec documents the override key and ambiguity behavior.
- [ ] `_validate_meta` accepts the key only when the pipeline applies it end-to-end.
- [ ] `convert_choices_to_enum()` uses the explicit name when provided.
- [ ] Tests cover explicit naming, cache reuse, duplicate/conflicting names, and default first-reader behavior.

#### Files likely touched

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/registry.py`
- `tests/types/test_converters.py`

#### Other

- bounded override surface (`Meta.choice_enum_names`) preserving `(model, field)` enum reuse; touches `base.py` / `converters.py` / `registry.py` + tests.
- Choice fields generate Strawberry enums and cache them by `(model, field_name)`.
- The first `DjangoType` to read a choice column wins the generated enum's GraphQL name.
- This is deterministic for a fixed import order but still makes schema naming dependent on which type imports first.
- Add a stable override surface such as `Meta.choice_enum_names = {"status": "ItemStatusEnum"}`.
- Decide whether this belongs in the consumer-overrides spec or a small choice-enum follow-up spec.
- Preserve enum reuse by `(model, field_name)` while making the published schema name explicit when consumers need it.

<a id="fakeshop_graphql_schema_activation"></a>
### [TODO-BETA-049-0.1.5 — Fakeshop GraphQL schema activation](https://riodw.github.io/django-strawberry-framework/#fakeshop_graphql_schema_activation)

- Priority: Medium
- Severity: Medium
- Status: Planned
- Relative size: S
- Labels: `example-app`, `graphql-api`, `relay`, `schema`

#### Planning note

blocked on `TODO-ALPHA-031-0.0.9` (Relay decisions) and `TODO-BETA-047-0.1.3` (Layer 3 Meta key promotion).

#### Dependencies

- `TODO-ALPHA-031-0.0.9` — Full Relay story (Node + Connection + Root + validation)
- `TODO-BETA-047-0.1.3` — Layer 3 Meta key promotion

#### Definition of done

- [ ] Uncomment only the portions whose dependencies have shipped.
- [ ] Keep unshipped subsystem lines commented until their specs land.
- [ ] Move or defer `search_fields` before uncommenting because it is currently a rejected Meta key.
- [ ] Add in-process schema tests under `examples/fakeshop/tests/`.
- [ ] Add live `/graphql/` tests under `examples/fakeshop/test_query/` only when testing the HTTP endpoint.

#### Other

- example-wiring card: uncomment the product-catalog schema portions whose dependencies have shipped; in-process + live HTTP tests. Gated on the Layer-3 subsystems, not heavy itself.
- `examples/fakeshop/apps/products/schema.py` exposes a placeholder `hello` field for the product catalog.
- The aspirational schema block depends on `DjangoConnectionField`, Relay interfaces, filters, orders, aggregates, fieldsets, and permissions.

#### Card references

- Blocked by via Planning note: blocked on `TODO-ALPHA-031-0.0.9` (Relay decisions) and `TODO-BETA-047-0.1.3` (Layer 3 Meta key promotion). -> `TODO-ALPHA-031-0.0.9` — Full Relay story (Node + Connection + Root + validation)
- Blocked by via Planning note: blocked on `TODO-ALPHA-031-0.0.9` (Relay decisions) and `TODO-BETA-047-0.1.3` (Layer 3 Meta key promotion). -> `TODO-BETA-047-0.1.3` — Layer 3 Meta key promotion

<a id="product_catalog_layer_3_http_graphql_tests"></a>
### [TODO-BETA-050-0.1.5 — Product-catalog Layer 3 HTTP GraphQL tests](https://riodw.github.io/django-strawberry-framework/#product_catalog_layer_3_http_graphql_tests)

- Priority: Medium
- Severity: Medium
- Status: Planned
- Relative size: S
- Labels: `example-app`, `graphql-api`, `layer-3`, `tests`

#### Other

- activating the product-catalog fakeshop GraphQL schema
- connection/query fields and other Layer 3 public surfaces
- The library app already has live `/graphql/` acceptance tests under `examples/fakeshop/test_query/`.
- Future product-catalog HTTP tests should use the same placement and schema-reload pattern.
- In-process `schema.execute_sync` tests still go under `examples/fakeshop/tests/`.
- bounded test suite: live `/graphql/` acceptance tests for the activated product-catalog schema, reusing the library app's placement + schema-reload pattern.

<a id="migration_and_adoption_guides"></a>
### [TODO-BETA-051-0.1.6 — Migration and adoption guides](https://riodw.github.io/django-strawberry-framework/#migration_and_adoption_guides)

- Priority: Medium
- Severity: Medium
- Status: Planned
- Relative size: M
- Labels: `docs`, `guides`, `public-api`

#### Planning note

planned

#### Definition of done

- [ ] New docs are added for the two major migration paths.
- [ ] README and `GLOSSARY.md` link to the migration docs.
- [ ] Guides distinguish shipped migration steps from planned Layer 3 migration targets.

#### Files likely touched

- future migration docs under `docs/`
- `docs/README.md`
- `docs/GLOSSARY.md`

#### Other

- docs-only but substantial: two full migration guides (graphene-django → and strawberry-graphql-django →) plus DRF / django-filter mapping notes, with README / GLOSSARY links. No code.
- The package is intentionally shaped for teams coming from `django-filter`, DRF, `graphene-django`, and `strawberry-graphql-django`.
- The feature docs explain the positioning, but there are no dedicated migration guides yet.
- Add ability to set dsf settings to cap the number of schema hookups per model and error if it is more
- Add a `graphene-django` migration guide covering `DjangoObjectType` to `DjangoType`, enum/field conversion differences, query optimizations, and Relay caveats.
- Add a `strawberry-graphql-django` migration guide covering decorator-to-`Meta` translation, optimizer differences, `get_queryset`, and optimizer hints.
- Add concise notes for DRF / django-filter users mapping serializers/filtersets/orders into the planned Layer 3 surfaces.

<a id="adversarial_non_live_test_suite_try_to_break_it_not_just_cover_lines"></a>
### [TODO-BETA-052-0.1.7 — Adversarial non-live test suite (try to break it, not just cover lines)](https://riodw.github.io/django-strawberry-framework/#adversarial_non_live_test_suite_try_to_break_it_not_just_cover_lines)

- Priority: Medium-high
- Severity: Medium
- Status: Planned
- Relative size: M
- Labels: `adversarial-testing`, `hardening`, `tests`

#### Planning note

planned

#### Definition of done

- [ ] A dedicated adversarial suite under `tests/` exercises the categories above; every hostile input fails LOUDLY with a typed error rather than crashing.
- [ ] Root `tests/` holds only genuinely-unreachable-from-live cases plus the new adversarial ones; any remaining live-reachable duplicates are pruned (per `examples/fakeshop/test_query/README.md`).
- [ ] Coverage stays at 100% without relying on the pruned duplicates.

#### Files likely touched

- new adversarial test modules under `tests/`
- `examples/fakeshop/test_query/README.md` (cross-reference the adversarial-vs-unreachable split)

#### Why it matters

- `fail_under = 100` proves every LINE executes, not that the code is CORRECT under abuse. The failures that matter — deeply nested logic trees, malformed / wrong-`type_name` GlobalIDs, cyclic `RelatedFilter` graphs, conflicting multi-owner reuse, UNSET/None permutations, oversized `Meta.fields = "__all__"` expansions, unicode / null-byte / oversized values — are exactly the ones a happy-path live query never exercises.

#### Other

- An in-process `tests/` (NON-`/graphql/`) hardening pass whose goal is to BREAK the framework, not to earn line coverage. Live-reachable coverage already lives in `examples/fakeshop/test_query/` per its README rule; the root `tests/` tree is reserved for cases a live query cannot reach — fill it with hostile / pathological inputs rather than coverage duplicates.
- Root `tests/` historically mixed genuinely-unreachable-from-live cases with some that merely duplicated coverage already earned by the live `test_query/` suites (a first prune of redundant filter unit tests landed alongside `DONE-027-0.0.8`).
- There is no deliberate "try to break it" suite; adversarial inputs are covered only incidentally.
- Property-based / fuzz-style tests (e.g. Hypothesis) for the filter input normalizer, GlobalID decode/validate, and `Meta.fields = "__all__"` expansion.
- Pathological structure: logic-tree nesting past `_MAX_LOGIC_DEPTH`, cyclic / self-referential `RelatedFilter` graphs, conflicting multi-owner reuse, proxy / MTI model mixing.
- Hostile wire values: bad-base64 / wrong-`type_name` GlobalIDs, oversized `in` lists, unicode / emoji / null bytes, `strawberry.UNSET` / `None` across every operator-bag slot.
- Scale / resource: very large `"__all__"` field sets and many-relation BFS; assert every failure surfaces as `ConfigurationError` / `GraphQLError` (never a bare traceback) and finalize stays bounded.
- Extend the same philosophy to the future order / aggregate / fieldset subsystems as they land.

#### Card references

- Related via Card item: Root `tests/` historically mixed genuinely-unreachable-from-live cases with some that merely duplicated coverage already earned by the live `test_query/` suites (a first prune of redundant filter unit tests landed alongside `DONE-027-0.0.8`). -> `DONE-027-0.0.8` — Filtering subsystem

<a id="stable_release_api_freeze_cleanup_verification_beta_stable"></a>
### [TODO-STABLE-053-1.0.0 — Stable release (API freeze, cleanup, verification, beta → stable)](https://riodw.github.io/django-strawberry-framework/#stable_release_api_freeze_cleanup_verification_beta_stable)

- Priority: Critical
- Severity: Major
- Status: Planned
- Relative size: M-L
- Labels: `cleanup`, `release`, `stable-api`, `tests`

#### Planning note

planned; this is the final card in the Beta queue and gates the beta → stable milestone

#### Definition of done

- [ ] Every other Beta card (`TODO-BETA-044-0.1.1` through `TODO-BETA-051-0.1.6` plus `TODO-BETA-047-0.1.3` and `TODO-BETA-050-0.1.5`) is in `DONE`.
- [ ] API surface audit: top-level `__all__` confirmed stable; every public symbol documented; no `# experimental` markers in shipped code; no `_private` symbols accidentally referenced from docs.
- [ ] SemVer policy committed in CHANGELOG header: every release after `1.0.0` follows MAJOR / MINOR / PATCH rules strictly; pre-`0.1.0` deprecation shims removed entirely.
- [ ] Full async + sync coverage matrix validated; no `sync_to_async` workarounds remain on any resolver path.
- [ ] Security review: input-validation surfaces (mutations, filters, GlobalID decoding) audited for injection / authorization gaps.
- [ ] Version bumped to `1.0.0` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock`.
- [ ] `CHANGELOG.md` `[Unreleased]` block promoted to `## [1.0.0] - YYYY-MM-DD`. Release summary mentions the parity story (graphene-django + strawberry-graphql-django), the django-graphene-filters depth, and the SemVer policy switch.
- [ ] Final pass through `BACKLOG.md` to mark differentiators that landed and refresh the post-1.0 roadmap.
- [ ] Tag, publish to PyPI, write the 1.0 announcement.

#### Files likely touched

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`
- `BACKLOG.md`

#### Why it matters

- `1.0.0` is the API freeze. After this card lands, every public symbol — `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `finalize_django_types`, `DjangoConnectionField`, `DjangoListField`, mutation classes, filter / order / aggregate / fieldset surfaces, and the Meta key vocabulary — is bound by strict SemVer. Breaking changes from this point forward require a major bump.
- The release card is where we audit, finalize, and commit to that contract. Without a dedicated card, "1.0 is stable" becomes a soft promise spread across N patches; making it a single card means the audit happens before the version tag goes out.

#### Other

- the heaviest release card: API freeze + `__all__` audit, a security review of every input surface (mutations / filters / GlobalID decoding), full async + sync matrix, version bump to `1.0.0`, CHANGELOG, backlog refresh, tag + publish + announcement.

#### Card references

- Related via Card item: Every other Beta card (`TODO-BETA-044-0.1.1` through `TODO-BETA-051-0.1.6` plus `TODO-BETA-047-0.1.3` and `TODO-BETA-050-0.1.5`) is in `DONE`. -> `TODO-BETA-044-0.1.1` — `FieldSet`
- Related via Card item: Every other Beta card (`TODO-BETA-044-0.1.1` through `TODO-BETA-051-0.1.6` plus `TODO-BETA-047-0.1.3` and `TODO-BETA-050-0.1.5`) is in `DONE`. -> `TODO-BETA-051-0.1.6` — Migration and adoption guides
- Related via Card item: Every other Beta card (`TODO-BETA-044-0.1.1` through `TODO-BETA-051-0.1.6` plus `TODO-BETA-047-0.1.3` and `TODO-BETA-050-0.1.5`) is in `DONE`. -> `TODO-BETA-047-0.1.3` — Layer 3 Meta key promotion
- Related via Card item: Every other Beta card (`TODO-BETA-044-0.1.1` through `TODO-BETA-051-0.1.6` plus `TODO-BETA-047-0.1.3` and `TODO-BETA-050-0.1.5`) is in `DONE`. -> `TODO-BETA-050-0.1.5` — Product-catalog Layer 3 HTTP GraphQL tests

## Done

<a id="filtering_subsystem"></a>
### [DONE-027-0.0.8 — Filtering subsystem](https://riodw.github.io/django-strawberry-framework/#filtering_subsystem)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: XL
- Labels: `example-app`, `filters`, `graphql-api`, `public-api`
- Spec: [spec-027-filters-0_0_8.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-027-filters-0_0_8.md)

#### Planning note

shipped

#### Other

- both upstreams ship a FilterSet / filter surface; `django-graphene-filters` is the cookbook source.
- the milestone anchor: six-layer lazy-resolution filtering pipeline, `FilterSet` / `RelatedFilter` / `Meta.filterset_class`, parity-floor filter primitives, finalizer phase-2.5 wiring, 14 live HTTP tests.

<a id="scalar_conversion_end_to_end_coverage_in_the_fakeshop_example"></a>
### [DONE-026-0.0.7 — Scalar conversion end-to-end coverage in the fakeshop example](https://riodw.github.io/django-strawberry-framework/#scalar_conversion_end_to_end_coverage_in_the_fakeshop_example)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Low
- Status: Shipped
- Relative size: M
- Labels: `example-app`, `graphql-api`, `scalars`, `tests`
- Spec: [spec-026-scalar_conversion_fakeshop-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md)

#### Planning note

shipped

#### Other

- both upstreams ship scalar conversion for the full numeric / date / JSON / UUID set; this card moves those converter rows to live `/graphql/` HTTP coverage in both nullable and non-null shapes.
- new `apps.scalars` example app (paired non-null / nullable models, self-FK + cross-model `SET_NULL` FK) + eight live HTTP tests + a real-domain `BigIntegerField` on `Patron`.
- `ScalarSpecimen` — every scalar field non-null, exposed via `ScalarSpecimenType`. Adds an intra-model self-FK `parent` (`related_name="children"`) so the example exercises self-referential FK planning under the optimizer.
- `NullableScalarSpecimen` — every scalar field nullable (`null=True, blank=True`), exposed via `NullableScalarSpecimenType`. Adds a cross-model FK `partner: ForeignKey(ScalarSpecimen, on_delete=SET_NULL, related_name="nullable_partners")` — the only `SET_NULL` ondelete in the example tree, and the only cross-model FK in the scalars app.
- The pairing is deliberate (not a single model with paired fields). It exercises **upstream code paths no other example app reaches**: Django's two-`CreateModel` initial migration path, the registry / `finalize_django_types()` resolving sibling `DjangoType` classes in one app, Strawberry type registration across sibling types in one schema build, the optimizer planning across two managed models in one query, and `SET_NULL` ondelete behavior.
- `apps.scalars.schema` composes two root resolvers (`all_scalar_specimens`, `all_nullable_scalar_specimens`) into the project root `Query` at [`examples/fakeshop/config/schema.py`][example-schema]; `ScalarsConfig` lands in `INSTALLED_APPS` at [`examples/fakeshop/config/settings.py`][settings].
- Full non-null wire-format sweep covering every field on `ScalarSpecimen`
- Signed-negative `BigInt` round-trip
- `BigInt`-at-zero edge case
- Schema introspection asserting `BigInt` converter resolves correctly in both shapes (`NON_NULL` on `ScalarSpecimenType`; bare `SCALAR` on `NullableScalarSpecimenType`)
- All-NULL nullable wire format covering every nullable converter branch
- Cross-model `partner` FK linkage round-trip
- Reverse-FK `nullablePartners` exposure
- Self-FK `parent` / `children` traversal

<a id="warning_free_scalar_registration_via_strawberryconfigscalar_map"></a>
### [DONE-025-0.0.7 — Warning-free scalar registration via `StrawberryConfig.scalar_map`](https://riodw.github.io/django-strawberry-framework/#warning_free_scalar_registration_via_strawberryconfigscalar_map)

- Priority: Medium
- Severity: Medium
- Status: Shipped
- Relative size: S
- Labels: `config`, `public-api`, `scalar-map`, `scalars`
- Spec: [spec-025-scalar_map_helper-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-025-scalar_map_helper-0_0_7.md)

#### Planning note

shipped

#### Other

- package-specific scalar-registration plumbing (`StrawberryConfig.scalar_map` via `strawberry_config()`); not an upstream-parity primitive.
- `strawberry_config()` factory registering `BigInt` via `scalar_map` and removing the deprecation-suppression block; a documented breaking change in alpha.

<a id="django_trac_37064_hardening_safe_wrap_connection_method"></a>
### [DONE-024-0.0.7 — Django Trac #37064 hardening + `safe_wrap_connection_method`](https://riodw.github.io/django-strawberry-framework/#django_trac_37064_hardening_safe_wrap_connection_method)

- Priority: Low
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `django-integration`, `hardening`
- Spec: [spec-024-django_trac_37064_hardening-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md)

#### Planning note

shipped

#### Other

- defensive hardening unique to this package; neither upstream ships a Django Trac #37064 patch.
- two-half defense for Trac #37064: a package-level unwrap patch (auto-applied at app-load) plus the cooperative `safe_wrap_connection_method` helper + tests.

<a id="multi_database_cooperation_contract"></a>
### [DONE-023-0.0.7 — Multi-database cooperation contract](https://riodw.github.io/django-strawberry-framework/#multi_database_cooperation_contract)

- Priority: Low
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `multi-db`, `optimizer`, `tests`
- Spec: [spec-023-multi_db-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-023-multi_db-0_0_7.md)

#### Planning note

shipped

#### Other

- multi-DB is a Django capability neither upstream specifies a contract around (⚛️&🍓 parity-adjacent); pinning ours smooths the migrant story.
- pin the multi-DB cooperation contract (router-aware FK-id stubs, `.using()` preservation, `Prefetch` `_db` round-trip) + tests; zero production-code change.

<a id="schema_export_management_command"></a>
### [DONE-022-0.0.7 — Schema export management command](https://riodw.github.io/django-strawberry-framework/#schema_export_management_command)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `management-command`, `public-api`, `schema`
- Spec: [spec-022-export_schema-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-022-export_schema-0_0_7.md)

#### Planning note

shipped

#### Other

- strawberry-graphql-django ships `manage.py export_schema`; graphene-django's different `graphql_schema` command is parity-adjacent (deliberately not borrowed).
- one management command (positional `schema`, `--path`, SDL via `print_schema`, `CommandError` paths) + tests.

<a id="appspy_and_django_app_config"></a>
### [DONE-021-0.0.7 — `apps.py` and Django app config](https://riodw.github.io/django-strawberry-framework/#appspy_and_django_app_config)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Low
- Status: Shipped
- Relative size: XS
- Labels: `django-app`, `packaging`
- Spec: [spec-021-apps-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-021-apps-0_0_7.md)

#### Planning note

shipped

#### Other

- both upstreams ship an `apps.py` `AppConfig` for `INSTALLED_APPS`-driven discovery.
- tiny `AppConfig` (two class attributes, no `ready()` body in 0.0.7) + tests.

<a id="djangolistfield_non_relay_list"></a>
### [DONE-020-0.0.7 — `DjangoListField` (non-Relay list)](https://riodw.github.io/django-strawberry-framework/#djangolistfield_non_relay_list)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Severity: Medium
- Status: Shipped
- Relative size: M
- Labels: `graphql-api`, `list-field`, `optimizer`, `public-api`
- Spec: [spec-020-list_field-0_0_7.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-020-list_field-0_0_7.md)

#### Planning note

shipped

#### Other

- graphene-django ships `DjangoListField`; strawberry-graphql-django has no non-Relay list-field primitive.
- `DjangoListField` factory: default + consumer resolver, `Manager → QuerySet` coercion, sync/async `get_queryset`, outer-list nullability, root-gated optimizer cooperation.

<a id="consumer_override_semantics_scalar_fields"></a>
### [DONE-019-0.0.6 — Consumer override semantics (scalar fields)](https://riodw.github.io/django-strawberry-framework/#consumer_override_semantics_scalar_fields)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Shipped
- Relative size: L
- Labels: `public-api`, `relay`, `scalars`, `types`
- Spec: [spec-019-consumer_overrides_scalar-0_0_6.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md)

#### Planning note

shipped

#### Other

- both upstreams support consumer-authored scalar field overrides on model-backed types.
- annotation/assigned scalar-override contract (four-corner matrix), `relay.Node` `id`-collision rejection, cross-type choice-enum cache semantics.
- `DjangoType.__init_subclass__` collected `consumer_annotated_scalar_fields`
- `DjangoTypeDefinition` gained `consumer_annotated_scalar_fields: frozenset[str]`.
- The previously-skipped `test_consumer_annotation_overrides_synthesized`
- End-to-end test pinned the override surviving `strawberry.type(...)`
- **Consumer annotation overrides are authoritative.** `_build_annotations`'s
- **`relay.Node` `id` collision rejected at type-creation time.** A consumer
- No new public API. No `Meta.field_overrides = {...}`-style key. Opt-out
- 100% coverage was reached across `tests/types/test_definition_order.py`
- The four `consumer_*_fields` sets on `DjangoTypeDefinition`
- Resolver / metadata overrides for scalars stay on the assigned
- Type-annotation overrides are the consumer's responsibility for runtime

<a id="multiple_djangotypes_per_model_with_metaprimary"></a>
### [DONE-018-0.0.6 — Multiple DjangoTypes per model with `Meta.primary`](https://riodw.github.io/django-strawberry-framework/#multiple_djangotypes_per_model_with_metaprimary)

- Priority: Medium
- Severity: Medium
- Status: Shipped
- Relative size: L
- Labels: `optimizer`, `public-api`, `registry`, `types`
- Spec: [spec-018-meta_primary-0_0_6.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-018-meta_primary-0_0_6.md)

#### Planning note

shipped

#### Other

- 🍓 parity-adjacent (strawberry-graphql-django has an implicit primary-type concept via `is_type_of`; graphene-django ships no equivalent) — not required on either side.
- registry stores multiple types per model, `Meta.primary` flag, ambiguity audit at finalize, relation-deferral, optimizer origin-type threading.
- Registry stores multiple types per model (`_types: dict[Model, list[Type]]`).
- New `Meta.primary: bool` flag (default `False`); validated in `_validate_meta`.
- `registry.register(..., *, primary: bool = False) -> bool` and
- New registry surface: `primary_for(model)`, `types_for(model)`,
- `registry.get(model)` returns the primary if declared, else the single
- `finalize_django_types()` runs `audit_primary_ambiguity()` first: any
- Two primary types for the same model: rejected at registration time
- Relation conversion in `types/base.py` defers all **auto-synthesized**
- Optimizer planning threads the resolved origin Strawberry type from
- Schema audit (`optimizer/extension.py`) iterates every reachable
- `model_for_type` continues to work for any registered type so
- `DjangoTypeDefinition` gains `primary: bool = False`.
- 100% coverage across `tests/test_registry.py`, `tests/types/test_base.py`,
- Single-type-no-primary stays backward compatible: `registry.get(model)`
- `Meta.primary` is a per-class declaration, not a registry-level
- Already-shipped consumer relation overrides (direct annotation

<a id="deferred_scalar_conversions"></a>
### [DONE-017-0.0.6 — Deferred scalar conversions](https://riodw.github.io/django-strawberry-framework/#deferred_scalar_conversions)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Medium
- Status: Shipped
- Relative size: M
- Labels: `converters`, `public-api`, `scalars`
- Spec: [spec-017-deferred_scalars-0_0_6.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-017-deferred_scalars-0_0_6.md)

#### Planning note

shipped

#### Other

- both upstreams ship scalar conversion for `BigIntegerField` / `JSONField` / `HStoreField` / `ArrayField`, etc.
- `BigInt` scalar + strict parser/serializer, `JSONField` / `ArrayField` / `HStoreField` conversion, `SCALAR_MAP` value-type widening.
- Public `BigInt` scalar (`django_strawberry_framework/scalars.py`, `NewType`-based) with the Strawberry class-direct-to-`scalar()` `DeprecationWarning` suppressed at the definition site so consumers see no warning at import time.
- Strict `BigInt` parser via regex `^(0|-?[1-9][0-9]*)$` — rejects `bool`, `float`, empty / whitespace-padded strings, non-decimal strings, underscores, plus signs, leading zeroes, `-0`, and Unicode digits.
- Strict `BigInt` serializer — rejects `bool`, `float`, `str`, `Decimal`, and any non-`int` type with `TypeError`.
- `BigIntegerField → BigInt` and `PositiveBigIntegerField → BigInt` in `SCALAR_MAP`. `BigAutoField` preserved as `int` (no override recourse at the time of DONE-013; annotation-override recourse now available via `DONE-019-0.0.6`).
- `JSONField → strawberry.scalars.JSON` in `SCALAR_MAP`.
- `ArrayField` and `HStoreField` mapped via sentinel-guarded branches in `convert_scalar`. `HStoreField` not added to `SCALAR_MAP`.
- `ArrayField` rejects nested arrays and outer `choices` with `ConfigurationError`.
- `SCALAR_MAP`'s declared value type widened from `dict[type[models.Field], type]` to `dict[type[models.Field], Any]`.
- `BigInt` added to `django_strawberry_framework.__all__`; `tests/base/test_init.py`'s pinned `__all__` and `__version__` assertions updated.
- Atomic version-bump quintet: `pyproject.toml`, `__init__.py`, `tests/base/test_init.py`, `docs/GLOSSARY.md` package-version line, `uv.lock`.
- 100% coverage via `tests/test_scalars.py` (new flat file) and `tests/types/test_converters.py` (extended). Includes a `test_package_import_does_not_emit_strawberry_deprecation_warning` guard so future regressions to the suppression are explicit.
- Docs: `docs/GLOSSARY.md`, `docs/README.md`, `README.md`, `docs/TREE.md`, `TODAY.md`, `CHANGELOG.md`.
- The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` is suppressed at the definition site (tight `warnings.catch_warnings()` filter). The package import surface is therefore clean. Migration to a `StrawberryConfig.scalar_map`-based design is roadmapped as `DONE-025-0.0.7` — that path is a real public-API change (consumers using `BigInt` directly will merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`), not an internal-only refactor.

#### Card references

- Related via Card item: `BigAutoField` preserved as `int` before scalar override recourse shipped in `DONE-019-0.0.6`. -> `DONE-019-0.0.6` — Consumer override semantics (scalar fields)
- Related via Card item: The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` is suppressed at the definition site (tight `warnings.catch_warnings()` filter). The package import surface is therefore clean. Migration to a `StrawberryConfig.scalar_map`-based design is roadmapped as `DONE-025-0.0.7` — that path is a real public-API change (consumers using `BigInt` directly will merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`), not an internal-only refactor. -> `DONE-025-0.0.7` — Warning-free scalar registration via `StrawberryConfig.scalar_map`

<a id="fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement"></a>
### [DONE-016-0.0.6 — `FieldMeta` single-source-of-truth consolidation and mirror retirement](https://riodw.github.io/django-strawberry-framework/#fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement)

- Priority: Medium
- Severity: Medium
- Status: Shipped
- Relative size: M
- Labels: `cleanup`, `field-meta`, `metadata`, `optimizer`, `types`
- Spec: [spec-016-fieldmeta_consolidation-0_0_6.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md)

#### Planning note

shipped

#### Scope

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

#### Why it matters

- Three reader sites were re-deriving relation shape via `relation_kind(field)` + raw `getattr(field, ...)` instead of reading the `FieldMeta` already on `DjangoTypeDefinition.field_map` — duplicating logic and creating drift surface for any future relation-flag addition.
- `DjangoType.__init_subclass__` was writing legacy class-attribute mirrors (`cls._optimizer_field_map`, `cls._optimizer_hints`) that survived `registry.clear()`, then four optimizer sites read those mirrors instead of the canonical `DjangoTypeDefinition`. Two parallel sources of field metadata with no enforced consistency.

#### Other

- internal metadata-architecture refactor; no consumer-visible API change.
- consolidate field metadata onto `DjangoTypeDefinition` (single source of truth) and retire legacy class-attribute mirrors across ~7 reader sites.
- Commit `de35a62` (`refactor(types,optimizer): consolidate metadata onto DjangoTypeDefinition`).
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/extension.py`
- `CHANGELOG.md` (under `[Unreleased] → Changed`)
- Originally tracked as `BACKLOG.md` item 35 ("`FieldMeta` single-source-of-truth consolidation and mirror retirement"). Promoted to a DONE card and removed from `BACKLOG.md` when the work shipped — per `BACKLOG.md`'s "graduate into a `KANBAN.md` card when scheduled" workflow. This is the first `BACKLOG.md` item to graduate; the precedent for shipped items: strike-through with SHIPPED status is fine while the item awaits a release; once a release is imminent, move the item to a `KANBAN.md` `DONE` card and delete it from `BACKLOG.md` so the strategic-differentiation file doesn't keep pointing at completed architecture debt.
- The consolidation eliminates ~7 sites of duplicated relation-shape logic and removes legacy class-attribute residue that previously survived `registry.clear()`. Single source of truth for field metadata reduces drift surface whenever Django adds a new relation flag or changes a descriptor attribute.
- Internal refactor only; no `Meta` key changes, no public surface changes, no consumer-visible behavior changes. Existing tests pass without modification.

<a id="005_relay_interfaces_and_node_foundation"></a>
### [DONE-015-0.0.5 — 0.0.5 Relay interfaces and Node foundation](https://riodw.github.io/django-strawberry-framework/#005_relay_interfaces_and_node_foundation)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `public-api`, `relay`, `types`
- Spec: [spec-015-relay_interfaces-0_0_5.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-015-relay_interfaces-0_0_5.md)

#### Planning note

shipped

#### Scope

- `Meta.interfaces` accepted end-to-end for any Strawberry interface.
- Four Relay node resolver defaults injected when `relay.Node` is declared (canonical order: `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes`); consumer-declared overrides are preserved via Strawberry's `__func__` identity test.
- Automatic synthesized `id: int!` suppression when `relay.Node` is in `Meta.interfaces`; the Relay-supplied `id: GlobalID!` is used instead.
- `is_type_of` injection is unconditional for every `DjangoType` (Relay-declared or not); consumer-declared `is_type_of` is preserved.
- Models whose primary key is a Django 5.2+ `CompositePrimaryKey` raise `ConfigurationError` at finalization; declare an explicit `id: relay.NodeID[...]` annotation or remove `relay.Node` from `Meta.interfaces` to remediate.
- Both sync and async paths for `_resolve_node_default` / `_resolve_nodes_default`; async `get_queryset` hooks are awaited on the async branch and rejected with `ConfigurationError` on the sync branch.
- `Meta.interfaces` promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`.
- Package version bumped to `0.0.5` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock`.

#### Other

- both upstreams ship Relay Node interfaces; this shipped our 🍓-shaped Relay Node integration.
- Relay Node foundation: `Meta.interfaces`, four `resolve_*` defaults, `id: GlobalID!` suppression, `is_type_of` injection, composite-PK rejection, sync + async node resolution.
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
- Borrowed patterns from `strawberry-django` (spec "Borrowing posture", Decision 3). The override discriminator triad stays distinct across the three injection sites: `__dict__` membership for `is_type_of`, tuple membership for id suppression, `__func__` identity for the four `resolve_*` defaults.
- `Meta.interfaces` is the first `0.0.4`-reserved `DjangoTypeDefinition` slot that ships end-to-end through finalizer phase 2.5; subsequent Layer 3 subsystems plug into the same architectural seam.

<a id="move_test_fixture_out_of_example_settings"></a>
### [DONE-014-0.0.4 — Move test fixture out of example settings](https://riodw.github.io/django-strawberry-framework/#move_test_fixture_out_of_example_settings)

- Priority: Low
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `cleanup`, `example-app`, `tests`
- Spec: [spec-014-testing_shift-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-014-testing_shift-0_0_4.md)

#### Planning note

shipped

#### Scope

- Removed `tests.fixtures.apps.TestsCardinalityConfig` from the example project.
- Removed the old unmanaged cardinality fixture files under `tests/fixtures/`.
- Package tests that need OneToOne / M2M / cardinality coverage now use real models from `examples/fakeshop/apps/library/`.

#### Other

- test hygiene.
- remove the `tests.fixtures.apps` fixture app + unmanaged cardinality fixtures; switch package tests to real `library` models.
- `examples/fakeshop/config/settings.py`
- `examples/fakeshop/apps/library/models.py`
- `docs/SPECS/spec-014-testing_shift-0_0_4.md`
- `AGENTS.md`
- `docs/TREE.md`

<a id="real_m2m_coverage"></a>
### [DONE-013-0.0.4 — Real M2M coverage](https://riodw.github.io/django-strawberry-framework/#real_m2m_coverage)

- Priority: Medium
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `example-app`, `m2m`, `tests`
- Spec: [spec-013-real_m2m_coverage-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md)

#### Planning note

shipped

#### Scope

- Replaced test-only M2M/cardinality fixtures with real managed models in the `library` example app.
- Added package-level and HTTP-level coverage for M2M traversal and optimizer planning.

#### Other

- test hygiene.
- replace test-only M2M / cardinality fixtures with real `library` models; add package + HTTP coverage.
- `examples/fakeshop/apps/library/models.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `tests/types/test_definition_order.py`
- `tests/optimizer/test_definition_order.py`

<a id="004_version_and_release_alignment"></a>
### [DONE-012-0.0.4 — 0.0.4 version and release alignment](https://riodw.github.io/django-strawberry-framework/#004_version_and_release_alignment)

- Priority: Low
- Severity: Low
- Status: Shipped
- Relative size: XS
- Labels: `release`, `versioning`
- Spec: [spec-012-version_release_alignment-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-012-version_release_alignment-0_0_4.md)

#### Planning note

shipped

#### Scope

- Package metadata, runtime version, lockfile, tests, and changelog now agree on `0.0.4`.
- The changelog entry is condensed for the alpha release and covers the actual commit range through 2026-05-08.

#### Other

- release housekeeping (version alignment).
- align package metadata / runtime version / lockfile / tests / changelog on `0.0.4`.
- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`

<a id="stale_placeholder_cleanup"></a>
### [DONE-011-0.0.4 — Stale placeholder cleanup](https://riodw.github.io/django-strawberry-framework/#stale_placeholder_cleanup)

- Priority: Low
- Severity: Low
- Status: Shipped
- Relative size: XS
- Labels: `cleanup`, `docs`, `tests`
- Spec: [spec-011-stale_placeholder_cleanup-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md)

#### Planning note

shipped

#### Scope

- Replaced stale M2M and forward-reference skips with definition-order tests.
- Kept the remaining scalar override skip documented as a separate scalar-field concern under `DONE-019-0.0.6`.

#### Other

- internal test/doc cleanup.
- replace stale M2M / forward-reference skips with definition-order tests.
- `tests/types/test_definition_order.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_definition_order.py`
- `DONE-019-0.0.6`

#### Card references

- Related via Card item: Kept the remaining scalar override skip documented as a separate scalar-field concern under `DONE-019-0.0.6`. -> `DONE-019-0.0.6` — Consumer override semantics (scalar fields)

<a id="004_foundation_slice_definition_order_independence"></a>
### [DONE-010-0.0.4 — 0.0.4 foundation slice (definition-order independence)](https://riodw.github.io/django-strawberry-framework/#004_foundation_slice_definition_order_independence)

- Priority: High
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `finalizer`, `registry`, `relations`, `types`
- Spec: [spec-010-foundation-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-010-foundation-0_0_4.md)

#### Planning note

shipped

#### Scope

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

#### Other

- internal Layer-2 foundation (`DjangoTypeDefinition`, finalizer, pending-relation resolution) — enables the parity subsystems rather than being one itself.
- definition-order-independent finalizer, pending-relation registry, manual-override contract, real cardinality coverage — the seam every Layer-3 subsystem plugs into.
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
- `docs/SPECS/spec-010-foundation-0_0_4.md`
- `docs/feedback.md`
- The forward-reserved slots on `DjangoTypeDefinition` are the architectural seam where the cookbook-shaped Layer 3 subsystems plug in (each subsystem moves its `Meta` key out of `DEFERRED_META_KEYS`, populates the matching slot in collection, and consumes it during finalization or in `DjangoConnectionField`).
- The pending-resolution pattern (record at class creation, resolve at finalization, fail loud on missing target with named source model / field / target) generalizes directly to lazy related class references for `RelatedFilter`, `RelatedOrder`, and `RelatedAggregate`.
- The previous foundation-slice in-progress cards have been retired; this card is their successor in Done.

<a id="rich_schema_architecture"></a>
### [DONE-009-0.0.4 — Rich schema architecture](https://riodw.github.io/django-strawberry-framework/#rich_schema_architecture)

- Priority: High
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `layer-3`, `public-api`, `relations`, `types`
- Spec: [spec-009-rich_schema_architecture-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md)

#### Planning note

shipped

#### Scope

- Lay out the long-term architecture for filters, orders, aggregates, connections, permissions, and fieldsets.
- Compare Graphene, django-graphene-filters, and strawberry-graphql-django patterns against this package's DRF-shaped API.
- Define how the 0.0.4 foundation slice becomes the base for later Layer 3 subsystems.

#### Other

- Architecture design record paired with the narrower 0.0.4 foundation implementation spec.

<a id="definition_order_independence_design"></a>
### [DONE-008-0.0.4 — Definition-order independence design](https://riodw.github.io/django-strawberry-framework/#definition_order_independence_design)

- Priority: High
- Severity: Major
- Status: Shipped
- Relative size: M
- Labels: `finalizer`, `registry`, `relations`, `types`
- Spec: [spec-008-definition_order_independence-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-008-definition_order_independence-0_0_4.md)

#### Planning note

shipped

#### Scope

- Frame the class-definition-time relation-resolution problem.
- Compare options for preserving concrete related `DjangoType`s without import-order coupling.
- Set the failure-mode requirements that the 0.0.4 foundation slice implements.

#### Other

- Problem-space design record for definition-order independence.

<a id="004_onboarding_docs_and_spec_consolidation"></a>
### [DONE-007-0.0.4 — 0.0.4 onboarding docs and spec consolidation](https://riodw.github.io/django-strawberry-framework/#004_onboarding_docs_and_spec_consolidation)

- Priority: Medium
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `docs`, `release`
- Spec: [spec-007-onboarding_docs_spec_consolidation-0_0_4.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md)

#### Planning note

shipped

#### Scope

- Root `README.md` is the canonical documentation map and operational entry point.
- `docs/README.md` is code-first: quickstart, three-minute path, optimizer behavior, and status.
- `docs/GLOSSARY.md` is the capability catalog with value-led optimizer language and comparison table.
- `docs/TREE.md` is the detailed layout/test-tree reference.
- `CHANGELOG.md` is condensed and no longer relies on design-doc pointers for release context.
- Completed design-doc content is folded into durable docs, while remaining specs preserve design history and follow-up work.

#### Other

- internal docs cleanup / spec consolidation — no upstream-parity surface.
- onboarding-doc consolidation across README / docs / CHANGELOG; completed spec content folded into durable docs.
- `README.md`
- `docs/README.md`
- `docs/GLOSSARY.md`
- `docs/TREE.md`
- `CHANGELOG.md`
- Future in-flight design docs use the `docs/spec-<NNN>-<topic>-<0_0_X>.md` convention (NNN matches the KANBAN card number; see `docs/builder/BUILD.md` "Spec filename pattern"), then get folded into durable docs when shipped.

<a id="documentationstatus_positioning_for_shipped_layer_2"></a>
### [DONE-006-0.0.3 — Documentation/status positioning for shipped Layer 2](https://riodw.github.io/django-strawberry-framework/#documentationstatus_positioning_for_shipped_layer_2)

- Priority: Medium
- Severity: Low
- Status: Shipped
- Relative size: S
- Labels: `docs`
- Spec: [spec-006-public_surface-0_0_3.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-006-public_surface-0_0_3.md)

#### Planning note

shipped

#### Scope

- `docs/README.md` gives a quickstart, package positioning, optimizer value, and status.
- `docs/GLOSSARY.md` describes shipped, planned, deferred, and alpha-constrained capabilities.
- `docs/TREE.md` preserves detailed package/test tree responsibilities.

#### Other

- internal docs / status-positioning card — no upstream-parity surface.
- docs pass: `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md` quickstart + status positioning.
- `docs/README.md`
- `docs/GLOSSARY.md`
- `docs/TREE.md`
- User-facing docs avoid internal slice shorthand; maintainer docs can still use it where useful.

<a id="djangotype_contract_and_boundary"></a>
### [DONE-005-0.0.3 — DjangoType contract and boundary](https://riodw.github.io/django-strawberry-framework/#djangotype_contract_and_boundary)

- Priority: High
- Severity: Major
- Status: Shipped
- Relative size: M
- Labels: `docs`, `public-api`, `registry`, `types`
- Spec: [spec-005-django_type_contract-0_0_3.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-005-django_type_contract-0_0_3.md)

#### Planning note

shipped

#### Scope

- Document the alpha one-model-one-type registry constraint.
- Reject unsupported or deferred `Meta` keys instead of accepting unwired surface area.
- Remove consumer override promises that the implementation cannot honor yet.

#### Other

- Contract companion to the 0.0.3 public-surface documentation pass.

<a id="optimizer_beyond_slices_b1_b8"></a>
### [DONE-004-0.0.3 — Optimizer beyond slices B1-B8](https://riodw.github.io/django-strawberry-framework/#optimizer_beyond_slices_b1_b8)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `optimizer`, `performance`, `query-planning`, `schema-audit`
- Spec: [spec-004-optimizer_beyond-0_0_3.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-004-optimizer_beyond-0_0_3.md)

#### Planning note

shipped

#### Scope

- B1: plan cache keyed by selected operation AST, directive variables, model, and root runtime path
- B2: forward-FK-id elision
- B3: strictness mode (`off`, `warn`, `raise`)
- B4: `Meta.optimizer_hints` with `OptimizerHint`
- B5: plan introspection via context
- B6: schema-build-time audit
- B7: precomputed optimizer field metadata
- B8: queryset diffing against consumer-applied `select_related`, `prefetch_related`, and `Prefetch`

#### Other

- continuation of DONE-002's optimizer lineage (⚛️ parity-adjacent).
- eight optimizer sub-features B1–B8: AST plan cache, FK-id elision, strictness modes, `OptimizerHint`, context plan introspection, schema audit, precomputed field metadata, queryset diffing.
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/hints.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/plans.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_hints.py`
- `tests/optimizer/test_field_meta.py`
- `tests/optimizer/test_plans.py`
- B8 went beyond the initial simple exact-match diff and now handles subtree-aware prefetch reconciliation.
- Fragment-spread directive and multi-operation cache-key bugs have been fixed in source; the old `alpha-review-feedback.md` entries are now historical.

<a id="optimizer_o4_nested_prefetch_chains"></a>
### [DONE-003-0.0.2 — Optimizer O4 nested prefetch chains](https://riodw.github.io/django-strawberry-framework/#optimizer_o4_nested_prefetch_chains)

- Priority: High
- Severity: Major
- Status: Shipped
- Relative size: M
- Labels: `optimizer`, `performance`, `query-planning`, `relations`
- Spec: [spec-003-optimizer_nested_prefetch_chains-0_0_2.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md)

#### Planning note

shipped

#### Scope

- Plan depth > 1 relation selections from the root optimizer pass.
- Emit nested `Prefetch` objects for many-side branches that need shaped child querysets.
- Recurse through single-valued relation chains with `select_related` and `only()` fields intact.

#### Other

- Design record for the O4 slice split out from the broader optimizer foundation.

<a id="optimizer_o1_o6_foundation"></a>
### [DONE-002-0.0.2 — Optimizer O1-O6 foundation](https://riodw.github.io/django-strawberry-framework/#optimizer_o1_o6_foundation)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `optimizer`, `performance`, `query-planning`, `relations`
- Spec: [spec-002-optimizer-0_0_2.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-002-optimizer-0_0_2.md)

#### Planning note

shipped

#### Scope

- generated relation resolvers
- selection-tree walker
- root-gated optimizer extension
- nested `Prefetch` chains
- same-query `select_related` recursion
- `only()` projection
- custom `get_queryset` downgrade to `Prefetch`

#### Other

- strawberry-graphql-django ships a heavy optimizer extension; graphene-django has only `select_related_field` (⚛️ parity-adjacent).
- heavy optimizer extension: relation resolvers, selection-tree walker, root-gated planning, nested `Prefetch` chains, `only()` projection, `get_queryset` downgrade.
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/plans.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_walker.py`
- `tests/optimizer/test_plans.py`
- Shipped behavior is consolidated into `docs/GLOSSARY.md`; source/tests are the truth for optimizer behavior.

<a id="djangotype_core_foundation"></a>
### [DONE-001-0.0.1 — DjangoType core foundation](https://riodw.github.io/django-strawberry-framework/#djangotype_core_foundation)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Severity: Major
- Status: Shipped
- Relative size: L
- Labels: `public-api`, `registry`, `relations`, `scalars`, `types`
- Spec: [spec-001-django_types-0_0_1.md](https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-001-django_types-0_0_1.md)

#### Planning note

shipped

#### Scope

- `DjangoType` base class
- Meta validation
- scalar conversion
- relation conversion
- choice enums
- type registry
- relation resolvers
- `get_queryset` hook and `has_custom_get_queryset`

#### Other

- `DjangoObjectType` (graphene-django) / `@strawberry_django.type` (strawberry-graphql-django) are the namesake primitive.
- core foundational subsystem: `DjangoType` base, Meta validation, scalar/relation conversion, choice enums, type registry, relation resolvers, `get_queryset` hook.
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `tests/types/test_base.py`
- `tests/types/test_converters.py`
- `tests/types/test_resolvers.py`
- The public shape is intentionally narrow and explicit.
- Deferred Meta keys are rejected, not silently accepted.
- Definition-order independence is now covered by `DONE-010-0.0.4`.

#### Card references

- Related via Card item: Definition-order independence is now covered by `DONE-010-0.0.4`. -> `DONE-010-0.0.4` — 0.0.4 foundation slice (definition-order independence)

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
- Strategic differentiation candidates (features neither `graphene-django` nor `strawberry-graphql-django` ship cleanly) live in [`BACKLOG.md`][backlog] or the Backlog board section. When a backlog item is scheduled, promote it to a `TODO[-MILESTONE]-NNN-X.Y.Z` card here and cross-reference back.

## Decision: FilterSet subclassing unsupported

FilterSet / FilterArgumentsFactory subclassing is unsupported (decided 2026-05-30).

FilterArgumentsFactory raises TypeError on subclassing: its class-level input_object_types / _type_filterset_registry caches are shared mutable dicts a subclass would inherit rather than isolate, silently cross-contaminating builds.

Rationale: supporting subclassing would turn a currently-discouraged pattern into a real API commitment and pull in cache / lifecycle fixes (H-filters-3, M-filters-4, M-filters-5) that do not buy much without a concrete consumer need. Revisit if a real consumer need arises.

Ref: spec-021 pre-merge review M-filters-3 / H-filters-3.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: BACKLOG.md
[goal]: GOAL.md
[readme]: README.md

<!-- docs/ -->
[docs-readme]: docs/README.md
[glossary-bigint-scalar]: docs/GLOSSARY.md#bigint-scalar
[glossary-django-trac-37064-hardening]: docs/GLOSSARY.md#django-trac-37064-hardening
[glossary-filterset]: docs/GLOSSARY.md#filterset
[glossary-metafilterset_class]: docs/GLOSSARY.md#metafilterset_class
[glossary-multi-database-cooperation]: docs/GLOSSARY.md#multi-database-cooperation
[glossary-optimizerhint]: docs/GLOSSARY.md#optimizerhint
[glossary-relatedfilter]: docs/GLOSSARY.md#relatedfilter
[glossary-safe-wrap-connection-method]: docs/GLOSSARY.md#safe_wrap_connection_method
[glossary-strawberry-config]: docs/GLOSSARY.md#strawberry_config
[spec-021]: docs/SPECS/spec-027-filters-0_0_8.md

<!-- docs/SPECS/ -->
[spec-011]: docs/SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-016]: docs/SPECS/spec-020-list_field-0_0_7.md
[spec-019]: docs/SPECS/spec-023-multi_db-0_0_7.md

<!-- docs/builder/ -->
[build-020-scalar-map-helper-0-0-7]: docs/builder/build-020-scalar_map_helper-0_0_7.md

<!-- django_strawberry_framework/ -->
[apps]: django_strawberry_framework/apps.py
[converters]: django_strawberry_framework/types/converters.py
[django-patches]: django_strawberry_framework/_django_patches.py
[filters]: django_strawberry_framework/filters/
[plans]: django_strawberry_framework/optimizer/plans.py
[resolvers]: django_strawberry_framework/types/resolvers.py
[test-init]: django_strawberry_framework/test/__init__.py
[wrap]: django_strawberry_framework/test/_wrap.py

<!-- tests/ -->
[test-converters]: tests/types/test_converters.py
[test-multi-db]: tests/optimizer/test_multi_db.py
[test-resolvers]: tests/types/test_resolvers.py

<!-- examples/ -->
[db-shard-b.sqlite3]: examples/fakeshop/db_shard_b.sqlite3
[example-schema]: examples/fakeshop/config/schema.py
[fakeshop-library]: examples/fakeshop/apps/library/
[fakeshop-test-multi-db]: examples/fakeshop/test_query/test_multi_db.py
[settings]: examples/fakeshop/config/settings.py
[test-library-api]: examples/fakeshop/test_query/test_library_api.py
[test-scalars-api]: examples/fakeshop/test_query/test_scalars_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
