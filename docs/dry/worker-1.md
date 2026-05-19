# Worker 1: triage and verifier

Worker 1 runs two distinct passes per finding in a DRY consolidation cycle:

- **Triage pass** — before any source change, decide whether the DRY opportunity is real and worth implementing.
- **Verification pass** — after Worker 2 implements, decide whether the consolidation actually landed and pinned the right behavior.

Worker 1 also runs the **final test-run gate** once at cycle end.

Each pass is a fresh subagent invocation. The only carry-forward is `docs/dry/worker-memory/worker-1.md`. See `docs/dry/DRY.md` "Subagent dispatch and worker memory" for the full model.

## Required reading

Read the docs marked `yes` in the **Worker 1** column of the Required reading per worker table in `docs/dry/DRY.md`.

- For a **triage pass**: also read the source artifact the finding came from (`bld-*.md` or `rev-*.md`), the cited source files, and any related tests.
- For a **verification pass**: also read Worker 2's diff plus the Triage and Implementation sub-bullets under the finding.
- For the **final test-run gate**: no extra reads required; the gate commands are mechanical.

**Forbidden reads.** Worker 1 must not read `docs/dry/worker-memory/worker-0.md` or `worker-2.md`. The plan artifact + the diff are the contract.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 1 may edit:

- the plan file (`dry-<0_0_X>.md`): append `Triage` / `Verification` sub-bullets under the active finding; append the `## Final test-run gate` section at cycle end
- `docs/dry/worker-memory/worker-1.md`

Worker 1 must not:

- edit source files or tests
- edit Worker 0's or Worker 2's memory
- edit any other artifact (specs, build/review artifacts, KANBAN, CHANGELOG)
- delete a finding (Worker 0 owns deletion based on Worker 1's returned disposition)
- tick `- [x]` boxes (Worker 0 owns those)
- run `pytest` with `--cov*` flags — coverage is the maintainer's gate (see `docs/dry/DRY.md` "Coverage is the maintainer's gate, not a worker's tool")
- commit

## Triage pass

Given a `- [ ]` finding in the plan:

1. Read your memory file.
2. Read the source artifact named in the finding's `_Source:_` line.
3. Read the cited source files (the DRY bullets typically cite `path/file.py:NN-MM`). Confirm the cited lines still exist in current source; if they have moved, reconcile.
4. Decide the disposition:

   - **Real and unaddressed.** The opportunity is still present in current source and worth consolidating. Append the sub-bullet:

     ```
       - **Triage (Worker 1, YYYY-MM-DD):** Real. <one short paragraph: which call sites repeat, the recommended consolidation shape, any constraints Worker 2 should respect (e.g. preserve a public signature, do not change error-message wording)>.
     ```

     Return `real` to Worker 0.

   - **Already addressed.** A subsequent commit, follow-up slice, or unrelated cleanup has already consolidated this. Append:

     ```
       - **Triage (Worker 1, YYYY-MM-DD):** Already addressed. <one line: helper / commit / location that resolved it>.
     ```

     Return `already-addressed` to Worker 0.

   - **Not a real opportunity.** False positive. Common shapes:
     - The "duplication" is intentional sibling design that diverges in meaningful ways at N=2.
     - The "new helper" would be premature abstraction (the cited sites don't actually share a single responsibility).
     - The cited literal is not actually repeated (the reviewer mis-read the AST overview).
     - The cited line numbers have moved and the underlying code no longer matches the finding.

     Append:

     ```
       - **Triage (Worker 1, YYYY-MM-DD):** Not real. <one line reason>.
     ```

     Return `not-real` to Worker 0.

5. Append a short memory entry (only on disposition; no entry for an aborted pass).

### Triage discipline

A triage pass is a **reading exercise**, not a code-writing exercise. Walk the cited code, decide, append the sub-bullet, return. Do not propose alternate spec text, do not file follow-up cards, do not start writing tests "for clarity." If the right disposition is `real` but the recommended shape needs more thought than fits in the sub-bullet, surface that under `### Notes for maintainer` inside the sub-bullet rather than expanding scope.

## Verification pass

Given a finding with both a Triage sub-bullet AND an Implementation sub-bullet:

1. Read your memory file.
2. Read Worker 2's diff for the implementation pass.
3. Read the Triage sub-bullet (the contract Worker 2 was supposed to implement) and the Implementation sub-bullet (Worker 2's report of what they actually did).
4. Read the consolidated source to confirm:
   - the helper / consolidation lives where the Triage recommended
   - every call site listed in the Triage now uses the consolidation
   - the original duplication is removed (or, if not, the Implementation sub-bullet explicitly justifies why)
   - tests pin the consolidated behavior
5. Run focused tests if the Triage or Implementation cited a specific test file. **Never with `--cov*` flags.**
6. Decide:

   - **Verified.** Append:

     ```
       - **Verification (Worker 1, YYYY-MM-DD):** Verified. <one line: helper landed at path:NN, called from N sites, test_<x> pins the contract>.
     ```

     Return `verified` to Worker 0.

   - **Revision needed.** Something is missing, partial, or regressed. Append:

     ```
       - **Verification (Worker 1, YYYY-MM-DD):** Revision needed. <specific: which call site was missed, which assertion is unpinned, what regressed>.
     ```

     Return `revision-needed` to Worker 0. Worker 0 re-dispatches Worker 2.

7. Append a memory entry only when the pass reaches a `verified` state (do not append on `revision-needed`; wait until the cycle resolves).

### Verification discipline

A verification pass is also a **reading exercise**. Compare the diff to the Triage's recommended shape and the spec / source-artifact context. If a regression is suspected but not certain, prefer flagging `revision-needed` with the specific concern over accepting and discovering later. False acceptances are more expensive than false rejections in this workflow because the DRY cycle's whole purpose is to leave the package in a more consolidated shape.

## Final test-run gate

When Worker 0 dispatches the final gate (every finding is `- [x]` or removed), run these commands in order and record each result in a `## Final test-run gate` section appended at the end of the plan:

1. `uv run pytest --no-cov` — full sweep. The explicit `--no-cov` is required because `pytest.ini` auto-applies `--cov`.
2. `uv run python examples/fakeshop/manage.py check` — Django system check.
3. `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — migration consistency.
4. `uv run ruff format --check .` — read-only format check; do NOT pass `--fix`.
5. `uv run ruff check .` — read-only lint check; do NOT pass `--fix`.
6. `git diff --check` — whitespace / conflict-marker check on the working tree.

Record each command's pass/fail with a one-line summary. If any fails, return the failing command to Worker 0; do not append a `verified` status to the gate. Failures block closeout.

If a failure surfaces tool-induced drift in a file that no finding touched, escalate to Worker 0 — the cycle's lint / format gate failed on baseline issues, which is a workflow defect rather than a finding defect.

## Memory entry

Append 3-5 lines per closed pass (triage with a disposition, verification with `verified`, or final-gate completion). Capture:

- the finding handled and the disposition
- a triage / verification signal worth carrying forward (e.g. "review-style 'New helpers at N=2' triage as `not-real` ~80% of the time", "verification often catches a missed call site in `optimizer/walker.py` parallel branches")
- the focused test that confirmed the consolidation, if any

Entries are append-only. Consolidate before appending when the file exceeds ~50 lines.

## Stop conditions

Stop and record the blocker if:

- the source artifact named in the finding cannot be located
- the cited code lines have moved or been deleted and the triage cannot reconcile against current source
- Worker 2's diff is unavailable during a verification pass
- the consolidation would require a package-wide redesign beyond the finding's scope (escalate to Worker 0 with a one-line summary)
- the final test-run gate produces a failure unrelated to any cycle finding
