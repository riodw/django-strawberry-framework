# Rationale: spec-001 — DjangoType foundation (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-001-django_types-0_0_1.md`][spec-001]. The spec is the contract
and states only what it requires; everything that explains **how it got there** lives here: the
alternatives each decision rejected and why each lost, the derivations that do not change how a
decision is implemented, the chronology the spec used to narrate about itself, and every claim
the spec once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-001-0.0.1` shipped five
years of package history ago in version terms and the rule that gates a build on this move did
not exist then; this pass supplies it. Text marked *Moved* below was cut out of the spec, not
copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec section**, named by the section's own heading and linked to its anchor. A
  section whose text did not move has no entry here — that is not an omission, it means the whole
  section is contract.
- **Who reads it.** Worker 3 reads it during review; Worker 1 owns it; Worker 2 never reads it. A
  reader looking for what the package *does* wants the spec, not this file.
- **This spec has no numbered Decisions.** It predates that convention, so the key is the
  heading. Three entries key to headings that no longer exist in the spec at all
  (`## Scope creep into the N+1 problem`, `## Post-slice-7 future work`, `## Open questions`);
  each names the surviving sections its argument bears on.
- **What the rationale-extraction pass did NOT do.** It did not reconcile the spec against the
  shipped package. Every claim recorded under "Entries keyed to the spec" is recorded **as the spec
  made it**, in the spec's own tense; whether the package still honours it was item R2's
  determination, not that pass's. Where the spec's own text already superseded an earlier statement
  of its own, that supersession is recorded.
- **Item R2 has since run.** Its record is the second half of this file,
  "Item R2 — reconciliation against the shipped package", and it is where every claim the package
  falsified is answered. The two halves are chronological, not competing: the first records what the
  spec said and why, the second records what HEAD said back and what the spec now says instead.

## Provenance of this record

- **Moved** — cut from the spec by this pass, and now only here: the whole of
  `## Scope creep into the N+1 problem`, `## Post-slice-7 future work` and `## Open questions`;
  the `Deviation from earlier draft`, `Slice 2 implementation subset` and
  `Deferred scalar conversions` paragraphs under Scalar field conversion; the slice framing of the
  `## Choice field enum generation` section opener; the label-vs-value sanitization comparison; the
  `Slice 2 -> Slice 3 hand-off` and `Slice 3 status (post-implementation)` paragraphs; the three
  candidate `lazy_ref` approaches; and the `Status:` / `superseded by` / `Moved to` annotations on
  the slice list, together with the Slice 4 supersession narrative and the Slice 5 / Slice 6 move
  reasons those annotations carried.
- **Restated in the spec, not moved** — three passages that read like deliberation and are not.
  The unsupported-field-type raise (a silent `typing.Any` fallback is a fail-open, and the reason
  it is one is instruction to a builder, so that reason stays in the spec; the chronology came
  here, and the reason is restated here as well, because an entry recording a rejected alternative
  has to say why it lost). The value-based sanitization rule and its `MEMBER_<digit>` cost. The
  relation dispatch rule and the relation set `Meta.fields = "__all__"` surfaces, which the
  hand-off paragraph carried as narrative and the spec now carries as contract.
- **Deliberately left in the spec by this pass** — the `## N+1 strategy` section, including its
  per-slice implementation paragraphs and the PR #583 derivation; the `## get_queryset` O6
  sentinel-flip paragraph; the `Meta.interfaces` parking paragraph; `## Current state`. These are
  mechanism or status rather than deliberation, and their disposition against the shipped package
  is item R2's call. The PR #583 paragraph in particular is the load-bearing "why" — *FK joins
  bypass per-type visibility filtering and leak rows* — and a builder who never reads it writes
  the leak.

## Entries keyed to the spec

### Whole-document scope — the optimizer was bundled deliberately (former `## Scope creep into the N+1 problem`)

Bears on [`## Goal`][spec-001-goal], [`## N+1 strategy`][spec-001-n1] and
[`## Suggested implementation slices`][spec-001-slices].

*Moved — the scope argument in full.* The spec's strict scope is the type-generation foundation:
the `DjangoType` base class, Meta options, scalar and relation field conversion, the registry,
the `get_queryset` hook, choice-field enum generation, and type naming. Anything in it that
addresses the runtime resolver-optimization problem is creep into N+1 territory that, in a
stricter project layout, would live in its own document such as `spec-002-optimizer-0_0_2.md`.

The places the spec reached into N+1 were concrete, and the spec enumerated them: the Goal
sentence promising "relation resolution optimized by default" alongside type generation; the
Proposed public surface listing `DjangoOptimizerExtension` as a top-level package name; the whole
`## N+1 strategy` section, including the `select_related` / `prefetch_related` / `only()` rules
and the `get_queryset` + `Prefetch` downgrade rule borrowed from strawberry-graphql-django PR
#583; the `## get_queryset` section framing the hook as something "the optimizer must respect",
which leaks the optimizer's existence into what would otherwise be a pure type-system primitive,
plus the `has_custom_get_queryset()` introspection helper that exists solely so the optimizer can
detect overrides; Slices 4, 5 and 6 of the suggested order, which are entirely optimizer work;
the Testing strategy's "optimizer query counts on relation traversal" and its visibility-leak
scenario; and one of the open questions and two of the references.

*Alternative rejected — two specs in lockstep.* Splitting the optimizer into its own follow-up
spec at authoring time would have meant shipping a foundation that is **broken-by-default** until
that follow-up landed. An N+1 fix cannot be specced in isolation, because the problem only exists
once a type system resolves relations across the ORM graph, and the load-bearing `get_queryset` +
`Prefetch` rule in particular is what makes per-type visibility filtering work across joins. One
combined foundation was chosen over two specs that depend on each other in lockstep.

*The cut line the spec named for itself, and then took.* "If this document is ever split, the
optimizer is the natural cut line. The seam is clean: `DjangoType` knows about `get_queryset` and
exposes `has_custom_get_queryset()`; the optimizer is the only consumer of that introspection.
Lifting Slices 4 through 6, the `## N+1 strategy` section, the `DjangoOptimizerExtension` public
name, and the optimizer-shaped sentences in `## Goal` and `## get_queryset` into a
`spec-002-optimizer-0_0_2.md` would leave a coherent type-generation-only document behind."
[`spec-002-optimizer-0_0_2.md`][spec-002] exists and the slice list now points Slices 4-6 at it,
so the prediction was taken up on the slice axis. The spec still holds `## N+1 strategy`, the
`DjangoOptimizerExtension` public name, and the optimizer-shaped sentences in `## Goal` and
`## get_queryset` — the second half of the cut was never performed.

### `## Scalar field conversion` — the `typing.Any` fallback, and the Slice 2 subset

Spec: [Scalar field conversion][spec-001-scalars].

*Alternative rejected — `typing.Any` for an unmapped field type.* The illustrative converter
originally fell back to `typing.Any` when `type(field)` was missing from `SCALAR_MAP`. It lost
because a silent `Any` fallback masks unsupported columns at schema-build time and surfaces them
as opaque type errors much later (Strawberry has no native `Any` scalar mapping), where
`ConfigurationError` fails fast with the field path in the message and a one-line fix. The
**rule** stays in the spec, and so does the sentence stating why it holds: that reason is
instruction to a builder, and a builder never reads this file. What came here is the chronology
(an earlier draft carried the fallback at all) and the record that the alternative was weighed and
lost, which this file is required to carry. The one reason clause therefore appears in both files
by design; it is not a copy leak.

*Moved — Slice 2 implementation subset.* "The converter above is the eventual end-state. Slice 2
implements the `SCALAR_MAP` lookup, the unsupported-type raise, and the `field.null` widening.
The `if field.choices:` branch is deferred to Slice 7 (choice-field enum generation) so coverage
stays at 100% without an unreached path. `type_name` is therefore unused in Slice 2 and is
annotated as such; it is preserved in the signature so the Slice 7 change is purely additive."

*Moved — deferred scalar conversions, as the spec stated them.* "`BigIntegerField` -> custom
`BigInt` scalar, `ArrayField` -> `list[inner_type]`, and `JSONField` / `HStoreField` -> Strawberry
JSON scalar are all spec'd above but not implemented in Slice 2 because the fakeshop example
models do not exercise them. They can be added without further design work as soon as a fakeshop
model (or a real consumer) declares one. The TODO comments for each live in
`django_strawberry_framework/converters.py` so they surface in code search."

*Claims the spec no longer makes.* That any scalar conversion is unimplemented; that `type_name`
is unused; that a TODO comment for a deferred scalar lives in `converters.py`. All three were
Slice-2-era status. The scalar table itself is unchanged and still contract.

### `## Choice field enum generation` — sanitizing the value, not the label

Spec: [Choice field enum generation][spec-001-enums].

*Alternative rejected — label-based member names.* graphene-django and strawberry-graphql-django
sanitize labels (`"Active"` -> `ACTIVE`) because labels are human-readable phrases that round-trip
cleanly to identifiers; values can be opaque (`"M"`, `"F"`, `1`, `2`) and produce uglier members
(`M`, `F`, `MEMBER_1`, `MEMBER_2`). The label path lost anyway: labels are display strings
consumers may translate or restyle, and coupling the GraphQL schema to them is fragile. The
`MEMBER_<digit>` prefix in the sanitization step is the explicit, accepted cost of the trade-off —
and that sentence stays in the spec, because a later reader tempted by prettier members needs to
see the price was known.

*Moved — the slice framing of the section opener.* The section opened by attributing the work to
Slice 7: it "completes the scalar-conversion surface — it is the only branch `convert_scalar`
deferred in Slice 2", the change "consists of adding the `if field.choices:` branch to
`convert_scalar` and implementing `convert_choices_to_enum`", and "with Slices 4 through 6 moved
to `spec-002-optimizer-0_0_2.md`, Slice 7 is unblocked as soon as Slice 3 has shipped, and is the
only remaining slice in this spec." The mechanism survives in the spec as a present-tense rule;
the scheduling did not.

*Deliberately not moved.* The import-order consequence of registry-cached enum naming ("the first
type defined wins the enum's name … consumers who want a stable, predictable name should declare
the `DjangoType` they want to win first") reads like a confession and is consumer instruction, so
it stays. It also carries the spec's only link to the `Meta.choice_enum_names` glossary anchor.

### `## Relation field conversion` — the staged hand-off, and what Slice 3 actually shipped

Spec: [Relation field conversion][spec-001-relations].

*Moved — Slice 2 -> Slice 3 hand-off.* "`_build_annotations` in Slice 2 filters relations out
entirely (`[f for f in model._meta.get_fields() if not f.is_relation]`) so a model with FKs or
reverse rels can be partially mapped (scalars only) without the unimplemented `convert_relation`
raising. Slice 3 must flip that filter: every field goes through dispatch, with relations routed
to `convert_relation` and scalars to `convert_scalar`. Once that change lands,
`Meta.fields = "__all__"` will include relations on Category (`items`, `properties`), Item
(`category`, `entries`), Property (`category`), and Entry (`property`, `item`). The
`tests/test_django_types.py` placeholders for `test_relation_fk_to_target_djangotype`,
`test_relation_reverse_fk_returns_list`, `test_relation_m2m_returns_list`, and
`test_forward_reference_resolves_when_target_defined_later` already mark the test surface Slice 3
must fill in." The dispatch rule and the relation set were promoted into the spec as contract; the
staging, the interim filter, and the test-placeholder inventory came here.

*Moved — Slice 3 status (post-implementation), a self-amendment the spec made to its own
forward-reference promise.* "Slice 3 shipped eager-only relation resolution. `convert_relation`
looks up the target via `registry.get(field.related_model)` and raises `ConfigurationError` (with
a message naming the unregistered model) if the target is not yet declared. `registry.lazy_ref`
therefore stays as `NotImplementedError`; the spec's promise of definition-order independence is
deferred to a future slice. The practical implication: consumers must declare related
`DjangoType`s in dependency order — declare a target type before any type that references it via
FK / OneToOne / M2M, or before any type whose model surfaces it via a reverse rel. The fakeshop
dependency order is `CategoryType -> (PropertyType, ItemType) -> EntryType`. M2M handling is
implemented in `convert_relation` (the `field.many_to_many` branch shares the same line as
`field.one_to_many`, so line coverage holds), but no fakeshop model declares an M2M field, so the
dedicated test placeholder stays skipped."

*Change the section has undergone.* This paragraph is where the spec first contradicted itself:
the contract sentence says forward references make definition order irrelevant, and the status
paragraph immediately below said order was mandatory. Removing the status paragraph leaves the
contract sentence, which now also carries the `definition-order-independence` glossary link the
status paragraph used to own — the anchor was re-sited into contract prose rather than rescued by
keeping narration.

*Claims the spec no longer makes.* That relation resolution is eager-only; that `lazy_ref` is
`NotImplementedError`; that consumers must declare types in dependency order; that M2M has no
dedicated test.

### `## Registry` — three candidate `lazy_ref` approaches

Spec: [Registry][spec-001-registry].

*Moved — the candidate list Slice 3 was to pick from.* The spec offered three, without choosing:

- `Annotated["TargetType", strawberry.lazy("module.path")]` for cross-module references, resolved
  at schema-build time via a named import.
- A string annotation (`"TargetType"`) that `_build_annotations` rewrites once all sibling types
  are registered. Simplest for same-module references.
- A registry-tracked "pending relation" that `DjangoType.__init_subclass__` post-processes after
  every subclass has been seen.

*Which one was taken.* The third. The package's registry carries pending-relation bookkeeping and
a finalize pass over registered types rather than a `lazy_ref` returning a Strawberry lazy
annotation, so the `lazy_ref` **name** in the spec's registry surface is the part that did not
survive contact — item R2 owns restating that surface. Recorded here so the next reader does not
re-open a settled choice on the grounds that the spec never marked one.

*A later restatement of the same three options.* `## Post-slice-7 future work` listed the same
trio in different words ("string-annotation rewriting after every sibling registers; a
`strawberry.lazy`-backed wrapper that resolves through the registry at schema-build time; or a
deferred-`strawberry.type` pass invoked by a `finalize_types()` call"), attributing them to
`lazy_ref`'s docstring. Both statements are now here, and the duplication is the reason the spec
could go stale in one place and not the other.

### `## Suggested implementation slices` — status annotations, and the optimizer supersession

Spec: [Suggested implementation slices][spec-001-slices].

*Moved — the per-slice `Status:` annotations.* Slice 1 "shipped"; Slice 2 "shipped (v0.0.2
prerelease)"; Slice 3 "shipped (eager-only resolution; `lazy_ref` deferred)"; Slice 7 "shipped".
A slice list is a plan; its completion state is history, and the package version is the honest
record of what shipped.

*Moved — why Slice 4 was superseded rather than finished.* Slice 4 shipped as a partial /
depth-1-only implementation and was then superseded by `spec-002-optimizer-0_0_2.md`. Running the
slice's tests surfaced **two architectural issues** that warranted a dedicated optimizer spec:
Strawberry's default resolver chokes on `RelatedManager` for reverse rels, and per-resolver hooks
cannot emit nested `prefetch_related("items__entries")` chains. The shipped code
(`DjangoOptimizerExtension`, `_optimize`, `_plan`, `_unwrap_return_type`, `_snake_case`,
`registry.model_for_type`) stayed in tree as the starting point. The rebuild split across
`spec-002` slices: O1 lands custom relation-field resolvers in `DjangoType.__init_subclass__` (a
separate seam in `types.py`, not a refactor of optimizer code); O2 promotes `_plan` to a pure
walker module; O3 swaps the `resolve` / `aresolve` hooks for `on_executing_start`; O4-O6 then
layer nested prefetch, `only()`, and the `Prefetch` downgrade onto the rebuilt architecture.

*Moved — why Slices 5 and 6 moved before they were built.* Slice 5 (`only()` optimization) moved
to O5 because the `only()` column list and the FK-column inclusion rule both depend on the
selection-tree walker introduced in O2, so they could not land before that walker existed. Slice 6
(the `get_queryset` + downgrade-to-`Prefetch` rule) moved to O6 because the optimizer is the only
consumer of the sentinel flip and the downgrade; the `_is_default_get_queryset` sentinel and the
`has_custom_get_queryset()` helper stayed behind as type-system surface. That split rule survives
in the spec, because it says which document owns which symbol.

*Claim the spec no longer makes.* That any slice is un-shipped, in progress, or "the only
remaining slice in this spec".

### `## Post-slice-7 future work` — the deferral list as it stood at Slice 7 (section removed)

Bears on [Scalar field conversion][spec-001-scalars], [Relation field conversion][spec-001-relations],
[Registry][spec-001-registry] and [`DjangoType`][spec-001-djangotype].

The whole section was the spec keeping a to-do list about itself, item by item. Recorded here in
full as **claims the spec made at Slice 7 and no longer makes**; which of them the package has
since discharged is item R2's determination, and the durable place for anything still open is
`KANBAN.md`, not a shipped spec.

- **`registry.lazy_ref` and definition-order independence.** Slice 3 shipped eager-only relation
  lookup, leaving `lazy_ref` as `NotImplementedError`. Lifting the dependency-order constraint
  requires one of the three approaches recorded under the Registry entry above. "The choice point
  and test surface are captured by the `test_forward_reference_resolves_when_target_defined_later`
  placeholder."
- **`Meta.interfaces` wiring.** "Slice 2 accepted the key in `ALLOWED_META_KEYS` but never injects
  declared interfaces into `cls.__bases__` before `strawberry.type` finalizes. Consumers wanting a
  Strawberry interface (typically `relay.Node`) subclass it directly until this lands." The spec
  still carries a second copy of this claim, as the `Meta.interfaces` parking paragraph under
  `## DjangoType`; that copy is a status statement rather than deliberation and was left for R2.
- **Scalar-conversion deferrals.** `BigInt` (for plain `BigIntegerField`), `ArrayField ->
  list[inner_type]`, and `JSONField` / `HStoreField -> JSON`, "not implemented because no fakeshop
  model exercises them. Each has a `TODO(future)` comment in
  `django_strawberry_framework/converters.py`."
- **M2M relation tests.** "`convert_relation` already handles `many_to_many` … but no fakeshop
  model declares an M2M field, so the dedicated `test_relation_m2m_returns_list` placeholder stays
  skipped. Adding M2M to a fakeshop model or seeding `User.groups` for a sibling test fills this
  gap."
- **Relay `GlobalID` for primary keys.** "The open question about `MAP_AUTO_ID_AS_GLOBAL_ID`-style
  remapping resolves once a relay-support spec lands. Until then, `AutoField` / `BigAutoField` /
  `SmallAutoField` map to `int`."
- **Example schema uncomment.** "`examples/fakeshop/fakeshop/products/schema.py` is still a
  commented-out aspirational design. Slices 4 through 7 do not require it to come uncommented; the
  package and its tests work without the example schema being wired. Whichever spec ships the last
  subsystem the example depends on is responsible for the uncomment + the matching `urls.py`
  change." The coordination note that pairs with this — move every `search_fields` line into the
  doubly-commented set before uncommenting, or land FilterSet first — is instruction to whoever
  performs the uncomment, so it stayed in the spec under `### Files NOT in this spec`. Item R2 later
  found the uncomment already performed and the note's premise gone; see its entry for that heading.

### `## Open questions` — the three questions and their recommendations (section removed)

Bears on [`## N+1 strategy`][spec-001-n1] and [Scalar field conversion][spec-001-scalars].

*Moved verbatim, questions and recommendations both.*

- "Should the optimizer be opt-in via schema extensions or auto-attached whenever a `DjangoType`
  appears? Recommendation: opt-in, matching strawberry-graphql-django." **Settled as
  recommended** — the spec's own `## N+1 strategy` section specifies schema-level opt-in via
  `extensions=[DjangoOptimizerExtension()]`, so the question was already answered inside the
  document that asked it. The rejected alternative — auto-attachment on the presence of a
  `DjangoType` — lost because it takes the choice away from the consumer at schema construction,
  the one place a consumer can see it.
- "Should `id` auto-map to relay `GlobalID` behind a setting, similar to strawberry-graphql-django's
  `MAP_AUTO_ID_AS_GLOBAL_ID`? Recommendation: defer until relay support is implemented." Deferred
  to a relay-support spec by its own terms. The spec's scalar table still maps the auto-field
  family to `int`; whether that survived relay support is item R2's determination.
- "Do we want model-property optimization hints (`model_property`, `cached_model_property`) now?
  Recommendation: no; defer until the core optimizer exists." Rejected for this spec on sequencing
  grounds, not on merit.

*Claim the spec no longer makes.* That any of these three is open. A spec is a contract; a
question with a recommendation attached is a decision that was never written down as one, and
leaving it in the contract invites a later reader to re-litigate a settled call.

## Item R2 — reconciliation against the shipped package

The pass above moved deliberation out of the spec without asking whether the spec was still true.
Item R2 asked. It read the shipped package at HEAD (`0.0.14`, fifty-odd specs after this one) and
rewrote every claim spec-001 makes that the package falsifies, so the spec reads as a clean current
contract. Nothing below is in the spec: the spec states what holds, this states why it changed.

### The two judgement calls the whole pass rests on

**Spec-001 is not a description of today's package, and correcting it that way would have been
wrong.** It owns the `DjangoType` type-generation foundation. Where a later spec took ownership of a
surface, the correction is a **pointer to the owning spec**, not a restatement — a restatement is a
second copy that goes stale, and this document has already proved it goes stale in exactly that way.
`spec-002-optimizer-0_0_2.md` sets the precedent for the shape ("The O4 design record remains in
`docs/SPECS/spec-003-…`"). Where the surface spec-001 still owns simply works differently now, the
contract is restated in place.

**Not every falsified claim earns a spec edit, and not every spec edit answers a drift row.** Some
rows are the spec being *superseded* rather than *wrong*; one row was already discharged by the
rationale move and needed nothing. Conversely the two largest stale surfaces — `## Current state`
and `## Files to add` — were named by no row at all, because four rows converge in the second one
and none of them cites it by heading.

**Precedent carried from the rationale move, applied per row rather than re-decided.** A falsified
status claim is *moved* here, quoted in the spec's own tense, and listed under "claims the spec no
longer makes"; the spec keeps only the corrected contract. That reconciles `worker-1.md`'s
delete-do-not-move rule with `BUILD.md`'s requirement that this file carry every claim a decision may
no longer make. It is defensible because a builder never reads this file, so no builder can implement
a quoted retraction.

**Illustrative code blocks were the pass's hardest disposition, and every block illustrating a
package module was deleted.** Each had drifted from the module it illustrates — two of them calling a
`registry.lazy_ref` the registry has never had. The alternative considered and rejected was
*correcting* each block: rejected because an illustrative literal of every method on
`registry.py::TypeRegistry`, or of every entry in `types/converters.py::SCALAR_MAP`, is a second copy
of the source that nothing keeps in sync, which is how they drifted in the first place. Each deletion
was gated on one check — locate every normative rule the block carried in surviving spec prose first,
delete second — and each block was replaced by a symbol-qualified pointer to the module that is now
the truth. The `Meta`-key consumer examples under `## DjangoType` were kept and corrected: they
illustrate the *consumer* surface this spec owns, not package internals, so they have no module to
defer to.

### `## Current state` -> `## Prior art`

Spec: [Prior art][spec-001-prior-art].

*Deleted — the pre-implementation status paragraph.* "The package source currently contains only
`django_strawberry_framework/conf.py`. The aspirational example schema at
`examples/fakeshop/fakeshop/products/schema.py` already assumes the existence of `DjangoType`,
`DjangoConnectionField`, and `apply_cascade_permissions`. The sibling files … likewise assume a
future package surface, but none of those names exist yet."

*Why the heading changed rather than the paragraph.* A section called "Current state" is a promise to
keep describing the present, and no shipped spec can keep it — this one had been wrong about the
package's contents for the entire life of the package. What survives is the example-project fixture
the spec is written against and the prior-art survey of graphene-django and strawberry-graphql-django.
Both are durable and both are prior art in the sense the heading now claims — the fakeshop models
predate the spec and are what drove it, exactly as the two upstream libraries are — which is what
`## What both libraries overlap on` and `## References` already assume sits above them. Retitling
makes the section's obligation one it can meet.

*Alternative rejected — restate the section as the package's present state.* It would have to be
rewritten on every release, would duplicate `docs/GLOSSARY.md` (which is generated and therefore
cannot go stale), and would put the whole package's surface inside the spec of one subsystem.

*Alternative rejected — delete the section outright.* It carried **six of the spec's twenty-one**
glossary anchors, and the prior-art survey is genuinely load-bearing for the scope argument. The six
were re-sited into surviving contract prose instead — `DjangoType` into `## Goal`,
`DjangoConnectionField` and `apply_cascade_permissions` into `## Non-goals` (which already named both
in plain text), Relay Node integration into the `Meta.interfaces` paragraph, `DjangoOptimizerExtension`
and `only()` into `## N+1 strategy`. Each destination is a sentence where the concept is normative
rather than incidental, which is a better home than the survey was: the `DjangoOptimizerExtension`
link in particular used to hang off a sentence about *strawberry-graphql-django's* extension of the
same name, so it pointed a reader at this package's glossary entry from a claim about someone else's
code.

*Claims the spec no longer makes.* That the package contains only `conf.py`; that the example lives
under `examples/fakeshop/fakeshop/`; that `DjangoType`, `DjangoConnectionField` and
`apply_cascade_permissions` do not exist; that the example's `filters.py` / `orders.py` /
`aggregates.py` / `fields.py` are unimplemented placeholders (three of the four now exist and
`aggregates.py` was deleted); that the products example's integration tests live in `tests/`.

### `## Proposed public surface`

Spec: [Proposed public surface][spec-001-surface].

*Corrected.* The internal-support-module list said `converters.py` at the package root; the converter
layer moved into the `types/` package. The first correction wrote it as "the converter layer *now* at
`types/converters.py`", which smuggled the move back into the spec as a version-tense hedge — the same
shape the `## Files to add` correction removed, and the spec's own rule is that it states where a
module lives, never that it moved. The hedge is gone; the fact that it moved is this
entry's to carry. The added sentence about later public names is not new scope —
it is a boundary marker, because a reader arriving at "this spec adds three public names" from a
package that exports forty of them needs to be told the other thirty-seven are not this spec's to
explain.

*Claim the spec no longer makes.* That `converters.py` sits at the package root.

### `## DjangoType`

Spec: [`DjangoType`][spec-001-djangotype].

*Corrected — the pipeline no longer finalizes.* The section said the pipeline "registers the
resulting type … and then finalizes the class as a Strawberry type". Collection and finalization are
separate: `__init_subclass__` collects, and `finalize_django_types()` decorates. This is the single
change with the widest blast radius in the spec, because the old sentence is what made the registry's
`lazy_ref`, the relation section's "forward references", and the `## Registry` illustrative block
cohere with each other; all four moved together.

*Corrected — the abstract-intermediate rule.* "Pass through `__init_subclass__` untouched" is no
longer true and the exception is the load-bearing one: the `get_queryset` sentinel is stamped
*before* the `Meta`-absent early return precisely so a shared-scoping base is not invisible to the
optimizer. Saying "untouched" invites the naive implementation that drops a consumer's visibility
filter.

*Corrected — the deferred-key set.* `filterset_class` and `orderset_class` left
`DEFERRED_META_KEYS` at `0.0.8` and now wire through to a working filter / order surface. The spec
had both in the raising set, in prose and in a code block whose comments asserted the raise.

*Alternative rejected — enumerate the current `ALLOWED_META_KEYS` in the spec.* Seventeen keys, most
belonging to specs 018 through 048, every one of which would need this spec edited when it changed.
The spec now states the *rule* (a key moves from deferred to allowed in the change that ships its
feature) and points at the two frozensets, so the enumeration lives in exactly one place — the code.

*Corrected — `Meta.interfaces` is wired.* The parking paragraph said the key "is accepted by
validation … but not yet wired" and told consumers to subclass `relay.Node` directly instead.
`types/relay.py::apply_interfaces` has injected declared interfaces into `cls.__bases__` since
`0.0.5`. Direct subclassing survives as an equivalent spelling rather than as the workaround it was
described as, and the paragraph now says which spec owns the Relay contract it opens onto.

*Claims the spec no longer makes.* That subclass creation finalizes the Strawberry type; that a
`Meta`-less subclass is wholly untouched; that `filterset_class` or `orderset_class` raises; that
`Meta.interfaces` has no effect; that subclassing `relay.Node` directly is the recommended
workaround.

### `## Scalar field conversion`

Spec: [Scalar field conversion][spec-001-scalars].

*Corrected — five rows of the table.* `BigIntegerField` -> `BigInt`, `ArrayField` ->
`list[inner_type]` and `JSONField` / `HStoreField` -> JSON shipped (the rationale entry above records
them as deferred, which was true when it was written and is the claim R2 answers).
`FileField` / `ImageField` no longer read as `str`. **Two rows the drift table did not carry, found
by reading `SCALAR_MAP` against the table row by row rather than checking only the rows someone had
already flagged:** `PositiveBigIntegerField` moved from `int` to `BigInt` at `0.0.6` (a recorded
breaking wire-format change), and `DurationField` / `BinaryField` are **absent** from the map
entirely — Strawberry ships no first-party scalar for `timedelta` or `bytes`, so both raise the
unsupported-field-type error the section itself specifies. The spec promised conversions for two
columns that in fact fail closed, which is the most consumer-visible falsehood the pass found.

*Corrected — the auto-field family and the settled open question.* The row still maps
`AutoField` / `BigAutoField` / `SmallAutoField` to `int`, which is right, but the answer to "whether
these remap to a relay `GlobalID`" is no longer open: a Relay-Node-shaped type suppresses the
synthesized pk annotation and takes `id: GlobalID!` from the interface. The forward reference to a
question is replaced by the answer plus the spec that owns the payload encoding.

*Deleted — the `convert_scalar` illustrative block.* Its `SCALAR_MAP` literal was wrong in five
places (the same five above) and its `convert_scalar` body predates `force_nullable`, the postgres
sentinel branches, and the `__mro__` walk. Every rule it carried survives: the raise is stated in
prose directly above where the block sat, and the choices-then-null ordering is stated in
`### null=True interaction`. Replaced by symbol pointers to `types/converters.py::SCALAR_MAP` and
`::scalar_for_field`.

*Claims the spec no longer makes.* That `DurationField` maps to `datetime.timedelta`; that
`BinaryField` maps to `bytes`; that `PositiveBigIntegerField` maps to `int`; that `FileField` /
`ImageField` read as `str`; that the auto-field-to-`GlobalID` question is open.

### `## Choice field enum generation`

Spec: [Choice field enum generation][spec-001-enums].

*Corrected — the algorithm's step order and its rejection set.* The spec rejected grouped choices
*before* checking the cache; HEAD checks the cache first, so a cached column never re-derives a name
or re-runs a rejection. The spec named one rejection; HEAD raises for three — empty choices, the
grouped form, and two values that sanitize to one member. The sanitization rule the spec carried
stopped at the leading-digit `MEMBER_` prefix — coerce to `str()`, rewrite non-identifier characters,
prefix a leading digit. HEAD adds two further rewrites after those: an underscore prefix on a Python
keyword, and a `MEMBER_` prefix on a GraphQL-reserved value (`true` / `false` / `null`), a
`__`-prefixed name, or a name Python's `enum` reserves. Neither is decoration: each exists because
the naive sanitizer either crashed Python's `enum` or silently dropped a member.

*Recorded — the build core is shared with the DRF serializer path.* `build_enum_from_choices` is
called by both the model-choice path and `rest_framework/serializer_converter.py`. The spec now says
so, because the sharing is the reason the rules cannot be restated per flavor, and a reader who
changes one rejection needs to know it lands in two places.

*Corrected — the test surface.* The named file `tests/test_choice_enums.py` does not exist; the
fixture and all six named tests live in `tests/types/test_converters.py`. The fixture's mechanism was
also wrong: it registers by declaring a synthetic `app_label` on the fixture model's own `Meta`, with
no `django.apps.apps.register_model` call and no teardown from Django's app registry — an autouse
`registry.clear()` fixture is what supplies isolation. All six test names survived verbatim, which is
why the list itself was kept rather than rewritten.

*Claims the spec no longer makes.* That grouped-choice rejection precedes the cache check; that
grouped choices are the only rejection; that sanitization ends at the leading-digit `MEMBER_` prefix;
that
`tests/test_choice_enums.py` exists; that the fixture is registered via `apps.register_model` and torn
down.

### `## Relation field conversion`

Spec: [Relation field conversion][spec-001-relations].

*Corrected — the mechanism behind definition-order independence.* "Use Strawberry forward references"
describes neither what shipped nor what the glossary entry the sentence links to describes. A relation
is recorded as a `PendingRelation` behind a placeholder annotation and resolved by
`finalize_django_types()`. Consumer-written forward references are honoured too, and are now stated as
a parallel supported spelling rather than as the mechanism. The `definition-order-independence`
glossary link stays on this sentence, where the rationale move re-sited it.

*Corrected again — "on the same footing" was the wrong footing.* The parallel-spelling sentence said
consumer-written forward references are honoured "on the same footing", which reads as *also routed
through the pending-relation pass*. They are not:
`types/base.py::_build_annotations` #"fields short-circuit out of the synthesis loop" skips relation
deferral for any name in the consumer-authored set, so those annotations never
become a `PendingRelation` and Strawberry resolves them itself. The sentence now says that, and cites
the symbol. The third spelling it listed — a cross-module
`Annotated[..., strawberry.lazy("module.path")]` on a `DjangoType` relation — was dropped rather than
re-cited: `strawberry.lazy` is load-bearing in the filter / order / form input factories and pinned
there, but no test under `tests/types/` exercises it as a consumer override of a `DjangoType`
relation, and a contract sentence with no pin is a claim, not a contract. The plain string annotation
does have one, `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver`.

*Deleted — the `convert_relation` illustrative block.* It called `registry.lazy_ref`, a method that
does not exist, and returned an annotation eagerly, which is the shape definition-order independence
exists to avoid. Its cardinality rules are already the section's own cardinality table, one paragraph
above. Replaced by the real dispatch path: `types/base.py::_build_annotations` and
`types/converters.py::resolved_relation_annotation`.

*Corrected — the relation set, a factual error the drift table did not carry.* The spec said
`Meta.fields = "__all__"` surfaces `category` on Property. `Entry.property` declares
`related_name="entries"`, so Property surfaces `category` **and** `entries`. Found by reading
`examples/fakeshop/apps/products/models.py` rather than by trusting a sentence that the rationale move
had just promoted into contract prose — which is the argument for re-deriving a promoted claim at the
promotion, not only at the row that named it.

*Claims the spec no longer makes.* That `convert_relation` exists; that `registry.lazy_ref` is what
resolves a relation target; that Property surfaces only `category`.

### `## Registry`

Spec: [Registry][spec-001-registry].

*Corrected — registration is many-to-one.* "Registering the same model twice should raise
`ConfigurationError` by default" is the opposite of the shipped contract: several `DjangoType`s may
register against one model and `Meta.primary` flags the relation-resolution target. The three
collisions that *do* raise are narrower and none of them is "same model twice" — reverse collision
(one class, two models), duplicate primary, and a `primary` flag flipped on re-register. The
three-state behaviour of `get()` is stated because the relation half depends on it and the `None`
return for an undeclared-primary model is indistinguishable from "not registered" without
`types_for()`.

*Deleted — the `TypeRegistry` illustrative block.* It declared `lazy_ref` and a `register` whose body
is the retracted collision rule, and its body — `__init__`, `register`, `get`, `lazy_ref`,
`register_enum`, `get_enum`, `clear` — is not the registry's surface: the real
class also carries the pending-relation trio, the definition store, the finalization latch, the
class-to-model reverse lookup, and the multi-type / primary accessors. Replaced by prose plus a
pointer to `registry.py::TypeRegistry`.

*Corrected — `lazy_ref` is stated as absent, not silently dropped.* The rationale entry above records
that the pending-relation approach won; the spec now says the registry carries no `lazy_ref` and names
what does the job instead. Saying "no `lazy_ref`" rather than deleting the sentence is deliberate: the
name appears in the spec's own history and in the rationale, so a reader who arrives with it needs the
answer, not silence.

*Claims the spec no longer makes.* That registering one model twice raises; that the registry exposes
`lazy_ref`; that `_types` maps a model to a single type.

### `## get_queryset`

Spec: [`get_queryset`][spec-001-getqueryset].

*Corrected — the sentinel flip.* The spec pinned an implementation that is not the shipped one and
whose two differences are both correctness-bearing. HEAD calls `_detect_custom_get_queryset(cls)`,
which walks the MRO to `DjangoType`, rather than testing `"get_queryset" in cls.__dict__` on the
subclass alone; and it stamps *before* the `Meta`-absent early return rather than after the
`strawberry.type` call (which no longer happens in `__init_subclass__` at all). Both exist so an
abstract base that declares `get_queryset` without a `Meta` is visible through its concrete
subclasses. That is the exact base-class pattern `## DjangoType` invites consumers to write, so the
naive spelling the spec pinned would silently drop those consumers' visibility filters — which is why
the corrected text states the *why* rather than only the call.

*Claim the spec no longer makes.* That `__init_subclass__` runs a `cls.__dict__` membership test after
the `strawberry.type` call.

### `## N+1 strategy`

Spec: [N+1 strategy][spec-001-n1].

*The disposition this section was left open for.* The scope-creep entry above records the spec
predicting its own cut line: lift Slices 4-6, `## N+1 strategy`, the `DjangoOptimizerExtension` public
name, and the optimizer-shaped sentences in `## Goal` / `## get_queryset` into an optimizer spec. Half
of it happened — `spec-002-optimizer-0_0_2.md` exists and owns O1-O6, and the slice list points at it
— and the prose was never lifted. R2 finished the cut on the terms the maintainer set: point where a
later spec took ownership, restate where this spec still owns the surface.

**Lifted to `spec-002`, by pointer.** The extension's hook shape, the resolver-to-type tracing
paragraph, the `only()`-plus-FK-columns paragraph, the `plan_relation` integration paragraph, and the
`plan_relation` pseudocode block. Each was checked against `spec-002` before removal, and each is
stated there (O2 the walker, O3 the root-gated hook, O5 `only()`, O6 the downgrade). Three of the five
were also *wrong*: the extension is root-gated on `resolve` (`info.path.prev is None`), not a wrapper
around every resolver's `resolve` / `aresolve`; `plan_relation` returns a `(kind, reason)` pair of
strings and constructs no `Prefetch`; and the tracing paragraph reaches into `registry._types`, a
private attribute with a public `model_for_type` accessor. Deleting a wrong paragraph whose correct
version lives in the owning spec is strictly better than maintaining a second copy.

**Kept, and it is the one thing that could not be pointed elsewhere.** The PR #583 derivation —
*otherwise FK joins bypass per-type visibility filtering and leak rows*. `spec-002` states the O6 rule
("the planner avoids `select_related` … and emits a `Prefetch`") but not the reason, and its only
mention of #572 / #583 frames them as the argument for bundling the optimizer with spec-001 in the
first place. So this spec holds the sole statement of *why the downgrade exists*, a builder who does
not read it writes the leak, and `spec-002` is outside this cycle's write set. It stays here, with the
cardinality rules it depends on and the schema-level opt-in.

*Corrected — the opt-in example.* It passed a bare `DjangoOptimizerExtension()` instance in
`extensions=`, the form Strawberry warns on at the declared floor `0.316.0`, and omitted
`finalize_django_types()` entirely, so a consumer copying it got a `DeprecationWarning` and an
unfinalized schema. The callable-factory form is also what preserves the extension instance's plan
cache across operations, so the fix is a contract, not a lint.

*Corrected — the `extensions=` sentence now names its owner, and stops over-attributing the
deprecation.* Two defects in one sentence. First, the corrected text restated
`spec-029-consumer_dx_cleanup-0_0_9.md` Decision 3 — the singleton-factory form, the plan-cache
argument, and the deprecation finding are all that decision's — without naming it, which is the one
un-pointered restatement among the ten sibling corrections that each name their owning spec, and it
is a second copy of a claim about *upstream version behavior*, the copy most likely to rot. It now
names `spec-029`. Second, "the bare-instance form Strawberry deprecated in `0.316.0`" asserts which
release introduced the deprecation, and nothing in this repo establishes that. What is verifiable is
that `0.316.0` — the floor `docs/builder/BUILD.md` `## Floor verification` declares — already warns,
so the sentence reads "as of `0.316.0`". Guessing the introducing release is exactly the failure the
standing rule against reasoning from one version to hand exists to stop.

*Restored — the two rules the lift left stated nowhere, and why they came back rather than being
handed on.* Checking each lifted paragraph against `spec-002` found three of five covered and two
not. `spec-002`'s O5 entry states the mechanism ("records selected scalar columns and required FK
connector columns in `OptimizationPlan.only_fields`") without the reason, and its O6 entry covers
only the downgrade branch, so nothing anywhere stated that the ordinary many-side prefetch is
visibility-filtered too. Both are now in spec-001's `## N+1 strategy`:

- **The projection rule with its reason.** A projection over a joined relation must carry the source
  row's local FK column alongside the joined columns; masking the FK column makes Django treat the
  joined attributes as deferred and re-query on first access. Verified at HEAD rather than restored
  from the deleted paragraph: `optimizer/plans.py` #"including the FK columns required to materialize"
  states the rule, and `optimizer/walker.py::_record_relation_access` states the
  consequence of dropping it ("reintroduce the N+1") as the reason its call must precede the
  FK-elision check.
- **Visibility filtering on every branch the planner builds.** The deleted paragraph's own wording —
  *"every `plan_relation` call also runs `target_type.get_queryset(target_qs, info)`"* — is false at
  HEAD, so it was **not** restored: `optimizer/walker.py::plan_relation` returns a `(kind, reason)`
  pair and touches no queryset. The rule underneath it is true and is what the spec now states:
  `::_build_child_queryset` applies the target type's `get_queryset` to the child queryset of every
  `Prefetch` the planner builds, and `::_plan_prefetch_relation` computes that independently of *why*
  the prefetch branch fired, so the ordinary many-side prefetch is filtered on the same footing as the
  downgraded FK. The downgrade closes the one branch — a collapsed join — with no child queryset to
  apply it to.

  *The consequence clause is bounded to the querysets the planner builds, and that bound is the
  contract.* The restored paragraph first drew the consequence as a universal — that no plan branch
  could return rows the target type would have filtered out — and the package falsifies it:
  `optimizer/walker.py::_apply_hint` #"if hint.prefetch_obj is not None:" rebases a consumer-supplied
  `Prefetch` through `::_prefetch_hint_for_path` and appends it, returning before `::plan_relation`,
  the downgrade, and `::_build_child_queryset` are ever reached, so that child queryset never meets
  `utils/querysets.py::apply_type_visibility_sync`. The behaviour is deliberate — `::_apply_hint`
  #"Consumer-supplied Prefetch objects commonly close over" treats the consumer's queryset as
  authoritative and marks the plan non-cacheable for it — and the read side adds nothing:
  `types/resolvers.py::_make_relation_resolver` #"prefetched.get(accessor_name)" hands back Django's
  materialised rows. So the true width is the population `::_build_child_queryset` covers,
  and the spec states that width instead of the universal. Naming the hint surface here was rejected
  on the pass's own pointer rule: `Meta.optimizer_hints` belongs to a later spec, and a bounded claim
  needs no exception clause to be true.

  *Claim the spec no longer makes.* That no plan branch can return rows the target type would have
  filtered out.

*Alternative rejected — hand both rules to a later pass that may write `spec-002`.* The cheaper-
looking option, and the one the reviewer named first: fold the two clauses into `spec-002`'s O5 and
O6 entries in the pass that is already opening that file for two inherited cross-reference
obligations. It lost on the same reasoning that kept the PR #583 carve-out here. A hand-over is a
promise, not a discharge: until it is performed, a data-isolation rule and a fail-open-shaped
performance rule are stated in no document at all, and this cycle has already watched one hand-over
("record that the lift happened") turn out to close neither rule. The write set is the constraint
that decides it, exactly as it decided the carve-out — `spec-002` is outside this pass's writable
list, spec-001 is inside it, and a rule stated in the wrong spec is a smaller defect than a rule
stated nowhere. **If a later cycle whose scope includes `spec-002` re-homes these two rules, it must
re-home the PR #583 carve-out with them and delete all three from spec-001 in the same change** —
splitting them is how the duplication this whole item exists to remove gets recreated.

*Alternative rejected — delete `## N+1 strategy` entirely and point at `spec-002`.* It would have
deleted the PR #583 carve-out with it, and the only place to re-home that reasoning is a file this
cycle may not write. Rejected on write-set grounds, and worth re-opening only in a cycle whose scope
includes `spec-002`.

*Claims the spec no longer makes.* That the extension wraps every resolver via `resolve` / `aresolve`;
that `plan_relation` returns a `Prefetch`; that the optimizer reverse-walks `registry._types`; that
`extensions=[DjangoOptimizerExtension()]` is the supported spelling.

### `## Type naming`

Spec: [Type naming][spec-001-typenaming].

*Corrected.* "Relay connection types and edges should follow the same naming family later" was a
prediction; connections shipped at `0.0.9` and do follow it (`<TypeName>Connection`). Restated in the
present with the owning spec named. The scope sentence — this spec fixes only the object-type and
choice-enum naming rules — is unchanged and still true.

### `## What this enables immediately after implementation` (section removed)

Bears on [`## Goal`][spec-001-goal].

*Moved — the whole section.* "Once this spec lands, the placeholder example schema in
`examples/fakeshop/fakeshop/products/schema.py` can begin shedding its commented scaffold in favor of
real `DjangoType` classes. The next spec can then focus narrowly on wiring `filterset_class` into the
type and connection field, instead of having to re-solve model conversion and N+1 at the same time."

*Why removed rather than restated.* Both sentences are predictions, and the second is simply wrong
about what happened: the next spec was the optimizer, and `filterset_class` landed at `0.0.8`, six
specs later. Restating it in the past tense would have reintroduced exactly the self-narration the
rationale move removed, and `## Goal` already says what the foundation is for. It carried no glossary
anchor, so the removal cost nothing structurally.

*Claims the spec no longer makes.* That the example schema is a commented scaffold; that the next spec
wires `filterset_class`.

### `## Testing strategy`

Spec: [Testing strategy][spec-001-testing].

*Corrected — the placement rule.* "All new package tests go in a new root-level file" is falsified by
`tests/types/` and `tests/optimizer/`, and it was always the weaker half of the rule; the durable half
is that `tests/base/` is reserved, which survives. The replacement names the real modules.

*Corrected again — the replacement named two directories where the inventory names three locations.*
The first replacement said package tests for this surface live under `tests/types/` and
`tests/optimizer/`. `## Files to add`'s own inventory, two sections later, lists `tests/test_registry.py`,
which sits directly in `tests/` — so the placement rule was falsified by the same document's inventory
of the very files it governs, which is worse than the rule it replaced because a reader cannot tell
which half is current. The sentence now names the third location. It was found by reading the
reconciled spec end to end rather than section by section: the two claims sit in different sections
and answer to no shared drift row, so a pass working a claim list could not have put them side by side.

*Deleted — the illustrative test module.* It imported from `fakeshop.products` (the pre-restructure
path), asserted `ConfigurationError` on `filterset_class` (which now wires through and would leave the
test asserting a raise that cannot happen), and built a schema without `finalize_django_types()`. It
was not repairable into a useful example without becoming a copy of a real test file.

*Replaced with the two placement rules a copy of that block would have taught by accident.* The
autouse `registry.clear()` fixture is load-bearing rather than cosmetic — the registry is
process-global and refuses a new concrete `DjangoType` after finalization, so a module declaring its
own types fails from the second test onward without it. And AGENTS.md's live-first rule sends the
optimizer's query counts and the downgrade rule to `examples/fakeshop/test_query/`, which is where
they now are; the deleted block asserted them in the package tier, so a reader would have copied the
wrong tier.

*Claims the spec no longer makes.* That package tests for this surface live in one root-level file;
that `fakeshop.products` is an importable path; that declaring `filterset_class` raises.

### `## Files to add`

Spec: [Files to add][spec-001-files].

*The largest stale surface in the spec, and no drift row named it.* Four separate rows converge here —
the flat module layout, `registry.lazy_ref`, the deferred-key list, and the three test filenames — and
each row cited a different section. The lesson is that a verified drift table is a floor: it is
organized by *claim*, and a section can be wrong in four ways at once without appearing in it by name.

*Corrected — the module map.* `types.py` and `optimizer.py` are packages; `converters.py` is
`types/converters.py`. The section's opener states that layout in the present and stops there. The
per-module bullets were rewritten to the surface that actually exists, including the finalizer split
(`types/base.py` collects, `types/finalizer.py` decorates) and the fact that `BigInt` lives in
`scalars.py`, not the converter module.

*Corrected again — the restructure chronology left the opener.* The first correction kept a
translation aid: the modules "were single modules when the first slices landed and became packages
under the later restructure", so an older document's `types.py` means the package. The fact is true —
the three flat modules were added at `084b4643` and deleted at `70c7bff2` — but stating it in the
spec is the one thing `BUILD.md` `## Spec rationale extraction` forbids outright: a reader must never
have to apply a chronology to work out what is currently true. The translation aid belongs here, and
this paragraph is it. In a document written before that restructure, `types.py` means
`django_strawberry_framework/types/`, `optimizer.py` means `django_strawberry_framework/optimizer/`,
and `converters.py` means `django_strawberry_framework/types/converters.py`.

*Corrected — `exceptions.py`.* "Plus two subclasses" is now four, and the module's no-Django-imports
property is stated as the *reason* later specs have been able to add to it, which is the part a future
reader needs.

*Corrected — the three test files.* None of `tests/test_django_types.py`,
`tests/test_optimizer.py`, or `tests/test_choice_enums.py` exists. Replaced by the modules that carry
the same coverage, with the optimizer's query-count assertions correctly attributed to the live tier.

*Claims the spec no longer makes.* That the package layout is flat; that `registry.py` exposes
`lazy_ref`; that `converters.py` defines `convert_relation` or the `BigInt` scalar; that `types.py`
finalizes via `@strawberry.type`; that the three named test files exist; that no tests are added under
`examples/fakeshop/`.

### `### Files NOT in this spec`

Spec: [Files to add][spec-001-files].

*Corrected — three of the five modules shipped.* Filters, orders, and permissions have landed;
`FieldSet` and aggregates have not, and their `Meta` keys are still deferred. The section now says
which is which and names the owning spec, so "belongs to a later spec" stops being a permanent
unknown.

*Corrected — the `search_fields` coordination note.* Its premise is gone: the example schema is
uncommented and live, and the `search_fields` lines were not left in an uncommentable block — each is
individually commented beside the card that will enable it. The note's *rule* is still live, though,
which is why it was restated rather than deleted: `search_fields` is still in `DEFERRED_META_KEYS`, so
declaring one still raises at import. What changed is that the instruction now generalizes to any
future block-uncomment instead of describing one file's 2026 state.

*Claims the spec no longer makes.* That `examples/fakeshop/…/products/schema.py` is a commented
aspirational block; that its `search_fields` lines sit in an outer commented block; that
`aggregates.py` exists in the example as a design placeholder.

### `## References`

Spec: [References][spec-001-references].

*Corrected — line-number refs to symbol paths.* `AGENTS.md` rule 27 bans raw `path:NN` in a standing
doc, and this section carried four of them, all pointing into a third-party venv whose contents move
on every upstream release: the line range the spec pinned inside `graphene_django/types.py` holds
`::DjangoObjectType` today and could hold anything tomorrow. Now symbol-qualified, with the two
checkout roots named once instead of repeated in full on every line. The same substitution was
applied to the two surviving prior-art paragraphs.

### Drift rows that changed nothing, and why

- **M2M coverage.** The claim that no fakeshop model declares an M2M field and the dedicated test
  placeholder stays skipped left the spec with the rationale move, inside
  `Slice 3 status (post-implementation)`, and is already listed among that entry's claims the spec no
  longer makes. R2 confirmed it against HEAD — `library.Book.genres` / `alt_branches` are M2M and
  `tests/types/test_definition_relations.py` covers both directions — and made no edit. A row can be
  discharged by a prior pass; re-editing to "answer" it would have added text saying nothing.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-001]: ../spec-001-django_types-0_0_1.md
[spec-001-djangotype]: ../spec-001-django_types-0_0_1.md#djangotype
[spec-001-enums]: ../spec-001-django_types-0_0_1.md#choice-field-enum-generation
[spec-001-files]: ../spec-001-django_types-0_0_1.md#files-to-add
[spec-001-getqueryset]: ../spec-001-django_types-0_0_1.md#get_queryset
[spec-001-goal]: ../spec-001-django_types-0_0_1.md#goal
[spec-001-n1]: ../spec-001-django_types-0_0_1.md#n1-strategy
[spec-001-prior-art]: ../spec-001-django_types-0_0_1.md#prior-art
[spec-001-references]: ../spec-001-django_types-0_0_1.md#references
[spec-001-registry]: ../spec-001-django_types-0_0_1.md#registry
[spec-001-relations]: ../spec-001-django_types-0_0_1.md#relation-field-conversion
[spec-001-scalars]: ../spec-001-django_types-0_0_1.md#scalar-field-conversion
[spec-001-slices]: ../spec-001-django_types-0_0_1.md#suggested-implementation-slices
[spec-001-surface]: ../spec-001-django_types-0_0_1.md#proposed-public-surface
[spec-001-testing]: ../spec-001-django_types-0_0_1.md#testing-strategy
[spec-001-typenaming]: ../spec-001-django_types-0_0_1.md#type-naming
[spec-002]: ../spec-002-optimizer-0_0_2.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
