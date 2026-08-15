# Rationale: spec-002 — Optimizer & reverse-relation resolution (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-002-optimizer-0_0_2.md`][spec-002]. The spec is the contract and
states only what holds; everything that explains **how it got there** lives here: the alternatives
each decision rejected and why each lost, the derivations that do not change how a decision is
implemented, the chronology the spec used to narrate about itself, and every claim the spec once
made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-002-0.0.2` shipped twelve patch
versions ago and the rule that gates a build on this move did not exist then; this pass supplies
it. Text marked *Moved* below was cut out of the spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec section**, named by the section's own heading and linked to its anchor. A
  section whose text did not move has no entry here — that is not an omission, it means the whole
  section is contract.
- **Who reads it.** The role-by-role answer is [`BUILD.md`][build] `### Who reads it, and when`,
  which is that mechanism's canonical home; a copy here would go stale silently. A reader looking
  for what the package *does* wants the spec, not this file.
- **This spec has no numbered Decisions.** It predates that convention, so the key is the heading.
  Three entries key to headings that no longer exist in the spec at all (`## O4 extraction`,
  `## Open questions`, and `## Current state`); each names the surviving section its argument bears
  on. Sub-headings are keyed to their parent section's anchor rather than their own: the `### O`
  slice headings carry an em dash, and the two sluggers in play disagree on how many hyphens that
  produces, so a sub-heading anchor here would be unverifiable by the one checker that could verify
  it.
- **Two passes wrote this file, and they had different jobs.** The rationale-extraction pass
  (`## Provenance of this record`) moved the deliberative layer out of the spec and deliberately did
  **not** reconcile the spec against the shipped package: every claim it recorded is recorded **as
  the spec made it**, in the spec's own tense. The reconciliation pass
  (`## Provenance of the reconciliation record`) is the one that read HEAD and decided which of those
  claims still hold. Where the two disagree about a claim's status, the reconciliation pass is
  current.
- **Read `## Standing notes` before editing the spec.** It records one deliberate gap (the terms
  CSV stands at three anchors) and three wordings that read as defects and are not. All four are
  decisions already taken, and all four are things a passing sweep would otherwise "correct".
- **This spec is the parent of an optimizer family.** `spec-003` (nested prefetch chains),
  `spec-004` (optimizer beyond), and the later `spec-033` / `spec-035` optimizer specs own the
  detail. Deliberation belonging to one of those documents is not duplicated here.

## Provenance of this record

- **Moved** — cut from the spec by this pass, and now only here: the `## Problem statement`'s
  opening chronology (the `spec-001` prediction, what confirmed it, and the "pushed the optimizer
  story into its own subsystem" framing); the `## Purpose` sentence recording that O4 "was extracted
  out of this document during implementation"; the whole of `## O4 extraction`; the
  `## Architecture decision` justification for keeping generated relation resolvers alongside the
  optimizer; the whole of `## Open questions`; and the `## References` clause recording that the
  issue #572 / PR #583 discussion is what originally motivated bundling the optimizer with
  `spec-001-django_types-0_0_1.md`.
- **Restated in the spec, not moved** — two rules that lived inside moved prose. The scope rule —
  now `## Purpose`'s "It records that behavior at a high level only" — and the O4 ownership
  pointer, which `## Purpose` and `## O4 extraction` each carried a half of; they are now one
  paragraph in `## Purpose`. And the two conditions under which a generated relation resolver must
  still be correct, which were stated as a justification and are now stated as a requirement in
  `## Architecture decision`.
- **Deliberately left in the spec by this pass** — `## Current state`, `## Shipped slices`,
  `## Visibility status`, and the `## Implementation checklist`. These are status claims, not
  deliberation: a status claim moved into a rationale file is neither a legitimate entry here nor
  the deletion the move prescribes for falsified prose, and their disposition against the shipped
  package is item R2's call. Also left: the whole of `## Coordination with
  spec-001-django_types-0_0_1.md`, which states the division of ownership normatively rather than
  narrating how it was reached, and `## References`, which is contract scaffolding — every locator
  it carries stayed, including issue #572 and PR #583; only the clause recording what that
  discussion once motivated moved.

## Provenance of the reconciliation record

The reconciliation pass read the shipped package and rewrote every spec claim the package
falsifies. It moved no deliberation; it produced a **change record**, and that record is the
`*Changed —*` and `**Claims the spec no longer makes.**` material in the entries below.

- **Rewritten in the spec** — the O1 attachment site and resolver shapes, the O2 planner signature
  and field-map lookup, the O3 context stash, the O5 projection gate, the O6 visibility boundary, the
  `## Architecture decision` root-gate paragraph, and the `## Purpose` scope rule's extension from
  one sibling spec to the whole optimizer family. Each is stated as the contract that holds, with no
  trace of the claim it replaced; what it replaced is recorded here.
- **Removed from the spec** — the whole of `## Current state`. It carried five facts. The O1-O6
  roster and the plan-on-context stash were already stated in `## Shipped slices`, and the
  extension's public status was already stated — at lower precision, without the import path — in
  `## Visibility status`. Of the two that were genuinely only there, O2's module path moved to the O2
  slice paragraph and the export path was merged into `## Visibility status`; the fifth, that the
  extension is covered by the optimizer test suite, is a claim about the repository's test tree
  rather than a contract, and is simply gone. The reasoning, and the retitle alternative it was
  chosen over, is the entry below.
- **Deliberately NOT restated in the spec** — every behavior a later optimizer spec owns beyond a
  one-clause pointer: the `OptimizationPlan`'s full field inventory and its immutability contract,
  the optimizer's context-key vocabulary and its start-of-execution reset, the sealed visibility
  boundary's own rules, the nested-connection fetch strategies, and `Meta.optimizer_hints`. Each is
  named where a reader of this spec would otherwise be misled, and nowhere else.
- **Verified and left alone** — `## References` (all four upstream locators re-checked against the
  checkouts `AGENTS.md` names, all present), `## Problem statement`, `## Coordination with
  spec-001-django_types-0_0_1.md`, and `## Implementation checklist`.

## Entries keyed to the spec

### Whole-document scope — why the optimizer became its own document

Spec: [Problem statement][spec-002-problem], and bears on [Purpose][spec-002-purpose],
[Coordination with `spec-001-django_types-0_0_1.md`][spec-002-coordination], and
[References][spec-002-references].

*Moved — the chronology of how this document came to exist.* The spec opened its problem statement
with its own provenance: "`spec-001-django_types-0_0_1.md` predicted that the optimizer half of its
scope would eventually warrant its own document; running the early DjangoType slice tests confirmed
it." That prediction, the argument that produced it, and the cut line `spec-001` named for itself
are recorded in [`spec-001-django_types-0_0_1-rationale.md`][spec-001-rationale] under
*"Whole-document scope — the optimizer was bundled deliberately"*; this pass did not duplicate them
here. What is worth keeping on this side of the split is that the prediction was not acted on
speculatively — it was acted on when running the early `DjangoType` slice tests produced the two
concrete failures the spec now lists as its problem statement.

*Moved — the framing of those two failures.* The spec read "Two concrete failures pushed the
optimizer story into its own subsystem", which is an account of a document boundary rather than a
statement of the problems. The two problems themselves stayed, restated as what they are: the two
problems in relation resolution that define the subsystem. The seam sentence that follows them
("how the framework gets from Strawberry field resolution to the underlying Django model relation")
also stayed — it names where the code lives, not how the document was assembled.

*Alternative rejected — leave the optimizer inside `spec-001`.* Recorded in `spec-001`'s own
rationale rather than restated here; the short form is that a foundation spec which resolves
relations across the ORM graph is broken-by-default without an N+1 answer, so the two were specced
together first and split once the type-system half had shipped. This document is the second half of
that split, taken on the slice axis: `spec-001`'s Slices 4-6 point here.

*Moved — what the spec recorded as the trigger for that original bundling.* Its `## References`
named the upstream visibility-leak / `Prefetch` downgrade discussion — issue #572 and PR #583 on
`strawberry-graphql/strawberry-django` — as the discussion "that motivated bundling the optimizer
with `spec-001-django_types-0_0_1.md` originally". The reference itself is contract scaffolding and
stayed, pointing at the same issue and PR; the account of what it once motivated is document
history and belongs here, beside the alternative it explains.

**Claims the spec no longer makes.** None. Nothing normative left this section — the removed text
was provenance in every sentence, the `## References` clause included: it named a document-assembly
decision, never a behavior of the package.

### `## Purpose` and the former `## O4 extraction` — the O4 record moved to `spec-003`

Spec: [Purpose][spec-002-purpose]. The `## O4 extraction` heading no longer exists.

*Moved — the chronology.* "O4 was extracted out of this document during implementation." A reader of
the current spec needs to know where the O4 record lives, not when it got there; that sentence is
the spec narrating its own history, which is precisely what the spec is not for.

*Moved — the duplicate section.* `## O4 extraction` said, in full: "The detailed O4 implementation
record lives in `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`. This parent spec
only records the shipped behavior at a high level." Both sentences were already stated, in slightly
different words, in `## Purpose` — the ownership pointer verbatim and the scope rule not at all.
Two statements of one fact in one 113-line document is the mechanism by which a spec goes stale in
one place and not the other, so the section was cut and the scope rule folded into the `## Purpose`
paragraph that already carried the pointer.

**The scope rule is contract, and it stayed** — as `## Purpose`'s "It records that behavior at a
high level only". That rule is what stops this document being rewritten into a summary of
`spec-003`, `spec-004`, `spec-033`, and `spec-035`. It was the more load-bearing half of a section
that was otherwise pure self-narration, which is why the section was folded rather than simply
deleted.

**Claims the spec no longer makes.** None; the fold preserved both facts the section carried.

### `## Architecture decision` — why the optimizer does not subsume generated relation resolvers

Spec: [Architecture decision][spec-002-architecture].

*Moved — the derivation.* The spec justified the generated relation resolvers' continued existence:
"Generated relation resolvers remain necessary even with the optimizer because they provide correct
behavior when the optimizer is disabled or when a relation is not already loaded." The question
behind that sentence is a real one and was worth answering once — a root-gated planner that already
walks the selection tree and attaches `select_related` / `prefetch_related` looks, from a distance,
like it makes a per-relation resolver layer redundant.

*Alternative rejected — let the planned root queryset be the only path to a relation.* It loses on
two independent conditions, and both are conditions the package cannot control:

- **The optimizer can be absent.** [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]
  is an extension a consumer adds to `strawberry.Schema(..., extensions=[...])`. A schema without
  it is a supported schema, and every relation field on it must still resolve.
- **A relation can be unplanned even when the optimizer is installed.** The plan is built from the
  selection tree at the operation root; a relation reached by any path the root plan did not cover
  is reached with nothing prefetched.

So the resolver layer is not an optimization the planner supersedes — it is the correctness floor
the planner sits on top of. That is why the spec now states the two conditions as a **requirement**
on the resolvers rather than as a reason they survived: what a builder needs from this paragraph is
"these must work with no plan in hand", and a builder never reads this file.

**Not deliberation, and it stayed:** the sentence that generated relation resolvers host the B2/B3
runtime sentinels. That is a statement of what the layer is *for*, consumed by O6 and by later
optimizer behavior, and moving it would have taken a mechanism out of the spec.

**Claims the spec no longer makes.** None. The restatement is the same two conditions in the
normative voice a contract uses; it neither weakens nor widens them.

### The two questions this spec left open (former `## Open questions`)

Spec: [Shipped slices][spec-002-shipped], bearing on O1 and O5. The `## Open questions` heading no
longer exists. Also bears on [`spec-004-optimizer_beyond-0_0_3.md`][spec-004], which this spec
named as the future optimizer-control document.

*Moved — both questions, in the spec's own tense.* Recorded verbatim, because a question a spec
carried is the deliberation a later spec answers, and the answer is worthless without the question:

> **Custom resolver opt-out**: consumers should eventually be able to override generated relation
> resolvers with their own resolver. The generated resolver should only fire when no
> consumer-declared resolver exists for that field.

> **`only()` opt-out per consumer field**: strawberry-graphql-django ships
> `disable_optimization=True` on individual fields. A similar flag should be considered in a future
> optimizer-control spec.

Both are shaped as *questions about a contract this spec deliberately did not write*, not as
statements about what the package does. The first names the precedence rule it would want
(consumer-declared wins) without saying how a consumer-declared resolver is detected; the second
names an upstream feature and declines to copy its shape, deferring even the decision of whether to
have one.

**Why they moved rather than being deleted.** The move rule deletes prose the current decisions have
falsified and moves deliberation. An open question is deliberation by construction: it records that
the spec's authors saw a gap, framed it, and chose not to close it in this document. Whether either
question is still open at HEAD is not something this pass established — it is item R2's
determination, and the answer belongs in the spec (as contract, if the answer shipped) or in this
file's change record (as a claim the spec no longer makes).

**Claims the spec no longer makes.** The spec no longer claims to carry any open question. It made
neither of the two above as an assertion about the package, so nothing normative was retracted by
removing them.

**Both questions are answered at HEAD, and they were routed differently.** This is the
reconciliation pass's determination, which the extraction pass explicitly left to it.

- **Custom resolver opt-out — answered, and the answer is this spec's own contract.** The generated
  relation resolvers skip any field the consumer assigned a resolver to; the skip set is
  `DjangoTypeDefinition.consumer_assigned_relation_fields`, passed into
  `django_strawberry_framework/types/resolvers.py::_attach_relation_resolvers`, and the file/image
  twin `_attach_file_resolvers` takes the broader `consumer_authored_fields`. The precedence rule the
  question asked for — consumer-declared wins — holds exactly as asked. Because that behavior lives
  inside O1's own attachment pass, it is stated in `## Shipped slices` as contract rather than
  recorded here as history. The introspection surface it rests on is specified by
  [`spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019] and extended by
  [`spec-037-upload_file_image_mapping-0_0_11.md`][spec-037].
- **`only()` opt-out per consumer field — answered, and the answer is NOT this spec's contract.**
  [`spec-004-optimizer_beyond-0_0_3.md`][spec-004] B4 specifies `Meta.optimizer_hints` with the
  `OptimizerHint` typed wrapper, and names it "the DRF-shaped analog of strawberry-graphql-django's
  `disable_optimization=True` per-field marker, but richer" because it allows positive overrides, not
  only opt-out. The question declined to copy the upstream shape and deferred even the decision of
  whether to have one; `spec-004` decided both. Nothing about it is restated in this spec: an option
  another spec specifies and `docs/GLOSSARY.md` catalogues is precisely the surface the scope rule
  exists to keep out.

*Alternative rejected — restate both answers in the spec, on the reasoning that "the question was
this spec's, so the answer is too".* It loses on the test that actually discriminates: not whether
the answer shipped, but **whose contract the answer is**. Applied to the second question it would
have pulled a `Meta` option, its typed wrapper, and its validation rules into a parent spec that
explicitly records its family at a high level only — the failure mode the scope rule names. Applied
to the first it happens to give the right result, which is why the weaker test is tempting.

### The removed `## Current state` — a standing-promise heading that was also a duplicate

Spec: [Shipped slices][spec-002-shipped], which absorbed the O1-O6 roster, the context stash, and
O2's module path. The one fact that went elsewhere — the extension's public-surface status, merged
into `## Visibility status` — is no longer in this spec at all: the `spec-006` cycle retired that
section as a cross-spec duplicate, and `## The discharged deferral — Visibility status retired by
the spec-006 cycle` at the end of this file records why. The `## Current state` heading no longer
exists.

*Changed — the section was removed rather than retitled.* It listed O1-O6 as one-liners and then
made three statements about the extension. Read against the rest of the document, most of it was
already in the document: the O1-O6 roster appeared in `## Shipped slices`' six sub-headings and
again in `## Implementation checklist`'s six boxes — a *three-way* duplication of one roster — the
context stash appeared in the O3 slice paragraph, and the extension's public status appeared in
`## Visibility status`. Two statements of one fact are how a spec goes stale in one place and not
the other; that is the same argument that folded `## O4 extraction`.

Only two facts were genuinely only there, and they went different ways. O2's module path moved to
the O2 slice paragraph, beside the symbol it qualifies. The `__init__` export path — the one
precision `## Visibility status` lacked — was merged into that section's existing public-surface
sentence.

*Moved — the last fact, which is not contract at all.* "The extension is covered by the optimizer
test suite" is a claim about the repository's test tree, true at HEAD (`tests/optimizer/`,
seventeen modules including `test_extension.py`) and true of essentially every shipped surface in
the package. A spec that asserts its own coverage is asserting something the coverage gate already
enforces and that no reader can act on.

*Alternative rejected — retitle `## Current state`, following `spec-001`.* The precedent is real:
`spec-001`'s residual cycle retitled its own `## Current state` to `## Prior art` on the reasoning
that a section named for the present is a promise no shipped spec can keep, and the deferral this
spec inherited names that precedent explicitly. It loses here on content. `spec-001`'s section
*contained* a prior-art survey, so the new title described what was there; `spec-002`'s contains a
shipped-slice roster, so the same title would be false and any honest replacement
("Shipped surface", "Delivered slices") would name the section immediately below it. A retitle would
have kept the duplication and bought only the heading.

*Alternative rejected — retitle `## Shipped slices` and `## Implementation checklist` too, on the
same standing-promise argument.* They survive it on their merits. "Shipped" is a past-tense fact
about slices that did ship and cannot become untrue; a checklist of what this spec's build delivered
is a closed record, not a promise about the present. The argument the deferral makes is against a
section named for *now*, and after this pass the spec has exactly one such heading left.

*Not rejected, and not this cycle's to change — `## Visibility status`.* It is named for the
present and so is in the deferral's target set, but
[`spec-006-public_surface-0_0_3.md`][spec-006] cites it **by section title, twice**, as the place
the optimizer-visibility decision is recorded. That sibling is read-only in this cycle, so retitling
here would break a live cross-spec pointer to buy a heading. The rule the pass followed: do not
rename a heading another file cites; fix it in the citing file instead, in the cycle that owns that
file.

**Claims the spec no longer makes.** That the O1-O6 roster is a statement of *current state* — the
spec now states only that the six slices shipped, which is a fact about the past that stays true.
That the extension is covered by the optimizer test suite. Nothing else: every other sentence the
section carried survives somewhere in the spec.

### `## Purpose` — why the scope rule now names four specs instead of one

Spec: [Purpose][spec-002-purpose].

*Changed — the family scope rule.* The rule preserved by the extraction pass ("It records that
behavior at a high level only") named exactly one owner, `spec-003`, because that was the only
optimizer spec that existed when it was written. Four now own optimizer surface, and the
reconciliation had to decide, ten separate times, whether a behavior belonged in this spec or in one
of them. A rule that licenses only the `spec-003` split cannot answer those ten questions, so the
paragraph now states the general form over the whole family — state what holds, name the owner in
one clause, restate none of the owner's rules.

That sentence is contract, not narration — it constrains what a future author may write here — which
is why it is in the spec rather than only in this file.

*Alternative rejected — leave the rule naming `spec-003` only and decide each pointer ad hoc.* Ten ad
hoc judgements that agree with each other by luck are indistinguishable, to the next reader, from ten
judgements that do not. The rule is also the only durable defence: a parent spec of four children is
rewritten into a summary of them one well-meaning clause at a time, and the pass that does it will be
reading this document, not this file.

**Claims the spec no longer makes.** None. The rule was widened, not reversed; the `spec-003` pointer
it already carried is unchanged and verbatim.

### `## Architecture decision` — the root gate, and the second caller

Spec: [Architecture decision][spec-002-architecture].

*Changed — "Non-root resolvers and non-`QuerySet` values pass through unchanged".* False at HEAD in
one specific and consequential way: a Django `Manager` is a non-`QuerySet` value and it does **not**
pass through. It is coerced through `django_strawberry_framework/utils/querysets.py::normalize_query_source`,
so a resolver returning `Model.objects` is optimized rather than silently skipped — the same
Manager-coercion decision the list and connection consumer paths use, which is why it lives in a
shared helper and not in the middleware. A reader who wrote a resolver returning a manager and
believed this spec would have expected no optimization and gotten it.

*Changed — the evaluated-queryset pass-through.* A second thing passes through that the sentence did
not cover: a queryset whose `_result_cache` is already populated. The reason is stated because it is
the kind of "why" that changes how the gate is built — plan application clones, and a clone of an
evaluated queryset re-executes the consumer's SQL — but the guard's own rules belong to
[`spec-035-optimizer_hardening-0_0_10.md`][spec-035] and are named rather than restated.

*Changed — "The optimizer runs from Strawberry's `SchemaExtension.resolve` hook".* True but no
longer exclusive, and the sentence reads as exclusive. `DjangoConnectionField` calls the shared
plan-and-apply tail (`DjangoOptimizerExtension.apply_to`) directly, because Strawberry's connection
slicing hides the pre-slice queryset from schema middleware — so a claim that the optimizer runs
*from* the resolve hook would tell a reader the connection field is unoptimized, which is the
opposite of true. One implementation, two entry points; the connection path is
[`spec-033-connection_optimizer-0_0_9.md`][spec-033]'s.

*Alternative rejected — describe the connection field's cooperation point here.* It is a whole
subsystem (slicing, cursor parity, windowed nested fetch) with its own spec. What this spec owes its
reader is the single architectural fact that plan application has two callers; anything past that is
`spec-033` restated worse.

**Claims the spec no longer makes.** That every non-`QuerySet` value passes through unchanged. That
`resolve` is the optimizer's only entry point into plan application.

### `## Shipped slices` — the six slices, reconciled against the package

Spec: [Shipped slices][spec-002-shipped]. Each item names its `###` slice.

*Changed — O1's attachment site.* The spec said `DjangoType.__init_subclass__` attaches one resolver
per relation field. Attachment moved to the finalization pass:
`django_strawberry_framework/types/finalizer.py::finalize_django_types` calls
`_attach_relation_resolvers` in its Phase 2 window, before Strawberry freezes the class.
`__init_subclass__` is still where the `_is_default_get_queryset` sentinel is stamped, so the
`## Coordination` paragraph that depends on *that* was correct and now says where the stamping
happens; only the resolver attachment moved.

*Changed — O1's forward and many-side resolver shapes.* Two qualifiers the spec stated without.
A forward FK / OneToOne resolver returns the related attribute *except* under B2 FK-id elision,
which substitutes a stub carrying only the target's identifier — B2 is already this spec's
vocabulary (`## Architecture decision` names the B2/B3 sentinels), so naming the exception costs
nothing and omitting it makes the sentence false on a shipped path. And the many-side no longer
returns `list(manager.all())` unconditionally: the rows are bounded by the request resource policy,
so the spec now states the shape it promises (a materialized list, so Strawberry receives an
iterable) and names [`spec-047-resource_policy-0_0_14.md`][spec-047] for the bound.

*Alternative rejected — state the row bound's own rules here (where the ceiling comes from, what
happens at it).* That is a request-scoped policy subsystem with its own spec. O1's promise is the
iterable; the ceiling is somebody else's contract that O1 must not contradict.

*Changed — O2's signature.* `plan_optimizations` takes two further keyword-only parameters,
`runtime_prefixes` and `source_type`, both defaulting to `None`. A spec that publishes a signature
publishes the whole signature or none of it; a reader calling it with the three-parameter form the
spec gave would still work, which is exactly why the omission would survive unnoticed.

*Changed — O2's field map.* The spec routed relation fields through `_optimizer_field_map`. **No
such symbol exists in the package.** HEAD reads `DjangoTypeDefinition.field_map`, resolved by
`django_strawberry_framework/optimizer/walker.py::_resolve_field_map`. A spec naming a symbol the
package does not have is the worst failure available to a document whose whole job is to be checkable
against source, so this row was rewritten rather than pointed elsewhere even though the consolidation
that renamed it belongs to another spec.

*Changed — O3's context stash.* "Stashed on context for introspection" understated it to a
diagnostic. The stash is also the hand-off the generated relation resolvers read — the B2 elision
set and the B3 planned-key set are how a resolver knows what the plan already covered — so the spec
now says the stash serves both and that the extension owns its per-execution lifetime. The key
vocabulary itself, and the reset that enforces that lifetime, are named by module and left to the
specs that added them.

*Changed — O4 and nested Relay connections.* The spec's statement is still true for plain relations
and is unchanged. What it does not cover is a nested connection selection, which is not planned as a
plain `Prefetch` at all; that is delegated to the connection optimizer's own seam, and a one-clause
pointer at [`spec-033-connection_optimizer-0_0_9.md`][spec-033] is the whole edit. O4's detailed
record is `spec-003`'s by this spec's own rule, so nothing about the nested machinery is described
here.

*Changed — O5's projection gate.* Unqualified, the spec's O5 sentences are false for mutations and
subscriptions: the walker records no projected fields under a non-`QUERY` operation, so the returned
queryset carries `select_related` / `prefetch_related` and no column deferral. The gate is
[`spec-035-optimizer_hardening-0_0_10.md`][spec-035]'s and is named, not re-specified. Note that
`OptimizationPlan.apply()`'s own behavior is unchanged and the spec's sentence about it stayed
verbatim — the gate is upstream of `apply()`, in what the walker records.

*Changed — O6's invocation of the target `get_queryset`.* The downgrade decision is unchanged and is
this spec's. What changed is that the planner no longer calls the target's `get_queryset` itself:
every framework-owned invocation runs through the shared visibility boundary
(`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`), which hands the
planner a framework-owned queryset to compose over. That is the fact an O6 reader needs, because it
is why the queryset the `Prefetch` carries is not simply whatever the consumer's hook returned; the
boundary's own contract is [`spec-045-visibility_boundary-0_0_14.md`][spec-045]'s.

*Alternative rejected — restate the `OptimizationPlan`'s current field inventory.* The plan carries
eleven dataclass fields (`django_strawberry_framework/optimizer/plans.py::OptimizationPlan`; three
further annotated names are `ClassVar` constants) plus a `finalize()` immutability contract. The
spec's claim is that O2 "produces an `OptimizationPlan`", which is true, and the only plan attribute
it names is `OptimizationPlan.only_fields`, which is O5's own. Enumerating the other ten is the scope
trap in its purest form: a parent spec that publishes a plan's field inventory goes stale the next
time any optimizer slice adds a field. Left unchanged deliberately, and recorded here so it is not
re-raised as an omission.

**Claims the spec no longer makes.** That relation resolvers are attached at
`DjangoType.__init_subclass__`. That a forward FK resolver always returns the related attribute.
That the many-side returns `list(manager.all())` unconditionally. That `plan_optimizations` takes
three parameters. That a symbol named `_optimizer_field_map` exists. That the context stash is for
introspection. That column projection applies to every operation. That the planner invokes a target's
`get_queryset` directly.

## Standing notes — deliberate gaps, and wordings not to "fix"

Neither of these is a deferral. They are the reverse: decisions already taken, recorded here because
a do-not-touch note is worth nothing in a place nobody reads before editing. Anyone opening
[the spec][spec-002] to correct something should read this section first.

### The terms CSV stands at three anchors, and four unlinked terms are deliberate

`spec-002-optimizer-0_0_2-terms.csv` carries three data rows and three distinct anchors, each
carried by exactly one link in the spec body. Four further glossary-backed terms are named in that
body **without** a link: `DjangoConnectionField` (in `## Architecture decision`),
`finalize_django_types` and FK-id elision (both in `### O1`), and the visibility boundary (in
`### O6`).

That gap is not an oversight. `AGENTS.md` rule 26 gives glossary fold-in to the **completing spec's
shipping slice**, and this spec's shipping slice closed at `0.0.2`; a later pass that adds a link
without owning the fold-in desynchronizes the CSV from the board. Reopening therefore requires a
cycle that owns both this spec's body **and** card 2's board record — not a documentation sweep that
happens to be passing through.

If such a cycle does open, the order is mechanical and worth not re-deriving: add the link to the
spec body first, then the CSV row, then run `check_spec_glossary` and `import_spec_terms --check`
together (the first validates the pair, the second validates every done card's links, so a green
first command is not sufficient), and only then re-render `KANBAN.md`. Adding the CSV row before the
body link fails `check_spec_glossary` on an anchor nothing carries.

### Three wordings that look like defects and are not

Each was examined and deliberately left. A later reader is likely to reach for the same three.

*The repeated `when` in `## Architecture decision`* — "must return correct results **when** the
optimizer is disabled **and when** a relation is not already loaded". The repetition is the
disambiguator: it distributes the obligation across two independent conditions rather than one
conjunction of them. Collapsing it to a single `when` silently narrows the contract to the case
where both hold at once.

*"Where one of them changed how one of the slices below behaves" in `## Purpose`* — the only
before-implying verb in the reconciled spec, and the one thing a chronology sweep will flag. It
survives because the change it describes is a **sibling spec changing package behavior**, not this
document changing its own text. The rule forbids a spec narrating its own revision history; it does
not forbid stating that another spec moved a contract.

*The rationale pointer appears three times, not five* — in `## Purpose`, `## Problem statement`, and
`## Architecture decision`. A literal reading of the per-section pointer convention yields five. On a
document this short, five would make the pointer the loudest recurring element in three consecutive
sections and would crowd out the contract it is annotating. Three was chosen for that reason; do not
"complete" the set.

## The discharged deferral — Visibility status retired by the spec-006 cycle

Appended by the `spec-006` residual cycle, which owns the citing file and therefore owned the fix.
The closing note of the removed-`## Current state` entry above deferred one heading — "*Not rejected,
and not this cycle's to change — `## Visibility status`*" — on the rule that you do not rename a heading
another file cites; you fix it in the citing file instead, in the cycle that owns that file. That
cycle has now run, and this entry is the other half of that deferral. The deferral was correctly
reasoned and is left standing above: it recorded a constraint that held while spec-006 was
read-only, and the constraint is what routed the work to the right cycle rather than blocking it.

*The section is removed, not retitled.* Both of its sentences state facts this spec already carries
or does not own. That O1 through O6 have shipped is already the six sub-headings of
`## Shipped slices` and the six ticked boxes of `## Implementation checklist` — the heading made it a
third copy of one roster. That the optimizer is public via the extension, exported from the package
root, is a claim about the **package's public surface**, which is
`spec-006-public_surface-0_0_3.md`'s to make; its
`#### Decision for 0.0.3` states the rule, the two supported import forms, and where the exported
roster is pinned, so it is a strict superset of the sentence removed here. Under the single-ownership
rule a concrete claim lives in one spec only, and provenance settles which copy is the surplus one:
this section existed **because spec-006 asked for a copy**, in a coordination bullet whose exact
wording, and the reasoning that made it the requester rather than the owner, are recorded in
spec-006's own rationale companion. That bullet is gone, so the copy has no requester.

*The merged `__init__` export path, which is the one thing a deletion could silently lose.* This
file's own record of the `## Current state` removal states that the export path "was merged into that
section's existing public-surface sentence" as "the one precision `## Visibility status` lacked".
Retiring the section retires that precision from this spec. That is a deliberate loss, not an
oversight: the precision is a public-surface fact, and it is stated at higher resolution in the spec
that owns the surface.

*Alternative rejected — keep one sentence in `## Shipped slices` naming the extension's import path,
stated as contract rather than as status.* It was the smaller residue and it was on the table. It
loses because a smaller duplicate is still a duplicate: the retirement exists to remove a second
place the same fact can go stale, and a one-sentence copy inside the roster section reintroduces
exactly that at a location no cross-reference points at, which makes the next drift harder to find
rather than easier. Standing alone does not require this spec to restate the surface — its subject is
the optimizer's behavior, every slice below names its own symbols and module paths, and a reader who
needs the import form has two places that own it (`docs/GLOSSARY.md` `## Public exports` and
spec-006's decision).

*Alternative rejected — retitle rather than delete, following the `spec-001` `## Current state` →
`## Prior art` precedent this file weighs above.* It loses for the same reason it lost there and one
more: a retitle preserves the duplication the retirement exists to remove, and here the heading was
never the defect — the second copy was.

**Claims this spec no longer makes.** That O1 through O6 have shipped, as a statement under its own
heading; the fact survives as `## Shipped slices`' structure and the checklist's ticked boxes. That
the optimizer is public via the extension, or that the extension is exported from
`django_strawberry_framework.__init__` — both are now made only where the public surface is owned.
No slice's behavior claim changed, and nothing else in the spec was touched by this cycle.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-djangooptimizerextension]: ../../GLOSSARY.md#djangooptimizerextension

<!-- docs/SPECS/ -->
[spec-001-rationale]: spec-001-django_types-0_0_1-rationale.md
[spec-002]: ../spec-002-optimizer-0_0_2.md
[spec-002-architecture]: ../spec-002-optimizer-0_0_2.md#architecture-decision
[spec-002-coordination]: ../spec-002-optimizer-0_0_2.md#coordination-with-spec-001-django_types-0_0_1md
[spec-002-problem]: ../spec-002-optimizer-0_0_2.md#problem-statement
[spec-002-purpose]: ../spec-002-optimizer-0_0_2.md#purpose
[spec-002-references]: ../spec-002-optimizer-0_0_2.md#references
[spec-002-shipped]: ../spec-002-optimizer-0_0_2.md#shipped-slices
[spec-004]: ../spec-004-optimizer_beyond-0_0_3.md
[spec-006]: ../spec-006-public_surface-0_0_3.md
[spec-019]: ../spec-019-consumer_overrides_scalar-0_0_6.md
[spec-033]: ../spec-033-connection_optimizer-0_0_9.md
[spec-035]: ../spec-035-optimizer_hardening-0_0_10.md
[spec-037]: ../spec-037-upload_file_image_mapping-0_0_11.md
[spec-045]: ../spec-045-visibility_boundary-0_0_14.md
[spec-047]: ../spec-047-resource_policy-0_0_14.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
