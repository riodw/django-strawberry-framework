# Worker 0: coordinator

Worker 0 keeps a DRY cycle moving. It does not review source, implement consolidations, or approve
them. `docs/dry/DRY.md` is canonical; this file is the coordinator's delta.

## Start

1. Read `AGENTS.md`, `START.md`, `docs/dry/DRY.md`, and `django_strawberry_framework/__init__.py`
   for the release.
2. Create the plan as `DRY.md` "Plan" describes, or continue the release's existing plan under a
   dated `## Run` heading. Never pass `--force`. Append `## Responsibility index`, `## Families`,
   and `## Outcomes`.
3. Record the mode. Preserve existing artifacts and every baseline-dirty path.

## Dispatch one item

1. Record the baseline as `DRY.md` "Baseline" describes.
2. Spawn a fresh Worker 1 with the item (file, family, folder, project, or final gate), its
   artifact path, the baseline, and the required reading.
3. Dispatch by artifact status: `fix-implemented` → fresh Worker 2; `revision-needed` →
   Worker 1; `designed` → a Worker 1 with edit rights, or the maintainer; `verified` → advance.
   Add a `## Families` item whenever an artifact names a family that has none, and an index row
   for every sub-rule a family artifact decomposes into.
4. Reopen a verified item when an input its freshness field names changes.
5. Let the artifact and the item-scoped diff carry the evidence; never substitute private worker
   memory for recorded reasoning. Escalate to the maintainer after two unsuccessful implementation
   re-passes.

## Closeout

Dispatch Worker 1 for the final gate only after every item is verified, and only with the
maintainer's explicit pytest authorization. Home every `## Defects` entry on a named owning card.
Fill `## Outcomes` before deleting anything, then remove
only this run's scratch by explicit path as `DRY.md` "Final gate and closeout" describes. Do not
commit.
