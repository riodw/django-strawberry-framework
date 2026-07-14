# System-wide bug hunt

Hunt for bugs in `django_strawberry_framework/` one file at a time. The target is one file; the
investigation is not. Follow the target through callers, dependencies, state, framework hooks,
tests, examples, and public contracts before deciding that it is correct.

Treat bug discovery as a multi-layer problem. In clean code, serious bugs are rarely isolated
golden-nugget mistakes; they emerge when individually reasonable layers stack into a broken
lifecycle, state transition, ownership boundary, or public behavior. Think holistically and
creatively. Search the interactions between layers, not only suspicious lines inside the target.

This is a fresh hunt of the current working tree. Do not seed findings from old build, review, DRY,
or bug-hunt artifacts. The generated shadow snapshot is an orientation aid fixed at the start of
the hunt; the live source is always authoritative.

There are exactly two worker roles:

- **Worker 1 — coordinator and verifier:** sets up and owns the progress file, dispatches every
  item, independently verifies every fix, and runs the final gate.
- **Worker 2 — hunter and implementer:** searches for confirmed bugs, implements root-cause fixes,
  and adds the permanent tests that prove them.

No Worker 0 or Worker 3 participates. Once started, the process is autonomous: continue through
the next unchecked item and every necessary revision until the hunt is complete or a genuine
external blocker requires maintainer input.

## Ground rules

- Read `AGENTS.md`, `START.md`, `README.md`, `GOAL.md`, `docs/README.md`, `docs/TREE.md`, and
  `docs/GLOSSARY.md` before beginning a run. `AGENTS.md` governs repository safety, test placement,
  formatting, changelog edits, and commits.
- Preserve unrelated dirty and concurrent work. A bug fix may cross files when the broken invariant
  does, but unrelated cleanup stays out of scope.
- Confirm a defect before editing. Static warnings, suspicious shapes, shadow markers, and missing
  tests are leads, not findings.
- Prefer the root-cause fix at the layer that owns the violated contract. Do not patch only the
  observed caller when the system invariant is wrong.
- Every production fix receives a permanent behavioral test at the strongest reachable tier
  required by `AGENTS.md`.
- Worker 2 may be deliberately messy and destructive inside disposable scratch scope. It may write
  many temporary tests, mutate throwaway databases and state, monkeypatch internals, force invalid
  sequences, and leave failed experiments in place. Scratch belongs under
  `docs/bug_hunt/temp-tests/<scope>/` or another path Worker 1 can identify and remove.
- Destructiveness stops at the scratch boundary. Worker 2 never deletes or corrupts package source,
  permanent tests, maintainer work, credentials, external services, or non-disposable data. Its
  production edits are limited to confirmed fixes and their permanent tests.
- Worker 2 does not clean up its scratch work. Worker 1 owns cleanup after the item is verified and
  before the next item begins, so verification can inspect and rerun the exact destructive probes.
- Only the maintainer commits, creates or switches branches, pushes, or changes the changelog.

## Progress file and setup

Worker 1 owns one generated `docs/bug_hunt/bug_hunt-<release>.md` file for the entire run, named
from the release like the review and DRY flows (`0.0.13` becomes `bug_hunt-0_0_13.md`). It is the
canonical plan, progress record, and handoff between workers.

If an in-progress file already exists, resume it. Otherwise Worker 1 runs:

```shell
uv run python scripts/bug_hunt.py
```

The generator:

- resolves the current `HEAD` as the hunt baseline;
- refreshes only `docs/shadow/current/` through
  `scripts/review_historical_package_snapshot_at_commit.py`;
- reads `docs/bug_hunt/dicta.md` as optional maintainer-authored probing questions;
- inventories the live package and creates one item for every non-`__init__.py` Python file,
  followed by a package integration item and the final test gate;
- records autonomous mode and the full baseline commit, and names the file from the matching
  `pyproject.toml` and package `__init__.py` version (`--target-release` overrides it); and
- refuses to overwrite an existing progress file unless the maintainer explicitly requests a
  restart with `--force`.

`dicta.md` may be empty. Do not regenerate it from historical worker briefs or treat it as a list
of expected findings. Questions in it guide exploration; current source and executable behavior
decide the result.

The snapshot remains fixed for the run even as earlier items change the working tree. Its stripped
source and overview files help orient Worker 2 to the baseline structure when a matching snapshot
exists. A new live file may have no shadow and is still a full hunt item. Worker 2 must read the
complete live target and connected live code before reaching a conclusion.

Each progress item starts in this form:

```text
- [ ] path/to/target.py
    - Status: pending
    - Prompt:
        - <target and shadow inputs>
```

Worker 1 alone updates the progress file. Valid item states are `pending`, `hunting`,
`fix-implemented`, `revision-needed`, `no-bugs`, `verified`, and `blocked`. Before dispatch, Worker
1 records a cycle baseline so changes from the current item can be separated from earlier and
concurrent work.

## Worker 2: search and implement

Use a fresh Worker 2 context for each item. Give it the exact target and prompt, the progress-file
path, the hunt baseline, the cycle baseline, and the required reading. Worker 2 reads the progress
file but never edits it.

### Understand the target

Read the entire live target. Trace important behavior into and out of it until the relevant
contracts are clear:

- who calls, imports, registers, wraps, exposes, or configures it;
- which state, lifecycle, settings, ORM behavior, cache, or framework machinery it relies on;
- how representative inputs become outputs, errors, queries, or persistent state;
- which tests and public docs promise its behavior; and
- whether a suspicious local branch is actually protected or invalidated elsewhere.

Follow connections as far as the bug judgment requires. Do not stop at an adapter when the real
contract lives behind it, and do not expand into unrelated subsystems once an edge is understood.

### Search and verify

Worker 2's mandate is simple: **break things, break things, break things.** Write scratch test files.
Be messy. Be hostile. Try misuse, malformed state, unnatural ordering, interruption, repetition,
concurrency, partial success, and failure during failure handling. Within disposable scratch scope,
Worker 2 is free to do anything useful to make the behavior fail. Do not clean up after yourself;
leave every useful probe and its state for Worker 1.

Think creatively across layers, not merely through familiar local bug patterns. A clean function
can still participate in a broken system when its caller, adapter, cache, registry, ORM boundary,
framework hook, or error translator makes a different reasonable assumption. Combine those layers
in hostile sequences and search for failures that appear only after several individually valid
steps stack together.

For every direction tested, push hard in the opposite direction too: empty and enormous input,
missing and overspecified configuration, first and repeated calls, allowed and denied access,
uninitialized and stale state, commit and rollback, sync and async, one database and another,
single-threaded and concurrent execution, early and late lifecycle phases. Do not stop when one
extreme passes; contrast it with its inverse and then combine extremes across layers.

Challenge assumptions around invalid input, partial failure, request and cache isolation,
permissions, optional dependencies, schema lifecycle, type selection, error translation, and
ordering. These are prompts for invention, not a checklist to reproduce.

Try to disprove every candidate. Read the existing test bodies and exercise uncertain framework or
state behavior with a small scratch probe. A confirmed bug must have:

- **Defect:** the violated behavior or invariant;
- **Evidence:** a reproducible path, experiment, test, or authoritative contract;
- **Impact:** the real consequence and affected callers;
- **Severity:** High, Medium, or Low; and
- **Proof:** the permanent test that will fail without the fix and pass with it.

High means a correctness, security, data-isolation, or public-contract failure with serious impact.
Medium means a material edge-case, lifecycle, performance, or integration failure. Low means a
bounded real defect with limited consequence. Do not record style preferences or speculative risks
as bugs.

### Implement

Implement the best root-cause correction for every confirmed defect found in the item. Cross-file
source, test, example, or documentation changes are allowed when the invariant requires them; name
why every changed file is necessary. Do not limit a systemic fix to the entry-point file merely to
keep the diff small.

Add permanent tests in the same change. Use focused validation when useful and normally pass
`--no-cov` to focused pytest runs. Do not run the full suite; Worker 1 owns the final gate. After
any edit, run:

```shell
uv run ruff format .
uv run ruff check --fix .
```

Worker 2 reports:

- target and result: `No bugs`, `Fixed <severity>`, or `Blocked`;
- system paths and behavior examined;
- confirmed defects and evidence, or the strongest evidence supporting a no-bug conclusion;
- files changed and why;
- permanent and scratch tests, commands, and outcomes;
- formatter and linter outcomes; and
- every scratch path and disposable state deliberately left for Worker 1.

## Worker 1: verify and advance

Worker 1 reviews every Worker 2 report for completeness and scope. A `No bugs` result needs enough
system trace and verification evidence to justify completion, but it does not require a second full
hunt. Worker 1 reruns or inspects the strongest scratch probes, removes all item-owned scratch and
disposable state, records `Status: no-bugs` and a concise `Result:` line, then checks the item.

After any fix, Worker 1 independently verifies it before advancing:

1. Inspect the item-scoped changes without absorbing unrelated dirty work.
2. Re-trace the violated contract through the live target, affected callers, dependencies, tests,
   examples, docs, and public exports.
3. Reproduce the original failure or otherwise prove the pre-fix behavior was wrong.
4. Try to break the fix with different inputs, ordering, repeated calls, state boundaries, and
   failure paths relevant to the defect.
5. Confirm the fix lives at the correct owner, connected behavior remains compatible, and every
   necessary file moved with the invariant.
6. Confirm permanent tests exercise real usage at the strongest reachable tier and would fail
   without the correction.
7. Only after verification passes, remove every scratch file and disposable state created for the
   item and confirm that cleanup did not touch unrelated work.

Worker 1 may use new scratch probes or focused tests when they improve confidence. It does not edit
the production fix or its permanent tests during verification.

If the fix is complete, Worker 1 records `Status: verified`, the verification evidence, changed
files, validation, and cleanup, then checks the item and advances. If anything remains, it records
`Status: revision-needed` with concrete reproducible feedback and returns the same item to Worker 2.
Leave the scratch environment intact during a revision so Worker 2 can reproduce and extend it. The
Worker 2 → Worker 1 loop continues automatically until verified. Use `blocked` only when the solution
requires maintainer authority or an external dependency that the workers cannot obtain.

Use concise stable result lines:

```text
Result: No bugs. Evidence: <paths/probes examined>.
Result: Fixed Medium. Files changed: <paths>; validation: <commands/results>.
Verification: Passed. Evidence: <independent checks>.
Cleanup: Removed <item-owned scratch paths/state>; unrelated work preserved.
Blocked: <specific condition and required decision>.
```

Do not erase earlier results or revision feedback. Append an `Iteration:` line when an item cycles.

## Integration and final gate

After all source-file items, Worker 2 performs the package integration item against the live final
tree. It traces representative behavior across package boundaries and explicitly examines public
exports and `__init__.py` files. It searches for failures that no individual entry point reveals:
incompatible lifecycle phases, state owned in two places, circular initialization, divergent public
flavors, and gaps between implementation, tests, examples, and documentation. Any fix follows the
same Worker 2 implementation and Worker 1 verification loop.

At the final item, Worker 1 runs:

```shell
uv run pytest
```

The gate passes only when the suite passes and configured package coverage remains 100%. Record the
result, coverage, skips, and xfails. A product failure returns to Worker 2 for a root-cause fix and
then through Worker 1 verification; an unrelated environment or concurrent-work failure is recorded
precisely and treated as a genuine blocker.

When every item and the final gate are checked, Worker 1 sets the progress file to `Status:
complete` and reports confirmed fixes, no-bug items, blockers, final validation, and unrelated work
left untouched. Confirm that Worker 1 removed all item-owned scratch before closeout. Do not remove
`HUNT.md`, `dicta.md`, the completed progress file, or any sibling output under `docs/shadow/`, and
do not commit.
