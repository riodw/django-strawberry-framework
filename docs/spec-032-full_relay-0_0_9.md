# Spec: Full Relay story — root `node(id:)` / `nodes(ids:)` via `DjangoNodeField` / `DjangoNodesField`, the relation-as-Connection upgrade (`Meta.relation_shapes`), schema-validation diagnostics, and the public `testing.relay` helpers

Planned for `0.0.9` (card [`WIP-ALPHA-032-0.0.9`][kanban]). **This spec is an open build plan, not a shipped record.** The card is the lowest-NNN WIP card in the `0.0.9` cohort and the **connective tissue of the Relay surface**: it assembles the already-shipped pieces — [`DjangoConnectionField`][glossary-djangoconnectionfield] ([`DONE-030-0.0.9`][kanban]) and the model-anchored `GlobalID` encode/decode ([`DONE-031-0.0.9`][kanban]) — into the complete consumer-facing Relay story: root refetch fields, relation connections, validation diagnostics, and public test helpers. The [Slice checklist](#slice-checklist) below stays unticked as the contract record (build progress is tracked in the build plan, not here); the [Definition of done](#definition-of-done) describes the closure conditions; the [Current state](#current-state) section describes the repo as of this spec's authoring, before the build. **Version boundary** (see [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)): this card shares the `0.0.9` patch line with the sibling WIP card [`WIP-ALPHA-033-0.0.9`][kanban] and the already-shipped [`DONE-029-0.0.9`][kanban] / [`DONE-030-0.0.9`][kanban] / [`DONE-031-0.0.9`][kanban]; the `pyproject.toml` / [`__version__`][package-init] / [`tests/base/test_init.py::test_version`][test-base-init] bump to `0.0.9` is owned by the **joint cut**, not by this card. This card's slices land within the `0.0.9` line and never bump the version themselves (the on-disk version is still `0.0.8` at spec-authoring time).

Status: planned — not started. Seven slices: Slice 1 (the [schema-validation diagnostics](#decision-8--the-six-schema-validation-diagnostics) — named-helper rejections for the six `strawberry.relay` non-interface helpers in [`Meta.interfaces`][glossary-metainterfaces], plus re-affirmation tests for the two already-shipped gates), Slice 2 (the **root refetch fields** — `DjangoNodeField` / `DjangoNodesField` in a new top-level [`relay.py`][relay-toplevel], dispatching through the shipped [`decode_global_id`][types-relay], honoring [`get_queryset`][glossary-get_queryset-visibility-hook], with the null-for-invisible / error-for-malformed contract and the no-Node-types finalization check, exported from the package public surface), Slice 3 (the **relation-as-Connection upgrade** — the net-new [`Meta.relation_shapes`][glossary-djangotype] key plus the Phase-2.5 synthesis of `<field>_connection` siblings for many-side relations whose target is Relay-Node-shaped), Slice 4 (the **cursor-contract conformance suite** — the Relay-spec `first` / `after` / `last` / `before` / `pageInfo` edge cases pinned as tests against the shipped connection machinery, plus the permission-integration tests for the root fields), Slice 5 (the **public test helpers** — [`testing/relay.py`][testing-init] with `global_id_for` / `decode_global_id`), Slice 6 (**fakeshop library activation** — live HTTP Relay-shaped queries: refetch, paginated connection, cursor round-trip, `totalCount`, and one live relation-as-Connection proof), and Slice 7 (doc updates + the card-completion wrap; grants the per-card [`CHANGELOG.md`][changelog] edit permission [`AGENTS.md`][agents] otherwise withholds). Slices 1–2 are foundation-first; 3 builds on 2; 4 builds on 2–3; 5 and 6 build on 2–4; 7 lands last.

Owner: package maintainer.

Predecessors: [`spec-031-globalid_encoding-0_0_9.md`][spec-031] (the most-recently-shipped spec — the canonical voice / depth / section-layout reference for this document; its [Decision 8][spec-031] `decode_global_id` resolve-then-enforce dispatch is the decode seam this card's root fields consume; its [Decision 11][spec-031] explicitly deferred the top-level `relay.py` module and the public `testing/relay` helpers to this card; its [Decision 12][spec-031] joint-`0.0.9`-cut version-bump boundary is the precedent [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut) reuses verbatim); [`spec-030-connection_field-0_0_9.md`][spec-030] (the connection machinery this card extends to relations — its [Decision 4][spec-030] `DjangoConnection[T]` / per-target concrete connection classes, [Decision 6][spec-030] synthesized-signature sidecar arguments, [Decision 7][spec-030] composition pipeline, and [Decision 9][spec-030] cursor delegation are all reused, not reinvented); [`spec-015-relay_interfaces-0_0_5.md`][spec-015] (the [Relay Node integration][glossary-relay-node-integration] foundation — the injected `resolve_node` / `resolve_nodes` defaults this card's root fields dispatch to, the [`SyncMisuseError`][glossary-syncmisuseerror] contract, and the `Meta.interfaces` validation this card's diagnostics extend). [`docs/GLOSSARY.md`][glossary] carries [`DjangoNodeField`][glossary-djangonodefield] (`planned for 0.0.9`); it does **not** yet carry `DjangoNodesField` or `Meta.relation_shapes` entries (the net-new symbols this card introduces — see [Risks and open questions](#risks-and-open-questions)).

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`WIP-ALPHA-032-0.0.9`][kanban] card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-06-10). Pinned the canonical spec filename (the card's `docs/spec-relay_connection.md` name predates the structured convention), the card-scope boundary against the shipped `0.0.9` cohort and the parallel [`WIP-ALPHA-033-0.0.9`][kanban], the root-field dispatch through the package's [`decode_global_id`][types-relay] (Strawberry's native `NodeExtension` resolves the type-name slot via `info.schema.get_type_by_name`, which cannot decode the `0.0.9` model-label default payload — source-verified against the locked Strawberry `0.316.0`), the bare-interface and typed `DjangoNodeField` forms, the null-for-invisible / `GraphQLError`-for-malformed contract, the Phase-2.5 relation-as-Connection synthesis with the net-new `Meta.relation_shapes` key, the six-diagnostic enumeration, the cursor-conformance posture (mechanics stay Strawberry's; this card pins the contract as tests), the public `testing/relay` helpers with the strategy-aware `global_id_for`, the module / test-file locations (preferring the card's named test files over a strict `docs/TREE.md` mirror — conflict flagged), the sequencing guard against [`WIP-ALPHA-033-0.0.9`][kanban] (nested connections derive an empty optimizer plan until the connection-aware walker lands), the library-first fakeshop activation (products activation stays deferred to [`TODO-BETA-051-0.1.5`][kanban]), and the joint-cut version boundary.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [Relay Node integration][glossary-relay-node-integration] — the shipped `0.0.5` foundation: `Meta.interfaces = (relay.Node,)` declares a Relay-Node-shaped type with `id: GlobalID!` and the four injected `resolve_*` defaults wired through `cls.get_queryset`. This card's root fields dispatch to those defaults; nothing about the per-type wiring changes.
- [`DjangoNodeField`][glossary-djangonodefield] — the planned root single-node lookup field this card ships: `genre: GenreType | None = DjangoNodeField(GenreType)` (typed) and `node: relay.Node | None = DjangoNodeField()` (the Relay-spec interface form). The first consumer of [`DONE-031-0.0.9`][kanban]'s decode dispatch.
- [`DjangoConnectionField`][glossary-djangoconnectionfield] / [`DjangoConnection`][glossary-djangoconnection] — the shipped [`DONE-030-0.0.9`][kanban] connection surface whose factory pipeline (per-target connection classes, synthesized sidecar arguments, visibility→filter→order→default-order→optimizer→slice composition) the relation-as-Connection upgrade reuses with a relation-manager-seeded source.
- [`Meta.connection`][glossary-metaconnection] — the type-level `{"total_count": bool}` opt-in; a synthesized relation connection resolves through the same per-target connection class, so `totalCount` availability follows the **target** type's declaration (type-level, one stable connection shape per node type).
- [`Meta.interfaces`][glossary-metainterfaces] — the key whose validation this card's Slice 1 extends with named rejections for the six `strawberry.relay` non-interface helpers ([Decision 8](#decision-8--the-six-schema-validation-diagnostics)).
- [`Meta.globalid_strategy`][glossary-metaglobalid_strategy] / [`RELAY_GLOBALID_STRATEGY`][glossary-relay-globalid-strategy] — the shipped (`0.0.9`, [`DONE-031-0.0.9`][kanban]) encoding-strategy system; the root fields decode whatever payload the strategy system emits, and [`testing.relay.global_id_for`](#decision-10--public-testingrelaypy-helpers-and-the-export-gate) computes the strategy-appropriate encoded id for a `(type, pk)` pair.
- [`Meta.primary`][glossary-metaprimary] — a decoded model-label id routes to the model's primary [`DjangoType`][glossary-djangotype]; the typed `DjangoNodeField(Target)` form layers a declared-target check on top ([Decision 4](#decision-4--djangonodefield--djangonodesfield-a-bare-interface-form-and-a-typed-form)).
- [`Meta.name`][glossary-metaname] — type-name-anchored ids decode through `registry.definition_for_graphql_name`, which honors `Meta.name`; the root fields inherit that contract unchanged.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — the load-bearing permission surface: the shipped `resolve_node` / `resolve_nodes` defaults run it, so a decoded id for a hidden row resolves to `null`, never an error ([Decision 5](#decision-5--null-for-invisible-rows-graphqlerror-for-malformed-ids)).
- [`ConfigurationError`][glossary-configurationerror] — raised at type-creation time for a malformed [`Meta.relation_shapes`][glossary-djangotype] declaration and at finalization for the no-Node-types and non-Node-target diagnostics; the decode helper's uniform failure type, converted to `GraphQLError` at the root-field boundary.
- [`finalize_django_types`][glossary-finalize_django_types] — Phase 2.5 already injects interfaces, the Relay `resolve_*` defaults, and the `GlobalID` typename resolver; the relation-as-Connection synthesis and the no-Node-types check land in the same phase ([Decision 6](#decision-6--relation-as-connection-synthesis-at-finalization-phase-25)).
- [Definition-order independence][glossary-definition-order-independence] — the collection-then-finalize split the connection synthesis rides on: relation targets are resolved (Phase 1) before the upgrade runs (Phase 2.5), so the target-is-Node-shaped gate reads settled definitions.
- [`SyncMisuseError`][glossary-syncmisuseerror] — the typed marker the `resolve_node` / `resolve_nodes` defaults raise on the sync branch when `get_queryset` returns a coroutine; the root fields and synthesized relation connections inherit this contract unchanged.
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] — the parallel [`WIP-ALPHA-033-0.0.9`][kanban] card. Until it lands, every connection (root or nested) derives an **empty** optimizer plan, so nested `edges { node }` selections lazy-load — the sequencing constraint [Decision 12](#decision-12--sequencing-against-the-connection-aware-optimizer-and-the-library-first-activation) builds around.
- [Strictness mode][glossary-strictness-mode] — a `"raise"` run surfaces the pre-`033` unplanned nested-connection access as an N+1 (no silent cap); the live tests this card adds assert behavior, not SQL shape, until the walker lands.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — root-gated optimization is untouched; the connection field owns its own cooperation seam ([`spec-030`][spec-030] Decision 11) and the synthesized relation connections reuse it.
- [`FilterSet`][glossary-filterset] / [`OrderSet`][glossary-orderset] / [`Meta.filterset_class`][glossary-metafilterset_class] / [`Meta.orderset_class`][glossary-metaorderset_class] — the sidecars whose `filter:` / `orderBy:` arguments the synthesized relation connections carry, exactly as the shipped root connection field does ([`filter_input_type`][glossary-filter_input_type] / [`order_input_type`][glossary-order_input_type] drive the lazy annotations).
- [`DjangoListField`][glossary-djangolistfield] — the annotation-driven factory-function precedent (`list[T]` vs `list[T] | None` drives outer nullability) the root node fields follow.
- [Relation handling][glossary-relation-handling] — the shipped list-shaped relation conversion the connection counterparts sit alongside; the `"both"` default keeps the `list[T]` field, so nothing shipped changes shape.
- [`apply_cascade_permissions`][glossary-apply_cascade_permissions] / [Per-field permission hooks][glossary-per-field-permission-hooks] — the `0.0.10` permissions subsystem ([`TODO-ALPHA-034-0.0.10`][kanban]); the root fields respect `get_queryset` immediately and integrate with declared permissions when it lands.
- [`Meta.search_fields`][glossary-metasearch_fields] — the `search:` argument stays absent from every connection until `0.1.2` ([`TODO-BETA-046-0.1.2`][kanban]); reaffirmed for the synthesized relation connections.
- [`strawberry_config`][glossary-strawberry_config] — the scalar-map factory every example schema in this spec passes to `strawberry.Schema(...)`; its `relay_max_results` passthrough is the knob that caps connection page sizes ([Edge cases and constraints](#edge-cases-and-constraints)).
- [`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase] — the `0.0.12` consumer test clients; `testing/relay.py` is this card's narrower test-helper surface and shares the `testing/` subpackage with them.
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — the `1.0.0` rule that example-project schemas reference only shipped features; the library activation slice references only surfaces this card and its predecessors ship.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package tests under `tests/` mirroring source; live HTTP tests under `examples/fakeshop/test_query/`); the live-HTTP-priority coverage rule; the no-pytest-after-edits rule; the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — Slice 7's doc-update step grants the explicit per-card permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical (Slice 6) and package-internal `tests/` where the path is unreachable from a live query.
- [`docs/TREE.md`][tree] — tests mirror source one-to-one; this card adds two flat source modules ([`relay.py`][relay-toplevel], [`testing/relay.py`][testing-init]) and the card names two flat test files (`tests/test_relay_node_field.py`, `tests/test_relay_connection.py`) — the mirror tension is pinned in [Decision 11](#decision-11--module-and-test-file-locations) and flagged in [Risks and open questions](#risks-and-open-questions).
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, all defs at the bottom under the 10 canonical group headers); the "Strawberry is the engine; DRF is the shape" rule (the root fields reuse Strawberry's `GlobalID` / `Node` machinery and the shipped `resolve_*` defaults — only the type-resolution dispatch is package-owned, because the engine's dispatch cannot decode the model-label payload).

## Slice checklist

Each top-level item maps to one commit / PR. **Seven slices: six functional (1→2→3→4, with 5 and 6 after 4) plus a doc + card-completion wrap (7).** Boxes are unticked because the work has not started.

- [ ] Slice 1: schema-validation diagnostics (per [Decision 8](#decision-8--the-six-schema-validation-diagnostics))
  - [ ] [`django_strawberry_framework/types/base.py::_validate_interfaces`][base] gains a named-helper rejection branch: each of `relay.GlobalID`, `relay.NodeID`, `relay.Connection`, `relay.ListConnection`, `relay.Edge`, `relay.PageInfo` appearing in [`Meta.interfaces`][glossary-metainterfaces] raises [`ConfigurationError`][glossary-configurationerror] **naming the helper** and explaining what it is instead (a scalar / an annotation helper / a generic output type) and what the consumer probably meant (`relay.Node`, or [`Meta.connection`][glossary-metaconnection] / [`DjangoConnectionField`][glossary-djangoconnectionfield] for connection shapes). Today all six fall into the generic "is not a Strawberry interface" rejection; the named branch fires **before** the generic one.
  - [ ] Re-affirmation coverage for the two already-shipped diagnostics the card enumerates: a non-Strawberry-interface class in `Meta.interfaces` is rejected naming the class ([`spec-011`][spec-011]-era behavior), and `Meta.connection` on a non-Relay-Node type is rejected with the add-`relay.Node`-or-remove-the-key remediation ([`spec-030`][spec-030] Decision 8). No behavior change; the tests pin the documented messages.
  - [ ] Package coverage: [`tests/types/test_base.py`][test-types-base] — one named-rejection test per helper (six), plus the two re-affirmation pins.
- [ ] Slice 2: root `node(id:)` / `nodes(ids:)` — `DjangoNodeField` / `DjangoNodesField` (per [Decision 3](#decision-3--root-fields-dispatch-through-the-package-decode-not-strawberrys-native-node-field) / [Decision 4](#decision-4--djangonodefield--djangonodesfield-a-bare-interface-form-and-a-typed-form) / [Decision 5](#decision-5--null-for-invisible-rows-graphqlerror-for-malformed-ids))
  - [ ] New top-level [`django_strawberry_framework/relay.py`][relay-toplevel]: `DjangoNodeField(target_type=None, *, description=, deprecation_reason=, directives=)` and `DjangoNodesField(target_type=None, *, ...)` factory functions returning `strawberry.field(resolver=...)` values picked up by Strawberry's class-body walk (the [`DjangoListField`][glossary-djangolistfield] mechanism). The synthesized resolvers declare `id: relay.GlobalID` / `ids: list[relay.GlobalID]` arguments, decode **server-side** via [`types/relay.py::decode_global_id`][types-relay] (never trusting the client's claim of which type the id belongs to), dispatch to the resolved type's `resolve_node` / `resolve_nodes` (which honor [`get_queryset`][glossary-get_queryset-visibility-hook]), and return `null` (or a `null` list entry) for hidden and missing rows. `nodes` preserves input order, resolves per-type **batched** (`resolve_nodes` once per distinct type), and supports duplicate ids.
  - [ ] The typed form (`DjangoNodeField(GenreType)`) runs the shared [`list_field.py::_validate_djangotype_target`][list-field] guards plus the connection-style Relay-Node-shaped guard at construction time, and at request time rejects an id that decodes to a different type with a `GraphQLError` naming the expected and received types ([Decision 4](#decision-4--djangonodefield--djangonodesfield-a-bare-interface-form-and-a-typed-form)).
  - [ ] Decode failures ([`ConfigurationError`][glossary-configurationerror] from `decode_global_id`) are caught at the root-field boundary and re-raised as `GraphQLError("Invalid GlobalID: ...", extensions={"code": "GLOBALID_INVALID"})` — the [`FilterSet`][glossary-filterset] `FILTER_INVALID` precedent ([Decision 5](#decision-5--null-for-invisible-rows-graphqlerror-for-malformed-ids)).
  - [ ] A module-level `_node_fields_declared` ledger (appended by both factories, co-cleared by `registry.clear()` — the `_helper_referenced_filtersets` precedent) backs a [`finalize_django_types`][glossary-finalize_django_types] check: a declared node field on a registry with **no** Relay-Node-shaped [`DjangoType`][glossary-djangotype]s raises `ConfigurationError("node lookup configured but no Node types registered.")`.
  - [ ] `DjangoNodeField` and `DjangoNodesField` are exported from [`django_strawberry_framework/__init__.py`][package-init] (the card's DoD names both).
  - [ ] Package coverage: `tests/test_relay_node_field.py` (new) per the [Test plan](#test-plan).
- [ ] Slice 3: relation-as-Connection upgrade — `Meta.relation_shapes` + Phase-2.5 synthesis (per [Decision 6](#decision-6--relation-as-connection-synthesis-at-finalization-phase-25) / [Decision 7](#decision-7--metarelation_shapes-is-a-net-new-allowed_meta_keys-key-stored-on-the-definition))
  - [ ] [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] grows `"relation_shapes"` (net-new public key — NOT a `DEFERRED_META_KEYS` promotion, the [`spec-031`][spec-031] Decision 6 / [`spec-030`][spec-030] Decision 8 rule). `_validate_relation_shapes` (modeled on `_validate_connection`) accepts a `dict[str, str]` with values in `{"list", "connection", "both"}`, gated to Relay-Node-shaped declaring types; unknown keys / values / shapes raise [`ConfigurationError`][glossary-configurationerror]. The normalized value is stored on [`DjangoTypeDefinition`][definition] (a new `relation_shapes` slot).
  - [ ] [`django_strawberry_framework/types/finalizer.py`][finalizer] Phase 2.5 gains the synthesis step: for every Relay-Node-shaped type, each selected many-side relation (reverse FK, forward / reverse M2M) whose **target** type is also Relay-Node-shaped gets a `<field>_connection` sibling (rendered `<field>Connection` by Strawberry's camel-casing) per the resolved shape — `"both"` (default) keeps the `list[T]` field and adds the connection; `"connection"` suppresses the list field; `"list"` suppresses the connection. The synthesized field reuses the [`spec-030`][spec-030] machinery (`_connection_type_for`, the synthesized sidecar signature, the pipeline tail) with a relation-manager-seeded source. Field-name validation (relation-ness, many-side-ness, membership in the selected set) and the explicit-shape-on-non-Node-target rejection run at finalization, where relation targets are settled.
  - [ ] Package coverage: `tests/test_relay_connection.py` (new) + [`tests/types/test_base.py`][test-types-base] (key validation) per the [Test plan](#test-plan).
- [ ] Slice 4: cursor-contract conformance + permission integration (per [Decision 9](#decision-9--cursor-mechanics-stay-delegated-to-strawberry-this-card-pins-the-conformance-contract) / [Decision 5](#decision-5--null-for-invisible-rows-graphqlerror-for-malformed-ids))
  - [ ] A Relay-spec conformance suite pinning, against both a root [`DjangoConnectionField`][glossary-djangoconnectionfield] and a synthesized relation connection: `first: 0` → empty edges + `pageInfo`; `first: N` past the remainder → the actual remainder; an `after` cursor whose row no longer exists → falls through to the next existing row (offset-cursor semantics, no error); `first` + `last` together → the shipped `GraphQLError`; `pageInfo` four-field correctness including the spec-mandated `hasNextPage`-is-correct-even-when-unrequested invariant; backward pagination (`last` / `before`).
  - [ ] Permission-integration tests for the root fields: `node(id:)` for a row hidden by [`get_queryset`][glossary-get_queryset-visibility-hook] returns `null` (not an error); the hidden-row and missing-row paths traverse the same queryset code path (no existence oracle); `nodes(ids:)` mixes visible / hidden / missing ids into the right `null` positions.
  - [ ] Package coverage: extends `tests/test_relay_connection.py`, `tests/test_relay_node_field.py`, and [`tests/test_connection.py`][test-connection] per the [Test plan](#test-plan).
- [ ] Slice 5: public `testing/relay.py` helpers (per [Decision 10](#decision-10--public-testingrelaypy-helpers-and-the-export-gate))
  - [ ] New [`django_strawberry_framework/testing/relay.py`][testing-init]: `global_id_for(type_cls, id)` — the strategy-aware encoded `GlobalID` string a finalized Relay-Node-shaped type emits for a pk (`model` / `type+model` → model-label payload; `type` → `graphql_type_name` payload; `callable` / `custom` → [`ConfigurationError`][glossary-configurationerror], encode needs a live `root` / `info`) — and `decode_global_id(gid)` — the public re-export of the internal dispatch returning `(target_type, node_id)`.
  - [ ] Package coverage: `tests/testing/test_relay.py` (new — mirrors `testing/relay.py` per [`docs/TREE.md`][tree]).
- [ ] Slice 6: fakeshop library activation (per [Decision 12](#decision-12--sequencing-against-the-connection-aware-optimizer-and-the-library-first-activation))
  - [ ] [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema]: add `node: relay.Node | None = DjangoNodeField()` and `nodes: list[relay.Node | None] = DjangoNodesField()` to the library `Query`; promote [`BookType`][fakeshop-library-schema] to Relay-Node shape (`interfaces = (relay.Node,)`) so `GenreType.books` (reverse M2M) synthesizes a live `booksConnection` counterpart.
  - [ ] [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]: live HTTP Relay-shaped queries — `node(id:)` refetch of an emitted Genre `GlobalID`; `nodes(ids:)` batch with order preservation and a `null` entry; the paginated `allLibraryGenresConnection` cursor round-trip (`endCursor` → `after`) and `totalCount`; a `genre → booksConnection` nested relation-as-Connection query asserting **behavior** (right rows, right pagination), not SQL shape (pre-`033` posture); the hidden-row `null` semantics through a `get_queryset`-filtered type.
  - [ ] Update the existing library assertions the `BookType` Relay promotion changes (its `id` becomes `GlobalID!`; emitted book ids move to the encoded model-label payload).
- [ ] Slice 7: doc updates + card-completion wrap (grants the per-card [`CHANGELOG.md`][changelog] edit permission)
  - [ ] [`docs/GLOSSARY.md`][glossary]: flip [`DjangoNodeField`][glossary-djangonodefield] to `shipped (0.0.9)` and rewrite its body for both forms; add net-new `## DjangoNodesField` and `## Meta.relation_shapes` entries (`shipped (0.0.9)`) with Index rows and "Relay" / "Type generation" Browse-by-category entries; extend [Relay Node integration][glossary-relay-node-integration] / [`DjangoConnectionField`][glossary-djangoconnectionfield] cross-references. **These two entries do not exist at spec-authoring time and creating them is out of scope for the [`docs/SPECS/NEXT.md`][next] flow** (see [Risks and open questions](#risks-and-open-questions)) — Slice 7 of the build creates them.
  - [ ] [`docs/README.md`][docs-readme]: add the root node/nodes fields, the relation-as-Connection upgrade, and the `testing.relay` helpers to the shipped-surface list; update the "Coming next" `0.0.9` line.
  - [ ] [`docs/TREE.md`][tree]: add [`relay.py`][relay-toplevel] and `testing/relay.py` to the current-layout tree, plus the new test files.
  - [ ] [`TODAY.md`][today]: products is **not** activated (deferred to [`TODO-BETA-051-0.1.5`][kanban]) — touch only the `0.0.9` `GlobalID` note if it references root `node(id:)` as unshipped (the "nothing decodes a GlobalID until root `node(id:)` ships" sentence becomes stale when this card lands); keep the file products-centric.
  - [ ] [`README.md`][readme]: update the status paragraph's newest-shipped-surface line.
  - [ ] [`CHANGELOG.md`][changelog]: `### Added` bullets under `[Unreleased]` for `DjangoNodeField` / `DjangoNodesField`, `Meta.relation_shapes` + the relation-as-Connection upgrade, and `testing.relay`. **This is the per-card CHANGELOG-edit permission grant** ([`AGENTS.md`][agents] withholds it by default); the Slice 7 maintainer prompt must name this edit explicitly. No version-heading promotion (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).
  - [ ] [`KANBAN.md`][kanban]: move [`WIP-ALPHA-032-0.0.9`][kanban] to the Done column with the next `DONE-NNN-0.0.9` id; confirm the card's spec reference points at [`docs/spec-032-full_relay-0_0_9.md`][spec-032] (this document). (`KANBAN.md` is a generated export — the edit is a `SpecDoc` / card-column DB change re-rendered via `scripts/build_kanban_md.py`.)
  - [ ] **No version-file edits in this card.** Leave `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` to the joint `0.0.9` cut per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut).

## Problem statement

`django-strawberry-framework` has every Relay ingredient on disk but no assembled Relay story. The `0.0.5` [Relay Node integration][glossary-relay-node-integration] gave Relay-Node-shaped types `id: GlobalID!` and `get_queryset`-aware `resolve_node` / `resolve_nodes` defaults. [`DONE-030-0.0.9`][kanban] shipped [`DjangoConnectionField`][glossary-djangoconnectionfield] — cursor pagination with sidecar-derived `filter:` / `orderBy:` arguments and opt-in `totalCount`. [`DONE-031-0.0.9`][kanban] settled the durable identity format (the model-anchored `GlobalID` default) and shipped the internal `decode_global_id` resolve-then-enforce dispatch. But a consumer still **cannot refetch a node by id** — there is no root `node(id:)` field, no `nodes(ids:)` batch field, no way to expose a relation as a connection, and no public helper to mint or decode a `GlobalID` in a test. The Relay contract that makes client frameworks (Relay Compiler, Apollo with the Node pattern) "just work" — *any* object with an `id` is refetchable through one canonical root field — is unmet, and both upstreams meet it: graphene-django's `DjangoObjectType.get_node` runs `cls.get_queryset(model.objects, info).get(pk=id)` behind its root Node field, and strawberry-graphql-django's `resolve_model_node(s)` run the type's `get_queryset` behind Strawberry's `relay.node()`. The card's parity tags are **Required** for both upstreams.

The assembly is not a thin wrapper over Strawberry's native root field. Strawberry's `relay.node()` dispatches via `GlobalID.resolve_type(info)` → `info.schema.get_type_by_name(type_name)` — a **GraphQL-type-name** schema lookup. Under the `0.0.9` model-anchored default, an emitted id carries `library.genre`, not `GenreType`; the native dispatch cannot decode it ([`spec-031`][spec-031] flagged exactly this and deferred the consumer to this card). The package must own the root-field dispatch through its own [`decode_global_id`][types-relay], which also enforces the per-type strategy contract and never trusts the client's claim of which type an id belongs to ([Decision 3](#decision-3--root-fields-dispatch-through-the-package-decode-not-strawberrys-native-node-field)).

The card also closes the relation gap: a Relay-shaped schema exposes collections as connections, but the package's generated relation fields are `list[T]`-only. The implicit relation-as-Connection upgrade gives every Relay-Node-shaped type's many-side relations a `<field>Connection` sibling (with the `Meta.relation_shapes` opt-out), so the cookbook-shaped nested-connection queries the [`GOAL.md`][goal] astronomy showcase promises become expressible. Finally, the card hardens the configuration surface (six named schema-validation diagnostics) and ships the public `testing.relay` helpers that make the new durable ids testable by consumers.

## Current state

A true description of the repo as of this writing (the plan is written against it), source-verified against the locked Strawberry `0.316.0`:

- [`django_strawberry_framework/types/relay.py`][types-relay] ships the complete per-type Relay foundation: the four injected `resolve_*` defaults — `_resolve_node_default` / `_resolve_nodes_default` run [`get_queryset`][glossary-get_queryset-visibility-hook] on sync and async branches, `_resolve_nodes_default` is order-preserving via `_order_nodes` (the port of `strawberry_django/relay/utils.py::resolve_model_nodes` #"def map_results") with `required=False` emitting `None` for missing ids — plus the [`DONE-031-0.0.9`][kanban] strategy system: `encode_typename`, `install_globalid_typename_resolver`, and `decode_global_id` (the resolve-then-enforce dispatch with the uniform-[`ConfigurationError`][glossary-configurationerror] contract, documented in-source as "the forward-looking piece root `node(id:)` / `nodes(ids:)` (`WIP-ALPHA-032-0.0.9`) will consume").
- [`registry.py::definition_for_graphql_name`][registry] resolves a type-name payload over Relay-Node definitions only, keyed on `graphql_type_name` (honors [`Meta.name`][glossary-metaname]); `registry.get(model)` resolves a model-label payload to the primary type. Both halves of the decode dispatch are shipped and package-tested.
- [`connection.py`][connection] ships the full root connection machinery: `DjangoConnection[T]` + the `first`+`last` mutual-exclusivity `GraphQLError` guard, `_connection_type_for` (per-target concrete connection classes with the [`Meta.connection`][glossary-metaconnection] `totalCount` opt-in), `_synthesized_signature` (sidecar-derived `filter:` / `order_by:` arguments registered against the orphan ledgers), `_build_connection_resolver` (sync / async committed per construction), the `_pipeline_sync` / `_pipeline_async` composition (visibility → filter → orderBy → deterministic order → optimizer seam), and the `DjangoConnectionField` factory whose fifth guard requires a Relay-Node-shaped target via the canonical `_is_relay_shaped` predicate. The optimizer seam (`apply_connection_optimization`) derives an **empty plan** — the flat walker is connection-unaware until [`WIP-ALPHA-033-0.0.9`][kanban].
- **Strawberry's native root node field cannot decode the package's default payload.** `strawberry/relay/fields.py::NodeExtension.get_node_resolver` resolves `node_type = id.resolve_type(info)`, and `GlobalID.resolve_type` is `info.schema.get_type_by_name(self.type_name)` — a GraphQL-type-name lookup. An emitted `library.genre:<pk>` (the `0.0.9` `model`-strategy default) has no schema type named `library.genre`, so native `relay.node()` fails for exactly the ids the package now emits. The batch resolver (`get_node_list_resolver`) groups ids per resolved type and calls `resolve_nodes` once per type with `required=not is_optional` — the per-type-batched, order-preserving shape this card's `DjangoNodesField` mirrors.
- **Cursor mechanics are Strawberry's.** `relay/types.py` pins `PREFIX = "arrayconnection"`; `ListConnection.resolve_connection` slices via `to_base64("arrayconnection", offset)` cursors and enforces `max_results` (schema-config `relay_max_results`, default 100). [`spec-030`][spec-030] Decision 9 delegated cursor mechanics wholesale; the card's `b64("offset:N")` wording describes this shape conceptually, not byte-exactly ([Decision 9](#decision-9--cursor-mechanics-stay-delegated-to-strawberry-this-card-pins-the-conformance-contract)).
- [`types/base.py`][base] holds `ALLOWED_META_KEYS` = `{connection, description, exclude, fields, filterset_class, globalid_strategy, interfaces, model, name, nullable_overrides, optimizer_hints, orderset_class, primary, required_overrides}` and `DEFERRED_META_KEYS` = `{aggregate_class, fields_class, search_fields}`. `"relation_shapes"` is in neither — declaring it today raises via the unknown-key typo guard. `_validate_interfaces` rejects every non-interface entry with the **generic** "entry `X` is not a Strawberry interface" message; the six `strawberry.relay` helpers the card names all take that generic path today (`GlobalID` is a plain class, `NodeID` an annotation helper, `PageInfo` / `Edge` / `Connection` / `ListConnection` are `@strawberry.type` object types — none carries `is_interface=True`), so no helper is *accepted*, but none is *named* either.
- [`types/finalizer.py`][finalizer] Phase 2.5 runs, per Relay-Node-shaped type: `apply_interfaces`, `_check_composite_pk_for_relay_node`, `install_relay_node_resolvers`, `install_globalid_typename_resolver`; then `_audit_model_label_routing`, `_bind_filtersets`, `_bind_ordersets` — all before Phase 3's `strawberry.type(...)` decoration. The relation-as-Connection synthesis has the same needs (settled relation targets, pre-decoration annotation mutation) and lands in this phase.
- [`testing/__init__.py`][testing-init] exports only [`safe_wrap_connection_method`][glossary-safe_wrap_connection_method]; its docstring names the `0.0.12` [`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase] as future exports. There is no `testing/relay.py`.
- [`django_strawberry_framework/__init__.py`][package-init] exports twelve symbols; `DjangoNodeField` / `DjangoNodesField` are absent. No top-level `relay.py` module exists ([`spec-031`][spec-031] Decision 11 explicitly deferred it to this card).
- **Fakeshop:** the library app has exactly one Relay-Node-shaped type — `GenreType` (`interfaces = (relay.Node,)`, `connection = {"total_count": True}`, both sidecars) — with a root `all_library_genres_connection` already live; `BookType` (the [`Meta.primary`][glossary-metaprimary] type for `library.Book`, declared alongside the `NullabilityOverrideBookType` secondary) is **not** Relay-shaped, so `GenreType.books` (reverse M2M of `Book.genres`) has no Node-shaped target today. The products app's four types are all Relay-Node-shaped with sidecars wired, but their `Query` is list-resolver-shaped; the connections-only conversion is explicitly deferred to [`TODO-BETA-051-0.1.5`][kanban] and gated on [`WIP-ALPHA-033-0.0.9`][kanban] (the card: a `0.0.9` connection derives an empty plan, so converting products before the walker lands would regress the `test_products_optimizer_*` SQL-shape coverage).
- The card's five struck-through foundation items are all shipped and need no work here: `Meta.interfaces` end-to-end, the `GlobalID` mapping (`id: GlobalID!` replacing `id: int!` with the pk kept as a connector column), the four `resolve_*` defaults with `__func__`-test override preservation, unconditional `is_type_of` injection, and the `CompositePrimaryKey` rejection.

## Goals

1. Ship the root refetch surface: `DjangoNodeField` (bare `node(id: GlobalID!): Node` interface form **and** typed single-node form) and `DjangoNodesField` (`nodes(ids: [GlobalID!]!): [Node]!` batch, order-preserving, per-type-batched), dispatching server-side through the shipped [`decode_global_id`][types-relay], honoring [`get_queryset`][glossary-get_queryset-visibility-hook] via the shipped `resolve_node` / `resolve_nodes` defaults, returning `null` for hidden and missing rows with no existence leak, exported from the package public surface (Slice 2, [Decision 3](#decision-3--root-fields-dispatch-through-the-package-decode-not-strawberrys-native-node-field) / [Decision 4](#decision-4--djangonodefield--djangonodesfield-a-bare-interface-form-and-a-typed-form) / [Decision 5](#decision-5--null-for-invisible-rows-graphqlerror-for-malformed-ids)).
2. Ship the relation-as-Connection upgrade: every Relay-Node-shaped [`DjangoType`][glossary-djangotype]'s selected many-side relations whose target is also Relay-Node-shaped expose a `<field>Connection` sibling by default (`"both"`), with the net-new [`Meta.relation_shapes`][glossary-djangotype] key narrowing per relation to `"list"` / `"connection"`, synthesized at finalization Phase 2.5 by reusing the shipped connection machinery — per-target connection classes, sidecar-derived `filter:` / `orderBy:` arguments, [`Meta.connection`][glossary-metaconnection]-driven `totalCount` (Slice 3, [Decision 6](#decision-6--relation-as-connection-synthesis-at-finalization-phase-25) / [Decision 7](#decision-7--metarelation_shapes-is-a-net-new-allowed_meta_keys-key-stored-on-the-definition)).
3. Harden the configuration surface with the six named schema-validation diagnostics — the six `strawberry.relay` non-interface helpers in [`Meta.interfaces`][glossary-metainterfaces] each rejected **naming the helper**, plus re-affirmed pins for the shipped non-interface-class and [`Meta.connection`][glossary-metaconnection]-on-non-Node gates and the new no-Node-types finalization check (Slices 1–2, [Decision 8](#decision-8--the-six-schema-validation-diagnostics)).
4. Pin the cursor contract as a Relay-spec conformance suite — `first: 0`, overrun `first`, stale `after` falls through, `first`+`last` rejection, four-field `pageInfo` correctness including unrequested `hasNextPage`, backward pagination — against both root and synthesized relation connections, without changing the delegated Strawberry mechanics (Slice 4, [Decision 9](#decision-9--cursor-mechanics-stay-delegated-to-strawberry-this-card-pins-the-conformance-contract)).
5. Ship the public test helpers: `django_strawberry_framework.testing.relay` with the strategy-aware `global_id_for(type_cls, id)` and the public `decode_global_id(gid)` (Slice 5, [Decision 10](#decision-10--public-testingrelaypy-helpers-and-the-export-gate)).
6. Earn live coverage through the fakeshop library suite — refetch, batch refetch, paginated connection with cursor round-trip and `totalCount`, one nested relation-as-Connection behavior proof (via the `BookType` Relay promotion) — while products activation stays deferred to [`TODO-BETA-051-0.1.5`][kanban] (Slice 6, [Decision 12](#decision-12--sequencing-against-the-connection-aware-optimizer-and-the-library-first-activation)).
7. Keep package version state command-gated and owned by the joint `0.0.9` cut: no slice edits `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock` (Slice 7, [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).

## Non-goals

- **Connection-aware optimizer planning.** The walker's `edges { node }` recognition, slice-aware prefetch planning, plan-cache key hygiene for pagination args, and strictness-mode interaction are [`WIP-ALPHA-033-0.0.9`][kanban] ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]); this card's connections derive empty plans until it lands ([Decision 12](#decision-12--sequencing-against-the-connection-aware-optimizer-and-the-library-first-activation)).
- **Fakeshop products activation.** The connections-only products conversion (replacing the four list resolvers with `DjangoConnectionField`s, mirroring the `django-graphene-filters` cookbook Query) is deferred to [`TODO-BETA-051-0.1.5`][kanban] and gated on `033` per the card's own deferral note.
- **The permissions subsystem.** [`apply_cascade_permissions`][glossary-apply_cascade_permissions] and [Per-field permission hooks][glossary-per-field-permission-hooks] are [`TODO-ALPHA-034-0.0.10`][kanban]; the root fields respect [`get_queryset`][glossary-get_queryset-visibility-hook] immediately and integrate with declared permissions when that card lands.
- **The post-`1.0.0` "Relay magic" differentiators** — type-rename `GlobalID` migrations, polymorphic connections (`Connection[Interface]`), `Meta.cursor_field` stable column-based cursors, row-count-threshold auto-upgrade, refetchable-container schema metadata, permission-aware cursor decoding. All live in [`BACKLOG.md`][backlog] item 39; they extend this story rather than block it (the card's planning note).
- **`search:` argument** — [`Meta.search_fields`][glossary-metasearch_fields] is `0.1.2` ([`TODO-BETA-046-0.1.2`][kanban]); the argument stays absent from root and relation connections alike.
- **[`Meta.fields_class`][glossary-metafields_class] / aggregates / mutations** — later-version surfaces unrelated to the Relay assembly.
- **A version bump.** Owned by the joint `0.0.9` cut ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it? → foundational" test, the root Node field and relation connections are **foundational** — both upstreams ship them, and the card tags both parities Required. The package's additions on top (the model-label-aware dispatch, `Meta.relation_shapes`, the named diagnostics) are consequences of decisions already shipped, not new differentiation.

### Reference-package parity checkpoint

| Upstream | `django-strawberry-framework` | Status |
| --- | --- | --- |
| graphene-django `relay.Node.Field()` root field; `DjangoObjectType.get_node` runs `cls.get_queryset(...).get(pk=id)` | `DjangoNodeField` dispatching to the `get_queryset`-aware `resolve_node` default | **this card (`0.0.9`) — required parity** |
| strawberry-graphql-django: Strawberry `relay.node()` + `resolve_model_node(s)` running the type's `get_queryset` | `DjangoNodeField` / `DjangoNodesField` over the shipped `resolve_node` / `resolve_nodes` defaults | **this card (`0.0.9`) — required parity** |
| Both upstreams: relations exposable as connections (graphene-django `DjangoFilterConnectionField` on relations; strawberry-django `@strawberry_django.connection()` fields) | implicit relation-as-Connection upgrade + `Meta.relation_shapes` | **this card (`0.0.9`)** — the *implicit* default is package-shaped (declarative Meta, not per-field decorators) |
| (no model-anchored decode upstream) | root dispatch through `decode_global_id` (model-label + type-name + strategy enforcement) | this card — consequence of [`DONE-031-0.0.9`][kanban]'s beyond-parity encoding |

### From `graphene-django` — borrow the user-facing shape and the null contract

The one-line root field (`node = relay.Node.Field()` → `node: relay.Node | None = DjangoNodeField()`) and the visibility contract (`get_node` filters through `get_queryset`; an invisible row is `None`, not an error). The typed form's expected-type check mirrors graphene's `Node.Field(only_type)` posture of failing loud on a wrong-type id ([Decision 4](#decision-4--djangonodefield--djangonodesfield-a-bare-interface-form-and-a-typed-form) keeps the error but moves nothing else).

### From `strawberry-graphql-django` — borrow the runtime mechanism

The per-type-batched, order-preserving `nodes` resolution (group ids by resolved type, one `resolve_nodes` call per type, reassemble in input order with `null` holes) is Strawberry's own `NodeExtension.get_node_list_resolver` shape, which strawberry-django rides as-is; the package's `_order_nodes` already ports the order-preserving half. The relation-as-Connection runtime reuses the [`spec-030`][spec-030] machinery that was itself borrowed from Strawberry's `ListConnection`.

### Explicitly do not borrow

- **Strawberry's native `NodeExtension` dispatch.** `id.resolve_type(info)` is a GraphQL-type-name schema lookup; it cannot decode the model-label payload the package now emits by default, and it trusts the client-supplied type-name slot. The package owns the dispatch through `decode_global_id` ([Decision 3](#decision-3--root-fields-dispatch-through-the-package-decode-not-strawberrys-native-node-field)).
- **strawberry-django's decorator-per-field connection surface.** Connections on relations arrive declaratively (the implicit upgrade + `Meta.relation_shapes`), not as per-field `@strawberry_django.connection()` decorations — the package's reason to exist ([`START.md`][start] "Meta classes everywhere on consumer surfaces").
- **graphene-django's connection-on-list auto-wrapping internals.** The cursor/connection mechanics stay Strawberry's (`ListConnection`), per [`spec-030`][spec-030] Decision 9.

## User-facing API

### Root refetch fields

```python
import strawberry
from strawberry import relay

from django_strawberry_framework import DjangoNodeField, DjangoNodesField, finalize_django_types

from apps.library.schema import GenreType


@strawberry.type
class Query:
    # The Relay-spec canonical fields (interface-shaped):
    node: relay.Node | None = DjangoNodeField()
    nodes: list[relay.Node | None] = DjangoNodesField()

    # The typed single-node convenience (the GOAL.md astronomy shape):
    genre: GenreType | None = DjangoNodeField(GenreType)


finalize_django_types()
```

`node(id:)` decodes the `GlobalID` **server-side** (model-label `library.genre:42` or type-name `GenreType:42`, per the target's recorded strategy), dispatches to the resolved type's `resolve_node` — which runs [`get_queryset`][glossary-get_queryset-visibility-hook] — and returns `null` for a row the requesting user cannot see or that does not exist. `nodes(ids:)` resolves per-type batched and returns results in input order with `null` entries for missing / hidden ids. The consumer's class-attribute annotation drives outer nullability (the [`DjangoListField`][glossary-djangolistfield] contract): `relay.Node | None` renders `node: Node`, a non-optional annotation renders `node: Node!` (and a missing row then surfaces the model's `DoesNotExist` as a GraphQL error — the consumer opted out of the null contract).

### Relation-as-Connection upgrade

```python
class BookType(DjangoType):
    class Meta:
        model = models.Book
        fields = ("id", "title", "shelf", "genres", "loans")
        interfaces = (relay.Node,)
        primary = True


class GenreType(DjangoType):
    class Meta:
        model = models.Genre
        fields = ("id", "name", "books")
        interfaces = (relay.Node,)
        connection = {"total_count": True}
        # Optional narrowing; "both" is the default for every eligible relation:
        relation_shapes = {"books": "both"}   # or "connection" (drop the list) or "list" (drop the connection)
```

`GenreType` now exposes `books: [BookType!]!` **and** `booksConnection: BookTypeConnection!` — the connection sibling carries `first` / `after` / `last` / `before`, the target's sidecar-derived `filter:` / `orderBy:` arguments, and `totalCount` when the **target** declares [`Meta.connection`][glossary-metaconnection]` = {"total_count": True}`. Eligibility: the declaring type is Relay-Node-shaped, the relation is many-side (reverse FK, forward / reverse M2M), and the relation **target**'s type is Relay-Node-shaped. An eligible relation defaults to `"both"`; a non-Node-target relation silently stays list-only under the default but raises [`ConfigurationError`][glossary-configurationerror] when `relation_shapes` explicitly requests `"connection"` / `"both"` for it.

### Public test helpers

```python
from django_strawberry_framework.testing.relay import decode_global_id, global_id_for

gid = global_id_for(GenreType, 42)            # strategy-aware: base64("library.genre:42") under the model default
target_type, node_id = decode_global_id(gid)  # (GenreType, "42")
```

### Error shapes

- `relay.GlobalID` (or `relay.NodeID`, `relay.Connection`, `relay.ListConnection`, `relay.Edge`, `relay.PageInfo`) in [`Meta.interfaces`][glossary-metainterfaces] → [`ConfigurationError`][glossary-configurationerror] at type creation **naming the helper** and what it actually is ([Decision 8](#decision-8--the-six-schema-validation-diagnostics)).
- A non-Strawberry-interface class in `Meta.interfaces` → [`ConfigurationError`][glossary-configurationerror] naming the class (shipped; re-affirmed).
- [`Meta.connection`][glossary-metaconnection] on a non-Relay-Node type → [`ConfigurationError`][glossary-configurationerror] with the add-`relay.Node`-or-remove-the-key remediation (shipped; re-affirmed).
- A `DjangoNodeField()` / `DjangoNodesField()` declaration on a schema with **no** registered Relay-Node-shaped [`DjangoType`][glossary-djangotype]s → [`ConfigurationError`][glossary-configurationerror] at finalization: `"node lookup configured but no Node types registered."`.
- [`Meta.relation_shapes`][glossary-djangotype] that is not a `dict[str, str]`, carries a value outside `{"list", "connection", "both"}`, names an unknown / non-relation / single-valued field, is declared on a non-Relay-Node type, or explicitly requests a connection over a non-Node-shaped target → [`ConfigurationError`][glossary-configurationerror] (shape and key-name failures at type creation; target-shape failures at finalization, where relation targets are settled).
- A generated `<field>_connection` name colliding with a model field or consumer-declared attribute → [`ConfigurationError`][glossary-configurationerror] at finalization naming the collision and the `relation_shapes = {"<field>": "list"}` opt-out.
- A malformed / undecodable / strategy-forbidden `GlobalID` fed to `node(id:)` / `nodes(ids:)` → `GraphQLError("Invalid GlobalID: ...", extensions={"code": "GLOBALID_INVALID"})` (the internal [`ConfigurationError`][glossary-configurationerror] is caught and converted at the field boundary; [Decision 5](#decision-5--null-for-invisible-rows-graphqlerror-for-malformed-ids)).
- A typed `DjangoNodeField(GenreType)` receiving an id that decodes to a different type → `GraphQLError` naming the expected and received types ([Decision 4](#decision-4--djangonodefield--djangonodesfield-a-bare-interface-form-and-a-typed-form)).
- `first` + `last` together on any connection → the shipped `GraphQLError` (re-affirmed by the conformance suite).
- An async [`get_queryset`][glossary-get_queryset-visibility-hook] reached from a sync execution context → [`SyncMisuseError`][glossary-syncmisuseerror] (inherited from the `resolve_node` / `resolve_nodes` defaults, unchanged).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-032-full_relay-0_0_9.md`** (this document).

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `WIP-ALPHA-032-0.0.9`, so `<NNN>` is `032` and `<0_0_X>` is `0_0_9`.
- The topic slug is `full_relay` — the card titles itself "Full Relay story"; the slug names the umbrella, not one member.

Alternatives considered (and rejected):

- **The card's own `docs/spec-relay_connection.md`.** Rejected: the card body predates the structured-filename convention; [`spec-031`][spec-031] Decision 1 set the precedent of preferring the convention and recording the card's older name. The card-named file is additionally wrong on substance — the connection field shipped separately under [`spec-030`][spec-030], so `relay_connection` would mislabel this card's actual scope.
- **Topic slug `relay_root` or `node_field`.** Rejected: both under-describe the umbrella (the card also ships the relation-as-Connection upgrade, the diagnostics, and the test helpers).

### Decision 2 — Card-scope boundary against the 0.0.9 Relay cohort

`0.0.9` carries five Relay-cohort cards; this card ships **the assembly**, and the boundary is explicit:

- **[`DONE-030-0.0.9`][kanban] (shipped)** — the connection field: cursor pagination, sidecar arguments, `totalCount`, the `first`+`last` guard, the per-target connection classes, the pipeline. This card *reuses* all of it for relation connections and adds **no** new cursor mechanics.
- **[`DONE-031-0.0.9`][kanban] (shipped)** — the `GlobalID` strategy system and the internal `decode_global_id`. This card is its **first consumer** (the ordering the `031` card pinned: "this card should land before Full Relay because root `node(id:)` … make[s] GlobalID encoding a public durability contract").
- **`WIP-ALPHA-032-0.0.9` (this card)** — root `node(id:)` / `nodes(ids:)` (`DjangoNodeField` / `DjangoNodesField`), the relation-as-Connection upgrade (`Meta.relation_shapes`), the six schema-validation diagnostics, the cursor-contract conformance suite, the public `testing.relay` helpers, and the library-first fakeshop activation.
- **[`WIP-ALPHA-033-0.0.9`][kanban] (parallel)** — connection-aware optimizer planning. The card body says both cards "rely on the walker recognizing `edges { node }`"; precisely: this card's surfaces are **functionally complete without `033`** but nested-connection selections lazy-load until the walker lands ([Decision 12](#decision-12--sequencing-against-the-connection-aware-optimizer-and-the-library-first-activation)).
- **[`TODO-ALPHA-034-0.0.10`][kanban]** — permissions; soft dependency (the Node entry points respect [`get_queryset`][glossary-get_queryset-visibility-hook] now, integrate with declared permissions later).

Justification: the card's own dependency list names `030` as the hard dependency (satisfied — it shipped) and the rest as soft/parallel; pinning the boundary keeps this spec scoped to the unshipped remainder of the eight-goal umbrella instead of re-describing shipped work.

Alternatives considered (and rejected): **Fold `033`'s walker work in (one mega-card).** Rejected: the cards were split deliberately — the optimizer walker is a bounded extension with its own spec home, and the card body pins the split ("ships in parallel").

### Decision 3 — Root fields dispatch through the package decode, not Strawberry's native node field

`DjangoNodeField` / `DjangoNodesField` synthesize their own resolvers that call [`types/relay.py::decode_global_id`][types-relay] and then dispatch to the resolved type's `resolve_node` / `resolve_nodes` classmethods. They do **not** wrap Strawberry's `relay.node()` field.

Justification:

- **Native dispatch cannot decode the default payload.** Strawberry's `NodeExtension` resolves `node_type = id.resolve_type(info)` = `info.schema.get_type_by_name(type_name)` (source-verified, `0.316.0`). The `0.0.9` default emits model-label payloads (`library.genre:42`); no schema type carries that name, so the native field fails for every default-strategy id. [`spec-031`][spec-031] shipped `decode_global_id` exactly as "the forward-looking helper `032` dispatches through".
- **The card mandates server-side distrust.** "Decode the GlobalID server-side (never trust the client's claim of which type the ID belongs to)" — `decode_global_id`'s resolve-then-enforce dispatch rejects payload shapes the resolved candidate's recorded strategy does not emit, which the native schema lookup cannot do.
- **The permission contract is already downstream.** `decode_global_id` returns the *type*; the shipped `resolve_node` / `resolve_nodes` defaults run [`get_queryset`][glossary-get_queryset-visibility-hook] on both sync and async branches, so dispatching to them gives the card's "respects `get_queryset`" requirement with zero new permission code.
- **Engine reuse everywhere else.** `GlobalID` parsing, the `Node` interface, the field machinery, and the connection mechanics all stay Strawberry's ([`START.md`][start] "Strawberry is the engine"); only the type-resolution hop is package-owned, because it is the one hop the engine resolves by GraphQL type name.

Alternatives considered (and rejected):

- **Use Strawberry's `relay.node()` and require the `type` strategy for refetchable types.** Rejected: it would make the `0.0.9` model-anchored default — the headline of [`DONE-031-0.0.9`][kanban] — incompatible with the Relay story shipping in the same release; the two cards were sequenced precisely so the root fields decode the new payload.
- **Patch `GlobalID.resolve_type` to recognize model labels.** Rejected: process-global monkeypatching of engine internals, breaks non-package Strawberry usage in the same process; the per-field resolver is surgical (the same reasoning that rejected the global `resolve_typename` patch in [`spec-031`][spec-031] Decision 3).
- **A registry-backed `Schema` subclass overriding type resolution.** Rejected: forces a package-owned `Schema` class onto consumers — a much larger surface commitment than two field factories, and contrary to the `strawberry.Schema(...)` + [`strawberry_config`][glossary-strawberry_config] composition every shipped example uses.

### Decision 4 — `DjangoNodeField` / `DjangoNodesField`: a bare interface form and a typed form

Both factories accept an **optional** target type:

- **Bare form** — `node: relay.Node | None = DjangoNodeField()` / `nodes: list[relay.Node | None] = DjangoNodesField()`: the Relay-spec canonical fields. The decoded id may resolve to *any* registered Relay-Node-shaped [`DjangoType`][glossary-djangotype]; the consumer's class-attribute annotation (the `relay.Node` interface) drives the GraphQL field type, mirroring [`DjangoListField`][glossary-djangolistfield]'s annotation-driven contract. `is_type_of` injection (shipped, unconditional) lets Strawberry resolve each returned model instance to its concrete GraphQL type.
- **Typed form** — `genre: GenreType | None = DjangoNodeField(GenreType)`: the [`GOAL.md`][goal] astronomy showcase shape (`galaxy: GalaxyNode = DjangoNodeField(GalaxyNode)`). Construction-time validation reuses the shared [`list_field.py::_validate_djangotype_target`][list-field] guards plus the connection-style fifth guard (the target must be Relay-Node-shaped, via the canonical `_is_relay_shaped` predicate). At request time, an id that decodes to a **different** type raises `GraphQLError` naming the expected and received types; a matching id dispatches to the target's `resolve_node` as usual. `DjangoNodesField(GenreType)` is the typed batch sibling with the same per-id check.
- **`nodes` semantics** — `ids: [GlobalID!]!`; results in input order; missing / hidden ids become `null` entries (so the return annotation is `list[relay.Node | None]`, rendering `[Node]!`); duplicate ids are resolved per position (each occurrence gets its row); resolution is **batched per distinct type** — ids are grouped by their decoded type and each type's `resolve_nodes` runs once (the shipped order-preserving `_order_nodes` reassembly), mirroring Strawberry's `get_node_list_resolver` grouping.

Justification:

- The card pins the canonical signatures (`node(id: GlobalID!): Node`, `nodes(ids: [GlobalID!]!): [Node]!` with positional `null`s) and the DoD exports both symbols; [`GOAL.md`][goal] independently pins the typed shape as the `1.0.0` consumer surface. One factory with an optional target serves both without a third symbol.
- The typed mismatch **error** (rather than `null`) is graphene-django's `Node.Field(only_type)` posture: a wrong-type id at a typed field is a client bug, and surfacing it costs nothing — the check runs on decoded payload data before any database query, so it cannot leak row existence.
- Batched per-type `resolve_nodes` is the only shape that scales a heterogeneous `nodes(ids:)` list — one query per distinct type rather than one per id.

Alternatives considered (and rejected):

- **Separate `DjangoNodeField` (typed-only) and a `DjangoRootNodeField` (bare).** Rejected: two names for one concept; the optional-argument form matches `DjangoConnectionField(target)` / `DjangoListField(target)` muscle memory while keeping the bare Relay-spec spelling available.
- **Typed mismatch returns `null`.** Rejected: it silently masks client bugs (an Item id at a `genre:` field is a programming error, not a visibility outcome), and the Relay-spec `null` contract is about *visibility*, which the mismatch check — running pre-query — never touches.
- **`nodes` raises on any missing id.** Rejected: the card pins "missing IDs become `null` entries (preserves positional correspondence)", which is also Strawberry's `required=not is_optional` behavior for the optional-entry annotation.

### Decision 5 — Null for invisible rows, GraphQLError for malformed ids

Two failure families with two contracts:

- **Visibility / existence failures → `null`.** A well-formed id whose row is hidden by [`get_queryset`][glossary-get_queryset-visibility-hook] or absent from the database resolves to `null` (bare and typed forms; a `null` list entry for `nodes`). Hidden and missing rows traverse the **same** code path — the filtered queryset's `qs.first()` (`required=False`) — so neither error shape nor timing distinguishes "exists but hidden" from "does not exist" (the card: "never reveal *existence* of hidden rows through error timing or status codes").
- **Format / decode failures → `GraphQLError`.** A malformed base64 string, a non-`type:id` payload, an unresolvable model label / type name, a payload shape the resolved type's strategy forbids, or a candidate with no recorded strategy — every [`ConfigurationError`][glossary-configurationerror] from [`decode_global_id`][types-relay] — is caught at the field boundary and re-raised as `GraphQLError("Invalid GlobalID: <reason>", extensions={"code": "GLOBALID_INVALID"})`. Decode runs entirely on payload data (no database access), so the error reveals nothing about any row.

Justification:

- The Relay spec requires `null` (not an exception) for an unresolvable-but-well-formed node lookup, and the card pins it twice; the shipped `resolve_node` default with `required=False` already implements the single-code-path property.
- A malformed id is a *request* error: silently returning `null` for it would make client bugs (truncated ids, double-encoding) indistinguishable from visibility outcomes — the exact debugging trap the loud-`GraphQLError` posture of the `first`+`last` guard and the filter layer's `Invalid filter input` (`extensions={"code": "FILTER_INVALID"}`) already avoids. The `GLOBALID_INVALID` code follows that shipped naming convention.
- Converting at the field boundary (rather than letting [`ConfigurationError`][glossary-configurationerror] bubble raw) keeps internal exception classes and `decode_global_id`'s implementation-flavored messages out of the public wire contract while preserving the diagnostic reason.

Alternatives considered (and rejected):

- **`null` for everything (malformed included).** Rejected: masks client bugs; loses the strategy-enforcement signal (`031`'s Step-2 rejections exist to be *seen*).
- **Raw `ConfigurationError` for malformed ids.** Rejected: leaks internal exception taxonomy into the wire contract; the message text would become an accidental API.
- **HTTP-level 4xx for malformed ids.** Rejected: GraphQL errors travel in-band; the transport stays 200 per the GraphQL-over-HTTP convention the rest of the package follows.

### Decision 6 — Relation-as-Connection synthesis at finalization Phase 2.5

A new finalizer step (after `install_globalid_typename_resolver`, before Phase 3 decoration) synthesizes connection siblings: for each Relay-Node-shaped type, walk the selected many-side relations (reverse FK, forward / reverse M2M — the [Relation handling][glossary-relation-handling] many-side set); for each whose resolved **target** type is Relay-Node-shaped, apply the resolved shape (`Meta.relation_shapes` entry, else `"both"`):

- `"both"` — keep the generated `list[T]` field; add `<field>_connection` (camel-cased to `<field>Connection` by Strawberry).
- `"connection"` — add `<field>_connection`; remove the `list[T]` annotation/resolver for the relation.
- `"list"` — synthesize nothing (today's shipped shape).

The synthesized field is `relay.connection(_connection_type_for(target_type), resolver=<relation resolver>)` — the [`spec-030`][spec-030] factory pieces verbatim, with one difference: the resolver body seeds the pipeline from the **parent's relation manager** (`getattr(root, <accessor>).all()`) instead of `model._default_manager.all()`, then runs the same tail (target [`get_queryset`][glossary-get_queryset-visibility-hook] → `filter` → `orderBy` → deterministic pk-order → optimizer seam → cursor slice). The synthesized signature carries the **target**'s sidecar-derived `filter:` / `order_by:` arguments (the shipped `_synthesized_signature`), and `totalCount` follows the target's [`Meta.connection`][glossary-metaconnection] (type-level, one stable connection shape per node type — the `_connection_type_for` cache is reused as-is). Name collisions (`<field>_connection` already a model field, a consumer-declared attribute, or another synthesized name) raise [`ConfigurationError`][glossary-configurationerror] naming the collision and the `"list"` opt-out.

Justification:

- Phase 2.5 is the only correct home: relation targets are settled (Phase 1), generated relation resolvers exist (Phase 2), and `strawberry.type` has not yet frozen the annotation set (Phase 3) — the same reasoning that placed interface application and sidecar binding there.
- The implicit `"both"` default is the card's pre-pinned direction ("Implicit upgrade (default): every `DjangoType` whose `Meta.interfaces` includes `relay.Node` automatically exposes its reverse-FK and M2M relations as Connections **in addition to** the existing `list[T]` shape", default `"both"` for Relay types) — preserved as a Decision, not re-litigated.
- Requiring a Relay-Node-shaped **target** mirrors the shipped `DjangoConnectionField` fifth guard: a connection's `node` field is typed by the target, and a connection of non-Node types has no Relay identity. Degrading silently to list-only under the *default* (while failing loud on an *explicit* request) keeps existing valid schemas building — the library's `GenreType.books` over the non-Node `BookType` must not start erroring because this card landed.
- Seeding from the relation manager (not the default manager) keeps Django's prefetch caches reachable — the seam [`WIP-ALPHA-033-0.0.9`][kanban]'s window-pagination planning will cooperate with.

Alternatives considered (and rejected):

- **Synthesize at class-creation time (`__init_subclass__`).** Rejected: relation targets may be undeclared at that point ([Definition-order independence][glossary-definition-order-independence]); the target-is-Node-shaped gate needs settled definitions.
- **Connections only on explicit `Meta.relation_shapes` opt-in (no implicit default).** Rejected: the card pre-pins the implicit upgrade as the default; per-relation opt-in is the `"list"` narrowing, not the baseline.
- **Allow connections over non-Node targets (plain edges, no `GlobalID`).** Rejected: contradicts the shipped `DjangoConnectionField` guard and produces connections whose nodes are not refetchable — the broken half of the Relay contract this card exists to complete.
- **A `<field>s_connection`-free naming scheme (replace the list field wholesale).** Rejected: silently removing the shipped `list[T]` shape is a breaking schema change for every existing Relay-shaped consumer; the sibling-field convention (`itemsConnection` alongside `items`) is the card's stated naming and is additive.

### Decision 7 — `Meta.relation_shapes` is a net-new `ALLOWED_META_KEYS` key, stored on the definition

`Meta.relation_shapes` lands **directly** in [`ALLOWED_META_KEYS`][base] (NOT a `DEFERRED_META_KEYS` promotion) — the net-new-key rule of [`spec-031`][spec-031] Decision 6 / [`spec-030`][spec-030] Decision 8: the key ships functional in the same card that adds it. A `_validate_relation_shapes(meta, value, relay_shaped)` helper (called from [`_validate_meta`][base], structurally modeled on `_validate_connection`):

- `None` (absent) → `None` (every eligible relation defaults to `"both"` at synthesis time);
- a non-`dict`, non-`str` keys, or values outside `{"list", "connection", "both"}` → [`ConfigurationError`][glossary-configurationerror] naming the offending entry and listing the valid shapes (typo guard);
- the key on a non-Relay-Node type (the precomputed `relay_shaped` bool, the same predicate `Meta.connection` uses) → [`ConfigurationError`][glossary-configurationerror] ("`Meta.relation_shapes` requires a Relay-Node-shaped type; add `relay.Node` to `Meta.interfaces` or remove the key");
- key names referencing unknown model fields, non-relation fields, single-valued relations (forward FK / OneToOne — there is nothing to paginate), or fields excluded from the selected set → [`ConfigurationError`][glossary-configurationerror] naming the field and the reason. Name-existence checks run at type creation (mirroring the [`Meta.optimizer_hints`][glossary-metaoptimizer_hints] typo guard); the target-is-Node-shaped check runs at finalization (targets resolve there — [Decision 6](#decision-6--relation-as-connection-synthesis-at-finalization-phase-25)).

The normalized dict is stored on [`DjangoTypeDefinition`][definition] (a new `relation_shapes` slot, populated in `__init_subclass__` like the `connection` / `filterset_class` / `orderset_class` / `globalid_strategy` slots), so the Phase-2.5 synthesis reads the per-type declaration from the canonical definition record.

Justification: identical to the four precedents — the key's feature ships in this card, the finalizer reads definitions (not re-parsed `Meta`), and gating to Relay-Node types keeps the eligibility rule single-sited with `Meta.connection` / `Meta.globalid_strategy`.

Alternatives considered (and rejected):

- **A `DEFERRED_META_KEYS` promotion.** Rejected: never reserved; ships functional now.
- **A boolean `Meta.relation_connections = True`.** Rejected: cannot express the per-relation `"list"` / `"connection"` / `"both"` narrowing the card pre-pins.
- **Defer all validation to finalization.** Rejected: name-level typos are detectable at type creation, and the package's posture is fail-at-the-earliest-phase-that-can-know ([`Meta.optimizer_hints`][glossary-metaoptimizer_hints] precedent); only the target-shape check genuinely needs finalization.

### Decision 8 — The six schema-validation diagnostics

The card's DoD requires "six schema-validation diagnostics … with the documented messages." This spec pins the enumeration — the six are the six `strawberry.relay` **non-interface helpers**, each rejected by name when found in [`Meta.interfaces`][glossary-metainterfaces]:

1. `relay.GlobalID` — "a scalar-like id wrapper, not an interface; Relay-Node-shaped types get `id: GlobalID!` automatically from `relay.Node`."
2. `relay.NodeID` — "an annotation helper for custom id fields (`id: relay.NodeID[int]`), not an interface."
3. `relay.Connection` — "a generic output type; declare [`Meta.connection`][glossary-metaconnection] / use [`DjangoConnectionField`][glossary-djangoconnectionfield] for connection shapes."
4. `relay.ListConnection` — same remediation as `Connection`.
5. `relay.Edge` — "a generic output type the connection machinery instantiates; not consumer-declarable."
6. `relay.PageInfo` — "a generated pagination type; not an interface."

All six already *fail* today through `_validate_interfaces`'s generic "is not a Strawberry interface" branch (none carries `is_interface=True` — [Current state](#current-state)); Slice 1 adds a named branch that fires **first**, so the message tells the consumer what the helper is and what they probably meant (`relay.Node`). Two further diagnostics the card body lists are **already shipped** and get re-affirmation pins, not new code: the non-Strawberry-interface-class rejection naming the offending class, and the `Meta.connection`-on-non-Node rejection with the documented remediation. One is **net-new in Slice 2**: a declared `DjangoNodeField()` / `DjangoNodesField()` on a registry with no Relay-Node-shaped types raises at finalization with the card's exact message — `"node lookup configured but no Node types registered."` — backed by a module-level ledger both factories append to (`registry.clear()` co-clears it; the `_helper_referenced_filtersets` / `_helper_referenced_ordersets` precedent).

Justification:

- The named-helper messages convert the most common Relay-configuration mistake (reaching for the helper class that *sounds* right) from a generic rejection into a remediation: each message says what the helper is and names the correct surface.
- The enumeration ambiguity is real — the card's DoD count ("six") could also be read as the four validation bullets plus two — so this spec pins the six-helpers reading (the only reading that yields exactly six) and tracks the call in [Risks and open questions](#risks-and-open-questions).
- The no-Node-types check must live at finalization, not field construction: `DjangoNodeField()` runs at class-body time, typically before any `DjangoType` module imports; only the finalizer sees the settled registry.

Alternatives considered (and rejected):

- **Skip the named branch (the generic rejection already fires).** Rejected: the card explicitly requires the helper-naming messages; a generic "not an interface" for `relay.Connection` leaves the consumer to guess that `Meta.connection` exists.
- **Validate the no-Node-types case at the first `node(id:)` request.** Rejected: a schema-shape error must fail at build time (the package's fail-loud-at-finalization posture), not on first traffic.

### Decision 9 — Cursor mechanics stay delegated to Strawberry; this card pins the conformance contract

No new cursor code ships. The cursor remains Strawberry's `ListConnection` opaque payload — `to_base64("arrayconnection", <offset>)` — documented as **opaque** (clients must not parse it), with `relay_max_results` (via [`strawberry_config`][glossary-strawberry_config] passthrough, default 100) capping page sizes. What this card adds is the **conformance suite**: tests pinning the Relay-spec edge cases the card enumerates, against both a root [`DjangoConnectionField`][glossary-djangoconnectionfield] and a synthesized relation connection:

- `first: 0` → empty `edges` + well-formed `pageInfo`.
- `first: N` where N exceeds the remainder → the actual remainder, `hasNextPage: false`.
- An `after` cursor whose row was deleted → falls through to the next existing row, no error (the natural property of offset cursors: the cursor names a position, not a row).
- `first` + `last` together → the shipped `GraphQLError` (re-affirmed).
- `pageInfo` four-field correctness (`hasNextPage`, `hasPreviousPage`, `startCursor`, `endCursor`), **including** the spec-mandated invariant that `hasNextPage` is computed correctly even when the consumer did not request it.
- Backward pagination (`last` / `before`) honoring the Relay spec.

The card's `b64("offset:N")` wording is read as the *conceptual* cursor shape; the byte-exact payload is Strawberry's `arrayconnection:N`. Both are opaque base64 offset cursors; the spec records the discrepancy rather than changing the shipped format ([Risks and open questions](#risks-and-open-questions)). `Meta.cursor_field` (stable column-keyed cursors) stays out of scope per the card (BACKLOG item 39 sub-feature 3).

Justification: [`spec-030`][spec-030] Decision 9 already delegated cursor mechanics with the explicit rationale that hand-rolling pagination math is engine duplication; re-implementing it here to match an illustrative byte format would churn the shipped wire contract for zero consumer value. The conformance suite is the card's actual deliverable ("Cursor pagination math passes the Relay-spec test suite").

Alternatives considered (and rejected): **Re-implement cursors as literal `b64("offset:N")`.** Rejected: breaks every cursor minted since [`DONE-030-0.0.9`][kanban], duplicates `ListConnection`, and buys nothing — both formats are equally opaque to a compliant client.

### Decision 10 — Public `testing/relay.py` helpers and the export gate

A new [`django_strawberry_framework/testing/relay.py`][testing-init] ships exactly the two helpers the card's DoD names:

- **`global_id_for(type_cls, id) -> str`** — the encoded `GlobalID` string a finalized Relay-Node-shaped type emits for a pk: reads the definition's recorded `effective_globalid_strategy` and computes the strategy-appropriate payload (`model` / `type+model` → `model._meta.label_lower`; `type` → `graphql_type_name`), then base64-encodes via Strawberry's own `GlobalID`. For a `callable` / `custom` strategy it raises [`ConfigurationError`][glossary-configurationerror] — those encoders run on a live `(root, info)` pair the helper does not have, so it cannot promise the emitted payload. Non-finalized / non-Relay-Node inputs raise with the finalize-first remediation.
- **`decode_global_id(gid) -> tuple[type, str]`** — the public re-export of [`types/relay.py::decode_global_id`][types-relay] (same uniform-[`ConfigurationError`][glossary-configurationerror] contract; the internal helper's signature is already consumer-shaped).

This satisfies the package's tested-usage promotion discipline ([`spec-031`][spec-031] Decision 11 withheld the public export because "no shipped `0.0.9` consumer" existed): this card ships the consumer (the root fields) and the live fakeshop usage, so the public surface is earned. The helpers live under `testing/` (not the package root) because their audience is consumer *test suites* — the card's own DoD places them at `django_strawberry_framework.testing.relay`.

Justification: consumers writing live tests against the new durable ids need to mint expected ids without copy-pasting base64 (`global_id_for`) and to assert what an emitted id resolves to (`decode_global_id`); both upstreams leave this to hand-rolled `to_global_id` calls in consumer tests.

Alternatives considered (and rejected):

- **Export from the package root (`django_strawberry_framework.global_id_for`).** Rejected: the card names the `testing.relay` home; the root namespace is the schema-authoring surface, and these are test utilities.
- **`global_id_for` accepts a model instance and supports `callable` / `custom`.** Rejected for `0.0.9`: an instance-accepting variant could thread `root` but still lacks `info`; the strategy system pinned `callable` / `custom` as encode-only-at-request-time, and the helper must not mint ids the type would not emit. A consumer with a custom encoder owns its test helper (the same ownership line `031` drew for custom decode).

### Decision 11 — Module and test-file locations

- **Source:** `DjangoNodeField` / `DjangoNodesField` and the root-resolver synthesis land in a **new top-level [`django_strawberry_framework/relay.py`][relay-toplevel]** — the card's Files-likely-touched location, the home [`spec-031`][spec-031] Decision 11 explicitly reserved for this card, and the sibling of the same-shaped `connection.py` / `list_field.py` flat factory modules. The encode/decode internals **stay** in [`types/relay.py`][types-relay] (shipped there by `031`); the new module imports them. `testing/relay.py` is the public-helper home per [Decision 10](#decision-10--public-testingrelaypy-helpers-and-the-export-gate). The finalizer synthesis step and the `Meta.relation_shapes` validation land in [`types/finalizer.py`][finalizer] / [`types/base.py`][base] respectively (the card's list).
- **Tests:** the card names `tests/test_relay_node_field.py` and `tests/test_relay_connection.py`. A strict [`docs/TREE.md`][tree] mirror would instead demand a single `tests/test_relay.py` for the one new flat module. Per the [`docs/SPECS/NEXT.md`][next] conflict rule (prefer the card; flag the conflict), this spec adopts the card's **two** files — `tests/test_relay_node_field.py` for the Slice-2 root-field surface, `tests/test_relay_connection.py` for the Slice-3/4 relation-upgrade + conformance surface — and flags the mirror tension in [Risks and open questions](#risks-and-open-questions). `tests/testing/test_relay.py` mirrors `testing/relay.py` (no card conflict there). Relation-shapes *key validation* tests sit with the other `Meta` validation in [`tests/types/test_base.py`][test-types-base].

Justification: the top-level module matches both the card and the `connection.py` precedent (root-field factories are package-surface modules, not `types/` internals); splitting the two large test surfaces along slice lines keeps each file reviewable for an XL card.

Alternatives considered (and rejected):

- **Extend `types/relay.py` instead of a new top-level module.** Rejected: `types/relay.py` is the per-type Relay *foundation* (resolver injection, encode/decode); the root fields are consumer-facing schema surface, and `031` already pinned the split.
- **One `tests/test_relay.py`.** Rejected per the prefer-the-card rule; recorded as the fallback if the maintainer prefers strict mirroring.

### Decision 12 — Sequencing against the connection-aware optimizer and the library-first activation

Two sequencing constraints shape Slices 3–6:

- **Nested connections lazy-load until [`WIP-ALPHA-033-0.0.9`][kanban] lands.** Every connection derives an empty optimizer plan in `0.0.9`-as-shipped ([Current state](#current-state)); a synthesized `booksConnection` under a parent list therefore runs per-parent queries, and [Strictness mode][glossary-strictness-mode] `"raise"` correctly surfaces that as an N+1. Consequences pinned here: (a) this card's live nested-connection tests assert **behavior** (right rows, right pagination, right `totalCount`), never SQL shape — the SQL-shape assertions are `033`'s deliverable; (b) no shipped example converts an *optimizer-dogfooding* surface to connections in this card (the products conversion stays at [`TODO-BETA-051-0.1.5`][kanban], per the card's own deferral note); (c) the synthesized relation resolver seeds from the relation manager precisely so `033`'s window-pagination planning has a cooperation seam.
- **Library-first activation, via the `BookType` promotion.** The card's live-coverage DoD (refetch, paginated connection, cursor round-trip, `totalCount`) is satisfiable with the existing `GenreType` alone — but a *live* relation-as-Connection proof needs a Relay-shaped parent whose many-side target is also Relay-shaped, and the library has none today. Slice 6 promotes **`BookType`** to Relay-Node shape (`interfaces = (relay.Node,)`), making `GenreType.books` eligible and giving `nodes(ids:)` a second concrete type to batch across. The promotion changes `BookType.id` to `GlobalID!` (existing library assertions on integer book ids move to encoded model-label payloads — bounded test churn, the [`spec-031`][spec-031] Slice-4 precedent). `BookType` is the [`Meta.primary`][glossary-metaprimary] type for `library.Book`; its non-Relay `NullabilityOverrideBookType` secondary is unaffected (the model-label-routing audit constrains only model-label *emitters*, and the primary now both emits and decodes).

Justification: the card binds the products conversion to `033` explicitly; the library suite is the card's named live-coverage home; and promoting one library type is the minimal change that makes every DoD bullet live-provable without touching the optimizer-dogfooding products suite.

Alternatives considered (and rejected):

- **Hold Slice 3 (relation-as-Connection) until `033` merges.** Rejected: the surfaces are functionally independent; serializing XL-card slices behind a sibling card's schedule risks the joint `0.0.9` cut, and the behavior-only test posture plus strictness documentation cover the gap honestly.
- **Live relation-as-Connection proof in products instead.** Rejected: products' `test_products_optimizer_*` SQL-shape suite is exactly the regression surface the card fences off until `033`.
- **A new fakeshop fixture app instead of promoting `BookType`.** Rejected: a synthetic app exercises nothing real ([`START.md`][start]'s coverage-is-a-feature posture — the example exists to exercise the package via real flows), and the library graph already has the right shapes.

### Decision 13 — Version bumps are owned by the joint `0.0.9` cut

No slice edits `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock`; no [`CHANGELOG.md`][changelog] release heading is promoted. CHANGELOG bullets land under `[Unreleased]`. The `0.0.8` → `0.0.9` bump is owned by the **joint cut** releasing this card together with [`WIP-ALPHA-033-0.0.9`][kanban] and the shipped [`DONE-029-0.0.9`][kanban] / [`DONE-030-0.0.9`][kanban] / [`DONE-031-0.0.9`][kanban].

Justification: the exact precedent [`spec-031`][spec-031] Decision 12, [`spec-030`][spec-030] Decision 13, and [`spec-029`][spec-029] Decision 11 set; [`docs/SPECS/NEXT.md`][next] Step 6 mandates this Decision when multiple WIP cards share the target patch version. The on-disk version is still `0.0.8`; several `0.0.9`-tagged surfaces already ship under `[Unreleased]` against the unchanged version.

Alternatives considered (and rejected): **Bump the version in Slice 7.** Rejected: would race the sibling card for the same bump and promote a release heading before the cohort is cut.

## Implementation plan

The card ships as **six functional slices plus a doc + card-completion wrap**. Each functional slice is one PR; 1–2 are foundation-first, 3 builds on 2, 4 on 2–3, 5–6 close the public surface and live coverage. Line deltas are estimates.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — named-helper diagnostics + re-affirmation pins | [`django_strawberry_framework/types/base.py`][base] (named branch in `_validate_interfaces`), [`tests/types/test_base.py`][test-types-base] (extend) | ~8 (six named-helper rejections; non-interface-class pin; `Meta.connection`-on-non-Node pin) | `+70 / -5` |
| 2 — root fields: `DjangoNodeField` / `DjangoNodesField` + no-Node-types check + exports | [`django_strawberry_framework/relay.py`][relay-toplevel] (new), [`django_strawberry_framework/types/finalizer.py`][finalizer] (ledger check), [`django_strawberry_framework/__init__.py`][package-init] (exports), [`registry.py`][registry] (`clear()` co-clears the ledger), `tests/test_relay_node_field.py` (new) | ~22 (bare/typed node; nodes order/batch/duplicates; null semantics; `GLOBALID_INVALID` conversion; typed mismatch; no-Node-types finalize check; async paths; `SyncMisuseError` pass-through) | `+330 / -2` |
| 3 — relation-as-Connection: `Meta.relation_shapes` + Phase-2.5 synthesis | [`django_strawberry_framework/types/base.py`][base] (`ALLOWED_META_KEYS` += `"relation_shapes"` + `_validate_relation_shapes`), [`django_strawberry_framework/types/definition.py`][definition] (`relation_shapes` slot), [`django_strawberry_framework/types/finalizer.py`][finalizer] (synthesis step), [`django_strawberry_framework/connection.py`][connection] (relation-seeded resolver variant), `tests/test_relay_connection.py` (new), [`tests/types/test_base.py`][test-types-base] (extend) | ~18 (key validation matrix; both/connection/list shapes; default eligibility; non-Node-target silent-skip vs explicit-raise; name collision; sidecar args + `totalCount` on synthesized field; suppressed list field) | `+300 / -10` |
| 4 — cursor-contract conformance + permission integration | `tests/test_relay_connection.py` (extend), `tests/test_relay_node_field.py` (extend), [`tests/test_connection.py`][test-connection] (extend) | ~14 (first:0; overrun; stale-after fall-through; first+last; pageInfo incl. unrequested `hasNextPage`; backward pagination; hidden→null; missing→null same-path; mixed nodes batch) | `+260 / -0` |
| 5 — public `testing/relay.py` helpers | `django_strawberry_framework/testing/relay.py` (new), [`testing/__init__.py`][testing-init] (docstring note), `tests/testing/test_relay.py` (new) | ~8 (strategy-aware `global_id_for` per decodable strategy; callable/custom raise; non-finalized raise; `decode_global_id` re-export round-trip) | `+120 / -2` |
| 6 — fakeshop library activation | [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] (root node/nodes + `BookType` Relay promotion), [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] (extend + update churned assertions) | ~9 (live refetch; batch with null hole + order; cursor round-trip; totalCount; nested `booksConnection` behavior; hidden-row null; `global_id_for` round-trip through the live API) | `+220 / -60` |
| 7 — doc updates + card-completion wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`TODAY.md`][today], [`README.md`][readme], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban] | 0 (doc-only) | `+140 / -30` |

Total expected delta: ~1,400 lines across six functional slices plus the wrap — consistent with the card's XL sizing. No version-file edits (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).

## Edge cases and constraints

- **`first: 0`** — empty `edges`, well-formed `pageInfo` (`hasNextPage` true iff rows exist past the empty window). Pinned by the conformance suite.
- **Stale `after` cursor** — offset cursors name a *position*; a deleted row shifts the sequence and the cursor falls through to the next existing row, no error. Documented as inherent to the opaque offset format; stable column-keyed cursors are BACKLOG item 39 sub-feature 3.
- **`relay_max_results`** — Strawberry caps any single page (default 100) for root and synthesized connections alike; consumers raise it via [`strawberry_config`][glossary-strawberry_config]`(relay_max_results=...)`. The conformance suite pins the over-cap error shape.
- **Duplicate ids in `nodes(ids:)`** — each position resolves independently (the same row may appear twice); the per-type batch still issues one query per distinct type. Strawberry's own index-map collapses duplicate `GlobalID` keys, which is one reason the package owns the batch resolver rather than borrowing the native one wholesale.
- **`nodes(ids: [])`** — returns `[]` without touching the database.
- **A `GlobalID` for a non-Node `DjangoType`** — `decode_global_id` rejects it (absent recorded strategy); the root field surfaces `GLOBALID_INVALID`. No database access occurs, so no existence signal leaks.
- **Multi-type models at the root fields** — a model-label id routes to the [`Meta.primary`][glossary-metaprimary] type; a type-name id routes to the named type. The `031` model-label-routing audit already guarantees the primary can decode whatever its secondaries emit; the root fields inherit that invariant without new checks.
- **Typed field + secondary type** — `DjangoNodeField(SecondaryType)` is legal (the four target guards accept any registered Relay-shaped type); a model-label id then decodes to the *primary* and fails the typed match. Documented: typed fields over secondaries pair naturally with the `type` strategy (type-scoped ids), the same pairing `031` documented for disjoint identity scopes.
- **Bare `node` field with no other root fields** — Strawberry only registers schema types it can reach; a schema whose *only* root field is interface-typed `node` must pass its concrete types via `strawberry.Schema(types=[...])` or expose them through other fields. Documented in the root-field docstring; not package-fixable (engine behavior).
- **Relation shape `"connection"` removing the list field** — the synthesized connection replaces the annotation *before* Phase-3 decoration, so the SDL never carries the list form; consumer overrides of the relation field (annotation or `strawberry.field`) are `consumer_authored_fields` and the synthesis **skips overridden relations entirely** (the shipped override contract outranks the upgrade — the consumer owns that field's shape).
- **Self-referential M2M / reverse-FK cycles** — the synthesis is per-relation and non-recursive (it adds fields, never walks into the target), so cycles terminate trivially; nested query depth is the consumer's choice and the pre-`033` N+1 caveat applies per level.
- **Async end-to-end** — the root resolvers return the `resolve_node(s)` defaults' values, which are coroutines in async context; Strawberry awaits plain-field coroutines, and the synthesized relation connections reuse the shipped sync/async pipeline split ([`spec-030`][spec-030] Decision 10). An async [`get_queryset`][glossary-get_queryset-visibility-hook] met from a sync context raises [`SyncMisuseError`][glossary-syncmisuseerror], unchanged.
- **No existence oracle** — hidden and missing rows share one queryset path and one `null` result; the typed-mismatch and decode errors run before any query. The conformance suite asserts the error-paths-never-query property with a query-count assertion.

## Test plan

Tests live across the package-internal `tests/` tree and the `examples/fakeshop/test_query/` tree, per [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Coverage that can be earned by a real GraphQL query is earned there first; the rest lands in the package tree. File placement per [Decision 11](#decision-11--module-and-test-file-locations).

### Slice 1 — `tests/types/test_base.py` (extend)

- `test_interfaces_rejects_relay_globalid_named` / `..._nodeid_named` / `..._connection_named` / `..._listconnection_named` / `..._edge_named` / `..._pageinfo_named` — each helper in `Meta.interfaces` raises [`ConfigurationError`][glossary-configurationerror] whose message names the helper and the remediation.
- `test_interfaces_rejects_non_interface_class_named` — the shipped generic rejection still names the offending class (re-affirmation pin).
- `test_connection_key_requires_relay_node` — the shipped `Meta.connection` gate message (re-affirmation pin).

### Slice 2 — `tests/test_relay_node_field.py` (new)

- `test_bare_node_field_resolves_model_label_id` / `..._type_name_id` — `node(id:)` decodes both payload shapes per the target's strategy and returns the right concrete type (`is_type_of` dispatch).
- `test_typed_node_field_resolves_target` / `test_typed_node_field_mismatch_raises` — the typed form returns the row for a matching id and a `GraphQLError` naming expected/received types for a mismatched one.
- `test_node_hidden_row_returns_null` / `test_node_missing_row_returns_null` — both through a `get_queryset`-filtered type; plus `test_node_null_paths_issue_equal_queries` (the no-existence-oracle query-count pin).
- `test_node_malformed_id_graphql_error` — malformed base64 / unresolvable label / strategy-forbidden shape each surface `GLOBALID_INVALID`, never a raw [`ConfigurationError`][glossary-configurationerror].
- `test_nodes_preserves_input_order_with_null_holes` / `test_nodes_batches_per_type` (query-count: one per distinct type) / `test_nodes_duplicate_ids` / `test_nodes_empty_list`.
- `test_node_field_without_node_types_raises_at_finalize` — the ledger check fires with the documented message; `registry.clear()` resets the ledger.
- `test_node_async_context` / `test_nodes_async_context` — async execution paths; `test_node_sync_async_get_queryset_raises_sync_misuse` — the [`SyncMisuseError`][glossary-syncmisuseerror] pass-through.
- `test_public_exports` — `DjangoNodeField` / `DjangoNodesField` importable from the package root.

### Slice 3 — `tests/test_relay_connection.py` (new) + `tests/types/test_base.py` (extend)

- `test_meta_relation_shapes_in_allowed_meta_keys` (not in `DEFERRED_META_KEYS`); `test_relation_shapes_validation_matrix` — non-dict, bad value, unknown field, non-relation field, single-valued relation, excluded field, non-Relay declaring type each raise.
- `test_default_both_synthesizes_connection_sibling` — an eligible reverse-FK / forward-M2M / reverse-M2M relation gains `<field>Connection` alongside the list field (SDL assertion).
- `test_shape_connection_suppresses_list` / `test_shape_list_suppresses_connection`.
- `test_non_node_target_silently_list_only` (default) / `test_non_node_target_explicit_raises` (explicit `"connection"` / `"both"`).
- `test_consumer_overridden_relation_skipped` — a consumer-authored relation field is never upgraded.
- `test_generated_name_collision_raises` — a model field / consumer attribute named `<field>_connection`.
- `test_synthesized_connection_carries_sidecar_args_and_total_count` — `filter:` / `orderBy:` from the target's sidecars; `totalCount` iff the target's [`Meta.connection`][glossary-metaconnection] opts in.
- `test_synthesized_connection_runs_target_get_queryset` — visibility filtering inside the nested connection.

### Slice 4 — `tests/test_relay_connection.py` / `tests/test_relay_node_field.py` / `tests/test_connection.py` (extend)

- The conformance matrix of [Decision 9](#decision-9--cursor-mechanics-stay-delegated-to-strawberry-this-card-pins-the-conformance-contract), run against both a root connection and a synthesized relation connection: `test_first_zero`, `test_first_overrun`, `test_stale_after_cursor_falls_through`, `test_first_and_last_rejected` (re-affirmation), `test_page_info_four_fields`, `test_has_next_page_correct_when_unrequested`, `test_backward_pagination_last_before`, `test_relay_max_results_cap`.
- Permission integration per the Slice-4 checklist (hidden/missing/mixed `nodes` positions).

### Slice 5 — `tests/testing/test_relay.py` (new)

- `test_global_id_for_model_strategy` / `..._type_strategy` / `..._type_plus_model_strategy` — the helper's output equals the live emitted id (cross-checked against a schema execution).
- `test_global_id_for_callable_or_custom_raises` / `test_global_id_for_unfinalized_raises` / `test_global_id_for_non_node_raises`.
- `test_public_decode_round_trip` — `decode_global_id(global_id_for(T, pk)) == (T, str(pk))` for the decodable strategies.

### Slice 6 — `examples/fakeshop/test_query/test_library_api.py` (extend)

Against the live `/graphql/` HTTP stack (preserving the suite's schema-reload pattern):

- `test_node_refetch_genre` — query a genre's `id`, refetch it via `node(id:)`, assert field equality.
- `test_nodes_batch_mixed_types_order_and_null` — genre + book ids interleaved with one bogus-pk id; order preserved, `null` hole in place.
- `test_genres_connection_cursor_round_trip` / `test_genres_connection_total_count` — `endCursor` → `after` continuation; `totalCount` against the seeded count.
- `test_genre_books_connection_behavior` — nested `booksConnection` pagination + row correctness (**behavior only**; SQL-shape assertions are [`WIP-ALPHA-033-0.0.9`][kanban]'s).
- `test_node_hidden_row_null_live` — through a visibility-filtered type.
- Update existing `BookType` id assertions for the Relay promotion (integer ids → encoded model-label `GlobalID`s, minted via `testing.relay.global_id_for`).

## Doc updates

Each slice owns its own doc edits. The CHANGELOG-edit permission comes from Slice 7's doc-update step per the explicit-instruction rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — **AGENTS.md prohibits `CHANGELOG.md` edits without permission, and this spec's Slice 7 grants that permission**; the Slice 7 maintainer prompt must name the `CHANGELOG.md` edits explicitly so an agent does not infer permission from a standing document.

- **Slice 7 — GLOSSARY**
  - [`docs/GLOSSARY.md`][glossary]: flip [`DjangoNodeField`][glossary-djangonodefield] to `shipped (0.0.9)` and document both forms + the null/error contract; add net-new `## DjangoNodesField` and `## Meta.relation_shapes` entries (`shipped (0.0.9)`) with Index rows and Browse-by-category placements ("Relay"; "Type generation" for the `Meta` key); extend [Relay Node integration][glossary-relay-node-integration] (root refetch now shipped) and [`DjangoConnectionField`][glossary-djangoconnectionfield] (relation-as-Connection cross-reference). **The two net-new entries do not exist at spec-authoring time and creating them is out of scope for the [`docs/SPECS/NEXT.md`][next] flow** — Slice 7 of the build creates them (see [Risks and open questions](#risks-and-open-questions)).
- **Slice 7 — package docs**
  - [`docs/README.md`][docs-readme]: shipped-surface bullets for the root fields, the relation upgrade, and `testing.relay`; update the "Coming next" `0.0.9` line (the in-progress remainder shrinks to `033`).
  - [`docs/TREE.md`][tree]: add [`relay.py`][relay-toplevel], `testing/relay.py`, and the new test files to the current-layout trees.
  - [`TODAY.md`][today]: keep products-centric; refresh the `0.0.9` breaking-change note's "nothing decodes a GlobalID until root `node(id:)` ships" framing (the latent break is now live) — no products-surface claims change (activation is `0.1.5`).
  - [`README.md`][readme]: update the status paragraph's newest-shipped-surface line.
  - [`CHANGELOG.md`][changelog]: `### Added` bullets under `[Unreleased]` for `DjangoNodeField` / `DjangoNodesField` (+ public exports), the relation-as-Connection upgrade + `Meta.relation_shapes`, and `django_strawberry_framework.testing.relay` (the explicit permission grant above). No version-heading promotion (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).
- **Slice 7 — card-completion wrap**
  - [`KANBAN.md`][kanban]: move [`WIP-ALPHA-032-0.0.9`][kanban] to Done with the next `DONE-NNN-0.0.9` id; confirm the spec reference points at [`docs/spec-032-full_relay-0_0_9.md`][spec-032] (a `SpecDoc` DB edit re-rendered via `scripts/build_kanban_md.py`, not a hand edit). No version-file edits.

## Risks and open questions

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **The GLOSSARY needs net-new entries for `DjangoNodesField` and `Meta.relation_shapes`.** Neither symbol has a [`docs/GLOSSARY.md`][glossary] heading at spec-authoring time, and creating glossary entries is out of scope for the [`docs/SPECS/NEXT.md`][next] flow. Preferred answer: the build's Slice 7 adds both as `shipped (0.0.9)`, at which point both belong in the companion terms CSV; until then they are intentionally **absent** from `spec-032-full_relay-0_0_9-terms.csv` (the checker flags CSV terms with no glossary heading). Fallback: none — the entries are required before the card closes; this item makes the gap explicit, not deferred.
- **The "six diagnostics" enumeration.** The card's DoD says "Six schema-validation diagnostics from Goal 6"; the rendered card body lists six relay helpers in one bullet plus three more validation bullets, so the count is ambiguous. Preferred answer ([Decision 8](#decision-8--the-six-schema-validation-diagnostics)): the six are the six named-helper rejections — the only reading yielding exactly six — with the remaining bullets handled as two re-affirmation pins and one net-new finalization check. Fallback: if the maintainer intended a different six-item slate, the Slice-1/2 test names map one-to-one onto messages and can be re-grouped without code changes.
- **Card-named test files vs the `docs/TREE.md` mirror rule.** The card names `tests/test_relay_node_field.py` + `tests/test_relay_connection.py`; the TREE rule would put one `tests/test_relay.py` beside the one new flat module. Per the [`docs/SPECS/NEXT.md`][next] conflict rule this spec prefers the card ([Decision 11](#decision-11--module-and-test-file-locations)). Fallback: merge into `tests/test_relay.py` at review time; only file names move.
- **Cursor byte-format wording.** The card describes the cursor as `b64("offset:N")`; the shipped format is Strawberry's `b64("arrayconnection:N")`. Preferred answer ([Decision 9](#decision-9--cursor-mechanics-stay-delegated-to-strawberry-this-card-pins-the-conformance-contract)): keep the shipped format — both are opaque offset cursors and the card's wording is conceptual; changing bytes now would break every cursor minted since [`DONE-030-0.0.9`][kanban]. Fallback: a `CURSOR_PREFIX` override on [`DjangoConnection`][glossary-djangoconnection] if byte-exactness is ever required.
- **Nested-connection N+1 until `033`.** The relation-as-Connection upgrade ships functionally complete but unoptimized; [Strictness mode][glossary-strictness-mode] `"raise"` flags nested access. Preferred answer ([Decision 12](#decision-12--sequencing-against-the-connection-aware-optimizer-and-the-library-first-activation)): land with behavior-only live assertions and let [`WIP-ALPHA-033-0.0.9`][kanban] add the SQL-shape coverage; both cards ship in the same joint cut, so no released version carries the gap silently. Fallback: if `033` slips past the cut, the joint-cut CHANGELOG documents the nested-connection caveat explicitly before release.
- **`BookType` Relay-promotion blast radius.** Promoting `BookType` flips its `id` to `GlobalID!` and churns existing library assertions. Preferred answer: bounded, mechanical churn (the [`spec-031`][spec-031] Slice-4 precedent), worth it for a real live relation-connection proof. Fallback: keep `BookType` non-Relay and prove relation-as-Connection only in package tests, deferring live nested coverage to the products activation (`0.1.5`).
- **Interface-only schema reachability.** A consumer schema whose only root field is the bare `node` cannot reach concrete types for schema registration (engine behavior). Preferred answer: document the `strawberry.Schema(types=[...])` recourse in the root-field docstring and [`docs/GLOSSARY.md`][glossary]; every shipped example already reaches its types through other fields. Fallback: a package helper that feeds all registered Relay-Node types into `types=` — deferred until a consumer actually hits the edge (tested-usage discipline).
- **Suppressing the list field under `"connection"` interacts with sidecar resolvers.** Removing a generated list relation after consumers may have referenced it in hand-written resolver annotations is consumer-visible. Preferred answer: `"connection"` is an explicit opt-in narrowing; the default `"both"` never removes anything, so no existing schema changes shape without a consumer edit. Fallback: none needed — the failure mode requires the consumer to both opt in and keep stale references, which fails loud at schema build.

## Out of scope (explicitly tracked elsewhere)

- **Connection-aware optimizer planning** ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]) — the parallel [`WIP-ALPHA-033-0.0.9`][kanban]: walker recognition of `edges { node }`, window-paginated prefetch planning, [Plan cache][glossary-plan-cache] key hygiene for pagination args, and the products `test_products_optimizer_*` SQL-shape coverage for connections.
- **Fakeshop products activation** — the connections-only Query conversion, [`TODO-BETA-051-0.1.5`][kanban] (gated on `033` per the card).
- **Permissions subsystem** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions] / [Per-field permission hooks][glossary-per-field-permission-hooks]) — [`TODO-ALPHA-034-0.0.10`][kanban]; the Node entry points integrate when it lands.
- **BACKLOG item 39 "Relay magic"** — type-rename `GlobalID` migrations, polymorphic connections, `Meta.cursor_field`, row-count-threshold auto-upgrade, refetchable-container metadata, permission-aware cursor decoding ([`BACKLOG.md`][backlog]).
- **`search:` argument** — [`Meta.search_fields`][glossary-metasearch_fields], `0.1.2` ([`TODO-BETA-046-0.1.2`][kanban]).
- **Consumer test clients** — [`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase], `0.0.12`; `testing/relay.py` shares the subpackage but not the scope.
- **Version bump** — owned by the joint `0.0.9` cut ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).

## Definition of done

The completion contract the card is built against. Items are grouped by slice; the card completes when all six functional slices' items plus the wrap are satisfied.

**Spec + companion CSV**

1. [`docs/spec-032-full_relay-0_0_9.md`][spec-032] (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/spec-032-full_relay-0_0_9-terms.csv`][spec-032-terms] anchoring every project-specific term that **has** a [`docs/GLOSSARY.md`][glossary] heading; [`uv run python scripts/check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md`][check-spec-glossary] reports `OK: <N> terms`. The net-new `DjangoNodesField` / `Meta.relation_shapes` symbols have **no** glossary heading yet (out of scope for the spec-authoring flow), so they are intentionally absent from the CSV and tracked as the first [Risks and open questions](#risks-and-open-questions) item; the build's Slice 7 adds their glossary entries.

**Slice 1 — diagnostics**

2. [`types/base.py::_validate_interfaces`][base] rejects each of the six `strawberry.relay` non-interface helpers by name with the documented remediations; the non-interface-class and [`Meta.connection`][glossary-metaconnection]-on-non-Node gates carry re-affirmation pins. [`tests/types/test_base.py`][test-types-base] covers all eight messages ([Decision 8](#decision-8--the-six-schema-validation-diagnostics)).

**Slice 2 — root fields**

3. [`django_strawberry_framework/relay.py`][relay-toplevel] ships `DjangoNodeField` (bare + typed) and `DjangoNodesField` (bare + typed): server-side decode via [`decode_global_id`][types-relay], dispatch to the resolved type's `resolve_node` / `resolve_nodes` (honoring [`get_queryset`][glossary-get_queryset-visibility-hook]), `null` for hidden/missing rows through one shared code path, `GraphQLError` `GLOBALID_INVALID` for decode failures, `GraphQLError` for typed mismatches, per-type-batched order-preserving `nodes` with `null` holes and duplicate-id support, sync + async execution, and the [`SyncMisuseError`][glossary-syncmisuseerror] pass-through ([Decision 3](#decision-3--root-fields-dispatch-through-the-package-decode-not-strawberrys-native-node-field) / [Decision 4](#decision-4--djangonodefield--djangonodesfield-a-bare-interface-form-and-a-typed-form) / [Decision 5](#decision-5--null-for-invisible-rows-graphqlerror-for-malformed-ids)).
4. Both factories are exported from [`django_strawberry_framework/__init__.py`][package-init]; the no-Node-types ledger check raises the documented finalization error and `registry.clear()` resets the ledger. `tests/test_relay_node_field.py` covers the slice.

**Slice 3 — relation-as-Connection**

5. [`ALLOWED_META_KEYS`][base] contains `"relation_shapes"` (not in `DEFERRED_META_KEYS`); `_validate_relation_shapes` enforces the shape / value / key-name / Relay-gating matrix at type creation and the value is stored on [`DjangoTypeDefinition`][definition] ([Decision 7](#decision-7--metarelation_shapes-is-a-net-new-allowed_meta_keys-key-stored-on-the-definition)).
6. The Phase-2.5 synthesis gives every eligible relation its `<field>Connection` sibling per the resolved shape (`"both"` default, `"connection"` suppresses the list, `"list"` suppresses the connection), reusing the shipped connection classes / sidecar arguments / `totalCount` opt-in with a relation-manager-seeded pipeline; consumer-overridden relations are skipped; non-Node targets degrade silently under the default and raise on explicit request; name collisions raise ([Decision 6](#decision-6--relation-as-connection-synthesis-at-finalization-phase-25)). `tests/test_relay_connection.py` + [`tests/types/test_base.py`][test-types-base] cover the slice.

**Slice 4 — conformance + permissions**

7. The Relay-spec conformance suite passes against root and synthesized connections (`first: 0`, overrun `first`, stale `after` fall-through, `first`+`last` rejection, four-field `pageInfo` incl. unrequested `hasNextPage`, backward pagination, `relay_max_results` cap), and the permission-integration tests pin the `null`-with-no-existence-oracle contract ([Decision 5](#decision-5--null-for-invisible-rows-graphqlerror-for-malformed-ids) / [Decision 9](#decision-9--cursor-mechanics-stay-delegated-to-strawberry-this-card-pins-the-conformance-contract)).

**Slice 5 — test helpers**

8. `django_strawberry_framework.testing.relay` exposes `global_id_for(type_cls, id)` (strategy-aware; raises for `callable` / `custom` / unfinalized / non-Node inputs) and `decode_global_id(gid)` (the public re-export); `tests/testing/test_relay.py` covers both ([Decision 10](#decision-10--public-testingrelaypy-helpers-and-the-export-gate)).

**Slice 6 — live coverage**

9. The fakeshop library suite gains the live Relay-shaped queries — `node(id:)` refetch, `nodes(ids:)` batch with order preservation and a `null` hole, paginated connection with cursor round-trip and `totalCount`, the nested `booksConnection` behavior proof (via the `BookType` Relay promotion), and the hidden-row `null` — with churned assertions updated via `testing.relay.global_id_for` ([Decision 12](#decision-12--sequencing-against-the-connection-aware-optimizer-and-the-library-first-activation)). Products activation remains untouched ([`TODO-BETA-051-0.1.5`][kanban]).

**Slice 7 — doc + card-completion wrap**

10. [`docs/GLOSSARY.md`][glossary] flips [`DjangoNodeField`][glossary-djangonodefield] to shipped and gains the `DjangoNodesField` / `Meta.relation_shapes` entries with Index + Browse-by-category rows; [`docs/README.md`][docs-readme] / [`docs/TREE.md`][tree] / [`TODAY.md`][today] / [`README.md`][readme] reflect the shipped surface; [`CHANGELOG.md`][changelog] `[Unreleased]` carries the `### Added` bullets (the explicit per-card permission grant named in the Slice 7 maintainer prompt).
11. [`KANBAN.md`][kanban] records the card as `DONE-NNN-0.0.9` (moved from [`WIP-ALPHA-032-0.0.9`][kanban]) with the card's spec reference pointing at [`docs/spec-032-full_relay-0_0_9.md`][spec-032], applied through the kanban DB + re-render.
12. **No version bump lands in this card** per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut): `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` are unchanged; no [`CHANGELOG.md`][changelog] release heading is promoted (the joint `0.0.9` cut owns the bump).
13. Package coverage stays at 100% (`fail_under = 100`). Routine per-slice work does not run pytest locally — owned by CI per the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"Do not run pytest after edits"; worker-local validation is `uv run ruff format .` and `uv run ruff check --fix .`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[backlog]: ../BACKLOG.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
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
[glossary-filter_input_type]: GLOSSARY.md#filter_input_type
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-graphqltestcase]: GLOSSARY.md#graphqltestcase
[glossary-metaconnection]: GLOSSARY.md#metaconnection
[glossary-metafields_class]: GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: GLOSSARY.md#metafilterset_class
[glossary-metaglobalid_strategy]: GLOSSARY.md#metaglobalid_strategy
[glossary-metainterfaces]: GLOSSARY.md#metainterfaces
[glossary-metaname]: GLOSSARY.md#metaname
[glossary-metaoptimizer_hints]: GLOSSARY.md#metaoptimizer_hints
[glossary-metaorderset_class]: GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: GLOSSARY.md#metaprimary
[glossary-metasearch_fields]: GLOSSARY.md#metasearch_fields
[glossary-order_input_type]: GLOSSARY.md#order_input_type
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-per-field-permission-hooks]: GLOSSARY.md#per-field-permission-hooks
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-relay-globalid-strategy]: GLOSSARY.md#relay_globalid_strategy
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-safe_wrap_connection_method]: GLOSSARY.md#safe_wrap_connection_method
[glossary-strawberry_config]: GLOSSARY.md#strawberry_config
[glossary-strictness-mode]: GLOSSARY.md#strictness-mode
[glossary-syncmisuseerror]: GLOSSARY.md#syncmisuseerror
[glossary-testclient]: GLOSSARY.md#testclient
[spec-032]: spec-032-full_relay-0_0_9.md
[spec-032-terms]: spec-032-full_relay-0_0_9-terms.csv
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-011]: SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md
[spec-015]: SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-029]: SPECS/spec-029-consumer_dx_cleanup-0_0_9.md
[spec-030]: SPECS/spec-030-connection_field-0_0_9.md
[spec-031]: SPECS/spec-031-globalid_encoding-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../django_strawberry_framework/types/base.py
[connection]: ../django_strawberry_framework/connection.py
[definition]: ../django_strawberry_framework/types/definition.py
[finalizer]: ../django_strawberry_framework/types/finalizer.py
[list-field]: ../django_strawberry_framework/list_field.py
[package-init]: ../django_strawberry_framework/__init__.py
[registry]: ../django_strawberry_framework/registry.py
[relay-toplevel]: ../django_strawberry_framework/relay.py
[testing-init]: ../django_strawberry_framework/testing/__init__.py
[types-relay]: ../django_strawberry_framework/types/relay.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-connection]: ../tests/test_connection.py
[test-types-base]: ../tests/types/test_base.py

<!-- examples/ -->
[fakeshop-library-schema]: ../examples/fakeshop/apps/library/schema.py
[fakeshop-test-library]: ../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->
[check-spec-glossary]: ../scripts/check_spec_glossary.py

<!-- .venv/ -->

<!-- External -->
