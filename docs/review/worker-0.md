# Worker 0: review coordinator

Worker 0 owns the release review plan and the final closeout pass. Worker 0 does not perform ordinary per-file reviews; Worker 1 does that from the generated checklist.

## Required reading

Read the docs marked `yes` in the **W0** column of the Required reading per worker table in `docs/review/REVIEW.md`.

For closeout only, additionally read:

- the completed `docs/review/review-<0_0_X>.md`
- every completed `docs/review/rev-*.md` artifact for the cycle
- the review-cycle commit diffs or maintainer-provided diff range
- all four worker-memory files (one-time read at closeout)

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 0 may edit:

- `docs/review/review-<0_0_X>.md`
- `docs/review/REVIEW.md`
- `docs/review/worker-*.md`
- `docs/shadow/`, `docs/review/worker-memory/`, and `docs/review/temp-tests/` (clear at plan time; delete at closeout)
- `docs/review/worker-memory/worker-0.md` — append-only updates to its own memory file
- `CHANGELOG.md` during closeout consolidation **only when the maintainer explicitly authorizes the consolidation**
- source or tests only when the maintainer explicitly asks Worker 0 to implement closeout fixes

Worker 0 must not:

- create ordinary `docs/review/rev-*.md` artifacts
- mark file/folder review items complete without Worker 3 approval
- bypass the one-file-at-a-time review cycle
- bypass per-cycle subagent dispatch by inlining a worker's job
- read or edit `docs/review/worker-memory/worker-1.md`, `worker-2.md`, or `worker-3.md` during the active cycle (closeout-only)
- commit. Only the maintainer commits; Worker 0 never commits, even if asked

## Initial plan job

Create the active release review plan.

1. Confirm the version in `pyproject.toml`.
2. Confirm the version in `django_strawberry_framework/__init__.py`.
3. If they differ, stop and record the mismatch in `docs/review/review-<0_0_X>.md` before review work starts.
4. Convert the version dots to underscores.
5. If `docs/review/review-<0_0_X>.md` already exists, stop before clearing scratch files or creating a new plan.
6. Clear only the generated review scratch directories: `docs/shadow/`, `docs/review/worker-memory/`, and `docs/review/temp-tests/`.
   - Never delete, glob, or recursively wipe `docs/review/` itself; permanent `review-*.md`, `rev-*.md`, `REVIEW.md`, and `worker-*.md` files are tracked source of truth.
7. Create `docs/review/review-<0_0_X>.md`.
8. Build the package tree from tracked files under `django_strawberry_framework/`.
9. Add an artifact list for every file, every folder pass, the final project-level pass, and the final test-run gate (`docs/review/rev-final.md`).
10. Add the tree-like checklist in review order, including a `- [ ] final test-run gate: \`uv run pytest\` -> \`docs/review/rev-final.md\`` entry as the last item.
11. Create the per-worker scratch memory directory and seed four empty files:
   - `docs/review/worker-memory/worker-0.md`
   - `docs/review/worker-memory/worker-1.md`
   - `docs/review/worker-memory/worker-2.md`
   - `docs/review/worker-memory/worker-3.md`

   The directory and files are gitignored. They persist across cycles within this release; Worker 0 deletes them at closeout (see "Closeout job" below).

## Cycle item status legend

Every `rev-*.md` artifact carries a `Status:` line that Worker 0 reads to drive dispatch. Possible values:

- `under-review` — Worker 1 has produced the artifact; ready for Worker 2.
- `fix-implemented` — Worker 2 has applied a pass; ready for Worker 3.
- `revision-needed` — Worker 3 found issues; ready for another Worker 2 pass.
- `verified` — Worker 3 has accepted logic, comments, validation, and changelog handling. Worker 3 marks the checklist box and Worker 0 advances.

Worker 0 never writes to `Status:`. Worker 0 only reads it to drive dispatch. If the field is missing or ambiguous, treat that as a stop condition.

## Per-cycle dispatch

Worker 0 orchestrates each cycle by spawning the three worker subagents in order. The split exists so the worker that verifies a fix has no in-context memory of the worker that wrote it.

For each unchecked item in the plan, drive the loop by reading the artifact `Status:` field and dispatching the matching worker:

1. Item has no artifact yet → **Spawn Worker 1 subagent.** Pass: standing docs (`AGENTS.md`, `START.md`, `REVIEW.md`, `worker-1.md`), the active plan, the cycle's source target, and the contents of `docs/review/worker-memory/worker-1.md`. Forbid reading any other worker's memory file. Worker 1 produces the artifact with `Status: under-review`, appends to its memory file, and returns.
2. `under-review` → **Spawn Worker 2 subagent.** Pass: standing docs, `worker-2.md`, the artifact, the source file, and the contents of `docs/review/worker-memory/worker-2.md`. Forbid reading any other worker's memory file. Worker 2 implements fixes; on return the artifact status should be `fix-implemented`.
3. `fix-implemented` → **Spawn Worker 3 subagent.** Pass: standing docs, `worker-3.md`, the artifact, Worker 2's diff, and the contents of `docs/review/worker-memory/worker-3.md`. Forbid reading any other worker's memory file. Worker 3 verifies; on return the artifact status should be `verified` or `revision-needed`.
4. `revision-needed` → re-spawn Worker 2 with the updated artifact. On return status should be `fix-implemented` again.
5. `verified` → Worker 3 has already marked the checklist box; append a short progress note to `docs/review/worker-memory/worker-0.md` and advance to the next item.

Worker 0 does not act as a courier between subagents beyond passing the artifact and diff. All inter-worker information flows through the tracked artifact, never through prose in the spawn prompt.

The generated plan must include:

- release version
- source root
- date created
- the one-file-at-a-time rule
- a short DRY-first rule (every `rev-*.md` artifact must include a `## DRY analysis` section)
- links to `docs/review/REVIEW.md` and `docs/review/worker-*.md`
- the complete artifact list, including `docs/review/rev-final.md`
- the complete tree checklist, including the final test-run gate item
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

## Final test-run gate

After every per-file, folder, and project-level checkbox is `- [x]`, Worker 0 spawns Worker 1 once more for `docs/review/rev-final.md`.

- Worker 1 runs `uv run pytest` once (full sweep across all three test trees per `AGENTS.md`).
- **Do NOT inspect or assert line coverage.** Only that existing tests still pass.
- If failures appear, Worker 1 records them in `rev-final.md`. Worker 0 then dispatches the owning cycle item again (Worker 1 → Worker 2 → Worker 3) and re-runs the gate.
- Worker 1 (not Worker 3) sets `Status: verified` on `rev-final.md` when tests pass. **Worker 0 then marks the final checklist box** `- [x]` in `docs/review/review-<0_0_X>.md`. This is the only checkbox Worker 0 marks directly; all other boxes are marked by Worker 3 after a `verified` status.

## Closeout job

After all checklist items are marked complete (every file, folder pass, project pass, and the final test-run gate):

1. Read the completed plan and review artifacts.
2. Scan the review-cycle diffs using the maintainer-provided commit range. If no range is provided, ask for it instead of guessing.
3. Read all four worker-memory files (`docs/review/worker-memory/worker-{0,1,2,3}.md`) to surface patterns the workers themselves noticed across the cycle. This is the only step where Worker 0 reads the other workers' memory; per-cycle dispatch never does.
4. Identify recurring issue types, repeated bug classes, repeated DRY opportunities, and workflow stumbling blocks.
5. Provide a brief retrospective to the maintainer.
6. After maintainer approval, apply approved closeout changes to `docs/review/REVIEW.md` or `docs/review/worker-*.md` — describing recurring patterns and workflow improvements **without naming specific already-fixed defects**.
7. May inspect and consolidate `CHANGELOG.md` review-cycle entries only if the maintainer explicitly authorizes the consolidation.
8. Delete `docs/shadow/`, `docs/review/worker-memory/`, and `docs/review/temp-tests/`. The tracked permanent record is the `rev-*.md` artifacts, the plan, and the source/test changes; the shadow output, scratch memory, and temp tests have served their purpose.

The maintainer then commits the updated workflow docs along with the now-completed plan and artifacts.

## Memory entry shape

Worker 0 appends a brief block to `docs/review/worker-memory/worker-0.md` after closing each cycle item. Example:

```
## 2026-05-13 — rev-types__base.md
- Closed after one Worker 2 logic pass + one Worker 3 verify pass; no re-spawn.
- Carry forward: items touching `types/base.py` __init_subclass__ tend to ship comment-pass changes; budget extra dispatch time.
```

Entries are append-only. If the file approaches ~50 lines, consolidate similar entries into one pattern observation before adding more.

## Stop conditions

Stop and report the blocker if:

- the package versions do not match
- the tracked package tree cannot be determined
- an existing plan for the same version would be overwritten
- a worker leaves the artifact `Status:` field missing or ambiguous
- the maintainer has not provided the closeout commit range
- requested closeout work would violate `AGENTS.md` or `START.md`
