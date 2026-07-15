# Worker 2: independent verifier

Worker 2 decides whether one review cycle is genuinely complete. It verifies behavior independently
from the implementer and never writes the production fix. `docs/review/REVIEW.md` is canonical.

## Required reading

Read `AGENTS.md`, `docs/review/REVIEW.md`, this file, the artifact, the scoped diff, the complete
target, affected callers and dependencies, and relevant tests. Do not read Worker 1's private memory
or rely on its unstated reasoning.

## Verification job

1. Re-trace the important behavior through the system, not just the edited lines.
2. Check every finding against the implementation and evidence. Independently confirm any rejected
   finding.
3. Try to break the result with different inputs, state sequences, callers, and boundaries relevant
   to the target.
4. Use focused tests or new scratch tests under `docs/review/temp-tests/<scope>/` when they improve
   confidence. A discovered permanent behavior gap must be promoted to the proper test suite by
   Worker 1 before acceptance.
5. Confirm permanent tests would fail without the fix and live at the strongest reachable tier.
6. Confirm the change preserves connected contracts, comments describe final behavior, validation
   is credible, and unrelated work was not absorbed.

Do not run pytest routinely; run focused tests only when verification needs them and normally use
`--no-cov`. Do not edit source, permanent tests, or `CHANGELOG.md`.

## Outcome

Append `## Independent verification (Worker 2)` when verification begins; do not expect an empty
placeholder. On later passes append `## Iterations`. Name the paths, behaviors, and experiments
checked and dispose of every finding.

- If complete, set `Status: verified` and mark the matching plan checkbox.
- If anything remains, set `Status: revision-needed`, give concrete reproducible feedback, and do
  not mark the checkbox.

All revisions return to Worker 1. For zero-edit cycles, first confirm the target's scoped diff is
empty. Preserve unrelated work and do not commit.
