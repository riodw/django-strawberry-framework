# Rationale companion: spec-030 (`DjangoConnectionField` — the Relay connection field)

Companion to [`docs/SPECS/spec-030-connection_field-0_0_9.md`][spec-030]. It carries each Decision's justification and the alternatives it rejected; the spec carries the contract.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-030-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `DONE-030-0.0.9`, so `<NNN>` is `030` and `<0_0_X>` is `0_0_9`.
- The topic slug is `connection_field` — it names the card's subject (the `DjangoConnectionField` primitive) in snake_case, parallel to the [`DjangoListField`][glossary-djangolistfield] sibling's `spec-020-list_field-0_0_7.md`.

### Alternatives considered (and rejected)

- **Honor the card body verbatim with `docs/spec-connection.md`.** Rejected: unnumbered against its card, breaks the structured-filename convention, would not sort alongside its siblings.
- **Topic slug `connection` or `relay_connection`.** Rejected: `connection` is too terse to disambiguate from the future `relay.py` Root-Node work; `relay_connection` over-claims the Relay-Root surface this card scopes out ([Decision 2](#decision-2--card-scope-boundary-against-the-sibling-relay-cards)).

## Decision 2 — Card-scope boundary against the sibling Relay cards

Spec: [Decision 2 — Card-scope boundary against the sibling Relay cards][spec-030-d2].

### Justification

The card body and `032`'s body both name this dependency direction; pinning the boundary keeps the spec scoped to what `030` ships and prevents pulling `032`'s eight-goal umbrella into one card.

### Alternatives considered (and rejected)

**Fold the Full Relay story into this spec.** Rejected: `032` is an L-XL eight-goal card with its own spec; one spec per WIP card is the [`docs/SPECS/NEXT.md`][next] flow, and the connection field is independently shippable.

## Decision 3 — Build on Strawberry's native Relay machinery, but own the `first` + `last` guard

Spec: [Decision 3 — Build on Strawberry's native Relay machinery, but own the `first` + `last` guard][spec-030-d3].

### Justification

- [`START.md`][start]'s rule: "Strawberry = engine." Re-implementing cursor math would duplicate correct engine behavior and drift from the Relay spec. The package's value is the Django-aware queryset pipeline and the Meta-driven argument generation, not cursor arithmetic.
- The one place Strawberry's behavior diverges from the card's contract — the missing `first` + `last` guard — is surfaced honestly and implemented in the one method that receives the pagination args, rather than left as a false claim that the engine handles it.

### Alternatives considered (and rejected)

- **Rely on Strawberry to reject `first` + `last`.** Rejected: `SliceMetadata.from_arguments` does not (locked `0.324.0`); a spec must not rely on absent upstream behavior.
- **Allow `first` + `last` (drop the guard).** Rejected: the card body explicitly wants it rejected; combining them is a client error worth surfacing.
- **Hand-roll the whole cursor / pageInfo math.** Rejected: re-implements engine behavior and balloons the test surface.

## Decision 4 — `DjangoConnection[T]` base plus per-target concrete connection classes

Spec: [Decision 4 — `DjangoConnection[T]` base plus per-target concrete connection classes][spec-030-d4].

### Justification

- Concrete-per-shape connection classes are exactly `strawberry-django`'s `ListConnectionWithTotalCount` pattern — the proven place to add `total_count` and override `resolve_connection` without disturbing cursor mechanics.
- Selection-gating avoids an unconditional count query when a client selects only `edges` / `pageInfo`; instance-attachment avoids the fragility of context keying under aliasing.

### Alternatives considered (and rejected)

- **One generic `DjangoConnection[T]` with a conditional field.** Rejected: a static Strawberry class cannot toggle a field per specialization.
- **Always-present `totalCount`, count execution opt-in.** Rejected: the card specifies the field itself is opt-in; advertising `totalCount` on a type that never wants it pollutes the schema.
- **Stashing the count on `info.context` keyed by path-string.** Rejected: fragile under aliasing; the connection instance is the natural carrier.

## Decision 5 — Factory-function mechanism, Meta-only derivation

Spec: [Decision 5 — Factory-function mechanism, Meta-only derivation][spec-030-d5].

### Justification

- Strawberry's class-body walk picks up the factory's return value like `relay.connection(...)`; the consumer writes `attr: Annotation = DjangoConnectionField(T)`, identical in shape to the shipped `DjangoListField(T)`.
- Meta-only derivation keeps the API minimal and avoids two ways to specify the same thing; it also removes the connection-type naming/caching ambiguity per-field overrides would create.

### Alternatives considered (and rejected)

- **Keep `filters=` / `order=` / `total_count=` overrides.** Rejected: they leave the API undecided and force per-field connection-type variants (naming/caching cost); `Meta`-driven is the borrow and the primary surface. An override would be additive, with its own validation / precedence / naming rules.
- **A `DjangoConnectionField` class (descriptor).** Rejected: diverges from the shipped `DjangoListField` factory shape for no gain.

## Decision 6 — Sidecar-derived arguments via a synthesized resolver signature

Spec: [Decision 6 — Sidecar-derived arguments via a synthesized resolver signature][spec-030-d6].

### Justification

- It reuses Strawberry's native resolver-argument derivation and the exact `filter_input_type` / `order_input_type` shapes the hand-written resolvers use, so a connection field and a hand-written resolver on the same type resolve to the *same* `<Type>FilterInputType` (Apollo-cache friendly) and inherit active-input gating, `check_*_permission` propagation, and [`RelatedFilter`][glossary-relatedfilter] / [`RelatedOrder`][glossary-relatedorder] visibility scoping unchanged.
- It needs no custom field-extension class for the common path — the resolver signature *is* the SDL contract.

### Alternatives considered (and rejected)

- **Rely on the helpers alone.** Rejected: they return annotations and write ledgers; nothing adds the arguments to the field.
- **A custom `FieldExtension.apply(...)` appending `StrawberryArgument`s.** Not needed: signature derivation composes with `relay.connection()`'s `ConnectionExtension`, which merges the resolver-signature arguments with its pagination arguments and forwards the non-pagination kwargs to the resolver. An extension that appends `filter` / `order_by` before field build and pops them in `resolve` would produce the same SDL through a second mechanism.
- **Generate fresh per-connection-field input types.** Rejected: duplicate GraphQL input types per field, breaking Apollo cache reuse and the stable-name contract.

## Decision 7 — Composition pipeline: visibility→filter→order→default-order→optimizer

Spec: [Decision 7 — Composition pipeline: visibility→filter→order→default-order→optimizer][spec-030-d7].

### Justification

- This is the card body's composition order, correct for three reasons: visibility must run first so a filter cannot match a parent through a child the visibility hook hides (the [`RelatedFilter`][glossary-relatedfilter] contract); the optimizer must plan the pre-slice queryset; and `totalCount` is the count of the post-filter, pre-pagination set.
- The deterministic-total-ordering step prevents nondeterministic pages: Strawberry's `ListConnection` uses positional offset cursors, which are stable across requests ONLY over a unique total order. A bare `order_by("name")` (supplied `orderBy` or `Meta.ordering`) with duplicate names is not a total order — SQL leaves tied rows unspecified — so the step appends the pk as a terminal tiebreaker in every case except when the ordering already ends in a unique column. This is distinct from the `Meta.cursor_field` keyset-cursor opt-in ([Decision 9](#decision-9--cursor-encoding-delegated-to-strawberry-keyset-cursors-are-a-separate-opt-in)); it is a guaranteed total order, not a value-based cursor.
- The explicit consumer-resolver contract prevents a custom resolver from silently skipping the advertised Meta-driven behavior.

### Alternatives considered (and rejected)

- **Filter before visibility / order before filter / count after the slice.** Rejected: an existence leak, wasted work, and a count equal to the page size.
- **No default ordering (rely on the database's natural order).** Rejected: nondeterministic pages from an unordered plan.
- **Treat any consumer-resolver return as paginatable regardless of sidecar input.** Rejected: filter/order can only apply to querysets; silently ignoring sidecar input on a list would advertise behavior the field does not deliver.

## Decision 8 — `Meta.connection` opt-in key, stored on the definition

Spec: [Decision 8 — `Meta.connection` opt-in key, stored on the definition][spec-030-d8].

### Justification

- A key whose feature ships with it — the [`spec-029`][spec-029] [Decision 6][spec-029] situation, so straight into `ALLOWED_META_KEYS`.
- A dict is forward-compatible: a further connection option is a new sub-key, not a new `Meta` key.
- Storing on the definition is required because the connection-type generation happens at field-construction / finalization time, away from the `Meta` shape; the definition is the canonical per-type record the rest of the package already reads.

### Alternatives considered (and rejected)

- **Validate `Meta.connection` but not store it.** Rejected: the connection-class generator has nowhere to read the opt-in from; re-parsing `Meta` later is fragile and diverges from how `filterset_class` / `orderset_class` are threaded.
- **A flat `Meta.total_count = True` boolean.** Rejected: not forward-compatible.
- **Always-on `totalCount`.** Rejected per [Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes).

## Decision 9 — Cursor encoding delegated to Strawberry; keyset cursors are a separate opt-in

Spec: [Decision 9 — Cursor encoding delegated to Strawberry; keyset cursors are a separate opt-in][spec-030-d9].

### Justification

Opaque offset cursors are the Relay-spec-compliant default `ListConnection` ships. Value-encoded cursors are a larger design with their own codec, seek planning, and finalization validation, so they live in `keyset.py` behind `Meta.cursor_field` and the connection base only dispatches to them.

### Alternatives considered (and rejected)

**Build the keyset codec into the connection field.** Rejected: its own design space; the connection field owns the dispatch seam, not the codec.

## Decision 10 — Sync + async resolver paths reuse the shared visibility helpers

Spec: [Decision 10 — Sync + async resolver paths reuse the shared visibility helpers][spec-030-d10].

### Justification

The Relay foundation already solved sync/async `get_queryset` dispatch and the sync-meets-async misuse; reusing those helpers keeps one source of truth and inherits [`SyncMisuseError`][glossary-syncmisuseerror]. The async `totalCount` count uses `.acount()` on the async path.

### Alternatives considered (and rejected)

**Sync-only connection resolver.** Rejected: both upstreams and the rest of this package support async.

## Decision 11 — The connection field owns its optimizer cooperation point

Spec: [Decision 11 — The connection field owns its optimizer cooperation point][spec-030-d11].

### Justification

- It is the only correct way to optimize a connection field given Strawberry's pipeline: the field must apply the plan before the connection result hides the queryset.
- Passing `target_type` / `target_model` explicitly sidesteps the `info.return_type`-is-the-connection-type problem.
- One shared core (`apply_to`) rather than a duplicate of `_optimize` keeps the middleware and the connection field on one plan-application implementation, so the connection-aware walker work in `033` improves both.

### Alternatives considered (and rejected)

- **Rely on the root-gated middleware.** Rejected: it never sees the queryset behind the connection result.
- **Block the connection field on `033`.** Rejected: a root connection field is useful on its own (filter / order / cursor pagination / `totalCount`) and its cooperation point plans the root node type; `033`'s nested-window planning plugs into the same seam as a walker change, not a connection-field retrofit.
- **Infer the model from `info.return_type`.** Rejected: the return type is the connection type; the helper must be told the node type / model.

## Decision 12 — No auto-trigger of `finalize_django_types()` for `0.0.9`

Spec: [Decision 12 — No auto-trigger of `finalize_django_types()` for `0.0.9`][spec-030-d12].

### Justification

An auto-trigger must respect the single-threaded-setup window: either be constrained to schema-construction time, or acquire a real lock around the finalizer. Neither [`DjangoListField`][glossary-djangolistfield] nor [`DjangoNodeField`][glossary-djangonodefield] auto-triggers finalize; matching their posture avoids a finalizer-locking surface the connection field does not need.

### Alternatives considered (and rejected)

**Auto-trigger finalize from the field constructor now.** Rejected: introduces the single-threaded-setup-window problem for a field that works fine with explicit finalize, and diverges from the `DjangoListField` precedent for no benefit.

## Decision 13 — Version bumps are owned by the joint `0.0.9` cut

Spec: [Decision 13 — Version bumps are owned by the joint `0.0.9` cut][spec-030-d13].

### Justification

[`docs/SPECS/NEXT.md`][next] Step 6 requires this Decision whenever another non-Done card shares the target's patch version: the bump belongs to the joint cut, so no single card's slice races its siblings for it.

### Alternatives considered (and rejected)

**Bump the version in this card's Slice 5.** Rejected: would race the sibling cards for the same bump and promote a release heading before the cohort is cut.

## Decision 14 — `connection.py` module and the public-export gate

Spec: [Decision 14 — `connection.py` module and the public-export gate][spec-030-d14].

### Justification

A flat module matches `list_field.py`; exporting in the slice that proves the export (Slice 4) is cleaner than a two-step export-then-document split; the Root-Node surface is its own flat `relay.py`.

### Alternatives considered (and rejected)

- **Export in Slice 5.** Rejected: conflicts with Slice 4's live consumer-facing usage; public export and the live proof should land together.
- **A `relay/` subpackage now.** Rejected: premature for one factory + connection types; the Root-Node surface is the separate flat `relay.py`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[start]: ../../../START.md

<!-- docs/ -->
[glossary-djangolistfield]: ../../GLOSSARY.md#djangolistfield
[glossary-djangonodefield]: ../../GLOSSARY.md#djangonodefield
[glossary-relatedfilter]: ../../GLOSSARY.md#relatedfilter
[glossary-relatedorder]: ../../GLOSSARY.md#relatedorder
[glossary-syncmisuseerror]: ../../GLOSSARY.md#syncmisuseerror

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-029]: ../spec-029-consumer_dx_cleanup-0_0_9.md
[spec-030]: ../spec-030-connection_field-0_0_9.md
[spec-030-d1]: ../spec-030-connection_field-0_0_9.md#decision-1--spec-filename-and-canonical-naming
[spec-030-d10]: ../spec-030-connection_field-0_0_9.md#decision-10--sync--async-resolver-paths-reuse-the-shared-visibility-helpers
[spec-030-d11]: ../spec-030-connection_field-0_0_9.md#decision-11--the-connection-field-owns-its-optimizer-cooperation-point
[spec-030-d12]: ../spec-030-connection_field-0_0_9.md#decision-12--no-auto-trigger-of-finalize_django_types-for-009
[spec-030-d13]: ../spec-030-connection_field-0_0_9.md#decision-13--version-bumps-are-owned-by-the-joint-009-cut
[spec-030-d14]: ../spec-030-connection_field-0_0_9.md#decision-14--connectionpy-module-and-the-public-export-gate
[spec-030-d2]: ../spec-030-connection_field-0_0_9.md#decision-2--card-scope-boundary-against-the-sibling-relay-cards
[spec-030-d3]: ../spec-030-connection_field-0_0_9.md#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard
[spec-030-d4]: ../spec-030-connection_field-0_0_9.md#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes
[spec-030-d5]: ../spec-030-connection_field-0_0_9.md#decision-5--factory-function-mechanism-meta-only-derivation
[spec-030-d6]: ../spec-030-connection_field-0_0_9.md#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature
[spec-030-d7]: ../spec-030-connection_field-0_0_9.md#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer
[spec-030-d8]: ../spec-030-connection_field-0_0_9.md#decision-8--metaconnection-opt-in-key-stored-on-the-definition
[spec-030-d9]: ../spec-030-connection_field-0_0_9.md#decision-9--cursor-encoding-delegated-to-strawberry-keyset-cursors-are-a-separate-opt-in

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
