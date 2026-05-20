# Worker 1: file and folder reviewer

Worker 1 performs exactly one unchecked review item at a time and creates exactly one review artifact for that item. Worker 1 does not fix code.

Worker 1 runs as a **fresh subagent invocation per cycle item**, dispatched by Worker 0. Worker 1 has no in-context memory of previous cycles within this release; its only carry-forward is its private memory file `docs/review/worker-memory/worker-1.md`. See `REVIEW.md` "Subagent dispatch and worker memory" for the full model.

## Required reading

Read the docs marked `yes` in the **W1** column of the Required reading per worker table in `docs/review/REVIEW.md`. Read `docs/review/worker-memory/worker-1.md` first — the patterns and calibration you flagged in earlier cycles inform how you read this one.

For folder-level passes, also read every sibling `docs/review/rev-*.md` artifact for that folder. For the final project-level pass, read the completed folder and file artifacts needed to understand package-wide patterns. For the final test-run gate, only `rev-final.md` is in scope.

**Forbidden reads.** Worker 1 must not read `docs/review/worker-memory/worker-0.md`, `worker-2.md`, or `worker-3.md`. Those files are private to their respective workers; reading them defeats the isolation that makes the cycle's verification independent.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 1 may create or replace:

- `docs/review/rev-<folder__file_name>.md` — the current planned review artifact
- `docs/review/rev-final.md` — the final test-run gate artifact (Worker 1 owns this end-to-end; Worker 3 has no role)
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
- truncate or rewrite history in `worker-memory/worker-1.md` — append only (consolidate via merge when the file **approaches ~45 lines**)
- commit. Only the maintainer commits; Worker 1 never commits, even if asked

## Job

1. Read your memory file `docs/review/worker-memory/worker-1.md`.
2. Read the active plan.
3. Find the first checklist item not marked `- [x]` (or use the item Worker 0's spawn prompt named explicitly).
4. Review only that file, folder pass, or final project pass.
5. Create the exact artifact named by the plan, including a `Status: under-review` line at the top and a `## DRY analysis` section listing actionable DRY opportunities per the artifact template (recap of patterns already reused goes in `## What looks solid`, not here).
6. Append a short entry (3-5 lines) to `docs/review/worker-memory/worker-1.md`: what kind of review this was, what patterns or severity calibrations are worth carrying forward, anything you noticed that the next cycle should pay attention to.
7. Stop.

The artifact is the only inter-worker output. Your memory entry is for your own future spawns, never for Worker 2 or Worker 3.

### DRY analysis shape

The `## DRY analysis` section lists **actionable** DRY consolidation candidates only — each top-level bullet is one opportunity a future DRY cycle could pick up. Two legitimate bullet shapes:

- **Act-now opportunities.** Name the consolidation shape, cite the call sites, recommend the helper signature or shared dataclass. Example: "Extract `_walk_relation_target(sel, related_model, plan, prefix, info, runtime_paths)` from `walker.py:302-309` and `walker.py:369-376`; both branches share six of seven arguments."
- **Defer-with-trigger opportunities.** Same shape, but explicitly gated. Quote the trigger condition verbatim so the next DRY cycle can grep for it and re-triage when the trigger fires. Example: "Defer until a third walker lands; collapse `walker.py:302-309` and `walker.py:369-376` then."

If no real opportunities exist for the file, write a single bullet `- None — <one sentence why the current factoring is correct>`. Silence on DRY is not acceptance.

The positive audit trail — "Existing patterns reused", "No new helper needed at this granularity", "Considered-and-rejected duplication" — belongs in the artifact's `## What looks solid` section under a `### DRY recap` H3 subsection, NOT in `## DRY analysis`. The DRY-cycle export script (`docs/dry/export_dry_review.py`) extracts every top-level bullet from `## DRY analysis` as a finding, so recap bullets become noise in the consolidation plan and force every DRY cycle to re-triage them.

### `## What looks solid` subsection structure

Worker 1 writes `## What looks solid` with **two H3 subsections in this order**:

```
## What looks solid

### DRY recap

- **Existing patterns reused.** <which canonical helpers the file already reuses; cite path/file.py:NN-MM>
- **New helpers considered.** <candidates evaluated and rejected, or deferred without trigger conditions; state why>
- **Duplication risk in the current file.** <repeated literals / near-copies that are intentional sibling design; state why correct>

### Other positives

- <design choice, test discipline, error-handling shape, etc.>
- <design choice, test discipline, error-handling shape, etc.>

### Summary

<one paragraph>
```

Rules:

- Use the exact heading text: `### DRY recap` and `### Other positives` (no trailing colon, no variation).
- `### DRY recap` carries the positive audit trail that used to live as the three sub-bullets of `## DRY analysis` under the previous template. Keep the `**Existing patterns reused.**` / `**New helpers considered.**` / `**Duplication risk in the current file.**` bold-prefixed shape so the audit trail is greppable across artifacts.
- If a recap category is genuinely empty (e.g. a pure-class skip artifact), drop that bullet rather than writing "None." — the recap is audit trail, not a checklist.
- `### Other positives` keeps the artifact's positive-observation bullets in the same flat-list shape they used before.
- `### Summary` follows immediately after `### Other positives`.
- The DRY-cycle export script does NOT scan `## What looks solid`, so recap content placed here will not be re-promoted to findings.

### Memory entry shape

Append a brief block per cycle. Example:

```
## 2026-05-06 — types/base.py
- Reviewed `__init_subclass__` pipeline; flagged `optimizer_hints` validation gap.
- Calibration: when a guard exists for "real Django field" but not "selected field", that's Medium not Low — silent dead code is the bug.
- Carry forward: check converter/registry layers for the same "validates A but not the intersection of A and B" pattern.
```

Keep entries terse. If the file **approaches ~45 lines**, merge similar entries into a single pattern observation before adding more (the earlier threshold keeps each consolidation a real merge instead of a frantic compaction at the limit).

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
- **Use the overview as a checklist.** The Django/ORM markers section enumerates executable-code marker lines and is the audit list for ORM-heavy files; the control-flow hotspots section flags branchy functions for Medium-tier complexity attention; the calls-of-interest section surfaces reflective-access sites; the repeated-literals section drives the folder-pass DRY check.
- **Cite original source-file line numbers** in the artifact, never shadow-file line numbers — comments and docstring statements are removed from the shadow file, other string literals are replaced, and the line numbers will not match.

Example:

```shell
python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
```

Use `python scripts/review_inspect.py --all --output-dir docs/shadow` when Worker 0 or a folder/project pass needs fresh shadow output for the full package tree.

Every review-cycle helper invocation must pass `--output-dir docs/shadow`. The helper writes ignored shadow byproducts under that path. The tracked, committed review artifact is the `docs/review/rev-<folder__file_name>.md` file you produce.

## Final test-run gate job

When Worker 0 dispatches Worker 1 to produce `docs/review/rev-final.md`:

1. Run `uv run pytest` (full sweep across all three test trees per `AGENTS.md`).
2. Record the command output and pass/fail result in `rev-final.md`.
3. Do **not** inspect line coverage; the gate's only requirement is that existing tests still pass.
4. On pass, set `Status: verified`. Worker 0 marks the final checklist box.
5. On fail, set `Status: revision-needed`, record the failing tests in the artifact, and stop. Worker 0 will dispatch the owning cycle item again before re-running the gate.

Worker 2 and Worker 3 are **not** involved in the final test-run gate. The artifact uses the same `Status:` line as ordinary `rev-*.md` artifacts but bypasses the normal Worker 2 → Worker 3 loop.

### Coverage-gate vs test-failure: read the summary line, not the exit code

`pyproject.toml` configures `[tool.coverage.report] fail_under = 100` and `pytest-cov` is wired into the default `uv run pytest` invocation, so a sub-100% coverage run produces:

- a `=== N passed, M skipped ===` summary line that means the test suite passed, AND
- a non-zero process exit code driven by `--cov-fail-under` reporting a coverage shortfall.

**The gate cares about the summary line, not the exit code.** A pytest non-zero exit driven by `--cov-fail-under` is NOT a test failure for this gate — coverage gating belongs to CI and the maintainer per `REVIEW.md` ("Do NOT inspect or assert line coverage at this stage"). Only a `failed` count in the summary line, a collection error, or a test-assertion error flips the gate to `revision-needed`.

Parse the `=== N passed, ... ===` line as the source of truth. Record the coverage-shortfall message (if any) in the artifact's `## Notes` section as a follow-up signal for the maintainer; do not flip the gate.

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
