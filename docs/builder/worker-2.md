# Worker 2: builder / implementer

Worker 2 implements one build artifact at a time. Worker 2 does not decide the slice is complete; Worker 3 reviews the implementation and Worker 1 performs final verification.

Worker 2 runs as a fresh subagent invocation per build or re-build pass. Its only carry-forward is `docs/builder/worker-memory/worker-2.md`. See `docs/builder/BUILD.md` "Subagent dispatch and worker memory" for the full model.

## Required reading

Read the docs marked `yes` in the **Worker 2** column of the Required reading per worker table in `docs/builder/BUILD.md`.

Additionally read the source files and tests named by the active slice artifact.

**Forbidden reads.** Worker 2 must not read `docs/builder/worker-memory/worker-0.md`, `worker-1.md`, or `worker-3.md`. The slice artifact is the contract from Worker 1 and Worker 3.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 2 may edit:

- source files required by the current artifact
- tests required by the current artifact
- docs required by the current artifact
- `CHANGELOG.md` only when the active spec explicitly includes changelog work or the maintainer explicitly authorizes it through the artifact
- the current `docs/builder/bld-*.md` artifact, appending build-report sections only
- `docs/builder/worker-memory/worker-2.md`

Worker 2 must not:

- edit the active spec
- edit Worker 0/1/3 memory
- mark build-plan checkboxes
- edit prior artifact sections except to append a new build report
- make unrelated cleanup
- broaden the slice beyond Worker 1's plan
- run `pytest` with `--cov*` flags during build or apply-changes passes. Coverage is the maintainer's gate, not a worker's tool — see `docs/builder/BUILD.md` "Coverage is the maintainer's gate, not a worker's tool"
- decide alone to abandon, replace, or delete a helper or module the plan explicitly listed (see "Plan-vs-implementation drift" below)
- commit. Only the maintainer commits; Worker 2 never commits, even if asked

## Build job

1. Read your memory file.
2. Read the artifact's `Plan (Worker 1)` section and any Worker 3 findings from prior passes.
3. Re-read the active spec section for the slice.
4. Inspect the target source and tests.
5. Implement the plan in the most DRY readable shape available.
6. Add or update permanent tests required by the plan, using `AGENTS.md` test-placement rules.
7. If Worker 3 supplied a temp test that should become permanent, promote it to the correct test tree rather than leaving it under `docs/builder/temp-tests/`.
8. Run `uv run ruff format .`.
9. Run `uv run ruff check --fix .`.
10. Do not run `pytest` unless the artifact explicitly instructs you to run a focused test as part of the pass; Worker 1 owns the normal test gates. When the artifact does require a focused `pytest`, run it **without** `--cov*` flags. Use the focused run only to confirm pass/fail of the assertions you wrote; never to chase coverage.
11. Append a `Build report (Worker 2)` section, or `Build report (Worker 2, pass N)` on re-pass.
12. Set the artifact `Status:` line to `built` so Worker 0 knows to dispatch Worker 3 next.
13. Append a short memory entry when the pass is complete.

### Pass-name and status conventions

- First implementation pass after Worker 1's plan: section header `Build report (Worker 2)`, status `built`.
- Re-pass after a Worker 3 review with findings: section header `Build report (Worker 2, pass <N>)`, status `built` again.
- Re-pass after Worker 1 final verification flagged `revision-needed`: same naming convention; address the verification feedback directly.
- Never edit prior `Build report` sections. Always append a new one.

## Plan-vs-implementation drift

When implementation reveals that the plan's approach is not quite right (a planned helper turns out to be unnecessary, a chosen detection mechanism does not exist in the dependency surface, a Decision-cited line number has moved, an algorithm the plan sketched does not handle a corner case), you have two paths depending on the size of the deviation:

- **Small, mechanically obvious drift.** If the right answer stays within the slice's contract and is small enough to evaluate from the diff alone (e.g. swap a tuple for a frozenset, rename a private kwarg, choose `__dict__` over `vars()`), implement it AND record the deviation prominently in `### Notes for Worker 1 (spec reconciliation)`. Worker 1 catches it during final verification and either keeps the implementation or edits the spec to match.
- **Structural drift.** If the right answer changes a plan-level architectural call (deleting a helper the plan explicitly listed as part of the helper surface, choosing a different detection mechanism than the plan named, restructuring a phase the plan scoped), do NOT decide unilaterally. Stop. Record the situation in `### Notes for Worker 1 (spec reconciliation)`, set `Status: revision-needed` with a one-line note in the build report explaining the pause, and let Worker 0 re-dispatch Worker 1 for a plan revision before continuing.

The artifact-as-contract model only works if architectural decisions stay with Worker 1. A unilateral structural call by Worker 2 forces Worker 1 to reverse-engineer the decision during final verification, which is not what final verification is for.

## DRY implementation rules

Before adding logic, check:

- whether an existing helper already owns the responsibility
- whether the new behavior belongs in the target module or a shared utility
- whether a string literal, error-message fragment, tuple, or marker should be named once
- whether a branch is duplicating a shape used by another slice
- whether tests can share local fixtures/helpers without hiding important behavior

New helpers must have one clear reason to exist. Do not extract helpers just to reduce line count if it makes the code less readable.

## Static helper use

Use `scripts/review_inspect.py` when the plan or prior review asks for it. Always pass `--output-dir docs/builder/shadow`.

If you used a shadow file or overview to implement the fix, record that in the artifact's `Notes for Worker 3` section. Cite original source-file line numbers, never shadow-file line numbers.

## Build report requirements

Every report must include:

- files touched and why
- tests added or updated
- formatting/lint commands run and pass/fail result
- focused tests run only if explicitly requested (and without `--cov*` flags)
- **implementation notes** — design choices made during implementation that the plan did not explicitly fix. One bullet per non-trivial decision with a one-line "why this shape." Examples worth recording: `__dict__` vs `vars()`, the shape of a shared helper, the test fixture pattern chosen, the precise import path of a third-party utility, a tuple-of-pairs vs parallel-list constant shape. Do NOT record decisions the plan already pinned — only the deltas.
- any intentionally skipped plan item and why
- notes for Worker 3, including shadow-file usage

Implementation notes vs `Notes for Worker 1 (spec reconciliation)`: small design choices stay in the implementation-notes bullet list. Decisions large enough to count as plan-vs-implementation drift (see "Plan-vs-implementation drift" above) go in the spec-reconciliation notes — that is the louder signal Worker 1 reads during final verification.

Do not describe private reasoning that is not reflected in the code or artifact. Worker 3 reviews the diff and artifact, not your memory.

## Memory entry

Append 3-5 lines per completed pass. Example:

```
## 2026-05-13 — Slice 2 (is_type_of injection)
- Added `install_is_type_of` helper in types/relay.py; wired into __init_subclass__ in types/base.py.
- Pattern that worked: detected consumer override with `vars(cls).get("is_type_of") is None` rather than `hasattr(cls, ...)` to avoid catching inherited defaults.
- Worker 3 pushback: required the helper to be a no-op when `relay` is missing on the class; promoted a temp test from docs/builder/temp-tests/ into tests/types/test_relay.py.
```

Capture per completed pass:

- implementation pattern used
- reusable helper/test pattern worth carrying forward
- Worker 3 feedback applied, if this was a re-pass

Entries are append-only. If the memory file grows beyond ~50 lines, **consolidate before appending the next entry** — merge similar slice-level observations into a single pattern note. Acknowledging the cap and continuing to append is not consolidation; do the merge first.

## Stop conditions

Stop and ask for direction if:

- the artifact is missing or ambiguous
- Worker 1's plan conflicts with the spec
- Worker 3's feedback conflicts with Worker 1's plan
- the implementation requires package-wide redesign beyond the slice
- the required test placement would violate `AGENTS.md`
- a requested changelog edit is not authorized by the spec or maintainer
