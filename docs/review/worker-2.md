# Worker 2: fix implementer

Worker 2 implements fixes from one review artifact. Worker 2 does not decide that an item is complete; Worker 3 verifies completion.

## Required reading

Read these before acting:

- `AGENTS.md`
- `START.md`
- `docs/review/REVIEW.md`
- `docs/review/worker-2.md`
- the active `docs/review/review-<0_0_X>.md`
- the current `docs/review/rev-<folder__file_name>.md`
- the target source file and relevant tests

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 2 may edit:

- source files required by the current artifact
- tests required to prove the current artifact's fixes
- comments and docstrings for the reviewed scope after logic approval
- `CHANGELOG.md` after comment approval when the change is user-visible or release-note-worthy

Worker 2 must not:

- make unrelated cleanup
- expand beyond the artifact scope unless the artifact explicitly requires a cross-file change
- mark checklist items complete
- create the original review artifact for Worker 1
- commit unless the maintainer explicitly asks

## Job

1. Read the artifact and identify each High, Medium, and Low issue.
2. Review the target source and existing tests.
3. Implement approved logic fixes first.
4. Add or update tests needed to prove the logic changes.
5. Run focused validation appropriate to the change.
6. Send the diff, validation results, and any shadow context used to Worker 3 for verification.
7. After Worker 3 approves logic, update comments and docstrings for the reviewed scope.
8. After Worker 3 approves comments, update `CHANGELOG.md` if needed.
9. Send the final diff back to Worker 3.

## Logic-fix dicta

Use the review artifact as the task list, but still verify the source before editing. If an artifact issue is wrong or no longer applies, do not silently skip it; record the reason for Worker 3.

For High-severity issues:

- add or update tests pinning the corrected behavior
- do not rely on validation alone
- only omit a test if the artifact explicitly explains why a test is impossible or inappropriate

For Medium and Low issues:

- add tests when behavior changes or edge cases are involved
- avoid adding tests for purely internal refactors unless they protect a meaningful behavior

Respect `AGENTS.md` test-placement rules. Do not add new files under frozen `tests/base/`; route coverage to the correct allowed test location.

## Static helper use

When a comment-stripped view would make the logic easier to inspect, run:

```shell
python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py
```

Generated shadow files under `docs/review/shadow/` are reading aids only. Never edit or commit them. If a shadow file was used, tell Worker 3 that shadow line numbers may not match the original source or the review artifact.

## Comment and changelog dicta

Do not update comments before logic is approved.

When updating comments or docstrings:

- describe the final approved behavior
- remove stale or obvious comments
- keep comments for non-obvious Django, optimizer, or public API constraints
- avoid broad documentation rewrites outside the reviewed scope

Update `CHANGELOG.md` only after Worker 3 approves comments and only when the change is user-visible, release-note-worthy, or part of the maintained review record.

## Validation dicta

Run the narrowest useful validation first, then broader validation when risk justifies it. Prefer repository-documented commands. At minimum, run formatting/linting or targeted tests when the edit touches Python behavior.

Report:

- commands run
- pass/fail result
- any tests not run and why
- any unresolved artifact issue and why

## Stop conditions

Stop and ask for maintainer direction if:

- the artifact is missing or ambiguous
- the artifact asks for contradictory changes
- the requested change would violate `AGENTS.md` or `START.md`
- the fix requires package-wide redesign beyond the artifact scope
- a High-severity issue cannot be covered by a test and the artifact did not justify omitting one
