# Spec: Django-model-based GlobalID encoding — `Meta.globalid_strategy`, the `RELAY_GLOBALID_STRATEGY` setting, and the `model` / `type` / `type+model` / callable strategies

Planned for `0.0.9` (card [`WIP-ALPHA-031-0.0.9`][kanban]). **This spec is an open build plan, not a shipped record.** The card is the lowest-NNN WIP card in the `0.0.9` cohort and the **Relay identity-format decision**: it pins the durable shape of every Relay `GlobalID` a [`DjangoType`][glossary-djangotype] emits before the [Full Relay story][kanban] ([`WIP-ALPHA-032-0.0.9`][kanban]) mints durable root `node(id:)` / refetch IDs into the public surface. The [Slice checklist](#slice-checklist) below stays unticked as the contract record (build progress is tracked in the build plan, not here); the [Definition of done](#definition-of-done) describes the closure conditions; the [Current state](#current-state) section describes the repo as of this spec's authoring, before the build. **Version boundary** (see [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)): this card shares the `0.0.9` patch line with two sibling WIP cards ([`WIP-ALPHA-032-0.0.9`][kanban], [`WIP-ALPHA-033-0.0.9`][kanban]) and the already-shipped [`DONE-029-0.0.9`][kanban] / [`DONE-030-0.0.9`][kanban]; the `pyproject.toml` / [`__version__`][package-init] / [`tests/base/test_init.py::test_version`][test-base-init] bump to `0.0.9` is owned by the **joint cut**, not by this card. This card's slices land within the `0.0.9` line and never bump the version themselves (the on-disk version is still `0.0.8` at spec-authoring time).

Status: planned — not started. Five slices: Slice 1 (the net-new [`Meta.globalid_strategy`][glossary-djangotype] key validated AND stored on [`DjangoTypeDefinition`][definition], the `RELAY_GLOBALID_STRATEGY` settings read, and the `Meta` → setting → package-default precedence resolver), Slice 2 (the **encode** seam — a strategy-parameterized `resolve_typename` default injected at finalization Phase 2.5 via the existing `__func__` identity test, with the `model` / `type` / `type+model` / callable encoders and the default flipped to `model`), Slice 3 (the **decode** seam — `decode_global_id`'s resolve-then-enforce dispatch: resolve a candidate via Django's app registry / a `graphql_type_name` lookup → the primary [`DjangoType`][glossary-djangotype], then enforce the candidate's strategy permits the payload shape, plus the encoder/decoder symmetry coverage for the three decodable strategies including the transitional `type+model` accept-old-IDs path — `callable` is encode-only), Slice 4 (live HTTP coverage proving emitted IDs use the model-label payload and that filtering by the new [`GlobalID`][glossary-relay-node-integration] round-trips, plus the multiple-`DjangoType`-per-model routing assertion), and Slice 5 (doc updates + the card-completion wrap; grants the per-card [`CHANGELOG.md`][changelog] edit permission [`AGENTS.md`][agents] otherwise withholds). Slices 1→2→3→4 are sequential (each builds on the prior); Slice 5 lands last.

Owner: package maintainer.

Predecessors: [`spec-030-connection_field-0_0_9.md`][spec-030] (the most-recently-shipped spec — the canonical voice / depth / section-layout reference for this document; its [Decision 13][spec-030] joint-`0.0.9`-cut version-bump boundary is the precedent [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut) reuses verbatim, and its [Decision 8][spec-030] net-new-`ALLOWED_META_KEYS`-stored-on-the-definition pattern is the precedent [Decision 6](#decision-6--metaglobalid_strategy-is-a-net-new-allowed_meta_keys-key-stored-on-the-definition) reuses for the net-new `Meta.globalid_strategy` key); [`spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (its [Decision 6][spec-029] net-new-key rule and its [Decision 11][spec-029] joint-cut version boundary are the twin precedents this card cites); [`spec-015-relay_interfaces-0_0_5.md`][spec-015] (the [Relay Node integration][glossary-relay-node-integration] foundation this card extends — the four injected `resolve_*` defaults, the `__func__` identity test that distinguishes consumer overrides from framework defaults, the `id: GlobalID!` suppression, the [`SyncMisuseError`][glossary-syncmisuseerror] marker, and the [composite-primary-key rejection][glossary-relay-node-integration] this card inherits unchanged). [`docs/GLOSSARY.md`][glossary] carries [Relay Node integration][glossary-relay-node-integration] (`shipped 0.0.5`), which already documents the type-anchored `id: GlobalID!` this card re-roots onto the Django model label; it does **not** yet carry `Meta.globalid_strategy` or `RELAY_GLOBALID_STRATEGY` entries (the net-new symbols this card introduces — see [Risks and open questions](#risks-and-open-questions)).

Revision history (kept inline so the spec is self-contained):

- **Revision 2** — first feedback pass (review of rev1 captured in [`docs/feedback.md`][feedback]). Three P1 (foundational) findings reshaped the encode/decode contract, applied foundation-first because they shape the rest:
  - **P1 — callable encoder signature must match the `resolve_typename` seam, not `resolve_id`.** [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion) changes the callable signature from `(type_cls, model, node_id, info)` to `(type_cls, model, root, info)` (sync; mirrors `resolve_typename(root, info)`, which runs *before* `resolve_id`). Supplying `node_id` would force a premature/doubled `resolve_id` and break async — contradicting the spec's own async edge case. Node-id-dependent type-name slots are out of scope for this seam. Strategy table, Slice 2 encode helper, and the async edge case updated.
  - **P1 — decode must enforce the resolved candidate's strategy shape.** [Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type) is rewritten as a two-step **resolve-then-enforce** dispatch: resolve a candidate, then reject a payload shape the candidate's `_resolve_globalid_strategy` does not emit (`model` model-label only / `type` type-name only / `type+model` both). Without it `type+model` was indistinguishable from a permissive decoder and `model` kept silently accepting stale type-anchored IDs. Negative tests added.
  - **P1 — type-name decode keys on `graphql_type_name`, not `type_cls.__name__`.** A `Meta.name`-renamed type emits its `graphql_type_name`, so decode must invert that, not the class name. Added a new `registry.definition_for_graphql_name(name)` helper and a `Meta.name` `type`-strategy round-trip test.
  - **P2 — callable decode is encode-only in `0.0.9`.** Slice 3 required a callable decode path the spec left open; resolved by making `callable` **encode-only** (no `decode_global_id` branch; consumer-owned, paired decoder deferred to [`WIP-ALPHA-032-0.0.9`][kanban]). Round-trip symmetry now covers the three decodable strategies; the open question is closed.
  - **P3 — `decode_global_id` input shape pinned.** It accepts a [`relay.GlobalID`][glossary-relay-node-integration] instance or its base64 string (which it `from_base64`-decodes), never a raw `"app_label.model:pk"` payload; examples and tests use encoded values.
- **Revision 1** — initial draft authored from the [`WIP-ALPHA-031-0.0.9`][kanban] card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-06-09). Pinned the canonical spec filename, the card-scope boundary against the two sibling `0.0.9` Relay cards, the encode seam (a strategy-parameterized `resolve_typename` default injected through the existing Phase-2.5 `__func__` mechanism — verified against the locked Strawberry `0.316.0` source: `relay.types.Node._id` reads `resolve_typename` for the `type_name` slot), the four strategies (`model` as the new default, `type` as the opt-in legacy/standard-Relay convention, `type+model` as the transitional decoder/encoder mode, callable for custom encodings), the `Meta.globalid_strategy` → `RELAY_GLOBALID_STRATEGY` → package-default precedence, the decode dispatch through Django's app registry then the framework registry to the primary [`DjangoType`][glossary-djangotype], the breaking-default-flip posture (acceptable pre-`1.0.0`, opt-out via the `type` strategy), the proxy / MTI / custom-`resolve_id_attr` / composite-pk / model-rename edge cases, the `types/relay.py` module location, the no-public-export posture (the public `testing/relay` helpers ship with [`WIP-ALPHA-032-0.0.9`][kanban]), and the joint-cut version boundary.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [Relay Node integration][glossary-relay-node-integration] — the shipped `0.0.5` foundation this card extends: `Meta.interfaces = (relay.Node,)` declares a Relay-Node-shaped type with `id: GlobalID!` and the four injected `resolve_*` defaults wired through `cls.get_queryset`. The `GlobalID` payload is what this card re-roots from the GraphQL type name onto the Django model label.
- [`DjangoType`][glossary-djangotype] — the type whose rows emit the `GlobalID`; the net-new [`Meta.globalid_strategy`][glossary-djangotype] key declares the per-type encoding strategy. The new key is validated and stored on the definition exactly as [`Meta.connection`][glossary-metaconnection] was in [`spec-030`][spec-030].
- [`Meta.interfaces`][glossary-metainterfaces] — the key that declares `relay.Node`; [Decision 6](#decision-6--metaglobalid_strategy-is-a-net-new-allowed_meta_keys-key-stored-on-the-definition) gates `Meta.globalid_strategy` to a Relay-Node-shaped type via the canonical `_is_relay_shaped(cls, interfaces)` predicate (the same one [`Meta.connection`][glossary-metaconnection] uses), accepting both `relay.Node` in `Meta.interfaces` and direct `relay.Node` inheritance.
- [`Meta.name`][glossary-metaname] — overrides the GraphQL type name; under the `type` strategy the `GlobalID` payload's type-name slot tracks `Meta.name` (the GraphQL surface name), which is exactly the refactor-fragility the `model` default avoids ([Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion)).
- [`Meta.model`][glossary-metamodel] — the Django model whose `model._meta.label_lower` (`"app_label.modelname"`, e.g. `products.item`) is the `model`-strategy payload; the decode side resolves that label back to the model via Django's app registry ([Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type)).
- [`Meta.primary`][glossary-metaprimary] — the multi-`DjangoType`-per-model rule; a decoded model-label ID routes through `registry.get(model)` (the primary, or the lone registered type), unless the consumer opts into type-scoped IDs via the `type` strategy for disjoint auth / cache scopes.
- [`ConfigurationError`][glossary-configurationerror] — raised at type-creation time for an unknown / malformed `Meta.globalid_strategy` value or the key on a non-Relay-Node type, and at finalization for an unknown `RELAY_GLOBALID_STRATEGY` setting value (the card DoD: "validation reject unknown strategy names loudly with `ConfigurationError`").
- [`finalize_django_types`][glossary-finalize_django_types] — the single-threaded schema-setup synchronization point whose Phase 2.5 already injects the four Relay `resolve_*` defaults; the strategy-parameterized `resolve_typename` injection lands in the same phase ([Decision 10](#decision-10--resolve_typename-injection-via-the-__func__-identity-test-at-phase-25)).
- [Definition-order independence][glossary-definition-order-independence] — the collection-then-finalize split the `resolve_typename` injection rides on; the effective strategy is resolved once per type at finalization, so the encoding is a stable schema-build-time contract.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — the decode dispatch routes through the resolved type's `resolve_node`, which honors `get_queryset`; a decoded ID for a row the requesting user cannot see resolves to `null`, never an error (the contract [`WIP-ALPHA-032-0.0.9`][kanban] consumes).
- [`SyncMisuseError`][glossary-syncmisuseerror] — the typed marker the Relay-foundation `resolve_node` / `resolve_nodes` raise on the sync branch when `get_queryset` returns a coroutine; the decode helper inherits this contract unchanged.
- [`DjangoConnectionField`][glossary-djangoconnectionfield] / [`DjangoConnection`][glossary-djangoconnection] — the [`DONE-030-0.0.9`][kanban] connection surface; its `edges { node { id } }` emit `GlobalID`s through the same per-node `resolve_typename` seam this card re-roots, so the connection field picks up the model-label payload with no `connection.py` change.
- [`DjangoNodeField`][glossary-djangonodefield] — the planned root single-node lookup field; **not** this card (it lands with the [Full Relay story][kanban], [`WIP-ALPHA-032-0.0.9`][kanban]); cited because it is the first consumer of the [decode helper](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type) this card ships.
- [`Relation handling`][glossary-relation-handling] — relation `id`-only selections; [FK-id elision][glossary-fk-id-elision] reads the FK column off the parent and stringifies it into the `node_id` slot, so the model-label re-root touches only the type-name slot, never the relation's `id` round-trip.
- [FK-id elision][glossary-fk-id-elision] — the optimizer reads a forward-FK's `id` off the parent row; its [Multi-database cooperation][glossary-multi-database-cooperation] `router.db_for_read` stub-routing is the multi-DB analogue of this card's model-label-to-model routing — both resolve a Django model from a payload without a second query.
- [Scalar field conversion][glossary-scalar-field-conversion] — the converter table that maps an auto-pk to the Relay `GlobalID` when `Meta.interfaces = (relay.Node,)` is declared; this card changes the `GlobalID`'s payload, not the converter row that selects it.
- [Schema introspection management command][glossary-schema-introspection-management-command] — `manage.py inspect_django_type` reports the interface-supplied `GlobalID!` row for a Relay-Node pk; the row label is unaffected by the payload change (the command reports the GraphQL type / nullability, not the wire payload).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the optimizer projects the Django pk as a connector column for `resolve_id`; the model-label re-root needs the same pk projection unchanged ([Current state](#current-state)).
- [`strawberry_config`][glossary-strawberry_config] — the scalar-map factory every example schema in this spec passes to `strawberry.Schema(...)` alongside the singleton-factory [`DjangoOptimizerExtension`][glossary-djangooptimizerextension].
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — the `1.0.0` rule that example-project schemas reference only shipped features; the breaking default flip ([Decision 9](#decision-9--changing-the-default-to-model-is-a-breaking-wire-format-change-acceptable-pre-100)) is timed before that freeze so the durable identity format is settled at `1.0.0`.

Dependency and forward-composition surfaces a reader will hit:

- [`DjangoNodeField`][glossary-djangonodefield] / the [Full Relay story][kanban] (`0.0.9`, [`WIP-ALPHA-032-0.0.9`][kanban]) — the first consumer of the decode dispatch; root `node(id:)` / `nodes(ids:)` are out of scope here.
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] (`0.0.9`, [`WIP-ALPHA-033-0.0.9`][kanban]) — orthogonal; the GlobalID payload does not change the connection-walker work.
- [`BigInt` scalar][glossary-bigint-scalar] — a `BigAutoField` / `BigIntegerField` pk stringifies into the `node_id` slot via `str(...)`, same as today; the payload change is on the type-name slot only.
- [`apply_cascade_permissions`][glossary-apply_cascade_permissions] (`0.0.10`) — the decode dispatch respects [`get_queryset`][glossary-get_queryset-visibility-hook] immediately and gains declared-permission integration when the permissions subsystem lands.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package tests under `tests/` mirroring source; live HTTP tests under `examples/fakeshop/test_query/`); the live-HTTP-priority coverage rule; the no-pytest-after-edits rule; the settings-keys rule (add a settings key only when a feature needs it — [Decision 7](#decision-7--the-relay_globalid_strategy-setting-and-the-settings-key-discipline) adds `RELAY_GLOBALID_STRATEGY` now because this card is the feature that needs it); the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — Slice 5's doc-update step grants the explicit per-card permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; coverage is earned through fakeshop live-HTTP flows where practical (Slice 4) and package-internal `tests/types/` where the path is unreachable from a live query.
- [`docs/TREE.md`][tree] — tests mirror source one-to-one; the encode / decode logic lands in the existing [`django_strawberry_framework/types/relay.py`][relay] (the Relay foundation module) with coverage in [`tests/types/test_relay_interfaces.py`][test-relay-interfaces], not a new top-level module ([Decision 11](#decision-11--module-location-encodedecode-in-typesrelaypy-no-public-export-in-009)).
- [`START.md`][start] — markdown link convention (reference-style for cross-file links, all defs at the bottom under the 10 canonical group headers); the "Strawberry is the engine; DRF is the shape" rule ([Decision 3](#decision-3--the-encode-seam-a-strategy-parameterized-resolve_typename-default) injects into Strawberry's own `GlobalID` construction rather than hand-rolling one); the "add a settings key only when the feature that needs it lands" rule (a documented past mistake [`START.md`][start] #"Don't preemptively populate `conf.py` with future-feature settings").

## Slice checklist

Each top-level item maps to one commit / PR. **Five slices: four sequential functional slices (1→2→3→4, each builds on the prior) plus a doc + card-completion wrap (5).** Boxes are unticked because the work has not started.

- [ ] Slice 1: `Meta.globalid_strategy` net-new key (validated + stored on the definition) + `RELAY_GLOBALID_STRATEGY` settings read + the precedence resolver (per [Decision 5](#decision-5--precedence-metaglobalid_strategy--relay_globalid_strategy--package-default-model) / [Decision 6](#decision-6--metaglobalid_strategy-is-a-net-new-allowed_meta_keys-key-stored-on-the-definition) / [Decision 7](#decision-7--the-relay_globalid_strategy-setting-and-the-settings-key-discipline))
  - [ ] [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] grows `"globalid_strategy"` (net-new public key — NOT a [`DEFERRED_META_KEYS`][base] promotion, mirroring [`spec-030`][spec-030] [Decision 8][spec-030] and [`spec-029`][spec-029] [Decision 6][spec-029]). A `_validate_globalid_strategy` helper (called from [`_validate_meta`][base], structurally modeled on `_validate_connection`) accepts `"model"` / `"type"` / `"type+model"` or a callable; an unknown string or wrong type raises [`ConfigurationError`][glossary-configurationerror]; the key is gated to a Relay-Node-shaped type via the precomputed `relay_shaped` bool (`_is_relay_shaped(cls, interfaces)`).
  - [ ] The normalized value is **stored on [`DjangoTypeDefinition`][definition]** (a new `globalid_strategy` slot, populated in [`__init_subclass__`][base] like the `connection` / `filterset_class` / `orderset_class` slots) so the Phase-2.5 injection reads the per-type opt-in from the definition, not by re-parsing `Meta`.
  - [ ] A `_resolve_globalid_strategy(definition)` helper applies the precedence — `definition.globalid_strategy` (the `Meta` override) → [`conf.settings`][conf]`.RELAY_GLOBALID_STRATEGY` (the schema-wide setting, read defensively as "absent → package default") → the `"model"` package default — and validates the **setting** value (unknown setting string → [`ConfigurationError`][glossary-configurationerror] naming `RELAY_GLOBALID_STRATEGY`), since [`conf.py`][conf] is a thin reader that does not validate domain values.
  - [ ] Package coverage: [`tests/types/test_base.py`][test-types-base] gains the `"globalid_strategy"`-in-`ALLOWED_META_KEYS` / not-in-`DEFERRED_META_KEYS` assertion, the `_validate_globalid_strategy` failure modes (unknown string, non-Relay type, wrong type), and the `definition.globalid_strategy` storage assertion. A focused `tests/types/` test pins the three-tier precedence and the unknown-setting `ConfigurationError`.
- [ ] Slice 2: the encode seam — strategy-parameterized `resolve_typename` injection + the four encoders + the default flip to `model` (per [Decision 3](#decision-3--the-encode-seam-a-strategy-parameterized-resolve_typename-default) / [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion) / [Decision 9](#decision-9--changing-the-default-to-model-is-a-breaking-wire-format-change-acceptable-pre-100) / [Decision 10](#decision-10--resolve_typename-injection-via-the-__func__-identity-test-at-phase-25))
  - [ ] [`django_strawberry_framework/types/relay.py`][relay] gains an `encode_typename(definition, strategy)`-style internal helper that returns the type-name slot for the resolved strategy: `model` → `definition.model._meta.label_lower` (`"products.item"`); `type` → the GraphQL type name ([`definition.graphql_type_name`][definition], matching Strawberry's `info.path.typename` default); `type+model` → the model label (emit model-anchored, accept both on decode, per [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion)); callable → the consumer callable's return (signature `(type_cls, model, root, info) -> str`, sync, mirroring the `resolve_typename` seam — it never receives `node_id`, per [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion)).
  - [ ] An `install_globalid_typename_resolver(type_cls, definition)` step (called from [`finalize_django_types`][glossary-finalize_django_types] Phase 2.5, alongside `install_relay_node_resolvers`) resolves the effective strategy via `_resolve_globalid_strategy` and installs a `resolve_typename` classmethod UNLESS the consumer has overridden it — the same `__func__` identity test the four `resolve_*` defaults use (`existing.__func__ is relay.Node.resolve_typename.__func__`). For the `type` strategy the framework leaves Strawberry's default in place (which returns `info.path.typename`); for `model` / `type+model` / callable it installs the package closure.
  - [ ] Flip the **package default** from the (DONE-015) type-anchored `GlobalID` to `model`: a Relay-Node-shaped type with no `Meta.globalid_strategy` and no `RELAY_GLOBALID_STRATEGY` setting now emits the model-label payload (per [Decision 9](#decision-9--changing-the-default-to-model-is-a-breaking-wire-format-change-acceptable-pre-100)).
  - [ ] Package coverage: [`tests/types/test_relay_interfaces.py`][test-relay-interfaces] — each strategy's emitted type-name slot; the consumer-`resolve_typename`-override preservation (a declared override survives injection); the default-flip (no override → `model`); the `type`-strategy reproduces the pre-`0.0.9` GraphQL-type-name payload.
- [ ] Slice 3: the decode seam — `decode_global_id` dispatch + encoder/decoder symmetry + transitional `type+model` (per [Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type))
  - [ ] [`registry.py`][registry] gains `definition_for_graphql_name(name)` — a unique-`graphql_type_name` lookup over [`iter_definitions()`][registry] returning the matching [`DjangoTypeDefinition`][definition], raising [`ConfigurationError`][glossary-configurationerror] on ambiguity or miss (the type-name decode entry point; keyed on `graphql_type_name`, NOT `type_cls.__name__`, so a [`Meta.name`][glossary-metaname]-renamed type still decodes — [`docs/feedback.md`][feedback] P1).
  - [ ] [`django_strawberry_framework/types/relay.py`][relay] gains an internal `decode_global_id(gid: relay.GlobalID | str)` (accepts a [`relay.GlobalID`][glossary-relay-node-integration] or its base64 string, NOT a raw payload — [`docs/feedback.md`][feedback] P3) implementing the **resolve-then-enforce** dispatch of [Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type): Step 1 resolves a candidate — a model-label slot via `django.apps.apps.get_model(...)` → [`registry.get(model)`][registry] (primary / lone type), a GraphQL-type-name slot via `registry.definition_for_graphql_name(...)`; Step 2 enforces the candidate's effective `_resolve_globalid_strategy` permits the payload shape (`model` → model-label only; `type` → type-name only; `type+model` → both; `callable` → no decode, encode-only). An unresolvable label or a strategy-forbidden shape raises [`ConfigurationError`][glossary-configurationerror] (the [`RelatedFilter`][glossary-relation-handling]-style fail-loud message).
  - [ ] Encoder/decoder round-trip symmetry tests for the **three decodable strategies** (`model` / `type` / `type+model`; `callable` is encode-only — no decode symmetry); the transitional-mode test proving an old type-anchored ID still decodes while new emitted IDs use the model-label payload (the card DoD's explicit requirement); a [`Meta.name`][glossary-metaname]-renamed `type`-strategy round-trip (`ItemType` with `Meta.name = "Item"` emits `Item:<pk>` and decodes back through the `graphql_type_name` helper); and the **negative** Step-2 cases (a type-name ID rejected by a `model`-strategy type, a model-label ID rejected by a `type`-strategy type). The decode helper honors [`Meta.primary`][glossary-metaprimary] (a model-label ID for a multi-type model routes to the primary) — pinned with a multi-`DjangoType` fixture.
  - [ ] Package coverage: [`tests/types/test_relay_interfaces.py`][test-relay-interfaces] (the one-to-one mirror of [`types/relay.py`][relay] per [`docs/TREE.md`][tree], where the encode / decode lands) covers the `model` / `type` / `type+model` decode paths, the `graphql_type_name` (not `__name__`) lookup, the Step-2 strategy-shape enforcement (both rejection directions), the primary-routing rule, and the unresolvable-label `ConfigurationError`. [`registry.definition_for_graphql_name`][registry] coverage lands in [`tests/test_registry.py`][test-registry].
- [ ] Slice 4: live HTTP coverage on a Relay-Node-shaped fakeshop type (per the card DoD)
  - [ ] Update the existing live `GlobalID` assertions in [`examples/fakeshop/test_query/`][fakeshop-test-products] (and [`test_library_api.py`][fakeshop-test-library]) for the new model-label payload — the default-flip changes every **emitted** `GlobalID`, so the response-shape assertions that pin `id` (the `_global_id("ItemType"/"CategoryType"/"EntryType", …)` expectations in [`test_products_api.py`][fakeshop-test-products] and the `assert type_name == "GenreType"` round-trip in [`test_library_api.py`][fakeshop-test-library]) move to `products.item:<pk>` / `library.genre:<pk>`. A type-anchored `GlobalID` passed as **filter input** still narrows correctly (filtering reads only the `node_id` slot), so those filter tests pass unchanged but adopt the model-label form for representativeness; the own-PK `GlobalID` filtering examples in [`TODAY.md`][today] are updated to display `products.item:<pk>` etc.
  - [ ] Add live tests: (a) an emitted `node { id }` decodes to the model-label payload (base64 of `"app_label.modelname:<pk>"`); (b) a `filter: { id: { exact: "<model-label GlobalID>" } }` round-trips to the right row (filtering uses only the `node_id` slot, so a model-label payload narrows correctly); (c) the `type`-strategy opt-out (set `Meta.globalid_strategy = "type"` on one fakeshop type or `RELAY_GLOBALID_STRATEGY = "type"`) reproduces the GraphQL-type-name payload.
- [ ] Slice 5: doc updates + card-completion wrap (grants the per-card [`CHANGELOG.md`][changelog] edit permission)
  - [ ] [`docs/GLOSSARY.md`][glossary]: add a `## Meta.globalid_strategy` entry and a `## RELAY_GLOBALID_STRATEGY` (or a single "Django-model-based GlobalID encoding") entry as `shipped (0.0.9)`, add their Index rows, and add them to the "Relay" / "Type generation" [Browse by category][glossary] rows; extend the [Relay Node integration][glossary-relay-node-integration] body to describe the model-anchored default and the strategy override. **These glossary entries do not exist at spec-authoring time and creating them is out of scope for the [`docs/SPECS/NEXT.md`][next] flow** (see [Risks and open questions](#risks-and-open-questions)) — Slice 5 of the build creates them.
  - [ ] [`docs/README.md`][docs-readme]: note the model-anchored `GlobalID` default and the `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` opt-out in the shipped-surface list.
  - [ ] [`docs/TREE.md`][tree]: no new module (encode / decode live in the existing [`types/relay.py`][relay]); add the [`conf.py`][conf] `RELAY_GLOBALID_STRATEGY` settings note if the layout reference enumerates settings keys.
  - [ ] [`TODAY.md`][today]: update the products `GlobalID`-filtering examples to the model-label payload and add the breaking-wire-format-change note (parallel to the `PositiveBigIntegerField → BigInt` `0.0.6` precedent); keep the file products-centric.
  - [ ] [`README.md`][readme]: update the status paragraph's newest-shipped-surface line if it enumerates the GlobalID encoding.
  - [ ] [`CHANGELOG.md`][changelog]: a `### Changed` (breaking) bullet for the model-anchored `GlobalID` default plus an `### Added` bullet for `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY`, both under `[Unreleased]`. **This is the per-card CHANGELOG-edit permission grant** ([`AGENTS.md`][agents] withholds it by default); the Slice 5 maintainer prompt must name this edit explicitly. No version-heading promotion (per [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).
  - [ ] [`KANBAN.md`][kanban]: move [`WIP-ALPHA-031-0.0.9`][kanban] to the Done column with the next `DONE-NNN-0.0.9` id; add / confirm the card body's spec reference points at [`docs/spec-031-globalid_encoding-0_0_9.md`][spec-031] (this document).
  - [ ] **No version-file edits in this card.** Leave `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` to the joint `0.0.9` cut per [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut).

## Problem statement

`django-strawberry-framework`'s `0.0.5` [Relay Node integration][glossary-relay-node-integration] gave every `Meta.interfaces = (relay.Node,)` type an `id: GlobalID!` field. The `GlobalID` is Strawberry's standard `to_base64(type_name, node_id)` payload, and the `type_name` slot is the **GraphQL type name** — Strawberry's `relay.types.Node._id` field resolver computes it via `resolve_typename(root, info)`, whose default returns `info.path.typename`. So a `CategoryType` row's `GlobalID` decodes to `CategoryType:42`.

That is the standard Relay convention both upstreams ship (`graphene-django`'s `Node.to_global_id` base64-encodes `<GraphQL type name>:<id>`; `strawberry.relay.GlobalID` encodes `to_base64(type_name, node_id)`), and GlobalID parity proper was met at `DONE-015-0.0.5`. **But the GraphQL type name is the wrong durability anchor for a Django app.** In Django, the *model* is the durable thing — `products.Item` rarely moves — while the GraphQL type name (`ItemType`, `AdminItemType`, anything [`Meta.name`][glossary-metaname] sets) is a refactor-friendly facade a schema author renames freely. Baking the GraphQL type name into durable object identity means a type rename invalidates every cached `GlobalID` a client holds: a `useRefetchableFragment`, a persisted URL, a bookmarked node, an Apollo cache entry.

This card re-roots the default `GlobalID` payload onto the Django model label (`products.item:42`), so a schema author can rename `ItemType` → `ProductType` without breaking a single durable ID. It does this **before** the [Full Relay story][kanban] ([`WIP-ALPHA-032-0.0.9`][kanban]) mints root `node(id:)` / `nodes(ids:)` refetch fields into the public surface — because once those ship, the encoding format is a public durability contract, and changing it afterward becomes migration work instead of a config default. The card's own "Why it matters" is exactly this: "Getting this right before `1.0.0` lets consumers rename GraphQL types without invalidating every cached GlobalID. Waiting until after Full Relay ships turns the same decision into migration work."

The change is not all-or-nothing. Some consumers genuinely want type-scoped identity (disjoint auth or cache scopes per GraphQL type, or strict standard-Relay interop), so the card ships four strategies — `model` (new default), `type` (the opt-in legacy/standard convention), `type+model` (a transitional decode mode that accepts old type-anchored IDs while emitting model-anchored ones), and `callable` (fully custom) — selectable per type via `Meta.globalid_strategy` or schema-wide via the `RELAY_GLOBALID_STRATEGY` setting, with `Meta` override → setting → default precedence.

## Current state

A true description of the repo as of this writing (the plan is written against it), verified against the locked Strawberry `0.316.0`:

- The `GlobalID` payload is type-anchored. Strawberry's `relay.types.Node._id` (the `@field(name="id")` classmethod, source-verified) computes `type_name = resolve_typename(root, info)` and `node_id = resolve_id(root, info=info)`, then returns `GlobalID(type_name=type_name, node_id=str(node_id))`. The default `Node.resolve_typename` returns `info.path.typename` (the GraphQL type name); the `else` branch of `_id` (for a raw model instance, the package's integration case) reads `origin.resolve_typename` off the GraphQL type def resolved from `info.schema.get_type_by_name(parent_type.name)`. **Either branch reads `resolve_typename` off the `DjangoType` class**, which is why [Decision 3](#decision-3--the-encode-seam-a-strategy-parameterized-resolve_typename-default) injects there.
- [`django_strawberry_framework/types/relay.py`][relay] ships the `0.0.5` Relay foundation: the four injected `resolve_*` defaults (`resolve_id`, `resolve_id_attr`, `resolve_node`, `resolve_nodes`) in the `_RELAY_RESOLVER_DEFAULTS` table; `install_relay_node_resolvers(type_cls)` that installs each default UNLESS the consumer overrode it (the `existing.__func__ is relay.Node.<attr>.__func__` identity test); `_resolve_id_default` (returns `str(node_id)`, the `node_id` slot); `_check_composite_pk_for_relay_node`; the [`SyncMisuseError`][glossary-syncmisuseerror] marker; `_model_for` / `_initial_queryset`. There is **no** `resolve_typename` default and **no** `decode_global_id` helper yet.
- `resolve_typename` is **not** in `_RELAY_RESOLVER_DEFAULTS` — the package leaves Strawberry's default in place today, which is exactly why every emitted `GlobalID` is type-anchored.
- [`django_strawberry_framework/types/base.py`][base] holds `ALLOWED_META_KEYS` = `{"connection", "description", "exclude", "fields", "filterset_class", "interfaces", "model", "name", "nullable_overrides", "optimizer_hints", "orderset_class", "primary", "required_overrides"}` and `DEFERRED_META_KEYS` = `{"aggregate_class", "fields_class", "search_fields"}`. `"globalid_strategy"` is in neither; declaring it today raises [`ConfigurationError`][glossary-configurationerror] via the unknown-key typo guard. `_validate_connection(meta, connection, relay_shaped)` (and `_is_relay_shaped(cls, interfaces)`, computed once in `_validate_meta`) are the structural template for `_validate_globalid_strategy`.
- [`django_strawberry_framework/types/definition.py`][definition]'s [`DjangoTypeDefinition`][definition] carries `connection` / `filterset_class` / `orderset_class` slots and a `graphql_type_name` property (`self.name` if set else `self.origin.__name__` — the same derivation Strawberry uses for the `type` strategy's type-name slot). It has **no** `globalid_strategy` slot yet.
- [`django_strawberry_framework/conf.py`][conf] is a thin reader over `DJANGO_STRAWBERRY_FRAMEWORK`: `settings.<KEY>` raises `AttributeError` on a missing key; a non-mapping top-level value raises [`ConfigurationError`][glossary-configurationerror]. It does **no** per-key domain validation (the documented contract — "*Other* invalid shapes are no longer defensively coerced here" / the `getattr(..., None)` reflective reads), so an unknown `RELAY_GLOBALID_STRATEGY` value must be validated by the consumer ([Decision 7](#decision-7--the-relay_globalid_strategy-setting-and-the-settings-key-discipline)). No `RELAY_GLOBALID_STRATEGY` key exists yet.
- [`django_strawberry_framework/registry.py`][registry]'s `TypeRegistry` already supports the routing this card needs: `get(model)` returns the primary (`_primaries[model]`) or the lone registered type; `primary_for(model)` is the strict primary lookup; `types_for(model)` is the full tuple; `get_definition(type_cls)` returns the definition. Django's `django.apps.apps.get_model(app_label, model_name)` is the canonical label→model resolver for the decode side.
- `GlobalID` input (filtering) uses only the `node_id` slot. The Relay foundation's `_coerce_node_id(node_id)` returns `node_id.node_id` for a `relay.GlobalID`; the [`FilterSet`][glossary-djangotype] / order paths filter on the pk column. So **filtering by a `GlobalID` never validates the `type_name` slot against the schema** — the model-label payload is compatible with the shipped filter surface with no change.
- Strawberry's native **decode** (`GlobalID.resolve_type(info)` → `info.schema.get_type_by_name(self.type_name)`) **does** expect a GraphQL type name. It is reached only through a root `node(id:)` field, which is **not shipped until** [`WIP-ALPHA-032-0.0.9`][kanban]. So in `0.0.9` no shipped path hits native `resolve_type` with a model-label payload; the package's own `decode_global_id` is the forward-looking helper [`WIP-ALPHA-032-0.0.9`][kanban] dispatches through ([Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type) / [Risks and open questions](#risks-and-open-questions)).
- [`finalize_django_types`][glossary-finalize_django_types] Phase 2.5 already runs `apply_interfaces`, `_check_composite_pk_for_relay_node`, and `install_relay_node_resolvers` per Relay-Node-shaped type; the `resolve_typename` injection slots into the same loop.
- Live HTTP suites in [`examples/fakeshop/test_query/`][fakeshop-test-products] assert concrete `GlobalID` values (own-PK filtering, `node(id:)` refetch shape per [`TODAY.md`][today]). The default flip changes those expected payloads (Slice 4).

## Goals

1. Re-root the **default** `DjangoType` Relay `GlobalID` payload from the GraphQL type name onto the Django model label (`products.item:42`) via a strategy-parameterized `resolve_typename` default injected at finalization Phase 2.5, preserving any consumer-declared `resolve_typename` override through the existing `__func__` identity test (Slices 1–2, [Decision 3](#decision-3--the-encode-seam-a-strategy-parameterized-resolve_typename-default) / [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion) / [Decision 10](#decision-10--resolve_typename-injection-via-the-__func__-identity-test-at-phase-25)).
2. Ship the four strategies — `model` (default), `type` (opt-in legacy / standard Relay), `type+model` (transitional decode), callable (custom) — selectable per type via the net-new [`Meta.globalid_strategy`][glossary-djangotype] key (validated and stored on [`DjangoTypeDefinition`][definition]) and schema-wide via the `RELAY_GLOBALID_STRATEGY` setting, with `Meta` override → setting → package-default precedence (Slices 1–2, [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion) / [Decision 5](#decision-5--precedence-metaglobalid_strategy--relay_globalid_strategy--package-default-model) / [Decision 6](#decision-6--metaglobalid_strategy-is-a-net-new-allowed_meta_keys-key-stored-on-the-definition)).
3. Ship a `decode_global_id` **resolve-then-enforce** dispatch: resolve a candidate type (model-label via Django's app registry → the framework registry's **primary** [`DjangoType`][glossary-djangotype] honoring [`Meta.primary`][glossary-metaprimary]; GraphQL-type-name via a `graphql_type_name` lookup that honors [`Meta.name`][glossary-metaname], not `type_cls.__name__`), then enforce the candidate's effective strategy permits the payload shape (`model` / `type` / `type+model`; `callable` is encode-only). The transitional `type+model` mode accepts old type-anchored IDs alongside new model-anchored ones; unknown strategy / label values and strategy-forbidden shapes are rejected with [`ConfigurationError`][glossary-configurationerror] (Slice 3, [Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type)).
4. Keep the `node_id` slot, the FK-`id` round-trip, the [composite-pk rejection][glossary-relay-node-integration], the optimizer's pk-as-connector-column projection, and the `GlobalID`-filtering surface unchanged — the payload change is on the type-name slot only (Goal-wide, [Current state](#current-state) / [Edge cases and constraints](#edge-cases-and-constraints)).
5. Earn package coverage through a live fakeshop HTTP round-trip proving emitted IDs use the model-label payload and that `GlobalID` filtering round-trips, per [`docs/TREE.md`][tree]'s coverage-priority rule (Slice 4).
6. Keep package version state command-gated and owned by the joint `0.0.9` cut: no slice edits `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock` (Slice 5, [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).

## Non-goals

- **Root `node(id:)` / `nodes(ids:)` refetch fields and the `DjangoNodeField` / `DjangoNodesField` exports.** Those are the [Full Relay story][kanban] ([`WIP-ALPHA-032-0.0.9`][kanban]); this card ships the encode default and the `decode_global_id` helper they consume, not the root fields themselves ([Decision 2](#decision-2--card-scope-boundary-against-the-sibling-relay-cards)).
- **Public `testing/relay.py` `global_id_for(type_cls, id)` / `decode_global_id(gid)` test helpers.** Those public helpers are named in [`WIP-ALPHA-032-0.0.9`][kanban]'s Files-likely-touched list; this card ships the internal encode / decode and validates them through package tests, no public export ([Decision 11](#decision-11--module-location-encodedecode-in-typesrelaypy-no-public-export-in-009)).
- **First-class type-rename / model-rename GlobalID migration history** (decoding old-format IDs across a rename through a recorded alias map). That is `BACKLOG.md` item 39's "type-rename GlobalID migrations"; this card's `type+model` transitional mode is the lighter-weight bridge ([Edge cases and constraints](#edge-cases-and-constraints)).
- **Connection-aware optimizer planning** ([`WIP-ALPHA-033-0.0.9`][kanban]) and **the connection field** ([`DONE-030-0.0.9`][kanban], shipped) — orthogonal; the connection field picks up the model-label payload through the same per-node `resolve_typename` seam with no change.
- **`search:` argument, `Meta.fields_class`, `aggregates`** — later-version surfaces unrelated to identity encoding.
- **A version bump.** Owned by the joint `0.0.9` cut ([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it? → foundational" test, the `GlobalID` *primitive* is foundational and already shipped (`DONE-015-0.0.5`). What this card adds — a model-anchored payload default, the per-type / project-wide strategy override, and the transitional decode mode — is a **beyond-parity differentiator** neither upstream offers. The card's own upstream verification tags it `parity-adjacent, not required` for both upstreams: GlobalID parity proper was met at `0.0.5`, and the type-anchored convention stays available as the opt-in `type` strategy.

### Reference-package parity checkpoint

| Upstream | `django-strawberry-framework` | Status |
| --- | --- | --- |
| `graphene` `Node.to_global_id` → base64 `<GraphQL type name>:<id>` | `GlobalID` `type` strategy (opt-in) | parity met at `DONE-015-0.0.5` |
| `strawberry.relay.GlobalID` → `to_base64(type_name, node_id)` (type-name slot) | the `GlobalID` encode mechanism (reused wholesale) | parity met at `DONE-015-0.0.5` |
| (no model-anchored option upstream) | **`model` strategy default (`app_label.modelname:id`)** | **this card (`0.0.9`) — beyond parity** |
| (no per-type/project encoding override upstream) | **[`Meta.globalid_strategy`][glossary-djangotype] / `RELAY_GLOBALID_STRATEGY` / `type+model` / callable** | **this card (`0.0.9`) — beyond parity** |

### From Strawberry — borrow the encode/decode mechanism, re-root only the payload

Strawberry owns `GlobalID`, `to_base64` / `from_base64`, the `id: GlobalID!` field, and the `resolve_typename` seam. This card injects a `resolve_typename` default and supplies a `decode_global_id` dispatch — it does **not** hand-roll a base64 scheme or a parallel `GlobalID` type ([Decision 3](#decision-3--the-encode-seam-a-strategy-parameterized-resolve_typename-default)). The package's value is *what goes in the type-name slot* and *how a model label routes back to a type*, not the cursor/base64 plumbing. This mirrors the `0.0.5` foundation's posture of injecting `resolve_*` defaults rather than re-implementing the `Node` interface.

### From `graphene-django` / `strawberry-graphql-django` — borrow nothing new on the format

Both are type-anchored. The `type` strategy preserves that convention verbatim for consumers who want standard-Relay interop or type-scoped identity; nothing else is borrowed.

### Explicitly do not borrow

- **A hand-rolled GlobalID scheme.** `to_base64` / `from_base64` and the `GlobalID` type come from Strawberry.
- **Strawberry's native `GlobalID.resolve_type` for model-label decode.** It is hardcoded to a GraphQL-type-name schema lookup; the package supplies its own `decode_global_id` for the model-label shape ([Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type)).
- **Recorded rename-history migration.** `BACKLOG.md` item 39; this card stops at the `type+model` transitional bridge.

## User-facing API

### Declaring a per-type strategy

```python
import strawberry
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types

from . import models


class ItemType(DjangoType):
    class Meta:
        model = models.Item
        fields = ("id", "name", "category")
        interfaces = (relay.Node,)            # required — a strategy is only meaningful on a Node type
        # globalid_strategy omitted -> resolves to RELAY_GLOBALID_STRATEGY, then the "model" default


class LegacyItemType(DjangoType):
    class Meta:
        model = models.Item
        fields = ("id", "name")
        interfaces = (relay.Node,)
        primary = False                       # a secondary type ...
        globalid_strategy = "type"            # ... that keeps type-scoped identity for disjoint cache scopes


finalize_django_types()
```

`ItemType`'s `id` now decodes to `products.item:42` (the `model._meta.label_lower` payload); `LegacyItemType`'s `id` decodes to `LegacyItemType:42` (the GraphQL-type-name payload).

### Schema-wide default via the setting

```python
# settings.py
DJANGO_STRAWBERRY_FRAMEWORK = {
    "RELAY_GLOBALID_STRATEGY": "type+model",   # transitional: emit model-anchored, accept both on decode
}
```

The setting is the schema-wide fallback for any type that does not declare `Meta.globalid_strategy`. Precedence is `Meta.globalid_strategy` → `RELAY_GLOBALID_STRATEGY` → the `"model"` package default ([Decision 5](#decision-5--precedence-metaglobalid_strategy--relay_globalid_strategy--package-default-model)).

### The four strategies

| Strategy | Type-name slot (encode) | Decode accepts | Use case |
| --- | --- | --- | --- |
| `"model"` (default) | `app_label.modelname` (`products.item`) | model-label | durable, rename-proof Django-idiomatic identity |
| `"type"` | GraphQL type name ([`Meta.name`][glossary-metaname] or class name) | type-name | standard-Relay interop; type-scoped auth / cache scopes |
| `"type+model"` | `app_label.modelname` | **both** model-label and type-name | migrating a deployed schema off type-anchored IDs |
| callable | `callable(type_cls, model, root, info) -> str` (sync; mirrors the `resolve_typename` seam, never sees `node_id`) | n/a — **encode-only in `0.0.9`** (consumer-owned decode) | fully custom encodings |

The **`node_id` slot is unchanged across every strategy** — it is `resolve_id`'s `str(pk)` (or a custom [`resolve_id_attr`][glossary-relay-node-integration] slug), so a strategy switch never affects `GlobalID` filtering or the relation `id` round-trip. The callable strategy is **encode-only** in `0.0.9` (its `decode` is consumer-owned — [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion) / [Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type)); the other three round-trip.

### Decode dispatch (consumed by `node(id:)` in `0.0.9`'s sibling card)

```python
# internal, in types/relay.py; the public testing/relay helper lands with WIP-ALPHA-032-0.0.9.
# `gid` is a relay.GlobalID instance (or its base64 string) — NOT a raw "app_label.model:pk" payload.
target_type, node_id = decode_global_id(gid)
#  GlobalID("products.item", "42") -> apps.get_model("products","item") -> registry.get(Item) -> ItemType, "42"
#  GlobalID("Item", "42")          -> registry.definition_for_graphql_name("Item")  (honors Meta.name) -> ItemType, "42"
#  Step 2 then checks the resolved type's strategy permits the payload shape;
#  a callable-strategy type has no decode path (encode-only in 0.0.9).
```

### Error shapes

- `Meta.globalid_strategy = "modle"` (typo) or any non-`{"model","type","type+model"}` string that is not callable → [`ConfigurationError`][glossary-configurationerror] at type creation.
- `Meta.globalid_strategy` on a non-Relay-Node type (no `relay.Node` in `Meta.interfaces` and no direct inheritance) → [`ConfigurationError`][glossary-configurationerror] at type creation.
- `RELAY_GLOBALID_STRATEGY = "bogus"` → [`ConfigurationError`][glossary-configurationerror] naming the setting, raised when the strategy is resolved (finalization), since [`conf.py`][conf] does no domain validation.
- A `decode_global_id` payload that resolves to no installed app / model, to a model or GraphQL name with no registered [`DjangoType`][glossary-djangotype], or to an ambiguous `graphql_type_name` → [`ConfigurationError`][glossary-configurationerror] naming the resolution attempt.
- A `decode_global_id` payload whose shape the **resolved candidate's** strategy does not permit (a type-name payload for a `model`-strategy type, a model-label payload for a `type`-strategy type, or any payload for a `callable`-strategy type, which is encode-only) → [`ConfigurationError`][glossary-configurationerror] (the Step-2 enforcement of [Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type)).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-031-globalid_encoding-0_0_9.md`** (this document).

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `WIP-ALPHA-031-0.0.9`, so `<NNN>` is `031` and `<0_0_X>` is `0_0_9`.
- The topic slug is `globalid_encoding` — it names the card's subject (the GlobalID encoding strategy system) in snake_case.
- The card DoD permits "A new **or amended** Relay spec." This flow authors a **new** spec per the one-spec-per-WIP-card [`docs/SPECS/NEXT.md`][next] rule rather than amending [`spec-015`][spec-015]; amending a shipped predecessor would bury a `0.0.9` build plan inside a `0.0.5` record.

Alternatives considered (and rejected):

- **Amend `spec-015-relay_interfaces-0_0_5.md`.** Rejected: `spec-015` is a shipped record; the flow's structured-filename convention bakes the card's NNN into a fresh file.
- **Topic slug `relay_globalid` or `model_globalid`.** Rejected: `relay_globalid` over-claims the Relay-Root surface this card scopes out ([Decision 2](#decision-2--card-scope-boundary-against-the-sibling-relay-cards)); `model_globalid` under-describes the strategy system (the card ships `type` and callable too). `globalid_encoding` names the whole encoding decision.

### Decision 2 — Card-scope boundary against the sibling Relay cards

`0.0.9` carries three WIP Relay cards plus two shipped ones. This card ships **only the GlobalID encoding/decoding strategy system**; the boundary is explicit:

- **`WIP-ALPHA-031-0.0.9` (this card)** — the model-anchored default, `Meta.globalid_strategy`, `RELAY_GLOBALID_STRATEGY`, the four strategies, and the `decode_global_id` dispatch.
- **`WIP-ALPHA-032-0.0.9`** — Full Relay story: root `node(id:)` / `nodes(ids:)`, the relation-as-Connection upgrade, `DjangoNodeField` / `DjangoNodesField`, the public `testing/relay` helpers, schema-validation diagnostics, fakeshop activation. **The first consumer of this card's `decode_global_id`.** This card must land before it (the card's "Card references": *"This card should land before Full Relay because root `node(id:)`, `nodes(ids:)`, and refetch helpers make GlobalID encoding a public durability contract"*).
- **`WIP-ALPHA-033-0.0.9`** — connection-aware optimizer planning. Orthogonal to the GlobalID payload.
- **`DONE-030-0.0.9`** — `DjangoConnectionField` (shipped). Connection pagination does not change the `GlobalID` payload (the card's "Card references": *"`DjangoConnectionField` can land before this card because connection pagination does not require changing the Relay GlobalID payload"*); the connection's `edges { node { id } }` pick up the model-label payload through the same per-node `resolve_typename` seam.

Justification: the card body names the ordering dependency (031 before 032) and the orthogonality (031 independent of 030); pinning the boundary keeps the spec scoped to what `031` ships and prevents pulling `032`'s eight-goal umbrella into one card.

Alternatives considered (and rejected): **Fold the encoding decision into the Full Relay story (`032`).** Rejected: the card was promoted out of `BACKLOG.md` item 40 specifically to settle the format *before* `032` makes it a public contract; merging them re-creates the migration-work risk the card exists to avoid.

### Decision 3 — The encode seam: a strategy-parameterized `resolve_typename` default

Strawberry's `relay.types.Node._id` field resolver computes the `GlobalID`'s `type_name` slot via `resolve_typename(root, info)` (source-verified against the locked `0.316.0`). The default `Node.resolve_typename` returns `info.path.typename` (the GraphQL type name). **The encode seam is therefore `resolve_typename`** — inject a package default that returns the model label (or the strategy-appropriate value) and every emitted `GlobalID` re-roots, with zero change to Strawberry's `GlobalID` construction, `to_base64`, or the `node_id` slot.

The injection rides the existing Phase-2.5 mechanism: `install_relay_node_resolvers` already installs the four `resolve_*` defaults UNLESS the consumer overrode them (the `existing.__func__ is relay.Node.<attr>.__func__` identity test). The `resolve_typename` injection uses the same identity test against `relay.Node.resolve_typename.__func__`, so a consumer who declares their own `resolve_typename` keeps it ([Decision 10](#decision-10--resolve_typename-injection-via-the-__func__-identity-test-at-phase-25)).

Both branches of Strawberry's `_id` read `resolve_typename` off the `DjangoType` class — the `isinstance(root, Node)` branch via `root.__class__.resolve_typename`, the integration branch (raw model instance) via `origin.resolve_typename` resolved from the schema's type def. Installing the classmethod on the `DjangoType` class covers both.

Justification:

- [`START.md`][start]'s "Strawberry is the engine" rule: re-rooting via the documented `resolve_typename` seam reuses Strawberry's correct `GlobalID` plumbing; hand-rolling a base64 scheme would duplicate engine behavior and drift from the Relay spec.
- The seam is the exact analogue of the `0.0.5` `resolve_*` injection, so the consumer-override-preservation contract (`__func__` identity test) and the Phase-2.5 timing are reused, not reinvented.

Alternatives considered (and rejected):

- **Override the `id` field wholesale on the `DjangoType`.** Rejected: duplicates Strawberry's `GlobalID(type_name=..., node_id=str(...))` construction and the awaitable branch; the collision guard at `__init_subclass__` already rejects `id` overrides on Relay types, so this would fight the shipped contract.
- **Monkeypatch `strawberry.relay.GlobalID` / `Node.resolve_typename` globally.** Rejected: process-global, breaks the `type` strategy and any other Strawberry library in the process; the per-type injection is surgical.
- **Encode the strategy into `resolve_id` (the `node_id` slot).** Rejected: the `node_id` slot is the pk and must stay clean for `GlobalID` filtering and the relation `id` round-trip; the type-name slot is the correct home.

### Decision 4 — Four strategies (`model`, `type`, `type+model`, callable) and an unchanged `node_id` portion

The card pre-pins the four strategies; this Decision pins their exact encode/decode semantics:

- **`model` (new default)** — type-name slot = `definition.model._meta.label_lower` (`"app_label.modelname"`, lowercased — Django's canonical model label, e.g. `products.item`). Decode resolves the label via `django.apps.apps.get_model(...)`.
- **`type` (opt-in legacy / standard Relay)** — type-name slot = the GraphQL type name ([`definition.graphql_type_name`][definition] = `Meta.name` or the class name), identical to Strawberry's `info.path.typename` default. The package leaves Strawberry's default `resolve_typename` in place for this strategy (installs nothing), so the payload is byte-identical to the pre-`0.0.9` output. This is the documented opt-out for type-scoped auth / cache scopes and standard-Relay interop.
- **`type+model` (transitional)** — **emits** the model-label payload (so new IDs are already rename-proof) but **decodes both** model-label and type-name payloads (so old type-anchored IDs minted before the migration still resolve). The bridge for a deployed schema turning on the `model` default without orphaning cached client IDs.
- **callable (encode-only in `0.0.9`)** — `Meta.globalid_strategy = my_encoder` where `my_encoder(type_cls, model, root, info) -> str` returns the type-name slot for fully custom encodings. **The signature mirrors the `resolve_typename(root, info)` seam, NOT `resolve_id`** — it receives the model instance `root` and `info`, the only inputs Strawberry's `Node._id` has *before* it calls `resolve_id`, and it must synchronously return `str`. It deliberately does **not** receive `node_id`: the seam computes the type-name slot before the node-id slot, so a node-id-dependent type-name would force a premature (and, for async / custom `resolve_id`, doubled) `resolve_id` call — incompatible with the `resolve_typename` seam without a fuller custom-`id`-resolver design that is out of scope here ([`docs/feedback.md`][feedback] P1). Custom encodings whose type-name slot genuinely depends on the node id are therefore not expressible via this strategy in `0.0.9`. `callable` is **encode-only**: decode of a callable-encoded ID is the consumer's responsibility (or lands with the root-Node decode in [`WIP-ALPHA-032-0.0.9`][kanban]), so the `decode_global_id` dispatch has no callable branch ([Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type), [`docs/feedback.md`][feedback] P2).

Across every strategy the `node_id` slot is `resolve_id`'s `str(pk)` (or a custom `resolve_id_attr` value). Only the type-name slot varies, and it is computed synchronously by `resolve_typename` for every strategy.

Justification:

- The four strategies are the card's stated scope. `model` as default is the card's headline; `type` is the parity-preserving opt-out; `type+model` is the explicit transitional mode the card names; callable is the escape hatch for custom schemes.
- Decoupling the type-name slot from the `node_id` slot keeps `GlobalID` filtering, FK-`id` elision, and the relation `id` round-trip untouched ([Current state](#current-state)).

Alternatives considered (and rejected):

- **Ship only `model` (no `type` opt-out).** Rejected: the card explicitly keeps the legacy mode available; some consumers need type-scoped identity (disjoint auth/cache scopes), which the card calls out as a "legitimate legacy mode."
- **Make `type` the default and `model` opt-in.** Rejected: the card explicitly makes `model` the new default; deferring the breaking change to opt-in re-creates the post-`1.0.0` migration-work problem the card exists to prevent ([Decision 9](#decision-9--changing-the-default-to-model-is-a-breaking-wire-format-change-acceptable-pre-100)).
- **`type+model` emits type-name during the window.** Rejected: emitting model-anchored from day one is what makes new IDs durable; accepting both on decode is the migration bridge, so the emit direction should already be the target format.

### Decision 5 — Precedence: `Meta.globalid_strategy` → `RELAY_GLOBALID_STRATEGY` → package default (`model`)

A `_resolve_globalid_strategy(definition)` helper resolves the effective strategy once per type, **at finalization** (when `resolve_typename` is injected), in this order: the per-type `definition.globalid_strategy` (`Meta` override) if set; else the schema-wide [`conf.settings`][conf]`.RELAY_GLOBALID_STRATEGY` if configured; else the `"model"` package default. The resolved strategy is frozen at schema-build time — the encoding is a stable schema contract, not request-scoped state.

Justification:

- `Meta`-over-setting-over-default is the package's standard precedence shape (the card pins it verbatim) and matches how a per-type opt-out should beat a project-wide knob.
- Resolving at finalization (not per request) means the injected `resolve_typename` is a fixed closure — no per-call strategy lookup on the `id`-resolution hot path, and a single source of truth for the type's identity format.

Alternatives considered (and rejected):

- **Resolve per request.** Rejected: the `GlobalID` format is a durable client contract; varying it per request would mint inconsistent IDs and defeat caching.
- **Setting-only (no per-type override).** Rejected: the card wants per-type `Meta.globalid_strategy` so a consumer can keep one type type-scoped while the rest go model-anchored (disjoint auth/cache scopes).

### Decision 6 — `Meta.globalid_strategy` is a net-new `ALLOWED_META_KEYS` key, stored on the definition

`Meta.globalid_strategy` lands **directly** in [`ALLOWED_META_KEYS`][base] (NOT a [`DEFERRED_META_KEYS`][base] promotion), the same net-new-key rule [`spec-030`][spec-030] [Decision 8][spec-030] and [`spec-029`][spec-029] [Decision 6][spec-029] set — its feature ships in the same card that adds the key, so it was never reserved-but-nonfunctional. A `_validate_globalid_strategy(meta, value, relay_shaped)` helper (called from [`_validate_meta`][base], modeled on `_validate_connection`):

- `None` (absent) → returns `None` (resolves to the setting/default later);
- a string not in `{"model", "type", "type+model"}` and not callable → [`ConfigurationError`][glossary-configurationerror] naming the offending value and listing the valid strategies (typo guard);
- a callable → accepted (the callable strategy);
- the key on a non-Relay-Node type — i.e. when the precomputed `relay_shaped` bool (`_is_relay_shaped(cls, interfaces)`, threaded in from `_validate_meta`, the same predicate `_validate_connection` uses) is False → [`ConfigurationError`][glossary-configurationerror] ("`Meta.globalid_strategy` requires a Relay-Node-shaped type; add `relay.Node` to `Meta.interfaces` or remove the key").

The normalized value is **stored on [`DjangoTypeDefinition`][definition]** (a new `globalid_strategy` slot, populated in [`__init_subclass__`][base] like the `connection` / `filterset_class` / `orderset_class` slots), so the Phase-2.5 `resolve_typename` injection reads the per-type opt-in from the canonical definition record, not by re-parsing `Meta` (which is normalized away after validation).

Justification:

- Net-new key whose feature ships in the same card — the [`spec-030`][spec-030] / [`spec-029`][spec-029] situation, so straight into `ALLOWED_META_KEYS`.
- Storing on the definition is required because the `resolve_typename` injection happens at finalization, away from the `Meta` shape; the definition is the canonical per-type record the finalizer already reads ([`connection`][definition] set the exact precedent).
- Gating to Relay-Node types via the shared `_is_relay_shaped` predicate keeps the eligibility rule single-sited with `Meta.connection`.

Alternatives considered (and rejected):

- **A `DEFERRED_META_KEYS` promotion.** Rejected: the key was never reserved; it ships functional in this card.
- **Validate but do not store (re-parse `Meta` at finalize).** Rejected: fragile and divergent from how `connection` / `filterset_class` / `orderset_class` are threaded; the definition is the one record the finalizer consults.
- **A boolean `Meta.model_globalid = True`.** Rejected: cannot express `type+model` or callable; the four-way strategy is the card's scope.

### Decision 7 — The `RELAY_GLOBALID_STRATEGY` setting and the settings-key discipline

The `RELAY_GLOBALID_STRATEGY` key is added to the `DJANGO_STRAWBERRY_FRAMEWORK` settings surface **now**, because this card is the feature that needs it ([`START.md`][start]'s rule, born from the documented past mistake of pre-populating `conf.py` with future-feature settings #"Don't preemptively populate `conf.py` with future-feature settings"). [`conf.py`][conf] stays a thin reader — it does **not** validate the value; `_resolve_globalid_strategy` validates it at strategy-resolution time and raises [`ConfigurationError`][glossary-configurationerror] naming the setting on an unknown string. A callable setting value is accepted (project-wide custom encoder).

Justification:

- The settings-key-only-when-needed rule is a hard project convention ([`START.md`][start]); this card is exactly the landing card for the key.
- [`conf.py`][conf]'s documented contract is "thin reader, no domain coercion" ([Current state](#current-state)); putting the strategy validation in the consumer keeps that contract and matches where `Meta.globalid_strategy`'s validation lives.

Alternatives considered (and rejected):

- **Validate the setting eagerly inside `conf.py`.** Rejected: [`conf.py`][conf] is intentionally domain-agnostic; coupling it to the strategy vocabulary would re-introduce the defensive-coercion shape the module's docstring warns against.
- **No setting (per-type `Meta` only).** Rejected: the card explicitly wants a schema-wide default knob so a project can flip every type at once without touching each `Meta`.

### Decision 8 — Decode routes through Django's app registry then the framework registry to the primary type

`decode_global_id(gid: relay.GlobalID | str)` accepts a Strawberry [`relay.GlobalID`][glossary-relay-node-integration] instance or its base64 string form (which it `from_base64`-decodes); it never accepts a raw, un-encoded `"app_label.modelname:pk"` payload ([`docs/feedback.md`][feedback] P3). It splits the decoded `(type_name, node_id)` and runs a **two-step resolve-then-enforce** dispatch.

**Step 1 — resolve a candidate type from the type-name slot's shape:**

- A **model-label** slot (contains a dot, `"app_label.modelname"`) → `django.apps.apps.get_model(app_label, model_name)` → [`registry.get(model)`][registry] (which returns the primary, or the lone registered type) → candidate `target_type`.
- A **GraphQL-type-name** slot (no dot) → a `graphql_type_name` registry lookup, **NOT** a `type_cls.__name__` lookup: the `type` strategy emits [`definition.graphql_type_name`][definition], which honors [`Meta.name`][glossary-metaname], so a class `ItemType` with `Meta.name = "Item"` emits `Item:<pk>` and can only decode by inverting the same function ([`docs/feedback.md`][feedback] P1). The lookup is a new `registry.definition_for_graphql_name(name)` helper that scans [`registry.iter_definitions()`][registry] for a unique `graphql_type_name` match → candidate `target_type`.

**Step 2 — enforce the candidate's effective strategy permits the payload shape** ([`docs/feedback.md`][feedback] P1). Resolve `_resolve_globalid_strategy(candidate_definition)` ([Decision 5](#decision-5--precedence-metaglobalid_strategy--relay_globalid_strategy--package-default-model)) and reject a shape the strategy does not emit:

- `model` → a model-label payload only; a type-name payload for a `model`-strategy type raises [`ConfigurationError`][glossary-configurationerror].
- `type` → a type-name payload only; a model-label payload for a `type`-strategy type raises.
- `type+model` → **both** shapes (the transitional bridge — old type-anchored IDs and new model-anchored IDs both resolve).
- `callable` → **no decode path in `0.0.9`** (encode-only, [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion)); a payload whose candidate resolves to a callable-strategy type raises [`ConfigurationError`][glossary-configurationerror] directing the consumer to own the decode (or await the root-Node decode in [`WIP-ALPHA-032-0.0.9`][kanban]).

On success returns `(target_type, node_id)`. An unresolvable label (no installed app/model, a model or GraphQL name with no registered [`DjangoType`][glossary-djangotype], or an ambiguous name), or a shape the candidate's strategy forbids, raises [`ConfigurationError`][glossary-configurationerror] naming the resolution attempt — the same fail-loud shape [`RelatedFilter`][glossary-relation-handling] uses for unqualified names. The Step-2 enforcement is what makes `type+model` distinguishable from a permissive "accept anything resolvable" decoder, stops a `model`-strategy type from silently accepting stale type-anchored IDs, and preserves the type-scoped-identity guarantee of the `type` strategy.

Multiple [`DjangoType`][glossary-djangotype]s for one model resolve through the **primary** ([`registry.get`][registry] honors [`Meta.primary`][glossary-metaprimary] as its first return state); a consumer who needs disjoint per-type identity uses the `type` strategy so the ID carries the GraphQL type name and routes type-scoped. The resolved type's `resolve_node` (the `0.0.5` default) then honors [`get_queryset`][glossary-get_queryset-visibility-hook], returning `null` for a hidden row.

In `0.0.9` the decode helper is the **forward-looking** piece: root `node(id:)` / `nodes(ids:)` (the only callers) ship with [`WIP-ALPHA-032-0.0.9`][kanban], and `GlobalID` filtering uses only the `node_id` slot ([Current state](#current-state)), so no shipped `0.0.9` path requires native-Strawberry decode of a model-label payload. The helper is validated directly by Slice 3 tests and consumed by `032`.

Justification:

- Django's `apps.get_model` is the canonical `app_label.model → model` resolver and the durable anchor the whole card is built on; routing through it (then `registry.get`) reuses the registry's existing primary-resolution contract rather than inventing a parallel label index.
- Primary-routing matches how relation targets already resolve ([`DjangoTypeDefinition.related_target_for`][definition] uses `registry.get`), so a decoded ID and a traversed relation land on the same type.
- Keying type-name decode on `graphql_type_name` (not `type_cls.__name__`) is the only spelling that round-trips a `type`-strategy ID: the encode side emits `graphql_type_name`, so the decode side must invert the same function or a [`Meta.name`][glossary-metaname] rename silently breaks refetch.
- Resolving the candidate's strategy and enforcing the payload shape (Step 2) is what gives each strategy its documented contract — without it the decoder is permissive-by-default and `model` / `type` / `type+model` collapse into one indistinguishable behavior.

Alternatives considered (and rejected):

- **Decode to a secondary type.** Rejected: ambiguous which secondary; the primary is the canonical relation-resolution target, and `type`-scoped IDs are the explicit path for disjoint scopes.
- **A package-owned `{label: type}` index instead of Django's app registry.** Rejected: duplicates Django's model registry, misses proxy/MTI label resolution Django already handles, and drifts on app renames.
- **Reuse Strawberry's native `GlobalID.resolve_type`.** Rejected: it is hardcoded to `info.schema.get_type_by_name(type_name)` (a GraphQL type name), so it cannot resolve a model label; the package must own the model-label dispatch.
- **A permissive decoder that accepts any resolvable shape (no Step-2 strategy enforcement).** Rejected ([`docs/feedback.md`][feedback] P1): it makes `type+model` indistinguishable from the default, lets a `model`-strategy type keep accepting stale type-anchored IDs, and dissolves the `type` strategy's type-scoped guarantee.
- **Type-name decode via `type_cls.__name__`.** Rejected ([`docs/feedback.md`][feedback] P1): the `type` strategy emits `graphql_type_name`, so a `Meta.name`-renamed type would emit its `Meta.name` value yet be undecodable by class name; decode must invert the encode function.

### Decision 9 — Changing the default to `model` is a breaking wire-format change, acceptable pre-`1.0.0`

`GlobalID` shipped type-anchored at `DONE-015-0.0.5`. Flipping the default to `model` changes **every** emitted `GlobalID` for a Relay-Node type that does not opt out — a breaking wire-format change. It is acceptable now because:

- The package is alpha (`README.md`: "alpha-quality … not production"; the public *names* are stable, "correctness and edge-case behavior are still hardening"), `GlobalID` is recent (`0.0.5`), and `1.0.0` is the API-freeze boundary ([Cross-subsystem invariants][glossary-cross-subsystem-invariants]).
- The card's entire rationale is to settle the durable format *before* `1.0.0` so a rename does not invalidate cached IDs; deferring the flip past `1.0.0` turns it into migration work.
- There is a clean opt-out: the `type` strategy reproduces the exact pre-`0.0.9` payload per type or project-wide, and `type+model` bridges a deployed schema.

The flip is documented as a breaking change in `CHANGELOG.md` (`### Changed`), [`TODAY.md`][today], and [`docs/GLOSSARY.md`][glossary] — parallel to the `PositiveBigIntegerField → BigInt` `0.0.6` breaking-wire-format precedent ([`BigInt` scalar][glossary-bigint-scalar]).

Justification: settling identity format pre-`1.0.0` is the card's reason to exist; the alpha window plus the `type` opt-out make the breaking flip the right call now rather than after the freeze.

Alternatives considered (and rejected):

- **Default to `type`, ship `model` as opt-in.** Rejected: the card explicitly makes `model` the new default; opt-in `model` leaves every existing consumer type-anchored into `1.0.0`, re-creating the migration-work problem.
- **Ship `type+model` as the default.** Rejected: `type+model` is the migration bridge, not a steady state — its dual-accept decode is a transitional cost, not something to bake in as the default; `model` is the destination.

### Decision 10 — `resolve_typename` injection via the `__func__` identity test, at Phase 2.5

An `install_globalid_typename_resolver(type_cls, definition)` step runs in [`finalize_django_types`][glossary-finalize_django_types] Phase 2.5, alongside `install_relay_node_resolvers`, for every Relay-Node-shaped type. It resolves the effective strategy via `_resolve_globalid_strategy(definition)` and:

- installs a package `resolve_typename` classmethod closure (for `model` / `type+model` / callable) **only if** the consumer has not overridden `resolve_typename` — the `existing.__func__ is relay.Node.resolve_typename.__func__` identity test, the same discriminator the four `resolve_*` defaults use;
- for the `type` strategy, installs nothing (leaves Strawberry's default `resolve_typename`, which returns `info.path.typename`), so the payload is byte-identical to pre-`0.0.9`.

`resolve_typename` is **not** added to the static `_RELAY_RESOLVER_DEFAULTS` table, because that table maps a name to a single static default; the typename default is strategy-parameterized per type, so it needs its own injection site that reads the resolved strategy.

Justification:

- Phase 2.5 is where Relay resolver injection already happens, and the `__func__` identity test is the shipped, tested mechanism for preserving consumer overrides; reusing both keeps one source of truth for Relay-method injection.
- Keeping `resolve_typename` out of `_RELAY_RESOLVER_DEFAULTS` respects that table's invariant (name → one static default) while still installing through the same `__func__`-gated discipline.

Alternatives considered (and rejected):

- **Add `resolve_typename` to `_RELAY_RESOLVER_DEFAULTS`.** Rejected: that table's entries are static `(name, default_impl)` pairs; the typename default varies by resolved strategy, so it cannot be a single static impl.
- **Inject at class-creation time (`__init_subclass__`) instead of Phase 2.5.** Rejected: the effective strategy depends on the `RELAY_GLOBALID_STRATEGY` setting and the registry being stable; finalization is the package's "registry is stable now" point, matching where the other Relay defaults install.

### Decision 11 — Module location: encode/decode in `types/relay.py`, no public export in `0.0.9`

The encode helper, the strategy resolver, and `decode_global_id` land in the existing [`django_strawberry_framework/types/relay.py`][relay] (the Relay foundation module the four `resolve_*` defaults already live in), with coverage in [`tests/types/test_relay_interfaces.py`][test-relay-interfaces] (the one-to-one mirror of [`types/relay.py`][relay] per [`docs/TREE.md`][tree] — a `tests/types/test_globalid.py` would require a `types/globalid.py` source module this card does not create). The `RELAY_GLOBALID_STRATEGY` read is a one-line `conf.settings` access; the `Meta.globalid_strategy` validation lives in [`types/base.py`][base] beside `_validate_connection`.

**No new public export in `0.0.9`.** `Meta.globalid_strategy` is a `Meta` key (not a re-exported symbol) and `RELAY_GLOBALID_STRATEGY` is a setting; the `decode_global_id` / encode helpers are internal. The public `testing/relay` helpers (`global_id_for(type_cls, id)`, `decode_global_id(gid)`) are named in [`WIP-ALPHA-032-0.0.9`][kanban]'s Files-likely-touched list and ship there, with the root-Node fields that justify a public test surface.

Justification: a flat addition to the shipped Relay foundation module matches where the `0.0.5` resolver defaults live; [`WIP-ALPHA-032-0.0.9`][kanban] already plans a new `relay.py` for Root-Node work and the public test helpers, so promoting them here would front-run that card's surface.

Alternatives considered (and rejected):

- **A new top-level `relay.py` now.** Rejected: premature for an encode/decode pair that belongs with the existing Relay foundation; `032` introduces `relay.py` for the Root-Node surface.
- **Export `decode_global_id` publicly in `0.0.9`.** Rejected: no shipped `0.0.9` consumer (root `node(id:)` is `032`); the tested-usage promotion discipline (a symbol reaches `__init__.py` only after a live consumer proves the shape) defers the export to `032`.

### Decision 12 — Version bumps are owned by the joint `0.0.9` cut

No slice edits `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock`; no [`CHANGELOG.md`][changelog] release heading is promoted. CHANGELOG bullets land under `[Unreleased]`. The `0.0.8` → `0.0.9` bump is owned by the **joint cut** releasing the WIP cards together with the shipped [`DONE-029-0.0.9`][kanban] / [`DONE-030-0.0.9`][kanban].

Justification: the exact precedent [`spec-030`][spec-030] [Decision 13][spec-030] and [`spec-029`][spec-029] [Decision 11][spec-029] set; [`docs/SPECS/NEXT.md`][next] Step 6 mandates this Decision when multiple WIP cards share the target patch version ("The Slice 5 / Definition of done checklist must NOT bump the version"). The on-disk version is still `0.0.8`; several `0.0.9`-tagged surfaces already ship under `[Unreleased]` against the unchanged version.

Alternatives considered (and rejected): **Bump the version in Slice 5.** Rejected: would race the sibling cards for the same bump and promote a release heading before the cohort is cut.

## Implementation plan

The card ships as **four sequential functional slices plus a doc + card-completion wrap**. Each functional slice is one PR; later slices build on earlier ones. Line deltas are estimates.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — `Meta.globalid_strategy` validate+store + setting read + precedence resolver | [`django_strawberry_framework/types/base.py`][base] (`ALLOWED_META_KEYS` += `"globalid_strategy"` + `_validate_globalid_strategy` + `__init_subclass__` store), [`django_strawberry_framework/types/definition.py`][definition] (`globalid_strategy` slot), [`django_strawberry_framework/types/relay.py`][relay] (`_resolve_globalid_strategy` reading [`conf.settings`][conf]), [`tests/types/test_base.py`][test-types-base] (extend) | ~8 (`ALLOWED_META_KEYS` membership; `_validate_globalid_strategy` unknown-string / non-Relay / wrong-type; `definition.globalid_strategy` storage; three-tier precedence; unknown-setting `ConfigurationError`) | `+150 / -2` |
| 2 — encode seam: `resolve_typename` injection + four encoders + default flip | [`django_strawberry_framework/types/relay.py`][relay] (encode helper + `install_globalid_typename_resolver`), [`django_strawberry_framework/types/finalizer.py`][finalizer] (Phase 2.5 call), [`tests/types/test_relay_interfaces.py`][test-relay-interfaces] (extend) | ~10 (each strategy's type-name slot; override preservation; default flip → `model`; `type` reproduces pre-`0.0.9` payload) | `+170 / -6` |
| 3 — decode seam: `decode_global_id` resolve-then-enforce + `graphql_type_name` lookup + transitional `type+model` | [`django_strawberry_framework/types/relay.py`][relay] (`decode_global_id`), [`registry.py`][registry] (`definition_for_graphql_name`), [`tests/types/test_relay_interfaces.py`][test-relay-interfaces] (the `types/relay.py` mirror), [`tests/test_registry.py`][test-registry] (the helper) | ~12 (three-strategy round-trip symmetry; `Meta.name` round-trip; transitional accept-old-ID; both Step-2 rejection directions; callable-no-decode; primary-routing; unresolvable-label `ConfigurationError`) | `+185 / -0` |
| 4 — live HTTP coverage + existing-assertion updates | [`examples/fakeshop/test_query/test_products_api.py`][fakeshop-test-products], [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] (update existing `GlobalID` assertions + add model-label / filter-roundtrip / `type`-opt-out tests); [`examples/fakeshop/apps/*/schema.py`][fakeshop-products-schema] only if a `type`-strategy fixture is needed | ~5 (emitted model-label id; filter round-trip; `type`-strategy opt-out) | `+120 / -40` |
| 5 — doc updates + card-completion wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`TODAY.md`][today], [`README.md`][readme], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban] | 0 (doc-only) | `+110 / -30` |

Total expected delta: ~750 lines across four functional slices plus the wrap. No version-file edits (per [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).

## Edge cases and constraints

- **Proxy models** — the model-label payload uses the [`DjangoType`][glossary-djangotype]'s *declared* [`Meta.model`][glossary-metamodel] `label_lower`, so a proxy-backed type encodes the proxy's label and a concrete-backed type encodes the concrete label; both decode through `apps.get_model`, which resolves proxy labels. The `node_id` slot keys on `root.__class__._meta.pk.attname` (the existing `_resolve_id_default` proxy-safe behavior), unchanged.
- **Multi-table inheritance (MTI)** — a child model has its own label and its own pk; `apps.get_model(app, child)` resolves it and the child pk fills the `node_id` slot. A `DjangoType` over the parent encodes the parent label. No special handling beyond using the declared model's label.
- **Slug / custom `resolve_id_attr`** — the `node_id` slot is `resolve_id`'s value (a slug, a UUID, whatever `resolve_id_attr` selects), independent of the type-name strategy; a slug-keyed type gets `app_label.modelname:<slug>` under `model`. The two slots are orthogonal.
- **Composite primary key** — already rejected at finalization for Relay-Node types ([composite-pk rejection][glossary-relay-node-integration]); a model-label `GlobalID` still needs a single-column `node_id`, so this card inherits the existing `ConfigurationError` unchanged.
- **Model / app rename** — Django's `apps.get_model` does **not** follow historical renames; renaming `products.Item` → `catalog.Product` changes the label and invalidates old `model`-anchored IDs. This is the model-anchored analogue of the type-rename fragility the card mitigates (model renames are far rarer than GraphQL-type renames). Mitigations: the `type+model` transitional mode plus a callable strategy with a consumer alias map; first-class recorded rename-history decoding is `BACKLOG.md` item 39 ("type-rename GlobalID migrations"). Flagged in [Risks and open questions](#risks-and-open-questions).
- **`Meta.name` interaction under `type`** — the `type` strategy's payload tracks [`Meta.name`][glossary-metaname] (the GraphQL surface name), so renaming via `Meta.name` under `type` still invalidates IDs — which is exactly the fragility `model` avoids; documented so a consumer choosing `type` understands the trade.
- **Multiple `DjangoType`s per model, mixed strategies** — a `model`-strategy ID for a multi-type model decodes to the [`Meta.primary`][glossary-metaprimary] type; a sibling can opt into `type` for disjoint identity. A model-anchored ID cannot distinguish secondaries (by design — they share the model); type-scoped IDs are the path for that.
- **`GlobalID` filtering** — unchanged: filtering coerces a `GlobalID` to its `node_id` slot only, so a model-label payload narrows correctly with no decode of the type-name slot.
- **The connection field** ([`DONE-030-0.0.9`][kanban]) and any [`DjangoListField`][glossary-djangolistfield] emitting nodes — `edges { node { id } }` / `list[T]` `{ id }` pick up the model-label payload through the same per-node `resolve_typename`, no field change.
- **Async `resolve_id`** — Strawberry's `_id` computes the type-name slot via `resolve_typename(root, info)` **first**, then handles an awaitable `node_id` (the `resolve_awaitable` branch) by constructing the `GlobalID` after the await. `resolve_typename` is sync for all four strategies — including the callable strategy, whose signature is `(type_cls, model, root, info) -> str` and which never touches `node_id` ([Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion)) — so the awaitable-`node_id` branch is unaffected and no strategy forces a premature or doubled `resolve_id`.

## Test plan

Tests live across the package-internal `tests/types/` tree and the `examples/fakeshop/test_query/` tree, per [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Coverage that can be earned by a real GraphQL query is earned there first; the rest lands in `tests/types/`.

### Slice 1 — `tests/types/test_base.py` (extend)

- `test_meta_globalid_strategy_in_allowed_meta_keys` — `"globalid_strategy"` in [`ALLOWED_META_KEYS`][base], not in [`DEFERRED_META_KEYS`][base].
- `test_meta_globalid_strategy_unknown_string_raises` / `..._non_relay_type_raises` / `..._wrong_type_raises` — the three `_validate_globalid_strategy` failures raise [`ConfigurationError`][glossary-configurationerror].
- `test_meta_globalid_strategy_callable_accepted` — a callable value validates.
- `test_meta_globalid_strategy_stored_on_definition` — the normalized value lands on `definition.globalid_strategy`.
- `test_resolve_globalid_strategy_precedence` — `Meta` override beats setting beats `"model"` default; an unknown `RELAY_GLOBALID_STRATEGY` raises [`ConfigurationError`][glossary-configurationerror] naming the setting.

### Slice 2 — `tests/types/test_relay_interfaces.py` (extend)

- `test_globalid_model_strategy_emits_model_label` — a Relay-Node type with the default emits `app_label.modelname` in the type-name slot.
- `test_globalid_type_strategy_emits_graphql_type_name` — `Meta.globalid_strategy = "type"` reproduces the pre-`0.0.9` GraphQL-type-name payload (byte-identical).
- `test_globalid_type_plus_model_emits_model_label` — `type+model` emits the model-label payload.
- `test_globalid_callable_strategy_emits_custom` — a callable returns the type-name slot.
- `test_consumer_resolve_typename_override_preserved` — a consumer-declared `resolve_typename` survives injection (the `__func__` identity test).
- `test_globalid_default_is_model` — no `Meta` key + no setting → `model`.

### Slice 3 — `tests/types/test_relay_interfaces.py` (the `types/relay.py` mirror)

- `test_decode_model_label_routes_to_primary` — `decode_global_id(relay.GlobalID("products.item", "42"))` (an encoded `GlobalID`, not a raw payload) → `(ItemType, "42")` via `apps.get_model` + `registry.get`; a multi-type model routes to the [`Meta.primary`][glossary-metaprimary] type.
- `test_decode_type_name_routes_via_graphql_name` — a type-name payload resolves via `registry.definition_for_graphql_name(...)`, keyed on `graphql_type_name`.
- `test_decode_type_strategy_honors_meta_name_round_trip` — `ItemType` with `Meta.name = "Item"` under the `type` strategy emits `GlobalID("Item", …)` and decodes back to `ItemType` (proves the decode keys on `graphql_type_name`, not `__name__` — [`docs/feedback.md`][feedback] P1).
- `test_type_plus_model_decodes_both` — the transitional mode decodes an old type-anchored ID AND a new model-anchored ID (the card DoD's explicit requirement).
- `test_encode_decode_round_trip_decodable_strategies` — encode→decode symmetry for `model` / `type` / `type+model` (callable is encode-only — no decode symmetry; covered by the Slice 2 encode test only).
- `test_decode_model_strategy_rejects_type_name_id` / `test_decode_type_strategy_rejects_model_label_id` — the Step-2 strategy-shape enforcement raises [`ConfigurationError`][glossary-configurationerror] in both directions ([`docs/feedback.md`][feedback] P1).
- `test_decode_callable_strategy_has_no_decode_path` — a payload resolving to a `callable`-strategy type raises [`ConfigurationError`][glossary-configurationerror] (encode-only in `0.0.9` — [`docs/feedback.md`][feedback] P2).
- `test_decode_unresolvable_label_raises` — an unknown app/model, an unregistered model, or an ambiguous `graphql_type_name` raises [`ConfigurationError`][glossary-configurationerror] naming the attempt.

### Slice 4 — `examples/fakeshop/test_query/` (extend)

Against a Relay-Node-shaped fakeshop type, reached through the live `/graphql/` HTTP stack (per the fakeshop reload pattern):

- `test_emitted_globalid_is_model_anchored` — an emitted `node { id }` decodes (base64) to `app_label.modelname:<pk>`.
- `test_globalid_filter_round_trip` — `filter: { id: { exact: "<model-label GlobalID>" } }` returns the right row.
- `test_type_strategy_opt_out_reproduces_type_name` — a type (or the project setting) set to `"type"` emits the GraphQL-type-name payload.
- Update the existing `GlobalID` assertions in [`test_products_api.py`][fakeshop-test-products] / [`test_library_api.py`][fakeshop-test-library] for the model-label payload (the default flip changes their expected values).

A check before declaring the suites undisturbed: the encode change alters every **emitted** `GlobalID` value (filter-input GlobalIDs still narrow via the `node_id` slot, so filter tests pass unmodified). Confirm no live test snapshots a whole SDL (the `GlobalID` scalar shape is unchanged — only the wire payload differs) and re-run the affected suites at implementation time.

## Doc updates

Each slice owns its own doc edits. The CHANGELOG-edit permission comes from Slice 5's doc-update step per the explicit-instruction rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — **AGENTS.md prohibits `CHANGELOG.md` edits without permission, and this spec's Slice 5 grants that permission**; the Slice 5 maintainer prompt must name the `CHANGELOG.md` edits explicitly so an agent does not infer permission from a standing document.

- **Slice 5 — GLOSSARY**
  - [`docs/GLOSSARY.md`][glossary]: add a `## Meta.globalid_strategy` entry and a `## RELAY_GLOBALID_STRATEGY` (or a single "Django-model-based GlobalID encoding") entry as `shipped (0.0.9)`, with Index rows and "Relay" / "Type generation" [Browse by category][glossary] entries; extend the [Relay Node integration][glossary-relay-node-integration] body to describe the model-anchored default, the four strategies, and the precedence. **These entries do not exist at spec-authoring time and creating them is out of scope for the [`docs/SPECS/NEXT.md`][next] flow** — they are net-new symbols the build's Slice 5 adds (see [Risks and open questions](#risks-and-open-questions)).
- **Slice 5 — package docs**
  - [`docs/README.md`][docs-readme]: note the model-anchored `GlobalID` default and the `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` opt-out in the shipped surface.
  - [`docs/TREE.md`][tree]: no new module (encode / decode in the existing [`types/relay.py`][relay]); add the [`conf.py`][conf] `RELAY_GLOBALID_STRATEGY` settings-key note if the layout reference enumerates settings.
  - [`TODAY.md`][today]: update the products `GlobalID`-filtering examples to the model-label payload and add the breaking-wire-format-change note (parallel to the `PositiveBigIntegerField → BigInt` `0.0.6` precedent); keep the file products-centric.
  - [`README.md`][readme]: update the status paragraph's shipped-surface line only if it enumerates the GlobalID encoding.
  - [`CHANGELOG.md`][changelog]: a `### Changed` (breaking) bullet for the model-anchored default plus an `### Added` bullet for `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY`, both under `[Unreleased]` (the explicit permission grant above). No version-heading promotion (per [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).
- **Slice 5 — card-completion wrap**
  - [`KANBAN.md`][kanban]: move [`WIP-ALPHA-031-0.0.9`][kanban] to Done with the next `DONE-NNN-0.0.9` id; add / confirm the card body's spec reference points at [`docs/spec-031-globalid_encoding-0_0_9.md`][spec-031]. No version-file edits.

## Risks and open questions

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **The GLOSSARY needs net-new entries for `Meta.globalid_strategy` and `RELAY_GLOBALID_STRATEGY`.** Neither symbol has a [`docs/GLOSSARY.md`][glossary] heading at spec-authoring time, and creating glossary entries is out of scope for the [`docs/SPECS/NEXT.md`][next] flow (the flow may only author the spec + its CSV + the Step-8 archive sweep). Preferred answer: the build's Slice 5 adds `## Meta.globalid_strategy` and `## RELAY_GLOBALID_STRATEGY` (or a single "Django-model-based GlobalID encoding" heading) as `shipped (0.0.9)`, at which point both belong in the companion terms CSV; until then they are intentionally **absent** from `spec-031-globalid_encoding-0_0_9-terms.csv` (the checker flags CSV terms with no glossary heading, so an entry-less term must not be listed). Fallback: none — the entries are required before the card closes; this item exists to make the gap explicit, not to defer it.
- **Strawberry's integration branch reads the injected `resolve_typename`.** Preferred answer per [Decision 3](#decision-3--the-encode-seam-a-strategy-parameterized-resolve_typename-default): `Node._id`'s `else` branch reads `origin.resolve_typename` off the GraphQL type def, and `origin` is the `DjangoType` class carrying the injected classmethod, so the model-label payload is produced for both the `isinstance(root, Node)` and the raw-model-instance branches (verified against the `0.316.0` source). Open risk: a Strawberry version where the integration branch resolves `resolve_typename` differently. Fallback: wire the encode through a custom `id` field resolver on the `DjangoType` (the wholesale-override path Decision 3 rejected for the common case) if the `origin` lookup ever misbehaves.
- **Model-label decode vs Strawberry's native `GlobalID.resolve_type`.** Preferred answer per [Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type): no shipped `0.0.9` path hits native `resolve_type` with a model-label payload (root `node(id:)` is [`WIP-ALPHA-032-0.0.9`][kanban]; filtering uses only `node_id`), so the package's `decode_global_id` is the sole model-label decoder and `032` dispatches through it. Fallback: if a `0.0.9` path is found to reach native `resolve_type` with a model-label `type_name`, gate the `model` strategy default behind `032` (keep `model` available but leave `type` the default until the root fields ship) or install a `GlobalID.resolve_type` shim that recognizes the model-label shape.
- **`type+model` emit direction.** Preferred answer per [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion): emit model-anchored, accept both on decode. Fallback: a sub-mode that emits type-anchored during a deprecation window before flipping to model-anchored, if a consumer needs old clients to keep receiving the old format temporarily.
- **Callable-strategy decode (RESOLVED — encode-only in `0.0.9`).** The earlier draft left the callable decoder an open question while Slice 3 required a callable decode path — an unimplementable contradiction ([`docs/feedback.md`][feedback] P2). Resolved per [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion) / [Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type): callable is **encode-only** in `0.0.9` — the `decode_global_id` dispatch has no callable branch and raises for a callable-strategy candidate; the consumer owns a callable-encoded ID's decode. Fallback / forward path: a paired `(encoder, decoder)` registration API lands with the root-Node decode in [`WIP-ALPHA-032-0.0.9`][kanban] if demand surfaces. The callable encoder signature is fixed to `(type_cls, model, root, info) -> str` (mirrors the `resolve_typename` seam, never sees `node_id`, [`docs/feedback.md`][feedback] P1), so node-id-dependent custom type-name slots are out of scope for this strategy.
- **Default-flip blast radius in the example suites.** Preferred answer: Slice 4 updates every affected live `GlobalID` assertion. Fallback: if the blast radius is larger than estimated, land the example-suite updates as their own commit within Slice 4 so the source change and the test churn are reviewable separately.

## Out of scope (explicitly tracked elsewhere)

- **Root `node(id:)` / `nodes(ids:)`, the relation-as-Connection upgrade, `DjangoNodeField` / `DjangoNodesField`, the public `testing/relay` helpers** ([`DjangoNodeField`][glossary-djangonodefield]) — the [Full Relay story][kanban] ([`WIP-ALPHA-032-0.0.9`][kanban]), which consumes this card's `decode_global_id`.
- **Connection-aware optimizer planning** ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]) — the sibling [`WIP-ALPHA-033-0.0.9`][kanban] card; orthogonal to the GlobalID payload.
- **`DjangoConnectionField`** ([`DjangoConnectionField`][glossary-djangoconnectionfield]) — shipped in [`DONE-030-0.0.9`][kanban]; picks up the model-label payload through the shared `resolve_typename` seam with no change.
- **First-class type-rename / model-rename GlobalID migration history** — `BACKLOG.md` item 39; the `type+model` transitional mode is the lighter bridge this card ships.
- **`search:` argument / `Meta.fields_class` / `aggregates`** — later-version surfaces unrelated to identity encoding.
- **Version bump** — owned by the joint `0.0.9` cut ([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).

## Definition of done

The completion contract the card is built against. Items are grouped by slice; the card completes when all four functional slices' items plus the wrap are satisfied.

**Spec + companion CSV**

1. [`docs/spec-031-globalid_encoding-0_0_9.md`][spec-031] (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/spec-031-globalid_encoding-0_0_9-terms.csv`][spec-031-terms] anchoring every project-specific term that **has** a [`docs/GLOSSARY.md`][glossary] heading; [`uv run python scripts/check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md`][check-spec-glossary] reports `OK: <N> terms`. The net-new `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` symbols have **no** glossary heading yet (out of scope for the spec-authoring flow), so they are intentionally absent from the CSV and tracked as the first [Risks and open questions](#risks-and-open-questions) item; the build's Slice 5 adds their glossary entries.

**Slice 1 — `Meta.globalid_strategy` + setting + precedence**

2. [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] contains `"globalid_strategy"` (not in [`DEFERRED_META_KEYS`][base]); `_validate_globalid_strategy` rejects an unknown string, a non-Relay-Node type, and a wrong type with [`ConfigurationError`][glossary-configurationerror], and accepts a callable; the normalized value is stored on [`DjangoTypeDefinition.globalid_strategy`][definition] ([Decision 6](#decision-6--metaglobalid_strategy-is-a-net-new-allowed_meta_keys-key-stored-on-the-definition)).
3. `_resolve_globalid_strategy(definition)` applies `Meta` → [`conf.settings`][conf]`.RELAY_GLOBALID_STRATEGY` → `"model"` precedence and raises [`ConfigurationError`][glossary-configurationerror] on an unknown setting value ([Decision 5](#decision-5--precedence-metaglobalid_strategy--relay_globalid_strategy--package-default-model) / [Decision 7](#decision-7--the-relay_globalid_strategy-setting-and-the-settings-key-discipline)). [`tests/types/test_base.py`][test-types-base] covers the slice.

**Slice 2 — encode**

4. [`django_strawberry_framework/types/relay.py`][relay] ships the strategy-parameterized encoder and `install_globalid_typename_resolver`, called from [`finalize_django_types`][glossary-finalize_django_types] Phase 2.5, installing a `resolve_typename` default UNLESS the consumer overrode it (the `__func__` identity test), with the `type` strategy leaving Strawberry's default in place ([Decision 3](#decision-3--the-encode-seam-a-strategy-parameterized-resolve_typename-default) / [Decision 10](#decision-10--resolve_typename-injection-via-the-__func__-identity-test-at-phase-25)). The package default is flipped to `model` ([Decision 9](#decision-9--changing-the-default-to-model-is-a-breaking-wire-format-change-acceptable-pre-100)). [`tests/types/test_relay_interfaces.py`][test-relay-interfaces] covers each strategy's payload, override preservation, and the default flip.

**Slice 3 — decode**

5. [`django_strawberry_framework/types/relay.py`][relay] ships `decode_global_id(gid: relay.GlobalID | str)` (accepts an encoded [`relay.GlobalID`][glossary-relay-node-integration] / its base64 string, never a raw payload) implementing the **resolve-then-enforce** dispatch of [Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type): Step 1 resolves a candidate (model-label via `django.apps.apps.get_model` → [`registry.get`][registry] to the primary [`DjangoType`][glossary-djangotype] honoring [`Meta.primary`][glossary-metaprimary]; GraphQL-type-name via the new `registry.definition_for_graphql_name` helper keyed on [`definition.graphql_type_name`][definition], NOT `type_cls.__name__`); Step 2 rejects a payload shape the candidate's effective strategy does not permit (`model` model-label only / `type` type-name only / `type+model` both / `callable` no decode — encode-only). An unresolvable label or a strategy-forbidden shape raises [`ConfigurationError`][glossary-configurationerror]. Tests pin the three-decodable-strategy round-trip symmetry, the `Meta.name` `type`-strategy round-trip, the transitional accept-old-ID path, both Step-2 rejection directions, the callable-no-decode path, primary-routing, and the unresolvable-label error.

**Slice 4 — live HTTP coverage**

6. Live HTTP tests in [`examples/fakeshop/test_query/`][fakeshop-test-products] prove an emitted `GlobalID` is model-anchored, that `GlobalID` filtering round-trips, and that the `type` strategy reproduces the GraphQL-type-name payload; the existing `GlobalID` assertions are updated for the model-label default flip (per the [Test plan](#test-plan)).

**Slice 5 — doc + card-completion wrap**

7. [`docs/GLOSSARY.md`][glossary] gains `## Meta.globalid_strategy` / `## RELAY_GLOBALID_STRATEGY` entries (`shipped (0.0.9)`) with Index + Browse-by-category rows, and the [Relay Node integration][glossary-relay-node-integration] body describes the model-anchored default; [`docs/README.md`][docs-readme] / [`docs/TREE.md`][tree] / [`TODAY.md`][today] / [`README.md`][readme] reflect the shipped surface and the breaking-format note; [`CHANGELOG.md`][changelog] `[Unreleased]` carries the `### Changed` (breaking) + `### Added` bullets (the explicit per-card permission grant named in the Slice 5 maintainer prompt).
8. [`KANBAN.md`][kanban] records the card as `DONE-NNN-0.0.9` (moved from [`WIP-ALPHA-031-0.0.9`][kanban]) with the card body's spec reference pointing at [`docs/spec-031-globalid_encoding-0_0_9.md`][spec-031].
9. **No version bump lands in this card** per [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut): `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` are unchanged; no [`CHANGELOG.md`][changelog] release heading is promoted (the joint `0.0.9` cut owns the bump).
10. Package coverage stays at 100% (`fail_under = 100`). Routine per-slice work does not run pytest locally — owned by CI per the no-pytest-after-edits rule at [`AGENTS.md`][agents] #"Do not run pytest after edits"; worker-local validation is `uv run ruff format .` and `uv run ruff check --fix .`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[kanban]: ../KANBAN.md
[package-init]: ../django_strawberry_framework/__init__.py
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[feedback]: feedback.md
[glossary]: GLOSSARY.md
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-bigint-scalar]: GLOSSARY.md#bigint-scalar
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
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: GLOSSARY.md#fk-id-elision
[glossary-get_queryset-visibility-hook]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-metaconnection]: GLOSSARY.md#metaconnection
[glossary-metainterfaces]: GLOSSARY.md#metainterfaces
[glossary-metamodel]: GLOSSARY.md#metamodel
[glossary-metaname]: GLOSSARY.md#metaname
[glossary-metaprimary]: GLOSSARY.md#metaprimary
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-scalar-field-conversion]: GLOSSARY.md#scalar-field-conversion
[glossary-schema-introspection-management-command]: GLOSSARY.md#schema-introspection-management-command
[glossary-strawberry_config]: GLOSSARY.md#strawberry_config
[glossary-syncmisuseerror]: GLOSSARY.md#syncmisuseerror
[spec-031]: spec-031-globalid_encoding-0_0_9.md
[spec-031-terms]: spec-031-globalid_encoding-0_0_9-terms.csv
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-015]: SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-029]: SPECS/spec-029-consumer_dx_cleanup-0_0_9.md
[spec-030]: SPECS/spec-030-connection_field-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../django_strawberry_framework/types/base.py
[conf]: ../django_strawberry_framework/conf.py
[definition]: ../django_strawberry_framework/types/definition.py
[finalizer]: ../django_strawberry_framework/types/finalizer.py
[registry]: ../django_strawberry_framework/registry.py
[relay]: ../django_strawberry_framework/types/relay.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-registry]: ../tests/test_registry.py
[test-relay-interfaces]: ../tests/types/test_relay_interfaces.py
[test-types-base]: ../tests/types/test_base.py

<!-- examples/ -->
[fakeshop-products-schema]: ../examples/fakeshop/apps/products/schema.py
[fakeshop-test-library]: ../examples/fakeshop/test_query/test_library_api.py
[fakeshop-test-products]: ../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->
[check-spec-glossary]: ../scripts/check_spec_glossary.py

<!-- .venv/ -->

<!-- External -->
