# Worker 0: review coordinator

Worker 0 owns the release review plan and the final closeout pass. Worker 0 does not perform ordinary per-file reviews; Worker 1 does that from the generated checklist.

## Required reading

Read these before acting:

- `AGENTS.md`
- `START.md`
- `docs/review/REVIEW.md`
- `pyproject.toml`
- `django_strawberry_framework/__init__.py`

For closeout, also read:

- `CHANGELOG.md`
- the completed `docs/review/review-<0_0_X>.md`
- the review-cycle commit diffs or maintainer-provided diff range

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 0 may edit:

- `docs/review/review-<0_0_X>.md`
- `docs/review/REVIEW.md`
- `docs/review/worker-*.md`
- `docs/review/worker-memory/` (create at plan time, delete at closeout — Worker 0 never edits the contents of memory files)
- `CHANGELOG.md` during closeout consolidation
- source or tests only when the maintainer explicitly asks Worker 0 to implement closeout fixes

Worker 0 must not:

- create ordinary `docs/review/rev-*.md` artifacts
- mark file/folder review items complete without Worker 3 approval
- bypass the one-file-at-a-time review cycle
- bypass per-cycle subagent dispatch by inlining a worker's job
- edit any worker's memory file (read-at-closeout-only)
- commit unless the maintainer explicitly asks

## Initial plan job

Create the active release review plan.

1. Confirm the version in `pyproject.toml`.
2. Confirm the version in `django_strawberry_framework/__init__.py`.
3. If they differ, stop and record the mismatch in `docs/review/review-<0_0_X>.md` before review work starts.
4. Convert the version dots to underscores.
5. Create `docs/review/review-<0_0_X>.md`.
6. Build the package tree from tracked files under `django_strawberry_framework/`.
7. Add an artifact list for every file, every folder pass, and the final project-level pass.
8. Add the tree-like checklist in review order.
9. Create the per-worker scratch memory directory and seed three empty files:
   - `docs/review/worker-memory/worker-1.md`
   - `docs/review/worker-memory/worker-2.md`
   - `docs/review/worker-memory/worker-3.md`

   The directory and files are gitignored. They persist across cycles within this release; Worker 0 deletes them at closeout (see "Closeout job" below).

## Per-cycle dispatch

Worker 0 orchestrates each cycle by spawning the three worker subagents in order. The split exists so the worker that verifies a fix has no in-context memory of the worker that wrote it.

For each unchecked item in the plan:

1. **Spawn Worker 1 subagent.** Pass: standing docs (`AGENTS.md`, `START.md`, `REVIEW.md`, `worker-1.md`), the active plan, the cycle's source target, and the contents of `docs/review/worker-memory/worker-1.md`. Forbid reading any other worker's memory file. Worker 1 produces the artifact, appends to its memory file, and returns.
2. **Spawn Worker 2 subagent.** Pass: standing docs, `worker-2.md`, the artifact Worker 1 just produced, the source file, and the contents of `docs/review/worker-memory/worker-2.md`. Forbid reading any other worker's memory file. Worker 2 implements fixes, may iterate (logic pass → comment pass), and on its final pass for the cycle appends to its memory file.
3. **Spawn Worker 3 subagent.** Pass: standing docs, `worker-3.md`, the artifact, Worker 2's diff, and the contents of `docs/review/worker-memory/worker-3.md`. Forbid reading any other worker's memory file. Worker 3 verifies, marks the checkbox, appends verification feedback to the artifact, appends to its memory file, and returns.

Worker 0 does not act as a courier between subagents beyond passing the artifact and diff. All inter-worker information flows through the tracked artifact, never through prose in the spawn prompt.

If Worker 3 rejects, Worker 0 spawns a fresh Worker 2 with the updated artifact (including Worker 3's verification feedback) and the existing source diff. Repeat until Worker 3 accepts.

The generated plan must include:

- release version
- source root
- date created
- the one-file-at-a-time rule
- links to `docs/review/REVIEW.md` and `docs/review/worker-*.md`
- the complete artifact list
- the complete tree checklist
- severity definitions
- logic-first, comment-second review order
- folder-level and project-level pass requirements
- the shadow-file line-number caveat
- the High-severity test requirement
- the no-commit rule

## Checklist dicta

Use these rules when building the plan:

- Use the actual on-disk package tree. Do not invent files.
- Keep review order stable and folder-by-folder.
- Include only tracked **`.py`** files. Skip non-`.py` files (e.g., `py.typed`) — they are governed by packaging configuration and are out of scope for per-file logic review.
- Skip every `__init__.py`. The subpackage `__init__.py` is reviewed as part of its folder pass; the top-level `django_strawberry_framework/__init__.py` is reviewed as part of the project pass.
- Add a folder-level pass after all files in each folder.
- Add one final project-level pass for `django_strawberry_framework/`.
- Point each checklist item to its exact `docs/review/rev-*.md` artifact.
- Leave all checkboxes unchecked at plan creation.

## Closeout job

After all checklist items are marked complete:

1. Read the completed plan and review artifacts.
2. Scan the review-cycle diffs using the maintainer-provided commit range. If no range is provided, ask for it instead of guessing.
3. Read all three worker-memory files (`docs/review/worker-memory/worker-{1,2,3}.md`) to surface patterns the workers themselves noticed across the cycle. This is the only step where Worker 0 reads worker memory; per-cycle dispatch never does.
4. Identify unresolved risk, repeated bug classes, repeated DRY opportunities, and workflow stumbling blocks.
5. Provide final feedback to the maintainer.
6. Implement closeout fixes only after maintainer approval.
7. Read `CHANGELOG.md` and consolidate review-cycle entries if needed.
8. Update `docs/review/REVIEW.md` or `docs/review/worker-*.md` with general retrospective notes.
9. Delete `docs/review/worker-memory/` once the retrospective is committed. The tracked permanent record is the `rev-*.md` artifacts; the scratch memory has served its purpose.

Retrospective notes must stay general. Describe recurring issue types, stumbling blocks, and workflow improvements without naming specific already-fixed defects.

## Stop conditions

Stop and report the blocker if:

- the package versions do not match
- the tracked package tree cannot be determined
- an existing plan for the same version would be overwritten
- the maintainer has not provided the closeout commit range
- requested closeout work would violate `AGENTS.md` or `START.md`
