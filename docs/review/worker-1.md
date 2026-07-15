# Worker 1: reviewer and implementer

Worker 1 investigates one file, folder, project integration, or final gate. Its job is to understand,
verify, imagine improvements, and implement the best root-cause result—not to fill a checklist. It
never approves its own work. `docs/review/REVIEW.md` is canonical.

## Required reading

Read `AGENTS.md`, `START.md`, `docs/review/REVIEW.md`, this file, the active plan, the complete
target, and every connected source, test, doc, or history entry needed for a sound judgment. Do not
read another worker's private memory.

## Review and implementation job

1. **Understand:** identify the target's responsibility and trace representative behavior through
   callers, dependencies, state, framework hooks, tests, and public promises. Follow connections as
   far as the judgment requires.
2. **Verify:** challenge uncertain behavior with focused commands or scratch tests under
   `docs/review/temp-tests/<scope>/`. Read existing test bodies; coverage and names are not proof.
3. **Improve:** look for both defects and better designs. Test your ideas against real callers and
   assign the recommendation to the true invariant owner.
4. Write the concise artifact from `REVIEW.md`. Every finding needs Observation, Evidence, Impact,
   Recommendation, and Proof. Try to disprove it before recording it.
5. Reproduce or otherwise verify every accepted finding before editing.
6. Implement the findings together with permanent behavioral tests at the strongest reachable test
   tier required by `AGENTS.md`. Cross-file changes are appropriate when the root cause crosses
   files; unrelated cleanup is not.
7. Review changed comments and docstrings for the final behavior.
8. Run focused validation when useful. Use `--no-cov` for focused pytest unless coverage is the
   subject of the check. Do not run the full pytest suite.
9. After edits, run `uv run ruff format .` and `uv run ruff check --fix .`.

Use `scripts/review_inspect.py` only when its AST overview helps orient a complex file. It is an
index, never evidence by itself. Source and executable behavior remain authoritative.

For a folder or project pass, read the final integrated source and search for cross-file behavior an
individual review could not see. Do not concatenate prior artifacts.

## Finish

Append `## Implementation (Worker 1)` when implementation begins. Record:

- changed files and why each was necessary
- permanent tests and the behavior they pin
- scratch or focused verification and its result
- formatter and linter results
- evidence for any rejected finding
- whether the completed behavior merits a changelog entry

If a finding is false, do not force a change. Record the specific caller, test, experiment, or
contract that contradicts it so Worker 2 can independently verify the rejection. Do not edit
`CHANGELOG.md` without explicit maintainer authorization.

For a zero-edit cycle, record the empty scoped diff and enough evidence to justify the conclusion,
then write `None — zero-edit cycle` under the implementation heading. Set
`Status: fix-implemented` only when the complete result is ready for Worker 2.

Omit `### DRY analysis` when no genuine duplication was found. Do not create placeholder
independent-verification or iteration sections; the worker who performs that work appends the
section. On later passes, append to `## Iterations`; do not erase prior reasoning.

Do not run the full suite except when assigned the final gate. Preserve unrelated work and do not
commit.

For the final gate, run `uv run pytest`, record the result, coverage, skips, and xfails, and set
`verified` only when tests pass with 100% package coverage.
