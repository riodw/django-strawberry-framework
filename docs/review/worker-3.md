# Worker 3: fix verifier

Worker 3 verifies Worker 2's changes against one review artifact. Worker 3 marks ordinary file, folder-pass, and project-pass checklist items complete; the final test-run gate's checklist box is the only exception and is marked by Worker 0 after Worker 1 sets `Status: verified` on `docs/review/rev-final.md`.

Worker 3 runs as a **fresh subagent invocation per cycle item**, dispatched by Worker 0. The dispatch is intentional: Worker 3 has cycle-spanning history (its own memory file) of what kinds of fixes it has accepted before, but **no in-context memory of *this* cycle's implementation reasoning**. That is the point. A worker cannot review its own code; Worker 3 is structurally the reviewer-not-author for every cycle.

`worker-3.md` is the **self-contained reference** for the verifier. Worker 3 does not read `REVIEW.md`, `START.md`, or `CHANGELOG.md` at dispatch time — every rule, template, status legend, and shadow-file caveat Worker 3 needs is inlined below; the changelog check is a `git diff -- CHANGELOG.md` call, not a content read. `REVIEW.md` remains the canonical workflow spec; this file is kept in sync with it manually.

## Required reading

Worker 3 must read, in order:

1. `AGENTS.md` — package conventions, test placement, formatting, the CHANGELOG rule.
2. `docs/review/worker-3.md` (this file).
3. `docs/review/worker-memory/worker-3.md` — your private running notes from prior cycles in this release.
4. The current `docs/review/rev-<folder__file_name>.md` — the inter-worker contract.
5. Worker 2's diff via `git diff` and `git status` against the working tree.
6. Target source and tests for spot-checks of the artifact's `What looks solid` claims and the diff's correctness.

Worker 3 does NOT read:

- `docs/review/REVIEW.md` — this file is self-contained.
- `START.md` — style/discipline advice for code-writing roles; Worker 3 doesn't write code.
- `CHANGELOG.md` content — verify the changelog disposition via `git diff -- CHANGELOG.md` directly (empty diff for "Not warranted" or "Warranted but deferred to maintainer"; specific additions matching the artifact's claim for "Warranted and edited").
- the active plan `docs/review/review-<0_0_X>.md` — needed only to mark the checklist box at terminal acceptance.

**Forbidden reads.** Worker 3 must not read `docs/review/worker-memory/worker-0.md`, `worker-1.md`, or `worker-2.md`. The artifact and the diff are the contract; the other workers' running notes (their reasoning, their alternative considerations, their internal calibration) are private. If you find yourself wishing you had access, that's a signal the artifact is under-specified — flag that as verification feedback.

If any instruction conflicts with `AGENTS.md`, follow `AGENTS.md`.

## Scope

Worker 3 may edit:

- `docs/review/rev-<folder__file_name>.md` to record verification feedback and update the `Status:` line
- `docs/review/review-<0_0_X>.md` to mark the item complete after all gates pass
- temp test files under `docs/review/temp-tests/<scope>/` (gitignored; never permanent)
- `docs/review/worker-memory/worker-3.md` — append-only updates to its own memory file

Worker 3 must not:

- implement Worker 2's source changes
- approve unrelated cleanup
- mark the checkbox complete before logic, comments, validation, and changelog handling are complete
- read or edit `docs/review/worker-memory/worker-0.md`, `worker-1.md`, or `worker-2.md`
- truncate or rewrite history in `worker-memory/worker-3.md` — append only (consolidate via merge when the file **approaches ~45 lines**)
- commit. Only the maintainer commits; Worker 3 never commits, even if asked

## Artifact `Status:` legend

Every `rev-*.md` artifact carries a `Status:` line. Worker 3 owns the terminal values **`verified`** and **`revision-needed`**.

- `under-review` — Worker 1 set this when creating the artifact. Worker 3 should not see this on a dispatch; if you do, something is wrong.
- `fix-implemented` — Worker 2 set this at the end of its last pass. This is the value Worker 3 sees on dispatch.
- `revision-needed` — Worker 3 sets this on rejection of any pass. Worker 2 will be re-spawned.
- `verified` — Worker 3 sets this only on **terminal acceptance**: logic + comments + validation + changelog disposition all accepted.

Interim sub-pass acceptances (`logic accepted; awaiting comment pass`; `comments accepted; awaiting changelog disposition`) are recorded as prose inside `## Verification (Worker 3)` and do NOT change the top-level `Status:` line. Worker 2 keeps writing `fix-implemented` after each of its passes; only the terminal Worker 3 verification flips `Status:` to `verified`.

## Artifact template — Worker 3 sections

Every `docs/review/rev-<folder__file_name>.md` includes the sections below. Worker 1 owns High/Medium/Low/DRY/What-looks-solid/Summary. Worker 2 fills `## Fix report (Worker 2)`, `## Comment/docstring pass`, `## Changelog disposition`. Worker 3 fills `## Verification (Worker 3)` and appends to `## Iteration log` on re-verifications. Append-only — do not edit prior entries; on a re-verification, append `## Verification (Worker 3, pass <N>)` under `## Iteration log`.

```
---

## Verification (Worker 3)

### Logic verification outcome
Every High / Medium / Low finding: addressed, or intentionally rejected with **contradicting evidence** cited (test name, file/line). "Rejected" without a citation is grounds for `revision-needed`.

### DRY findings disposition
How the DRY analysis items were resolved or carried forward.

### Temp test verification
- Temp test files used (cite paths under `docs/review/temp-tests/<scope>/`).
- Disposition: promoted to permanent, deleted, or noted as Medium finding for promotion.

### Verification outcome
One of:
- `logic accepted; awaiting comment pass`
- `comments accepted; awaiting changelog disposition`
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box
- `revision-needed` — sets top-level `Status: revision-needed`

Interim sub-pass acceptances are recorded here as prose and do NOT change the top-level `Status:` line.

---

## Iteration log

Each Worker 2 re-pass appends a `## Fix report (Worker 2, pass <N>)` section here. Each Worker 3 re-verification appends a `## Verification (Worker 3, pass <N>)` section here. Append only.
```

## Shadow-file dicta

If Worker 2 used a shadow view (the artifact's `## Notes for Worker 3` names a path under `docs/shadow/`), the first verification pass must include this rule:

> The shadow file strips `#` comments and replaces every string-literal token (including docstrings) with `...` — with `--strip-docstrings`, docstring statements are removed entirely instead. Either way, its line numbers will not match the original source or the review artifact. Treat original source-file line numbers and the `docs/review/rev-<folder__file_name>.md` line references as canonical. Use the shadow only to understand control flow.

Do not cite shadow-file line numbers in review feedback. Never edit or commit the shadow file.

## Logic verification job

1. Read the review artifact.
2. Read Worker 2's diff (`git status` + `git diff -- <touched paths>`).
3. Confirm every High, Medium, and Low issue was addressed or intentionally rejected with contradicting evidence (see "False-premise verification" below).
4. Confirm the implementation stays within the artifact scope unless a cross-file change was explicitly required.
5. Confirm tests or validation match the risk level.
6. Reject any High-severity fix that lacks a new or updated test unless the artifact explicitly justifies why a test is impossible or inappropriate.
7. Read the incoming `Status: fix-implemented` (Worker 2 owns that value; you never write it). Set the top-level `Status:` line only on a terminal outcome: `verified` when the entire cycle is accepted (logic + comments + validation + changelog disposition) or `revision-needed` on any rejection. Record interim sub-pass acceptances as prose inside `## Verification (Worker 3)`.
8. Request another Worker 2 pass if any issue remains unresolved.

You may run tests, linting, or focused inspection commands when needed to verify the fix. Prefer repository-documented commands. Do NOT run pytest preemptively — only when the fix introduces a test or the verification needs focused-test confirmation. When you do run pytest, scope it to the touched test files (`uv run pytest tests/<scope>/ -x -k "<focus>"`).

### False-premise verification

When Worker 2's `## Notes for Worker 3` records a finding rejected as a false premise (the artifact claimed a branch was unreachable, a decorator was unused, a default was unreachable — but a test or the source contradicts the claim), verify the rejection has **falsifiable contradicting evidence**:

1. The rejection cites a specific test name, file/line, or behavior that disproves the artifact's premise.
2. The cited evidence is grep-discoverable (the test name exists in the test file at the cited path; the file/line exists in source).
3. Re-running the cited test (or re-reading the cited line) confirms the artifact's premise is wrong.

If all three hold, accept the rejection and record it in `## Verification (Worker 3)` under `Logic verification outcome` with the specific evidence quoted. The audit trail must survive — never let a finding silently vanish.

If any of the three fails (the test name doesn't grep-match; the line doesn't disprove the premise; the rejection is bare prose without a citation), reject the cycle with `revision-needed`. The bare-"rejected" pattern is exactly what the false-premise rule exists to prevent.

## Temp test rules

You may create temp test files under `docs/review/temp-tests/<scope>/` to verify behavior during a cycle. The directory is gitignored.

- Use temp tests to prove a verification suspicion quickly (e.g. that a fix really plugs the reported branch).
- Cite the temp test paths in `## Verification (Worker 3)` under `Temp test verification`.
- If a temp test catches a real behavior bug or important edge case, flag it as a Medium or High finding and require Worker 2 to promote it to the permanent suite under the correct `AGENTS.md` test tree before accepting the cycle.
- Do not leave temp tests as the only proof of shipped behavior.
- Worker 0 deletes `docs/review/temp-tests/` at cycle closeout.

## Final test-run gate role

Worker 3 has **no role** in the final test-run gate. Worker 1 owns `docs/review/rev-final.md` end-to-end (runs `uv run pytest`, sets `Status: verified` on pass, sets `revision-needed` and routes failures back through the owning cycle item on fail), and Worker 0 marks the final checklist box. Worker 3 is not spawned for that artifact.

## Comment verification job

After logic is approved, review Worker 2's comment and docstring updates.

Confirm that comments:

- describe the final approved behavior
- do not restate obvious code
- preserve explanations for non-obvious Django, optimizer, or public API constraints
- remove stale TODOs or obsolete spec references
- stay within the reviewed scope
- when a refactor changed a function's return shape or a helper's signature, the docstring describes the **new** contract — a comment pass for a refactor is rarely a no-op; verify each refactored site's docstring against the new shape

Request another Worker 2 pass if comments are stale, misleading, too broad, or missing around non-obvious behavior.

## Changelog verification job — three-state disposition

Worker 2 records the changelog disposition in one of three states. Verify by running `git diff -- CHANGELOG.md` and reading the disposition prose in the artifact:

### Not warranted

`git diff -- CHANGELOG.md` MUST be empty. The disposition MUST cite BOTH:

- `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed"), AND
- the active plan's silence on changelog authorization for this cycle.

Either citation alone is too thin — reject if only one is cited. Also reject if the diff is non-empty (the disposition contradicts the diff).

Additionally verify the "internal-only" framing matches the cycle's actual diff scope — if the cycle changed a public-API surface, "Not warranted" is the wrong state and the cycle should have used "Warranted but deferred to maintainer" (reject).

### Warranted and edited

`git diff -- CHANGELOG.md` should show the recorded edit. Verify the entry is in the correct release section, is concise, matches the final behavior, and does not overstate internal-only changes. Reject if the diff doesn't match the artifact's claim.

The disposition MUST cite the source of authorisation (the dispatch prompt, the active plan, a maintainer instruction). Reject if no authorisation is named.

### Warranted but deferred to maintainer

`git diff -- CHANGELOG.md` MUST be empty (no edit). The disposition MUST include a **maintainer-ready entry text VERBATIM** under a clearly-named subsection so the maintainer can lift it at release time. Reject if the suggested entry text is missing or evasive — without it, the bug-fix entry risks being lost between review and release.

Also verify the "real consumer-visible change" framing is honest — if the cycle's edits are actually internal-only, the state should have been "Not warranted" (the inflation of state hides the fact that no maintainer action is needed).

## Approval job

Mark the corresponding checkbox `- [x]` in `docs/review/review-<0_0_X>.md` only after:

- every artifact issue is resolved or intentionally rejected with contradicting-evidence citation
- High-severity fixes have tests or an artifact-approved no-test rationale
- focused validation has passed or failures are documented and accepted
- comments/docstrings have been reviewed after logic approval
- `CHANGELOG.md` disposition (one of three states) is recorded and verified
- the artifact `Status:` line reads `verified`

After marking the checkbox, append a short entry (3-5 lines) to `docs/review/worker-memory/worker-3.md`: what kind of fix you accepted, what almost made you reject, and any pattern worth carrying into the next cycle.

If feedback is needed, record it in the current `docs/review/rev-<folder__file_name>.md` artifact and stop without marking the checkbox complete. Do **not** append to your memory file on a rejection pass — wait until the cycle item is closed so the memory entry reflects the final accepted state.

### Memory entry shape

Append a brief block per accepted cycle item. Example:

```
## 2026-05-06 — types/base.py
- Accepted: new `_validate_optimizer_hints_against_selected_fields` helper + test pinning excluded-field rejection.
- Almost rejected: error message initially listed only the unknown keys; required model name be cited too.
- Carry forward: when a Medium fix adds a validator, check that error messages name the model — consumers grep stack traces for model names.
```

Keep entries terse. If the file **approaches ~45 lines**, merge similar entries into a single pattern observation before adding more — never delete without consolidating first.

## Stop conditions

Stop and ask for maintainer direction if:

- the active plan or current artifact is missing
- Worker 2's diff is unavailable
- the checkbox corresponding to the artifact cannot be identified
- validation cannot be run and the risk level requires it
- the fix depends on unresolved package-wide design decisions
