# Rationale: spec-012 — 0.0.4 version and release alignment (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-012-version_release_alignment-0_0_4.md`][spec-012]. The spec is the
contract and states only what holds; everything that explains **how it got there** lives here: what
the release commit actually touched, why four of the five version surfaces were already aligned
before it ran, the alternatives each reconciliation choice rejected, and every claim the spec once
made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-012-0.0.4` shipped at `0.0.4` on
2026-05-08 (`231911a8`) and the rule that gates a build on this move did not exist then; this pass
supplies it. Text marked *Moved* below was cut out of the spec, not copied: it exists here and
nowhere else.

## How to read this file

- **One entry per spec section**, named by the section's own heading and linked to its anchor. A
  section with no entry here lost nothing.
- **This spec has no numbered Decisions**, and it was never deliberated: it is a rendered snapshot of
  a Kanban card, created at `81e4704d` (2026-06-01) by the archive-and-renumber pass, three weeks
  after the work shipped. So the key is the heading, and two entries key to headings the
  reconciliation removed while a third keys to a paragraph it removed; each says so and anchors the
  section its subject bears on.
- **The stub shape, and the boilerplate preamble, are argued once and not retold here.**
  [`spec-007-…-rationale.md`][spec-007-rationale] `### The preamble — the stub's own justification,
  and an instruction that cannot be followed` weighs expand-it / delete-it / keep-and-reconcile
  against constraints verifiable at HEAD, and names this spec by byte count (1,651 at `947f7494`)
  among the seven archived specs it measured as carrying the identical paragraph. That argument
  applies here unchanged and is cross-referenced rather than repeated; this file records only what is
  specific to spec-012. The same disposition was applied by
  [`spec-011-…-rationale.md`][spec-011-rationale], the immediately preceding residual cycle.
- **The substance is therefore the change record.** [`BUILD.md`][build] requires each entry to carry
  the alternatives rejected, every change the claim has undergone with the cause, and any claim the
  section may no longer make. For this spec the deliverable is two findings plus the history the stub
  does not contain. The first is structural: the stub states **a release-cut fact in the present
  tense**, so a reader at HEAD meets it as a standing invariant about a version the package left ten
  patches ago — and the stub's file list is a board *prediction*, not a record of what the card
  changed. The second is external to the spec's own text: **the release policy `0.0.4` was cut under
  was rewritten a week after the cut**, which changes what the aligned version number meant without
  changing any of the five surfaces or a single byte of the `0.0.4` entry.
- **Every fact below was measured at this working tree, not restated.** Each commit, count, and
  quotation carries the command or blob it came from. Where a figure in this cycle's build plan
  disagreed with the measurement, the measurement is recorded and the disagreement is named.
- **The move and the reconciliation are one pass**, so this file carries both records: the entries
  keyed to the spec first, then `## Reconciliation record — what the spec now says, and why`.

## Provenance of this record

- **Moved** — cut from the spec by this pass, and now only here: the whole preamble paragraph
  beginning "This file is intentionally lightweight", and the whole `## Planning note` section
  (heading plus its one-word body). Both are quoted below inside the entries that dispose of them.
- **Added in exchange:** the paragraph's slot now carries the one-line pointer sentence naming what
  moved and where, plus its `[spec-012-rationale]` link definition under `<!-- docs/SPECS/ -->`.
- **Deleted outright rather than moved**, per [`worker-1.md`][worker-1] rule 2, because the current
  contract falsifies them: the `## Card snapshot` board-metadata bullets (the label list is wrong at
  HEAD), the `## Other` heading and its seven bullets, and the tense of `## Scope` bullet 1. Each
  deletion is recorded below as a claim the spec may no longer make; none is restored anywhere as
  live text.
- **No fenced code block was involved.** The spec carried zero before this pass and carries zero
  after.
- **The single glossary anchor changed carrier and survives.** `#djangotype` was carried by
  `## Scope` bullet 1 as "[`DjangoType`][glossary-djangotype] release line"; the reconciled
  `## Scope` carries it on the `__init__.py` surface bullet, where the runtime version and the type
  surface are the same subject. The ref-id `glossary-djangotype` and its def are unchanged, so the
  one-row `spec-012-…-terms.csv` still matches and
  `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-012-version_release_alignment-0_0_4.md`
  exits 0 (`OK: 1 terms`) after the rewrite.

## What the card actually did — recovered, because the stub does not say

The card's own commit is **`231911a8`** ("Release 0.0.4;", 2026-05-08) and `git show --stat 231911a8`
reports exactly **two** files: `CHANGELOG.md` (31 changed lines) and `KANBAN.md` (147). It performed
one substantive edit, the changelog condensation, against `1d9ca597` ("Finished spec-foundation.md",
2026-05-07):

| Section | Before (`1d9ca597`) | After (`231911a8`) |
|---|---|---|
| release date | `## [0.0.4] - 2026-05-07` | `## [0.0.4] - 2026-05-08` |
| `[Unreleased]` | one `### Changed` bullet (docs consolidation) | emptied; the bullet folded into `0.0.4`'s `### Changed` |
| `### Added` | 6 bullets | 5, condensed (two API bullets merged; the fakeshop restructure added) |
| `### Changed` | 4 bullets | 6, condensed and widened (optimizer-internals and test-expansion rows added) |
| `### Fixed` | absent | 4 bullets, one of them the `GenericForeignKey` `ConfigurationError` row **reclassified out of `### Changed`** |
| `### Removed` | 1 bullet | unchanged |

**The four non-changelog surfaces were already on `0.0.4` before this card ran.** They moved a day
earlier in `118f71a1` ("Complete spec-foundation.md - Slices 7-12 (v0.0.4)", 2026-05-07), which
carries cards `DONE-010-0.0.4` and `DONE-011-0.0.4`. Measured directly: at `118f71a1~1`
`pyproject.toml` and `__init__.py` both read `0.0.3`; at `118f71a1` `pyproject.toml`,
`__init__.py`, `uv.lock`, and `tests/base/test_init.py` all read `0.0.4`.

This does **not** make the stub's alignment claim false — it states an end state at the release cut,
and that end state was verified surface by surface. It does make the stub's five-file list a board
prediction rather than a record of the card's diff, which is why the reconciled `## Scope` presents
the five as *the surfaces a release cut aligns* rather than as files this card edited.

### Nothing was skipped in the code

Re-derived at this working tree rather than accepted from the build plan.

- **At `231911a8`:** `pyproject.toml:4` `version = "0.0.4"`; `__init__.py:14`
  `__version__ = "0.0.4"`; `tests/base/test_init.py:7` `assert __version__ == "0.0.4"`; `uv.lock`
  root entry `version = "0.0.4"`; `CHANGELOG.md:10` `## [0.0.4] - 2026-05-08`.
- **At this working tree (`HEAD` = `5851bb59`):** the same five surfaces agree on `0.0.14`
  (`pyproject.toml:4`, `__init__.py:58`, `tests/base/test_init.py:21`, `uv.lock:544`,
  `CHANGELOG.md:19`). The invariant holds; only its value moved.
- **The `0.0.4` changelog entry survives byte-identical.** The `## [0.0.4]`-to-`## [0.0.3]` block
  extracted from `git show 231911a8:CHANGELOG.md` and from the working-tree file are both **2,621
  bytes** and `diff` clean. No later commit rewrote it — which is what licenses the spec to call it
  "the entry of record".
- **The condensation lost no substantive claim.** The one bullet that changed section — unsupported
  relation fields such as `GenericForeignKey` raising `ConfigurationError` — survives in `### Fixed`
  with its consumer guidance ("with guidance to exclude or override the field") intact, and the
  `[Unreleased]` bullet was folded in rather than dropped.

**No code defect was found, so this cycle dispatched no builder pass.** The one real gap is not this
card's: `AGENTS.md` rule 31 pairs `pyproject.toml` and `__init__.py` in prose, and
`tests/base/test_init.py::test_version` asserts a **literal** (`assert __version__ == "0.0.14"`)
without reading `pyproject.toml`. A bump editing one file and not the other is caught only if the
literal is edited too. Widening the spec to claim a mechanical check that does not exist was
**rejected outright** — it would be this cycle inventing scope for a shipped card, and a spec that
claims an enforcement the tree lacks is worse than one that is silent. The reconciled `## Scope`
instead states precisely what is true: rule 31 is prose, and `::test_version` pins the runtime
literal alone. The missing pin goes to the cycle's deferred-work catalog.

## Entries keyed to the spec

### The preamble — boilerplate whose instruction is counterfactual

Bears on [Card snapshot][spec-012-card-snapshot], the section the paragraph introduced.

*Moved verbatim, the whole paragraph.* "This file is intentionally lightweight. It preserves the card
scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable repository
file. Before implementation work starts from this file, expand it into the full builder-format spec
described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`."

*Claim the spec no longer makes.* That implementation work may start from this file, and that the
file should first be expanded into a full builder-format spec. The card's work shipped in the release
commit `231911a8` (2026-05-08); this file was created on 2026-06-01 at `81e4704d`, so there was never
any implementation work for it to precede — and the specific irony here is that the file's own
subject, the release, is the event that predates it.

*Why the first two sentences moved rather than stayed.* They explain why the file exists, which is
process justification and not a contract about anything — and the spec's `Status:` line already says
the same thing one level up, in the line whose job it is. The three-way choice behind the stub shape
is [`spec-007-…-rationale.md`][spec-007-rationale]'s, cross-referenced above and not re-argued.

### `## Planning note` — a retained field's discarded value

Bears on [Card snapshot][spec-012-card-snapshot]; the section this entry keys to no longer exists.

*Moved verbatim, the whole section.* The heading `## Planning note` and its entire body, the single
word "shipped".

*Why it was removed rather than restated.* It renders one Kanban column, and the value it rendered is
a **status**, which the spec's `Status:` line already carries in the line whose job that is —
"Status: shipped". A section whose body duplicates a header line one screen above it is not a
contract; it is a render artifact. The planning-state dimension's own retirement is recorded in
[`spec-007-…-rationale.md`][spec-007-rationale]'s entry for the same section and is not repeated
here.

*Claim the spec no longer makes.* That the card carries a planning note.

### `## Card snapshot` — the board fields are the database's, and they had drifted

Spec: [Card snapshot][spec-012-card-snapshot].

*Nothing moved; the board-metadata bullets were deleted.* The section claimed "Labels: `release`,
`versioning`". The card carries **three** at HEAD — `internal`, `release`, `versioning` — and the
divergence is eight days old at the snapshot's own age: the two-label set was current on 2026-06-01
(`bdfdc9cc`, the day this file was created), the board then rendered **no** `- Labels:` line for the
card at all from `91f9db12` (2026-06-04) through `c8f03087` (2026-06-09), and the dimension came back
rebuilt at `2baf93b5` (2026-06-09) with `internal` present. The same commit gave `internal` to card 7
(`docs`, `internal`, `release`) and card 11 (`cleanup`, `docs`, `internal`, `tests`); it touches eight
label lines carrying `internal` in total. Each figure was read from the blob at the commit named.

*The drift is the argument, not an incidental defect.* A hand-copied render of database rows in a
file that nothing re-renders is wrong the moment the board is edited, and nothing in the repository
can detect it: `KANBAN.md` regenerates from `examples/fakeshop/db.sqlite3`, the spec does not. So
patching the label list to read three labels lost — it buys correctness until the next board edit and
owes the same patch again. Deleting the section outright also lost: the card's identity is the one
board fact a spec is entitled to state, since this spec exists to be that card's `SpecDoc` target,
and entries in this file resolve to its anchor.

*Claims the spec no longer makes.* That card 12 carries exactly the two labels `release` and
`versioning`; that it is Low priority or relative size XS. All three remain true in the database
(save the label list, which was already false) and none is the spec's to assert.

### `## Scope` 1 — a release-cut fact written in the present tense

Spec: [Scope][spec-012-scope].

*Nothing moved; the bullet was rewritten.* The claim was "Package metadata for the
[`DjangoType`][glossary-djangotype] release line, runtime version, lockfile, tests, and changelog
**now** agree on `0.0.4`."

*This is the cycle's central reconciliation, and the fault is the tense, not the fact.* Every clause
is true of the `0.0.4` cut and was verified surface by surface above. But "now agree on `0.0.4`" is
written from inside the release, and a spec is read from outside it: at HEAD the five surfaces agree
on `0.0.14`, so the sentence presents as a standing invariant about the package that is false. This
is the failure mode a version-alignment card is uniquely exposed to — its subject is a value that is
*designed* to move, so the one thing it must not do is write that value as a present-tense property
of the files.

*The alternatives the rewrite rejected.*

- **Change "now" to "at the `0.0.4` release cut".** The smallest possible edit, and it lost twice
  over: it leaves the reader with a bare historical assertion and no statement of what is true of
  these five files in general, and the surrounding sentence still reads as though the five-file set
  were this card's edit list rather than the release mechanism's.
- **Delete the bullet and let the changelog speak.** Rejected: the alignment across five *distinct*
  surfaces is the card's entire contract, and a reader confirming a version-alignment card needs the
  set enumerated. The changelog is one of the five, not a summary of them.
- **Add a standing rule that all five must always agree, and cite `::test_version` as its
  enforcement.** Rejected as an over-claim; see the enforcement gap recorded above.

*What replaced it.* The set is now enumerated one surface per bullet, each named by symbol path or
by the exact key it carries, with `0.0.4` stated as what **the `0.0.4` cut** carries — followed by an
explicit sentence that alignment is a per-release obligation rather than a standing property of the
five files. That sentence is the direct remedy: it makes the moving value legible as moving, so no
later reader has to apply a chronology to work out whether the spec is still true.

*Claim the spec no longer makes.* That these five surfaces presently read `0.0.4`.

### `## Scope` 2 — the condensation, restated as the entry's shape

Spec: [Scope][spec-012-scope].

*Nothing moved; the bullet was rewritten.* The claim was "The changelog entry is condensed for the
alpha release and covers the actual commit range through 2026-05-08."

*Why it was rewritten rather than kept.* It was true and uncheckable in the same way spec-011's
cleanup bullet was: "condensed" names an act performed against a draft the reader cannot see, so
nothing in the sentence can be confirmed against the tree. The reconciled text states the entry's
resulting **shape** — five `### Added`, six `### Changed`, four `### Fixed`, one `### Removed`
(counted from the block at this working tree) — and the date, which is the checkable half of "commit
range". The act, its before-and-after table, and the reclassification it performed live in
`## What the card actually did` above.

*Added rather than rewritten: "no later commit rewrites it."* This is the byte-identity finding
promoted into the contract, and it is worth a sentence because it is the only claim in this spec that
a future commit could falsify without anyone editing the spec — which makes it the card's live
guarantee rather than a historical note.

*Claim the spec no longer makes.* None. The bullet was true; it was rewritten to be checkable.

### `## Scope` — the release policy `0.0.4` was cut under was rewritten a week later

Spec: [Scope][spec-012-scope].

*Nothing moved and nothing was rewritten; this entry records a change to the frame around the spec's
subject rather than to any of its five surfaces.* It is the "later work changed the shipped shape"
case for a spec whose whole subject is release alignment, and the change is one no reader of the
`0.0.4` entry can see from the entry.

*What the policy said at the cut.* At `231911a8` (2026-05-08) the header of
[`CHANGELOG.md`][changelog] read, in two lines: "The format is based on [Keep a Changelog]…, and this
project adheres to [Semantic Versioning]…". A release cut under that header is a release cut under
strict SemVer, and `0.0.4` is the version string the card aligned five surfaces on.

*What changed it.* `27ed0b30` ("update plan;", 2026-05-15) — **seven days later**, a single-file
change of 14 insertions and 3 deletions against `CHANGELOG.md`. It **deleted the SemVer clause** from
the header, leaving "The format is based on [Keep a Changelog]…", and added a `## Versioning` section
carrying a five-row milestone cadence whose `0.0.x` row states that strict Semantic Versioning "does
**not** apply here". The change is retroactive in effect: it covers the whole `0.0.x` line, `0.0.4`
included, without touching `0.0.4`'s entry.

*What the section says now, measured at this working tree rather than at `27ed0b30`.* The alpha row's
substantive claim is unchanged — strict SemVer does not apply during `0.0.x` — while the presentation
around it has moved three times. The row label reads **`Alpha (0.0.x)`** where `27ed0b30` wrote
`Pre-alpha (0.0.x)` (changed at `2bd7cb84`, 2026-05-16); the final row reads `Stable (1.x.y)` where it
wrote `Post-stable (1.x.y)`; the two milestone rows now cite board cards 052 and 067 through
reference-style links where they cited the literal ids `BETA-033-0.1.0` and `STABLE-042-1.0.0`; and
`## [Unreleased]` no longer exists in the file at all, removed at `24d11143` (2026-06-16). So the
policy frame is not merely different from the one `0.0.4` was cut under — it has itself been revised
since, which is the argument for recording the frame here rather than quoting any one version of it
into the spec.

*Why this does not disturb the spec's live guarantee, and why that is the point.* Every one of these
edits sits **above** the release entries, so the `## [0.0.4]`-to-`## [0.0.3]` block is untouched by
all of them: re-measured at this pass, the block extracted from `git show 231911a8:CHANGELOG.md` and
from the working tree are both **2,621 bytes** and `diff` clean. The spec's "no later commit rewrites
it" therefore holds — and is *blind* to this change, because byte-identity of an entry says nothing
about the policy the entry was written under. That blindness is exactly why the fact needs a written
home.

*The alternatives rejected.*

- **State the change in the spec's `## Scope`** ("`0.0.4` was cut under a SemVer header later
  replaced by a milestone cadence"). Rejected: that is chronology, and [`BUILD.md`][build]
  `## Spec rationale extraction` is explicit that a spec states the current contract and never
  narrates how it got there. The spec would also be the only per-release document in the repository
  carrying release-policy history.
- **Add a standing "this is not a SemVer release" sentence to the spec.** Rejected: the versioning
  policy belongs to [`CHANGELOG.md`][changelog] and is stated there, in one place, for every release.
  A per-release spec restating a repository-wide policy is the same duplication the `## Card snapshot`
  board-metadata bullets were deleted for, and it would drift the same way — as the three revisions
  measured above show it already would have.
- **Treat it as out of scope, since none of the five surfaces moved.** Rejected: a reader of a
  release-*alignment* spec is precisely the reader who asks what the aligned version number meant, and
  the answer to that question changed a week after the cut. Silence here would leave them to infer it
  from a header that no longer exists.
- **Annotate `CHANGELOG.md`'s `0.0.4` entry with the policy that applied.** Rejected twice over:
  `AGENTS.md` rule 21 closes `CHANGELOG.md` to an unrequested edit, and any such edit would break the
  byte-identity the spec now guarantees.

*Claim the spec may not make.* That `0.0.4` was, or is, a Semantic Versioning release. It was cut
under a header asserting SemVer adherence and now sits inside a policy that excludes the entire
`0.0.x` line from it, and its own entry records neither. The spec's contract — five surfaces carrying
one version string at the cut — is unaffected either way, which is why this is recorded here and no
sentence of the spec changed.

### `## Other` — seven rows of three kinds under a heading that names none of them

Bears on [Scope][spec-012-scope]; the heading this entry keys to no longer exists.

*Nothing moved; the heading and its seven bullets were deleted.* The section rendered two `#### Note`
rows ("release housekeeping (version alignment)." and "align package metadata / runtime version /
lockfile / tests / changelog on `0.0.4`.") and the five `#### Files likely touched` paths, flattened
into one undifferentiated list under a heading that names neither kind. **This cycle's build plan
calls it six bullets; the measured figure is seven** — the plan's own enumeration ("two `#### Note`
bullets and the five `#### Files likely touched` paths") sums to seven, so the discrepancy is
arithmetic in the plan rather than a change in the file, and the plan's number is the one to
distrust.

*Disposition, bullet by bullet, rather than a bulk drop.*

- "release housekeeping (version alignment)." — no successor. It is a board-level triage note about
  the card's value, and a spec that tells a reader its own subject is housekeeping says nothing the
  `## Scope` section does not.
- "align package metadata / runtime version / lockfile / tests / changelog on `0.0.4`." — a
  restatement of `## Scope` bullet 1 in the imperative. Duplicate; dropped with it.
- The five paths — carried forward, but **re-framed**. This is the F7 correction: as rendered they
  read as a record of what the card changed, and the card's diff touched two files, neither of them
  in this list. In the reconciled `## Scope` the same five appear as the surfaces the version string
  lives on, which is the claim that is both true and checkable.

*Claim the spec no longer makes.* That `Other` is a section of card 12, or that the card's diff
touched those five files.

### The `[backlog]` link definition — recorded, not fixed

Spec: the link-definitions block, `<!-- Root -->` group.

`[backlog]: ../../BACKLOG.md` is defined and never used: `grep -c 'backlog'` over the spec returns 1,
the definition itself. It is **deliberately left in place**, exactly as the spec-011 cycle left its
own. The board already owns the pattern: `KANBAN.md` catalogues 71 unused link definitions across 23
files, "including an unused `[backlog]` definition in eight archived specs (`spec-011`, `spec-012`,
`spec-013`, `spec-016`, `spec-024`, `spec-026`, `spec-036`, `spec-054`)", to be retired in one sweep
by the checker card. Fixing one file of a cross-surface pattern leaves the surface *divergently*
wrong rather than uniformly wrong, which is the disposition [`worker-0.md`][worker-0] `## Closing out
a kanban card` prescribes, so it goes to this cycle's deferred-work catalog instead.

## Reconciliation record — what the spec now says, and why

The spec went from 1,651 bytes / 60 lines to 2,814 bytes / 57 lines: it grew in prose and shrank in
structure, because four sections became two and every surviving sentence had to state a contract
rather than render a row. The before-figure is the committed file at `5851bb59` (identical to the
1,651 the spec-007 rationale measured at `947f7494`, so nothing touched this spec in between); the
after-figure is this pass's working tree on top of it. Both were read with `wc -c -l`.

### The strategy, and what it rejected

The strategy: a version-alignment card's contract **is** the set of surfaces the version string lives
on plus the mechanism that keeps them equal, so the spec must enumerate that set, state what the cut
put on it, and make explicit that the value moves. Two alternatives lost.

- **Leave `## Scope` as two summary bullets and put the surface list only here.** Rejected: it keeps
  the spec uncheckable against the tree, which is the defect this pass exists to close. A reader
  confirming an alignment card needs the surfaces in the contract, not in the deliberation file —
  the rationale answers *why*, and the spec must answer *what*.
- **Rewrite the spec into a full builder-format spec** with slices, a test plan, and a definition of
  done. Rejected for the reason [`spec-007-…-rationale.md`][spec-007-rationale] gives: the work
  shipped three weeks before the file existed, so any such expansion is a reconstruction presented in
  the shape readers trust as a pre-implementation contract. A stub cannot mislead about a
  deliberation it does not claim to have had.

### `## Scope` — one present-tense sentence became an enumerated set plus a stated obligation

Spec: [Scope][spec-012-scope]. The section now names all five surfaces, each by the file plus the key
it carries — `AGENTS.md` rule 27's `path #"unique substring"` form for the two source files, since
neither version assignment sits inside a symbol, and no `path:NN` line numbers, which rot on the next
edit of a file this spec does not own. It closes with the per-release-obligation sentence and the
enforcement statement, which together carry F6's remedy and V5's honest limit in the same breath.

*Why the enforcement limit is stated at all.* A reader who sees `::test_version` in the surface list
will assume it is the mechanism that holds the pairing. Saying that it pins the runtime literal alone
is the difference between a contract and an invitation to trust something that is not there — and it
is the sentence a future card closing that gap will delete.

### The link scaffold

The block keeps all ten canonical group headers in order. It gained `[spec-012-rationale]` under
`<!-- docs/SPECS/ -->`, `[changelog]` / `[pyproject]` / `[uv-lock]` under `<!-- Root -->`, `[init]`
under `<!-- django_strawberry_framework/ -->`, and `[test-init]` under `<!-- tests/ -->`; it keeps
the unused `[backlog]` for the reason the entry above gives. Every path was disk-checked from
`docs/SPECS/`, and the archived-depth trap was re-checked in both directions: `../../tests/…` and
`../../django_strawberry_framework/…` reach the real trees and `../GLOSSARY.md` reaches
[`docs/GLOSSARY.md`][glossary], with no same-named file one level up to mask a bad depth. This
file's own defs sit one level deeper again (`../../../`, `../../`), disk-checked the same way.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../../BACKLOG.md
[changelog]: ../../../CHANGELOG.md
[kanban]: ../../../KANBAN.md

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md
[glossary-djangotype]: ../../GLOSSARY.md#djangotype

<!-- docs/SPECS/ -->
[spec-007-rationale]: spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
[spec-011-rationale]: spec-011-stale_placeholder_cleanup-0_0_4-rationale.md
[spec-012]: ../spec-012-version_release_alignment-0_0_4.md
[spec-012-card-snapshot]: ../spec-012-version_release_alignment-0_0_4.md#card-snapshot
[spec-012-scope]: ../spec-012-version_release_alignment-0_0_4.md#scope

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
