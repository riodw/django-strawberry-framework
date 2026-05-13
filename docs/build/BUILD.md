# Package build workflow

This document defines the reusable process for **building a feature from a spec doc** under `docs/spec-<topic>.md`. It does not track a specific build run. A build run is tracked in a per-spec plan file under `docs/build/`.

The build is driven by a given spec — `docs/spec-<topic>.md` is the input contract delivered to Worker 0, not something Worker 0 invents. Worker 0 turns the spec's slice checklist into a build plan. Worker 1 is the only worker authorized to mutate the spec when implementation reveals pitfalls or conflicts that need to be reconciled.

!!IMPORTANT!!
Begin by reading README.md and docs/README.md and docs/TREE.md and docs/FEATURES.md and GOAL.md and the active spec file at docs/spec-<topic>.md
Begin by reading README.md and docs/README.md and docs/TREE.md and docs/FEATURES.md and GOAL.md and the active spec file at docs/spec-<topic>.md

!!IMPORTANT — DRY FIRST!!
Every plan, every implementation, every review pass must answer one question before anything else: **is this the maximally DRY shape that stays readable?** Duplicated logic, parallel data flows, near-copies between modules, and repeated string/key/tuple literals are all build-time defects. Worker 1 plans for DRY before code is written; Worker 3 enforces DRY before code is accepted; Worker 1 re-checks DRY across slices at the integration pass.

The standing worker instructions live beside this overview:

- [Worker 0: project manager](worker-0.md)
- [Worker 1: architect, planner, spec custodian, final QA](worker-1.md)
- [Worker 2: builder / implementer](worker-2.md)
- [Worker 3: code reviewer and DRY enforcer](worker-3.md)

Permanent workflow files under `docs/build/` are tracked: `BUILD.md`, `worker-*.md`, `build-*.md`, and every `bld-*.md` build artifact. They are committed to git and kept as the permanent record of the build cycle. The only intentionally untracked paths are generated scratch directories: `docs/build/shadow/`, `docs/build/worker-memory/`, and `docs/build/temp-tests/`.

`AGENTS.md` and `START.md` still apply during build runs. This workflow adds the per-worker artifact discipline on top; it does not override standing validation, formatting, commit, or test-placement rules.

Only the maintainer commits. Workers never commit, even if asked. Workers may stage edits and produce artifacts; pushing those edits to git is a maintainer-exclusive action.

## Required reading per worker

Every worker reads the standing project docs and its own role file before acting. The matrix below is the single source of truth; worker role sections and the standalone `worker-*.md` files reference it instead of re-listing.

| Document | W0 | W1 | W2 | W3 |
|---|---|---|---|---|
| `AGENTS.md` | yes | yes | yes | yes |
| `START.md` | yes | yes | yes | yes |
| `docs/build/BUILD.md` | yes | yes | yes | yes |
| `docs/build/worker-0.md` | yes | — | — | — |
| `docs/build/worker-1.md` | — | yes | — | — |
| `docs/build/worker-2.md` | — | — | yes | — |
| `docs/build/worker-3.md` | — | — | — | yes |
| `GOAL.md` | yes | yes | — | — |
| `docs/FEATURES.md` | yes | yes | — | — |
| `CHANGELOG.md` | — | yes | — | — |
| `docs/TREE.md` | — | — | yes | — |
| `docs/README.md` | — | — | — | yes |
| `examples/fakeshop/test_query/README.md` | — | — | — | yes |
| active `docs/spec-<topic>.md` | yes | yes | yes | yes |
| active `docs/build/build-<topic>-<0_0_X>.md` | yes (owns) | yes | yes | yes |
| current `docs/build/bld-*.md` artifact | yes (read-only) | yes (owns plan + final sections) | yes (writes build reports) | yes (writes review section) |
| own `docs/build/worker-memory/worker-N.md` | yes | yes | yes | yes |
| relevant source / tests | — | yes (read-only) | yes (writes) | yes (read-only) |
| Worker 2's diff | — | — | — | yes |

Workers never read another worker's memory file during the cycle; see "Subagent dispatch and worker memory" below. Adding a new standing doc (e.g., a future `docs/ARCHITECTURE.md`) is a one-line change to this table.

## Versioned build plan

Worker 0 is **handed** the active spec file (e.g. `docs/spec-<topic>.md`) at the start of the cycle. Worker 0 does not write the spec; Worker 0 derives the build plan from it.

1. Read the active spec file at `docs/spec-<topic>.md`.
2. Identify the spec's topic slug and target release version from the spec itself; convert the target release dots to underscores (e.g. `0.0.5` becomes `0_0_5`). Version-bump correctness is the maintainer's responsibility — Worker 0 does not validate `pyproject.toml`, `__init__.py`, or the shipped-status of the target version.
3. Create `docs/build/build-<topic>-<0_0_X>.md`. For an `example_topic` spec targeting `0.0.X`, this is `docs/build/build-example_topic-0_0_X.md`.
4. The plan file is the canonical checklist for the whole build and is committed alongside the implementation changes. It is kept in git as the permanent record of the cycle.

If the spec is missing, malformed, or its slice checklist cannot be parsed, stop and record that mismatch in the plan before any slice work starts.

## Build scope

The build covers every slice listed in the spec's "Slice checklist" section, in declared order. The plan file mirrors that checklist, one cycle per slice, plus a final cross-slice integration pass and a final test-run gate.

Rules:

- Build only one slice at a time.
- Do not start the next slice until the current slice's plan/build/review/verification/spec-reconciliation cycle is complete.
- After all in-spec slices are built, perform one cross-slice **integration pass** for cross-cutting DRY opportunities, redundant helpers, repeated literals, and inconsistent shapes between slices. The integration pass is Worker 1's job; it may trigger a second-loop refactor cycle through Worker 2 and Worker 3 if DRY opportunities are found.
- The build closes with one final test-run gate (existing tests must still pass) handled by Worker 1.

## Required plan structure

The generated `docs/build/build-<topic>-<0_0_X>.md` file must begin with:

- spec source path
- target release version
- date created
- a short copy of the one-slice-at-a-time rule
- a short copy of the DRY-first rule
- a list of every build artifact that will be created

Then it must include a slice-level checklist for the build. Every slice and every integration/final pass must have:

- a checkbox (only Worker 0 marks these `- [x]`, and only after Worker 1 final verification accepts the slice)
- the spec slice it implements
- the exact build artifact file to create

### Template shape:

The block below is a **fictional placeholder**. Substitute the active spec's topic, target version, and actual slice titles when generating the real plan; do not treat any of these names as referencing a current or past build.

```text
# Package build plan: example_topic / 0.0.X

Spec source: `docs/spec-example_topic.md`
Target release: `0.0.X`
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

## Artifact list

- `docs/build/bld-slice-1-<short_slug>.md`
- `docs/build/bld-slice-2-<short_slug>.md`
- `docs/build/bld-slice-3-<short_slug>.md`
- `docs/build/bld-integration.md`
- `docs/build/bld-final.md`

## Checklist

- [ ] Slice 1: <slice title from spec> -> `docs/build/bld-slice-1-<short_slug>.md`
- [ ] Slice 2: <slice title from spec> -> `docs/build/bld-slice-2-<short_slug>.md`
- [ ] Slice 3: <slice title from spec> -> `docs/build/bld-slice-3-<short_slug>.md`
- [ ] Cross-slice integration pass -> `docs/build/bld-integration.md`
- [ ] Final test-run gate -> `docs/build/bld-final.md`
```

Use the actual slice list from the spec when creating the plan. Do not invent slices. Keep the checklist in the spec's declared slice order.

## Build artifact naming

Per-slice, integration, and final build artifacts are tracked Markdown files under `docs/build/`. They are committed alongside the source changes they describe and form a permanent record of the build cycle.

Naming rules:

- Start with `docs/build/bld-`.
- For a spec slice: `bld-slice-<N>-<short_slug>.md` where `N` is the 1-indexed slice number from the spec and `<short_slug>` is a lowercase underscore-separated summary of the slice title.
- For the cross-slice integration pass: `docs/build/bld-integration.md`.
- For the final test-run gate: `docs/build/bld-final.md`.
- End with `.md`.

Examples (fictional placeholders, not a real spec):

- Spec slice 1 ("<slice title>") -> `docs/build/bld-slice-1-<short_slug>.md`
- Spec slice 4 ("<slice title>") -> `docs/build/bld-slice-4-<short_slug>.md`
- Integration pass -> `docs/build/bld-integration.md`
- Final pass -> `docs/build/bld-final.md`

The generated `docs/build/build-<topic>-<0_0_X>.md` file must list every artifact before build work starts.

## Build artifact template

Every `docs/build/bld-<slice>.md` file accumulates the full back-and-forth for that slice. The artifact is the contract that flows between workers; everything inter-worker happens through this file plus the working-tree diff.

### Status field ownership

The artifact's `Status:` line is set by exactly one worker per transition:

- `planned` — Worker 1 sets this when the artifact is first created (the planning pass writes the `Plan (Worker 1)` section and `Status: planned`). The status field never starts empty; new artifacts always have `Status: planned`.
- `built` — Worker 2 sets this at the end of every build pass (including re-passes after a Worker 3 rejection). The status returns to `built` whenever Worker 2 finishes implementing, signaling Worker 0 to spawn Worker 3 next.
- `revision-needed` — set by Worker 3 (after the review pass surfaces unresolved High/Medium findings) or by Worker 1 (when the final-verification pass rejects). Either case triggers Worker 0 to spawn Worker 2 again.
- `review-accepted` — set by Worker 3 when accepting the diff at the review-pass exit; signals Worker 0 to spawn Worker 1 for final verification.
- `final-accepted` — set by Worker 1 at the end of final verification; signals Worker 0 to mark the checklist box and advance.

Worker 0 never writes to `Status:`. Worker 0 reads it to drive dispatch.

````text
# Build: Slice <N> — <slice title>

Spec reference: `docs/spec-<topic>.md` (lines <start>-<end>)
Status: planned | built | revision-needed | review-accepted | final-accepted

## Plan (Worker 1)

### DRY analysis

- What patterns from the existing codebase can be reused? Cite file:line.
- What new shared helper or module is justified? What is its single responsibility?
- What duplication does this slice risk introducing? How does the plan avoid it?

### Implementation steps

1. Step one. Cite the file:line touched.
2. Step two.
3. ...

### Test additions / updates

- Which tests prove the slice? Pin the path and assertion shape.
- Are temp/scratch tests appropriate for development? Note them here for Worker 3.

### Open questions for Worker 2

List any ambiguities the plan leaves to Worker 2's discretion.

---

## Build report (Worker 2)

### Files touched

- `path/to/file.py` — what changed and why
- ...

### Tests added or updated

- `tests/path/test_x.py::test_name` — what it pins

### Validation run

- `uv run ruff format .` — pass/fail
- `uv run ruff check --fix .` — pass/fail
- Focused test commands run, if any

### Notes for Worker 3

Anything Worker 3 should know before reviewing (shadow file used, unusual control flow, etc.).

### Notes for Worker 1 (spec reconciliation)

If the implementation surfaced a spec gap, conflict, or unstated assumption, record it here. Worker 1 reads this section during final verification and decides whether to edit the spec.

---

## Review (Worker 3)

### High:

#### Issue name

Issue summary, why it matters, and the recommended change.

```path/to/file.py:NN:MM
Relevant excerpt or pseudo-diff context.
```

### Medium:

### Low:

### DRY findings

- Duplication observed (cite file:line in both sites)
- Repeated literal / key / tuple
- Near-copy of existing helper that should be consolidated

### What looks solid

- Thing one.
- Thing two.

### Temp test verification

- Temp test files used during review (cite paths).
- Disposition: kept and promoted to a permanent test, deleted, or noted for follow-up.

### Notes for Worker 1 (spec reconciliation)

Flag anything Worker 1 should weigh during final verification (spec ambiguity, possible spec edit, follow-up slice candidate).

### Review outcome

`review-accepted` (every High/Medium/Low finding addressed or intentionally rejected with a recorded reason) or `revision-needed`. Setting this also updates the artifact's top-level `Status:` line.

---

## Iteration log

Each Worker 2 re-pass appends a "Build report (Worker 2, pass <N>)" section here. Each Worker 3 re-review appends a "Review (Worker 3, pass <N>)" section here. Do not edit prior entries; append.

---

## Final verification (Worker 1)

- DRY check across this slice and prior accepted slices: any new duplication?
- Existing tests still pass: `uv run pytest <focused scope>`.
- Spec reconciliation: does the spec need a Worker 1 edit to reflect what landed?
- Final status: `final-accepted` or `revision-needed`.

### Summary

A short summary of what this slice shipped.

### Spec changes made (Worker 1 only)

If the spec was edited as part of this slice, cite the spec lines and a one-line reason per change.
````

If a severity has no issues, keep the heading and write `None.` under it. Do not include speculative defects.

## Severity definitions

High:

- confirmed correctness bugs in the implementation
- spec contract violation (the build does not deliver what the spec says it will)
- API breakage against shipped `0.0.x` surface
- DRY violation that will entrench duplicated logic across the package
- Django ORM behavior that can return wrong data
- security / data-isolation regression
- crashes a normal consumer code path

Medium:

- likely performance regressions
- N+1 risk or unnecessary database work
- redundant implementation that should be consolidated
- unclear ownership between modules introduced by the new code
- brittle edge-case behavior
- missing tests for important branches
- repeated literal / key / tuple that should be a named constant

Low:

- small maintainability issues
- naming clarity
- minor typing/API polish
- localized simplification
- comments or docstrings that are stale or wrong but not load-bearing

## What each step checks

### DRY-first planning (Worker 1)

The first pass is a DRY check, not a code-writing pass.

Worker 1 must answer, before writing the plan:

- What existing module already does some of this?
- What helpers already exist that the implementation can call?
- What single new module/function justifies its own existence vs. extending an existing one?
- What patterns are likely to recur in **later** slices of the same spec? Hoist them now if cheap, defer them with a TODO anchor (per `AGENTS.md`) if not.
- What would a maintainer searching for similar logic find in the package today? Place new logic where they will look.

### Implementation (Worker 2)

Worker 2 builds against the plan. Worker 2:

- follows the plan steps in order
- adds tests in the same change as the code
- does not add scope beyond the artifact unless the plan explicitly required it
- runs `uv run ruff format .` and `uv run ruff check --fix .` after every edit (per `AGENTS.md` / `START.md`)
- does NOT run `pytest` after every edit (per `START.md`)

### Code review (Worker 3)

Worker 3 reviews Worker 2's diff and the resulting working tree. Worker 3 focuses on:

- functional correctness against the plan and the spec
- DRY violations introduced by the build (this is the primary review lens)
- module placement and responsibility boundaries
- Django ORM correctness, lazy evaluation, relation caches, optimizer cooperation
- async/sync behavior
- cache keys, mutability, request-scope state
- typing quality
- whether tests exercise the right branches
- Two Scoops of Django structure: small focused modules, explicit queryset boundaries, minimal magic, reusable utilities only when genuinely shared

Worker 3 may create **temp test files** under `docs/build/temp-tests/<slice-name>/` to verify behavior during review. Temp tests are gitignored and are NOT part of the permanent test suite. If a temp test pins a bug or important behavior, Worker 3 records it as a Medium finding so Worker 2 can promote it to the permanent test suite under the correct `AGENTS.md` test-placement tree.

### Static inspection helper: `scripts/review_inspect.py`

The build cycle uses a static inspection helper at `scripts/review_inspect.py`. It parses the target file as text and AST only — it never imports or executes the module — so it is safe to run on files that touch Django settings, the registry, or Strawberry type creation at import time. The script name is historical; treat it as the build cycle's static inspection helper.

#### When to run the helper during build

Worker 1 **must run** the helper during planning when:

- The plan adds logic to any existing `.py` file with at least 150 source lines.
- The plan adds logic to any file under `django_strawberry_framework/optimizer/` or `django_strawberry_framework/types/`.

Reading the helper output is how Worker 1 confirms the new logic lands where similar logic already lives, and how Worker 1 spots duplication risk before writing the plan.

Worker 3 **must run** the helper during review when:

- The slice adds a new `.py` file of any size, **unless** it is a pure-class-definition module (only `class` declarations with docstrings, no logic). For low-surface files like that, Worker 3 skips the helper and records the skip and reason in the artifact.
- The slice touches an existing `.py` file under `optimizer/` or `types/`.
- The slice adds 30 or more lines of new logic to any file under `django_strawberry_framework/`.
- The slice adds 50 or more lines of new logic to any file outside `django_strawberry_framework/` (e.g. tests or example projects).

Worker 3 uses the **Repeated string literals** and **Imports** sections to catch duplication and boundary leaks. The **Django/ORM markers** section is the audit checklist for ORM-heavy slices.

Worker 1 and Worker 3 may also skip the helper for files where the artifact will be a "no review-worthy logic" disposition (pure re-exports, single-line constants, etc.). When the helper is skipped, the artifact must say so explicitly with a short reason.

Worker 2 **may re-run** the helper with `--strip-docstrings` when the logic is hard to read with docstrings inline. If Worker 2 used the shadow file during implementation, that must be noted in the artifact's "Notes for Worker 3" section.

#### How to run

From the repository root:

```shell
python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/build/shadow
```

Every build-cycle helper invocation must pass `--output-dir docs/build/shadow` so generated artifacts land inside the build sandbox.

Useful flags:

- `--strip-docstrings` — also strip module/class/function docstrings from the shadow file. Use when docstrings obscure the control flow being read.
- `--outline-only` — keep only Imports, Symbols, Control-flow hotspots, and Django/ORM markers in the overview. Use for fast-scan passes on a file already inspected.
- `--stdout` — print the overview to stdout in addition to writing it. Useful for quick triage from the terminal.
- `--marker NAME` — add a custom marker to the Django/ORM marker table. Repeatable. Use when the slice traffics in a name (e.g. `Connection`, `relay`) the default marker list does not cover.
- `--long-function-lines N` and `--long-function-branches N` — raise or lower the control-flow hotspot thresholds (defaults: 40 lines, 8 branches).
- `--first-party-prefix PREFIX` — add a first-party import prefix; defaults to `django_strawberry_framework`. Repeatable.
- `--literal-min-length N` — minimum length for repeated string literals to surface (default 8).

#### Overview sections — what each one tells you

- **Imports** — every import categorized as local / first-party / django / strawberry / standard-or-third-party. Cross-folder imports are usually structural changes worth flagging.
- **Symbols** — table of contents for the file's classes and functions, with line ranges and parent class. Use to jump to the symbol under review.
- **Control-flow hotspots** — functions exceeding the line or branch thresholds. Apply Medium-tier complexity attention to every hotspot.
- **Django / ORM markers** — every line that touches `QuerySet`, `select_related`, `prefetch_related`, `Prefetch`, `only`, `_meta`, `get_queryset`, `_prefetched_objects_cache`, `fields_cache`, `DjangoType`, `OptimizationPlan`, `OptimizerHint`, `dst_optimizer_plan`, or `_optimizer_field_map`. Walk every entry; each needs either a one-line justification or a finding.
- **Calls of interest** — reflective-access and container-coercion calls (`getattr`, `hasattr`, `isinstance`, `setattr`, `dict`, `frozenset`, `iter`, `len`, `list`, `set`, `tuple`). These are the typical sites of shape-contract bugs and missing defensive defaults.
- **Comments and docstrings** — docstring inventory, TODO comments, and the full comment inventory. Use to verify docstrings describe the final approved behavior and that TODOs are still actionable.
- **Repeated string literals** — DRY signal. Essential at the cross-slice integration pass for catching cross-file duplication.

#### Output files

Two files land under `docs/build/shadow/<stable-stem>`:

- `<stem>.stripped.py` — target source with `#` comments removed.
- `<stem>.overview.md` — static AST overview.

`docs/build/shadow/` is gitignored.

#### Shadow-file line numbers are NOT canonical

The shadow file strips `#` comments (and optionally docstrings), so its line numbers do not match the original source. Build artifacts, code-review feedback, and source edits must cite **original source-file line numbers**, never shadow-file line numbers. The shadow file is read-only; never edit or commit it.

## Subagent dispatch and worker memory

Workers 1, 2, and 3 each run as **separate subagent invocations per cycle item**. Worker 0 stays in the main thread as the project manager. The split exists so the worker that reviews a build has no in-context memory of the worker that wrote it — a worker cannot review its own implementation reasoning, just the artifact-and-diff contract handed to it.

### Why subagent dispatch

A single agent role-playing every worker can convince itself a build is sufficient because it remembers _why_ it built it that way. Subagent isolation removes that path: Worker 3 starts fresh per cycle, sees only the artifact and the diff, and accepts or rejects on what is actually written down.

### Worker memory

Each worker keeps a private scratch memory file that **persists across slices within a single build** but is invisible to every other worker:

- `docs/build/worker-memory/worker-0.md` — Worker 0's coordination notebook (lighter than the other workers — mostly progress notes)
- `docs/build/worker-memory/worker-1.md` — Worker 1's planning, spec-reconciliation, and final-QA notebook
- `docs/build/worker-memory/worker-2.md` — Worker 2's implementation notebook
- `docs/build/worker-memory/worker-3.md` — Worker 3's review notebook

These files are gitignored. Worker 0 creates the directory at plan time and deletes it at closeout. The tracked permanent record is the `bld-*.md` artifacts and the spec edits, never these notes.

**What a worker writes to its memory.** At the end of each cycle, the worker appends a short entry — typically 3-5 lines — capturing what to carry into the next cycle:

- Worker 0: which slice closed, any maintainer follow-ups, friction noticed in dispatch.
- Worker 1: recurring patterns being planned for, DRY observations across slices, spec edits made and why.
- Worker 2: implementation patterns that worked, reusable scaffolding, maintainer pushback to remember.
- Worker 3: kinds of code that passed muster, kinds that bit later, DRY-violation patterns to keep watching for.

Entries are append-only. If a worker's memory exceeds ~50 lines, the worker must consolidate (merge similar entries into a single pattern observation) before adding more — never delete without consolidating first.

**Read isolation rules.** A worker may read **only** its own memory file:

- Worker 0 may not read worker-1/2/3 memory during the cycle (it may read all four at closeout for the retrospective).
- Worker 1 may not read worker-0/2/3 memory.
- Worker 2 may not read worker-0/1/3 memory. (Worker 2 reads the _artifact_ Worker 1 produced — that is the contract — but never Worker 1's running notes.)
- Worker 3 may not read worker-0/1/2 memory. (Worker 3 reads the _artifact_ and the _diff_ — those are the contract — but never the other workers' running notes.)

**Write isolation rules.** A worker writes only to its own memory file. The main thread (Worker 0) never edits another worker's memory.

**Spawn-per-cycle dispatch.** Worker 0 spawns the workers in this order per slice:

1. Worker 1 subagent (planning pass) — produces the plan section of the artifact, appends to `worker-1.md`, returns.
2. Worker 2 subagent (build pass) — implements the slice, appends a build report to the artifact, appends to `worker-2.md`, returns.
3. Worker 3 subagent (review pass) — reviews, appends review section to the artifact, may create temp tests under `docs/build/temp-tests/<slice>/`, appends to `worker-3.md`, returns.
4. If Worker 3 found issues: Worker 0 re-spawns Worker 2 (apply-changes pass) — implements the fixes, appends a new build report to the artifact, returns. Then Worker 0 re-spawns Worker 3 (re-review pass). Repeat until Worker 3 has no unresolved High/Medium/Low findings or all remaining findings are intentionally rejected with a recorded reason.
5. Worker 1 subagent (final-verification pass) — runs the slice-local checks, reconciles the spec if needed, appends final verification section to the artifact, appends to `worker-1.md`, returns.
6. Worker 0 marks the slice's checkbox `- [x]` in `docs/build/build-<topic>-<0_0_X>.md` only if Worker 1 set the artifact status to `final-accepted`, then appends progress to `worker-0.md`.

Each subagent's prompt must include: standing project docs (`AGENTS.md`, `START.md`, `BUILD.md`, the worker's own role file), the active build plan, the active spec, the cycle's artifact, and the worker's own memory file contents. The subagent's prompt must explicitly forbid reading the other workers' memory files.

**No cross-worker chatter.** Subagents do not message each other directly. All inter-worker information flows through the artifact (`bld-<slice>.md`) and the diff.

**Lifecycle.**

- Worker 0 creates `docs/build/worker-memory/` and seeds four empty files (one per worker) at plan-creation time.
- Workers read their own file at the start of every spawn and append at the end.
- Worker 0 deletes `docs/build/worker-memory/` at cycle closeout, after the retrospective is written.

## Worker process

### Worker 0: project manager

Worker 0 is the lightest-touch role. Worker 0 does not plan, does not write code, does not review code, does not edit the spec. Worker 0:

- reads per the **Required reading per worker** table
- creates `docs/build/build-<topic>-<0_0_X>.md` from the spec's slice checklist
- creates `docs/build/worker-memory/` and seeds the four memory files
- dispatches the per-slice subagent sequence described above
- routes Worker 3's review feedback to Worker 2 by re-spawning Worker 2 with the updated artifact
- marks `- [x]` on the build plan after Worker 1's final verification sets the artifact to `final-accepted`
- runs the closeout pass after every slice is checked, including the integration pass and the final test-run gate
- never edits the spec
- never marks an item complete on its own assessment
- never commits

If something stalls — Worker 3 keeps rejecting, Worker 1 keeps finding cross-slice DRY issues, or the spec needs maintainer-level adjudication — Worker 0 surfaces the blocker to the maintainer and waits.

### Worker 1: architect, planner, spec custodian, final QA

Worker 1 is the central hub of every cycle. Worker 1:

- reads per the **Required reading per worker** table
- plans each slice **DRY-first**: every plan entry must cite which existing helpers/modules it reuses or extends, and must justify any new helper as load-bearing-and-shared
- produces the "Plan (Worker 1)" section of each `bld-slice-N-<...>.md` artifact and sets the artifact's initial `Status: planned`
- is the **only** worker authorized to edit the active spec file (`docs/spec-<topic>.md`); spec edits are recorded in the artifact's "Spec changes made" section
- runs slice-level final verification after Worker 3 reaches `review-accepted` and sets the artifact to `final-accepted` or `revision-needed`
- runs the integration pass after every slice is built — looks for cross-slice DRY opportunities, repeated literals, and inconsistent shapes between slices; may ask Worker 0 to dispatch a second-loop refactor cycle through Worker 2 / Worker 3
- runs the final test-run gate at the end of the build (existing tests still pass; **do NOT check coverage line-by-line — only that existing tests still pass**)
- never commits

Worker 1 may iterate the whole pipeline (re-plan → re-build → re-review) when integration-pass DRY findings warrant it.

### Worker 2: builder / implementer

Worker 2 reads the plan section of the active artifact and the target source, then implements. Worker 2:

- reads per the **Required reading per worker** table
- implements the plan's steps in order
- adds or updates tests in the same change
- runs `uv run ruff format .` and `uv run ruff check --fix .` (per `START.md`); does NOT run `pytest` (per `START.md`)
- appends a "Build report (Worker 2)" section to the slice artifact and sets the artifact `Status:` line to `built` at the end of every pass
- on a re-pass after Worker 3 review, appends a "Build report (Worker 2, pass N)" section — never edits prior reports
- never edits the spec
- never marks the checkbox
- never commits

When Worker 3 hands back review findings, Worker 2 applies the changes and reports back via a new build-report entry.

### Worker 3: code reviewer and DRY enforcer

Worker 3 reviews Worker 2's diff against the slice artifact and the spec. Worker 3:

- reads per the **Required reading per worker** table
- runs `scripts/review_inspect.py` per the "When to run the helper during build" rules above
- focuses on DRY violations as the primary review lens, then correctness, then performance, then bugs
- may create temp test files under `docs/build/temp-tests/<slice>/` to verify behavior; temp tests are gitignored and the disposition is recorded in the artifact
- appends a "Review (Worker 3)" section to the slice artifact (or "Review (Worker 3, pass N)" on re-review) and sets the artifact `Status:` line to `review-accepted` or `revision-needed`
- never edits source files (Worker 2 applies changes after Worker 3's feedback)
- never edits the spec
- never marks the checkbox
- never commits

If review tests catch a bug worth preserving, Worker 3 flags it as a Medium issue with a recommendation to promote the test to the permanent suite under the correct `AGENTS.md` test-placement tree.

### Maintainer checkpoint

After Worker 0 marks a slice done:

1. The maintainer is notified the slice is `final-accepted`.
2. Worker 1 is informed that the slice closed and re-reads the full diff for the slice plus the artifact to confirm nothing slipped through (final-verification was per-pass; this re-check is the cycle-closing audit).
3. If Worker 1's re-check finds anything missed, Worker 1 sets the artifact status back to `revision-needed` and Worker 0 dispatches a Worker 2 / Worker 3 loop again.
4. If Worker 1's re-check is clean, the maintainer may request any final adjustments. The **maintainer** then commits the source changes together with the corresponding `bld-*.md` artifact, the spec edits (if any), and the updated build-plan checkbox.
5. Worker 0 moves on to the next unchecked slice.

Only the maintainer commits. Workers never commit, even if asked.

### Isolation is non-waivable

Worker 2 and Worker 3 must always run as separate subagent invocations. The build cycle does not allow combining them — even for slices with no High-severity findings, even for trivial slices. Combining them would let the agent that wrote the code also approve it, which defeats the dispatch's only guarantee. If the cycle feels ceremonious for a small slice, that is the intended cost.

## Cross-slice integration pass

After every slice in the spec is checked complete, Worker 1 runs the integration pass and produces `docs/build/bld-integration.md`.

Before writing `bld-integration.md`, Worker 1 must:

1. Read every prior `docs/build/bld-slice-*.md` artifact for the build, in slice order. No "as needed" — every artifact is required context for the cross-slice DRY scan.
2. Confirm the static inspection helper has been run on every Python file the build touched (overviews exist under `docs/build/shadow/`). If any are missing, run the helper before continuing.
3. Compare the **Repeated string literals** sections across every shadow overview. A literal that appears in two or more files is a cross-slice DRY candidate; record it in the integration artifact.
4. Compare the **Imports** sections across every shadow overview to confirm one-way dependency direction inside the new code and to spot a sibling that has started importing from outside the documented boundary.
5. Walk every accepted slice artifact's `What looks solid` and `DRY findings` sections to catch any deferred follow-up that should land in this pass.

The integration pass itself should check:

- duplicated helpers across slices
- inconsistent naming or error handling between slices
- repeated ORM/queryset patterns that should be centralized
- misplaced responsibilities between modules touched by different slices
- missing or too-broad exports introduced by the build
- repeated string literals / dictionary keys / tuple shapes across slices
- whether comments now tell one coherent story across the new code

If DRY opportunities are found, Worker 1 records them in `bld-integration.md` and asks Worker 0 to dispatch Worker 2 for a consolidation pass and Worker 3 for a review pass. The results are recorded as additional sections in `bld-integration.md`. Repeat until the integration pass is clean.

## Final test-run gate

After the integration pass is clean, Worker 1 runs the final test-run gate and produces `docs/build/bld-final.md`.

The gate is intentionally narrow:

- Run `uv run pytest` (full sweep across all three test trees per `AGENTS.md`).
- **Do NOT inspect or assert line coverage at this stage.** The only requirement is that the existing test suite passes. Coverage gating belongs to CI (`pyproject.toml` `[tool.coverage.report] fail_under = 100`) and to the maintainer, not to this gate.
- If failures appear, record them in `bld-final.md`, then re-loop through whichever slice owns the failing behavior (Worker 1 plans the fix, Worker 0 dispatches Worker 2 to implement, Worker 0 dispatches Worker 3 to review, Worker 1 re-runs the gate).
- If the build added user-visible behavior, `CHANGELOG.md` is edited only when the active spec explicitly includes that work or the maintainer explicitly authorizes it. Worker 1 checks the changelog contract; Worker 2 applies the edit when the plan says so.

The gate closes the build cycle. Worker 0 then marks the final checkbox `- [x]`.

## Spec reconciliation

The spec is **input** to the build, not output. But implementation routinely reveals:

- gaps in the spec (a Decision that turns out to depend on something unstated)
- conflicts between Decisions (e.g., Decision 5's ordering vs. Decision 3's identity check)
- realities of the codebase that the spec didn't anticipate

When this happens, **only Worker 1** may mutate `docs/spec-<topic>.md`. Worker 1 records the edit in the active slice artifact under "Spec changes made (Worker 1 only)" with:

- cited spec line(s)
- one-line reason per change
- the slice that triggered the change

Workers 0, 2, and 3 must surface spec issues by writing them into the slice artifact under "Notes for Worker 1 (spec reconciliation)"; they may not edit the spec themselves.

If a spec edit fundamentally changes the slice contract that Worker 2 already implemented against, Worker 1 must re-spawn Worker 2 for an adjustment pass before final verification.

## Cleanup and closeout

When all checklist items are marked `- [x]` (every slice plus integration plus final):

1. Worker 0 scans all build-cycle commit diffs (using the maintainer-provided commit range).
2. Worker 0 reads all four worker-memory files (one-time read at closeout) to surface patterns the workers themselves noticed across the build.
3. Worker 0 identifies recurring DRY patterns, repeated bug classes, and workflow stumbling blocks.
4. Worker 0 provides a brief retrospective to the maintainer.
5. After maintainer approval, Worker 0 updates `docs/build/BUILD.md` or the worker role files with general retrospective notes — describing recurring patterns and workflow improvements **without naming specific already-shipped fixes**.
6. Worker 0 deletes `docs/build/worker-memory/` and `docs/build/temp-tests/`. The tracked permanent record is the `bld-*.md` artifacts, the build plan, and the spec edits — the scratch memory and temp tests have served their purpose.
7. The maintainer commits the updated `docs/build/` workflow docs along with the now-completed `docs/build/build-<topic>-<0_0_X>.md` plan and any remaining `bld-*.md` artifacts to finish the build cycle. The plan and artifacts stay in git as the permanent record of the build.
