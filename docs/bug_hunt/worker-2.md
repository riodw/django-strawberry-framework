# Worker 2: independent verifier

Worker 2 decides whether one item is complete. It derives the expected behavior from the contract
before it reads the hunter's diagnosis, replays and attacks the fix, and never writes production
code. `docs/bug_hunt/HUNT.md` is canonical; this file is the role's delta.

## Required reading

`AGENTS.md`, `docs/bug_hunt/HUNT.md`, this file, the item's contract rows, the minimal reproducer,
the item-scoped diff including new files, the fresh workspace, the complete live target and its
important consumers and tests, plus anything upstream or downstream your own trace needs.
Worker 1's diagnosis and report only after step 1 below is written.

## Job

1. Write the expected behavior from the contract row and the reproducer into the verification
   record before reading the diagnosis.
2. Replay the reproducer in the fresh workspace; prove the pre-fix behavior was wrong by reverting
   the production hunk inside the workspace only.
3. Attack the fix with other inputs, orderings, repeated calls, state boundaries, failure paths,
   the opposite extreme of everything tried, and every other applicable cell; list unavailable
   cells as `unverified`.
4. Confirm the owner, the compatibility of connected behavior, that every necessary file moved, and
   that the permanent tests exercise real usage at the `AGENTS.md` tier and fail without the fix.
5. For a `No bugs` submission, rerun the strongest probes, judge each claimed inapplicable axis on
   its reason against the target's real surface, and search independently where the trace is
   shallow.
6. Confirm the severity factors. A dispute about product semantics is reported for the maintainer,
   never settled by regrading.
7. Check the item-scoped diff against the `AGENTS.md` prose rules and run `uv run ruff format
   --check` and `uv run ruff check` on the touched paths; a violation or a failure is
   `revision-needed`.

Report `verified` with the `Verification:` line, or `revision-needed` with concrete reproducible
challenges. Preserve unrelated work; never edit the fix or its tests; do not commit.
