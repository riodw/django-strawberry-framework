# Worker 2: independent verifier

Worker 2 decides whether one DRY item is complete. It independently challenges the claimed shared
responsibility and the resulting ownership; it never writes the production fix.
`docs/dry/DRY.md` is canonical.

## Required reading

Read `AGENTS.md`, `docs/dry/DRY.md`, this file, the artifact, item-scoped diff, complete target,
consolidated sites, important consumers, and relevant tests. Do not use historical cycle artifacts
or Worker 1's private reasoning beyond the shared artifact.

## Verification job

1. Re-trace the responsibility through the system rather than reviewing only edited lines.
2. Independently verify that every consolidated site shares the promised contract and reason to
   change. Confirm that rejected or intentionally separate sites truly differ.
3. Search for missed implementations, stale representations, bypasses, duplicate policy, imports,
   tests, docs, and exports.
4. Try to break the result with different inputs, state sequences, lifecycle phases, framework
   paths, and extension points relevant to the target.
5. Use focused tests or fresh scratch tests under `docs/dry/temp-tests/<scope>/` when useful.
   Permanent behavior gaps return to Worker 1 for production tests and fixes.
6. Confirm the new owner is clearer than the old repetition, all call sites migrated, compatibility
   is preserved, validation is credible, and unrelated work was not absorbed.

## Outcome

Append `## Independent verification (Worker 2)` and dispose of every finding and material rejected
candidate.

- If complete, set `Status: verified` and mark the matching plan item.
- If anything remains, set `Status: revision-needed` with concrete, reproducible feedback and leave
  the plan item open.

Every review or implementation problem returns to Worker 1. For a zero-edit item, first confirm the
scoped diff is empty and independently search for a real consolidation opportunity. Preserve
unrelated work and do not commit.
