# REVIEW: three axes on every package file

Entry: `Execute docs/review/REVIEW.md (You are Worker-0)`, optionally followed by
`scope: <folders or modules>` and the mode word `pause-after-each-item`. Worker-0 reads
[AGENTS.md][agents] + [START.md][start], generates or resumes the plan over the named scope (no
scope named: the release's own committed changes, "Plan"), then runs every item, revision and the
final gate autonomously until the plan's run is closed; a `blocked` item is recorded and passed,
never a halt. `pause-after-each-item` only when the command names that mode. Nothing here
self-starts. [AGENTS.md][agents] governs safety, tests, formatting, commits.

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

- **Worker-0 — coordinator.** Owns the plan, baselines, bench baseline, dispatch, mechanical
  acceptance checks, ledger, scratch cleanup, final gate. Never reviews, implements, approves,
  overrides a verifier.
- **Worker-1 — axis reviewer and verifier.** Three per file item, one per axis, read-only on
  production code. Reviews the file as it stands and writes finding records, each carrying the
  proof that will show its fix landed, BEFORE any edit exists. After Worker-2 implements, a fresh
  Worker-1 on the same axis verifies the combined change, starting from that record. A Worker-1
  never edits production code or tests; its scratch lives under its item's scratch root
  ("Workspace") or in a workspace copy.
- **Worker-2 — implementer.** One per file item. Implements every accepted finding from all three
  axis records in axis order, with permanent tests and instrument numbers where the axis demands
  them, in the shared tree. Owns ruff, the ledger rows it proposes (Worker-0 copies them into the
  plan), and the docstrings of everything it changed. Never approves anything.

Worker-0 alone edits the plan and sets the main artifact's `Status:`; each Worker-1 alone writes
its axis record, and nobody writes into another's: parallel reviewers rewrite their own records
whole, so a section placed in someone else's record is lost; Worker-2 writes the main artifact's
`## Implementation (Worker-2)`, `## Defects`, `## Pending execution` and `## Iterations`
entries ("Artifacts").

**Every dispatch is a fresh agent, carried forward by its record.** No worker is continued w/ its
old context: a harness cannot compact a subagent, and an agent id dies w/ the session. Every
Worker-1 and Worker-2 ends what it wrote this pass w/ a `Handoff:` paragraph: what it read beyond
the record's trace, conclusions its findings do not state, open threads, a few lines. The next
dispatch of that role and axis starts fresh from the record and its handoffs. That is the flow's
compaction, written to disk, so it survives Worker-0's own compaction and a session restart.

**Effort.** Worker-0 High (the session it runs in), Worker-1 Medium, Worker-2 High. In Claude Code
the tracked definitions `.claude/agents/review-worker-1.md` and `.claude/agents/review-worker-2.md`
pin the subagents' effort, and Worker-0 dispatches through them by name. A harness or model w/o
per-agent effort, or a session started before the definitions existed, inherits the session's
effort; that is an accepted fallback, never a reason to stop.

**The item fences edits, never inspection.** Worker-1 and Worker-2 read and trace wherever the
file leads: callers, consumers, sibling flavors, tests at every tier, examples, docs, the
installed Django / Strawberry / DRF sources in `.venv`. A review that stayed inside the target's
own module has not been done. Only the edit is scoped: the target, the owner a root-cause fix
requires (a caller outside the target when the defect lives there; its hunks are ledgered under
this item like the target's), their tests, the ledger rows the item lands.

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
  it grades the text Worker-2 left, including text Worker-2 wrote.
- **Sensitive findings.** A client-reachable isolation or authorization defect takes the
  [SECURITY.md][security] maintainer path before its reproducer lands in any tracked file: item
  `blocked`, defect named abstractly, evidence held in scratch.
- **Test runs.** The entry command authorizes any `workspace.py run` or `prove` in any cell
  ("Workspace", "Database cells"), a focused permanent test w/ `--no-cov` in the shared tree, and
  the final gate `workspace.py gate review`. Nothing else converts into a test run. A cell is
  `inapplicable by construction` when the target reaches no database, alias or dialect decision
  (the reviewer states the reason, the verifier judges it); a cell the environment cannot run is
  `unverified`, listed w/ the failing command.
- **Database cells.** Three modes, mutually exclusive, chosen by `workspace.py run --cell`:
  `default` (single SQLite on the copy's own `db.sqlite3`), `sharded` (`FAKESHOP_SHARDED=1`: the
  same plus `shard_b` on the copy's own `db_shard_b.sqlite3`, which `seed_shards` may rewrite),
  `pg` (`FAKESHOP_PG_DSN` on the throwaway `docker-compose.postgres.yml` container, in a database
  of the copy's own). A finding whose target reaches an alias or dialect decision runs its Proof
  in every mode it reaches, as a pytest node under that cell: the Performance instruments
  (`count_queries.py` and the benches bar the nested fetch) always measure an in-memory SQLite
  database whatever the cell, so they prove nothing about another cell. The tool starts the
  container on the first `--cell pg` run; each copy's database is its own, and pytest's `test_`
  databases derive from it, so parallel copies and sibling flows never collide, and
  `bench_nested_fetch.py` reseeds only its copy's database. `gc` stops the container when the tool
  started it and no flow still holds a database. Nobody runs `docker compose` by hand:

  ```shell
  uv run python scripts/workspace.py run review/<item>/<role> --cell sharded -- \
      pytest <node> --no-cov
  uv run python scripts/workspace.py run review/<item>/<role> --cell pg -- pytest <node> --no-cov
  ```
- Only Rio commits, branches, pushes, edits the changelog. Concurrent work is preserved
  ("Baseline and ownership").

## Scripts

Every script the flow runs, from the repo root as `uv run python scripts/<name>.py`. The section
named in the last column owns the command form; `--help` gives flags and defaults, the module
docstring is the manual. "Shared" = the shared tree; "copy" = through
`workspace.py run <address> -- python scripts/<name>.py ...` ("Workspace").

| Script | Run by | Where | For |
|---|---|---|---|
| [workspace.py][workspace] | `run`, `prove`, `path`, `audit` (read-only; Worker-0's is the binding check): every role; `baseline`, `release`, `gate`, `gc`: Worker-0 | shared; runs everything else in copies | copies, cells, provenance, run ids, gate ("Workspace") |
| [review_plan.py][review-plan] | Worker-0 | shared (needs git) | `scope`, `plan`, `resume`, `reconcile` ("Plan") |
| [review_inspect.py][review-inspect] | every Worker-1; `--code-digest`: Comments roles, Worker-2 | shared; `--output-dir <scratch>` | AST orientation, never imports ("Worker-1 reviews"); prose-only identity ("Comments") |
| [count_queries.py][count-queries] | Performance roles | copy | queries per cardinality + verdict ("Performance") |
| [bench_plan_cache.py][bench-plan-cache] | Worker-0, Performance roles | copy | plan cache warm vs cleared ("Bench baseline") |
| [bench_optimizer_walk.py][bench-optimizer-walk] | Worker-0, Performance roles | copy | the walk alone ("Bench baseline") |
| [bench_nested_fetch.py][bench-nested-fetch] | Worker-0, Performance roles | copy, `--cell pg` | nested-connection strategies ("Database cells") |
| [importtime_report.py][importtime-report] | Worker-0, Performance roles | copy | per-module import-time minimum ("Performance") |
| [prove_failability.py][prove-failability] | Worker-2, Performance + Mechanics verifiers | `workspace.py prove` only | a gate can fail ("Workspace") |
| [build_tree_md.py][build-tree-md] | `--list-docstrings`: Comments roles, Worker-2; render: Worker-2 | shared | module first lines; TREE.md ("Comments") |
| [check_citations.py][check-citations] | `--paths`: Worker-0, Worker-1; `--cited-by`: Worker-1, Worker-2; `--check`: Worker-2, Mechanics verifier | shared, read-only | `path::Symbol` resolution ("Mechanics", "Comments") |
| [check_trailing_commas.py][check-trailing-commas] | Worker-2, Mechanics verifier | shared; `--check <paths>` | layout gate ("Worker-2 implements") |
| [review_changed_python_diffs_against_head.py][review-diffs] | Comments verifier | shared; `--output-dir <scratch>` | the item's prose diff ("Comments") |
| [_bench_common.py][bench-common], [_plan_common.py][plan-common] | nobody | n/a | plumbing the scripts above import |
| [clean_up.py][clean-up] | never | n/a | Rio runs it by hand; its globs match tracked records |

Two defaults write where the flow must not: `review_inspect.py` and
`review_changed_python_diffs_against_head.py` write into `docs/shadow/`, whose folders have one
owner each ([AGENTS.md][agents] rule 23), so both always take `--output-dir <scratch>/...`;
`check_trailing_commas.py` w/o `--check` auto-fixes, and w/o paths it rewrites the whole repo,
concurrent work included.

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
import-time cost (a module the package import pulls in, settings read at import); allocation in the
walk (throwaway lists, dict rebuilds, string building in the hot loop).

Instrument, every one run through `workspace.py run` ("Workspace"), before and after, same command:

- query shape: [count_queries.py][count-queries] runs one operation at several parent
  cardinalities and prints the count per cell plus a verdict (`batched`, exit 0;
  `scales with cardinality` or `mixed`, exit 1; exit 2 when nothing comparable was measured: a
  GraphQL error, fewer than two cardinalities, root rows that did not grow at every step, or a
  refused `--compare`); `--no-optimizer` is the positive control, `--json` the record,
  `--compare <earlier.json>` the before/after delta. The permanent test pins the same shape w/
  `CaptureQueriesContext` or the `django_assert_num_queries` fixture; `QuerySet.explain()` for plan
  shape;
- time: `timeit` median over a stated iteration count (the instrument for a pure-CPU saving
  below bench spread that no query count shows: a scratch probe, median of N repeats, the
  threshold in the Proof), or the repo benches
  [bench_plan_cache.py][bench-plan-cache] (plan cache warm vs cleared: cold clears the plan cache
  and the document-key memo), [bench_optimizer_walk.py][bench-optimizer-walk] (the walk alone),
  [bench_nested_fetch.py][bench-nested-fetch] (nested-connection strategies, w/ `--cell pg` in the
  role's own copy and database; `--sqlite-smoke` figures never compare to Postgres ones), each w/
  `--json`;
- import time: [importtime_report.py][importtime-report] `--rounds 5 --json <scratch>/...`, each
  module's minimum across the rounds, never a single `python -X importtime` reading.

A timing comparison on a shared machine interleaves its runs (before, after, before, after, the
same count each) and compares medians; two back-to-back batches measure the machine's drift.

The benches and `count_queries.py` bootstrap Django through [_bench_common.py][bench-common] and
print its provenance header: package path, database `NAME` (the in-memory SQLite name for every
instrument but the Postgres nested fetch), a content digest of the package and the blob ids of the
instrument scripts; `importtime_report.py` prints the package path, digest and instrument ids but
no database (it never opens one), settings or version lines. Two figures compare only when the
digest they claim to measure and every instrument id match; a figure w/o that header is not a
number.

Record carries: `Path class: hot | cold` w/ the reason (which caller runs it per what); the
instrument; before; after; delta; the permanent test that pins the shape (query count at two
cardinalities + absolute, or, when no test can pin it, the bench delta, which Worker-0 records
under the plan's `## Bench baseline` from Worker-2's report).

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

Instrument: the trace (`rg` for callers, importers, registrations, tests, docs; `check_citations.py
--cited-by <path>::<Symbol>` for every standing doc and code comment citing a symbol a move would
rename); a workspace probe for any behavior the reader is unsure of (the error policy masks a resolver's
exception as `An unexpected error occurred`; `-o log_cli=true --log-cli-level=ERROR` on the
pytest command shows the real one); for a suspected defect, HUNT's
evidence record (the workspace run id, whose header carries copy, package `__file__` and database
`NAME`; command, digests, collected/executed counts, reach assertion, positive control); for
suspected duplication, DRY's finding record (contract + variation, sites + roles, challenges w/
counts, owner + lifetime, migration, behavioral proof, structural gate).

Record carries: the owner it should live at and why; the contract source cited; for a defect the
HUNT fields (Defect, Evidence, Impact, Severity w/ factors, Proof); for duplication the DRY
fields and the negative control its gate passes.

### Comments

A review pass grades every docstring and comment in the target and in its own test modules
(those named for it, graded whole), plus the prose any other test module holds about the target's
symbols; stale prose about them in another package module is a lead for that module's item, in the
report as `Routed: <path::Symbol> - <why>`, which Worker-0 carries into that item's dispatch or
`## Decisions` when it is out of scope. A verify pass
grades what the item-scoped diff wrote or moved, plus any docstring or comment in a touched
symbol the change made false. Pre-existing prose elsewhere in a file the diff touches is not
graded. Each is one of:

- **true** — matches the body and its callers today;
- **stale** — described a body that has since changed (the worst grade: it misleads);
- **duplicates the code** — says what the next line says; delete it;
- **process provenance** — names a spec (a pointer to a spec Decision is kept, START.md
  "Style"; a bare `(spec-NNN)` is provenance), card, round, worker, review, "fix for", "legacy",
  "moved from", "now", "no longer" ([AGENTS.md][agents]); delete or rewrite as the present-tense
  rule.

First lines, by kind:

- **Module** (and a folder's `__init__.py`) — names what the module is, as a description, not an
  imperative ("Shared connection contracts for ...", "``DjangoSchema`` - the schema whose ...").
  It is the module's row in [docs/TREE.md][tree], so it must satisfy
  [build_tree_md.py][build-tree-md]: one physical line, exactly one sentence, ending `.`, no
  `e.g.` / `i.e.`. Provenance here is doubly wrong: it renders into TREE.md as a description.
- **Function, method, class** — imperative for a function or method ("Return ...", "Build ..."),
  a description for a class; ruff's Google pydocstyle convention leaves mood (D401) unchecked, so
  the reviewer is the gate.

A module first-line edit is a TREE.md edit, and that holds for test modules too (the `tests/` and
fakeshop test trees render there, each module in two rows): Worker-2 runs `uv run python scripts/build_tree_md.py` in the
same change, since nothing regenerates it locally and CI's `build_tree_md.py --check` goes red on
a stale file. The render takes its rows from the files git tracks (a new module renders once it
is `git add`-ed) but each row's text from the working tree, so Worker-2 attributes every TREE.md
hunk like any other: a row it did not change is concurrent work.

Also: a public symbol w/o a docstring; a docstring restating the signature or the type hints; "we"
/ "you" / "I"; a test docstring beginning "Tests that" or "Ensures" instead of stating the expected
behavior; a source reference by line number or by a name that no longer exists; a stated reason for
a design that the body contradicts (DRY principle 10: wrong stated reason is worse than none); an
intentional separation or a rejected consolidation that is NOT recorded at the owner when the trace
shows it should be.

Instrument: reading each docstring against its body and against one real caller;
`uv run python scripts/build_tree_md.py --list-docstrings <path>` for the module first line (flags
each rule violation by name, needs no Django);
`uv run python scripts/check_citations.py --paths <path> --substrings --json` for every
`path::Symbol` citation in the file (each w/ `resolved`, its target and candidates), and
`--cited-by <path>::<Symbol>` for every citer of a symbol the item renames; the Comments census of
[review_inspect.py][review-inspect] and
`rg -n -i 'spec-|card|round|worker|legacy|moved from|no longer|previously|\bnow\b|fix for' <path>`
as orientation for provenance (a hit is a lead, the grade is the finding). The verifier reads the
item's prose changes w/ the command below, one `--path` per file in the item-scoped diff so
concurrent edits stay out; a prose hunk marked `[code changed too]` changed code beside the prose:

```shell
uv run python scripts/review_changed_python_diffs_against_head.py <ITEM_BASELINE> \
    --against worktree --prose --include-tests --include-init --path <each item path> \
    --output-dir <root>/verify-comments-<n>/diff
```

Record carries: the symbol; the grade; the text before; the text after. Text after is the
reviewer's proposal; Worker-2 may improve it and the verifier grades what landed, the whole
docstring the changed line sits in. A prose-only change proves it moved no code w/
`uv run python scripts/review_inspect.py --code-digest <ITEM_BASELINE>:<path> <path>` (exit 0,
two equal digests; exit 1 when code moved; START.md "Instruments that lie" names this inverse
proof), and owes nothing else:
no before / after, no permanent test, no failability. On a file another axis's finding also changed
in code, the digest compares the live file against a reconstruction under `<root>/<role>/`:
`ITEM_BASELINE`'s text plus only those code hunks.

## Severity

By consequence, across all axes:

- **High** — correctness, security, data isolation or public-contract failure; a per-row or N+1
  query on a hot path; a stale docstring on a public symbol (exported through an `__all__`, or
  documented in [docs/README.md][docs-readme] or [docs/GLOSSARY.md][glossary]) that states the
  wrong contract.
- **Medium** — a measured cost on a hot path without N+1; a rule enforced at the wrong layer; a
  stale comment on internal code.
- **Low** — a bounded clarity or maintainability improvement; a cold-path cost; a comment that
  duplicates its code.

Every High and Medium finding is implemented unless rejected in the record w/ a trigger. Low
findings are implemented when they ride on a file Worker-2 is already changing for a higher
finding, else recorded `deferred` w/ the reason and left visible in `## Outcomes`. Style
preference, and speculative risk w/o a reachable input, are not findings.

## Plan

One plan per release, `docs/review/review-<release>.md` (`0.0.15` → `review-0_0_15.md`), release
read from the package `__version__`. Existing plan for the release → resume: validate `Status:`,
`Run:` and `## Cycle baseline` against the tree (a `Status:` line alone is never trusted), continue
under `## Run <release> <date>-<n>`, never replace (`review_plan.py resume` appends that heading,
`Scope:`, a computed `Drift:` line and items for inventory the plan lacks; it never rewrites a
line; an item it carries w/ `Status: out-of-scope` is set `pending` by Worker-0). Worker-0 alone
edits the plan; nobody erases prior lines. A plan w/o `## Cycle baseline` predates this flow: its
ticks are history and every item is re-verified under the new run.

[review_plan.py][review-plan] owns the plan's shape and inventory; Worker-0 runs it from the repo
root in the shared tree (it needs git) and never hand-builds an inventory:

```shell
uv run python scripts/review_plan.py plan --changed
uv run python scripts/review_plan.py plan --scope <folder or module> ...
uv run python scripts/review_plan.py resume --plan docs/review/review-<release>.md --changed
uv run python scripts/review_plan.py reconcile --plan docs/review/review-<release>.md
uv run python scripts/review_plan.py scope --json
```

The run's scope: the entry command's `scope:` entries, each passed as `--scope` to `plan` or
`resume`, else `--changed`. `--changed` works the release's own changes: every module whose
committed content changed since the latest tag (`--since <rev>` overrides), the folder integration
item of the folder each sits in, the folder item of a changed folder `__init__.py`, the project
item for a changed package-root `__init__.py`. Dirty and untracked paths are concurrent work, never
scope. Each resumed run recomputes it; an item the plan already holds is carried, never re-added.
When nothing changed, `plan` writes `Status: complete` w/ a `Nothing in scope:` line, every item
out of scope and no gate, `resume` appends the run w/ that line, both print `nothing in scope`, and
Worker-0 reports and stops. `scope` lists the same changes for reading: committed w/ their `HEAD`
blob ids, dirty or untracked (concurrent work), renames, each path w/ the item covering it (a
module its file item, a folder's `__init__.py` that folder's integration item, the package-root
`__init__.py` the project item). `plan` writes the plan: one file item per module minus
`__init__.py`, one folder item per package folder carrying that folder's `__init__.py` on its
`Init files:` line, the project item carrying the package-root `__init__.py`, the final gate, and
`## Out of scope this run` for everything the scope leaves out. `--scope` also takes a folder's
`__init__.py` (that folder item) or the package-root `__init__.py` (the project item, otherwise in
scope only for the whole package). On an existing plan `plan` refuses and names `resume`; `--force`
replaces a plan only while its `## Owned changes` and `## Outcomes` hold nothing beyond the
generated text. `reconcile` is read-only and exits 1 when the plan and the inventory disagree: a
`.py` w/o an item, an item whose file is gone or renamed, a folder w/o an item, an `__init__.py`
missing from, misplaced on or gone from an `Init files:` line, an item whose status needs artifacts
that are missing. It reports untracked `.py` files too, while `plan` and `resume` itemize tracked
files only: a new module gets its item once it is `git add`-ed, and an untracked one no ledger row
names is concurrent work. It checks no fingerprint and no `HEAD` drift (it reads `HEAD` only to
spot renames); those are Worker-0's checks below.

Plan header: `Status: planned | in-progress | complete | partial (<scope>) | blocked`;
`Mode: autonomous | pause-after-each-item`; `Run: <release> <date>-<n>` (repeated on every
artifact); `Scope: package | <folder or path list> | changed since <rev> (<sha>)` (the entry
command's scope, package-relative as `review_plan.py` normalizes it: `optimizer/`; or the
`--changed` rule); `## Cycle baseline`; `## Bench baseline`; `## How to work one item`; one file
item per inventory line; one folder integration item per package folder; the project integration
item; the final gate; `## Decisions` (maintainer decisions the run surfaced: ruff rules to enable,
trade-offs, contracts nobody could cite); `## Owned changes` (ledger); `## Outcomes` (closeout).

Item shape:

```text
- [ ] optimizer/walker.py
    - Status: pending
    - Path class: <hot | cold, from the Performance record; blank until reviewed>
    - Artifacts: rev-optimizer__walker.md, rev-optimizer__walker.performance.md, rev-optimizer__walker.mechanics.md, rev-optimizer__walker.comments.md
```

`review_plan.py` writes that shape and `reconcile` parses it; an item added by hand copies it
exactly (one comma list of artifact names).

A run scoped below the whole plan (`Scope:` names folders or paths) works only its scope, sets
`Status: partial (<scope>)` at closeout, and closes w/ an `## Outcomes` "Scope of this run"
section naming what ran and what did not; an unticked box never reads as examined. Scoped runs
are the normal mode: a full pass over the package is seven dispatches per file across a hundred
files, and a release rarely changes more than a few folders.

Before a run's first dispatch, and again before the final gate, Worker-0 runs `reconcile` and acts
on every line it reports: `.py` added → new item; removed / renamed → item closed w/ note,
artifacts re-keyed. The one line it leaves standing is an untracked `.py` no ledger row names: that
is concurrent work, recorded on a `Drift:` line, and `reconcile` keeps exiting 1 for it; the gate's
"inventory re-reconciled" means no line but those. Worker-0 then re-hashes every fingerprint
recorded on an open or ticked item (`git hash-object <path>`); an item whose fingerprints no longer
match is reopened, whatever its checkbox says.

## Baseline and ownership

Cycle entry: Worker-0 appends `CYCLE_BASELINE=$(git stash create)` (empty → the sha of
`git rev-parse HEAD`, never the word `HEAD`, which would move) + untracked
files under the package to `## Cycle baseline`, once. Everything dirty there = concurrent work:
never edited, reverted, tidied. The block is never rewritten; fingerprints, not the block, decide
staleness. When `HEAD` moves or `git status --short` names a path the block lacks, Worker-0
appends one `Drift: <date> HEAD <old>..<new>; dirty + <paths>` line under the current run heading
(the header `Run:` line on the first run, `## Run <release> <date>-<n>` afterwards), continuation
lines indented two spaces. `resume` writes a run's first `Drift:` line; drift found later in the
run is appended by hand.

Per item: `uv run python scripts/workspace.py baseline review/<item>` prints `ITEM_BASELINE`
(`git stash create`; empty → the `git rev-parse HEAD` sha, since an empty value would send the diff
tooling back to the latest tag) and takes the item's `before` copy ("Workspace"); Worker-0 records
it + the same listings as `Item baseline:` fields on the plan item. Item-scoped diff =
`git diff <item baseline> -- <paths touched>` PLUS every file the item added
(`git diff --no-index /dev/null <new>`).

Each item landing tracked edits or new files appends to `## Owned changes`: path, item, axis,
symbols changed. A later item may build on a ledgered path. Attribute by content, never by dirty
status: before editing a dirty path, Worker-2 diffs vs `git show HEAD:<path>` and matches every
hunk to the ledger, the cycle baseline, or an earlier pass of this item (the item-scoped diff
Worker-0 wrote to scratch); a hunk in none = external edit → stop, report to Worker-0, who
reconciles w/ Rio. Same stop when the item-scoped diff shows hunks the worker didn't make.

A test failing before the item's first edit is pre-existing: Worker-2 reproduces it in the item's
`before` copy and records it under the artifact's `## Defects` w/ the failing command; one Worker-0
meets outside a pass (at the gate, or in a check) goes to the plan's `## Decisions` instead, since
Worker-0 writes no artifact section. Either way Worker-0 routes it to Rio. It blocks the gate row,
never the item.

### Bench baseline

Performance verdicts need a per-release reference. At cycle entry Worker-0 runs the four commands
`plan` writes under `## Bench baseline` w/ `<phase>` = `baseline`, each through
`workspace.py run review/bench/baseline`, recording command, run id, provenance header and figures:
[bench_plan_cache.py][bench-plan-cache], [bench_optimizer_walk.py][bench-optimizer-walk],
[bench_nested_fetch.py][bench-nested-fetch] (`--cell pg`) and
[importtime_report.py][importtime-report] `--rounds 5`, each w/ `--json` into scratch. The package
digest in each header is the baseline's binding; `CYCLE_BASELINE` is recorded beside it. The final
gate reruns them w/ `<phase>` = `gate` (a copy synced then) and records the delta; a gate figure
whose instrument ids differ from the baseline's compares nothing. A Performance record cites the
baseline figure it moves; a file item whose change moves no bench figure pins its claim w/ a
query-count test instead. Worker-0 then runs `workspace.py release review/bench`, since items need
the pool.

## Workspace

A scratch directory is not a sandbox: a probe under `docs/review/temp-tests/` still imports the
live package and opens the tracked `examples/fakeshop/db.sqlite3`. Every measurement, every
destructive or source-mutating probe, every bench run goes through [workspace.py][workspace],
which owns the copies: building, syncing, virtualenv, databases, provenance, cleanup. A worker
knows one thing, the address its dispatch names:

```shell
uv run python scripts/workspace.py run review/<item>/<role> [--cell sharded|pg] [--fresh] -- <cmd>
uv run python scripts/workspace.py prove review/<item>/<role> <manifest.json>
uv run python scripts/workspace.py path review/<item>/<role>
```

`<item>` is the target path (`optimizer/walker.py`), a folder item's folder (`optimizer`), or
`project`; `<role>` is `before` (taken by Worker-0's `baseline`, never edited), `performance`,
`mechanics` or `comments` (reviewers), `implement` (Worker-2), `verify-<axis>-<n>` (verifiers of
pass `<n>`). `<command>` is what follows `uv run` (`pytest <node> --no-cov`,
`python scripts/count_queries.py ...`); its relative paths resolve inside the copy. An address's
first run syncs a copy from the shared tree as it stands; later runs reuse that copy as it stands,
edits included; `--fresh` resyncs it. `path` prints the copy for reading or editing, syncing it first when
unbound: a verifier reverting a hunk edits there, never in the shared tree. Reverse-apply a diff
inside a copy w/ `patch -R -p1 -d <copy> < <diff>`; `git apply` run from inside a checkout
resolves paths from that checkout's root and skips a hunk it cannot place w/o failing.

Every run prints a provenance header on stderr: run id, copy, the package file it imports and its
digest, cell and every database `NAME`, whether the copy is `fresh` or `modified`, whether the
shared tree moved since the sync. The tool refuses to run (exit 125) when the package, the
interpreter or a database resolves outside the copy, so a measurement cannot read the wrong
tree. A record cites the run id; the run's full output stays in the flow's evidence folder, and
`workspace.py audit <record>` checks every id a record cites: a log entry exists and its package
and databases lay in its copy. It prints each run's address and `fresh | modified`; whether that
address is the record's own is Worker-0's reading. A copy holds no `.git`, so provenance
comes from the header's digests, never a `HEAD` sha, and a full-suite run in a worker copy fails
the two git-census rows of `tests/test_ci_governance.py` by construction; only the gate copy
carries an index. `prove` runs `scripts/prove_failability.py`
in its workspace form (`--workspace` = the copy, `--scratch-root` and `--json` in the evidence
folder), so a proof never touches the shared tree and parallel verifiers never share pristine
copies.

Reviewers run in a copy of the tree as it stands. Worker-2 measures "before" in `before` and
"after" in `implement` w/ `--fresh` after its own edits. A verifier's address is new each pass, so
its first run syncs a copy of the exact change. Promotion = Worker-2 applying the change to the
shared tree by hand, then the focused permanent test there. No branches, no shared-tree restores.

Worker-0 alone manages the pool: `baseline` before the item's first edit, `release review/<item>
--keep before` between phases so the next phase's copies fit, `release review/<item>` when the
item closes, `gc review` at closeout. Workers never clean up.

Item scratch root: `docs/review/temp-tests/<stem>/`, untracked, `<stem>` the artifact name w/o
`rev-` and `.md` (`optimizer__walker`); each pass writes only under `<root>/<role>/` (its address's
last segment), and Worker-0 writes the item-scoped diff to `<root>/diff/`. Copies exclude
`temp-tests/`, so a scratch source is kept there. A probe script runs by its absolute path
(`workspace.py run <address> -- python <root>/<role>/probe.py`), which edits no copy; a scratch
pytest module needs the conftest and fixtures of the tree it probes, so a copy of it goes under
the matching `tests/` subfolder of the copy (`workspace.py path`), never while a run in that copy
is collecting. A `--json` or other output path a copy command writes is absolute, under
`<root>/<role>/`. Worker-0 removes an item's scratch only after the item is `verified` or
`blocked`.

## Cycle per file item

```text
Worker-0: ITEM_BASELINE, skeleton artifact, dispatch
    ├─ Worker-1 · Performance ─┐
    ├─ Worker-1 · Mechanics   ─┤  parallel, read-only, each writes rev-<path>.<axis>.md
    └─ Worker-1 · Comments    ─┘
Worker-0: mechanical checks on every record → Status: ready-for-implementation
Worker-2: implements axis by axis, Performance → Mechanics → Comments
Worker-0: mechanical checks on the report → Status: ready-for-verification/<n>
    ├─ Worker-1 · Performance ─┐  parallel, fresh agent + workspace each, from its record
    └─ Worker-1 · Mechanics   ─┘
    then Worker-1 · Comments    last, so it grades the final text
Worker-0: all three axes verified → ledger, tick, cleanup, advance
```

### Worker-0 dispatches

Runs `workspace.py baseline review/<item>` and records `ITEM_BASELINE`; writes the skeleton
`rev-<path>.md` (header, `Status: reviewing`, `Run:`, `Path class:` blank) and nothing else in it;
spawns three fresh Worker-1s at once, each w/ its axis, the target, the plan path, run id, both
baselines, the ledger, its axis record path, its address `review/<item>/<axis>`, the item scratch
root, required reading. Every Worker-1 reads the plan and the other axes' records when they exist;
edits only its own axis record.

### Worker-1 reviews

Reads the whole live target, then traces in and out until the contracts are clear: who calls,
imports, registers, wraps, configures it; which state, lifecycle, settings, ORM, cache or framework
hook it relies on; how representative input becomes output, error, queries, persistent state; which
tests and public docs promise its behavior. [review_inspect.py][review-inspect] gives the
orientation every axis starts from: per-symbol `path::Symbol` cites and blob ids, performance
leads, the Comments census. It is a lead list, never a finding:

```shell
uv run python scripts/review_inspect.py <path> --output-dir <root>/<axis>/inspect \
    --json <root>/<axis>/<module stem>.json
```

Then reads for its axis as "The three axes" describes, discharging every list entry w/ a finding, a
`none` w/ the reason, or a rejection w/ its trigger.

A finding that belongs to another axis goes in the reviewer's OWN record under
`## Cross-axis (for <axis>)`, w/ every common field; Worker-2 implements it w/ that axis, and that
axis's verifier runs its Proof and grades it like one of its own. A finding that spans axes (a
consolidation that also removes a query) lives at the axis that owns the proof, cited from the
other.

Each finding record:

- **Observation** — what is wrong or improvable, `path::Symbol` for every site.
- **Evidence** — the trace, probe, measurement or contract source; for a measurement its
  workspace run id ("Workspace"); for a defect the HUNT evidence record; for duplication the DRY
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
  line verbatim (a static command, `rg`, `git`, `check_citations.py`, `--code-digest`, in the
  shared tree; anything that imports the package or opens a database at the verify address; a
  Comments Proof pairs its static command w/ the grade the text must earn), so a proof that
  cannot be run is not a proof: self-contained (no shell variable
  defined elsewhere in the record), `<n>` for the verify pass number in an address or path, the
  node count the run must report (`3 passed`), a test that does not exist yet named in plain text
  (`test_mixed_case_field in tests/optimizer/test_extension.py`), since `path::Symbol` to a missing
  symbol fails `check_citations.py`. A failability Proof names the rows that must fail; the
  verifier's manifest declares the exact set the revert fails, and its Verification says why each
  row beyond the Proof's fails.
- **Freshness** — `git hash-object` of every file inspected, including files excluded from the
  finding on the strength of their body.

Plus the axis-specific fields. Rejected candidates are recorded w/ the contract difference or
rule reason and the trigger that would reopen them. Zero findings on an axis is a legitimate
result when every list entry is discharged and the strongest rejections carry reasons. Worker-1
closes its record `Status: findings-recorded` (or `no-findings`) and reports to Worker-0: findings
by severity, rejections, defects, cells unverified, scratch paths, fingerprints.

### Worker-0 checks the records

Mechanically, before Worker-2 reads anything:

| Record shows | Verdict |
|---|---|
| a measurement w/o a workspace run id | `invalid: instrument` |
| a run id `workspace.py audit <record>` fails (no log entry, package or database outside its copy) | `invalid: wrong tree` |
| a Performance finding w/o `Path class` or w/o a before number | back to that Worker-1 |
| a finding w/o a runnable Proof line | back to that Worker-1 |
| a defect w/o a contract row or a reachable input | `rejected as defect`; may stand as Mechanics |
| a Recommendation or text after that would land a line-number citation in code, tests or a standing doc, or a symbol `check_citations.py --paths <record>` cannot resolve (checked on the review pass; a symbol the item later deletes stays in that text as written) | back to that Worker-1 |
| a list entry neither discharged nor rejected | back to that Worker-1 |

Twice back on the same row → `blocked` for Rio. All three records pass → Worker-0 copies
`Path class` into the plan item and the artifact header, sets the artifact
`Status: ready-for-implementation`, runs `workspace.py release review/<item> --keep before`, sets
`Status: implementing` and spawns a fresh Worker-2 w/ the target, the main artifact, all three
records, the plan, run id, both baselines, the ledger, its address `review/<item>/implement`, the
`before` address, the item scratch root.

### Worker-2 implements

Reads all three records, then the target and its neighbours until it can hold the whole change in
mind. Implements in axis order: Performance first because it may restructure; Mechanics next
because a rule moves to its owner on the code as Performance left it; Comments last so the prose
describes the result. A later axis's finding may be discharged by an earlier axis's change;
Worker-2 records that in its `## Implementation (Worker-2)` instead of applying it twice.

Per finding: attribute hunks on every dirty path first ("Baseline and ownership"); measure "before"
in the `before` copy where the record's Proof asks for a number; apply the change to the shared
tree by hand; measure "after" in `implement` w/ `--fresh`; write the permanent test at the
strongest reachable tier ([AGENTS.md][agents]: live GraphQL usage against fakeshop first, then
example tests, then package tests); run it focused w/ `--no-cov` (node ids or a module; `-k` and `-n0` may narrow it, no
other flag). A live-tier test needing a
fakeshop fixture that does not exist lands at the strongest existing tier and Worker-2 names the
missing fixture in its report, which Worker-0 records under `## Decisions`; never a new example
model inside an item. Every gate a finding relies on must be shown able to fail
(`workspace.py prove`).

Worker-2 may dispute a finding: it records `disputed: <reason>` against the finding in its
`## Implementation (Worker-2)`, implements nothing for it, and the owning verifier judges. It may
improve a Recommendation's shape or text when the trace shows a better one, recording there what it
did instead and why; the Proof line still governs. It never silently skips a finding and never
edits an axis record.

After the last axis, on the paths touched (explicit paths, never `.`, which rewrites files no item
owns): `uv run ruff check --fix <paths>`, then
`uv run python scripts/check_trailing_commas.py <paths>`, then `uv run ruff format <paths>` last,
until `uv run ruff check <paths>`, `uv run ruff format --check <paths>` and
`uv run python scripts/check_trailing_commas.py --check <paths>` pass, and
`uv run python scripts/check_citations.py --check` passes on the whole tree (a rename rots
citations in files the item never opened). These are the CI lint gates; ruff alone passes a file
the layout gate rejects. Then appends `## Implementation (Worker-2)` to `rev-<path>.md`: per axis,
per finding, what landed (`implemented | discharged by <finding> | disputed | deferred`), files
changed and why each moved, before / after numbers w/ their run ids, permanent tests and their
focused results, failability proofs, formatter result, every scratch path and run id, fingerprints
of every file touched or read for the change, and the `## Owned changes` rows it proposes (path,
item, axis, symbols changed). Reports to Worker-0.

### Worker-0 checks the report

The evidence table again, on the report: every High and Medium finding has a disposition; every
number has a run id `audit` binds; every changed path is attributed; the lint gates passed; the
item-scoped diff contains no hunk the report does not explain. Failure → back to Worker-2 w/ the
row named (twice → `blocked`). Pass → `Status: ready-for-verification/<n>`, item-scoped diff
written to scratch, `release review/<item> --keep before`, three fresh Worker-1s dispatched on the
same axes at addresses `review/<item>/verify-<axis>-<n>`, each from its axis record and its
handoffs, Performance and Mechanics at once, Comments after those two report.

### Worker-1 verifies

Expectation-first: the Proof line written before the edit is the expectation. Each verifier, on
its own axis, first confirms the shared tree still carries the change it was sent to grade:
`git diff <ITEM_BASELINE> -- <paths>` hashes equal to `<root>/diff/pass-<n>.diff` (a mismatch →
report to Worker-0, grade nothing). Then it:

1. Runs every Proof line in its record, those the other records hold for its axis under
   `## Cross-axis (for <axis>)`, and on a re-pass the ones earlier passes verified, in its own
   copy, and records the result beside it; reproduces
   every number Worker-2 reported for its axis from the recorded command; a Performance verifier
   also confirms the "before" figure against the bench baseline or a read-only run at the item's
   `before` address (never `--fresh`, never edited).
2. Re-reads the WHOLE item-scoped diff through its axis, not only its own findings: the Performance
   verifier measures a Mechanics move that touched a hot path; the Mechanics verifier checks a
   Performance rewrite or a consolidation preserved observable behavior (temporarily revert the
   production hunk inside its copy and show the pre-fix behavior was the worse one); the Comments
   verifier grades every docstring and comment Worker-2 wrote or moved.
3. Attacks the change on its axis: the other cardinality, the other flavor, the other cell, the
   caller Worker-2 did not name. A passing attack is recorded w/ its run id and owes nothing; a
   failing one is a new finding.
4. Judges every `disputed` finding on its reason; a standing disagreement is `blocked` at once w/
   both positions recorded and a `Blocked:` line in the report, whatever the record's `Status:`,
   never a third pass to break it.
5. Confirms permanent tests exercise real usage at the mandated tier and fail w/o the change
   (Mechanics and Performance verifiers), and that the item-scoped diff carries no process
   provenance, no line-number citation, no `we` (Comments verifier).
6. Runs the lint gates Worker-2 ran (ruff check, ruff format `--check`,
   `check_trailing_commas.py --check` on the touched paths, `check_citations.py --check` on the
   tree) (Mechanics verifier); a failure is `revision-needed`.

Appends `## Verification (<axis>)` to its record w/ the checks and results, sets the record
`Status: verified` or `Status: revision-needed` w/ concrete named gaps, reports to Worker-0.
Verifiers never edit production code or tests; a verifier that finds a new problem on its axis
records it under `## Findings` as a new finding labelled `verify <n>` w/ a Proof line and returns
the record `revision-needed`; one on another axis is a named gap Worker-0 routes to that axis's
next verifier, which makes it a `verify <n>` finding in its own record when it rides on the
item's change (the change made it false, or it sits in a symbol the item touched). A gap outside
that reach, a cost the change newly reaches outside the item's fence included, is no revision: it
goes to the plan's `## Decisions` w/ a named owner.

### Worker-0 closes the item

Any axis `revision-needed` → the artifact `Status: revision-needed`, a fresh Worker-2 from the
artifact and its handoffs, then fresh verifiers on the axes that failed and on any axis a verifier
named a gap on (Comments too whenever the re-pass touches prose; a prose-only re-pass owes
Comments alone, its `--code-digest` identity the evidence the other axes stand); two failed
re-passes → `blocked` for Rio. All three `verified` → ledger rows (Worker-2's proposal, checked against the item-scoped
diff), `Result:` and `Verification:` lines on the plan item, tick, remove item scratch by explicit
path, `workspace.py release review/<item>`, advance (`autonomous`) or report and wait
(`pause-after-each-item`). Worker-0 never regrades a verifier.

Plan item result lines:

```text
Result: <n> findings implemented (<H>/<M>/<L>), <n> rejected, <n> deferred. Files: <paths>.
Verification: Passed. Performance <numbers or none>; Mechanics; Comments.
Cleanup: Removed <item scratch paths>; copies released; unrelated work preserved.
Blocked: <condition and the decision Rio must make>.
```

## Artifacts

Four per file item, all under `docs/review/`, untracked until Rio commits them, protected by
[AGENTS.md][agents] rule 22 from bulk deletion. Names take the source path relative to the
package, `/` → `__`, `.py` dropped: `optimizer/walker.py` → `rev-optimizer__walker.md` +
`rev-optimizer__walker.performance.md`, `.mechanics.md`, `.comments.md`. Folder
pass `rev-<folder>.md`; project pass `rev-project.md`.

Main artifact, written by Worker-0 and Worker-2 only:

```text
# Review: `path/to/target.py`

Status: reviewing | ready-for-implementation | implementing | ready-for-verification/<n> |
        revision-needed | verified | blocked
Run: <release> <date>-<n>
Path class: hot | cold — <reason>

## Implementation (Worker-2)

Per axis, per finding: disposition, files, numbers, tests, proofs, formatter result, paths,
fingerprints. `Handoff:` last.

## Defects

Correctness defects fixed in this item (HUNT fields) or blocked for Rio; pre-existing failures.

## Pending execution

`proof: <command>` for a proof only the final gate can run; `gate: <command>` for a witness that
routes nowhere. Absent when none.

## Iterations

Created by the first re-pass; later passes append; nobody erases prior reasoning.
```

Axis record, written by its Worker-1 only:

```text
# Review · <Axis>: `path/to/target.py`

Status: reviewing | findings-recorded | no-findings | verified | revision-needed
Run: <release> <date>-<n>

Baselines: CYCLE_BASELINE=<sha> ITEM_BASELINE=<sha>

## Trace

What was read, callers followed, cells covered; fingerprints (a finding's Freshness then lists
only files beyond these).

## Findings

### High / ### Medium / ### Low

One record each (common fields + axis fields). `None.` under an empty severity.

## Rejected

Each w/ the reason and the trigger that reopens it.

## Cross-axis (for <axis>)

Only when there are any: findings this reviewer made on another axis, one heading per receiving
axis; that axis's verifier grades them.

## Verification (<Axis>)

Proof results, numbers reproduced, whole-diff reading, attacks, disputes judged, verdict. A later
pass appends `## Verification (<Axis>) pass <n>`.

Each pass ends w/ its `Handoff:` paragraph.
```

No inventories, copied tool output, empty placeholders. Raw `path:NN` is tolerated in these
per-cycle artifacts only; everything that lands in code, tests or standing docs cites
`path::Symbol`.

## Integration passes

Folder pass after every file item in the folder is verified: one Worker-1 per axis again, on the
folder as one component, looking for what no file shows alone: a hot path that crosses the folder
(Performance), a rule split across siblings or a flavor missing a guard its siblings have
(Mechanics), module docstrings that disagree w/ each other about who owns what (Comments). It
also reviews the folder's own `__init__.py`, named on the item's `Init files:` line. Same cycle,
same records, `rev-<folder>.md`.

Project pass after every folder: public exports and the package-root `__init__.py`, import-time
cost of the package as a whole against the bench baseline, end-to-end lifecycle, gaps between
package behavior and its tests, examples and docs. Re-inventory first. `rev-project.md`.

## Final gate and closeout

Every item but the gate verified or `blocked` + inventory re-reconciled → Worker-0 runs the gate:
`uv run python scripts/workspace.py gate review`, every `## Pending execution` command from every
artifact as listed, and the bench baseline commands w/ `<phase>` = `gate`, delta recorded. `gate`
syncs a gate copy carrying its own git index of `HEAD` (the suite's CI-governance tests ask git for
the committable file list) and runs CI's jobs: the `lint` job's commands in the workflow's order
(`workspace.py`'s `LINT_COMMANDS`, held to `django.yml` by a test), then the suite three times: the
full default suite
(package coverage 100%); the `sharded` cell w/o coverage, since sharded-only tests skip by default
and the default run owns the floor; the `pg` cell, only the database-touching tests, on the gate
copy's own database. It writes `gate-<run id>.json` to the evidence folder, bound to
`git stash create` at gate time, the blob ids of `pyproject.toml` and `uv.lock` and each suite's
cell, and prints per suite the run id, exit, summary and coverage lines; a cell that cannot run is
`unverified` w/ the reason.

Record, per suite, failures, coverage, skips, xfails, collected/selected counts and the cell. A
change to package source, tests, fixtures, pytest or coverage config, dependencies or mode
invalidates it; prose does not. Failure in a path an item touched, or of a `proof:` command → that
item back to Worker-2 and its verifiers; a failing `gate:` command reopens no item; a failure
reproduced against `git show HEAD:` of its test and target → pre-existing, `## Decisions`, gate
row `blocked` for Rio; environment failure → recorded precisely, `blocked`.

Worker-0 fills `## Outcomes` BEFORE `gc`: an item's scratch is gone once it closes, but its
plan fields and the evidence folder (run logs, proofs, gate results) stand until `gc`. Per item: findings per axis w/ severity and
disposition; every number before / after w/ its command; owner moves; consolidations w/ their
challenge counts; comments regraded; defects fixed w/ their permanent tests; rejections w/
triggers; deferred Lows. Per run: bench baseline vs gate figures; decisions owed to Rio
(`## Decisions`); cells unverified; blocked items; net source change vs cycle baseline; gate
record; concurrent work untouched; "Scope of this run" for a scoped run. Then `Status: complete`
(`partial (<scope>)`; `blocked` w/ the decision Rio owes). Remove only this run's
`docs/review/temp-tests/<stem>/` dirs, bar a sensitive `blocked` item's evidence, and
`docs/review/worker-memory/` contents, by explicit path, then
`uv run python scripts/workspace.py gc review`: copies, gate copy, evidence, databases, and the
Postgres container once no flow holds a database. Never recursively clear `docs/review/`; never
remove `REVIEW.md`, the role files, the plan, or any `rev-*.md`. Do not commit.

Under [MUSE.md][muse], a REVIEW Worker-0 running beside a hunt or DRY Worker-0 states the
production files its open items own in the sibling prompts, and honours theirs: a path another
flow's ledger names is concurrent work here. Sibling flows share one Postgres container, each copy
in its own database; `gc` stops it only once no flow holds a database, so one flow's closeout
never pulls it from under another.

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
[tree]: ../TREE.md
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
[build-tree-md]: ../../scripts/build_tree_md.py
[check-citations]: ../../scripts/check_citations.py
[check-trailing-commas]: ../../scripts/check_trailing_commas.py
[clean-up]: ../../scripts/clean_up.py
[count-queries]: ../../scripts/count_queries.py
[importtime-report]: ../../scripts/importtime_report.py
[plan-common]: ../../scripts/_plan_common.py
[prove-failability]: ../../scripts/prove_failability.py
[review-diffs]: ../../scripts/review_changed_python_diffs_against_head.py
[review-inspect]: ../../scripts/review_inspect.py
[review-plan]: ../../scripts/review_plan.py
[workspace]: ../../scripts/workspace.py

<!-- .venv/ -->

<!-- External -->
