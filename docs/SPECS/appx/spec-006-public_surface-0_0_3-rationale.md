# Rationale: spec-006 — Public surface & documentation discipline (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-006-public_surface-0_0_3.md`][spec-006]. The spec is the contract
and states only the rules it requires; everything that explains **how it got there** lives here: the
alternatives each rule rejected and why each lost, the provenance the spec used to narrate about
itself, and every claim it once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-006-0.0.3` shipped eleven minor
versions ago and the rule that gates a build on this move did not exist then; this pass supplies it.
Text marked *Moved* below was cut out of the spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec section**, named by the section's own heading and linked to its anchor. A
  section with no entry here lost nothing — that is not an omission, it means the whole section is
  contract.
- **Who reads it.** The role-by-role answer is [`BUILD.md`][build] `### Who reads it, and when`,
  which is that mechanism's canonical home. A reader looking for what the package *does* wants the
  spec, not this file.
- **This spec has no numbered Decisions.** It predates that convention, so the key is the heading.
  One entry keys to a heading that no longer exists in the spec at all (`## Open questions`); it
  anchors the section its judgement bore on and says so.
- **This spec's subject is a set of rules, which makes the deliberation line unusually fine.** A
  sentence saying *why* a rule reads the way it does is frequently the thing that stops the rule
  being mis-implemented, and `worker-1.md` `### Performing the rationale move` keeps that in the
  spec. Three passages moved; the rest of the document's argument is load-bearing on its own rules
  and stayed. `## Provenance of this record` lists both sides exhaustively.
- **The rationale-extraction pass did NOT reconcile the spec against the shipped package.** Every
  claim recorded below is recorded **as the spec made it**. Which of the spec's surviving claims
  still hold is the reconciliation item's determination, not this pass's, and its record appends
  below this one when it runs.
- **The siblings are pointed at, not duplicated.**
  [`spec-005-django_type_contract-0_0_3-rationale.md`][spec-005-rationale] narrates the `Meta`-key
  contract this spec extends to the package level, and
  [`spec-002-optimizer-0_0_2-rationale.md`][spec-002-rationale] narrates the optimizer's own section
  removals and retitles. Neither is retold here.

## Provenance of this record

- **Moved** — cut from the spec by this pass, and now only here: the `## Problem statement`'s
  provenance sentence recording that the original alpha review raised the alignment problem while
  the optimizer was still incomplete; the whole third paragraph of `### docs/README.md structure`
  (the rejected `Current` / `Planned` / `Not implemented yet` sectioning and the reason it lost);
  and the whole of `## Open questions`.
- **Deliberately left in the spec by this pass**, and the list is exhaustive:
  - `## Problem statement`'s second paragraph — its two-sentence thesis, that the remedy is stricter
    discipline rather than a larger volume of docs — and the sentence every rule below it derives
    from. It reads as argument and it is the argument the rules *are*, which is the load-bearing
    carve-out.
  - `### Alpha signaling rules`' closing rule-of-thumb paragraph, which tests a passage against what
    a Django developer would conclude they can do today. It reads as reasoning and it is the
    operative test: the three marker-to-tense bullets above it enumerate cases, and this paragraph is
    what decides a case they do not cover. A writer who never reads it mismatches language and
    marker the moment the case is novel.
  - `### Top-level re-export rule`'s closing paragraph on dotted submodule paths, and
    `#### Decision for 0.0.3`'s worked application of the four conditions. Both explain *why* a name
    sits where it sits, and both change how a promotion is performed.
  - Every status claim in the document — `## Current state`'s five-name surface list and README
    structure summary, its Layer-3 mismatch-risk paragraph, `#### Decision for 0.0.3`'s O1-O6 /
    B1-B8 roster and fenced `__all__` tuple. A status claim moved into a rationale file is neither a
    legitimate entry here nor the deletion the move prescribes for falsified prose, and its
    disposition against the shipped package is the reconciliation item's call. This is the same line
    [`spec-002`][spec-002-rationale]'s extraction pass drew around `## Current state`,
    `## Shipped slices`, and `## Visibility status`.
  - `## References`' alpha-review bullet, which names recommendations #1 / #2 / #7 / #8 of a document
    not present in the repository. It is a reference entry rather than deliberation — contract
    scaffolding, in the shape [`spec-002`][spec-002-rationale]'s pass left alone — and whether an
    unresolvable locator is corrected or removed is a claim-level decision, not a move.
    [`spec-005`][spec-005-rationale] records its own cycle removing the identical bullet; that
    precedent is available to the reconciliation and was not pre-empted here.
- **Nothing was deleted outright by this pass.** `worker-1.md` rule 2 deletes rather than moves prose
  the current decisions have falsified. Nothing in spec-006 is falsified by spec-006 — the document
  is internally consistent, and it was falsified by the package and by the docs it points at, which
  is a different question and a different item's. The claim is measured rather than asserted: every
  non-empty line the move removed from the spec was checked individually for presence here.
- **No fenced code block was involved.** The spec carried three fenced blocks before this pass (two
  import examples and the `__all__` tuple) and carries the same three after; all three are contract
  or status, and none sat inside moved prose.
- **No glossary anchor changed carrier.** All seven of the spec's terms are carried by exactly one
  reference-style link each, and none of the three moved passages contained one, so this pass
  re-sited nothing. Verified by re-running `scripts/check_spec_glossary.py` against the spec after
  the move.

## Entries keyed to the spec

### `## Problem statement` — where the alignment problem came from

Spec: [Problem statement][spec-006-problem].

*Moved — the provenance sentence in full.* "The original alpha review called this out while the
optimizer was still incomplete."

The sentence is chronology: it says who raised the problem and at what point in the package's life,
and it carries no requirement, no boundary, and nothing that changes how a rule below it is applied.
The paragraph's first sentence states the alignment requirement and its third states what the spec
does about it as of `0.0.3`; the middle sentence only dated them. That is the same disposition
[`spec-002`][spec-002-rationale] gave its own problem statement's opening chronology.

*Why the sentence is worth keeping rather than deleting, given what it points at.* The document it
names is not in the repository, so as a locator it resolves to nothing — but as provenance it records
something the spec cannot: this spec is not a discipline someone invented in the abstract, it is a
response to a specific review finding raised **while a headline feature was visibly half-shipped**.
That is the condition the four re-export conditions were written against, and it is why condition 1
says "effective end-to-end" rather than "exists". A reader who knows only the rules cannot tell
whether they were derived from a real failure or from taste.

*The thesis stayed.* The paragraph's opening pair of sentences — discipline rather than volume — is
what the rest of the document implements, and it reads as argument only because the document's
subject is an argument. Moving it would have left a rule set with no statement of what it is for.

### `### docs/README.md structure` — the rejected third section

Spec: [`docs/README.md` structure][spec-006-readme].

*Moved — the rejected alternative in full, with the reason it lost.* "There is no third section. The
reviewer suggested `Current` / `Planned` / `Not implemented yet`, but the third section duplicates the
second once the markers are in place. The sharper fix is the markers themselves, not more sectioning."

This is the one rejection the spec states as a rejection, and it is the paragraph a later reader is
most likely to re-open: a three-bucket split is the obvious shape for "works / coming / not built",
and nothing in the surviving two-section contract explains why it was declined. The reason is worth
preserving precisely because it generalizes past the README — **a status marker on every entry makes
a section boundary that encodes the same status redundant**, so adding the section buys a second
place for the same fact to go stale. That argument is the spec's own case for
`### Status-marker vocabulary` existing at all, stated once here against a concrete alternative.

*The rejection's own weak point, recorded because the spec never states it.* The argument assumes the
markers land. It answers "two sections or three?" and never answers "and what if neither section is
ever created?" — which is the branch that actually occurred. That is a fact about the outcome rather
than about the choice, so it belongs to the reconciliation item and not here; what belongs here is
that the alternative was weighed on redundancy grounds alone, with no fallback considered.

*No other alternative was weighed in this section, and that is the record rather than an omission.*
The two-tree split in the section's closing paragraph is stated as a requirement with its reason
attached inline — the reason names the generated tree document as the place both shapes are already
kept side by side, and casts the README's role as a pointer to it rather than a second copy — and
both halves stayed in the spec under the load-bearing carve-out.

### `## Open questions` — the release-gating judgement (section removed)

Bears on [Decision for 0.0.3][spec-006-decision].

*Moved verbatim, the whole section.* "None blocking 0.0.3."

*Why the section was removed rather than restated.* Every word of it is a judgement about one
release, made while that release was in flight: whether anything blocked `0.0.3`. A shipped spec
cannot keep answering that question, and the answer it froze is now trivially historical. Unlike its
sibling specs' `## Open questions` sections it carried no follow-up pointers, so nothing durable was
left behind by removing it — the section is three words of release status under a heading that
promises deliberation.

*What the judgement was worth, which is the one thing recording it buys.* It was correct about
`0.0.3` and it was measuring the wrong surface. Nothing blocked the release, because everything the
spec gated on was a **rule**, and rules ship the moment they are written down. The open question the
section could not see is the one this spec's own `### When to amend this spec` was supposed to
answer — whether anyone would apply the rules afterwards — and an `## Open questions` section scoped
to a single release has no slot for a question whose answer arrives over eleven versions. Recorded
here so the empty section is not read as evidence that the spec had nothing outstanding.

*Claim the spec no longer makes.* That anything is, or is not, blocking `0.0.3`.

## Standing note — the rules outlived their instruments

This is the observation the extraction pass is in a position to make and the spec itself never can,
because it is an observation *about* the document rather than a claim inside it. It is recorded as
analysis, not as a disposition: which sentences change, and how, is the reconciliation item's.

Spec-006 is the only spec in this repository whose subject is the repository's own documentation, and
that gave it a failure mode none of its siblings has. A feature spec is falsified when the feature
changes. This spec's rules were never falsified — the four re-export conditions, the promotion path,
and the never-promote-an-internal-helper rule all still describe how a name reaches the public
surface, and two of its topics hold at HEAD exactly as written. What was falsified is every **surface
the rules were aimed at**:

- The gate's documentation condition names a `docs/README.md` section, `## Current surface`, that
  never existed. Measured rather than inferred: `grep -n '^## ' docs/README.md` lists eighteen
  headings and none is it. The locus that emerged instead — a per-entry `**Status:**` line under
  `docs/GLOSSARY.md` `## Public exports` — satisfies the condition *better* than the section named,
  because the marker is per-entry and rendered from a database rather than hand-maintained.
- The seven-marker vocabulary the spec declares closed and single-sourced shrank by disuse.
  `experimental` and `aspirational` occur **zero** times across `docs/README.md`, `docs/TREE.md`,
  `docs/GLOSSARY.md`, and `TODAY.md`; `in flight` occurs **once**, in the glossary. The
  DB-enforced vocabulary behind the rendered glossary is **two** rows, `shipped` and `planned`.
- The gate was written as a **biconditional** over the four conditions rather than as a one-way
  requirement: satisfying all four was stated to be sufficient for a root export and not merely
  necessary. The package went the other way. Several families are shipped, tested, documented, and
  stable, and are still deliberately absent from the root namespace, because for them the import
  path *is* the opt-in boundary — so the four conditions are necessary and never sufficient. The
  claim is recorded here by its **shape and its consequence, not by its wording**: the
  reconciliation item rewrites the sentence that carries it, and a quotation of that sentence here
  would outlive the sentence itself.

The common cause is one property of this spec and not of the others: **its rules are discharged by
authors, and nothing executes them.** A `Meta`-key rule is checked by `types/base.py` every time a
type is declared; a re-export rule is checked by whoever remembers to check it. So the parts of
spec-006 that survived are the parts a later author would have re-derived anyway, and the parts that
rotted are the ones that required someone to come back to this document — which its own
`### When to amend this spec` asked for by name and received from nobody. The lesson generalizes past
this spec: **a documentation-discipline rule keeps only as much of its shape as some executable or
generated artifact is willing to hold.** The two rules that held are the two whose subject is source
code an author reads anyway; the three that drifted are the three whose subject was a prose document,
and the one surface that *did* deliver the spec's intent — per-entry status markers — did it from a
database, which is the same lesson stated as a success.

## Reconciliation against the shipped package

Appended by the reconciliation pass — the pass the extraction record above says would decide which of
the spec's surviving claims still hold. It ran eleven minor versions after the release, and its
instruction was to make the spec state what actually exists, in the spec's own voice, with every
explanation of a change landing here instead. So the spec carries no amendment block, no retraction
paragraph, and no chronology: it reads as a clean current contract, and this section is the only place
that says it once read otherwise.

**One correction to the record above, made rather than hidden.** `## Provenance of this record` states
that the spec carried three fenced blocks before the move and the same three after. That was true of
the move. This pass removed one of them — the `0.0.3` `__all__` tuple — so the spec now carries two,
both import-form examples. The move record is not edited; it describes the document as it stood at the
move, and this is the sentence that keeps a later reader from reading it as a current count.

**Where the spec asked for the duplicate that was retired, recorded here because nothing else durable
holds it.** Spec-006's `## Coordination with other specs` used to carry a bullet saying the
optimizer-visibility decision is "amended into" the optimizer spec's "Visibility status" so that spec
"carries the local context for its own re-export trajectory", and `## References` carried a second
bullet describing spec-002 as the carrier of "the local visibility-status amendment that this spec
governs". Those two bullets are the provenance of spec-002's copy: it existed because this spec
requested one. Under the single-ownership rule a concrete claim belongs to exactly one spec, and
provenance is what decides which copy is the duplicate — a copy that exists because another spec asked
for it is the duplicate. Both bullets are gone, and so is the section they requested.

### `## Problem statement` — the release-scoped second sentence

Spec: [Problem statement][spec-006-problem].

*Changed — the sentence that dated the document to one release.* It read that as of `0.0.3` the Layer 2
optimizer was effective end-to-end, so the spec recorded the promotion discipline **and the current
exported surface**. Two things falsified it. The clause about the optimizer is a status claim about a
release eleven versions back, and a spec that states its own release position has to be re-dated
forever. The second half was a promise this document should never have made: it said the spec records
the surface, and the surface is a roster this spec is the wrong place for.

*Alternative rejected — keep the clause and re-date it to the current release.* It loses on the same
argument the whole reconciliation runs on: a sentence that must be re-dated to stay true is a
maintenance obligation on prose, and this spec's central failure was obligations on prose. The
condition the clause was making — that a promoted name's code path is effective end-to-end — is already
condition 1 of the gate, where it is checkable.

*Claim the spec no longer makes.* That it records the exported surface. It records the rule and names
where the surface is defined.

### `## Where the public surface is defined` — the replaced `## Current state`

Spec: [Where the public surface is defined][spec-006-surface].

*Changed — the section was replaced, and its heading with it.* It carried three things, each falsified
differently. A five-name surface list, against 37 entries in `__all__` at the time of this pass. A
two-line summary of the onboarding document's structure, naming headings that document has never had.
And a Layer-3 mismatch paragraph listing eight not-yet-existing modules, six of which now exist, while
the two that do not have moved on: aggregates is carded for the beta line, and the fieldset surface is
planned as a package rather than the single module the spec named.

*Alternative rejected — refresh the roster to the current 37 names.* This is the obvious fix and it is
the trap. The roster has changed at least eleven times since `0.0.3` and changes again at `0.1.0`, so
refreshing it re-creates the maintenance obligation this cycle exists to retire, in the one document
whose subject is why such obligations fail. It also puts a package-surface inventory in a rules document
while two artifacts already hold it authoritatively — one executable, one generated.

*Alternative rejected — delete the section outright, as the optimizer spec's cycle did with its own
`## Current state`.* The precedent is real and it nearly applies. It loses because the gate's rules refer
to the roster: condition 3 reads a documented marker, the promotion path adds a name to a tuple, and a
reader who can find neither has a rule with no referent. What the section owed was **pointers, not
contents**, and that is what it now carries.

*Alternative rejected — retitle to `## Prior art`, following `spec-001`.* Rejected on content, exactly
as the optimizer spec's cycle rejected it: the section contains no prior-art survey, so the title would
be false. A heading named for the present was the defect the retitle was invented for, and a heading
naming where the surface is defined is not a claim about the present that can rot.

*Two categories the old binary framing had no room for, now stated in the spec.* One is structural — a
family that reaches consumers only by its own import path, on purpose. The other is conditional on an
optional distribution being installed, which is why its names resolve without appearing in the exported
tuple. Both were live at HEAD, and neither is expressible in a section that lists names plus a rule that
gates them: the old framing had exactly two states and these are a third and a fourth.

*Claims the spec no longer makes.* That the public surface is those five names; that the onboarding
document has the structure it summarized; that the eight named modules are absent from disk; that the
remaining mismatch risk is Layer 3.

### `### Top-level re-export rule` — the gate stops being a biconditional

Spec: [Top-level re-export rule][spec-006-reexport].

*Changed — the strongest single claim in the document.* The gate was written as a biconditional: the
package re-exports a name **iff** all four conditions hold. Satisfying all four was therefore stated to
be sufficient, not merely necessary. The package went the other way and did so deliberately, six times
over: families that are shipped, tested, documented, and stable, and are still absent from the root
namespace because for them the import path *is* the consumer's opt-in. A seventh case is conditional
rather than deliberate — the soft-dependency names stay reachable on the package while staying out of the
exported tuple. The corrected rule asserts necessity and denies sufficiency outright, and hands the
remaining half of the question to the promotion-path section. The wording is deliberately not reproduced
here: this pass rewrote the sentence that carries it, and a quotation would outlive the sentence.

*Alternative rejected — keep the biconditional and treat the six families as exceptions to it.* It
loses because they are not exceptions; they are the outcome of a rule the owning specs each applied on
purpose, and a gate whose exception list has six entries and grows with every subsystem is not a gate.
Naming them here would also do what the single-ownership rule forbids: pull six other specs' placement
decisions into this document, where they would go stale as each of those specs moved.

*Alternative rejected — weaken the gate to a checklist and drop the sufficiency question entirely.* It
loses because sufficiency is the interesting half. A reader whose subsystem passes all four conditions
needs to know that passing them does not settle the question, and a checklist that never says so is how
an accidental promotion happens.

*Changed — condition 3's locus.* It required the symbol appear in an onboarding-document section called
`## Current surface`, with a `shipped` marker. That section has never existed in that document. The
locus that emerged instead is the generated glossary's `## Public exports` list, each bullet linking a
per-feature entry that carries its own marker — which satisfies the condition's intent better than the
section named, because the marker is per-entry and rendered from a database rather than hand-kept.
Rejected alternative: name the section the spec wanted and leave the obligation open for whichever cycle
creates it — lost because the condition is a *gate*, and a gate pointed at a document section that does
not exist cannot be failed, which is why nothing ever failed it.

*Changed — the dotted-path closing paragraph.* It described the submodule path as what a name that
failed the gate falls back to. True, and it understated the case: for the boundary families the dotted
path is the contract. The paragraph now states both readings and says outright that the import form does
not distinguish them — only the owning spec does.

*Claims the spec no longer makes.* That satisfying the four conditions is sufficient for a root export.
That a documented contract lives in an onboarding-document "Current surface" section. That a dotted
submodule path implies a name failed something.

### `#### Decision for 0.0.3` — the fenced `__all__` tuple

Spec: [Decision for 0.0.3][spec-006-decision].

*Changed — the fenced five-name tuple was removed.* As a statement of what `__all__` contains it is
false by a factor of seven, and as a fenced code block it reads as the current surface no matter what
prose surrounds it. The decision itself survives in substance — which two names were promoted, on which
condition, and that both import forms remain supported — and the two fenced import examples that
demonstrate it are untouched. In the tuple's place is a single sentence naming the mechanical act of
promotion and pointing at the section that says where the tuple is pinned.

*Alternative rejected — keep the tuple, labelled as the surface `0.0.3` shipped with.* It loses on the
rule that a spec never narrates its own history: a labelled historical tuple is a chronology, and a
reader would have to apply a date to it to know what is true. Git holds the `0.0.3` tuple; the pinned
export test holds the current one.

*Also changed — the roster label.* The decision cited "O1-O6 and B1-B8" as its evidence. Those labels
are the optimizer spec family's vocabulary, and restating that family's roster here is the duplication
the single-ownership rule names. The evidence is now stated as the capabilities themselves, with the
optimizer spec named as the document that keeps the slice-by-slice record.

*Claim the spec no longer makes.* That `__all__` is a five-name tuple.

### `### When a subsystem is top-level vs subpackage-only` — the boundary rule the gate needed

Spec: [When a subsystem is top-level vs subpackage-only][spec-006-subsystem].

*Verified true and left standing, which is worth recording as a result rather than as silence.* The
promotion path — subpackage first, root export when the conditions are met, subpackage re-exports kept
so both import forms keep working — holds at HEAD subsystem by subsystem, and so does the rule that
internal helpers never get a top-level re-export. Two of the document's topics needed no correction, and
both are the two whose subject is source code an author reads anyway.

*Added — the third promotion outcome.* The section described exactly two states, subpackage-only until
promoted and promoted thereafter, which is why the gate could be written as a biconditional at all. The
missing state is a deliberate terminus: a subsystem that never gets promoted, because reaching it costs
the consumer something they are entitled to decline — an extra installed distribution, a body of Django
machinery they never asked for, a diagnostic surface that is unsafe left on. The added rule places that
call with the shipping spec, requires the reasoning to be recorded there, and makes this document a
licence for the call rather than an override of it. The three examples in the spec are illustrative of
the cost, not a closed list, and deliberately name no family.

*Alternative rejected — enumerate the families that took that route.* Six did, and naming them would
make this section a register that goes stale on the next one. The rule is what generalizes; the register
is the generated glossary, which already documents each of them with its import path stated.

### `### How status is published` — the replaced `### docs/README.md structure`

Spec: [How status is published][spec-006-readme].

*Changed — the section prescribed two onboarding-document sections that were never created.* It required
a `## Current surface` and a `## Planned surface`, each entry marked, plus the folder tree split into a
current tree and a planned tree with per-entry markers. Measured against that document during this pass,
none of the four exists; it runs installation, a quick start, a what-just-happened walkthrough, a
shipped-and-coming summary stamped with one version, the per-subsystem contract sections, testing, and
running the example, and it points at the glossary for per-feature status. The two-tree half **did** land,
in the generated tree document rather than the README, and it stamps each unbuilt entry with the card
that owns it instead of with a vocabulary marker — card-anchored provenance, which resolves further than
the marker the spec asked for.

*The rule survived its instrument, and that is what the section now states.* The requirement that nothing
consumer-visible goes unmarked is unchanged; what changed is the pair of documents that publish the
markers, and the fact that both are rendered rather than hand-kept. That last property is what the
original two-section scheme was trying to buy by hand, and it is worth more than the scheme was: a
hand-kept marker can disagree with the record it describes and a rendered one cannot.

*Alternative rejected — keep the obligation and hand it to the cycle that owns the onboarding document.*
That cycle exists and was live during this pass. It loses anyway: the obligation is only correct if a
hand-maintained per-entry marker list in a prose README is the right shape, and the outcome is evidence
that it is not — the same status arrived per-entry and generated, and the README's job turned out to be
pointing at it. A spec should not carry an obligation on a document it does not own when the requirement
is already met elsewhere in a better form.

*Alternative rejected — delete the section and fold "no entry without a marker" into the vocabulary
section.* It loses because *where* a marker is published and *which words* are markers are two rules, and
collapsing them hides the load-bearing half: that the marker attaches to the feature's entry rather than
being encoded by which section the entry sits in. That is also the surviving generalization of the
rejected three-section alternative the move recorded, which is why the pointer to it stays in this
section.

*The reason clause the move's record describes as attached inline was restated, and that record is not
edited.* The two-tree requirement's reason still sits inline with the requirement; what changed is which
document the trees live in. That record's load-bearing claim — that no other alternative was weighed in
the section — is untouched by this pass.

*Claims the spec no longer makes.* That the onboarding document carries a `## Current surface` or a
`## Planned surface` section. That the folder tree in that document becomes two trees. That a marker
vocabulary of `shipped` / `partial` / `experimental` governs one section and `planned` / `in flight` /
`deferred` the other.

### `### Status-marker vocabulary` — seven markers, one source, and neither was this spec

Spec: [Status-marker vocabulary][spec-006-vocabulary].

*Changed — the closed seven-marker list was replaced by a pointer to the single source that emerged.*
The spec declared seven markers and declared them single-sourced here. Four died of disuse: across the
four documents the rule governs, `experimental` and `aspirational` occur zero times, `in flight` once,
and `partial`'s occurrences are the ordinary word rather than a marker. Meanwhile a real single source
appeared where the rule could not see it — the glossary's own `## Status legend`, rendered from the same
database as the entries whose markers it explains, so the two cannot disagree. The section now delegates
outright: it names the source and says this document is not it.

*Alternative rejected — prune the list to the markers still in use and keep it here.* It loses twice
over. It would still be a second copy of a vocabulary that has an authoritative home, which is the
defect the single-ownership rule names; and pruning is precisely the maintenance-by-remembering that
produced four dead markers in the first place. A vocabulary in a document nothing renders decays the
moment the rendered one moves.

*Alternative rejected — keep the seven and record the four as unused.* It loses on the no-narration
rule: a closed vocabulary annotated with which members are dead is a chronology, and it asks the reader
to work out what is current.

*Kept deliberately — two properties of the legend, and one cross-spec pointer.* That a marker carries
the release it is true of is not decoration: the gate's condition 3 reads the stamp, so changing that
part of the legend changes what this spec gates on. That a marker attaches to an entry rather than to a document is
the argument the rejected three-section alternative lost on. And the `deferred` marker's meaning for a
held-back `Meta` key still names the type-contract spec's own section **by title**, because that spec
records the dependency in the other direction; dropping the citation would have falsified a sibling this
cycle has no licence to edit, and fixing it there would have been a second file's change for no gain.

*Claims the spec no longer makes.* That the marker vocabulary is these seven words. That it is
single-sourced in this document. That `partial`, `experimental`, `in flight`, and `aspirational` are live
markers.

### `### Alpha signaling rules` — both exemplars shipped

Spec: [Alpha signaling rules][spec-006-signaling].

*Changed — the two examples, not the rule.* The rule that language must match the marker is sound and
untouched, and its closing rule-of-thumb is the operative test the move deliberately left in place. But
its `partial` exemplar described the optimizer's end-to-end execution hook as still in flight, and that
hook shipped in the very release this spec records; its future-tense exemplars were the filter set and
the permissions module, which shipped at `0.0.8` and `0.0.10`. An example of hedged language whose
subject has shipped teaches the opposite of the rule.

*Alternative rejected — swap in currently-unshipped features as the new exemplars.* It loses on the
arithmetic of the last eleven versions: every feature the spec named as future has shipped, so any
replacement is a bet against the roadmap and rots the same way. The exemplars are now the *language
patterns* themselves, detached from any named feature, plus a requirement that hedged prose say which
release or card it is betting on. A pattern cannot ship, so it cannot rot.

*Changed — the marker the middle case keys to.* The three-way split keyed to `partial`, a marker the
live vocabulary does not carry. The case it covered is real and the legend has a marker for it: an entry
available but narrower than its eventual API. The rule now keys to that, and still requires both halves
be stated.

*Claims the spec no longer makes.* That the optimizer's end-to-end hook is in flight. That the filter
set and the permissions module are future work. That `partial` is a marker prose can carry.

### `### What a subsystem spec owes these rules` — the replaced `### When to amend this spec`

Spec: [What a subsystem spec owes these rules][spec-006-owes].

*Changed — the section asked for something that never happened once, in either direction, and this is
the cycle's root cause.* It listed eight future subsystems and asked each to pick a marker, specify a
migration path through the markers, list its test surface, and reference this spec for the rules; and it
required any new marker be folded back here in the same change, because the vocabulary was
single-sourced here. Seven of the eight shipped. Not one cited this spec. Every one decided its own
export placement locally, in its own spec, and no marker was ever folded back. The three drifted topics —
the documentation condition's locus, the two-section README scheme, and the marker vocabulary — are
downstream of exactly that.

*The correction is not a stronger request. It is moving the obligation onto artifacts that can hold
it.* The four obligations the section now carries are all discharged inside the subsystem's own change
and each leaves a trace something else already checks: a published entry carrying its marker, a test
pinning the consumer-visible contract plus the export pin where a promotion happened, a stated placement
decision with its reason, and any unknown marker landed where the vocabulary actually lives. None of them
asks anyone to return to this document. The section says why in one line, because in this case the reason
*is* the finding — the request that failed was the only one of the five that had no artifact behind it.

*Alternative rejected — keep the amendment obligation and add a compliance check.* Nothing can check it.
The obligation is "an author remembers to edit a document", and the only enforcement available would be
another rule discharged by an author, which is the same failure one level up.

*Alternative rejected — delete the section as unenforceable and say nothing.* It loses because the four
obligations above **are** enforceable and are the ones that matter; deleting the section would drop them
along with the request that failed, and leave the spec with a gate and no statement of who discharges it.

*Alternative rejected — keep the eight-subsystem list, updated to name the one that has not shipped.* It
loses on the roster argument again: a list of pending subsystems is an inventory, and this section's
subject is an obligation that does not depend on which subsystems are outstanding.

*Claims the spec no longer makes.* That a future subsystem spec should reference this spec for the rules,
or specify a migration path through the markers as a documentation deliverable. That a new marker is
added to this spec in the same change. That the vocabulary is single-sourced here. That filters, orders,
permissions, the connection field, relay interfaces, `Meta.primary`, and consumer overrides are future
work.

### `## Non-goals` — the second undischargeable pointer to a section that does not exist

Spec: [Non-goals][spec-006-nongoals].

*Changed — the layout pointer, not the non-goal.* Declining to own the layout is still right. But the
declining sentence pointed at a `## Package architecture` section of the onboarding document, which that
document does not have and, measured during this pass, has never had. The layout lives in the generated tree document,
which keeps the on-disk and target shapes side by side. Same shape as the documentation condition's
locus, and the same fix: point at what exists.

*Claim the spec no longer makes.* That the package layout lives in an onboarding-document
"Package architecture" section.

### `## References` — the unresolvable locator

Spec: [References][spec-006-references].

*Deleted — the alpha-review bullet.* It named recommendations #1, #2, #7, and #8 of a document that is
not in this repository, and its own second clause said this spec is the durable record of those findings.
The extraction pass declined to move it and argued the reason: a reference-list entry is a locator, not
an argument, so its defect is a claim-level question rather than a move. As a claim-level question the
answer is deletion. A locator that resolves to nothing is not a reference, the sibling contract spec's
cycle removed the identical bullet, and what the bullet was actually worth — that these rules answer a
specific review finding raised while a headline feature was visibly half-shipped, which is why condition
1 says "effective end-to-end" rather than "exists" — is already recorded in this file under
`## Problem statement`, at more length than the bullet ever carried.

*Alternative rejected — keep the bullet and reword it to say the review is not preserved.* It loses
because a reference section is a list of things a reader can go and read; an entry whose content is "the
source of this is unavailable" belongs in a rationale, and it is in one.

*Also changed — two more bullets.* The optimizer spec's entry described it as the carrier of the
visibility-status amendment, which the retirement removed; it now names spec-002 as the subsystem whose
public entry point the `0.0.3` decision applies the rule to. The onboarding document's entry called it
the surface this spec governs, which overstated a document this spec now makes no structural claim
about; the governed surfaces are named as what they are — the glossary for the documented surface and
the vocabulary, the consumer-facing prose for the signaling rules, and the package `__init__` for the
canonical surface.

*Claims the spec no longer makes.* That it is the durable record of the alpha review's findings. That
spec-002 carries a visibility-status amendment. That the onboarding document is the surface this spec
governs.

### The coordinated retirement of spec-002's `## Visibility status`

Spec: [Coordination with other specs][spec-006-coordination] and [References][spec-006-references].

*Changed by maintainer decision, and executed across every inbound site in one change.* The optimizer
spec carried a two-sentence `## Visibility status` section whose content this spec's own
`#### Decision for 0.0.3` already states at higher resolution, and it carried it **because this spec
asked for a copy** — the provenance recorded in this section's preamble. This spec has stopped asking.
The `## Coordination` bullet that requested the amendment and the `## References` bullet that described
it are both gone; spec-002 is still named as an implementation spec by the coordination bullet that
always did so. **The section's own disposition is argued where the section lived**, in the optimizer
spec's rationale companion, which is also where the export precision a prior cycle deliberately merged
into it is accounted for. This entry records only what spec-006 changed and why it stopped requesting a
copy; the two alternatives about the section itself are not restated here, because that would rebuild
the duplicate one level up.

*Alternative rejected — leave the duplicate and record the deferral for a sixth time.* Four prior cycles
took that posture and a standing board card carries it. It loses because it is what kept a two-sentence
duplicate alive across five cycles, and because the instruction that opened this one named it directly:
the inbound references were not fixed in the same change last time, so they are fixed in this one.

*Alternative rejected — retire this spec's `#### Decision for 0.0.3` instead and let spec-002 own the
optimizer's export placement.* It loses on subject. This spec owns the rule that admits a name to the
public surface and the decision is that rule's worked application; moving it would leave a rule with no
instance here and put a package-surface decision inside a subsystem spec, which is the shape the
single-ownership rule exists to prevent rather than an instance of it.

*What was verified rather than assumed, because a retirement is exactly where an inbound reference gets
missed.* The section was the second of two carriers of the optimizer-extension glossary anchor in
spec-002, so its removal leaves that anchor carried and spec-002's own glossary check green. The only
`#anchor` citation of spec-002 anywhere pointed at this section from its rationale companion; that
definition is removed and the sentence that used it now names what actually absorbed the content. The
deferral record in that companion is left standing and answered by an appended entry, so the deferral
and its discharge both survive. Two remaining occurrences of the words are quotations of historical
instructions in other cycles' documents, and are deliberately untouched.

*Claims this spec no longer makes.* That the optimizer-visibility decision is amended into spec-002. That
spec-002 carries the local context for its own re-export trajectory.

### What this pass measured, and what it deliberately did not touch

Every claim above about the onboarding document, the generated tree, the glossary, the export tuple, and
the marker counts was measured against the working tree during this pass rather than taken from a prior
reading — a separate cycle was editing the onboarding document at the same time, and four of the drift
findings are claims about that document. The measurements are recorded with their timestamp in the pass's
own build artifact, which closes with its cycle; what belongs here is the reason the numbers are not
repeated in the spec. **A count in a spec is a maintenance obligation with no owner.** The spec therefore
names loci and states rules, and every number this reconciliation rests on lives either in the artifact
that measured it or in the generated document that renders it.

No source file, test, or generated document was changed by this pass. The one measured contract violation
the reconciliation found — a handful of exported names carrying no bullet in the documented export list,
which is a live failure of condition 3 — is closed by the following item in the same cycle as a
documentation gap, not by weakening the condition to match the gap.

## Documented is not the same as exported

Appended by the pass that closed the reconciliation's review round. Two of the reconciliation's decisions
were sound in outcome and wrong in the premise they rested on, and one sentence it left standing could be
read as either a rule or a report. Both are settled here in the same shape the entries above use: the
correction lands in the spec's own voice, and the reasoning stays in this file.

### `## Where the public surface is defined` and `### Top-level re-export rule` — the documented locus is grouped, not flat

Spec: [Where the public surface is defined][spec-006-surface], [Top-level re-export rule][spec-006-reexport],
[When a subsystem is top-level vs subpackage-only][spec-006-subsystem].

*Changed — three sentences treated the glossary's export section as a flat list of root-exported names,
and it has never been one.* Read from its heading to the next one, that section is a set of lists
distinguished by import path: the package-root roster, then one list per family whose own dotted path is
how a consumer reaches it. So three of the six families the boundary rule governs are already registered
inside the very section the rule described as the place they are *not*. The consequences were an
unenforceable contrast in the boundary rule, and a documentation condition whose literal test could be
passed by names that are deliberately unexported — a quieter re-run of the drift this whole reconciliation
was convened to remove, and one the earlier pass had the evidence to catch, having counted the roster
itself.

*What replaced it is a distinction, not a longer description.* Carrying a bullet is what makes a name
documented, which every consumer-visible name owes; the list a bullet sits in is what says which import
surface the name is on. The gate's third condition now reads the roster list specifically and says
outright that a per-family list satisfies the documentation obligation while recording the opposite
placement, and the boundary rule now says where such a family's documentation goes instead of asserting
where it does not go. Nothing about the gate's strength moved.

*Alternative rejected — assert that the section is the root roster and treat the per-family lists as
non-conforming.* It loses twice. The document is generated from a database, so the assertion would be a
claim this spec cannot make true, and the lists it would condemn are the correct place for exactly the
placement the boundary rule licenses. A spec does not get to declare a conforming practice a violation
because a sentence would be tidier.

*Alternative rejected — relax the documentation condition to "documented anywhere in the glossary".* It
loses on the same ground as the reconciliation's refusal to soften that condition to fit the roster's
missing bullets: a condition that cannot fail is not a gate. The distinction between the two placements
is precisely what the condition is for.

*Alternative rejected — name the three registered families, or the three whose entries carry the path
inline.* It loses to the single-ownership rule for the same reason the boundary rule names no family: a
register in this document goes stale on the next family, and the generated glossary already is the
register.

*Claims the spec no longer makes.* That the documented export section is one bullet per exported name.
That a boundary family's documentation lives somewhere other than that section.

### `### How status is published` — the prose clause is a rule, and it is written as one

Spec: [How status is published][spec-006-readme].

*Settled — the sentence about documentation prose repeating markers was a rule wearing a report's
clothes.* As a report it was false the day it was written: the onboarding document and the capability
snapshot both use legend words freely, one of them as a release-stamped heading over a large group of
capabilities. As a rule it was worth keeping, because the failure it prevents is real — a second,
hand-kept marker surface drifting from the generated one. It is now stated as a prohibition with the
scope question answered inside it: prose publishes no marker of its own, and a summary written at release
scope is not a per-feature marker for the capabilities it covers.

*Why that resolves the composition problem rather than deferring it.* The rule about markers attaching to
a feature's own entry rather than to a document or a section already implied this: a summary is a section's
claim, so it never was a marker for anything inside it. And the scope sentence in the vocabulary section —
which lists the onboarding document and the capability snapshot among the documents whose status words come
from the legend — now reads as the same rule seen from the other side: those documents may use the
vocabulary, and may not become a second locus for it.

*Alternative rejected — record the onboarding document's release-stamped summary as a known
non-conformance owned by the cycle that owns that document.* It loses because the practice is correct, not
merely tolerated. A summary that points at the per-feature locus is what this spec asks prose to do, and
escalating it would have exported a defect the spec had invented in its own wording.

*Alternative rejected — narrow the sentence to a description of what those documents happen to do
today.* It loses to the rule the reconciliation itself established: a sentence that must be re-checked
against another document to stay true is an obligation on prose with no owner, and this section's subject
is the discipline, not the current contents of two files.

*Claim the spec no longer makes.* That documentation prose does not repeat the markers, stated flatly
enough to be read as a measurement of two documents this spec does not own.

## A rule stated over an artifact nobody measured

Appended by the pass that closed the documentation-completion round, after the writes that finished the
documented export list. One sentence about that list was falsified by the very bullets the round added, and
it is the third correction of one shape rather than a third unrelated defect. Both are recorded here: the
correction in the same form as the entries above, then the shape itself, once.

### `## Where the public surface is defined` — what a bullet's link can be required to reach

Spec: [Where the public surface is defined][spec-006-surface], and the gate it feeds,
[Top-level re-export rule][spec-006-reexport].

*Changed — one sentence required every bullet in the documented export list to link the entry carrying
that bullet's own name's marker, and the generated list has never worked that way.* Measured over the
rendered document, **fourteen of its forty-eight bullets** reach an entry titled by some other name: two
all-defaults constants documented inside the frozen dataclass entry that names them, an async client twin
and a typed result object documented inside their client's entry, a set of unittest bases sharing one
entry, a coroutine sharing its sync sibling's, a package version string reached through the release
mechanism that moves it, and two classes whose only honest destination is the entry for the behavior they
wrap. **Two of the fourteen were written by the round that found this; twelve predate it.** So the sentence
was a claim about a generated document that the document contradicts — the same defect as the flat-list
premise the preceding entry corrects, in the same sentence's neighbourhood, one level further down.

*What replaced it keeps the obligation and drops the arithmetic.* A bullet must reach a per-feature entry
carrying the marker the name is documented under, whether the link sits on the name or inside the gloss,
and the reason a gloss may carry it is stated rather than left to precedent: the entry serves several names,
or it documents the behavior the name wraps. The requirement still fails for a bullet that reaches no entry
at all — which is exactly what caught a bulleted-but-unlinked export in this cycle — so it remains a
condition that can fail. The bullet-versus-group distinction the preceding entry installed is untouched,
and the gate's third condition is byte-unchanged: it reads the roster group and a `shipped` marker, and
neither depends on which name titles the entry.

*Alternative rejected — leave the sentence and let the two undocumented classes earn entries of their
own.* It loses on measurement, not on taste. Entries for those two names would close two of the fourteen
falsifications and leave twelve standing, so the sentence would still be false about the document after the
work meant to make it true; and it makes a durable file's accuracy contingent on a card on the beta line.

*Alternative rejected — a carve-out for names with no entry of their own.* It buys the first exception in a
gate this cycle finished de-exceptioning, and the shape it would except is the majority practice among the
non-conforming bullets rather than an edge case.

*Alternative rejected — record the divergence and change nothing.* It leaves the reconciled spec carrying a
clause its own cycle's write falsified, which is the failure the cycle was convened to end.

*Claim the spec no longer makes.* That a bullet's link resolves to an entry named for that bullet's own
name.

### The shape behind three corrections, named once

*Three of this cycle's corrections were one failure, and naming it is worth more than the three
instances.* Each time, a rule the reconciliation wrote turned out stricter than the practice it described:
the documented export list was read as one flat roster when it is four lists distinguished by import path;
the documentation condition was read as satisfied by every bulleted export when one bullet carried no link
at all; and a bullet's link was required to resolve to its own name's entry when a third of the list points
elsewhere by long-standing convention. Not one was a mistake about what the rule should require. Each was a
mistake about the artifact the rule was written over, made by describing that artifact from its heading
instead of measuring it.

*Why it matters beyond this document.* It is the same failure as the obligations this spec carried from the
start against a section of the onboarding document that never existed — the failure that made a residual
cycle necessary eleven versions after the release. A rule stated over an unmeasured artifact is
unenforceable in one specific direction: it condemns conforming practice, so the practice reads as the
defect and the rule reads as sound, which is why such a rule survives review. The repair each time was to
measure the artifact and state the rule over what is there, never to relax the rule to fit — and the two
are easy to confuse, because each ends in a sentence admitting more cases than the one it replaced. The
test that separates them is whether the replacement can still fail, and against which input.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-002-rationale]: spec-002-optimizer-0_0_2-rationale.md
[spec-005-rationale]: spec-005-django_type_contract-0_0_3-rationale.md
[spec-006]: ../spec-006-public_surface-0_0_3.md
[spec-006-coordination]: ../spec-006-public_surface-0_0_3.md#coordination-with-other-specs
[spec-006-decision]: ../spec-006-public_surface-0_0_3.md#decision-for-003
[spec-006-nongoals]: ../spec-006-public_surface-0_0_3.md#non-goals
[spec-006-owes]: ../spec-006-public_surface-0_0_3.md#what-a-subsystem-spec-owes-these-rules
[spec-006-problem]: ../spec-006-public_surface-0_0_3.md#problem-statement
[spec-006-readme]: ../spec-006-public_surface-0_0_3.md#how-status-is-published
[spec-006-reexport]: ../spec-006-public_surface-0_0_3.md#top-level-re-export-rule
[spec-006-references]: ../spec-006-public_surface-0_0_3.md#references
[spec-006-signaling]: ../spec-006-public_surface-0_0_3.md#alpha-signaling-rules
[spec-006-subsystem]: ../spec-006-public_surface-0_0_3.md#when-a-subsystem-is-top-level-vs-subpackage-only
[spec-006-surface]: ../spec-006-public_surface-0_0_3.md#where-the-public-surface-is-defined
[spec-006-vocabulary]: ../spec-006-public_surface-0_0_3.md#status-marker-vocabulary

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
