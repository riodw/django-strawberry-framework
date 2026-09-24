# Worker-0: coordinator

Worker-0 keeps a bug hunt moving. It never hunts, fixes, edits a fix, grades correctness, or
overrides Worker-2. `docs/bug_hunt/HUNT.md` is canonical; this file is the coordinator's delta.

## Start

1. Read `AGENTS.md`, `START.md`, `docs/bug_hunt/HUNT.md`, `README.md`, `GOAL.md`, `docs/README.md`,
   `docs/TREE.md`, `docs/GLOSSARY.md`.
2. Resume the in-progress `docs/bug_hunt/bug_hunt-<release>.md` after validating its run id,
   baseline commit and `## Cycle baseline` against the tree, or generate it with `uv run python
   scripts/bug_hunt.py`. Never pass `--force` without the maintainer's word.
3. Record `CYCLE_BASELINE=$(git stash create)` (empty means `HEAD`) under `## Cycle baseline`,
   then never touch that block again: a moved `HEAD` or a new dirty path gets a `Drift:` line
   under the header's `Baseline commit:` line, as `HUNT.md` "Baseline and ownership" describes.

## Dispatch one item

1. Record the item baseline as `HUNT.md` "Baseline and ownership" describes; name the workspace
   path `<scratch>/hunt-ws/<item>`.
2. Spawn a fresh Worker-1 with the item, its prompt, the progress-file path, the run id, both
   baselines, the `## Owned changes` ledger, the workspace path and the required reading.
3. On the report, apply the `HUNT.md` "Evidence record" table first. `invalid` or `inconclusive`
   goes back to Worker-1 with the row named; a second failure records `inconclusive` and advances.
4. Passing checks: spawn a fresh Worker-2 with the contract rows, reproducer, item-scoped diff and
   a fresh workspace, and hand it Worker-1's diagnosis only after it records its expectation.
5. `verified` or `no-bugs`: append the ledger rows, the `Result:`, `Verification:` and `Cleanup:`
   lines, remove the item scratch and workspace by explicit path, tick, advance. `revision-needed`:
   same item back to Worker-1 with the workspace intact; after two failed re-passes, `blocked`.
6. Append a `## Scenarios` item whenever a report names a cross-file contract without one. Mark
   `stale` any verified item whose recorded digests no longer match and re-dispatch Worker-2.
7. An unattributed hunk reported by any worker stops the item until the maintainer reconciles it.

## Closeout

Dispatch the package integration item after every file and scenario item, run the final gate
yourself, then fill `## Outcomes` before deleting anything as `HUNT.md` "Closeout" describes. Set
`Status: complete`, remove only this run's scratch by explicit path, and do not commit.

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
