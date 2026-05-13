# Remaining feedback: build/review workflow verification

## Overall assessment

The top-level build and review workflows are now much closer architecturally. They remain properly sandboxed under `docs/build/` and `docs/review/`, and they now share the same core shape: DRY-first discipline, generated plan, tracked artifacts, Worker 0 orchestration, Worker 1 analysis, Worker 2 mutation, Worker 3 independent verification, private worker memory, temp/shadow directories, maintainer-only commits, and a final `uv run pytest` gate.

The remaining inconsistencies are mostly stale role-file language inside the review workflow. `docs/review/REVIEW.md` now states the desired architecture, but a few `docs/review/worker-*.md` sections still describe the older lifecycle. There is also one build Worker 3 helper-rule drift from `docs/build/BUILD.md`.

## High-priority feedback

### 1. `verified` still means two different things in the review artifact template

`docs/review/REVIEW.md:262` says that after logic verification reaches `verified`, Worker 2 returns for a comment/docstring pass and the status later moves back to `fix-implemented`. But the status legend at `docs/review/REVIEW.md:290` defines `verified` as the final state after logic, comments, validation, and changelog handling are all accepted, and says Worker 3 then marks the checklist.

Recommendation: do not use top-level `Status: verified` for logic-only acceptance. Use wording like "after Worker 3 accepts the logic pass" inside the comment/docstring section, and reserve top-level `verified` for the final completed cycle item.

### 2. Worker 3 still claims ownership of the final test-run gate

`docs/review/REVIEW.md:648` and `docs/review/worker-0.md:132` say Worker 1 owns `docs/review/rev-final.md` end-to-end and Worker 0 marks the final checklist box; Worker 3 is not part of the final gate. `docs/review/worker-3.md:86` still says Worker 3 verifies the final gate artifact like any other cycle item.

Recommendation: remove Worker 3's final test-run gate role, or replace it with an explicit note that Worker 3 has no role in `rev-final.md`.

### 3. Worker 3 still claims it sets `fix-implemented`

The status legend in `docs/review/REVIEW.md:287` says Worker 2 owns `fix-implemented`. `docs/review/worker-3.md:68` still tells Worker 3 to set the artifact status to `fix-implemented` when verifying a fresh pass.

Recommendation: Worker 3 should read an incoming `fix-implemented` status and then set only `verified` or `revision-needed`. Worker 2 should remain the sole owner of `fix-implemented`.

## Medium-priority feedback

### 4. Worker 0's review-plan instructions still omit the final gate and DRY-first rule

`docs/review/REVIEW.md:113` requires generated review plans to include `docs/review/rev-final.md` and a DRY-first rule. `docs/review/worker-0.md:49` still says to add artifacts for every file, every folder pass, and the final project-level pass, but not the final test-run gate. The generated-plan checklist in `docs/review/worker-0.md:101` also omits the final gate and DRY-first rule from the required plan contents.

Recommendation: update Worker 0's role file so it independently requires `rev-final.md`, the final-gate checklist item, and the DRY-first rule in generated review plans.

### 5. Worker 1 owns the final gate in `REVIEW.md`, but its role file does not define the job

`docs/review/REVIEW.md:648` says Worker 1 writes `rev-final.md`, runs `uv run pytest`, and sets `Status: verified` when tests pass. `docs/review/worker-1.md:29` only allows Worker 1 to create or replace `docs/review/rev-<folder__file_name>.md`, and its job section only covers file, folder, and final project pass reviews.

Recommendation: add a Worker 1 final-gate section and scope entry for `docs/review/rev-final.md`: run `uv run pytest`, record the result, set `Status: verified` on pass, and stop. Make clear this gate bypasses Worker 2 and Worker 3.

### 6. Worker 2's changelog scope still uses the old authorization rule

`docs/review/REVIEW.md:655` and `docs/review/worker-2.md:109` say `CHANGELOG.md` edits require active review-plan or maintainer authorization. But `docs/review/worker-2.md:24` says Worker 2 may edit `CHANGELOG.md` after comment approval when a change is user-visible or release-note-worthy, and `docs/review/worker-2.md:49` says to update `CHANGELOG.md` if needed.

Recommendation: align Worker 2's scope and job steps with the stricter rule: record changelog disposition every time, but edit `CHANGELOG.md` only with explicit plan or maintainer authorization.

### 7. Review helper examples still omit the sandbox output directory

`docs/review/REVIEW.md:397` says every review-cycle helper invocation must pass `--output-dir docs/review/shadow`. The examples in `docs/review/worker-1.md:124` and `docs/review/worker-2.md:94` omit that flag.

Recommendation: add `--output-dir docs/review/shadow` to the worker role examples so the quick-start commands match the sandbox rule.

### 8. Build Worker 3 helper quick rules drift from `BUILD.md`

`docs/build/BUILD.md` has precise helper triggers for Worker 3: new `.py` files with a pure-class exception, existing files under `optimizer/` or `types/`, 30+ lines of package logic, and 50+ lines outside the package. `docs/build/worker-3.md:72` simplifies this to new `.py`, `types/` or `optimizer/`, and more than ~50 lines in any file.

Recommendation: either duplicate the exact trigger list from `BUILD.md` or make `worker-3.md` point only to the canonical `BUILD.md` rules. The current abbreviated version under-enforces package changes between 30 and 50 lines.

## Low-priority feedback

### 9. Worker 3's intro should mention the final-gate exception

`docs/review/worker-3.md:3` says Worker 3 is the only worker role that marks the active review checklist item complete. That is no longer true for `rev-final.md`, where Worker 0 marks the final checklist box after Worker 1 sets `Status: verified`.

Recommendation: change the sentence to say Worker 3 marks ordinary file/folder/project review items complete, while Worker 0 marks the final test-run gate.

### 10. Worker 0's changelog scope should include the authorization caveat

`docs/review/worker-0.md:27` says Worker 0 may edit `CHANGELOG.md` during closeout consolidation. The closeout job later adds the correct authorization guard at `docs/review/worker-0.md:136`.

Recommendation: add "only when the maintainer explicitly authorizes consolidation" to the Scope bullet too, so the role file does not rely on a later section to narrow the permission.

## What looks fixed

- `docs/review/REVIEW.md` now has a required-reading matrix.
- The generated review plan now includes a DRY-first rule and `rev-final.md`.
- The review artifact template now captures Worker 2 reports, Worker 3 verification, comments/docstrings, changelog disposition, and iteration logs.
- Review helper output is now explicitly sandboxed under `docs/review/shadow/` in the top-level review workflow.
- The review plan is now treated as a checklist/progress tracker, not a findings log.
- Build Low-severity acceptance language is now consistent in `docs/build/BUILD.md` and `docs/build/worker-3.md`.
