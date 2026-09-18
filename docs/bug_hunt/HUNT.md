# System-wide bug hunt

Entry: `Execute docs/bug_hunt/HUNT.md (You are Worker-0)`. Worker 0 reads [AGENTS.md][agents] +
[START.md][start], generates or resumes the progress file, then runs the hunt autonomously through
every item, revision, and the final gate until `Status: complete` or a genuine maintainer decision
blocks it. Nothing here self-starts; Rio starts a hunt by that command.

Hunt the current working tree for confirmed defects in `django_strawberry_framework/`. Contracts
are the unit, files are the inventory: every `.py` is an entry point into the live system,
cross-file contracts (pagination, authorization, transaction lifecycle) are scenario items, and the
investigation always crosses files. Fresh hunt: prior build, review, DRY, hunt artifacts and
`pbugs.md` are leads w/ provenance, never expected results.

Three roles, fresh context per item:

- **Worker 0 — coordinator.** Owns the progress file, baselines, dispatch, mechanical acceptance
  checks, scratch cleanup, final gate. Never hunts, never fixes, never grades correctness.
- **Worker 1 — hunter and implementer.** Breaks things inside a disposable workspace, confirms
  defects w/ attributable evidence, implements root-cause fixes + permanent tests in the shared
  tree.
- **Worker 2 — independent verifier.** Derives the expected behavior from the contract BEFORE
  reading Worker 1's diagnosis, reproduces, attacks the fix, judges. Only Worker 2 completes an
  item; Worker 0 never overrides a Worker 2 rejection.

Role files [worker-0.md][worker-0], [worker-1.md][worker-1], [worker-2.md][worker-2] = role delta
only; this doc is canonical.

## Ground rules

- [AGENTS.md][agents] governs safety, test placement, formatting, changelog, commits. Preserve
  concurrent work; a fix crosses files when the invariant does; unrelated cleanup stays out.
- Invoking this flow authorizes the runs it names: a focused permanent test w/ `--no-cov` in the
  shared tree, any run inside a workspace copy, and the final gate `uv run pytest`. Nothing else
  converts into a test run. `FAKESHOP_SHARDED=1` and Postgres cells need Rio's separate word;
  without it a cell is `unverified`, or `inapplicable by construction` when the target's code
  path reaches no database, alias or dialect decision (Worker 1 states the reason, Worker 2
  judges it).
- **The item fences edits, never inspection.** A defect lives where several layers meet, so
  Worker 1 and Worker 2 read and trace wherever the contract leads: upstream callers, downstream
  consumers, sibling flavors, tests at every tier, examples, docs, the installed Django /
  Strawberry / DRF sources in `.venv`, any package folder. Nobody needs permission to open a file
  outside the item; a hunt that stayed inside the target's own module has not been done. Only the
  fix is scoped: the layer owning the broken invariant, its tests, the ledger rows.
- **Confirm before editing.** Warnings, suspicious shapes, shadow markers, missing tests, surviving
  mutants = leads. A defect has evidence a stranger can replay.
- **Contract row first.** Before probing a boundary, record the contract that governs it: boundary,
  failure class, promised wire shape, masking, logging, rollback, absence of unauthorized effects.
  Sources: [docs/README.md][docs-readme] (error policy, mutation envelope, sealed queryset),
  [docs/GLOSSARY.md][glossary] anchors, owner docstrings, existing oracles. The package has no
  blanket "every unhandled exception → `FieldError`" rule: parse/coercion errors, deliberate
  `GraphQLError` rejections incl. authorization denials, mutation validation envelopes, masking
  under `error_policy.py::ErrorPolicy`, transport rejections each have an owner + wire shape. An
  unexpected internal exception is a lead; its Python class alone never justifies a `FieldError`
  conversion, and masking never proves the behavior beneath it correct. A contract nobody can cite
  → `blocked`, Rio decides; never a fix.
- **Property premise before property run.** Every property records the authoritative contract
  citation, valid input domain, transformation, observable, an INDEPENDENT oracle (querying the
  same implementation isn't one), known exceptions. `utils/strings.py::pascal_case` is the
  cautionary case: documented for snake_case input, `"PaymentMethod"` → `"Paymentmethod"` by
  design; an invented idempotence property would have "fixed" it.
- **Coverage ≠ correctness.** 100% lines = each line ran under one expected path. Hunt the missing
  branch, the unhandled shape, the guard that should exist. A new guard needs a test that reaches
  it through real usage; `pragma: no cover` never lands one.
- **Root cause at the owner.** Fix the layer owning the violated contract, never only the observed
  caller. Permanent behavioral test at the strongest reachable tier, same change. Live tier
  needing a fakeshop fixture that doesn't exist (model, relation shape) → test at the strongest
  existing tier + the missing fixture reported as its own `blocked` line for Rio; never a new
  example model inside an item.
- **Severity = impact.** Reachability, actor prerequisites, likelihood, C/I/A impact, blast radius,
  confidence, each stated. No origin floors or caps: a developer-robustness defect and a security
  vulnerability are different categories, yet a fail-open authorization outcome reachable by a
  plausible integration mistake is High. CVSS claimed = vector + rationale supplied. High / Medium
  / Low as in the finding record; style preferences and speculative risks are not bugs.
- **Sensitive findings.** A client-reachable isolation/authorization defect gets the
  [SECURITY.md][security] maintainer path before its reproducer lands in any tracked file: record
  the item `blocked` w/ the defect named abstractly, evidence held in scratch, Rio decides
  disclosure. A card plus a failing test is not a parked vulnerability.
- Only Rio commits, branches, pushes, edits the changelog.

## Progress file

One generated `docs/bug_hunt/bug_hunt-<release>.md` per hunt (`0.0.14` → `bug_hunt-0_0_14.md`) =
plan, progress record, handoff, durable outcome. In-progress file exists → resume it (validate its
run id, baseline commit and `## Cycle baseline` against the tree first; a `Status:` line alone is
never trusted). Else:

```shell
uv run python scripts/bug_hunt.py
```

[scripts/bug_hunt.py][generator]: resolves `HEAD` as the hunt baseline; refreshes only
`docs/shadow/current/` via `scripts/review_historical_package_snapshot_at_commit.py`; records the
run id (`<release>-<HEAD sha>`) and `## Cycle baseline` (`git status --short` at generation: every
dirty/untracked path = concurrent work); reads [dicta.md][dicta] into `## Package questions` (empty
→ explicit "no questions" fallback; questions guide exploration, never define results); writes one
item per non-`__init__.py` live file, the standing `## Scenarios`, the package integration item,
the final gate, an empty `## Owned changes` ledger and `## Outcomes`. Refuses to overwrite without
`--force`; `--target-release` names the file when the version literal is mid-change.

Shadow = orientation fixed at baseline (stripped source + overview per eligible file); live source
is authoritative. A live file w/o a shadow states the applicable reason the generator wrote
(excluded by the `test` path filter, added since baseline, or unexpectedly incomplete); it is still
a full item.

Item shape:

```text
- [ ] path/to/target.py
    - Status: pending
    - Prompt:
        - <target and shadow inputs>
```

Worker 0 alone edits the progress file. Statuses: `pending`, `hunting`, `candidate`,
`fix-implemented`, `revision-needed`, `no-bugs`, `verified`, `inconclusive`, `stale`, `blocked`.
`candidate` = Worker 1 confirmed a defect and is implementing. `inconclusive` = budget exhausted or
evidence missing/empty/timed-out/setup-only; never spelled `no-bugs`. `stale` = a verified item
whose inspected inputs changed; re-verification queued. Nobody erases prior lines; cycles append
`Iteration:` lines. Result lines:

```text
Result: No bugs. Evidence: <workspace, probes, contract rows examined>.
Result: Fixed <severity>. Files changed: <paths>; validation: <commands/results>.
Result: Inconclusive. Missing: <what never ran, and why>.
Verification: Passed. Expected-before-diagnosis: <recorded expectation>. Evidence: <checks>.
Cleanup: Removed <item-owned scratch/workspace paths>; unrelated work preserved.
Blocked: <condition and the decision Rio must make>.
```

## Baseline and ownership

Cycle baseline = the generator's `## Cycle baseline` + `CYCLE_BASELINE=$(git stash create)` (empty
→ `HEAD`) that Worker 0 records at start. Dirty there = concurrent work: never edited, reverted,
tidied, attributed to an item. The block is the entry snapshot, never rewritten or extended;
recorded digests, not the block, decide staleness. When `HEAD` moves or `git status --short`
names a path the block lacks, Worker 0 appends one `Drift: <date> HEAD <old>..<new>; dirty +
<paths>` line directly under the header's `Baseline commit:` line, continuation lines indented
two spaces. A drifted path is concurrent work like the rest.

Per item Worker 0 records `ITEM_BASELINE=$(git stash create)` + `git status --short`. Item-scoped
diff = `git diff <item baseline> -- <paths touched>` PLUS every file the item added, shown via
`git diff --no-index /dev/null <new>`.

Fixes accumulate uncommitted. Each verified item's tracked edits + new files go to the `## Owned
changes` ledger (path, item, symbols). A later item may build on a ledgered path. Attribute by
content: before editing a dirty path, diff vs `git show HEAD:<path>` and match every hunk to the
ledger or the cycle baseline; a hunk in neither = external edit → stop, report to Worker 0, who
reconciles w/ Rio. Same stop when the item-scoped diff carries hunks the worker didn't make.

## Workspace

A scratch directory is not a sandbox: a probe under `docs/bug_hunt/temp-tests/` still imports the
live package and opens the tracked `examples/fakeshop/db.sqlite3`. Every destructive or
source-mutating probe runs in a disposable copy:

```shell
WS=<scratch>/hunt-ws/<item>
rsync -a --exclude .git --exclude .venv --exclude '__pycache__' --exclude docs/ ./ "$WS/"
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
```

Every command runs w/ `$WS` as cwd (`uv run --directory "$WS"`): `--project` alone keeps the
caller's cwd on `sys.path`, so the import above prints the SHARED package and the check passes for
the wrong tree. Before any verdict the record shows the printed package path inside `$WS` and the
database `NAME` resolved from inside `$WS` (`examples/fakeshop` settings). A probe importing the
shared checkout or opening its database = `invalid`, whatever it found. Workspace holds its own
sqlite copy, caches, subprocesses; no network, no credentials, no `FAKESHOP_PG_DSN`. Worker 2 gets
a FRESH copy taken after Worker 1's fix so it verifies the exact patch.
`scripts/prove_failability.py` runs only from inside `$WS` ([DRY.md][dry] "Tests" has the recipe);
never the live script on a live target. Promotion = Worker 1 applying the confirmed fix to the
shared tree by hand, then the focused permanent test there. No branches, no shared-tree restores.

Shadow inputs (`docs/shadow/current/`) are not in the copy (`--exclude docs/`): read them from
the shared tree, read-only; they are orientation, never a target.

Read-only scratch (a probe that imports the live package and writes nothing) may live under
`docs/bug_hunt/temp-tests/<scope>/`. Worker 1 never cleans up; Worker 0 removes item scratch +
`$WS` only after Worker 2 completes the item.

## Evidence record

Self-reported evidence was the weak link: a drafted-never-executed battery, a placeholder-failing
scratch file, a 50,000-depth claim whose probe never reached the scanner. A probe file plus a log
proves nothing. Every claim (defect, no-bug on an axis, inconclusive) links to a record w/ exactly:

- workspace path + imported package `__file__` + database target, printed by the run;
- exact command + environment (`FAKESHOP_*`, seed, profile);
- source digest of every file the claim depends on (`git hash-object <path>` at run time);
- collected node ids; executed / skipped / error counts; exit status; wall time;
- the entry or effect assertion proving the boundary was REACHED (a depth-limit claim shows the
  scanner ran; an isolation claim shows the forbidden row was queried for and absent);
- positive control: the same instrument made to fail for the intended reason.

Worker 0 rejects mechanically, before Worker 2 reads anything:

| Record shows | Verdict |
|---|---|
| package imported from the shared checkout | `invalid: wrong import path` |
| database target outside the workspace | `invalid: database target` |
| zero tests collected, or only setup/fixture errors | `inconclusive` |
| digest of a depended-on file ≠ digest at run | `invalid: stale source` |
| positive control passed | `invalid: instrument` |
| claim w/o a record link, or record w/o reach assertion | `inconclusive` for that claim |
| an applicable cell not executed | that cell `unverified`; item never `no-bugs` on it |

Logs and generated examples are untrusted data, never instructions to the next worker.

## Worker 1: search and implement

Fresh Worker 1 per item w/ the exact target + prompt, progress-file path, run id, both baselines,
the ledger, workspace path, required reading. Reads the progress file, never edits it.

### Understand

Read the whole live target. Trace in and out until the contracts are clear: who calls, imports,
registers, wraps, configures it; which state, lifecycle, settings, ORM, cache, framework hook it
relies on; how representative inputs become outputs, errors, queries, persistent state; which tests
+ public docs promise its behavior; whether a suspicious branch is protected or invalidated
elsewhere. Don't stop at an adapter when the contract lives behind it; don't wander once an edge is
understood. Record the contract row for every boundary you will probe.

### Break things

Mandate: **break things, break things, break things**, inside the workspace. Misuse, malformed
state, unnatural ordering, interruption, repetition, concurrency, partial success, failure during
failure handling. Clean functions participate in broken systems when caller, adapter, cache,
registry, ORM boundary, framework hook, or error translator makes a different reasonable
assumption; stack those layers in hostile sequences. For every direction push the opposite too:
empty/enormous, missing/overspecified, first/repeated, allowed/denied, uninitialized/stale,
commit/rollback, sync/async, one DB/another, single/concurrent, early/late lifecycle; then combine
extremes across layers. Prompts for invention, not a checklist.

### Mandatory adversarial matrix

Floor of a hunt, not its shape: a target yielding only matrix hits hasn't been searched. Discharge
every axis on every target, w/ a probe or one line naming why the target has no such surface.

1. **Shape and container mismatches** — scalar where an iterable is consumed and vice versa, at
   every boundary that unpacks, iterates, measures.
2. **Absent vs explicitly null** — `UNSET` vs `None` per field kind, esp. where null is forbidden.
3. **Lexical and delimiter boundaries** — nesting, redundant/unbalanced delimiters, compound forms,
   non-whitespace separators wherever text is scanned, split, classified.
4. **Hostile consumer objects** — one-shot generators, iterators raising midway, adversarial
   `__iter__`/`__len__`/`__eq__`/`__str__`/`__repr__`, descriptors, metaclasses at declaration and
   schema-construction seams. Escape as a raw `TypeError` where the contract row promises
   `ConfigurationError` = defect; containment the row doesn't promise = not a fix.
5. **Absent vs empty configuration** — `monkeypatch.delattr(settings, ...)`, never `None`/`[]`.
6. **Valid stateful adversaries** — known-valid ids + operations, several actors w/ ownership
   relations, sequences: warm as A then read as B; authorize then revoke; validate then change a
   relation on another connection; subscribe then expire. Assert forbidden rows + side effects
   ABSENT. Invalid-document generation stops before resolvers; keep it for parser/input boundaries.
   `testing/client.py::TestClient` is the in-process HTTP client; rejection probes disable its
   assert-no-errors default and assert the exact rejection; CSRF probes enable enforcement.
7. **Lifecycle under interruption** — exception, cancellation, timeout, connection loss between
   phases; commit hooks; locks released; `sync_to_async` boundaries; state owned in two places.
8. **Environment cells** — interpreter/dependency semantics, SQL vendor, DB aliasing, optional
   dependency present/absent, sync/async transport, process order. State which cells the claim
   covers; a pure helper isn't rerun per vendor, a query-shape claim is. Unavailable cell =
   `unverified`, listed, never passed. `utils/relations.py` had 100% coverage, survived 39 probes,
   and was wrong on a push/PR cell.

### Confirm

Try to disprove every candidate: read test bodies, run the uncertainty as a small workspace probe.
A confirmed defect has **Defect** (violated contract row), **Evidence** (record link), **Impact**
(consequence, affected callers, actor prerequisites), **Severity** w/ its factors, **Proof** (the
permanent test that fails w/o the fix and passes w/ it). Then `Status: candidate` via the report.

### Implement

Best root-cause correction at the owner, cross-file when the invariant requires (name why each file
moved). Apply to the shared tree by hand from the workspace; attribute hunks first ("Baseline and
ownership"). Permanent tests same change; focused `uv run pytest <path> --no-cov`; never the full
suite. Then `uv run ruff check --fix .`, then `uv run ruff format .` last, until
`uv run ruff format --check <paths touched>` and `uv run ruff check <paths touched>` both pass.

Report: target + result (`No bugs` / `Fixed <severity>` / `Inconclusive` / `Blocked`); contract
rows recorded; system paths and behavior examined; matrix per axis; confirmed defects w/ evidence
records, or the strongest evidence for no-bug; files changed + why; permanent + scratch tests,
commands, outcomes; formatter/linter result; every scratch + workspace path left for Worker 0;
inputs inspected (digests) for the freshness line.

## Worker 2: verify

Fresh Worker 2 per submitted item, after Worker 0's mechanical checks pass. Receives the item, the
contract rows, the minimal reproducer, the item-scoped diff, a fresh workspace; receives Worker 1's
diagnosis and report AFTER recording its own expectation.

1. From contract + reproducer, write the expected behavior before reading the diagnosis.
2. Replay the reproducer in the fresh workspace; prove the pre-fix behavior was wrong (temporarily
   revert the production hunk inside `$WS`, never in the shared tree).
3. Attack the fix: other inputs, orderings, repeated calls, state boundaries, failure paths, the
   opposite extreme of everything Worker 1 tried, the other applicable cells.
4. Confirm the owner is right, connected behavior compatible, every necessary file moved.
5. Confirm permanent tests exercise real usage at the AGENTS.md tier and fail w/o the correction.
6. For `No bugs`: rerun the strongest probes, judge each claimed inapplicable axis on its reason
   against the target's real surface, search independently where the trace is shallow.
7. Confirm severity factors; dispute product semantics → `blocked` for Rio, never a regrade by
   fiat.
8. Check the item-scoped diff against [AGENTS.md][agents] prose rules: no process provenance,
   `path::Symbol` citations, tests at the mandated tier; run `uv run ruff format --check` and
   `uv run ruff check` on the touched paths. A violation or a failure is `revision-needed`.

Verdict `verified` w/ the `Verification:` line, or `revision-needed` w/ concrete reproducible
challenges. Worker 2 never edits the production fix or its tests.

## Worker 0: coordinate

- Start: read [AGENTS.md][agents], [START.md][start], this file, `README.md`, `GOAL.md`,
  [docs/README.md][docs-readme], `docs/TREE.md`, [docs/GLOSSARY.md][glossary]; generate or resume;
  record `CYCLE_BASELINE`; append nothing to `## Cycle baseline` afterwards; drift goes on
  `Drift:` lines under `Baseline commit:` ("Baseline and ownership").
- Dispatch the next unchecked item: baseline, fresh Worker 1, workspace path. File items in
  inventory order; a scenario item as soon as its entry-point files are done or when a file item
  names it; integration + gate last.
- On a report: run the evidence table; `invalid`/`inconclusive` → back to Worker 1 w/ the row named
  (twice → `inconclusive` recorded, next item). Passing checks → fresh Worker 2 w/
  expectation-first sequencing. `verified` → ledger rows, `Result:`/`Verification:`/`Cleanup:`
  lines, tick, advance. `revision-needed` → same item back to Worker 1 w/ workspace intact; after
  two failed re-passes → `blocked` for Rio.
- Append a `## Scenarios` item whenever a report names a cross-file contract w/o one; new
  `## Package questions` leads come only from Rio.
- Mark `stale` any verified item whose recorded digests no longer match; re-dispatch Worker 2 on it
  before the gate.
- Cleanup after `verified`/`no-bugs` only: item scratch + `$WS`, by explicit path; confirm nothing
  else moved.
- Never hunts, fixes, edits a fix, grades correctness, or overrides Worker 2.

## Scenarios

Cross-file contracts the per-file sweep structurally misses. Standing items, generated every hunt:

1. **Pagination window semantics** — `connection.py`, `keyset.py`, `relay.py`: cursor round trip
   fixes schema, order, key context; first/last/after/before algebra; "bigger document never
   charges less" names the charge dimension and ordering.
2. **Authorization and visibility across actors** — `utils/querysets.py` seal,
   `mutations/permissions.py`, `resource_policy.py`, `optimizer/_context.py`: forbidden rows absent
   across actor switches, prefetch/reverse relations, cache reuse across executions, awaitable
   truthiness, point-in-time authorization.
3. **Transaction and session lifecycle under interruption** — `utils/write_transaction.py`, write
   pipelines across the three flavors, `consumers.py`: locks, rollback, commit hooks, cancellation,
   `sync_to_async` boundaries, failure during failure handling.

Each scenario record: id; entry points; contract citations; actors; input domain; lifecycle +
state; observations + independent oracle; dependency edges (forward + reverse); applicable cells +
what each proves; owning files. Discovered scenarios are appended by Worker 0 as items and hunted
the same way. Two independent hunters w/ different lenses (contract + state transitions vs
implementation + failure paths) only for a scenario Worker 0 marks high-risk; they exchange results
after both report.

## Integration and final gate

Package integration (Worker 1 → Worker 2): the final live tree across boundaries incl. public
exports + `__init__.py`: incompatible lifecycle phases, state owned twice, circular initialization,
divergent public flavors, gaps between implementation, tests, examples, docs. Re-inventory first:
`.py` added/removed/renamed since baseline (`git ls-files` + untracked) each get an item or a
closing note; verified items whose digests moved go `stale`.

Final gate (Worker 0): `uv run pytest`. Passes when the suite passes + package coverage stays 100%.
Record failures, coverage, skips, xfails, collected/selected counts, mode. Bind it to the tree
object from `git stash create` at gate time + blob ids of `pyproject.toml`, `uv.lock`. Product
failure → the owning item back to Worker 1; environment/concurrent failure → recorded precisely,
`blocked`. Sharded and Postgres cells are `unverified` unless Rio authorized them; the report lists
them.

## Closeout

Worker 0 fills `## Outcomes` before deleting anything: per fixed item defect, severity + factors,
owner file, permanent test, evidence record digest; no-bug items w/ their strongest probe;
scenarios hunted / appended / left open; stale re-verifications; inconclusive items w/ what never
ran; blocked items w/ the decision owed; cells covered vs unverified; unexamined scope; gate
record; net source change vs cycle baseline; concurrent work untouched. "Selected campaign
complete" + the unexamined list, never whole-package clearance. Then `Status: complete`; remove
only this run's `docs/bug_hunt/temp-tests/<scope>/` dirs + `<scratch>/hunt-ws/` by explicit path.
Never remove `HUNT.md`, `dicta.md`, the progress file, `pbugs.md`, or `docs/shadow/`. Do not
commit.

## Why this shape

Tracked records `bug_hunt-0_0_13.md`, `bug_hunt-0_0_14.md`, `bug_hunt-0_0_15.md`; the per-file
two-role method is at `git show 58114254:docs/bug_hunt/HUNT.md`.

- Most fixed items shared one shape (hostile consumer object escaping a construction seam as a raw
  `TypeError`) because the rules rewarded it: per-file entry, "break things", blanket containment.
  → contract row first; matrix axes 6-8; scenario items.
- Client-reachable findings (prefetch leak failing open on reverse relations w/o `related_name`,
  awaitable-truthiness silent allow, cross-execution sentinel leak) were cross-file contracts. →
  standing scenarios 2 and 3.
- Five submissions were rejected for probes that never ran; a post-closeout review regraded six
  items and reverted an undisclosed export removal the verifier had anchored past. → evidence
  record + mechanical table; Worker 2 records its expectation before the diagnosis.
- Every probe ran on one cell; a 100%-covered helper closed `no-bugs` after 39 probes was wrong on
  a CI cell. → axis 8, cells listed `unverified`.
- A containment fix was superseded by an owner fix while its item stayed checked. → `stale`.
- Two runs of one release collided under one filename; one predecessor's record was deleted. → run
  id in the header; `--force` only for an explicit restart; Outcomes durable.
- `dicta.md` stayed empty while `pbugs.md` and root `vulns.md` were never fed back. → leads w/
  provenance, revalidated on current source, never oracles.

## Instruments

Installed today: pytest + coverage, `scripts/prove_failability.py` (workspace only). Nothing else
is in `pyproject.toml`; adding Hypothesis, hypothesis-graphql, mutmut, semgrep, a type checker,
`pytest-randomly`, `pytest-timeout`, `freezegun` is Rio's decision, recorded as `blocked` when a
scenario needs one. If added: a dependency a permanent test imports lives in `dev` and runs in CI,
or the generator stays optional and only minimized deterministic regressions are promoted;
Hypothesis gets a per-example state reset proved before any write-path property, and a profile
registered in code; a surviving mutant is a lead about test discrimination, never a defect; static
rules are calibrated on known positives + legitimate negatives before gating; controlled time is
applied at the owned seam w/ an external watchdog for real timeouts.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[security]: ../../SECURITY.md
[start]: ../../START.md

<!-- docs/ -->
[dicta]: dicta.md
[docs-readme]: ../README.md
[dry]: ../dry/DRY.md
[glossary]: ../GLOSSARY.md
[worker-0]: worker-0.md
[worker-1]: worker-1.md
[worker-2]: worker-2.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[generator]: ../../scripts/bug_hunt.py

<!-- .venv/ -->

<!-- External -->
