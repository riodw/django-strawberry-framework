# Rationale companion: spec-032 (Full Relay story)

Companion to [`docs/SPECS/spec-032-full_relay-0_0_9.md`][spec-032]. It carries each Decision's justification and the alternatives it rejected; the spec carries the contract.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-032-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `DONE-032-0.0.9`, so `<NNN>` is `032` and `<0_0_X>` is `0_0_9`.
- The topic slug is `full_relay` — the card titles itself "Full Relay story"; the slug names the umbrella, not one member.

### Alternatives considered (and rejected)

- **The card's own `docs/spec-relay_connection.md`.** Rejected: the structured-filename convention governs, as in [`spec-031`][spec-031] Decision 1 ([its rejected naming alternatives][spec-031-rationale-d1]). The card-named file is also wrong on substance — the connection field shipped separately under [`spec-030`][spec-030], so `relay_connection` would mislabel this card's actual scope.
- **Topic slug `relay_root` or `node_field`.** Rejected: both under-describe the umbrella (the card also ships the relation-as-Connection upgrade, the diagnostics, and the test helpers).

## Decision 2 — Card-scope boundary against the 0.0.9 Relay cohort

Spec: [Decision 2 — Card-scope boundary against the 0.0.9 Relay cohort][spec-032-d2].

### Justification

The card's own dependency list names `030` as the hard dependency and the rest as soft/parallel; pinning the boundary keeps this spec scoped to its own part of the eight-goal umbrella instead of re-describing the sibling cards' work.

### Alternatives considered (and rejected)

**Fold `033`'s walker work in (one mega-card).** Rejected: the cards were split deliberately — the optimizer walker is a bounded extension with its own spec home, and the card body pins the split ("ships in parallel").

## Decision 3 — Root fields dispatch through the package decode, not Strawberry's native node field

Spec: [Decision 3 — Root fields dispatch through the package decode, not Strawberry's native node field][spec-032-d3].

### Justification

- **Native dispatch cannot decode the default payload.** Strawberry's `NodeExtension` resolves `node_type = id.resolve_type(info)` = `info.schema.get_type_by_name(type_name)` (locked `0.324.0`). The default strategy emits model-label payloads (`library.genre:42`); no schema type carries that name, so the native field fails for every default-strategy id. [`spec-031`][spec-031] Decision 8 makes `decode_global_id` the package's single decode entry point.
- **The card mandates server-side distrust.** "Decode the GlobalID server-side (never trust the client's claim of which type the ID belongs to)" — `decode_global_id`'s resolve-then-enforce dispatch rejects payload shapes the resolved candidate's recorded strategy does not emit, which the native schema lookup cannot do.
- **The permission contract is already downstream.** `decode_global_id` returns the *type*; the shipped `resolve_node` / `resolve_nodes` defaults run [`get_queryset`][glossary-get_queryset-visibility-hook] on both sync and async branches, so dispatching to them gives the card's "respects `get_queryset`" requirement with zero new permission code.
- **Engine reuse everywhere else.** `GlobalID` parsing, the `Node` interface, the field machinery, and the connection mechanics all stay Strawberry's ([`START.md`][start] "Strawberry = engine"); only the type-resolution hop is package-owned, because it is the one hop the engine resolves by GraphQL type name.

### Alternatives considered (and rejected)

- **Use Strawberry's `relay.node()` and require the `type` strategy for refetchable types.** Rejected: it would make the model-anchored default — the headline of [`DONE-031-0.0.9`][kanban] — incompatible with the Relay story; the two cards were sequenced precisely so the root fields decode the new payload.
- **Patch `GlobalID.resolve_type` to recognize model labels.** Rejected: process-global monkeypatching of engine internals, breaks non-package Strawberry usage in the same process; the per-field resolver is surgical (the same reasoning that rejected the global `resolve_typename` patch in [`spec-031`][spec-031] [Decision 3][spec-031-rationale-d3]).
- **A registry-backed `Schema` subclass overriding type resolution.** Rejected: forces a package-owned `Schema` class onto consumers — a much larger surface commitment than two field factories, and contrary to the `strawberry.Schema(...)` + [`strawberry_config`][glossary-strawberry_config] composition every shipped example uses.

## Decision 4 — `DjangoNodeField` / `DjangoNodesField`: a bare interface form and a typed form

Spec: [Decision 4 — `DjangoNodeField` / `DjangoNodesField`: a bare interface form and a typed form][spec-032-d4].

### Justification

- The card pins the canonical signatures (`node(id: ID!): Node`, `nodes(ids: [ID!]!): [Node]!` with positional `null`s — the `ID` scalar form per the spec's Argument-spelling bullet) and the DoD exports both symbols; [`GOAL.md`][goal] independently pins the typed shape as the `1.0.0` consumer surface. One factory with an optional target serves both without a third symbol.
- The typed mismatch **error** (rather than `null`) is graphene-django's `Node.Field(only_type)` posture: a wrong-type id at a typed field is a client bug, and surfacing it costs nothing — the check runs on decoded payload data before any database query, so it cannot leak row existence.
- Batched per-type `resolve_nodes` is the only shape that scales a heterogeneous `nodes(ids:)` list — one query per distinct type rather than one per id.

### Alternatives considered (and rejected)

- **Separate `DjangoNodeField` (typed-only) and a `DjangoRootNodeField` (bare).** Rejected: two names for one concept; the optional-argument form matches `DjangoConnectionField(target)` / `DjangoListField(target)` muscle memory while keeping the bare Relay-spec spelling available.
- **Typed mismatch returns `null`.** Rejected: it silently masks client bugs (an Item id at a `genre:` field is a programming error, not a visibility outcome), and the Relay-spec `null` contract is about *visibility*, which the mismatch check — running pre-query — never touches.
- **`nodes` raises on any missing id.** Rejected: the card pins "missing IDs become `null` entries (preserves positional correspondence)", which is also Strawberry's `required=not is_optional` behavior for the optional-entry annotation.

## Decision 5 — Null for invisible rows, GraphQLError for malformed ids

Spec: [Decision 5 — Null for invisible rows, GraphQLError for malformed ids][spec-032-d5].

### Justification

- The Relay spec requires `null` (not an exception) for an unresolvable-but-well-formed node lookup, and the card pins it twice; the shipped `resolve_node` default with `required=False` already implements the single-code-path property.
- A malformed id is a *request* error: silently returning `null` for it would make client bugs (truncated ids, double-encoding) indistinguishable from visibility outcomes — the exact debugging trap the loud-`GraphQLError` posture of the `first`+`last` guard and the filter layer's `Invalid filter input` (`extensions={"code": "FILTER_INVALID"}`) already avoids. The `GLOBALID_INVALID` code follows that shipped naming convention.
- Converting at the field boundary (rather than letting [`ConfigurationError`][glossary-configurationerror] bubble raw) keeps internal exception classes and `decode_global_id`'s implementation-flavored messages out of the public wire contract while preserving the diagnostic reason.

### Alternatives considered (and rejected)

- **`null` for everything (malformed included).** Rejected: masks client bugs; loses the strategy-enforcement signal (`031`'s Step-2 rejections exist to be *seen*).
- **Annotation-sensitive `required=True` dispatch** (a non-optional field annotation routes to `resolve_node(..., required=True)` so a missing row raises the model's `DoesNotExist` — Strawberry's native `required=not is_optional` shape). Rejected: it forks the single null code path the no-existence-oracle property depends on, and the spec centers the Relay null contract throughout; a consumer who wants a raising lookup writes a plain field over `get_queryset` themselves.
- **Raw `ConfigurationError` for malformed ids.** Rejected: leaks internal exception taxonomy into the wire contract; the message text would become an accidental API.
- **Declare the id argument as `relay.GlobalID`** (rather than `strawberry.ID`). Rejected: Strawberry's `strawberry/types/arguments.py::convert_argument` runs `GlobalID.from_id(value)` during argument conversion, *before* the resolver — a malformed base64 / non-`type:id` payload then raises the engine's `GlobalIDValueError` upstream of the package, the wire response carries Strawberry's internal error text with **no** `GLOBALID_INVALID` extensions code (an accidental API), and `decode_global_id`'s `from_id`-`ValueError`-wrapping branch is dead code on that path — so the `GLOBALID_INVALID` contract above would be unreachable for exactly the malformed cases it exists to cover. Declaring `strawberry.ID` and feeding the raw string to `decode_global_id` (which accepts `relay.GlobalID | str`) lets the package own every failure shape uniformly; the SDL is byte-identical (`GlobalID` renders as `ID` under Strawberry's modern `relay_use_legacy_global_id = False` default). The weaker fallback — keep `relay.GlobalID` and split the contract so malformed-shape failures surface Strawberry's argument-conversion error (pinning only that it is an in-band GraphQL error, never a 500) while `GLOBALID_INVALID` covers post-parse decode failures only — was rejected for using two error vocabularies for one client-mistake family.
- **HTTP-level 4xx for malformed ids.** Rejected: GraphQL errors travel in-band; the transport stays 200 per the GraphQL-over-HTTP convention the rest of the package follows.

## Decision 6 — Relation-as-Connection synthesis at finalization Phase 2.5

Spec: [Decision 6 — Relation-as-Connection synthesis at finalization Phase 2.5][spec-032-d6].

### Justification

- Phase 2.5 is the only correct home: relation targets are settled (Phase 1), generated relation resolvers exist (Phase 2), and `strawberry.type` has not yet frozen the annotation set (Phase 3) — the same reasoning that placed interface application and sidecar binding there.
- The implicit upgrade is the card's pre-pinned direction (every Relay-Node-shaped `DjangoType` exposes its eligible reverse-FK and M2M relations as Connections). Its default is `"connection"` rather than `"both"` because a raw many-side list beside a bounded connection is a way around that connection's page cap; `"both"` is the explicit opt-in, and the list it restores is row-bounded.
- Requiring a Relay-Node-shaped **target** mirrors the shipped `DjangoConnectionField` fifth guard: a connection's `node` field is typed by the target, and a connection of non-Node types has no Relay identity. Degrading silently to list-only under the *default* (while failing loud on an *explicit* request) keeps a schema building when a Relay type relates to a non-Node target — the library's `BookType.loans` over the non-Node `LoanType` stays list-only.
- Seeding from the relation manager (not the default manager) keeps Django's prefetch caches reachable — the seam [`DONE-033-0.0.9`][kanban]'s window-pagination planning cooperates with.

### Alternatives considered (and rejected)

- **Synthesize at class-creation time (`__init_subclass__`).** Rejected: relation targets may be undeclared at that point ([Definition-order independence][glossary-definition-order-independence]); the target-is-Node-shaped gate needs settled definitions.
- **Connections only on explicit `Meta.relation_shapes` opt-in (no implicit default).** Rejected: the card pre-pins the implicit upgrade as the default; per-relation opt-in is the `"list"` narrowing, not the baseline.
- **Allow connections over non-Node targets (plain edges, no `GlobalID`).** Rejected: contradicts the shipped `DjangoConnectionField` guard and produces connections whose nodes are not refetchable — the broken half of the Relay contract this card exists to complete.
- **Reuse the relation's own field name for the connection (`items: ItemTypeConnection!`).** Rejected: one name would carry two different types across the `"both"` and `"connection"` shapes, so `"both"` could not exist; the distinct `<field>Connection` name (`itemsConnection` alongside `items`) is the card's stated naming and keeps every shape expressible.

## Decision 7 — `Meta.relation_shapes` is a net-new `ALLOWED_META_KEYS` key, stored on the definition

Spec: [Decision 7 — `Meta.relation_shapes` is a net-new `ALLOWED_META_KEYS` key, stored on the definition][spec-032-d7].

### Justification

The rule `Meta.connection` / `Meta.globalid_strategy` follow — the key's feature ships with it, the finalizer reads definitions (not re-parsed `Meta`), and gating to Relay-Node types keeps the eligibility rule single-sited with those two keys.

### Alternatives considered (and rejected)

- **A `DEFERRED_META_KEYS` promotion.** Rejected: the key is not a reserved placeholder; it ships functional.
- **A boolean `Meta.relation_connections = True`.** Rejected: cannot express the per-relation `"list"` / `"connection"` / `"both"` narrowing the card pre-pins.
- **Defer all validation to finalization.** Rejected: name-level typos are detectable at type creation, and the package's posture is fail-at-the-earliest-phase-that-can-know ([`Meta.optimizer_hints`][glossary-metaoptimizer_hints] precedent); only the target-shape check genuinely needs finalization.

## Decision 8 — The six schema-validation diagnostics

Spec: [Decision 8 — The six schema-validation diagnostics][spec-032-d8].

### Justification

- The named-helper messages convert the most common Relay-configuration mistake (reaching for the helper class that *sounds* right) from a generic rejection into a remediation: each message says what the helper is and names the correct surface.
- The enumeration ambiguity is real — the card's DoD count ("six") could also be read as the four validation bullets plus two — so this spec pins the six-helpers reading (the only reading that yields exactly six).
- The no-Node-types check must live at finalization, not field construction: `DjangoNodeField()` runs at class-body time, typically before any `DjangoType` module imports; only the finalizer sees the settled registry.

### Alternatives considered (and rejected)

- **Skip the named branch (the generic rejection already fires).** Rejected: the card explicitly requires the helper-naming messages; a generic "not an interface" for `relay.Connection` leaves the consumer to guess that `Meta.connection` exists.
- **Validate the no-Node-types case at the first `node(id:)` request.** Rejected: a schema-shape error must fail at build time (the package's fail-loud-at-finalization posture), not on first traffic.

## Decision 9 — Cursor mechanics stay delegated to Strawberry; this card pins the conformance contract

Spec: [Decision 9 — Cursor mechanics stay delegated to Strawberry; this card pins the conformance contract][spec-032-d9].

### Justification

[`spec-030`][spec-030] Decision 9 already delegated cursor mechanics, on the [rationale its companion records][spec-030-rationale-d3] that re-implementing cursor math duplicates correct engine behavior; re-implementing it here to match an illustrative byte format would churn the shipped wire contract for zero consumer value. The conformance suite is the card's actual deliverable ("Cursor pagination math passes the package's hand-authored Relay-spec conformance suite").

### Alternatives considered (and rejected)

**Re-implement cursors as literal `b64("offset:N")`.** Rejected: breaks every cursor minted since [`DONE-030-0.0.9`][kanban], duplicates `ListConnection`, and buys nothing — both formats are equally opaque to a compliant client.

## Decision 10 — Public `testing/relay.py` helpers and the export gate

Spec: [Decision 10 — Public `testing/relay.py` helpers and the export gate][spec-032-d10].

### Justification

Consumers writing live tests against the durable ids need to mint expected ids without copy-pasting base64 (`global_id_for`) and to assert what an emitted id resolves to (`decode_global_id`); both upstreams leave this to hand-rolled `to_global_id` calls in consumer tests.

### Alternatives considered (and rejected)

- **Export from the package root (`django_strawberry_framework.global_id_for`).** Rejected: the card names the `testing.relay` home; the root namespace is the schema-authoring surface, and these are test utilities.
- **`global_id_for` accepts a model instance and supports `callable` / `custom`.** Rejected: an instance-accepting variant could thread `root` but still lacks `info`; the strategy system pinned `callable` / `custom` as encode-only-at-request-time, and the helper must not mint ids the type would not emit. A consumer with a custom encoder owns its test helper (the same ownership line `031` drew for custom decode).
- **`global_id_for` rejects secondary model-label emitters (to force round-trip symmetry).** Rejected: a secondary legitimately emits the model-label payload — refusing to mint it would leave consumers hand-encoding exactly the ids their live tests must assert against, and the asymmetry is real schema behavior (`node(id:)` routes the same id to the primary), so the helper documents it rather than hiding it.

## Decision 11 — Module and test-file locations

Spec: [Decision 11 — Module and test-file locations][spec-032-d11].

### Justification

The top-level module matches both the card and the `connection.py` precedent (root-field factories are package-surface modules, not `types/` internals); splitting the two large test surfaces along slice lines keeps each file reviewable for an XL card.

### Alternatives considered (and rejected)

- **Extend `types/relay.py` instead of a new top-level module.** Rejected: `types/relay.py` is the per-type Relay *foundation* (resolver injection, encode/decode); the root fields are consumer-facing schema surface, and `031` already pinned the split.
- **One `tests/test_relay.py`.** Rejected per the prefer-the-card rule.

## Decision 12 — Sequencing against the connection-aware optimizer and the library-first activation

Spec: [Decision 12 — Sequencing against the connection-aware optimizer and the library-first activation][spec-032-d12].

### Justification

The card binds the products conversion to `033` explicitly; the library suite is the card's named live-coverage home; and promoting one library type is the minimal change that makes every DoD bullet live-provable without touching the optimizer-dogfooding products suite.

### Alternatives considered (and rejected)

- **Hold Slice 3 (relation-as-Connection) until `033` merges.** Rejected: the surfaces are functionally independent, and both cards ship in `0.0.9`, so no released version carries an unplanned nested connection.
- **Live relation-as-Connection proof in products instead.** Rejected: products' `test_products_optimizer_*` SQL-shape suite is the regression surface `033` owns.
- **A new fakeshop fixture app instead of promoting `BookType`.** Rejected: a synthetic app exercises nothing real ([`START.md`][start]'s coverage-is-a-feature posture — the example exists to exercise the package via real flows), and the library graph already has the right shapes.

## Decision 13 — Version bumps are owned by the joint `0.0.9` cut

Spec: [Decision 13 — Version bumps are owned by the joint `0.0.9` cut][spec-032-d13].

### Justification

[`docs/SPECS/NEXT.md`][next] Step 6 requires this Decision whenever another non-Done card shares the target's patch version: the bump belongs to the joint cut, so no single card's slice races its siblings for it.

### Alternatives considered (and rejected)

**Bump the version in this card's Slice 7.** Rejected: would race the sibling card for the same bump and promote a release heading before the cohort is cut.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../../GOAL.md
[kanban]: ../../../KANBAN.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-definition-order-independence]: ../../GLOSSARY.md#definition-order-independence
[glossary-get_queryset-visibility-hook]: ../../GLOSSARY.md#get_queryset-visibility-hook
[glossary-metaoptimizer_hints]: ../../GLOSSARY.md#metaoptimizer_hints
[glossary-strawberry_config]: ../../GLOSSARY.md#strawberry_config

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-030-rationale-d3]: spec-030-connection_field-0_0_9-rationale.md#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard
[spec-030]: ../spec-030-connection_field-0_0_9.md
[spec-031-rationale-d1]: spec-031-globalid_encoding-0_0_9-rationale.md#decision-1--spec-filename-and-canonical-naming
[spec-031-rationale-d3]: spec-031-globalid_encoding-0_0_9-rationale.md#decision-3--the-encode-seam-a-strategy-parameterized-resolve_typename-default
[spec-031]: ../spec-031-globalid_encoding-0_0_9.md
[spec-032-d10]: ../spec-032-full_relay-0_0_9.md#decision-10--public-testingrelaypy-helpers-and-the-export-gate
[spec-032-d11]: ../spec-032-full_relay-0_0_9.md#decision-11--module-and-test-file-locations
[spec-032-d12]: ../spec-032-full_relay-0_0_9.md#decision-12--sequencing-against-the-connection-aware-optimizer-and-the-library-first-activation
[spec-032-d13]: ../spec-032-full_relay-0_0_9.md#decision-13--version-bumps-are-owned-by-the-joint-009-cut
[spec-032-d1]: ../spec-032-full_relay-0_0_9.md#decision-1--spec-filename-and-canonical-naming
[spec-032-d2]: ../spec-032-full_relay-0_0_9.md#decision-2--card-scope-boundary-against-the-009-relay-cohort
[spec-032-d3]: ../spec-032-full_relay-0_0_9.md#decision-3--root-fields-dispatch-through-the-package-decode-not-strawberrys-native-node-field
[spec-032-d4]: ../spec-032-full_relay-0_0_9.md#decision-4--djangonodefield--djangonodesfield-a-bare-interface-form-and-a-typed-form
[spec-032-d5]: ../spec-032-full_relay-0_0_9.md#decision-5--null-for-invisible-rows-graphqlerror-for-malformed-ids
[spec-032-d6]: ../spec-032-full_relay-0_0_9.md#decision-6--relation-as-connection-synthesis-at-finalization-phase-25
[spec-032-d7]: ../spec-032-full_relay-0_0_9.md#decision-7--metarelation_shapes-is-a-net-new-allowed_meta_keys-key-stored-on-the-definition
[spec-032-d8]: ../spec-032-full_relay-0_0_9.md#decision-8--the-six-schema-validation-diagnostics
[spec-032-d9]: ../spec-032-full_relay-0_0_9.md#decision-9--cursor-mechanics-stay-delegated-to-strawberry-this-card-pins-the-conformance-contract
[spec-032]: ../spec-032-full_relay-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
