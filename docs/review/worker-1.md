# Worker 1: file and folder reviewer

Worker 1 performs exactly one unchecked review item at a time and creates exactly one review artifact for that item. Worker 1 does not fix code.

Worker 1 runs as a **fresh subagent invocation per cycle item**, dispatched by Worker 0. Worker 1 has no in-context memory of previous cycles within this release; its only carry-forward is its private memory file `docs/review/worker-memory/worker-1.md`. See `REVIEW.md` "Subagent dispatch and worker memory" for the full model.

## Required reading

Read these before acting:

- `AGENTS.md`
- `START.md`
- `docs/review/REVIEW.md`
- `docs/review/worker-1.md`
- the active `docs/review/review-<0_0_X>.md`
- `docs/review/worker-memory/worker-1.md` — your own running notes from prior cycles in this release. Read first; the patterns and calibration you flagged in earlier cycles inform how you read this one.
- the target source file or folder

For folder-level passes, also read every sibling `docs/review/rev-*.md` artifact for that folder. For the final project-level pass, read the completed folder and file artifacts needed to understand package-wide patterns.

**Forbidden reads.** Worker 1 must not read `docs/review/worker-memory/worker-2.md` or `docs/review/worker-memory/worker-3.md`. Those files are private to their respective workers; reading them defeats the isolation that makes the cycle's verification independent.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 1 may create or replace:

- `docs/review/rev-<folder__file_name>.md` — the current planned review artifact
- `docs/review/worker-memory/worker-1.md` — append-only updates to its own memory file

Worker 1 must not:

- modify source code
- modify tests
- update comments or docstrings in source files
- update `CHANGELOG.md`
- mark checkboxes complete
- review more than one checklist item
- produce a separate narrative response after the artifact is created
- read or edit `docs/review/worker-memory/worker-2.md` or `worker-3.md`
- truncate or rewrite history in `worker-memory/worker-1.md` — append only (consolidate via merge if the file exceeds ~50 lines)
- commit unless the maintainer explicitly asks

## Job

1. Read your memory file `docs/review/worker-memory/worker-1.md`.
2. Read the active plan.
3. Find the first checklist item not marked `- [x]` (or use the item Worker 0's spawn prompt named explicitly).
4. Review only that file, folder pass, or final project pass.
5. Create the exact artifact named by the plan.
6. Append a short entry (3-5 lines) to `docs/review/worker-memory/worker-1.md`: what kind of review this was, what patterns or severity calibrations are worth carrying forward, anything you noticed that the next cycle should pay attention to.
7. Stop.

The artifact is the only inter-worker output. Your memory entry is for your own future spawns, never for Worker 2 or Worker 3.

### Memory entry shape

Append a brief block per cycle. Example:

```
## 2026-05-06 — types/base.py
- Reviewed `__init_subclass__` pipeline; flagged `optimizer_hints` validation gap.
- Calibration: when a guard exists for "real Django field" but not "selected field", that's Medium not Low — silent dead code is the bug.
- Carry forward: check converter/registry layers for the same "validates A but not the intersection of A and B" pattern.
```

Keep entries terse. If the file approaches 50 lines, merge similar entries into a single pattern observation before adding more.

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

The static helper `scripts/review_inspect.py` is **mandatory** for several file shapes. The full when/how/section-by-section rules live in `docs/review/REVIEW.md` under "Static review helper" — read that section before reviewing any Python file in this package.

Quick rules:

- **Run the helper before reviewing** any `.py` file ≥150 lines, any file under `optimizer/` or `types/`, or any file whose folder pass is next on the checklist (folder passes need an overview for every sibling, including the folder's `__init__.py`).
- **Skip the helper** for pure-class-definition modules like `exceptions.py`. State the skip and the reason in the artifact's `What looks solid` section. (Non-`.py` files and standalone `__init__.py` reviews are out of scope entirely — see `REVIEW.md` "Review scope".)
- **Use the overview as a checklist.** The Django/ORM markers section enumerates every line that touches the ORM and is the audit list for ORM-heavy files; the control-flow hotspots section flags branchy functions for Medium-tier complexity attention; the calls-of-interest section surfaces reflective-access sites; the repeated-literals section drives the folder-pass DRY check.
- **Cite original source-file line numbers** in the artifact, never shadow-file line numbers — comments and docstrings are stripped from the shadow file and the line numbers will not match.

Example:

```shell
python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py
```

The helper writes ignored shadow byproducts under `docs/review/shadow/`. The tracked, committed review artifact is the `docs/review/rev-<folder__file_name>.md` file you produce.

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
