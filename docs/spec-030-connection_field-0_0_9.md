# Spec: `DjangoConnectionField` (Relay connection field) — `DjangoConnection[T]`, sidecar-derived `filter:` / `orderBy:` arguments, opt-in `totalCount`

Planned for `0.0.9` (card [`WIP-ALPHA-030-0.0.9`][kanban]). **This spec is an open build plan, not a shipped record.** The card is the lowest-NNN WIP card in the `0.0.9` cohort and the **central read-side primitive** for the package's Relay surface: every Layer-3 argument (filter, order, and later search / aggregate / field-selection) composes through this one field, and the [Full Relay story][kanban] ([`WIP-ALPHA-032-0.0.9`][kanban]) is hard-blocked on it landing. The [Slice checklist](#slice-checklist) below stays unticked as the contract record (build progress is tracked in the build plan, not here); the [Definition of done](#definition-of-done) describes the closure conditions; the [Current state](#current-state) section describes the repo as of this spec's authoring, before the build. **Version boundary** (see [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)): this card shares the `0.0.9` patch line with three sibling WIP cards ([`WIP-ALPHA-031-0.0.9`][kanban], [`WIP-ALPHA-032-0.0.9`][kanban], [`WIP-ALPHA-033-0.0.9`][kanban]) and the already-shipped [`DONE-029-0.0.9`][kanban]; the `pyproject.toml` / [`__version__`][package-init] / [`tests/base/test_init.py::test_version`][test-base-init] bump to `0.0.9` is owned by the **joint cut**, not by this card. This card's slices land within the `0.0.9` line and never bump the version themselves (the on-disk version is still `0.0.8` at spec-authoring time).

Status: planned — no slice started. Five slices: Slice 1 (the [`DjangoConnection`][glossary-djangoconnection]`[T]` return alias + opt-in `totalCount` + the net-new `Meta.connection` validation), Slice 2 (the [`DjangoConnectionField`][glossary-djangoconnectionfield] factory + sidecar-derived `filter:` / `orderBy:` arguments + the visibility→filter→order→slice composition order + sync/async paths), Slice 3 (optimizer cooperation against the existing flat-selection walker; connection-aware planning is the sibling [`WIP-ALPHA-033-0.0.9`][kanban] card, deferred), Slice 4 (live HTTP coverage on a Relay-Node-shaped fakeshop type), and Slice 5 (doc updates + the card-completion wrap; grants the per-card [`CHANGELOG.md`][changelog] edit permission [`AGENTS.md`][agents] otherwise withholds). Slices 1→2→3→4 are sequential (each builds on the prior); Slice 5 lands last.

Owner: package maintainer.

Predecessors: [`spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (the most-recently-shipped spec — the canonical voice / depth / section-layout reference for this document; its [Decision 11][spec-029] joint-`0.0.9`-cut version-bump boundary is the precedent [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut) reuses verbatim, and its [Decision 3][spec-029] singleton-factory `extensions=` form is the construction shape every example schema in this spec uses); [`spec-028-orders-0_0_8.md`][spec-028] (the [`OrderSet`][glossary-orderset] subsystem whose [`order_input_type`][glossary-order_input_type] helper, `apply_sync` / `apply_async` pair, and `_helper_referenced_ordersets` orphan-validation ledger this card's `orderBy:` argument reuses); [`spec-027-filters-0_0_8.md`][spec-027] (the [`FilterSet`][glossary-filterset] subsystem whose [`filter_input_type`][glossary-filter_input_type] helper and `apply_sync` / `apply_async` pair this card's `filter:` argument reuses, and whose [Decision 8][spec-027] `get_queryset` cooperation contract this card's composition order extends to the connection-pagination case); [`spec-020-list_field-0_0_7.md`][spec-020] (the [`DjangoListField`][glossary-djangolistfield] non-Relay sibling — the closest existing analogue: a PascalCase factory function returning a `strawberry.field(...)`, with the same `get_queryset`-applying sync/async resolver wrappers and the same root-gated optimizer cooperation this card mirrors for the Relay shape, and whose [Decision 8][spec-020] explicitly scoped the connection field out to this card); [`spec-015-relay_interfaces-0_0_5.md`][spec-015] (the [Relay Node integration][glossary-relay-node-integration] foundation — `Meta.interfaces = (relay.Node,)`, the injected `resolve_*` defaults, `id: GlobalID!` suppression, and [`SyncMisuseError`][glossary-syncmisuseerror] — that the connection field's per-edge node resolution and visibility-hook cooperation build on). [`docs/GLOSSARY.md`][glossary] already carries [`DjangoConnectionField`][glossary-djangoconnectionfield], [`DjangoConnection`][glossary-djangoconnection], and [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] entries (all status `planned for 0.0.9`); this card flips the first two to `shipped (0.0.9)` and leaves the third planned (it ships under [`WIP-ALPHA-033-0.0.9`][kanban]). The net-new `Meta.connection` key has **no** glossary heading yet; its entry is authored during implementation (per [Doc updates](#doc-updates)) and flagged in [Risks and open questions](#risks-and-open-questions) as the missing-glossary-heading caveat.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`WIP-ALPHA-030-0.0.9`][kanban] card body via the [`docs/SPECS/NEXT.md`][next] flow. Pinned: the canonical spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)) over the card body's unnumbered `docs/spec-connection.md` reference; the card-scope boundary against the three sibling `0.0.9` Relay cards ([Decision 2](#decision-2--card-scope-boundary-against-the-sibling-relay-cards)); building on Strawberry's native [`relay.ListConnection`][strawberry-relay] / `relay.connection()` rather than hand-rolling cursor math ([Decision 3](#decision-3--build-on-strawberrys-native-relay-connection-machinery)); the [`DjangoConnection`][glossary-djangoconnection]`[T]` `ListConnection` subclass carrying the opt-in `totalCount` ([Decision 4](#decision-4--djangoconnectiont-is-a-listconnection-subclass-with-opt-in-totalcount)); the factory-function mechanism mirroring [`DjangoListField`][glossary-djangolistfield] ([Decision 5](#decision-5--factory-function-mechanism-mirroring-djangolistfield)); sidecar-derived `filter:` / `orderBy:` argument generation reusing the shipped helper machinery ([Decision 6](#decision-6--sidecar-derived-filter--orderby-arguments-reuse-the-shipped-helper-machinery)); the visibility→filter→order→slice composition order ([Decision 7](#decision-7--composition-order-visibilityfilterorderslice)); the net-new `Meta.connection = {"total_count": True}` opt-in key + its validation ([Decision 8](#decision-8--metaconnection-opt-in-totalcount-key-net-new-allowed_meta_keys-entry)); the opaque-cursor delegation to Strawberry with `Meta.cursor_field` deferred ([Decision 9](#decision-9--opaque-cursor-delegated-to-strawberry-metacursor_field-deferred)); the sync + async resolver paths reusing the Relay-foundation `get_queryset` helpers ([Decision 10](#decision-10--sync--async-resolver-paths-reuse-the-relay-foundation-get_queryset-helpers)); optimizer cooperation against the existing flat-selection root-gated walker with connection-aware planning deferred to [`WIP-ALPHA-033-0.0.9`][kanban] ([Decision 11](#decision-11--optimizer-cooperation-against-the-flat-selection-walker-connection-aware-planning-deferred)); the no-auto-trigger-of-`finalize_django_types()` posture for `0.0.9` ([Decision 12](#decision-12--no-auto-trigger-of-finalize_django_types-for-009)); the joint-`0.0.9`-cut version-bump boundary ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)); the `connection.py` flat-module location with the public-export-on-tested-usage gate ([Decision 14](#decision-14--connectionpy-flat-module-and-the-public-export-gate)). Conflicts called out in [Risks and open questions](#risks-and-open-questions): the card body's unnumbered `docs/spec-connection.md` filename, and the `Meta.connection` key that has no glossary heading at authoring time.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoConnectionField`][glossary-djangoconnectionfield] — the Relay-style connection field this card ships: `edges` / `node` / `pageInfo` / `totalCount`, cursor pagination, and `filter:` / `orderBy:` arguments flowing into the wrapped type's [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class]. Status flips `planned for 0.0.9` → `shipped (0.0.9)`.
- [`DjangoConnection`][glossary-djangoconnection] — the generic `DjangoConnection[T]` return alias this card ships as the annotation on a `DjangoConnectionField` declaration. Status flips `planned for 0.0.9` → `shipped (0.0.9)`.
- [Relay Node integration][glossary-relay-node-integration] — the shipped `0.0.5` foundation (`Meta.interfaces = (relay.Node,)`, injected `resolve_*` defaults, `id: GlobalID!`). A `DjangoConnectionField` is only meaningful over a Relay-Node-shaped [`DjangoType`][glossary-djangotype]; the connection's `edges { node }` are that type's nodes.
- [`Meta.interfaces`][glossary-metainterfaces] — the key that declares `relay.Node`; [Decision 8](#decision-8--metaconnection-opt-in-totalcount-key-net-new-allowed_meta_keys-entry) rejects `Meta.connection` on a type whose `Meta.interfaces` omits `relay.Node`.
- [`FilterSet`][glossary-filterset] / [`filter_input_type`][glossary-filter_input_type] / [`Meta.filterset_class`][glossary-metafilterset_class] — the shipped filter subsystem the connection field's `filter:` argument is auto-derived from; the field reuses the `apply_sync` / `apply_async` classmethod pair and the `filter_input_type` lazy-`Annotated` machinery (Slice 2, [Decision 6](#decision-6--sidecar-derived-filter--orderby-arguments-reuse-the-shipped-helper-machinery)).
- [`OrderSet`][glossary-orderset] / [`order_input_type`][glossary-order_input_type] / [`Meta.orderset_class`][glossary-metaorderset_class] / [`Ordering`][glossary-ordering] — the shipped ordering subsystem the `orderBy:` argument is auto-derived from; the list-shaped `orderBy: [<T>OrderInputType!]` argument is the multi-field tie-breaker mechanism.
- [`RelatedFilter`][glossary-relatedfilter] / [`RelatedOrder`][glossary-relatedorder] — the cross-relation traversal primitives whose active-branch [`get_queryset`][glossary-get_queryset-visibility-hook] scoping the connection field inherits unchanged when it routes input through `apply_sync` / `apply_async`.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — runs FIRST in the connection field's composition order ([Decision 7](#decision-7--composition-order-visibilityfilterorderslice)); the visibility scope is what filter, order, and the cursor slice all narrow, never widen.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] / [Plan cache][glossary-plan-cache] / [`only()` projection][glossary-only-projection] / [FK-id elision][glossary-fk-id-elision] / [Queryset diffing][glossary-queryset-diffing] / [Strictness mode][glossary-strictness-mode] — the optimizer surface the connection field cooperates with. In `0.0.9` it rides the existing **root-gated flat-selection** walker ([Decision 11](#decision-11--optimizer-cooperation-against-the-flat-selection-walker-connection-aware-planning-deferred)); [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] (`edges { node }` recognition) is the sibling [`WIP-ALPHA-033-0.0.9`][kanban] card.
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] — the deferred sibling slice that teaches the walker to recognize `edges { node { ... } }`; this card ships against the flat walker and the connection-aware walker takes over without retrofit when [`WIP-ALPHA-033-0.0.9`][kanban] lands.
- [`DjangoListField`][glossary-djangolistfield] — the shipped non-Relay `list[T]` sibling whose factory-function mechanism ([Decision 5](#decision-5--factory-function-mechanism-mirroring-djangolistfield)), `get_queryset`-applying sync/async resolver wrappers ([Decision 10](#decision-10--sync--async-resolver-paths-reuse-the-relay-foundation-get_queryset-helpers)), and root-gated optimizer cooperation this card mirrors for the Relay shape.
- [`DjangoNodeField`][glossary-djangonodefield] — the planned root single-node lookup field; **not** this card (it lands with the [Full Relay story][kanban], [`WIP-ALPHA-032-0.0.9`][kanban]); cited because it shares the finalizer auto-trigger seam this card declines to build ([Decision 12](#decision-12--no-auto-trigger-of-finalize_django_types-for-009)).
- [`finalize_django_types`][glossary-finalize_django_types] — the single-threaded schema-setup synchronization point; the connection field is constructed at schema-build time and does NOT auto-trigger it for `0.0.9` ([Decision 12](#decision-12--no-auto-trigger-of-finalize_django_types-for-009)).
- [`ConfigurationError`][glossary-configurationerror] — raised at type-creation / field-construction time for the connection field's validation failures (`Meta.connection` on a non-Relay type, a non-`DjangoType` target, the mutually-exclusive `first` + `last`).
- [`DjangoType`][glossary-djangotype] / [`Meta.primary`][glossary-metaprimary] — the type the field wraps; the [`Meta.primary`][glossary-metaprimary] multi-type rule governs which type a relation-as-connection upgrade resolves to (the upgrade itself is [`WIP-ALPHA-032-0.0.9`][kanban]'s job, out of scope here).
- [`SyncMisuseError`][glossary-syncmisuseerror] — the typed marker the Relay-foundation `get_queryset` helpers raise when a sync resolver context meets an async `get_queryset`; the connection field's sync path inherits this contract ([Decision 10](#decision-10--sync--async-resolver-paths-reuse-the-relay-foundation-get_queryset-helpers)).
- [`strawberry_config`][glossary-strawberry_config] — the scalar-map factory every example schema in this spec passes to `strawberry.Schema(...)` alongside the singleton-factory [`DjangoOptimizerExtension`][glossary-djangooptimizerextension].

Dependency and forward-composition surfaces a reader will hit:

- [`Meta.search_fields`][glossary-metasearch_fields] (`0.1.2`) — the `search: String` connection argument is **absent** until search ships; the connection field reserves the seam but does not generate the argument in `0.0.9` (per the card body).
- [`FieldSet`][glossary-fieldset] / [`Meta.fields_class`][glossary-metafields_class] (`0.1.1`) — field-selection composition layers onto the connection field after it ships; out of scope here.
- [`AggregateSet`][glossary-aggregateset] / [`Meta.aggregate_class`][glossary-metaaggregate_class] / [`RelatedAggregate`][glossary-relatedaggregate] (`0.1.3`) — the `aggregates` connection argument; a later composition surface, listed only as an out-of-scope pointer.
- [`apply_cascade_permissions`][glossary-apply_cascade_permissions] (`0.0.10`) — the permissions card; the connection field respects [`get_queryset`][glossary-get_queryset-visibility-hook] immediately and gains declared-permission integration when the permissions subsystem lands.
- [Multi-database cooperation][glossary-multi-database-cooperation] — the connection field's queryset flows through the same `.using(alias)` `_db`-preservation contract; no new multi-db surface here.
- [`OptimizerHint`][glossary-optimizerhint] / [`Meta.optimizer_hints`][glossary-metaoptimizer_hints] — per-relation overrides on the wrapped type; unchanged by the connection field, which plans against the root queryset like any other root resolver.
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — the `1.0.0` rule that every Layer-3 argument composes with the optimizer; this card is the field through which that composition runs.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package tests under `tests/` mirroring source; example-project non-HTTP tests under `examples/fakeshop/tests/`; live HTTP tests under `examples/fakeshop/test_query/`); the live-HTTP-priority coverage rule; the no-pytest-after-edits rule; the settings-keys rule (add a settings key only when a feature needs it); the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — Slice 5's doc-update step grants the explicit per-card permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical (Slice 4) and package-internal `tests/test_connection.py` where the path is unreachable from a live query.
- [`docs/TREE.md`][tree] — tests mirror source one-to-one; the connection field lands as the flat module [`django_strawberry_framework/connection.py`][connection] (the target layout already reserves the `connection.py [alpha]` slot) with the flat test file [`tests/test_connection.py`][test-connection].
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, all defs at the bottom under the 10 canonical group headers); the "Strawberry is the engine; DRF is the shape" rule ([Decision 3](#decision-3--build-on-strawberrys-native-relay-connection-machinery) builds on Strawberry's relay, not a hand-rolled one); the "fork a subsystem into its own spec mid-stream when a slice grows past ~one module" advice ([Decision 14](#decision-14--connectionpy-flat-module-and-the-public-export-gate)).

## Slice checklist

Each top-level item maps to one commit / PR. **Five slices: four sequential functional slices (1→2→3→4, each builds on the prior) plus a doc + card-completion wrap (5).** Boxes are unticked because the work has not started.

- [ ] Slice 1: `DjangoConnection[T]` return alias + opt-in `totalCount` + `Meta.connection` validation (per [Decision 4](#decision-4--djangoconnectiont-is-a-listconnection-subclass-with-opt-in-totalcount) / [Decision 8](#decision-8--metaconnection-opt-in-totalcount-key-net-new-allowed_meta_keys-entry))
  - [ ] Ship [`django_strawberry_framework/connection.py`][connection] with a generic `DjangoConnection[NodeType]` subclass of [`strawberry.relay.ListConnection`][strawberry-relay] that adds an opt-in `total_count: int` field whose resolver reads the count off a context stash populated by the field resolver (the unpaginated post-filter queryset's `.count()` / `.acount()`), NOT a second `qs.count()` at edge-resolution time.
  - [ ] [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] grows `"connection"` (net-new public key — NOT a [`DEFERRED_META_KEYS`][base] promotion, mirroring [`spec-029`][spec-029] [Decision 6][spec-029]). [`_validate_meta`][base] grows a `_validate_connection` helper that shape-checks the dict (`{"total_count": bool}` only; unknown sub-keys raise) and rejects `Meta.connection` declared on a type whose `Meta.interfaces` omits `relay.Node` ([`ConfigurationError`][glossary-configurationerror] naming the type and suggesting either remove the key or add `relay.Node`).
  - [ ] Package coverage: [`tests/test_connection.py`][test-connection] (the `DjangoConnection[T]` shape; `total_count` present-only-when-opted-in; the `Meta.connection` shape / non-Relay-type rejection). [`tests/types/test_base.py`][test-types-base] gains the `"connection"`-in-`ALLOWED_META_KEYS` / not-in-`DEFERRED_META_KEYS` assertion.
- [ ] Slice 2: `DjangoConnectionField` factory + sidecar-derived arguments + composition order + sync/async (per [Decision 5](#decision-5--factory-function-mechanism-mirroring-djangolistfield) / [Decision 6](#decision-6--sidecar-derived-filter--orderby-arguments-reuse-the-shipped-helper-machinery) / [Decision 7](#decision-7--composition-order-visibilityfilterorderslice) / [Decision 10](#decision-10--sync--async-resolver-paths-reuse-the-relay-foundation-get_queryset-helpers))
  - [ ] `DjangoConnectionField(target_type, *, filters=…, order=…, total_count=…, description=…, …)` PascalCase factory returning a Strawberry `relay.connection(...)`-shaped field bound to a [`DjangoType`][glossary-djangotype], mirroring the [`DjangoListField`][glossary-djangolistfield] constructor-guard discipline (`isclass` → `issubclass(DjangoType)` → own-class `__django_strawberry_definition__.origin is target_type` → Relay-Node-shaped). A non-Relay target raises [`ConfigurationError`][glossary-configurationerror] (a connection field requires `Meta.interfaces = (relay.Node,)`).
  - [ ] Auto-derive the `filter:` argument from the target's [`Meta.filterset_class`][glossary-metafilterset_class] via the shipped [`filter_input_type`][glossary-filter_input_type] machinery (absent when the type declares no filterset); auto-derive `orderBy: [<T>OrderInputType!]` from [`Meta.orderset_class`][glossary-metaorderset_class] via [`order_input_type`][glossary-order_input_type] (absent when none). Register the derived sets against the existing `_helper_referenced_filtersets` / `_helper_referenced_ordersets` ledgers so [`finalize_django_types`][glossary-finalize_django_types] orphan validation stays honest. The `search:` argument is NOT generated (search is `0.1.2`).
  - [ ] The connection resolver applies the composition order on the resolved queryset: `target_type.get_queryset(qs, info)` (visibility) → `FilterSet.apply_*` (active-input gates) → `OrderSet.apply_*` (per-field gates) → hand the **unpaginated post-filter** queryset to Strawberry's `ListConnection.resolve_connection` for the cursor slice; stash the `.count()` for `totalCount` BEFORE the slice. Sync and async resolver paths mirror [`DjangoListField`][glossary-djangolistfield], reusing `_apply_get_queryset_sync` / `_apply_get_queryset_async` and the `apply_sync` / `apply_async` classmethod pairs; a sync context meeting an async `get_queryset` raises [`SyncMisuseError`][glossary-syncmisuseerror].
  - [ ] The mutually-exclusive `first` + `last` guard and the `after` / `before` cursor decoding are delegated to Strawberry's `ListConnection` (it already raises a typed error); the field surfaces it unchanged.
  - [ ] Package coverage: [`tests/test_connection.py`][test-connection] extends — constructor guards (non-class, non-`DjangoType`, non-own-class, non-Relay), argument presence/absence by sidecar declaration, composition-order unit (visibility before filter before order before slice), sync + async resolver dispatch.
- [ ] Slice 3: optimizer cooperation against the flat-selection walker (per [Decision 11](#decision-11--optimizer-cooperation-against-the-flat-selection-walker-connection-aware-planning-deferred))
  - [ ] Confirm a **root** `DjangoConnectionField` selection rides the existing root-gated ([`info.path.prev is None`][optimizer-extension]) [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] hook: the resolved pre-slice queryset is what the optimizer plans `select_related` / `prefetch_related` / [`only()`][glossary-only-projection] against, exactly as a root `list[T]` resolver does. No walker change in this card.
  - [ ] Document the alpha constraint honestly: nested `edges { node { ... } }` connection selections are functional but NOT yet connection-aware-planned — that is the sibling [`WIP-ALPHA-033-0.0.9`][kanban] card; the connection-aware walker takes over without retrofit when it lands. No silent cap — the constraint is named in [`docs/GLOSSARY.md`][glossary] and [Edge cases and constraints](#edge-cases-and-constraints).
  - [ ] Package coverage: an optimizer-cooperation test (root connection field → planned root queryset; a [Strictness mode][glossary-strictness-mode] `"raise"` assertion that an unplanned nested-connection access still surfaces as N+1, guarding the seam the connection-aware card will close).
- [ ] Slice 4: live HTTP coverage on a Relay-Node-shaped fakeshop type (per [Decision 7](#decision-7--composition-order-visibilityfilterorderslice) / the card DoD)
  - [ ] Add a root `DjangoConnectionField` over the [`library`][fakeshop-library-schema] `GenreType` (already Relay-Node-shaped with both [`Meta.filterset_class`][glossary-metafilterset_class] and [`Meta.orderset_class`][glossary-metaorderset_class] declared) with `Meta.connection = {"total_count": True}`, exposed on the `library` `Query` via [`DjangoConnectionField(GenreType)`][connection].
  - [ ] Two-plus live HTTP tests in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]: (a) a full round-trip requesting `edges { node { id name } } pageInfo { hasNextPage endCursor } totalCount` with `filter:` + `orderBy:` + `first:` + `after:` asserting correct pagination, ordering, and `totalCount` on the unpaginated post-filter set; (b) the mutually-exclusive `first` + `last` typed-error path; (c) a `first: 0` empty-edges + `pageInfo` shape.
- [ ] Slice 5: doc updates + card-completion wrap (grants the per-card [`CHANGELOG.md`][changelog] edit permission)
  - [ ] [`docs/GLOSSARY.md`][glossary]: flip [`DjangoConnectionField`][glossary-djangoconnectionfield] and [`DjangoConnection`][glossary-djangoconnection] from `planned for 0.0.9` to `shipped (0.0.9)` in the [Index][glossary-index] table and their entry bodies; add a `## Meta.connection` entry (status `shipped (0.0.9)`) describing the `{"total_count": bool}` shape and the Relay-Node requirement; add `Meta.connection` to the Index and the "Relay" / "Type generation" [Browse by category][glossary] rows. Leave [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] `planned for 0.0.9` (ships under [`WIP-ALPHA-033-0.0.9`][kanban]).
  - [ ] [`docs/README.md`][docs-readme]: move `DjangoConnectionField` from the "coming next" `0.0.9` line to the shipped surface list; note the sidecar-derived `filter:` / `orderBy:` arguments and opt-in `totalCount`.
  - [ ] [`docs/TREE.md`][tree]: list [`connection.py`][connection] under the current on-disk package layout (drop its `[alpha]` planned tag) and the mirrored [`tests/test_connection.py`][test-connection].
  - [ ] [`TODAY.md`][today]: update the products "still waiting for" list — `DjangoConnectionField` moves from waiting to shipped (or note products' Relay-connection activation tracking, lit up at fakeshop activation per [`TODO-BETA-051-0.1.5`][kanban]); keep the file products-centric.
  - [ ] [`README.md`][readme]: update the status paragraph's newest-shipped-surface line if it enumerates the connection field (include only if reflected there).
  - [ ] [`CHANGELOG.md`][changelog]: `### Added` bullet under `[Unreleased]` for `DjangoConnectionField` / `DjangoConnection` / `Meta.connection`. **This is the per-card CHANGELOG-edit permission grant** ([`AGENTS.md`][agents] withholds it by default); no version-heading promotion (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).
  - [ ] [`KANBAN.md`][kanban]: move [`WIP-ALPHA-030-0.0.9`][kanban] to the Done column with the next `DONE-NNN-0.0.9` id; add / confirm the card body's spec reference points at [`docs/spec-030-connection_field-0_0_9.md`][spec-030] (this document).
  - [ ] **No version-file edits in this card.** Leave `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` to the joint `0.0.9` cut per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut).

## Problem statement

`django-strawberry-framework`'s `0.0.8` surface ships [`DjangoType`][glossary-djangotype], the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], the [`FilterSet`][glossary-filterset] and [`OrderSet`][glossary-orderset] subsystems, [Relay Node integration][glossary-relay-node-integration] (`Meta.interfaces = (relay.Node,)` with injected `resolve_*` defaults), and the non-Relay [`DjangoListField`][glossary-djangolistfield]. What it does **not** ship is a Relay-shaped **connection field**. Today a consumer who wants paginated, cursor-based access to a model collection has only two options: a non-Relay [`DjangoListField`][glossary-djangolistfield] (no `edges` / `pageInfo` / `totalCount`, no pagination), or a hand-written `@strawberry.field` resolver that constructs a `relay.ListConnection` by hand AND re-wires the `filter:` / `orderBy:` arguments from the type's sidecars by hand. The second is exactly the boilerplate this package exists to eliminate.

Both upstreams ship this primitive. `graphene-django` (via `django-graphene-filters`) ships `AdvancedDjangoFilterConnectionField` — one declaration (`all_object_types = AdvancedDjangoFilterConnectionField(ObjectTypeNode)`) exposes the type's declared filter / order sidecars as connection arguments plus Relay pagination. `strawberry-graphql-django` ships `strawberry_django.connection()` over a `ListConnectionWithTotalCount`, planning connection selections natively. This card is the package's Strawberry-native, `class Meta`-driven equivalent: `all_genres: DjangoConnection[GenreType] = DjangoConnectionField(GenreType)` reads the per-type [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] declarations and generates the `filter:` / `orderBy:` arguments identically, with cursor pagination and an opt-in `totalCount` on top — no hand-written list resolver, no parallel argument declarations.

It is the **central read-side primitive**. The card body and the sibling [`WIP-ALPHA-032-0.0.9`][kanban] (Full Relay story) both name it: every Layer-3 argument composes through this field. Filtering and ordering shipped in `0.0.8` and are consumed on day one; field-selection ([`FieldSet`][glossary-fieldset], `0.1.1`), search ([`Meta.search_fields`][glossary-metasearch_fields], `0.1.2`), and aggregation ([`AggregateSet`][glossary-aggregateset], `0.1.3`) layer on after the connection field ships. The [Full Relay story][kanban] is hard-blocked on this card landing; [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] ships in parallel. Getting the field's seams right — the composition order, the sidecar-argument derivation, the optimizer cooperation point, and the finalizer-trigger posture — is therefore load-bearing for the entire `0.0.9` Relay cohort and everything Layer-3 after it.

## Current state

A true description of the repo as of this writing (the plan is written against it):

- There is **no** `connection.py` on disk. [`docs/TREE.md`][tree]'s target package layout reserves a `connection.py [alpha]` slot (`# [alpha] DjangoConnectionField (Relay)`); this card fills it. The public surface ([`django_strawberry_framework/__init__.py`][package-init]) exports `DjangoType`, `DjangoListField`, `DjangoOptimizerExtension`, `OptimizerHint`, `BigInt`, `SyncMisuseError`, `finalize_django_types`, `strawberry_config`, `auto`, `__version__` — neither `DjangoConnectionField` nor `DjangoConnection` yet.
- [`django_strawberry_framework/list_field.py`][list-field] is the closest analogue: a PascalCase factory function `DjangoListField(target_type, *, resolver=…, description=…, …)` returning `strawberry.field(resolver=wrapped, …)`. It runs four constructor-site guards (`inspect.isclass` → `issubclass(DjangoType)` → own-class `definition.origin is target_type` → callable resolver), and its default resolver branches on [`in_async_context()`][list-field] to dispatch `_apply_get_queryset_sync` vs `_apply_get_queryset_async`. The Relay connection field mirrors this mechanism and these guards, adding the Relay-Node-shaped guard and the sidecar-argument derivation.
- [`django_strawberry_framework/types/relay.py`][relay] ships the `0.0.5` Relay foundation: `_apply_get_queryset_sync` / `_apply_get_queryset_async` (the [`get_queryset`][glossary-get_queryset-visibility-hook] appliers the connection resolver reuses), `_initial_queryset`, the [`SyncMisuseError`][glossary-syncmisuseerror] marker, and the four injected `resolve_*` defaults. The connection field's per-edge node resolution rides the same `resolve_node` / `resolve_id` machinery already installed on every Relay-Node-shaped type.
- The [`FilterSet`][glossary-filterset] subsystem exposes the classmethod pair `FilterSet.apply_sync(input_value, queryset, info)` / `FilterSet.apply_async(...)` and the [`filter_input_type`][glossary-filter_input_type] resolver-argument helper, which returns `Annotated["<Name>FilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]` and records the FilterSet against `_helper_referenced_filtersets` for [`finalize_django_types`][glossary-finalize_django_types] orphan validation. The [`OrderSet`][glossary-orderset] subsystem mirrors this exactly: `OrderSet.apply_sync` / `apply_async`, [`order_input_type`][glossary-order_input_type] (element type, wrapped as `list[order_input_type(...)]` at the call site), and `_helper_referenced_ordersets`. The connection field reuses all of this rather than re-deriving argument types.
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension] gates optimization on `info.path.prev is None` — only **root** resolvers returning a Django `QuerySet` trigger planning. A root [`DjangoListField`][glossary-djangolistfield] selection is planned today; a root `DjangoConnectionField` returning the same pre-slice queryset shape will be too, **provided** the optimizer sees the queryset at the root before the cursor slice. The walker is flat-selection — it does not yet recognize Relay `edges { node { ... } }` wrappers (that is [`WIP-ALPHA-033-0.0.9`][kanban]).
- [`django_strawberry_framework/types/base.py`][base] holds `ALLOWED_META_KEYS` = `{"description", "exclude", "fields", "filterset_class", "interfaces", "model", "name", "nullable_overrides", "optimizer_hints", "orderset_class", "primary", "required_overrides"}` and `DEFERRED_META_KEYS` = `{"aggregate_class", "fields_class", "search_fields"}`. `"connection"` is in neither; declaring it today raises [`ConfigurationError`][glossary-configurationerror] via the unknown-key typo guard at [`_validate_meta`][base]. `_validate_filterset_class` / `_validate_orderset_class` are the structural template for the new `_validate_connection` helper.
- The locked Strawberry is `0.316.0` (`pyproject.toml` floor `>=0.262.0`; `uv.lock` resolves `0.316.0`). [`strawberry.relay`][strawberry-relay] exposes `Connection`, `ListConnection`, `Edge`, `PageInfo`, `GlobalID`, `Node`, `NodeID`, `connection`, `node`, `to_base64`, `from_base64`. `ListConnection.resolve_connection(nodes, *, info, before, after, first, last, **kwargs)` owns the cursor math, the `first` + `last` mutually-exclusive guard, and the `pageInfo` semantics. The package builds on it ([Decision 3](#decision-3--build-on-strawberrys-native-relay-connection-machinery)).
- The [`library`][fakeshop-library-schema] app already hosts a Relay-Node-shaped type with both sidecars: `GenreType` declares `Meta.interfaces = (relay.Node,)`, `filterset_class = filters_genre.GenreFilter`, and `orderset_class = orders_genre.GenreOrder`. It is the natural live-HTTP host for Slice 4 — no new model or migration is needed. [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] already constructs its schema with the [`spec-029`][spec-029] singleton-factory `extensions=[lambda: _optimizer]` form and a [`strawberry_config()`][glossary-strawberry_config] call.
- [`docs/GLOSSARY.md`][glossary] already has `## DjangoConnectionField`, `## DjangoConnection`, and `## Connection-aware optimizer planning` headings (all `planned for 0.0.9`). It has **no** heading for `Meta.connection`; that entry is authored in Slice 5.

## Goals

1. Ship [`DjangoConnectionField`][glossary-djangoconnectionfield] — a Relay-style connection field over a Relay-Node-shaped [`DjangoType`][glossary-djangotype] with `edges` / `node` / `pageInfo` / `totalCount`, `first` / `after` / `last` / `before` cursor pagination, and `filter:` / `orderBy:` arguments auto-derived from the wrapped type's [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] — with no hand-written list resolver and no parallel argument declarations (Slice 2).
2. Ship the [`DjangoConnection`][glossary-djangoconnection]`[T]` generic return alias as a [`strawberry.relay.ListConnection`][strawberry-relay]`[T]` subclass carrying the opt-in `totalCount` field, gated by the net-new `Meta.connection = {"total_count": True}` key (Slice 1).
3. Pin the composition order — [`get_queryset`][glossary-get_queryset-visibility-hook] (visibility) → `filter` (active-input gates) → `orderBy` (per-field gates) → cursor slice — so the pre-pagination queryset is what the optimizer plans against and `totalCount` counts the unpaginated post-filter set (Slice 2, [Decision 7](#decision-7--composition-order-visibilityfilterorderslice)).
4. Cooperate with the existing root-gated flat-selection [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] without a walker change, and document the nested-`edges { node }`-planning gap as the sibling [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] card's job — the connection-aware walker takes over without retrofit when [`WIP-ALPHA-033-0.0.9`][kanban] lands (Slice 3, [Decision 11](#decision-11--optimizer-cooperation-against-the-flat-selection-walker-connection-aware-planning-deferred)).
5. Earn package coverage through a live fakeshop HTTP round-trip on the Relay-Node-shaped `GenreType` (filter + orderBy + cursor + totalCount), per [`docs/TREE.md`][tree]'s coverage-priority rule; the package coverage gate (`fail_under = 100`) is reached because that test exercises the field end-to-end (Slice 4).
6. Keep package version state command-gated and owned by the joint `0.0.9` cut: no slice in this card edits `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock` (Slice 5, [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).

## Non-goals

- **Root `node(id:)` / `nodes(ids:)` refetch fields, the relation-as-Connection implicit upgrade, and the `DjangoNodesField` export.** Those are the [Full Relay story][kanban] ([`WIP-ALPHA-032-0.0.9`][kanban]), which is hard-blocked on this card. This card ships the connection **field** only; [`DjangoNodeField`][glossary-djangonodefield] and the Root-Node entry points land with `032` (see [Decision 2](#decision-2--card-scope-boundary-against-the-sibling-relay-cards)).
- **Connection-aware optimizer planning.** Teaching the walker to recognize `edges { node { ... } }` and plan nested `Prefetch` chains across connection-paginated relations is the sibling [`WIP-ALPHA-033-0.0.9`][kanban] card. This card ships against the existing flat-selection walker ([Decision 11](#decision-11--optimizer-cooperation-against-the-flat-selection-walker-connection-aware-planning-deferred)).
- **Django-model-based GlobalID encoding.** The GlobalID payload format (`products.item:42` vs type-name+id) is the sibling [`WIP-ALPHA-031-0.0.9`][kanban] card. This card uses the GlobalID encoding the Relay foundation already emits; the encoding decision is orthogonal to cursor pagination.
- **`search:` connection argument.** [`Meta.search_fields`][glossary-metasearch_fields] is `0.1.2`; the connection field reserves the seam but generates no `search:` argument in `0.0.9` (per the card body).
- **`aggregates` connection argument and `Meta.aggregate_class` composition.** [`AggregateSet`][glossary-aggregateset] is `0.1.3`; out of scope.
- **`Meta.fields_class` / `FieldSet` field-selection composition.** [`FieldSet`][glossary-fieldset] is `0.1.1`; field-selection layers onto the connection field after this card (the card's Dependencies section defers it to `TODO-BETA-045-0.1.1`).
- **`Meta.cursor_field` for stable column-based cursors.** Opaque offset cursors are the `0.0.9` shape ([Decision 9](#decision-9--opaque-cursor-delegated-to-strawberry-metacursor_field-deferred)); stable cursors live in `BACKLOG.md` item 39 sub-feature 3.
- **`Meta.relation_shapes` (list-vs-connection opt-out on relations).** That governs the relation-as-Connection upgrade, which is [`WIP-ALPHA-032-0.0.9`][kanban].
- **Auto-triggering `finalize_django_types()` from the field constructor.** Deferred ([Decision 12](#decision-12--no-auto-trigger-of-finalize_django_types-for-009)); the explicit-finalize contract is unchanged for `0.0.9`.
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
| (Relay Root `node` / `nodes`) | [`DjangoNodeField`][glossary-djangonodefield] / Full Relay | planned (`0.0.9` — [`WIP-ALPHA-032-0.0.9`][kanban]) |
| (connection-aware optimization) | [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] | planned (`0.0.9` — [`WIP-ALPHA-033-0.0.9`][kanban]) |
| `AdvancedFieldSet` | [`FieldSet`][glossary-fieldset] | planned (`0.1.1`) |
| `AdvancedAggregateSet` / `RelatedAggregate` | [`AggregateSet`][glossary-aggregateset] / [`RelatedAggregate`][glossary-relatedaggregate] | planned (`0.1.3`) |
| `apply_cascade_permissions` | [`apply_cascade_permissions`][glossary-apply_cascade_permissions] | planned (`0.0.10`) |

### From `django-graphene-filters` — borrow the user-facing shape

`AdvancedDjangoFilterConnectionField(ObjectTypeNode)` is the surface to recreate: one declaration over a node type, with the type's declared filter / order sidecars driving argument generation. The Strawberry side is `DjangoConnectionField(GenreType)` returning `DjangoConnection[GenreType]`; the per-type [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] declarations drive `filter:` / `orderBy:` argument generation identically. The Meta-driven argument derivation is the load-bearing borrow — it is what makes the connection field *consume* the sidecars rather than ask the consumer to re-declare them.

### From `strawberry-graphql-django` — borrow the runtime mechanism

`strawberry_django.connection()` builds on Strawberry's native `relay.connection()` over a `ListConnectionWithTotalCount` (a [`relay.ListConnection`][strawberry-relay] subclass that adds `total_count`). This card borrows that mechanism wholesale ([Decision 3](#decision-3--build-on-strawberrys-native-relay-connection-machinery) / [Decision 4](#decision-4--djangoconnectiont-is-a-listconnection-subclass-with-opt-in-totalcount)): Strawberry owns cursor encoding, `pageInfo`, the `first`/`last` guard, and edge mechanics; the package supplies a Django-aware connection resolver that runs the visibility→filter→order pipeline before handing the queryset to `ListConnection.resolve_connection`. We do NOT hand-roll cursor math.

### From `graphene-django` — borrow nothing new

`graphene-django`'s own `DjangoConnectionField` predates the filter-connection composition; the `django-graphene-filters` `AdvancedDjangoFilterConnectionField` is the richer surface and the one we mirror. No separate primitive to borrow here.

### Explicitly do not borrow

- **Graphene's connection internals.** The cursor math, `PageInfo` construction, and edge wrapping come from Strawberry, not a Graphene port.
- **A bespoke cursor scheme.** No `Meta.cursor_field` / stable-column cursors in `0.0.9` ([Decision 9](#decision-9--opaque-cursor-delegated-to-strawberry-metacursor_field-deferred)).
- **strawberry-django's connection-aware optimizer extension here.** That behavior is the sibling [`WIP-ALPHA-033-0.0.9`][kanban] card; this card does not pull it forward.

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

`GenreTypeConnection` carries `edges { node cursor }`, `pageInfo { hasNextPage hasPreviousPage startCursor endCursor }`, and (because `Meta.connection = {"total_count": True}`) `totalCount: Int!`.

### Wiring — sidecar-driven argument generation

The connection field reads the wrapped type's [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] at construction time:

- type declares both → `filter:` AND `orderBy:` arguments present.
- type declares only `filterset_class` → only `filter:` present.
- type declares neither → only the Relay pagination arguments present (`first` / `after` / `last` / `before`).

The `filter:` argument type is the same [`filter_input_type`][glossary-filter_input_type]-derived lazy `Annotated[...]` a hand-written resolver would use; the `orderBy:` argument is `list[order_input_type(...)]`. Two connection fields on the same model therefore resolve to the same `<Type>FilterInputType` / `<Type>OrderInputType` (stable class-derived names — Apollo-cache friendly).

### Opt-in `totalCount`

```python
class GenreType(DjangoType):
    class Meta:
        model = models.Genre
        interfaces = (relay.Node,)
        connection = {"total_count": True}   # adds `totalCount: Int!` to the connection
```

`totalCount` runs `qs.count()` (sync) / `qs.acount()` (async) on the **unpaginated post-filter** queryset, so a paginated UI can show "N of M" without a second round-trip. It is opt-in because the extra count query is not free on large tables; absent the key, the connection has no `totalCount` field.

### Composing with `get_queryset`, filter, and order

The field's resolver runs the pipeline so a consumer needs no manual chaining (contrast the hand-written `@strawberry.field` form documented for the filter / order subsystems):

```text
qs = GenreType.get_queryset(Genre.objects.all(), info)   # 1. visibility (first, always)
qs = GenreFilter.apply_sync(filter, qs, info)            # 2. filter (active-input gates)   — if filter given
qs = GenreOrder.apply_sync(order_by, qs, info)           # 3. orderBy (per-field gates)     — if orderBy given
# 4. Strawberry's ListConnection.resolve_connection slices `qs` by the cursor args.
# totalCount (if opted in) = qs.count() captured BEFORE the slice.
```

### Error shapes

- `DjangoConnectionField(NotADjangoType)` / `DjangoConnectionField(int)` → [`ConfigurationError`][glossary-configurationerror] at the construction site (mirrors [`DjangoListField`][glossary-djangolistfield]'s guard messages).
- `DjangoConnectionField(PlainType)` where `PlainType.Meta.interfaces` omits `relay.Node` → [`ConfigurationError`][glossary-configurationerror] ("a connection field requires a Relay-Node-shaped DjangoType; add `relay.Node` to `Meta.interfaces`").
- `Meta.connection` declared on a type whose `Meta.interfaces` omits `relay.Node` → [`ConfigurationError`][glossary-configurationerror] at type creation (suggest removing the key or adding `relay.Node`).
- `Meta.connection = {"total_count": True, "bogus": 1}` (unknown sub-key) or a non-dict value → [`ConfigurationError`][glossary-configurationerror] at type creation.
- A query passing both `first:` and `last:` → typed error from Strawberry's `ListConnection`, surfaced unchanged in the GraphQL `errors` array.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-030-connection_field-0_0_9.md`** (this document), NOT `docs/spec-connection.md` as the [`WIP-ALPHA-030-0.0.9`][kanban] card's Definition-of-done item names it.

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `WIP-ALPHA-030-0.0.9`, so `<NNN>` is `030` and `<0_0_X>` is `0_0_9`.
- The topic slug is `connection_field` — it names the card's subject (the `DjangoConnectionField` primitive) in snake_case, parallel to the [`DjangoListField`][glossary-djangolistfield] sibling's `spec-020-list_field-0_0_7.md` (`DjangoListField` → `list_field`).
- The card body's `docs/spec-connection.md` is the older unnumbered convention; per [`docs/SPECS/NEXT.md`][next] the card-body reference is rewritten to the canonical name in the same archive sweep / card-completion wrap.

Alternatives considered (and rejected):

- **Honor the card body verbatim with `docs/spec-connection.md`.** Rejected: unnumbered against its card, breaks the structured-filename convention, and would not sort alongside its siblings.
- **Topic slug `connection` or `relay_connection`.** Rejected: `connection` is too terse to disambiguate from the future `relay.py` Root-Node work; `relay_connection` over-claims the Relay-Root surface this card explicitly scopes out ([Decision 2](#decision-2--card-scope-boundary-against-the-sibling-relay-cards)). `connection_field` names exactly the symbol shipped.

### Decision 2 — Card-scope boundary against the sibling Relay cards

`0.0.9` carries four WIP Relay cards. This card ships **only the connection field**; the boundary is explicit:

- **`WIP-ALPHA-030-0.0.9` (this card)** — `DjangoConnectionField` + `DjangoConnection[T]` + the sidecar-derived arguments + opt-in `totalCount`, against the existing flat optimizer walker.
- **`WIP-ALPHA-031-0.0.9`** — Django-model-based GlobalID encoding. Orthogonal; the connection field uses whatever GlobalID the Relay foundation emits.
- **`WIP-ALPHA-032-0.0.9`** — Full Relay story: Root `node(id:)` / `nodes(ids:)`, the relation-as-Connection implicit upgrade, `DjangoNodeField` / `DjangoNodesField`, cursor contracts, schema-validation diagnostics, fakeshop activation. **Hard-blocked on this card.**
- **`WIP-ALPHA-033-0.0.9`** — connection-aware optimizer planning. Ships in parallel; takes over the walker for nested `edges { node }` without retrofit.

Justification:

- The card body and `032`'s body both name this dependency direction (`032` "blocked on `WIP-ALPHA-030-0.0.9`"; this card ships "against the existing flat-selection walker and the connection-aware walker takes over when 032 lands" — the card body's own seam note). Pinning the boundary keeps the spec scoped to what `030` actually ships and prevents pulling `032`'s eight-goal umbrella into one card.
- `DjangoNodeField` and the Root-Node entry points need the GlobalID-encoding decision (`031`) settled first; sequencing them after the connection field (which does not need that decision) is the card-order rationale `031`'s body records.

Alternatives considered (and rejected):

- **Fold the Full Relay story into this spec.** Rejected: `032` is an L-XL eight-goal card with its own spec (`docs/spec-relay_connection.md` per its body); one spec per WIP card is the [`docs/SPECS/NEXT.md`][next] flow, and the connection field is independently shippable and independently valuable.

### Decision 3 — Build on Strawberry's native Relay connection machinery

The connection field is implemented on top of [`strawberry.relay`][strawberry-relay]'s `connection()` / `ListConnection` / `Edge` / `PageInfo`, NOT a hand-rolled cursor implementation. Strawberry (locked at `0.316.0`) owns: cursor encoding/decoding (`to_base64` / `from_base64`), `ListConnection.resolve_connection(nodes, *, info, before, after, first, last)`, the `first` + `last` mutually-exclusive guard, and the four `pageInfo` fields with their spec-mandated semantics (including "resolve `hasNextPage` correctly even when not requested").

Justification:

- [`START.md`][start]'s rule: "Strawberry is the engine; DRF is the shape." Re-implementing cursor math would duplicate a correct, spec-compliant implementation the engine already ships and would drift from the Relay spec over time. The package's value is the Django-aware *queryset pipeline* (visibility → filter → order) and the *Meta-driven argument generation*, not cursor arithmetic.
- This is the same mechanism `strawberry-graphql-django` uses (`ListConnectionWithTotalCount` over `relay.ListConnection`), so the behavioral borrow is honest and battle-tested.
- It keeps the package's connection surface forward-compatible: when Strawberry hardens cursor behavior, the package inherits it.

Alternatives considered (and rejected):

- **Hand-roll the cursor / pageInfo math.** Rejected: re-implements engine behavior, invites Relay-spec drift, and balloons the test surface (every `pageInfo` edge case becomes ours to pin rather than Strawberry's).
- **Wrap graphene-django's connection field shape.** Rejected: that is a Graphene primitive on a Graphene runtime; the package's whole reason for existing is to drop the Graphene runtime.

### Decision 4 — `DjangoConnection[T]` is a `ListConnection` subclass with opt-in `totalCount`

[`DjangoConnection`][glossary-djangoconnection] is a generic `DjangoConnection[NodeType]` subclass of [`strawberry.relay.ListConnection`][strawberry-relay]`[NodeType]` that adds an opt-in `total_count` field. It is the return annotation a consumer writes: `all_genres: DjangoConnection[GenreType] = DjangoConnectionField(GenreType)`.

`totalCount` resolves off a **context stash** the field resolver populates with the unpaginated post-filter count, NOT a second `qs.count()` at edge-resolution time:

- the field resolver computes `qs.count()` (sync) / `await qs.acount()` (async) on the post-filter pre-slice queryset and stashes it on `info.context` (a per-request, connection-field-keyed slot, parallel to how the optimizer stashes plan state on `info.context`);
- `DjangoConnection.total_count`'s resolver reads the stashed value;
- when `Meta.connection` omits `total_count` (or omits the key), the `totalCount` field is absent from the connection type — it is conditionally included, not always present-but-null.

Justification:

- A `ListConnection` subclass is exactly `strawberry-django`'s `ListConnectionWithTotalCount` shape — the proven place to add `total_count` without disturbing cursor mechanics.
- Stashing the count avoids a redundant query: the resolver already has the post-filter queryset in hand to slice; counting it once and reading the stash is cheaper than re-counting at field-resolution time, and it guarantees the count matches the exact queryset that was paginated (no race between two `count()` calls under a `get_queryset` that embeds request state).
- Conditional inclusion (field absent unless opted in) matches the card's "opt-in via `Meta.connection`" wording and keeps the default connection lean (no count query on every request).

Alternatives considered (and rejected):

- **Always-on `totalCount`.** Rejected: a `count()` on every connection query is a real cost on large tables; the card specifies opt-in.
- **Re-count at `total_count` field-resolution time.** Rejected: a second query, and it can disagree with the paginated set when `get_queryset` embeds request-scoped state.
- **A standalone (non-`ListConnection`) connection type.** Rejected: would re-implement `edges` / `pageInfo` / cursor wiring Strawberry already provides on `ListConnection`.

### Decision 5 — Factory-function mechanism mirroring `DjangoListField`

`DjangoConnectionField` is a **factory function** (PascalCase for graphene-django parity), not a class:

```python
def DjangoConnectionField(  # noqa: N802
    target_type: type,
    *,
    resolver: Callable | None = None,
    total_count: bool | None = None,   # explicit override; defaults from Meta.connection
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Sequence[object] = (),
) -> Any: ...
```

It runs the [`DjangoListField`][glossary-djangolistfield] guard sequence — `inspect.isclass(target_type)` → `issubclass(target_type, DjangoType)` → own-class `definition.origin is target_type` → callable `resolver` — plus a Relay-Node-shaped guard (`relay.Node in interfaces`), then returns a Strawberry `relay.connection(...)`-shaped field whose resolver runs the [Decision 7](#decision-7--composition-order-visibilityfilterorderslice) pipeline.

Justification:

- Strawberry's class-body walk picks up the factory's return value the same way it picks up `strawberry.field(...)` / `relay.connection(...)` — the consumer writes `attr: Annotation = DjangoConnectionField(T)`, identical in shape to the shipped `DjangoListField(T)`. One mental model across both fields.
- Constructor-site guards fail at the line that wrote `DjangoConnectionField(...)` rather than at finalize time — the same fail-loud-early property the list-field guards deliver.

Alternatives considered (and rejected):

- **A `DjangoConnectionField` class (descriptor).** Rejected: diverges from the shipped `DjangoListField` factory shape for no gain; Strawberry's field machinery already consumes a factory return value cleanly.

### Decision 6 — Sidecar-derived `filter:` / `orderBy:` arguments reuse the shipped helper machinery

The field auto-derives its `filter:` and `orderBy:` arguments from the wrapped type's [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] by reusing the **already-shipped** [`filter_input_type`][glossary-filter_input_type] / [`order_input_type`][glossary-order_input_type] machinery — the same lazy `Annotated["<Name>InputType", strawberry.lazy(...)]` forms a hand-written resolver uses, and the same `_helper_referenced_filtersets` / `_helper_referenced_ordersets` orphan-validation ledgers.

Justification:

- The filter / order subsystems already produce stable, class-derived input-type names materialized as module globals by [`finalize_django_types`][glossary-finalize_django_types] phase 2.5. Reusing that machinery means a connection field and a hand-written resolver on the same type resolve to the *same* `<Type>FilterInputType` (Apollo-cache friendly, no duplicate types) and inherit the active-input gating, `check_*_permission` propagation, and [`RelatedFilter`][glossary-relatedfilter] / [`RelatedOrder`][glossary-relatedorder] visibility scoping unchanged.
- Registering the derived sets against the existing `_helper_referenced_*` ledgers keeps finalize-time orphan validation honest: a connection field referencing a FilterSet/OrderSet not wired via `Meta.*_class` fails loud, exactly as a `filter_input_type(...)` call would.

Alternatives considered (and rejected):

- **Generate fresh per-connection-field input types.** Rejected: duplicate GraphQL input types for the same model, breaking Apollo cache reuse and the stable-name contract the filter/order specs pinned.
- **Accept the filterset/orderset as explicit `DjangoConnectionField(T, filters=…, order=…)` arguments only.** Rejected as the *default*: the card's borrow is Meta-driven derivation. An explicit override (`filters=` / `order=`) MAY be offered as an escape hatch for a non-default set, but the no-argument form reads the type's `Meta` — that is the whole point.

### Decision 7 — Composition order: visibility→filter→order→slice

The connection resolver applies, in this exact order on the resolved queryset:

1. **`target_type.get_queryset(qs, info)`** — visibility scoping (always first; the scope filter, order, and the cursor slice all narrow, never widen).
2. **`FilterSet.apply_sync/async(filter, qs, info)`** — active-input filter gates (only when a `filter:` value is given).
3. **`OrderSet.apply_sync/async(order_by, qs, info)`** — per-field order gates (only when an `orderBy:` value is given).
4. **cursor slice** — hand the unpaginated post-filter-post-order queryset to Strawberry's `ListConnection.resolve_connection`; `totalCount` (if opted in) is the `count()` of the queryset entering step 4, captured before the slice.

Justification:

- This is the card body's pinned composition order, and it is correct for three independent reasons: (a) visibility must run first so a filter cannot match a parent through a child the visibility hook would hide (the [`RelatedFilter`][glossary-relatedfilter] contract from the filter spec); (b) the optimizer plans against the pre-slice queryset, so visibility/filter/order must all be applied before the slice for the plan to be accurate; (c) `totalCount` is the count of the *post-filter, pre-pagination* set so paginated UIs can show "N of M" — counting after the slice would always equal the page size.
- It is the exact order the `0.0.8` filter/order subsystems already document for hand-written resolvers (`get_queryset` → `apply_sync(filter)` → `apply_sync(order_by)`); the connection field automates the same chain, so a consumer migrating a hand-written resolver to a `DjangoConnectionField` sees identical semantics.

Alternatives considered (and rejected):

- **Filter before visibility.** Rejected: a filter could match rows the visibility hook hides, leaking existence.
- **Count after the slice.** Rejected: `totalCount` would equal the page size, defeating its purpose.
- **Order before filter.** Rejected: ordering a not-yet-filtered set wastes work and can change which rows the cursor slice sees in pathological tie cases; filter-then-order is the standard SQL composition.

### Decision 8 — `Meta.connection` opt-in `totalCount` key: net-new `ALLOWED_META_KEYS` entry

`Meta.connection` lands **directly** in [`ALLOWED_META_KEYS`][base] (NOT a [`DEFERRED_META_KEYS`][base] promotion, mirroring [`spec-029`][spec-029]'s net-new-key rule for `nullable_overrides` / `required_overrides`). It accepts a dict; for `0.0.9` the only recognized sub-key is `{"total_count": bool}`. Validation (a new `_validate_connection` helper called from [`_validate_meta`][base], structurally modeled on `_validate_filterset_class`):

- value must be a dict; non-dict raises [`ConfigurationError`][glossary-configurationerror].
- unknown sub-keys raise (typo guard — only `total_count` is recognized in `0.0.9`).
- `total_count` value must be a bool.
- the key is rejected on a type whose `Meta.interfaces` omits `relay.Node` — a connection-only setting on a non-connectable type is a configuration error (suggest removing the key or adding `relay.Node`).

Justification:

- `Meta.connection` was never reserved in `DEFERRED_META_KEYS`; it is a net-new key whose feature ships in the same card that adds it — exactly the [`spec-029`][spec-029] [Decision 6][spec-029] situation, so it goes straight into `ALLOWED_META_KEYS` and the deferred-set machinery is not involved.
- A dict (rather than a flat `Meta.total_count = True`) is forward-compatible: `032`'s Full Relay story extends `Meta.connection` with more sub-keys (the card body shows `Meta.connection = {"total_count": True}` as the canonical shape and reserves the dict for growth). A flat boolean would force a second key per future option.
- Rejecting the key on a non-Relay type catches the most likely misuse (declaring `connection` settings on a type that can never be a connection) at type-creation time, fail-loud per the package's validation posture.

Alternatives considered (and rejected):

- **A flat `Meta.total_count = True` boolean.** Rejected: not forward-compatible; `032` needs the dict for additional connection options.
- **`total_count` only as a `DjangoConnectionField(T, total_count=True)` constructor argument, no `Meta` key.** Rejected as the *primary* surface: the card pins `Meta.connection`. The constructor `total_count=` override is offered as a per-field escape hatch ([Decision 5](#decision-5--factory-function-mechanism-mirroring-djangolistfield)), defaulting from `Meta.connection`.
- **Always-on `totalCount`, no opt-in.** Rejected per [Decision 4](#decision-4--djangoconnectiont-is-a-listconnection-subclass-with-opt-in-totalcount).

### Decision 9 — Opaque cursor delegated to Strawberry; `Meta.cursor_field` deferred

Cursors are the opaque base64 offset cursors Strawberry's [`relay.ListConnection`][strawberry-relay] emits by default (`b64("arrayconnection:N")`). They are documented as opaque — clients must not parse them. Stable column-based cursors (`Meta.cursor_field`) are explicitly out of scope for `0.0.9`.

Justification:

- Opaque offset cursors are the Relay-spec-compliant default and are what `ListConnection` ships; delegating to them keeps cursor behavior the engine's responsibility ([Decision 3](#decision-3--build-on-strawberrys-native-relay-connection-machinery)).
- Stable cursors are a meaningfully larger design (deterministic-column keying, tie-breaking, cursor stability across inserts/deletes) — the card body and `032`'s body both route it to `BACKLOG.md` item 39 sub-feature 3. Pulling it into the foundational connection field would bloat the slice.

Alternatives considered (and rejected):

- **Ship `Meta.cursor_field` now.** Rejected: its own design space; not required for the foundational connection field and explicitly deferred by both the `030` and `032` card bodies.

### Decision 10 — Sync + async resolver paths reuse the Relay-foundation `get_queryset` helpers

The connection resolver has sync and async variants mirroring [`DjangoListField`][glossary-djangolistfield]'s dispatch: visibility runs through `_apply_get_queryset_sync` / `_apply_get_queryset_async` ([`types/relay.py`][relay]); filter / order run through the `apply_sync` / `apply_async` classmethod pairs; the cursor slice runs through `ListConnection.resolve_connection`. A sync resolver context that meets an async `get_queryset` (a coroutine return) raises [`SyncMisuseError`][glossary-syncmisuseerror], reusing the foundation contract (the unawaited coroutine is closed before the raise so Python emits no "coroutine was never awaited" warning).

Justification:

- The Relay foundation already solved sync/async `get_queryset` dispatch and the sync-meets-async misuse; reusing `_apply_get_queryset_sync` / `_apply_get_queryset_async` keeps one source of truth and inherits [`SyncMisuseError`][glossary-syncmisuseerror] for free.
- The filter/order subsystems already ship the `apply_sync` / `apply_async` pair for exactly this composition; the connection field calls the matching variant for its execution context.

Alternatives considered (and rejected):

- **Sync-only connection resolver.** Rejected: both upstreams and the rest of this package support async; a sync-only connection field would be a regression against the `DjangoListField` and Relay-node async support already shipped.
- **A new connection-specific `get_queryset` applier.** Rejected: duplicates the foundation helpers and risks divergence on the `SyncMisuseError` contract.

### Decision 11 — Optimizer cooperation against the flat-selection walker; connection-aware planning deferred

In `0.0.9` the connection field rides the existing **root-gated flat-selection** [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]: a root `DjangoConnectionField` selection's resolved pre-slice queryset is planned (`select_related` / `prefetch_related` / [`only()`][glossary-only-projection]) exactly as a root `list[T]` resolver's queryset is, because the optimizer's [root gate][optimizer-extension] (`info.path.prev is None`) fires on the connection field's root resolver and sees the queryset before the cursor slice. The card ships **no walker change**. Nested `edges { node { ... } }` connection selections are functional but NOT connection-aware-planned — that is the sibling [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] card ([`WIP-ALPHA-033-0.0.9`][kanban]).

Justification:

- The card body's own seam note: "this card ships against the existing flat-selection walker and the connection-aware walker takes over when 032 [033] lands." The two cards are scoped to ship in parallel; `030` must not block on the walker work.
- The root-gated optimizer already plans any root queryset, so a root connection field gets `select_related` / `prefetch_related` / `only()` planning for free as long as the resolved queryset reaches the root resolver before the slice — which [Decision 7](#decision-7--composition-order-visibilityfilterorderslice) guarantees.
- Naming the nested-connection-planning gap honestly (rather than implying full optimization) is the [`docs/SPECS/NEXT.md`][next] "no silent caps" discipline: the constraint is documented in [`docs/GLOSSARY.md`][glossary] and [Edge cases](#edge-cases-and-constraints), and a [Strictness mode][glossary-strictness-mode] `"raise"` test pins that unplanned nested-connection access still surfaces as an N+1 (guarding the seam `033` will close).

Alternatives considered (and rejected):

- **Pull connection-aware planning into this card.** Rejected: it is a separate M-sized card (`033`) with its own walker / plans / extension changes and mirrored tests; folding it in violates the one-card-one-spec scope and couples the connection field to walker internals.
- **Block the connection field until `033` lands.** Rejected: root connection fields are useful and optimized today via the flat walker; the nested-connection gap is a known follow-up, not a blocker.

### Decision 12 — No auto-trigger of `finalize_django_types()` for `0.0.9`

The connection field does NOT auto-trigger [`finalize_django_types`][glossary-finalize_django_types] from its constructor for `0.0.9`. The explicit-finalize contract is unchanged: the consumer calls `finalize_django_types()` once during single-threaded schema setup, as for [`DjangoListField`][glossary-djangolistfield] and every Relay-Node type today.

Justification:

- The card's Foundation-slice seam names the auto-trigger as a possibility ("`finalize_django_types()` is the single architectural entry point that `DjangoConnectionField(DjangoType)` (and `DjangoNodeField`) will auto-trigger as their wrapper") but immediately qualifies it: "an auto-trigger wrapper must respect the single-threaded-setup window: either be constrained to schema-construction time, or acquire a real lock around the finalizer." That locking design is non-trivial and is shared with [`DjangoNodeField`][glossary-djangonodefield], which lands with the [Full Relay story][kanban] (`032`).
- [`DjangoListField`][glossary-djangolistfield] — the directly analogous shipped field — does NOT auto-trigger finalize; matching its posture keeps the `0.0.9` connection field a clean parallel and avoids introducing a finalizer-locking surface this card does not need.
- Deferring the auto-trigger to `032` (where `DjangoNodeField` forces the design anyway) means one design pass for both fields, not two.

Alternatives considered (and rejected):

- **Auto-trigger finalize from the field constructor now.** Rejected: introduces the single-threaded-setup-window / locking problem for a field that works fine with explicit finalize, and would diverge from the `DjangoListField` precedent for no `0.0.9` benefit.

### Decision 13 — Version bumps are owned by the joint `0.0.9` cut

No slice in this card edits `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock`; no [`CHANGELOG.md`][changelog] release heading is promoted. CHANGELOG bullets land under `[Unreleased]`. The `0.0.8` → `0.0.9` bump is owned by the **joint cut** that releases the four WIP cards ([`WIP-ALPHA-030/031/032/033-0.0.9`][kanban]) together with the already-shipped [`DONE-029-0.0.9`][kanban].

Justification:

- This is the exact precedent [`spec-029`][spec-029] [Decision 11][spec-029] set: `0.0.9` is a shared patch line across four sibling cards, so the version bump belongs to whichever cut releases them, not to any single card's slice. The on-disk version is still `0.0.8`; several `0.0.9`-tagged surfaces (`Meta.nullable_overrides`, `inspect_django_type`) already ship under `[Unreleased]` against the unchanged version, confirming the joint-cut posture.
- [`docs/SPECS/NEXT.md`][next] Step 6 mandates this Decision explicitly when multiple WIP cards share the target patch version: "include a Decision that explicitly defers the `pyproject.toml` / `__version__` / `tests/base/test_init.py` version bump to the joint cut card. The Slice 5 / Definition of done checklist must NOT bump the version."

Alternatives considered (and rejected):

- **Bump the version in this card's Slice 5.** Rejected: would race the three sibling cards for the same bump and promote a release heading before the cohort is cut; the joint cut is the single owner.

### Decision 14 — `connection.py` flat module and the public-export gate

The connection field ships as the flat module [`django_strawberry_framework/connection.py`][connection] (the [`docs/TREE.md`][tree] target layout already reserves the `connection.py [alpha]` slot), with the flat test file [`tests/test_connection.py`][test-connection], mirroring the [`DjangoListField`][glossary-djangolistfield] / [`tests/test_list_field.py`][test-list-field] single-file pairing. `DjangoConnectionField` and `DjangoConnection` are promoted to the [`django_strawberry_framework`][package-init] public surface **only when end-to-end schema usage is tested** (the card DoD's "Promote only when end-to-end schema usage is tested" — satisfied by Slice 4's live HTTP round-trip).

The card DoD asks "Decide whether full Relay support belongs here or a separate `relay/` subpackage." **Decision: `connection.py` now; the Root-Node surface (`DjangoNodeField` / `DjangoNodesField` / GlobalID decode dispatch) lands in a separate `relay.py` with `032`.** If the combined connection + Root-Node surface grows past ~one module, it forks into a `relay/` subpackage at that time (the [`START.md`][start] "fork a subsystem into its own spec/module mid-stream when a slice grows past ~one module" advice, and the parallel to how `filters/` / `orders/` are subpackages while `list_field.py` stays flat).

Justification:

- A flat `connection.py` matches the shipped `list_field.py` (a single-file Layer-3 module) and the [`docs/TREE.md`][tree] reservation; a subpackage is unwarranted for one factory + one connection type.
- The public-export-on-tested-usage gate is the card DoD's explicit promotion discipline (it also governed `DjangoListField`): a symbol reaches `__init__.py` only after a live test proves the end-to-end shape, so the public surface never advertises an untested field.
- `032`'s Files-likely-touched list already names a *new* `django_strawberry_framework/relay.py` for the Root-Node work — keeping the connection field in `connection.py` and the Root-Node fields in `relay.py` matches `032`'s own plan and leaves the fork-to-subpackage decision for when the surface actually demands it.

Alternatives considered (and rejected):

- **A `relay/` subpackage now holding `connection.py` + a future `node.py`.** Rejected: premature; one module of connection code does not justify a subpackage, and `032` can introduce `relay.py` (or fork the subpackage) when the Root-Node surface lands.
- **Promote `DjangoConnectionField` to the public surface before the live test.** Rejected: violates the card's tested-usage promotion gate.

## Implementation plan

The card ships as **four sequential functional slices plus a doc + card-completion wrap**. Each functional slice is one PR; later slices build on earlier ones. Line deltas are estimates.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — `DjangoConnection[T]` + `totalCount` + `Meta.connection` validation | [`django_strawberry_framework/connection.py`][connection] (new — `DjangoConnection` class + context stash), [`django_strawberry_framework/types/base.py`][base] (`ALLOWED_META_KEYS` += `"connection"` + `_validate_connection`), [`tests/test_connection.py`][test-connection] (new), [`tests/types/test_base.py`][test-types-base] (extend) | ~8 (`DjangoConnection[T]` shape; `totalCount` present-only-when-opted-in; `Meta.connection` dict / sub-key / non-Relay-type validation; `ALLOWED_META_KEYS` membership) | `+140 / -2` |
| 2 — `DjangoConnectionField` factory + sidecar args + composition order + sync/async | [`django_strawberry_framework/connection.py`][connection] (factory + resolver + arg derivation), [`tests/test_connection.py`][test-connection] (extend) | ~14 (constructor guards: non-class / non-`DjangoType` / non-own-class / non-Relay; arg presence/absence by sidecar; composition-order unit; `totalCount` stash captured pre-slice; sync + async dispatch; `SyncMisuseError` on async-`get_queryset`-in-sync) | `+220 / -0` |
| 3 — optimizer cooperation (flat walker) | [`tests/test_connection.py`][test-connection] (extend) or [`tests/optimizer/`][test-extension] (cooperation test) — **no source change**; documents the flat-walker seam | ~3 (root connection field → planned root queryset; strictness `"raise"` surfaces an unplanned nested-connection access as N+1) | `+60 / -0` |
| 4 — live HTTP coverage | [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] (a root `DjangoConnectionField(GenreType)` + `GenreType.Meta.connection`), [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] (extend) | ~4 (filter+orderBy+first+after round-trip incl. `totalCount`; `first`+`last` typed-error; `first: 0` empty-edges shape) | `+120 / -2` |
| 5 — doc updates + card-completion wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`TODAY.md`][today], [`README.md`][readme], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban], [`django_strawberry_framework/__init__.py`][package-init] (public-export promotion) | 0 (doc-only + export) | `+90 / -25` |

Total expected delta: ~640 lines across four functional slices plus the wrap. No version-file edits (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).

## Edge cases and constraints

- **`first: 0`** — returns empty `edges` plus a valid `pageInfo` (`hasNextPage` reflects whether rows exist beyond the zero-width slice). Delegated to Strawberry's `ListConnection`; pinned by a Slice 4 live test.
- **`first: N` with N greater than the remaining rows** — returns the actual remainder (not an error). Delegated to `ListConnection`.
- **`after:` cursor for a row that no longer exists** — the offset cursor falls through to the next existing row; no error. (Opaque-offset-cursor behavior per [Decision 9](#decision-9--opaque-cursor-delegated-to-strawberry-metacursor_field-deferred); stable-cursor semantics are out of scope.)
- **Both `first:` and `last:` in one query** — Strawberry's `ListConnection` raises a typed error; the field surfaces it in the GraphQL `errors` array unchanged ([Decision 3](#decision-3--build-on-strawberrys-native-relay-connection-machinery)). Pinned by a Slice 4 live test.
- **`totalCount` requested but `Meta.connection` omits `total_count`** — the `totalCount` field is absent from the connection type, so the query fails GraphQL validation (unknown field), not at runtime. Conditional inclusion per [Decision 4](#decision-4--djangoconnectiont-is-a-listconnection-subclass-with-opt-in-totalcount).
- **`totalCount` under a `get_queryset` that embeds request-scoped state** — the count is captured off the *same* post-filter queryset that is sliced (the context stash), so the count cannot disagree with the paginated set. Pinned by the Slice 1 stash test.
- **A connection field over a type with no `filterset_class` / `orderset_class`** — the `filter:` / `orderBy:` argument is simply absent; the field still paginates. Pinned by a Slice 2 arg-absence test.
- **An async `get_queryset` invoked from a sync GraphQL execution** (`schema.execute_sync` / the sync `/graphql/` view) — raises [`SyncMisuseError`][glossary-syncmisuseerror] (the unawaited coroutine is closed first), reusing the Relay-foundation contract ([Decision 10](#decision-10--sync--async-resolver-paths-reuse-the-relay-foundation-get_queryset-helpers)). The async `get_queryset` path is genuinely unreachable from the sync `GraphQLView` mounted at `/graphql/`, so its coverage lands in [`tests/test_connection.py`][test-connection] (the [`DjangoListField`][glossary-djangolistfield] precedent for the same unreachability).
- **Nested connection selection (`edges { node { relConnection { edges { node } } } }`)** — functional but NOT connection-aware-planned in `0.0.9`; a [Strictness mode][glossary-strictness-mode] `"raise"` run surfaces the unplanned nested access as an N+1 (Slice 3 guards this seam). The connection-aware walker ([`WIP-ALPHA-033-0.0.9`][kanban]) closes the gap without retrofit. No silent cap — named in [`docs/GLOSSARY.md`][glossary].
- **Two `DjangoConnectionField`s on the same model** — both resolve to the same `<Type>FilterInputType` / `<Type>OrderInputType` (stable class-derived names via the shared [`filter_input_type`][glossary-filter_input_type] / [`order_input_type`][glossary-order_input_type] machinery), so the schema carries one input type per model, not one per field ([Decision 6](#decision-6--sidecar-derived-filter--orderby-arguments-reuse-the-shipped-helper-machinery)).
- **A connection field over a [`Meta.primary`][glossary-metaprimary]`= False` secondary type** — supported; the field wraps the type it is given, and relation resolution still routes through the model's primary. The relation-as-Connection *implicit upgrade* (which must choose a type) is [`WIP-ALPHA-032-0.0.9`][kanban]'s problem, not this card's.
- **`Meta.connection` on a non-Relay type** — rejected at type creation with [`ConfigurationError`][glossary-configurationerror] ([Decision 8](#decision-8--metaconnection-opt-in-totalcount-key-net-new-allowed_meta_keys-entry)); a connection setting on a type that can never be a connection is a config error, not a silent no-op.

## Test plan

Tests live across the package-internal `tests/` tree and the `examples/fakeshop/test_query/` tree, per [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Coverage that can be earned by a real GraphQL query is earned there first; the rest lands in [`tests/test_connection.py`][test-connection].

### Slice 1 — `tests/test_connection.py` (new) + `tests/types/test_base.py` (extend)

- `test_django_connection_is_listconnection_subclass` — `DjangoConnection[T]` is a [`strawberry.relay.ListConnection`][strawberry-relay]`[T]` subclass and carries the generic parameter.
- `test_total_count_present_only_when_opted_in` — a type with `Meta.connection = {"total_count": True}` exposes `totalCount` on its connection; a type without the key (or with `{"total_count": False}`) does not.
- `test_total_count_reads_context_stash` — the `total_count` resolver reads the stashed unpaginated count, not a re-count.
- `test_meta_connection_in_allowed_meta_keys` (in `tests/types/test_base.py`) — `"connection"` is in [`ALLOWED_META_KEYS`][base] and NOT in [`DEFERRED_META_KEYS`][base] (pins [Decision 8](#decision-8--metaconnection-opt-in-totalcount-key-net-new-allowed_meta_keys-entry)).
- `test_meta_connection_non_dict_raises` / `test_meta_connection_unknown_subkey_raises` / `test_meta_connection_non_relay_type_raises` — the three `_validate_connection` failure modes raise [`ConfigurationError`][glossary-configurationerror].

### Slice 2 — `tests/test_connection.py` (extend)

- `test_connection_field_requires_djangotype` / `test_connection_field_requires_djangotype_subclass` / `test_connection_field_requires_own_class_definition` / `test_connection_field_requires_relay_node` — the four constructor guards raise [`ConfigurationError`][glossary-configurationerror] at the construction site.
- `test_connection_field_derives_filter_arg_from_filterset` / `test_connection_field_derives_orderby_arg_from_orderset` / `test_connection_field_omits_args_without_sidecars` — argument presence/absence tracks the wrapped type's [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class].
- `test_connection_field_registers_sidecars_against_orphan_ledgers` — the derived FilterSet/OrderSet are recorded against `_helper_referenced_filtersets` / `_helper_referenced_ordersets` so [`finalize_django_types`][glossary-finalize_django_types] orphan validation stays honest.
- `test_connection_resolver_composition_order` — a unit asserting `get_queryset` runs before `filter` runs before `order` runs before the slice, and that `totalCount` is captured before the slice.
- `test_connection_resolver_sync_dispatch` / `test_connection_resolver_async_dispatch` — sync execution uses `apply_sync` + `_apply_get_queryset_sync`; async execution awaits `apply_async` + `_apply_get_queryset_async`.
- `test_connection_sync_context_async_get_queryset_raises_sync_misuse` — a sync execution against an async `get_queryset` raises [`SyncMisuseError`][glossary-syncmisuseerror].

### Slice 3 — optimizer cooperation

- `test_root_connection_field_queryset_is_planned` — a root `DjangoConnectionField` selection's pre-slice queryset receives `select_related` / `prefetch_related` / [`only()`][glossary-only-projection] planning from the root-gated [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] (the flat walker, [Decision 11](#decision-11--optimizer-cooperation-against-the-flat-selection-walker-connection-aware-planning-deferred)).
- `test_nested_connection_unplanned_raises_under_strictness` — under [Strictness mode][glossary-strictness-mode] `"raise"`, an unplanned nested `edges { node { relConnection } }` access surfaces as an N+1 `OptimizerError` — pinning the seam [`WIP-ALPHA-033-0.0.9`][kanban] will close (no silent cap).

### Slice 4 — `examples/fakeshop/test_query/test_library_api.py` (extend)

Against a root `DjangoConnectionField(GenreType)` (Relay-Node-shaped, with `GenreFilter` / `GenreOrder` sidecars and `Meta.connection = {"total_count": True}`), exposed on the `library` `Query` and reached through the live `/graphql/` HTTP stack (per the fakeshop reload pattern):

- `test_genre_connection_full_round_trip` — query `edges { node { id name } } pageInfo { hasNextPage endCursor } totalCount` with `filter:` + `orderBy:` + `first:` + `after:`; assert correct ordering, page boundaries, `endCursor`, and `totalCount` equal to the unpaginated post-filter count; assert no `errors`.
- `test_genre_connection_first_and_last_rejected` — passing both `first:` and `last:` returns a GraphQL `errors` entry (the typed `ListConnection` guard).
- `test_genre_connection_first_zero_empty_edges` — `first: 0` returns empty `edges` plus a valid `pageInfo`.

A check before declaring the suite undisturbed: a new reachable root field changes the registered-type count and the full SDL. Confirm no existing `test_query/` test snapshots the whole SDL or asserts a registered-type count (the `0.0.8` filter/order live tests are per-field, not snapshots); re-run the check at implementation time.

## Doc updates

Each slice owns its own doc edits. The CHANGELOG-edit permission comes from Slice 5's doc-update step per the explicit-instruction rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — **AGENTS.md prohibits `CHANGELOG.md` edits without permission, and this spec's Slice 5 grants that permission** for the `DjangoConnectionField` / `DjangoConnection` / `Meta.connection` bullet.

- **Slice 5 — GLOSSARY**
  - [`docs/GLOSSARY.md`][glossary]: flip [`DjangoConnectionField`][glossary-djangoconnectionfield] and [`DjangoConnection`][glossary-djangoconnection] from `planned for 0.0.9` to `shipped (0.0.9)` in the [Index][glossary-index] table and entry bodies; add the sidecar-derived-argument / composition-order / opt-in-`totalCount` detail and the flat-walker alpha-constraint note to the `DjangoConnectionField` body; add a `## Meta.connection` entry (status `shipped (0.0.9)`) describing the `{"total_count": bool}` shape and the Relay-Node requirement, with Index + "Relay" / "Type generation" [Browse by category][glossary] rows. Leave [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] `planned for 0.0.9`.
- **Slice 5 — package docs**
  - [`docs/README.md`][docs-readme]: move `DjangoConnectionField` to the shipped surface; note the sidecar-derived `filter:` / `orderBy:` arguments and opt-in `totalCount`.
  - [`docs/TREE.md`][tree]: list [`connection.py`][connection] in the current on-disk layout (drop the `[alpha]` planned tag) and the mirrored [`tests/test_connection.py`][test-connection].
  - [`TODAY.md`][today]: move `DjangoConnectionField` off the products "still waiting for" list (or note its activation tracking, lit up at fakeshop activation per [`TODO-BETA-051-0.1.5`][kanban]); keep the file products-centric.
  - [`README.md`][readme]: update the status paragraph's shipped-surface line only if it enumerates the connection field.
  - [`CHANGELOG.md`][changelog]: `### Added` bullet under `[Unreleased]` (the permission grant above). No version-heading promotion (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).
- **Slice 5 — card-completion wrap**
  - [`KANBAN.md`][kanban]: move [`WIP-ALPHA-030-0.0.9`][kanban] to Done with the next `DONE-NNN-0.0.9` id; add / confirm the card body's spec reference points at [`docs/spec-030-connection_field-0_0_9.md`][spec-030]; rewrite the card-body DoD's unnumbered `docs/spec-connection.md` reference to the canonical name. No version-file edits.

## Risks and open questions

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **GLOSSARY has no entry yet for `Meta.connection`.** The net-new key has no [`docs/GLOSSARY.md`][glossary] heading at spec-authoring time ([`docs/SPECS/NEXT.md`][next] Step 7 defers glossary anchoring to the companion CSV until the heading ships). Preferred answer: the entry is authored during Slice 5's doc-update step and is therefore **omitted from the companion [`docs/spec-030-connection_field-0_0_9-terms.csv`][spec-030-terms]** so [`scripts/check_spec_glossary.py`][check-spec-glossary] stays green (the checker requires every CSV term to resolve to a real glossary heading). Fallback: if the maintainer wants the heading before implementation, a doc-only change adds a `## Meta.connection` (`planned for 0.0.9`) heading, after which the CSV can carry the row.
- **Card body names an unnumbered spec filename.** The card's DoD says "Add `docs/spec-connection.md`." Preferred answer per [Decision 1](#decision-1--spec-filename-and-canonical-naming): this spec is `docs/spec-030-connection_field-0_0_9.md`; the card-body reference is rewritten to the canonical name in the [`docs/SPECS/NEXT.md`][next] Step-8 archive sweep / card-completion wrap. Fallback: none — the structured-filename convention is unambiguous.
- **Explicit `filters=` / `order=` constructor overrides vs Meta-only derivation.** Preferred answer per [Decision 6](#decision-6--sidecar-derived-filter--orderby-arguments-reuse-the-shipped-helper-machinery): the default reads `Meta.filterset_class` / `Meta.orderset_class`; an explicit `DjangoConnectionField(T, filters=…, order=…)` override is offered as an escape hatch for a non-default set. Fallback: if the override proves confusing (two ways to specify the same thing), drop it and require the `Meta` declaration — the Meta-driven form is the borrow and the primary surface.
- **`totalCount` context-stash keying.** Preferred answer per [Decision 4](#decision-4--djangoconnectiont-is-a-listconnection-subclass-with-opt-in-totalcount): the count is stashed on `info.context` keyed per connection-field-occurrence (so two connection fields in one query do not collide), parallel to the optimizer's `info.context` plan stash. Fallback: if per-occurrence keying proves fragile under aliasing, compute `total_count` directly in the connection type's resolver from the queryset Strawberry passes to `resolve_connection` (a re-count) — slower but collision-proof.
- **`Meta.connection` dict vs flat boolean.** Preferred answer per [Decision 8](#decision-8--metaconnection-opt-in-totalcount-key-net-new-allowed_meta_keys-entry): a forward-compatible dict (`{"total_count": bool}`). Fallback: if `032` never adds further sub-keys, the dict could collapse to `Meta.total_count = True` — but the dict is the card body's stated shape and the safer default.
- **Auto-trigger of `finalize_django_types()`.** Preferred answer per [Decision 12](#decision-12--no-auto-trigger-of-finalize_django_types-for-009): no auto-trigger in `0.0.9`; explicit finalize unchanged, matching [`DjangoListField`][glossary-djangolistfield]. Fallback: if consumer friction surfaces, the auto-trigger wrapper is designed once for both `DjangoConnectionField` and [`DjangoNodeField`][glossary-djangonodefield] in `032`, constrained to schema-construction time or guarded by a real lock around the finalizer.
- **`connection.py` flat module vs `relay/` subpackage.** Preferred answer per [Decision 14](#decision-14--connectionpy-flat-module-and-the-public-export-gate): flat `connection.py` now; `relay.py` (Root-Node) with `032`; fork to a `relay/` subpackage only if the combined surface grows past ~one module. Fallback: if the connection field alone grows past one module before `032`, fork to `connection/` at that point.
- **Optimizer flat-walker constraint.** Preferred answer per [Decision 11](#decision-11--optimizer-cooperation-against-the-flat-selection-walker-connection-aware-planning-deferred): root connection fields are flat-walker-planned; nested-connection planning is [`WIP-ALPHA-033-0.0.9`][kanban], guarded by a strictness `"raise"` test. Fallback: if `033` slips past the joint cut, the documented constraint stands and the strictness test keeps the gap visible — the connection field is still useful and root-optimized.

## Out of scope (explicitly tracked elsewhere)

- **Root `node(id:)` / `nodes(ids:)`, the relation-as-Connection upgrade, `DjangoNodeField` / `DjangoNodesField`** ([`DjangoNodeField`][glossary-djangonodefield]) — the [Full Relay story][kanban] ([`WIP-ALPHA-032-0.0.9`][kanban]), hard-blocked on this card.
- **Connection-aware optimizer planning** ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]) — the sibling [`WIP-ALPHA-033-0.0.9`][kanban] card; ships in parallel, takes over the walker without retrofit.
- **Django-model-based GlobalID encoding** — the sibling [`WIP-ALPHA-031-0.0.9`][kanban] card; orthogonal to cursor pagination.
- **`search:` argument** ([`Meta.search_fields`][glossary-metasearch_fields]) — `0.1.2`; the connection field reserves the seam, generates no argument in `0.0.9`.
- **`Meta.fields_class` field-selection composition** ([`FieldSet`][glossary-fieldset], [`Meta.fields_class`][glossary-metafields_class]) — `0.1.1`.
- **`aggregates` argument** ([`AggregateSet`][glossary-aggregateset], [`Meta.aggregate_class`][glossary-metaaggregate_class], [`RelatedAggregate`][glossary-relatedaggregate]) — `0.1.3`.
- **Permissions cascade** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions]) — `0.0.10`; the connection field respects [`get_queryset`][glossary-get_queryset-visibility-hook] immediately and integrates with declared permissions when the permissions subsystem lands.
- **`Meta.cursor_field` / stable column cursors** — `BACKLOG.md` item 39 sub-feature 3 ([Decision 9](#decision-9--opaque-cursor-delegated-to-strawberry-metacursor_field-deferred)).
- **`Meta.relation_shapes` (list-vs-connection relation opt-out)** — [`WIP-ALPHA-032-0.0.9`][kanban].
- **Auto-trigger of `finalize_django_types()`** — deferred to `032` ([Decision 12](#decision-12--no-auto-trigger-of-finalize_django_types-for-009)).
- **Version bump** — owned by the joint `0.0.9` cut ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).

## Definition of done

The completion contract the card is built against. Items are grouped by slice; the card completes when all four functional slices' items plus the wrap are satisfied.

**Spec + companion CSV**

1. [`docs/spec-030-connection_field-0_0_9.md`][spec-030] (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/spec-030-connection_field-0_0_9-terms.csv`][spec-030-terms] anchoring every project-specific term that **has** a [`docs/GLOSSARY.md`][glossary] heading; [`uv run python scripts/check_spec_glossary.py --spec docs/spec-030-connection_field-0_0_9.md`][check-spec-glossary] reports `OK: <N> terms`. The net-new `Meta.connection` symbol has **no glossary heading yet** and is therefore intentionally NOT in the CSV until Slice 5's doc-update step adds the heading (per [Risks and open questions](#risks-and-open-questions)).

**Slice 1 — `DjangoConnection[T]` + `totalCount` + `Meta.connection`**

2. [`django_strawberry_framework/connection.py`][connection] ships a generic `DjangoConnection[NodeType]` subclass of [`strawberry.relay.ListConnection`][strawberry-relay] with an opt-in `total_count` field reading a per-request context stash (per [Decision 4](#decision-4--djangoconnectiont-is-a-listconnection-subclass-with-opt-in-totalcount)); the field is absent unless opted in.
3. [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] contains `"connection"` (not in [`DEFERRED_META_KEYS`][base], per [Decision 8](#decision-8--metaconnection-opt-in-totalcount-key-net-new-allowed_meta_keys-entry)); `_validate_connection` rejects a non-dict value, an unknown sub-key, and the key on a non-Relay type with [`ConfigurationError`][glossary-configurationerror]. [`tests/test_connection.py`][test-connection] + [`tests/types/test_base.py`][test-types-base] cover the slice.

**Slice 2 — `DjangoConnectionField` factory**

4. [`django_strawberry_framework/connection.py`][connection] ships `DjangoConnectionField(target_type, *, …)` (PascalCase factory) running the four [`DjangoListField`][glossary-djangolistfield]-style guards plus the Relay-Node guard, deriving `filter:` from [`Meta.filterset_class`][glossary-metafilterset_class] and `orderBy:` from [`Meta.orderset_class`][glossary-metaorderset_class] via the shipped [`filter_input_type`][glossary-filter_input_type] / [`order_input_type`][glossary-order_input_type] machinery (registered against the orphan-validation ledgers), and returning a `relay.connection(...)`-shaped field over [`DjangoConnection`][glossary-djangoconnection] (per [Decision 5](#decision-5--factory-function-mechanism-mirroring-djangolistfield) / [Decision 6](#decision-6--sidecar-derived-filter--orderby-arguments-reuse-the-shipped-helper-machinery)).
5. The connection resolver applies the composition order `get_queryset` → `filter` → `orderBy` → cursor slice, capturing the `totalCount` count before the slice; sync and async resolver paths reuse `_apply_get_queryset_sync` / `_apply_get_queryset_async` and `apply_sync` / `apply_async`, and a sync-context async-`get_queryset` raises [`SyncMisuseError`][glossary-syncmisuseerror] (per [Decision 7](#decision-7--composition-order-visibilityfilterorderslice) / [Decision 10](#decision-10--sync--async-resolver-paths-reuse-the-relay-foundation-get_queryset-helpers)). [`tests/test_connection.py`][test-connection] covers the guards, argument derivation, composition order, and sync/async dispatch.

**Slice 3 — optimizer cooperation**

6. A root `DjangoConnectionField` selection's pre-slice queryset is planned by the existing root-gated flat-selection [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] with no walker change (per [Decision 11](#decision-11--optimizer-cooperation-against-the-flat-selection-walker-connection-aware-planning-deferred)); a [Strictness mode][glossary-strictness-mode] `"raise"` test pins that an unplanned nested-connection access still surfaces as an N+1 (the seam [`WIP-ALPHA-033-0.0.9`][kanban] closes). The nested-planning gap is named in [`docs/GLOSSARY.md`][glossary] (no silent cap).

**Slice 4 — live HTTP coverage**

7. A root `DjangoConnectionField(GenreType)` (Relay-Node-shaped, with `GenreFilter` / `GenreOrder` sidecars and `Meta.connection = {"total_count": True}`) is added to [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema]. Live HTTP tests in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] cover a filter+orderBy+first+after round-trip (incl. `totalCount` on the unpaginated post-filter set, no `errors`), the `first`+`last` typed-error path, and a `first: 0` empty-edges shape (per the [Test plan](#test-plan)).

**Slice 5 — doc + card-completion wrap**

8. [`docs/GLOSSARY.md`][glossary] flips [`DjangoConnectionField`][glossary-djangoconnectionfield] / [`DjangoConnection`][glossary-djangoconnection] to `shipped (0.0.9)` and adds the `## Meta.connection` entry; [`docs/README.md`][docs-readme] / [`docs/TREE.md`][tree] / [`TODAY.md`][today] / [`README.md`][readme] reflect the shipped field; [`CHANGELOG.md`][changelog] `[Unreleased]` carries the `### Added` bullet (the per-card permission grant). `DjangoConnectionField` / `DjangoConnection` are promoted to [`django_strawberry_framework/__init__.py`][package-init] (the tested-usage gate, [Decision 14](#decision-14--connectionpy-flat-module-and-the-public-export-gate)).
9. [`KANBAN.md`][kanban] records the card as `DONE-NNN-0.0.9` (moved from [`WIP-ALPHA-030-0.0.9`][kanban]) with the card body's spec reference pointing at [`docs/spec-030-connection_field-0_0_9.md`][spec-030].
10. **No version bump lands in this card** per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut): `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` are unchanged; no [`CHANGELOG.md`][changelog] release heading is promoted (the joint `0.0.9` cut owns the bump).
11. Package coverage stays at 100% (`fail_under = 100`). Routine per-slice work does not run pytest locally — owned by CI per the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"Do not run pytest after edits"; worker-local validation is `uv run ruff format .` and `uv run ruff check --fix .`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[package-init]: ../django_strawberry_framework/__init__.py
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-aggregateset]: GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: GLOSSARY.md#connection-aware-optimizer-planning
[glossary-cross-subsystem-invariants]: GLOSSARY.md#cross-subsystem-invariants
[glossary-definition-order-independence]: GLOSSARY.md#definition-order-independence
[glossary-djangoconnection]: GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangonodefield]: GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-filter_input_type]: GLOSSARY.md#filter_input_type
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: GLOSSARY.md#fk-id-elision
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-index]: GLOSSARY.md#index
[glossary-metaaggregate_class]: GLOSSARY.md#metaaggregate_class
[glossary-metaconnection]: GLOSSARY.md#metaconnection
[glossary-metafields_class]: GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: GLOSSARY.md#metafilterset_class
[glossary-metainterfaces]: GLOSSARY.md#metainterfaces
[glossary-metaoptimizer_hints]: GLOSSARY.md#metaoptimizer_hints
[glossary-metaorderset_class]: GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: GLOSSARY.md#metaprimary
[glossary-metasearch_fields]: GLOSSARY.md#metasearch_fields
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-optimizerhint]: GLOSSARY.md#optimizerhint
[glossary-ordering]: GLOSSARY.md#ordering
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-order_input_type]: GLOSSARY.md#order_input_type
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-queryset-diffing]: GLOSSARY.md#queryset-diffing
[glossary-relatedaggregate]: GLOSSARY.md#relatedaggregate
[glossary-relatedfilter]: GLOSSARY.md#relatedfilter
[glossary-relatedorder]: GLOSSARY.md#relatedorder
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-strawberry_config]: GLOSSARY.md#strawberry_config
[glossary-strictness-mode]: GLOSSARY.md#strictness-mode
[glossary-syncmisuseerror]: GLOSSARY.md#syncmisuseerror
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[spec-030]: spec-030-connection_field-0_0_9.md
[spec-030-terms]: spec-030-connection_field-0_0_9-terms.csv
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-015]: SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-020]: SPECS/spec-020-list_field-0_0_7.md
[spec-027]: SPECS/spec-027-filters-0_0_8.md
[spec-028]: SPECS/spec-028-orders-0_0_8.md
[spec-029]: SPECS/spec-029-consumer_dx_cleanup-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../django_strawberry_framework/types/base.py
[connection]: ../django_strawberry_framework/connection.py
[list-field]: ../django_strawberry_framework/list_field.py
[optimizer-extension]: ../django_strawberry_framework/optimizer/extension.py
[relay]: ../django_strawberry_framework/types/relay.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-connection]: ../tests/test_connection.py
[test-extension]: ../tests/optimizer/test_extension.py
[test-list-field]: ../tests/test_list_field.py
[test-types-base]: ../tests/types/test_base.py

<!-- examples/ -->
[fakeshop-config-schema]: ../examples/fakeshop/config/schema.py
[fakeshop-library-schema]: ../examples/fakeshop/apps/library/schema.py
[fakeshop-test-library]: ../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->
[check-spec-glossary]: ../scripts/check_spec_glossary.py

<!-- .venv/ -->

<!-- External -->
[strawberry-relay]: https://strawberry.rocks/docs/guides/relay
[upstream-cookbook]: https://github.com/riodw/django-graphene-filters
