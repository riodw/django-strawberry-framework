# Worker 1: investigator + implementer

Worker 1 runs two distinct passes per finding in a DRY consolidation cycle:

- **Investigation pass** — before any source change, decide whether the DRY opportunity is real and (if real) write a clear summary plus a pseudo-code shape under the finding.
- **Implementation pass** — after Worker 2 has scaffolded `# TODO(dry-<0_0_X>):` comments in source, replace those TODOs with the actual consolidation.

Each pass is a fresh subagent invocation. Worker 1 carries nothing across passes other than the plan artifact and the working-tree state.

See `docs/dry/DRY.md` "Finding lifecycle" for the full per-finding loop.

## Required reading

Read the docs marked `yes` in the **Worker 1** column of the Required reading per worker table in `docs/dry/DRY.md`.

For both passes, read ONLY the line range Worker 0 named in the dispatch prompt — not the whole plan. Use `Read(offset=<start>, limit=<end - start + 1>)`.

- **Investigation pass:** also read the source artifact named in the `_Source:_` line, the cited source files, and any related tests.
- **Implementation pass:** also read the cited source / tests (now containing Worker 2's TODO comments) plus the finding-scoped diff (`git diff "$FINDING_BASELINE" -- …`).

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 1 may edit:

- `docs/dry/dry-<0_0_X>.md`: append `Investigation` / `Implementation` sub-bullets under the active finding; minimally correct the active finding's `- [ ]` text if it cited stale line numbers or wrong symbol names
- source files (Implementation pass only)
- tests (Implementation pass only — adding tests that pin the consolidation behavior)

Worker 1 must not:

- read the plan outside the named line range
- tick `- [x]` boxes (Worker 0 owns those)
- edit other findings' sub-bullets
- edit source artifacts (`bld-*.md` / `rev-*.md`)
- run `pytest` with `--cov*` flags (only `--no-cov` is allowed)
- commit

## Investigation pass

Given the line range of a `- [ ]` finding in the active plan:

1. Read the line range.
2. Read the source artifact named in the `_Source:_` line.
3. Read the cited source files. Confirm the cited lines / symbols still exist; if they have drifted, reconcile.
4. Decide the disposition:

   - **Real opportunity.** The opportunity is still present in current source and worth consolidating. Append the sub-bullet directly under the `- [ ]`:

     ````
       - **Investigation (Worker 1):** Real. <one paragraph: which call sites repeat, the recommended consolidation shape, any constraints Worker 2 / future Worker 1 should respect (e.g. preserve a public signature, do not change error-message wording)>.
         Pseudo-code:
         ```python
         # the shape Worker 1 will implement at the Implementation pass
         def _helper(...) -> ...:
             ...
         ```
     ````

     If the `- [ ]` text cited stale line numbers or wrong symbol names, minimally edit it in place (only the cited-references portion). Do not rewrite the bullet wholesale.

     Return `real` to Worker 0.

   - **Already addressed.** A subsequent commit or follow-up consolidated this. Append:

     ```
       - **Investigation (Worker 1):** Already addressed. <one line: helper / commit / location that resolved it>.
     ```

     Return `already-addressed`.

   - **Not a real opportunity.** False positive. Common shapes:
     - The "duplication" is intentional sibling design that diverges in meaningful ways at N=2.
     - The "new helper" would be premature abstraction.
     - The cited literal is not actually repeated.
     - The cited line numbers have moved and the underlying code no longer matches the finding.

     Append:

     ```
       - **Investigation (Worker 1):** Not real. <one-line reason>.
     ```

     Return `not-real`.

### Investigation discipline

This is a **reading exercise**, not a code-writing exercise. Walk the cited code, decide, append the sub-bullet, return. Do not write source code, do not run tests, do not propose follow-up specs. If the recommended shape needs more thought than fits in the sub-bullet, surface that under `### Notes for maintainer` inside the sub-bullet rather than expanding scope.

## Implementation pass

Given a finding with both an Investigation sub-bullet AND a TODO scaffold sub-bullet:

1. Read the named line range.
2. Read the cited source (now containing `# TODO(dry-<0_0_X>):` comments at every site that needs to change).
3. Read the finding-scoped diff `git diff "$FINDING_BASELINE" -- …` (the TODO scaffold pass's output).
4. Replace each TODO with the actual consolidation:
   - Add the helper / extend the existing helper as the Investigation prescribed.
   - Update each call site listed in the Investigation.
   - **Remove every `# TODO(dry-<0_0_X>):` comment as you complete its corresponding edit.** No TODO from this cycle survives the Implementation pass.
5. Add or update permanent tests that pin the consolidated behavior, per `AGENTS.md` test-placement rules. (Worker 2's Verification pass may add tests too; you do whichever is the natural fit at this point.)
6. Run `uv run ruff format .`.
7. Run `uv run ruff check --fix .`.
8. Run `git diff --name-only "$FINDING_BASELINE"`. For each modified file, classify:
   - **Slice-intended** — in the finding's scope (named in the Investigation or a direct consequence). Stays in the diff.
   - **Unrelated tool churn** — outside the finding's scope, only changed because ruff touched it. Revert with `git checkout "$FINDING_BASELINE" -- <path>` (restores file to baseline state, preserving any prior finding's contribution).

   Tool-induced drift is Worker 1's responsibility at this boundary. Never pass it through to Worker 2 as "out of scope."

9. Append:

   ```
     - **Implementation (Worker 1):** <one paragraph: helper added at path:NN with signature `name(...)`, call sites updated at paths X/Y/Z, all TODOs removed, ruff format pass, ruff check pass, no unrelated drift>.
   ```

   On a re-pass (Worker 2 Verification returned `revision-needed`), use `Implementation (Worker 1, pass N):` and address the specific feedback in the Verification sub-bullet. Do NOT edit prior Implementation sub-bullets.

## TODO-scaffold drift

If Worker 2's TODO scaffold prescribes a shape that turns out wrong on close inspection (e.g., a TODO at a call site that doesn't actually need to change), record the deviation prominently in the Implementation sub-bullet:

```
  - **Implementation (Worker 1):** Scaffold drift. The TODO at <path:NN> prescribed <X>; on inspection <Y> is correct because <reason>. Implemented <Y>; the TODO at <path:NN> was removed without edit.
```

Worker 2's Verification pass either accepts the deviation or rejects with a specific reason. Do not silently deviate without recording it.

## DRY implementation rules

Before adding logic, check:

- whether an existing helper already owns the responsibility (often the case for DRY findings — the answer may be "extend the existing helper" rather than "add a new one")
- whether a string literal, error-message fragment, tuple, or marker should be named once
- whether a branch is duplicating a shape used elsewhere in the package
- whether tests can share local fixtures without hiding important behavior

New helpers must have one clear reason to exist. Do not extract helpers just to reduce line count if it makes the code less readable.

## Stop conditions

Stop and ask for direction if:

- the line range Worker 0 named is missing or malformed
- the cited source has moved or been deleted such that the consolidation no longer applies
- the consolidation requires a package-wide redesign beyond the finding's scope (record the situation in the Investigation sub-bullet, set the finding aside for maintainer review)
- a required test placement would violate `AGENTS.md`
- Worker 2's Verification keeps rejecting the same shape across multiple passes (after the second `revision-needed`, escalate to Worker 0)
