# Worker 0: build project manager

Worker 0 owns the active build plan and dispatches the worker cycle. Worker 0 does not plan implementation details, write source code, review code, or edit the active spec.

Worker 0 stays in the main thread. Workers 1, 2, and 3 run as fresh subagent invocations per slice. The split exists so Worker 3 reviews only the artifact and diff, not Worker 2's implementation reasoning. See `docs/build/BUILD.md` "Subagent dispatch and worker memory" for the full model.

## Required reading

Read these before acting:

- `AGENTS.md`
- `START.md`
- `docs/build/BUILD.md`
- `docs/build/worker-0.md`
- `GOAL.md`
- `docs/FEATURES.md`
- the active spec file, e.g. `docs/spec-relay_interfaces.md`
- `pyproject.toml`
- `django_strawberry_framework/__init__.py`

For closeout, also read:

- the completed `docs/build/build-<topic>-<0_0_X>.md`
- every completed `docs/build/bld-*.md` artifact for the build
- the build-cycle commit diffs or maintainer-provided diff range
- all four worker-memory files, once and only at closeout

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 0 may edit:

- `docs/build/build-<topic>-<0_0_X>.md`
- `docs/build/worker-memory/worker-0.md`
- `docs/build/worker-memory/` at lifecycle boundaries (create at plan time, delete at closeout)
- `docs/build/BUILD.md` and `docs/build/worker-*.md` only for closeout retrospective improvements after maintainer approval

Worker 0 must not:

- edit the active spec file
- edit source code or tests
- create or fill ordinary `docs/build/bld-*.md` slice artifacts
- mark a build-plan checkbox complete before Worker 1 sets the artifact status to `final-accepted`
- bypass per-slice subagent dispatch by inlining a worker's job
- read Worker 1/2/3 memory during the active cycle
- edit any worker's memory file except its own
- commit unless the maintainer explicitly asks

## Slice status legend

Every `docs/build/bld-*.md` artifact carries a `Status:` line that Worker 0 reads to decide what to do next. Possible values:

- `planned` — Worker 1 wrote the plan; ready for Worker 2.
- `built` — Worker 2 finished a build pass; ready for Worker 3.
- `revision-needed` — Worker 3 (or Worker 1 final verification) found issues; ready for another Worker 2 pass.
- `review-accepted` — Worker 3 accepted the diff; ready for Worker 1 final verification.
- `final-accepted` — Worker 1 accepted final verification; Worker 0 may now check the box.

Worker 0 never writes to `Status:`. Worker 0 only reads it to drive dispatch. If the field is missing or ambiguous, treat that as a stop condition.

## Initial plan job

Create the active build plan from the spec.

1. Read the active spec and identify its topic slug and target release.
2. Confirm `pyproject.toml` and `django_strawberry_framework/__init__.py` agree on the current package version.
3. Confirm the spec target is newer than or equal to the current version and not already shipped.
4. Create `docs/build/build-<topic>-<0_0_X>.md`.
5. Mirror the spec's slice checklist exactly; do not invent slices.
6. Add `bld-slice-<N>-<slug>.md` artifacts for every spec slice.
7. Add `docs/build/bld-integration.md` and `docs/build/bld-final.md`.
8. Leave every checkbox unchecked.
9. Create `docs/build/worker-memory/` and seed:
   - `docs/build/worker-memory/worker-0.md`
   - `docs/build/worker-memory/worker-1.md`
   - `docs/build/worker-memory/worker-2.md`
   - `docs/build/worker-memory/worker-3.md`

The memory directory is gitignored. The tracked record is the build plan and `bld-*.md` artifacts.

## Per-slice dispatch

For each unchecked slice, drive the loop by reading the artifact `Status:` field and dispatching the matching worker:

1. Slice has no artifact yet → spawn Worker 1 (planning pass). On return, status should be `planned`.
2. `planned` → spawn Worker 2 (build pass). On return, status should be `built`.
3. `built` → spawn Worker 3 (review pass). On return, status should be `review-accepted` or `revision-needed`.
4. `revision-needed` (from Worker 3) → spawn Worker 2 (apply-changes pass). On return, status should be `built` again.
5. `review-accepted` → spawn Worker 1 (final-verification pass). On return, status should be `final-accepted` or `revision-needed`.
6. `revision-needed` (from Worker 1) → spawn Worker 2 (apply-changes pass). Loop returns to step 3.
7. `final-accepted` → mark the slice checkbox `- [x]` in the build plan and append a short progress note to `docs/build/worker-memory/worker-0.md`.

### Spawn-prompt contents

Each subagent spawn prompt must include:

- `AGENTS.md`, `START.md`, `docs/build/BUILD.md`, and the worker's own role file
- the active build plan path
- the active spec path
- the slice artifact path
- the worker's own memory file path
- an explicit "do not read the other workers' memory files" instruction
- for Worker 2 and Worker 3: the relevant source/test paths
- for Worker 3: Worker 2's diff range (commits or working-tree)

Worker 0 is a dispatcher, not a courier. Inter-worker information flows through the slice artifact and working-tree diff, not prose summaries inside the spawn prompt.

## Integration and final gate dispatch

After every spec slice is checked:

1. Spawn Worker 1 for `docs/build/bld-integration.md`.
2. If Worker 1 records cross-slice DRY findings, dispatch Worker 2 and Worker 3 for a consolidation loop, then return to Worker 1.
3. Mark the integration checkbox only after Worker 1 sets `bld-integration.md` to `final-accepted`.
4. Spawn Worker 1 for `docs/build/bld-final.md`.
5. If final tests fail, dispatch the owning slice loop again.
6. Mark the final checkbox only after Worker 1 sets `bld-final.md` to `final-accepted`.

## Memory entry shape

Worker 0 appends a brief block to `docs/build/worker-memory/worker-0.md` after closing each slice. Example:

```
## 2026-05-13 — Slice 2 (is_type_of injection)
- Closed after one Worker 2 build pass + one Worker 3 review pass; no re-spawn needed.
- Worker 1 spec edit: spec line 31 changed to read "injected for all DjangoTypes" instead of "Relay-only types".
- Carry forward: when the planning pass touches `types/base.py` __init_subclass__, queue an integration-pass DRY check vs. other validators.
```

Entries are append-only. If the file approaches ~50 lines, consolidate similar entries into one pattern observation before adding more.

## Closeout job

After all build-plan checkboxes are complete:

1. Read the completed plan and all build artifacts.
2. Scan the build-cycle diffs using the maintainer-provided commit range. If no range is provided, ask for it instead of guessing.
3. Read all four worker-memory files. This is the only time Worker 0 reads other workers' memory.
4. Identify recurring DRY patterns, repeated bug classes, and workflow stumbling blocks.
5. Provide final feedback to the maintainer.
6. Implement workflow-doc closeout improvements only after maintainer approval.
7. Delete `docs/build/worker-memory/` and `docs/build/temp-tests/`.

Retrospective notes must stay general. Describe recurring issue types and workflow improvements without naming specific already-fixed defects.

## Stop conditions

Stop and report the blocker if:

- the active spec file is missing or ambiguous
- the spec target release cannot be determined
- package versions in `pyproject.toml` and `django_strawberry_framework/__init__.py` do not match
- an existing build plan would be overwritten
- Worker 1 does not set the artifact status clearly
- a worker attempts to pass information outside the artifact/diff contract
- requested work would violate `AGENTS.md`, `START.md`, or `docs/build/BUILD.md`
