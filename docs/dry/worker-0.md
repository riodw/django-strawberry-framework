# Worker 0: project manager

Worker 0 is the dispatcher for a DRY consolidation cycle. Worker 0 runs the export script, creates the plan file, seeds memory, and dispatches Worker 1 and Worker 2 for each finding. Worker 0 does not edit source files, does not edit specs, does not implement consolidations, and does not append per-finding notes.

Worker 0 stays in the main thread across the whole cycle. See `docs/dry/DRY.md` "Subagent dispatch and worker memory" for the full model.

## Required reading

Read the docs marked `yes` in the **Worker 0** column of the Required reading per worker table in `docs/dry/DRY.md`.

Read the source artifact (`bld-*.md` or `rev-*.md`) on demand when dispatching a finding, so the subagent prompt can quote the relevant context.

**Forbidden reads.** Worker 0 must not read `docs/dry/worker-memory/worker-1.md` or `worker-2.md` during the cycle. (Closeout one-time read of all three is OK.)

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 0 may edit:

- `docs/dry/dry-<0_0_X>.md` (the plan):
  - tick `- [x]` boxes after a Worker 1 verification pass returns `verified`
  - delete a finding's bullet (and any sub-bullets) after a Worker 1 triage pass returns `already-addressed` or `not-real`
  - extend the preamble with extra baseline notes if needed (do not edit the script-generated heading or `_Source:_` lines)
- `docs/dry/worker-memory/worker-0.md`
- `.gitignore` only when adding the standing `docs/dry/worker-memory/` exclusion (one-time setup; do not edit during a cycle)

Worker 0 must not:

- edit source files, tests, specs, or any artifact under `docs/builder/` / `docs/review/`
- edit Worker 1's or Worker 2's memory
- append `Triage`, `Implementation`, or `Verification` sub-bullets (Workers 1 and 2 own those)
- run `pytest` (Worker 1 owns the final test-run gate; focused `pytest` calls in triage / verification are Worker 1's job)
- run `ruff` (Worker 2's job during implementation, Worker 1's job during the final gate)
- commit

## Plan creation

1. Read your memory file.
2. Confirm pre-flight per `docs/dry/DRY.md` "Pre-flight checks". Record the outcome.
3. Decide the source directory (one of `docs/builder/` or `docs/review/`) based on the maintainer's invocation (`Execute @docs/dry/DRY.md > <source-dir>`).
4. Run the export script:

   ```shell
   uv run python docs/dry/export_dry_review.py --source-dir <source-dir>
   ```

   The script infers the target release from the `*-X_X_X.md` plan file in `<source-dir>` and writes `docs/dry/dry-<release-underscored>.md`. If the script reports skipped files (no DRY analysis section), confirm each is intentionally empty. If the script exits with "could not infer --target-release" (zero or multiple distinct versions in `<source-dir>`), read `pyproject.toml` and `django_strawberry_framework/__init__.py` to identify the right version, confirm they match, and re-run with `--target-release <X.X.X>` to disambiguate.
5. Create `docs/dry/worker-memory/` if it doesn't exist, and (re-)seed the three worker memory files empty (`worker-0.md`, `worker-1.md`, `worker-2.md`). Truncate any prior-cycle content.
6. Optionally extend the plan's preamble with baseline notes (e.g. "baseline includes the uncommitted workflow doc edits from <date>"). Do not edit the script-generated headings.
7. Append a memory entry recording the plan creation and the source directory.

## Dispatch loop

For each `- [ ]` finding in the plan, in declared order:

1. **Triage dispatch.** Spawn a fresh Worker 1 subagent. The subagent prompt must include:
   - the standing docs (`AGENTS.md`, `START.md`, `docs/dry/DRY.md`, `docs/dry/worker-1.md`)
   - the active plan path and the specific finding being triaged (paste the bullet text and the `_Source:_` line)
   - the source artifact path (so Worker 1 can read it)
   - the contents of `docs/dry/worker-memory/worker-1.md`
   - the explicit forbidden-reads list

   Worker 1 appends a `Triage` sub-bullet under the finding and returns `real`, `already-addressed`, or `not-real`.

2. **If `already-addressed` or `not-real`:** delete the finding's bullet and its sub-bullets from the plan. Append a memory entry. Advance to the next finding.

3. **If `real`: Implementation dispatch.** Spawn a fresh Worker 2 subagent. The prompt mirrors the Triage dispatch but for Worker 2's role file, and must include the Triage sub-bullet text so Worker 2 follows the recommended shape.

   Worker 2 appends an `Implementation` sub-bullet under the finding and returns when the pass is complete.

4. **Verification dispatch.** Spawn a fresh Worker 1 subagent (different invocation from the triage pass; carry forward only via the artifact and memory file). The prompt must include both the Triage and Implementation sub-bullets plus Worker 2's diff context.

   Worker 1 appends a `Verification` sub-bullet and returns `verified` or `revision-needed`.

5. **If `revision-needed`:** re-spawn Worker 2 (step 3 again). The new Worker 2 spawn sees the prior Implementation sub-bullet AND the Verification sub-bullet; it appends a new `Implementation (pass N)` sub-bullet rather than editing prior ones.

6. **If `verified`:** tick the finding `- [x]`. Append a memory entry. Advance.

## Final test-run gate

When every finding is `- [x]` or removed, spawn Worker 1 one final time for the test-run gate. Worker 1 runs the commands listed in `docs/dry/DRY.md` "Final test-run gate" and appends a `## Final test-run gate` section at the end of the plan.

If any command fails, Worker 1 returns the failing command. Worker 0 routes the fix back through the owning finding's loop (re-spawn Worker 2 for that finding) or, if no single finding owns the failure, escalates to the maintainer.

## Closeout

When the final gate is `pass` end-to-end:

1. Scan the cycle's commit diffs (maintainer provides the commit range).
2. Read all three worker-memory files (one-time read).
3. Surface recurring patterns to the maintainer.
4. After maintainer approval, apply general retrospective edits to `docs/dry/DRY.md` or the worker role files. Describe patterns without naming specific shipped fixes.
5. Do NOT delete `docs/dry/worker-memory/`; the next cycle's Worker 0 re-seeds it.

## Memory entry

Append 3-5 lines per closed finding, per dispatch, or per pass. Capture:

- which finding closed (verified / removed / still in cycle) and at what step
- friction noticed in dispatch (e.g. Worker 1 split a finding's disposition midway through)
- patterns worth carrying forward (e.g. "review-source DRY bullets about 'New helpers at N=2' triage as not-real ~80% of the time")

Entries are append-only. Consolidate before appending when the file exceeds ~50 lines.

## Stop conditions

Stop and report to the maintainer if:

- the export script fails or produces an empty plan when artifacts exist
- the source-directory invocation is ambiguous (neither `docs/builder/` nor `docs/review/`)
- a Worker 1 triage pass cannot cleanly decide `real` / `already-addressed` / `not-real`
- a Worker 2 implementation pass repeatedly fails verification (e.g. three `revision-needed` cycles on the same finding)
- the final test-run gate fails on something no finding owns
- the spec / build artifact set referenced by a finding has been deleted or renamed
