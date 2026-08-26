# Spec: `DjangoConnectionField` (Relay connection field) — `DjangoConnection[T]`, sidecar-derived `filter:` / `orderBy:` arguments, opt-in `totalCount`

Shipped in `0.0.9` (card [`DONE-030-0.0.9`][kanban]). **This spec is the final implementation record, not an open build plan.** The card is the **central read-side primitive** for the package's Relay surface: every Layer-3 argument (filter, order, and later search / aggregate / field-selection) composes through this one field, and the [Full Relay story][kanban] ([`DONE-032-0.0.9`][kanban]) builds directly on it. The [Slice checklist](#slice-checklist) below stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention; build progress is tracked in the build plan, not here); the [Definition of done](#definition-of-done) describes the closure conditions; the [Current state](#current-state) section describes the repo as of this spec's authoring, before the build. **Version boundary** (see [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)): this card shares the `0.0.9` patch line with three sibling cards ([`DONE-031-0.0.9`][kanban], [`DONE-032-0.0.9`][kanban], [`DONE-033-0.0.9`][kanban]) and [`DONE-029-0.0.9`][kanban]; the `pyproject.toml` / [`__version__`][package-init] / [`tests/base/test_init.py::test_version`][test-base-init] bump to `0.0.9` is owned by the **joint cut**, not by this card. This card's slices land within the `0.0.9` line and never bump the version themselves (the on-disk version is still `0.0.8` at spec-authoring time).

Status: **SHIPPED (`0.0.9`)** — card [`DONE-030-0.0.9`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.9]` heading. Five slices: Slice 1 (the [`DjangoConnection`][glossary-djangoconnection]`[T]` base + the per-target **concrete** connection classes that carry the opt-in `totalCount`, the net-new `Meta.connection` key validated AND stored on [`DjangoTypeDefinition`][definition], and the `first` + `last` guard the package must implement itself), Slice 2 (the [`DjangoConnectionField`][glossary-djangoconnectionfield] factory + the synthesized-signature resolver that injects the sidecar-derived `filter:` / `orderBy:` arguments + the visibility→filter→order→default-order composition pipeline + the consumer-`resolver=` contract + the extracted optimizer cooperation point + sync/async paths), Slice 3 (verify the optimizer cooperation the field owns and name the nested-connection planning boundary the sibling [`DONE-033-0.0.9`][kanban] card owns), Slice 4 (live HTTP coverage on a Relay-Node-shaped fakeshop type **and** the public-export promotion), and Slice 5 (doc updates + the card-completion wrap; grants the per-card [`CHANGELOG.md`][changelog] edit permission [`AGENTS.md`][agents] otherwise withholds). Slices 1→2→3→4 are sequential (each builds on the prior); Slice 5 lands last. The [Slice checklist](#slice-checklist) below stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention).

Owner: package maintainer.

Predecessors: [`spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (the most-recently-shipped spec — the canonical voice / depth / section-layout reference for this document; its [Decision 11][spec-029] joint-`0.0.9`-cut version-bump boundary is the precedent [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut) reuses verbatim, and its [Decision 3][spec-029] singleton-factory `extensions=` form is the construction shape every example schema in this spec uses); [`spec-028-orders-0_0_8.md`][spec-028] (the [`OrderSet`][glossary-orderset] subsystem whose [`order_input_type`][glossary-order_input_type] helper, `apply_sync` / `apply_async` pair, and `_helper_referenced_ordersets` orphan-validation ledger this card's `orderBy:` argument reuses); [`spec-027-filters-0_0_8.md`][spec-027] (the [`FilterSet`][glossary-filterset] subsystem whose [`filter_input_type`][glossary-filter_input_type] helper and `apply_sync` / `apply_async` pair this card's `filter:` argument reuses, and whose [Decision 8][spec-027] `get_queryset` cooperation contract this card's composition order extends to the connection-pagination case); [`spec-020-list_field-0_0_7.md`][spec-020] (the [`DjangoListField`][glossary-djangolistfield] non-Relay sibling — the closest existing analogue: a PascalCase factory function returning a Strawberry field, with the same `get_queryset`-applying sync/async resolver wrappers and the same `Manager` / `QuerySet` / iterable consumer-resolver contract this card extends to the Relay shape, and whose [Decision 8][spec-020] explicitly scoped the connection field out to this card); [`spec-015-relay_interfaces-0_0_5.md`][spec-015] (the [Relay Node integration][glossary-relay-node-integration] foundation — `Meta.interfaces = (relay.Node,)`, the injected `resolve_*` defaults, `id: GlobalID!` suppression, and [`SyncMisuseError`][glossary-syncmisuseerror] — that the connection field's per-edge node resolution and visibility-hook cooperation build on). [`docs/GLOSSARY.md`][glossary] carries [`DjangoConnectionField`][glossary-djangoconnectionfield], [`DjangoConnection`][glossary-djangoconnection], [`Meta.connection`][glossary-metaconnection], and [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] entries; this card ships and documents the first three, and the fourth's status belongs to [`DONE-033-0.0.9`][kanban].

This spec's deliberative layer — the three-revision review history that produced it, every Decision's justification, every alternative each Decision rejected, and the risk / open-question deliberation that settled the card's design questions — lives in the rationale companion [`docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`][spec-030-rationale].

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoConnectionField`][glossary-djangoconnectionfield] — the Relay-style connection field this card ships: `edges` / `node` / `pageInfo` / `totalCount`, cursor pagination, and `filter:` / `orderBy:` arguments flowing into the wrapped type's [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class]. Status flips `planned for 0.0.9` → `shipped (0.0.9)`.
- [`DjangoConnection`][glossary-djangoconnection] — the generic `DjangoConnection[T]` base the consumer annotates; the concrete per-target connection class the factory resolves it to carries the opt-in `totalCount` ([Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes)). Status flips `planned for 0.0.9` → `shipped (0.0.9)`.
- [Relay Node integration][glossary-relay-node-integration] — the shipped `0.0.5` foundation (`Meta.interfaces = (relay.Node,)`, injected `resolve_*` defaults, `id: GlobalID!`). A `DjangoConnectionField` is only meaningful over a Relay-Node-shaped [`DjangoType`][glossary-djangotype]; the connection's `edges { node }` are that type's nodes.
- [`Meta.interfaces`][glossary-metainterfaces] — the key that declares `relay.Node`; [Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition) rejects `Meta.connection` on a non-Relay-Node type (the type must be Relay-Node-shaped — `relay.Node` in `Meta.interfaces`, or direct `relay.Node` inheritance).
- [`Meta.connection`][glossary-metaconnection] — the net-new type-level Relay connection options key this card ships; `0.0.9` accepts `{"total_count": bool}`, requires a Relay-Node-shaped type (`relay.Node` in [`Meta.interfaces`][glossary-metainterfaces] or direct inheritance), and drives the per-target connection class's `totalCount` shape.
- [`FilterSet`][glossary-filterset] / [`filter_input_type`][glossary-filter_input_type] / [`Meta.filterset_class`][glossary-metafilterset_class] — the shipped filter subsystem the connection field's `filter:` argument is auto-derived from; the field reuses the `apply_sync` / `apply_async` classmethod pair and the `filter_input_type` lazy-`Annotated` machinery, injected through the resolver signature ([Decision 6](#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature)).
- [`OrderSet`][glossary-orderset] / [`order_input_type`][glossary-order_input_type] / [`Meta.orderset_class`][glossary-metaorderset_class] / [`Ordering`][glossary-ordering] — the shipped ordering subsystem the `orderBy:` argument is auto-derived from; the list-shaped `orderBy: [<T>OrderInputType!]` argument is the multi-field tie-breaker mechanism.
- [`RelatedFilter`][glossary-relatedfilter] / [`RelatedOrder`][glossary-relatedorder] — the cross-relation traversal primitives whose active-branch [`get_queryset`][glossary-get_queryset-visibility-hook] scoping the connection field inherits unchanged when it routes input through `apply_sync` / `apply_async`.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — runs FIRST in the connection field's composition pipeline ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)); the visibility scope is what filter, order, the default ordering, and the cursor slice all narrow, never widen.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] / [Plan cache][glossary-plan-cache] / [`only()` projection][glossary-only-projection] / [FK-id elision][glossary-fk-id-elision] / [Queryset diffing][glossary-queryset-diffing] / [Strictness mode][glossary-strictness-mode] — the optimizer surface the connection field cooperates with. Because the schema middleware cannot see the queryset behind Strawberry's connection slicing, the field **owns its own cooperation point** via a helper extracted from the optimizer ([Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point)), and that point derives the node type's plan from the `edges { node { ... } }` selections. Windowed planning of a **nested** `<field>Connection` reached under `edges { node { … } }` is [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning], the sibling [`DONE-033-0.0.9`][kanban] card.
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] — the sibling [`DONE-033-0.0.9`][kanban] card that teaches the walker to recognize and window-plan **nested** connection selections; it plugs into the cooperation point this card wires, so it is a walker change, not a connection-field retrofit.
- [`DjangoListField`][glossary-djangolistfield] — the shipped non-Relay `list[T]` sibling whose factory-function mechanism ([Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation)), `get_queryset`-applying sync/async resolver wrappers, and `Manager` / `QuerySet` / iterable consumer-resolver contract ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)) this card extends to the Relay shape.
- [`DjangoNodeField`][glossary-djangonodefield] — the root single-node lookup field; **not** this card's surface — it belongs to the [Full Relay story][kanban] ([`DONE-032-0.0.9`][kanban]), which ships it in [`django_strawberry_framework/relay.py`][relay-root]. Cited because it shares the finalizer auto-trigger seam this card declines to build ([Decision 12](#decision-12--no-auto-trigger-of-finalize_django_types-for-009)).
- [`finalize_django_types`][glossary-finalize_django_types] — the single-threaded schema-setup synchronization point; the connection field is constructed at schema-build time and does NOT auto-trigger it for `0.0.9` ([Decision 12](#decision-12--no-auto-trigger-of-finalize_django_types-for-009)).
- [`ConfigurationError`][glossary-configurationerror] — raised at type-creation / field-construction time for the connection field's static validation failures (`Meta.connection` malformed or on a non-Relay type, a non-`DjangoType` target). The runtime `first` + `last` rejection is a `GraphQLError`, not a `ConfigurationError` (see [Decision 3](#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard)).
- [`DjangoType`][glossary-djangotype] / [`Meta.primary`][glossary-metaprimary] — the type the field wraps; the [`Meta.primary`][glossary-metaprimary] multi-type rule governs which type a relation-as-connection upgrade resolves to (the upgrade itself is [`DONE-032-0.0.9`][kanban]'s job, out of scope here).
- [`SyncMisuseError`][glossary-syncmisuseerror] — the typed marker the shared visibility helpers ([`utils/querysets.py`][querysets]) raise when a sync resolver context meets an async `get_queryset`; the connection field's sync path inherits this contract ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)).
- [`strawberry_config`][glossary-strawberry_config] — the scalar-map factory every example schema in this spec passes to `strawberry.Schema(...)` alongside the singleton-factory [`DjangoOptimizerExtension`][glossary-djangooptimizerextension].
- [Public exports][glossary-public-exports] / [Definition-order independence][glossary-definition-order-independence] — the package-surface and schema-finalization backdrop for Slice 4's `__init__.py` promotion and the [Decision 12](#decision-12--no-auto-trigger-of-finalize_django_types-for-009) no-auto-finalize posture.
- [`Meta.model`][glossary-metamodel] / [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] / [`Meta.name`][glossary-metaname] / [`Meta.description`][glossary-metadescription] / [`Meta.nullable_overrides`][glossary-metanullable_overrides] / [`Meta.required_overrides`][glossary-metarequired_overrides] — the shipped baseline `DjangoType` `Meta` keys framing why the new `Meta.connection` key is added directly to `ALLOWED_META_KEYS` and stored on the definition.
- [Relation handling][glossary-relation-handling] — the relation-field behavior a connection field composes beside; the relation-as-Connection upgrade over it (and the `Meta.relation_shapes` opt-out that governs which relations take it) is the sibling Full Relay story's surface, not this card's.

Dependency and forward-composition surfaces a reader will hit:

- [`Meta.search_fields`][glossary-metasearch_fields] (`0.1.2`) — the `search: String` connection argument is **absent** until search ships; the connection field reserves the seam but does not generate the argument in `0.0.9` (per the card body).
- [`FieldSet`][glossary-fieldset] / [`Meta.fields_class`][glossary-metafields_class] (`0.1.1`) — field-selection composition layers onto the connection field after it ships; out of scope here.
- [`AggregateSet`][glossary-aggregateset] / [`Meta.aggregate_class`][glossary-metaaggregate_class] / [`RelatedAggregate`][glossary-relatedaggregate] (`0.1.3`) — the `aggregates` connection argument; a later composition surface, listed only as an out-of-scope pointer.
- [`apply_cascade_permissions`][glossary-apply_cascade_permissions] (`0.0.10`) — the permissions card; the connection field respects [`get_queryset`][glossary-get_queryset-visibility-hook] immediately and gains declared-permission integration when the permissions subsystem lands.
- [Multi-database cooperation][glossary-multi-database-cooperation] — the connection field's queryset flows through the same `.using(alias)` `_db`-preservation contract; no new multi-db surface here.
- [`OptimizerHint`][glossary-optimizerhint] / [`Meta.optimizer_hints`][glossary-metaoptimizer_hints] — per-relation overrides on the wrapped type; the extracted optimizer helper honors them exactly as the middleware path does.
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — the `1.0.0` rule that every Layer-3 argument composes with the optimizer; this card is the field through which that composition runs.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package tests under `tests/` mirroring source; example-project non-HTTP tests under `examples/fakeshop/tests/`; live HTTP tests under `examples/fakeshop/test_query/`); the live-HTTP-priority coverage rule; the no-pytest-after-edits rule; the settings-keys rule (add a settings key only when a feature needs it); the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" — Slice 5's doc-update step grants the explicit per-card permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical (Slice 4) and package-internal `tests/test_connection.py` where the path is unreachable from a live query.
- [`docs/TREE.md`][tree] — tests mirror source one-to-one; the connection field is the flat module [`django_strawberry_framework/connection.py`][connection], listed there under the on-disk package layout, with the flat test file [`tests/test_connection.py`][test-connection].
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, all defs at the bottom under the 10 canonical group headers); the "Strawberry is the engine; DRF is the shape" rule ([Decision 3](#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard) builds on Strawberry's relay, not a hand-rolled one); the "fork a subsystem into its own spec mid-stream when a slice grows past ~one module" advice ([Decision 14](#decision-14--connectionpy-module-and-the-public-export-gate)).

## Slice checklist

Each top-level item maps to one commit / PR. **Five slices: four sequential functional slices (1→2→3→4, each builds on the prior) plus a doc + card-completion wrap (5).** Boxes stay unticked because the `Status:` line is the completion source of truth (the shipped-spec convention).

- [ ] Slice 1: `DjangoConnection[T]` base + per-target concrete connection classes + `Meta.connection` validated and stored on the definition + the `first` + `last` guard (per [Decision 3](#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard) / [Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes) / [Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition))
  - [ ] Ship [`django_strawberry_framework/connection.py`][connection] with a generic `DjangoConnection[NodeType]` subclass of [`strawberry.relay.ListConnection`][strawberry-relay] that has **no** `totalCount` field and overrides `resolve_connection` to raise a `GraphQLError` when both `first` and `last` are supplied (the guard Strawberry's `SliceMetadata.from_arguments` does NOT provide), then dispatches the prepared source — an ordinary offset queryset delegates to `super().resolve_connection(...)`; a keyset-cursor source routes to the package's own slicer instead (per [Decision 9](#decision-9--cursor-encoding-delegated-to-strawberry-keyset-cursors-are-a-separate-opt-in)).
  - [ ] A cached factory `_connection_type_for(target_type)` that returns the connection class for a node type: always a generated concrete subclass of `DjangoConnection[target_type]` named `<TypeName>Connection` (e.g. `GenreTypeConnection`) from the node type's canonical GraphQL type name ([`Meta.name`][glossary-metaname] when set, else the Python `__name__`), declaring `total_count: int` and selection-gating + capturing the count when the type opts in, and adding nothing over the base when it does not. The schema is never handed the generic `DjangoConnection[target_type]` alias itself — Strawberry's generic specialization copies an alias into a plain specialized class whose `resolve_connection` is `ListConnection`'s, which would silently drop the `first` + `last` guard. Cache keyed on `target_type` (one connection shape per node type — no per-field override, per [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation), so no naming/caching ambiguity).
  - [ ] The `total_count` resolver reads a private instance attribute set by `resolve_connection`; the value is the **post-filter pre-slice** cardinality of `nodes`, captured **only when `totalCount` is in the selection set** (per [Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes)) and attached to the connection instance. An ordinary offset queryset is counted with sync `.count()` / async `.acount()` around the delegation to super; a prepared source that already carries its own count reads it from there rather than issuing a second query.
  - [ ] [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] grows `"connection"` (net-new public key — NOT a [`DEFERRED_META_KEYS`][base] promotion, mirroring [`spec-029`][spec-029] [Decision 6][spec-029]). A `_validate_connection` helper (called from [`_validate_meta`][base], structurally modeled on `_validate_filterset_class`) shape-checks the dict (`{"total_count": bool}` only; a non-dict value, an unknown sub-key, and a non-bool `total_count` each raise) and gates `Meta.connection` to a Relay-Node-shaped type via the `relay_shaped` bool ([`_is_relay_shaped`][base], computed once in [`_validate_meta`][base] from `cls` + the validated interfaces) — accepting both `relay.Node` in `Meta.interfaces` and direct `relay.Node` inheritance, the same single predicate the field guard uses. The normalized value is **stored on [`DjangoTypeDefinition`][definition]** (a `connection` slot) so the factory and the connection-class generator can read it (per [Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition)).
  - [ ] Package coverage: [`tests/test_connection.py`][test-connection] (the `DjangoConnection[T]` shape; the `first` + `last` `GraphQLError` guard; `<TypeName>Connection` generation + caching; `totalCount` present-only-when-opted-in and counted-only-when-selected). [`tests/types/test_base.py`][test-types-base] gains the `"connection"`-in-`ALLOWED_META_KEYS` / not-in-`DEFERRED_META_KEYS` assertion, the `_validate_connection` failure modes, and the `definition.connection` storage assertion.
- [ ] Slice 2: `DjangoConnectionField` factory + synthesized-signature argument injection + composition pipeline + consumer-resolver contract + optimizer cooperation point + sync/async (per [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation) / [Decision 6](#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature) / [Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer) / [Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point))
  - [ ] `DjangoConnectionField(target_type, *, resolver=None, description=None, deprecation_reason=None, directives=())` PascalCase factory (Meta-only derivation — no `filters=` / `order=` / `total_count=` kwargs, per [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation)) running the four [`DjangoListField`][glossary-djangolistfield]-style guards (`isclass` → `issubclass(DjangoType)` → own-class `definition.origin is target_type` → callable resolver) plus a Relay-Node-shaped guard that reuses the canonical `_is_relay_shaped(target_type, definition.interfaces)` predicate — accepting both the declared `Meta.interfaces` tuple and direct `relay.Node` inheritance (`class Foo(DjangoType, relay.Node)`), the same single definition the `Meta.connection` gate uses (per [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation)). A non-Relay target raises [`ConfigurationError`][glossary-configurationerror]. Returns `relay.connection(_connection_type_for(target_type), resolver=<synthesized>, description=…, …)`.
  - [ ] Build the field's resolver with a **synthesized `__signature__`** (and matching `__annotations__`) carrying `filter: filter_input_type(FS) | None = None` when the type declares [`Meta.filterset_class`][glossary-metafilterset_class] and `order_by: list[order_input_type(OS)] | None = None` when it declares [`Meta.orderset_class`][glossary-metaorderset_class], so Strawberry's native resolver-argument derivation emits the `filter:` / `orderBy:` arguments (the same shape the hand-written filter/order resolvers use); `ConnectionExtension` forwards these non-pagination kwargs to the resolver. Register the referenced FilterSet/OrderSet against the existing `_helper_referenced_filtersets` / `_helper_referenced_ordersets` ledgers so [`finalize_django_types`][glossary-finalize_django_types] orphan validation stays honest — calling `filter_input_type` / `order_input_type` to build the annotations IS the registration, so no separate `.add(...)` is wanted. Import both helpers **at call time** (inside the signature builder), never at module scope: [`connection.py`][connection] is reached by a bare `import django_strawberry_framework` through [`__init__.py`][package-init], so a module-level import would eagerly pull in the `filters` / `orders` subpackages and break the lazy-subpackage contract. The `search:` argument is NOT generated (search is `0.1.2`).
  - [ ] The resolver runs the composition pipeline: build the base queryset (default [`utils/querysets.py::initial_queryset`][querysets] or the consumer `resolver=` return with the [Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer) `Manager` / `QuerySet` / unsliced / iterable contract) → `target_type.get_queryset(qs, info)` (visibility) → `FilterSet.apply_*` (if `filter` given) → `OrderSet.apply_*` (if `order_by` given) → **deterministic total ordering** (append the pk as a terminal tiebreaker — resolving the effective ordering from `qs.query.order_by` or `model._meta.ordering` — so the cursors index a unique total order in ALL cases, unless the ordering already ends in a unique non-nullable column; a supplied `orderBy` / model `Meta.ordering` is preserved with the pk appended) → **apply the optimizer plan helper** → return the queryset. `ConnectionExtension` then slices it. Sync and async paths mirror [`DjangoListField`][glossary-djangolistfield], reusing [`utils/querysets.py`][querysets]'s `apply_type_visibility_sync` / `apply_type_visibility_async` and `apply_sync` / `apply_async`; a sync context meeting an async `get_queryset` raises [`SyncMisuseError`][glossary-syncmisuseerror].
  - [ ] The plan-application logic lives in a reusable core on the optimizer extension, [`DjangoOptimizerExtension.apply_to`][optimizer-extension], which takes `target_type` / `target_model` directly rather than inferring them from `info.return_type`; the middleware's `_optimize` resolves the return type and delegates to it, so both paths share one plan-application implementation. The connection field calls it through [`optimizer/extension.py::apply_connection_optimization`][optimizer-extension] before slicing (per [Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point)). The middleware path stays behavior-identical for non-connection fields.
  - [ ] Package coverage: [`tests/test_connection.py`][test-connection] extends — constructor guards; argument presence/absence by sidecar declaration; the four consumer-resolver cases (`Manager` coercion, `QuerySet` pipeline, iterable-without-sidecar-input, iterable-with-sidecar-input error); deterministic total ordering (unordered → pk order; supplied non-unique `orderBy` → `orderBy, pk`; `Meta.ordering` over a non-unique column preserved + pk appended, NOT clobbered to pk-only; an already-unique terminal left alone — [`optimizer/plans.py::ends_in_unique_column`][optimizer-plans], re-exported into [`connection.py`][connection] as `_ends_in_unique_column`); composition order (visibility before filter before order before total-order before plan before slice); sync + async dispatch; `SyncMisuseError` on async-`get_queryset`-in-sync.
- [ ] Slice 3: verify optimizer cooperation; bound the connection-aware-planning gap (per [Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point))
  - [ ] Tests that a root `DjangoConnectionField`'s pre-slice queryset is run through the extracted helper — the cooperation point the field owns, NOT the middleware: the field publishes an [`OptimizationPlan`][glossary-djangooptimizerextension] to `info.context` before the slice (which the schema middleware never does for a connection field, since it cannot reach the queryset behind `ConnectionExtension`). The plan is derived from the **node-level** selections, because [`apply_connection_optimization`][optimizer-extension] defaults its `selection_extractor` to the `edges { node { ... } }` navigator, so the walker receives the same child-selection list a [`DjangoListField`][glossary-djangolistfield] over that node type would: a root connection plans `select_related` for a selected to-one relation, `prefetch_related` for a selected many-side relation, and the [`only()`][glossary-only-projection] projection for the selected scalars. The plan is applied only when a [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] is installed for the execution and `target_type` has a registered model (per [Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point)).
  - [ ] Name the planning boundary this card does NOT cross: a **nested** `<field>Connection` reached under `edges { node { relConnection { ... } } }` is window-planned by the sibling [`DONE-033-0.0.9`][kanban] card, which plugs into this card's cooperation point (a walker change, not a field retrofit) and owns its own fallback shapes. No silent cap — the ownership split is named in [`docs/GLOSSARY.md`][glossary] and [Edge cases and constraints](#edge-cases-and-constraints).
  - [ ] Package coverage: a [Strictness mode][glossary-strictness-mode] `"raise"` assertion that a genuinely unplanned relation access reached through a connection's `edges { node }` response path still surfaces as an N+1 (the connection response shape does not blind the strictness detector); a no-regression check that the existing B1–B8 optimizer suite is unaffected by the `_optimize` helper extraction.
- [ ] Slice 4: live HTTP coverage on a Relay-Node-shaped fakeshop type + public-export promotion (per [Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer) / [Decision 14](#decision-14--connectionpy-module-and-the-public-export-gate) / the card DoD)
  - [ ] Promote `DjangoConnectionField` / `DjangoConnection` to the [`django_strawberry_framework/__init__.py`][package-init] public surface **in this slice**, alongside the live usage that proves the public shape (per [Decision 14](#decision-14--connectionpy-module-and-the-public-export-gate)).
  - [ ] Add a root `DjangoConnectionField` over the [`library`][fakeshop-library-schema] `GenreType` (already Relay-Node-shaped with both [`Meta.filterset_class`][glossary-metafilterset_class] and [`Meta.orderset_class`][glossary-metaorderset_class] declared) with `Meta.connection = {"total_count": True}`, exposed on the `library` `Query` via [`DjangoConnectionField(GenreType)`][connection], imported from the public surface.
  - [ ] Live HTTP tests in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]: (a) a full round-trip requesting `edges { node { id name } } pageInfo { hasNextPage endCursor } totalCount` with `filter:` + `orderBy:` + `first:` + `after:` asserting correct pagination, ordering, and `totalCount` on the unpaginated post-filter set; (b) the `first` + `last` `GraphQLError` path; (c) a `first: 0` empty-edges + `pageInfo` shape; (d) a query that omits `totalCount` and asserts the response is correct with no count query issued, plus the directive-excluded spelling of the same gate (`@skip` / `@include` on the field or its fragment wrapper) with a keep-resolving control (the selection-gating contract); (e) two aliases of the connection with different `filter:` values asserting independent `totalCount`s (the per-instance-count contract).
- [ ] Slice 5: doc updates + card-completion wrap (grants the per-card [`CHANGELOG.md`][changelog] edit permission)
  - [ ] [`docs/GLOSSARY.md`][glossary]: flip [`DjangoConnectionField`][glossary-djangoconnectionfield], [`DjangoConnection`][glossary-djangoconnection], and [`Meta.connection`][glossary-metaconnection] from `planned for 0.0.9` to `shipped (0.0.9)` in the [Index][glossary-index] table and entry bodies; confirm `Meta.connection` describes the `{"total_count": bool}` shape and the Relay-Node requirement and remains present in the Index plus the "Relay" / "Type generation" [Browse by category][glossary] rows. Do not touch the [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] entry — its status is [`DONE-033-0.0.9`][kanban]'s to set.
  - [ ] [`docs/README.md`][docs-readme]: move `DjangoConnectionField` from the "coming next" `0.0.9` line to the shipped surface list; note the sidecar-derived `filter:` / `orderBy:` arguments and opt-in `totalCount`.
  - [ ] [`docs/TREE.md`][tree]: list [`connection.py`][connection] under the current on-disk package layout (drop its `[alpha]` planned tag) and the mirrored [`tests/test_connection.py`][test-connection].
  - [ ] [`TODAY.md`][today]: update the products "still waiting for" list — `DjangoConnectionField` moves from waiting to shipped (or note products' Relay-connection activation tracking, lit up at fakeshop activation per [`TODO-BETA-061-0.1.5`][kanban]); keep the file products-centric.
  - [ ] [`README.md`][readme]: update the status paragraph's newest-shipped-surface line if it enumerates the connection field (include only if reflected there).
  - [ ] [`CHANGELOG.md`][changelog]: `### Added` bullets for `DjangoConnectionField` / `DjangoConnection` / `Meta.connection`. **This is the per-card CHANGELOG-edit permission grant** ([`AGENTS.md`][agents] withholds it by default); the Slice 5 maintainer prompt must name this edit explicitly. This card contributes bullets only and promotes no release heading — the heading they ship under belongs to the joint `0.0.9` cut (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).
  - [ ] [`KANBAN.md`][kanban]: move this card to the Done column, where it is [`DONE-030-0.0.9`][kanban] (the column-move pass assigns the next available id); add / confirm the card body's spec reference points at [`docs/SPECS/spec-030-connection_field-0_0_9.md`][spec-030] (this document).
  - [ ] **No version-file edits in this card.** Leave `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` to the joint `0.0.9` cut per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut).

## Problem statement

`django-strawberry-framework`'s `0.0.8` surface ships [`DjangoType`][glossary-djangotype], the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], the [`FilterSet`][glossary-filterset] and [`OrderSet`][glossary-orderset] subsystems, [Relay Node integration][glossary-relay-node-integration] (`Meta.interfaces = (relay.Node,)` with injected `resolve_*` defaults), and the non-Relay [`DjangoListField`][glossary-djangolistfield]. What it does **not** ship is a Relay-shaped **connection field**. Today a consumer who wants paginated, cursor-based access to a model collection has only two options: a non-Relay [`DjangoListField`][glossary-djangolistfield] (no `edges` / `pageInfo` / `totalCount`, no pagination), or a hand-written `@strawberry.field` resolver that constructs a `relay.ListConnection` by hand AND re-wires the `filter:` / `orderBy:` arguments from the type's sidecars by hand. The second is exactly the boilerplate this package exists to eliminate.

Both upstreams ship this primitive. `graphene-django` (via `django-graphene-filters`) ships `AdvancedDjangoFilterConnectionField` — one declaration (`all_object_types = AdvancedDjangoFilterConnectionField(ObjectTypeNode)`) exposes the type's declared filter / order sidecars as connection arguments plus Relay pagination. `strawberry-graphql-django` ships `strawberry_django.connection()` over a `ListConnectionWithTotalCount` (a concrete `relay.ListConnection` subclass per node shape). This card is the package's Strawberry-native, `class Meta`-driven equivalent: `all_genres: DjangoConnection[GenreType] = DjangoConnectionField(GenreType)` reads the per-type [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] declarations and generates the `filter:` / `orderBy:` arguments identically, with cursor pagination and an opt-in `totalCount` on top — no hand-written list resolver, no parallel argument declarations.

It is the **central read-side primitive**. The card body and the sibling [`DONE-032-0.0.9`][kanban] (Full Relay story) both name it: every Layer-3 argument composes through this field. Filtering and ordering shipped in `0.0.8` and are consumed on day one; field-selection ([`FieldSet`][glossary-fieldset], `0.1.1`), search ([`Meta.search_fields`][glossary-metasearch_fields], `0.1.2`), and aggregation ([`AggregateSet`][glossary-aggregateset], `0.1.3`) layer on after the connection field ships. The [Full Relay story][kanban] depends on this card; [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] ships in parallel. Getting the field's seams right — the composition pipeline, the sidecar-argument injection, the **optimizer cooperation point** (which cannot ride the existing middleware because Strawberry's connection slicing hides the queryset), the per-shape connection type, and the finalizer-trigger posture — is therefore load-bearing for the entire `0.0.9` Relay cohort and everything Layer-3 after it.

## Current state

A true description of the repo as of this writing (the plan is written against it), verified against the locked Strawberry `0.316.0`:

- There is **no** `connection.py` on disk. [`docs/TREE.md`][tree]'s target package layout reserves a `connection.py [alpha]` slot. The public surface ([`django_strawberry_framework/__init__.py`][package-init]) exports `DjangoType`, `DjangoListField`, `DjangoOptimizerExtension`, `OptimizerHint`, `BigInt`, `SyncMisuseError`, `finalize_django_types`, `strawberry_config`, `auto`, `__version__` — neither `DjangoConnectionField` nor `DjangoConnection` yet.
- [`django_strawberry_framework/list_field.py`][list-field] is the closest analogue: a PascalCase factory `DjangoListField(target_type, *, resolver=…, …)` returning `strawberry.field(resolver=wrapped, …)`, with four constructor guards and a default resolver that branches on `in_async_context()` to dispatch `_apply_get_queryset_sync` vs `_apply_get_queryset_async`. Its consumer-resolver post-processing (`_post_process_consumer_sync` / `_async`) coerces a `Manager` to a `QuerySet`, applies `get_queryset` to a `QuerySet`, and passes a Python list/generator through unchanged — the contract [Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer) extends.
- [`django_strawberry_framework/types/relay.py`][relay] ships the `0.0.5` Relay foundation: `_apply_get_queryset_sync` / `_apply_get_queryset_async`, `_initial_queryset` (returns `model._default_manager.all()` — **unordered** for a model without `Meta.ordering`, which is why [Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer) adds a default-ordering step), the [`SyncMisuseError`][glossary-syncmisuseerror] marker, and the four injected `resolve_*` defaults.
- The [`FilterSet`][glossary-filterset] subsystem exposes `FilterSet.apply_sync(input_value, queryset, info)` / `apply_async(...)` and the [`filter_input_type`][glossary-filter_input_type] helper, which returns `Annotated["<Name>FilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` and records the FilterSet against `_helper_referenced_filtersets`. The [`OrderSet`][glossary-orderset] subsystem mirrors this (`apply_sync` / `apply_async`, [`order_input_type`][glossary-order_input_type], `_helper_referenced_ordersets`). These helpers **return annotations and write ledgers — they do not add arguments to a field by themselves**, which is why [Decision 6](#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature) pins an explicit injection mechanism.
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]'s `DjangoOptimizerExtension.resolve` gates on `info.path.prev is None` and then calls `_optimize` only when the resolved value is a Django `QuerySet`. **Strawberry's [`relay.connection()`][strawberry-relay] installs `ConnectionExtension`, whose `resolve` calls the inner resolver, then immediately `connection_type.resolve_connection(...)` and returns a connection object** — so the schema middleware sees the post-connection result, not the pre-slice queryset, and cannot optimize it. This is the root cause [Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point) fixes by extracting a reusable plan helper and calling it from the connection field itself.
- `strawberry.relay.connection(graphql_type=None, *, resolver=None, extensions=None, …)` accepts an `extensions: list[FieldExtension]` argument and appends `ConnectionExtension` itself. `ConnectionExtension.resolve(self, next_, source, info, *, before, after, first, last, **kwargs)` consumes the four pagination args as keyword-only and forwards the remaining `**kwargs` (i.e. `filter` / `order_by`) to the inner resolver. `strawberry.relay.types.SliceMetadata.from_arguments` applies `first` then `last` and validates negatives / `max_results` but **does NOT reject `first` + `last` together** — the mutual-exclusivity guard [Decision 3](#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard) requires must be implemented by this package. `ListConnection.resolve_connection(cls, nodes, *, info, before, after, first, last, max_results, **kwargs)` receives the pagination args, so an override is the right home for both the guard and the `totalCount` capture.
- [`django_strawberry_framework/types/base.py`][base] holds `ALLOWED_META_KEYS` = `{"description", "exclude", "fields", "filterset_class", "interfaces", "model", "name", "nullable_overrides", "optimizer_hints", "orderset_class", "primary", "required_overrides"}` and `DEFERRED_META_KEYS` = `{"aggregate_class", "fields_class", "search_fields"}`. `"connection"` is in neither; declaring it today raises [`ConfigurationError`][glossary-configurationerror] via the unknown-key typo guard. `_validate_filterset_class` / `_validate_orderset_class` are the structural template for `_validate_connection`.
- [`django_strawberry_framework/types/definition.py`][definition]'s [`DjangoTypeDefinition`][definition] carries the per-type metadata (`selected_fields`, `field_map`, `filterset_class` / `orderset_class` slots, `finalized`). It has **no** `connection` slot yet; [Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition) adds one so the factory and connection-class generator read the opt-in from the definition, not by re-parsing `Meta`.
- The [`library`][fakeshop-library-schema] app already hosts a Relay-Node-shaped type with both sidecars: `GenreType` declares `Meta.interfaces = (relay.Node,)`, `filterset_class = filters_genre.GenreFilter`, and `orderset_class = orders_genre.GenreOrder`. It is the natural live-HTTP host for Slice 4 — no new model or migration is needed. [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] already constructs its schema with the [`spec-029`][spec-029] singleton-factory `extensions=[lambda: _optimizer]` form and a [`strawberry_config()`][glossary-strawberry_config] call.
- [`docs/GLOSSARY.md`][glossary] already has `## DjangoConnectionField`, `## DjangoConnection`, `## Meta.connection`, and `## Connection-aware optimizer planning` headings (all `planned for 0.0.9`). Slice 5 flips the first three to `shipped (0.0.9)`; the connection-aware entry is the sibling [`DONE-033-0.0.9`][kanban] card's to set.

## Goals

1. Ship [`DjangoConnectionField`][glossary-djangoconnectionfield] — a Relay-style connection field over a Relay-Node-shaped [`DjangoType`][glossary-djangotype] with `edges` / `node` / `pageInfo` / `totalCount`, `first` / `after` / `last` / `before` cursor pagination (with a package-owned `first` + `last` guard), and `filter:` / `orderBy:` arguments injected from the wrapped type's [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] via the resolver signature — with no hand-written list resolver and no parallel argument declarations (Slices 1–2).
2. Ship the [`DjangoConnection`][glossary-djangoconnection]`[T]` base plus per-target concrete connection classes that carry the opt-in `totalCount` (counted only when selected, attached to the connection instance), gated by the net-new `Meta.connection = {"total_count": True}` key stored on [`DjangoTypeDefinition`][definition] (Slice 1).
3. Pin the composition pipeline — [`get_queryset`][glossary-get_queryset-visibility-hook] (visibility) → `filter` → `orderBy` → deterministic total ordering (terminal pk tiebreaker) → optimizer plan → cursor slice — and the consumer-`resolver=` contract, so pagination is deterministic over a unique total order (the positional offset cursors are stable across requests even for a non-unique `orderBy` / `Meta.ordering`) and `totalCount` counts the unpaginated post-filter set (Slice 2, [Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)).
4. Make the connection field own an optimizer cooperation point: extract the plan-application logic from [`DjangoOptimizerExtension._optimize`][optimizer-extension] into a reusable helper taking `target_type` / `target_model` directly, and call it from the connection resolver before slicing — because the schema middleware cannot see the queryset behind Strawberry's connection result. Name nested-`<field>Connection` window planning as the sibling [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] card's job (Slices 2–3, [Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point)).
5. Earn package coverage through a live fakeshop HTTP round-trip on the Relay-Node-shaped `GenreType` (filter + orderBy + cursor + totalCount, selection-gating, two-alias counts), per [`docs/TREE.md`][tree]'s coverage-priority rule (Slice 4).
6. Keep package version state command-gated and owned by the joint `0.0.9` cut: no slice edits `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock` (Slice 5, [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).

## Non-goals

- **Root `node(id:)` / `nodes(ids:)` refetch fields, the relation-as-Connection implicit upgrade, and the `DjangoNodesField` export.** Those are the [Full Relay story][kanban] ([`DONE-032-0.0.9`][kanban]), which depends on this card. This card ships the connection **field** only; [`DjangoNodeField`][glossary-djangonodefield] and the Root-Node entry points land with `032` (see [Decision 2](#decision-2--card-scope-boundary-against-the-sibling-relay-cards)).
- **Connection-aware optimizer planning.** Teaching the walker to recognize a **nested** `<field>Connection` inside a parent's selection walk and plan windowed `Prefetch` chains across connection-paginated relations is the sibling [`DONE-033-0.0.9`][kanban] card. This card wires the cooperation point and derives the root connection's own plan through it; `033` makes the walker connection-aware ([Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point)).
- **Django-model-based GlobalID encoding.** The GlobalID payload format is the sibling [`DONE-031-0.0.9`][kanban] card; orthogonal to cursor pagination.
- **`search:` connection argument.** [`Meta.search_fields`][glossary-metasearch_fields] is `0.1.2`; the connection field reserves the seam but generates no `search:` argument in `0.0.9`.
- **`aggregates` connection argument and `Meta.aggregate_class` composition.** [`AggregateSet`][glossary-aggregateset] is `0.1.3`; out of scope.
- **`Meta.fields_class` / `FieldSet` field-selection composition.** [`FieldSet`][glossary-fieldset] is `0.1.1`; field-selection layers onto the connection field after this card.
- **`filters=` / `order=` / `total_count=` per-field constructor overrides.** Dropped for `0.0.9` — the field derives everything from `Meta`, which keeps one connection shape per node type ([Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation)).
- **`Meta.cursor_field` value-encoded (keyset) cursors.** This card's cursor shape is Strawberry's opaque offset cursor ([Decision 9](#decision-9--cursor-encoding-delegated-to-strawberry-keyset-cursors-are-a-separate-opt-in)); the keyset codec, its seek planning, and the `Meta.cursor_field` key itself belong to [`django_strawberry_framework/keyset.py`][keyset], which this card's connection base only dispatches to.
- **`Meta.relation_shapes` (list-vs-connection opt-out on relations).** That governs the relation-as-Connection upgrade, which is [`DONE-032-0.0.9`][kanban].
- **Auto-triggering `finalize_django_types()` from the field constructor.** Deferred ([Decision 12](#decision-12--no-auto-trigger-of-finalize_django_types-for-009)).
- **A version bump.** Owned by the joint `0.0.9` cut ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).

## Borrowing posture

This card ports a primitive both upstreams ship, so the borrowing posture is explicit per the [`START.md`][start] "do both libraries provide it? → foundational" test: yes, both do, so this is foundational, not optional.

### Reference-package parity checkpoint

The card advances the larger effort to rebuild the released [`django_graphene_filters`][upstream-cookbook] feature set on the Strawberry foundation. It ports the cookbook's central read-side surface:

| `django_graphene_filters` (Graphene) | `django-strawberry-framework` (Strawberry) | Status |
| --- | --- | --- |
| `AdvancedDjangoObjectType` | [`DjangoType`][glossary-djangotype] (`class Meta` sidecars) | shipped |
| `AdvancedFilterSet` / `RelatedFilter` | [`FilterSet`][glossary-filterset] / [`RelatedFilter`][glossary-relatedfilter] | shipped (`0.0.8`) |
| `AdvancedOrderSet` / `RelatedOrder` | [`OrderSet`][glossary-orderset] / [`RelatedOrder`][glossary-relatedorder] | shipped (`0.0.8`) |
| **`AdvancedDjangoFilterConnectionField`** | **[`DjangoConnectionField`][glossary-djangoconnectionfield] / [`DjangoConnection`][glossary-djangoconnection]** | **this card (`0.0.9`)** |
| (Relay Root `node` / `nodes`) | [`DjangoNodeField`][glossary-djangonodefield] / Full Relay | sibling card (`0.0.9` — [`DONE-032-0.0.9`][kanban]) |
| (connection-aware optimization) | [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] | sibling card (`0.0.9` — [`DONE-033-0.0.9`][kanban]) |
| `AdvancedFieldSet` | [`FieldSet`][glossary-fieldset] | planned (`0.1.1`) |
| `AdvancedAggregateSet` / `RelatedAggregate` | [`AggregateSet`][glossary-aggregateset] / [`RelatedAggregate`][glossary-relatedaggregate] | planned (`0.1.3`) |
| `apply_cascade_permissions` | [`apply_cascade_permissions`][glossary-apply_cascade_permissions] | shipped (`0.0.10`) |

### From `django-graphene-filters` — borrow the user-facing shape

`AdvancedDjangoFilterConnectionField(ObjectTypeNode)` is the surface to recreate: one declaration over a node type, with the type's declared filter / order sidecars driving argument generation. The Strawberry side is `DjangoConnectionField(GenreType)` returning `DjangoConnection[GenreType]`; the per-type [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] declarations drive `filter:` / `orderBy:` argument generation identically. The Meta-driven argument derivation is the load-bearing borrow — it is what makes the connection field *consume* the sidecars rather than ask the consumer to re-declare them.

### From `strawberry-graphql-django` — borrow the runtime mechanism

`strawberry_django.connection()` builds on Strawberry's native `relay.connection()` over `ListConnectionWithTotalCount` (a concrete `relay.ListConnection` subclass per node shape that adds `total_count` and overrides `resolve_connection`). This card borrows that mechanism wholesale ([Decision 3](#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard) / [Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes)): Strawberry owns cursor encoding, `pageInfo`, and edge mechanics; the package supplies a Django-aware resolver pipeline (visibility→filter→order→default-order→optimizer) before handing the queryset to `ConnectionExtension`, plus the per-shape concrete connection class and the `first` + `last` guard Strawberry omits. We do NOT hand-roll cursor math.

### From `graphene-django` — borrow nothing new

`graphene-django`'s own `DjangoConnectionField` predates the filter-connection composition; the `django-graphene-filters` `AdvancedDjangoFilterConnectionField` is the richer surface and the one we mirror.

### Explicitly do not borrow

- **Graphene's connection internals.** Cursor math, `PageInfo` construction, and edge wrapping come from Strawberry.
- **A bespoke cursor scheme.** Cursor encoding is Strawberry's on the offset path and [`keyset.py`][keyset]'s on the `Meta.cursor_field` path; this card writes neither ([Decision 9](#decision-9--cursor-encoding-delegated-to-strawberry-keyset-cursors-are-a-separate-opt-in)).
- **strawberry-django's connection-aware optimizer extension here.** That behavior is the sibling [`DONE-033-0.0.9`][kanban] card; this card wires the cooperation point but does not pull the connection-aware walker forward.

## User-facing API

### Declaring a connection field

```python
import strawberry
from strawberry import relay

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoType,
    finalize_django_types,
)

from . import filters, models, orders


class GenreType(DjangoType):
    class Meta:
        model = models.Genre
        fields = ("id", "name", "books")
        interfaces = (relay.Node,)                 # required — a connection is over a Node type
        filterset_class = filters.GenreFilter      # drives the `filter:` argument
        orderset_class = orders.GenreOrder         # drives the `orderBy:` argument
        connection = {"total_count": True}         # opt-in `totalCount`


@strawberry.type
class Query:
    # One declaration. `filter:` / `orderBy:` / `first` / `after` / `last` / `before` /
    # `totalCount` are generated from the type's sidecars and Relay machinery.
    all_genres: DjangoConnection[GenreType] = DjangoConnectionField(GenreType)


finalize_django_types()
```

The generated GraphQL field:

```graphql
allGenres(
  filter: GenreFilterInputType
  orderBy: [GenreOrderInputType!]
  first: Int
  after: String
  last: Int
  before: String
): GenreTypeConnection!
```

`GenreTypeConnection` carries `edges { node cursor }`, `pageInfo { hasNextPage hasPreviousPage startCursor endCursor }`, and (because `Meta.connection = {"total_count": True}`) `totalCount: Int!`. The annotation `DjangoConnection[GenreType]` documents the node type; the factory resolves the actual field type to the generated concrete `GenreTypeConnection`, whose shape — `totalCount` present or absent — comes from the type's stored `Meta.connection` ([Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes)).

### Wiring — sidecar-driven argument generation

The connection field reads the wrapped type's [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] at construction time and synthesizes a resolver whose signature carries `filter` / `order_by` parameters ([Decision 6](#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature)):

- type declares both → `filter:` AND `orderBy:` arguments present.
- type declares only `filterset_class` → only `filter:` present.
- type declares neither → only the Relay pagination arguments (`first` / `after` / `last` / `before`).

The `filter:` argument type is the same [`filter_input_type`][glossary-filter_input_type]-derived lazy `Annotated[...]` a hand-written resolver would use; the `orderBy:` argument is `list[order_input_type(...)]`. Two connection fields on the same model resolve to the same `<Type>FilterInputType` / `<Type>OrderInputType` (stable class-derived names — Apollo-cache friendly).

### Opt-in `totalCount` (per type)

```python
class GenreType(DjangoType):
    class Meta:
        model = models.Genre
        interfaces = (relay.Node,)
        connection = {"total_count": True}   # adds `totalCount: Int!` to GenreTypeConnection
```

`totalCount` is opt-in **per type** (not per field) so a node type has exactly one connection shape. When selected by a query, the value is the cardinality of the **unpaginated post-filter** queryset, attached to the connection instance: an ordinary offset queryset is counted with `qs.count()` (sync) / `qs.acount()` (async), and a prepared source that already carries its own count is read from there rather than re-counted. When the query omits `totalCount`, no count query runs ([Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes)).

### Composing with `get_queryset`, filter, and order

The field's resolver runs the pipeline so a consumer needs no manual chaining (contrast the hand-written `@strawberry.field` form documented for the filter / order subsystems):

```text
qs = GenreType.get_queryset(Genre.objects.all(), info)   # 1. visibility (first, always)
qs = GenreFilter.apply_sync(filter, qs, info)            # 2. filter (active-input gates)   — if filter given
qs = GenreOrder.apply_sync(order_by, qs, info)           # 3. orderBy (per-field gates)     — if orderBy given
qs = qs.order_by(*effective_ordering, pk)                # 4. deterministic TOTAL order (append pk tiebreaker unless terminal already unique)
qs = apply_connection_optimization(GenreType, qs, info)  # 5. optimizer plan (the field's own cooperation point)
# 6. ConnectionExtension slices `qs` by the cursor args; totalCount (if selected) = qs.count() pre-slice.
```

### Consumer `resolver=` contract

`DjangoConnectionField(GenreType, resolver=my_resolver)` is an escape hatch. Its return is contracted ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)):

- a `Manager` → coerced to `QuerySet`, then the full pipeline;
- an **unsliced** `QuerySet` → the full pipeline (visibility / filter / order / default-order / optimizer / pagination);
- an **already-sliced** `QuerySet` (`Genre.objects.all()[:5]`) → a clear `GraphQLError`. The field owns ordering and cursor pagination, and Django forbids reordering or re-slicing a sliced query, so a pre-sliced source cannot be paginated at all;
- a non-queryset iterable (list / generator) → paginated only when **no** `filter:` / `orderBy:` input is supplied; supplying sidecar input against a non-queryset raises a clear `GraphQLError`.

### Error shapes

- `DjangoConnectionField(NotADjangoType)` / `DjangoConnectionField(int)` → [`ConfigurationError`][glossary-configurationerror] at the construction site (mirrors [`DjangoListField`][glossary-djangolistfield]'s guard messages).
- `DjangoConnectionField(PlainType)` where `PlainType` is not Relay-Node-shaped (no `relay.Node` in `Meta.interfaces` and no direct `relay.Node` inheritance) → [`ConfigurationError`][glossary-configurationerror] ("a connection field requires a Relay-Node-shaped DjangoType; add `relay.Node` to `Meta.interfaces` or inherit `relay.Node` directly").
- `Meta.connection` declared on a non-Relay-Node type (no `relay.Node` in `Meta.interfaces` and no direct `relay.Node` inheritance), a non-dict value, an unknown sub-key, or a non-bool `total_count` → [`ConfigurationError`][glossary-configurationerror] at type creation (the four `_validate_connection` rejections, [Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition)).
- A query passing both `first:` and `last:` → `GraphQLError` raised by the connection class's `resolve_connection` override (the package's own guard — Strawberry does not provide it), surfaced in the GraphQL `errors` array.
- Sidecar input supplied against a consumer resolver that returned a non-queryset iterable → `GraphQLError`.
- A consumer resolver that returned an already-sliced `QuerySet` → `GraphQLError`, raised whether or not `filter:` / `orderBy:` was supplied (the connection reorders and slices on every request). The guard converts what would otherwise leak as Django's raw `TypeError: Cannot reorder a query once a slice has been taken` into a package error naming the cause and the fix ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)).
- `totalCount` selected against a consumer resolver that returned a non-queryset iterable (on a `total_count`-opted-in type) → `GraphQLError` (a non-queryset cannot be `.count()`-ed into the non-null `totalCount: Int!` field; the count helper raises a clear package error rather than letting the field return `null` and triggering the engine's `Cannot return null for non-nullable field …totalCount` violation). Symmetric with the sidecar-input rule above ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec's canonical name is the structured filename **`spec-030-connection_field-0_0_9.md`** (`spec-<NNN>-<topic>-<0_0_X>`), NOT the unnumbered `docs/spec-connection.md` the [`DONE-030-0.0.9`][kanban] card's Definition-of-done item names. This document is that file: [`docs/SPECS/spec-030-connection_field-0_0_9.md`][spec-030], with its `-terms.csv` and `-rationale.md` companions under `docs/SPECS/appx/`, per [`AGENTS.md`][agents]'s spec-archival convention.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 1][rationale-d1].

### Decision 2 — Card-scope boundary against the sibling Relay cards

`0.0.9` carries four Relay cards. This card ships **only the connection field**; the boundary is explicit:

- **`DONE-030-0.0.9` (this card)** — `DjangoConnectionField` + `DjangoConnection[T]` + the sidecar-derived arguments + opt-in `totalCount`, with the field owning its optimizer cooperation point.
- **`DONE-031-0.0.9`** — Django-model-based GlobalID encoding. Orthogonal.
- **`DONE-032-0.0.9`** — Full Relay story: Root `node(id:)` / `nodes(ids:)`, the relation-as-Connection upgrade, `DjangoNodeField` / `DjangoNodesField`, schema-validation diagnostics, fakeshop activation. **Depends on this card.**
- **`DONE-033-0.0.9`** — connection-aware optimizer planning: walker recognition and windowed planning of **nested** `<field>Connection` selections. Plugs into this card's cooperation point.

Rationale companion — this Decision's justification and its one rejected alternative: [Decision 2][rationale-d2].

### Decision 3 — Build on Strawberry's native Relay machinery, but own the `first` + `last` guard

The connection field is implemented on top of [`strawberry.relay`][strawberry-relay]'s `connection()` / `ListConnection` / `Edge` / `PageInfo` — Strawberry owns cursor encoding/decoding (`to_base64` / `from_base64`), `ListConnection.resolve_connection`, the `pageInfo` semantics, and the `first` / `last` slice-window math in `SliceMetadata.from_arguments`.

**But Strawberry `0.316.0` does NOT reject `first` + `last` together.** `SliceMetadata.from_arguments` applies `first`, then `last`, producing a combined window; it validates negatives and `max_results` but never mutual exclusivity (verified against the locked source). The card body wants `first` + `last` to be illegal ("rejected as a typed error"). Therefore **the package implements that guard itself**, in the [`DjangoConnection`][glossary-djangoconnection] base class's `resolve_connection` override (which receives `before` / `after` / `first` / `last`): when both `first` and `last` are **supplied** — non-`None` and not `strawberry.UNSET`, since an omitted Relay argument reaches the override as either — raise a `GraphQLError` (a query-runtime error that lands in the response `errors` array — NOT a [`ConfigurationError`][glossary-configurationerror], which is construction-time). The guard runs first in the override, before anything reads `info`, so a malformed pagination request answers with this error rather than with whichever later bound fires; a well-formed request goes on to the override's source dispatch ([Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes) / [Decision 9](#decision-9--cursor-encoding-delegated-to-strawberry-keyset-cursors-are-a-separate-opt-in)), whose ordinary offset path is `super().resolve_connection(...)`.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 3][rationale-d3].

### Decision 4 — `DjangoConnection[T]` base plus per-target concrete connection classes

A static Strawberry class cannot make one field appear or disappear per generic specialization, so a single generic `DjangoConnection[T]` with a conditional `totalCount` is impossible. The design is therefore two-tier:

- **`DjangoConnection[NodeType]`** — a generic [`strawberry.relay.ListConnection`][strawberry-relay]`[NodeType]` subclass with **no** `total_count` field. It owns the single `resolve_connection` override: the [Decision 3](#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard) `first` + `last` guard, then the dispatch of the prepared source, whose ordinary-offset path delegates to super. It is a base, never the field's own type — see below.
- **A per-target concrete class** `<TypeName>Connection` (e.g. `GenreTypeConnection`), generated and **cached** by a `_connection_type_for(target_type)` factory. Every node type gets one; it subclasses `DjangoConnection[target_type]` and is named from the node type's canonical GraphQL type name ([`Meta.name`][glossary-metaname] when set, else the Python `__name__`, so two `DjangoType` classes sharing a Python `__name__` cannot generate two connections with one SDL name). The `totalCount` opt-in controls only the **shape**: an opted-in type's class declares `total_count: int` and flips a class flag the inherited `resolve_connection` reads, so it (a) keeps the `first` + `last` guard, (b) **counts only when `totalCount` is selected** in the query — selection is **directive-resolved**, so a `@skip(if: true)` / `@include(if: false)` on the field, or on the fragment wrapping it, suppresses the count exactly as omitting the field does, (c) takes the **post-filter pre-slice** cardinality of `nodes` (sync `.count()` / async `.acount()` for an ordinary offset queryset; a prepared source carrying its own count is read rather than re-counted), (d) attaches the count to the connection **instance** (a private attribute the `total_count` field resolver reads), (e) delegates the ordinary offset slice to super. A type that does not opt in gets the same generated class with none of those members added, inheriting the base's SDL description.

The flag is class **data**, not a second `resolve_connection` override: the upstream-pinned signature and the whole dispatch body are spelled exactly once, so the opted variant cannot drift from the base or from `ListConnection`.

**The field is never given the generic `DjangoConnection[target_type]` alias**, even for a type that skips `totalCount`. Strawberry's schema-build generic specialization copies an alias into a plain specialized class whose `resolve_connection` is `ListConnection`'s, which drops this package's override — and with it the `first` + `last` guard — for every through-schema query. A concrete class is used as-is, so the override survives.

Because the `totalCount` option is strictly **per type** (no per-field override, [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation)), a node type has exactly one connection shape, so the generated `<TypeName>Connection` name is unique and the cache is keyed on `target_type` alone — no naming/caching ambiguity.

The captured count lives on the connection instance, **not** an `info.context` path-string stash: a connection result is already a per-field, per-alias object, so two aliases of the same connection with different `filter:` values carry independent counts without any keying logic.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 4][rationale-d4].

### Decision 5 — Factory-function mechanism, Meta-only derivation

`DjangoConnectionField` is a **factory function** (PascalCase for graphene-django parity), not a class, with Meta-only derivation:

```python
def DjangoConnectionField(  # noqa: N802
    target_type: type,
    *,
    resolver: Callable | None = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Sequence[object] = (),
) -> Any: ...
```

It runs the [`DjangoListField`][glossary-djangolistfield] guard sequence (`inspect.isclass` → `issubclass(DjangoType)` → own-class `definition.origin is target_type` → callable `resolver`) plus a Relay-Node-shaped guard, then returns `relay.connection(_connection_type_for(target_type), resolver=<synthesized>, …)`.

The Relay-Node-shaped guard at this **construction-time** call site reuses the canonical `_is_relay_shaped(target_type, definition.interfaces)` predicate — the single source of truth in [`types/base.py`][base] that also drives [Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition)'s `Meta.connection` eligibility gate. It accepts a type that is Relay-Node-shaped by **either** spelling: `relay.Node` in the declared `Meta.interfaces` tuple, **or** direct inheritance (`class Foo(DjangoType, relay.Node)`). Both signals are available at class-body time — the interfaces tuple is validated at class creation, and a directly-inherited `relay.Node` is already in `target_type.__bases__`. A naive MRO-only check (`implements_relay_node(target_type)`) would NOT suffice for the `Meta.interfaces` spelling, because [`finalize_django_types()`][glossary-finalize_django_types] Phase 2.5 (`apply_interfaces`) injects `relay.Node` into `target_type.__bases__` only later, AFTER this factory runs — which is exactly why `_is_relay_shaped` ORs the interfaces-tuple disjunct with the `issubclass(target_type, relay.Node)` disjunct, catching both spellings here. A non-Relay target raises [`ConfigurationError`][glossary-configurationerror].

**No `filters=` / `order=` / `total_count=` keyword arguments.** The filter / order sidecars come from `Meta.filterset_class` / `Meta.orderset_class`; the `totalCount` opt-in comes from `Meta.connection`. Dropping the per-field overrides is what lets [Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes) key the connection class on the node type alone.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 5][rationale-d5].

### Decision 6 — Sidecar-derived arguments via a synthesized resolver signature

[`filter_input_type`][glossary-filter_input_type] / [`order_input_type`][glossary-order_input_type] return annotations and write orphan-validation ledgers; **they do not add arguments to a field**. The field needs an explicit mechanism to receive `filter` / `order_by`.

**Mechanism: a synthesized resolver `__signature__`.** `DjangoConnectionField` builds the field's resolver as a wrapper whose `__signature__` (and matching `__annotations__`) carries `filter: filter_input_type(FS) | None = None` (when the type declares [`Meta.filterset_class`][glossary-metafilterset_class]) and `order_by: list[order_input_type(OS)] | None = None` (when it declares [`Meta.orderset_class`][glossary-metaorderset_class]). Strawberry's native resolver-argument derivation reads the signature and emits the `filter:` / `orderBy:` GraphQL arguments — the *same* path the hand-written filter/order resolvers documented in the `0.0.8` subsystems already use. `ConnectionExtension.resolve` forwards these non-pagination `**kwargs` to the resolver, which pops them and applies them in the pipeline. The referenced FilterSet / OrderSet are recorded against the existing `_helper_referenced_filtersets` / `_helper_referenced_ordersets` ledgers so [`finalize_django_types`][glossary-finalize_django_types] orphan validation stays honest.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 6][rationale-d6].

### Decision 7 — Composition pipeline: visibility→filter→order→default-order→optimizer

The connection resolver applies, in this exact order on the resolved queryset, before handing it to `ConnectionExtension` for slicing:

1. **base queryset** — the consumer `resolver=` return (with the contract below) or the default [`utils/querysets.py::initial_queryset`][querysets]`(target_type)`, which returns `model._default_manager.all()` — **unordered** for a model without `Meta.ordering`, which is why step 5 exists.
2. **`target_type.get_queryset(qs, info)`** — visibility (always; filter, order, default-order, and the slice all narrow, never widen).
3. **`FilterSet.apply_sync/async(filter, qs, info)`** — active-input filter gates (only when `filter:` given).
4. **`OrderSet.apply_sync/async(order_by, qs, info)`** — per-field order gates (only when `orderBy:` given).
5. **deterministic total ordering** — append the pk as a terminal tiebreaker so the `ORDER BY` is a unique TOTAL order in ALL cases, not just the fully-unordered one. Resolve the effective ordering (`qs.query.order_by`, or `model._meta.ordering` when that is empty-but-`ordered` — Django applies `Meta.ordering` implicitly, so reading `qs.query.order_by` alone would drop it) and `qs.order_by(*effective, pk)` UNLESS the effective ordering already ends in a unique column. A supplied `orderBy` (step 4) and a model `Meta.ordering` are preserved, with the pk appended for the tiebreaker — a NON-unique `orderBy` / `Meta.ordering` (e.g. `name` with duplicates) would otherwise make the positional offset cursors unstable across requests with zero concurrent writes. Both halves of the rule live in [`optimizer/plans.py`][optimizer-plans] — `deterministic_order` decides the tuple and `ends_in_unique_column` decides the skip — so the plan-time window order and this resolve-time order can never disagree; [`connection.py`][connection] re-exports the predicate as `_ends_in_unique_column`. **Unique means unique AND non-nullable**: SQL `UNIQUE` permits multiple NULLs, so a nullable unique terminal is not a total order and still takes the pk. A relation path (`shelf__code`), an annotation alias, and any non-`F` expression are treated as non-unique. A node type in keyset mode ([Decision 9](#decision-9--cursor-encoding-delegated-to-strawberry-keyset-cursors-are-a-separate-opt-in)) with no explicit `orderBy:` orders by its declared `Meta.cursor_field` instead — that ordering IS the cursor vocabulary and is finalization-validated to be a total order, so it beats a model `Meta.ordering` whose columns the keyset cursors do not encode.
6. **optimizer plan** — [`optimizer/extension.py::apply_connection_optimization`][optimizer-extension] ([Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point)) applies `select_related` / `prefetch_related` / [`only()`][glossary-only-projection] for the node type / model explicitly, never inferred from `info.return_type`.
7. **cursor slice** — `ConnectionExtension` / `resolve_connection` slices the prepared queryset; `totalCount` (if selected) counts the queryset entering step 7 (post-filter, pre-slice).

**Consumer `resolver=` contract** (extends the [`DjangoListField`][glossary-djangolistfield] post-processing): a `Manager` is coerced to a `QuerySet`; an unsliced `QuerySet` receives steps 2–7; an **already-sliced** `QuerySet` raises a `GraphQLError` regardless of sidecar input, because the field reorders and re-slices on every request and Django permits neither on a sliced query; a non-queryset iterable (list / generator) may be paginated only when **no** `filter:` / `orderBy:` input is supplied (steps 2–6 apply only to querysets), and supplying sidecar input against a non-queryset raises a `GraphQLError` (the advertised Meta-driven behavior cannot apply to a non-queryset). The same non-queryset incompatibility extends to `totalCount`: on a `total_count`-opted-in type, **selecting `totalCount` against a consumer-resolver return that is not a `QuerySet` raises a clear package `GraphQLError`** (`.count()` / `.acount()` is a queryset operation; a plain iterable cannot be counted into the non-null `totalCount: Int!` field without falling through to a generic engine non-null violation). All three rejections share one shape — the Meta-driven connection behavior cannot apply to that source, so the field says so rather than leaking a Django internal, silently ignoring an argument, or returning `null` into `Int!`.

Sync and async resolver paths mirror `DjangoListField`, reusing [`utils/querysets.py`][querysets]'s `apply_type_visibility_sync` / `apply_type_visibility_async`; a sync context meeting an async `get_queryset` raises [`SyncMisuseError`][glossary-syncmisuseerror]. Those helpers are a **sealed-execution boundary, not a passthrough**: the source and the hook's return are each rebuilt into a fresh framework-owned `QuerySet` from validated query state (shape, concrete and actual-base table, sealability, model-row, database alias), so a `get_queryset` that returns a widened queryset — or a type that shadows `all()` / the query chain to widen one — cannot broaden what the connection paginates or counts. Every non-sealable shape is rejected fail-closed. So the visibility step guarantees more than "the hook ran": step 2's scope is an upper bound the later steps can only narrow, and that guarantee holds for the `totalCount` count as well as for the edges.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 7][rationale-d7].

### Decision 8 — `Meta.connection` opt-in key, stored on the definition

`Meta.connection` lands **directly** in [`ALLOWED_META_KEYS`][base] (NOT a [`DEFERRED_META_KEYS`][base] promotion, mirroring [`spec-029`][spec-029]'s net-new-key rule). It accepts a dict; for `0.0.9` the only recognized sub-key is `{"total_count": bool}`. A `_validate_connection` helper (called from [`_validate_meta`][base], modeled on `_validate_filterset_class`):

- value must be a dict; non-dict raises [`ConfigurationError`][glossary-configurationerror];
- unknown sub-keys raise (typo guard — only `total_count` recognized in `0.0.9`);
- `total_count` must be a bool;
- the key is rejected on a non-Relay-Node type — i.e. when the `relay_shaped` bool (`_is_relay_shaped(cls, interfaces)`, threaded in from `_validate_meta`) is False: neither `relay.Node` in `Meta.interfaces` nor direct `relay.Node` inheritance.

The normalized value is **stored on [`DjangoTypeDefinition`][definition]** (a new `connection` slot, populated in [`__init_subclass__`][base] like the `filterset_class` / `orderset_class` slots), NOT merely validated and discarded. The `_connection_type_for(target_type)` factory and the connection-class generator read `definition.connection` to decide whether to emit the `totalCount` variant — they must not re-parse `Meta` (which is normalized away after validation).

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 8][rationale-d8].

### Decision 9 — Cursor encoding delegated to Strawberry; keyset cursors are a separate opt-in

A connection over a node type that declares no `Meta.cursor_field` uses the opaque base64 **offset** cursors Strawberry's [`relay.ListConnection`][strawberry-relay] emits (`b64("arrayconnection:N")`). They are documented as opaque — clients must not parse them.

This card writes no cursor scheme of its own. Value-encoded **keyset** cursors are the separate `Meta.cursor_field` opt-in, implemented in [`django_strawberry_framework/keyset.py`][keyset]; declaring the key makes every connection over that node type keyset-mode, which [`DjangoConnection`][glossary-djangoconnection]`.resolve_connection` dispatches to the package's own slicer instead of to `ListConnection`. The two cursor vocabularies are mutually exclusive per node type and each rejects the other's payload, so they can never be silently confused. What [`connection.py`][connection] owns is the dispatch seam, not the codec.

Rationale companion — this Decision's justification and its one rejected alternative: [Decision 9][rationale-d9].

### Decision 10 — Sync + async resolver paths reuse the shared visibility helpers

The connection resolver has sync and async variants mirroring [`DjangoListField`][glossary-djangolistfield]'s dispatch: visibility runs through `apply_type_visibility_sync` / `apply_type_visibility_async` ([`utils/querysets.py`][querysets] — the sealed-execution boundary every recomposing read surface shares, so the connection field inherits its guarantees rather than re-deriving them); filter / order run through the `apply_sync` / `apply_async` pairs; the cursor slice runs through `ConnectionExtension` / `resolve_connection`. A sync resolver context that meets an async `get_queryset` raises [`SyncMisuseError`][glossary-syncmisuseerror] (the unawaited coroutine is closed before the raise).

**Dispatch shape — the connection field is dispatch-frozen at build time, NOT per-call.** Unlike `DjangoListField` (whose default resolver picks sync vs async per call via `in_async_context()`), the connection field's sync/async handling is committed at schema-build time by Strawberry's `ConnectionExtension`: `ConnectionExtension.resolve` (the sync path, used when the field is not `async def`) passes the inner-resolver return straight to `resolve_connection` **without awaiting it**, while only `ConnectionExtension.resolve_async` (used when the resolver is `async def`) awaits it. So a sync `def` resolver returning a coroutine — the `DjangoListField` per-call shape — would hand an unawaited coroutine to `resolve_connection` and fail its iterable check; the per-call dispatch is therefore not achievable here. The implemented shape: the **default resolver** (`resolver is None`) and the **sync consumer-`resolver=`** branch are sync `def` resolvers running the sync pipeline and returning a **lazy queryset** that works under both `execute_sync` and `await execute` (`resolve_connection` materializes it with `.count()` or `.acount()` per the runtime context, so async counting still happens for the default field); the **async consumer-`resolver=`** branch is an `async def` resolver running the async pipeline. **Consequence:** the default resolver is build-time sync, so an async `get_queryset` hook on a connection field works ONLY via an `async def resolver=` — on the default branch the resolver routes through `apply_type_visibility_sync` and raises [`SyncMisuseError`][glossary-syncmisuseerror] for an async `get_queryset`, and it does so under `await schema.execute` exactly as under `execute_sync`, because the branch was chosen at construction and the execution mode cannot change it. Both `apply_type_visibility_sync` and `apply_type_visibility_async` are still reused as above (the former in the default / sync-consumer branch, the latter in the async-consumer branch); only the per-call dispatch the `DjangoListField` analogy implies is replaced by this build-time freeze. The sync branch also carries the two runtime guards the freeze makes necessary: a plain `def` resolver returning an awaitable is rejected before normalization, and one returning an async-only iterable in a sync execution context raises [`SyncMisuseError`][glossary-syncmisuseerror] rather than reaching Strawberry's sync slicer as a bare assertion. A declared async-generator resolver deliberately takes the sync branch — `is_async_callable` is False for it — because Strawberry's async executor consumes its `AsyncIterable` natively.

Rationale companion — this Decision's justification and its one rejected alternative: [Decision 10][rationale-d10].

### Decision 11 — The connection field owns its optimizer cooperation point

[`DjangoOptimizerExtension.resolve`][optimizer-extension] optimizes only when the resolved value is a Django `QuerySet`. Strawberry's `ConnectionExtension.resolve` calls the inner resolver and then `connection_type.resolve_connection(...)`, returning a **connection object** — so the schema middleware sees the post-connection result and cannot optimize the pre-slice queryset (verified against the locked source).

**Fix:** the plan-application logic is a reusable core on the extension, [`DjangoOptimizerExtension.apply_to`][optimizer-extension]`(target_type, target_model, queryset, info)`, taking the node type and model **directly**. It must NOT infer the model from `info.return_type`, because the connection field's root return type is the connection type, not the node type. Two callers share that one core: the middleware's `_optimize`, which resolves `(origin, model)` from the return type and then delegates — the only step the connection field does not need — and [`optimizer/extension.py::apply_connection_optimization`][optimizer-extension]`(target_type, queryset, info)`, the connection field's entry point, which resolves the model from `target_type`'s registered definition and calls `apply_to`. The connection resolver calls it as step 6 of the pipeline ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)), before `ConnectionExtension` slices, so the field self-optimizes. The middleware path is unchanged for non-connection fields.

The helper is **opt-in on the extension, not self-installing**: it reads the active extension from the `_active_optimizer` `ContextVar` that `on_execute` publishes, so it shares the instance-bound plan cache, and when no optimizer extension is installed for the execution it returns the queryset unoptimized rather than fabricating a throwaway optimizer. A connection field therefore follows the same install-to-get-optimization contract as every middleware-optimized field. It also returns the queryset unchanged when `target_type` has no registered model. The node-selection navigator is a parameter rather than a hardcoded connection shape, so a caller whose response nests the node type under a different slot passes its own and the walker still sees the child-selection list a list field over that node type would.

**Planning scope — what the cooperation point derives, and the boundary it does not cross.** The helper plans the **node type**, not the connection type: `apply_connection_optimization` defaults its `selection_extractor` to the `edges { node { ... } }` navigator, so the O2 walker receives the same child-selection list a [`DjangoListField`][glossary-djangolistfield] over that node type would, and a root connection derives the same plan — `select_related` for a selected to-one relation, a `Prefetch` for a selected many-side relation, and the [`only()`][glossary-only-projection] projection for the selected scalars. The one difference from the list-field shape is deliberate and load-bearing: the node children keep the connection's own response path as a runtime prefix, so the planned resolver keys read `<Type>.<rel>@<field>.edges.node.<rel>` and [Strictness mode][glossary-strictness-mode] accounting matches the path a resolver actually runs at. Two conditions still return the queryset unplanned, both stated above — no [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] installed for the execution, and a `target_type` with no registered model.

The boundary is the **nested** one. A `<field>Connection` reached under `edges { node { relConnection { ... } } }` needs the walker to recognize a connection *inside* a parent's selection walk and plan a windowed `Prefetch` for it; that is the sibling [`DONE-033-0.0.9`][kanban] card, together with the fallback shapes it names. It arrives as a **walker change plugged into this cooperation point** rather than a connection-field retrofit, which is the durable payoff of putting the seam here: richer planning is bought in the optimizer, and the field's pipeline keeps calling one helper at step 6. The ownership split is named in [`docs/GLOSSARY.md`][glossary], and a genuinely unplanned relation reached through a connection's `edges { node }` response path still trips [Strictness mode][glossary-strictness-mode] `"raise"` — the connection response shape does not hide an N+1 from the detector (no silent cap).

**Aggregate-ordering coexistence.** The plan's `select_related` / [`only()`][glossary-only-projection] columns land on a queryset the [`OrderSet`][glossary-orderset] step may already have grouped: a to-many `orderBy` path is ordered through a `Min` / `Max` aggregate annotation over the related column, which forces a `GROUP BY` on the parent ([`orders/sets.py::OrderSet._resolve_order_expressions`][orders-sets]). The pipeline order is what keeps the two compatible. The aggregate keeps exactly one row per parent, so the cursors index distinct nodes and `totalCount` counts distinct parents; a `select_related` of a to-one relation adds no row multiplication and its columns stay functionally dependent on the grouped parent pk on strict backends (Postgres `ONLY_FULL_GROUP_BY`, MySQL `5.7+`); and the projection narrows the select list the `GROUP BY` follows rather than widening it. So a root connection applies the grouped queryset and then its cursor slice, and a to-many aggregate order never sits beneath the optimizer's window annotations — on the sibling card's nested path a relation connection carrying `orderBy:` is deliberately left unplanned for that same reason ([`DONE-033-0.0.9`][kanban]). Pinned live by [`test_genre_connection_order_by_to_many_no_node_multiplication`][fakeshop-test-library], which runs the whole pipeline over `/graphql/` with the optimizer installed.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 11][rationale-d11].

### Decision 12 — No auto-trigger of `finalize_django_types()` for `0.0.9`

The connection field does NOT auto-trigger [`finalize_django_types`][glossary-finalize_django_types] from its constructor. The explicit-finalize contract is unchanged: the consumer calls `finalize_django_types()` once during single-threaded schema setup, as for [`DjangoListField`][glossary-djangolistfield] and every Relay-Node type today.

Rationale companion — this Decision's justification and its one rejected alternative: [Decision 12][rationale-d12].

### Decision 13 — Version bumps are owned by the joint `0.0.9` cut

No slice edits `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock`; no [`CHANGELOG.md`][changelog] release heading is promoted. The card contributes `### Added` bullets only; the release heading they ship under is not this card's to write. The `0.0.8` → `0.0.9` bump is owned by the **joint cut** releasing the four Relay cards together with [`DONE-029-0.0.9`][kanban].

Rationale companion — this Decision's justification and its one rejected alternative: [Decision 13][rationale-d13].

### Decision 14 — `connection.py` module and the public-export gate

The connection field ships as the flat module [`django_strawberry_framework/connection.py`][connection], listed under the on-disk package layout in [`docs/TREE.md`][tree], with the flat test file [`tests/test_connection.py`][test-connection], mirroring the [`DjangoListField`][glossary-djangolistfield] / [`tests/test_list_field.py`][test-list-field] pairing.

**`DjangoConnectionField` and `DjangoConnection` are promoted to the [`django_strawberry_framework`][package-init] public surface in Slice 4 — the same functional slice as the live fakeshop usage that proves the public shape.** Promoting the export with the live usage means the example imports from the public surface, not a temporary submodule path, and the tested-usage promotion discipline (a symbol reaches `__init__.py` only after a live test proves the end-to-end shape — the same gate `DjangoListField` followed) is satisfied within Slice 4.

The card DoD asks "full Relay support here or a separate `relay/` subpackage." **Decision: a flat pair, not a subpackage — `connection.py` carries the connection surface, and the Root-Node surface (`DjangoNodeField` / `DjangoNodesField` / GlobalID decode dispatch) is the separate flat module [`django_strawberry_framework/relay.py`][relay-root] owned by [`DONE-032-0.0.9`][kanban].** Flat placement follows the rule `list_field.py` follows while `filters/` and `orders/` are subpackages (the [`START.md`][start] fork-when-it-grows advice): whether the Relay surface later consolidates into a `relay/` subpackage is a package-layout decision no slice of this card makes, and [`docs/TREE.md`][tree] records the layout that is on disk.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 14][rationale-d14].

## Implementation plan

The card ships as **four sequential functional slices plus a doc + card-completion wrap**. Each functional slice is one PR; later slices build on earlier ones. Line deltas are estimates.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — `DjangoConnection[T]` + per-target classes + `Meta.connection` validate+store + `first`/`last` guard | [`django_strawberry_framework/connection.py`][connection] (new — `DjangoConnection`, `_connection_type_for`, `resolve_connection` guard + count), [`django_strawberry_framework/types/base.py`][base] (`ALLOWED_META_KEYS` += `"connection"` + `_validate_connection` + `__init_subclass__` store), [`django_strawberry_framework/types/definition.py`][definition] (`connection` slot), [`tests/test_connection.py`][test-connection] (new), [`tests/types/test_base.py`][test-types-base] (extend) | ~12 (`DjangoConnection[T]` shape; `first`+`last` `GraphQLError`; `<TypeName>Connection` generation + caching; `totalCount` present-only-opted-in + counted-only-selected; `Meta.connection` validation + `definition.connection` storage; `ALLOWED_META_KEYS` membership) | `+200 / -3` |
| 2 — `DjangoConnectionField` factory + synthesized-signature args + pipeline + resolver contract + optimizer helper + sync/async | [`django_strawberry_framework/connection.py`][connection] (factory + resolver + signature synthesis + pipeline), [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension] (extract `apply_connection_optimization` helper from `_optimize`), [`tests/test_connection.py`][test-connection] (extend), [`tests/optimizer/`][test-extension] (helper-extraction no-regression) | ~18 (constructor guards; arg presence/absence; four resolver-contract cases; default-ordering; composition order; optimizer helper applies plan; sync + async; `SyncMisuseError`) | `+280 / -15` |
| 3 — verify optimizer cooperation + name the nested-connection planning boundary | [`tests/test_connection.py`][test-connection] / [`tests/optimizer/`][test-extension] (cooperation + strictness seam) — **no new source** (helper landed in Slice 2) | ~4 (root connection's to-one plan; its many-side prefetch; strictness `"raise"` surfaces an unplanned relation reached through `edges { node }`; B1–B8 no-regression) | `+70 / -0` |
| 4 — live HTTP coverage + public-export promotion | [`django_strawberry_framework/__init__.py`][package-init] (export `DjangoConnectionField` / `DjangoConnection`), [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] (root `DjangoConnectionField(GenreType)` + `GenreType.Meta.connection`), [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] (extend) | ~6 (round-trip incl. `totalCount`; `first`+`last` error; `first: 0`; `totalCount`-omitted no-count; two-alias independent counts) | `+150 / -3` |
| 5 — doc updates + card-completion wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`TODAY.md`][today], [`README.md`][readme], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban] | 0 (doc-only) | `+95 / -25` |

Total expected delta: ~770 lines across four functional slices plus the wrap. No version-file edits (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).

## Edge cases and constraints

- **`first: 0`** — returns empty `edges` plus a valid `pageInfo`. Delegated to Strawberry's `ListConnection`; pinned by a Slice 4 live test.
- **`first: N` with N greater than the remaining rows** — returns the actual remainder. Delegated to `ListConnection`.
- **Both `first:` and `last:` in one query** — the package's own `resolve_connection` override raises a `GraphQLError` (Strawberry's `SliceMetadata.from_arguments` does NOT guard it, [Decision 3](#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard)); surfaced in the GraphQL `errors` array. Pinned by a Slice 4 live test.
- **`after:` cursor under concurrent inserts/deletes** — the query does **not** error, but offset cursors encode a position, not row identity, so inserts/deletes before that position can skip or duplicate rows; offset-cursor stability under *concurrent mutation* is **not guaranteed** on the offset path. A node type that needs it declares `Meta.cursor_field`, whose value-encoded cursors make `after:` a tuple-comparison seek rather than a position ([Decision 9](#decision-9--cursor-encoding-delegated-to-strawberry-keyset-cursors-are-a-separate-opt-in)). This is distinct from cursor stability over a NON-UNIQUE ordering (which needs no concurrency at all): the pipeline's terminal pk tiebreaker (step 5) guarantees a unique total order so a non-unique `orderBy` / `Meta.ordering` does not skip/duplicate rows across pages.
- **Non-unique / unordered base queryset** — the pipeline's deterministic-total-ordering step ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)) appends the pk as a terminal tiebreaker so the cursors index a unique total order: a fully-unordered [`initial_queryset`][querysets] (a model without `Meta.ordering`) becomes `order_by(pk)`; a supplied `orderBy` or model `Meta.ordering` over a non-unique column becomes `order_by(<that>, pk)` (preserved, with the tiebreaker appended); an ordering already ending in a unique non-nullable column is left alone. Pinned by Slice 2 tests.
- **`totalCount` requested but `Meta.connection` omits `total_count`** — the field is absent from the connection type, so the query fails GraphQL validation (unknown field), not at runtime ([Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes)).
- **`totalCount` enabled but not selected by a query** — no count query runs (selection-gated). A `@skip` / `@include` directive that excludes `totalCount` — on the field itself or on the fragment wrapping it — is the same case, because selection is directive-resolved: Strawberry's converted selections carry the field with its already-resolved directive arguments rather than dropping the node, so the predicate applies the include gate itself ([Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes)). Pinned by Slice 4 live tests.
- **Two aliases of the same connection with different `filter:` values** — each carries its own `totalCount` (count on the connection instance, not an `info.context` stash). Pinned by a Slice 4 live test.
- **Consumer `resolver=` returns a `Manager`** — coerced to `QuerySet`, full pipeline ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)).
- **Consumer `resolver=` returns a non-queryset iterable with `filter:` / `orderBy:` input** — `GraphQLError` (the Meta-driven behavior cannot apply to a non-queryset); without sidecar input, the iterable is paginated. Pinned by Slice 2 tests.
- **Consumer `resolver=` returns a non-queryset iterable while `totalCount` is selected** (on a `total_count`-opted-in type) — `GraphQLError` (a non-queryset cannot be `.count()`-ed into the non-null `totalCount: Int!` field; the count helper raises a clear package error rather than skipping the count and letting the field return `null`, which would otherwise surface as the engine's `Cannot return null for non-nullable field …totalCount` violation). Symmetric with the sidecar-input case above ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)). Pinned by a Slice 2 test (escalated from Slice 1 review M1). Without `totalCount` selected, a non-queryset iterable without sidecar input still paginates normally.
- **Consumer `resolver=` returns an already-sliced `QuerySet`** — `GraphQLError` naming the cause and the fix, raised whether or not sidecar input was supplied ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)). Pinned by a Slice 2 test.
- **An async `get_queryset` invoked from a sync GraphQL execution** — raises [`SyncMisuseError`][glossary-syncmisuseerror], reusing the shared visibility helpers' contract ([Decision 10](#decision-10--sync--async-resolver-paths-reuse-the-shared-visibility-helpers)). The same happens on a default connection field under `await schema.execute`, because the sync branch is frozen at construction. The async path is genuinely unreachable from the sync `/graphql/` view, so its coverage lands in [`tests/test_connection.py`][test-connection] (the [`DjangoListField`][glossary-djangolistfield] precedent).
- **Root connection selection (`edges { node { rel } }`)** — planned through this card's cooperation point: the node-level selections drive the plan, so a to-one relation is `select_related`-ed, a many-side relation is prefetched, and the selected scalars become an [`only()`][glossary-only-projection] projection ([Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point)). Nothing is planned when no [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] is installed for the execution — the field does not fabricate one. Pinned by Slice 3 tests.
- **Nested connection selection (`edges { node { relConnection { edges { node } } } }`)** — windowed planning of the inner connection is the sibling [`DONE-033-0.0.9`][kanban] card's surface, which plugs into this card's cooperation point and owns its own fallback shapes; this card's contract ends at the root connection's own plan. A [Strictness mode][glossary-strictness-mode] `"raise"` run still surfaces a genuinely unplanned relation reached through a connection's `edges { node }` response path as an N+1 (Slice 3). No silent cap — the ownership split is named in [`docs/GLOSSARY.md`][glossary].
- **Two `DjangoConnectionField`s on the same model** — both resolve to the same `<Type>FilterInputType` / `<Type>OrderInputType` (stable class-derived names via the shared helper machinery), so the schema carries one input type per model ([Decision 6](#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature)). Because `totalCount` is per type, both also share the one connection shape for that node type ([Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes)).
- **A connection field over a [`Meta.primary`][glossary-metaprimary]`= False` secondary type** — supported; the field wraps the type it is given. The relation-as-Connection *implicit upgrade* (which must choose a type) is [`DONE-032-0.0.9`][kanban]'s problem.
- **`Meta.connection` on a non-Relay type** — rejected at type creation with [`ConfigurationError`][glossary-configurationerror] ([Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition)).

## Test plan

Tests live across the package-internal `tests/` tree and the `examples/fakeshop/test_query/` tree, per [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Coverage that can be earned by a real GraphQL query is earned there first; the rest lands in [`tests/test_connection.py`][test-connection].

### Slice 1 — `tests/test_connection.py` (new) + `tests/types/test_base.py` (extend)

- `test_django_connection_is_listconnection_subclass` — `DjangoConnection[T]` is a [`strawberry.relay.ListConnection`][strawberry-relay]`[T]` subclass, no `total_count` field.
- `test_first_and_last_raises_graphql_error` / `test_first_and_last_guard_on_generated_subclass` / `test_first_and_last_guard_with_unset` — `resolve_connection` with both `first` and `last` raises a `GraphQLError` (the package's own guard; Strawberry's `SliceMetadata` does not), the generated subclass shares it, and an omitted argument arriving as `strawberry.UNSET` does not trip it.
- `test_connection_type_for_caches_per_target` / `test_connection_type_for_generates_named_subclass_when_opted_in` / `test_connection_type_for_returns_concrete_subclass_without_opt_in` / `test_connection_type_for_returns_concrete_subclass_when_total_count_false` / `test_generated_connection_name_uses_graphql_type_name_not_python_name` — `_connection_type_for` returns one cached class per node type; every node type yields a generated concrete `<TypeName>Connection` named from the type's canonical GraphQL name, carrying `total_count` only when the type opts in, never the generic alias.
- `test_total_count_present_only_when_opted_in` / `test_total_count_requested_true_when_selected` / `test_total_count_requested_false_when_absent` / `test_total_count_requested_scoped_to_direct_children` / `test_total_count_requested_recurses_through_fragments` — `totalCount` exists only for an opted-in type, and the count runs only when `totalCount` is one of the connection's OWN selected fields (fragment wrappers at that level included; a `totalCount` deeper inside `edges { node { ... } }` excluded).
- `test_meta_connection_in_allowed_meta_keys` (in `tests/types/test_base.py`) — `"connection"` in [`ALLOWED_META_KEYS`][base], not in [`DEFERRED_META_KEYS`][base].
- `test_meta_connection_non_dict_raises` / `test_meta_connection_unknown_subkey_raises` / `test_meta_connection_non_bool_total_count_raises` / `test_meta_connection_non_relay_type_raises` — the four `_validate_connection` failures raise [`ConfigurationError`][glossary-configurationerror].
- `test_meta_connection_stored_on_definition` — the normalized value lands on `definition.connection` ([Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition)).

### Slice 2 — `tests/test_connection.py` (extend) + `tests/optimizer/` (no-regression)

- `test_connection_field_requires_djangotype` / `test_connection_field_requires_djangotype_subclass` / `test_connection_field_requires_own_class_definition` / `test_connection_field_rejects_non_callable_resolver` / `test_connection_field_requires_relay_node` — the four `DjangoListField`-style guards plus the Relay-Node guard each raise [`ConfigurationError`][glossary-configurationerror]. `test_connection_field_accepts_direct_relay_node_inheritance` pins the other accepted spelling of the fifth.
- `test_connection_field_derives_filter_arg_from_filterset` / `..._orderby_arg_from_orderset` / `..._omits_args_without_sidecars` — argument presence/absence tracks the sidecars (the synthesized resolver signature).
- `test_connection_field_registers_sidecars_against_orphan_ledgers` — the referenced FilterSet/OrderSet are recorded against `_helper_referenced_filtersets` / `_helper_referenced_ordersets`.
- `test_consumer_resolver_manager_coerced` / `..._queryset_full_pipeline` / `..._iterable_without_sidecar_input_paginates` / `..._iterable_with_sidecar_input_raises` — the four consumer-`resolver=` cases ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)).
- `test_consumer_resolver_iterable_with_total_count_selected_raises` — on a `total_count`-opted-in type, a consumer `resolver=` returning a non-queryset iterable while the query selects `totalCount` raises a clear package `GraphQLError` (NOT the engine's `Cannot return null for non-nullable field …totalCount` violation) — the `totalCount`-over-non-queryset half of the [Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer) consumer-resolver contract; the count helper raises rather than skipping the count. (Escalated from Slice 1 review M1 — the count helpers landed in Slice 1 but the contract becomes reachable only once the Slice 2 factory admits non-queryset resolver returns.)
- `test_consumer_resolver_pre_sliced_queryset_raises_clear_error` — an already-sliced `QuerySet` return raises the package `GraphQLError` rather than leaking Django's `Cannot reorder a query once a slice has been taken`.
- `test_default_ordering_applied_when_unordered` / `test_default_ordering_preserves_supplied_orderby` / `test_default_ordering_preserves_meta_ordering` — the default-ordering step through the field. `test_finalize_queryset_appends_pk_tiebreaker_to_non_unique_ordering` / `test_finalize_queryset_preserves_meta_ordering_and_appends_pk` / `test_finalize_queryset_skips_pk_when_terminal_already_unique` pin the same three cases plus the already-unique-terminal skip directly on the pipeline tail, and `test_ends_in_unique_column_recognizes_unique_and_non_unique_terminals` / `test_ends_in_unique_column_false_for_unnameable_terminal` pin the predicate itself.
- `test_connection_resolver_composition_order` — visibility before filter before order, with `totalCount` captured pre-slice on the post-filter set. The last two steps are pinned where they are decided rather than by call-order instrumentation: the `test_finalize_queryset_*` rows above for the default order, and `test_root_connection_field_queryset_is_planned` / `test_apply_connection_optimization_short_circuits_without_optimizer` / `test_apply_connection_optimization_short_circuits_when_target_has_no_model` for the plan step before the slice.
- `test_connection_resolver_async_dispatch` (the async `execute` path, `.acount()` included) / `test_sync_context_async_get_queryset_raises_sync_misuse` / `test_async_execution_default_connection_async_get_queryset_raises_sync_misuse` — the build-time dispatch freeze of [Decision 10](#decision-10--sync--async-resolver-paths-reuse-the-shared-visibility-helpers), including that a default field refuses an async `get_queryset` under async execution too. The sync path has no dedicated dispatch row because every `execute_sync` row above drives it; its misuse boundaries are pinned by `test_connection_sync_resolver_returning_coroutine_raises_sync_misuse` / `test_connection_sync_resolver_returning_async_iterable_raises_sync_misuse` / `test_connection_sync_async_generator_resolver_raises_sync_misuse` / `test_connection_async_generator_resolver_executes_on_async_path`.
- `test_pipeline_async_coerces_manager_source_and_finalizes` / `test_connection_async_pipeline_applies_filter_and_order` / `test_async_consumer_resolver_iterable_with_total_count_selected_raises` / `test_connection_async_resolver_resolving_to_residual_awaitable_fails_closed` — the async pipeline mirrors the sync one step for step and guard for guard.
- `test_optimizer_helper_extraction_no_regression` (in `tests/optimizer/`) — the existing B1–B8 middleware suite is unaffected by extracting `apply_connection_optimization` from `_optimize`.

### Slice 3 — optimizer cooperation

- `test_root_connection_field_queryset_is_planned` — a root `DjangoConnectionField`'s pre-slice queryset is run through the extracted helper, which publishes an [`OptimizationPlan`][glossary-djangooptimizerextension] to `info.context` (the field's cooperation point, [Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point)); the middleware publishes nothing for a connection field, so a published plan over the connection proves the field's own helper ran. The plan itself is asserted, not merely its presence: a forward FK selected under `edges { node { category { … } } }` lands as `select_related == ("category",)` with the full `only()` projection (parent scalars, the FK id, and the related columns), and the planned resolver key carries the connection response path (`PlanItemNode.category@items.edges.node.category`).
- `test_root_connection_field_queryset_prefetches_node_many_relation` — the many-side half of the same contract: a relation selected under `edges { node { items { … } } }` lands as a `Prefetch` rather than a `select_related`, with the parent projection unchanged.
- `test_nested_connection_unplanned_raises_under_strictness` — with no optimizer extension installed and an empty strictness context, a relation access reached through `edges { node { items } }` trips [`types/resolvers.py::_check_n1`][resolvers] and surfaces as `OptimizerError("Unplanned N+1: items")`. It pins that the connection response shape does not blind the strictness detector (no silent cap); the fallback shapes of a *planned* nested connection belong to [`DONE-033-0.0.9`][kanban].

### Slice 4 — `examples/fakeshop/test_query/test_library_api.py` (extend)

Against a root `DjangoConnectionField(GenreType)` (Relay-Node-shaped, `GenreFilter` / `GenreOrder` sidecars, `Meta.connection = {"total_count": True}`), imported from the public surface and reached through the live `/graphql/` HTTP stack (per the fakeshop reload pattern):

- `test_genre_connection_full_round_trip` — `edges { node { id name } } pageInfo { hasNextPage endCursor } totalCount` with `filter:` + `orderBy:` + `first:` + `after:`; assert ordering, page boundaries, `endCursor`, `totalCount` == unpaginated post-filter count; no `errors`.
- `test_genre_connection_first_and_last_rejected` — both `first:` and `last:` returns a GraphQL `errors` entry (the package's own guard).
- `test_genre_connection_first_zero_empty_edges` — `first: 0` returns empty `edges` + valid `pageInfo`.
- `test_genre_connection_total_count_omitted_no_count` — a query without `totalCount` returns correct edges and issues no `COUNT(` SQL at all, asserted over the captured queries rather than inferred from the wire shape — the selection-gating contract.
- `test_genre_connection_total_count_skip_include_no_count` — the directive half of the same contract: a direct `@skip(if: true)`, a variable-driven `@include(if: $show)` with `$show = false`, and a named-fragment-wrapped `@skip(if: true)` each omit the field and issue zero `COUNT(` SQL, with a `@skip(if: false)` control proving the count still fires when the directive resolves to keep.
- `test_genre_connection_two_aliases_independent_total_counts` — two aliases with different `filter:` values return independent `totalCount`s — the per-instance-count contract.

A check before declaring the suite undisturbed: a new reachable root field changes the registered-type count and the full SDL. Confirm no existing `test_query/` test snapshots the whole SDL or asserts a registered-type count; re-run the check at implementation time.

## Doc updates

Each slice owns its own doc edits. The CHANGELOG-edit permission comes from Slice 5's doc-update step per the explicit-instruction rule at [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" — **AGENTS.md prohibits `CHANGELOG.md` edits without permission, and this spec's Slice 5 grants that permission**; the Slice 5 maintainer prompt must name the `CHANGELOG.md` `### Added` edit explicitly so an agent does not infer permission from a standing document.

- **Slice 5 — GLOSSARY**
  - [`docs/GLOSSARY.md`][glossary]: flip [`DjangoConnectionField`][glossary-djangoconnectionfield], [`DjangoConnection`][glossary-djangoconnection], and [`Meta.connection`][glossary-metaconnection] from `planned for 0.0.9` to `shipped (0.0.9)` in the [Index][glossary-index] table and entry bodies; add the sidecar-derived-argument / composition-order / opt-in-`totalCount` / per-shape-connection-class detail and the cooperation-point note (the field owns its own optimizer seam; nested-connection window planning is the sibling card's) to the `DjangoConnectionField` body; confirm the `Meta.connection` body describes the `{"total_count": bool}` shape and the Relay-Node requirement, with Index + "Relay" / "Type generation" [Browse by category][glossary] rows still present. Do not touch the [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] entry — its status is [`DONE-033-0.0.9`][kanban]'s to set.
- **Slice 5 — package docs**
  - [`docs/README.md`][docs-readme]: move `DjangoConnectionField` to the shipped surface; note the sidecar-derived `filter:` / `orderBy:` arguments and opt-in `totalCount`.
  - [`docs/TREE.md`][tree]: list [`connection.py`][connection] in the current on-disk layout (drop the `[alpha]` planned tag) and the mirrored [`tests/test_connection.py`][test-connection].
  - [`TODAY.md`][today]: move `DjangoConnectionField` off the products "still waiting for" list (or note its activation tracking, lit up at fakeshop activation per [`TODO-BETA-061-0.1.5`][kanban]); keep the file products-centric.
  - [`README.md`][readme]: update the status paragraph's shipped-surface line only if it enumerates the connection field.
  - [`CHANGELOG.md`][changelog]: `### Added` bullets (the explicit permission grant above). No release-heading promotion — the heading they ship under belongs to the joint `0.0.9` cut (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).
- **Slice 5 — card-completion wrap**
  - [`KANBAN.md`][kanban]: move this card to Done, where it is [`DONE-030-0.0.9`][kanban] (the column-move pass assigns the next available id); add / confirm the card body's spec reference points at [`docs/SPECS/spec-030-connection_field-0_0_9.md`][spec-030]; rewrite the card-body DoD's unnumbered `docs/spec-connection.md` reference to the canonical name. No version-file edits.

## Risks and open questions

Every question this card opened is answered by a Decision above. The deliberation that answered them — each question's preferred answer for the cut, its fallback if implementation proved the preferred answer wrong, and the [`KANBAN.md`][kanban] card-body filename conflict it reconciled — is recorded in the rationale companion under [Risks and open questions][rationale-risks].

One rule outlives the build and stays here:

- **Every Strawberry-mechanism claim is pinned to a derivation baseline, and the declared floor is a range, not a point.** The upstream behaviors this spec relies on — `SliceMetadata.from_arguments` does not reject `first` + `last` ([Decision 3](#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard)), `ConnectionExtension.resolve` forwards the non-pagination `**kwargs` to the inner resolver and does not await its return ([Decision 6](#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature) / [Decision 10](#decision-10--sync--async-resolver-paths-reuse-the-shared-visibility-helpers)), and `ListConnection.resolve_connection` receives the pagination arguments ([Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes)) — are derived against the uv.lock-resolved Strawberry `0.316.0`, while `pyproject.toml` declares an open `strawberry-graphql` floor, so the *mechanism* can drift across the supported range even where the conclusion holds. A supported version that changes any of them requires the affected Decision to be re-derived by executing against that version — never read forward from this document, and never inferred from a changelog.

## Out of scope (explicitly tracked elsewhere)

- **Root `node(id:)` / `nodes(ids:)`, the relation-as-Connection upgrade, `DjangoNodeField` / `DjangoNodesField`** ([`DjangoNodeField`][glossary-djangonodefield]) — the [Full Relay story][kanban] ([`DONE-032-0.0.9`][kanban]), which depends on this card.
- **Connection-aware optimizer planning** ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]) — the sibling [`DONE-033-0.0.9`][kanban] card; plugs into this card's cooperation point.
- **Django-model-based GlobalID encoding** — the sibling [`DONE-031-0.0.9`][kanban] card.
- **`search:` argument** ([`Meta.search_fields`][glossary-metasearch_fields]) — `0.1.2`.
- **`Meta.fields_class` field-selection composition** ([`FieldSet`][glossary-fieldset], [`Meta.fields_class`][glossary-metafields_class]) — `0.1.1`.
- **`aggregates` argument** ([`AggregateSet`][glossary-aggregateset], [`Meta.aggregate_class`][glossary-metaaggregate_class], [`RelatedAggregate`][glossary-relatedaggregate]) — `0.1.3`.
- **Permissions cascade** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions]) — `0.0.10`; the connection field respects [`get_queryset`][glossary-get_queryset-visibility-hook] immediately.
- **`filters=` / `order=` / `total_count=` per-field overrides** — dropped for `0.0.9` ([Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation)); an additive follow-up if demand surfaces.
- **`Meta.cursor_field` / keyset cursors** — [`django_strawberry_framework/keyset.py`][keyset] ([Decision 9](#decision-9--cursor-encoding-delegated-to-strawberry-keyset-cursors-are-a-separate-opt-in)).
- **`Meta.relation_shapes` (list-vs-connection relation opt-out)** — [`DONE-032-0.0.9`][kanban].
- **Auto-trigger of `finalize_django_types()`** — not built by this card ([Decision 12](#decision-12--no-auto-trigger-of-finalize_django_types-for-009)), and not built by any card since: no shipped helper auto-triggers finalization, so the explicit consumer call remains the only trigger and the direction is recorded as not adopted ([`spec-010-foundation-0_0_4.md`][spec-010] #"Layer 3: Finalization trigger"). Any future helper that takes it up owes the single-threaded-setup-window guarantee the card body named — constrained to schema-construction time, or a real lock around the finalizer.
- **Version bump** — owned by the joint `0.0.9` cut ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).

## Definition of done

The completion contract the card is built against. Items are grouped by slice; the card completes when all four functional slices' items plus the wrap are satisfied.

**Spec + companion CSV**

1. [`docs/SPECS/spec-030-connection_field-0_0_9.md`][spec-030] (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv`][spec-030-terms] anchoring every project-specific term that **has** a [`docs/GLOSSARY.md`][glossary] heading; [`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md`][check-spec-glossary] reports `OK: <N> terms`. The net-new [`Meta.connection`][glossary-metaconnection] symbol has a [`docs/GLOSSARY.md`][glossary] heading and a row in the CSV anchoring it there.

**Slice 1 — `DjangoConnection[T]` + per-target classes + `Meta.connection`**

2. [`django_strawberry_framework/connection.py`][connection] ships `DjangoConnection[NodeType]` (a [`strawberry.relay.ListConnection`][strawberry-relay] subclass, no `total_count`, `resolve_connection` raises a `GraphQLError` on `first` + `last`) and a cached `_connection_type_for(target_type)` that returns a generated concrete `<TypeName>Connection` for every node type — never the generic alias — carrying `total_count` (selection-gated, counted on the post-filter pre-slice source, attached to the connection instance) only when the type opts in, per [Decision 3](#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard) / [Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes).
3. [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] contains `"connection"` (not in [`DEFERRED_META_KEYS`][base]); `_validate_connection` rejects a non-dict, an unknown sub-key, a non-bool `total_count`, and a non-Relay type with [`ConfigurationError`][glossary-configurationerror]; the normalized value is stored on [`DjangoTypeDefinition.connection`][definition] ([Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition)). [`tests/test_connection.py`][test-connection] + [`tests/types/test_base.py`][test-types-base] cover the slice.

**Slice 2 — `DjangoConnectionField` factory**

4. [`django_strawberry_framework/connection.py`][connection] ships `DjangoConnectionField(target_type, *, resolver=None, …)` (Meta-only — no `filters=` / `order=` / `total_count=`) running the four [`DjangoListField`][glossary-djangolistfield]-style guards plus the Relay-Node guard, injecting `filter:` / `orderBy:` via a synthesized resolver signature (the FilterSet/OrderSet registered against the orphan ledgers), and returning `relay.connection(_connection_type_for(target_type), …)` ([Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation) / [Decision 6](#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature)).
5. The resolver applies the composition pipeline `get_queryset` → `filter` → `orderBy` → default-order → optimizer-plan → slice with the consumer-`resolver=` contract (`Manager` coerced, unsliced `QuerySet` piped, already-sliced `QuerySet` rejected, non-queryset iterable paginated only without sidecar input else `GraphQLError`); sync/async reuse [`utils/querysets.py`][querysets]'s `apply_type_visibility_sync` / `apply_type_visibility_async` + `apply_sync` / `apply_async`, and a sync-context async-`get_queryset` raises [`SyncMisuseError`][glossary-syncmisuseerror] ([Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer) / [Decision 10](#decision-10--sync--async-resolver-paths-reuse-the-shared-visibility-helpers)). The plan-application core [`DjangoOptimizerExtension.apply_to`][optimizer-extension] takes `target_type` / `target_model` and is reached before the slice through [`apply_connection_optimization`][optimizer-extension] ([Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point)); the middleware's `_optimize` delegates to the same core, so that path is behavior-identical for non-connection fields. [`tests/test_connection.py`][test-connection] covers guards, arg derivation, the resolver-contract cases, default-ordering, composition order, and sync/async.

**Slice 3 — optimizer cooperation**

6. A root `DjangoConnectionField`'s pre-slice queryset is run through the extracted helper (the field's own cooperation point, [Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point)) — the field publishes an [`OptimizationPlan`][glossary-djangooptimizerextension] to `info.context` before the slice, which the middleware never does for a connection field, and the plan is derived from the `edges { node { ... } }` selections so a root connection plans `select_related` / `prefetch_related` / [`only()`][glossary-only-projection] exactly as a [`DjangoListField`][glossary-djangolistfield] over the node type does, with the connection response path carried into the planned resolver keys. Nested `<field>Connection` window planning belongs to [`DONE-033-0.0.9`][kanban], which plugs into this seam. A [Strictness mode][glossary-strictness-mode] `"raise"` test pins that a genuinely unplanned relation reached through a connection's `edges { node }` response path still surfaces as an N+1; the existing B1–B8 optimizer suite is unaffected by the helper extraction. The ownership split is named in [`docs/GLOSSARY.md`][glossary] (no silent cap).

**Slice 4 — live HTTP coverage + public export**

7. `DjangoConnectionField` / `DjangoConnection` are exported from [`django_strawberry_framework/__init__.py`][package-init] in this slice ([Decision 14](#decision-14--connectionpy-module-and-the-public-export-gate)). A root `DjangoConnectionField(GenreType)` (Relay-Node, `GenreFilter` / `GenreOrder`, `Meta.connection = {"total_count": True}`) is added to [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] importing from the public surface. Live HTTP tests in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] cover the filter+orderBy+first+after round-trip (incl. `totalCount`, no `errors`), the `first`+`last` `GraphQLError`, `first: 0` empty edges, the `totalCount`-omitted no-count path, and two-alias independent counts (per the [Test plan](#test-plan)).

**Slice 5 — doc + card-completion wrap**

8. [`docs/GLOSSARY.md`][glossary] flips [`DjangoConnectionField`][glossary-djangoconnectionfield] / [`DjangoConnection`][glossary-djangoconnection] / [`Meta.connection`][glossary-metaconnection] to `shipped (0.0.9)`; [`docs/README.md`][docs-readme] / [`docs/TREE.md`][tree] / [`TODAY.md`][today] / [`README.md`][readme] reflect the shipped field; [`CHANGELOG.md`][changelog] carries the `### Added` bullets under the `0.0.9` release heading the joint cut owns (the explicit per-card permission grant named in the Slice 5 maintainer prompt).
9. [`KANBAN.md`][kanban] records the card as [`DONE-030-0.0.9`][kanban] with the card body's spec reference pointing at [`docs/SPECS/spec-030-connection_field-0_0_9.md`][spec-030].
10. **No version bump lands in this card** per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut): `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` are unchanged; no [`CHANGELOG.md`][changelog] release heading is promoted (the joint `0.0.9` cut owns the bump).
11. Package coverage stays at 100% (`fail_under = 100`). Routine per-slice work does not run pytest locally — owned by CI per the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"No pytest after edits"; worker-local validation is `uv run ruff format .` and `uv run ruff check --fix .`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[kanban]: ../../KANBAN.md
[readme]: ../../README.md
[start]: ../../START.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-aggregateset]: ../GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: ../GLOSSARY.md#apply_cascade_permissions
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
[glossary-fk-id-elision]: ../GLOSSARY.md#fk-id-elision
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-index]: ../GLOSSARY.md#index
[glossary-metaaggregate_class]: ../GLOSSARY.md#metaaggregate_class
[glossary-metaconnection]: ../GLOSSARY.md#metaconnection
[glossary-metadescription]: ../GLOSSARY.md#metadescription
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metafields_class]: ../GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: ../GLOSSARY.md#metafilterset_class
[glossary-metainterfaces]: ../GLOSSARY.md#metainterfaces
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaname]: ../GLOSSARY.md#metaname
[glossary-metanullable_overrides]: ../GLOSSARY.md#metanullable_overrides
[glossary-metaoptimizer_hints]: ../GLOSSARY.md#metaoptimizer_hints
[glossary-metaorderset_class]: ../GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-metarequired_overrides]: ../GLOSSARY.md#metarequired_overrides
[glossary-metasearch_fields]: ../GLOSSARY.md#metasearch_fields
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-order_input_type]: ../GLOSSARY.md#order_input_type
[glossary-ordering]: ../GLOSSARY.md#ordering
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-public-exports]: ../GLOSSARY.md#public-exports
[glossary-queryset-diffing]: ../GLOSSARY.md#queryset-diffing
[glossary-relatedaggregate]: ../GLOSSARY.md#relatedaggregate
[glossary-relatedfilter]: ../GLOSSARY.md#relatedfilter
[glossary-relatedorder]: ../GLOSSARY.md#relatedorder
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-strawberry_config]: ../GLOSSARY.md#strawberry_config
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[rationale-d10]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-10--sync--async-resolver-paths-reuse-the-shared-visibility-helpers
[rationale-d11]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-11--the-connection-field-owns-its-optimizer-cooperation-point
[rationale-d12]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-12--no-auto-trigger-of-finalize_django_types-for-009
[rationale-d13]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-13--version-bumps-are-owned-by-the-joint-009-cut
[rationale-d14]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-14--connectionpy-module-and-the-public-export-gate
[rationale-d1]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-2--card-scope-boundary-against-the-sibling-relay-cards
[rationale-d3]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard
[rationale-d4]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes
[rationale-d5]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-5--factory-function-mechanism-meta-only-derivation
[rationale-d6]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature
[rationale-d7]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer
[rationale-d8]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-8--metaconnection-opt-in-key-stored-on-the-definition
[rationale-d9]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-9--cursor-encoding-delegated-to-strawberry-keyset-cursors-are-a-separate-opt-in
[rationale-risks]: appx/spec-030-connection_field-0_0_9-rationale.md#risks-and-open-questions
[spec-030-rationale]: appx/spec-030-connection_field-0_0_9-rationale.md
[spec-010]: spec-010-foundation-0_0_4.md
[spec-015]: spec-015-relay_interfaces-0_0_5.md
[spec-020]: spec-020-list_field-0_0_7.md
[spec-027]: spec-027-filters-0_0_8.md
[spec-028]: spec-028-orders-0_0_8.md
[spec-029]: spec-029-consumer_dx_cleanup-0_0_9.md
[spec-030]: spec-030-connection_field-0_0_9.md
[spec-030-terms]: appx/spec-030-connection_field-0_0_9-terms.csv

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/types/base.py
[connection]: ../../django_strawberry_framework/connection.py
[definition]: ../../django_strawberry_framework/types/definition.py
[keyset]: ../../django_strawberry_framework/keyset.py
[list-field]: ../../django_strawberry_framework/list_field.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[package-init]: ../../django_strawberry_framework/__init__.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[relay]: ../../django_strawberry_framework/types/relay.py
[relay-root]: ../../django_strawberry_framework/relay.py
[resolvers]: ../../django_strawberry_framework/types/resolvers.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-connection]: ../../tests/test_connection.py
[test-extension]: ../../tests/optimizer/test_extension.py
[test-list-field]: ../../tests/test_list_field.py
[test-types-base]: ../../tests/types/test_base.py

<!-- examples/ -->
[fakeshop-config-schema]: ../../examples/fakeshop/config/schema.py
[fakeshop-library-schema]: ../../examples/fakeshop/apps/library/schema.py
[fakeshop-test-library]: ../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->
[check-spec-glossary]: ../../scripts/check_spec_glossary.py

<!-- .venv/ -->

<!-- External -->
[strawberry-relay]: https://strawberry.rocks/docs/guides/relay
[upstream-cookbook]: https://github.com/riodw/django-graphene-filters
