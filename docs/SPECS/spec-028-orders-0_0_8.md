# Spec: Ordering subsystem (`OrderSet`, `RelatedOrder`, `Meta.orderset_class`)

Target release: `0.0.8` (card [`DONE-028-0.0.8`][kanban]).
Status: shipped (`0.0.8`). [`django_strawberry_framework/orders/`][orders] ships `__init__.py`, `base.py`, `factories.py`, `inputs.py`, and `sets.py`; finalizer phase-2.5 binding runs through `_bind_ordersets()`; `Meta.orderset_class` is in `ALLOWED_META_KEYS`; the fakeshop library schema carries `Meta.orderset_class` on its `DjangoType` classes plus `orderBy:` arguments on its root resolvers; [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] carries the live `/graphql/` order tests and [`tests/orders/test_composition.py`][test-orders-composition] the filter-plus-order composition tests.
Owner: package maintainer.
Predecessors: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] (the Filtering subsystem — the lazy-resolution layers, the finalizer phase-2.5 binding seam, the per-module input-class namespace, the consumer-helper pattern, the active-input-only permission discipline, and the sync/async `apply_*` split all carry over); [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020]; [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-015] (Relay-Node wiring at finalizer phase 2.5); [`docs/SPECS/spec-018-meta_primary-0_0_6.md`][spec-018] (the `Meta.primary` design + the [`TypeRegistry`][registry-typeregistry] keying convention [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) respects); [`docs/GLOSSARY.md`][glossary] entries [`OrderSet`][glossary-orderset], [`RelatedOrder`][glossary-relatedorder], [`Meta.orderset_class`][glossary-metaorderset_class].

Each Decision's justification and rejected alternatives live in the rationale companion [`docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md`][spec-028-rationale].

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`OrderSet`][glossary-orderset] — the declarative ordering class. Reuses the [`FilterSet`][glossary-filterset] subsystem's lazy-resolution architecture with `OrderSet` substituted for `FilterSet` and `RelatedOrder` for `RelatedFilter`.
- [`Ordering`][glossary-ordering] — the public direction enum used as the leaf value in generated order input types (`ASC` / `DESC` plus NULLS-positioning variants).
- [`order_input_type`][glossary-order_input_type] — the consumer helper (with its `OrderInput[...]` spelling) that returns the resolver-argument element annotation; resolvers wrap it as `list[OrderInput[MyOrder]] | None` to expose `orderBy: [<T>OrderInputType!]`.
- [`RelatedOrder`][glossary-relatedorder] — cross-relation ordering traversal. Accepts a target `OrderSet` class, an absolute import path string, or an unqualified name for circular references; lazy-resolved at finalizer time.
- [`Meta.orderset_class`][glossary-metaorderset_class] — the consumer-facing key that points a [`DjangoType`][glossary-djangotype] at its `OrderSet`. In `ALLOWED_META_KEYS` per [Decision 7](#decision-7--metaorderset_class-promotion-gate).
- [`DjangoType`][glossary-djangotype] — the model-backed Strawberry type the ordering sidecar attaches to.
- [`Meta.fields`][glossary-metafields] — the Meta key whose list / `"__all__"` shorthand defines which model fields are orderable on an `OrderSet`.
- [`finalize_django_types`][glossary-finalize_django_types] — the synchronization point where the ordering subsystem's lazy-resolution pipeline runs (phase 2.5, the same seam [`Meta.interfaces = (relay.Node,)`][glossary-metainterfaces] and [`Meta.filterset_class`][glossary-metafilterset_class] use).
- [`FilterSet`][glossary-filterset] / [`RelatedFilter`][glossary-relatedfilter] / [`filter_input_type`][glossary-filter_input_type] / [`Meta.filterset_class`][glossary-metafilterset_class] — the sibling family whose architecture this subsystem mirrors; Layer 6 (the dynamic-factory cache for connection fields without an explicit `*_class`) is not part of either, per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — an `.order_by(...)` clause does not break the optimizer's [Queryset diffing][glossary-queryset-diffing] cooperation; covered by [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer) and a live HTTP test.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — pre-order visibility scoping ([Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer)).
- [`DjangoConnectionField`][glossary-djangoconnectionfield] and [`DjangoListField`][glossary-djangolistfield] — both build an `orderBy:` argument from the target type's `Meta.orderset_class` and apply it through the same `OrderSet`.
- [`Meta.primary`][glossary-metaprimary] — the multi-`DjangoType`-per-model design whose [`TypeRegistry`][registry-typeregistry] keying convention this subsystem respects per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle).
- [`ConfigurationError`][glossary-configurationerror] — raised at type-creation, finalization and apply time for a non-`OrderSet` `Meta.orderset_class`, unresolvable `RelatedOrder` targets, invalid order paths, owner-model mismatches, multi-owner conflicts, and orphan helper references — see [Error shapes](#error-shapes).
- [`AggregateSet`][glossary-aggregateset] / [`get_child_queryset`][glossary-get_child_queryset] — planned Layer-3 sidecars that will reuse the architecture; [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — the shipped cascade helper a `get_queryset` hook can call.
- [`FieldSet`][glossary-fieldset] / [`Meta.fields_class`][glossary-metafields_class] — planned Layer-3 sidecar; orthogonal to ordering (field selection vs ordering).

Foundational invariants and cross-cutting surfaces — all defined in [`docs/GLOSSARY.md`][glossary]:

- [Relation handling][glossary-relation-handling] — the FK / OneToOne / M2M / reverse-relation traversal `RelatedOrder` plugs into.
- [Relay Node integration][glossary-relay-node-integration] — ordering does NOT consult Relay shape (an `ORDER BY id` against a Relay-Node-shaped target uses the Django PK column, not the GraphQL `GlobalID`), so unlike the filter side's Decision 4 conditional the order side has no Relay-vs-scalar branch.
- [Definition-order independence][glossary-definition-order-independence] — the invariant the lazy-resolution pipeline preserves so cross-module `RelatedOrder("...")` references work regardless of import order.
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — the deferred-Meta-key promotion rule; [Decision 7](#decision-7--metaorderset_class-promotion-gate)'s gate is one instance of it.
- [Choice enum generation][glossary-choice-enum-generation] — choice-backed columns produce a Strawberry enum on the type side; the order side does not consult it (an `ORDER BY status` orders by the stored DB value).
- [Scalar field conversion][glossary-scalar-field-conversion] — the type side's column conversion; an order leaf is typed `Ordering | None` regardless of the column's scalar.
- [OptimizerHint][glossary-optimizerhint] — the hint primitive `Meta.optimizer_hints` declarations carry; ordering clauses compose with hints.
- [only() projection][glossary-only-projection] — the optimizer's projection contract. The projection is selection-tree-derived: the optimizer does not extend its `.only(...)` field set from the queryset's `ORDER BY` (it reads `query.order_by` only to plan connection windows). The user-visible behavior is correct because Django fetches the columns an `ORDER BY` needs regardless of the `.only(...)` hint — that cooperation is Django's, not the package's.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule at [`AGENTS.md`][agents] #"Test placement:" (package tests under `tests/orders/`; live HTTP tests under `examples/fakeshop/test_query/`); the live-HTTP-priority rule at [`AGENTS.md`][agents] #"any line reachable via a real GraphQL query against fakeshop"; the settings-keys rule at [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands".
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical per [Decision 13](#decision-13--live-http-coverage-strategy).
- [`docs/TREE.md`][tree] — tests mirror source one-to-one. The subsystem lives at [`django_strawberry_framework/orders/`][orders] per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface); [`docs/TREE.md`][tree] lists `orders/` in its current on-disk layout (rendered from module docstrings by [`scripts/build_tree_md.py`][build-tree], which omits `__init__.py`) and the mirrored `tests/orders/` tree alongside it.
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, all defs at the bottom under the 10 canonical group headers).

## Slice checklist

Six slices; boxes stay unticked by convention, the Status line is the truth.

- [ ] Slice 1: Foundation — module layout + `RelatedOrder` primitive + `OrderSet` metaclass
  - [ ] [`django_strawberry_framework/orders/`][orders] is a subpackage with `__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py` per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface). Module docstrings pin each file's responsibility (`base.py` = `RelatedOrder`; `sets.py` = `OrderSet` + metaclass + `apply_sync` / `apply_async`; `factories.py` = `OrderArgumentsFactory`; `inputs.py` = order input classes materialized as module globals + `Ordering` enum + input-data adapters + lifecycle ledger).
  - [ ] `base.py` ships `RelatedOrder` (the collapsed port of [`django_graphene_filters/orders.py::BaseRelatedOrder`][upstream-cookbook-orders] + `RelatedOrder`). It derives from the **neutral shared** [`django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin`][sets-mixins], a subclass of [`sets_mixins.py::LazyRelatedClassMixin`][sets-mixins], reached by sibling import (NOT through `filters/base.py`, which would load the entire filter subsystem just to build orders); the same module carries [`ClassBasedTypeNameMixin`][sets-mixins], which `OrderSet` inherits for the `{cls.__name__}InputType` naming convention shared across the set families.
  - [ ] `sets.py` ships `OrderSetMetaclass` (port from [`django_graphene_filters/orderset.py::OrderSetMetaclass`][upstream-cookbook-orderset]) and `OrderSet` (port from [`django_graphene_filters/orderset.py::AdvancedOrderSet`][upstream-cookbook-orderset] — Layer 3 + Layer 4 of [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6)). `OrderSet` accepts [`Meta.model`][glossary-metamodel] and `Meta.fields` (a re-readable collection of field-name strings such as `["name", "created_date"]`, or the `"__all__"` shorthand for every **column-backed** model field per [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6) — includes forward FK / OneToOne columns; excludes reverse relations and M2M managers), and per-field `check_<field>_permission` hooks. It carries the `_owner_definition: DjangoTypeDefinition | None` slot bound at finalizer phase 2.5, and the resolver-facing classmethod pair `apply_sync(input_value, queryset, info) -> QuerySet` / `async def apply_async(input_value, queryset, info) -> QuerySet` per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer); each carries `info` end-to-end so per-field `check_<field>_permission` gates and active-input-only scope run consistently.
  - [ ] `inputs.py` IS the input-class namespace per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) — generated order input classes are materialized as real module globals of `django_strawberry_framework.orders.inputs` via `materialize_input_class(name, input_cls)`, keyed by stable class-derived names (e.g., `"BranchOrderInputType"`); the private `_materialized_names: dict[str, type]` ledger tracks `name → input class` (source-class collision detection lives in `OrderArgumentsFactory._type_orderset_registry`). This namespace is **disjoint** from `django_strawberry_framework.filters.inputs` — each Layer-3 family owns its own per-module namespace, so `OrderSet` and `FilterSet` input classes never collide on the lookup path Strawberry's [`LazyType.resolve_type`][strawberry-lazy] uses.
  - [ ] `inputs.py` also ships the `Ordering` enum (`ASC` / `DESC` / `ASC_NULLS_FIRST` / `ASC_NULLS_LAST` / `DESC_NULLS_FIRST` / `DESC_NULLS_LAST` per [Decision 5](#decision-5--ordering-enum-and-argument-shape)) as a `@strawberry.enum`, the leaf field type on every generated order input.
- [ ] Slice 2: Factories — `OrderArgumentsFactory` BFS + inputs adapters
  - [ ] `factories.py` ships `OrderArgumentsFactory` (the [`django_graphene_filters/order_arguments_factory.py::OrderArgumentsFactory`][upstream-cookbook-order-arguments-factory] BFS) — Layer 5 of [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6). The walk lives on the shared [`django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory`][utils-inputs] base; `OrderArgumentsFactory` supplies `_build_input_triples` plus the order-family caches. Classes are emitted `@strawberry.input`-decorated through `django_strawberry_framework.orders.inputs.build_input_class` (an alias of `utils/inputs.py::build_strawberry_input_class`). Leaf fields use the `Ordering` enum; `RelatedOrder` fields emit `Annotated["<TargetOrderSet>InputType", strawberry.lazy("django_strawberry_framework.orders.inputs")] | None` references (the same Layer-5 cycle-safe forward-reference shape the filter subsystem uses per [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 3).
  - [ ] `inputs.py` ships the input-data adapters: `_build_input_fields` (target-orderset references via `strawberry.lazy(...)` over module globals; leaf fields typed `Ordering | None`), `convert_order_field_to_input_annotation(model_field, owner_definition)` (always `Ordering | None`, because the only legal input value for a leaf is a direction, NOT the field's value), and `normalize_input_value(orderset_cls, input_value)` (the runtime symmetric — walks the nested `RelatedOrder` input tree and produces the flat list of `(field_path, Ordering | None)` tuples the apply pipeline turns into `order_by(...)` arguments).
- [ ] Slice 3: Wiring — `Meta.orderset_class` promotion + finalizer phase 2.5 binding
  - [ ] [`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`][definition] carries an `orderset_class` slot, populated by `DjangoType.__init_subclass__` from `Meta.orderset_class`.
  - [ ] `"orderset_class"` is in [`ALLOWED_META_KEYS`][base], not [`DEFERRED_META_KEYS`][base]. [`django_strawberry_framework/types/base.py::_validate_orderset_class`][base] raises [`ConfigurationError`][glossary-configurationerror] unless the supplied class is an `OrderSet` subclass (sharing the `_validate_set_sidecar` skeleton with `_validate_filterset_class`). **The helper uses a local in-function `from ..orders.sets import OrderSet` import** — NOT a top-of-file import — to dodge the `types → orders → types` module-load cycle.
  - [ ] [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer] runs the order-binding pass in phase 2.5 (after `_bind_filtersets()`, before phase 3's `strawberry.type` decoration) through `_bind_ordersets`, which configures the shared driver `_bind_sidecar_sets`. Four ordered subpasses per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering): (1) bind every `OrderSet`'s `_owner_definition`, no `get_fields()` calls; (2) call `get_fields()` AND read `.orderset` on every `related_orders` entry (so Layer-2 lazy-class resolution fires here — the order side's `get_fields()` does not itself resolve lazy targets the way the filter side's `get_filters()` does), with an `ImportError` from an unresolved `RelatedOrder("...")` rewrapped as [`ConfigurationError`][glossary-configurationerror], `__cause__` preserved; (3) **orphan-validate** `_helper_referenced_ordersets` against the wired ordersets — BEFORE materialization, so an orphan failure leaves no partial state in `_materialized_names` or `OrderArgumentsFactory.input_object_types`; (4) **materialize** input classes via `OrderArgumentsFactory(orderset_cls).arguments` plus a `materialize_input_class(name, input_cls)` call for every built class. `orders/inputs.py` registers `clear_order_input_namespace` and `orders/__init__.py` registers `_clear_helper_referenced_ordersets`, each through [`django_strawberry_framework/registry.py::register_subsystem_clear`][registry], and `TypeRegistry.clear()` replays every registered callback via `::iter_subsystem_clears()` per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle).
- [ ] Slice 4: Live HTTP coverage in fakeshop
  - [ ] [`examples/fakeshop/apps/library/orders.py`][fakeshop-library] declares `BranchOrder`, `ShelfOrder`, `BookOrder`, `LoanOrder`, `PatronOrder` (among the app's other ordersets) over the same `DjangoType` owners the filter side uses, so the live tests exercise filter / order composition end-to-end. The M2M side targets `GenreType`; `GenreOrder` lives in the **separate module** [`examples/fakeshop/apps/library/orders_genre.py`][fakeshop-library] so `BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")` exercises the Layer-2 absolute-import-path branch, and `GenreOrder.books = RelatedOrder("apps.library.orders.BookOrder")` closes the cycle in the same form from the other side. Same-module unqualified-name resolution is exercised by every other `RelatedOrder("...")` declaration in `orders.py`.
  - [ ] [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] declares `Meta.orderset_class = orders.BranchOrder` (etc.) on the corresponding `DjangoType` classes. Root-list resolvers (`all_library_branches`, `all_library_books`, etc.) annotate `order_by:` as `list[OrderInput[orders.BranchOrder]] | None` per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper). Each resolver **calls the owning type's `get_queryset(queryset, info)` BEFORE `OrderSet.apply_sync(...)`**, then chains `queryset = <Type>Filter.apply_sync(filter, queryset, info)` → `queryset = <Type>Order.apply_sync(order_by, queryset, info)` (filter narrows the rows, order arranges them).
  - [ ] [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] carries the live `/graphql/` order contracts listed in the [Test plan](#test-plan): scalar ascending order; NULLS positioning on `Book.subtitle`, parametrized across all four NULLS directions; forward-FK relation order; reverse-FK relation order, **row-preserving via aggregate** (a to-many path is ordered by a `Min` (ascending) / `Max` (descending) aggregate of the child column, so the parent row is never multiplied); M2M relation order through the absolute-import-path `RelatedOrder`; flat-shorthand path order (`Meta.fields = ["shelf__code"]` rendering as `shelfCode: ASC`); composition with the filter subsystem; optimizer cooperation at a pinned query count; root `get_queryset` honoring; split-pair active-input-only `check_<field>_permission` discipline; the active-branch relation-level permission gate; multi-field priority ordering; and the empty-list / null-direction no-op.
- [ ] Slice 5: Docs
  - [ ] [`docs/GLOSSARY.md`][glossary] carries [`OrderSet`][glossary-orderset], [`RelatedOrder`][glossary-relatedorder], [`Meta.orderset_class`][glossary-metaorderset_class], [`order_input_type`][glossary-order_input_type], and [`Ordering`][glossary-ordering] (all `shipped (0.0.8)`), under the Ordering category and in the [Index][glossary-index].
  - [ ] [`docs/TREE.md`][tree] lists `orders/` in the current on-disk layout and the mirrored `tests/orders/` tree.
  - [ ] [`docs/README.md`][docs-readme] documents the ordering surface, `Ordering` included; [`README.md`][readme] and [`TODAY.md`][today] show `Meta.orderset_class` wiring an `OrderSet`.
- [ ] Slice 6: Cross-family composition test with the Filtering subsystem
  - [ ] [`tests/orders/test_composition.py`][test-orders-composition] — `test_filter_and_order_compose_through_finalizer_and_apply_pipelines` constructs a `DjangoType` with BOTH `Meta.filterset_class` AND `Meta.orderset_class`, calls `finalize_django_types()`, and asserts both factories' input types are reachable from the schema AND a resolver consuming both arguments produces a queryset whose SQL carries the `WHERE <filter>` AND `ORDER BY <order>` clauses; `test_filter_and_order_share_lazy_related_class_mixin_via_neutral_module` asserts both families reach the Layer-2 mixin through the neutral [`sets_mixins.py`][sets-mixins] module rather than through each other. This test carries the filter spec's Slice 6.

## Problem statement

Consumers who wire `Meta.filterset_class` reach for `Meta.orderset_class = ItemOrder` next. Both upstreams expect an ordering surface beside the filter surface: `strawberry-graphql-django` ships `@strawberry_django.order_type(Model)` as a peer to `@strawberry_django.filter_type(...)`; `graphene-django` orders through `django_filters.OrderingFilter` declared on the `FilterSet`, which still needs an explicit `orderBy:` argument on the GraphQL surface.

The architecture is the filter subsystem's: Layers 1–4 of the lazy-resolution pipeline port with `OrderSet` substituted for `FilterSet` and `RelatedOrder` for `RelatedFilter`; Layer 5 reuses the filter side's Strawberry adaptation; Layer 6 (dynamic generation) has no cookbook counterpart on the order side and is not part of the surface per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface). [`DjangoConnectionField`][glossary-djangoconnectionfield] and [`DjangoListField`][glossary-djangolistfield] build their `orderBy:` arguments from the same factory output.

`django-graphene-filters` (the working reference per [`START.md`][start]) ships `AdvancedOrderSet`, `RelatedOrder`, `OrderArgumentsFactory`, `OrderDirection`, and `get_flat_orders` as a complete ordering surface. The cookbook's `OrderDirection` is replaced by strawberry-django's six-member `Ordering` enum per [Decision 5](#decision-5--ordering-enum-and-argument-shape), because consumers need `NULLS_FIRST` / `NULLS_LAST` positioning more than `DISTINCT ON` partitioning (the cookbook's `ASC_DISTINCT` / `DESC_DISTINCT` modifiers are not ported per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface)).

## Current state

- [`django_strawberry_framework/orders/`][orders]: all five files, with the mechanics shared with the filter family single-sited in [`utils/inputs.py`][utils-inputs] and [`sets_mixins.py`][sets-mixins] (see [Decision 2](#decision-2--subpackage-layout-and-public-export-surface)).
- [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] holds `"aggregate_class"`, `"fields_class"`, `"search_fields"`; `"orderset_class"` is in `ALLOWED_META_KEYS`.
- [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer] phase 2.5 runs `apply_interfaces` / `install_relay_node_resolvers`, then `_bind_filtersets()`, then `_bind_ordersets()`.
- [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] wires `Meta.orderset_class` (beside `Meta.filterset_class`) onto its library types, including `Meta.interfaces = (relay.Node,)` on `GenreType` and [`Meta.optimizer_hints`][glossary-metaoptimizer-hints] on `LoanType`; it is the host for the live HTTP order coverage per [Decision 13](#decision-13--live-http-coverage-strategy).
- Upstream cookbook: [`~/projects/django-graphene-filters/django_graphene_filters/`][upstream-cookbook] — [`django_graphene_filters/orders.py::BaseRelatedOrder`][upstream-cookbook-orders] / [`orders.py::RelatedOrder`][upstream-cookbook-orders] (Layer 1); [`django_graphene_filters/mixins.py::LazyRelatedClassMixin`][upstream-cookbook-mixins] (Layer 2, ported at [`django_strawberry_framework/sets_mixins.py::LazyRelatedClassMixin`][sets-mixins]); [`django_graphene_filters/orderset.py::OrderSetMetaclass`][upstream-cookbook-orderset] (Layer 3); [`django_graphene_filters/orderset.py::AdvancedOrderSet`][upstream-cookbook-orderset] with `get_fields` / `get_flat_orders` (Layer 4); [`django_graphene_filters/order_arguments_factory.py::OrderArgumentsFactory`][upstream-cookbook-order-arguments-factory] (Layer 5).
- Upstream `strawberry-graphql-django`: [`~/projects/strawberry-django-main/strawberry_django/ordering.py`][upstream-strawberry-ordering] — the decorator-driven implementation, providing the [`Ordering` enum][upstream-strawberry-ordering], the [`OrderSequence`][upstream-strawberry-ordering] tie-breaker descriptor, the [`process_order`][upstream-strawberry-ordering] / [`process_ordering`][upstream-strawberry-ordering] / [`apply_ordering`][upstream-strawberry-ordering] runtime pipeline, and the [`ORDER_ARG = "order"`][upstream-strawberry-ordering] / [`ORDERING_ARG = "ordering"`][upstream-strawberry-ordering] constants. The package borrows the `Ordering` enum shape per [Decision 5](#decision-5--ordering-enum-and-argument-shape) and otherwise follows the cookbook's `AdvancedOrderSet` runtime shape.
- Upstream `graphene-django`: [`~/projects/django-graphene-filters/.venv/lib/python*/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField`][upstream-graphene-filter-fields] #"order_by=None" — the connection field's `order_by` argument composes through `django_filters.OrderingFilter` declared on the `FilterSet`. **`graphene-django` has no separate ordering primitive**; `graphene-django` parity is met by the filter subsystem, and the package's `OrderSet` is the strawberry-side counterpart.

## Goals

1. Ship `OrderSet` + `RelatedOrder` + per-field `check_*_permission` gates + cross-relation traversal with cycle-safe lazy resolution, mirroring the Filtering subsystem's architecture with the class substitution.
2. Keep [`Meta.orderset_class`][glossary-metaorderset_class] out of `DEFERRED_META_KEYS` only because the ordering subsystem applies the configured class end-to-end — same gate as [`Meta.interfaces`][glossary-metainterfaces] and [`Meta.filterset_class`][glossary-metafilterset_class].
3. Compose cleanly with the Filtering subsystem at the resolver layer (filter narrows the rows, order arranges them) and with the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — an `.order_by(...)` clause is just another queryset method call before the optimizer walks the selection tree.
4. Reuse the per-module input-class namespace lifecycle of [`django_strawberry_framework.filters.inputs`][filters-inputs] (separate `django_strawberry_framework.orders.inputs` module globals; `materialize_input_class` / `clear_order_input_namespace` / `_materialized_names` ledger; `registry.clear()` co-clears both namespaces).
5. Expose enough introspection (`OrderSet.get_fields()`, `OrderArgumentsFactory(cls).arguments`) for a maintainer to ask "what ordering surface does this type support?" from the REPL in one call.
6. Earn package coverage through live fakeshop HTTP flows per [Decision 13](#decision-13--live-http-coverage-strategy).

## Non-goals

- **Aggregation / fieldsets / permissions cascade.** Each is its own card.
- **`DISTINCT ON` partitioning** (the cookbook's `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT` modifiers and [`AdvancedOrderSet.apply_distinct`][upstream-cookbook-orderset] Window-function fallback). Not ported per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface) — the to-many fan-out DISTINCT ON addressed is prevented by row-preserving aggregate ordering instead.
- **Layer 6 (memoized dynamic `OrderSet` generation).** The cookbook ships no `orderset_factories.py` and no `_dynamic_orderset_cache`, and the package ports no dynamic-factory mechanism on either side. Every consumer, [`DjangoConnectionField`][glossary-djangoconnectionfield] included, declares an explicit `orderset_class` per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface).
- **`OrderSequence` tie-breaker descriptor** (per [`~/projects/strawberry-django-main/strawberry_django/ordering.py::OrderSequence`][upstream-strawberry-ordering]). The list-shaped `orderBy:` argument's element order IS the tie-breaker mechanism (earlier list entries dominate later ones).
- **Replacing the optimizer's queryset-diffing contract.** Orders land as `.order_by(...)` calls before the optimizer walks the selection tree.
- **Auto-generation of `OrderSet` from `Meta.fields` without declaring an explicit class.** A standing non-goal per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface): no package path generates an `OrderSet` from a field's `Meta`-shaped kwargs.

## Borrowing posture

The architectural answer is the Filtering subsystem's ([`DONE-027-0.0.8`][kanban] / [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027]), preserved by class substitution.

### From `django-graphene-filters` — borrow heavily (the cookbook is the working reference)

Local source path: [`~/projects/django-graphene-filters/django_graphene_filters/`][upstream-cookbook]. The goal is to recreate "what the package enables for the schema author," not to port Graphene internals:

- [`django_graphene_filters/orders.py::BaseRelatedOrder`][upstream-cookbook-orders] → `django_strawberry_framework.orders.base::RelatedOrder` (Layer 1; mirrors the filter side's `BaseRelatedFilter` → `RelatedFilter` port).
- [`django_graphene_filters/mixins.py::LazyRelatedClassMixin`][upstream-cookbook-mixins] → **shared** across the set families at [`django_strawberry_framework/sets_mixins.py::LazyRelatedClassMixin`][sets-mixins] (Layer 2), alongside [`ClassBasedTypeNameMixin`][sets-mixins]; both families sibling-import from this neutral home, and per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface) nothing is duplicated in `orders/base.py`.
- [`django_graphene_filters/orderset.py::OrderSetMetaclass`][upstream-cookbook-orderset] → `django_strawberry_framework.orders.sets::OrderSetMetaclass` (Layer 3; leaner than `FilterSetMetaclass` because there is no operator-bag / lookup-set discovery).
- [`django_graphene_filters/orderset.py::AdvancedOrderSet`][upstream-cookbook-orderset] → `django_strawberry_framework.orders.sets::OrderSet`, with `get_fields` doing the Layer-4 expansion under the `_expanded_fields` cache / `_is_expanding_fields` guard slots (the filter side's `_expanded_filters` / `_is_expanding_filters`, with the field naming swapped).
- [`django_graphene_filters/orderset.py::AdvancedOrderSet.check_permissions`][upstream-cookbook-orderset] → ported as the **classmethod** permission pipeline `OrderSet._run_permission_checks`, inherited from [`django_strawberry_framework/sets_mixins.py::ActiveInputPermissionMixin`][sets-mixins] and configured by a class-level `ActiveInputPermissionAttrs`, with **active-input-only scope**: the per-field `check_<field>_permission(request)` gate runs only when the consumer's input names the field, NOT for every declared field. The cookbook recurses into child ordersets through `related_orders`; the package preserves that recursion under the same active-input-only narrowing the filter side ships. No instance-method `check_permissions` is shipped on `OrderSet` — the classmethod is the whole surface, so there is one source of truth for the gate walk rather than a bound-method alias over it.
- [`django_graphene_filters/orderset.py::AdvancedOrderSet.get_flat_orders`][upstream-cookbook-orderset] → `OrderSet.get_flat_orders`. The recursive walk of nested `RelatedOrder` input lives in `orders/inputs.py::normalize_input_value`, which already produces flat `(field_path, Ordering | None)` pairs with ORM paths (`"shelf__code"`); `get_flat_orders` re-applies an optional prefix per pair. Instead of the cookbook's `-name` string prefix, each direction compiles through `Ordering.resolve` into an `F(field).asc(nulls_first=...)` / `F(field).desc(nulls_last=...)` expression, so NULLS positioning is honored.
- [`django_graphene_filters/order_arguments_factory.py::OrderArgumentsFactory`][upstream-cookbook-order-arguments-factory] → the BFS that builds every reachable `strawberry.input` type (Layer 5), single-sited with the filter side's `FilterArgumentsFactory` on the shared base.

What the cookbook ships that is NOT borrowed:

- [`django_graphene_filters/order_arguments_factory.py::OrderDirection`][upstream-cookbook-order-arguments-factory] (the four-member `ASC` / `DESC` / `ASC_DISTINCT` / `DESC_DISTINCT` graphene enum) — replaced by the six-member `Ordering` enum per [Decision 5](#decision-5--ordering-enum-and-argument-shape).
- [`django_graphene_filters/orderset.py::AdvancedOrderSet.apply_distinct`][upstream-cookbook-orderset] / [`_apply_distinct_postgres`][upstream-cookbook-orderset] / [`_apply_distinct_emulated`][upstream-cookbook-orderset] (the Window-function fallback for DISTINCT ON on non-PostgreSQL backends). Not ported per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface).

### From `strawberry-graphql-django` — borrow the `Ordering` enum shape (and the runtime-pipeline pattern)

Local source path: [`~/projects/strawberry-django-main/strawberry_django/ordering.py`][upstream-strawberry-ordering]. The runtime layer is conceptually parallel ([`process_order`][upstream-strawberry-ordering] compiles input values into queryset arguments); the declaration surface diverges per the package's DRF-shaped positioning:

- [`strawberry_django/ordering.py::Ordering`][upstream-strawberry-ordering] — the public direction enum: `ASC` / `DESC` / `ASC_NULLS_FIRST` / `ASC_NULLS_LAST` / `DESC_NULLS_FIRST` / `DESC_NULLS_LAST`. Borrowed verbatim per [Decision 5](#decision-5--ordering-enum-and-argument-shape).
- [`strawberry_django/ordering.py::OrderSequence`][upstream-strawberry-ordering] — **NOT borrowed**; the list-shaped `orderBy: [<T>OrderInput!]` argument's element order IS the tie-breaker mechanism.
- [`strawberry_django/ordering.py::process_order`][upstream-strawberry-ordering] / [`apply_ordering`][upstream-strawberry-ordering] — the runtime side; `OrderSet.apply_sync(input_value, queryset, info)` / `apply_async(...)` is the equivalent consumer-facing entry point.
- [`strawberry_django/ordering.py::ORDER_ARG`][upstream-strawberry-ordering] (`= "order"`) and [`strawberry_django/ordering.py::ORDERING_ARG`][upstream-strawberry-ordering] (`= "ordering"`) — **NOT borrowed as a pair**; the package ships a single list-shaped `orderBy: [<T>OrderInput!]` argument per [Decision 5](#decision-5--ordering-enum-and-argument-shape), and **no argument-name constant at all** — Strawberry derives the GraphQL `orderBy:` argument from the resolver's Python `order_by` parameter by auto-camel-case, so a constant would have no reader.
- [`strawberry_django/ordering.py::StrawberryDjangoFieldOrdering`][upstream-strawberry-ordering] — **NOT borrowed**; the package's `Meta`-driven shape forbids subclassing Strawberry field classes for consumer-facing declarations; the equivalent is the [Decision 11](#decision-11--order_input_typeorderset-consumer-helper) helper on a plain `@strawberry.field` resolver.
- [`strawberry_django/ordering.py::order_type`][upstream-strawberry-ordering] (`@strawberry_django.order_type(Model)`) — **NOT borrowed** (the `Meta`-driven shape per [`START.md`][start] "Style Rio cares about" forbids decorator-on-order-type for consumer-facing classes).
- [`strawberry_django/ordering.py::order`][upstream-strawberry-ordering] — the legacy decorator alias marked deprecated in favor of `order_type`; **NOT borrowed**.

### From `graphene-django` — no separate ordering primitive to borrow

`graphene-django` has no `OrderSet` equivalent — ordering is handled by `django_filters.OrderingFilter` declared on the `FilterSet`, which the filter subsystem's `BaseFilterSet` parent already covers. The package's `OrderSet` is new surface for `graphene-django` consumers: `RelatedOrder` traversal + per-field permission gates + NULLS positioning, declared in the same DRF shape as the filter side. The cookbook's [`AdvancedOrderSet`][upstream-cookbook-orderset] is the closest precedent.

### Explicitly do not borrow

- **Graphene's `lambda: target_input_type` cycle-safe forward references** (the `lambda tn=target_name: self.input_object_types[tn]` form in [`django_graphene_filters/order_arguments_factory.py::OrderArgumentsFactory._build_class_type`][upstream-cookbook-order-arguments-factory]). Replaced by `Annotated["{TargetOrderSet}InputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]` at Layer 5.
- **`@strawberry_django.order_type(Model, ordering=Ordering)` decorator surface.** Forbidden for consumer-facing classes by the `Meta`-driven shape.
- **The cookbook's `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT`.** Direction modifiers conflating ordering with DISTINCT ON partitioning; rejected per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface), which ships no `Meta.distinct` key and no `distinct_on:` argument.

## User-facing API

The consumer surface is re-exported from `django_strawberry_framework.orders`: `OrderSet`, `RelatedOrder`, `Ordering` (the six-member direction enum), and the resolver-annotation helper in two spellings, `OrderInput` and `order_input_type`. [`Meta.orderset_class`][glossary-metaorderset_class] is the wiring on the existing [`DjangoType`][glossary-djangotype] surface; the helper lets a normal `@strawberry.field` resolver accept an `orderBy:` argument that resolves to the generated input class at schema-build time.

**Resolver-facing API split (mirrors the filter side).** Consumers call `OrderSet.apply_sync(...)` from sync resolvers and `await OrderSet.apply_async(...)` from async resolvers per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer).

### Default usage — declaring an `OrderSet`

```python
from django_strawberry_framework.orders import OrderSet, RelatedOrder

from . import models


class GalaxyOrder(OrderSet):
    # Reverse FK — referenced lazily by string so Galaxy and CelestialBody
    # ordersets can live in the same file without an import cycle.
    celestial_bodies = RelatedOrder("CelestialBodyOrder", field_name="celestial_bodies")

    class Meta:
        model = models.Galaxy
        fields = "__all__"

    def check_name_permission(self, request):
        """Only staff users may order by Galaxy.name."""
        from graphql import GraphQLError
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to order by Galaxy name.")


class CelestialBodyOrder(OrderSet):
    galaxy = RelatedOrder(GalaxyOrder, field_name="galaxy")

    class Meta:
        model = models.CelestialBody
        # Explicitly list only "name" and "body_type" — "description" is intentionally
        # excluded so consumers can't `ORDER BY description` (large TEXT column).
        fields = ["name", "body_type"]
```

`OrderSet` subclasses no third-party class (the filter subsystem subclasses `django_filters.filterset.BaseFilterSet` for its form-cleaning machinery; the cookbook's `AdvancedOrderSet` has no `django-filter` inheritance, and the package's `OrderSet` follows that shape — its bases are the shared set-family mixins). Consumers familiar with `django-filter`'s `OrderingFilter` will recognize the Meta-class declaration; consumers familiar with `strawberry-graphql-django`'s `@order_type(Model)` will recognize the `Ordering` enum on the GraphQL surface.

### Wiring into a `DjangoType`

```python
from django_strawberry_framework import DjangoType

from . import models, orders


class GalaxyType(DjangoType):
    class Meta:
        model = models.Galaxy
        fields = "__all__"
        orderset_class = orders.GalaxyOrder
```

`Meta.orderset_class` is the only wiring required at the `DjangoType` site. The finalizer-phase-2.5 binding (per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering)) takes care of owner binding, lazy-related-order resolution, and input-class materialization as module globals of [`django_strawberry_framework.orders.inputs`][orders-inputs].

### Exposing the `orderBy:` argument on a resolver

```python
import strawberry

from django_strawberry_framework.orders import OrderInput

from . import models, orders


@strawberry.type
class Query:
    @strawberry.field
    def all_galaxies(
        self,
        info: strawberry.Info,
        order_by: list[OrderInput[orders.GalaxyOrder]] | None = None,
    ) -> list["GalaxyType"]:
        queryset = GalaxyType.get_queryset(models.Galaxy.objects.all(), info)
        if order_by is not None:
            queryset = orders.GalaxyOrder.apply_sync(order_by, queryset, info)
        return queryset
```

Strawberry's auto-camel-case converts the Python `order_by` parameter into the GraphQL `orderBy:` argument; consumers write `{ allGalaxies(orderBy: [{ name: ASC }, { celestialBodies: { bodyType: DESC } }]) { id } }`. The resolver pattern is **`get_queryset` → optional `Filter.apply_sync` → optional `Order.apply_sync`** — the same shape `DjangoConnectionField` composes internally.

**Note on `noqa: A002`.** The Python parameter name `order_by` does NOT shadow a builtin, so it needs no `# noqa: A002`; the filter side's `filter` parameter does shadow Python's `filter`, hence the suppression on the `filter:` parameter in the [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] root resolvers. A future `input:` resolver argument would shadow Python's `input` builtin and need the same suppression.

### Composing with the Filtering subsystem

```python
@strawberry.field
def all_library_books(
    self,
    info: strawberry.Info,
    filter: FilterInput[filters.BookFilter] | None = None,  # noqa: A002  (filter shadows builtin)
    order_by: list[OrderInput[orders.BookOrder]] | None = None,
) -> list["BookType"]:
    queryset = BookType.get_queryset(models.Book.objects.all(), info)
    if filter is not None:
        queryset = filters.BookFilter.apply_sync(filter, queryset, info)
    if order_by is not None:
        queryset = orders.BookOrder.apply_sync(order_by, queryset, info)
    return queryset
```

The ordering applies AFTER the filter (filter narrows the rows, order arranges them). Either argument is optional; both can be present.

### Per-field permission gates

```python
class GalaxyOrder(OrderSet):
    class Meta:
        model = models.Galaxy
        fields = "__all__"

    def check_name_permission(self, request):
        """Only staff users may order by Galaxy.name. Fires only when the
        consumer's input names the `name` field (active-input-only scope,
        same discipline the filter subsystem ships)."""
        from graphql import GraphQLError
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError(
                "You must be a staff user to order by Galaxy name.",
                extensions={"code": "ORDER_PERMISSION_DENIED"},
            )
```

The denial gate raises `GraphQLError`; the consumer sees a structured response error with the named `extensions.code`. The gate does NOT fire when the consumer's `orderBy:` input omits the `name` field (active-input-only — permissions gate USE of the order field, not its declaration).

**The hook must be a plain `def`.** An `async def check_<field>_permission` is **rejected**, not awaited: [`django_strawberry_framework/utils/permissions.py::invoke_permission_method`][utils-permissions] runs the gate's return through [`django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`][utils-querysets] and raises `SyncMisuseError`. The pipeline is synchronous on both surfaces (on the async surface it runs inside one `sync_to_async` worker), so an un-awaited coroutine would be a truthy value whose `raise` never executes — an intended denial would silently become an authorization **bypass**.

### Multi-field priority ordering

```graphql
{
  allLibraryBooks(
    orderBy: [
      {
        shelf: {
          code: ASC
        }
      }
      {
        title: DESC
      }
    ]
  ) {
    id
    title
    shelf {
      code
    }
  }
}
```

The list-shaped argument's element order IS the tie-breaker mechanism — earlier list entries dominate later ones. The example produces `ORDER BY library_shelf.code ASC, library_book.title DESC` (Django's default `<app_label>_<model_name>` table names for the fakeshop `library` app) via `Ordering.resolve("title")` returning `F('title').desc(nulls_first=None, nulls_last=None)`. The contract illustrated is the list-element-order tie-breaker, not the table-name literals. (`Book.title` is non-null, so its NULLS variants are no-ops; `Book.subtitle` is nullable — see the `subtitle: DESC_NULLS_LAST` query in Decision 5.)

### Error shapes

- Invalid `Meta.fields` entry (a field or relation path that does not resolve on `Meta.model`): [`ConfigurationError`][glossary-configurationerror] (`"OrderSet <qualname>.Meta.fields contains invalid order path '<path>' for model <Model>: <reason>"`), every entry pre-validated through [`django_strawberry_framework/utils/relations.py::classify_path`][utils-relations]. It is raised when `get_fields()` first expands — finalize phase-2.5 subpass 2 — not at type creation: [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6) Layer 3 is explicit that the metaclass does not expand. A non-string entry, or `"__all__"` without `Meta.model`, raises at the same point.
- A resolved order path that does not resolve on the queryset's model at apply time: [`ConfigurationError`][glossary-configurationerror] (`"OrderSet <qualname> received invalid order path '<path>' for model <Model>: <reason>"`).
- Two `RelatedOrder`s on one `OrderSet` naming the same relation: [`ConfigurationError`][glossary-configurationerror] (`"<owner>: RelatedOrders '<attr>' and '<attr>' both declare the relation '<path>'. ..."`) at class creation, an inherited declaration included.
- A `RelatedOrder` whose `field_name` continues another branch's relation into a path that branch's target `OrderSet` reaches: [`ConfigurationError`][glossary-configurationerror] (`"<owner>: RelatedOrder '<attr>' declares the relation '<path>', which continues the relation '<path>' of '<attr>' into '<path>', a path the target <Target> of '<attr>' reaches. ..."`) when `OrderSet.get_fields` builds the expansion.
- Unresolved `RelatedOrder("...")` target: [`ConfigurationError`][glossary-configurationerror] (`"Cannot finalize Django types: orderset <qualified name> references an unresolved related-order target. <ImportError text>"`) at finalize subpass 2, with the `ImportError` from the shared `LazyRelatedClassMixin.resolve_lazy_class` on `__cause__`. A target that resolves to something other than an `OrderSet` (a `FilterSet`, a plain class) raises [`ConfigurationError`][glossary-configurationerror] from `RelatedOrder._validate_target` at the same read.
- `Meta.orderset_class = NotAnOrderSet`: [`ConfigurationError`][glossary-configurationerror] (`"<Model>.Meta.orderset_class must be an OrderSet subclass; got <value>"`) at type creation.
- An orderset wired onto a `DjangoType` whose model is neither its `Meta.model` nor derived from it: [`ConfigurationError`][glossary-configurationerror] at finalize subpass 1 naming the owner type, owner model, orderset class, and orderset model.
- One orderset wired onto two `DjangoType`s whose models are different tables (a multi-table-inheritance parent and child; not one model or its proxies): [`ConfigurationError`][glossary-configurationerror] at finalize subpass 1 (`"OrderSet <qualname> cannot bind to multiple owners over different tables: <Owner> (model <Model>) and <Owner> (model <Model>). ... Declare separate OrderSet subclasses per owner."`) naming both owners and their models, per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering) (b). The filter side raises the same message under `FilterSet`.
- One orderset wired onto two `DjangoType`s when either overrides `get_queryset`: [`ConfigurationError`][glossary-configurationerror] at finalize subpass 1 (`"OrderSet <qualname> cannot bind to multiple owners when either scopes get_queryset visibility: ... Declare separate OrderSet subclasses per owner."`) naming both owners, per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering) (b).
- `check_<field>_permission(request)` denial inside an active branch: the consumer's `GraphQLError` (e.g. `extensions={"code": "ORDER_PERMISSION_DENIED"}`) propagating to the GraphQL response.
- `async def check_<field>_permission` declared instead of `def`: `SyncMisuseError`, raised by [`reject_async_in_sync_context`][utils-querysets] rather than the coroutine being awaited or passed through — see [Per-field permission gates](#per-field-permission-gates).
- Orphan `OrderSet` referenced via `OrderInput[StandaloneOrder]` / `order_input_type(StandaloneOrder)` but never wired via `Meta.orderset_class`: [`ConfigurationError`][glossary-configurationerror] at finalize naming the orphan.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file carries the canonical structured name **`spec-028-orders-0_0_8.md`** (this document). It lives in [`docs/SPECS/`][spec-028] with its `-terms.csv` and `-rationale.md` companions under `docs/SPECS/appx/`, the archive location the [`docs/SPECS/NEXT.md`][next] Step-8 pass moves a completed spec to.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 1][rationale-d1].

### Decision 2 — Subpackage layout and public export surface

The order subsystem is a subpackage at **[`django_strawberry_framework/orders/`][orders]** (NOT a flat single-file module). Five files mirror the Filtering subsystem layout:

- `__init__.py` — the entry-point surface in three tiers, mirroring the filter twin one-for-one:
  - **Public** (listed in `__all__`): `OrderSet`, `RelatedOrder`, `Ordering`, and the consumer helper in both spellings, `OrderInput` and `order_input_type` (per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper)).
  - **Advanced, also listed in `__all__`**: `OrderSetMetaclass`, because the filter twin keeps `FilterSetMetaclass` in *its* `__all__`.
  - **Advanced, NOT re-exported from this entry point**: `OrderArgumentsFactory` is reached via `django_strawberry_framework.orders.factories`, exactly as the filter side keeps `FilterArgumentsFactory` out of `filters/__init__.py`. (`INPUTS_MODULE_PATH` and `_input_type_name_for` are imported at module scope for internal callers but excluded from `__all__`.)
  - The module also hosts the **orphan-tracking ledger** `_helper_referenced_ordersets: set[type[OrderSet]]` (parallel to [`django_strawberry_framework/filters/__init__.py::_helper_referenced_filtersets`][filters-init]), **co-located with its only writer** — the helper defined in the same module. The two order ledgers clear through **two separate `register_subsystem_clear` rows** — owner `orders.helper_references` for this one, owner `orders.input_namespace` (`before_bind=True`) for `inputs._materialized_names` — per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle); they track unrelated lifecycle state (consumer resolver-annotation references vs finalizer-side class registrations), so each is owned and reset by the module that writes it.
- `base.py` — `RelatedOrder` (the cookbook's `BaseRelatedOrder` port). Its direct base is [`sets_mixins.py::RelatedSetTargetMixin`][sets-mixins] — a [`LazyRelatedClassMixin`][sets-mixins] subclass that owns the set-family target plumbing (`_bind_owner` / `_resolved_target` / `_set_target`) — reached by sibling import from the neutral [`sets_mixins.py`][sets-mixins] module; neither the mixin nor the plumbing is duplicated.
- `sets.py` — `OrderSetMetaclass`, `OrderSet` (with `Meta.model`, `Meta.fields`, the `_owner_definition: DjangoTypeDefinition | None` slot bound at finalizer phase 2.5; the resolver-facing classmethod **pair** `apply_sync(input_value, queryset, info) -> QuerySet` / `async def apply_async(input_value, queryset, info) -> QuerySet` per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer); `get_fields`, `get_flat_orders`, and the inherited classmethod permission pipeline `_run_permission_checks` with active-input-only scope — inherited from [`sets_mixins.py::ActiveInputPermissionMixin`][sets-mixins], configured through a class-level `ActiveInputPermissionAttrs`, with no instance-method `check_permissions`). **No `apply(...)` dispatcher is shipped** — the filter side's `apply(...)` exists to rewrap the sync-misuse error raised when a `RelatedFilter` target declares an `async def get_queryset`; the order side's `apply_sync` raises that `SyncMisuseError` (a `RuntimeError` whose message points at `apply_async`) itself when a related term's target type has an async-only `get_queryset` ([Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer) step 4), so there is no second spelling for a dispatcher to translate.
- `factories.py` — `OrderArgumentsFactory` (Layer 5 BFS, deriving input field types from the resolved fields on `orderset_cls.get_fields()`).
- `inputs.py` — the `Ordering` enum (per [Decision 5](#decision-5--ordering-enum-and-argument-shape)); the per-module input-class namespace; `INPUTS_MODULE_PATH: str = "django_strawberry_framework.orders.inputs"` (used in every `strawberry.lazy(INPUTS_MODULE_PATH)` call site and by `materialize_input_class` — mirrors [`django_strawberry_framework/filters/inputs.py::INPUTS_MODULE_PATH`][filters-inputs]); `_input_type_name_for(orderset_class) -> str` returning `f"{orderset_class.__name__}InputType"` (mirrors [`django_strawberry_framework/filters/inputs.py::_input_type_name_for`][filters-inputs], so the `<Name>InputType` formula lives in one place); `build_input_class`, `_build_input_fields`, `convert_order_field_to_input_annotation(model_field, owner_definition)`, `normalize_input_value(orderset_cls, input_value)`, `materialize_input_class`, `clear_order_input_namespace`, `_materialized_names`.

  **Where the mechanics live.** Every name above resolves from `django_strawberry_framework.orders.inputs`, which is the surface contract, but the machinery is single-sited with the filter twin in [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: `FieldSpec`, `build_input_class`, `_input_type_name_for`, and `_iter_orderset_subclasses` are one-line aliases of `::GeneratedInputFieldSpec`, `::build_strawberry_input_class`, `::set_input_type_name`, and `::iter_set_subclasses`, and `materialize_input_class` / `clear_order_input_namespace` are thin family wrappers over the materializer and heavy clear that `::make_set_input_namespace` builds. The order-side names are the addressable surface — [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle)'s lifecycle contract, `registry.clear()`, and the test suite all reach the subsystem through them — while one implementation serves both set families.

Public re-export is opted in by the subpackage's `__init__.py`, NOT by the top-level package: consumers `from django_strawberry_framework.orders import OrderSet, RelatedOrder, Ordering, OrderInput` (the import path [`GOAL.md`][goal]'s astronomy showcase uses). The top-level package's `__all__` does not carry the order symbols.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 2][rationale-d2].

### Decision 3 — Five-layer port plus a deferred Layer 6

Layers 1–4 of the lazy-resolution pipeline port from `django-graphene-filters` library-agnostic; Layer 5 reuses the filter subsystem's Strawberry adaptation. Layer 6 (dynamic `OrderSet` generation) has no cookbook counterpart and is not part of the ordering surface per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface).

**Layer 1 — Lazy class references in `RelatedOrder`** — port of [`django_graphene_filters/orders.py::BaseRelatedOrder`][upstream-cookbook-orders]. `RelatedOrder` accepts the target as a class, an absolute import path string (`"apps.library.orders_genre.GenreOrder"`), an unqualified name (`"GenreOrder"`), a zero-arg factory, or `None` (a placeholder skipped at input emission). `_orderset` stores it unresolved; the `.orderset` property triggers resolution and rejects a resolved non-`OrderSet` target.

**Layer 2 — Module-fallback resolution** — reused from the neutral shared [`django_strawberry_framework/sets_mixins.py`][sets-mixins]. `RelatedOrder` derives from `::RelatedSetTargetMixin`, itself a `::LazyRelatedClassMixin` subclass. Both families sibling-import from this module rather than from each other. Two-step resolution: try as absolute path via `django.utils.module_loading.import_string`; on `ImportError`, retry with the `bound_class.__module__` prefix. Handles circular references within one module.

**Layer 3 — Metaclass discovery, deferred expansion** — port of the [`django_graphene_filters/orderset.py::OrderSetMetaclass`][upstream-cookbook-orderset] pattern. The metaclass collects `RelatedOrder` declarations into `cls.related_orders` (plural, like the filter side's `cls.related_filters`) through the shared [`sets_mixins.py::collect_related_declarations`][sets-mixins] walk, which copies each base's declarations and lets the current class override them, and binds every collected declaration to the new class (`bind_orderset` is the public spelling of that bind) so the module-fallback resolver knows the owning module. A set declares each relation once: two `RelatedOrder`s naming one relation (its `field_name`, or its attribute name when it declares none) raise [`ConfigurationError`][glossary-configurationerror] at class creation, since an order term and a flat-path permission gate carry only the ORM path and [`utils/permissions.py::walk_declared_relation_path`][utils-permissions] reads it as the one declaration on the relation ([Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer) step 4 reads the hop's target type from it). A longer declaration continuing a branch's relation (`shelf__branch` beside `shelf`) stays allowed unless the branch's target `OrderSet` reaches the continuation, by a `Meta.fields` path of its own or through its own branches: a nested term under the branch normalizes to a path the walk would read through the longer declaration, so [`sets_mixins.py::reject_captured_branches`][sets-mixins] raises [`ConfigurationError`][glossary-configurationerror] when `get_fields()` expands the set. It **does not** expand; expansion is deferred to `get_fields()`.

**Layer 4 — Expansion + cache** — port of [`django_graphene_filters/orderset.py::AdvancedOrderSet.get_fields`][upstream-cookbook-orderset]. `get_fields()` merges the `Meta.fields` expansion with `related_orders` and stores `RelatedOrder` instances unresolved, except the targets [`sets_mixins.py::reject_captured_branches`][sets-mixins] reads for a pair of overlapping declarations; that check reads a target's `Meta.fields` expansion and its declarations, never its `get_fields()`, so expansion never re-enters another orderset's `get_fields()` and cannot cycle. The `_expanded_fields` cache slot and `_is_expanding_fields` guard are named by a class-level `SetLifecycleAttrs` on `OrderSet` and driven by the shared [`sets_mixins.py::expanded_once`][sets-mixins] / [`::should_cache_expansion`][sets-mixins] helpers — one implementation of the guard-and-cache discipline for both families. Two-condition cache write: `related_orders` is on the class itself AND no string `_orderset` remains on any related order.

**Layer 5 — BFS schema build with module-global materialization (Strawberry-adapted)** — the BFS from [`django_graphene_filters/order_arguments_factory.py::OrderArgumentsFactory`][upstream-cookbook-order-arguments-factory], single-sited with the filter twin on [`django_strawberry_framework/utils/inputs.py::GeneratedInputArgumentsFactory`][utils-inputs]. `OrderArgumentsFactory` supplies `_build_input_triples` plus the class-level `input_object_types` and `_type_orderset_registry` ledgers [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle) names; `arguments` is the shared base's property. The shared base walks a FIFO queue (deterministic breadth-first, aligned with the filter side) where the cookbook's order factory used LIFO; both reach the same class set for a finite graph. Specifically:

- Every generated order input class is a **real module global** of [`django_strawberry_framework.orders.inputs`][orders-inputs].
- The Strawberry idiom is `Annotated["{TargetOrderSet}InputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]` for `RelatedOrder` fields. Leaf fields use the public `Ordering` enum directly (no forward reference).
- The `Annotated[...]` directly wraps the forward-reference string (no list wrapper — each `RelatedOrder` field is single-valued and there is no `and_` / `or_` operator bag for ordering).
- The factory does NOT materialize built classes as module globals — that is the finalizer's phase-2.5 subpass-4 contract per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering), which reads `factory.input_object_types` and calls `materialize_input_class(name, input_cls)` for every built class. The factory emits the `Annotated[...]` shape and caches built classes at class level so a sibling root's factory instance sees them.

**Layer 6 — Memoized dynamic `OrderSet` generation** — **NOT PART OF THE PIPELINE** per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface). Every consumer declares an explicit `Meta.orderset_class = MyOrder`.

**`Meta.fields = "__all__"` scope** — expands to every **real-column-backed** model field: every field whose `column` attribute names an actual database column AND which is not a many-to-many manager. The cookbook's [`get_concrete_field_names`][upstream-cookbook-mixins] is `[f.name for f in model._meta.get_fields() if hasattr(f, "column")]`, and its docstring claims this "excludes reverse relations, many-to-many managers, and other virtual fields" — but a `ManyToManyField` exposes `.column = None`, so `hasattr(f, "column")` admits it, and a bare M2M leaf (`order_by("genres")`, i.e. `genres__id`) duplicates parent rows under JOIN multiplicity. The package ships the cookbook's documented intent: [`django_strawberry_framework/orders/inputs.py`][orders-inputs]'s `_get_concrete_field_names_for_order(model)` is `[f.name for f in model._meta.get_fields() if getattr(f, "column", None) is not None and not getattr(f, "many_to_many", False)]`. The `not many_to_many` clause excludes the M2M leaf; the `getattr(..., None) is not None` clause also excludes Django's **virtual** `GenericRelation` and `GenericForeignKey` descriptors, which expose `column = None` too. **Concrete shape for the fakeshop `Book` model:** `"__all__"` produces leaves for `id`, `title`, `subtitle`, `circulation_status`, AND `shelf` (the forward FK column, ordered by `shelf_id`) — but NOT `genres` / `archive_genres` (M2M) or `loans` (reverse FK, which has no `column`). For nested traversal across a forward FK (`orderBy: [{ shelf: { code: ASC } }]` instead of `orderBy: [{ shelf: ASC }]`), the consumer declares a same-name `RelatedOrder(ShelfOrder, field_name="shelf")`, which overrides the column leaf. M2M relations are orderable only through an explicit `RelatedOrder`. Package tests pin the forward-FK column's inclusion (`test_get_concrete_field_names_for_order_direct`) and the virtual-descriptor exclusion (`test_orderset_all_excludes_virtual_generic_fields`).

**Proxy / multi-table-inheritance semantics.** `"__all__"` reads `model._meta.get_fields()` of the orderset's `Meta.model`:

- **Proxy models**: a proxy carries its concrete parent's columns, so `"__all__"` yields the parent's column set.
- **Multi-table inheritance (MTI)** children: the child's field list includes the inherited parent columns (plus the parent link), so `"__all__"` yields the union. Consumers wanting only the child's own columns declare `Meta.fields` explicitly.
- **Abstract base models**: no rule targets them. Nothing rejects `OrderSet.Meta.model = <AbstractModel>`, and the expansion yields whatever `_meta.get_fields()` returns for it; consumers declare `Meta.model = <ConcreteSubclass>`. Because paths are resolved against `queryset.model` at apply time ([Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer) step 7), an orderset keyed on a base model applies correctly to a concrete descendant's queryset.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 3][rationale-d3].

### Decision 4 — Upstream-primitives parity floor

The cookbook ships **`AdvancedOrderSet`**, **`RelatedOrder`**, **`OrderArgumentsFactory`**, and **`OrderDirection`** as the public surface. strawberry-graphql-django ships **`Ordering`**, **`OrderSequence`**, **`order_type`**, and the **`process_order`** runtime pipeline:

- `strawberry_django/ordering.py::Ordering` — public `Ordering` enum: `ASC`, `DESC`, `ASC_NULLS_FIRST`, `ASC_NULLS_LAST`, `DESC_NULLS_FIRST`, `DESC_NULLS_LAST`.
- `strawberry_django/ordering.py::OrderSequence` — per-field sequence descriptor used to order ties when multiple fields participate.
- `strawberry_django/ordering.py::process_order` / `::process_ordering` / `::process_ordering_default` / `::apply_ordering` — the runtime pipeline that compiles an order-input value into queryset `order_by()` arguments and applies them.
- `strawberry_django/ordering.py::StrawberryDjangoFieldOrdering` — field-base subclass that injects the `order: <T>OrderInput` and `ordering: list[<T>OrderInput]` arguments on a Django-backed field.
- `strawberry_django/ordering.py::order_type` — the consumer-facing `@strawberry_django.order_type(Model)` decorator.
- `strawberry_django/ordering.py::order` — legacy decorator alias marked deprecated in favor of `order_type`; no parity is claimed with it.
- `strawberry_django/ordering.py::ORDER_ARG` (`= "order"`) and `strawberry_django/ordering.py::ORDERING_ARG` (`= "ordering"`) — module-level constants for the singular one-of and list GraphQL argument names.
- `~/projects/django-graphene-filters/.venv/lib/python*/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField #"order_by=None"` — the connection field's `order_by` argument composes through `django_filters.OrderingFilter` declared on the FilterSet. Graphene has no separate ordering primitive; its parity is met by the filter subsystem.

The package's parity floor:

- `OrderSet` (the cookbook's `AdvancedOrderSet`) — class-based declaration with `Meta.model`, `Meta.fields`, per-field `check_<field>_permission` gates, classmethod resolver-facing `apply_sync` / `apply_async` API.
- `RelatedOrder` (the cookbook's port + the Layer-2 lazy resolution shared with the filter subsystem) — cross-relation traversal.
- `OrderArgumentsFactory` (the cookbook's BFS factory + the Strawberry-adapted Layer 5 from [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 3) — produces the `orderBy: [<T>OrderInput!]` element type.
- `Ordering` (the strawberry-django six-member enum) — direction modifiers per [Decision 5](#decision-5--ordering-enum-and-argument-shape).
- `OrderInput[OrderSet]` / `order_input_type(OrderSet)` (the consumer helper, parallel to the filter side's) — per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper).

NOT in the parity floor:

- `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT` (the cookbook's DISTINCT ON modifiers) — not ported per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface).
- `AdvancedOrderSet.apply_distinct` / `_apply_distinct_postgres` / `_apply_distinct_emulated` (the cookbook's Window-function emulation) — not ported per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface).
- `OrderSequence` — NOT borrowed per [Decision 5](#decision-5--ordering-enum-and-argument-shape) (the list-shaped argument provides the tie-breaker positionally).
- `StrawberryDjangoFieldOrdering` — NOT borrowed (the `Meta`-driven shape forbids subclassing Strawberry field classes).
- `order_type` / `order` decorators — NOT borrowed (the `Meta`-driven shape forbids decorator-on-input-type).
- Auto-generated ordersets (Layer 6) — not a consumer surface per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface).

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 4][rationale-d4].

### Decision 5 — `Ordering` enum and argument shape

The public direction enum is `Ordering` — borrowed verbatim from [`~/projects/strawberry-django-main/strawberry_django/ordering.py::Ordering`][upstream-strawberry-ordering]:

```python
# django_strawberry_framework/orders/inputs.py
@strawberry.enum
class Ordering(enum.Enum):
    ASC = "ASC"
    DESC = "DESC"
    ASC_NULLS_FIRST = "ASC_NULLS_FIRST"
    ASC_NULLS_LAST = "ASC_NULLS_LAST"
    DESC_NULLS_FIRST = "DESC_NULLS_FIRST"
    DESC_NULLS_LAST = "DESC_NULLS_LAST"

    @property
    def is_ascending(self) -> bool:
        return self.name.startswith("ASC")

    def resolve(self, value: str) -> OrderBy:
        nulls_first = True if "NULLS_FIRST" in self.name else None
        nulls_last = True if "NULLS_LAST" in self.name else None
        if self.is_ascending:
            return F(value).asc(nulls_first=nulls_first, nulls_last=nulls_last)
        return F(value).desc(nulls_first=nulls_first, nulls_last=nulls_last)
```

`resolve` compiles a direction + a Django ORM field path into an `OrderBy` expression. NULLS positioning is passed via Django's `F(value).asc(nulls_first=...)` / `.desc(nulls_last=...)` rather than a bare string prefix, so the SQL carries it unambiguously. Django's sentinel semantics: `nulls_first=True` opts INTO "NULLS FIRST"; `None` leaves the backend default and emits no NULLS clause — so a bare `Ordering.ASC` maps to `F(value).asc(nulls_first=None, nulls_last=None)`, not "NULLS FIRST False". `is_ascending` anchors on the member-name PREFIX so every `ASC_*` variant is ascending and every `DESC_*` descending.

`is_ascending` has **two** consumers, which is why it is a property rather than a local test inside `resolve`: `resolve` uses it to pick `.asc()` over `.desc()`, and [`django_strawberry_framework/orders/sets.py::OrderSet._resolve_order_expressions`][orders-sets] uses it to pick `Min` over `Max` for the row-preserving aggregate a to-many term is ordered by per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface). A second copy of the discrimination could drift and order a to-many term by the wrong end of its child range.

**Portability note carried by the enum itself.** A bare `ASC` / `DESC` over a nullable column defers NULL placement to the backend — SQLite sorts NULLs first on `ASC`, PostgreSQL and MySQL sort them last — so the NULL partition, and therefore the page boundaries of a connection paged over a nullable column, differs across databases. Cursor stability WITHIN one backend is unaffected; consumers wanting a backend-independent NULL partition use the explicit `ASC_NULLS_FIRST` / `ASC_NULLS_LAST` / `DESC_NULLS_FIRST` / `DESC_NULLS_LAST` members.

The GraphQL argument shape is **`orderBy: [<TypeName>OrderInputType!]`** (list of non-null order-input objects). Consumers write `orderBy: [{ name: ASC }, { shelf: { code: DESC_NULLS_LAST } }]`. The list's element order IS the tie-breaker mechanism — terms are emitted in list order, so earlier entries dominate later ones.

GraphQL surface examples:

```graphql
{
  allLibraryBranches(
    orderBy: [
      {
        name: ASC
      }
    ]
  ) {
    id
  }
}

{
  allLibraryBooks(
    orderBy: [
      {
        subtitle: DESC_NULLS_LAST
      }
    ]
  ) {
    id
  }
}

{
  allLibraryBooks(
    orderBy: [
      {
        shelf: {
          code: ASC
        }
      }
      {
        title: DESC
      }
    ]
  ) {
    id
  }
}

{
  allLibraryBooks(
    orderBy: [
      {
        genres: {
          name: ASC
        }
      }
    ]
  ) {
    id
  }
}
```

Rationale companion — this Decision's justification and its four rejected alternatives: [Decision 5][rationale-d5].

### Decision 6 — Finalizer phase-2.5 binding seam + materialize-before-`Schema` ordering

The finalizer-phase-2.5 binding for `Meta.orderset_class` runs after `_bind_filtersets()` and before phase 3's `strawberry.type` decoration. The implementation is [`django_strawberry_framework/types/finalizer.py::_bind_ordersets`][finalizer]. It and `::_bind_filtersets` both delegate to one shared driver, `::_bind_sidecar_sets`, configured by a `_SidecarBindingSpec` naming the family's `Meta` key, owner-bind function, expansion function, helper ledger, factory class, materializer, and orphan-error formatter — so the subpass ORDER is single-sited and cannot drift between the two families. The driver's filter-only subpass 2.5 (the unregistered-related-target and GlobalID-strategy audits) is opted out of for orders (`post_expand_audit=None`): an order hop whose model no type registers hides nothing ([Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer) step 4), so there is no unregistered target to refuse, and ordering never consults Relay shape. The four subpasses the order side runs:

1. **Bind owners.** For each `DjangoType` whose `definition.orderset_class is not None`, `_bind_orderset_owner(orderset_class, definition)` runs the shared `_bind_set_owner_common`:

   **(a) Model compatibility (every binding).** `definition.model` must BE the orderset's `Meta.model` OR derive from it (proxy / multi-table-inheritance children carry every column the orderset's paths reference); a non-class `Meta.model` (e.g. the Django lazy-reference string, which the raw order-side `Meta` does not validate) fails the same check. Otherwise [`ConfigurationError`][glossary-configurationerror] names the owner type, owner model, orderset class, and orderset model — the same check the filter side's [`_bind_filterset_owner`][finalizer] runs. Without it, a `BookOrder` wired onto `BranchType` would build a valid-looking `Book`-field input AND then apply `Book` paths to a `Branch` queryset, surfacing as a late Django `FieldError` at query time.

   **(b) Multi-owner reuse.** Only the first binding is stored, and [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer) step 4 reads visibility from it: a hop a `RelatedOrder` declares answers for the type its target set is bound to, and a path re-entering the set's table (the same `_meta.concrete_model`) for the type the set is bound to. A second, distinct owner is therefore refused with [`ConfigurationError`][glossary-configurationerror] naming both owners when the two owners read different tables (a multi-table-inheritance parent and child, whichever declares first: the parent owner would answer re-entry into the parent table with itself, the child owner with the parent's primary type), checked first by the shared `types/finalizer.py::_check_set_owner_table_identity`; owners over one model or its proxies share the table and pass it. It is refused too when EITHER owner overrides `get_queryset` (`DjangoTypeDefinition.has_custom_get_queryset`, the filter side's check, one shared `types/finalizer.py::_check_set_owner_get_queryset_safety`); a hook two owners inherit from one base is refused too, since it runs with each owner's own `cls`. Otherwise whichever owner finalized first would decide which related rows may position a parent. The remedy is a separate `OrderSet` per owner, a subclass included: the binder reads only the class's own `_owner_definition`, never one inherited from its base, so `class AdminShelfOrder(ShelfOrder)` binds its own owner in either declaration order. An accepted second owner is then allowed only when, for every declared `RelatedOrder`, both owners' `related_target_for(field_name)` resolve to the same `DjangoTypeDefinition` and the same `graphql_type_name`. The filter side's own-PK Relay-identity check is **NOT** ported: `ORDER BY id` uses the column, not the GraphQL ID type.

   **(c) Idempotent re-bind.** Re-binding the same `(orderset_class, definition)` pair is a no-op.

   Pinned by `test_phase_2_5_rejects_orderset_wired_to_unrelated_owner_model` (a `BookOrder(Meta.model=Book)` wired onto `BranchType` raises with all four names in the message) and `tests/types/test_finalizer.py::test_orderset_multi_owner_model_mismatch_raises_on_secondary_owner`.
2. **Expand orderset fields.** Only after every owner is bound, `_expand_orderset` calls `orderset_cls.get_fields()` AND, in the same try/except scope, reads `.orderset` on every `related_orders` entry so Layer-2 lazy-class resolution fires at the subpass-2 boundary. The explicit `.orderset` read is load-bearing because `OrderSet.get_fields()` stores `RelatedOrder` instances WITHOUT resolving their lazy class refs (unlike the filter side's `FilterSet.get_filters()`, whose `_expand_related_filter` reads `f.filterset`); without it an unresolved `RelatedOrder("Name")` would only surface at subpass-4 materialize time as a bare `ImportError` from inside `_build_input_fields`. An `ImportError` is rewrapped as [`ConfigurationError`][glossary-configurationerror] with `__cause__` preserving it; any other non-`ConfigurationError` exception from `get_fields()` or the `.orderset` read rewraps as [`ConfigurationError`][glossary-configurationerror] with `repr(exc)` in the message (the shared driver's uniform finalize-time error shape). Pinned by `test_phase_2_5_unresolved_related_order_raises_at_finalize`.
3. **Orphan validation.** Compare `_helper_referenced_ordersets` (every `OrderSet` passed to `OrderInput[...]` / `order_input_type(...)`) against the `Meta.orderset_class`-wired ordersets and raise [`ConfigurationError`][glossary-configurationerror] for the orphans (message quoted under [Decision 11](#decision-11--order_input_typeorderset-consumer-helper)). **Runs BEFORE materialization** so an orphan failure leaves no partial state in `_materialized_names` / `OrderArgumentsFactory.input_object_types` (pinned by `test_phase_2_5_orphan_check_runs_before_materialization`).
4. **Materialize input classes.** Read `OrderArgumentsFactory(orderset_cls).arguments` to trigger the Layer-5 BFS, then call `materialize_input_class(name, cls)` for every class in `factory.input_object_types` so each becomes a module global of [`django_strawberry_framework.orders.inputs`][orders-inputs]. Materialization runs BEFORE `strawberry.Schema(...)` is constructed (the consumer-side ordering is pinned in [`docs/README.md`][docs-readme]'s schema setup section). A sibling root's factory sees the cached build through the factory's class-level dict.

`registry.clear()` replays every registered subsystem teardown through [`::iter_subsystem_clears()`][registry], so the model-to-`DjangoType` clear, the order-input clear, the orphan-tracking clear, AND the filter-input clear all run from one entry point without `registry.py` naming any of them (see [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle)). Calling `finalize_django_types()` twice is a no-op via the `registry.is_finalized()` guard.

Rationale companion — this Decision's justification and its four rejected alternatives: [Decision 6][rationale-d6].

### Decision 7 — `Meta.orderset_class` promotion gate

`Meta.orderset_class` is in `ALLOWED_META_KEYS` (out of [`DEFERRED_META_KEYS`][base]) because the subsystem applies it end-to-end: the class hierarchy (Slices 1 + 2) and the finalizer-phase-2.5 binding (Slice 3) exist, and `tests/types/test_base.py::test_meta_orderset_class_is_promoted_to_allowed_meta_keys` pins the promotion. Same gate as [`Meta.interfaces`][glossary-metainterfaces] and [`Meta.filterset_class`][glossary-metafilterset_class] — a deferred `Meta` key is accepted only when its subsystem applies it end-to-end.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 7][rationale-d7].

### Decision 8 — Cooperation with filtering, `get_queryset`, and the optimizer

The ordering subsystem composes with three surfaces without modification: the Filtering subsystem, the `get_queryset` visibility hook, and the `DjangoOptimizerExtension`. The composition flows through the resolver-facing classmethods `OrderSet.apply_sync(input_value, queryset, info)` and `OrderSet.apply_async(input_value, queryset, info)`; resolvers pick the variant matching their own sync/async shape.

**`GraphQLError` import path** — every `GraphQLError` raised in this Decision and in [Decision 11](#decision-11--order_input_typeorderset-consumer-helper) is `from graphql import GraphQLError` (the class Strawberry's response builder honors for the `extensions` payload), NOT `strawberry.exceptions.StrawberryGraphQLError`.

**Apply pipeline (the filter side's, simplified — no operator bag, no form validation, no related-queryset filter-scope constraint):**

1. **The consumer resolver calls `<OwnerType>.get_queryset(queryset, info)` first** on the consumer-shaped root queryset — visibility scoping happens BEFORE any order clause runs. Unlike the filter side, where this ordering is security-critical (a filter clause can see through visibility to hidden rows), here it is discipline: ordering applied after visibility scoping arranges the rows the user may see. (An `ORDER BY name` against the unscoped manager orders the universe, and the consumer sees the wrong row at the head of the list.)
2. **The consumer resolver optionally calls `<TypeName>Filter.apply_sync(filter, queryset, info)`** (or `apply_async`) to narrow the row set. A resolver without a `filter:` argument skips this.
3. **The consumer resolver then calls `OrderSet.apply_sync(input_value, queryset, info)`** (or `await OrderSet.apply_async(input_value, queryset, info)`).
4. **A related order term reads only related rows the viewer may see.** `<OwnerType>.get_queryset` is not re-applied (step 1 already scoped the parent rows), but every relation hop an order path walks is scoped by its target type, exactly as the filter side scopes a branch ([spec-027 Decision 8][spec-027-d8] step 3): a related row the target type's `get_queryset` hides orders the parent as if that row did not exist. The hops are every relation segment of the term's path, whichever spelling produced it: a nested `RelatedOrder` branch (`shelf: { topic: ASC }`), a `Meta.fields` path through relations (`"shelf__code"`), and a path a consumer `get_flat_orders` override returns. The hops are [`utils/relations.py::leading_relation_hops`][utils-relations]'s over `queryset.model` (a `pk` segment on a model keyed by a relation is that relation), and [`OrderSet._scoped_hops`][orders-sets] resolves each one's type: a hop a `RelatedOrder` declares ([`utils/permissions.py::walk_declared_relation_path`][utils-permissions]) answers for the type its target set is bound to; every other hop, the intermediate models of a declaration whose `field_name` spans several relations included, answers for [`utils/querysets.py::relation_target_type`][utils-querysets]'s type, so a path re-entering the table of the set it walks from (the same `_meta.concrete_model`: a proxy shares its concrete model's table, a multi-table-inheritance parent and child do not) reads the type that set is bound to. A target model no `DjangoType` registers is unscoped, and a target type that does not override `get_queryset` (`DjangoType.has_custom_get_queryset`) hides nothing and leaves the hop unwrapped, so a path crossing only such hops orders by its plain column. A scoped hop's visible rows are `<TargetType>.get_queryset(<target base queryset on the parent queryset's database alias>, info)`, derived once per call per target type. Each scoped hop contributes one test, [`optimizer/predicates.py::visible_row_exists`][optimizer-predicates]: a correlated `EXISTS` over those visible rows whose primary key equals the row the term's own join reaches, so it reuses that join and adds none. The term's value is [`optimizer/predicates.py::visible_value`][optimizer-predicates], one `CASE WHEN <test> THEN ... END` per scoped hop around `F(path)`, `NULL` when any hop on the chain is hidden. A to-one term orders by that value directly; a to-many term's `Min` / `Max` aggregates it, so a hidden child contributes a `NULL` the aggregate skips and a parent whose related rows are all hidden sorts like a parent with none. A hidden related row therefore sorts exactly where a missing one does: under the `NULLS` placement the direction names, or the backend default for a bare `ASC` / `DESC` (see [`Ordering`][glossary-ordering]). The parent's `check_<branch>_permission` gate (step 6) still fires for an active branch; it now authorizes ordering through the relation at all, and is no longer needed to hide related values.
5. **The apply pipeline resolves the Django request** through `_request_from_info(info)`, the shared [`utils/permissions.py::request_from_info`][utils-permissions]: `info.context.request`, a bare `HttpRequest` context, a mapping context whose `"request"` is an `HttpRequest`, or Strawberry's Channels context; any other shape raises [`ConfigurationError`][glossary-configurationerror]. Same as the filter side.
6. **The apply pipeline calls the classmethod `cls._run_permission_checks(input_value, request)`** — denial gates raise `GraphQLError(...)` before any `order_by(...)` clause touches the queryset. The classmethod is the whole gate surface: `OrderSet` inherits it, along with `_active_permission_targets` / `_iter_active_related_branches` / `_invoke_permission_method` / `_extract_branch_value` / `_request_from_info`, from [`django_strawberry_framework/sets_mixins.py::ActiveInputPermissionMixin`][sets-mixins], configured through a class-level `ActiveInputPermissionAttrs`; the order family's `_prepare_permission_input` hook builds its field specs first, because they are built lazily. The per-field `check_<field>_permission(request)` gate runs **only for fields present in the input**; an omitted field and an explicit `null` direction are both inactive.

   **The gate must be a plain `def`.** The single invocation point, [`django_strawberry_framework/utils/permissions.py::invoke_permission_method`][utils-permissions], runs the gate's return through [`django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`][utils-querysets] and raises `SyncMisuseError` for an awaitable. The pipeline is synchronous on both surfaces (the async surface runs it inside one `sync_to_async` worker), so an `async def check_<field>_permission` would return a truthy, un-awaited coroutine whose `raise` never executes — a **denial silently becoming an allow**. Every sibling authorization seam in the package applies the same guard.

   **Active-branch double-dispatch** (the shared walk [`sets_mixins.py::ActiveInputPermissionMixin._run_permission_checks`][sets-mixins] that `FilterSet` also inherits). For an active `RelatedOrder` branch such as `shelves` (input `orderBy: [{ shelves: { code: ASC } }]`), **both** gates fire:

   - **Parent's per-branch gate.** The owning orderset's `check_shelves_permission(request)` fires for the active branch: the consumer's way to refuse ordering through a relation at all (step 4 already keeps hidden related rows out of the order).
   - **Child orderset's own field gates.** The walk recurses into the child orderset with the nested input (`{ code: ASC }`); the child fires its own `check_code_permission(request)` if declared and active.

   **Dedup contract.** A shared `_fired: dict[type, set[str]]` map keyed on `(OrderSet class, method name)`, owned by [`ActiveInputPermissionMixin`][sets-mixins] and threaded into [`invoke_permission_method`][utils-permissions] as the per-class set, ensures each gate fires at most once per class across the entire input — e.g., `orderBy: [{ shelves: { code: ASC } }, { shelves: { code: DESC } }]` fires the parent's `check_shelves_permission` ONCE AND the child `ShelfOrder.check_code_permission` ONCE.

   **Naming convention.** The parent's per-branch gate name is `check_<branch>_permission` (e.g., `check_shelves_permission` for the `shelves` `RelatedOrder` field — NOT `check_shelves_code_permission`).

   **Tests pin the contract** at the layer that owns each half. The double-dispatch-plus-dedup walk is pinned once, family-neutrally, at [`tests/utils/test_permissions.py::test_run_active_input_permission_checks_double_dispatch_and_dedup`][test-utils-permissions]; the family wiring — that both set families reach the facade through the mixin — by [`tests/test_sets_mixins.py`][test-sets-mixins], including `::test_permission_facade_methods_are_single_sourced_on_the_mixin`. The order-side residue lives in [`tests/orders/test_sets.py`][test-orders]: `::test_orderset_check_permission_dedups_repeated_list_entries` and `::test_orderset_inactive_input_does_not_resolve_lazy_related_target` (an inactive branch does not even force Layer-2 resolution of its target). The live test `test_order_check_permission_denies_active_related_branch` in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] exercises an active `RelatedOrder` gate end to end.
7. **The classmethod chain applies `queryset.order_by(*expressions)`** — `apply_sync` / `apply_async` both tail into `OrderSet._apply_orderings`, which calls `_normalize_input` (the nested `RelatedOrder` walk into `(field_path, Ordering | None)` pairs; `_normalize_input` must be pure, because a `DjangoListField` re-normalizes the input to check for active terms), then `get_flat_orders`, then `_resolve_order_expressions` to build the expressions per [Decision 5](#decision-5--ordering-enum-and-argument-shape). `get_flat_orders` returns paths paired with directions — it does NOT produce `OrderBy` expressions — and `_resolve_order_expressions` is the post-pass that converts each pair, which keeps `Ordering`'s `OrderBy`-producing semantics at one call site. Three properties of that post-pass are contract:

   - **The model is the queryset's, not `Meta.model`.** `_apply_orderings` passes `model=queryset.model`. The paths execute against that queryset, so its model is the only authoritative metadata root — `Meta.model` may be absent altogether (a related-only `OrderSet` is legal), or may name a base model while a caller applies the set to a concrete descendant carrying additional relations.
   - **Every resolved path is pre-validated** through [`django_strawberry_framework/utils/relations.py::classify_path`][utils-relations], raising [`ConfigurationError`][glossary-configurationerror] naming the path and the model rather than letting a Django `FieldError` surface at execution time; a direction that is not an `Ordering` member raises the same way.
   - **A to-many term is ordered by an aggregate, not by the raw path.** A path [`::path_traverses_to_many`][utils-relations] reports as to-many is annotated `Min` (ascending) / `Max` (descending) — picked by `Ordering.is_ascending` — over step 4's value when any hop is scoped, and ordered by the alias, so the join cannot multiply the parent row. A to-one term crossing a scoped hop orders by step 4's `CASE` expression itself (`Ordering.resolve` accepts an expression as well as a path); a scalar term and a to-one term crossing no scoped hop order by `F(path)`. See [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface).
   - **A value step 4 can make `NULL` is a nullable order column.** A `Meta.cursor_field` connection accepts a related `orderBy:` path only when it can never be `NULL`, so a path crossing a scoped hop is refused by [`connection.py::_keyset_order_state`][connection] with the same `require non-nullable ordering columns` rejection a nullable column or a nullable intermediate relation gets, naming the path and the hiding type. A [`DjangoListField`][glossary-djangolistfield] certifies the visibility test as deterministic for its `offset` guard: its rows are the target type's `get_queryset`, which the guard trusts for the parent rows too. Both recognize it by its exact type, [`utils/querysets.py::VisibleRowExists`][utils-querysets], Django's `Exists` under a framework name that defines nothing of its own; the visibility boundary's seal admits that one framework type by identity beside Django's own classes ([spec-045][spec-045] Decision 2). An `OrderSet` term on a combined (`union` / `intersection` / `difference`) queryset is an expression the primary-key-set rewrite cannot carry, so a sealed surface refuses it as a lost property, scoped or not.

   A term-less input (an empty list, an empty object, omitted fields, or explicit `null` directions) returns the queryset unchanged, preserving any pre-existing order. The pipeline returns the ordered queryset to the resolver.
8. **The optimizer ([`DjangoOptimizerExtension`][glossary-djangooptimizerextension]) walks the selection tree on the ordered queryset**; [Queryset diffing][glossary-queryset-diffing] cooperates with any consumer `select_related` / `prefetch_related` work already present. The optimizer's `.only(...)` projection is **selection-tree-derived only**; Django fetches the columns required to execute the `ORDER BY` clause regardless of the `.only(...)` hint, so the user-visible behavior is correct — that cooperation is Django's. Order-aware projection augmentation is out of scope.

**Sync / async API split.** Same shape as the filter side:

- `OrderSet.apply_sync(input_value, queryset, info) -> QuerySet` — the sync-resolver entry point.
- `async def apply_async(input_value, queryset, info) -> QuerySet` (a classmethod on `OrderSet`) — the async-resolver entry point. The annotation is the value the coroutine resolves to; `await OrderSet.apply_async(...)` at the consumer site IS the awaitable. Matches the filter side's [`django_strawberry_framework/filters/sets.py::FilterSet.apply_async`][filters-sets] signature.
- **No `OrderSet.apply(...)` dispatcher.** `apply_sync` derives step 4's hop visibility through `apply_type_visibility_sync`, so a hop whose target type's `get_queryset` is async-only raises [`SyncMisuseError`][utils-querysets] (a `RuntimeError` whose message points at `apply_async`) out of `apply_sync` directly; there is no second spelling for a dispatcher to translate.

**`apply_async` permission-hook dispatch.** `OrderSet.apply_async` resolves the request via `_request_from_info(info)`, then dispatches the permission pass through `await run_in_one_sync_boundary(cls._run_permission_checks, input_value, request)` from [`django_strawberry_framework/utils/querysets.py`][utils-querysets] — so a consumer `check_<field>_permission` hook that performs a blocking ORM read runs in a worker thread and does **not** block the event loop. That helper is the package's one-boundary primitive (ONE worker per resolution, `thread_sensitive=True`), shared by every async surface that keeps a consumer-overridable sync hook off the event loop. It then awaits step 4's visibility for every scoped hop the normalized terms walk (`apply_type_visibility_async`), so an async-only target `get_queryset` works, and hands the derived rows to the shared tail. Normalization and queryset construction (`_apply_orderings`: `_normalize_input`, `get_flat_orders`, `Ordering.resolve()`, `alias` / `annotate` / `order_by`) are NOT wrapped: they are pure Python plus lazy queryset-method calls that issue no I/O. `thread_sensitive=True` keeps the hooks on the main sync thread, and because a `sync_to_async` worker is itself a sync context, the async-gate rejection in step 6 fires identically on both surfaces. The filter side runs its permission pass through the same helper inside [`FilterSet.apply_async`][filters-sets]'s `_apply_common_finalize` worker. Pinned by [`tests/orders/test_sets.py::test_orderset_apply_async_runs_check_permission_in_sync_to_async`][test-orders].

**Optimizer cooperation.** Order clauses are pure queryset-method calls; they do not change the result type, do not invalidate `select_related` / `prefetch_related`, and do not affect the optimizer's plan cache. The live `test_library_books_order_preserves_optimizer_cooperation` pins the cooperation at three queries.

**Composition.** [`apply_cascade_permissions`][glossary-apply_cascade_permissions] runs inside step 1 (the `get_queryset` hook); [Per-field permission hooks][glossary-per-field-permission-hooks], when they ship, slot into the field-resolver layer that runs after step 8. [`DjangoConnectionField`][glossary-djangoconnectionfield] builds its `orderBy:` argument from `Meta.orderset_class` and applies its pagination after step 7's `order_by(...)`.

Rationale companion — this Decision's justification and its four rejected alternatives: [Decision 8][rationale-d8].

### Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle

**The input-class namespace is the [`django_strawberry_framework.orders.inputs`][orders-inputs] module's own global namespace**, separate from the model-to-`DjangoType` registry at [`django_strawberry_framework.registry.registry`][registry] (which powers [`Meta.primary`][glossary-metaprimary]) AND separate from the [`django_strawberry_framework.filters.inputs`][filters-inputs] namespace.

Every generated order input class is a real module global of `django_strawberry_framework.orders.inputs`, set at finalize time. The class names are stable and class-derived (`_input_type_name_for(GalaxyOrder)` → `"GalaxyOrderInputType"`). The "registry" IS the module's `__dict__` — there is no separate private dict registry, because Strawberry's `LazyType.resolve_type` reads `module.__dict__` directly and cannot traverse a sidecar dict. A lifecycle ledger (`django_strawberry_framework.orders.inputs._materialized_names`, a private `dict[str, type]`) tracks `name → input class` (the class written to the module global); source-class collision detection lives separately in `OrderArgumentsFactory._type_orderset_registry`, mirroring the filter side's split between the materialization ledger and the factory's source-class registry. Re-materialization with the same `(name, input_cls)` pair is idempotent; collision against a different `input_cls` raises [`ConfigurationError`][glossary-configurationerror].

The order-input namespace and the filter-input namespace are **disjoint by module path**: `strawberry.lazy("django_strawberry_framework.orders.inputs")` and `strawberry.lazy("django_strawberry_framework.filters.inputs")` resolve against two distinct `module.__dict__` lookups. The `*Order` / `*Filter` naming convention (cookbook + strawberry-django) keeps the generated names apart as well (`BranchOrder` → `BranchOrderInputType`, `BranchFilter` → `BranchFilterInputType`).

Lifecycle contract (mirrors [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] Decision 9):

- **Registration is idempotent for the same `(name, input_class)` pair.** Calling `materialize_input_class("GalaxyOrderInputType", input_cls_a)` twice with the same `input_cls_a` is a no-op; the second call neither raises nor reassigns the module global.
- **Registration raises [`ConfigurationError`][glossary-configurationerror] when the same name is claimed by a DIFFERENT input class**, with both qualified names in the message.
- **`registry.clear()` replays `clear_order_input_namespace()`, which clears the order-input lifecycle ledger AND the `OrderArgumentsFactory` class-level caches AND every `OrderSet` subclass's per-class binding state — but leaves already-materialized module globals parked in `orders.inputs.__dict__`.** Parking is **load-bearing**: `materialize_input_class` overwrites the module global on the next finalize, so the parked class is replaced in place; stripping it via `delattr` would break any `strawberry.lazy(...)` LazyType held by a consumer module whose reload fixture did NOT also reload the holder. The shared clear point lets test-fixture reload patterns reset the `TypeRegistry` and every registered subsystem namespace (filter inputs and order inputs among them) in one call.
- **Import-cycle-safe integration through a registration seam.** [`django_strawberry_framework/registry.py`][registry] names no subsystem. Every loaded subsystem announces its own teardown callback at import time via `::register_subsystem_clear(clear, *, owner, before_bind=False)`, and `TypeRegistry.clear()` replays the callables through `::iter_subsystem_clears()`:

  ```python
  # django_strawberry_framework/orders/inputs.py - registered at import time.
  register_subsystem_clear(
      clear_order_input_namespace,
      owner="orders.input_namespace",
      before_bind=True,
  )

  # django_strawberry_framework/orders/__init__.py - the second, separate row.
  register_subsystem_clear(_clear_helper_referenced_ordersets, owner="orders.helper_references")

  # django_strawberry_framework/registry.py - the replay, subsystem-agnostic.
  class TypeRegistry:
      def clear(self) -> None:
          ...  # the registry's own state
          for clear in iter_subsystem_clears():
              clear()
  ```

  Three properties are load-bearing:

  - **A rename cannot silently drift.** Importing the owner module must resolve the function object before registration can succeed, so renaming `clear_order_input_namespace` breaks at the owner's own import.
  - **`registry.py` carries no `ImportError` guard for any subsystem.** Optional subsystems stay lazy structurally: only an imported owner can register, so an unimported subsystem contributes no callback. Adding a further clear phase (aggregates, fieldsets) requires no edit to `registry.py`.
  - **`owner` is a stable logical identity, not an import path.** It lets factory-generated callbacks register without colliding, and lets `importlib.reload` replace the old function object rather than accumulate duplicates — the reload pattern the fakeshop live-HTTP fixtures depend on. `before_bind=True` marks a generated-state reset the finalizer replays before every rebuild, which is why the order-input namespace carries it and the consumer-helper ledger does not.

  [`tests/orders/test_inputs.py::test_registry_clear_works_without_orders_imported`][test-orders-inputs] imports `django_strawberry_framework.registry` alone and asserts `registry.clear()` runs cleanly with no order-side callback registered; it mirrors `test_registry_clear_works_without_filters_imported` on the filter side.
- **Partial-finalize recovery.** If `finalize_django_types()` raises mid-phase-2.5, the module globals materialized before the raise stay parked. The next `finalize_django_types()` replays every `before_bind=True` row (`clear_order_input_namespace` among them) before phase 2.5, so it rebuilds from a cleared ledger, cleared factory caches and unbound ordersets, and its materialization overwrites the parked globals in place instead of colliding with them.
- **Public `clear_order_input_namespace()` helper.** Exposed from `django_strawberry_framework.orders.inputs` so tests can clear the order namespace WITHOUT clearing the full `TypeRegistry`; `registry.clear()` reaches it through its registered row. **Exact behavior (the shared heavy clear [`django_strawberry_framework/utils/inputs.py::make_set_input_namespace`][utils-inputs] builds for both families):** (a) clears `_materialized_names`; (b) clears `_field_specs` (the `(orderset, field) → FieldSpec` map the runtime `normalize_input_value` consults); (c) clears `OrderArgumentsFactory.input_object_types` AND `OrderArgumentsFactory._type_orderset_registry` (stale entries would let the shared base's idempotent build skip its rebuild and surface prior-build classes against a freshly-cleared registry); (d) resets every `OrderSet` subclass's binding state — `_owner_definition`, `_expanded_fields`, `_is_expanding_fields` — only where the subclass set it directly, so an inherited default is restored rather than masked; (e) **does NOT strip materialized module globals** from `orders.inputs.__dict__`.
- **`_helper_referenced_ordersets` clears through its OWN registered row** (owner `orders.helper_references`, registered in `orders/__init__.py` per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface)), NOT inside `clear_order_input_namespace()`. Two rows keep the two unrelated ledger lifecycles separately owned, matching the filter side, and only the namespace row carries `before_bind=True`.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 9][rationale-d9].

### Decision 10 — Version bumps are maintainer-commanded

Ordering shipped in `0.0.8`. The release is single-sourced in [`django_strawberry_framework/__init__.py::__version__`][package-init] (hatchling derives the packaging metadata from it, and [`tests/base/test_init.py::test_version`][test-base-init] pins it), and bumping it — like promoting a `CHANGELOG.md` release heading — happens only on the maintainer's explicit command, never as a side effect of a feature card completing.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 10][rationale-d10].

### Decision 11 — `order_input_type(OrderSet)` consumer helper

The package ships a public helper at [`django_strawberry_framework.orders.order_input_type`][orders], parallel to the filter side's `filter_input_type(FilterSet)`. **The helper returns the *element* type — NOT the list type**; resolvers wrap it as `list[...] | None` to match the [`orderBy: [<TypeName>OrderInputType!]`](#decision-5--ordering-enum-and-argument-shape) list-shaped GraphQL argument. The filter side's helper also returns the element type, but its resolvers don't wrap because `filter:` is a single object on the GraphQL surface. Symmetry is preserved at the helper level; the divergence lives only at the resolver-annotation site.

The helper ships in two spellings that evaluate to one annotation: the call `order_input_type(MyOrder)` and the type-checkable generic `OrderInput[MyOrder]` (wrapped as `list[OrderInput[MyOrder]] | None` at the resolver site):

```python
# django_strawberry_framework/orders/__init__.py (shape; the module is authoritative)
from ..utils.inputs import build_lazy_input_annotation
from .inputs import INPUTS_MODULE_PATH, _input_type_name_for
from .sets import OrderSet

# The orphan-tracking ledger, co-located with its only writer (Decision 2).
_helper_referenced_ordersets: set[type[OrderSet]] = set()


def _order_input_annotation(orderset_class: object, *, helper_spelling: str) -> object:
    return build_lazy_input_annotation(
        orderset_class,
        expected_base=OrderSet,
        helper_spelling=helper_spelling,
        expected_label="an OrderSet",
        ledger=_helper_referenced_ordersets,
        input_type_name_for=_input_type_name_for,
        module_path=INPUTS_MODULE_PATH,
    )


def order_input_type(orderset_class: type[OrderSet]) -> object:
    return _order_input_annotation(orderset_class, helper_spelling="order_input_type()")


class OrderInput(Generic[_OrderSetT]):  # _OrderSetT is bound to OrderSet
    def __class_getitem__(cls, orderset_class: object) -> object:
        return _order_input_annotation(orderset_class, helper_spelling="OrderInput[...]")
```

Both spellings return the element type `Annotated["<Name>OrderInputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]`, which Strawberry resolves via `LazyType.resolve_type` at schema-build time, after `finalize_django_types()` has materialized the class (per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering)). A call is not a valid type expression, so a type checker rejects `order_input_type(MyOrder)` in an annotation and accepts `OrderInput[MyOrder]`, rejecting `OrderInput[NotAnOrderSet]` statically through the `OrderSet` bound. `OrderInput` is never instantiated: the resolver receives the generated Strawberry input objects, opaque handles whose one use is `MyOrder.apply_sync(order_by, queryset, info)` / `apply_async`. The eager `TypeError` is worded with the spelling the consumer wrote (`order_input_type() requires an OrderSet subclass; got ...` or `OrderInput[...] requires ...`), so a typo at the resolver signature fails at evaluation time rather than at schema build.

The body is single-sited with the filter twin at [`django_strawberry_framework/utils/inputs.py::build_lazy_input_annotation`][utils-inputs], which performs the eager `issubclass` validation, records the set into the supplied `ledger` for the finalize-time orphan check, and builds the annotation. Two clauses inside that helper are contract:

- **The runtime-computed name must be passed as the first `Annotated[...]` argument, not interpolated into a literal.** `Annotated[<str variable>, ...]` wraps the string as a `typing.ForwardRef` in the first `__args__` position, the form `LazyType.resolve_type` resolves against `module.__dict__`.
- **The ledger write is idempotent**, because it is a `set` of classes — so evaluating the helper repeatedly with the same `OrderSet` (which PEP 563 / `typing.get_type_hints` re-evaluation can do) neither duplicates the orphan record nor changes the returned annotation.

Consumers use it as a normal Python type annotation in a resolver signature:

```python
@strawberry.field
def all_galaxies(
    self,
    info: strawberry.Info,
    order_by: list[OrderInput[GalaxyOrder]] | None = None,
) -> list[GalaxyType]:
    queryset = GalaxyType.get_queryset(models.Galaxy.objects.all(), info)
    if order_by is not None:
        queryset = GalaxyOrder.apply_sync(order_by, queryset, info)
    return queryset
```

**Evaluation timing.** Strawberry evaluates the annotation during schema declaration / collection — same mechanics as the filter side. With normal annotations it evaluates at module-load time; with `from __future__ import annotations` (PEP 563), Strawberry evaluates the string in the resolver's `__globals__` at type-collection time, so `GalaxyOrder` MUST be importable from the resolver module's globals then.

**Orphan `OrderSet` validation.** An `OrderSet` referenced via the helper but never wired via `Meta.orderset_class = MyOrder` on any `DjangoType` would not be materialized, and `LazyType.resolve_type` would fail for `MyOrderInputType` at `strawberry.Schema(...)` time. The package fails loud at finalize:

- The helper records every `OrderSet` it is called with into the module-level `_helper_referenced_ordersets: set[type[OrderSet]]` in [`django_strawberry_framework.orders`][orders].
- Finalizer phase 2.5 subpass 3 compares the helper-referenced set against the wired ordersets; one orphan raises [`ConfigurationError`][glossary-configurationerror] with `"OrderSet '<MyOrder>' is referenced via OrderInput[...] / order_input_type(...) but never assigned to a DjangoType via Meta.orderset_class. Add 'orderset_class = <MyOrder>' to the relevant DjangoType's Meta."` (the message names both helper spellings, since the ledger does not record which one the consumer wrote); several orphans are listed in one message.
- `registry.clear()` clears `_helper_referenced_ordersets` along with the model-to-`DjangoType` registry and the order-input namespace per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle).
- `test_orphan_order_input_type_reference_raises_at_finalize` pins this.

Rationale companion — this Decision's justification and its four rejected alternatives: [Decision 11][rationale-d11].

### Decision 12 — No Layer 6 auto-generation and no DISTINCT ON surface

The cookbook ships no `orderset_factories.py` and no `_dynamic_orderset_cache` — only the filter side upstream has a dynamic-factory mechanism — and its `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT` modifiers plus [`AdvancedOrderSet.apply_distinct`][upstream-cookbook-orderset] Window-function emulation offer a DISTINCT ON surface.

**Decision: the ordering surface carries neither. A type that wants an `orderBy:` argument declares an explicit [`Meta.orderset_class`][glossary-metaorderset_class], and the to-many fan-out DISTINCT ON was reached for is prevented inside the ordering itself.**

Layer 6 — the consumer declares the class:

- **The declaration is the whole surface.** [`DjangoConnectionField`][glossary-djangoconnectionfield] builds its `orderBy:` argument from the owner definition's already-resolved [`Meta.orderset_class`][glossary-metaorderset_class] sidecar: `django_strawberry_framework/connection.py::_synthesized_signature` appends the parameter only when `definition.orderset_class is not None`, and `connection.py::_pipeline_sync` / `connection.py::_pipeline_async` apply it through `django_strawberry_framework/utils/querysets.py::apply_orderset_sync` / `::apply_orderset_async`, which call [`OrderSet`][glossary-orderset]`.apply_sync` / `apply_async` and re-seal the returned queryset. [`DjangoListField`][glossary-djangolistfield]'s `orderBy:` argument ([`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050]) reads the same sidecar. A field whose target type declares no orderset gets no `orderBy:` argument at all — a legible contract rather than a missing feature.
- **No dynamic-factory plumbing.** The package carries no dynamic-`OrderSet` getter or cache, on the order side or the filter side. **Auto-generating an `OrderSet` from a field's `Meta`-shaped kwargs, without an explicit class, is a standing non-goal** — that is the surface Layer 6 would serve, and it has no consumer.
- Layers 1-5 do not depend on a Layer 6 cache, so adding one stays additive whenever a caller arrives.

DISTINCT ON — the fan-out is prevented in the ordering, not by de-duplicating afterwards:

- **A to-many term is ordered by an aggregate.** `django_strawberry_framework/orders/sets.py::OrderSet._resolve_order_expressions` annotates such a term with `Min` for an ascending direction and `Max` for a descending one and orders by the alias, so the join cannot multiply the parent row. Only paths `django_strawberry_framework/utils/relations.py::path_traverses_to_many` reports as to-many are annotated; scalar and to-one paths order directly. That keeps exactly one row per parent without any `DISTINCT`, which is what the cookbook's `apply_distinct` was for. A root [`DjangoConnectionField`][glossary-djangoconnectionfield] cursor-slices that grouped queryset; a nested relation connection carrying `orderBy:` runs the per-parent pipeline instead of window planning, so the aggregate never sits below the optimizer's row-number window.
- **The direction enum stays six-membered.** [`Ordering`][glossary-ordering] carries `ASC` / `DESC` / `ASC_NULLS_FIRST` / `ASC_NULLS_LAST` / `DESC_NULLS_FIRST` / `DESC_NULLS_LAST` per [Decision 5](#decision-5--ordering-enum-and-argument-shape) — the same six members `strawberry-graphql-django`'s ordering enum declares. The cookbook's `ASC_DISTINCT` / `DESC_DISTINCT` have no counterpart in that enum, and `graphene-django` carries no DISTINCT ordering directive at all, so the capability is optional under [`START.md`][start]'s parity test (what both reference libraries provide is foundational; what only one provides is optional). The members also conflate two orthogonal things — a direction and a partition.
- **No declaration surface ships for it.** Neither `Meta.distinct` nor `Meta.distinct_class` is in [`ALLOWED_META_KEYS`][base] or [`DEFERRED_META_KEYS`][base], so `_validate_meta`'s typo guard rejects either as an unknown key, and there is no `distinct_on:` argument.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 12][rationale-d12].

### Decision 13 — Live HTTP coverage strategy

Package coverage is earned through fakeshop live `/graphql/` HTTP flows wherever a real query reaches the line, per [`AGENTS.md`][agents] #"any line reachable via a real GraphQL query against fakeshop".

Live HTTP tests land in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] and cover: scalar-field ascending order, NULLS positioning on `Book.subtitle` across all four NULLS directions, forward-FK relation order, reverse-FK relation order asserting the row-preserving aggregate result (one row per parent, never one per child), M2M relation order through the absolute-import-path `RelatedOrder`, flat-shorthand path order (`Meta.fields = ["shelf__code"]` → `shelfCode:`), composition with the Filtering subsystem, composition with the optimizer (a pinned query count for a filtered + ordered queryset with nested selection), root `get_queryset` honoring, the **split-pair active-input-only scalar `check_*_permission` discipline**, the **active-branch relation-level permission gate** (`check_shelves_permission`), multi-field priority ordering, and the empty-list / null-direction no-op.

Package-internal tests (`tests/orders/`) land in seven files: the `__init__.py` shell, four mirrors (`test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`), `test_finalizer.py` for the phase-2.5 binding pass, and `test_composition.py`. They cover what a live query cannot easily reach: `LazyRelatedClassMixin.resolve_lazy_class` failure paths, `Ordering.resolve(field_path)` returning the correct `OrderBy` expressions, `normalize_input_value`'s walk across nested `RelatedOrder` inputs, and the [`ConfigurationError`][glossary-configurationerror] surface for invalid `Meta.fields`.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 13][rationale-d13].

## Implementation plan

Six slices aligned with the [Slice checklist](#slice-checklist).

| Slice | Files |
| --- | --- |
| 1 — Foundation | [`django_strawberry_framework/orders/__init__.py`][orders], [`django_strawberry_framework/orders/base.py`][orders], [`django_strawberry_framework/orders/sets.py`][orders], [`django_strawberry_framework/orders/inputs.py`][orders], [`tests/orders/__init__.py`][test-orders], [`tests/orders/test_base.py`][test-orders], [`tests/orders/test_sets.py`][test-orders] |
| 2 — Factories | [`django_strawberry_framework/orders/factories.py`][orders], [`django_strawberry_framework/orders/inputs.py`][orders], [`tests/orders/test_factories.py`][test-orders], [`tests/orders/test_inputs.py`][test-orders] |
| 3 — Wiring | [`django_strawberry_framework/types/base.py`][base], [`django_strawberry_framework/types/definition.py`][definition], [`django_strawberry_framework/types/finalizer.py`][finalizer], [`django_strawberry_framework/orders/__init__.py`][orders], [`tests/types/test_base.py`][test-types], `tests/orders/test_finalizer.py` |
| 4 — Live HTTP coverage | [`examples/fakeshop/apps/library/orders.py`][fakeshop-library], [`examples/fakeshop/apps/library/orders_genre.py`][fakeshop-library], [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema], [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] |
| 5 — Docs | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`README.md`][readme], [`TODAY.md`][today] |
| 6 — Composition test | [`tests/orders/test_composition.py`][test-orders-composition] |

## Edge cases and constraints

- **Same-module `RelatedOrder` references** (e.g., `BranchOrder` and `ShelfOrder` in one `orders.py` with `RelatedOrder("ShelfOrder")` and `RelatedOrder("BranchOrder")`). Layer 2 handles this: the absolute-path lookup fails and the `bound_class.__module__` retry succeeds.
- **Cross-module `RelatedOrder` references via absolute path** (e.g., `RelatedOrder("apps.library.orders_genre.GenreOrder")`). The absolute-path lookup succeeds; the retry is never reached. Exercised by the fakeshop `BookOrder.genres` declaration.
- **Circular `RelatedOrder` references** (`A → B → A`, or a self-reference such as `RelatedOrder("Self")` on a self-referential model). Expansion cannot cycle: `get_fields()` never expands a target (the captured-branch check reads only a target's `Meta.fields` expansion and declarations), so it never re-enters another orderset's `get_fields()`; the BFS factory visits each orderset once, and an input walk recurses only as deep as the consumer's input nests. The cache writes only when no string `_orderset` remains on any related order.
- **`Meta.fields = "__all__"`** (the shorthand). Expands to every **real-column-backed** model field: INCLUDES forward FK and forward OneToOne columns (`<field>_id`), EXCLUDES reverse relations, M2M managers, and Django's virtual `GenericRelation` / `GenericForeignKey` descriptors (see [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6)). For `BookOrder` against the fakeshop `Book` model: leaves for `id`, `title`, `subtitle`, `circulation_status`, AND `shelf` (ordered by `shelf_id`); NOT `genres` / `archive_genres` (M2M) or `loans` (reverse FK). A same-name `RelatedOrder(ShelfOrder, field_name="shelf")` **overrides** the column leaf — `shelf: Ordering` becomes `shelf: ShelfOrderInputType`. `"__all__"` without `Meta.model` raises [`ConfigurationError`][glossary-configurationerror].
- **`Meta.fields = ["shelf__code"]`** (the double-underscore path shorthand). **Renders as a flat field named `shelfCode` with an `Ordering` leaf** (`orderBy: [{ shelfCode: ASC }]`) — NOT `orderBy: [{ shelf: { code: ASC } }]`. Consumers wanting the nested surface declare an explicit `RelatedOrder(ShelfOrder)`. The runtime normalizer maps the flat field's Python attr to the Django source path via `FieldSpec.django_source_path`; the filter side keys its form data from `django_strawberry_framework/filters/inputs.py::filter_lookup_table` instead.
- **`Meta.orderset_class = AdminOrder` on a secondary `Meta.primary = False` `DjangoType`**. The secondary type is registered and reverse-discoverable; the order binding runs on its definition exactly as on the primary's. The input-type namespace is name-keyed, so two `DjangoType`s on one model with different `orderset_class`es generate two distinct input types.
- **`Meta.orderset_class` on a `DjangoType` that also declares `Meta.interfaces = (relay.Node,)`**. The order binding runs at phase 2.5 after the Relay-Node injection. The `Ordering` leaf type does not depend on Relay shape (ordering by `id` uses the Django PK column), so the order side has no equivalent to the filter side's Relay-vs-scalar conditional.
- **Order on a field that is NOT in the `DjangoType`'s `Meta.fields`** (e.g., the type exposes `name` but the orderset declares `description`). The order clause still applies; the consumer can order on columns they cannot select. This matches the cookbook and is intentional; no dedicated test pins it.
- **Order paths are pre-validated; backend expression support is not.** Every path — each `Meta.fields` entry at expansion, and each resolved path at apply time — goes through [`classify_path`][utils-relations] and raises [`ConfigurationError`][glossary-configurationerror] naming the path and the model. What is NOT pre-validated is whether the backend can execute an expression it accepted structurally (e.g. an unsupported collation or function); there, the Django `FieldError` / `NotImplementedError` propagates as a `GraphQLError`.
- **`Meta.fields` referencing a model property (not a field)**. Rejected with [`ConfigurationError`][glossary-configurationerror] when `get_fields()` first expands — finalize phase-2.5 subpass 2, not type creation, because the metaclass does not expand per [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6) Layer 3. Only model fields and resolvable relation paths are orderable; ordering on a computed expression is out of scope.
- **Empty `orderBy:` input** (`orderBy: []`). The apply pipeline returns the queryset unchanged; no `order_by(...)` call is made.
- **`orderBy: [{ name: null }]`** (an `Ordering` field set to GraphQL null). Treated as if the field were omitted: the leaf is `Ordering | None = None`, `null` decodes to `None`, and `normalize_input_value` emits no term for it (nor does the field's permission gate fire). The order falls through to the next list element, or to the queryset's existing order.
- **`orderBy: [{ shelf: null }]`** (a `RelatedOrder` field set to GraphQL null). Same — the nested input is `None`, so the branch contributes no term.
- **`orderBy: [{ name: ASC }, { name: DESC }]`** (the same field twice with conflicting directions). Django does not dedup `order_by(*expressions)`: both clauses are emitted (`ORDER BY name ASC, name DESC`), and the second has no observable effect because every row pair is already strictly ordered by the first. The result IS the `ASC` ordering; the package does not pre-validate the redundant declaration.
- **Async resolver returning an ordered queryset**. Strawberry's async path awaits the resolver; the queryset's `order_by(...)` clause applies normally.
- **`OrderSet`-derived input class name collision across two ordersets that share `__name__`**. Rejected per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle): the same `(name, input_cls)` pair is idempotent; two distinct ordersets claiming one name raise [`ConfigurationError`][glossary-configurationerror] in the factory's `_type_orderset_registry` check, and a different input class claiming a materialized name raises at materialization.
- **Partial-finalize recovery for the input-class namespace.** If `finalize_django_types()` raises mid-phase-2.5 (e.g., on an unresolved `RelatedOrder`), already-materialized classes stay parked in the module's `__dict__`; the next `finalize_django_types()` clears the ledger through the pre-bind sweep and re-materializes over them (see [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle)).
- **Fakeshop schema-reload pattern with already-materialized order inputs.** `registry.clear()` resets the model-to-`DjangoType` registry, the filter-input namespace, AND the order-input namespace in one call; the reload re-runs `finalize_django_types()`, which re-materializes the input classes and replaces the parked module globals in place.
- **Helper validation**. `order_input_type` / `OrderInput[...]` validate eagerly (`TypeError` for a non-`OrderSet`) even though the returned annotation is lazy.
- **Multi-database cooperation**. An `.order_by(...)` clause does not change the queryset's database alias; the [Multi-database cooperation][glossary-multi-database-cooperation] contract is untouched by order clauses. On the list and connection fields, an `apply_*` override that re-routes its returned queryset is rejected by the post-sidecar seal in `django_strawberry_framework/utils/querysets.py::apply_orderset_sync`; the `test_post_orderset_*` rows in [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db] pin it on the sharded layout.

## Test plan

The order side's tests live in [`tests/orders/`][test-orders] (package tests), [`tests/types/`][test-types] (the `Meta` promotion), and [`examples/fakeshop/test_query/`][fakeshop-test-library] (live `/graphql/` HTTP). Two further trees hold contracts the order side shares with the filter side: [`tests/utils/test_permissions.py`][test-utils-permissions] for the family-neutral active-input permission walk, and [`tests/test_sets_mixins.py`][test-sets-mixins] for the set-family mixin wiring, the one-declaration-per-relation and captured-branch refusals included. A contract is pinned once, in the tree that owns the code implementing it.

### `tests/orders/` (package tests)

System-under-test is `django_strawberry_framework` itself. Seven files: the `__init__.py` shell, four source mirrors, `test_finalizer.py`, and `test_composition.py` — matching [Decision 2](#decision-2--subpackage-layout-and-public-export-surface), [Decision 13](#decision-13--live-http-coverage-strategy), and [Definition of done](#definition-of-done) item 11.

- [`tests/orders/__init__.py`][test-orders] — empty shell so pytest collects under `tests.orders.<module>`.
- [`tests/orders/test_base.py`][test-orders] — covers `RelatedOrder` and the shared `LazyRelatedClassMixin`: `RelatedOrder` accepts class / absolute path / unqualified name forms; an unresolvable string propagates the `ImportError`, and a non-`OrderSet` target raises [`ConfigurationError`][glossary-configurationerror]; `bind_orderset` is idempotent; `RelatedOrder` reaches the lazy mixin through `sets_mixins`, not `filters.base`; `_validate_orderset_class` accepts an `OrderSet`, rejects anything else and imports `OrderSet` locally.
- [`tests/orders/test_sets.py`][test-orders] — covers `OrderSetMetaclass` + `OrderSet`: the metaclass collects `RelatedOrder` declarations into `cls.related_orders` (inherited declarations overridden by the current class); `get_fields()` expansion and its cache gate; `_run_permission_checks` recursion with **active-input-only scope**; an unresolvable `Meta.fields` path raises [`ConfigurationError`][glossary-configurationerror] (`test_orderset_meta_fields_rejects_unknown_order_path`), as does an unresolvable path at apply time (`test_orderset_resolve_order_expressions_rejects_unknown_order_path`); paths resolve against the QUERYSET's model, so a model-less `OrderSet` is legal (`test_modelless_orderset_uses_queryset_model_for_to_many_order`) and the queryset's model wins over a conflicting `Meta.model` (`test_queryset_model_overrides_conflicting_orderset_meta_model`); the `apply_sync` / `apply_async` pair returning a term-less input's queryset unchanged; to-many paths ordered by `Min` / `Max` and scalar paths directly (`test_resolve_order_expressions_aggregates_to_many_orders_scalar_directly`); the `Meta.fields` declaration gates (non-string entries, one-shot iterators, `"__all__"` without `Meta.model`); the dedup (`test_orderset_check_permission_dedups_repeated_list_entries`) and inactive-branch quiet path (`test_orderset_inactive_input_does_not_resolve_lazy_related_target`); the `apply_async` permission hop through `run_in_one_sync_boundary` (`test_orderset_apply_async_runs_check_permission_in_sync_to_async`); `_request_from_info` context shapes (`test_orderset_request_from_info_reads_context_request_attribute`, `test_orderset_request_from_info_reads_bare_httprequest_context`, `test_orderset_request_from_info_raises_on_unrecognized_context_shape`, `test_orderset_request_from_info_raises_when_info_context_is_none`); `OrderSet.type_name_for()` returning `f"{cls.__name__}InputType"` through `ClassBasedTypeNameMixin`; the `_normalize_input` purity check behind a `DjangoListField`'s active-term test ([`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050]'s contract).
- [`tests/orders/test_factories.py`][test-orders] — covers `OrderArgumentsFactory`: the BFS visits every reachable orderset via `orderset_cls.get_fields()`; `RelatedOrder` fields resolve via the `Annotated["Name", strawberry.lazy("django_strawberry_framework.orders.inputs")]` shape; the factory derives input field shape from resolved fields; input classes register under stable class-derived names, and two distinct ordersets claiming one name raise; cycles, diamonds and deep chains build each class once; an orderset with no orderable field raises; leaf fields take `Ordering | None`; subclassing the factory is rejected.
- [`tests/orders/test_inputs.py`][test-orders] — covers `_build_input_fields`, `convert_order_field_to_input_annotation`, `normalize_input_value`, `materialize_input_class`, the helper, and `Ordering`: `RelatedOrder` fields emit `Annotated["TargetOrderInputType", strawberry.lazy(...)] | None` and leaf fields `Ordering | None`; the converter returns `Ordering | None` whatever model field it is given (it ignores its arguments); `Ordering` has six members, `is_ascending` classifies all six, and `resolve` maps bare `ASC` / `DESC` to an `F(...)` expression with no NULLS clause (the four NULLS members are pinned live by `test_library_books_order_by_subtitle_null_positioning`); `normalize_input_value` produces flat `(field_path, Ordering)` tuples, including `shelf__code` for a `RelatedOrder("ShelfOrder", field_name="shelf")` branch; `materialize_input_class(name, input_cls)` sets the module global and writes the ledger, is idempotent for one `(name, input_cls)` pair, and raises [`ConfigurationError`][glossary-configurationerror] for a different input class; `clear_order_input_namespace()` resets the ledgers, caches and binding state and **leaves materialized module globals parked**; the helper raises `TypeError` for a non-`OrderSet`; `test_order_input_type_returns_element_annotation_for_orderset_subclass` asserts the first `Annotated` arg is a `typing.ForwardRef` with `__forward_arg__ == "MyOrderInputType"` and that the return is the element type (not `list[...]`); `test_order_input_type_is_idempotent_under_repeated_calls` (three calls, equivalent shapes, ledger size `1`); `registry.clear()` replays both order rows (`test_registry_clear_invokes_clear_order_input_namespace`, `test_registry_clear_clears_helper_referenced_ordersets`); `test_registry_clear_works_without_orders_imported`. The list-wrap SDL shape (`orderBy: [MyOrderInputType!]`) is exercised by the fakeshop schema's `list[OrderInput[...]] | None` resolver annotations and the live order tests rather than a dedicated SDL unit test.

`tests/orders/test_finalizer.py` — covers the phase-2.5 binding pass: `Meta.orderset_class` promotion accepts an `OrderSet` and rejects a non-`OrderSet`; **subpass ordering** — `test_phase_2_5_binds_all_owners_before_expansion` instruments `ShelfOrder.get_fields` and asserts its `_owner_definition` is already bound when the expansion subpass runs; **orphan validation** — `test_orphan_order_input_type_reference_raises_at_finalize` (a `StandaloneOrder` referenced by the helper but never wired raises with its name and the wiring suggestion); several orphans listed in one message; an orphan failure materializes nothing (`test_phase_2_5_orphan_check_runs_before_materialization`); subpass 4 sets the module globals; idempotent re-finalize; `test_phase_2_5_unresolved_related_order_raises_at_finalize`, with a non-`ImportError` expansion failure rewrapped and a `ConfigurationError` propagating by identity; the first-bind model check (`test_phase_2_5_rejects_orderset_wired_to_unrelated_owner_model`); the multi-owner `get_queryset` refusal in both declaration orders (`test_phase_2_5_rejects_shared_orderset_when_an_owner_scopes_get_queryset`), for a hook two owners inherit from one base (`test_phase_2_5_rejects_shared_orderset_whose_owners_share_one_custom_get_queryset`), and the identity-hook pairing it accepts (`test_phase_2_5_accepts_shared_orderset_whose_owners_keep_the_identity_get_queryset`); the different-table refusal in both declaration orders (`test_phase_2_5_rejects_shared_orderset_whose_owners_read_different_tables`) and the one-table pairing it accepts (`test_phase_2_5_accepts_shared_orderset_whose_owners_read_one_table`); the per-subclass binding that remedy relies on (`test_an_orderset_subclass_binds_its_own_owner_apart_from_its_base`: base and subclass on a hiding and a plain owner, every declaration order, each branch ordering by its own owner on the wire); multi-owner related-target agreement and the absent Relay-identity check (`test_bind_orderset_owner_*`).

### `tests/orders/test_composition.py`

In-process tests that construct a `DjangoType` with BOTH `Meta.filterset_class` AND `Meta.orderset_class`, call `finalize_django_types()`, and assert:

- Both factories' input types are reachable from the schema (`<TypeName>FilterInputType` AND `<TypeName>OrderInputType` resolve via `strawberry.Schema(...)` introspection).
- A resolver that consumes both arguments produces a queryset whose SQL carries `WHERE <filter>` AND `ORDER BY <order>` clauses.
- The shared `LazyRelatedClassMixin` resolution works when called from both families in one finalize pass, reached through the neutral `sets_mixins` module.

### `tests/types/test_base.py`

`test_meta_orderset_class_is_promoted_to_allowed_meta_keys` asserts `"orderset_class" not in DEFERRED_META_KEYS` AND `"orderset_class" in ALLOWED_META_KEYS`, pinning [Decision 7](#decision-7--metaorderset_class-promotion-gate).

### `examples/fakeshop/test_query/test_library_api.py`

System-under-test is the live `/graphql/` HTTP endpoint; coverage MUST be earned here where a real query reaches the line. The order contracts:

- `test_library_branches_order_by_name_asc` — `{ allLibraryBranches(orderBy: [{ name: ASC }]) { name } }`; branches sorted by name ascending. **Issued via the staff client** because `BranchOrder.check_name_permission` is declared permanently on the orderset for the split-pair coverage below; the staff client bypasses the gate so the ASC contract is pinned cleanly.
- `test_library_books_order_by_subtitle_null_positioning` — **parametrized over all four NULLS directions** (`ASC_NULLS_FIRST`, `ASC_NULLS_LAST`, `DESC_NULLS_FIRST`, `DESC_NULLS_LAST`). `Book.subtitle = TextField(blank=True, null=True)` is the nullable text field on `Book` (`Book.title` is non-null); the fixture seeds a `subtitle=None` row beside two non-null rows, and each row asserts the full expected subtitle sequence, so the NULL partition AND the non-null ordering are pinned per direction. Parametrizing is what makes the four sentinel combinations observable independently — a single `DESC_NULLS_LAST` case cannot distinguish a correct `nulls_last=True` from a backend default that happens to agree.
- `test_library_books_order_by_forward_fk_relation` — `{ allLibraryBooks(orderBy: [{ shelf: { code: ASC } }]) { shelf { code } } }`; books sorted by their shelf's code through the same-module `RelatedOrder("ShelfOrder")`.
- `test_library_branches_order_by_reverse_fk_relation` — `{ allLibraryBranches(orderBy: [{ shelves: { code: ASC } }]) { name } }`; **asserts the row-preserving aggregate result**: with `Branch(name="Alpha")` owning shelves `A`, `C`, `E` and `Branch(name="Beta")` owning shelf `B`, the response is `["Alpha", "Beta"]` — each branch exactly ONCE, ordered by the `Min` of its shelf codes ([Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface)). The uneven shelf count is what makes the contract observable: a raw `order_by("shelves__code")` fan-out would return Alpha three times. **Issued via the staff client** because `BranchOrder.check_shelves_permission` is declared permanently for the active-related-branch coverage below.
- `test_library_books_order_by_m2m_absolute_import_path` — `{ allLibraryBooks(orderBy: [{ genres: { name: ASC } }]) { title } }`; `BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")` resolves at finalize via `import_string`.
- `test_library_books_filter_and_order_compose` — `{ allLibraryBooks(filter: { circulationStatus: { exact: ... } }, orderBy: [{ title: ASC }]) { title circulationStatus } }`; only books in that status, sorted by title (the resolver chains `Filter.apply_sync` → `Order.apply_sync`).
- `test_library_books_order_preserves_optimizer_cooperation` — a filtered + ordered query selecting `shelf { code }` and `genres { name }` executes exactly three queries under `CaptureQueriesContext`; the optimizer's `select_related("shelf")` / `prefetch_related("genres")` survive the clauses. It does NOT assert that the package adds order columns to the `.only(...)` projection.
- `test_root_get_queryset_runs_before_order_apply` — `BranchType.get_queryset` hides `city == "restricted"` branches for anonymous users; with `Alpha` (`city="Boston"`) and `Zeta` (`city="restricted"`), an anonymous `orderBy: [{ city: DESC }]` returns only `Alpha`, while the staff client sees `["Zeta", "Alpha"]`. It orders by `city` because an anonymous `name` order would trigger `check_name_permission`, and the staff client would bypass the visibility hook under test.
- `test_related_order_reads_a_hidden_row_as_missing_for_anonymous` and `test_related_order_reads_every_row_for_staff` — one node per shape (declared to-one ascending and descending, a `Meta.fields` path, a declared many-to-many, a declared reverse FK, two declared hops, an undeclared many-to-many `altShelvesTopic`, an undeclared reverse one-to-one `circulationDeskName`): the anonymous order reads each hidden related row as missing (a genre whose only book is hidden sorts beside the genre with none), the staff order reads every row. `test_related_order_on_a_connection_reads_a_hidden_row_as_missing`, `test_nested_related_order_under_one_parent_reads_a_hidden_row_as_missing` (a nested `booksConnection(orderBy:)` under one genre), `test_related_order_on_a_list_field_keeps_a_positive_offset` (one hop and two), `test_related_order_adds_no_join_or_distinct_to_a_to_many_term`, and `test_related_order_reads_a_hidden_row_as_missing_async` over `/graphql-async-test/`. Package rows: the `_scoped_hops` reading in `tests/orders/test_sets.py` (`::test_scoped_hops_read_a_declared_hop_through_its_target_sets_bound_type` with its applied twin `::test_declared_hop_orders_by_the_rows_its_target_sets_bound_type_shows`, `::test_scoped_hops_read_the_intermediate_model_of_a_multi_relation_declaration`, `::test_scoped_hops_reentering_the_sets_model_read_the_type_the_set_is_bound_to` with `::test_reentering_path_orders_by_the_rows_the_sets_bound_type_shows` (re-entry by table, a proxy-typed owner's `orderBy` and a shared set's two one-table owners, in `tests/utils/test_relation_reentry.py`), `::test_scoped_hops_read_a_pk_segment_on_a_relation_keyed_model_as_that_relation`, and `::test_apply_async_awaits_an_async_only_hook_behind_a_related_term` over a to-one and a to-many term), the keyset refusal `tests/test_keyset_connection.py::test_keyset_order_state_rejects_a_related_value_read_through_a_hiding_type` (flat and nested spellings, against an identity-hook control), and the combinator refusal `tests/utils/test_querysets.py::test_validate_post_orderset_result_refuses_a_combined_result_ordered_through_a_hiding_type`.
- `test_order_check_permission_denies_for_active_field` — `BranchOrder.check_name_permission` raises `GraphQLError(..., extensions={"code": "ORDER_PERMISSION_DENIED"})` for non-staff users; an anonymous `orderBy: [{ name: ASC }]` returns that error.
- `test_order_check_permission_quiet_for_inactive_field` — the split partner: an anonymous `orderBy: [{ city: ASC }]` (the gated `name` absent) succeeds.
- `test_order_check_permission_denies_active_related_branch` — `BranchOrder.check_shelves_permission` raises `ORDER_PERMISSION_DENIED` for non-staff users; an anonymous `orderBy: [{ shelves: { code: ASC } }]` returns it (the parent's per-branch gate fired on the active `shelves` branch), and an anonymous `orderBy: [{ city: ASC }]` succeeds (the branch is inactive and `city` is unguarded).
- `test_library_books_order_by_multi_field_priority` — `orderBy: [{ shelf: { code: ASC } }, { title: DESC }]` over books sharing shelves and titles; shelf code dominates, title is secondary.
- `test_library_books_order_by_flat_shorthand_path` — `Meta.fields = ["shelf__code"]` with no explicit `RelatedOrder`; `orderBy: [{ shelfCode: ASC }]` is accepted and orders by `shelf__code`.
- `test_library_branches_order_empty_list_and_null_direction_no_op` — (a) `orderBy: []` succeeds and leaves the resolver's `order_by("id")`; (b) `orderBy: [{ name: null }]` succeeds with no `ORDER BY name` and without firing `check_name_permission` (a `None` leaf is inactive).

The same section carries further row-preserving rows for [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface)'s aggregate contract, among them `test_library_branches_order_by_scalar_then_to_many_aggregate_no_multiplication` (a mixed scalar + to-many `orderBy:` composes without one term clobbering the other's GROUP BY) and `test_library_genres_connection_pages_by_to_many_aggregate` (a `DjangoConnectionField` cursor-slices the grouped queryset, where a multiplied parent row would corrupt cursors and `totalCount`).

Every live suite in `test_query/` picks up the module-scoped autouse fixture `_reload_project_schema_for_acceptance_tests` in [`examples/fakeshop/test_query/conftest.py`][fakeshop-test-conftest]; the order binding re-runs on the post-reload `finalize_django_types()`.

## Doc updates

- [`docs/GLOSSARY.md`][glossary] — the [`OrderSet`][glossary-orderset], [`RelatedOrder`][glossary-relatedorder], [`Meta.orderset_class`][glossary-metaorderset_class], [`order_input_type`][glossary-order_input_type] and [`Ordering`][glossary-ordering] entries carry the shipped contract: declarative `Meta.model` / `Meta.fields` (list or column-backed `"__all__"`); `RelatedOrder` traversal and the shared Layer-2 resolution (the mixin propagates a failed resolution's `ImportError`; the finalize-time rewrap into a [`ConfigurationError`][glossary-configurationerror] happens a layer up, naming the offending set); `check_*_permission` gates with active-input-only scope and active-branch double-dispatch; the list-shaped `orderBy:` tie-breaker; the six-member `Ordering` enum and `resolve(field_path)`; row-preserving to-many ordering (ascending by `Min(path)`, descending by `Max(path)`), the root connection's cursor slice over that grouped queryset, and the nested relation connection's per-parent pipeline; the position-side-channel note on `RelatedOrder` ([Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer) step 4). They sit under the Ordering category; the [Public exports][glossary-public-exports] section does not list them, because per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface) the order symbols live at `django_strawberry_framework.orders`.
- [`docs/README.md`][docs-readme] documents the ordering surface (`Ordering` included) under "Ordering with `OrderSet`"; [`README.md`][readme] and [`TODAY.md`][today] show `Meta.orderset_class` wiring an `OrderSet`.
- [`docs/TREE.md`][tree] is rendered from module docstrings by [`scripts/build_tree_md.py`][build-tree]; it lists `orders/`'s four non-`__init__` modules and the mirrored `tests/orders/` tree.
- [`GOAL.md`][goal] — the astronomy showcase references `Meta.orderset_class = orders.GalaxyOrder` and the per-app `orders.py` shape.

## Risks and open questions

- **`Ordering` enum vs cookbook's `OrderDirection`.** The six-member enum ships per [Decision 5](#decision-5--ordering-enum-and-argument-shape). If consumers ever want the cookbook's `DISTINCT` modifiers, adding enum members is additive rather than breaking.
- **List-shaped `orderBy:` vs a sibling singular `order:` argument.** A single list argument ships per [Decision 5](#decision-5--ordering-enum-and-argument-shape); a singular `order:` that normalizes into a one-element list would be additive.
- **Orphan validation false positives.** The orphan check raises for any `OrderSet` referenced via the helper but never wired via `Meta.orderset_class`; there is no opt-out for a deliberately unwired helper reference.
- **Multi-`DjangoType`-per-model orderset binding (Meta.primary interaction).** The input-class namespace is name-keyed, so two `DjangoType`s on one model with two `orderset_class`es generate two distinct input types; the strict-reuse check for one orderset on two owners is the filter side's minus its own-PK Relay-identity axis: a custom `get_queryset` on either owner or a diverging `RelatedOrder` target is refused ([Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering) subpass 1). No aliasing key exists for two ordersets that should share one input type.
- **Per-field permission gate scope (active-input-only vs declaration-only).** Active-input-only ships, matching the filter side ([Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer)); there is no declaration-scoped mode.
- **`Meta.fields = "__all__"` performance and schema-size growth.** The BFS runs once at finalize and is cached, so per-request cost is unaffected. Schema size grows linearly with the column count (one input field per ordered column, NOT `field_count × lookup_count` like the filter side).
- **Glossary entry parity for internal symbols.** `OrderSetMetaclass`, `OrderArgumentsFactory`, `get_flat_orders` are internal symbols not in [`docs/GLOSSARY.md`][glossary]; they are documented here and in module docstrings.

## Out of scope (explicitly tracked elsewhere)

- **Aggregation** ([`AggregateSet`][glossary-aggregateset], [`RelatedAggregate`][glossary-relatedaggregate], [`Meta.aggregate_class`][glossary-metaaggregate_class], [`get_child_queryset`][glossary-get_child_queryset]) — planned Layer-3 sidecar reusing Layers 1–4 of the pipeline.
- **Field selection** ([`FieldSet`][glossary-fieldset], [`Meta.fields_class`][glossary-metafields_class]) — planned; orthogonal to ordering (field selection gates result shape, ordering arranges result order).
- **Search fields** ([`Meta.search_fields`][glossary-metasearch_fields]) — planned; consumes the filter subsystem's `LOOKUP_PREFIXES` + `construct_search`.
- **Permissions cascade** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions], [Per-field permission hooks][glossary-per-field-permission-hooks]) — their own cards; the cascade composes with the `check_*_permission` gates through `get_queryset` per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer).
- **`DjangoConnectionField`** ([`DjangoConnectionField`][glossary-djangoconnectionfield]), **`DjangoNodeField`** ([`DjangoNodeField`][glossary-djangonodefield]), **`DjangoConnection`** ([`DjangoConnection`][glossary-djangoconnection]) and [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] — their own specs; the connection field consumes this subsystem's factory output for its `orderBy:` argument.
- **`DjangoListField` arguments** ([`DjangoListField`][glossary-djangolistfield]) — its `offset` / `limit` / `orderBy` surface is [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050]'s; the `orderBy:` there applies the target's `Meta.orderset_class` through this subsystem.
- **Layer 6 auto-generated ordersets** — not a shipped surface per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface).
- **DISTINCT ON** (cookbook's `OrderDirection.ASC_DISTINCT` / `DESC_DISTINCT` + `AdvancedOrderSet.apply_distinct`) — not ported per [Decision 12](#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface).
- **`OrderSequence` tie-breaker descriptor** — not planned; positional list-element ordering covers the use case per [Decision 5](#decision-5--ordering-enum-and-argument-shape).
- **Custom expressions (ORM `F(...)` / `Func(...)` / `Case` ordering)** — not planned. Consumers needing custom expressions call `queryset.order_by(...)` in their own resolver, bypassing the `OrderSet` pipeline.
- **[`DEFERRED_META_KEYS`][base] entries other than `"orderset_class"`** — `"aggregate_class"`, `"fields_class"`, `"search_fields"` ship under their own cards.

## Definition of done

1. [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028] (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/SPECS/appx/spec-028-orders-0_0_8-terms.csv`][spec-028-terms] anchoring every project-specific term to its [`docs/GLOSSARY.md`][glossary] heading; [`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-028-orders-0_0_8.md`][check-spec-glossary] passes.
2. [`django_strawberry_framework/orders/`][orders] is a subpackage with `__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py` per [Decision 2](#decision-2--subpackage-layout-and-public-export-surface). Its `__all__` is `OrderInput`, `OrderSet`, `OrderSetMetaclass`, `Ordering`, `RelatedOrder`, `order_input_type`; `OrderArgumentsFactory` is reached via `django_strawberry_framework.orders.factories`. The top-level package's `__all__` does not carry them.
3. `base.py` ships `RelatedOrder` (port of the cookbook's `BaseRelatedOrder`), deriving from the shared [`sets_mixins.py::RelatedSetTargetMixin`][sets-mixins] (a `LazyRelatedClassMixin` subclass) via sibling import; nothing is duplicated. `OrderSet` (in `sets.py`) inherits [`ClassBasedTypeNameMixin`][sets-mixins] from the same module so `OrderSet.type_name_for()` produces the canonical `{cls.__name__}InputType` name.
4. `sets.py` ships `OrderSetMetaclass` and `OrderSet` per Layers 3 + 4 of [Decision 3](#decision-3--five-layer-port-plus-a-deferred-layer-6). `OrderSet` carries: (a) the `_owner_definition: DjangoTypeDefinition | None` slot bound at finalizer phase 2.5; (b) **the resolver-facing classmethod pair `apply_sync(input_value, queryset, info) -> QuerySet` and `async def apply_async(input_value, queryset, info) -> QuerySet`** per [Decision 8](#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer): resolve the request (`info.context.request`, a bare `HttpRequest`, a mapping or Channels context), run `_run_permission_checks` with **active-input-only scope** (an `async def` gate raises `SyncMisuseError`), then normalize the input into `(field_path, Ordering | None)` pairs, resolve every path against **`queryset.model`** (so a model-less `OrderSet` is legal), pre-validate each through [`utils/relations.py::classify_path`][utils-relations], order a to-many path by a row-preserving `Min` / `Max` aggregate over an annotation alias and every other path directly through `Ordering.resolve(...)`, and return the ordered queryset (a term-less input returns it unchanged); (c) **NO `apply(...)` dispatcher** (the filter side's `apply` exists for sync-misuse rewrapping the order side never triggers); (d) `get_fields` expanding the `Meta.fields` list or the `"__all__"` shorthand (every column-backed model field — includes forward FK / OneToOne columns; excludes reverse relations and M2M managers); (e) `Meta.model`, `Meta.fields`, the inherited classmethod permission pipeline from [`sets_mixins.py::ActiveInputPermissionMixin`][sets-mixins] (no instance-method `check_permissions`), and `get_flat_orders`.
5. `factories.py` ships `OrderArgumentsFactory` (Layer 5 BFS on the shared `GeneratedInputArgumentsFactory`, deriving input field types from the resolved fields on `orderset_cls.get_fields()`). Leaf fields land as `Ordering | None`; `RelatedOrder` fields as `Annotated["<Target>OrderInputType", strawberry.lazy(...)] | None`.
6. `inputs.py` IS the input-class namespace per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle): order input classes are materialized as real module globals of `django_strawberry_framework.orders.inputs` via `materialize_input_class(name, input_cls)` (idempotent for `(name, input_cls)` pairs — `_materialized_names` stores `name → input class`; source-class collision detection lives in `OrderArgumentsFactory._type_orderset_registry`), raising [`ConfigurationError`][glossary-configurationerror] on a name claimed by a different input class. The module ships the `Ordering` enum, `INPUTS_MODULE_PATH`, `_input_type_name_for`, `materialize_input_class`, `clear_order_input_namespace` (clears `_materialized_names`, `_field_specs`, `OrderArgumentsFactory.input_object_types`, `OrderArgumentsFactory._type_orderset_registry`, and every `OrderSet` subclass's `_owner_definition` / `_expanded_fields` / `_is_expanding_fields`; **leaves materialized module globals parked**), `_build_input_fields`, `convert_order_field_to_input_annotation(model_field, owner_definition)`, and `normalize_input_value(orderset_cls, input_value)`.
7. `orders/__init__.py` exports the helper in both spellings per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper): `OrderInput[BranchOrder]` / `order_input_type(BranchOrder)` return the **element type** `Annotated["BranchOrderInputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]`, which resolvers wrap as `list[...] | None = None` to match the list-shaped `orderBy: [<T>OrderInputType!]` argument from [Decision 5](#decision-5--ordering-enum-and-argument-shape). The helper validates eagerly (`TypeError` for a non-`OrderSet`) AND records the orderset into `_helper_referenced_ordersets` for the finalizer's orphan check.
8. [`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`][definition] carries the `orderset_class` slot, populated from `Meta.orderset_class`.
9. [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] does not contain `"orderset_class"`; [`ALLOWED_META_KEYS`][base] does; [`django_strawberry_framework/types/base.py::_validate_orderset_class`][base] raises [`ConfigurationError`][glossary-configurationerror] for a non-`OrderSet`, importing `OrderSet` inside the function (`from ..orders.sets import OrderSet`) to dodge the `types → orders → types` module-load cycle, exactly as [`django_strawberry_framework/types/base.py::_validate_filterset_class`][base] does for `FilterSet`.
10. [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer] runs the phase-2.5 order-binding pass per [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering): `_bind_ordersets()` runs four ordered subpasses **(1) bind owners, (2) expand fields, (3) orphan-validate against `_helper_referenced_ordersets`, (4) materialize input classes**, after `_bind_filtersets()`. Both delegate to [`django_strawberry_framework/types/finalizer.py::_bind_sidecar_sets`][finalizer], configured by a `_SidecarBindingSpec`; the driver's filter-only subpass 2.5 is opted out of for orders. `registry.clear()` replays every subsystem's registered teardown callback.
11. `tests/orders/` carries **seven** files: the `__init__.py` shell, four source mirrors (`test_base.py`, `test_sets.py`, `test_factories.py`, `test_inputs.py`), `test_finalizer.py`, and `test_composition.py`, per the [Test plan](#test-plan).
12. [`tests/types/test_base.py`][test-types] carries the `Meta.orderset_class` promotion test.
13. [`examples/fakeshop/apps/library/`][fakeshop-library] ships `orders.py` (with `BranchOrder`, `ShelfOrder`, `BookOrder`, `LoanOrder`, `PatronOrder` for the relation graph, `PeriodicalOrder` / `IssueOrder` as the keyset-cursor `orderBy:` substrate, and further ordersets for the app's other types, with same-module `RelatedOrder("...")` references) AND `orders_genre.py` (`GenreOrder`, the cross-module fixture so `BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")` exercises the Layer-2 absolute-import-path branch, closing the cycle through `GenreOrder.books = RelatedOrder("apps.library.orders.BookOrder")`).
14. [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] wires `Meta.orderset_class` on its `DjangoType` classes; its root resolvers annotate `order_by:` as **`list[OrderInput[orders.<Name>Order]] | None`** per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper) and call the orderset's `apply_sync(order_by, queryset, info)` AFTER `<OwnerType>.get_queryset(queryset, info)` and the optional `<TypeName>Filter.apply_sync(filter, queryset, info)`.
15. [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] carries the live order contracts listed in the [Test plan](#test-plan).
16. [`docs/GLOSSARY.md`][glossary] carries the [`OrderSet`][glossary-orderset], [`RelatedOrder`][glossary-relatedorder], [`Meta.orderset_class`][glossary-metaorderset_class], [`order_input_type`][glossary-order_input_type], and [`Ordering`][glossary-ordering] entries under the Ordering category, with the [Index][glossary-index] listing all five.
17. [`docs/TREE.md`][tree] lists `orders/` on disk and enumerates the mirrored `tests/orders/` tree.
18. Package coverage stays at 100% (`fail_under = 100` in `pyproject.toml [tool.coverage.report]`), gated by CI.
19. Slice 6 (the composition test with the Filtering subsystem) lives in [`tests/orders/test_composition.py`][test-orders-composition].

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[readme]: ../../README.md
[start]: ../../START.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-aggregateset]: ../GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-cross-subsystem-invariants]: ../GLOSSARY.md#cross-subsystem-invariants
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-djangoconnection]: ../GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fieldset]: ../GLOSSARY.md#fieldset
[glossary-filter_input_type]: ../GLOSSARY.md#filter_input_type
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-get_child_queryset]: ../GLOSSARY.md#get_child_queryset
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-index]: ../GLOSSARY.md#index
[glossary-metaaggregate_class]: ../GLOSSARY.md#metaaggregate_class
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metafields_class]: ../GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: ../GLOSSARY.md#metafilterset_class
[glossary-metainterfaces]: ../GLOSSARY.md#metainterfaces
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaoptimizer-hints]: ../GLOSSARY.md#metaoptimizer_hints
[glossary-metaorderset_class]: ../GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-metasearch_fields]: ../GLOSSARY.md#metasearch_fields
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-order_input_type]: ../GLOSSARY.md#order_input_type
[glossary-ordering]: ../GLOSSARY.md#ordering
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: ../GLOSSARY.md#per-field-permission-hooks
[glossary-public-exports]: ../GLOSSARY.md#public-exports
[glossary-queryset-diffing]: ../GLOSSARY.md#queryset-diffing
[glossary-relatedaggregate]: ../GLOSSARY.md#relatedaggregate
[glossary-relatedfilter]: ../GLOSSARY.md#relatedfilter
[glossary-relatedorder]: ../GLOSSARY.md#relatedorder
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[spec-050]: ../spec-050-list_field_arguments-0_0_15.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[next]: NEXT.md
[rationale-d10]: appx/spec-028-orders-0_0_8-rationale.md#decision-10--version-bumps-are-maintainer-commanded
[rationale-d11]: appx/spec-028-orders-0_0_8-rationale.md#decision-11--order_input_typeorderset-consumer-helper
[rationale-d12]: appx/spec-028-orders-0_0_8-rationale.md#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface
[rationale-d13]: appx/spec-028-orders-0_0_8-rationale.md#decision-13--live-http-coverage-strategy
[rationale-d1]: appx/spec-028-orders-0_0_8-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-028-orders-0_0_8-rationale.md#decision-2--subpackage-layout-and-public-export-surface
[rationale-d3]: appx/spec-028-orders-0_0_8-rationale.md#decision-3--five-layer-port-plus-a-deferred-layer-6
[rationale-d4]: appx/spec-028-orders-0_0_8-rationale.md#decision-4--upstream-primitives-parity-floor
[rationale-d5]: appx/spec-028-orders-0_0_8-rationale.md#decision-5--ordering-enum-and-argument-shape
[rationale-d6]: appx/spec-028-orders-0_0_8-rationale.md#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering
[rationale-d7]: appx/spec-028-orders-0_0_8-rationale.md#decision-7--metaorderset_class-promotion-gate
[rationale-d8]: appx/spec-028-orders-0_0_8-rationale.md#decision-8--cooperation-with-filtering-get_queryset-and-the-optimizer
[rationale-d9]: appx/spec-028-orders-0_0_8-rationale.md#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle
[spec-015]: spec-015-relay_interfaces-0_0_5.md
[spec-018]: spec-018-meta_primary-0_0_6.md
[spec-020]: spec-020-list_field-0_0_7.md
[spec-027]: spec-027-filters-0_0_8.md
[spec-027-d8]: spec-027-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation
[spec-028-rationale]: appx/spec-028-orders-0_0_8-rationale.md
[spec-028-terms]: appx/spec-028-orders-0_0_8-terms.csv
[spec-028]: spec-028-orders-0_0_8.md
[spec-045]: spec-045-visibility_boundary-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/types/base.py
[connection]: ../../django_strawberry_framework/connection.py
[definition]: ../../django_strawberry_framework/types/definition.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[optimizer-predicates]: ../../django_strawberry_framework/optimizer/predicates.py
[orders]: ../../django_strawberry_framework/orders/
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[package-init]: ../../django_strawberry_framework/__init__.py
[registry]: ../../django_strawberry_framework/registry.py
[registry-typeregistry]: ../../django_strawberry_framework/registry.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-orders]: ../../tests/orders/
[test-orders-composition]: ../../tests/orders/test_composition.py
[test-orders-inputs]: ../../tests/orders/test_inputs.py
[test-sets-mixins]: ../../tests/test_sets_mixins.py
[test-types]: ../../tests/types/
[test-utils-permissions]: ../../tests/utils/test_permissions.py

<!-- examples/ -->
[fakeshop-library]: ../../examples/fakeshop/apps/library/
[fakeshop-library-schema]: ../../examples/fakeshop/apps/library/schema.py
[fakeshop-test-conftest]: ../../examples/fakeshop/test_query/conftest.py
[fakeshop-test-library]: ../../examples/fakeshop/test_query/test_library_api.py
[fakeshop-test-multi-db]: ../../examples/fakeshop/test_query/test_multi_db.py

<!-- scripts/ -->
[build-tree]: ../../scripts/build_tree_md.py
[check-spec-glossary]: ../../scripts/check_spec_glossary.py

<!-- .venv/ -->

<!-- External -->
[strawberry-lazy]: https://strawberry.rocks
[upstream-cookbook]: https://github.com/riodw/django-graphene-filters
[upstream-cookbook-mixins]: https://github.com/riodw/django-graphene-filters
[upstream-cookbook-order-arguments-factory]: https://github.com/riodw/django-graphene-filters
[upstream-cookbook-orders]: https://github.com/riodw/django-graphene-filters
[upstream-cookbook-orderset]: https://github.com/riodw/django-graphene-filters
[upstream-graphene-filter-fields]: https://github.com/graphql-python/graphene-django
[upstream-strawberry-ordering]: https://github.com/strawberry-graphql/strawberry-django
