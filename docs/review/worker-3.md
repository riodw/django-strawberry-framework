# Worker 3: fix verifier

Worker 3 verifies Worker 2's changes against one review artifact. Worker 3 is the only worker role that marks the active review checklist item complete.

## Required reading

Read these before acting:

- `AGENTS.md`
- `START.md`
- `docs/review/REVIEW.md`
- `docs/review/worker-3.md`
- the active `docs/review/review-<0_0_X>.md`
- the current `docs/review/rev-<folder__file_name>.md`
- Worker 2's diff
- the target source file and relevant tests

If Worker 2 used a shadow file, also read the shadow overview or stripped file as a control-flow aid only.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 3 may edit:

- `docs/review/rev-<folder__file_name>.md` to record verification feedback
- `docs/review/review-<0_0_X>.md` to mark the item complete after all gates pass

Worker 3 must not:

- implement Worker 2's source changes
- approve unrelated cleanup
- mark the checkbox complete before logic, comments, validation, and changelog handling are complete
- commit unless the maintainer explicitly asks

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
7. Request another Worker 2 pass if any issue remains unresolved.

Worker 3 may run tests, linting, or focused inspection commands when needed to verify the fix. Prefer repository-documented commands.

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

If feedback is needed, record it in the current `docs/review/rev-<folder__file_name>.md` artifact and stop without marking the checkbox complete.

## Stop conditions

Stop and ask for maintainer direction if:

- the active plan or current artifact is missing
- Worker 2's diff is unavailable
- the checkbox corresponding to the artifact cannot be identified
- validation cannot be run and the risk level requires it
- the fix depends on unresolved package-wide design decisions
