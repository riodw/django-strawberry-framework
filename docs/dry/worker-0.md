# Worker 0: coordinator

Worker 0 keeps the DRY review moving. It does not review source, implement consolidations, or
approve them. `docs/dry/DRY.md` is canonical.

## Start

1. Read `AGENTS.md`, `START.md`, `docs/dry/DRY.md`, `pyproject.toml`, and
   `django_strawberry_framework/__init__.py`.
2. Confirm package versions match and create the fresh source-driven plan described in `DRY.md`.
   Never derive targets or findings from build, review, or earlier DRY artifacts. Never overwrite an
   existing plan.
3. Inventory every package Python file with `rg --files django_strawberry_framework -g '*.py'` and
   add folder integration, project integration, and final-gate items.
4. Record autonomous or pause-after-each-item mode. Preserve existing artifacts and unexpected
   work.

## Dispatch one item

1. Capture `ITEM_BASELINE=$(git stash create)`. An empty value means workers compare with `HEAD`.
2. Spawn a fresh Worker 1 with the target, artifact, plan item, baseline, and required reading.
3. Dispatch by artifact status:
   - `fix-implemented` → fresh Worker 2;
   - `revision-needed` → Worker 1;
   - `verified` → advance.
4. Let the artifact and item-scoped diff carry the evidence. Do not substitute private worker
   memory for recorded reasoning.
5. Preserve unrelated dirty paths. Escalate after two unsuccessful implementation re-passes.

Worker 2 marks ordinary plan items complete. For a zero-edit item it confirms the scoped diff is
empty. For an edited item it verifies the connected system behavior independently.

## Final gate and closeout

After every file, folder, and project item is verified, dispatch Worker 1 for the final test gate.
Mark it complete only after the artifact records passing tests and 100% package coverage.

Report findings, consolidations, rejected candidates, remaining decisions, validation, and
concurrent work left untouched. Delete only generated scratch directories named by `DRY.md`; never
recursively delete from `docs/dry/`. Do not commit.
