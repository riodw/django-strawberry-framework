# Worker 2: consolidation implementer

Worker 2 turns one reviewed artifact into the best root-cause consolidation. It does not approve
its own work. `docs/dry/DRY.md` is canonical.

## Required reading

Read `AGENTS.md`, `START.md`, `docs/dry/DRY.md`, this file, the artifact, the complete target, every
confirmed duplicate site, their important consumers, and relevant tests. Inspect the item-scoped
diff from the baseline. Do not use historical cycle artifacts or another worker's private memory.

## Implementation job

1. Reproduce each finding before editing. Reject it when the sites do not share a contract or
   reason to change; record the concrete evidence.
2. Put the single source of truth at the layer that owns the shared responsibility. Prefer extending
   an existing owner, deleting an obsolete path, or establishing one canonical representation over
   adding a forwarding helper.
3. Migrate every confirmed site. Preserve intentional variation explicitly; do not accumulate mode
   flags merely to make unrelated behavior share a function.
4. Add permanent behavioral tests at the strongest reachable tier required by `AGENTS.md`. Tests
   must prove the shared contract and protect any boundary that intentionally remains separate.
5. Review comments, docstrings, exports, and public docs affected by the new ownership.
6. Run focused verification when useful, then `uv run ruff format .` and
   `uv run ruff check --fix .` after edits.

## Artifact update

Append `## Implementation (Worker 2)` and record:

- the owner chosen and why it is the correct boundary;
- every source, caller, test, export, or doc migrated;
- behavior deliberately kept separate;
- permanent and scratch verification results;
- formatter and linter results;
- evidence for rejected findings;
- whether the completed change merits a changelog entry.

Do not edit `CHANGELOG.md` without explicit maintainer authorization. Set
`Status: fix-implemented` only when the complete item is ready for independent verification. On a
later pass, append to `## Iterations`; preserve the audit trail.

Keep unrelated cleanup out of the diff, preserve concurrent work, and do not commit.
