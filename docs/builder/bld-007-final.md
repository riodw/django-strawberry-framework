# Build: Final test-run gate — spec-007 residual-completion cycle

Spec reference: `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` (57 lines / 2,983 bytes)
Plan reference: `docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md`, `## Checklist` final row
Status: final-accepted

## Spec status-line re-verification (every Worker 1 spawn)

Read this pass: spec lines 1-7 — title, `Target release: 0.0.4 (per KANBAN.md card DONE-007-0.0.4)`,
`Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact`,
`Owner: package maintainer`, and the rationale pointer paragraph.

All still describe the build's current state. `Card.objects.get(number=7)` is `done` at `0.0.4`; the
rationale target the pointer names resolves on disk (`docs/SPECS/appx/spec-007-…-rationale.md`, 672
lines / 46,045 bytes). **No edit made.** No status line was falsified by this pass.

## Gate commands and their real results

Run from the repository root against the shared `.venv`, in the order `docs/builder/BUILD.md`
`## Final test-run gate` gives them. Every result below is the verbatim outcome of the run.

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **pass** — `5640 passed, 40 skipped in 73.13s`, exit 0 |
| 2 | `uv run python examples/fakeshop/manage.py check` | **pass** — `System check identified no issues (0 silenced).`, exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **pass** — `No changes detected`, exit 0 |
| 4 | `uv run ruff format --check .` | **pass** — `418 files already formatted`, exit 0 |
| 5 | `uv run ruff check .` | **pass** — `All checks passed!`, exit 0 |
| 6 | `git diff --check` | **pass** — no output, exit 0 |

No `--cov*` flag was passed in this pass or any pass of this cycle. `--no-cov` is the only
coverage-shaped flag used, per `BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`.

### Failures, and their attribution

**There are none.** Every gate command exited 0, so the plan's baseline exception
(`## Baseline-dirty out-of-scope files`, "Baseline exception for the final test-run gate") was **not
exercised** — nothing had to be attributed away from `final-accepted`, and nothing is reported to the
maintainer under it.

This is worth stating rather than passing over, because the exception was live and expected to matter.
All six commands read the entire tree, and three concurrent sessions are writing it — including five
package-source and test files on the transport surface
(`django_strawberry_framework/_boundary_ordering.py`, `_cross_web_patches.py`,
`middleware/request_body.py`, `examples/fakeshop/test_query/test_transport_api.py`,
`tests/test_views.py`), which is precisely where a `pytest` or `ruff` failure would have surfaced. The
third session's in-flight work happens to be green at the moment this gate ran. Had it not been, the
attribution rule below would have applied; it is recorded so a re-run of this gate at a different
moment has the reasoning in hand rather than having to re-derive it.

**The attribution rule this gate would have applied.** This cycle's entire writable output is two
Markdown files — `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` and
`docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` — plus four
`docs/builder/bld-007-*.md` artifacts and the gitignored namespaced memory file. A `pytest` failure is
caused by Python collected by `pytest.ini`'s test paths, and a `ruff` failure by a file ruff lints;
neither reaches a Markdown file under `docs/SPECS/` or `docs/builder/`, so no `pytest` or `ruff` result
can be caused by anything this cycle wrote. That is a statement about what the tools read, not an
assertion of innocence — and it is why a failure in the transport surface would have been reported to
the maintainer and named to the third session, never routed back through R1/R2/R3's loop.

### `git diff --check`, filtered

`git diff --check` reads the whole tree for whitespace errors and conflict markers. It produced **no
output at all**, so the filter to this cycle's own files is trivially satisfied: there is no hit
belonging to this cycle and none belonging to any other session to report as attributed.

## Also run, because this cycle's chain depends on them

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/builder/bld-007-final.md
exit=0        (run after this file was written; re-run after every later edit to it)

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0
```

The 1-anchor constraint holds at the close: the spec's sole glossary carrier is `## Scope` bullet 2's
`[optimizer behavior][glossary-djangooptimizerextension]`, and both the `check_spec_glossary` and
`import_spec_terms` chains are green against it. `docs/GLOSSARY.md` was **read only** — this gate wrote
no database row and no generated doc.

### Staged-anchor sweep (`BUILD.md` `## Cross-slice integration pass` step 6)

```text
$ grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' .
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:34
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:266
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:302
exit=0

$ grep -rEn --exclude='build-007-*.md' --exclude='bld-007-*.md' 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' .
exit=1        (no match)
```

**Three self-hits, all in this cycle's own build plan, all prose describing the sweep** — the R3
scope bullet, the read-only-audit bullet, and the R3 checklist row. None is staged work. Their **line
numbers have moved three times** as Worker 0 appended growth sections to the plan, which is why the
match is made on the **file**, never the line: at R2 they were lines 34 / 244 / 280, and they read 34 /
266 / 302 now.

**The excluded population, named in full so a reader can see it swallows nothing else.** The two globs
exclude exactly four files, enumerated by `find . -name 'build-007-*.md' -o -name 'bld-007-*.md'`:

- `docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md` (the plan — carries all three hits)
- `docs/builder/bld-007-r1-rationale_move.md`
- `docs/builder/bld-007-r2-spec_reconciliation.md`
- `docs/builder/bld-007-r3-doc_completion_archive.md`

`docs/builder/bld-007-final.md` — this file — matches the `bld-007-*.md` glob too and is excluded on
the same ground. Every excluded file is a per-cycle artifact of **this** cycle that closes with it; no
shipped source, test, example, standing doc, or other cycle's file is inside the exclusion. The shipped
trees are clean under both sweep forms.

## Declarations, recorded as absences rather than left silent

- **Ownership partition: none.** The plan declares it (`Ownership partition: none; sequential residual
  items`), and the cycle ran R1 → R2 → R3 sequentially with no parallel cohort.
- **Hot-path declaration: none.** No number is owed and the absence is correct — no item in this cycle
  changed package source, so nothing runs per request, per resolver, per row, per connection, or per
  outbound message.
- **Failability proofs: none owed.** No item introduced a boundary, guard, gate, or rejection path;
  the cycle's whole diff is Markdown.
- **Fail-open shapes: none possible.** There is no expression in this cycle's diff — it contains no
  executable code.

### Floor verification

**The plan declares `Floor-verification scope: none`, and this gate confirms that declaration was
correct rather than treating the silence as discharge.** No floor venv was built and no floor run
happened in any pass of this cycle, which is the right outcome: `BUILD.md` `### When it is required`
scopes floor runs to slices touching a Django / Strawberry / channels integration seam, and no residual
item here touched one — the cycle edited one archived spec and created one rationale sibling, both
Markdown. `BUILD.md` `## Final test-run gate` makes this gate the **backstop confirming a planned floor
verification happened**, not a second owner; with none planned, there is nothing to confirm ran and
nothing left unrun. The shared `.venv` was not mutated by any pass, and no `uv pip install` was run.

## Concurrent-commit check, not `git status` alone

```text
$ git rev-parse HEAD          -> 947f74948c16b20b0c15ff359bb53fbe462d4b8c   (open and close)
$ git log --stat -- <this cycle's six paths>
    1592bb90  refactor(kanban): consolidate the card queue onto Status; drop PlanningState
    e1f9ed26  docs: backfill shipped spec glossary CSVs
    81e4704d  docs: archive prior specs to docs/SPECS/ and renumber per Step 8 pass
```

Every commit touching this cycle's paths long predates the cycle — the newest is the kanban `Status`
consolidation, and it touched the spec only. **No commit landed during this cycle, and nothing this
cycle wrote was swept into a concurrent session's commit.** `HEAD` is unchanged from the plan's
pre-flight reading.

The spec's uncommitted state is confirmed still exactly what R2 left and R3 verified:
`git diff --numstat` reads `20 28` and `wc -lc` reads `57 2983`. The rationale reads `672 46045` and is
still untracked, so it enters the maintainer's commit window alongside the spec.

## Working-tree growth — ninth growth event

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` read **31 entries** at this
pass's open, matching R3's close reading exactly. The only new entry at this pass's close is
**`docs/builder/bld-007-final.md` — this artifact**, which is this pass's own output and not growth
from another session. Measured at the close rather than inferred from the open, per the lesson R3's
final verification recorded.

No other session's file changed during this pass. The out-of-scope population is unchanged from R3's
close:

- **All four generated / binary files are dirty** — `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`,
  `examples/fakeshop/db.sqlite3` — from the concurrent spec-006 cycle's authorized DB-backed glossary
  completion. Read only by this gate; never written, never regenerated.
- **Five package-source and test files** are dirty from a third session working the transport surface
  (listed under `### Failures, and their attribution`). Not read for content, not touched.
- **The `docs/review/` set is four deletions plus one modification** (`rev-_django_patches.md`,
  `rev-_strawberry_patches.md`, `rev-apps.md`, `rev-conf.md` deleted; `rev-_cross_web_patches.md`
  modified), with two untracked (`rev-_boundary_ordering.md`, `review-0_0_14.md`). **Escalated to the
  maintainer at R1 and still unresolved.** Untouched by this gate; `AGENTS.md` rule 22's `git checkout`
  remedy is banned in this cycle and only the maintainer can adjudicate it.
- The concurrent spec-002 and spec-006 paths were not read for content and not touched.

## `### Deferred work catalog`

The next spec author's reading list, and this gate's most durable output. Walked from every per-item
artifact's `### Notes for Worker 1 (spec reconciliation)` and final-verification sections across
`bld-007-r1-rationale_move.md`, `bld-007-r2-spec_reconciliation.md`, and
`bld-007-r3-doc_completion_archive.md`. R3 catalogued eight items; each is re-verified live here, and
**none is reclassified**. Nothing the later passes surfaced adds a ninth.

1. **`CHANGELOG.md`'s `0.0.8` entry relies on design-doc pointers for release context.**
   Source: R3 `### 3`, reconciled in the spec at drift row **D9**; licensed as a deferral by
   `AGENTS.md` rule 21, which closes `CHANGELOG.md` to this cycle. Re-verified: line **140** cites
   `spec-027-filters-0_0_8.md` and `spec-028-orders-0_0_8.md`, definitions live at **388-389**; the
   file is **437 lines / 100,289 bytes**, so the card's "condensed" claim no longer describes it
   either. Maintainer decision.
2. **`CONTRIBUTING.md` cites a `BUILD.md` heading that does not exist.**
   Source: plan `### Every reference TO spec-007` (found at R1), carried by R2 `### 8` and R3 `### 3`.
   Re-verified: `CONTRIBUTING.md` line **11** cites `docs/builder/BUILD.md` "Spec filename pattern";
   `grep -c 'Spec filename pattern' docs/builder/BUILD.md` → **0**, and the real heading is
   `## Spec and build-plan filename pattern` at line **7**. Outside this cycle's writable set.
3. **`KANBAN.md`'s "three-minute path" row is a Done card's historical record — correctly NOT drift.**
   Source: R3 `### 3`, item 3. Re-verified: one occurrence in `KANBAN.md` and one in the `KANBAN.html`
   payload, both renders of card 7's `CardItem`. **The H1 history makes this sharper**: the phrase
   accurately described `docs/README.md`'s `## Three-minute path` heading as it stood at `83c25963`,
   so editing the DB row would falsify a correct historical record. Catalogued so no later pass
   "fixes" it.
4. **The escalated `docs/review/` set.** Source: plan `### First growth` (R1), unresolved through every
   later pass. Current state as measured above: four deletions plus one modification plus two
   untracked. Only the maintainer can adjudicate intent and restore safely.
5. **A `BUILD.md`-level convention question, escalated by Worker 3 at R2:** whether a durable figure
   must name both the commit it was measured at and whether that is committed or working-tree state.
   Unacted on; the escalated Low that R3's final verification closed is a further data point in its
   population-boundary variant. Standing-doc decision.
6. **`AGENTS.md` rule 27 does not name `build-*.md` alongside `bld-*.md`.** Source: R1
   `### Plan rows this pass's reading shows wrong`, carried to R3. The rule exempts per-cycle
   `docs/builder/bld-*.md` scratchpads from the no-raw-`path:NN` requirement but not the committed
   `build-*.md` plans, six of which carry the same shape. Standing-doc question, not a cycle defect.
7. **The rationale is 46,045 bytes against a 2,983-byte spec.** Source: R3 `### 3`, item 7; re-measured
   unchanged this pass. Not a defect and not this cycle's to fix — the ratio is what a spec whose every
   content claim was falsified looks like once the falsifications are recorded — but a future reader
   may want the record split or indexed.
8. **The concurrent spec-006 cycle names spec-007 as owner of four of its drift rows.** Source: R3
   `### 3`, item 8. No conflict: spec-007's reconciled `docs/README.md` bullet names sections that
   exist, spec-006's rows name sections that do not — disjoint. **The population update R3 flagged for
   this gate, re-measured here rather than restated:** `grep -rln 'spec-007-onboarding_docs_spec_consolidation'
   --include='*.md' .`, excluding the spec / plan / artifacts of this cycle, returns
   `KANBAN.md` (generated, expected) plus five concurrent-session files —
   `docs/review/review-0_0_14.md`, `docs/builder/bld-006-final.md`,
   `docs/builder/bld-006-r1-rationale_move.md`, `docs/builder/bld-006-r3-doc_completion_archive.md`,
   and `docs/builder/build-006-public_surface-0_0_3.md`. The set grows as the sibling cycle writes, so
   it is named rather than counted forward. It changes nothing about the **zero inbound-reference**
   property, which is scoped to `docs/SPECS/*.md` and re-verified here:
   `grep -rln 'spec-007' docs/SPECS/*.md` returns the spec itself and no sibling.

## For the maintainer — the short version

**What changed, and why.** Two durable files. `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md`
was a card-snapshot stub whose every content claim about the `0.0.4` documentation set had been
falsified by later work — five of its six `## Scope` bullets were true the day they were written and
wrong now. It was reconciled from an **inventory** into a **contract**: it states only the division of
responsibility the card established — which document answers which question, and why no two answer the
same one — in claims that are true at HEAD, and it ends at 57 lines / 2,983 bytes with its sole glossary
anchor re-sited inside the surviving prose so the DONE-card chain never broke. Every claim it can no
longer make, each with the commit or later card that falsified it, moved into a new tracked companion,
`docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` (672 lines / 46,045
bytes) — the only record of the `0.0.4` documentation-set history anywhere in the repository. Both
files enter one commit window; the rationale is still untracked.

**What was deliberately NOT changed.** Card 7's body (a Done card's `CardItem` rows are a record of
what it did, and all fourteen are accurate history even where the present tense they are written in no
longer holds); `CHANGELOG.md` (rule 21); `examples/fakeshop/db.sqlite3`; and the generated docs
`docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`. No source, test, or example file was written by any
pass — spec-007 shipped five Markdown files and no code, and the read-only correctness audit found no
defect in shipped source. Those files' dirty state in the working tree is other sessions' work.

**What is escalated and still needs your decision.** The `docs/review/` set — four tracked `rev-*.md`
deleted, one modified, two new untracked — appeared mid-cycle from a session outside this one.
`AGENTS.md` rule 22 calls `rev-*.md` committed source of truth and prescribes `git checkout HEAD --
docs/review/`, which this cycle is banned from running. It is either a REVIEW cycle's authorized
regeneration or a rule-22 violation; the evidence leans to the former (a deleted file came back) but
only you can confirm. Alongside it, four smaller follow-ups sit in the catalog above: `CHANGELOG.md`'s
`0.0.8` design-doc pointers, `CONTRIBUTING.md`'s stale `BUILD.md` heading citation, and two standing-doc
convention questions (`AGENTS.md` rule 27's exemption list, and whether a durable figure must name its
commit).

**The cycle's one recurring defect class.** Across eleven passes this cycle produced **ten** instances
of a single defect: **an unmeasured quantifier in durable prose** — a number, count, interval, or
absolute word written in the same sentence as the argument it supports rather than measured in its own
command first. It mutated as each catching discipline closed the previous form: bare numbers first,
then universals and "only"-shaped absolutes once numbers were being re-derived, then historical
absolutes ("never", "always", an interval in months) once present-tense universals were being grepped.
It even reached the plan correction that documents the class — "three months" against a measured
twenty-seven days. **One rule would have prevented every instance: a quantifier is a measurement, so
only the command that produced it may write it — and for a historical quantifier that command names a
commit, not the working tree.**

## Final status

`final-accepted`. Every gate command passed, no failure needed attributing, the staged-anchor sweep is
clean outside this cycle's own artifacts, the deferred-work catalog carries eight live items, and the
plan's `Floor-verification scope: none` is confirmed correct rather than silently inherited. Worker 0
may tick the plan's final checklist row and close the cycle.

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
