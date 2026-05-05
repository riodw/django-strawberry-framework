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
- `CHANGELOG.md` during closeout consolidation
- source or tests only when the maintainer explicitly asks Worker 0 to implement closeout fixes

Worker 0 must not:

- create ordinary `docs/review/rev-*.md` artifacts
- mark file/folder review items complete without Worker 3 approval
- bypass the one-file-at-a-time review cycle
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
- Include package marker files such as `py.typed`.
- Add a folder-level pass after all files in each folder.
- Add one final project-level pass for `django_strawberry_framework/`.
- Point each checklist item to its exact `docs/review/rev-*.md` artifact.
- Leave all checkboxes unchecked at plan creation.

## Closeout job

After all checklist items are marked complete:

1. Read the completed plan and review artifacts.
2. Scan the review-cycle diffs using the maintainer-provided commit range. If no range is provided, ask for it instead of guessing.
3. Identify unresolved risk, repeated bug classes, repeated DRY opportunities, and workflow stumbling blocks.
4. Provide final feedback to the maintainer.
5. Implement closeout fixes only after maintainer approval.
6. Read `CHANGELOG.md` and consolidate review-cycle entries if needed.
7. Update `docs/review/REVIEW.md` or `docs/review/worker-*.md` with general retrospective notes.

Retrospective notes must stay general. Describe recurring issue types, stumbling blocks, and workflow improvements without naming specific already-fixed defects.

## Stop conditions

Stop and report the blocker if:

- the package versions do not match
- the tracked package tree cannot be determined
- an existing plan for the same version would be overwritten
- the maintainer has not provided the closeout commit range
- requested closeout work would violate `AGENTS.md` or `START.md`
