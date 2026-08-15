# Rationale: spec-007 — 0.0.4 onboarding docs and spec consolidation (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-007-onboarding_docs_spec_consolidation-0_0_4.md`][spec-007]. The
spec is the contract and states only what holds; everything that explains **how it got there** lives
here: the alternatives each choice rejected and why each lost, the justification the spec used to
narrate about itself, and every claim it once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-007-0.0.4` shipped ten minor
versions ago and the rule that gates a build on this move did not exist then; this pass supplies it.
Text marked *Moved* below was cut out of the spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec section**, named by the section's own heading and linked to its anchor. A
  section with no entry here lost nothing.
- **Who reads it.** The role-by-role answer is [`BUILD.md`][build] `### Who reads it, and when`,
  which is that mechanism's canonical home. A reader looking for what the package *does* wants the
  spec, and neither file: this card shipped no package surface at all.
- **This spec has no numbered Decisions.** It predates that convention, so the key is the heading.
  Two entries key to headings the move removed; each says so and anchors the section its subject
  bears on.
- **The move itself is two items, and that is the whole move.** This spec is a card-snapshot stub, and
  it is among the repository's smallest rather than its smallest: 011, 012, 013 and 024 are all
  smaller, and the `### The preamble ...` entry below names them with their byte counts. Spec-007
  measured 2,282 bytes, 65 lines and zero fenced code blocks at `947f7494`, before this pass cut
  anything out of it. It has almost no deliberative layer, because it was never deliberated: it is a
  rendered snapshot of a Kanban card. Exactly two passages were deliberation rather than contract,
  and both are recorded under `## Provenance of this record`. A two-item move is the correct move
  here, not a thin one, and this file does not pad it with invented debate.
- **The substance is therefore the change record, not the move.** [`BUILD.md`][build] requires each
  entry to carry the alternatives rejected, every change the claim has undergone with the cause, and
  any claim the section may no longer make. For this spec the third clause is the deliverable:
  **five of six `## Scope` claims were true on the day they were written and are false, uncheckable,
  or superseded now**, and this file is the only place that history is recorded.
- **Where the record is a change and not a choice, it says so.** Several of the changes below were
  made by bulk housekeeping commits whose messages state no reasoning. Those entries name the commit
  and stop. Where this pass supplies reasoning of its own — the stub-shape entry does — it is
  labelled as this pass's argument against constraints verifiable at HEAD, never as a recovered
  discussion.
- **This pass did NOT reconcile the spec.** Every claim below is recorded **as the spec makes it**.
  Which surviving claims are restated, repointed, or dropped is the reconciliation pass's
  determination, and its record appends below this one when it runs.
- **The siblings are pointed at, not duplicated.**
  [`spec-006-public_surface-0_0_3-rationale.md`][spec-006-rationale] narrates the documentation
  *discipline* this card's doc set was arranged under, and
  [`spec-005-django_type_contract-0_0_3-rationale.md`][spec-005-rationale] shows the
  entry-per-heading shape. Neither is retold. Nor are the decisions of the *later* cards that
  falsified this spec's claims: each owns its own reasoning, and this file records only what
  spec-007 claimed and how it fared.

## Provenance of this record

- **Moved** — cut from the spec by this pass, and now only here: the whole preamble paragraph
  beginning "This file is intentionally lightweight", and the whole `## Planning note` section
  (heading plus its one-word body). **Added in exchange, and it is the pass's only addition to the
  spec:** the paragraph's slot now carries the one-line pointer sentence naming what was moved and
  where, plus its `[spec-007-rationale]` link definition under `<!-- docs/SPECS/ -->`.
- **Nothing was deleted outright by this pass.** [`worker-1.md`][worker-1] rule 2 deletes rather
  than moves prose the current decisions have falsified, and one sentence inside the moved preamble
  is falsified. It is quoted below **inside an entry that states it is falsified** — as the record of
  a claim the spec may no longer make, which is a record clause and not a restoration. It is not
  reproduced anywhere as live instruction, and its removal from the spec is unconditional.
- **Deliberately left in the spec by this pass**, and the list is exhaustive: the title, target-release
  and owner lines; the `Status:` line; the whole of `## Card snapshot`; all six `## Scope` bullets;
  all **eight** `## Other` bullets; the link-definition block. Every one is either contract-shaped or a
  **status claim**, and a status claim moved into a rationale file is neither a legitimate entry here
  nor the deletion the move prescribes for falsified prose — its disposition against HEAD is the
  reconciliation pass's call. This is the same line [`spec-006`][spec-006-rationale]'s extraction
  pass drew around its status sections.
- **No fenced code block was involved.** The spec carried zero before this pass and carries zero
  after.
- **No glossary anchor changed carrier.** The spec's single term is carried by one reference-style
  link, `[optimizer behavior][glossary-djangooptimizerextension]` in `## Scope` bullet 2. Neither
  moved passage contained it and this pass did not touch that bullet, so nothing was re-sited.
  Confirmed by re-running `scripts/check_spec_glossary.py` against the spec after the move.

## Entries keyed to the spec

### The preamble — the stub's own justification, and an instruction that cannot be followed

Bears on [Card snapshot][spec-007-card-snapshot], the section the paragraph introduced.

*Moved verbatim, the whole paragraph.* "This file is intentionally lightweight. It preserves the
card scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable
repository file. Before implementation work starts from this file, expand it into the full
builder-format spec described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`."

*Why the first two sentences moved rather than stayed.* They explain why the file exists, which is
process justification and not a contract about anything. They are also a **duplicate**: the spec's
`Status:` line already says "canonical spec stub created to keep the Kanban DB one-to-one spec
invariant intact", so the identity survives the move intact, one level up, in the line whose job it
is. A concrete claim stated twice goes stale in one of the two copies.

*Claim the spec no longer makes, and why it is false rather than merely stale.* That implementation
work may start from this file, and that the file should be expanded into a full builder-format spec.
Both are impossible. The card's work shipped at `0.0.4` on 2026-05-08 and this file was created
**afterwards**, on 2026-06-01, as a back-fill — so there was never any implementation work to start
from it. And the expansion was never performed, in this file or in any of its six siblings carrying
the identical paragraph.

*The paragraph is boilerplate, not authorship, which is why it is worth recording that it was
removed.* The same three sentences appear verbatim in seven archived specs — measured at `947f7494`,
007 (2,282 bytes), 011 (1,797), 012 (1,651), 013 (1,669), 016 (4,558), 024 (1,618), 026 (3,593), and
007's figure is the pre-move one. It carries no fact about
this card. Removing it from this one file makes spec-007 diverge from its siblings; that divergence
is intended, and each sibling's own residual cycle owns its own copy.

*Why the stub is the right shape — this pass's argument, not a recovered debate.* No commit message,
spec, or standing doc records the stub shape being weighed against anything, so what follows is
reasoning supplied here against constraints that are verifiable at HEAD. The instruction the
paragraph carries is one of three things that could have happened to this file, and it is the worst
of them:

- **Expand it into a full builder-format spec.** Rejected. The work shipped three weeks before the
  file existed, so an expansion could only be a reconstruction — a document *inferred* from the
  finished doc set and then presented in the shape readers trust as a pre-implementation contract.
  Every later pass would have to treat invented slices, tests, and decisions as the record of what
  was actually decided. A stub cannot mislead about a deliberation it does not claim to have had.
- **Delete the file.** Rejected, and mechanically refused. `examples/fakeshop/apps/kanban/signals.py`
  will not save a card whose status is `done` without a linked `SpecDoc`
  (`signals.py::_validate_done_card_has_spec`) and at least one glossary link
  (`signals.py::_validate_done_card_has_glossary_link`), and it refuses to move or delete either off
  a done card (`signals.py::protect_done_card_spec`,
  `signals.py::protect_done_card_glossary_link`). The file *is* the `SpecDoc` target. Deleting it
  would leave the FK pointing at nothing.
- **Keep the snapshot and reconcile it when it drifts.** What happened, and what this residual cycle
  is. The shape's real cost is the one this file's entries measure: a rendered snapshot of a
  documentation state has a short half-life, and nothing re-renders it.

### `Status:` — the one-to-one invariant is real, and enforced in code

Spec: the `Status:` line above [Card snapshot][spec-007-card-snapshot].

*Nothing moved, and nothing should change.* Recorded because the sentence reads like self-narration a
reconciliation pass would cut, and it is instead an accurate description of an executable
constraint. The four guards named in the entry above are the mechanism; the backfilled
`-terms.csv` row is the glossary link they demand. The stub is load-bearing.

### `## Planning note` — a retained field's discarded value

Bears on [Card snapshot][spec-007-card-snapshot]; the section this entry keys to no longer exists.

*Moved verbatim, the whole section.* The heading `## Planning note` and its entire body, the single
word "shipped".

*Why the section was removed rather than restated.* It renders one Kanban field, and the field is
now empty: `Card.planning_note` for card 7 is `''`. A section whose only content is a database
value has nothing to restate once the value is gone.

*What actually happened to it, stated precisely because the obvious reading is wrong.* The
planning-state *dimension* was retired — `1592bb90` (2026-07-09) dropped the `PlanningState` lookup
model and the `Card.planning_state` FK — but `Card.planning_note`, the free-text field this section
renders, was **explicitly retained** by that same commit. What changed is its value: card 7's note
went from `"shipped"` to `""` in `1592bb90` itself, alongside the removal of the now-meaningless
`Severity:` and `Planning state: Shipped` lines from this spec's `## Card snapshot`. So the section
was rendering a live field whose value had been discarded as redundant with `Status`, not a column
that ceased to exist. The distinction matters to anyone reading the other six stubs: their
`## Planning note` sections are stale for the same reason, and none of them is stale because a model
was dropped.

*Claim the spec no longer makes.* That the card carries a planning note, or that it says "shipped".

### `## Card snapshot` — the label list

Spec: [Card snapshot][spec-007-card-snapshot].

*Nothing moved.* The claim is "Labels: `docs`, `release`"; the card carries **three**, `docs`,
`internal`, and `release`. The third was added on 2026-06-09 (`2baf93b5`), eight days after the
snapshot was rendered.

*The row is a symptom and the section is the cause.* This snapshot has already been hand-maintained
once — `1592bb90` deleted two of its lines when the fields behind them were retired — which is the
whole objection to it: a hand-copied render of database rows in a file that nothing re-renders will
drift on every board edit, and each drift has to be noticed by a person. Recorded so the
reconciliation weighs the section rather than patching one bullet.

*Claim the spec no longer makes.* That card 7 carries exactly two labels.

### `## Scope` 1 — the root README's two jobs, one of which moved out

Spec: [Scope][spec-007-scope].

*Nothing moved.* The claim is "Root [`README.md`][root-readme] is the canonical documentation map
**and operational entry point**." The first half holds and the second does not.

*What the file lost, measured.* At the release commit `231911a8` the root README carried
`## Installation`, `## Development Setup`, `## Running`, `### Seeding the example database`,
`### Test users`, `### Sharded mode (multi-DB)`, `## Testing`, `### Formatting and Linting`,
`### Updating Version`, `## Build`, `## Publish`, `### Updating dependencies`, and
`### Local usage in another project`. None of them is in the file at HEAD, whose eight `##` headings
are "Why this package exists", "Why it's fast", "Is this for you?", "Status", a pointer to
[`docs/README.md`][readme], "Project documentation", "Inspired by", and "Contributing & Security" —
positioning, map, and status, with no operational step in any of them. The operational content is now
split between [`CONTRIBUTING.md`][contributing] (setup, test, lint, version, build, publish,
dependencies) and [`docs/README.md`][readme] (install, quick start, running, seeding). The removal
landed at `2bd7cb84` (2026-05-16).

*The surviving half is intact, which is worth recording separately.* `## Project documentation` is
present at HEAD with eight entries, and every reference-style definition behind them resolves on
disk.

*Claim the spec no longer makes.* That the root README is the operational entry point.

### `## Scope` 2 — three of four items, and the sole glossary carrier

Spec: [Scope][spec-007-scope].

*Nothing moved.* The claim is "[`docs/README.md`][readme] is code-first: quickstart, three-minute
path, [optimizer behavior], and status."

*Item by item at HEAD.* Quickstart holds (`## Quick start`). Status holds
(`## Today and coming next`). Optimizer behavior holds (`## Nested connection indexing`).
**"Three-minute path" names no section anywhere in the repository.** When this record was written the
phrase sat on exactly three surfaces — this spec, the card row in `KANBAN.md`, and the same row
inside the `KANBAN.html` payload — all three renders of the one `CardItem`. **It did name a section
once, and card 7's own commits are the whole of that section's lifetime.** [`docs/README.md`][readme]
gained a literal `## Three-minute path` heading with a five-step body at `83c25963` and lost it again
at `3a4d40b7`, both commits dated 2026-05-05. The `0.0.4` release commit `231911a8`, three days
later, already contains no occurrence of the phrase, and the file this spec renders from first enters
the tree at `81e4704d` (2026-06-01) with the bullet intact — so the section had already been gone for
twenty-seven days on the day the bullet was rendered into a spec that describes it in the present
tense.

*And "code-first" now describes a different document.* [`docs/README.md`][readme] is 1,003 lines and
117,358 bytes at HEAD, and its bulk is consumer documentation later cards landed there — the
production security profile, the transport boundary, the write contracts, the session-auth
deployment boundary. The adjective was accurate about a much smaller file.

*The constraint any rewrite of this bullet inherits.* The words "optimizer behavior" in this sentence
are the **sole carrier** of the spec's only glossary anchor, and the DONE-card glossary chain depends
on it. They were not written as a link: `e1f9ed26` (2026-06-04) converted the plain phrase into
`[optimizer behavior][glossary-djangooptimizerextension]` precisely to give the backfilled
`-terms.csv` row a body link. So the link is a retrofit onto whichever sentence happened to contain
a linkable phrase, which is why it sits inside the most heavily falsified bullet in the file.

*Claim the spec no longer makes.* That [`docs/README.md`][readme] contains a "three-minute path".

### `## Scope` 3 — a true claim about a file whose name was mechanically replaced

Spec: [Scope][spec-007-scope].

*Nothing moved.* The claim is "[`docs/GLOSSARY.md`][glossary] is the capability catalog with
value-led optimizer language **and comparison table**."

*The subject of the sentence did not exist under that name when the card shipped.* At `231911a8` the
capability catalog was `docs/FEATURES.md`, and it did carry the comparison table: `## Quick
comparison`, a four-column `| Concern | graphene-django | strawberry-graphql-django | this package |`.
The rename to [`docs/GLOSSARY.md`][glossary] landed twelve days later at `40c1855f`, a bulk
"housekeeping: rename files" commit that also renamed `BETTER.md` to [`BACKLOG.md`][backlog] and
rewrote every mention across the tree, `KANBAN.md` included. **The card row was rewritten by that
sweep**: at `231911a8` it read `docs/FEATURES.md`, and it still did one commit before the rename.
The kanban database was then seeded from the already-rewritten board, and this spec rendered the
substituted text on 2026-06-01.

*That chain is the entry's whole point.* The sentence is not a false claim about
[`docs/GLOSSARY.md`][glossary]; it is a true claim about `docs/FEATURES.md` with a different
filename substituted into it by a mechanical sweep. It therefore cannot be checked against the state
it describes at all — the reader has no way to know which file is being asserted about. That failure
mode is not "the docs moved on"; it is a rename sweep silently converting a historical record into a
present-tense claim. `40c1855f`'s message records no reasoning for the rename and this file does not
invent any.

*What is gone, and what changed hands.* There is no comparison table at HEAD: the file's only table
is its `## Index`, and no file in the repository contains a `## Quick comparison` heading. Upstream
comparison survives in a different form — the per-entry parity markers and the root README's "Why
it's fast" — but not as a table. Separately, the file's
**provenance** changed: it is now rendered from the fakeshop glossary app's database by
`scripts/build_glossary_md.py`, so the "value-led optimizer language" the bullet credits is produced
by a generator from database rows, and hand edits to the file are reverted by the next render.

*Claims the spec no longer makes.* That the capability catalog carries a comparison table; and that
its wording is authored in the file it names.

### `## Scope` 4 — the one claim that held

Spec: [Scope][spec-007-scope].

*Nothing moved, and nothing is retired.* "[`docs/TREE.md`][tree] is the detailed layout/test-tree
reference" is true at HEAD, and it is the only `## Scope` bullet that is wholly true.

*It gained a provenance the spec cannot know.* [`docs/TREE.md`][tree] is now rendered by
`scripts/build_tree_md.py` from module docstrings plus the kanban database's predicted-path rows, so
a missing module docstring fails the render and hand edits are clobbered. The document's *role* is
unchanged; who writes it is not.

### `## Scope` 5 — a promise the changelog broke four minors later

Spec: [Scope][spec-007-scope].

*Nothing moved.* The claim is "[`CHANGELOG.md`][changelog] is condensed and **no longer relies on
design-doc pointers for release context**."

*Falsified, and measurably.* The `0.0.8` entry cites `spec-027-filters-0_0_8.md` and
`spec-028-orders-0_0_8.md` for exactly that purpose, with both reference definitions live in the
bottom block. "Condensed" is also no longer descriptive: 100,289 bytes across 437 lines at
`947f7494`.

*Why this entry stops at recording.* The falsified statement is a claim *about*
[`CHANGELOG.md`][changelog] rather than a defect in it, and `AGENTS.md` rule 21 closes that file to
any change not explicitly asked for. Whether the changelog itself should stop citing specs is a
maintainer question; whether this spec may keep promising that it does not is the reconciliation
pass's.

*Claims the spec no longer makes.* That [`CHANGELOG.md`][changelog] is condensed, or free of
design-doc pointers.

### `## Scope` 6 — the fold-in policy, reversed by the commit that created this file

Spec: [Scope][spec-007-scope].

*Nothing moved.* The claim is "Completed design-doc content is folded into durable docs, while
remaining specs preserve design history and follow-up work." This is the entry worth the most,
because the bullet's two halves were in tension and the repository resolved it against the first
one.

*What "folded into durable docs" meant when the card shipped: deletion.* The card's work is three
commits, none of which is the release commit. `4b8dce07` (2026-05-05) created `docs/FEATURES.md` and
cut [`docs/README.md`][readme] down to a code-first document. `83c25963`, the same day, condensed
[`CHANGELOG.md`][changelog] and **deleted six completed spec files** —
`docs/spec-django_types.md`, `docs/spec-optimizer.md`,
`docs/spec-optimizer_nested_prefetch_chains.md`, `docs/spec-optimizer_beyond.md`,
`docs/spec-django_type_contract.md`, and `docs/spec-public_surface.md` — 2,495 deleted lines against
459 added. `3a4d40b7` finished the pass. The release commit `231911a8` (2026-05-08) touched only
[`CHANGELOG.md`][changelog] and `KANBAN.md`; it is the version cut, not the work.

*And the deletion was undone twenty-seven days later, by the commit that created this file.*
`81e4704d` (2026-06-01) re-established every one of those six specs under `docs/SPECS/` with the
`spec-<NNN>-<topic>-<0_0_X>` naming — as restorations of the deleted content, not new writing:
`docs/spec-django_types.md` was 50,075 bytes when deleted and
`docs/SPECS/spec-001-django_types-0_0_1.md` was 50,195 bytes when `81e4704d` created it, the
difference being self-referential filename updates and nothing else. Both figures are measured at
the commits they belong to, which is what makes them evidence that the restoration was a
restoration; neither is a claim about the file at HEAD, where later cycles have since edited it.

*The rejected alternative, and it is on the record by outcome rather than by argument.*
Delete-on-fold-in lost because it destroyed the design history the same bullet's second clause
promises to preserve. The two halves cannot both hold while completed specs are deleted, and the
archive convention is what makes them compatible: the content folds into the durable docs **and**
the spec survives at `docs/SPECS/`. No commit message argues this; the reversal is the argument.

*The second layer the bullet stops short of.* "Remaining specs preserve design history" is now an
explicit two-file split — the spec carries the contract and a `-rationale.md` sibling carries the
deliberation ([`BUILD.md`][build] `## Spec rationale extraction`) — and the fold-in target set is
pinned by `AGENTS.md` rule 26 to [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], and
`KANBAN.md`, in the completing spec's own slice. **This file is an instance of the mechanism the
bullet predates.**

*Claim the spec no longer makes.* That folding completed design-doc content into the durable docs
retires the spec file.

### `## Other` — a heading that names a card section the board has retired

Bears on [Scope][spec-007-scope]; the heading this entry keys to no longer exists — the reconciliation
pass retired it, for the reason this entry gives, and `### `## Other` — retired, not renamed` below
records that disposition.

*Nothing moved.* Three separate facts about this section, and the first corrects the obvious reading.

*The heading was faithful when it was written.* At `81e4704d`, the commit that created this file,
card 7's items sat in exactly **two** sections, `Scope` and `Other` — measured from the `KANBAN.html`
payload at that commit. So the spec did not flatten a differentiated card body into an
undifferentiated list; it rendered, accurately, a section the board actually had. The four-way
taxonomy the card carries at HEAD (`Scope`, `Why it matters`, `Files likely touched`, `Note`) arrived
on 2026-07-20, seven weeks later, in a three-commit board-wide migration: `0c08204f` reclassified 378 `other` items
board-wide, `ac7cc6a4` emptied the section, and `4f68d3f2` deleted its lookup row in migration 0016.
`#### Other` renders zero times in `KANBAN.md` at HEAD. **The spec's `## Other` heading now names a
card section that does not exist in the database at all**, and its eight bullets are the
pre-reclassification shape frozen in place — one `Why it matters` row, five `Files likely touched`
rows that read as scope commitments, and two `Note` rows.

*The final bullet is a borrowed claim, stale in two ways.* It states the spec-filename convention and
cites `docs/builder/BUILD.md` "Spec filename pattern". (a) That heading does not exist:
[`BUILD.md`][build]'s heading is `## Spec and build-plan filename pattern`. A dangling section-title
citation is invisible to `scripts/check_spec_glossary.py`, which validates glossary anchors and not
section titles — which is why it survived four months. The same dangling citation also sits in
[`CONTRIBUTING.md`][contributing], a file outside this cycle's reach. (b) The lifecycle now has a
second half the bullet stops short of: a completed spec is archived to `docs/SPECS/` with its
`-terms.csv` and `-rationale.md` companions to `docs/SPECS/appx/`, by the **next** spec's author at
[`NEXT.md`][next] Step 8, never at the completing spec's own merge. The convention's owners are
`AGENTS.md` rule 26 and [`BUILD.md`][build]; this spec is the borrower, and a borrowed copy is what
went stale while the owners moved on.

*And the whole document is written in the present tense about 2026-05-08.* Every `## Scope` and
`## Other` bullet is an accurate record of what card 7 did; five of the six `## Scope` bullets are
false as statements about now. Nothing in the file tells a reader which tense it means. The card body
has the same property and is correct to have it — a Done card's `Scope` is a record — but a spec is
read as a contract that currently holds.

*Claim the spec no longer makes.* That `Other` is a section of card 7.

## Standing note — what survived was the roles, not the contents

This is the observation the extraction pass is in a position to make and the spec itself never can,
because it is about the document rather than a claim inside it. It is analysis, not a disposition:
which sentences change, and how, belongs to the reconciliation pass.

Spec-007's subject is **the state of five documentation files**, and documentation state is the
fastest-moving thing in this repository. But the failures are not evenly spread, and the split is
measurable. The spec makes two kinds of claim:

- **Role claims** — which document answers which question. `docs/TREE.md` is the layout reference;
  the root README is the documentation map. **Both hold at HEAD, unchanged, after ten minor
  versions.**
- **Content-inventory claims** — what a document contains, or what it no longer needs to contain.
  The README is also the operational entry point; the code-first doc has a three-minute path; the
  catalog has a comparison table; the changelog is condensed and cites no specs. **Every one of them
  failed**, by a different mechanism each time: content relocated (`2bd7cb84`), a section the card's
  own commits created and deleted on one day (`83c25963` then `3a4d40b7`), a rename sweep
  substituting the subject (`40c1855f`), a generator taking over authorship, and a later release
  simply doing the thing the card promised it would stop doing.

  The second of those is the sharpest illustration the thesis has. Every other mechanism in the list
  is some *later* commit than card 7's own falsifying the claim; this one is the authoring card
  falsifying itself, before the release the card shipped in. A scope bullet can describe a section
  that the same day's next commit has already removed, and nothing in the process that renders a card
  into a spec can notice.

So the durable contribution of a documentation-consolidation card is the **division of
responsibility** it established, and the perishable part is the table of contents each document had
on the day it shipped. This matters beyond one spec, because the pull when reconciling a file like
this is toward rewriting it as a current inventory — which guarantees the same reconciliation is owed
again at the next release, and makes the spec a duplicate of a map whose owner is the root README's
own `## Project documentation` section.

The stub shape sharpens the same point rather than causing it. A card snapshot renders whatever the
card said, so it cannot distinguish a role claim from an inventory claim, and it freezes both in the
present tense. What it buys in exchange is that it never pretends to more than it has: the one thing
this file could not have recovered, had the 2026-06-01 back-fill been written as a full
builder-format spec instead, is which of its claims someone actually decided.

## Reconciliation record — what the spec now says, and why

The record above was written by the extraction pass, which deliberately reconciled nothing: every claim
is recorded there **as the spec made it**. This section is the reconciliation pass's own record, appended
below it as that pass's `## How to read this file` bullet said it would be. Nothing above is retracted —
one link definition and one entry's pointer line were re-aimed at the section that survives, and both
re-aimings are named below.

The spec went from 2,365 bytes / 62 lines to 2,983 bytes / 57 lines. Both are **working-tree**
measurements taken on top of `947f7494` — the before-figure is the state the extraction pass left on
disk, not the committed file, whose own figure `## How to read this file` records. The file grew in
prose and shrank in structure, because two sections became one and every surviving sentence had to
state a contract rather than render a row.

### The strategy, and what it rejected

The strategy is the one `## Standing note` above argues for, adopted without restatement: reconcile
toward the **division of responsibility** the card established — which document answers which
question — and let the contents of each document be that document's own business. Every claim in the
reconciled `## Scope` is therefore a role claim, and the section opens by saying so: no two of these
files answer the same question. The lead sentence states that division and does **not** credit it to
the card, because the division as it now stands is not entirely the card's act — see the root-README
bullet below.

Two alternatives lost:

- **Rewrite `## Scope` as a current inventory** of what the five files contain. Rejected: every content
  claim this spec has ever made has failed within ten minor versions, so an inventory would owe the same
  reconciliation again at the next release, and it would make the spec a second copy of the map whose
  owner is the root [`README.md`][root-readme]'s own `## Project documentation` section.
- **Keep the falsified halves with a tense marker** — an "as of `0.0.4`" hedge, or a note that a claim
  has since been superseded. Rejected on [`BUILD.md`][build] `## Spec rationale extraction`: the spec
  states the contract that holds and never narrates its own history, so a reader never has to apply a
  chronology to work out what is true. The chronology is this file's job, and every claim retired below
  is already recorded above with the commit that falsified it.

### `## Card snapshot` — the board fields are the database's

Spec: [Card snapshot][spec-007-card-snapshot].

The section kept its heading and lost its board-metadata bullets. It now names the card, its status, and
its milestone, and says outright that labels, priority, relative size, and the card's item rows belong to
the Kanban database and are rendered into `KANBAN.md`.

*Why the section rather than the bullet.* The stale-label finding is `## Card snapshot`'s third drift in
one file: two lines were hand-deleted from it when the fields behind them were retired, and the label
list went stale eight days after it was rendered. Patching the label bullet to read three labels was the
obvious repair and was rejected — it re-rots on the next board edit, and it re-states rows whose owner
re-renders them on every change. Deleting the section outright was also rejected: four entries above this
one resolve to its anchor — the preamble entry, the status-line entry, the planning-note entry, and the
label entry — and the card's identity is the one board fact a spec is entitled to state, since the spec
exists to be that card's `SpecDoc` target.

*Claims the spec no longer makes.* That card 7 carries exactly two labels; that it is Medium priority or
relative size S. All three remain true in the database and none is the spec's to assert.

### `## Scope` — six rendered rows became eight contract claims

Spec: [Scope][spec-007-scope].

Bullet by bullet, against the record above:

- **The root README.** The map half held and is restated as the whole claim, narrowed from "every
  other document" to the rest of this set: the README points at all five of the other files named
  here, but at none of `AGENTS.md`, `START.md`, or [`BUILD.md`][build], so the universal was false
  outside the set. The operational half is gone, and the division that replaced it is stated
  positively in a new bullet: [`CONTRIBUTING.md`][contributing] owns setup, tests, formatting,
  versioning, build, and publish. Naming the successor is the point — a
  claim that merely dropped "operational entry point" would leave the reader unable to tell where the
  content went, which is the failure this whole spec is about.
  **That division is not this card's act, and the spec must not say it is.** The card's three
  documentation commits (`4b8dce07`, `83c25963`, `3a4d40b7`, all 2026-05-05) and the release commit
  `231911a8` (2026-05-08) touch `CONTRIBUTING.md` in none of their file sets. At `231911a8` the file
  carried three of the six responsibilities this bullet names — getting started, test suite, and
  linting — and none of the other three; versioning, build, publish, and a dependencies section
  arrived at `b57eba38`, on the same day as the root-README removal the entry above dates and eight
  days after the release. So the bullet is a true statement of the settled division
  and a false one about who performed it, which is why the lead sentence was decoupled from the card
  rather than the bullet dropped.
- **`docs/README.md`.** "Three-minute path" has named nothing since `3a4d40b7` and is deleted rather
  than moved ([`worker-1.md`][worker-1] rule 2). "Code-first" is dropped too: it was an accurate
  adjective about a much smaller file and is now an inventory claim about a document ten cards have
  written into. What survives is the role — the entry point for *using* the package — and the three
  items that still resolve. **The glossary anchor was re-sited in the same edit that rewrote the
  sentence**, into the clause about runtime behavior, which is the clause the term actually belongs
  to; the link text is unchanged, so the `-terms.csv` row still matches.
- **`docs/GLOSSARY.md`.** The comparison table is gone and the claim goes with it. The catalog role
  holds, and the reconciled bullet adds the one property that makes the role load-bearing rather than
  decorative: one stable anchor per entry, which is why the rest of the documentation links to it instead
  of re-explaining it. The file's generated provenance is deliberately **not** stated — `START.md`
  "Rendered docs — fix the source, not the file" owns that, and a borrowed copy is what went stale in the
  bullet retired below. The bullet's first form borrowed one more thing — the glossary's own category
  taxonomy, of which it named three of four. A partial enumeration that reads as complete is the same
  defect in miniature, so the enumeration is dropped rather than completed: the entry-and-anchor
  property is the spec's to state, and the taxonomy is [`docs/GLOSSARY.md`][glossary]'s.
- **`docs/TREE.md`.** Unchanged in substance; the wording is normalized to match the other bullets.
- **`CHANGELOG.md`.** "Condensed" and "no longer relies on design-doc pointers" are both false and both
  deleted; what remains is the release-record role. `AGENTS.md` rule 21 closes the changelog itself, so
  the reconciliation happens here and in the spec, never by editing the file the claim is about. Whether
  the changelog should stop citing specs stays a maintainer question, unchanged from the entry above.
- **The fold-in bullet.** Restated to say what the repository actually settled on — completed content
  folds into the durable docs **and** the spec files are retained as the design-history record — which is
  the resolution `81e4704d` imposed on the bullet's own internal tension. The lifecycle around it is
  pointed at rather than restated; see the next entry.
- **The non-goal.** The card's `Why it matters` row said "no upstream-parity surface"; it is the one
  claim under the retired `## Other` heading that was not a duplicate, and it is now the closing `## Scope`
  bullet, stated as what it is: this card shipped documentation only.

### `## Other` — retired, not renamed

Bore on [Scope][spec-007-scope]. The heading named a card section the board deleted in migration 0016,
and the entry above records that in full. Its eight bullets were dispositioned rather than dropped: the
five `Files likely touched` paths were already named in `## Scope`, the first `Note` row restated
`## Scope` in summary, the `Why it matters` row became `## Scope`'s closing bullet, and the second `Note`
row is the borrowed convention retired in the next paragraph. Nothing survived that `## Scope` does not
now say, so a renamed section would have been an empty container kept for the sake of its heading.

*The borrowed spec-filename bullet is pointed at, not corrected.* The single-ownership rule says a
concrete claim stated in two places is a defect and provenance decides which copy is the duplicate: the
owners are `AGENTS.md` rule 26 and [`BUILD.md`][build] `## Spec and build-plan filename pattern`, and
spec-007 is the borrower. Repairing the dangling heading citation was the smaller edit and was rejected —
a corrected borrowed copy is still a copy, and this one had already gone stale twice while the owners
moved on. The reconciled fold-in bullet cites both owners instead. **This does not retire the last stale
copy**: [`CONTRIBUTING.md`][contributing] carries the same dangling citation and is outside this cycle's
writable set, so it is a maintainer follow-up rather than an edit.

*Claim the spec no longer makes.* That an in-flight design doc's lifecycle ends at the fold-in, or that
[`BUILD.md`][build] has a heading called "Spec filename pattern".

### The present-tense reading is resolved by construction

Every surviving sentence is now true at `947f7494` as a statement about now, so the document no longer
needs a tense a reader has to infer. The card body still carries the original present-tense rows and is
still correct to — a Done card's `Scope` is a record — and the divergence between the two is intended.

### The link scaffold, and this file's own pointers

The spec's definition block gained `[changelog]`, `[contributing]`, `[root-readme]`, `[glossary]`,
`[readme]`, `[tree]`, and `[build]`, and lost `[backlog]`, which no body text had used since the file was
created. All ten canonical group headers are present and in order and every definition resolves on disk.
The depth trap the archived location creates was re-checked in both directions: from `docs/SPECS/`,
`../../README.md` is the root [`README.md`][root-readme] and `../README.md` is
[`docs/README.md`][readme] — two different files with the same name, both now linked from the same
section.

In this file, `[spec-007-other]` was removed and the entry that used it re-aimed at
[Scope][spec-007-scope], matching the pattern the `## Planning note` entry already uses for a section
that no longer exists. That is the only change to anything above this section, and it exists so no
definition points at an anchor the spec no longer has.

### What the audit of this record changed in it

The reconciliation above was audited before it closed, and that audit corrected four of its
statements in place rather than appending to them, because each was a defect *in* the record rather
than a further change to the spec. Named here so a reader of the finished file does not have to diff
it:

- The measurement sentence opening this section attributed both the before- and after-figures to
  `947f7494`. Neither is the committed file at that commit: both are working-tree measurements taken
  on top of it, and the committed figure `## How to read this file` carries is a third number again.
  Both are now labelled as the working-tree states they are.
- `### The strategy, and what it rejected` called the division the card's durable output. It now says
  the lead sentence deliberately does not credit the division to the card.
- The root-README bullet gained the chronology that decoupling rests on: which commits performed the
  `CONTRIBUTING.md` half, and that none of the card's own did.
- The `docs/GLOSSARY.md` bullet gained the reason its enumeration was dropped rather than completed.

The spec changed in three places in the same pass: the `## Scope` lead sentence no longer attributes
the division to the card, the root-README bullet's "every other document" is narrowed to this set,
and the glossary bullet's three-of-four category list is gone. All three are recorded in the bullets
above rather than as a separate list, so each change sits with the claim it belongs to.

A later pass — this cycle's final verification of the reconciliation — corrected two further
statements in this file and none in the spec. The root-README bullet's `231911a8` clause read as a
claim about a three-section `CONTRIBUTING.md`; the file carried seven `##` headings at that commit,
three of them the ones the clause names, so the clause is now scoped to the six responsibilities the
bullet is about. And the first bullet in this section had been corrected in place without retiring
the qualifier the correction contradicted, leaving a sentence that said "only" of one figure and then
claimed the other too.

The cycle's closing archive audit corrected one statement, and it sits in the extraction record above
rather than in this one. The `## Scope` 2 entry counted the "three-minute path" surfaces in the
present tense, and the reconciliation the entry precedes then deleted the phrase from the spec — so a
count that was correct when it was measured described a set the same cycle had changed. It is
anchored to the state it measured rather than restated at the new one, which keeps it a measurement
instead of a claim that rots again on the next edit. Nothing in the spec was touched.

That audit's own review then found that the same sentence's other half was false, and correcting it
supplied the record a fact it had been missing rather than retracting one it had. The clause read
"there never was a section by that name"; `docs/README.md` carried a literal `## Three-minute path`
heading with a five-step body from `83c25963` to `3a4d40b7`, both card 7's commits and both
2026-05-05. So the section's whole lifetime is inside the card that named it, and the enumeration in
`## Standing note` now carries that as its own falsification mechanism instead of "a section that
never existed". A third site, the `docs/README.md` bullet above, is scoped to `3a4d40b7` for the same
reason. Nothing in the spec was touched by this correction either. The clause was re-endorsed rather
than caught by the archive audit that rewrote its sentence: the audit kept it on the strength of a
working-tree `grep`, which can reach only the present-tense half standing beside it — **a
present-tense command cannot verify a past-tense claim, and an absolute about history needs a command
that names a commit.**

This item's final verification then dropped the count that sentence carried — it read "survived two
passes" — rather than restating it at a re-derived value. The sentence named no population for the
number, so a reader could not tell which passes it ranged over, and the rule it teaches does not
depend on a count at all.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../../BACKLOG.md
[changelog]: ../../../CHANGELOG.md
[contributing]: ../../../CONTRIBUTING.md
[root-readme]: ../../../README.md

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md
[readme]: ../../README.md
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-005-rationale]: spec-005-django_type_contract-0_0_3-rationale.md
[spec-006-rationale]: spec-006-public_surface-0_0_3-rationale.md
[spec-007]: ../spec-007-onboarding_docs_spec_consolidation-0_0_4.md
[spec-007-card-snapshot]: ../spec-007-onboarding_docs_spec_consolidation-0_0_4.md#card-snapshot
[spec-007-scope]: ../spec-007-onboarding_docs_spec_consolidation-0_0_4.md#scope

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
