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
12. Refresh the shadow overviews for every in-scope file in one shot:

    ```shell
    python scripts/review_inspect.py --all --output-dir docs/shadow
    ```

   Running the helper once at plan time (rather than per-file inside each Worker 1 spawn) is cheaper and keeps every spawn's shadow available the moment Worker 1 reads its memory file. Worker 1 may still re-run the helper on a single target if a fix-pass needs a fresh overview, but the initial sweep belongs to plan creation.

## Cycle item status legend

Every `rev-*.md` artifact carries a `Status:` line that Worker 0 reads to drive dispatch. Possible values:

- `under-review` — Worker 1 has produced the artifact; ready for Worker 2.
- `fix-implemented` — Worker 2 has applied a pass; ready for Worker 3.
- `revision-needed` — Worker 3 found issues; ready for another Worker 2 pass.
- `verified` — Worker 3 has accepted logic, comments, validation, and changelog handling. Worker 3 marks the checklist box and Worker 0 advances.

Worker 0 never writes to `Status:`. Worker 0 only reads it to drive dispatch. If the field is missing or ambiguous, treat that as a stop condition.

## Per-cycle dispatch

Default mode is **autonomous** — Worker 0 continues cycle-to-cycle, notifying the maintainer only at run boundaries (start, end, fatal blockers, two consecutive `revision-needed` outcomes). Maintainer-pause mode is opt-in via "review one at a time" / "pause after each cycle" / a single named item in the dispatch prompt.

Read the bare `Status:` (everything before any `(`) and dispatch per the Status legend table in `REVIEW.md`. Standing-docs sets per spawn:

| Spawn | Pass | Do NOT pass |
|---|---|---|
| Worker 1 | AGENTS.md, START.md, REVIEW.md, worker-1.md, active plan, source target, worker-memory/worker-1.md, `$CYCLE_BASELINE` | other workers' memory |
| Worker 2 | AGENTS.md, START.md, worker-2.md, artifact, source/tests, worker-memory/worker-2.md, `$CYCLE_BASELINE` | REVIEW.md, active plan (unless ambiguous), CHANGELOG.md (unless authorised), other workers' memory |
| Worker 3 | AGENTS.md, worker-3.md, artifact, source/tests, worker-memory/worker-3.md, `$CYCLE_BASELINE` | START.md, REVIEW.md, CHANGELOG.md, other workers' memory |

Worker 0 is not a courier — all inter-worker information flows through the tracked artifact, the diff, and `$CYCLE_BASELINE`. At cycle close: run the re-check, append a closure note, discard the baseline, advance.

### Per-cycle baseline

```shell
CYCLE_BASELINE=$(git stash create)  # at cycle start; empty SHA if working tree clean
```

Pass the SHA to every dispatch this cycle. Cycle diffs use `git diff "$CYCLE_BASELINE" -- …`. Empty SHA → use HEAD. Stash-create commits don't appear on the stash stack; Git reflog-GCs them.

**Concurrent-work fallbacks.** `git stash create` fails when the index has staged entries (e.g. a concurrent maintainer commit-in-progress) — fall back to baseline HEAD and have subagents scope to the specific cycle file (`git diff HEAD -- <target>`); since each item touches distinct files, file-scoped diffs stay clean even with accumulated review work in other files. **Drift re-open:** if the run spans concurrent maintainer commits, an already-`verified` artifact whose source later changed is stale — re-open it (uncheck the box, re-run the full cycle against current source) before the final gate. Refresh `docs/shadow/` (`--all`) after any such gap so reviews read current source.

### Cycle-closing re-check

Diffs always scope via `$CYCLE_BASELINE`. Tiered:

- **Skip** when the cycle diff is empty (shape #5, recording-only forwards, all-Lows-forward-looking).
- **Worker 0 inline** when diff is comments/docstrings only — every hunk inside a docstring/comment, no source-logic lines, `tests/` untouched.
- **Worker 1 spawn** for logic edits, test changes, or cross-file refactors. No judgment-skipping when those apply.

Plan header + checklist follow the template in `REVIEW.md` "Required plan structure". Per-cycle build rules:

- Use the actual on-disk package tree; do not invent files.
- Tracked **`.py`** files only. Skip non-`.py` (e.g. `py.typed`) and every `__init__.py` (covered by folder/project pass per `REVIEW.md` "Review scope").
- Folder-by-folder order; one folder pass per folder; one project pass at the end; `rev-final.md` last.
- Point each checklist item at its exact `docs/review/rev-*.md` artifact.
- All checkboxes unchecked at creation.

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
## rev-types__base.md
- Closed after one Worker 2 logic pass + one Worker 3 verify pass; no re-spawn.
- Carry forward: items touching `types/base.py` __init_subclass__ tend to ship comment-pass changes; budget extra dispatch time.
```

Entries are append-only. Consolidate similar entries when approaching ~75 lines.

## Stop conditions

Stop and report the blocker if:

- the package versions do not match
- the tracked package tree cannot be determined
- an existing plan for the same version would be overwritten
- a worker leaves the artifact `Status:` field missing or ambiguous
- the maintainer has not provided the closeout commit range
- requested closeout work would violate `AGENTS.md` or `START.md`
