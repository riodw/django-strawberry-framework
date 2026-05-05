# Worker 1: file and folder reviewer

Worker 1 performs exactly one unchecked review item at a time and creates exactly one review artifact for that item. Worker 1 does not fix code.

## Required reading

Read these before acting:

- `AGENTS.md`
- `START.md`
- `docs/review/REVIEW.md`
- `docs/review/worker-1.md`
- the active `docs/review/review-<0_0_X>.md`
- the target source file or folder

For folder-level passes, also read every sibling `docs/review/rev-*.md` artifact for that folder. For the final project-level pass, read the completed folder and file artifacts needed to understand package-wide patterns.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 1 may create or replace only the current planned review artifact:

- `docs/review/rev-<folder__file_name>.md`

Worker 1 must not:

- modify source code
- modify tests
- update comments or docstrings in source files
- update `CHANGELOG.md`
- mark checkboxes complete
- review more than one checklist item
- produce a separate narrative response after the artifact is created
- commit unless the maintainer explicitly asks

## Job

1. Read the active plan.
2. Find the first checklist item not marked `- [x]`.
3. Review only that file, folder pass, or final project pass.
4. Create the exact artifact named by the plan.
5. Stop.

The artifact is the only output after the review. It must be a tracked Markdown file under `docs/review/`.

## Review order

Run the logic review first.

Focus on:

- correctness and edge cases
- public API behavior and backward compatibility
- Django ORM correctness and database-query behavior
- optimizer behavior, N+1 risk, and relation loading
- cache/request-state mutation bugs
- async/sync hazards
- performance and memory use
- redundancy and DRY opportunities
- module responsibility and Two Scoops of Django structure
- import-time side effects and circular imports
- typing and runtime annotation behavior
- tests needed to prove a recommended change

Run the comment/docstring review second.

Focus on:

- stale comments
- comments that restate obvious code
- missing comments for non-obvious Django or optimizer behavior
- docstrings that promise behavior the implementation does not provide
- obsolete TODOs or deleted-spec references
- public API docstrings that need consumer-visible constraints

Do not recommend comment polish before logic is correct.

## Static helper use

For Python files, use the static helper when it helps clarify logic:

```shell
python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py
```

The helper writes ignored shadow byproducts under `docs/review/shadow/`. Shadow line numbers are not canonical because comments may be stripped. Artifact references must use original source-file line numbers.

## Artifact dicta

Every artifact must:

- use the template from `docs/review/REVIEW.md`
- keep High, Medium, and Low headings even when a section is `None.`
- cite original source paths and line numbers
- include only confirmed issues or clearly bounded follow-ups
- include test expectations for any High-severity issue
- explain why low-surface files are skipped when there is no meaningful review surface
- include a short "What looks solid" section
- include a short summary

Do not include speculative defects. If package-wide context is required, record the concern as a folder-pass or project-pass follow-up instead of presenting it as a local defect.

## Folder and project passes

For folder-level passes:

- read all completed sibling artifacts first
- look for duplicated helpers, naming drift, repeated ORM patterns, misplaced responsibilities, export issues, circular-import risk, and comment consistency
- stay within that folder unless a cross-folder dependency is necessary to explain the issue

For the final project-level pass:

- look for duplicated patterns across folders
- check public API/export consistency
- check settings and configuration boundaries
- identify shared utility candidates
- identify optimizer/type/registry responsibility boundaries
- note package-wide test gaps and recurring bug classes

## Stop conditions

Stop without creating a normal issue artifact if:

- the active plan does not exist
- no unchecked item exists
- the target file named by the plan does not exist
- the planned artifact path is missing or ambiguous
- required sibling artifacts are missing for a folder pass

When stopping for one of these reasons, create the planned artifact only if the plan gives an unambiguous artifact path; otherwise report the blocker to the maintainer.
