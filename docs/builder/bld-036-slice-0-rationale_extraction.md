# Build: Slice 0 — spec rationale extraction (pre-flight step 7)

Spec reference: `docs/SPECS/spec-036-mutations-0_0_11.md` (whole file; the move touched lines 11-17,
252-260, 272-277, 283-288, 295-300, 315-325, 340-346, 358-366, 384-390, 402-407, 415-420, 426-431,
437-442, 448-452, 458-463, 480-486, 500, 554-562 and the link-definition block, in HEAD numbering)
Status: final-accepted

This is a **procedural-closure pass** (`docs/builder/BUILD.md` `### Procedural-closure slices`): no
Worker 2 build, no Worker 3 review. The Plan and Final-verification blocks are combined below, and
Worker 1 sets `final-accepted` directly. The authorizing clause is
`docs/builder/BUILD.md` `## Spec rationale extraction` — "**The first substantive action of every
build.** Before the build plan is written, Worker 1 MOVES the spec's *deliberative layer* into a
companion file" — read with `## Pre-flight checks`: "No slice is dispatched until step 7, Worker 1's
spec-rationale extraction, is done and verified, because every spawn after it reads the smaller
spec." The plan this pass gates, `docs/builder/build-036-mutations-0_0_11.md`, does not exist yet and
is Worker 0's file.

---

## Plan + Final verification (Worker 1)

### Files touched

Three files, all owned by this pass:

- `docs/SPECS/spec-036-mutations-0_0_11.md` — the deliberative layer cut out; 15 per-Decision
  pointers, one deliberative-layer pointer, one Risks pointer and 17 link definitions added; one
  chronology parenthetical deleted; one pre-existing broken in-page anchor repaired at 12 sites; one
  link definition orphaned by the move removed.
- `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md` — **created**. Lands directly in
  `docs/SPECS/appx/` beside the existing `spec-036-mutations-0_0_11-terms.csv`, matching every other
  archived spec, because `spec-036` is already archived.
- `docs/builder/bld-036-slice-0-rationale_extraction.md` — this artifact.

Plus `docs/builder/worker-memory/worker-1-036.md` (untracked worker memory).

Nothing else in the tree was edited. `git status --short -- docs/SPECS/` reports exactly
`M docs/SPECS/spec-036-mutations-0_0_11.md` and `?? docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md`.

### Pre-edit baseline check

`docs/SPECS/spec-036-mutations-0_0_11.md` was verified **clean at HEAD before the first edit**, read-only
per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` (no `git stash`,
no `git checkout`, no `git restore`, no `git worktree`):

```shell
$ git show HEAD:docs/SPECS/spec-036-mutations-0_0_11.md > <scratch>/spec-036-HEAD.md
$ diff -q <scratch>/spec-036-HEAD.md docs/SPECS/spec-036-mutations-0_0_11.md && echo "IDENTICAL TO HEAD"
IDENTICAL TO HEAD
$ git diff HEAD --stat -- docs/SPECS/spec-036-mutations-0_0_11.md   # no output, exit 0
$ wc -c -l docs/SPECS/spec-036-mutations-0_0_11.md
     709  164498 docs/SPECS/spec-036-mutations-0_0_11.md
```

Gate baselines taken before the first edit, so a post-move green is a comparison and not an assertion:

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-036-mutations-0_0_11.md
OK: 38 terms - all have glossary entries and at least one spec link.      # exit 0
$ uv run python scripts/check_citations.py
OK: 929 citations resolve (772 in 435 .py files, 157 in KANBAN.md).       # exit 0
$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-036-mutations-0_0_11.md
                                                                          # exit 0
```

Baseline-dirty, out-of-scope files were neither edited nor reverted (`AGENTS.md` rule 34). The tree
carries a concurrent session's work across the whole mutations subsystem — every
`django_strawberry_framework/mutations/*.py`, many `django_strawberry_framework/utils/*.py`,
`django_strawberry_framework/types/finalizer.py`, most `tests/mutations/*.py`, `docs/GLOSSARY.md`
(+18 lines), `docs/TREE.md`, `README.md`, `docs/README.md`, `KANBAN.md`, `KANBAN.html`,
`examples/fakeshop/db.sqlite3` — plus `docs/builder/bld-003-final.md` from a different committed
cycle. That churn is recorded here so a later pass does not read it as this move's output. It is also
load-bearing for the audit cohorts: see
[### Notes for Worker 1 (spec reconciliation)](#notes-for-worker-1-spec-reconciliation) item 5.

### What the move did, by route

Four routes carried text out of the spec, plus two mechanical repairs the move exposed. Every figure
below was measured as it was written.

**Route 1 — the whole `Revision history (kept inline so the spec is self-contained):` block**
(HEAD lines 11-17): preamble + blank line + five `Revision N` entries, **7 lines, 14,609 bytes**. The
five entries moved byte-for-byte to `## Revision history` in the companion, **14,546 bytes** of them.
The **62-byte preamble line was deleted, not moved** — its claim that the history is kept inline is
exactly what this move made untrue — and so was the 1-byte blank line under it. Replaced in the spec by
one 370-byte deliberative-layer pointer paragraph, in the `034` / `035` wording.

**Route 2 — 15 `Justification:` blocks and 15 `Alternatives considered (and rejected):` blocks**, one
pair under each of Decisions 1-15, carrying **19** justification bullets or paragraphs and **33**
rejected alternatives, **17,539 bytes** (7,691 justification + 9,848 alternatives; the justification
figure includes the blank line that separated each pair). Reproduced byte-for-byte under each
Decision's heading in the companion. The 30 labels became `###` headings there: **18 stood on their
own line** (3 `Justification:` — Decisions 1, 5, 7 — and all 15 `Alternatives considered (and
rejected):`) and **12 were inline prefixes** stripped from the paragraph they introduced (Decisions
2-4, 6, 8-15). Each block pair was replaced in the spec by a single one-line pointer reading
`Rationale companion — this Decision's justification and its N rejected alternatives:` followed by a
reference-style link to that Decision's heading in the companion — 15 lines, 1,774 bytes. The
ordinal is spelled out and singularised where a Decision rejected exactly one alternative (Decision
13), matching the `034` / `035` wording.

**Route 3 — the body of `## Risks and open questions`** (HEAD lines 554-562): preamble plus **7**
items, each a preferred-answer / fallback pair, **5,332 bytes**. That shape is a build-time
deliberation instrument, not a contract, so — exactly as the `034` move did — the **body moved and the
spec keeps the heading plus a pointer** (413 bytes) at
`## Risks and open questions` in the companion. Three of the seven items are questions a Decision later
answered outright (`Meta.operation` selector, payload exposure surface, write authorization) and two
are card-citation corrections the cut recorded rather than silently reconciled; every conclusion
already lives in a Decision, so nothing was held back from this route.

**Route 4 — chronology framing embedded in surviving contract prose: 1 site, 98 bytes.** The
`## Implementation plan` expected-delta line read "an XL cut, matching the card's relative size (the
write-auth seam, shape-derived naming, and transaction boundary added since the first draft)". The
parenthetical dated the total against a draft the spec no longer carries; it was **deleted** and
recorded under the companion's `## Non-Decision deliberation`, because a planning-total line belongs
to no Decision.

**Repair A — a pre-existing broken in-page anchor, 16 uses.** Decision 8's heading reads "… optimizer
re-fetch …", which slugs to `…optimizer-re-fetch…`; every in-page reference to it spelled
`…optimizer-refetch…` and therefore resolved to nothing. Measurable at HEAD:

```shell
$ git show HEAD:docs/SPECS/spec-036-mutations-0_0_11.md | grep -o 'optimizer-refetch' | wc -l
      16
```

4 of the 16 sat inside the revision entries this move carried out. All 16 were repaired — 12 in the
spec (+12 bytes), 4 in the companion — rather than carried forward dangling, since this pass owes
"0 unresolved in-page anchors" on both files and an anchor left broken in a file created by this pass
would be this pass's defect. The repair is recorded as the second respect in which the move is not
byte-verbatim.

**Repair B — one link definition orphaned by the move.** `[utils-inputs]` had exactly one use, in
Decision 4's rejected alternatives, which moved; the def (66 bytes) was removed from the spec and
added to the companion. `[backlog]` was **already** orphaned at HEAD and was left alone — it is not
this move's to fix (see notes below).

### Byte accounting

| | bytes | lines |
|---|---|---|
| spec at HEAD | 164,498 | 709 |
| spec after the move | 131,777 | 623 |
| **net spec delta** | **-32,721** | **-86** |
| companion (new file) | 74,895 | 428 |

Carried out / deleted from the spec:

| route | bytes |
|---|---|
| Route 1 revision block (14,546 moved + 62 preamble deleted + 1 blank deleted) | 14,609 |
| Route 2 fifteen `Justification` + `Alternatives` pairs | 17,539 |
| Route 3 `## Risks and open questions` body | 5,332 |
| Route 4 chronology parenthetical (deleted) | 98 |
| Repair B orphaned `[utils-inputs]` def (deleted) | 66 |
| **total removed** | **37,644** |

Framing added back to the spec:

| addition | bytes |
|---|---|
| deliberative-layer pointer paragraph | 370 |
| 15 per-Decision `Rationale companion —` pointer lines | 1,774 |
| `## Risks and open questions` pointer paragraph | 413 |
| 17 link definitions (`rationale-d1`-`d15`, `rationale-risks`, `spec-036-rationale`) | 2,354 |
| Repair A: 12 one-byte anchor repairs | 12 |
| **total added** | **4,923** |

**The arithmetic closes: -37,644 + 4,923 = -32,721**, which is the measured net spec delta to the
byte. The companion is 74,895 bytes; it is larger than the 37,417 bytes of spec text that reached it
(14,546 + 17,539 + 5,332) because it also carries this pass's own framing — the header, `## Provenance
of this record`, the 15 `Spec:` back-pointer lines, the 15 `### Changes this Decision underwent`
sections, the `## Risks and open questions` and `## Non-Decision deliberation` framing, and its
50-definition link block — all of which the file says are this pass's own.

### Establishing the population: three grep grammars

Per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` — a long grep
phrase samples a claim's vocabulary rather than establishing its population, so the shortest
distinctive token was searched and **occurrences** were counted, not matching lines.

```shell
$ grep -on 'Revision [0-9]' <HEAD copy> | wc -l          #  6 occurrences, 5 lines
$ grep -oin 'evision'       <HEAD copy> | wc -l          #  7 occurrences, 6 lines
```

The first grammar is blind to the block's own preamble (`Revision history`, no digit); `evision`
catches it, and the one-occurrence gap is exactly that line. Both land **entirely inside lines
11-17**, which is the load-bearing finding: unlike the `034` spec (4 surviving `— see Revision N`
sites) and the `035` spec (11), `spec-036` carried **no** `Revision N` cross-reference anywhere
outside the block, so the block lifted whole without repointing a single surviving sentence.

A third grammar swept chronology vocabulary carrying no `revision` at all — `superseded`,
`earlier draft`, `prior draft`, `first draft`, `later changed`, `amendment`, `post-ship`,
`review round`, `as of`, `formerly`, `no longer`, `has since`, `retract`, `pre-build`, `post-build`,
`feedback`, `previously`, `used to`, `replaced by`, `reconciled` — and found **18** occurrences: 14
inside text this move carried out, 2 inside the Route-4 parenthetical it deleted, and **2 false
positives** (`feedback` twice in Decision 8's relation-decode paragraph, on the contract phrase
"field-level decode feedback"). That left exactly one genuine site, Route 4.

A fourth grammar measured the review-finding tags, the population this move deliberately held back:

```shell
$ grep -oE 'AR-[HM][0-9]+|Major-[0-9]+|Medium-[0-9]+|CR-[0-9]+|DRY-[0-9]+|Low-[0-9]+|\bP[12]\b' \
    <HEAD copy> | wc -l                                   # 184 occurrences
$ ... | sort | uniq -c | sort -rn | wc -l                 #  34 distinct tags
```

### Held-back passages, each with its reason

The implementation-relevant carve-out (`docs/builder/worker-1.md` `### Performing the rationale
move`) holds back the "why" that changes how a thing is built, and the rule that an unclear sentence
**stays**. Four passages and one whole population were held back; each is enumerated in the
companion's `## Provenance of this record` as well, so a reader of either file sees the same list.

1. **The 184 review-finding tags across 34 grammars.** Held back for three reasons. (a) A tag is a
   **lookup key**, not a chronology: the sentence reads as the current contract with or without it,
   and the tag is how a reader crosses from a clause to the companion entry recording why the clause
   has that shape — the keyed-to-the-spec property `docs/builder/BUILD.md` `## Spec rationale
   extraction` requires. (b) Both precedent executions of this move left the same shape standing: the
   `035` spec still carries a `Major-2` and neither companion records a tag population as moved, so
   stripping 184 here would break corpus consistency rather than restore it. (c) Stripping 184
   parentheticals in 34 grammars rewrites contract prose; it is not a cut-and-paste, and under the
   unclear-sentence-stays rule they stay. Recorded as an **open maintainer call** in the companion's
   `## Non-Decision deliberation`, not silently accepted.
2. **Decision 6's rejection of the blanket "every editable field required" rule.** It sits inside the
   Decision's own `<Model>Input` bullet rather than in the `Alternatives considered` block, and it is
   the reason the per-field `default` / `blank` / `null` test exists: the blanket rule would force
   `description` / `isPrivate` required on products **and** on `GOAL.md`'s north-star `Galaxy` /
   `CelestialBody` models, which share the identical `blank=True, default=""` / `default=False` shape.
   A builder who never reads it writes the blanket rule.
3. **Decision 6's M2M-always-optional derivation.** "A forward `ManyToManyField` reports
   `null=False, blank=False, has_default()=False`, so the literal rule would mark it required" reads
   as deliberation and is in fact why the generator must special-case M2M against its own
   required-ness rule.
4. **Decision 9's whole re-fetch-visibility paragraph.** The by-pk-without-the-visibility-filter rule
   is normative, and so is its derivation: a caller holding `add_item` can create an
   `is_private=True` row the visibility hook hides, so routing the re-fetch through `get_queryset`
   would null the payload of a successful, authorized write. It is a documented exception to a
   `GOAL.md` success criterion; a reader who cannot see why would "fix" it back.
5. **Decision 8's relation-decode-after-Authorize paragraph.** It reads as a note on an implementation
   choice and is a security guarantee: an unauthorized caller triggers no relation visibility query
   and receives no field-level decode feedback. Its error-precedence consequence is observable
   contract.

One passage was moved **despite carrying a stale numeral**, rather than deleted or silently repaired:
Decision 5's justification bullet "One `operation` key over three base classes … keeps the public
symbol count at three", which Revision 3 falsified when `DjangoModelPermission` made it four (the
Decision's own body says "Four net-new public symbols"). The **argument** — one selector key against
three per-operation base classes — is intact and only the count is wrong, so
`docs/builder/worker-1.md` rule 2 ("delete, do not move, prose the current decisions have
falsified") does not reach it. It moved as written, with the discrepancy recorded under the
companion's Decision 5 `### Changes this Decision underwent`.

### Not byte-verbatim, in two respects

1. **5 uses across 4 anchors re-pointed.** Moved text carrying `#borrowing-posture` (2 uses),
   `#edge-cases-and-constraints` (1), `#out-of-scope-explicitly-tracked-elsewhere` (1) and
   `#test-plan` (1) names spec sections the companion does not have; each is re-pointed at the spec
   through a reference-style link (`[spec-036-borrowing-posture]`, `[spec-036-edge-cases]`,
   `[spec-036-out-of-scope]`, `[spec-036-test-plan]`) rather than left to dangle. The
   `#decision-N--…` anchors were **left as they were**: the companion carries headings with exactly
   those slugs, so they resolve locally, which is where a reader of a moved sentence wants to land.
   `#risks-and-open-questions` likewise resolves locally.
2. **Repair A's 4 in-companion anchor repairs**, described above.

Verified mechanically: all 65 moved lines are present in the companion byte-identically once those
two transformations are applied forward, and none survives in the spec.

```
moved lines still present in the spec: 0        (of 65)
verbatim check: missing lines = 0
'Revision history (kept inline' in spec: False
'Justification' occurrences in spec: 0
'Alternatives considered' occurrences in spec: 0
'Rationale companion —' pointer lines in spec: 15
'added since the first draft' in spec: False
```

### `### Changes this Decision underwent` is ready for `**Post-ship:**` bullets

Every one of the 15 Decisions carries the section, seeded from the five revision entries with the
finding tag that caused each change (`Major-` / `Medium-` for Revision 2, `AR-H` / `AR-M` / `Low-1`
for Revision 3, `CR-` for Revision 4, `DRY-` for Revision 5, plus the `P1` / `P2` back-reference
Revision 4 records). Four Decisions (1, 3, 12, 13) carry a single "Revision 1 pinned it; nothing later
reopened it" bullet, which is a decided answer where silence is not. The companion's header carries
the **"How later passes append to this file"** paragraph naming `**Post-ship:**` as the append form
and `## Non-Decision deliberation` as the home for findings belonging to no Decision, so the R2 spec
reconciliation pass needs no restructuring to add its results.

### Spec changes made (Worker 1 only)

Every edit is one of the four routes or two repairs above; no contract sentence was rewritten,
retimed, or reinterpreted. Specifically:

- HEAD lines 11-17 -> one deliberative-layer pointer paragraph (Route 1).
- HEAD lines 252-260, 272-277, 283-288, 295-300, 315-325, 340-346, 358-366, 384-390, 402-407,
  415-420, 426-431, 437-442, 448-452, 458-463, 480-486 -> 15 `Rationale companion —` pointer lines
  (Route 2).
- HEAD line 500: the "added since the first draft" parenthetical deleted (Route 4).
- HEAD lines 554-562 -> one `## Risks and open questions` pointer paragraph; the heading stays
  (Route 3).
- 12 in-page anchor repairs at Decision 8's slug (Repair A).
- Link-definition block: `[utils-inputs]` removed (Repair B); `[rationale-d1]`…`[rationale-d15]`,
  `[rationale-risks]` and `[spec-036-rationale]` added under the `<!-- docs/SPECS/ -->` group, which
  is where an `appx/` target belongs — `START.md`'s ten group headers are a closed list, so a
  subdirectory shares its parent's group.

**Spec status-line re-verification** (`docs/builder/worker-1.md` `## Spec status-line
re-verification`): lines 1-9 (title, opener, `Status: **SHIPPED (`0.0.11`)**`, `Owner:`,
`Predecessors:`) were read and still describe the build's state — the card is `DONE-036-0.0.11`,
released under the `CHANGELOG.md` `## [0.0.11]` heading, all five slices final-accepted, and the
Slice-checklist-stays-unticked convention is stated explicitly. No status-line edit was needed. The
one line the move replaced in that block is the revision-history preamble, which is not a status line.

### Verification run

| check | command | result |
|---|---|---|
| glossary anchors | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-036-mutations-0_0_11.md` | `OK: 38 terms - all have glossary entries and at least one spec link.` exit 0 — same 38 as at pre-flight |
| rule-27 citations | `uv run python scripts/check_citations.py` | `OK: 929 citations resolve (772 in 435 .py files, 157 in KANBAN.md).` exit 0, unchanged from baseline |
| `.md` link-def scaffold | `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-036-mutations-0_0_11.md docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md` | exit 0 (both files; all 10 canonical group headers present, in `START.md`'s order) |
| whitespace / conflict markers | `git diff --check -- docs/SPECS/spec-036-mutations-0_0_11.md` | exit 0, no output |

The two new files were checked the same way (they are untracked, so `git diff --check` cannot see
them): 0 trailing-whitespace lines and no conflict markers in either. A **tree-wide** `git diff
--check` exits 2, on four trailing-whitespace lines in `docs/feedback2.md` — a baseline-dirty
out-of-scope file this pass neither edited nor reverted. Recorded as a baseline exception rather than
fixed, per `AGENTS.md` rule 34; it is unrelated to this move.

`check_citations.py --help` was read before invoking it: the whole corpus is swept on every run
(`pass_filenames: false`), `docs/` is deliberately out of scope, and the bare invocation above is the
documented usage — so the 929/929 result is the gate's verdict on the tree, not on these two files
alone. No `pytest` was run: this pass changed no `.py` file, and coverage flags are forbidden in every
worker pass. No `.py` file was edited, so `ruff format` / `ruff check --fix` were correctly not run.

Reference-vs-definition parity and anchor resolution, both files, measured with inline-code spans
stripped so a `[0-9]` inside a backticked grep pattern is not mistaken for a link:

| | spec | companion |
|---|---|---|
| headings | 37 | 23 |
| reference-style refs used | 97 | 50 |
| link definitions | 98 | 50 |
| unresolved in-page anchors | **0** | **0** |
| used-but-undefined refs | none | none |
| defined-but-unused refs | `backlog` (pre-existing at HEAD) | none |
| def paths missing on disk | **0** | **0** |
| cross-file `#anchor` targets unresolved | **0** | **0** |

Every rewritten link path was disk-exists-checked, and every `…md#anchor` definition was resolved
against the target file's actual headings — including all 15 `[rationale-dN]` defs in the spec against
the companion's `## Decision N` slugs, and all 15 `[spec-036-dN]` defs in the companion against the
spec's `### Decision N` slugs. The spec's single `defined-but-unused` ref, `[backlog]`, is orphaned at
HEAD as well (verified against the HEAD copy) and was left in place: nothing in this move caused it,
and deleting a definition with no cause is not this pass's business.

### Notes for Worker 1 (spec reconciliation)

Suspected divergences noticed while reading. **None was fixed here** — this move did not check the
spec against `HEAD`, and the companion's `## Provenance of this record` says so. The audit cohorts own
grading them.

1. **`## Current state` needs clause-by-clause grading, and several clauses are false at `HEAD`.** Its
   opener ("A true description of the repo as this spec is authored") dates every bullet, and
   `docs/builder/BUILD.md` `### `## Current state`: observations stand, predictions do not` licenses a
   dated observation to keep describing the pre-build repo. But at least three bullets read as
   present-tense claims a reader will take as current: "**No `mutations/` module, no write resolvers,
   no input generation** … neither exists on disk"; "**The products write target is connections-only
   today** … there is **no** `Mutation` type"; "**The sibling `0.0.11` card is unshipped**"
   (`DONE-037-0.0.11` has since shipped). Grade each clause as observation or prediction; a
   falsified prediction gets rewritten.
2. **The terms CSV's stated reason is falsified at `HEAD`.** The moved Risks item argues the companion
   `*-terms.csv` "does **not** list `DjangoMutationField` (it has no heading yet and would fail the
   checker)". `git show HEAD:docs/GLOSSARY.md` carries `## \`DjangoMutationField\`` (line 708) and
   `## \`DjangoModelPermission\`` (line 688), so the premise no longer holds, while
   `docs/SPECS/appx/spec-036-mutations-0_0_11-terms.csv` (39 rows) still omits both symbols — the only
   mention of `DjangoMutationField` in it is inside the `DjangoConnectionField` row's description. The
   CSV is out of this cycle's maintainer-set scope, so this is a maintainer call, not a cohort fix.
   Recorded in the companion's `## Risks and open questions` framing as well.
3. **Decision 5's public-symbol count.** Recorded above and in the companion under Decision 5: the
   moved justification says "three", the surviving Decision body says "Four net-new public symbols".
   Only the moved copy is wrong, so the spec is internally consistent after the move — but if a
   reconciliation pass touches Decision 5, this is the sentence it should not resurrect.
4. **The same broken-anchor defect exists in two sibling specs, uncorrected.**
   `docs/SPECS/spec-038-form_mutations-0_0_12.md` (**36** uses) and
   `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` (**34** uses) both carry a Decision 8 heading
   ending "… optimizer re-fetch → payload" and spell every in-page reference to it
   `…optimizer-refetch…`, so all 70 resolve to nothing, exactly as `spec-036`'s 16 did. Out of scope
   for this pass (this cycle owns `spec-036`); route it to whoever owns those specs. No file cites
   `spec-036`'s Decision 8 anchor cross-file, so Repair A needed no sweep beyond this spec.
5. **A concurrent session is actively extending the exact surface `spec-036` contracts, and the
   archived spec does not describe it.** The baseline-dirty `docs/GLOSSARY.md` (+18 lines, uncommitted)
   names contracts that Decisions 8, 10 and 15 do not carry: `Meta.select_for_update` row locking
   with a retryable `conflict` error code distinct from `not_found`; a single write alias resolved
   once per operation with a `ConfigurationError` on a re-routing hook; authorization as a
   point-in-time decision that must return an actual `bool`; frozen hook views; `Meta.injected_fields`;
   and a read-only-transaction authorization-phase database barrier. Whether any of it is at `HEAD` is
   for the cohorts to establish read-only — **do not read the dirty tree as `HEAD`** — but the surface
   is plainly moving, so the conformance audits should expect `spec-036`'s Decisions 8 / 10 / 15 to
   be the ones that diverge most, and should re-derive against `HEAD` rather than the working copy.

### Summary

`spec-036`'s deliberative layer is out of the spec and into
`docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md`, the gap that made `spec-036` the only
archived spec of its cohort without a `-rationale.md` sibling. The spec fell **164,498 -> 131,777
bytes (-32,721, -86 lines)** and the arithmetic closes against 37,644 bytes carried out and 4,923
bytes of framing added back. The companion is 74,895 bytes / 428 lines, keyed to the spec by heading
and anchor at all 15 Decisions, with `### Changes this Decision underwent` seeded from the five
revision entries and ready to take the R2 pass's `**Post-ship:**` bullets. Four gates pass, both files
have 0 unresolved in-page anchors and full reference/definition parity, and every moved line is
byte-verbatim except 5 re-pointed section anchors and 4 repairs of a slug the spec had broken at 16
sites. Five suspected divergences are routed to the audit cohorts above; none was fixed here.

Final status: `final-accepted`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
