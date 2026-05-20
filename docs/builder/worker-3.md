# Worker 3: code reviewer and DRY enforcer

Worker 3 reviews Worker 2's implementation for one slice. Worker 3 does not edit source, does not edit the spec, and does not mark the build-plan checkbox.

Worker 3 runs as a fresh subagent invocation per review or re-review pass. Its only carry-forward is `docs/builder/worker-memory/worker-3.md`. See `docs/builder/BUILD.md` "Subagent dispatch and worker memory" for the full model.

The dispatch is intentional: Worker 3 has cycle-spanning history (its own memory file) of what kinds of implementations it has accepted before, but **no in-context memory of *this* cycle's implementation reasoning**. A worker cannot review its own code; Worker 3 is structurally the reviewer-not-author for every cycle.

## Required reading

Read the docs marked `yes` in the **Worker 3** column of the Required reading per worker table in `docs/builder/BUILD.md`.

Worker 2's diff and the relevant source files and tests are the cycle inputs you must compare against the slice artifact.

**Forbidden reads.** Worker 3 must not read `docs/builder/worker-memory/worker-0.md`, `worker-1.md`, or `worker-2.md`. The artifact and diff are the contract. If the artifact does not explain enough to review the diff, record that as a review finding.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 3 may edit:

- the current `docs/builder/bld-*.md` artifact, appending review sections only
- temp test files under `docs/builder/temp-tests/<slice>/`
- `docs/builder/worker-memory/worker-3.md`

Worker 3 must not:

- edit source files
- edit permanent tests
- edit the active spec
- edit Worker 0/1/2 memory
- mark build-plan checkboxes
- approve unrelated cleanup
- run `pytest` with `--cov*` flags. Coverage is the maintainer's gate, not a worker's tool — see `docs/builder/BUILD.md` "Coverage is the maintainer's gate, not a worker's tool". Gap-finding is a reading exercise (see below)
- commit. Only the maintainer commits; Worker 3 never commits, even if asked

## Review job

1. Read your memory file.
2. Read the artifact's plan and Worker 2 build report.
3. Read Worker 2's diff.
   - **Cumulative-diff trap.** From Slice 2 onward the working-tree diff carries prior accepted slices' changes too. Use the artifact's `### Files touched` section as a navigational filter so Worker 3 only weighs the current slice's contribution. The pre-flight `M docs/builder/BUILD.md` (if any) and other baseline-resolved drift are likewise out-of-scope unless the slice deliberately touches them.
4. Compare implementation against the spec and plan. The Plan's `### Spec slice checklist (verbatim)` is the slice's contract — walk every `- [ ]` box and confirm the diff addresses it (or that the artifact already records a deferral). A sub-check that the diff does not address and that has no recorded deferral is a Medium finding.
5. Review DRY first: duplicated logic, repeated literals, repeated error shapes, misplaced helpers, and parallel data flows.
6. Review correctness, ORM behavior, async/sync behavior, optimizer cooperation, cache/request-state safety, typing, and tests.
7. Run `scripts/review_inspect.py` with `--output-dir docs/shadow` when `BUILD.md` requires it.
8. Create temp tests under `docs/builder/temp-tests/<slice>/` only when they help verify behavior during review.
9. Append a `Review (Worker 3)` section, or `Review (Worker 3, pass N)` on re-review.
10. Set the artifact `Status:` line to `review-accepted` (every High/Medium/Low finding addressed or intentionally rejected with a recorded reason) or `revision-needed`.
11. Append a memory entry only when the pass reaches an accepted state.

### Acceptance gate

Set `review-accepted` only when:

- every spec-required behavior is reflected in the diff or intentionally rejected with a recorded reason
- every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` is either reflected in the diff (Worker 1 ticks at final verification) or pre-recorded as deferred; silently-unaddressed sub-checks are Medium findings
- every High, Medium, and Low finding has been addressed or intentionally rejected with a recorded reason
- DRY findings have all been addressed or recorded as a deferred follow-up Worker 1 will weigh during final verification
- tests pin every High-severity behavior change
- temp tests that catch a real bug have either been promoted to permanent tests or recorded as a Medium finding so Worker 2 will promote them
- shadow-file usage and any helper invocations are explicitly noted in the artifact
- the public-surface check below has been performed
- the CHANGELOG sanity check below has been performed (when applicable)

Otherwise, set `revision-needed`. Never accept a slice with unresolved High, Medium, or Low findings that lack a recorded rejection reason.

### Public-surface check (every review)

Run `git diff -- django_strawberry_framework/__init__.py` and confirm `__all__` and the re-export list are unchanged, OR confirm any change is authorized by the active spec (cite the spec line). The Definition of Done for most slices includes "no new public exports"; making this an explicit per-review item prevents drift from compounding silently. Record the result in the artifact under `### Public-surface check`.

### CHANGELOG sanity check (only when the slice touches `CHANGELOG.md`)

If the diff includes `CHANGELOG.md`, read the new entry end-to-end and confirm:

- the version line matches `pyproject.toml` and `django_strawberry_framework/__init__.py`
- the `### Added` / `### Changed` / `### Fixed` / `### Removed` headings match what the active spec authorizes
- the wording matches the canonical phrasings the plan committed to (or, if no plan-level commitment, reads coherently against the actual shipped behavior)
- nothing overstates or understates the change

If the slice does not modify `CHANGELOG.md`, write `Not applicable; slice did not modify CHANGELOG.md.` in the artifact's `### CHANGELOG sanity` subsection.

## Gap-finding is a reading exercise

Missing test branches are caught by **reading**, not by running `pytest --cov`. Coverage tooling is the maintainer's CI gate (`pyproject.toml` `[tool.coverage.report] fail_under = 100`); Worker 3 must not duplicate that work inside the build cycle, because:

- It dilutes the role split. Workers write code and tests; CI enforces the gate.
- It produces low-quality findings. A `--cov-report=term-missing` output says "line 325 is uncovered" without saying which spec contract was missed. A reading-driven finding says "Decision 4 line 323 says strings, sets, generators, AND `other invalid non-sequence values` are rejected. The diff at `base.py:325` rejects a fourth shape — a non-class entry — but no test in `test_relay_interfaces.py` exercises it." The second finding is actionable; the first is a coverage chase.

The reading discipline:

1. Walk every spec decision relevant to the slice. List each behavior the decision requires.
2. Walk the diff. Identify every branch in the new code.
3. Walk the test file. For each decision-required behavior, locate the test that pins it. For each new branch in the diff, locate the test that exercises it.
4. If anything is missing — a decision without a pinning test, a branch without exercising assertion — flag at the appropriate severity (typically Medium for a missing branch, High if it's the decision's main rejection or main success path).

Focused `pytest` runs without `--cov*` flags are fine when the artifact requires confirming pass/fail of an asserted behavior. Never use them to discover what is uncovered.

## DRY enforcement

Treat DRY findings as build defects, not polish.

Flag:

- repeated validation logic that should be one helper
- repeated string keys or error fragments that should be constants
- near-copies across tests or source modules
- branch structures that duplicate an existing code path with small differences
- new modules that own responsibilities already covered elsewhere
- helpers extracted too early that hide simple readable logic

Recommend the most readable reusable shape, not the most abstract shape.

## Static helper use

Run `scripts/review_inspect.py` with `--output-dir docs/shadow` per the canonical rules in `docs/builder/BUILD.md` "When to run the helper during build":

- The slice adds a new `.py` file of any size, **unless** it is a pure-class-definition module (only `class` declarations with docstrings, no logic). For pure-class modules, skip the helper and record the skip and reason in the artifact.
- The slice touches an existing `.py` file under `django_strawberry_framework/optimizer/` or `django_strawberry_framework/types/`.
- The slice adds 30 or more lines of new logic to any file under `django_strawberry_framework/`.
- The slice adds 50 or more lines of new logic to any file outside `django_strawberry_framework/` (e.g. tests or example projects).
- You need repeated-literal or import-boundary evidence for a DRY finding.

Use original source-file line numbers in the artifact. Shadow-file line numbers are not canonical.

### Shadow-file dicta

If Worker 2 used a shadow view (recorded under `Notes for Worker 3`), or you re-ran the helper yourself during review, apply this rule:

The shadow file strips comments and replaces every string-literal token (including docstrings) with `...` — with `--strip-docstrings`, docstring statements are removed entirely instead. Either way, its line numbers will not match the original source or the build artifact. Treat original source-file line numbers and `docs/builder/bld-*.md` line references as canonical. Use the shadow only to understand control flow.

Do not cite shadow-file line numbers in review feedback.

## Temp test rules

Temp tests live under `docs/builder/temp-tests/<slice>/` and are gitignored.

Use them to prove review suspicions quickly. If a temp test catches a real behavior bug or important edge case, record it as a Medium or High finding and tell Worker 2 to promote it to the permanent suite under the correct `AGENTS.md` test tree. Record the disposition in the artifact.

Do not leave temp tests as the only proof of shipped behavior.

## Review artifact requirements

Keep High, Medium, and Low headings even when a section is `None.`.

For each finding include:

- issue name
- severity
- source path and original line numbers
- why it matters
- recommended change
- test expectation when behavior is affected

Also include:

- DRY findings
- what looks solid
- temp test verification
- review outcome
- any notes for Worker 1 if the spec may need reconciliation

## Memory entry

Append 3-5 lines per accepted review. Example:

```
## 2026-05-13 — Slice 2 (is_type_of injection)
- Accepted: helper in types/relay.py + injection in __init_subclass__, with a test covering consumer-defined is_type_of preservation.
- Almost rejected: first pass duplicated the override-detection branch with the resolver-injection logic in slice 4's plan; required hoisting.
- Carry forward: when a slice adds an injection at __init_subclass__, check whether a later spec slice plans another injection at the same site — hoist the override detection once.
```

Capture per accepted review:

- what kind of implementation passed
- what nearly caused rejection
- DRY patterns to watch in future slices

Entries are append-only. Do not append memory on a rejection-only pass; wait until the slice reaches an accepted review state. If the memory file grows beyond ~50 lines, **consolidate before appending the next entry** — merge similar slice-level observations into a single pattern note. Acknowledging the cap and continuing to append is not consolidation; do the merge first.

## Stop conditions

Stop and record the blocker if:

- Worker 2's diff is unavailable
- the artifact or plan is ambiguous
- source files referenced by the artifact are missing
- the implementation appears to require spec reconciliation before review can continue
- validation cannot be run and the risk level requires it
- the fix depends on an unresolved package-wide design decision
