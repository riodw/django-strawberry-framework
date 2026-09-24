# Worker-2: independent verifier

Worker-2 decides whether one item is complete. It challenges the claimed contract, the ownership
decision, and the proof; it never writes the production fix. `docs/dry/DRY.md` is canonical; this
file is the role's delta.

## Required reading

In this order: `AGENTS.md`, `docs/dry/DRY.md`, this file, the plan item, the complete target, the
item-scoped diff including new files, every site the diff touches with its important consumers and
tests, and anything upstream or downstream your own trace needs, in any folder. Then the
artifact. Never Worker-1's `worker-memory/`.

## Job

1. Before opening `## Findings`, record your own trace under
   `## Independent verification (Worker-2)`: sites, roles, definition counts per posited change,
   the owner you would choose. Then read the findings and reconcile every difference explicitly.
2. Check `### Enumeration` member by member against your own count; a sample proves nothing.
   Confirm the matrix was discharged against the target's real surface: judge a claimed
   inapplicability on its reason, and never let a found consolidation excuse an unsearched axis.
3. Confirm the definition counts. Confirm each site's role (definition, consumer, oracle,
   projection) and that no oracle was rewritten to read from the owner it checks.
4. Confirm observable equivalence on the axes of `DRY.md` principle 8, using fresh scratch tests
   under `docs/dry/temp-tests/<scope>/` when execution gives stronger evidence than inspection;
   anything mutating source runs through `workspace.py` at your address `dry/<item>/verify-<n>`,
   whose first run syncs a copy taken after Worker-1's edits, as `DRY.md` "Tests" describes.
   Permanent behavior gaps return to Worker-1 for production tests and fixes.
5. For a zero-edit family, folder, or project item, confirm the scoped diff is empty and search
   independently for a real consolidation before accepting. For a file item, validate coverage and
   assignment and route any candidate to its holding family; never demand a production edit.
6. Confirm every rejected candidate carries its contract difference and trigger, that the
   freshness field carries fingerprints, that each structural gate fails its negative control, that
   `## Pending execution` lists every deferred proof as `proof: <command>` and every witness as
   `gate: <command>`, and that coupled findings are marked so neither can be accepted alone.
7. Check the item-scoped diff against the `AGENTS.md` prose rules: no process provenance,
   `path::Symbol` citations, tests at the mandated tier; run `uv run ruff format --check` and
   `uv run ruff check` on the touched paths. A violation or a failure is `revision-needed`.
   Record any defect you find under `## Defects` marked `(Worker-2)`; do not spend the verdict
   asking Worker-1 to write it.
8. For the final gate, confirm the bound inputs still match the tree and every pending command
   ran, and that each failure is routed by type: a `proof:` failure to its item, a `gate:` failure
   to `## Defects` or the environment record, never to an item.

Set `Status: verified` and tick the plan item (marking it `pending execution` only when a `proof:`
entry remains), or `Status: revision-needed` with concrete named candidates and reproducible
feedback.
Preserve unrelated work; do not commit.

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
