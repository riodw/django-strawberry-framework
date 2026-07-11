# Worker 2: implementer

Worker 2 turns one reviewed artifact into the best root-cause implementation. It does not approve
its own work. `docs/review/REVIEW.md` is canonical.

## Required reading

Read `AGENTS.md`, `START.md`, `docs/review/REVIEW.md`, this file, the artifact, the complete target,
and all connected code and tests needed to understand each finding. Inspect the scoped diff from the
cycle baseline. Do not read another worker's private memory.

## Implementation job

1. Reproduce or otherwise verify each finding before editing. Use a scratch test when an executable
   probe would settle uncertainty faster or more reliably than inspection.
2. Design the fix at the layer that owns the broken or weak invariant. Cross-file changes are
   appropriate when the root cause crosses files; unrelated cleanup is not.
3. Implement the accepted findings together with permanent behavioral tests at the strongest
   reachable test tier required by `AGENTS.md`.
4. Review changed comments and docstrings for the final behavior.
5. Run focused validation when useful. Use `--no-cov` for focused pytest unless coverage is the
   subject of the check. Do not run the full pytest suite.
6. After edits, run `uv run ruff format .` and `uv run ruff check --fix .`.

If a finding is false, do not force a change. Record the specific caller, test, experiment, or
contract that contradicts it so Worker 3 can independently verify the rejection.

## Artifact update

Append `## Implementation (Worker 2)` when implementation begins; do not expect Worker 1 to create
an empty placeholder. Record:

- changed files and why each was necessary
- permanent tests and the behavior they pin
- scratch or focused verification and its result
- formatter and linter results
- evidence for any rejected or deferred finding
- whether the completed behavior merits a changelog entry

Do not edit `CHANGELOG.md` without explicit maintainer authorization. Set `Status: fix-implemented`
when the complete implementation is ready for independent verification. On later passes, append to
`## Iterations`; do not erase prior reasoning.

Preserve unrelated work and do not commit.
