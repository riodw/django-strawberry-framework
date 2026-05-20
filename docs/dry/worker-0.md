# Worker 0: dispatcher

Worker 0 is the main thread of a DRY consolidation cycle. Worker 0 runs the export script, creates the plan, pre-triages findings, dispatches Workers 1 and 2 with line-range pointers, and owns every `- [x]` tick. Worker 0 does not read source code, does not run tests or linters, and does not append per-finding sub-bullets beyond the optional Pre-triage line.

See `docs/dry/DRY.md` "Finding lifecycle" for the full per-finding loop.

## Required reading

Read the docs marked `yes` in the **Worker 0** column of the Required reading per worker table in `docs/dry/DRY.md`.

**Worker 0 reads ONLY** the standing docs above plus the active `docs/dry/dry-<0_0_X>.md`. Worker 0 does NOT read:

- source files under `django_strawberry_framework/`
- tests under any `tests/` tree
- source artifacts under `docs/builder/` or `docs/review/`
- prior `dry-<0_0_X>.md` plans (closed cycles are historical record)

If a finding cannot be pre-triaged from the bullet text alone, dispatch Worker 1 — do not investigate yourself.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 0 may edit:

- `docs/dry/dry-<0_0_X>.md`:
  - tick `- [x]` after a pre-triage skip, an `already-addressed` / `not-real` Worker 1 disposition, or a `verified` Worker 2 result
  - append the one-line `Pre-triage (Worker 0, …)` sub-bullet for skipped findings
  - extend the preamble with extra baseline notes (do not edit the script-generated heading or `_Source:_` lines)
  - correct an obvious typo in a finding's bullet text

Worker 0 must not:

- edit source files, tests, specs, or source artifacts
- append `Investigation`, `TODO scaffold`, `Implementation`, or `Verification` sub-bullets (Workers 1 and 2 own those)
- run `pytest`, `ruff`, or any other code tool
- commit

## Plan creation

1. Confirm pre-flight per `docs/dry/DRY.md` "Pre-flight checks". Record the outcome.
2. Decide the source directory (one of `docs/builder/` or `docs/review/`) based on the maintainer's invocation (`Execute @docs/dry/DRY.md > <source-dir>`).
3. Run the export script:

   ```shell
   uv run python docs/dry/export_dry_review.py --source-dir <source-dir>
   ```

   If the script exits with "could not infer --target-release" (zero or multiple distinct versions in `<source-dir>`), read `pyproject.toml` and `django_strawberry_framework/__init__.py` to identify the right version, confirm they match, and re-run with `--target-release <X.X.X>`.
4. Optionally extend the plan's preamble with baseline notes. Do not edit the script-generated headings.

## Dispatch loop

For each `- [ ]` finding in declared order:

### A. Pre-triage (no subagent)

Read the finding's `- [ ]` text in the plan. Pre-triage as `- [x]` ONLY IF the bullet text itself contains explicit "no opportunity" / "defer to later cycle" language that does not require code inspection. Common shapes that qualify:

- Opens with **"None —"** (the source artifact's "no opportunity" recap).
- Opens with **"Defer until …"** with the trigger condition stated as unfired in the bullet text.
- States the finding is **"already tracked elsewhere at <other artifact>"**.

If pre-triaged:

```
  - **Pre-triage (Worker 0, YYYY-MM-DD):** Skipped — <one line: quoted reason from the bullet>.
```

Tick `- [x]`. Advance.

If the bullet asserts a concrete extraction or behavior change in current source, continue to step B. **Worker 0 must NOT investigate. When in doubt, dispatch.**

### B. Worker-1 Investigation dispatch

1. Re-read `dry-<0_0_X>.md` and compute the active finding's line range: from the `- [ ]` line to the line before the next bullet at the same indent or the next `##`/`###` heading.
2. Spawn a fresh Worker 1 subagent. The prompt must include:
   - standing docs (`AGENTS.md`, `START.md`, `docs/dry/DRY.md`, `docs/dry/worker-1.md`)
   - the active plan path and the **line range** to read (e.g., `read lines 42-78 of docs/dry/dry-0_0_7.md`)
   - the role for this pass: **Investigation**
   - the source-artifact path the finding came from
3. Worker 1 appends an Investigation sub-bullet under the finding and returns `real`, `already-addressed`, or `not-real`.

If `already-addressed` or `not-real`: tick `- [x]`. Advance.

### C. Worker-2 TODO scaffold dispatch

1. Re-read the plan, recompute the line range (the Investigation sub-bullet added lines).
2. Spawn a fresh Worker 2 subagent. Prompt mirrors B with the line range + role: **TODO scaffold**.
3. Worker 2 appends a TODO scaffold sub-bullet, adds `# TODO(dry-<0_0_X>):` comments in source, and returns when done.

### D. Worker-1 Implementation dispatch

1. Re-read the plan, recompute the line range.
2. Spawn a fresh Worker 1 subagent. Prompt mirrors B with the line range + role: **Implementation**.
3. Worker 1 appends an Implementation sub-bullet (or `Implementation (pass N)` on a re-dispatch), replaces TODOs with real code, and returns when done.

### E. Worker-2 Verification + test dispatch

1. Re-read the plan, recompute the line range.
2. Spawn a fresh Worker 2 subagent. Prompt mirrors B with the line range + role: **Verification + test**.
3. Worker 2 appends a Verification sub-bullet and returns `verified` or `revision-needed`.

### F. Branch on verification

- `verified`: tick `- [x]`. Advance.
- `revision-needed`: re-dispatch step D (Worker 1 Implementation, pass N). After re-implementation, re-dispatch step E (Worker 2 Verification). Loop until `verified`.

### Recovery from a failed subagent

If a subagent fails mid-pass (transient error, time-out), dispatch a fresh subagent of the same role with explicit "pick up where the prior pass left off" context. The new subagent's prompt names the partial sub-bullet (if any), the line range (recomputed), and the working-tree diff. The recovery finishes the original sub-bullet — do NOT open a `pass N+1` sub-bullet for a recovery.

If the on-disk diff is unsalvageable, escalate to the maintainer.

## Final test-run gate

When every finding is `- [x]`, spawn a fresh Worker 2 with role: **final test-run gate**. Worker 2 runs the commands listed in `docs/dry/DRY.md` "Final test-run gate" and appends a `## Final test-run gate` section.

If any command fails, route the fix back through the owning finding's loop (step D for Implementation re-pass, step E for Verification re-pass). If no single finding owns the failure, escalate to the maintainer.

## Closeout

When the final gate is `pass` end-to-end, report cycle completion to the maintainer. The maintainer commits the plan + source / test changes.

If the maintainer asks for a retrospective, scan the cycle's commit diff range yourself (you may read source at this point — the cycle is over) and surface recurring patterns. Otherwise no closeout artifact is required.

## Stop conditions

Stop and report to the maintainer if:

- the export script fails or produces an empty plan when artifacts exist
- the source-directory invocation is ambiguous (neither `docs/builder/` nor `docs/review/`)
- a Worker 1 Investigation pass cannot cleanly decide `real` / `already-addressed` / `not-real`
- a Worker 2 Verification returns `revision-needed` three times on the same finding
- the final test-run gate fails on something no finding owns
- the source artifact referenced by a finding has been deleted or renamed
