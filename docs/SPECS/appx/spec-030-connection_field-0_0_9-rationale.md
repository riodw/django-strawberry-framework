# Rationale companion: spec-030 (`DjangoConnectionField` — the Relay connection field)

Companion to [`docs/SPECS/spec-030-connection_field-0_0_9.md`][spec-030]. It carries that spec's **deliberative layer** and nothing else: the three-revision review history that produced the contract, every Decision's justification, every alternative a Decision rejected and why it lost, and the risk / open-question deliberation that settled the card's design questions. The spec carries the contract; this file carries how the contract was arrived at. Neither duplicates the other — the text here **left** the spec.

Read this when checking a finished implementation against the reasoning that produced it, or before re-opening a settled question. Worker 2 never reads it ([`docs/builder/BUILD.md`][build-md] `### Who reads it, and when`).

**How later passes append to this file.** Each Decision below carries a `### Changes this Decision underwent` section. A reconciliation pass that finds the spec stale against `HEAD` — a renamed symbol, a bound a later card removed, a claim the Decision may no longer make — appends a `**Post-ship:**` bullet there, naming the shipped behavior and the card that changed it. Findings belonging to no single Decision go under [Non-Decision deliberation](#non-decision-deliberation). Nothing needs restructuring to take an addition, and the corrections themselves always land in the spec, stated directly and without chronology.

## Provenance of this record

Created by pre-flight step 7 of the `030` residual-reconciliation cycle (recorded in `docs/builder/bld-rationale-030.md`). `spec-030` shipped in `0.0.9` with a `-terms.csv` companion and no `-rationale.md` sibling — the only archived spec from `001` through `029` missing one; this file closes that gap. Nothing in it is new reasoning: every passage below was cut from the spec in the same pass that created this file.

Measured against the spec on disk before the move (138,023 bytes, 790 lines), three routes carried text out:

- **The whole `Revision history (kept inline so the spec is self-contained):` block** — its preamble plus three `Revision N` entries, 16 lines. Reproduced under [Revision history](#revision-history) below, byte-for-byte except for the preamble line (deleted, not moved — its claim that the history is kept inline is exactly what this move made untrue) and two in-page anchors repointed at the spec (see below).
- **14 `Justification:` blocks and 14 `Alternatives considered (and rejected):` blocks**, one pair under each of Decisions 1-14, carrying 25 justification bullets or paragraphs and 29 rejected alternatives. Reproduced byte-for-byte under each Decision's heading; the 28 label lines became `###` headings here.
- **The body of `## Risks and open questions`** — its preamble plus 6 items, each written as a preferred-answer / fallback pair. That shape is a build-time deliberation instrument, not a contract, so the whole body moved and the spec keeps the heading, a pointer, and the one rule that outlives the build (see [Risks and open questions](#risks-and-open-questions) below).

Those three routes account for **23,742** bytes of the pre-move spec (7,328 + 12,775 + 3,639). The spec on disk now measures **119,551** bytes over 698 lines, **18,472** below its pre-move size; the difference is the framing the move put back — the header pointer, fourteen per-Decision `Rationale companion —` pointers, the surviving Risks rule, and sixteen new link definitions, **5,745** bytes in total — set against a further **475** bytes the move removed outright (below).

A fourth, much smaller route carried out **chronology framing embedded in surviving contract prose**: ten `(the review round's PN)` / `per the review round's PN` parentheticals and two whole chronology sentences (`rev1's "Slice 3 needs no source change" was therefore false` under Decision 11, and `rev1 deferred the export to Slice 5 (docs), which conflicted …` under Decision 14). The parentheticals are pure provenance — the sentences around them state the contract and are unaffected — and both sentences are recorded under their Decision's `### Changes this Decision underwent`. One chronology reference was deliberately **kept** in the spec: Decision 11's `P1-B` label, because live source, live tests, and a sibling spec's companion all cite it by that name; it now points here instead of at a review round the spec no longer describes. The `[next]: NEXT.md` link definition went with this route: after the move, [`docs/SPECS/NEXT.md`][next] is cited only from text that now lives here, so the definition was orphaned in the spec and is defined in this file instead.

**Not byte-verbatim in two respects.** Two lines of the revision history carried in-page anchors naming spec sections this file does not have — `#test-plan` and `#doc-updates`. Both were repointed at the spec through reference-style links rather than left to dangle. The `#decision-N--…` anchors and `#risks-and-open-questions` were left as they were: this file carries headings with exactly those slugs, so they resolve locally, which is where a reader of a moved sentence wants to land.

**Four finding labels are cited from live code and tests but appear nowhere in the spec's revision history.** `P1-B` (once, in Decision 11's forward-design paragraph), `P3a`, `P3b`, and an `Open Question` about direct `relay.Node` inheritance are cited from [`django_strawberry_framework/orders/sets.py`][orders-sets], [`tests/test_connection.py`][test-connection], [`tests/test_registry.py`][test-registry], [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library], and [`spec-028-orders-0_0_8-rationale.md`][spec-028-rationale]. The spec records three revisions and one finding round, so at least one review round of this spec went unrecorded. Each label is now recorded under the Decision whose contract it belongs to, which is where those citations resolve; the underlying behavior is shipped and tested in every case.

**Not corrected here.** This pass moved text; it did not reconcile the spec against `HEAD`. Several Decisions describe a surface later cards renamed, relocated, or widened, and at least one bound Decision 11 asserts for `0.0.9` was closed by [`DONE-033-0.0.9`][kanban]. Those belong to the owning slices of the `030` cycle, and their corrections land in the spec with a `**Post-ship:**` record under the relevant Decision here.

## Revision history

Three revisions produced the contract, of which one (Revision 2) was a finding round. The block below is the spec's own, verbatim; every finding in it is also recorded under the Decision it changed, in that Decision's `### Changes this Decision underwent` section, or — when it belongs to no Decision — under [Non-Decision deliberation](#non-decision-deliberation). The chronology is what a reviewer of a Decision's history needs; the per-Decision record is what a reviewer of the implementation needs, so both are kept and the duplication is deliberate and bounded to this one block.

- **Revision 1** — initial draft authored from the [`WIP-ALPHA-030-0.0.9`][kanban] card body via the [`docs/SPECS/NEXT.md`][next] flow. Pinned the canonical spec filename, the card-scope boundary against the three sibling `0.0.9` Relay cards, building on Strawberry's native [`relay.ListConnection`][strawberry-relay] / `relay.connection()`, the [`DjangoConnection`][glossary-djangoconnection]`[T]` return alias, the factory-function mechanism, sidecar-derived arguments, the visibility→filter→order→slice composition order, the `Meta.connection` opt-in key, opaque-cursor delegation, sync/async paths, optimizer cooperation, the no-auto-finalize posture, the joint-cut version boundary, and the `connection.py` module location.
- **Revision 2** — first feedback pass (review of rev1), source-verified against the locked Strawberry `0.316.0`. Four P1 (foundational) findings reshaped the mechanism; four P2 and three P3 findings tightened the rest.
  - **P1 — the optimizer plan cannot ride the existing root-gated hook.** [`DjangoOptimizerExtension.resolve`][optimizer-extension] optimizes only when the resolved value is a Django `QuerySet`, but Strawberry's [`ConnectionExtension`][strawberry-relay] returns a connection object, so the schema middleware never sees the pre-slice queryset — rev1's "Slice 3 needs no source change" was false. [Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point) rewritten: the plan-application logic is extracted from `DjangoOptimizerExtension._optimize` into a reusable internal helper that takes `target_type` / `target_model` directly (NOT inferred from `info.return_type`, which is the connection type), and the connection field's own resolver calls it before Strawberry's slicing. The helper extraction is **source work in Slice 2**; Slice 3 verifies the cooperation and bounds the connection-aware gap. Problem statement, Current state, Goals, Implementation plan, Slice checklist, Test plan, and the DoD all updated.
  - **P1 — a single generic `DjangoConnection[T]` cannot conditionally omit `totalCount`.** A static Strawberry class cannot make one field appear/disappear per generic specialization. [Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes) rewritten: `DjangoConnection[T]` is the base (no `totalCount`); a **per-target concrete** connection class (cached, named `<TypeName>Connection`) is generated and carries `totalCount` when the type opts in via `Meta.connection`. `Meta.connection` is now **stored on [`DjangoTypeDefinition`][definition]** (not merely validated), so [`django_strawberry_framework/types/definition.py`][definition] joins the implementation plan. Dropping the per-field `total_count=` override ([Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation), per P3) collapses the shape space to one connection type per node type, which removes the naming/caching ambiguity.
  - **P1 — Strawberry 0.316.0 does not reject `first` + `last`.** `SliceMetadata.from_arguments` applies both without a mutual-exclusivity guard. The card body wants `first` + `last` illegal, so [Decision 3](#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard) now has the package implement the guard in the connection class's `resolve_connection` override (which receives the pagination args), raising a `GraphQLError`; the claim that Strawberry owns it is removed everywhere.
  - **P1 — sidecar argument generation needs an explicit Strawberry mechanism.** [`filter_input_type`][glossary-filter_input_type] / [`order_input_type`][glossary-order_input_type] return annotations + write ledgers; they do not add arguments to a field. [Decision 6](#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature) pins the mechanism: a resolver with a **synthesized `__signature__`** carrying `filter` / `order_by` params with the helper annotations (the route Strawberry's native resolver-argument derivation already uses for the hand-written filter/order resolvers), with a custom `FieldExtension.apply(...)` appending `StrawberryArgument`s as the documented fallback.
  - **P2 — `totalCount` selection-gated and carried on the connection instance.** [Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes) now counts only when the `totalCount` field is selected (not on every query against an opted-in type) and attaches the count to the connection **instance** via the `resolve_connection` override (not an `info.context` path-string stash). A two-alias-different-filters test and a `totalCount`-omitted no-count test join the [Test plan][spec-030-test-plan].
  - **P2 — cursor pagination needs a deterministic default ordering.** [Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer) adds a default-ordering step: after visibility/filter/order, if the queryset is still unordered, apply `order_by(model._meta.pk.attname)`; a supplied `orderBy` or a model `Meta.ordering` is preserved.
  - **P2 — the consumer `resolver=` contract is now explicit.** [Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer): `Manager` → coerced to `QuerySet`; `QuerySet` → full pipeline; a non-queryset iterable may be paginated only when no `filter:` / `orderBy:` input is supplied, and supplying sidecar input against a non-queryset raises a clear `GraphQLError`.
  - **P2 — the public-export gate is reconciled with the live example slice.** [Decision 14](#decision-14--connectionpy-module-and-the-public-export-gate): the public export of `DjangoConnectionField` / `DjangoConnection` lands in **Slice 4**, the same functional slice as the live fakeshop usage, so the example imports from the public surface, not a temporary submodule path.
  - **P3 — `filters=` / `order=` / `total_count=` field overrides dropped for `0.0.9`.** [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation) ships Meta-only derivation; the factory's only keyword arguments are `resolver=` and the standard field-metadata pass-throughs.
  - **P3 — the opaque-cursor edge case softened.** It no longer claims an `after` cursor "falls through to the next existing row"; it states the query does not error but offset-cursor stability under concurrent inserts/deletes is not guaranteed until the stable-cursor work ([Decision 9](#decision-9--cursor-encoding-delegated-to-strawberry-keyset-cursors-are-a-separate-opt-in)).
  - **P3 — spec hygiene.** The [`ConfigurationError`][glossary-configurationerror] Key-glossary bullet no longer lists `first` + `last` (a query-runtime path, not a construction error); the unused `[glossary-metaconnection]` link def is removed (the heading does not exist yet); Slice 5's [Doc updates][spec-030-doc-updates] names the `CHANGELOG.md` edit explicitly so the maintainer prompt does not infer permission from a standing document.
- **Revision 3** — glossary anchoring pass. Added [`Meta.connection`][glossary-metaconnection] to [`docs/GLOSSARY.md`][glossary] as `planned for 0.0.9`, then added it to the companion terms CSV and this spec's key-reference map so the net-new public `Meta` key is available to implementers before Slice 1 starts.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-030-d1].

### Justification (moved from the spec)

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `DONE-030-0.0.9`, so `<NNN>` is `030` and `<0_0_X>` is `0_0_9`.
- The topic slug is `connection_field` — it names the card's subject (the `DjangoConnectionField` primitive) in snake_case, parallel to the [`DjangoListField`][glossary-djangolistfield] sibling's `spec-020-list_field-0_0_7.md`.

### Alternatives considered (and rejected)

- **Honor the card body verbatim with `docs/spec-connection.md`.** Rejected: unnumbered against its card, breaks the structured-filename convention, would not sort alongside its siblings.
- **Topic slug `connection` or `relay_connection`.** Rejected: `connection` is too terse to disambiguate from the future `relay.py` Root-Node work; `relay_connection` over-claims the Relay-Root surface this card scopes out ([Decision 2](#decision-2--card-scope-boundary-against-the-sibling-relay-cards)).

### Changes this Decision underwent

- **Revision 1** pinned the canonical filename against the card body's unnumbered `docs/spec-connection.md`. Nothing later reopened it.
- **Post-ship: the Decision's subject was the naming convention, but the sentence carrying it asserted a location.** It read "The spec file lives at `docs/spec-030-connection_field-0_0_9.md`" — a present-tense path claim that the [`AGENTS.md`][agents] archival convention falsified the moment a later spec's author ran the [`docs/SPECS/NEXT.md`][next] archival step and moved every prior spec to `docs/SPECS/` with its `-terms.csv` / `-rationale.md` companions to `docs/SPECS/appx/`. The convention half — structured `spec-<NNN>-<topic>-<0_0_X>` over the card body's unnumbered `docs/spec-connection.md` — was never in doubt and still reads true, which is why the repair is a subject correction rather than a deletion: the Decision now pins the canonical *filename* and states the archived location as the answer, so the reader is never asked to reconstruct where the file is from a chronology. The `docs/spec-connection.md` contrast is untouched, because the card body's own wording is what the Decision exists to overrule.

## Decision 2 — Card-scope boundary against the sibling Relay cards

Spec: [Decision 2 — Card-scope boundary against the sibling Relay cards][spec-030-d2].

### Justification (moved from the spec)

the card body and `032`'s body both name this dependency direction; pinning the boundary keeps the spec scoped to what `030` ships and prevents pulling `032`'s eight-goal umbrella into one card.

### Alternatives considered (and rejected)

**Fold the Full Relay story into this spec.** Rejected: `032` is an L-XL eight-goal card with its own spec; one spec per WIP card is the [`docs/SPECS/NEXT.md`][next] flow, and the connection field is independently shippable.

### Changes this Decision underwent

- **Revision 1** drew the four-card boundary. No later revision moved it; the three sibling cards all shipped inside the same `0.0.9` line.

## Decision 3 — Build on Strawberry's native Relay machinery, but own the `first` + `last` guard

Spec: [Decision 3 — Build on Strawberry's native Relay machinery, but own the `first` + `last` guard][spec-030-d3].

### Justification (moved from the spec)

- [`START.md`][start]'s rule: "Strawberry is the engine." Re-implementing cursor math would duplicate correct engine behavior and drift from the Relay spec. The package's value is the Django-aware queryset pipeline and the Meta-driven argument generation, not cursor arithmetic.
- The one place Strawberry's behavior diverges from the card's contract — the missing `first` + `last` guard — is surfaced honestly and implemented in the one method that receives the pagination args, rather than left as a false claim that the engine handles it.

### Alternatives considered (and rejected)

- **Claim Strawberry rejects `first` + `last` (rev1).** Rejected: false against the locked `0.316.0` source; a spec must not rely on absent upstream behavior.
- **Allow `first` + `last` (drop the guard).** Rejected: the card body explicitly wants it rejected; combining them is a client error worth surfacing.
- **Hand-roll the whole cursor / pageInfo math.** Rejected: re-implements engine behavior and balloons the test surface.

### Changes this Decision underwent

- **Revision 2 P1 (foundational) — Strawberry `0.316.0` does not reject `first` + `last`.** rev1 claimed the engine owned the guard. `SliceMetadata.from_arguments` applies `first`, then `last`, validating negatives and `max_results` but never mutual exclusivity, so the claim was false against the locked source. The Decision was rewritten to have the package implement the guard in the [`DjangoConnection`][glossary-djangoconnection] base's `resolve_connection` override, raising a `GraphQLError`, and every sentence asserting Strawberry owned it was removed.
- **Claim this Decision may no longer make: that Strawberry owns the `first` + `last` guard.** Retracted by the finding above; the package owns it.
- **Post-ship: the guard's condition is "supplied", not "non-`None`".** As written the Decision said "when both `first` and `last` are non-`None`". An omitted Relay argument can reach `resolve_connection` as `strawberry.UNSET` rather than `None`, and under the original spelling `UNSET` counted as supplied, so a query passing only `first` could trip the mutual-exclusivity error. `django_strawberry_framework/connection.py::_guard_first_and_last` treats both sentinels as unsupplied and `tests/test_connection.py::test_first_and_last_guard_with_unset` pins it; the Decision now states the condition that way. The guard's home, its error type, and its ownership are unchanged.
- **Post-ship: "otherwise delegate to `super().resolve_connection(...)`" is no longer the whole tail.** The override is now the single head for every connection shape the package serves — it resolves the request's page-size ceiling, checks the cooperative deadline, primes `info.selected_fields`, and then dispatches by source shape, of which the ordinary offset queryset is the one that reaches `ListConnection`. The guard still runs first, before anything reads `info`, which is the property the Decision cares about; the Decision now says "goes on to the override's source dispatch, whose ordinary offset path is `super().resolve_connection(...)`" instead of implying a single unconditional delegation. The extra head work belongs to the resource-policy and connection-optimizer cards, not here, so the Decision names the dispatch without describing them.

## Decision 4 — `DjangoConnection[T]` base plus per-target concrete connection classes

Spec: [Decision 4 — `DjangoConnection[T]` base plus per-target concrete connection classes][spec-030-d4].

### Justification (moved from the spec)

- Concrete-per-shape connection classes are exactly `strawberry-django`'s `ListConnectionWithTotalCount` pattern — the proven place to add `total_count` and override `resolve_connection` without disturbing cursor mechanics.
- Selection-gating avoids an unconditional count query when a client selects only `edges` / `pageInfo`; instance-attachment avoids the fragility of context keying under aliasing.

### Alternatives considered (and rejected)

- **One generic `DjangoConnection[T]` with a conditional field.** Rejected: a static Strawberry class cannot toggle a field per specialization.
- **Always-present `totalCount`, count execution opt-in.** Rejected: the card specifies the field itself is opt-in; advertising `totalCount` on a type that never wants it pollutes the schema.
- **Stashing the count on `info.context` keyed by path-string.** Rejected: fragile under aliasing; the connection instance is the natural carrier.

### Changes this Decision underwent

- **Revision 2 P1 — a single generic `DjangoConnection[T]` cannot conditionally omit `totalCount`.** A static Strawberry class cannot make one field appear or disappear per generic specialization, so rev1's one-generic-type shape was impossible. The Decision was rewritten into the two-tier base-plus-per-target-concrete-class design, which also pulled [`django_strawberry_framework/types/definition.py`][definition] into the implementation plan (the opt-in has to be readable from the definition — see [Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition)).
- **Revision 2 P2 — `totalCount` is selection-gated and carried on the connection instance.** rev1 counted on every query against an opted-in type and considered an `info.context` path-string stash. The Decision now counts only when the `totalCount` field is selected and attaches the count to the connection instance, which makes two aliases of one connection with different `filter:` values carry independent counts with no keying logic. A two-alias-different-filters test and a `totalCount`-omitted no-count test joined the [Test plan][spec-030-test-plan] with it.
- **Revision 2 P3, inherited from [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation).** Dropping the per-field `total_count=` override collapsed the shape space to one connection type per node type, which is what lets the cache be keyed on `target_type` alone.
- **Post-ship: the bare `DjangoConnection[target_type]` alias path was removed; every node type now gets a generated concrete class.** As written, a type that did not opt into `totalCount` was handed the generic alias directly and only an opted-in type got a generated `<TypeName>Connection`. That shape had a defect the unit tests could not see: Strawberry's schema-build generic specialization copies a generic alias into a plain specialized class whose `resolve_connection` is `ListConnection`'s, so the package's override — and with it the [Decision 3](#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard) `first` + `last` guard — never ran for a non-opted type through the schema, while running fine when the classmethod was called directly. [`DONE-032-0.0.9`][kanban] closed it by making the bare path concrete too, so `_connection_type_for` always generates and the `Meta.connection` opt-in controls only whether the `total_count` members are added. The two shapes keep one SDL difference: the non-opted class inherits the base's description (read from the parent's strawberry definition, never re-spelled as a package literal) and the opted one ships description-less — shipped surface, pinned by `tests/test_connection.py::test_total_count_present_only_when_opted_in`. Both branches are pinned as concrete by `test_connection_type_for_returns_concrete_subclass_without_opt_in` and `..._when_total_count_false`. The Decision now states the always-concrete contract and why the alias may not be used; the Slice-1 checklist, the User-facing API paragraph, the Test plan, and DoD item 2 were reconciled with it.
- **Post-ship: the opted variant does not re-declare `resolve_connection`.** As written it "overrides `resolve_connection` to (a)…(e)". It instead flips a `ClassVar` flag the base's single override reads, so the upstream-pinned signature and the whole dispatch body are spelled once and the variant cannot drift from either the base or `ListConnection`. Same observable contract, one fewer copy of a signature this spec's own [Risks and open questions](#risks-and-open-questions) rule says can move upstream.
- **Post-ship: `.count()` / `.acount()` is the offset path's mechanism, not the only one.** The Decision's "(c) count the post-filter pre-slice `nodes` queryset (sync `.count()` / async `.acount()`)" is exact for an ordinary offset queryset and is what the field still does there. Two later sources supply the same post-filter pre-slice cardinality without a second query: an optimizer-planned window carries a conditional count annotation ([`DONE-033-0.0.9`][kanban]), and a keyset page counts through the package's own slicer. The counted VALUE and the selection gate are unchanged — only the mechanism forked — so the Decision now names the cardinality as the contract and `.count()` / `.acount()` as the offset path's means.
- **Post-ship: the generated class is named from the node type's canonical GraphQL type name.** The Decision said `<TypeName>Connection` without saying which name. Two `DjangoType` classes may share a Python `__name__` while declaring distinct `Meta.name` values, and naming from `__name__` generates two classes with one SDL type name, which Strawberry collapses — cross-wiring both fields' `edges` and node types. The generator reads `definition.graphql_type_name`, the same surface-name source the finalizer and the filter / order input types use; `tests/test_connection.py::test_generated_connection_name_uses_graphql_type_name_not_python_name` pins it.
- **Post-ship: the selection gate is directive-resolved, and the Decision never said so.** "Counts only when `totalCount` is selected" was written against the ordinary case — the field present or absent in the document. It is not the whole gate. Strawberry's `convert_selections` carries a `@skip` / `@include`-annotated field into `info.selected_fields` **with its already-resolved directive arguments** rather than dropping the node, so a predicate that only looked for the name would answer `True` for `totalCount @skip(if: true)`, issue a `COUNT`, and — on a non-`QuerySet` consumer-resolver return — trip [Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer)'s guard for a field the client had excluded. The shipped predicate applies the include gate itself: [`connection.py`][connection]`::_total_count_requested` delegates to `optimizer/selections.py::connection_total_count_selected`, whose walk is gated on `should_include` exactly as its sibling converted-selection walks are, so the resolve-time gate and the plan-time `connection_count_required` predicate cannot drift. The behavior arrived in the `0.0.9` review round that the spec's revision history does not record (the same gap [Provenance of this record](#provenance-of-this-record) names for four finding labels), which is why no revision entry carries it and why it reached this cycle as a shipped contract with no spec sentence. Four spec sites now state it: the Decision's clause (b), the `## Edge cases` `totalCount`-not-selected bullet, Slice 4's checklist sub-check (d), and a new Slice-4 [Test plan][spec-030-test-plan] row for `test_genre_connection_total_count_skip_include_no_count`. **The claim this Decision may no longer make** is that field presence in the document is what the gate reads.
- **Post-ship: the count-mechanism fork was stated in three of its five homes and not in the other two.** The bullet above records that `.count()` / `.acount()` became the offset path's means rather than the whole contract, and the reconciliation reached this Decision's clause (c), the Slice-1 checklist sub-bullet, and [Definition of done][spec-030-dod] item 2 — but not the two `## User-facing API` sites, which kept the unconditional "it runs `qs.count()` (sync) / `qs.acount()` (async)". That is the spec's **designed** redundancy failing in the one direction that matters: a contract legitimately restated in five places is only a contract while all five say the same thing, and no single-region pass can see the mismatch because each pass sees its own region. The prose site now names the cardinality as the contract and the two methods as the offset path's means. The fenced pipeline sketch beside it keeps `qs.count()` deliberately: every step in that block is spelled for one concrete sync-offset walkthrough (`GenreFilter.apply_sync`, `GenreOrder.apply_sync`), so `.count()` is correct for the path it illustrates rather than a claim about all paths.
- **Post-ship: the Slice-4 no-count row's "where observable" hedge was falsified by the test that discharged it.** The [Test plan][spec-030-test-plan] row for `test_genre_connection_total_count_omitted_no_count` asked for "correct edges (and, where observable, runs no count query)" — a hedge that would have accepted a wire-shape-only assertion, which is precisely the non-distinguishing shape [`docs/builder/BUILD.md`][build-md] `### Query-shape tests must pin the load-bearing property, not observability` forbids. The shipped test pins the load-bearing property outright, asserting over `CaptureQueriesContext` that no `COUNT(` SQL is issued at all. The row now states that assertion, so the hedge cannot be read as licensing the weaker test, and it matches the unhedged `## Edge cases` twin it always sat beside.
- **`P3b`, a finding label the spec's revision history never recorded.** [`tests/test_registry.py`][test-registry] cites `spec-030-connection_field-0_0_9 P3b` for the connection-type cache's co-clear: `clear_connection_type_cache` is reached through a cycle-safe local import, and the registry's `clear()` skips the block rather than raising when [`connection.py`][connection] cannot be imported. The behavior is shipped and tested; only its provenance was missing, and this bullet is where the citation now resolves.

## Decision 5 — Factory-function mechanism, Meta-only derivation

Spec: [Decision 5 — Factory-function mechanism, Meta-only derivation][spec-030-d5].

### Justification (moved from the spec)

- Strawberry's class-body walk picks up the factory's return value like `relay.connection(...)`; the consumer writes `attr: Annotation = DjangoConnectionField(T)`, identical in shape to the shipped `DjangoListField(T)`.
- Meta-only derivation keeps the API minimal and avoids two ways to specify the same thing; it also removes the connection-type naming/caching ambiguity per-field overrides would create.

### Alternatives considered (and rejected)

- **Keep `filters=` / `order=` / `total_count=` overrides.** Rejected: per the review round's P3, they leave the API undecided and force per-field connection-type variants (naming/caching cost); `Meta`-driven is the borrow and the primary surface. If override demand surfaces later, it is an additive follow-up with its own validation / precedence / naming rules.
- **A `DjangoConnectionField` class (descriptor).** Rejected: diverges from the shipped `DjangoListField` factory shape for no gain.

### Changes this Decision underwent

- **Revision 2 P3 — `filters=` / `order=` / `total_count=` field overrides dropped for `0.0.9`.** rev1 carried all three as factory keyword arguments. They left the API undecided and would have forced per-field connection-type variants with their own naming and caching rules, so the Decision became Meta-only derivation: the factory's only keyword arguments are `resolver=` and the standard field-metadata pass-throughs.
- **An `Open Question` about direct `relay.Node` inheritance, resolved in favour of accepting both spellings.** [`tests/test_connection.py::test_connection_field_accepts_direct_relay_node_inheritance`][test-connection] cites `spec-030-connection_field-0_0_9` "Open Question: direct `relay.Node` inheritance", a heading the spec never carried. The answer is in the Decision body: the construction-time guard reuses the canonical `_is_relay_shaped` predicate, which ORs the `Meta.interfaces` disjunct with `issubclass(target_type, relay.Node)`, so `class Foo(DjangoType, relay.Node)` is accepted even though `definition.interfaces` is empty. A naive MRO-only check would not have been enough, because [`finalize_django_types()`][glossary-finalize_django_types] injects `relay.Node` into `__bases__` only after the factory has run.

## Decision 6 — Sidecar-derived arguments via a synthesized resolver signature

Spec: [Decision 6 — Sidecar-derived arguments via a synthesized resolver signature][spec-030-d6].

### Justification (moved from the spec)

- It reuses Strawberry's native resolver-argument derivation and the exact `filter_input_type` / `order_input_type` shapes the hand-written resolvers use, so a connection field and a hand-written resolver on the same type resolve to the *same* `<Type>FilterInputType` (Apollo-cache friendly) and inherit active-input gating, `check_*_permission` propagation, and [`RelatedFilter`][glossary-relatedfilter] / [`RelatedOrder`][glossary-relatedorder] visibility scoping unchanged.
- It needs no custom field-extension class for the common path — the resolver signature *is* the SDL contract.

### Alternatives considered (and rejected)

- **Rely on the helpers alone (rev1).** Rejected: they return annotations and write ledgers; nothing adds the arguments to the field.
- **A custom `FieldExtension.apply(...)` appending `StrawberryArgument`s.** Kept as the documented **fallback** if signature-derivation proves insufficient when composed with `relay.connection()`'s `ConnectionExtension` (e.g. if Strawberry does not merge resolver-signature args with the auto-added pagination args as expected): the extension's `apply` appends the `filter` / `order_by` `StrawberryArgument`s before field build, and its `resolve` pops them before the pipeline. Pinned in [Risks and open questions](#risks-and-open-questions).
- **Generate fresh per-connection-field input types.** Rejected: duplicate GraphQL input types per field, breaking Apollo cache reuse and the stable-name contract.

### Changes this Decision underwent

- **Revision 2 P1 — sidecar argument generation needs an explicit Strawberry mechanism.** rev1 leaned on [`filter_input_type`][glossary-filter_input_type] / [`order_input_type`][glossary-order_input_type] alone; they return annotations and write orphan-validation ledgers, and nothing in them adds an argument to a field. The Decision now pins the synthesized-`__signature__` mechanism, with a custom `FieldExtension.apply(...)` appending `StrawberryArgument`s kept as the documented fallback.
- **Post-ship: only one of the two replacement mechanism facts actually reached the spec.** The bullet below records that two went in "in its place". One did — that calling the helpers IS the ledger registration. The other, that both helpers are imported **at call time** rather than at module scope, was written down here and never written into the spec, so this file asserted a spec state the spec did not have. It is genuinely load-bearing rather than trivia: [`connection.py`][connection] is reached by a bare `import django_strawberry_framework` through the package `__init__`, so a module-level import of `filter_input_type` / `order_input_type` eagerly pulls in the `filters` / `orders` subpackages and breaks the lazy-subpackage contract those subpackages' own tests pin. A builder reading only the spec would write the module-level import. The spec's Slice-2 sub-bullet now carries it beside the registration fact. Worth keeping as a shape: **a companion bullet that says "the spec now states X" is a claim about another file**, and nothing in a per-Decision append discipline checks it.
- **Post-ship: the `FieldExtension.apply(...)` fallback was never taken, and the spec no longer carries it as a contingency.** Signature derivation composed with `relay.connection()` exactly as the Decision predicted: `connection.py::_synthesized_signature` builds the parameter list and `_build_connection_resolver` assigns `__signature__` / `__annotations__`, and `ConnectionExtension` forwards the non-pagination kwargs. The Slice-2 checklist sub-bullet ended in a parenthetical naming the fallback mechanism and pointing at [Risks and open questions](#risks-and-open-questions); a shipped contract may not read as a live contingency, so that parenthetical was deleted from the spec rather than reworded. The fallback survives here, in the rejected-alternatives list above, which is where a reader looking for "what if the signature had not been enough" should find it. Two mechanism details went into the spec in its place, both load-bearing for a reader modifying the field: calling the `filter_input_type` / `order_input_type` helpers to build the annotations IS the ledger registration (no separate `.add(...)` is wanted, and adding one would double-register), and the helpers are imported at call time rather than at module scope so a bare `import django_strawberry_framework` does not eagerly pull in the `filters` / `orders` subpackages.

## Decision 7 — Composition pipeline: visibility→filter→order→default-order→optimizer

Spec: [Decision 7 — Composition pipeline: visibility→filter→order→default-order→optimizer][spec-030-d7].

### Justification (moved from the spec)

- This is the card body's composition order, correct for three reasons: visibility must run first so a filter cannot match a parent through a child the visibility hook hides (the [`RelatedFilter`][glossary-relatedfilter] contract); the optimizer must plan the pre-slice queryset; and `totalCount` is the count of the post-filter, pre-pagination set.
- The deterministic-total-ordering step (the review round's P2, hardened by P1) prevents nondeterministic pages: Strawberry's `ListConnection` uses positional offset cursors, which are stable across requests ONLY over a unique total order. A bare `order_by("name")` (supplied `orderBy` or `Meta.ordering`) with duplicate names is not a total order — SQL leaves tied rows unspecified — so the step appends the pk as a terminal tiebreaker in every case except when the ordering already ends in a unique column. This is distinct from (and much smaller than) the deferred `Meta.cursor_field` keyset-cursor work ([Decision 9](#decision-9--cursor-encoding-delegated-to-strawberry-keyset-cursors-are-a-separate-opt-in)); it is a guaranteed total order, not a value-based cursor.
- The explicit consumer-resolver contract (the review round's P2) prevents a custom resolver from silently skipping the advertised Meta-driven behavior.

### Alternatives considered (and rejected)

- **Filter before visibility / order before filter / count after the slice.** Rejected for the same reasons rev1 gave (existence leak, wasted work, count == page size).
- **No default ordering (rely on the database's natural order).** Rejected: nondeterministic pages from an unordered plan.
- **Treat any consumer-resolver return as paginatable regardless of sidecar input.** Rejected: filter/order can only apply to querysets; silently ignoring sidecar input on a list would advertise behavior the field does not deliver.

### Changes this Decision underwent

- **Revision 2 P2 — cursor pagination needs a deterministic default ordering.** rev1's pipeline ended at filter and order, so an unordered `_initial_queryset` produced nondeterministic pages. A default-ordering step was added.
- **Revision 2 P1 hardened that step from a default order into a total order.** Applying `order_by(pk)` only to the fully-unordered case still left a supplied non-unique `orderBy` (or a non-unique model `Meta.ordering`) indexing an unstable sequence, because SQL leaves tied rows unspecified and Strawberry's `ListConnection` cursors are positional offsets. The step became: resolve the effective ordering (`qs.query.order_by`, or `model._meta.ordering` when that is empty-but-`ordered`) and append the pk as a terminal tiebreaker in every case except one already ending in a unique column.
- **Revision 2 P2 — the consumer `resolver=` contract became explicit.** Without it a custom resolver could silently skip the advertised Meta-driven behavior. `Manager` is coerced; a `QuerySet` receives the whole pipeline; a non-queryset iterable is paginatable only without sidecar input, and sidecar input against a non-queryset raises. The symmetric `totalCount`-against-a-non-queryset rule is the same reasoning applied to the count.
- **Post-ship: the pipeline's step-1, step-2 and step-5 symbols all moved, and step 2's move changed what the reuse GUARANTEES.** `types/relay.py::_initial_queryset` is now `utils/querysets.py::initial_queryset` and `_apply_get_queryset_sync` / `_apply_get_queryset_async` are now `utils/querysets.py::apply_type_visibility_sync` / `apply_type_visibility_async`. The rename is the visible half; the substantive half is that the visibility helpers stopped being a passthrough that calls the hook and became a **sealed-execution boundary** — the source and the hook's return are each rebuilt into a fresh framework-owned `QuerySet` from validated query state (shape, concrete and actual-base table, sealability, model-row, database alias), with fail-closed rejection of every non-sealable shape. So the Decision's word "reusing" now buys the connection field more than it did when the sentence was written: step 2's scope is an upper bound the later steps can only narrow, and a `get_queryset` that returns a widened queryset — or a type that shadows `all()` or the query chain to widen one — cannot broaden what the connection paginates or counts. The Decision understated its own contract, so the spec now states the guarantee rather than only the call. It is pinned on the connection surface specifically by `tests/test_connection.py::test_connection_hostile_hook_narrows_edges_and_total_count_sync` / `..._async`, `::test_connection_instance_shadowed_all_hook_is_sealed`, `::test_connection_query_chain_shadow_hook_is_sealed`, and the `::test_connection_resolver_manager_degrading_to_list_fails_closed` pair. Step 5's `_ends_in_unique_column` also moved: the canonical predicate is `optimizer/plans.py::ends_in_unique_column` and the tuple decision is `optimizer/plans.py::deterministic_order`, hoisted so the plan-time window order and this resolve-time order cannot disagree (the cursor-parity invariant); `connection.py` keeps the old private name as a deliberate re-export, so the citation was imprecise rather than broken.
- **Post-ship: the consumer-`resolver=` contract has a FOURTH rejection the spec never contracted — an already-sliced `QuerySet`.** `connection.py::_guard_source_not_pre_sliced`, called from `_prepare_pipeline_source` so the sync and async pipelines share it, raises a `GraphQLError` when the resolver returns `qs[:5]`. It is not a later card's surface: it came from a standalone bug-fix commit with no spec and no card, closing a defect in exactly the seam this Decision owns. Left unguarded, step 5's `order_by` leaked Django's raw `TypeError: Cannot reorder a query once a slice has been taken` at the GraphQL boundary. It fires regardless of `filter:` / `orderBy:` input, because the field reorders and re-slices on every request — which makes it a different shape from its two siblings: they reject an argument the source cannot honor, this one rejects the source itself. Recorded as a spec gap found by reading the shipped guards rather than by checking the contracted ones: a guard absent from the contract is the "was anything skipped?" question inverted, and nothing in the checklist could have surfaced it. The spec now carries it in the consumer-resolver contract, the User-facing-API contract list, [Error shapes][spec-030-error-shapes]' twin, and [Edge cases and constraints][spec-030-edge-cases], pinned by `tests/test_connection.py::test_consumer_resolver_pre_sliced_queryset_raises_clear_error`.
- **Post-ship: step 5's unique-terminal rule gained a NULL clause and a keyset branch.** "Already ends in a unique column" now reads "unique AND non-nullable": SQL `UNIQUE` permits multiple NULLs, so terminal ties among NULL rows are nondeterministic and a nullable unique column is not a total order — it still takes the pk. A relation path, an annotation alias, and any non-`F` expression are likewise treated as non-unique. Separately, a node type in keyset mode with no explicit `orderBy:` orders by its declared `Meta.cursor_field` instead, which beats a model `Meta.ordering` whose columns the keyset cursors do not encode; that ordering is finalization-validated to be a total order, so the pk-append does not apply to it. Both are narrowings of a rule the Decision stated too loosely, not changes of direction: the goal is still one unique total order per connection.
- **Post-ship: step 6 now names its symbol.** The step said "the extracted helper … using `target_type` / `target_model`"; it now names `optimizer/extension.py::apply_connection_optimization`, and the reason the model is passed rather than inferred moved to where it is decided ([Decision 11][spec-030-d11]).

## Decision 8 — `Meta.connection` opt-in key, stored on the definition

Spec: [Decision 8 — `Meta.connection` opt-in key, stored on the definition][spec-030-d8].

### Justification (moved from the spec)

- Net-new key whose feature ships in the same card — the [`spec-029`][spec-029] [Decision 6][spec-029] situation, so straight into `ALLOWED_META_KEYS`.
- A dict is forward-compatible: `032`'s Full Relay story extends `Meta.connection` with more sub-keys.
- Storing on the definition is required because the connection-type generation happens at field-construction / finalization time, away from the `Meta` shape; the definition is the canonical per-type record the rest of the package already reads.

### Alternatives considered (and rejected)

- **Validate `Meta.connection` but not store it (rev1).** Rejected: the connection-class generator has nowhere to read the opt-in from; re-parsing `Meta` later is fragile and diverges from how `filterset_class` / `orderset_class` are threaded.
- **A flat `Meta.total_count = True` boolean.** Rejected: not forward-compatible.
- **Always-on `totalCount`.** Rejected per [Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes).

### Changes this Decision underwent

- **Revision 2 P1 — `Meta.connection` is stored, not merely validated.** rev1 validated the key and discarded it, which left the connection-class generator with nowhere to read the opt-in from. The normalized value now lands on a `connection` slot on [`DjangoTypeDefinition`][definition], populated in `__init_subclass__` beside the `filterset_class` / `orderset_class` slots.
- **Post-ship: `_validate_connection` has four rejection paths, not three.** This Decision always listed all four as bullets — non-dict, unknown sub-key, non-bool `total_count`, non-Relay-Node type — but the Slice-1 checklist, the [Test plan][spec-030-test-plan], and DoD item 3 each enumerated only three, dropping the non-bool one. `tests/types/test_base.py::test_meta_connection_non_bool_total_count_raises` has pinned it since the slice landed, so this was a stale enumeration in three places rather than a missing guard. The Decision itself needed no change.
- **Post-ship: a fourth stale enumeration of the same four rejections survived the first fix, because it never used the word "three".** [Error shapes][spec-030-error-shapes]' `Meta.connection` bullet listed non-Relay-Node, non-dict, and unknown sub-key and stopped — three items, spelled as a list rather than counted. The pass that corrected the other three sites swept for the *number word* (`three` / `the three`), which is invisible to a site that simply enumerates one fewer member. The general shape is worth keeping: **an enumeration is a count claim with no number in it**, so a count-word sweep cannot establish its population — the population has to come from the shipped guard list read against each enumeration in turn. All four homes now carry all four rejections, and the number is stated at the Error-shapes site so the next sweep has a token to find.

## Decision 9 — Cursor encoding delegated to Strawberry; keyset cursors are a separate opt-in

Spec: [Decision 9 — Cursor encoding delegated to Strawberry; keyset cursors are a separate opt-in][spec-030-d9].

### Justification (moved from the spec)

opaque offset cursors are the Relay-spec-compliant default `ListConnection` ships; stable cursors are a meaningfully larger design routed to `BACKLOG.md` item 39 sub-feature 3 by both the `030` and `032` card bodies.

### Alternatives considered (and rejected)

**Ship `Meta.cursor_field` now.** Rejected: its own design space; not required for the foundational connection field.

### Changes this Decision underwent

- **Revision 2 P3 — the opaque-cursor edge case was softened.** rev1 claimed a stale `after` cursor "falls through to the next existing row". It does not: the query does not error, but offset cursors encode a position rather than a row identity, so stability under concurrent inserts or deletes is not guaranteed until the stable-cursor work lands. The false clause was deleted rather than reworded.
- **Claim this Decision may no longer make: that a stale `after` cursor falls through to the next existing row.** Retracted by the finding above. The only guarantee is no-error.
- **Post-ship: the deferral closed — `Meta.cursor_field` shipped, and this Decision's subject narrowed to the dispatch seam.** The deferral was a real `0.0.9` scope boundary: keyset cursors are their own design space (tuple-comparison seek planning, an authenticated-encrypted payload, an order fingerprint, a soft `cryptography` dependency, and a portable-column contract validated at finalization), and none of it was required for the foundational connection field. The `stable_cursor_field` work in `BACKLOG.md` item 39 sub-feature 3 later landed as `django_strawberry_framework/keyset.py`, adding `cursor_field` to `ALLOWED_META_KEYS` and a keyset branch to the connection base's dispatch. Two claims the Decision may no longer make follow: that `Meta.cursor_field` is out of scope for the package (it exists), and that stable cursors "live in `BACKLOG.md` item 39 sub-feature 3" (that item is discharged). What survives unchanged is the part that was always the contract — this card writes no cursor codec, and a node type declaring no `cursor_field` keeps Strawberry's opaque offset cursors byte-identically. The Decision now states the offset default, points the keyset half at `keyset.py`, and records that `connection.py` owns the dispatch seam rather than the codec. Its heading changed with it, from `Opaque cursor delegated to Strawberry; Meta.cursor_field deferred` to `Cursor encoding delegated to Strawberry; keyset cursors are a separate opt-in`; the eight in-page anchors and two link definitions naming the old slug were repointed in the same pass, all of them inside this file and the spec.
- **Post-ship: the concurrent-mutation edge case has a recourse now.** The `after:`-under-concurrent-inserts bullet said stability is not guaranteed "until the stable-cursor work". It is still not guaranteed **on the offset path**, and that is now a property of a choice rather than of the calendar: the bullet names `Meta.cursor_field` as the recourse instead of pointing at unshipped work.

## Decision 10 — Sync + async resolver paths reuse the shared visibility helpers

Spec: [Decision 10 — Sync + async resolver paths reuse the shared visibility helpers][spec-030-d10].

### Justification (moved from the spec)

the Relay foundation already solved sync/async `get_queryset` dispatch and the sync-meets-async misuse; reusing those helpers keeps one source of truth and inherits [`SyncMisuseError`][glossary-syncmisuseerror]. The async `totalCount` count uses `.acount()` on the async path.

### Alternatives considered (and rejected)

**Sync-only connection resolver.** Rejected: both upstreams and the rest of this package support async.

### Changes this Decision underwent

- **Revision 1** set the reuse posture. The dispatch-shape paragraph in the Decision body — the connection field is dispatch-frozen at build time rather than per call, because `ConnectionExtension.resolve` hands the inner resolver's return to `resolve_connection` without awaiting it — is a mechanism a builder must know to implement the field correctly, so it stayed in the spec.
- **Post-ship: the dispatch freeze and its `SyncMisuseError` consequence are exactly what shipped, verified in both directions.** `connection.py::_build_connection_resolver` branches once on `is_async_callable(resolver)`: the async-consumer branch is an `async def` running `_pipeline_async`; the default field, a plain `def` resolver, and a declared async-generator resolver share one sync `def` running `_pipeline_sync`. So the default branch's async-`get_queryset` refusal holds under `await schema.execute` as well as under `execute_sync` — the branch was chosen at construction and the execution mode cannot revisit it. That second half was the testable claim worth checking rather than assuming; `tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse` pins it (and asserts `result.data is None`, so an async pipeline serving the seeded row would fail the row), alongside `::test_sync_context_async_get_queryset_raises_sync_misuse` for the sync-execution case.
- **Post-ship: the heading no longer says "Relay-foundation helpers", and the sync branch carries two guards the freeze makes necessary.** The helpers left `types/relay.py` for `utils/querysets.py`, where they are the shared sealed boundary four recomposing read surfaces use — the connection field, the list field, the Relay node defaults, and the permissions cascade — so "Relay-foundation" had become provenance rather than description. The heading became `Sync + async resolver paths reuse the shared visibility helpers`; the two in-page anchors, the two link definitions, and this file's own heading and back-pointer were repointed in the same pass, and a tree-wide sweep confirmed the old slug was cited from nowhere outside the spec/companion pair. The guards: a plain `def` resolver returning an awaitable is rejected before normalization, and one returning an async-only iterable in a sync execution context raises [`SyncMisuseError`][glossary-syncmisuseerror] rather than reaching Strawberry's sync slicer, whose failure mode there is a blank internal `AssertionError`. Both exist *because* the branch cannot be re-decided per call, which makes them part of this Decision's contract rather than incidental hardening — the spec now says so.

## Decision 11 — The connection field owns its optimizer cooperation point

Spec: [Decision 11 — The connection field owns its optimizer cooperation point][spec-030-d11].

### Justification (moved from the spec)

- It is the only correct way to optimize a connection field given Strawberry's pipeline: the field must apply the plan before the connection result hides the queryset.
- Passing `target_type` / `target_model` explicitly sidesteps the `info.return_type`-is-the-connection-type problem the review identified.
- Extracting a shared helper (rather than duplicating `_optimize`) keeps the middleware and the connection field on one plan-application implementation, so the connection-aware walker work in `033` improves both.

### Alternatives considered (and rejected)

- **Rely on the existing root-gated middleware (rev1).** Rejected: it never sees the queryset behind the connection result.
- **Block the connection field on `033`.** Rejected: a root connection field is useful today (filter / order / cursor pagination / `totalCount` all work) and the optimizer cooperation seam is wired and running — `033` is a documented walker-awareness follow-up that fills the (currently empty) plan with no `connection.py` change, not a blocker.
- **Infer the model from `info.return_type`.** Rejected: the return type is the connection type; the helper must be told the node type / model.

### Changes this Decision underwent

- **Revision 2 P1 — the optimizer plan cannot ride the existing root-gated hook.** rev1 asserted "Slice 3 needs no source change". [`DjangoOptimizerExtension.resolve`][optimizer-extension] optimizes only when the resolved value is a Django `QuerySet`, and Strawberry's `ConnectionExtension` returns a connection object, so the schema middleware never sees the pre-slice queryset. The Decision was rewritten around an extracted, reusable plan-application helper taking `target_type` / `target_model` directly, called by the connection field's own resolver before Strawberry's slicing. The helper extraction became source work in Slice 2, and the Problem statement, Current state, Goals, Implementation plan, Slice checklist, [Test plan][spec-030-test-plan] and Definition of done were all updated with it.
- **Claim this Decision may no longer make: that Slice 3 needs no source change.** Retracted by the finding above.
- **`P1-B` — the aggregate-ordering interaction, and the [`spec-028`][spec-028] claim it retired.** This card's review round found that [`OrderSet`][glossary-orderset] orders a to-many path through a `Min` / `Max` aggregate annotation so the parent row is not multiplied. Two things came out of it: the forward design constraint for [`DONE-033-0.0.9`][kanban] that survives in the spec's Decision body (a connection-aware walker must not plan a relation in a way that reintroduces the multiplication, and any scalar projection alongside an aggregate-ordered queryset must stay functionally dependent on the grouped parent pk on strict backends), and the retirement of `spec-028`'s reverse-FK denormalized-multiplicity claim, recorded in [`spec-028-orders-0_0_8-rationale.md`][spec-028-rationale]. The label `P1-B` is cited from live source and tests — [`django_strawberry_framework/orders/sets.py`][orders-sets], [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library], and that `spec-028` companion — so it is carried here verbatim; the spec's revision history never recorded it.
- **`P3a`, another unrecorded finding label.** [`tests/test_connection.py::test_apply_connection_optimization_short_circuits_without_optimizer`][test-connection] cites `spec-030-connection_field-0_0_9 P3a` for the cooperation point's short-circuit: with no optimizer installed the `_active_optimizer` `ContextVar` is `None` and the helper returns the queryset unchanged rather than fabricating a throwaway optimizer to self-optimize. Shipped and tested; recorded here so the citation resolves.
- **Post-ship: the extraction landed as a CORE plus an entry point, and the spec described only one of them.** The Decision said "a reusable internal helper … that takes `target_type` / `target_model` **directly**", and the Slice-2 checklist and DoD item 5 repeated it. Two symbols exist at HEAD, and the sentence is true of one each: [`DjangoOptimizerExtension.apply_to`][optimizer-extension]`(target_type, target_model, queryset, info)` is the shared plan-build-and-apply core taking both directly, and [`apply_connection_optimization`][optimizer-extension]`(target_type, queryset, info)` is the connection field's entry point, which resolves the model from `target_type`'s registered definition and calls the core. The Decision's own parenthetical example signature was already correct — it names `apply_connection_optimization(target_type, queryset, info)` — so the imprecision was in the surrounding prose, not the example, which is a shape a grep for the symbol name cannot detect. The substantive contract is intact and is what matters: the model is never inferred from `info.return_type`, and the middleware's `_optimize` shares the core rather than carrying a divergent copy (it adds only the return-type resolution the connection field does not need). Three sites now name both symbols.
- **Post-ship: the empty-plan bound was a deliberate intra-cohort sequencing boundary, and it is gone.** The Decision's `Scope honesty` paragraph asserted that the plan the helper derives is **empty for every connection field** in `0.0.9` — no `select_related`, no `prefetch_related`, no [`only()`][glossary-only-projection] — because the flat selection walker stopped at the connection's root children (`edges` / `pageInfo` / `totalCount`), which are not keys in the node model's field map. That was **true when written and correctly reasoned**, and it was not a defect: it described a real boundary *inside* the `0.0.9` patch line between two cards that shipped together, and the paragraph existed precisely so the card would not claim an optimization it had not built. It was argued at length — the Decision insisted the first `edges { node }` level could not be split from the deeper nested descent because both were the same recognition primitive, and it cited the sibling card's DoD wording as evidence of wholesale ownership.

  What closed it: a post-[`032`][kanban] hardening pass (commit `a3f84ea9`, 2026-06-11) added the `edges { node { ... } }` navigator `optimizer/extension.py::_connection_node_child_selections` and the `apply_to(..., selection_extractor=...)` parameter, and made that navigator `apply_connection_optimization`'s **default** — so a root connection's plan became non-empty with no [`connection.py`][connection] change, exactly as the Decision predicted the seam would allow. The same commit inverted the assertions of [`tests/test_connection.py::test_root_connection_field_queryset_is_planned`][test-connection] from `()`/`()`/`()` to `select_related == ("category",)` plus the full projection, and added the many-side twin. [`DONE-033-0.0.9`][kanban] then shipped the **nested** half — walker recognition of a connection inside a parent's selection walk and windowed `Prefetch` planning for it — and [`spec-033-connection_optimizer-0_0_9.md`][spec-033] records the same finding from its own side, as the card-premise staleness its Revision 1 opens with.

  **Claims this Decision may no longer make:** that the derived plan is empty for every connection field; that a root connection's own scalar projection and direct relation planning arrive only with the sibling card; and that recognizing the `edges { node }` wrapper at all is a single indivisible change owned wholesale elsewhere — the root unwrap and the nested walker recognition turned out to be separable, and were separated. The **prediction the Decision got right** and which therefore survives verbatim in substance: putting the seam in the field bought richer planning as an optimizer change rather than a connection-field retrofit. `Scope honesty` was replaced by a `Planning scope` paragraph stating what the cooperation point derives today and where its boundary now sits.

- **Post-ship: `P1-B`'s forward design input became a live property of this card's own pipeline.** The Decision carried a `Forward design input for 033` block asking that card to design the `GROUP BY` / `select_related` coexistence rather than discover it: when the plan became non-empty, its `select_related` / `only()` columns would have to coexist with the `GROUP BY` [`OrderSet`][glossary-orderset] emits for a to-many `orderBy` path. Two things changed its status. The advice is no longer forward — the addressee card has shipped, so a block of design input to it is a note to a closed audience. And the interaction is no longer hypothetical: a root connection's plan is non-empty, so steps 3 and 6 of the [Decision 7][spec-030-d7] pipeline now compose on every such request. It is also **answered** rather than open — [`orders/sets.py::OrderSet._resolve_order_expressions`][orders-sets] orders a to-many path through a `Min` / `Max` aggregate, keeping exactly one row per parent, and its docstring states the connection consequence directly; a nested relation connection carrying `orderBy:` is deliberately left unplanned on the sibling card's path so an aggregate order never sits beneath the window annotations. So the block became a stated property of the shipped pipeline under `Aggregate-ordering coexistence`, cited to that symbol and pinned live by [`test_genre_connection_order_by_to_many_no_node_multiplication`][fakeshop-test-library] — the maintainer's split applied literally: the constraint is contract and stays in the spec, the fact that it was once advice to an unshipped card is history and stays here.

- **Post-ship: two behaviors of the cooperation point the Decision never stated.** The helper is opt-in on the extension rather than self-installing — it reads the active extension from the `_active_optimizer` `ContextVar` `on_execute` publishes, so it shares the instance-bound plan cache, and returns the queryset unoptimized when no extension is installed (the `P3a` short-circuit above) or when `target_type` has no registered model. And the node-selection navigator is a `selection_extractor` parameter rather than a hardcoded `edges { node }` walk, so a caller whose response nests the node type under a different slot passes its own; the mutation re-fetch is the second caller that does. Both are recorded here and stated in the spec's Decision body, because "the field self-optimizes" reads as unconditional without them.

## Decision 12 — No auto-trigger of `finalize_django_types()` for `0.0.9`

Spec: [Decision 12 — No auto-trigger of `finalize_django_types()` for `0.0.9`][spec-030-d12].

### Justification (moved from the spec)

the card's Foundation-slice seam names the auto-trigger as a possibility but qualifies it ("must respect the single-threaded-setup window: either be constrained to schema-construction time, or acquire a real lock around the finalizer"); that locking design is shared with [`DjangoNodeField`][glossary-djangonodefield] (which lands with `032`). [`DjangoListField`][glossary-djangolistfield] does not auto-trigger finalize; matching its posture avoids a finalizer-locking surface this card does not need.

### Alternatives considered (and rejected)

**Auto-trigger finalize from the field constructor now.** Rejected: introduces the single-threaded-setup-window problem for a field that works fine with explicit finalize, and diverges from the `DjangoListField` precedent for no `0.0.9` benefit.

### Changes this Decision underwent

- **Revision 1** set the no-auto-trigger posture and it was never reopened. The finalizer-locking design the card's Foundation-slice seam gestured at was routed to [`DONE-032-0.0.9`][kanban], where [`DjangoNodeField`][glossary-djangonodefield] shares it.
- **Post-ship: the routing half of the deferral was never taken up, so `## Out of scope` was naming an obligation no card holds.** The Decision's own claim — this card does not auto-trigger finalization — is true and permanent, and needed no change; what drifted is the spec's `## Out of scope` twin, which said "deferred to `032`". `032` shipped [`DjangoNodeField`][glossary-djangonodefield] in [`django_strawberry_framework/relay.py`][relay-root] **without** an auto-trigger, `spec-032-full_relay-0_0_9.md` does not mention one, and no helper anywhere in the package calls `finalize_django_types()` — two instruments, the call-site sweep and a sweep for auto-trigger machinery, both return zero. The direction was subsequently recorded as **not adopted** in `spec-010-foundation-0_0_4.md` #"Layer 3: Finalization trigger", which also carries the standing single-threaded-setup-window constraint on any future helper that takes it up. So the bullet now states the scope boundary plus the current package state, and routes nothing at a closed card. This is the grading test applied to a *routing* claim rather than a state claim: "deferred to `032`" reads as scope but asserts that another card holds the work, which is a state claim about that card's scope and drifts exactly as any other state claim does when the card closes without it.

## Decision 13 — Version bumps are owned by the joint `0.0.9` cut

Spec: [Decision 13 — Version bumps are owned by the joint `0.0.9` cut][spec-030-d13].

### Justification (moved from the spec)

the exact precedent [`spec-029`][spec-029] [Decision 11][spec-029] set; [`docs/SPECS/NEXT.md`][next] Step 6 mandates this Decision when multiple cards share the target patch version ("The Slice 5 / Definition of done checklist must NOT bump the version").

### Alternatives considered (and rejected)

**Bump the version in Slice 5.** Rejected: would race the three sibling cards for the same bump and promote a release heading before the cohort is cut.

### Changes this Decision underwent

- **Revision 1** reused [`spec-029`][spec-029] Decision 11 verbatim. Unchanged since.
- **Post-ship: the no-version-bump rule held in full, and the audit is worth recording because the instrument is not the obvious one.** The version has moved several times since for unrelated reasons, so `HEAD` cannot answer the question; what is auditable is the card's own commits. `git show --stat` over each of them (`eaaf1385` authoring, `10fd7f48` terms, `8cac3495` the build, `e2b5b10b` the review round) touches `pyproject.toml` and `uv.lock` **zero** times; `__version__` is byte-identical `"0.0.8"` across `8cac3495`; and the joint-cut commit `6aeebd8d` is where all four version files move together — the boundary confirmed from both sides rather than only from the card's. The one subtlety: `8cac3495` **does** touch `tests/base/test_init.py`, adding `DjangoConnection` / `DjangoConnectionField` to the pinned `__all__` tuple in `test_public_api_surface_is_pinned`. That is [Decision 14](#decision-14--connectionpy-module-and-the-public-export-gate)'s Slice-4 export promotion, not a version edit, and the rule survives it **only because every one of the four sites states the symbol `tests/base/test_init.py::test_version` rather than the file**. A file-level phrasing anywhere in that population would have been false at ship time. Worth keeping: a claim can be right in every path and wrong in its subject.
- **Post-ship: "bullets land under `[Unreleased]`" was a true prediction whose enduring implication the joint cut falsified.** At `8cac3495` the card's two `### Added` bullets did land under a `## [Unreleased]` heading, exactly as the Decision said. The joint cut then promoted that heading to `## [0.0.9] - 2026-06-13`, which is the mechanism this same Decision assigns to it — so the sentence describes a state that the Decision's own boundary guaranteed would not last. Left as written it reads, in the present tense, as a claim about a heading `CHANGELOG.md` no longer contains at all. The third grading case again, and its second appearance outside `## Current state` after [Decision 14](#decision-14--connectionpy-module-and-the-public-export-gate)'s fork conditional: the repair states the scope boundary the sentence was really expressing — this card contributes bullets, not headings — and lets the [Definition of done][spec-030-dod] name where they ship. The bullets' wording was itself rewritten after `8cac3495` (shortened and reordered, same three symbols and same substance), which is a second reason no spec sentence should pin their surroundings.

## Decision 14 — `connection.py` module and the public-export gate

Spec: [Decision 14 — `connection.py` module and the public-export gate][spec-030-d14].

### Justification (moved from the spec)

a flat module matches the shipped `list_field.py` and the [`docs/TREE.md`][tree] reservation; promoting the export in the slice that proves it (Slice 4) is cleaner than a two-step export-then-document split and resolves the rev1 conflict; `032`'s own Files-likely-touched list already names a *new* `relay.py` for Root-Node work.

### Alternatives considered (and rejected)

- **Promote the export in Slice 5 (rev1).** Rejected: conflicts with Slice 4's live consumer-facing usage; public export and the live proof should land together.
- **A `relay/` subpackage now.** Rejected: premature for one factory + connection types; `032` can introduce `relay.py` or fork later.

### Changes this Decision underwent

- **Revision 2 P2 — the public-export gate was reconciled with the live example slice.** rev1 deferred the export of `DjangoConnectionField` / `DjangoConnection` to Slice 5 (docs). That conflicted with Slice 4 being the consumer-facing usage slice and with the spec's own User-facing-API section importing both symbols from the top-level package. The export moved to Slice 4, so the example imports from the public surface rather than a temporary submodule path, and the tested-usage promotion discipline is satisfied inside the slice that proves the shape.
- **Post-ship: the module-layout half was a prediction, and only its first clause survived as written.** The Decision said `connection.py` now, a separate `relay.py` with `032`, and a fork into a `relay/` subpackage "if the combined connection + Root-Node surface grows past ~one module". The first two clauses came true and read true today — [`django_strawberry_framework/relay.py`][relay-root] carries `DjangoNodeField` / `DjangoNodesField` and cites `spec-032` in its own docstring. The conditional did not: measured at `HEAD`, `connection.py` is 2,077 lines, `relay.py` 603, and the `Meta.cursor_field` codec `keyset.py` a further 654 — the Relay surface is three flat modules and roughly 3.3k lines, so the antecedent is long satisfied while the consequent never happened and no card owns it. That is the third grading case this cycle keeps meeting: **a true prediction whose enduring implication later work falsified.** Left as written it reads as an unmet restructuring obligation the shipped layout contradicts, because [`docs/TREE.md`][tree] records the flat modules as the on-disk layout and the card's own DoD box ("decide whether full Relay support belongs here or a separate `relay/` subpackage") is ticked. Deleting it would lose the real content, which is a scope boundary rather than a threshold: the flat pair is this card's answer, and any later consolidation is a package-layout decision no `030` slice makes. The Decision now states that, and keeps the [`START.md`][start] fork-when-it-grows pointer as the standing advice it is rather than as a pending trigger.
- **Post-ship: two Decision-14 sentences claimed a `docs/TREE.md` state Slice 5 itself removed.** The Decision's first paragraph and the `docs/TREE.md` entry in [Key glossary references][spec-030-key-glossary] both said the target layout "reserves the `connection.py [alpha]` slot" — present tense, and false from the moment Slice 5 discharged its own checklist item to drop that tag. Both now say what `docs/TREE.md` carries: `connection.py` listed flat under the on-disk package layout beside its mirrored flat test file. The three surviving `[alpha]` mentions are the Slice-5 checklist item and its `## Doc updates` twin, which are instructions describing landed work, and the `## Current state` bullet, which is a licensed dated observation verified true at the spec's authoring commit — a distinction worth naming, because a sweep on `[alpha]` alone cannot tell the three apart.

## Non-Decision deliberation

Findings that changed the spec without belonging to any one Decision. They left the spec with the revision history above; grouped here by what they were about.

### Spec hygiene and vocabulary

- **Revision 2 P3, spec hygiene.** Three unrelated corrections landed together: the [`ConfigurationError`][glossary-configurationerror] Key-glossary bullet stopped listing `first` + `last` (that is a query-runtime path, not a construction error, so it raises a `GraphQLError`); an unused `[glossary-metaconnection]` link definition was removed because the glossary heading did not exist yet; and Slice 5's [Doc updates][spec-030-doc-updates] was made to name the [`CHANGELOG.md`][changelog] edit explicitly, so the maintainer prompt grants the permission [`AGENTS.md`][agents] withholds rather than an agent inferring it from a standing document.
- **Revision 3, glossary anchoring.** [`Meta.connection`][glossary-metaconnection] was added to [`docs/GLOSSARY.md`][glossary] as `planned for 0.0.9`, then to the companion [`spec-030-connection_field-0_0_9-terms.csv`][spec-030-terms] and the spec's key-reference map, so the net-new public `Meta` key was available to implementers before Slice 1 started. This is the round that reversed the rev2 removal of that same link definition — the heading existed by then.

### Post-ship: symbol citations the Relay-foundation relocations invalidated

Three symbols the spec names by their `0.0.9` spelling moved after the card shipped, and two further sites made the same stale claim without naming a symbol at all. The renames are mechanical, but the population is larger than any one of them suggests, so it is recorded here as a whole rather than under a Decision:

- `types/relay.py::_initial_queryset` is now `django_strawberry_framework/utils/querysets.py::initial_queryset` — 4 occurrences in the spec.
- `types/relay.py::_apply_get_queryset_sync` / `_apply_get_queryset_async` are now `utils/querysets.py::apply_type_visibility_sync` / `apply_type_visibility_async`, the sealed-execution-queryset boundary — 15 occurrences across 7 lines.
- `connection.py::_ends_in_unique_column` is a re-export; the canonical implementation is `django_strawberry_framework/optimizer/plans.py::ends_in_unique_column` — 2 occurrences. This one still resolves at the cited module, and `tests/test_connection.py` imports it by the private name deliberately, so the citation was imprecise rather than broken.

**Two of those sites are not drift, and the distinction is the point.** The `## Current state` section is licensed as a dated observation of the pre-build repo, and at the spec's authoring commit `types/relay.py` genuinely carried all three private symbols (verified by reading that revision, not inferred). A `Current state` bullet describing the repo as it then was stays as written; a `## Slice checklist` sub-bullet, a Decision, an `## Edge cases` bullet, or a DoD item naming a symbol that no longer exists is a contract statement and is drift. The licence covers observations, never predictions the build falsified.

**Both `Current state` bullets were re-derived rather than inherited, and the second one needed it.** The first pass through this population verified the `types/relay.py` bullet at the authoring commit and graded the `list_field.py` bullet by the same reasoning without reading it. Reading it: at that commit `list_field.py` imported `_apply_get_queryset_async`, `_apply_get_queryset_sync`, `_initial_queryset` from `.types.relay`, branched on `in_async_context()`, and defined `_post_process_consumer_sync` / `_post_process_consumer_async`. Every clause of the bullet is true of the repo it describes, so the licence applies to it on its own evidence rather than by analogy. The general rule: a licence claim about a section is not a licence claim about each sentence in it, and grading by section is how a false sentence survives inside a true one.

**The population's last two sites were invisible to the symbol sweep, and that is the recurring defect rather than an accident.** A sweep keyed on the old private names cannot see a site that omits them:

- **The Decision-10 heading**, `Sync + async resolver paths reuse the Relay-foundation helpers`, made the same stale claim with no symbol in it — as did the `SyncMisuseError` glossary-reference bullet and an `## Edge cases` bullet, both saying "the Relay-foundation contract". Found by sweeping the *concept vocabulary* (`Relay-foundation`, 3 occurrences pre-edit) rather than the symbols; all three now name the shared visibility helpers, and the heading rename is recorded under [Decision 10][spec-030-d10].
- **`apply_connection_plan`**, in the `### Composing with get_queryset, filter, and order` fenced pipeline sketch, is a symbol spelling that **never existed in the package** — not a rename, an invention. It was invisible to two instruments at once: the old-name sweep (it is not an old name) and a sweep over backticked identifiers (it sits inside a fence, so it carries no backticks). Found by reading the section against the source. The real symbol is `apply_connection_optimization`. The `Current state` licence cannot cover it in either direction: it is not in that section, and a spelling that never existed describes no repo at any date.

### Post-ship: the empty-plan claim's population was mostly outside the Decision that made it

The claim recorded under [Decision 11][spec-030-d11] above — the derived plan is empty, and the sibling entry stays `planned` — lived in **eight** sections none of which is a Decision: the [Slice checklist][spec-030-slice-checklist] (three sub-bullets), `## Current state`, `## Goals`, the [reference-package parity checkpoint][spec-030-parity] table's Status column, `## Edge cases and constraints`, the [Test plan][spec-030-test-plan], [Doc updates][spec-030-doc-updates], and the [Definition of done][spec-030-dod] — plus the Predecessors paragraph and two Key-glossary bullets. Only two of those sites name a `select_related`-shaped symbol, and one carries the claim as a single word in a table cell (`planned`), so a reader who fixes the Decision and stops has fixed the least-read instance of it.

Two of the sites needed a judgement rather than an edit, and the tests are worth stating because they recur:

- **`## Out of scope` and `## Non-goals`** both list connection-aware planning as another card's job. Neither is drift. The test: does the sentence assert what some artifact's **state** is, or what **this card does not build**? Both assert the latter, and `030` genuinely did not build it, so both stay — the `Non-goals` bullet took one precision word (`nested`) because the root unwrap now lands at this card's own seam and an unqualified sentence would mis-assign it.
- **`## Current state`'s glossary bullet** is a dated observation and stays: at the spec's authoring commit `docs/GLOSSARY.md` did carry `## Connection-aware optimizer planning` at `**Status:** planned for 0.0.9` (read at that revision, not inferred). Its second sentence was not an observation but a statement about what the build's own Slice 5 would do, so it was reconciled to the scope boundary it was really expressing — the entry's status is the sibling card's to set — rather than left to read as a claim about the glossary today.

### Post-ship: the self-referential path claims the spec's own archival invalidated

A spec that names its own path makes a claim that the [`AGENTS.md`][agents] archival convention is guaranteed to break, and it breaks silently: the reference-style *definitions* were re-relativized by the archival sweep and all resolve, so every link still worked while the visible path in seven places named a file that is not there. Measured rather than asserted, and with two instruments on disjoint vocabulary: the literal token `docs/spec-030` occurred **7** times over **5** lines, and a second pass that never matches that token — reconstruct every path-shaped `…connection_field-0_0_9*` occurrence and classify it by its full prefix — returned the same 7 (six `.md`, one `-terms.csv`) alongside the correctly-relative `appx/…` definitions. The correct spelling `docs/SPECS/` appeared **2** times against those 7.

The seven did not grade alike, which is the point:

- The [Definition of done][spec-030-dod] item 1 sites are the sharpest, because one of them is a **runnable command** — `check_spec_glossary.py --spec docs/spec-030-…` would fail on a missing file today, so the completion condition could not be re-verified as written. Its companion-CSV path was stale in the same sentence.
- The [Slice checklist][spec-030-slice-checklist] KANBAN bullet and its [`## Doc updates`][spec-030-doc-updates] twin are a matched pair: they instruct the card to point [`KANBAN.md`][kanban]'s card body at the spec, so fixing one and leaving the other reproduces the partial-claim-fix defect this cycle keeps finding. Both moved in one change.
- [Definition of done][spec-030-dod] item 9 asserts what `KANBAN.md` records, and the board records the archived path — so the spec was the wrong half of that pair.
- [Decision 1](#decision-1--spec-filename-and-canonical-naming) is the odd one out and is graded in its own entry above: its subject is the naming convention, not the directory.

One further false state claim rode in the same sentence as item 1's paths and is not a path claim at all: the item said the net-new `Meta.connection` symbol "is present in both [`docs/GLOSSARY.md`][glossary] and the CSV as `planned for 0.0.9`; Slice 5 flips it to `shipped (0.0.9)`". Slice 5 did flip it — the glossary heading reads `shipped (0.0.9)` — so the sentence describes a pre-flip state as current while also instructing the flip that already happened. It now states the standing condition (a glossary heading exists, and a CSV row anchors the term to it) and leaves the flip itself to item 8, which is where a completion condition about status belongs. The [`-terms.csv`][spec-030-terms] companion, incidentally, never carried a status word for `Meta.connection` at all, so half the claim was never true.

### Post-ship: the shipped-sibling-surface status claims, and the row-by-row table check that found the second one

Four sites described work that has since shipped as still ahead. Two instruments, on disjoint vocabulary: the status word `planned` (30 occurrences spec-wide, of which the great majority are `030`'s own three glossary entries, the `[alpha]` planned tag, or the words `planning` / `unplanned`), and the future-tense vocabulary that carries no status word at all (`will …`, `lands with`, `after this card`, `not this card`). Neither instrument alone finds the population: `planned` misses the `## Key glossary references` [Relation handling][glossary-relation-handling] bullet, and the future-tense sweep misses the parity table's one-word Status cells.

- The [reference-package parity checkpoint][spec-030-parity] table's Relay-Root row read `planned (0.0.9 — DONE-032-0.0.9)` — the same `planned`-inside-a-`DONE-`-card-id defect that was fixed one row below it and deliberately left here, because no `030` slice had audited `032`. Audited now, from four independent directions: [`django_strawberry_framework/relay.py`][relay-root] defines `DjangoNodeField` and `DjangoNodesField`, the package `__init__` exports both, [`KANBAN.md`][kanban] carries the card as `DONE-032-0.0.9` in Done, and [`docs/GLOSSARY.md`][glossary]'s `DjangoNodeField` entry reads `shipped (0.0.9)`. The cell now reads `sibling card`, matching its `033` neighbour.
- The `DjangoNodeField` Key-glossary bullet called it "the planned root single-node lookup field" that "lands with" `032`. Same claim, second spelling; it moved in the same change, because fixing one and not the other is the partial-claim-fix defect this cycle keeps finding.
- The [Relation handling][glossary-relation-handling] Key-glossary bullet said the sibling story "upgrades to relation-as-Connection **after this card lands**" — a future-tense pointer at shipped work whose antecedent (this card landing) is long satisfied. `Meta.relation_shapes` reads `shipped (0.0.9)` in the glossary. It now states the ownership split without a tense.
- **The fourth site was found only by checking the table row by row, and it has a different shape.** The `apply_cascade_permissions` row read `planned (0.0.10)`, and `0.0.10` shipped — the glossary entry reads `shipped (0.0.10)`, [`django_strawberry_framework/permissions.py`][permissions] defines the helper pair, the package exports both, and [`CHANGELOG.md`][changelog] documents them. It survived every sweep aimed at the *first* defect because it carries no `DONE-` card id: the instrument that found the Relay-Root row was "a `planned` status beside a `DONE-` card id", and this row is a `planned` status beside a bare version number. **A finding's own shape is not its population's shape.** The two rows genuinely still planned (`FieldSet` at `0.1.1`, `AggregateSet` at `0.1.3`) were confirmed against their glossary entries and left alone, and the table carries no row for `DONE-031-0.0.9` at all — the upstream cookbook has no GlobalID counterpart, so there is nothing to pair.

### Post-ship: the neighbouring live test that is deliberately NOT a `030` contract

`test_anonymous_inline_fragment_under_connection_field_resolves` lives inside
this card's own live block in [`test_library_api.py`][fakeshop-test-library] and
is **not** a `030` contract: its subject is an optimizer selection-walker
behaviour, and the connection field is only the surface it happens to be
exercised through. The spec therefore names it nowhere, and that absence is a
postcondition to preserve rather than an oversight to correct - a later sweep of
that live block would otherwise adopt it into the `## Test plan` on proximity,
since every other test in the block belongs there. The check is
`grep -c 'test_anonymous_inline_fragment' docs/SPECS/spec-030-connection_field-0_0_9.md`,
which must stay `0`; recording the boundary here rather than in the spec is what
keeps it so.

### The spec-wide reshaping Revision 2's P1 findings forced

The four P1 findings were foundational rather than local: three rewrote a Decision outright ([3](#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard), [4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes), [6](#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature)) and the optimizer one ([11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point)) propagated into the Problem statement, Current state, Goals, Implementation plan, Slice checklist, [Test plan][spec-030-test-plan] and Definition of done, because it turned a no-source-change slice into source work. That is why the spec's non-Decision sections read as though the extracted helper was always the plan: they were rewritten to match, not amended. The record that they were rewritten is here.

## Risks and open questions

The spec's `## Risks and open questions` body, verbatim, its own preamble included. The preferred-answer / fallback shape that preamble describes is what makes the section a build-time instrument rather than a contract, which is why the whole body moved. Two of the six items are mechanism bets Slice 2 settled by compiling against the locked Strawberry; one is a [`KANBAN.md`][kanban] card-body conflict [Decision 1](#decision-1--spec-filename-and-canonical-naming) reconciles; the rest name fallbacks the build never needed.

**One rule inside these items stayed in the spec.** Every Strawberry-mechanism claim in this spec — that `SliceMetadata.from_arguments` does not reject `first` + `last`, that `ConnectionExtension.resolve` forwards non-pagination `**kwargs` to the inner resolver and does not await its return, that `ListConnection.resolve_connection` receives the pagination arguments — is derived against the uv.lock-resolved `0.316.0`, and `pyproject.toml` declares an open `strawberry-graphql` floor. A supported version that changes any of those requires the affected Decision to be re-derived by executing against that version. The spec restates that rule under the surviving heading; the preferred-answer / fallback framing around it is below.

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **Argument-injection mechanism: synthesized signature vs custom `FieldExtension`.** Preferred answer per [Decision 6](#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature): a synthesized resolver `__signature__` so Strawberry's native resolver-argument derivation emits `filter:` / `orderBy:`, and `ConnectionExtension` forwards them to the resolver. Open risk: whether `relay.connection()` cleanly merges resolver-signature arguments with the auto-added pagination arguments in `0.316.0`. Fallback: a custom `FieldExtension.apply(...)` that appends the `filter` / `order_by` `StrawberryArgument`s before field build and pops them in `resolve` — verified-viable by the review's source inspection. Slice 2 picks the route that compiles against the locked Strawberry; both produce identical SDL.
- **The consumer annotation `DjangoConnection[GenreType]` vs the resolved concrete type.** Preferred answer per [Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes) / [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation): the factory resolves the actual connection type (the generated `<TypeName>Connection` when `totalCount` is enabled) and wires it through `relay.connection(...)`; the consumer annotation documents the node type. Open risk: whether Strawberry tolerates the class-attribute annotation differing from the `relay.connection` type. Fallback: have `DjangoConnectionField` set the field's type explicitly so the annotation is purely documentary, or read the node type from the annotation (strawberry-django style) instead of the explicit `target_type` argument — Slice 2 confirms which Strawberry accepts.
- **Card body names an unnumbered spec filename.** Preferred answer per [Decision 1](#decision-1--spec-filename-and-canonical-naming): this spec is `docs/spec-030-connection_field-0_0_9.md`; the card-body reference is rewritten in the [`docs/SPECS/NEXT.md`][next] Step-8 archive sweep / card-completion wrap. Fallback: none.
- **Optimizer cooperation scope.** Preferred answer per [Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point): the field owns the cooperation point via the extracted helper, which runs and publishes a plan before the slice; ALL `edges { node }` planning (root scalar/FK projection included) is [`DONE-033-0.0.9`][kanban]'s walker-awareness change — the derived plan is empty in `0.0.9` — guarded by a strictness `"raise"` test. Fallback: if `033` slips past the joint cut, the documented constraint stands and the strictness test keeps the gap visible — connection fields are still correct (filter / order / pagination / `totalCount` all work) and the cooperation seam is in place, so `033` lights up optimization with no `connection.py` change.
- **Auto-trigger of `finalize_django_types()`.** Preferred answer per [Decision 12](#decision-12--no-auto-trigger-of-finalize_django_types-for-009): no auto-trigger in `0.0.9`. Fallback: the auto-trigger wrapper is designed once for both `DjangoConnectionField` and [`DjangoNodeField`][glossary-djangonodefield] in `032`, constrained to schema-construction time or guarded by a real lock.
- **`Meta.connection` dict vs flat boolean.** Preferred answer per [Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition): a forward-compatible dict. Fallback: if `032` never adds further sub-keys, it could collapse to a flat boolean — but the dict is the card body's stated shape.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[changelog]: ../../../CHANGELOG.md
[kanban]: ../../../KANBAN.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-djangoconnection]: ../../GLOSSARY.md#djangoconnection
[glossary-djangolistfield]: ../../GLOSSARY.md#djangolistfield
[glossary-djangonodefield]: ../../GLOSSARY.md#djangonodefield
[glossary-filter_input_type]: ../../GLOSSARY.md#filter_input_type
[glossary-finalize_django_types]: ../../GLOSSARY.md#finalize_django_types
[glossary-metaconnection]: ../../GLOSSARY.md#metaconnection
[glossary-only-projection]: ../../GLOSSARY.md#only-projection
[glossary-order_input_type]: ../../GLOSSARY.md#order_input_type
[glossary-orderset]: ../../GLOSSARY.md#orderset
[glossary-relatedfilter]: ../../GLOSSARY.md#relatedfilter
[glossary-relatedorder]: ../../GLOSSARY.md#relatedorder
[glossary-relation-handling]: ../../GLOSSARY.md#relation-handling
[glossary-syncmisuseerror]: ../../GLOSSARY.md#syncmisuseerror
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-028]: ../spec-028-orders-0_0_8.md
[spec-028-rationale]: spec-028-orders-0_0_8-rationale.md
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
[spec-030-doc-updates]: ../spec-030-connection_field-0_0_9.md#doc-updates
[spec-030-dod]: ../spec-030-connection_field-0_0_9.md#definition-of-done
[spec-030-edge-cases]: ../spec-030-connection_field-0_0_9.md#edge-cases-and-constraints
[spec-030-key-glossary]: ../spec-030-connection_field-0_0_9.md#key-glossary-references
[spec-030-error-shapes]: ../spec-030-connection_field-0_0_9.md#error-shapes
[spec-030-parity]: ../spec-030-connection_field-0_0_9.md#reference-package-parity-checkpoint
[spec-030-slice-checklist]: ../spec-030-connection_field-0_0_9.md#slice-checklist
[spec-030-terms]: spec-030-connection_field-0_0_9-terms.csv
[spec-030-test-plan]: ../spec-030-connection_field-0_0_9.md#test-plan
[spec-033]: ../spec-033-connection_optimizer-0_0_9.md

<!-- docs/builder/ -->
[build-md]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[connection]: ../../../django_strawberry_framework/connection.py
[definition]: ../../../django_strawberry_framework/types/definition.py
[optimizer-extension]: ../../../django_strawberry_framework/optimizer/extension.py
[orders-sets]: ../../../django_strawberry_framework/orders/sets.py
[permissions]: ../../../django_strawberry_framework/permissions.py
[relay-root]: ../../../django_strawberry_framework/relay.py

<!-- tests/ -->
[test-connection]: ../../../tests/test_connection.py
[test-registry]: ../../../tests/test_registry.py

<!-- examples/ -->
[fakeshop-test-library]: ../../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[strawberry-relay]: https://strawberry.rocks/docs/guides/relay
