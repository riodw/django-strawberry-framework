# Rationale companion: spec-031 (Django-model-based GlobalID encoding)

Companion to [`docs/SPECS/spec-031-globalid_encoding-0_0_9.md`][spec-031]. It carries each Decision's justification and the alternatives it rejected; the spec carries the contract.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-031-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `DONE-031-0.0.9`, so `<NNN>` is `031` and `<0_0_X>` is `0_0_9`.
- The topic slug is `globalid_encoding` — it names the card's subject (the GlobalID encoding strategy system) in snake_case.
- The card DoD permits "A new **or amended** Relay spec." This flow authors a **new** spec per the one-spec-per-WIP-card [`docs/SPECS/NEXT.md`][next] rule rather than amending [`spec-015`][spec-015]; amending a shipped predecessor would bury a `0.0.9` build plan inside a `0.0.5` record.

### Alternatives considered (and rejected)

- **Amend `spec-015-relay_interfaces-0_0_5.md`.** Rejected: `spec-015` is a shipped record; the flow's structured-filename convention bakes the card's NNN into a fresh file.
- **Topic slug `relay_globalid` or `model_globalid`.** Rejected: `relay_globalid` over-claims the Relay-Root surface this card scopes out ([Decision 2](#decision-2--card-scope-boundary-against-the-sibling-relay-cards)); `model_globalid` under-describes the strategy system (the card ships `type` and callable too). `globalid_encoding` names the whole encoding decision.

## Decision 2 — Card-scope boundary against the sibling Relay cards

Spec: [Decision 2 — Card-scope boundary against the sibling Relay cards][spec-031-d2].

### Justification

The card body names the ordering dependency (031 before 032) and the orthogonality (031 independent of 030); pinning the boundary keeps the spec scoped to what `031` ships and prevents pulling `032`'s eight-goal umbrella into one card.

### Alternatives considered (and rejected)

**Fold the encoding decision into the Full Relay story (`032`).** Rejected: the card exists to settle the format *before* `032` makes it a public contract; merging them re-creates the migration-work risk the card exists to avoid.

## Decision 3 — The encode seam: a strategy-parameterized `resolve_typename` default

Spec: [Decision 3 — The encode seam: a strategy-parameterized `resolve_typename` default][spec-031-d3].

### Justification

- [`START.md`][start]'s "Strawberry = engine" rule: re-rooting via the documented `resolve_typename` seam reuses Strawberry's correct `GlobalID` plumbing; hand-rolling a base64 scheme would duplicate engine behavior and drift from the Relay spec.
- The seam is the exact analogue of the `0.0.5` `resolve_*` injection, so the consumer-override-preservation contract (`__func__` identity test) and the Phase-2.5 timing are reused, not reinvented.

### Alternatives considered (and rejected)

- **Override the `id` field wholesale on the `DjangoType`.** Rejected: duplicates Strawberry's `GlobalID(type_name=..., node_id=str(...))` construction and the awaitable branch; the collision guard at `__init_subclass__` rejects `id` overrides on Relay types, so this would fight the shipped contract.
- **Monkeypatch `strawberry.relay.GlobalID` / `Node.resolve_typename` globally.** Rejected: process-global, breaks the `type` strategy and any other Strawberry library in the process; the per-type injection is surgical.
- **Encode the strategy into `resolve_id` (the `node_id` slot).** Rejected: the `node_id` slot is the pk and must stay clean for `GlobalID` filtering and the relation `id` round-trip; the type-name slot is the correct home.

## Decision 4 — Four strategies (`model`, `type`, `type+model`, callable) and an unchanged `node_id` portion

Spec: [Decision 4 — Four strategies (`model`, `type`, `type+model`, callable) and an unchanged `node_id` portion][spec-031-d4].

### Justification

- The four strategies are the card's stated scope. `model` as default is the card's headline; `type` is the parity-preserving opt-out; `type+model` is the explicit transitional mode the card names; callable is the escape hatch for custom schemes.
- Decoupling the type-name slot from the `node_id` slot keeps `GlobalID` filtering, FK-`id` elision, and the relation `id` round-trip untouched ([Current state][spec-031-current-state]).

### Alternatives considered (and rejected)

- **Ship only `model` (no `type` opt-out).** Rejected: the card explicitly keeps the legacy mode available; some consumers need type-scoped identity (disjoint auth/cache scopes), which the card calls out as a "legitimate legacy mode."
- **Make `type` the default and `model` opt-in.** Rejected: the card explicitly makes `model` the new default; deferring the breaking change to opt-in re-creates the post-`1.0.0` migration-work problem the card exists to prevent ([Decision 9](#decision-9--changing-the-default-to-model-is-a-breaking-wire-format-change-acceptable-pre-100)).
- **`type+model` emits type-name during the window.** Rejected: emitting model-anchored from day one is what makes new IDs durable; accepting both on decode is the migration bridge, so the emit direction should already be the target format.

## Decision 5 — Precedence: `Meta.globalid_strategy` → `RELAY_GLOBALID_STRATEGY` → package default (`model`)

Spec: [Decision 5 — Precedence: `Meta.globalid_strategy` → `RELAY_GLOBALID_STRATEGY` → package default (`model`)][spec-031-d5].

### Justification

- `Meta`-over-setting-over-default is the package's standard precedence shape (the card pins it verbatim) and matches how a per-type opt-out should beat a project-wide knob.
- Resolving at finalization (not per request) means the injected `resolve_typename` is a fixed closure — no per-call strategy lookup on the `id`-resolution hot path, and a single source of truth for the type's identity format.

### Alternatives considered (and rejected)

- **Resolve per request.** Rejected: the `GlobalID` format is a durable client contract; varying it per request would mint inconsistent IDs and defeat caching.
- **Setting-only (no per-type override).** Rejected: the card wants per-type `Meta.globalid_strategy` so a consumer can keep one type type-scoped while the rest go model-anchored (disjoint auth/cache scopes).

## Decision 6 — `Meta.globalid_strategy` is a net-new `ALLOWED_META_KEYS` key, stored on the definition

Spec: [Decision 6 — `Meta.globalid_strategy` is a net-new `ALLOWED_META_KEYS` key, stored on the definition][spec-031-d6].

### Justification

- A key whose feature ships with it — the [`spec-030`][spec-030] / [`spec-029`][spec-029] situation, so straight into `ALLOWED_META_KEYS`.
- Storing on the definition is required because the `resolve_typename` injection happens at finalization, away from the `Meta` shape; the definition is the canonical per-type record the finalizer already reads ([`connection`][definition] set the exact precedent).
- Gating to Relay-Node types via the shared `_is_relay_shaped` predicate keeps the eligibility rule single-sited with `Meta.connection`.

### Alternatives considered (and rejected)

- **A `DEFERRED_META_KEYS` promotion.** Rejected: the key is not a reserved placeholder; it ships functional.
- **Validate but do not store (re-parse `Meta` at finalize).** Rejected: fragile and divergent from how `connection` / `filterset_class` / `orderset_class` are threaded; the definition is the one record the finalizer consults.
- **A boolean `Meta.model_globalid = True`.** Rejected: cannot express `type+model` or callable; the four-way strategy is the card's scope.

## Decision 7 — The `RELAY_GLOBALID_STRATEGY` setting and the settings-key discipline

Spec: [Decision 7 — The `RELAY_GLOBALID_STRATEGY` setting and the settings-key discipline][spec-031-d7].

### Justification

- The settings-key-only-when-needed rule is a hard project convention ([`START.md`][start]); this card is exactly the landing card for the key.
- [`conf.py`][conf]'s documented contract is "thin reader, no domain coercion" ([Current state][spec-031-current-state]); putting the strategy validation in the consumer keeps that contract and matches where `Meta.globalid_strategy`'s validation lives.

### Alternatives considered (and rejected)

- **Validate the setting eagerly inside `conf.py`.** Rejected: [`conf.py`][conf] is intentionally domain-agnostic; coupling it to the strategy vocabulary would re-introduce the defensive-coercion shape the module's docstring warns against.
- **No setting (per-type `Meta` only).** Rejected: the card explicitly wants a schema-wide default knob so a project can flip every type at once without touching each `Meta`.

## Decision 8 — Decode routes through Django's app registry then the framework registry to the primary type

Spec: [Decision 8 — Decode routes through Django's app registry then the framework registry to the primary type][spec-031-d8].

### Justification

- Django's `apps.get_model` is the canonical `app_label.model → model` resolver and the durable anchor the whole card is built on; routing through it (then `registry.get`) reuses the registry's existing primary-resolution contract rather than inventing a parallel label index.
- Primary-routing matches how relation targets already resolve ([`DjangoTypeDefinition.related_target_for`][definition] uses `registry.get`), so a decoded ID and a traversed relation land on the same type.
- Keying type-name decode on `graphql_type_name` (not `type_cls.__name__`) is the only spelling that round-trips a `type`-strategy ID: the encode side emits `graphql_type_name`, so the decode side must invert the same function or a [`Meta.name`][glossary-metaname] rename silently breaks refetch.
- Resolving the candidate's strategy and enforcing the payload shape (Step 2) is what gives each strategy its documented contract — without it the decoder is permissive-by-default and `model` / `type` / `type+model` collapse into one indistinguishable behavior.

### Alternatives considered (and rejected)

- **Decode to a secondary type.** Rejected: ambiguous which secondary; the primary is the canonical relation-resolution target, and `type`-scoped IDs are the explicit path for disjoint scopes.
- **A package-owned `{label: type}` index instead of Django's app registry.** Rejected: duplicates Django's model registry, misses proxy/MTI label resolution Django already handles, and drifts on app renames.
- **Reuse Strawberry's native `GlobalID.resolve_type`.** Rejected: it is hardcoded to `info.schema.get_type_by_name(type_name)` (a GraphQL type name), so it cannot resolve a model label; the package must own the model-label dispatch.
- **A permissive decoder that accepts any resolvable shape (no Step-2 strategy enforcement).** Rejected: it makes `type+model` indistinguishable from the default, lets a `model`-strategy type keep accepting stale type-anchored IDs, and dissolves the `type` strategy's type-scoped guarantee.
- **Type-name decode via `type_cls.__name__`.** Rejected: the `type` strategy emits `graphql_type_name`, so a `Meta.name`-renamed type would emit its `Meta.name` value yet be undecodable by class name; decode must invert the encode function.
- **Authorize a model-label payload's shape from the *set* of all registered definitions for the model (while still routing to the primary), instead of the finalization invariant.** Rejected in favor of the stricter invariant: it leaves the schema in a state where a model-label ID is *accepted* but its resolved row comes from the primary's `get_queryset`, not the emitter's — a subtler identity confusion than a loud finalization error, and harder to reason about. The invariant makes the misconfiguration impossible to ship.

## Decision 9 — Changing the default to `model` is a breaking wire-format change, acceptable pre-`1.0.0`

Spec: [Decision 9 — Changing the default to `model` is a breaking wire-format change, acceptable pre-`1.0.0`][spec-031-d9].

### Justification

Settling identity format pre-`1.0.0` is the card's reason to exist; the alpha window plus the `type` opt-out make the breaking flip the right call before the freeze rather than after it. The upgrade trap is closed by documenting the upgrade sequence, not by changing the default away from the destination.

### Alternatives considered (and rejected)

- **Default to `type`, ship `model` as opt-in.** Rejected: the card explicitly makes `model` the new default; opt-in `model` leaves every existing consumer type-anchored into `1.0.0`, re-creating the migration-work problem.
- **Ship `type+model` as the default.** Rejected: `type+model` is the migration bridge, not a steady state — its dual-accept decode is a transitional cost, not something to bake in as the default; `model` is the destination.

## Decision 10 — `resolve_typename` injection via the `__func__` identity test, at Phase 2.5

Spec: [Decision 10 — `resolve_typename` injection via the `__func__` identity test, at Phase 2.5][spec-031-d10].

### Justification

- Phase 2.5 is where Relay resolver injection already happens, and the `__func__` identity test is the shipped, tested mechanism for preserving consumer overrides; reusing both keeps one source of truth for Relay-method injection.
- Keeping `resolve_typename` out of `_RELAY_RESOLVER_DEFAULTS` respects that table's invariant (name → one static default) while still installing through the same `__func__`-gated discipline.
- Classifying an override as `custom`/encode-only (rather than letting the override emit while the type's `Meta`/default strategy drives decode) is the only rule that keeps the package's emit and decode in agreement — the framework never emits an ID its own decoder refuses, because for a `custom` type the decoder explicitly declines (encode-only), exactly as for `callable`.
- Recording the effective strategy at finalization (pre-install) is required precisely because installing the framework closure erases the `__func__` signal decode would otherwise need.

### Alternatives considered (and rejected)

- **Add `resolve_typename` to `_RELAY_RESOLVER_DEFAULTS`.** Rejected: that table's entries are static `(name, default_impl)` pairs; the typename default varies by resolved strategy, so it cannot be a single static impl.
- **Inject at class-creation time (`__init_subclass__`) instead of Phase 2.5.** Rejected: the effective strategy depends on the `RELAY_GLOBALID_STRATEGY` setting and the registry being stable; finalization is the package's "registry is stable now" point, matching where the other Relay defaults install. (The MRO-aware `__func__` override test also belongs here — an override inherited from a non-`Meta` base is invisible to a `cls.__dict__`-only check at class creation.)
- **Let a `resolve_typename` override silently win and the `Meta.globalid_strategy` drive decode anyway.** Rejected: the override would emit a label the (`model`-default) decoder then rejects. The two are contradictory; the override wins for encode and forces `custom`/encode-only decode, and declaring both explicitly fails loud.

## Decision 11 — Module location: encode/decode in `types/relay.py`, no public export in `0.0.9`

Spec: [Decision 11 — Module location: encode/decode in `types/relay.py`, no public export in `0.0.9`][spec-031-d11].

### Justification

A flat addition to the Relay foundation module matches where the `0.0.5` resolver defaults live; the Root-Node surface and the public test helpers belong to [`DONE-032-0.0.9`][kanban]'s `relay.py` and `testing/relay.py`.

### Alternatives considered (and rejected)

- **Put encode/decode in the top-level `relay.py`.** Rejected: the pair belongs with the Relay foundation; `relay.py` is the Root-Node surface.
- **Export `decode_global_id` publicly from this card.** Rejected: the tested-usage export discipline puts a public symbol beside the live consumer that proves its shape — the `testing/relay.py` re-export `032` ships with the root fields.

## Decision 12 — Version bumps are owned by the joint `0.0.9` cut

Spec: [Decision 12 — Version bumps are owned by the joint `0.0.9` cut][spec-031-d12].

### Justification

[`docs/SPECS/NEXT.md`][next] Step 6 requires this Decision whenever another non-Done card shares the target's patch version: the bump belongs to the joint cut, so no single card's slice races its siblings for it.

### Alternatives considered (and rejected)

**Bump the version in this card's Slice 5.** Rejected: would race the sibling cards for the same bump and promote a release heading before the cohort is cut.

## Decision 13 — `GlobalID` filter validation is strategy-aware

Spec: [Decision 13 — `GlobalID` filter validation is strategy-aware][spec-031-d13].

### Justification

- For the three framework strategies the `type_name` check is a defense-in-depth sanity guard, so making it strategy-aware keeps the guard where the label can be computed and never blocks a legitimate emitted ID. For `callable` / `custom` the framework cannot compute the expected label AND has no decode path, so the correct posture is to fail closed rather than degrade to node-id-only matching: an encode-only target's IDs are not framework-consumable, and accepting them on `node_id` alone would silently admit arbitrary payloads.
- Reading the recorded `effective_globalid_strategy` keeps the filter layer on the single durable contract decode already uses — no second source of truth, no per-request settings read.
- Rejecting at schema build (the [`_audit_globalid_filter_strategies`][finalizer] Phase-2.5 audit) surfaces the misconfiguration at the earliest fail-loud point; the runtime `GLOBALID_UNVALIDATABLE` `GraphQLError` in [`_decode_and_validate_global_id`][filters-base] only backstops hand-built filtersets that never went through binding.

### Alternatives considered (and rejected)

- **Leave the filter check on `graphql_type_name` and tell consumers to filter with type-anchored IDs.** Rejected: the emitted ID is model-anchored under the default, so the consumer would have to hand-translate every ID before filtering — exactly the boilerplate the package removes.
- **Drop the `type_name` guard entirely (node-id-only for all strategies).** Rejected: it discards a useful wrong-model rejection the three framework strategies can still enforce.
- **Fall back to node-id-only for `callable` / `custom`.** Rejected: an encode-only strategy has no framework decode path, so a decode-requiring `GlobalID` input can never be validly consumed against such a target; node-id-only matching would silently accept arbitrary payloads. Fail-closed (build-time [`ConfigurationError`][glossary-configurationerror] from [`_audit_globalid_filter_strategies`][finalizer] plus the runtime `GLOBALID_UNVALIDATABLE` backstop) is the correct posture; a consumer who genuinely needs to filter a `callable` / `custom` type owns a decode path. The one retained node-id-only path is the unbound-owner / unresolvable-target `None`-expected case, where no strategy is available at all.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../../KANBAN.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-metaname]: ../../GLOSSARY.md#metaname

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-015]: ../spec-015-relay_interfaces-0_0_5.md
[spec-029]: ../spec-029-consumer_dx_cleanup-0_0_9.md
[spec-030]: ../spec-030-connection_field-0_0_9.md
[spec-031-current-state]: ../spec-031-globalid_encoding-0_0_9.md#current-state
[spec-031-d10]: ../spec-031-globalid_encoding-0_0_9.md#decision-10--resolve_typename-injection-via-the-__func__-identity-test-at-phase-25
[spec-031-d11]: ../spec-031-globalid_encoding-0_0_9.md#decision-11--module-location-encodedecode-in-typesrelaypy-no-public-export-in-009
[spec-031-d12]: ../spec-031-globalid_encoding-0_0_9.md#decision-12--version-bumps-are-owned-by-the-joint-009-cut
[spec-031-d13]: ../spec-031-globalid_encoding-0_0_9.md#decision-13--globalid-filter-validation-is-strategy-aware
[spec-031-d1]: ../spec-031-globalid_encoding-0_0_9.md#decision-1--spec-filename-and-canonical-naming
[spec-031-d2]: ../spec-031-globalid_encoding-0_0_9.md#decision-2--card-scope-boundary-against-the-sibling-relay-cards
[spec-031-d3]: ../spec-031-globalid_encoding-0_0_9.md#decision-3--the-encode-seam-a-strategy-parameterized-resolve_typename-default
[spec-031-d4]: ../spec-031-globalid_encoding-0_0_9.md#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion
[spec-031-d5]: ../spec-031-globalid_encoding-0_0_9.md#decision-5--precedence-metaglobalid_strategy--relay_globalid_strategy--package-default-model
[spec-031-d6]: ../spec-031-globalid_encoding-0_0_9.md#decision-6--metaglobalid_strategy-is-a-net-new-allowed_meta_keys-key-stored-on-the-definition
[spec-031-d7]: ../spec-031-globalid_encoding-0_0_9.md#decision-7--the-relay_globalid_strategy-setting-and-the-settings-key-discipline
[spec-031-d8]: ../spec-031-globalid_encoding-0_0_9.md#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type
[spec-031-d9]: ../spec-031-globalid_encoding-0_0_9.md#decision-9--changing-the-default-to-model-is-a-breaking-wire-format-change-acceptable-pre-100
[spec-031]: ../spec-031-globalid_encoding-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../../django_strawberry_framework/conf.py
[definition]: ../../../django_strawberry_framework/types/definition.py
[filters-base]: ../../../django_strawberry_framework/filters/base.py
[finalizer]: ../../../django_strawberry_framework/types/finalizer.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
