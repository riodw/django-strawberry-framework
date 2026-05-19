# Worker 2: fix implementer

Worker 2 reads a triaged finding and implements the DRY consolidation in source. Worker 2 runs as a fresh subagent invocation per implementation pass. The only carry-forward is `docs/dry/worker-memory/worker-2.md`. See `docs/dry/DRY.md` "Subagent dispatch and worker memory" for the full model.

## Required reading

Read the docs marked `yes` in the **Worker 2** column of the Required reading per worker table in `docs/dry/DRY.md`.

Also read the source files and tests the finding's Triage sub-bullet cites.

**Forbidden reads.** Worker 2 must not read `docs/dry/worker-memory/worker-0.md` or `worker-1.md`. The plan artifact's finding (including the Triage sub-bullet) is the contract Worker 1 hands over.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 2 may edit:

- source files required by the finding
- tests required by the finding
- the plan file (`dry-<0_0_X>.md`): append the `Implementation` sub-bullet (or `Implementation (pass N)` on a re-pass) under the active finding
- `docs/dry/worker-memory/worker-2.md`

Worker 2 must not:

- edit Worker 0's or Worker 1's memory
- tick `- [x]` boxes (Worker 0 owns those)
- delete findings (Worker 0 owns deletion based on Worker 1 triage)
- edit other findings, the workflow doc, or worker role files
- edit any source artifact (`bld-*.md` / `rev-*.md`) — those are the historical record of the cycle that produced the finding
- make changes beyond the active finding's scope (other findings are dispatched in their own passes)
- run `pytest` with `--cov*` flags — coverage is the maintainer's gate (see `docs/dry/DRY.md` "Coverage is the maintainer's gate, not a worker's tool")
- commit

## Implementation job

1. Read your memory file.
2. Read the finding's text, the `_Source:_` line, and the Triage sub-bullet. The Triage is Worker 1's recommended consolidation shape; treat it as the contract.
3. Read the source and tests the Triage cited.
4. Implement the consolidation in the most DRY readable shape consistent with the Triage's recommended shape. Place new helpers where similar logic already lives. Prefer extending an existing helper over introducing a new one when an extension is honest.
5. Add or update permanent tests that pin the consolidated behavior, per `AGENTS.md` test-placement rules. Every call site listed in the Triage should be exercised either directly or through a behavior test.
6. Run `uv run ruff format .`.
7. Run `uv run ruff check --fix .`.
8. Run `git status --short` after both ruff invocations. For each modified file, classify:
   - **Slice-intended** — the file is in the finding's scope (named in the Triage or a direct consequence). It stays in the diff and appears in the Implementation sub-bullet's "Files touched" list.
   - **Unrelated tool churn** — the file is outside the finding's scope and only changed because ruff touched it. Revert with `git checkout -- <path>` before continuing.

   Tool-induced drift is Worker 2's responsibility to own at this boundary. Never pass it through to Worker 1 as "out of scope," and do not defer it to a later finding. If a tooling-caused change cannot be cleanly classified, escalate to the maintainer.

9. Append the Implementation sub-bullet under the finding:

   ```
     - **Implementation (Worker 2, YYYY-MM-DD):** <one short paragraph: helper added at path:NN with signature `<name>(...)`, call sites updated at paths X, Y, Z; tests added at tests/.../test_<name>.py pinning the consolidation; ruff format pass, ruff check pass (no unrelated drift)>.
   ```

   On a re-pass (Verification returned `revision-needed`), use `Implementation (Worker 2, pass N, YYYY-MM-DD):` instead and address the specific feedback in the Verification sub-bullet. Do NOT edit the prior Implementation sub-bullet.

10. Append a short memory entry.

## Triage drift

If the Triage's recommended shape turns out to be wrong on close inspection — e.g. the cited call sites don't actually duplicate after re-reading, or the proposed helper would force an awkward signature, or one of the listed sites already has its own helper that should be reused instead — record the deviation prominently in the Implementation sub-bullet:

```
  - **Implementation (Worker 2, YYYY-MM-DD):** Triage drift. The Triage recommended <X>; on inspection, <Y> matches the actual call sites better because <reason>. Implemented <Y>. Verification can either accept this shape or flag `revision-needed` if the Triage shape was load-bearing for reasons not captured.
```

Worker 1's verification pass either accepts the deviation or rejects with a specific reason. Do not silently deviate without recording it.

## DRY implementation rules

Before adding logic, check:

- whether an existing helper already owns the responsibility (often the case for DRY findings — the answer to the finding may be "extend the existing helper" rather than "add a new one")
- whether a string literal, error-message fragment, tuple, or marker should be named once
- whether a branch is duplicating a shape used elsewhere in the package
- whether tests can share local fixtures without hiding important behavior

New helpers must have one clear reason to exist. Do not extract helpers just to reduce line count if it makes the code less readable.

## Memory entry

Append 3-5 lines per completed pass. Capture:

- which finding closed and the consolidation shape implemented
- pattern that worked (e.g. "extending `relation_kind` to expose `is_many_side_relation_kind` is the right shape when multiple sites probe the same kind set")
- Verification pushback applied, if this was a re-pass

Entries are append-only. Consolidate before appending when the file exceeds ~50 lines.

## Stop conditions

Stop and ask for direction if:

- the Triage sub-bullet is missing or ambiguous (the finding should have been triaged before dispatch — escalate to Worker 0)
- the cited source has moved or been deleted such that the consolidation no longer applies
- the consolidation requires a package-wide redesign beyond the finding's scope (record the situation in the Implementation sub-bullet, set the finding aside for maintainer review)
- a required test placement would violate `AGENTS.md`
- Worker 1's verification keeps rejecting the same shape across multiple passes (after the second `revision-needed` on the same finding, escalate to Worker 0)
