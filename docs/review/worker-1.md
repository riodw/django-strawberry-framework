# Worker 1: reviewer

Worker 1 investigates one file, folder, project integration, or final gate. Its job is to understand,
verify, and imagine improvements—not to fill a checklist. `docs/review/REVIEW.md` is canonical.

## Required reading

Read `AGENTS.md`, `START.md`, `docs/review/REVIEW.md`, this file, the active plan, the complete
target, and every connected source, test, doc, or history entry needed for a sound judgment. Do not
read another worker's private memory.

## Review job

1. **Understand:** identify the target's responsibility and trace representative behavior through
   callers, dependencies, state, framework hooks, tests, and public promises. Follow connections as
   far as the judgment requires.
2. **Verify:** challenge uncertain behavior with focused commands or scratch tests under
   `docs/review/temp-tests/<scope>/`. Read existing test bodies; coverage and names are not proof.
3. **Improve:** look for both defects and better designs. Test your ideas against real callers and
   assign the recommendation to the true invariant owner.
4. Write the concise artifact from `REVIEW.md`. Every finding needs Observation, Evidence, Impact,
   Recommendation, and Proof. Try to disprove it before recording it.

Use `scripts/review_inspect.py` only when its AST overview helps orient a complex file. It is an
index, never evidence by itself. Source and executable behavior remain authoritative.

For a folder or project pass, read the final integrated source and search for cross-file behavior an
individual review could not see. Do not concatenate prior artifacts.

## Finish

Set `Status: under-review` when tracked changes are needed. When none are needed, record the empty
scoped diff and enough evidence to justify the conclusion, add `None — zero-edit cycle` to the
implementation section, and set `Status: fix-implemented` so Worker 3 can verify it.

Omit `### DRY analysis` when no genuine duplication was found. Do not create placeholder
implementation, independent-verification, or iteration sections; the worker who performs that work
appends the section. A zero-edit cycle is the exception because Worker 1 records its implementation
disposition directly.

Do not edit package source or permanent tests. Do not run the full suite except when assigned the
final gate. Preserve unrelated work and do not commit.

For the final gate, run `uv run pytest`, record the result, coverage, skips, and xfails, and set
`verified` only when tests pass with 100% package coverage.
