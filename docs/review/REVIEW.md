# Package review workflow

Review every Python file under `django_strawberry_framework/` one file at a time. The target is
one file; the thinking is not. Follow its behavior through the rest of the system before deciding
whether it is correct or could be better.

The process exists to create space for three things:

1. **Verify.** Use scratch tests and focused experiments to challenge assumptions.
2. **Understand.** Take the time to trace how the target participates in the whole system.
3. **Improve.** Look creatively for a clearer, safer, or more capable design—not only bugs.

Everything recorded in an artifact should help one of those activities.

## Ground rules

- Read `AGENTS.md`, `START.md`, `README.md`, `GOAL.md`, `docs/README.md`, `docs/TREE.md`, and
  `docs/GLOSSARY.md` before beginning a run.
- `AGENTS.md` governs code, tests, formatting, changelog edits, and repository safety.
- Work on one planned target at a time. Read any connected code, tests, history, documentation,
  or upstream implementation needed to understand it.
- Prefer the root-cause fix. Put a rule at the layer that owns it.
- Similar code is not automatically duplication. Consolidate only when the sites implement the
  same rule and should change together.
- Record confirmed problems and worthwhile improvements, not generic checklist observations.
- Only the maintainer commits.

## Review plan

Worker 0 creates `docs/review/review-<release>.md` from the matching versions in
`pyproject.toml` and `django_strawberry_framework/__init__.py`. Do not overwrite an existing plan.

The plan lists:

- every non-`__init__.py` Python file under `django_strawberry_framework/`
- one integration pass after each folder
- one project integration pass, including top-level and package `__init__.py` files
- the final test gate

Each item links its artifact. Artifact names start with `rev-`, use the source path relative to the
package, replace `/` with `__`, and drop `.py`. For example, `optimizer/walker.py` becomes
`docs/review/rev-optimizer__walker.md`; the folder pass becomes `rev-optimizer.md`.

The plan states whether the run is autonomous or pauses after each item. It also records a cycle
baseline so review diffs can be separated from prior and concurrent work.

## The review

### 1. Understand

Read the entire target. Then follow the important paths into and out of it until you can explain:

- what responsibility and state it owns
- who calls, imports, registers, or exposes it and what they expect
- which helpers, frameworks, settings, ORM behavior, or global state it relies on
- how representative input becomes output, error, database work, or persistent state
- which tests and public documentation describe its behavior

Use `rg`, source history, sibling implementations, example-project usage, and upstream sources as
needed. Do not stop at an adapter when the real contract lives behind it. Do stop when an edge is
well understood and further expansion would not change the judgment.

Pay special attention to boundaries relevant to the target: invalid or empty input, repeat calls,
partial failure, cache and request isolation, sync/async behavior, database aliases, permissions,
optional dependencies, schema lifecycle, and GraphQL type selection. This is a prompt for thought,
not a checklist to reproduce in the artifact.

For folder and project passes, re-read the integrated source. Look for behavior that no individual
file owns cleanly: mismatched lifecycle phases, inconsistent public flavors, circular dependencies,
duplicated policy, unclear state ownership, and gaps between package behavior and its tests or docs.

### 2. Verify

Challenge every important conclusion. Prefer a small executable experiment over reasoning from
memory when framework behavior, state, ORM semantics, or an edge case is uncertain.

Scratch tests belong under `docs/review/temp-tests/<scope>/` and remain untracked. They may probe
private state, isolate a strange sequence, or deliberately violate assumptions. Keep them small and
disposable. Record what was run and what it proved.

A scratch test is evidence, not permanent coverage. If it exposes a real behavior that must remain
correct, the fix must add a permanent test at the strongest reachable level required by `AGENTS.md`:
live GraphQL usage first, then example-project tests, then package tests. Verification should try to
disprove findings and fixes, not merely repeat the expected happy path.

Do not run the full test suite during ordinary cycles. Use focused tests when an implementation or
verification pass needs them, normally with `--no-cov` so the package-wide coverage gate does not
turn an intentionally narrow run into a false failure. Enable coverage only when coverage itself is
being verified. The final gate owns the full `uv run pytest` run.

### 3. Improve

After understanding current behavior, ask what design would make the system easier to trust and
extend. Consider bugs, ambiguous contracts, unnecessary state, poor ownership, awkward APIs,
avoidable queries, missing abstractions, over-abstraction, confusing names, weak diagnostics, and
tests that permit the wrong behavior.

Be inventive, but make proposals concrete. A finding must state:

- **Observation:** what is wrong or meaningfully improvable
- **Evidence:** the caller, behavior trace, experiment, test, or contract supporting it
- **Impact:** why it matters beyond aesthetic preference
- **Recommendation:** the root-cause design and its proper owner
- **Proof:** the permanent test or verification that would demonstrate success

Classify findings as High, Medium, or Low by consequence. High means correctness, security,
data-isolation, or public-contract failure. Medium means material performance, design, test, or
edge-case weakness. Low means a bounded clarity or maintainability improvement. If there is no
finding, say so and summarize the evidence that earned that conclusion.

## Artifact

The artifact is a concise record of reasoning and the contract between workers. Use this template;
expand a section only when the target warrants it.

```text
# Review: `path/to/target.py`

Status: under-review | fix-implemented | revision-needed | verified

## Understanding

What the target owns, how it connects to the system, and the important behavior traced.

## Verification

Scratch experiments, existing tests examined, and what they proved or failed to prove.

## Improvements

### High

### Medium

### Low

Each finding: Observation / Evidence / Impact / Recommendation / Proof.
Write `None.` under empty severities.

## Summary

A short overall judgment.
```

When the review finds genuine duplication, insert `### DRY analysis` before `## Summary` with one
top-level bullet per duplication finding already described above. Omit the heading when there is no
DRY finding; never emit a `- None.` finding for downstream tooling to collect.

Worker 2 appends `## Implementation (Worker 2)` when implementation begins. Worker 3 appends
`## Independent verification (Worker 3)` when verification begins. Later passes append
`## Iterations`. Do not create empty placeholders or erase the prior audit trail.

Use source references permitted by `AGENTS.md`. Keep excerpts short. Do not inflate the artifact
with inventories, restated instructions, exhaustive applicability tables, or a narration of every
command.

## Cycle

Each item uses fresh workers so the implementer never approves their own work:

1. Worker 1 investigates and writes the artifact with `Status: under-review`.
2. If no tracked change is needed, Worker 1 records that proof and sets `fix-implemented`.
   Otherwise Worker 2 implements all accepted findings and sets `fix-implemented`.
3. Worker 3 independently re-traces the affected behavior and tries to break the result. It sets
   `verified` and checks the plan item, or sets `revision-needed` with concrete feedback.
4. A revision returns to Worker 2, except an inadequate review returns to Worker 1.

Worker 0 coordinates but does not review, implement, or approve. The artifact and scoped diff are
the shared record; private worker memory is optional scratch, never required evidence.

Workers preserve unrelated dirty files. Cycle diffs use the baseline captured by Worker 0, falling
back to `HEAD` when no baseline exists. A cross-file edit is allowed when the target's root-cause fix
requires it; name the expanded ownership in the artifact. Otherwise forward a finding to the folder
or project pass that owns it.

After an edit, Worker 2 runs `uv run ruff format .` and `uv run ruff check --fix .` as required by
`AGENTS.md`. Zero-edit cycles do not run them. Changelog changes require explicit maintainer
authorization; otherwise record only whether the completed change deserves a release note.

## Integration and final gates

A folder pass examines the folder as one component after its file cycles are complete. The project
pass examines public exports and the end-to-end package lifecycle after all folder passes. Neither
pass repeats old summaries; each searches for problems or improvements visible only in combination.

At the final plan item, Worker 1 runs `uv run pytest`. The gate passes only when tests pass and the
configured package coverage remains 100%. Record failures, coverage, skips, and xfails; route a
failure back to the item that owns its cause.

Worker 0 then reports the outcome and removes only generated review scratch under `docs/shadow/`,
`docs/review/temp-tests/`, and `docs/review/worker-memory/`. Never recursively clear
`docs/review/`.
