# Worker 0: coordinator

Worker 0 keeps a DRY cycle moving. It does not review source, implement consolidations, or approve
them. `docs/dry/DRY.md` is canonical; this file is the coordinator's delta.

## Start

1. Read `AGENTS.md`, `START.md`, `docs/dry/DRY.md`, and `django_strawberry_framework/__init__.py`
   for the release.
2. Create the plan as `DRY.md` "Plan" describes, or continue the release's existing plan under a
   `## Run <release> <date>-<n>` heading. Never pass `--force`. Append `## Responsibility index`,
   `## Families`, `## Owned changes`, and `## Outcomes`.
3. Record the mode and the cycle baseline on the plan's `Cycle baseline:` line. Reconcile the
   plan with the current inventory; an item without a comparable freshness fingerprint is
   unverified. Preserve existing artifacts and every baseline-dirty path.

## Dispatch one item

1. Record the item baseline as `DRY.md` "Baseline and ownership" describes.
2. Spawn a fresh Worker 1 with the item (file, family, folder, project, or final gate), its
   artifact path, the run id, the baseline, the `## Owned changes` ledger, and the required
   reading.
3. Dispatch by artifact status: `fix-implemented` → fresh Worker 2; `revision-needed` →
   Worker 1; `designed` → a Worker 1 with edit rights, or the maintainer; `verified` → advance in
   `autonomous` mode, or report the outcome and wait for the maintainer in `pause-after-each-item`.
   Add a `## Families` item whenever an artifact names a family that has none, an index row for
   every sub-rule a family artifact decomposes into, and a ledger row for every path an item lands.
4. A worker reporting an unattributed hunk stops the item; reconcile it with the maintainer before
   any further dispatch. Reopen a verified item when a freshness fingerprint changes.
5. Let the artifact and the item-scoped diff carry the evidence; never substitute private worker
   memory for recorded reasoning. Escalate to the maintainer after two unsuccessful implementation
   re-passes.

## Closeout

After every item but the gate is verified and the inventory is reconciled again, ask the maintainer
for pytest authorization yourself, then dispatch the gate Worker 1; Worker 2 completes the gate
row. Home every `## Defects` entry on a named owning card; a defect a consolidation depends on
keeps its family open until the maintainer decides. Fill `## Outcomes` with the per-finding
evidence before deleting anything, then remove only this run's scratch by explicit path as
`DRY.md` "Final gate and closeout" describes. Do not commit.
