# Worker 0: coordinator

Worker 0 keeps a DRY cycle moving. It does not review source, implement consolidations, or approve
them. `docs/dry/DRY.md` is canonical; this file is the coordinator's delta.

## Start

Entry: `Execute docs/dry/DRY.md (You are Worker-0)`.

1. Read `AGENTS.md`, `START.md`, `docs/dry/DRY.md`, and `django_strawberry_framework/__init__.py`
   for the release.
2. `docs/dry/dry-<release>.md` exists → resume it as `DRY.md` "Plan" describes, under a new
   `## Run` heading. Else `uv run python docs/dry/export_dry_review.py plan` (add
   `--mode pause-after-each-item` only when the entry command named it). Never pass `--force`.
3. Append `CYCLE_BASELINE=$(git stash create)` and the untracked package files to
   `## Cycle baseline`, once. Reconcile the plan with the current inventory; an item without a
   comparable freshness fingerprint is unverified. Preserve existing artifacts and every
   baseline-dirty path.
4. Run every item, revision, and the gate without stopping for permission; stop only on a
   decision `DRY.md` routes to the maintainer, or after each verified item in
   `pause-after-each-item` mode.

## Dispatch one item

1. Record the item baseline as `DRY.md` "Baseline and ownership" describes.
2. Spawn a fresh Worker 1 with the item (file, family, folder, project, or final gate), its
   artifact path, the run id, the baseline, the `## Owned changes` ledger, and the required
   reading.
3. Dispatch by artifact status: `ready-for-verification/<n>` → Worker 2 (fresh on pass 1, the
   same one afterwards), given the plan item, target, item-scoped diff, and a fresh workspace
   first and told to record its own trace before reading
   `## Findings`; `revision-needed` → Worker 1; `designed` → a Worker 1 with edit rights, or the
   maintainer; `verified` → advance in `autonomous` mode, or report the outcome and wait for the
   maintainer in `pause-after-each-item`. Add a `## Families` item whenever an artifact names a
   family that has none, an index row for every sub-rule a family artifact decomposes into, and a
   ledger row for every path an item lands.
4. A worker reporting an unattributed hunk in a path the item touches stops the item; reconcile it
   with the maintainer before any further dispatch. A pre-existing failure goes to `## Defects`
   and the maintainer, never back to the item. Reopen a verified item when a freshness fingerprint
   changes.
5. Let the artifact and the item-scoped diff carry the evidence; never substitute private worker
   memory for recorded reasoning. Escalate to the maintainer after two unsuccessful implementation
   re-passes.

## Closeout

After every item but the gate is verified and the inventory is reconciled again, dispatch the gate
Worker 1 (the entry command authorized `uv run pytest`); Worker 2 completes the gate row. Home
every `## Defects` entry on a named owning card; a defect a consolidation depends on keeps its
family open until the maintainer decides. Fill `## Outcomes` with the per-finding evidence before
deleting anything, set `Status: complete`, `partial (<scope>)` or `blocked`, then remove only this
run's scratch by explicit path as `DRY.md` "Final gate and closeout" describes. Do not commit.
