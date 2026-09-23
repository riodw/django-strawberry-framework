# Worker 1: hunter and implementer

Worker 1 owns one item: a file, a scenario, or the package integration pass. It breaks things in a
disposable workspace, confirms defects with attributable evidence, and lands root-cause fixes with
permanent tests. `docs/bug_hunt/HUNT.md` is canonical; this file is the role's delta.

## Required reading

`AGENTS.md`, `START.md`, `docs/bug_hunt/HUNT.md`, this file, the progress file (read only), the
item's shadow inputs when present, the complete live target, and every connected source, test,
example, doc and contract a sound judgment needs, upstream and downstream, in any folder: the
item fences your fix, never your reading. `## Package questions` guide exploration and
never define results. Prior hunt records and `pbugs.md` are leads with provenance, revalidated on
the current source.

## Job

1. Build the workspace as `HUNT.md` "Workspace" describes and print its package path and database
   target into the record before the first probe.
2. Record the contract row for every boundary you will probe. A boundary nobody can cite a contract
   for is reported `Blocked`, never fixed.
3. Break things inside the workspace; discharge every axis of the mandatory matrix with a probe or
   a one-line reason; keep the evidence record for every claim.
4. Confirm each candidate against its contract row with Defect, Evidence, Impact, Severity and
   Proof; try to disprove it first.
5. Implement the root-cause fix at the owner in the shared tree, attributing every hunk of a dirty
   path to the ledger or the cycle baseline first; add the permanent test in the same change; run
   only focused `uv run pytest <path> --no-cov`, then `uv run ruff check --fix .` and
   `uv run ruff format .` last, until `uv run ruff format --check` and `uv run ruff check` both
   pass on the paths you touched.
6. Report as `HUNT.md` "Worker 1" lists, including every scratch and workspace path left in place
   and the digests of the inputs inspected. Never clean up, never edit the progress file, never
   touch `CHANGELOG.md`, never commit.

A client-reachable isolation or authorization defect is reported abstractly with its evidence held
in scratch; the maintainer decides disclosure before any reproducer lands in a tracked file.

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
