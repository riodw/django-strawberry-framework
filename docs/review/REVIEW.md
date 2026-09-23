# REVIEW: three axes on every package file

Entry: `Execute docs/review/REVIEW.md (You are Worker-0)`. Worker 0 reads [AGENTS.md][agents] +
[START.md][start], generates or resumes the plan, then runs every item, revision and the final
gate autonomously until the plan says `Status: complete` or a genuine maintainer decision blocks
it; `pause-after-each-item` only when the command names that mode. Nothing here self-starts.
[AGENTS.md][agents] governs safety, tests, formatting, commits.

Population: package source under `django_strawberry_framework/`. Tests, examples and docs are read
wherever the trace leads and edited only as the media of a package change.

REVIEW complements [DRY.md][dry] and [HUNT.md][hunt]. DRY asks whether a rule has one owner; HUNT
asks whether a contract can be broken. REVIEW asks whether the code, as written, is the code a
senior maintainer would be glad to own: fast where it runs often, placed where its rule lives,
described by prose that is true. Three axes, in the order the implementation applies them:

1. **Performance** — cost per request, resolver, row, connection, outbound message; import-time
   cost; query shape. The axis this flow exists for.
2. **Mechanics** — placement (the layer that owns the rule), business logic against its contract
   sources, dependency direction, state ownership, duplication that implements one rule twice.
3. **Comments** — every docstring and comment graded true, stale, duplicating the code, or
   process provenance; test docstrings stating behavior.

Anything found is handled inside this flow. A correctness defect uncovered while reading is fixed
here under HUNT's evidence discipline; duplication uncovered here is consolidated under DRY's
ownership rules; neither is handed off. The one exit is a genuine maintainer decision, recorded
`blocked`.

## Roles

Three roles, fresh context per dispatch, the finder never the fixer, the fixer never the approver.
Role files [worker-0.md][worker-0], [worker-1.md][worker-1], [worker-2.md][worker-2] = role delta
only; this doc is canonical.

- **Worker 0 — coordinator.** Owns the plan, baselines, bench baseline, dispatch, mechanical
  acceptance checks, ledger, scratch cleanup, final gate. Never reviews, implements, approves,
  overrides a verifier.
- **Worker 1 — axis reviewer and verifier.** Three per file item, one per axis, read-only on
  production code. Reviews the file as it stands and writes finding records, each carrying the
  proof that will show its fix landed, BEFORE any edit exists. After Worker 2 implements, the same
  Worker 1 verifies its axis against the combined change. A Worker 1 never edits production code
  or tests; its scratch lives under `docs/review/temp-tests/<scope>/` or in a workspace copy.
- **Worker 2 — implementer.** One per file item. Implements every accepted finding from all three
  axis records in axis order, with permanent tests and instrument numbers where the axis demands
  them, in the shared tree. Owns ruff, the ledger rows, and the docstrings of everything it
  changed. Never approves anything.

**The item fences edits, never inspection.** Worker 1 and Worker 2 read and trace wherever the
file leads: callers, consumers, sibling flavors, tests at every tier, examples, docs, the
installed Django / Strawberry / DRF sources in `.venv`. A review that stayed inside the target's
own module has not been done. Only the edit is scoped: the target, the owner a root-cause fix
requires, their tests, the ledger rows the item lands.

## Ground rules

- **Numbers, not adjectives.** A performance claim carries a metric, an instrument, a before and
  an after, the same metric both sides, reproduced from a stated command. A single-shot wall-clock
  reading is not a number. Query-shape claims assert the count at two or more parent cardinalities
  plus one absolute count taken from a real run ([BUILD.md][build] "Query-shape tests must pin the
  load-bearing property").
- **Hot path decides the trade.** Hot = per request, resolver, row, connection, outbound message.
  Cold = per process start, schema build, management command, declaration. On a hot path a
  measured saving is implemented when the code stays as plain as it was, or the record states why
  it cannot; on a cold path plainness wins and a performance finding needs a stated reason to be
  implemented at all. No worker weakens a correctness or authorization boundary to buy a number.
- **A defect is a defect.** A Mechanics finding that names a broken contract follows HUNT: contract
  row first, a feasible project shape under the supported public API, the wire or configuration
  input that reaches it ([AGENTS.md][agents] rule 35), evidence a stranger can replay, root-cause
  fix at the owner, permanent test at the strongest reachable tier in the same change. A contract
  nobody can cite → `blocked`, Rio decides; never a fix.
- **Duplication needs one rule.** Consolidate only when sites implement one rule w/ one contract
  and the same reasons to change; count authoritative definitions the way DRY's change challenge
  does, and choose the owner by responsibility (DRY principle 7). Similar-looking code w/ separate
  reasons to change stays separate, recorded w/ its trigger.
- **Comments describe the final code.** The Comments axis is implemented last and verified last so
  it grades the text Worker 2 left, including text Worker 2 wrote.
- **Sensitive findings.** A client-reachable isolation or authorization defect takes the
  [SECURITY.md][security] maintainer path before its reproducer lands in any tracked file: item
  `blocked`, defect named abstractly, evidence held in scratch.
- **Test runs.** The entry command authorizes any run inside a workspace copy, a focused permanent
  test w/ `--no-cov` in the shared tree, the bench scripts inside a workspace copy, and the final
  gate `uv run pytest`. Nothing else converts into a test run. `FAKESHOP_SHARDED=1` and Postgres
  cells need Rio's separate word; without it a cell is `unverified` and listed, or
  `inapplicable by construction` when the target reaches no database, alias or dialect decision
  (the reviewer states the reason, the verifier judges it).
- Only Rio commits, branches, pushes, edits the changelog. Concurrent work is preserved
  ("Baseline and ownership").

## The three axes

Each axis = what the reviewer looks for, the instrument that turns a suspicion into evidence, and
what its finding record must carry beyond the common fields. The lists are the floor of a review,
not its shape; a file yielding only list hits has not been read.

### Performance

Looks for: N+1 and per-row queries (a related-object read inside a loop, `await` per row in an
async resolver, `.filter()` on a prefetched relation discarding the prefetch); `len(qs)` or
`bool(qs)` where `.count()` / `.exists()` is meant and the reverse; `only()` / `defer()` that
trigger deferred loads; unbatched writes where `bulk_create` / `bulk_update` fit; `blog.id` where
`blog_id` avoids a query; repeated `_meta` walks, repeated settings reads, repeated regex
compilation, repeated schema or type lookups per request; `lru_cache` on methods (leaks per
instance, `B019`); locks, cache reads, re-parses or extra round trips added to a per-request path;
import-time cost (`python -X importtime`, settings read at import); allocation in the walk
(throwaway lists, dict rebuilds, string building in the hot loop).

Instrument: `django.test.utils.CaptureQueriesContext` or the `django_assert_num_queries` fixture
at two cardinalities plus the absolute count; `QuerySet.explain()` for shape; `timeit` median over
a stated iteration count; the repo benches [bench_plan_cache.py][bench-plan-cache] (steady-state
plan cache), [bench_optimizer_walk.py][bench-optimizer-walk] (cold walk),
[bench_nested_fetch.py][bench-nested-fetch] (Postgres, needs Rio's word), all bootstrapped through
[_bench_common.py][bench-common]; `python -X importtime -c "import django_strawberry_framework"`.
Every measurement runs inside a workspace copy ("Workspace"), before and after, same command.

Record carries: `Path class: hot | cold` w/ the reason (which caller runs it per what); the
instrument; before; after; delta; the permanent test that pins the shape (query count at two
cardinalities + absolute, or the bench delta recorded under the plan's `## Bench baseline` when
no test can pin it).

### Mechanics

Looks for: a rule enforced at a caller instead of its owner; policy in an adapter, mechanism in a
policy layer; a decision the contract sources ([docs/README.md][docs-readme] error policy and
mutation envelope, [docs/GLOSSARY.md][glossary] anchors, owner docstrings, existing oracles) make
differently from the body; a branch no real path reaches; a mode flag standing in for a named
adapter; state owned in two places; a dependency pointing the wrong way (a lower layer importing
a flavor above it, `TYPE_CHECKING` hiding a real cycle); `django.conf.settings` read at import;
an `__all__` that disagrees w/ the public surface; two sites implementing one rule (run DRY's
change challenge: posit a change, count authoritative definitions; `> 1` = duplication);
sync/async twins that drifted; a guard one flavor has and a sibling lacks (a contract source must
establish the rule applies before it is a defect; otherwise a rejection w/ trigger).

Instrument: the trace (`rg` for callers, importers, registrations, tests, docs); a workspace probe
for any behavior the reader is unsure of; for a suspected defect, HUNT's evidence record
(workspace path + package `__file__` + database `NAME`, command, digests, collected/executed
counts, reach assertion, positive control); for suspected duplication, DRY's finding record
(contract + variation, sites + roles, challenges w/ counts, owner + lifetime, migration,
behavioral proof, structural gate).

Record carries: the owner it should live at and why; the contract source cited; for a defect the
HUNT fields (Defect, Evidence, Impact, Severity w/ factors, Proof); for duplication the DRY
fields and the negative control its gate passes.

### Comments

Grades every docstring and comment in the file, and in every test the item touches, as one of:

- **true** — matches the body and its callers today;
- **stale** — described a body that has since changed (the worst grade: it misleads);
- **duplicates the code** — says what the next line says; delete it;
- **process provenance** — names a spec, card, round, worker, review, "fix for", "legacy",
  "moved from", "now", "no longer" ([AGENTS.md][agents]); delete or rewrite as the present-tense
  rule.

Also: a public symbol w/o a docstring; a first line that is not imperative; a docstring restating
the signature or the type hints; "we" / "you" / "I"; a test docstring beginning "Tests that" or
"Ensures" instead of stating the expected behavior; a source reference by line number or by a
name that no longer exists; a stated reason for a design that the body contradicts (DRY principle
10: wrong stated reason is worse than none); an intentional separation or a rejected
consolidation that is NOT recorded at the owner when the trace shows it should be.

Instrument: reading each docstring against its body and against one real caller;
`rg -n '::[A-Za-z_]+' <path>` to check every symbol citation resolves; `rg -n -i
'spec-|card|round|worker|legacy|moved from|no longer|previously' <path>` as orientation for
provenance (a hit is a lead, the grade is the finding).

Record carries: the symbol; the grade; the text before; the text after. Text after is the
reviewer's proposal; Worker 2 may improve it and the verifier grades what landed.

## Severity

By consequence, across all axes:

- **High** — correctness, security, data isolation or public-contract failure; a per-row or N+1
  query on a hot path; a stale docstring on a public symbol that states the wrong contract.
- **Medium** — a measured cost on a hot path without N+1; a rule enforced at the wrong layer; a
  stale comment on internal code.
- **Low** — a bounded clarity or maintainability improvement; a cold-path cost; a comment that
  duplicates its code.

Every High and Medium finding is implemented unless rejected in the record w/ a trigger. Low
findings are implemented when they ride on a file Worker 2 is already changing for a higher
finding, else recorded `deferred` w/ the reason and left visible in `## Outcomes`. Style
preference, and speculative risk w/o a reachable input, are not findings.

## Plan

One plan per release, `docs/review/review-<release>.md` (`0.0.15` → `review-0_0_15.md`), release
read from the package `__version__`. Existing plan for the release → resume: validate `Status:`,
`Run:` and `## Cycle baseline` against the tree (a `Status:` line alone is never trusted),
continue under `## Run <release> <date>-<n>`, never replace. Worker 0 alone edits the plan; nobody
erases prior lines. A plan w/o `## Cycle baseline` predates this flow: its ticks are history and
every item is re-verified under the new run.

Inventory, run from the repo root:

```shell
git ls-files 'django_strawberry_framework/*.py' | grep -v '__init__\.py$' | sort
git ls-files 'django_strawberry_framework/*.py' | sed 's|/[^/]*$||' | sort -u
```

Plan header: `Status: planned | in-progress | complete | partial (<scope>) | blocked`; `Mode:
autonomous | pause-after-each-item`; `Run: <release> <date>-<n>` (repeated on every artifact);
`Scope: package | <folder or path list>` as the entry command named it; `## Cycle baseline`;
`## Bench baseline`; `## How to work one item`; one file item per inventory line; one folder
integration item per package folder; the project integration item; the final gate;
`## Decisions` (maintainer decisions the run surfaced: ruff rules to enable, trade-offs, contracts
nobody could cite); `## Owned changes` (ledger); `## Outcomes` (closeout).

Item shape:

```text
- [ ] optimizer/walker.py
    - Status: pending
    - Path class: <hot | cold, from the Performance record; blank until reviewed>
    - Artifacts: rev-optimizer__walker.md + rev-optimizer__walker.<axis>.md × 3
```

A run scoped below the whole plan (`Scope:` names folders or paths) works only its scope, sets
`Status: partial (<scope>)` at closeout, and closes w/ an `## Outcomes` "Scope of this run"
section naming what ran and what did not; an unticked box never reads as examined. Scoped runs
are the normal mode: a full pass over the package is seven dispatches per file across a hundred
files, and a release rarely changes more than a few folders.

Before a run's first dispatch, and again before the final gate, Worker 0 reconciles the plan w/
the current inventory: `.py` added → new item; removed / renamed → item closed w/ note, artifacts
re-keyed. An item whose freshness fingerprints no longer match is reopened, whatever its checkbox
says.

## Baseline and ownership

Cycle entry: Worker 0 appends `CYCLE_BASELINE=$(git stash create)` (empty → `HEAD`) + untracked
files under the package to `## Cycle baseline`, once. Everything dirty there = concurrent work:
never edited, reverted, tidied. The block is never rewritten; fingerprints, not the block, decide
staleness. When `HEAD` moves or `git status --short` names a path the block lacks, Worker 0
appends one `Drift: <date> HEAD <old>..<new>; dirty + <paths>` line under the current run heading
(the header `Run:` line on the first run, `## Run <release> <date>-<n>` afterwards), continuation
lines indented two spaces.

Per item: `ITEM_BASELINE=$(git stash create)` + the same listings. Item-scoped diff =
`git diff <item baseline> -- <paths touched>` PLUS every file the item added
(`git diff --no-index /dev/null <new>`).

Each item landing tracked edits or new files appends to `## Owned changes`: path, item, axis,
symbols changed. A later item may build on a ledgered path. Attribute by content, never by dirty
status: before editing a dirty path, Worker 2 diffs vs `git show HEAD:<path>` and matches every
hunk to the ledger or the cycle baseline; a hunk in neither = external edit → stop, report to
Worker 0, who reconciles w/ Rio. Same stop when the item-scoped diff shows hunks the worker
didn't make.

A test failing before the item's first edit is pre-existing: reproduce it in a workspace copy taken
before that edit, record it under the artifact's `## Defects` w/ the failing command, route to Rio
through Worker 0. It blocks the gate row, never the item.

### Bench baseline

Performance verdicts need a per-release reference. At cycle entry Worker 0 takes a workspace copy
and records under `## Bench baseline` the command and output of
[bench_plan_cache.py][bench-plan-cache] and [bench_optimizer_walk.py][bench-optimizer-walk] plus
`python -X importtime` for the package import, each bound to `CYCLE_BASELINE`.
[bench_nested_fetch.py][bench-nested-fetch] joins only when Rio authorizes a Postgres cell. The
final gate reruns the same commands in a fresh copy and records the delta. A Performance record
cites the baseline figure it moves; a file item whose change moves no bench figure pins its claim
w/ a query-count test instead.

## Workspace

A scratch directory is not a sandbox: a probe under `docs/review/temp-tests/` still imports the
live package and opens the tracked `examples/fakeshop/db.sqlite3`. Every measurement, every
destructive or source-mutating probe, every bench run lives in a disposable copy:

```shell
WS=<scratch>/review-ws/<item>/<role>
rsync -a --exclude .git --exclude .venv --exclude '__pycache__' --exclude docs/ ./ "$WS/"
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
```

Every command runs w/ `$WS` as cwd (`uv run --directory "$WS"`): `--project` alone keeps the
caller's cwd on `sys.path`, so the import above prints the SHARED package and the check passes for
the wrong tree. Before any verdict the record shows the printed package path inside `$WS` and the
database `NAME` resolved from inside `$WS`. A measurement importing the shared checkout or opening
its database = `invalid`, whatever it showed. `scripts/prove_failability.py` runs only from inside
`$WS`. Reviewers take a copy of the tree as it stands; Worker 2 measures "after" in a copy taken
after its own edits; verifiers take a FRESH copy after Worker 2 reports so they grade the exact
change. Promotion = Worker 2 applying the change to the shared tree by hand, then the focused
permanent test there. No branches, no shared-tree restores.

Read-only scratch (a probe that imports the live package and writes nothing) may live under
`docs/review/temp-tests/<scope>/`, untracked. Workers never clean up; Worker 0 removes item scratch
+ `$WS` only after the item is `verified`.

## Cycle per file item

```text
Worker 0: ITEM_BASELINE, skeleton artifact, dispatch
    ├─ Worker 1 · Performance ─┐
    ├─ Worker 1 · Mechanics   ─┤  parallel, read-only, each writes rev-<path>.<axis>.md
    └─ Worker 1 · Comments    ─┘
Worker 0: mechanical checks on every record → Status: ready-for-implementation
Worker 2: implements axis by axis, Performance → Mechanics → Comments
Worker 0: mechanical checks on the report → Status: ready-for-verification/<n>
    ├─ Worker 1 · Performance ─┐  parallel, fresh workspace each, same Worker 1 as the review
    └─ Worker 1 · Mechanics   ─┘
    then Worker 1 · Comments    last, so it grades the final text
Worker 0: all three axes verified → ledger, tick, cleanup, advance
```

### Worker 0 dispatches

Records `ITEM_BASELINE`; writes the skeleton `rev-<path>.md` (header, `Status: reviewing`, `Run:`,
`Path class:` blank) and nothing else in it; spawns three fresh Worker 1s at once, each w/ its
axis, the target, the plan path, run id, both baselines, the ledger, its axis record path,
workspace path, required reading. Every Worker 1 reads the plan and the other axes' records when
they exist; edits only its own axis record.

### Worker 1 reviews

Reads the whole live target, then traces in and out until the contracts are clear: who calls,
imports, registers, wraps, configures it; which state, lifecycle, settings, ORM, cache or
framework hook it relies on; how representative input becomes output, error, queries, persistent
state; which tests and public docs promise its behavior. Then reads for its axis as "The three
axes" describes, discharging every list entry w/ a finding, a `none` w/ the reason, or a
rejection w/ its trigger.

A finding that belongs to another axis is written into THAT axis's record under
`## Cross-axis (from <axis>)`, the one place a Worker 1 writes outside its own record; the owning
Worker 1 grades it during verification like any of its own. A finding that spans axes (a
consolidation that also removes a query) lives at the axis that owns the proof, cited from the
other.

Each finding record:

- **Observation** — what is wrong or improvable, `path::Symbol` for every site.
- **Evidence** — the trace, probe, measurement or contract source; for a measurement the
  workspace record ("Workspace"); for a defect the HUNT evidence record; for duplication the DRY
  challenge counts.
- **Impact** — why it matters beyond preference; the callers affected; for Performance the path
  class.
- **Severity** — High / Medium / Low w/ the factor that set it.
- **Recommendation** — the change and its owner; for Comments the text after.
- **Must not change** — the observable behavior the fix preserves (DRY principle 8), or `n/a`
  for a Comments finding.
- **Proof** — the command or check that shows the fix landed, written NOW, before any edit: the
  test node id and the count it asserts, the bench command and the direction the figure moves,
  the ruff select that goes quiet, the grade the rewritten text must earn. Verification runs this
  line, so a proof that cannot be run is not a proof.
- **Freshness** — `git hash-object` of every file inspected, including files excluded from the
  finding on the strength of their body.

Plus the axis-specific fields. Rejected candidates are recorded w/ the contract difference or
rule reason and the trigger that would reopen them. Zero findings on an axis is a legitimate
result when every list entry is discharged and the strongest rejections carry reasons. Worker 1
closes its record `Status: findings-recorded` (or `no-findings`) and reports to Worker 0: findings
by severity, rejections, defects, cells unverified, scratch paths, fingerprints.

### Worker 0 checks the records

Mechanically, before Worker 2 reads anything:

| Record shows | Verdict |
|---|---|
| a measurement w/o workspace path, package `__file__` and database `NAME` | `invalid: instrument` |
| package imported from the shared checkout, or database outside `$WS` | `invalid: wrong tree` |
| a Performance finding w/o `Path class` or w/o a before number | back to that Worker 1 |
| a finding w/o a runnable Proof line | back to that Worker 1 |
| a defect w/o a contract row or a reachable input | `rejected as defect`; may stand as Mechanics |
| a site cited by line number, or a symbol that does not resolve | back to that Worker 1 |
| a list entry neither discharged nor rejected | back to that Worker 1 |

Twice back on the same row → `blocked` for Rio. All three records pass → Worker 0 copies
`Path class` into the plan item and the artifact header, sets the artifact
`Status: ready-for-implementation`, spawns a fresh Worker 2 w/ the target, all three records, the
plan, run id, both baselines, the ledger, workspace path.

### Worker 2 implements

Reads all three records, then the target and its neighbours until it can hold the whole change in
mind. Implements in axis order: Performance first because it may restructure; Mechanics next
because a rule moves to its owner on the code as Performance left it; Comments last so the prose
describes the result. A later axis's finding may be discharged
by an earlier axis's change; Worker 2 records that under the finding instead of applying it
twice.

Per finding: attribute hunks on every dirty path first ("Baseline and ownership"); measure
"before" in a workspace copy where the record's Proof asks for a number; apply the change to the
shared tree by hand; measure "after" in a fresh copy; write the permanent test at the strongest
reachable tier ([AGENTS.md][agents]: live GraphQL usage against fakeshop first, then example
tests, then package tests); run it focused w/ `--no-cov`. A live-tier test needing a fakeshop
fixture that does not exist lands at the strongest existing tier and the missing fixture goes to
`## Decisions`; never a new example model inside an item. Every gate a finding relies on must be
shown able to fail (`scripts/prove_failability.py`, inside `$WS`).

Worker 2 may dispute a finding: it records `disputed: <reason>` under the finding, implements
nothing for it, and the owning verifier judges. It may improve a Recommendation's shape or text
when the trace shows a better one, recording what it did instead and why; the Proof line still
governs. It never silently skips a finding.

After the last axis: `uv run ruff check --fix .`, then `uv run ruff format .` last, until
`uv run ruff format --check <paths touched>` and `uv run ruff check <paths touched>` both pass.
Then appends `## Implementation (Worker 2)` to `rev-<path>.md`: per axis, per finding, what
landed (`implemented | discharged by <finding> | disputed | deferred`), files changed and why each
moved, before / after numbers w/ their workspace records, permanent tests and their focused
results, failability proofs, formatter result, every scratch and workspace path, fingerprints of
every file touched or read for the change. Reports to Worker 0.

### Worker 0 checks the report

The evidence table again, on the report: every High and Medium finding has a disposition; every
number has a workspace record; every changed path is attributed; ruff passed; the item-scoped
diff contains no hunk the report does not explain. Failure → back to Worker 2 w/ the row named
(twice → `blocked`). Pass → `Status: ready-for-verification/<n>`, item-scoped diff written to
scratch, three fresh workspace copies, the SAME three Worker 1s re-dispatched (fresh only when a
context is gone, w/ its record as the handoff), Performance and Mechanics at once, Comments after
those two report.

### Worker 1 verifies

Expectation-first: the Proof line written before the edit is the expectation. Each verifier, on
its own axis:

1. Runs every Proof line in its record against the fresh workspace and records the result beside
   it; reproduces every number Worker 2 reported for its axis from the recorded command; a
   Performance verifier also confirms the "before" figure against the bench baseline or its own
   pre-edit copy.
2. Re-reads the WHOLE item-scoped diff through its axis, not only its own findings: the
   Performance verifier measures a Mechanics move that touched a hot path; the Mechanics verifier
   checks a Performance rewrite or a consolidation preserved observable behavior (temporarily
   revert the production hunk inside `$WS` and show the pre-fix behavior was the worse one); the
   Comments verifier grades every docstring and comment Worker 2 wrote or moved.
3. Attacks the change on its axis: the other cardinality, the other flavor, the other cell, the
   caller Worker 2 did not name.
4. Judges every `disputed` finding on its reason; a standing disagreement is `blocked` at once w/
   both positions recorded, never a third pass to break it.
5. Confirms permanent tests exercise real usage at the mandated tier and fail w/o the change
   (Mechanics and Performance verifiers), and that the item-scoped diff carries no process
   provenance, no line-number citation, no `we` (Comments verifier).
6. Runs `uv run ruff format --check` and `uv run ruff check` on the touched paths (Mechanics
   verifier); a failure is `revision-needed`.

Appends `## Verification (<axis>)` to its record w/ the checks and results, sets the record
`Status: verified` or `Status: revision-needed` w/ concrete named gaps, reports to Worker 0.
Verifiers never edit production code or tests; a verifier that finds a new problem records it as a
new finding w/ a Proof line and returns the record `revision-needed`.

### Worker 0 closes the item

Any axis `revision-needed` → the artifact `Status: revision-needed`, Worker 2 again (same Worker 2
while its context lives), then back to the verifiers that failed; two failed re-passes → `blocked`
for Rio. All three `verified` → ledger rows, `Result:` and `Verification:` lines on the plan item,
tick, remove item scratch and `$WS` by explicit path, advance (`autonomous`) or report and wait
(`pause-after-each-item`). Worker 0 never regrades a verifier.

Plan item result lines:

```text
Result: <n> findings implemented (<H>/<M>/<L>), <n> rejected, <n> deferred. Files: <paths>.
Verification: Passed. Performance <numbers or none>; Mechanics; Comments.
Cleanup: Removed <item scratch and workspace paths>; unrelated work preserved.
Blocked: <condition and the decision Rio must make>.
```

## Artifacts

Four per file item, all under `docs/review/`, untracked until Rio commits them, protected by
[AGENTS.md][agents] rule 22 from bulk deletion. Names take the source path relative to the
package, `/` → `__`, `.py` dropped: `optimizer/walker.py` → `rev-optimizer__walker.md` +
`rev-optimizer__walker.performance.md`, `.mechanics.md`, `.comments.md`. Folder
pass `rev-<folder>.md`; project pass `rev-project.md`.

Main artifact, written by Worker 0 and Worker 2 only:

```text
# Review: `path/to/target.py`

Status: reviewing | ready-for-implementation | implementing | ready-for-verification/<n> |
        revision-needed | verified
Run: <release> <date>-<n>
Path class: hot | cold — <reason>

## Implementation (Worker 2)

Per axis, per finding: disposition, files, numbers, tests, proofs, formatter result, paths,
fingerprints.

## Defects

Correctness defects fixed in this item (HUNT fields) or blocked for Rio; pre-existing failures.

## Pending execution

`proof: <command>` for a proof only the final gate can run; `gate: <command>` for a witness that
routes nowhere. Absent when none.

## Iterations

Later passes append here; nobody erases prior reasoning.
```

Axis record, written by its Worker 1 only:

```text
# Review · <Axis>: `path/to/target.py`

Status: reviewing | findings-recorded | no-findings | verified | revision-needed
Run: <release> <date>-<n>

## Trace

What was read, callers followed, cells covered; fingerprints.

## Findings

### High / ### Medium / ### Low

One record each (common fields + axis fields). `None.` under an empty severity.

## Rejected

Each w/ the reason and the trigger that reopens it.

## Cross-axis (from <axis>)

Findings other reviewers placed here; graded at verification.

## Verification (<Axis>)

Proof results, numbers reproduced, whole-diff reading, attacks, disputes judged, verdict.
```

No inventories, copied tool output, empty placeholders. Raw `path:NN` is tolerated in these
per-cycle artifacts only; everything that lands in code, tests or standing docs cites
`path::Symbol`.

## Integration passes

Folder pass after every file item in the folder is verified: one Worker 1 per axis again, on the
folder as one component, looking for what no file shows alone: a hot path that crosses the folder
(Performance), a rule split across siblings or a flavor missing a guard its siblings have
(Mechanics), module docstrings that disagree w/ each other about who owns what (Comments). Same
cycle, same records, `rev-<folder>.md`.

Project pass after every folder: public exports and `__init__.py` files, import-time cost of the
package as a whole against the bench baseline, end-to-end lifecycle, gaps between package
behavior and its tests, examples and docs. Re-inventory first. `rev-project.md`.

## Final gate and closeout

Every item but the gate verified + inventory re-reconciled → Worker 0 runs the gate: `uv run
pytest` (full suite, package coverage 100%), every `## Pending execution` command from every
artifact as listed, the bench baseline commands in a fresh workspace copy w/ the delta recorded.
Record failures, coverage, skips, xfails, collected/selected counts, `FAKESHOP_SHARDED` mode
(sharded-only tests skip by default and stay `unverified` unless Rio authorizes a
`FAKESHOP_SHARDED=1` run). Bind the result: `git stash create` at gate time + blob ids of
`pyproject.toml` and `uv.lock` + mode. A change to package source, tests, fixtures, pytest or
coverage config, dependencies or mode invalidates it; prose does not. Failure in a path an item
touched, or of a `proof:` command → that item back to Worker 2 and its verifiers; a failing
`gate:` command reopens no item; a failure reproduced against `git show HEAD:` of its test and
target → pre-existing, `## Defects`, gate row `blocked` for Rio; environment failure → recorded
precisely, `blocked`.

Worker 0 fills `## Outcomes` BEFORE deleting anything. Per item: findings per axis w/ severity
and disposition; every number before / after w/ its command; owner moves; consolidations w/ their
challenge counts; comments regraded; defects fixed w/ their permanent tests; rejections w/
triggers; deferred Lows. Per run: bench baseline vs gate figures; decisions owed to Rio
(`## Decisions`); cells unverified; blocked items; net source change vs cycle baseline; gate
record; concurrent work untouched; "Scope of this run" for a scoped run. Then `Status: complete`
(`partial (<scope>)`; `blocked` w/ the decision Rio owes). Remove only this run's
`docs/review/temp-tests/<scope>/` dirs, `<scratch>/review-ws/`, and `docs/review/worker-memory/`
contents, by explicit path. Never recursively clear `docs/review/`; never remove `REVIEW.md`, the
role files, the plan, or any `rev-*.md`. Do not commit.

Under [MUSE.md][muse], a REVIEW Worker 0 running beside a hunt or DRY Worker 0 states the
production files its open items own in the sibling prompts, and honours theirs: a path another
flow's ledger names is concurrent work here.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[muse]: ../../MUSE.md
[security]: ../../SECURITY.md
[start]: ../../START.md

<!-- docs/ -->
[docs-readme]: ../README.md
[dry]: ../dry/DRY.md
[glossary]: ../GLOSSARY.md
[hunt]: ../bug_hunt/HUNT.md
[worker-0]: worker-0.md
[worker-1]: worker-1.md
[worker-2]: worker-2.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build]: ../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[bench-common]: ../../scripts/_bench_common.py
[bench-nested-fetch]: ../../scripts/bench_nested_fetch.py
[bench-optimizer-walk]: ../../scripts/bench_optimizer_walk.py
[bench-plan-cache]: ../../scripts/bench_plan_cache.py

<!-- .venv/ -->

<!-- External -->
