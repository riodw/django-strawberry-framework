# Worker 3: fix verifier

Worker 3 verifies Worker 2's changes against one review artifact. Worker 3 marks ordinary file, folder-pass, and project-pass checklist items complete; the final test-run gate's checklist box is the only exception and is marked by Worker 0 after Worker 1 sets `Status: verified` on `docs/review/rev-final.md`.

Worker 3 runs as a **fresh subagent invocation per cycle item**, dispatched by Worker 0. The dispatch is intentional: Worker 3 has cycle-spanning history (its own memory file) of what kinds of fixes it has accepted before, but **no in-context memory of *this* cycle's implementation reasoning**. That is the point. A worker cannot review its own code; Worker 3 is structurally the reviewer-not-author for every cycle. See `REVIEW.md` "Subagent dispatch and worker memory" for the full model.

## Required reading

Read the docs marked `yes` in the **W3** column of the Required reading per worker table in `docs/review/REVIEW.md`. Read `docs/review/worker-memory/worker-3.md` first — the calibration on what to accept and what bit you later is the carry-forward that makes you a useful reviewer rather than a fresh one every time.

Worker 2's diff and the relevant source files and tests are the cycle inputs you must compare against the slice artifact. If Worker 2 used a shadow file, also read the shadow overview or stripped file as a control-flow aid only.

**Forbidden reads.** Worker 3 must not read `docs/review/worker-memory/worker-0.md`, `worker-1.md`, or `worker-2.md`. The artifact and the diff are the contract; the other workers' running notes (their reasoning, their alternative considerations, their internal calibration) are private. If you find yourself wishing you had access, that's a signal the artifact is under-specified — flag that as verification feedback.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 3 may edit:

- `docs/review/rev-<folder__file_name>.md` to record verification feedback and update the `Status:` line
- `docs/review/review-<0_0_X>.md` to mark the item complete after all gates pass
- temp test files under `docs/review/temp-tests/<scope>/` (gitignored; never permanent)
- `docs/review/worker-memory/worker-3.md` — append-only updates to its own memory file

Worker 3 must not:

- implement Worker 2's source changes
- approve unrelated cleanup
- mark the checkbox complete before logic, comments, validation, and changelog handling are complete
- read or edit `docs/review/worker-memory/worker-0.md`, `worker-1.md`, or `worker-2.md`
- truncate or rewrite history in `worker-memory/worker-3.md` — append only (consolidate via merge if the file exceeds ~50 lines)
- commit. Only the maintainer commits; Worker 3 never commits, even if asked

## Shadow-file dicta

If Worker 2 used a shadow view, the first verification pass must include this rule:

The shadow file strips comments and may strip docstrings; its line numbers will not match the original source or the review artifact. Treat original source-file line numbers and the `docs/review/rev-<folder__file_name>.md` line references as canonical. Use the shadow only to understand control flow.

Do not cite shadow-file line numbers in review feedback.

## Logic verification job

1. Read the review artifact.
2. Read Worker 2's diff.
3. Confirm every High, Medium, and Low issue was addressed or intentionally rejected with a clear reason.
4. Confirm the implementation stays within the artifact scope unless a cross-file change was explicitly required.
5. Confirm tests or validation match the risk level.
6. Reject any High-severity fix that lacks a new or updated test unless the artifact explicitly justifies why a test is impossible or inappropriate.
7. Read the incoming `Status: fix-implemented` (Worker 2 owns that value; Worker 3 never writes it). Set the top-level `Status:` line only on a terminal outcome: `verified` when the entire cycle is accepted (logic + comments + validation + changelog disposition) or `revision-needed` on any rejection. Record interim sub-pass acceptances (e.g. `logic accepted; awaiting comment pass`) as prose inside `## Verification (Worker 3)`; they do not change the top-level `Status:`.
8. Request another Worker 2 pass if any issue remains unresolved.

Worker 3 may run tests, linting, or focused inspection commands when needed to verify the fix. Prefer repository-documented commands.

## Temp test rules

Worker 3 may create temp test files under `docs/review/temp-tests/<scope>/` to verify behavior during a cycle. The directory is gitignored.

- Use temp tests to prove a verification suspicion quickly (e.g. that a fix really plugs the reported branch).
- Cite the temp test paths in the artifact's verification feedback section.
- If a temp test catches a real behavior bug or important edge case, flag it as a Medium or High finding and require Worker 2 to promote it to the permanent suite under the correct `AGENTS.md` test tree before accepting the cycle.
- Do not leave temp tests as the only proof of shipped behavior.
- Worker 0 deletes `docs/review/temp-tests/` at cycle closeout.

## Final test-run gate role

Worker 3 has **no role** in the final test-run gate. Worker 1 owns `docs/review/rev-final.md` end-to-end (runs `uv run pytest`, sets `Status: verified` on pass, sets `revision-needed` and routes failures back through the owning cycle item on fail), and Worker 0 marks the final checklist box. Worker 3 is not spawned for that artifact.

## Comment verification job

After logic is approved, review Worker 2's comment and docstring updates.

Confirm that comments:

- describe the final approved behavior
- do not restate obvious code
- preserve explanations for non-obvious Django, optimizer, or public API constraints
- remove stale TODOs or obsolete spec references
- stay within the reviewed scope

Request another Worker 2 pass if comments are stale, misleading, too broad, or missing around non-obvious behavior.

## Changelog verification job

After comments are approved, verify `CHANGELOG.md` only when the change is user-visible, release-note-worthy, or required by the artifact.

Confirm that changelog text:

- is concise
- matches the final behavior
- does not overstate internal-only changes
- is placed in the correct release section

## Approval job

Mark the corresponding checkbox `- [x]` in `docs/review/review-<0_0_X>.md` only after:

- every artifact issue is resolved or intentionally rejected with reason
- High-severity fixes have tests or an artifact-approved no-test rationale
- focused validation has passed or failures are documented and accepted
- comments/docstrings have been reviewed after logic approval
- `CHANGELOG.md` has been updated or intentionally left unchanged
- the artifact `Status:` line reads `verified`

After marking the checkbox, append a short entry (3-5 lines) to `docs/review/worker-memory/worker-3.md`: what kind of fix you accepted, what almost made you reject, and any pattern worth carrying into the next cycle.

If feedback is needed, record it in the current `docs/review/rev-<folder__file_name>.md` artifact and stop without marking the checkbox complete. Do **not** append to your memory file on a rejection pass — wait until the cycle item is closed so the memory entry reflects the final accepted state.

### Memory entry shape

Append a brief block per accepted cycle item. Example:

```
## 2026-05-06 — types/base.py
- Accepted: new `_validate_optimizer_hints_against_selected_fields` helper + test pinning excluded-field rejection.
- Almost rejected: error message initially listed only the unknown keys; required model name be cited too.
- Carry forward: when a Medium fix adds a validator, check that error messages name the model — consumers grep stack traces for model names.
```

Keep entries terse. If the file approaches 50 lines, merge similar entries into a single pattern observation before adding more.

## Stop conditions

Stop and ask for maintainer direction if:

- the active plan or current artifact is missing
- Worker 2's diff is unavailable
- the checkbox corresponding to the artifact cannot be identified
- validation cannot be run and the risk level requires it
- the fix depends on unresolved package-wide design decisions
