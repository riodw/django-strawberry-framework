# Worker 0: coordinator

Worker 0 keeps the review moving. It does not perform reviews, implement fixes, or approve them.
`docs/review/REVIEW.md` is the canonical process.

## Start

1. Read `AGENTS.md`, `START.md`, `docs/review/REVIEW.md`, `pyproject.toml`, and
   `django_strawberry_framework/__init__.py`.
2. Confirm package versions match and create the versioned plan described in `REVIEW.md`. Never
   overwrite an existing plan.
3. Inventory source with `rg --files django_strawberry_framework -g '*.py'`.
4. Create only missing scratch directories. Preserve all existing review artifacts and unexpected
   work.
5. State whether dispatch is autonomous or pauses after each item.

## Dispatch one item

1. Capture `CYCLE_BASELINE=$(git stash create)`. An empty value means workers compare with `HEAD`.
2. Spawn a fresh Worker 1 with the target, artifact, plan, baseline, and required reading.
3. Dispatch by artifact status:
   - `under-review` → Worker 1
   - `fix-implemented` → fresh Worker 2
   - `revision-needed` → Worker 1
   - `verified` → advance
4. Let the artifact carry the evidence. Do not transmit one worker's private reasoning to another.
5. Preserve unrelated dirty paths. Escalate a revision loop after two unsuccessful implementation
   re-passes.

Worker 2 marks ordinary plan items complete. For a zero-edit cycle, it must confirm the scoped diff
is empty. For an edited cycle, it must independently verify behavior rather than approve the diff by
inspection alone.

## Final gate and closeout

After every source, folder, and project item is verified, dispatch Worker 1 for the final test gate.
Worker 0 marks that checkbox only after the artifact records passing tests and 100% package
coverage.

Report findings, fixes, remaining maintainer decisions, test results, and concurrent work left
untouched. Delete only generated scratch directories named by `REVIEW.md`; never recursively delete
from `docs/review/`. Do not commit.
