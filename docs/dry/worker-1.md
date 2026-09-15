# Worker 1: reviewer and implementer

Worker 1 owns one plan item: a file, a responsibility family, a folder or project integration pass,
or the final gate. `docs/dry/DRY.md` is canonical; this file is the role's delta.

## Required reading

`AGENTS.md`, `START.md`, `docs/dry/DRY.md`, this file, the plan item, the `## Owned changes`
ledger, the complete target, and every connected source, test, example, doc, or upstream
implementation a sound judgment needs. Inspect the item-scoped diff from the baseline, new files
included. Prior cycle records are inputs only as rejected-candidate triggers to check. Never read
another worker's `worker-memory/`.

## Job

- **File item:** discharge the probing matrix, then assign every rule the file defines or enforces
  to a family in the plan's `## Responsibility index` (adding `## Families` items for new ones), or
  record it as file-local with the challenge that proved it. Do not consolidate here.
- **Family item:** sweep the whole package for the rule's mechanism, inventory every site with
  its role, run the change challenges on the rule's variation axes, make the ownership decision,
  and implement the confirmed consolidation at its owner with permanent tests at the tier
  `AGENTS.md` mandates, in the same change. Record each intentional separation at the owner and
  each sub-rule as an index row. A member lacking a guard is a defect only once a contract source
  says the rule applies to it; bugs that are not duplication go under `## Defects`, unfixed, and
  one a consolidation depends on is named in that finding's Coupling.
- **Folder and project items:** audit the unassigned remainder and the families that cross
  ownership boundaries. Do not summarize prior artifacts.
- **Final gate:** run `uv run pytest` and every `## Pending execution` command only under the
  maintainer's explicit authorization; record result, coverage, skips, xfails, counts, mode, and
  the input bindings.

Before editing a dirty path, attribute every hunk to the ledger or the cycle baseline; an
unattributed hunk stops the item. Source-mutating proofs run only in the disposable workspace
`DRY.md` "Tests" describes. Write the artifact in `DRY.md`'s shape with its `Run:` line. After an
edit run `uv run ruff format .` and `uv run ruff check --fix .`. Append `## Implementation
(Worker 1)` when tracked changes are made; on a later pass append to `## Iterations`. Set
`Status: fix-implemented` only when the complete item, edited or zero-edit, is ready for
independent verification; without edit rights, set `Status: designed` instead. Keep unrelated
cleanup out of the diff, preserve concurrent work, never edit `CHANGELOG.md` without
authorization, and do not commit.
