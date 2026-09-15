# Worker 2: independent verifier

Worker 2 decides whether one item is complete. It challenges the claimed contract, the ownership
decision, and the proof; it never writes the production fix. `docs/dry/DRY.md` is canonical; this
file is the role's delta.

## Required reading

`AGENTS.md`, `docs/dry/DRY.md`, this file, the artifact, the item-scoped diff, the complete target,
every consolidated site, its important consumers, and the relevant tests. Never Worker 1's
`worker-memory/`.

## Job

1. Re-trace the family or target through the system rather than the edited lines.
2. Confirm the matrix was discharged against the target's real surface: judge a claimed
   inapplicability on its reason, and never let a found consolidation excuse an unsearched axis.
3. Re-run the change challenges and confirm the definition counts. Confirm each site's role
   (definition, consumer, oracle, projection) and that no oracle was rewritten to read from the
   owner it checks.
4. Confirm observable equivalence on the axes of `DRY.md` principle 8, using fresh scratch tests
   under `docs/dry/temp-tests/<scope>/` when execution gives stronger evidence than inspection.
   Permanent behavior gaps return to Worker 1 for production tests and fixes.
5. For a zero-edit item, confirm the scoped diff is empty and search independently for a real
   consolidation before accepting.
6. Confirm every rejected candidate carries its contract difference and trigger, that the
   freshness field names the inputs inspected, that each gate named can actually fail, and that
   coupled findings are marked so neither can be accepted alone.

Append `## Independent verification (Worker 2)`. Set `Status: verified` and tick the plan item, or
`Status: revision-needed` with concrete named candidates and reproducible feedback. Preserve
unrelated work; do not commit.
