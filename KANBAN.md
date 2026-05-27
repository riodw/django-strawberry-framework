# django-strawberry-framework Kanban

Last refreshed: 2026-05-26

This board summarizes what is shipped, what has recently landed, and what remains to finish based on the current code, tests, docs, and release-readiness notes. It is intentionally written as a project-management view: each card has a status, priority, scope, and a practical definition of done.

## Card ID format

Every card uses the form `<STATUS>[-<MILESTONE>]-NNN-X.Y.Z`:

- `<STATUS>` — the column the card lives in: `TODO` (committed to a milestone, not yet active), `WIP` (actively being worked), `BLOCKED` (waiting on a dependency), or `DONE` (shipped). Updated when the card moves between columns.
- `<MILESTONE>` *(optional)* — the development phase the card lives in while it's still pre-shipping: `ALPHA` (pre-`0.1.0`), `BETA` (post-`0.1.0` / pre-`1.0.0`), or `STABLE` (post-`1.0.0`). Used on `TODO`, `WIP`, and `BLOCKED` cards. The two release cards themselves are tagged with the phase they usher in: `TODO-BETA-036-0.1.0` is the alpha → beta cut-over and `TODO-STABLE-045-1.0.0` is the beta → stable cut-over. **Dropped when the card ships** — `DONE` cards use the bare `DONE-NNN-X.Y.Z` form (no milestone segment). The card's version tag (`X.Y.Z`) already encodes which phase the shipment belongs to, and the bare form keeps the shipped-card cluster compact and uniform across the package's history.
- `NNN` — a 3-digit sequence number indicating the order the card was completed (`DONE` cards) or is planned to be completed (every other card, ordered by planned ship version, ties broken by intra-version dependency order). **Unlike status, milestone, and version, this number is not stable** — it is recomputed whenever a card's position in the shipping sequence changes (reordered, new card inserted between two existing cards, version-tag bumped). Use the card title, not the NNN, when referencing a card from long-lived documents.
- `X.Y.Z` — the package version the card shipped in (Done cards) or is planned to ship in (everything else). Alpha cards span `0.0.6` through `0.0.12` leading up to `0.1.0`; Beta cards span `0.1.1` through `0.1.6` leading up to `1.0.0`. The `0.1.0` and `1.0.0` tags are reserved for the two release cards themselves. Anything beyond `1.0.0` lives in [`BACKLOG.md`][backlog], not here.

For install, local development, testing, and the canonical documentation map, start from [`README.md`][readme].

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

- `0.0.7` is the active patch. Five WIP cards were opened together so the small parity-driven slices land in one release; all five have shipped (`DONE-016-0.0.7` `DjangoListField`, `DONE-017-0.0.7` `apps.py` and Django app config, `DONE-018-0.0.7` schema-export management command, `DONE-019-0.0.7` multi-database cooperation contract, and `DONE-047-0.0.7` warning-free scalar registration via `StrawberryConfig.scalar_map`). Two further cards landed mid-cycle outside the original bundle — `DONE-046-0.0.7` (Django Trac #37064 hardening + `safe_wrap_connection_method` consumer helper) shipped the package's two-half defense-in-depth for an upstream Django bug, and `DONE-048-0.0.7` (scalar conversion end-to-end coverage in the fakeshop example) moved every non-trivial converter row from package-internal-only coverage to live `/graphql/` HTTP coverage via a new `apps.scalars` app plus a `BigIntegerField` on `apps.library.Patron`. Full card detail lives under the `## Done` board column below; `DONE-016-0.0.7`, `DONE-017-0.0.7`, `DONE-018-0.0.7`, `DONE-019-0.0.7`, `DONE-046-0.0.7`, `DONE-047-0.0.7`, and `DONE-048-0.0.7` are in the `## Done` column. The last `0.0.7` card to ship owns the version bump from `0.0.6` per Decision 10 of `docs/SPECS/spec-016-list_field-0_0_7.md`.
- Strategic differentiation roadmap (post-`0.0.6`) captured in [`BACKLOG.md`][backlog]: items neither `graphene-django` nor `strawberry-graphql-django` ship cleanly that should land on the roadmap once parity items are shipped.

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
- Test/example hygiene items surfaced by the foundation slice review have moved into the testing-shift docs and backlog: package-level override tests intentionally pin Strawberry internals while HTTP tests pin the consumer-visible override contract ([`BACKLOG.md`][backlog] item 38).
- The library GraphQL schema is real and wired into the project schema; the product-catalog Layer 3 aspirational schema block remains commented until those subsystems ship.

## Board columns

## In progress

_No cards in progress. The `0.0.7` queue is empty; the `0.1.0` cohort begins with `TODO-ALPHA-021-0.0.8`._

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
- `range_filter.py` — `RangeFilter(TypedFilter)`, `RangeField(Field)`, `validate_range`
- `list_filter.py` — `ListFilter(TypedFilter)`, `ListFilterMethod(FilterMethod)`
- `typed_filter.py` — `TypedFilter(Filter)` (base class for the four above)
- `global_id_filter.py` — `GlobalIDFilter(Filter)`, `GlobalIDMultipleChoiceFilter(MultipleChoiceFilter)`

All sourced from `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/filters/`. Our implementation should ship equivalents for each (DRF-style class declarations on the filterset rather than graphene-style filter-class subclassing where it matters); the global-ID filter in particular is required for Relay-aware filtering against `relay.Node` types shipped in `DONE-011-0.0.5`.

Verified upstream factory machinery (graphene-django, sibling files under the same `filter/` package):

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/__init__.py` — soft-dependency on `django-filter`: imports issue an `ImportWarning` when `DJANGO_FILTER_INSTALLED` is false. Our equivalent faces the same soft-dep question (pin the answer in the spec).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/utils.py::get_filtering_args_from_filterset` — the upstream function that converts a FilterSet class into GraphQL filter arguments. This is graphene-django's parity equivalent of the cookbook's `FilterArgumentsFactory`; our package needs the same end-to-end function (under whatever name we settle on).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/utils.py::get_filterset_class` — get-or-create helper that returns an explicit `Meta.filterset_class` if declared, else builds one via `custom_filterset_factory`. Note: name collision with the cookbook's `filterset_factories.py::get_filterset_class` — both files ship a function of the same name with different shapes; be explicit in the spec about which one we mirror.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/utils.py::replace_csv_filters` — already listed under "Dropped" below.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/filterset.py::GrapheneFilterSetMixin` — subclasses `django_filters.BaseFilterSet`; defines `FILTER_DEFAULTS` overriding FK/PK → `GlobalIDFilter` (cited again under "Strawberry-adapted bits" below).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/filterset.py::setup_filterset` / `::custom_filterset_factory` — upstream wrapper-avoidance / dynamic-factory pair; `setup_filterset` is dropped (see below); `custom_filterset_factory` is graphene's ancestor of the cookbook's `_dynamic_filterset_cache`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField` — graphene-django's filter-integrated connection field; the consumer-facing surface that composes FilterSet machinery onto a Relay connection. Cited here so the `TODO-ALPHA-023-0.0.9` (`DjangoConnectionField`) cross-card integration is clean — our equivalent must accept a `filterset_class` argument and thread filter args through the connection-field resolver.

`strawberry-graphql-django` covers the same surface through `filters.py` (single-file decorator-driven implementation) — verified at `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/filters.py`:

- `filters.py::FilterLookup` — generic `FilterLookup[T]` typed lookup descriptor (`exact`, `i_exact`, `contains`, `i_contains`, `starts_with`, etc.).
- `filters.py::process_filters` — compiles a filter input value into queryset filter arguments (the runtime side of the filter pipeline).
- `filters.py::StrawberryDjangoFieldFilters` — field-base subclass that injects the `filters: <T>FilterInput` argument and threads through to `process_filters`.
- `filters.py::filter_type` — current consumer-facing `@strawberry_django.filter_type(Model, lookups=True)` decorator (public API).
- `filters.py #"def __getattr__"` — module-level `__getattr__` exposes a legacy `filter` alias that emits a `DeprecationWarning` and forwards to `filter_type`. Do not claim parity with the deprecated symbol.
- `filters.py::FILTERS_ARG` (`= "filters"`) — module-level constant for the GraphQL argument name.

Our equivalent ships DRF-style class declarations (`Meta.filterset_class = ItemFilterSet`) rather than decorator-on-input-type, but the runtime pipeline (a `process_filters` analog) is conceptually parallel.

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
- `graphene_django.forms.converter.convert_form_field` → our own form-field → Strawberry-input converter; pairs with `TODO-ALPHA-029-0.0.11` (Form-based mutations), which builds the same converter for the mutation surface

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

Parity: 🍓 required (strawberry-graphql-django ships `strawberry_django.order_type`; graphene-django has no native ordering primitive — it composes `django_filters.OrderingFilter` into its FilterSet and exposes an `order_by` argument on `DjangoFilterConnectionField`, so ⚛️ parity is met via `TODO-ALPHA-021-0.0.8`'s filter subsystem rather than a separate surface here).

Status: planned

Scope:

- `Order`
- `OrderSet`
- GraphQL argument factory
- `Meta.orderset_class` promotion

Foundation-slice seam:

- `DjangoTypeDefinition.orderset_class` is the populated slot.
- Lazy related-order class references reuse the same record-now-resolve-at-finalization pattern as model relations (`PendingRelation` → analogous `PendingRelatedClass` shape).

Verified in strawberry-graphql-django (`/Users/riordenweber/projects/strawberry-django-main/strawberry_django/ordering.py`):

- `ordering.py::Ordering` — public `Ordering` enum: `ASC`, `DESC`, `ASC_NULLS_FIRST`, `ASC_NULLS_LAST`, `DESC_NULLS_FIRST`, `DESC_NULLS_LAST`.
- `ordering.py::OrderSequence` — per-field sequence descriptor used to order ties when multiple fields participate.
- `ordering.py::process_order` / `::process_ordering` / `::process_ordering_default` / `::apply_ordering` — the runtime pipeline that compiles an order-input value into queryset `order_by()` arguments and applies them.
- `ordering.py::StrawberryDjangoFieldOrdering` — field-base subclass that injects the `order: <T>OrderInput` and `ordering: list[<T>OrderInput]` arguments on a Django-backed field.
- `ordering.py::order_type` — current consumer-facing `@strawberry_django.order_type(Model)` decorator (public API).
- `ordering.py::order` — legacy decorator alias marked `@deprecated("strawberry_django.order is deprecated in favor of strawberry_django.order_type.")`; do not claim parity with this symbol.
- `ordering.py::ORDER_ARG` (`= "order"`) and `ordering.py::ORDERING_ARG` (`= "ordering"`) — module-level constants for the singular one-of and list GraphQL argument names.

Verified in graphene-django (no native ordering primitive):

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField #"order_by"` — connection field accepts an `order_by` argument that composes through `django_filters.OrderingFilter` declared on the FilterSet. Graphene has no separate ordering primitive; ⚛️ parity is met by the filter subsystem (`TODO-ALPHA-021-0.0.8`) rather than this card.

Lazy-resolution pipeline:

Reuses the lazy-resolution architecture spec'd in detail under `TODO-ALPHA-021-0.0.8` (Filtering subsystem), but only **five of the six layers** carry over from the cookbook with substitutions — the cookbook's ordering surface is leaner than its filter surface:

- **Layers 1-2** (lazy class refs + module-fallback resolution): port from `mixins.py::LazyRelatedClassMixin` and `orders.py::BaseRelatedOrder`. Same shape as the filter side; `RelatedOrder` substituted for `RelatedFilter`.
- **Layer 3** (metaclass discovery, deferred expansion): port from `orderset.py::OrderSetMetaclass`. Leaner than the filter side's `FilterSetMetaclass`; the discover-and-bind pattern is the same.
- **Layer 4** (cycle-safe expansion + cache): the cookbook's orderset uses `orderset.py::AdvancedOrderSet.get_fields` (and `::get_flat_orders` for the prefix-walked output) — **not** `get_filters()` or `get_orders()`. Earlier card revisions referenced a `get_orders()` method that does not exist in the cookbook. The cycle-safe expansion pattern carries over but the method names and cache-key shape are spelled differently from the filter side.
- **Layer 5** (BFS schema build with deferred references — Strawberry-adapted): port from `order_arguments_factory.py::OrderArgumentsFactory._ensure_built`. Graphene's `lambda tn=...: input_object_types[tn]` forward references become `strawberry.lazy("django_strawberry_framework.orders._registry.{TargetOrderSet}InputType")` (or `Annotated[..., strawberry.lazy(...)]`).
- **Layer 6** (memoized dynamic OrderSet generation): **no cookbook counterpart**. The cookbook ships no `orderset_factories.py` and no `_dynamic_orderset_cache` — only the filter side has the dynamic-factory mechanism. Our ordering subsystem must either design Layer 6 fresh (mirroring the filter side's `filterset_factories.py::_dynamic_filterset_cache`) or skip the dynamic-ordering-for-connection-field case and require explicit `orderset_class` declarations on every consumer. **Pin this decision in the spec.**

Synchronization runs inside `finalize_django_types()` phase 2.5 alongside filter resolution; the two subsystems share the same finalizer pass.

Reference symbols in the cookbook (`/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/`):

- `orders.py::BaseRelatedOrder`, `orders.py::RelatedOrder`
- `orderset.py::OrderSetMetaclass`, `orderset.py::AdvancedOrderSet` (with `::get_fields`, `::get_flat_orders`, `::apply_distinct`, `::check_permissions`, `::_apply_distinct_postgres`, `::_apply_distinct_emulated`)
- `order_arguments_factory.py::OrderArgumentsFactory`, `order_arguments_factory.py::OrderDirection`

Definition of done:

- Add `docs/spec-orders.md`.
- Add `django_strawberry_framework/orders/`.
- Add mirrored `tests/orders/`.
- Promote `Meta.orderset_class` only when ordering is applied end-to-end.
- Support simple fields and relation paths.
- Define interaction with filters and connection field.
- Keep ordering declarations introspectable from the owning type/query surface.

### TODO-ALPHA-023-0.0.9 — `DjangoConnectionField`

Priority: high once filters/orders are stable (FieldSet integration is deferred to `TODO-BETA-037-0.1.1` — `DjangoConnectionField` ships against the Layer-2 surface in 0.0.9 and gains field-selection composition when FieldSet lands).

Parity: ⚛️&🍓 required (both upstreams ship Relay-shaped connection fields).

Status: planned

Scope:

- Relay-style connection field
- composition of filtering, ordering, aggregation, field selection, and optimizer behavior

Foundation-slice seam:

- `finalize_django_types()` is the single architectural entry point that `DjangoConnectionField(DjangoType)` (and `DjangoNodeField`) will auto-trigger as their wrapper.
- An auto-trigger wrapper must respect the single-threaded-setup window: either be constrained to schema-construction time, or acquire a real lock around the finalizer.
- Connection-aware optimizer planning is its own follow-up slice (`TODO-ALPHA-025-0.0.9`); the foundation slice did not exercise nested connection prefetch shapes.

Definition of done:

- Add `docs/spec-connection.md`.
- Implement `django_strawberry_framework/connection.py`.
- Add `tests/test_connection.py`.
- Decide whether full Relay support belongs here or a separate `relay/` subpackage.
- Promote `DjangoConnectionField` only when end-to-end schema usage is tested.

Dependencies:

- `FilterSet` (`TODO-ALPHA-021-0.0.8`)
- `OrderSet` (`TODO-ALPHA-022-0.0.8`)
- Relay/interface decisions
- `FieldSet` — **deferred to `TODO-BETA-037-0.1.1`** (post-Alpha); field-selection composition is layered on after the connection field ships, not a 0.0.9 blocker.

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
- [`GOAL.md`][goal] explicitly names DRF as a target migration source ("keep the public API familiar to Django, DRF, and django-filter users"). Shipping `SerializerMutation` is on-mission, not just a parity item.

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

- The router helper must use a **distinctly-ours symbol name** (working name: `DjangoGraphQLProtocolRouter`) so the module is unambiguously ours and does not impersonate the upstream API. This respects the [`GOAL.md`][goal] non-goal "a thin wrapper around `strawberry-graphql-django`".
- Migration ergonomics are preserved by the upstream-equivalent mapping in the migration guide (`TODO-BETA-044-0.1.6`), not by copying the symbol name. A migrant changes one import line: `from strawberry_django.routers import AuthGraphQLProtocolTypeRouter` → `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`.

Definition of done:

- Implement `django_strawberry_framework/routers.py` exposing `DjangoGraphQLProtocolRouter` (final name pinned during implementation).
- `channels` is a soft dependency: top-level package import must not fail if `channels` is not installed. The helper wraps `channels` imports lazily and raises `ImportError` with an install hint when it is actually called.
- Tests under `tests/test_routers.py` exercise both the channels-present and channels-absent paths.
- Migration guide (`TODO-BETA-044-0.1.6`) gains a one-row entry in its "symbol equivalents" table mapping `AuthGraphQLProtocolTypeRouter` → `DjangoGraphQLProtocolRouter`, so the symbol rename is documented in one canonical location.

### TODO-ALPHA-033-0.0.12 — Debug-toolbar middleware

Priority: low (🍓 parity-required; developer experience)

Severity: **low**

Status: planned

Why it matters:

- `strawberry-graphql-django` ships a `middlewares/debug_toolbar.py` so `django-debug-toolbar`'s SQL panel captures queries triggered by GraphQL resolvers. Without it, developers can't see the SQL hit by their queries during a `/graphql/` request.
- `graphene-django` ships **no** equivalent; this card is strawberry-graphql-django parity only.

Verified in upstream:

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/middlewares/debug_toolbar.py` — `DebugToolbarMiddleware` (subclasses upstream `debug_toolbar.middleware.DebugToolbarMiddleware`); module-level `_get_payload` helper; `_HTML_TYPES` constant for content-type sniffing.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html` — HTML snippet rendered into the GraphiQL response; ships as a template asset alongside the Python module.

Architectural posture:

- **Not a from-scratch middleware**: strawberry-django **subclasses** `debug_toolbar.middleware.DebugToolbarMiddleware` and overrides `process_view` (to tag GraphiQL requests) and `_postprocess` (to inject the toolbar payload into the response). Our equivalent follows the same subclass-and-override shape; we do not re-implement the panel-rendering logic that `django-debug-toolbar` already owns.
- **GraphiQL-view detection**: strawberry-django tags `request._is_graphiql = bool(view and issubclass(view, BaseView))` where `BaseView` is `strawberry.django.views.BaseView`. Our equivalent uses the same `issubclass` check against whichever view class the package settles on (working name `DjangoGraphQLView`; pinned during implementation).
- **Two output paths, not one**:
  - **HTML response** (the GraphiQL page itself): the middleware appends a rendered toolbar template to the response body and refreshes `Content-Length`.
  - **JSON response** (a `/graphql/` operation result): the middleware parses the body, injects a `debugToolbar` key carrying per-panel `title` / `subtitle` metadata plus the toolbar's `requestId`, and re-encodes via `DjangoJSONEncoder`.
- **Introspection-query skip**: payload injection is suppressed when `operationName == "IntrospectionQuery"` so IDEs (Apollo Sandbox, etc.) that poll introspection on every keystroke don't flood their request history. Carry this behavior over.

Definition of done:

- Implement `django_strawberry_framework/middleware/debug_toolbar.py` exposing a `DebugToolbarMiddleware` that **subclasses** `debug_toolbar.middleware.DebugToolbarMiddleware` and overrides `process_view` + `_postprocess` for the two injection paths above.
- Ship the matching template asset at `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`; the middleware renders it via `render_to_string(...)` into HTML responses for the GraphiQL view.
- Introspection-query skip behavior preserved (no payload injection when `operationName == "IntrospectionQuery"`).
- `debug_toolbar` is a soft dependency: top-level package import must succeed without `django-debug-toolbar` installed; the middleware module raises `ImportError` with an install hint when actually imported.
- In-process test against a fakeshop request that emits SQL, covering both the GraphiQL HTML path and the JSON operation path.

### TODO-ALPHA-034-0.0.12 — Test client helper

Priority: low (⚛️&🍓 parity-required; developer experience)

Severity: **low**

Status: planned

Why it matters:

- `strawberry-graphql-django` ships `strawberry_django.test.client.TestClient`, a thin wrapper around `django.test.Client` that posts GraphQL requests with the right content type, parses the response, and exposes `.query(...)` / `.mutate(...)`.
- `graphene-django` ships `graphene_django.utils.testing` with `GraphQLTestMixin` / `GraphQLTestCase` / `GraphQLTransactionTestCase` / `graphql_query` helpers covering the same need.
- The fakeshop live tests already do this by hand; centralizing the pattern is a small win for consumers and keeps our HTTP tests crisp.

Verified in upstream:

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/test/client.py` — `TestClient` (subclasses Strawberry's `strawberry.test.BaseGraphQLTestClient`), `AsyncTestClient` (subclasses `TestClient`, takes an `AsyncClient`, overrides `.query()` and `.login()`). The `.query()` / `.mutate()` API surface lives on the upstream `BaseGraphQLTestClient`; strawberry-django adds Django-specific `request()`, `login()`, and the async `query()` override. `request()` switches to `format="multipart"` when `files=` is provided.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/utils/testing.py` — module-level `graphql_query` function; `GraphQLTestMixin` (the reusable mixin carrying `.query(...)`, `assertResponseNoErrors`, `assertResponseHasErrors`); `GraphQLTestCase` (`(GraphQLTestMixin, TestCase)`); `GraphQLTransactionTestCase` (`(GraphQLTestMixin, TransactionTestCase)`).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/settings.py #"TESTING_ENDPOINT"` — graphene reads `TESTING_ENDPOINT` (default `/graphql`) from its own settings dict so the testing helper has a project-wide override knob.

Architectural posture:

- **Mixin-first shape** (graphene-django convention): the reusable piece is `GraphQLTestMixin`; the concrete `GraphQLTestCase` / `GraphQLTransactionTestCase` are two-line `(Mixin, TestCase)` / `(Mixin, TransactionTestCase)` combinations so consumers with their own custom TestCase base can compose the mixin in directly. Our equivalent follows the same mixin-first shape rather than only shipping the concrete subclasses.
- **`.query()` return type — decide before writing the spec**: strawberry-django returns a typed `Response` dataclass (`data` / `errors` / `extensions`); graphene-django's `GraphQLTestMixin.query` returns a raw Django `HttpResponse` paired with `assertResponseNoErrors` / `assertResponseHasErrors` helpers that parse the body. The two flavors are not interchangeable — pick one and pin it (the typed-dataclass shape is the more DRF-shaped choice and composes better with future typed-error work).
- **Async**: strawberry-django's `AsyncTestClient` subclasses `TestClient` (not `BaseGraphQLTestClient` directly), takes a `django.test.client.AsyncClient`, and only overrides `.query()` + `.login()`. The sync `request()` is reused via `cast("Awaitable", ...)`. Our equivalent ports the same inheritance shape (or picks a flatter alternative explicitly in the spec).
- **Endpoint resolution**: project-wide default reads from `DJANGO_STRAWBERRY_FRAMEWORK["GRAPHQL_TESTING_ENDPOINT"]` (mirrors graphene's `TESTING_ENDPOINT` knob; final settings-key name pinned during implementation), with a per-instance / per-call override identical to strawberry-django's `path` constructor argument and graphene-django's `graphql_url` per-call argument.
- **File-upload coupling**: strawberry-django's `request()` switches to `format="multipart"` when `files=` is provided. Our helper must do the same so live HTTP tests for `TODO-ALPHA-028-0.0.11` (Upload scalar) can exercise multipart uploads through the helper rather than dropping back to raw `client.post(...)` calls.
- **Strawberry base-class reuse — decide before writing the spec**: subclass `strawberry.test.BaseGraphQLTestClient` (less code, couples our `.query()` / `.mutate()` shape to upstream Strawberry's choices) vs. roll our own base (more code, full control over the public surface). The strawberry-django decision was to subclass; the package's DRF-first stance argues for considering the from-scratch alternative.

Definition of done:

- Implement `django_strawberry_framework/test/client.py` exposing `TestClient` / `AsyncTestClient` (per the inheritance shape pinned above) plus a `GraphQLTestMixin` and two concrete `(Mixin, TestCase)` / `(Mixin, TransactionTestCase)` combinations for the unittest crowd.
- Mixin carries `assertResponseNoErrors` / `assertResponseHasErrors` helpers (or the equivalent named for the chosen `.query()` return type).
- Project-wide endpoint settings key (working name `GRAPHQL_TESTING_ENDPOINT`, final name pinned during implementation) under `DJANGO_STRAWBERRY_FRAMEWORK`, with constructor / per-call override.
- Multipart file-upload support on `request()` so consumers can drive `Upload`-scalar mutations from the same helper once `TODO-ALPHA-028-0.0.11` ships.
- Live HTTP tests under `examples/fakeshop/test_query/` switch to the helper.
- Tests under `tests/test/test_client.py`.

Dependencies:

- `TODO-ALPHA-028-0.0.11` (Upload scalar) — the file-upload helper path lights up once Upload-scalar inputs exist; the helper itself ships without it but gains a tested path here.

### TODO-ALPHA-035-0.0.12 — Response-extensions debug middleware

Priority: low (⚛️ parity-required; developer experience)

Severity: **low**

Status: planned; distinct from `TODO-ALPHA-033-0.0.12` (Django debug toolbar)

Why it matters:

- `graphene-django` ships a debug subsystem that exposes the executed SQL queries and raised exceptions for each GraphQL request via a `DjangoDebug` object. This is different from `TODO-ALPHA-033-0.0.12` (django-debug-toolbar SQL panel UI): graphene's mechanism is **inside the GraphQL response**, so frontend clients and Apollo DevTools can read it without the toolbar. Both mechanisms are useful and not mutually exclusive.
- A Strawberry-native equivalent is a small `SchemaExtension` that captures SQL (through `django.db.connection.queries` or via a port of graphene's cursor-wrap mechanism — see Architectural posture) and exceptions and attaches the result to the response's `extensions` map.
- `strawberry-graphql-django` ships **no** equivalent (no file references `connection.queries` and no `*debug*` module exists outside the toolbar middleware tracked by `TODO-ALPHA-033-0.0.12`); this card is graphene-django parity only.

Verified in upstream:

- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/__init__.py` — exports `DjangoDebugMiddleware`, `DjangoDebug`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/middleware.py` — `DjangoDebugContext` (lifecycle around cursor wrapping, exception capture, accumulated debug object), `DjangoDebugMiddleware` (Graphene `resolve` middleware — see Architectural posture; wraps each field resolution and returns the accumulated debug object when the field's return type matches `DjangoDebug`).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/types.py` — `class DjangoDebug(ObjectType)` with `sql: List(DjangoDebugSQL)` and `exceptions: List(DjangoDebugException)`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/sql/types.py` — `DjangoDebugSQL` shape: `vendor`, `alias`, `sql`, `duration`, `raw_sql`, `params`, `start_time`, `stop_time`, `is_slow`, `is_select`, plus Postgres-specific `trans_id`, `trans_status`, `iso_level`, `encoding`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/exception/types.py` — `DjangoDebugException` shape: `exc_type`, `message`, `stack`.
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/sql/tracking.py` — thread-local cursor wrapping (`wrap_cursor`, `unwrap_cursor`, `NormalCursorWrapper`, `ExceptionCursorWrapper`, `ThreadLocalState`).
- `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/exception/formating.py` — `wrap_exception` (serializes `exc_type`, `message`, `stack`).

Architectural posture:

- **"Middleware" is overloaded here**: graphene-django's `DjangoDebugMiddleware` is a **Graphene field-resolver middleware** (a callable invoked around each `resolve(root, info, **args)`), not a Django request/response middleware. The card title says "middleware" because that's what the graphene side calls the same idea; our Strawberry-native shape is a `SchemaExtension` (operation-scoped), not a Django middleware. The file name `middleware.py` is preserved on the graphene side for parity with their naming; ours lives under `extensions/`.
- **Exposure mechanism — pick one before writing the spec**:
  - graphene-django: **schema-level**. Consumers add a `_debug: DjangoDebug` field to their query and selectively pull `{ _debug { sql { duration } } }`. Pay-for-what-you-select.
  - Card's proposed Strawberry-native shape: **response-extensions-level**. Always emit the whole map under `extensions["debug"]` when the extension is enabled, or skip it entirely.
  - Both end up "in the GraphQL response," but the graphene shape gives consumers per-query selectivity at the cost of needing a schema field. The Strawberry-extension shape is simpler to wire and skips schema surface entirely.
- **Fidelity tradeoff — pick one before writing the spec**:
  - **Port graphene's cursor wrapping** (`sql/tracking.py`): wraps `connection.cursor` per-thread so the wrapper sees `start_time` before `execute()` and computes precise `duration`, captures Postgres-specific `iso_level` / `encoding`, surfaces `is_slow` / `is_select` flags. Higher fidelity; requires thread-local state management and `enable_instrumentation` / `disable_instrumentation` lifecycle hooks tied to the extension's operation begin / end.
  - **Use `django.db.connection.queries`**: the SchemaExtension reads `connection.queries` at operation end and emits a smaller shape. Lower fidelity (relies on Django's existing logging — no Postgres-specific data, less precise timing). Trivially threadsafe; no cursor wrapping to manage.
- **Thread-local state** (if porting the cursor wrap): `sql/tracking.py::ThreadLocalState` plus `enable_instrumentation` / `disable_instrumentation` are the lifecycle hooks. The SchemaExtension's `on_operation` (or equivalent) wraps `wrap_cursor` for the request and `unwrap_cursor` on teardown. Exception capture wires through the corresponding execution hooks similarly.

Definition of done:

- Implement `django_strawberry_framework/extensions/debug.py` as a Strawberry `SchemaExtension` that captures SQL and exceptions for the in-flight operation and attaches them to the response `extensions` map (key: `debug`).
- Pin the **exposure mechanism** (response-`extensions` map vs. schema-level `_debug` field) and the **fidelity choice** (cursor-wrap port vs. `connection.queries`) in the spec; default both to the simpler choice (response-`extensions` map + `connection.queries`) unless the spec authoring round chooses otherwise.
- Output shape mirrors graphene's `DjangoDebugSQL` / `DjangoDebugException` field names where the chosen fidelity supports them; document any shape narrowing (e.g., omitted Postgres-specific fields) explicitly.
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
- `Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (see also [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` custom Strawberry field class that field-level permissions will likely require).

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

- `Meta.search_fields` is one of the five django-graphene-filters Layer-3 Meta keys explicitly listed in [`GOAL.md`][goal] alongside `filterset_class`, `orderset_class`, `aggregate_class`, and `fields_class`. Without it the package cannot claim full DGF parity at 1.0.0.
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

Status: blocked on `TODO-ALPHA-023-0.0.9` (`DjangoConnectionField`). When the connection field lands, this card unblocks and ships in the same release. The post-`1.0.0` "Relay magic" differentiators (type-rename GlobalID migrations, polymorphic connections, stable cursors, refetchable containers, permission-aware cursor decoding) live separately in [`BACKLOG.md`][backlog] item 39 — they extend this story rather than block it.

This is the umbrella spec for the **complete Relay surface at `0.0.9`** — Node foundation + Connection + Root entry points + schema validation + test helpers. The Node half shipped in `DONE-011-0.0.5`; the Connection half is its own implementation slice (`TODO-ALPHA-023-0.0.9`); this card carries the connective tissue that ties them together into one end-to-end Relay story.

Resolved blockers (shipped in `DONE-011-0.0.5`):

- ~~`Meta.interfaces` design~~ — `Meta.interfaces` accepted end-to-end for any Strawberry interface; `(relay.Node,)` activates the Node foundation.
- ~~`GlobalID` mapping decision~~ — Strawberry-supplied `id: GlobalID!` from the Relay interface replaces the synthesized `id: int!`; Django primary key remains projected as a connector column for the optimizer (Decision 2 of [`docs/SPECS/spec-011-relay_interfaces-0_0_5.md`][spec-011]).
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

Shipped the `DjangoListField` factory function in `django_strawberry_framework/list_field.py` as a one-line `field: list[T] = DjangoListField(TargetType)` shape for root Query fields. The default resolver pulls `target_type.__django_strawberry_definition__.model._default_manager.all()` and applies `cls.get_queryset(...)` in both sync and async contexts; a consumer-supplied `resolver=` overrides the default body and any `Manager`/`QuerySet` return value receives `target_type.get_queryset(qs, info)` (graphene-django parity per rev2 H1 of `docs/SPECS/spec-016-list_field-0_0_7.md`), with `Manager → QuerySet` coercion handled by the field wrapper before `get_queryset` runs. Async consumer resolvers are detected at construction time via `inspect.iscoroutinefunction` and routed through an `async def` wrapper. Outer-list nullability is driven by the consumer's class-attribute annotation (`list[T]` → `[T!]!`, `list[T] | None` → `[T!]`). Optimizer cooperation rides the existing root-gated `info.path.prev is None` planning hook (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve`).

Added a new `all_library_branches_via_list_field` root field via `DjangoListField` to the library example schema. This is an intentional **card-text departure** from the original "Live HTTP coverage replacing one of the hand-rolled `all_library_*` resolvers" wording, per [Decision 9][spec-016] "Card-text departure" (rev4 H3): the add-only posture keeps `all_library_branches`'s `order_by("id")` intact so the existing live HTTP determinism tests stay green; no existing `all_library_*` resolver was replaced. A new live HTTP test `test_library_branches_via_djangolistfield_optimized_nested_selection` in `examples/fakeshop/test_query/test_library_api.py` pins the response shape and the optimizer's `prefetch_related("shelves")` plan via `CaptureQueriesContext`.

Validation tests in `tests/test_list_field.py` cover: non-class targets, non-`DjangoType` subclasses, unregistered types, non-callable `resolver=`, default-resolver shape, sync coroutine rejection in `get_queryset`, sync + async `get_queryset` paths, sync + async consumer-resolver `QuerySet` returns receiving `get_queryset`, sync + async Python `list` pass-through, nullable-outer / non-nullable-outer rendering, root-position optimizer planning, FK-id elision, and `Meta.primary` interaction (explicit primary + explicit secondary). The version bump from `0.0.6` is deferred to the last `0.0.7` card to ship per Decision 10 of the spec; this card leaves `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion at `0.0.6`.

Files touched: `django_strawberry_framework/list_field.py` (new), `django_strawberry_framework/__init__.py`, `tests/test_list_field.py` (new), `tests/base/test_init.py`, `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`, plus the Slice 5 doc sweep across `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `GOAL.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md`.

Spec: `docs/SPECS/spec-016-list_field-0_0_7.md`. Build plan: `docs/builder/build-016-list_field-0_0_7.md`.

### DONE-017-0.0.7 — `apps.py` and Django app config

Parity: ⚛️&🍓 required (both upstreams ship `apps.py` with an `AppConfig` for `INSTALLED_APPS`-driven discovery).

Shipped `django_strawberry_framework/apps.py` containing `DjangoStrawberryFrameworkConfig(AppConfig)` with `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"`; no `ready()` body in `0.0.7` (deferred to the card that needs one). Consumers list `"django_strawberry_framework"` in `INSTALLED_APPS`; Django's implicit single-AppConfig discovery resolves the explicit class, and Django's check / signal hooks now resolve through the package's AppConfig.

Borrowed the behavioral shape from `strawberry_django/apps.py` verbatim (two class-level attributes, `name` then `verbose_name`); the module docstring (required by ruff's `D100`) and class docstring (required by ruff's `D101`) are additive, forced by this repo's stricter pydocstyle gate. `DjangoStrawberryFrameworkConfig` is NOT re-exported from `django_strawberry_framework/__init__.py` — Django's app loader resolves it through its dotted module path, and consumers reach it via `INSTALLED_APPS`, not via the package's import surface.

Package-internal tests at `tests/test_apps.py` cover the four positive contracts (importability from `django_strawberry_framework.apps`, `django.apps.AppConfig` subclass, `name` / `verbose_name` attribute values, and Django registry pickup via `django.apps.apps.get_app_config("django_strawberry_framework")`) plus one consolidated negative-shape test (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) that iterates `{"ready", "label", "default_auto_field", "default"}` and asserts each is absent from `DjangoStrawberryFrameworkConfig.__dict__` — pinning the "no extra behavioral AppConfig attributes" discipline across Decisions 2 / 4 / 5 / 8 of the spec. The existing live `/graphql/` HTTP tests at `examples/fakeshop/test_query/test_library_api.py` continue to pass unmodified — `examples/fakeshop/config/settings.py #"django_strawberry_framework"`'s `"django_strawberry_framework"` `INSTALLED_APPS` entry now resolves to the explicit AppConfig without any consumer-side change.

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

Pinned the package's multi-database cooperation contract — `router.db_for_read` on FK-id elision stubs (parent row forwarded as the `instance=` hint when present), explicit `.using(alias)` `_db` preservation through [`OptimizationPlan.apply`][plans], consumer-provided [`OptimizerHint.prefetch(Prefetch(queryset=…))`][glossary-optimizerhint] round-trip with `_db` intact, and strictness-mode's connection-agnostic shape under non-default aliases. Tests in [`tests/types/test_resolvers.py`][test-resolvers] (five resolver-level tests against `_build_fk_id_stub` and `_check_n1` — four FK-id elision branches plus the strictness connection-agnostic shape; FK-id tests hermetic via mocked router), [`tests/optimizer/test_multi_db.py`][test-multi-db] (one optimizer-plan-level test against `OptimizerHint.prefetch` round-trip; `OptimizationPlan.apply` `_db` preservation is verified transitively by the live HTTP test per AGENTS.md #"any coverage line achievable via a real GraphQL query"), and [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db] (live `/graphql/` HTTP under `FAKESHOP_SHARDED=1` with `@pytest.mark.django_db(databases=...)` and full `Branch → Shelf → Book` seeding). [`examples/fakeshop/config/settings.py`][settings] ships an additive `DATABASES` layout — `default → db.sqlite3` in both modes; `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3` — and the secondary shard's seed is committed at [`examples/fakeshop/db_shard_b.sqlite3`][db-shard-b.sqlite3] so sharded mode works out of the box. [`docs/GLOSSARY.md#multi-database-cooperation`][glossary-multi-database-cooperation] flipped from `planned for 0.0.7` to `shipped (0.0.7)` with a four-axis entry body; [`docs/README.md`][docs-readme] `### Sharded mode (multi-DB)` describes the additive layout. Spec: [`docs/SPECS/spec-019-multi_db-0_0_7.md`][spec-019]. Zero production code change; the cooperation already existed in [`django_strawberry_framework/types/resolvers.py::_build_fk_id_stub`][resolvers]. [`BACKLOG.md`][backlog] item 41 owns first-class sharding-aware planning post-`1.0.0` (including threading the parent queryset's `_db` into generated child `Prefetch` querysets, which this card explicitly leaves to that future card).


### DONE-046-0.0.7 — Django Trac #37064 hardening + `safe_wrap_connection_method`

Parity: 🚧 defensive — neither upstream ships a patch for Django Trac #37064; this card is unique to django-strawberry-framework's hardening posture.

Shipped a two-half defense-in-depth for [Django Trac #37064](https://code.djangoproject.com/ticket/37064) (closed upstream as `wontfix`), which clobbers wrapped `connections[alias]` methods at `tearDownClass`:

**Half 1 (unwrap-time): package-level patch.** [`django_strawberry_framework/_django_patches.py`][django-patches] adds `_patched_remove_databases_failures` and an idempotent `apply()` entry point. [`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`][apps] invokes `apply()` at Django app-load time, so consumers get the fix automatically by having `"django_strawberry_framework"` in `INSTALLED_APPS` — no `conftest.py` workaround, no test-case base class to inherit. The patched `_remove_databases_failures` adds an `isinstance(method, _DatabaseFailure)` guard before the `setattr(..., method.wrapped)` step, leaving any consumer wrapper intact. Log-once sentinel guards against double-application across re-imports.

**Half 2 (wrap-time): consumer helper.** [`django_strawberry_framework/test/_wrap.py::safe_wrap_connection_method`][wrap] is the cooperative wrap-time mirror, modeled on `django-debug-toolbar`'s `wrap_cursor` `isinstance` check. When a consumer wants to monkey-patch a method on `connections[alias]` for testing, calling this helper installs the wrapper without clobbering an outer Django `_DatabaseFailure` wrapper that may already be in place. Public export from [`django_strawberry_framework.test`][test-init].

[`docs/GLOSSARY.md#django-trac-37064-hardening`][glossary-django-trac-37064-hardening] and [`docs/GLOSSARY.md#safe_wrap_connection_method`][glossary-safe-wrap-connection-method] flipped to `shipped (0.0.7)`. Tests cover the patch's idempotency, log-once sentinel, callable guard, defensive imports, the `installed=None` regression branch, and the consumer-side wrap helper's `_DatabaseFailure`-already-present refusal.

NNN note: `046` was assigned ahead of the prior max (`TODO-STABLE-045-1.0.0`) to avoid a multi-file rename of `WIP-ALPHA-020-0.0.7` across 5+ specs. Per the KANBAN card-ID convention, NNN is not stable and grouping is by version, not NNN.

### DONE-047-0.0.7 — Warning-free scalar registration via `StrawberryConfig.scalar_map`

Pinned the package-defined scalar registration path: [`BigInt`][glossary-bigint-scalar] is redefined as a bare `NewType("BigInt", int)` and registered via [`StrawberryConfig.scalar_map`](https://strawberry.rocks) through a new public [`strawberry_config(*, extra_scalar_map=None, **config_kwargs) -> StrawberryConfig`][glossary-strawberry-config] factory exported from `django_strawberry_framework`. The factory is keyword-only on `extra_scalar_map=` and forwards every other kwarg to upstream `StrawberryConfig(...)`, so consumers compose package scalars and custom `StrawberryConfig` options (`auto_camel_case=False`, `relay_max_results=200`, etc.) in one call; passing `scalar_map=` directly raises `ValueError`. Consumers add `config=strawberry_config()` to their `strawberry.Schema(...)` call once; direct `BigInt` annotations work unchanged. The `warnings.catch_warnings()` suppression block in `django_strawberry_framework/scalars.py` is removed because the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload at `.venv/lib/python3.10/site-packages/strawberry/types/scalar.py` returns a `ScalarDefinition` without triggering the `DeprecationWarning`. Tests in `tests/test_scalars.py` cover the factory contract (thirteen tests — eight scalar-map + five `**config_kwargs` passthrough) and the round-trip wire format through a `strawberry.Schema(config=strawberry_config())` (two integration tests); `tests/base/test_init.py`'s `__all__` assertion adds `strawberry_config`; `tests/types/test_converters.py`'s BigInt-section schemas migrate to `config=strawberry_config()`. `examples/fakeshop/config/schema.py` migrates to the new pattern; `docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, and `TODAY.md` schema-construction examples migrate too. Breaking change in alpha (per `docs/SPECS/spec-013-deferred_scalars-0_0_6.md` Decision 6 and the `PositiveBigIntegerField` precedent in `0.0.6`): any schema that resolves to `BigInt` — direct annotations OR converter-backed `BigIntegerField` / `PositiveBigIntegerField` `DjangoType` fields — that doesn't add `config=strawberry_config()` sees Strawberry schema-construction fail with `Unexpected type ...BigInt`. Spec: `docs/SPECS/spec-020-scalar_map_helper-0_0_7.md`. The version bump from `0.0.7 → 0.0.8` is NOT in this card per Decision 8.

Build plan: [`docs/builder/build-020-scalar_map_helper-0_0_7.md`][build-020-scalar-map-helper-0-0-7].

### DONE-048-0.0.7 — Scalar conversion end-to-end coverage in the fakeshop example

Parity: ⚛️&🍓 required (both upstreams ship scalar conversion for `BooleanField`, `FloatField`, `DecimalField`, `DateField`, `DateTimeField`, `TimeField`, `JSONField`, `UUIDField`, `BigIntegerField`, `PositiveBigIntegerField`); this card moves those converter rows from package-internal-only coverage to live `/graphql/` HTTP coverage on the fakeshop example in **both** nullable and non-null shapes.

Closed the gap between the package's converter table ([`django_strawberry_framework/types/converters.py::SCALAR_MAP`][converters]) and the example's live HTTP test surface. Before this card, the converter table was exercised end-to-end only for `int`/`str` collapses (covered transitively by every `id`/`name`/`title` selection) and `BigInt` via package-internal unit tests; every other row's wire format was unverified against a real `GraphQLView` round-trip on the example app.

**Surfaces shipped:**

1. **New `apps.scalars` app** — `examples/fakeshop/apps/scalars/` carries a **paired model layout**:
   - `ScalarSpecimen` — every scalar field non-null, exposed via `ScalarSpecimenType`. Adds an intra-model self-FK `parent` (`related_name="children"`) so the example exercises self-referential FK planning under the optimizer.
   - `NullableScalarSpecimen` — every scalar field nullable (`null=True, blank=True`), exposed via `NullableScalarSpecimenType`. Adds a cross-model FK `partner: ForeignKey(ScalarSpecimen, on_delete=SET_NULL, related_name="nullable_partners")` — the only `SET_NULL` ondelete in the example tree, and the only cross-model FK in the scalars app.
   - The pairing is deliberate (not a single model with paired fields). It exercises **upstream code paths no other example app reaches**: Django's two-`CreateModel` initial migration path, the registry / `finalize_django_types()` resolving sibling `DjangoType` classes in one app, Strawberry type registration across sibling types in one schema build, the optimizer planning across two managed models in one query, and `SET_NULL` ondelete behavior.
   - `apps.scalars.schema` composes two root resolvers (`all_scalar_specimens`, `all_nullable_scalar_specimens`) into the project root `Query` at [`examples/fakeshop/config/schema.py`][example-schema]; `ScalarsConfig` lands in `INSTALLED_APPS` at [`examples/fakeshop/config/settings.py`][settings].

2. **Reverse-FK exposure** — `ScalarSpecimenType.nullable_partners` is added to `Meta.fields` so a single GraphQL query can traverse the cross-model link in both directions.

3. **`Patron.lifetime_fines_cents`** — `BigIntegerField(default=0)` added to `apps.library.models.Patron` (migration `0003_patron_lifetime_fines_cents.py`); exposed via `PatronType.Meta.fields`. Pins the `BigIntegerField → BigInt` converter row on a real-domain library model in addition to the dedicated coverage row, so the BigInt path is proven on more than one model surface.

**Tests:** [`examples/fakeshop/test_query/test_scalars_api.py`][test-scalars-api] (eight tests):
- Full non-null wire-format sweep covering every field on `ScalarSpecimen`
- Signed-negative `BigInt` round-trip
- `BigInt`-at-zero edge case
- Schema introspection asserting `BigInt` converter resolves correctly in both shapes (`NON_NULL` on `ScalarSpecimenType`; bare `SCALAR` on `NullableScalarSpecimenType`)
- All-NULL nullable wire format covering every nullable converter branch
- Cross-model `partner` FK linkage round-trip
- Reverse-FK `nullablePartners` exposure
- Self-FK `parent` / `children` traversal

Plus one new test in [`examples/fakeshop/test_query/test_library_api.py`][test-library-api] selecting `lifetimeFinesCents` at `2**53 + 12345` so the decimal-string serialization is genuinely verified (a JS-number round-trip would lose precision).

**Migrated tests:** three tests in [`tests/types/test_converters.py`][test-converters] (`test_big_integer_field_maps_to_bigint_in_schema`, `test_big_integer_field_nullable_in_schema`, `test_positive_big_integer_field_maps_to_bigint_in_schema`) are removed because their assertions are now earned via the real-query path on the new scalars app — per the repository's real-query coverage rule. Further test migrations (JSONField, FK-id elision under the optimizer, etc.) are tracked separately as follow-ups under the audit identified during this card.

**Deferred:** `ArrayField` and `HStoreField` are PostgreSQL-only; the fakeshop runs on SQLite, so their converter rows stay covered by `tests/` against package-internal fixtures. The `apps.scalars.models` module docstring records the rationale.

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
- Strategic differentiation candidates (features neither `graphene-django` nor `strawberry-graphql-django` ship cleanly) live in [`BACKLOG.md`][backlog]. When a `BACKLOG.md` item is scheduled, promote it to a `TODO-NNN-X.Y.Z` or `TODO-NNN-X.Y.Z` card here and cross-reference back.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: BACKLOG.md
[goal]: GOAL.md
[readme]: README.md

<!-- docs/ -->
[docs-readme]: docs/README.md
[glossary-bigint-scalar]: docs/GLOSSARY.md#bigint-scalar
[glossary-django-trac-37064-hardening]: docs/GLOSSARY.md#django-trac-37064-hardening
[glossary-multi-database-cooperation]: docs/GLOSSARY.md#multi-database-cooperation
[glossary-optimizerhint]: docs/GLOSSARY.md#optimizerhint
[glossary-safe-wrap-connection-method]: docs/GLOSSARY.md#safe_wrap_connection_method
[glossary-strawberry-config]: docs/GLOSSARY.md#strawberry_config

<!-- docs/SPECS/ -->
[spec-011]: docs/SPECS/spec-011-relay_interfaces-0_0_5.md
[spec-016]: docs/SPECS/spec-016-list_field-0_0_7.md
[spec-019]: docs/SPECS/spec-019-multi_db-0_0_7.md

<!-- docs/builder/ -->
[build-020-scalar-map-helper-0-0-7]: docs/builder/build-020-scalar_map_helper-0_0_7.md

<!-- django_strawberry_framework/ -->
[apps]: django_strawberry_framework/apps.py
[converters]: django_strawberry_framework/types/converters.py
[django-patches]: django_strawberry_framework/_django_patches.py
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
[fakeshop-test-multi-db]: examples/fakeshop/test_query/test_multi_db.py
[settings]: examples/fakeshop/config/settings.py
[test-library-api]: examples/fakeshop/test_query/test_library_api.py
[test-scalars-api]: examples/fakeshop/test_query/test_scalars_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
