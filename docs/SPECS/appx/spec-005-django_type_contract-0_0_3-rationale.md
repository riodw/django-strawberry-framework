# Rationale: spec-005 — DjangoType contract and boundary (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-005-django_type_contract-0_0_3.md`][spec-005]. The spec is the
contract and states only what it requires; everything that explains **how it got there** lives
here: the alternatives each decision rejected and why each lost, the derivations that do not change
how a decision is implemented, and every claim the spec once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-005-0.0.3` shipped eleven minor
versions ago and the rule that gates a build on this move did not exist then; this pass supplies it.
Text marked *Moved* below was cut out of the spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec section**, named by the section's own heading and linked to its anchor. A
  section with no entry here lost nothing — that is not an omission, it means the whole section is
  contract.
- **Who reads it.** Worker 3 reads it during review; Worker 1 owns it; Worker 2 never reads it. A
  reader looking for what the package *does* wants the spec, not this file.
- **This spec has no numbered Decisions.** It predates that convention, so the key is the heading.
  Two entries key to headings that no longer exist in the spec at all (`## Open questions` and
  `## Current state`); each anchors the surviving section that absorbed what was durable in it and
  says so. Two more key to sections item R2 retitled; those entries name the old title in one
  parenthetical so a reader arriving from an older citation still lands.
- **The file has two layers.** `## Entries keyed to the spec` records the deliberative layer the
  rationale-extraction pass moved out. `## Entries keyed to the spec — the R2 reconciliation`
  records what the reconciliation pass changed and why, one entry per spec section it rewrote. A
  section appearing in both has been through both passes; nothing in the second layer edits the
  first. Layer 1 therefore describes the spec as it stood when that pass closed, and its
  present-tense statements about what the spec *currently* says are dated by construction. Four of
  them name text the reconciliation has since rewritten or removed: the `## Provenance of this
  record` "deliberately left in the spec" list, the note that `## Problem statement` item 1 is
  untouched, the observation that the placeholder-test promise is "still in the spec", and the same
  observation about the must-update instruction. That is the whole population — established by
  reading layer 1 for present-tense claims about spec content, not by collecting instances as they
  were noticed — and the layer-2 entry for each section carries its current disposition.
- **This spec's distinguishing feature is that it made two predictions.** Both mechanisms have since
  shipped, so this file can say what a prediction was worth, which almost no other document in the
  repository can. `## Standing note` draws the comparison; the two entries carry the detail.
- **What this pass did NOT do.** It did not reconcile the spec against the shipped package. Where a
  moved block is recorded against HEAD below, that is because the block's *whole content* is a
  prediction and its fate is the only thing worth recording about it. Every claim still standing in
  the spec is item R2's determination, not this pass's — including the three sections this pass
  deliberately left alone (see `## Provenance of this record`).
- **The siblings are pointed at, not duplicated.**
  [`spec-001-django_types-0_0_1-rationale.md`][spec-001-rationale] narrates the type-generation
  foundation this spec sits on, including the registry's own many-to-one correction; this file does
  not retell it. Neither does it restate [`spec-018`][spec-018]'s or [`spec-019`][spec-019]'s
  reasoning — those specs own the two mechanisms outright. What is recorded here is only what
  **spec-005 predicted** and how the prediction fared.

## Provenance of this record

- **Moved** — cut from the spec by this pass, and now only here: the "real friction" paragraph and
  the whole `**Future direction.**` block (its four rules, the lead-in naming the future spec, the
  three sub-questions, and the closing first-registered-wins rejection) under
  `### One-model-one-type (alpha constraint)`; the whole `**Future direction.**` block under
  `### Consumer override semantics`; and the whole of `## Open questions`.
- **Deliberately left in the spec by this pass** — four passages that read like deliberation and
  are not this pass's to touch, and the list is exhaustive. `## Current state`'s 0.0.2 / 0.0.3
  shipped lists are status, not argument, and their disposition against the shipped package is item
  R2's. The `### One-model-one-type` opening paragraph states *why* the collision rule exists (an
  unambiguous `model_for_type` reverse lookup, a single `convert_relation` target) — a reason
  attached to a live rule, which the load-bearing carve-out in `worker-1.md`
  `### Performing the rationale move` keeps in the spec. The `### Consumer override semantics`
  `**Decision for 0.0.3.**` keeps its merge-code-can-stay clause for the same reason: it is a
  standing instruction not to rip the merge out, and a builder never reads this file. That same
  section's first two paragraphs — the `@strawberry.type`-rewrites-`cls.__annotations__` diagnosis
  and the skipped-test sentence that follows it — also stayed, and for a different reason: both are
  falsified *factual* claims rather than deliberation (the entry below records that the diagnosis
  was already wrong when it was written, and the test no longer exists), and correcting a false fact
  is item R2's contract, not this pass's.
- **Nothing was deleted outright by this pass.** `worker-1.md` rule 2 deletes rather than moves
  prose the current decisions have falsified. Nothing in spec-005 is falsified by spec-005 — the
  document is internally consistent and was falsified by the package, which is a different question
  and a different item's. The claim is measured rather than asserted: every non-empty line the move
  removed from the spec was tested individually for presence here, at line granularity, not against
  a set of spans chosen by the same reasoning that made the cut.
- **No fenced code block was involved.** The spec carried none before this pass and carries none
  after, so unlike its three predecessor cycles this move had no pseudo-code to dispose of. Its
  deliberative layer was prose argument and predicted design.

## Entries keyed to the spec

### `### One model, many types, one primary` — the friction argument, the `Meta.primary` prediction, and the rejection of first-registered-wins

Spec: [One model, many types, one primary][spec-005-onemodel]. (The section was titled
`### One-model-one-type (alpha constraint)` when this entry was written; item R2 retitled it to the
contract that holds, and the key above follows the section.)

*Moved — the friction argument in full.* "The constraint is real friction. DRF projects routinely
define multiple Serializers per model — public vs admin, list vs detail, internal vs external,
permission-scoped variants. The package's own test suite already works around it manually:
`tests/types/test_resolvers.py`, `tests/types/test_converters.py`, and the new
`test_has_custom_get_queryset_inherits_through_intermediate_base` all call `registry.clear()` (or
directly clear the internal dicts) between defining sibling types over the same model."

This is the derivation for the `Meta.primary` prediction below rather than a statement of the
contract, which is why it moves whole. Its per-topic competitive comparison moves with it under the
maintainer decision recorded on the spec-004 cycle: per-topic competitive argument moves to the
rationale, while a problem statement's statement of the competitor gap stays when the comparison is
the document's subject. `## Problem statement` item 1 names the same three libraries and is
untouched — it is the only sentence saying why the constraint was flagged at all.

*The evidence half of that argument has since inverted, and the paragraph would mislead if it had
stayed.* All three call sites still call `registry.clear()`, and
`tests/types/test_base.py::test_has_custom_get_queryset_inherits_through_intermediate_base` still
exists — but since `0.0.6` sibling types over one model need no clear at all. What the surviving
calls buy is test isolation against a process-global registry, which is not what the paragraph says
they buy.

*Moved — the `Meta.primary` prediction in full, as the spec stated it.* "Introduce
`Meta.primary: bool = False`. The rule is strict and import-order-free:

- A single type per model continues to register without declaring `Meta.primary` — the new key only
  matters when more than one type wants the same model.
- When two or more types register the same model, **exactly one** must declare `Meta.primary = True`.
  That primary type wins for `model_for_type` and `convert_relation` reverse lookups; siblings are
  still registered (and importable) but never selected by reverse lookups.
- Two or more types claim primary -> registration raises (ambiguous primary).
- Two or more types and none claims primary -> registration raises (ambiguous primary by omission).
  This is the explicit rejection of "first-registered wins": import order will not be part of the API
  contract under any path."

*How the prediction fared: right on every point but the detection point of one rule.* [`spec-018`][spec-018]
Decision 5 is the authoritative catalog and this file does not restate it. The name, the default, the
single-type backward-compatibility carve-out, the exactly-one rule, the "siblings stay registered"
consequence, and the duplicate-primary raise all shipped as predicted. The fourth rule shipped with a
different **detection point**: ambiguity-by-omission is caught at `finalize_django_types()` by
`types/finalizer.py::_audit_primary_ambiguity`, not at registration. The reason is the prediction's
own stated goal turned against its stated mechanism — registration cannot know whether a later
sibling will claim primary, so a registration-time raise would have made the outcome depend on import
order, the exact property the paragraph demanded be kept out of the API contract. A prediction that
names its goal precisely enough to falsify its own mechanism is the best case for this kind of
writing, and it is why the block is worth recording rather than deleting.

*Moved — the lead-in naming the future spec, the three sub-questions it "will need to address", and
their answers.* "This work belongs to its own future spec (`spec-meta_primary.md` or similar) which
will need to address:" It did get its own spec, and even the guessed slug matched:
[`spec-018-meta_primary-0_0_6.md`][spec-018]. Each sub-question below is quoted as the spec asked it;
each answer names the owning decision rather than restating it.

- "Migration from current strict-collision behavior (probably opt-in via a new setting or implicit
  relaxation when any `Meta.primary` is declared)." **Answered: implicit relaxation, no new setting.**
  A single type still registers with no `Meta.primary` ([`spec-018`][spec-018] Decision 5, first row).
  The parenthesis offered both branches and the cheaper one won; a setting would have made the
  package's own default a consumer decision.
- "Per-type relation routing (does `Item.category` -> `CategoryType` always pick the primary, or does
  the relation field declare a target?)." **Answered: always the primary, resolved at finalization**
  ([`spec-018`][spec-018] Decision 6). The eager-bind shortcut in `_build_annotations` was removed so
  binding cannot happen before the primary is knowable.
- "Optimizer impact (does the `Prefetch` downgrade decision use the primary type's `get_queryset`, or
  does the relation target's chosen type take precedence?)." **Answered** by [`spec-018`][spec-018]
  Decision 9, origin-type propagation.

*Moved — the rejected alternative, with the reason it lost.* "The alpha review noted that
"first-registered wins" without an explicit primary marker would be the worst of the three options
because it makes import order part of the API contract. The future spec is explicitly choosing
`Meta.primary`, not first-registered-wins." This is the one rejection in the spec stated as a
rejection, and it is the one that survived contact unchanged: nothing in the shipped mechanism reads
registration order.

*A related design choice the shipped mechanism made that this spec did not anticipate.*
`registry.py::TypeRegistry.get` returns `None` for the ambiguous multi-type case rather than raising
there, and its docstring says callers cannot distinguish that from "no type registered" without
checking `types_for(model)`. It is deliberate and follows from the detection-point correction above —
the raise belongs to the finalizer audit, which is the only place that sees the whole registry at
once. Recorded here so a future reader does not read the `None` as a swallowed error.

*Claims the section no longer makes.* That the constraint is friction the test suite works around by
clearing the registry; that `Meta.primary` is future work; that any of the three sub-questions is
open; that ambiguity by omission is detected at registration.

### `### Consumer override semantics` — three candidate approaches, none of which shipped

Spec: [Consumer override semantics][spec-005-overrides]. (The section was titled
`### Consumer override semantics (deferred to a future spec)` when this entry was written; item R2
dropped the parenthetical, because the mechanism it deferred has shipped.)

*Moved — the prediction in full, as the spec stated it.* "The override path needs a real
implementation, but the design is non-trivial. Three approaches that have been mentioned in passing:

1. Bypass Strawberry's annotation rewrite by reaching into its internals to preserve consumer-declared
   annotations.
2. Route consumer overrides through Strawberry's own field-customization API (e.g., consumers write
   `name: str = strawberry.field(description="...")` instead of re-annotating the type).
3. Drop the implicit-override claim entirely and require an explicit Meta-level mechanism (e.g.,
   `Meta.field_overrides = {"name": int}`).

None of these belongs in this spec. They belong to a future `spec-consumer_overrides.md` (or whatever
it ends up being called) that picks one of the three after evaluating Strawberry's field-customization
API in detail. Until then: limited, not guaranteed."

*How the prediction fared: none of the three shipped, and the mechanism is a fourth.*
[`spec-019`][spec-019] Decisions 1-4 own it and this file does not restate them; what matters here is
the shape of the miss. The shipped mechanism extends the package's own existing
`consumer_annotated_relation_fields` collection with a parallel `consumer_annotated_scalar_fields`
set and unions it into `consumer_authored_fields`, so `types/base.py::_build_annotations`
short-circuits the field before synthesis. Approach 1 lost because no Strawberry internal had to be
touched. Approach 2 lost because it would have made a consumer write a different spelling to get the
behavior the plain annotation already implies. Approach 3 lost outright and explicitly: card
`DONE-019-0.0.6` states "No new public API. No `Meta.field_overrides = {...}`-style key."

*The prediction was aimed at a diagnosis that was already wrong when it was written.* All three
approaches are answers to "`@strawberry.type` rewrites `cls.__annotations__` after the merge, so the
consumer's annotation loses" — approach 1 works around the rewrite, approach 2 routes around it,
approach 3 abandons the annotation channel because of it. [`spec-019`][spec-019]'s
`## Problem statement` records that this skip reason "describes a pre-foundation-slice state": after
`DONE-010-0.0.4` the merge at
`types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"`
already put the consumer last. The real gap was narrower and elsewhere — the field name's absence
from `consumer_authored_fields`, which left the synthesized annotation computed anyway and let the
consumer win only by dict-merge order. **That is why all three candidates missed: a candidate list is
only as good as the diagnosis that generated it, and this one enumerated three exits from a room the
package had already left.** The lesson is the one thing this block is worth keeping for.

*A rejected alternative belonging to this section that the spec never recorded, because the choice was
made after it.* The section's `**Decision for 0.0.3.**` promises the skipped placeholder test will be
kept and unskipped when the real mechanism ships. [`spec-019`][spec-019] Decision 5 weighed exactly
that — unskip-and-keep — against deletion and chose deletion: a one-line smoke test sitting alone in
`tests/types/test_base.py` would drift from the canonical host, and the four-corner override matrix
lives in `tests/types/test_definition_order.py`. The promise sentence is still in the spec and is item
R2's, not this pass's; the rejection is recorded here so the deletion does not read as an oversight.

*Claims the section no longer makes.* That a real override mechanism is future work; that the design
is non-trivial in the way described; that any of the three candidate approaches is live; that a
`spec-consumer_overrides.md` is yet to be written.

### `## Open questions` — the release-gating judgement (section removed)

Bears on [`## Non-goals`][spec-005-nongoals] and both `### Topics` entries above.

*Moved verbatim, the whole section.* "None blocking 0.0.3. The two follow-on specs (`Meta.primary`
and consumer overrides) are deliberately deferred — naming them here is enough; designing them is
future work tracked under their own spec docs when those land."

*Why the section was removed rather than restated.* Every word of it is a judgement about one
release, made while that release was in flight: whether anything blocked `0.0.3`, and whether naming
a follow-up was enough for it. A shipped spec cannot keep answering that question, and the answer it
froze is now trivially yes-they-landed. What is durable in it — that this spec does not design either
mechanism — is already `## Non-goals`, which says so as a contract instead of as a status.

*The one thing it got right, and it is worth saying.* "Naming them here is enough" was a bet that a
named-but-undesigned follow-up would actually get designed. Both were, at `0.0.6`, by
[`spec-018`][spec-018] and [`spec-019`][spec-019]. The bet that did **not** pay is in a different
section: `## Coordination …`'s instruction that a future spec adding or changing a Meta key "must
update this contract spec accordingly" was followed by none of the eleven-plus specs that did so —
which is the direct cause of this spec's stale key lists and therefore of the cycle that produced
this file. That sentence is still in the spec and is item R2's to decide on.

*Claim the spec no longer makes.* That anything is open, or that either follow-on spec is undesigned.

## Entries keyed to the spec — the R2 reconciliation

The rationale-extraction pass above moved the deliberative layer out and deliberately corrected
nothing. This layer is the reconciliation: the spec's remaining claims were checked against the
shipped package, and where a later spec had corrected what landed, the spec was rewritten to state
the contract that holds. It reads as a clean current contract with no chronology in it, so what
changed, why, and what it may no longer say lives here.

**The direction of correction ran toward spec-005 and never away from it.** Every sibling that
superseded a claim here — [`spec-010`][spec-010], [`spec-011`][spec-011], [`spec-015`][spec-015],
[`spec-018`][spec-018], [`spec-019`][spec-019], [`spec-027`][spec-027], [`spec-028`][spec-028] — is
correct as written and was read-only throughout. None was edited, and none of their rules is
restated here or in the spec; each is named and pointed at.

### `## Problem statement` — from a dated gap report to four durable failure classes

Spec: [Problem statement][spec-005-problem].

The section opened by saying the contract "has not been pinned in a single document" and then listed
"four concrete gaps" the alpha review had surfaced, three of which stated present-tense facts the
package has since falsified. Every one of them was true when written and none of them survives:
registry collision no longer forces one type per model; the `@strawberry.type`-rewrite diagnosis was
wrong before the override mechanism shipped; and `Meta.interfaces` is accepted **and** applied today.

*Why the shape changed, not just the facts.* A gap list dates the instant it is written, because a
gap is a fact about a moment. The four gaps were only ever instances of four *classes* of boundary
failure, and the classes are what the rest of the document actually depends on — `## Goal`,
the promotion rule, and both remaining topics each cite one. Restated as classes, the section
carries the same argument and cannot go stale again; restated as corrected facts it would have
needed rewriting at the next Meta key.

*Rejected: keep the four gaps and mark them historical.* It reads as the smaller edit and is the
wrong one. A reader would have to apply a chronology to the section to learn what is true, which is
the difference between a contract and a changelog. The historical record belongs here.

*Rejected: drop the section and let `## Goal` carry the motivation.* `## Goal` states what the
contract must achieve; it does not say what goes wrong without it, and the promotion rule's "this is
a bug" clause has to point at something. The section earns its place once it stops being dated.

*The competitor comparison was removed, and this is the one removal that touches an already-settled
question.* Item 1 named DRF, `graphene-django`, and `strawberry-graphql-django` as libraries that
allow several types per model. The rationale-extraction pass kept that sentence under the maintainer
decision recorded on the spec-004 cycle — a problem statement's statement of the competitor gap
stays when the comparison is the document's subject. It was removed here for a different reason
that the decision does not reach: **the gap is closed.** The package allows several types per model
today, so a sentence saying the competitors allow what this package forbids is not a positioning
statement any more, it is a false one, and `worker-1.md` rule 2 deletes prose the current decisions
have falsified. The competitive argument itself survives, in the friction paragraph moved to the
entry above.

*Failure class 1 named the direction that structurally cannot fail, and the revision pass corrected
it.* The class was written as an ambiguous *reverse* lookup, over "the type-to-model reverse
lookup". That direction is `registry.py::TypeRegistry.model_for_type`, backed by `_models`, and it
is one-to-one by construction — a model reachable through fifteen types still resolves each of them
to exactly one model, which the topic below states outright. The direction that can be ambiguous is
model-to-type: the target a relation binds to, and the answer a bare `registry.get(model)` gives.
So one document was letting "reverse lookup" denote both directions while the source reserves the
phrase for the safe one (`model_for_type`'s own docstring calls itself the reverse lookup), and the
class now names its direction instead. Only the naming moved; the contract it motivates was already
right and was not reopened.

*Two smaller losses, named so they are not read as oversights.* The old item 3 dated itself
("until 0.0.3, `_select_fields` did a set intersection and silently dropped unknown names") — the
implementation it describes is two behaviours ago and the failure it describes is the durable half,
so only the failure survives. And the thread paragraph's "alpha-stage" qualifier went: the rule it
states is not one the package outgrows at `0.1.0`, and hedging it invites the reading that it does.

*Claims the section no longer makes.* That the contract is unpinned; that registry collision forces
one `DjangoType` per Django model; that the type-to-model direction of the registry can be
ambiguous; that `_select_fields` intersects rather than validates; that consumers of this package get fewer types per model than
DRF, `graphene-django`, or `strawberry-graphql-django` offer; that `DjangoType.__init_subclass__`'s
override merge does not hold because `@strawberry.type` rewrites `cls.__annotations__` after it;
that a skipped test pins that failure; that `Meta.interfaces` is accepted but never applied.

### `## Current state` — the release-status section, removed

Bears on [Coordination][spec-005-coordination], which absorbed the one durable claim it carried.

*Removed, whole.* The section listed what "0.0.2 shipped" and what "0.0.3 shipped (in flight)", then
closed by saying two contract items remained: the override-claim removal, shipping in `0.0.3`, and
the registry uniqueness rule, "deferred to a future `Meta.primary` spec". Its content is a release
status frozen at a release that shipped eleven minor versions ago. It carried **seven** bullets —
four under `0.0.2 shipped:` and three under `0.0.3 shipped (in flight):` — and **five** of them are
now false as present tense: that registry collision raises, that the override merge is known broken,
that `Meta.interfaces` is accepted and silently ignored, that `Meta.fields` / `Meta.exclude` typos
are silently dropped, and that `Meta.interfaces` has been moved into `DEFERRED_META_KEYS` with a
rejection pointing at a future relay spec. The two survivors are the `_select_fields` raise and the
`get_queryset` sentinel, and both were restated into the spec rather than lost. The closing
paragraph quoted above adds a sixth falsehood outside the bullet lists: that resolving registry
uniqueness is still future work.

*Why removed rather than restated.* A `## Current state` section is a status report by construction,
and a status report in a contract document is the exact shape the spec is not allowed to have: a
reader has to date it before they can use it. Each of its bullets is either already stated as
contract by the topic that owns it, or is history, which is this file.

*The one durable claim it carried, and where it went.* The `_is_default_get_queryset` /
`has_custom_get_queryset` bullet described a real invariant, and it under-described it: the sentinel
is stamped earlier in `__init_subclass__` than the section described, detection is an MRO walk rather
than an attribute comparison, the authoritative
value lives on the definition object, and the finalizer is a second consumer beside the optimizer.
That is a contract statement, so it was restated — not preserved — in
`## Coordination …`, where the optimizer half of the sentinel already lived.

*This section was the sole carrier of the `Meta.primary` glossary anchor.* The link was re-sited
into `### One model, many types, one primary` in the same edit that removed the paragraph, which is
the only ordering that never leaves the anchor uncarried. Re-siting it is why the anchor did not
have to be held alive by narration the reconciliation was otherwise deleting.

*Claims the spec no longer makes.* That `0.0.3` is in flight; that anything about the contract
remains to be pinned; that `Meta.interfaces` sits in `DEFERRED_META_KEYS`; that the deferred-key
message points at a future relay spec; that the registry uniqueness resolution is deferred.

### `## Goal` — neither the rejection nor the temporary-constraint label promises to name a spec

Spec: [Goal][spec-005-goal].

The first bullet promised every rejected knob would be "rejected with a clear error pointing at the
spec that will own it". The rejection is clear and it does name the keys, but it has never named a
specific spec. Its original wording pointed at an unshipped *spec*; a later consolidation pass moved
the package's consumer-facing vocabulary away from naming internal design documents, and the word
became *feature*.

*The correction runs toward the spec, not toward the code.* The wording in the source is right and
deliberate, for the reason the section now gives, and the spec's promise was over-stated even before
that pass — neither wording ever named a specific document. So the goal was restated to promise what
a rejection can actually owe a consumer.

*Rejected: change the message to name the spec.* It would have satisfied the sentence literally and
made the package worse, and it is the one shape a documentation cycle must not reach for — the code
is read-only here precisely so a stale document cannot pull a shipped, deliberate contract backwards.

*The third bullet carried the same defect and the revision pass corrected it with the first.* It
required a temporary constraint to name "the spec that will lift it". The place the package actually
publishes that label is `docs/GLOSSARY.md`'s per-key `**Status:**` line, and an unshipped surface is
labeled there by release — the three still-deferred keys read `planned for 0.1.1` / `0.1.2` /
`0.1.3` — never by spec document, which is the same consumer-facing choice the first bullet was
corrected to respect. Nothing at HEAD violated the bullet, because no constraint is currently
labeled temporary at all; it was demanding a form the package had already decided against, and would
have collected its first violation the moment one appeared. It now asks for the label and for what
lifting it waits on, which is exactly what the glossary carries. This bullet is also where the
never-dischargeable `docs/README.md` obligation recorded under `### One model, many types, one
primary` lands, so that entry's pointer at it still resolves.

*Claim the section no longer makes.* That a deferred-key rejection points at the spec that will own
the key; that a temporary constraint must name the spec that will lift it.

### `## Non-goals` — the two mechanisms are not future work

Spec: [Non-goals][spec-005-nongoals].

The sentence excluded "the future `Meta.primary` mechanism itself, or the future consumer-overrides
mechanism itself". The exclusions are still exactly right; the word *future* is not, and it was the
only place left in the spec where a reader could learn that the follow-ups exist. Both shipped at
`0.0.6`. The section now names the owning specs, so it doubles as the pointer the removed
`## Open questions` section used to be half of.

*No alternative was weighed here, and that is the record rather than an omission.* A word that
states the opposite of what shipped has one correct disposition. The only choice inside the change
was whether to name the owning specs at the same time, and leaving them unnamed would have removed
the last place in the document a reader could learn the follow-ups exist.

*Claim the section no longer makes.* That either mechanism is future work, or unnamed.

### `### One model, many types, one primary` — the constraint the section documented does not exist

Spec: [One model, many types, one primary][spec-005-onemodel].

The section documented one `DjangoType` per Django model, enforced by a collision raise, and decided
to keep it as a temporary alpha constraint. [`spec-018`][spec-018] lifted it at `0.0.6`:
`registry.py::TypeRegistry.register` has appended rather than rejected ever since, and its surviving
raises concern primary claims rather than the existence of a second type.

*What the section was rewritten to, and why it is not just a pointer to `spec-018`.* Strip the
lifted constraint away and something remains that belongs to this spec rather than to spec-018 — a
requirement on the *answer* the registry has to give, as against the mechanism that gives it.
`spec-018` supplies the mechanism; a contract spec owns the boundary that mechanism must satisfy,
and stating the boundary here is what leaves spec-018 checkable against anything. That framing is
also what this section's own moved prediction argued for, so the reconciliation did not invent it.

*Rejected: absorb spec-018's ambiguity rules into this section.* It reads as making the contract
concrete and creates a second source for rules that already have an owner and a glossary entry —
`docs/GLOSSARY.md`'s `Meta.primary` entry carries the full four-case table with its error strings.
The same failure as the key rosters below, at smaller scale.

*Rejected: delete the section and let `## Non-goals` point at spec-018.* It would have dropped the
import-order requirement, which nothing else states, and it would have left the `Meta.primary`
glossary anchor with no carrier anywhere in the spec.

*The doc obligation the decision carried was never dischargeable as written.* It required the
constraint be documented in `docs/README.md` "Current surface" with a status marker and a
back-reference to this spec. `docs/README.md` has no `## Current surface` section — it carries
`## Today and coming next` — and no reference to spec-005 anywhere. What it does carry is
`Meta.primary` in its shipped list, which is the opposite claim and the correct one. The obligation
went unfollowed, then obsolete; it is not restated, and the durable half of it survives as
`## Goal`'s third bullet, which states the rule rather than a one-time task.

*Claims the section no longer makes.* That registering a second type for one model raises; that one
model may have one type; that the constraint is temporary, alpha-scoped, or awaiting a future spec;
that `convert_relation` is the symbol a relation resolves through — it no longer exists, and
relation targets bind at finalization through `registry.primary_for(model)`; that `docs/README.md`
carries a "Current surface" section or a back-reference to this spec.

### `### Consumer override semantics` — the mechanism shipped, and the merge is not incidental

Spec: [Consumer override semantics][spec-005-overrides].

The section stated that the override contract "does not actually hold today", pinned the failure to
a skipped test, and decided to remove the claim from the `__init_subclass__` docstring while leaving
the merge in place as harmless. The docstring half was delivered and still holds. Everything else is
falsified: the mechanism shipped at `0.0.6`, the diagnosis was wrong before it shipped, and the
skipped test is gone.

*The merge-can-stay clause was kept through the extraction pass and is corrected here rather than
kept.* The rationale-extraction pass left it deliberately, as a standing instruction not to rip the
merge out — a builder never reads this file, so an instruction of that shape has to live in the
spec. The instruction is still right and its stated reason is now backwards: the merge is not
harmless-because-overridden, it is part of the shipped path. What actually decides an override is
the short-circuit ahead of synthesis rather than the merge ordering, and the section now says so —
which preserves the do-not-delete instruction while giving it a reason that will not mislead the
next reader into treating the merge as dead code.

*The lead clause was unconditional and the package ships one documented exception.* The section's
opening sentence made anything written on the class body win, with no qualification. That holds for
the four corners and fails for the fifth: `field: auto` is an annotation asking for the
model-inferred type, so
`types/base.py::DjangoType.__init_subclass__` keeps such names out of the consumer-authored union
and drops them from `consumer_annotations`, letting the synthesized annotation win the merge. The
four-corner sentence already scoped the claim, so a careful reader landed correctly — but this
spec's own second failure class is a promise the implementation does not keep, and an unconditional
lead clause with a shipped counter-example is one. The section now closes the boundary in a
subordinate clause rather than leaving it to be inferred. The alternative — setting out the `auto`
marker's own rules here — was rejected: the marker belongs to the specs that own the override
surface, and what a contract spec owes is the edge of its claim, not a second telling of the
mechanism behind it.

*Rejected: state the four-corner matrix and the short-circuit mechanism in full.* That is
[`spec-019`][spec-019] Decisions 1-4 and [`spec-010`][spec-010]'s relation contract, both of which
are correct as written and neither of which needs a second telling. The section names the surface
and its owners and stops.

*The placeholder-test promise became a general rule.* The section promised one specific skipped test
would be kept and unskipped. `spec-019` Decision 5 deleted it instead, for reasons recorded in the
entry above. Restating the promise about a test that does not exist was not an option; naming
`test_definition_order.py` as its replacement would have made this spec a test index. What was
durable in the promise is the general rule about what a placeholder test may be allowed to look
like, which is now the second half of the section's contract clause.

*Claims the section no longer makes.* That the override contract does not hold; that
`@strawberry.type` rewrites `cls.__annotations__` in a way that defeats the merge; that the merge
code is harmless; that a skipped `test_consumer_annotation_overrides_synthesized` exists or pins
anything; that `docs/README.md` calls consumer overrides "not guaranteed"; that the override
mechanism is deferred to a future spec.

### `### Invalid Meta.fields and Meta.exclude names` — true as written, and narrower than what shipped

Spec: [Invalid `Meta.fields` and `Meta.exclude` names][spec-005-selection].

The only topic whose every factual claim held at reconciliation time: `_select_fields` raises in
both the `fields` and the `exclude` arm, the message names the model, the unknowns, and the
available set, and all three named tests exist. Nothing in it was corrected.

*What was added, and why it belongs in this spec rather than in the specs that did it.* Five more
`Meta` keys have since adopted the shared formatter behind this message. The section claimed the
error shape as public contract for two keys; the package honours that claim for **seven**. The unit
is keys: the raise sites carry six distinct `attr` labels rather than seven, because
`nullable_overrides` and `required_overrides` are validated together under one label. Leaving the
claim at two would have understated a promise consumers can already rely on, so the section names
the five and then states the obligation a new field-naming key inherits. The obligation is what
makes the naming safe where a `Meta`-key roster would not be: a name added to that list is a
consequence of the rule stated beside it, so a reader who finds the list short still has the rule,
which is the opposite of a roster that has to be believed on its own.

*The heading's slash became "and".* The old title separated the two key names with a slash, which
slugs ambiguously: dropping the slash leaves a double space, which GitHub renders as a double hyphen
and this repository's anchor checker collapses to one. No inbound link targeted the section, so the
ambiguity was removed while it was still free to remove.

*Claim the section no longer makes.* None. It gained scope; it retracted nothing.

### `### Accepted vs deferred Meta keys` — the rule kept, both rosters retired

Spec: [Accepted vs deferred Meta keys][spec-005-metakeys].

The section listed five accepted keys and six deferred ones. The package has seventeen accepted and
three deferred; three of the six listed deferrals were promoted (`interfaces` at `0.0.5`,
`filterset_class` and `orderset_class` at `0.0.8`) and twelve keys were added across at least eleven
specs. The three still deferred — `fields_class`, `search_fields`, `aggregate_class` — are exactly
the three the Beta line owes.

*Rejected, and this is the section's whole judgement: refresh the two lists.* It is the obvious
edit, it would be correct for a few weeks, and it is what put this section eleven versions out of
date in the first place. The lists move whenever a key ships; three more move on the Beta line. A
roster in a spec is a copy of `ALLOWED_META_KEYS`, and a copy of an executable set is the second
source of truth that silently disagrees with the first. `docs/GLOSSARY.md` already publishes
per-key status and `types/base.py` already holds the sets, so the spec's durable contribution is the
**rule** — what licenses a key to be accepted, what a rejection owes the consumer, why silent
acceptance is a bug. The rule has not changed once in eleven versions, which is the evidence that it
is the right thing for this section to hold.

*Rejected: keep a short roster of "the keys this spec itself shipped".* A frozen historical list is
harder to read correctly than no list — a reader cannot tell from the page whether it is current,
and its being *deliberately* stale is invisible.

*Added: the third route in, which the two-bucket partition could not express.* **Nine** of the
twelve keys added since never sat in the deferred set at all — each one's feature landed in the same
card that introduced its key. The population is every historical definition of
`DEFERRED_META_KEYS`, replayed over the file's whole history rather than sampled: the set has held
only six keys ever (`aggregate_class`, `fields_class`, `filterset_class`, `interfaces`,
`orderset_class`, `search_fields`), three of which were promoted, so the other nine additions
entered as accepted outright. The comment beside `ALLOWED_META_KEYS` records the distinction but is
not the census — it annotates one run of specs, folds two keys into one clause, and names seven of
the nine; counting its clauses gives six, which is where the wrong figure in the first draft of this
entry came from. `tests/types/test_base.py::test_meta_relation_shapes_in_allowed_meta_keys` pins one
instance directly, and its sibling `::test_interfaces_is_shipped_not_deferred` pins the promoted
case the net-new one is defined against. It is worth a sentence in the spec because otherwise the
promotion rule reads as the only entrance, and nine of the seventeen accepted keys then look like
they skipped it. The pattern was named by `spec-032`; the rule it satisfies is this spec's.

*The `Meta.interfaces` example survived, inverted.* The section used it as the canonical instance of
the failure the promotion rule exists to catch — validated but never applied. That is history now:
the key is accepted and applied end-to-end. It is still the example, because it is the one key that
has been in more than one of them, and it now carries what is true of the key today and the test
that pins it, instead of a past mistake. It is also the sole carrier of the `Meta.interfaces` glossary anchor,
which is why the example had to be re-sited rather than dropped.

*Claims the section no longer makes.* That `ALLOWED_META_KEYS` is `model`, `fields`, `exclude`,
`name`, `description`; that `DEFERRED_META_KEYS` contains `filterset_class`, `orderset_class`, or
`interfaces`; that a deferred key's rejection points at the spec that will own it; that promotion is
the only way a key enters `ALLOWED_META_KEYS`.

### `## Coordination …` — the instruction that was never once followed

Spec: [Coordination][spec-005-coordination].

The section instructed that a future spec adding or changing a `Meta` key "must update this contract
spec accordingly". Twelve keys were added and three promoted across at least eleven specs, and not
one of them touched spec-005. That is the direct cause of the stale rosters above and therefore of
this reconciliation.

*The instruction was retired rather than re-issued.* An obligation with a zero-for-eleven record is
not being forgotten by careless authors; it is unenforceable by construction. Nothing fails when it
is skipped: no check runs, no test breaks, and the spec's own reader cannot tell the difference
between "no key has changed" and "nobody filed". What replaced it is an obligation that already
holds and is already checked — a spec adding or promoting a key satisfies the promotion rule inside
its own change, against source, and lands the key's glossary entry. The authoritative sets stay in
`types/base.py` and the published status stays in `docs/GLOSSARY.md`. That replacement is not new
either: the key-partition section already closed with "this rule should be checked at every spec
slice that introduces or moves a Meta key", which is the same obligation aimed at the code. It was
promoted out of a trailing sentence into the section that used to carry the unenforceable one.

*Rejected: keep the instruction and add a check that enforces it.* A tempting third way, and it
buys the wrong thing. Whatever the check verified would be that this document's copy of the key set
matches the real one — which is the roster problem again, now with tooling to keep the duplicate
alive. Delete the duplicate and the check has nothing to do.

*Rejected: keep the instruction unchanged, on the grounds that this cycle is proof it eventually
works.* It is proof of the opposite. The instruction did not surface the drift; a residual-completion
cycle eleven versions later did, and only because the whole spec was re-read against the package.

*Also restated here: the `get_queryset` sentinel.* Its optimizer half already lived in this section.
Its type-system half moved in from the removed `## Current state`, corrected to what shipped — the
stamping-order invariant, the MRO-walk detection, the definition object as the authoritative value,
and the finalizer as a second consumer beside the optimizer's `Prefetch` downgrade rule.

*Claim the section no longer makes.* That a later spec is obliged to update this document.

### `## References` — one bullet named a deleted test, one named a document that does not exist

Spec: [References][spec-005-references].

*Removed: the "original alpha review" bullet.* It named no path and no such document exists anywhere
in the repository. The bullet's own text says this spec is "the durable record of those findings",
which makes the reference circular — it points at the document containing it. Nothing is lost by
removing it and a reader stops hunting for a file.

*Corrected: the `tests/types/test_base.py` bullet.* It claimed the file pins "the override-merge
skipped placeholder", a test [`spec-019`][spec-019] Decision 5 deleted. The bullet now names what
the file actually pins.

*Added: the three owning specs.* [`spec-010`][spec-010] / [`spec-019`][spec-019] for the two halves
of the override surface and [`spec-018`][spec-018] for `Meta.primary`, so a reader sent onward by a
topic can get there from the reference list too. Three specs in two bullets: the two override halves
share one. The `spec-006` bullet now records that it cites
the key-partition section **by its title string** — a dependency invisible from the citing side, and
the reason that heading kept the words `Accepted vs deferred Meta keys` intact while the other three
topics were retitled. Only its trailing `(shipped in 0.0.3)` was dropped, which is outside the
quoted string; the citation still resolves.

*No alternative was weighed here, and that is the record rather than an omission.* An unresolvable
reference, a bullet naming a deleted test, and three owners a reader cannot reach each have one
correct disposition; there was no second option to lose to the first.

*Claims the section no longer makes.* That an alpha-review document is a resolvable reference; that
`tests/types/test_base.py` contains an override-merge skipped placeholder.

## Standing note — the two predictions were worth very different amounts

Spec-005 is the only document in this repository that predicted two mechanisms in the same breath and
then had both of them ship, so the comparison is available nowhere else and is the reason the two
`**Future direction.**` blocks were moved rather than deleted.

- **The `Meta.primary` prediction was substantially vindicated** — right name, right default, right
  exactly-one rule, right rejection of first-registered-wins — and wrong in exactly one detail, the
  detection point, which its own stated goal is what corrected.
- **The consumer-overrides prediction was wrong three ways out of three**, and the shipped mechanism
  was none of them.

The difference is not luck and not effort — the two blocks were written on the same day, and the one
that fared worse is also the shorter (112 words against 245) only because a shortlist of three
techniques takes fewer words than a table of required outcomes. The `Meta.primary` block predicted a
**contract**: it enumerated the configurations and
stated the outcome required of each, so the implementation had to satisfy it rather than resemble it,
and the one place it over-specified (*where* the rejection fires) is exactly the one place it strayed
from contract into mechanism. The consumer-overrides block predicted **implementations** — three of
them, each a route around a diagnosis that was wrong before either shipped. A prediction stated as a
required outcome survives a wrong diagnosis; a prediction stated as a technique does not, and
inherits every error in the diagnosis that generated it. When a spec must gesture at future work, the
cheap and durable form is the rule the future mechanism will have to satisfy, not a shortlist of ways
to build it.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-001-rationale]: spec-001-django_types-0_0_1-rationale.md
[spec-005]: ../spec-005-django_type_contract-0_0_3.md
[spec-005-coordination]: ../spec-005-django_type_contract-0_0_3.md#coordination-with-spec-001-django_types-0_0_1md-and-spec-002-optimizer-0_0_2md
[spec-005-goal]: ../spec-005-django_type_contract-0_0_3.md#goal
[spec-005-metakeys]: ../spec-005-django_type_contract-0_0_3.md#accepted-vs-deferred-meta-keys
[spec-005-nongoals]: ../spec-005-django_type_contract-0_0_3.md#non-goals
[spec-005-onemodel]: ../spec-005-django_type_contract-0_0_3.md#one-model-many-types-one-primary
[spec-005-overrides]: ../spec-005-django_type_contract-0_0_3.md#consumer-override-semantics
[spec-005-problem]: ../spec-005-django_type_contract-0_0_3.md#problem-statement
[spec-005-references]: ../spec-005-django_type_contract-0_0_3.md#references
[spec-005-selection]: ../spec-005-django_type_contract-0_0_3.md#invalid-metafields-and-metaexclude-names
[spec-010]: ../spec-010-foundation-0_0_4.md
[spec-011]: ../spec-011-stale_placeholder_cleanup-0_0_4.md
[spec-015]: ../spec-015-relay_interfaces-0_0_5.md
[spec-018]: ../spec-018-meta_primary-0_0_6.md
[spec-019]: ../spec-019-consumer_overrides_scalar-0_0_6.md
[spec-027]: ../spec-027-filters-0_0_8.md
[spec-028]: ../spec-028-orders-0_0_8.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
