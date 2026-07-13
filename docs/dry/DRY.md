# System-wide DRY review

Review every Python file under `django_strawberry_framework/` one file at a time. The target is one
file; the duplication search is system-wide. Use the target as an entry point into its callers,
dependencies, sibling implementations, tests, examples, and public contracts before deciding what
should be consolidated.

This is a fresh review of the current repository. Do not seed it from old build artifacts, review
artifacts, DRY plans, or their recommendations. They describe earlier reasoning, not present-day
evidence.

The process makes room for three kinds of work:

1. **Understand.** Trace the target's responsibility and how that responsibility is represented
   elsewhere.
2. **Verify.** Use searches, scratch tests, and focused experiments to prove whether apparent
   duplication really behaves and changes together.
3. **Improve.** Find the clearest ownership boundary that makes one rule, shape, or lifecycle have
   one authoritative implementation.

Everything recorded in an artifact must help one of those activities.

## Ground rules

- Read `AGENTS.md`, `START.md`, `README.md`, `GOAL.md`, `docs/README.md`, `docs/TREE.md`, and
  `docs/GLOSSARY.md` before a run. `AGENTS.md` governs repository safety, tests, formatting, and
  changelog changes.
- Work on one planned target at a time, but read as widely as needed to understand it.
- Similar-looking code is not automatically duplication. Consolidate only when sites encode the
  same responsibility, should obey the same contract, and should change together.
- Do not optimize for fewer lines. A helper that obscures ownership, couples independent domains,
  or needs mode flags to reconcile different rules makes the system less DRY.
- Prefer the root owner of an invariant over a convenience helper at its call sites.
- Preserve intentional repetition in tests when it keeps behaviors independently legible or honors
  the repository's test-placement rules.
- Record confirmed opportunities and meaningful rejected candidates, not checklist narration.
- Only the maintainer commits.

## Fresh plan

Worker 0 creates `docs/dry/dry-<release>.md` from the matching versions in `pyproject.toml` and
`django_strawberry_framework/__init__.py`. Never overwrite an existing plan.

Build the plan from the current source inventory returned by:

```shell
rg --files django_strawberry_framework -g '*.py'
```

The source-driven planner performs that inventory and refuses to overwrite an existing plan:

```shell
uv run python docs/dry/export_dry_review.py plan \
  --target-release <X.Y.Z> \
  --mode <autonomous|pause-after-each-item>
```

The plan contains, in order:

- every Python file, including `__init__.py` files;
- one folder integration pass after the files in each package folder;
- one project integration pass;
- the final test gate.

Each item links a fresh artifact. Use `dry-file-<path>.md` for files, replacing `/` with `__` and
dropping `.py`; `dry-folder-<path>.md` for folder passes; and `dry-project.md` for the project pass.
The plan records autonomous or pause-after-each-item mode and a baseline for separating cycle work
from pre-existing or concurrent changes.

## Review one file

### 1. Trace the responsibility

Read the complete target and follow its important paths through the system until you can explain:

- what rules, transformations, state, or lifecycle phases it owns;
- who calls, imports, registers, wraps, exposes, or configures it;
- where the same domain concept is represented in production code, tests, examples, docs, and
  framework adapters;
- which changes would require several sites to move in lockstep;
- which neighboring implementations only look similar but intentionally differ.

Search by concepts as well as names. Duplication often appears as different syntax implementing the
same policy: repeated validation, parallel caches, mirrored sync/async paths, copied type-shape
construction, repeated error translation, multiple lifecycle registries, or tests rebuilding the
same domain fixture.

Follow an edge until its contract is understood and further expansion would not change the DRY
judgment. The target remains the review unit; connected files are evidence and may become part of a
root-cause fix.

### 2. Verify candidates

For every apparent duplication, try to disprove that the sites share one responsibility. Compare
inputs, outputs, errors, state transitions, timing, framework hooks, extension points, and expected
reasons to change. Read test bodies and public documentation; names and structural similarity are
not proof.

Use small executable experiments when behavior is uncertain. Scratch tests belong under
`docs/dry/temp-tests/<scope>/` and remain untracked. They may probe private state, monkeypatch a
boundary, or exercise an awkward sequence. Record the command and what it proved.

The optional `audit` mode in `docs/dry/export_dry_review.py` can inventory definitions, importers,
references, exact duplicate bodies, repeated literals, and concept matches. It is an orientation
tool, not a source of findings. Static similarity must still be reconciled with behavior and
ownership. The optional `check` mode can verify that a completed artifact names every target
definition, but cannot judge the quality of its reasoning.

### 3. Design the consolidation

For a real opportunity, identify the narrowest owner that can state the shared rule once. Consider
whether the best change is to:

- reuse or extend an existing owner;
- move policy out of callers and into the object or lifecycle that owns it;
- replace parallel representations with one canonical model;
- parameterize a genuine variation without hiding distinct behavior;
- delete an obsolete path instead of abstracting both paths;
- reshape tests so shared setup is reusable while behavior remains explicit.

Be creative, but concrete. Every finding must state:

- **Repeated responsibility:** the rule or knowledge represented more than once;
- **Sites:** all confirmed implementations and important consumers;
- **Evidence:** why the sites have the same contract and change axis;
- **Owner:** where the single source of truth belongs;
- **Consolidation:** the proposed shape and migration of each site;
- **Proof:** the permanent tests or experiments that demonstrate equivalence and prevent drift;
- **Risks / non-goals:** behavior that must remain distinct or compatible.

If no consolidation is warranted, say so and preserve the strongest rejected candidates with the
evidence that kept them separate. A well-proved zero-edit review is a successful result.

## Integration passes

A folder pass re-reads the folder as one component after its file reviews. Look for duplicated
policy split across modules, unclear state ownership, competing helper layers, inconsistent public
flavors, and lifecycle work repeated at several phases. Do not concatenate file artifacts.

The project pass follows representative behavior across package boundaries and public exports. It
looks for package-wide duplication that no single file owns visibly: parallel subsystem registries,
repeated schema binding, divergent error or naming policy, duplicated settings interpretation,
mirrored sync/async behavior, and the same contract encoded separately in code, tests, and docs.

Integration findings use the same evidence standard and implementation cycle as file findings.

## Artifact

Keep the artifact concise. Expand only where the target warrants it.

```text
# DRY review: `path/to/target.py`

Status: investigating | implementation-ready | fix-implemented | revision-needed | verified

## System trace

What the target owns and the connected behavior examined.

## Verification

Searches, scratch experiments, tests, and rejected candidates that shaped the judgment.

## Opportunities

Each finding: Repeated responsibility / Sites / Evidence / Owner / Consolidation / Proof /
Risks and non-goals.

Write `None — <evidence-backed reason>` when no change is warranted.

## Judgment

A short overall conclusion.
```

Worker 2 appends `## Implementation (Worker 2)`. Worker 3 appends
`## Independent verification (Worker 3)`. Later passes append `## Iterations`; no worker erases the
reasoning that preceded it. Avoid inventories, copied tool output, pseudo-code ceremonies, and empty
placeholder sections.

## Cycle

Each plan item uses fresh workers so the author of a change never approves it:

1. Worker 1 performs the system-wide review and writes the artifact. It sets
   `implementation-ready` when a tracked change is needed, or `fix-implemented` for a proved
   zero-edit result.
2. Worker 2 reproduces the findings, implements every accepted consolidation at its true owner,
   adds permanent tests, and sets `fix-implemented`.
3. Worker 3 independently re-traces the connected behavior, challenges equivalence and boundaries,
   and sets `verified` or `revision-needed`.
4. A revision returns to Worker 2; an incomplete review returns to Worker 1. Worker 3 marks the plan
   item complete only after verification.

Worker 0 coordinates and preserves the baseline; it does not review, implement, or approve. The
artifact and item-scoped diff are the shared record. Cross-file changes are expected when the target
reveals a system-owned rule. Unrelated cleanup stays out of scope.

After an edit, Worker 2 runs `uv run ruff format .` and `uv run ruff check --fix .` as required by
`AGENTS.md`. Focused tests may be used to verify a consolidation; permanent tests belong at the
strongest reachable tier required by `AGENTS.md`. Changelog edits require explicit maintainer
authorization.

## Final gate and closeout

After all file, folder, and project items are verified, Worker 1 runs `uv run pytest`. The gate
passes only when the suite passes and configured package coverage remains 100%. Record failures,
coverage, skips, and xfails, and route each failure back to its owning item.

Worker 0 reports the consolidations, rejected candidates, remaining maintainer decisions, test
result, and concurrent work left untouched. Remove only generated scratch under
`docs/dry/temp-tests/` and `docs/dry/worker-memory/`; never recursively clear `docs/dry/`.
