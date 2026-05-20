# Worker 2: scaffolder + verifier + tester

Worker 2 runs two distinct passes per finding in a DRY consolidation cycle:

- **TODO scaffold pass** — after Worker 1's Investigation lands, add `# TODO(dry-<0_0_X>):` comments in source at every site that needs to change. This pins the structural skeleton before Worker 1 writes the actual code.
- **Verification + test pass** — after Worker 1's Implementation lands, review the diff, confirm the consolidation matches the Investigation, and run / add tests.

Worker 2 also runs the **final test-run gate** once at cycle end.

Each pass is a fresh subagent invocation. Worker 2 carries nothing across passes other than the plan artifact and the working-tree state.

See `docs/dry/DRY.md` "Finding lifecycle" for the full per-finding loop.

## Required reading

Read the docs marked `yes` in the **Worker 2** column of the Required reading per worker table in `docs/dry/DRY.md`.

For all passes, read ONLY the line range Worker 0 named in the dispatch prompt — not the whole plan. Use `Read(offset=<start>, limit=<end - start + 1>)`.

- **TODO scaffold pass:** also read the source artifact named in the `_Source:_` line and the cited source / tests.
- **Verification + test pass:** also read Worker 1's Implementation diff and the cited source / tests.
- **Final test-run gate:** no extra reads required — the gate commands are mechanical.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 2 may edit:

- `docs/dry/dry-<0_0_X>.md`: append `TODO scaffold` / `Verification` sub-bullets under the active finding; append the `## Final test-run gate` section at cycle end; minimally edit Worker 1's Investigation pseudo-code only if scaffold-time inspection surfaces a concrete error in it
- source files (TODO scaffold pass: adding `# TODO(dry-<0_0_X>):` comments; Verification pass: adding tests if needed)
- tests (Verification pass)

Worker 2 must not:

- read the plan outside the named line range
- tick `- [x]` boxes (Worker 0 owns those)
- edit other findings' sub-bullets
- edit source artifacts (`bld-*.md` / `rev-*.md`)
- delete findings
- run `pytest` with `--cov*` flags (only `--no-cov` is allowed)
- commit

## TODO scaffold pass

Given a finding with an Investigation sub-bullet (disposition: `real`):

1. Read the named line range.
2. Read the source artifact and the cited source / tests.
3. Walk the call sites listed in the Investigation. For each site that will change in the Implementation pass, add a `# TODO(dry-<0_0_X>): <one-line description>` comment directly above the line that will change. The TODO names the helper / consolidation shape from the Investigation's pseudo-code so the Implementation pass has structural guideposts.
4. If a call site listed in the Investigation does NOT actually need to change (e.g., already routed through a similar helper), do not add a TODO there; note it in the TODO scaffold sub-bullet as a deviation.
5. If a call site is missing from the Investigation but clearly should be in scope, add a TODO for it and note it in the TODO scaffold sub-bullet.
6. Append:

   ```
     - **TODO scaffold (Worker 2, YYYY-MM-DD):** TODOs added at path1:NN, path2:NN, path3:NN. <corrections to Worker 1's pseudo-code or call-site list, if any>.
   ```

7. Do NOT run ruff, do NOT run tests. TODOs are scaffolding; the Implementation pass owns formatting and lint.
8. `git status --short` should show only added `# TODO(dry-<0_0_X>):` lines in the cited source. Anything else is unrelated drift — revert before returning.

### Editing Worker 1's pseudo-code

If close inspection at scaffold time surfaces a concrete error in Worker 1's pseudo-code (e.g., wrong signature, missing parameter), Worker 2 may minimally edit the Investigation sub-bullet's pseudo-code block. Mark the edit:

````
  - **Investigation (Worker 1, YYYY-MM-DD):** Real. <...>
    Pseudo-code (corrected by Worker 2, YYYY-MM-DD):
    ```python
    # corrected shape
    ```
````

Larger drift (the whole approach is wrong) goes in the TODO scaffold sub-bullet as a deviation note; Worker 1's Implementation pass either accepts the deviation or surfaces it back.

## Verification + test pass

Given a finding with Investigation, TODO scaffold, AND Implementation sub-bullets:

1. Read the named line range.
2. Read Worker 1's Implementation diff.
3. Read the cited source / tests.
4. Confirm:
   - the helper / consolidation lives where the Investigation prescribed
   - every call site listed in the Investigation now routes through the helper
   - **every `# TODO(dry-<0_0_X>):` comment is removed** (a leftover TODO is an automatic `revision-needed`)
   - tests pin the consolidated behavior
5. Run focused tests if the Investigation or Implementation cited a specific test file. **Never with `--cov*` flags.** `uv run pytest --no-cov tests/path/to/test_file.py -x` is the typical invocation.
6. If a permanent test pinning the consolidation is missing, add one per `AGENTS.md` test-placement rules. (Either the Implementation or the Verification pass may add tests; whichever pass spots the gap owns it.)
7. Decide:

   - **Verified.** Append:

     ```
       - **Verification (Worker 2, YYYY-MM-DD):** Verified. <one line: helper landed at path:NN, called from N sites, tests at tests/.../test_<name>.py pin the contract>.
     ```

     Return `verified`.

   - **Revision needed.** Something is missing, partial, or regressed. Append:

     ```
       - **Verification (Worker 2, YYYY-MM-DD):** Revision needed. <specific: which call site was missed, which TODO was left in source, which assertion is unpinned, what regressed>.
     ```

     Return `revision-needed`. Worker 0 re-dispatches Worker 1 Implementation.

### Verification discipline

A verification pass is a **reading + testing exercise**. Compare the diff to the Investigation's recommended shape. If a regression is suspected but not certain, prefer `revision-needed` with the specific concern over accepting and discovering later. False acceptances are more expensive than false rejections in this workflow.

## Final test-run gate

When Worker 0 dispatches the final gate (every finding is `- [x]`), run these commands in order and record each result in a `## Final test-run gate` section appended at the end of the plan:

1. `uv run pytest --no-cov` — full sweep across all test trees. The explicit `--no-cov` is required because `pytest.ini` auto-applies `--cov`.
2. `uv run python examples/fakeshop/manage.py check` — Django system check.
3. `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — migration consistency.
4. `uv run ruff format --check .` — read-only; do NOT pass `--fix`.
5. `uv run ruff check .` — read-only; do NOT pass `--fix`.
6. `git diff --check` — whitespace / conflict-marker check.

Record each command's pass/fail with a one-line summary. If any fails, return the failing command to Worker 0; do not append a `verified` status to the gate. Failures block closeout.

If a failure surfaces tool-induced drift in a file that no finding touched, escalate to Worker 0 — the cycle's lint / format gate failed on baseline issues.

## Stop conditions

Stop and ask for direction if:

- the line range Worker 0 named is missing or malformed
- the cited source has moved or been deleted such that the consolidation no longer applies
- a required test placement would violate `AGENTS.md`
- the Investigation pseudo-code is so off-shape that minimal scaffold-time edits cannot fix it (TODO scaffold the call sites with a deviation note; Worker 1's Implementation pass will resolve)
- the final test-run gate produces a failure unrelated to any cycle finding
