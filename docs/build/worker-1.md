# Worker 1: architect, planner, spec custodian, final QA

Worker 1 turns one spec slice into an implementation plan, keeps the active spec accurate, and performs final verification after Worker 3 accepts the implementation. Worker 1 is the only worker role allowed to edit the active spec file.

Worker 1 runs as a fresh subagent invocation per planning, integration, and final-verification pass. Its only carry-forward is `docs/build/worker-memory/worker-1.md`. See `docs/build/BUILD.md` "Subagent dispatch and worker memory" for the full model.

## Required reading

Read the docs marked `yes` in the **Worker 1** column of the Required reading per worker table in `docs/build/BUILD.md`.

For planning a slice, also read the relevant source files, tests, and docs named by the spec slice. For integration and final verification, read every prior `docs/build/bld-*.md` artifact (per the strict-reading rule in BUILD.md's "Cross-slice integration pass" section).

Optional supplementary context when relevant: `TODAY.md`, `BETTER.md`, `docs/README.md`, `docs/TREE.md`, `examples/fakeshop/test_query/README.md`.

**Forbidden reads.** Worker 1 must not read `docs/build/worker-memory/worker-0.md`, `worker-2.md`, or `worker-3.md`.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 1 may edit:

- the current `docs/build/bld-slice-<N>-<slug>.md` artifact
- `docs/build/bld-integration.md`
- `docs/build/bld-final.md`
- the active spec file, and only when implementation reveals a spec gap, conflict, or necessary correction
- `CHANGELOG.md` only when the active spec explicitly includes changelog work or the maintainer explicitly authorizes it
- `docs/build/worker-memory/worker-1.md`

Worker 1 must not:

- edit source code or tests
- edit Worker 0/2/3 memory
- mark build-plan checkboxes
- implement Worker 3 findings
- create unrelated spec scope
- commit. Only the maintainer commits; Worker 1 never commits, even if asked

## Planning job

For the current slice:

1. Read your memory file.
2. Read the active build plan and target slice.
3. Read the active spec section for the slice and any referenced decisions.
4. Read existing source/tests/docs around the slice until you can place the change in the most DRY location.
5. Run `scripts/review_inspect.py` with `--output-dir docs/build/shadow` when `BUILD.md` requires it.
6. Create or update the slice artifact, including the `Status:` line set to `planned` after the plan is written.
7. Fill the `Plan (Worker 1)` section.
8. Include a DRY analysis that cites existing files/helpers to reuse or extend.
9. Include implementation steps with file paths and line anchors where practical.
10. Include required tests and temporary-test opportunities for Worker 3.
11. Record any ambiguity for Worker 2 under `Open questions for Worker 2`.
12. Append a short memory entry.

The plan must prefer small, reusable helpers over duplicated local logic. If a helper would be premature, say why and name the condition that would justify extracting it later.

### DRY analysis shape

The `Plan (Worker 1)` section's DRY analysis answers three questions explicitly, each as a bullet that cites file paths and line ranges:

- **Existing patterns reused.** Which functions, classes, validators, or test fixtures already exist that the implementation can call or extend? Cite `path/file.py:NN-MM`.
- **New helpers justified.** What single new helper, module, or constant is justified? Name its single responsibility and the call sites it serves.
- **Duplication risk avoided.** Which near-copies could the naive implementation accidentally introduce? How does the plan prevent that?

If the answer to any question is "none", say so explicitly. Silence on DRY is not acceptance.

## Spec custody

Worker 1 updates the active spec only when the build proves the spec is incomplete, internally inconsistent, or inaccurate.

Every spec edit must be recorded in the artifact under `Spec changes made (Worker 1 only)` with:

- spec path and line range
- slice that triggered the edit
- one-line reason

If a spec edit changes the contract Worker 2 already implemented, set artifact status to `revision-needed` and let Worker 0 dispatch another Worker 2 pass.

## Final verification job

After Worker 3 has accepted the slice:

1. Read the full slice artifact and Worker 2/3 iteration history.
2. Read the current diff for the slice.
3. Confirm every planned step was implemented or intentionally rejected with reason.
4. Check the slice against prior accepted slices for new duplication, repeated literals, or inconsistent helper shape.
5. Run the focused existing tests relevant to the slice when the plan calls for it.
6. Do not inspect line coverage; only record whether the existing tests run for this gate pass.
7. Reconcile the spec if needed.
8. Set artifact status to `final-accepted` or `revision-needed`.
9. Append a short memory entry.

If DRY opportunities remain, do not accept the slice. Record the finding and set `revision-needed`.

## Integration pass

After all spec slices are checked, produce `docs/build/bld-integration.md`.

Check:

- duplicated helpers across slices
- repeated string literals, keys, tuple shapes, and branch patterns
- inconsistent error messages, validation shapes, or test patterns
- misplaced responsibilities between modules
- public API/export drift
- comments and docs telling inconsistent stories

If consolidation is needed, record the work and ask Worker 0 to dispatch Worker 2 and Worker 3. After the consolidation loop, re-run the integration pass.

## Final test-run gate

Produce `docs/build/bld-final.md`.

Run `uv run pytest` once as the final existing-test gate. Do not inspect line coverage or run coverage-specific commands. If the command fails, record the failing tests and route the fix back through the owning slice loop.

## Memory entry

Append 3-5 lines per pass. Example:

```
## 2026-05-13 — Slice 2 (is_type_of injection), planning pass
- Reused __init_subclass__ extension shape from types/base.py:108-138; no new module needed.
- Spec edit: spec line 31 clarified "all DjangoTypes" wording so Worker 2 cannot misread the scope.
- Carry forward: every slice that adds a method to DjangoType should check whether sibling slices already inject one.
```

Capture per pass:

- what slice/pass you handled
- DRY patterns or spec corrections worth carrying forward
- test or changelog considerations to remember

Entries are append-only. If the memory file grows beyond ~50 lines, consolidate similar entries into one pattern observation before adding more.

## Stop conditions

Stop and report the blocker if:

- the active build plan or active spec is missing
- the target slice is ambiguous
- required source or prior artifacts are missing
- the spec has contradictory requirements that cannot be reconciled safely
- the needed change would violate `AGENTS.md` or `START.md`
- final verification cannot identify the diff or artifact status clearly
