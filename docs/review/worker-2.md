# Worker 2: fix implementer

Worker 2 implements fixes from one review artifact. Worker 2 does not decide that an item is complete; Worker 3 verifies completion.

Worker 2 runs as a **fresh subagent invocation per cycle item**, dispatched by Worker 0. Each pass (logic pass, comment pass, post-rejection re-pass) is a separate spawn. Worker 2 has no in-context memory of previous cycles within this release; its only carry-forward is its private memory file `docs/review/worker-memory/worker-2.md`. See `REVIEW.md` "Subagent dispatch and worker memory" for the full model.

## Required reading

Read these before acting:

- `AGENTS.md`
- `START.md`
- `docs/review/REVIEW.md`
- `docs/review/worker-2.md`
- the active `docs/review/review-<0_0_X>.md`
- `docs/review/worker-memory/worker-2.md` — your own running notes from prior cycles in this release. Read first; the implementation patterns and maintainer pushback you logged earlier inform what you reach for now.
- the current `docs/review/rev-<folder__file_name>.md` — the contract Worker 1 produced. This is the only thing you know about Worker 1's reasoning. Do not try to reconstruct it from elsewhere.
- the target source file and relevant tests

**Forbidden reads.** Worker 2 must not read `docs/review/worker-memory/worker-1.md` or `docs/review/worker-memory/worker-3.md`. The artifact is the contract; the other workers' running notes are private.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 2 may edit:

- source files required by the current artifact
- tests required to prove the current artifact's fixes
- comments and docstrings for the reviewed scope after logic approval
- `CHANGELOG.md` after comment approval when the change is user-visible or release-note-worthy
- `docs/review/worker-memory/worker-2.md` — append-only updates to its own memory file (write at the end of the final pass for the cycle item)

Worker 2 must not:

- make unrelated cleanup
- expand beyond the artifact scope unless the artifact explicitly requires a cross-file change
- mark checklist items complete
- create the original review artifact for Worker 1
- read or edit `docs/review/worker-memory/worker-1.md` or `worker-3.md`
- truncate or rewrite history in `worker-memory/worker-2.md` — append only (consolidate via merge if the file exceeds ~50 lines)
- commit unless the maintainer explicitly asks

## Job

1. Read your memory file `docs/review/worker-memory/worker-2.md`.
2. Read the artifact and identify each High, Medium, and Low issue. The artifact is the only thing you know about Worker 1's reasoning — if it is ambiguous, surface that as a question in the artifact's verification feedback section rather than guessing intent.
3. Review the target source and existing tests.
4. Implement approved logic fixes first.
5. Add or update tests needed to prove the logic changes.
6. Run focused validation appropriate to the change.
7. The diff and validation results are visible to Worker 3 through the working tree and the artifact (record any shadow-file usage in the artifact). Do not message Worker 3 directly.
8. After Worker 3 approves logic, update comments and docstrings for the reviewed scope.
9. After Worker 3 approves comments, update `CHANGELOG.md` if needed.
10. On the final pass for this cycle item, append a short entry (3-5 lines) to `docs/review/worker-memory/worker-2.md`: what implementation pattern you reached for, any test scaffolding worth reusing, anything Worker 3 pushed back on.

### Memory entry shape

Append a brief block per cycle item. Example:

```
## 2026-05-06 — types/base.py
- Added `_validate_optimizer_hints_against_selected_fields` after `_select_fields` in `__init_subclass__`; new test pinning excluded-field rejection.
- Pattern that worked: split validation into a helper that takes `(meta, fields)` rather than threading both through one larger validator.
- Worker 3 pushback: required that I cite the model name in the error message, not just the field list.
```

Keep entries terse. If the file approaches 50 lines, merge similar entries into a single pattern observation before adding more.

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

The full rules live in `docs/review/REVIEW.md` under "Static review helper". Worker 2 follows this shape:

- **Re-read the overview** Worker 1 already produced under `docs/review/shadow/<stem>.overview.md` before implementing any non-trivial fix. The Django/ORM markers, control-flow hotspots, and calls-of-interest sections are the same checklist that drove the review; consult them while planning the edit so the fix does not regress an unrelated marker line.
- **Re-run the helper** with `--strip-docstrings` when the logic is hard to read with docstrings inline:

```shell
python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --strip-docstrings
```

- **Pass the shadow path to Worker 3** on the first verification pass when the shadow was used during fix implementation. Worker 3's first-pass prompt must include the shadow-file caveat (see worker-3.md).
- **Cite original source-file line numbers** in source edits, tests, commit messages, and changelog entries. Shadow-file line numbers do not match the original source after comment / docstring stripping.

Generated shadow files under `docs/review/shadow/` are read-only review aids. Never edit or commit them.

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
