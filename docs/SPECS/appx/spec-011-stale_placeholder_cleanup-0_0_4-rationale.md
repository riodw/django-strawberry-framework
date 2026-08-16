# Rationale: spec-011 — stale placeholder cleanup (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-011-stale_placeholder_cleanup-0_0_4.md`][spec-011]. The spec is the
contract and states only what holds; everything that explains **how it got there** lives here: what
the card actually removed, why one placeholder survived it, the alternatives each choice rejected,
and every claim the spec once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-011-0.0.4` shipped at `0.0.4` on
2026-05-08 and the rule that gates a build on this move did not exist then; this pass supplies it.
Text marked *Moved* below was cut out of the spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec section**, named by the section's own heading and linked to its anchor. A
  section with no entry here lost nothing.
- **This spec has no numbered Decisions**, and it was never deliberated: it is a rendered snapshot of
  a Kanban card, created at `81e4704d` (2026-06-01) by the archive-and-renumber pass, three weeks
  after the work shipped. So the key is the heading, and two entries key to headings the
  reconciliation removed; each says so and anchors the section its subject bears on.
- **The stub shape, and the boilerplate preamble, are argued once and not retold here.**
  [`spec-007-…-rationale.md`][spec-007-rationale] `### The preamble — the stub's own justification,
  and an instruction that cannot be followed` weighs expand-it / delete-it / keep-and-reconcile
  against constraints verifiable at HEAD, and names this spec by byte count (1,797 at `947f7494`)
  among the seven archived specs it measured as carrying the identical paragraph. That argument
  applies here unchanged and is cross-referenced rather than repeated; this file records only what is
  specific to spec-011. Five of those seven still carry it at this working tree — `spec-012`,
  `spec-013`, `spec-016`, `spec-024`, `spec-026` — spec-007 and this spec being the two whose
  residual cycles have run.
- **The substance is therefore the change record.** [`BUILD.md`][build] requires each entry to carry
  the alternatives rejected, every change the claim has undergone with the cause, and any claim the
  section may no longer make. For this spec the deliverable is the **recovered history the stub does
  not contain**: three placeholders retired with their skip reasons, one kept and later closed, and a
  set of replacement fixtures that changed hands twice within a day. A card whose whole contract is a
  deletion is uncheckable unless the deleted set is named, and the stub named none of it.
- **Every fact below was measured, not restated.** Each commit, count, and quotation carries the
  command or blob it came from. Where a figure in this cycle's build plan disagreed with the
  measurement, the measurement is recorded and the disagreement is named.
- **The move and the reconciliation are one pass**, so this file carries both records: the entries
  keyed to the spec first, then `## Reconciliation record — what the spec now says, and why`.

## Provenance of this record

- **Moved** — cut from the spec by this pass, and now only here: the whole preamble paragraph
  beginning "This file is intentionally lightweight", and the whole `## Planning note` section
  (heading plus its one-word body). Both are quoted below inside the entries that dispose of them.
- **Added in exchange:** the paragraph's slot now carries the one-line pointer sentence naming what
  moved and where, plus its `[spec-011-rationale]` link definition under `<!-- docs/SPECS/ -->`.
- **Deleted outright rather than moved**, per [`worker-1.md`][worker-1] rule 2, because the current
  contract falsifies them: the `## Card snapshot` board-metadata bullets, the `## Other` heading and
  its six bullets, and the tense of `## Scope` bullet 2. Each deletion is recorded below as a claim
  the spec may no longer make; none is restored anywhere as live text.
- **No fenced code block was involved.** The spec carried zero before this pass and carries zero
  after.
- **Both glossary anchors changed carrier, and both survive.** `#definition-order-independence` and
  `#scalar-field-override-semantics` were carried by `## Scope` bullets 1 and 2; the reconciled
  `## Scope` carries them on the rewritten M2M bullet and the closing scalar-override paragraph. The
  link texts `definition-order` and `scalar-field` are unchanged, so both
  `spec-011-…-terms.csv` rows still match, and
  `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md`
  exits 0 (`OK: 2 terms`) after the rewrite.

## Entries keyed to the spec

### The preamble — boilerplate whose instruction is counterfactual

Bears on [Card snapshot][spec-011-card-snapshot], the section the paragraph introduced.

*Moved verbatim, the whole paragraph.* "This file is intentionally lightweight. It preserves the card
scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable repository
file. Before implementation work starts from this file, expand it into the full builder-format spec
described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`."

*Claim the spec no longer makes.* That implementation work may start from this file, and that the
file should first be expanded into a full builder-format spec. The card's work landed at `118f71a1`
(2026-05-07) and shipped in the `0.0.4` release commit `231911a8` (2026-05-08); this file was created
on 2026-06-01 at `81e4704d`, so there was never any implementation work for it to precede.

*Why the first two sentences moved rather than stayed.* They explain why the file exists, which is
process justification and not a contract about anything — and the spec's `Status:` line already says
the same thing one level up, in the line whose job it is. The three-way choice behind the stub shape
is [`spec-007-…-rationale.md`][spec-007-rationale]'s, cross-referenced above and not re-argued.

### `## Planning note` — a retained field's discarded value

Bears on [Card snapshot][spec-011-card-snapshot]; the section this entry keys to no longer exists.

*Moved verbatim, the whole section.* The heading `## Planning note` and its entire body, the single
word "shipped".

*Why it was removed rather than restated.* It renders one Kanban column, and the column is now empty
for this card: `select number, title, planning_note from kanban_card where number=11` against a
read-only copy of `examples/fakeshop/db.sqlite3` returns `11|Stale placeholder cleanup|`. A section
whose only content is a database value has nothing to restate once the value is gone. The field
itself was **retained** when the planning-state dimension was retired — the mechanism is recorded in
[`spec-007-…-rationale.md`][spec-007-rationale]'s entry for the same section, and is not repeated.

*Claim the spec no longer makes.* That the card carries a planning note, or that it says "shipped".

### `## Card snapshot` — the board fields are the database's

Spec: [Card snapshot][spec-011-card-snapshot].

*Nothing moved; the board-metadata bullets were deleted.* The section claimed "Labels: `cleanup`,
`docs`, `tests`". The card carries **four** at HEAD — `cleanup`, `docs`, `internal`, `tests` — the
fourth added on 2026-06-09 at `2baf93b5`, eight days after the snapshot was rendered, by the same
board-wide commit that added `internal` to card 7.

*Why the section rather than the bullet.* Patching the label list to read four labels was the obvious
repair and lost for the reason [`spec-007-…-rationale.md`][spec-007-rationale] gives at length: a
hand-copied render of database rows in a file that nothing re-renders drifts on every board edit, and
the same patch is then owed again. Deleting the section outright also lost — the card's identity is
the one board fact a spec is entitled to state, since the spec exists to be that card's `SpecDoc`
target, and three entries in this file resolve to its anchor.

*Claims the spec no longer makes.* That card 11 carries exactly three labels; that it is Low priority
or relative size XS. All remain true in the database and none is the spec's to assert.

### `## Scope` 1 — the card's whole contract was a deletion, and it named nothing deleted

Spec: [Scope][spec-011-scope].

*Nothing moved; the bullet was rewritten.* The claim was "Replaced stale M2M and forward-reference
skips with [definition-order][glossary-definition-order-independence] tests." True, and uncheckable:
it names no skip, no test, and no file, so a reader could not confirm it without recovering the
commit from history. The set is finite and nameable — **three** placeholders, retired in one commit,
`118f71a1` (2026-05-07, "Complete spec-foundation.md - Slices 7-12 (v0.0.4)"), which also carried the
foundation card's slices.

| Retired placeholder | Its skip reason at `118f71a1~1` |
|---|---|
| `tests/optimizer/test_extension.py::test_optimizer_applies_prefetch_related_for_m2m` | "Slice 4+: M2M relation — fakeshop has no M2M field; deferred." (body was a bare `pass`) |
| `tests/types/test_base.py::test_relation_m2m_returns_list` | "Slice 3+: M2M relation — fakeshop has no M2M field; deferred." (body was a bare `pass`) |
| `tests/types/test_base.py::test_forward_reference_resolves_when_target_defined_later` | "Slice 3+: forward-reference / definition-order independence. The current implementation requires targets to be registered first; lazy_ref is pending." (body was a bare `pass`) |

Read from `git show 118f71a1~1:tests/types/test_base.py` and
`git show 118f71a1~1:tests/optimizer/test_extension.py`. None of the three names exists anywhere
under `tests/`, `examples/`, or `django_strawberry_framework/` at HEAD, and
`grep -rEn "pytest\.mark\.(skip|xfail)" tests/types/ tests/optimizer/` returns zero lines.

*The same commit created all three replacement files* — `tests/types/test_definition_order.py`,
`tests/types/test_definition_order_schema.py`, and `tests/optimizer/test_definition_order.py` are
absent at `118f71a1~1` and present at `118f71a1` — and deleted the two staged anchors that named the
pending work: the `.. todo:: spec-foundation 0.0.4` module-docstring block in
`tests/types/test_base.py` and the `# TODO(spec-foundation 0.0.4): DELETE this skipped placeholder`
comment above the forward-reference placeholder. `grep -rn "spec-foundation"` over the tree at HEAD
hits only this cycle's own build plan, so no anchor from this card survives in source.

*What the replacement coverage was pinned against, and why that changed twice the same day.* This is
the fact the stub could not have: the definition-order tests `118f71a1` created imported
`tests.fixtures.cardinality_models` — **test-only** `Book` / `Profile` / `Tag` / `User` models
existing solely to give the suite the cardinalities `fakeshop` lacked. That is the same weakness the
retired placeholders had, moved rather than removed. Two later `0.0.4` cards closed it:

- `DONE-013-0.0.4` (real M2M coverage) added the managed `library` example app at `73004d74`
  (2026-05-07 12:22) — real migrated models with genuine `ManyToManyField` columns, plus live HTTP
  coverage in `examples/fakeshop/test_query/test_library_api.py`.
- `DONE-014-0.0.4` (testing shift) re-pointed the definition-order tests at those models and deleted
  `tests/fixtures/cardinality_models.py` at `1057ddc2` (2026-05-07 13:08). The import path became
  `apps.library.models` at `a7ca9cc2`, when the example project was restructured.

So `tests/optimizer/test_definition_order.py::test_plan_relation_decisions_match_cardinality_after_finalization`
asserts `plan_relation` on `Book.genres` and the reverse `Genre.books` against real managed models
today, which is what makes the retired optimizer placeholder's *intent* discharged rather than merely
deleted. The chain is worth recording because the card's scope bullet reads as though the cleanup
were complete on its own commit; it was completed by its two successors within three hours, and
neither the stub nor the board says so.

*Claim the spec no longer makes.* None. The bullet was true; it was rewritten because it was
uncheckable, not because it was false.

### `## Scope` 2 — the kept placeholder, and a tense the spec outlived

Spec: [Scope][spec-011-scope].

*Nothing moved; the bullet was deleted and replaced by a statement of the current division.* The
claim was "**Kept** the remaining scalar override skip documented as a separate
[scalar-field][glossary-scalar-field-override-semantics] concern under `DONE-019-0.0.6`" — written in
a tense that stopped holding at `0.0.6`.

*What was kept, and why.* `tests/types/test_base.py::test_consumer_annotation_overrides_synthesized`,
whose subject is an override contest between a consumer's class-level annotation and the synthesized
one — scalar-override semantics, not definition order. Its skip reason at `118f71a1~1` already
recorded the split in its own words: "Slice 2 known issue: Strawberry's `@strawberry.type` decorator
regenerates `cls.__annotations__` from its own field metadata after our merge in
`DjangoType.__init_subclass__`, so the consumer's class-level annotation loses to the synthesized
one. … Tracked separately from the optimizer split."

*The word "documented" in the bullet names an act, and it is one commit later than the retirement.*
`118f71a1` left that reason untouched; the very next commit, `1d9ca597` (2026-05-07 10:56, "Finished
spec-foundation.md"), rewrote it to point at the surviving coverage: "Deferred scalar-field override
behavior: … This is unrelated to the 0.0.4 relation-override contract, which is pinned in
`tests/types/test_definition_order.py`." Recorded because the bullet's tense is what falsified it and
the act it names is real — the card did document the split; it simply cannot go on claiming the skip
still stands.

*What closed it.* `a357c68c` (2026-05-19) deleted the placeholder
from `tests/types/test_base.py` — decorator, TODO block, and body, 33 deleted lines — and added
eighteen tests to `tests/types/test_definition_order.py` in the same commit
(`git show a357c68c -- tests/types/test_definition_order.py | grep -c "^+def test_"` -> 18), of which
`::test_annotation_only_scalar_field_override_wins_over_synthesized` is the direct successor. That
commit is card `DONE-019-0.0.6`'s, though its message names the spec by its **pre-renumber** number
(`docs/spec-015-consumer_overrides_scalar-0_0_6.md`, archived as
`spec-019-consumer_overrides_scalar-0_0_6.md`) — the same renumber that makes a bare `spec-011`
reference ambiguous across this repository's older documents. **This
cycle's build plan says "six siblings"; the measurement is eighteen**, and the deleted TODO block
inside the placeholder itself predicted "18 sibling tests", which corroborates it.

*The alternative the reconciliation rejected.* Restating the bullet as "the skip was later retired at
`0.0.6`" — the smallest possible edit, and forbidden: [`BUILD.md`][build] `## Spec rationale
extraction` says the spec never narrates its own history, so a reader never applies a chronology to
work out what is true. The reconciled text states the standing division of concerns and names the
owning card instead, and the chronology lives here.

*Claims the spec no longer makes.* That a scalar-override placeholder is kept, skipped, or pending
anywhere in the test tree; that `DONE-019-0.0.6` is where that placeholder is *documented*, as
opposed to where the behavior is owned and shipped.

### `## Other` — a heading that names a card section the board has retired

Bears on [Scope][spec-011-scope]; the heading this entry keys to no longer exists.

*Nothing moved; the heading and its six bullets were deleted.* The section rendered six Kanban rows
of four kinds under a heading that names none of them: one `Why it matters` row ("internal test/doc
cleanup."), one restatement of `## Scope` bullet 1, three `Files likely touched` paths, and one bare
card id (`DONE-019-0.0.6`). At HEAD the board carries a four-way taxonomy — `KANBAN.md`'s
`DONE-011-0.0.4` card renders `#### Scope`, `#### Files likely touched`, `#### Why it matters`, and
`#### Note` — so the spec's `## Other` names a card section the database no longer has, and its
bullets are the pre-reclassification shape frozen in place. The board-wide migration that retired the
section is recorded in [`spec-007-…-rationale.md`][spec-007-rationale] and is not repeated.

*Disposition, bullet by bullet, rather than a bulk drop.* The three file paths are named in the
reconciled `## Scope` as the tests that pin each retired placeholder's subject — with the two files
the placeholders were removed *from* added, which the rendered list never had. The restated scope row
was a duplicate of the bullet above it. The `DONE-019-0.0.6` row survives as the ownership sentence
closing `## Scope`. Only "internal test/doc cleanup." has no successor: it is a board-level triage
note about the card's value, not a claim about the package, and a spec that says its own subject is
internal cleanup tells a reader nothing the `## Scope` section does not.

*Claim the spec no longer makes.* That `Other` is a section of card 11.

### The `[backlog]` link definition — recorded, not fixed

Spec: the link-definitions block, `<!-- Root -->` group.

`[backlog]: ../../BACKLOG.md` is defined and never used: `grep -c "backlog"` over the spec returns 1,
the definition itself. It is **deliberately left in place**. Eight tracked Markdown files carry the
identical unused definition —

```shell
for f in docs/SPECS/*.md docs/SPECS/appx/*.md; do
  [ "$(grep -c '\[backlog\]' "$f")" = 1 ] && echo "$f"
done
```

lists `spec-011`, `spec-012`, `spec-013`, `spec-016`, `spec-024`, `spec-026`, `spec-036`, and
`spec-054`, and a repo-wide sweep of every `.md` defining `[backlog]` finds the same eight. Fixing
one file of a cross-surface pattern leaves the surface *divergently* wrong rather than uniformly
wrong, which is the disposition [`worker-0.md`][worker-0] `## Closing out a kanban card` prescribes,
so it goes to this cycle's deferred-work catalog instead. **This cycle's build plan says fifteen
stubs share it; the measured figure at this working tree is eight** — the plan's number is the one
to distrust, and two concurrently-edited specs are inside the swept set, so the count is anchored to
this measurement rather than asserted as stable.

## Reconciliation record — what the spec now says, and why

The spec went from 1,797 bytes / 60 lines to 3,440 bytes / 53 lines: it grew in prose and shrank in
structure, because four sections became two and every surviving sentence had to state a contract
rather than render a row. The before-figure is the committed file at `054de9dd`; the after-figure is
this pass's working tree on top of it.

### The strategy, and what it rejected

The strategy: a cleanup card's contract **is** the set it removed, so the spec must name that set and
say what covers each subject now, and nothing else. Two alternatives lost.

- **Leave `## Scope` as two summary bullets and put the names only here.** Rejected: it keeps the
  spec uncheckable against the tree, which is the defect this pass exists to close. A reader
  confirming a cleanup card needs the deleted names in the contract, not in the deliberation file —
  the rationale answers *why*, and the spec must answer *what*.
- **Rewrite the spec into a full builder-format spec** with slices, a test plan, and a definition of
  done. Rejected for the reason [`spec-007-…-rationale.md`][spec-007-rationale] gives: the work
  shipped three weeks before the file existed, so any such expansion is a reconstruction presented in
  the shape readers trust as a pre-implementation contract. A stub cannot mislead about a
  deliberation it does not claim to have had.

### `## Scope` — two rendered rows became a named set

Spec: [Scope][spec-011-scope]. The section now names all three retired placeholders by
`path::QualifiedName` (`AGENTS.md` rule 27 — no `path:NN` line numbers, which rot on the next edit of
a file this spec does not own), pairs each with the test that pins its subject today, and closes with
one checkable negative — no skipped or `xfail`-marked test remains under `tests/types/` or
`tests/optimizer/`. Every named symbol was re-derived at this working tree, not copied from the build
plan. The scalar-override paragraph replaces the kept-skip bullet with the standing division of
concerns and the owning card.

*Why the negative is stated at all.* It is the only sentence that can go stale without anyone editing
this spec, and that is deliberate: it is the card's contract, so a future skip landing in either
directory should have to face it.

### The link scaffold

The block keeps all ten canonical group headers in order. It gained `[spec-011-rationale]` under
`<!-- docs/SPECS/ -->` and three `<!-- tests/ -->` definitions for the surviving coverage files; it
keeps the unused `[backlog]` for the reason the entry above gives. Every path was disk-checked from
`docs/SPECS/`, and the archived-depth trap was re-checked in both directions: `../../tests/…` reaches
the package test tree and `../GLOSSARY.md` reaches [`docs/GLOSSARY.md`][glossary], with no
same-named file one level up to mask a bad depth. The retired placeholders' own files are cited as
bare symbol paths rather than links, since the symbols no longer exist in them and a link would
promise otherwise.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../../BACKLOG.md
[kanban]: ../../../KANBAN.md

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md
[glossary-definition-order-independence]: ../../GLOSSARY.md#definition-order-independence
[glossary-scalar-field-override-semantics]: ../../GLOSSARY.md#scalar-field-override-semantics

<!-- docs/SPECS/ -->
[spec-007-rationale]: spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
[spec-011]: ../spec-011-stale_placeholder_cleanup-0_0_4.md
[spec-011-card-snapshot]: ../spec-011-stale_placeholder_cleanup-0_0_4.md#card-snapshot
[spec-011-scope]: ../spec-011-stale_placeholder_cleanup-0_0_4.md#scope

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-0]: ../../builder/worker-0.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
