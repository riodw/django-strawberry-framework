# Package build workflow

This document defines the reusable process for **building a feature from a spec doc** under `docs/spec-<NNN>-<topic>-<0_0_X>.md`. It does not track a specific build run; a build run is tracked in a per-spec plan file under `docs/builder/`.

The build is driven by a given spec — `docs/spec-<NNN>-<topic>-<0_0_X>.md` is the input contract delivered to Worker 0, not something Worker 0 invents. Worker 0 turns the spec's slice checklist into a build plan. Worker 1 is the only worker authorized to mutate the spec when implementation reveals pitfalls or conflicts that need reconciliation.

## Spec and build-plan filename pattern

Spec files live at `docs/spec-<NNN>-<topic>-<0_0_X>.md`; build plans live at `docs/builder/build-<NNN>-<topic>-<0_0_X>.md` (same segments, different directory and prefix). Segments:

- `spec-` / `build-` — literal prefix.
- `<NNN>` — 3-digit zero-padded KANBAN card number (e.g. `013` from `DONE-013-0.0.6`, `011` from `DONE-011-0.0.5`). The NNN is the build's anchor identity: spec and build plan share it, every artifact references it, KANBAN cards link to it, and files sort alongside their peers in `ls`. DONE cards use the bare `DONE-<NNN>-<X.X.X>` form (no milestone prefix); TODO/BLOCKED cards keep the milestone prefix (`TODO-ALPHA-<NNN>`, `TODO-BETA-<NNN>`, `TODO-STABLE-<NNN>`, `BLOCKED-ALPHA-<NNN>`) until they ship.
- `<topic>` — lowercase underscore-separated topic slug (e.g. `deferred_scalars`, `relay_interfaces`).
- `<0_0_X>` — target release version with dots converted to underscores (e.g. `0_0_6`, `0_0_5`).
- `.md` — extension.

Example: spec `docs/spec-013-deferred_scalars-0_0_6.md` pairs with build plan `docs/builder/build-013-deferred_scalars-0_0_6.md`. Earlier specs predating this pattern may live without the NNN/version segments; new specs and their build plans use the pattern.

!!IMPORTANT!!
Begin by reading `README.md`, `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `GOAL.md`, and the active spec file at `docs/spec-<NNN>-<topic>-<0_0_X>.md`.

!!IMPORTANT — DRY FIRST!!
Every plan, every implementation, every review pass must answer one question before anything else: **is this the maximally DRY shape that stays readable?** Duplicated logic, parallel data flows, near-copies between modules, and repeated string/key/tuple literals are all build-time defects. Worker 1 plans for DRY before code is written; Worker 3 enforces DRY before code is accepted; Worker 1 re-checks DRY across slices at the integration pass.

Standing workflow files under `docs/builder/` are tracked: `BUILD.md` and `worker-*.md`. Per-build plans and artifacts (`build-*.md` and `bld-*.md`) are tracked only for the active build cycle and must start from a clean slate; pre-flight cleanup deletes old build artifacts. Untracked scratch paths: `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/`.

`AGENTS.md` and `START.md` still apply during build runs. Only the maintainer commits. Workers never commit, even if asked.

The standing worker instructions live beside this overview:

- [Worker 0: project manager](worker-0.md)
- [Worker 1: architect, planner, spec custodian, final QA](worker-1.md)
- [Worker 2: builder / implementer](worker-2.md)
- [Worker 3: code reviewer and DRY enforcer](worker-3.md)

## Required reading per worker

Every worker reads the standing project docs and its own role file before acting. The matrix below is the single source of truth; worker role files reference it instead of re-listing.

| Document | W0 | W1 | W2 | W3 |
|---|---|---|---|---|
| `AGENTS.md` | yes | yes | yes | yes |
| `START.md` | yes | yes | yes | yes |
| `docs/builder/BUILD.md` | yes | yes | yes | yes |
| `docs/builder/worker-0.md` | yes | — | — | — |
| `docs/builder/worker-1.md` | — | yes | — | — |
| `docs/builder/worker-2.md` | — | — | yes | — |
| `docs/builder/worker-3.md` | — | — | — | yes |
| `GOAL.md` | yes | yes | — | — |
| `docs/GLOSSARY.md` | yes | yes | — | — |
| `CHANGELOG.md` | — | yes | — | — |
| `docs/TREE.md` | — | — | yes | — |
| `docs/README.md` | — | — | — | yes |
| `examples/fakeshop/test_query/README.md` | — | — | — | yes |
| active `docs/spec-<NNN>-<topic>-<0_0_X>.md` | yes | yes | yes | yes |
| active `docs/builder/build-<NNN>-<topic>-<0_0_X>.md` | yes (owns) | yes | yes | yes |
| current `docs/builder/bld-*.md` artifact | yes (read-only) | yes (owns plan + final sections) | yes (writes build reports) | yes (writes review section) |
| own `docs/builder/worker-memory/worker-N.md` | yes | yes | yes | yes |
| relevant source / tests | — | yes (read-only) | yes (writes) | yes (read-only) |
| Worker 2's diff | — | — | — | yes |

Workers never read another worker's memory file during the cycle. Adding a new standing doc is a one-line change to this table.

## Pre-flight checks

Before Worker 0 creates `docs/builder/build-<NNN>-<topic>-<0_0_X>.md`:

1. **Working-tree baseline is explicit.** Run `git status --short`. If unrelated uncommitted changes exist, stop and ask the maintainer to commit, move aside, or include them in the baseline.
2. **`scripts/review_inspect.py` runs.** Smoke invocation: `uv run python scripts/review_inspect.py <pick_a_dst_module>.py --output-dir docs/shadow --stdout`. Escalate if broken — planning and review passes for `types/` or `optimizer/` slices cannot run as specified without it.
3. **Build artifacts are reset.** Delete any old `docs/builder/build-*.md` and `docs/builder/bld-*.md` files left from a prior cycle. Verify the new plan path and every `bld-*.md` path Worker 0 intends to create do not already exist.
4. **`.gitignore` lists the untracked scratch paths.** Confirm `docs/builder/worker-memory/`, `docs/shadow/`, and `docs/builder/temp-tests/` are gitignored.
5. **Scratch directories are cleared.** Delete every file under `docs/builder/worker-memory/`, `docs/shadow/`, and `docs/builder/temp-tests/`.

Record the outcome in the build plan's preamble (`Pre-flight: passed on YYYY-MM-DD; baseline: clean; cleanup: old artifacts removed, memory/shadow/temp-tests cleared` or `Pre-flight: <issue>, resolved by <action>; baseline: <summary>; cleanup: <summary>`). If any check fails and cannot be resolved without maintainer input, escalate before creating the build plan.

## Versioned build plan

Worker 0 is **handed** the active spec file at the start of the cycle. Worker 0 does not write the spec; Worker 0 derives the build plan from it.

1. Read the active spec.
2. Identify the spec's topic slug and target release version; convert dots to underscores (e.g. `0.0.5` becomes `0_0_5`). Version-bump correctness is the maintainer's responsibility.
3. Create `docs/builder/build-<NNN>-<topic>-<0_0_X>.md`.
4. The plan file is the canonical checklist for the whole build and is committed alongside the implementation changes.

If the spec is missing, malformed, or its slice checklist cannot be parsed, stop and record that mismatch in the plan before any slice work starts.

## Build scope

The build covers every slice listed in the spec's "Slice checklist" section, in declared order. The plan file mirrors that checklist, one cycle per slice, plus a final cross-slice integration pass and a final test-run gate.

Rules:

- Build only one slice at a time.
- Do not start the next slice until the current slice's plan/build/review/verification/spec-reconciliation cycle is complete.
- After all in-spec slices are built, run a cross-slice **integration pass** (Worker 1; may trigger a second-loop refactor through Worker 2 and Worker 3 if DRY opportunities are found).
- The build closes with one final test-run gate handled by Worker 1.

## Coverage is the maintainer's gate, not a worker's tool

Workers do not run `pytest` with coverage flags. `--cov=...`, `--cov-report=...`, `--cov-config=...`, and equivalent invocations are forbidden in every worker pass — planning, build, apply-changes, review, re-review, final verification, integration, and the final test-run gate. `--no-cov` is permitted (and is the only permitted coverage-shaped flag) when `pytest.ini`'s `addopts` auto-applies `--cov` — `--no-cov` opts OUT of coverage entirely rather than configuring it.

Coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`) and the maintainer's job. Missing test branches are caught by comparing the diff against the spec — "Decision 4 says X must be rejected; is there a test that asserts X is rejected?" — not by running coverage.

Tests themselves are still in scope:

- Worker 1 plans which tests must exist.
- Worker 2 writes them in the same change as the code.
- Worker 3 verifies they exercise the right branches by reading the diff against the spec; may run focused tests (without coverage flags) to confirm pass/fail.
- Worker 1's final test-run gate runs `uv run pytest --no-cov` once at the end (the explicit `--no-cov` is required because `pytest.ini` auto-applies `--cov`).

If gap-discovery feels intractable, escalate to the maintainer rather than running coverage.

## Required plan structure

`docs/builder/build-<NNN>-<topic>-<0_0_X>.md` must begin with:

- spec source path
- target release version
- date created
- pre-flight outcome and working-tree baseline summary
- a short copy of the one-slice-at-a-time rule
- a short copy of the DRY-first rule
- a list of every build artifact that will be created

Then a slice-level checklist. Every slice and every integration/final pass must have:

- a checkbox (only Worker 0 marks `- [x]`, and only after Worker 1 final verification accepts the slice)
- the spec slice it implements
- the exact build artifact file to create

### Template shape

The block below is a **fictional placeholder**. Substitute the active spec's topic, target version, and actual slice titles; do not treat any of these names as referencing a current or past build.

```text
# Package build plan: example_topic / 0.0.X (NNN)

Spec source: `docs/spec-NNN-example_topic-0_0_X.md`
Target release: `0.0.X`
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Pre-flight: passed on YYYY-MM-DD; baseline: clean.

## Artifact list

- `docs/builder/bld-slice-1-<short_slug>.md`
- `docs/builder/bld-slice-2-<short_slug>.md`
- `docs/builder/bld-slice-3-<short_slug>.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [ ] Slice 1: <slice title from spec> -> `docs/builder/bld-slice-1-<short_slug>.md`
- [ ] Slice 2: <slice title from spec> -> `docs/builder/bld-slice-2-<short_slug>.md`
- [ ] Slice 3: <slice title from spec> -> `docs/builder/bld-slice-3-<short_slug>.md`
- [ ] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [ ] Final test-run gate -> `docs/builder/bld-final.md`
```

Use the actual slice list from the spec. Do not invent slices. Keep the checklist in the spec's declared slice order.

## Build artifact naming

Per-slice, integration, and final build artifacts are tracked Markdown files under `docs/builder/` for the active cycle. They are committed alongside the source changes they describe, then treated as old build artifacts at the next build's pre-flight cleanup.

Naming rules:

- Start with `docs/builder/bld-`.
- For a spec slice: `bld-slice-<N>-<short_slug>.md` where `N` is the 1-indexed slice number from the spec and `<short_slug>` is a lowercase underscore-separated summary of the slice title.
- Cross-slice integration pass: `docs/builder/bld-integration.md`.
- Final test-run gate: `docs/builder/bld-final.md`.

The build plan must list every artifact before build work starts.

## Build artifact template

Every `docs/builder/bld-<slice>.md` file accumulates the full back-and-forth for that slice. The artifact is the contract that flows between workers; everything inter-worker happens through this file plus the working-tree diff.

### Status field ownership

The artifact's `Status:` line is set by exactly one worker per transition:

- `planned` — Worker 1 sets this when the artifact is first created. New artifacts always start with `Status: planned`.
- `built` — Worker 2 sets this at the end of every build pass (including re-passes after a Worker 3 rejection).
- `revision-needed` — set by Worker 3 (review surfaces unresolved findings) or Worker 1 (final verification rejects). Either triggers Worker 0 to spawn Worker 2 again.
- `review-accepted` — set by Worker 3 when accepting the diff; signals Worker 0 to spawn Worker 1 for final verification.
- `final-accepted` — set by Worker 1 at the end of final verification; signals Worker 0 to mark the checklist box.

Worker 0 never writes to `Status:`. Worker 0 reads it to drive dispatch.

````text
# Build: Slice <N> — <slice title>

Spec reference: `docs/spec-<NNN>-<topic>-<0_0_X>.md` (lines <start>-<end>)
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

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

### Test additions / updates

- Which tests prove the slice? Pin the path and assertion shape.
- Are temp/scratch tests appropriate for development? Note them here for Worker 3.

### Implementation discretion items

Items where Worker 1 has **assessed the design and decided** the choice is at Worker 2's discretion (e.g. a stylistic preference between two equally valid shapes, a private kwarg name, the order of two independent setup steps). This section is the planner's last attempt to make discretion explicit, not an architectural escape hatch. If Worker 1 cannot resolve a question by reading the spec and the codebase, stop the planning pass and escalate to the maintainer.

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for this slice from `## Slice checklist`, copied verbatim as `- [ ]` boxes (preserve exact text, nested sub-bullets, inline citations). Worker 1 ticks each `- [x]` during final verification as the contract lands. An unticked box at final verification is either deferred with a one-line reason under `### Spec changes made (Worker 1 only)` or the slice goes `revision-needed`. Worker 3 walks the list during review; a sub-check that appears silently un-addressed in the diff is a Medium finding.

- [ ] (verbatim sub-check #1)
- [ ] (verbatim sub-check #2)
- ...

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
- `git status --short` after both ruff invocations — list every modified file. Classify each: slice-intended (stays in the diff; appears in `### Files touched`) or unrelated tool churn (reverted with `git checkout -- path` before setting `Status: built`). Tool-induced drift is Worker 2's responsibility to own at this boundary; never pass it through as "out of scope" or defer to Worker 1.
- Focused test commands run, if any (without `--cov*` flags — see "Coverage is the maintainer's gate, not a worker's tool")

### Implementation notes

Design choices made during implementation that the plan did not explicitly fix — e.g. `__dict__` vs `vars()`, the shape of a shared helper, the test fixture pattern chosen, a tuple-of-pairs vs parallel-list constant, the precise import path of a third-party utility. One bullet per non-trivial decision with a one-line "why this shape." Worker 3 reads these to follow the reasoning without reverse-engineering the diff; Worker 1 reads them during final verification to spot drift from the plan.

If a decision is structural enough to count as plan-vs-implementation drift (see `worker-2.md` "Plan-vs-implementation drift"), surface it in `### Notes for Worker 1 (spec reconciliation)` instead — that is the louder signal.

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

### Public-surface check

Confirm `git diff -- django_strawberry_framework/__init__.py` does not change `__all__` or the re-export list, OR confirm any change is authorized by the active spec (cite the spec line). Definition-of-done items typically pin "no new public exports"; this check makes that explicit per review.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

If the slice's diff includes a change to `CHANGELOG.md`, read the new entry end-to-end and confirm:

- the version line matches `pyproject.toml` and `django_strawberry_framework/__init__.py`
- `### Added` / `### Changed` / `### Fixed` / `### Removed` headings used are the ones the active spec authorizes
- the wording matches the canonical phrasings the plan committed to (or reads coherently against the actual behavior shipped)
- nothing overstates or understates the change

If the slice does not touch `CHANGELOG.md`, write `Not applicable; slice did not modify CHANGELOG.md.`.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

If the slice's diff includes documentation, release metadata, KANBAN movement, or spec archival, read the changed files end-to-end and confirm:

- version strings, shipped/planned statuses, and card IDs match the active spec and the package version after the slice
- moved KANBAN cards are removed from their old section and appear in the target section exactly once
- Markdown links introduced or moved by the slice point at existing files or documented future files
- active-spec archival, if planned, preserves the historical record and leaves the live follow-up source of truth in the durable doc named by the spec
- when the slice copies verbatim text from the spec (e.g. KANBAN card bodies, CHANGELOG entries, GLOSSARY.md entry text), confirm character-for-character via `diff` against the spec source; for fenced-code drop-ins where the inner fence backtick count matches the outer, confirm the outer fence used four backticks (or another non-conflicting form) so markdown rendering is intact
- no obsolete "coming soon", "planned", or old-version wording remains in files the slice deliberately updated

If the slice does not touch those surfaces, write `Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.`.

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

## Re-pass sections

Each Worker 2 re-pass appends a `## Build report (Worker 2, pass <N>)` section at the same top level (NOT inside a sub-heading). Each Worker 3 re-review appends a `## Review (Worker 3, pass <N>)` section the same way. The artifact reads as a linear sequence of pass / review / pass / review entries; do not edit prior entries.

---

## Final verification (Worker 1)

- Spec slice checklist: every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` is `- [x]` (the contract landed), or has a one-line deferral reason under `### Spec changes made (Worker 1 only)`. Silently un-ticked boxes block `final-accepted`.
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
- spec contract violation (the build does not deliver what the spec says)
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
- silently-unaddressed spec slice sub-check (a `- [ ]` item in the Plan's `### Spec slice checklist (verbatim)` with no matching implementation in the diff and no recorded deferral)
- repeated literal / key / tuple that should be a named constant

Low:

- small maintainability issues
- naming clarity
- minor typing/API polish
- localized simplification
- comments or docstrings that are stale or wrong but not load-bearing

## Static inspection helper: `scripts/review_inspect.py`

The helper parses the target file as text and AST only — it never imports or executes the module — so it is safe to run on files that touch Django settings, the registry, or Strawberry type creation at import time.

### When to run the helper during build

Worker 1 **must run** the helper during planning when:

- The plan adds logic to any existing `.py` file with at least 150 source lines.
- The plan adds logic to any file under `django_strawberry_framework/optimizer/` or `django_strawberry_framework/types/`.

Worker 3 **must run** the helper during review when:

- The slice adds a new `.py` file of any size, **unless** it is a pure-class-definition module (only `class` declarations with docstrings, no logic). For low-surface files, Worker 3 skips the helper and records the skip and reason in the artifact.
- The slice touches an existing `.py` file under `optimizer/` or `types/`.
- The slice adds 30 or more lines of new logic to any file under `django_strawberry_framework/`.
- The slice adds 50 or more lines of new logic to any file outside `django_strawberry_framework/`.

Worker 1 and Worker 3 may skip the helper for files where the artifact will be a "no review-worthy logic" disposition (pure re-exports, single-line constants). The skip must be recorded explicitly with a short reason.

Worker 2 **may re-run** the helper when refreshed output would help implementation. Note shadow-file use in `Notes for Worker 3`.

### How to run

From the repository root:

```shell
python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
```

To refresh shadow output for every package `.py` file recursively:

```shell
python scripts/review_inspect.py --all --output-dir docs/shadow
```

Every build-cycle helper invocation must pass `--output-dir docs/shadow`.

Useful flags:

- `--all` — inspect every `.py` file under `django_strawberry_framework/` recursively. Do not pass a single-file target with this flag.
- `--outline-only` — keep only Imports, Symbols, Control-flow hotspots, and Django/ORM markers in the overview.
- `--stdout` — print the overview to stdout in addition to writing it.
- `--marker NAME` — add a custom marker to the Django/ORM marker table. Repeatable.
- `--long-function-lines N` and `--long-function-branches N` — raise or lower the control-flow hotspot thresholds (defaults: 40 lines, 8 branches).
- `--first-party-prefix PREFIX` — add a first-party import prefix; defaults to `django_strawberry_framework`. Repeatable.
- `--literal-min-length N` — minimum length for repeated string literals to surface (default 8).

### Overview sections

- **Quick scan** — count summary for imports, symbols, hotspots, executable marker lines, calls of interest, TODOs, and repeated string literals.
- **Imports** — every import categorized as local / first-party / django / strawberry / standard-or-third-party. Cross-folder imports are usually structural changes worth flagging.
- **Symbols** — table of contents for the file's classes and functions with line ranges and parent class.
- **Control-flow hotspots** — functions exceeding the line or branch thresholds. Apply Medium-tier complexity attention to every hotspot.
- **Django / ORM markers** — every line with an executable-code match for `QuerySet`, `select_related`, `prefetch_related`, `Prefetch`, `only`, `_meta`, `get_queryset`, `_prefetched_objects_cache`, `fields_cache`, `DjangoType`, `OptimizationPlan`, `OptimizerHint`, `dst_optimizer_plan`, or `_optimizer_field_map`; comment and string-literal mentions are ignored. Walk every entry; each needs either a one-line justification or a finding.
- **Calls of interest** — reflective-access and container-coercion calls (`getattr`, `hasattr`, `isinstance`, `setattr`, `dict`, `frozenset`, `iter`, `len`, `list`, `set`, `tuple`).
- **Comments and docstrings** — docstring inventory, TODO comments, and full comment inventory.
- **Repeated string literals** — DRY signal for executable string literals; docstrings are excluded. Essential at the cross-slice integration pass.

### Output files

Two files land under `docs/shadow/<stable-stem>`:

- `<stem>.stripped.py` — target source with `#` comments removed and every string-literal token (including docstrings) replaced by `...`; with `--strip-docstrings`, docstring statements are removed entirely instead.
- `<stem>.overview.md` — static AST overview.

`docs/shadow/` is gitignored.

### Shadow-file line numbers are NOT canonical

The shadow file strips `#` comments and replaces every string-literal token (including docstrings) with `...`; with `--strip-docstrings`, docstring statements are removed entirely instead. Either way, its line numbers do not match the original source. Build artifacts, code-review feedback, and source edits must cite **original source-file line numbers**, never shadow-file line numbers. The shadow file is read-only; never edit or commit it.

## Subagent dispatch and worker memory

Workers 1, 2, and 3 each run as **separate subagent invocations per cycle item**. Worker 0 stays in the main thread as the project manager. The split is what makes the artifact-as-contract model work: the worker that reviews a build has no in-context memory of the worker that wrote it.

### Worker memory

Each worker keeps a private scratch memory file that **persists across slices within a single build** but is invisible to every other worker:

- `docs/builder/worker-memory/worker-0.md` — Worker 0's coordination notebook
- `docs/builder/worker-memory/worker-1.md` — Worker 1's planning / spec-reconciliation / final-QA notebook
- `docs/builder/worker-memory/worker-2.md` — Worker 2's implementation notebook
- `docs/builder/worker-memory/worker-3.md` — Worker 3's review notebook

These files are gitignored. Worker 0 creates the directory at plan time and seeds the four files empty after the pre-flight cleanup has deleted any prior-build memory. The next build's pre-flight cleanup clears them again.

**What a worker writes to its memory.** At the end of each cycle, the worker appends a short entry (3-5 lines) capturing what to carry into the next cycle. Entries are append-only. If a worker's memory exceeds ~50 lines, the worker must consolidate (merge similar entries into a single pattern observation) before adding more.

**Read isolation.** A worker may read **only** its own memory file. Worker 0 may read all four at closeout for the retrospective — never during the active cycle.

**Write isolation.** A worker writes only to its own memory file. The main thread (Worker 0) never edits another worker's memory.

### Spawn-per-cycle dispatch

Worker 0 spawns the workers in this order per slice:

1. **Worker 1 (planning pass)** — produces the plan section of the artifact, sets `Status: planned`, appends to `worker-1.md`, returns.
2. **Worker 2 (build pass)** — implements the slice, appends a build report to the artifact, sets `Status: built`, appends to `worker-2.md`, returns.
3. **Worker 3 (review pass)** — reviews, appends review section to the artifact, may create temp tests under `docs/builder/temp-tests/<slice>/`, sets `Status: review-accepted` or `revision-needed`, appends to `worker-3.md`, returns.
4. **If `revision-needed`:** Worker 0 re-spawns Worker 2 (apply-changes pass) — implements fixes, appends a new build report. Then Worker 0 re-spawns Worker 3 (re-review pass). Repeat until Worker 3 has no unresolved findings or all remaining findings are intentionally rejected with a recorded reason.
5. **Worker 1 (final-verification pass)** — runs the slice-local checks, reconciles the spec if needed, appends final verification section, sets `Status: final-accepted` or `revision-needed`, appends to `worker-1.md`, returns.
6. **Worker 0** marks the slice's checkbox `- [x]` in the build plan only if Worker 1 set the artifact status to `final-accepted`, then appends progress to `worker-0.md`.

Each subagent's prompt must include: standing project docs (`AGENTS.md`, `START.md`, `BUILD.md`, the worker's own role file), the active build plan, the active spec, the cycle's artifact, and the worker's own memory file contents. The prompt must explicitly forbid reading the other workers' memory files.

**No cross-worker chatter.** Subagents do not message each other directly. All inter-worker information flows through the artifact and the diff.

### Isolation is non-waivable

Worker 2 and Worker 3 must always run as separate subagent invocations. The cycle does not allow combining them — even for slices with no High-severity findings, even for trivial slices. Combining them would let the agent that wrote the code also approve it.

### Recovery from interrupted subagent runs

If a subagent fails mid-run (transient API error, network failure, time-out), the on-disk diff captures whatever was changed and the artifact captures whatever sections were appended. To recover, Worker 0 dispatches a **fresh subagent of the same role** with explicit "pick up where the prior pass left off" context: name the partial artifact, the current working-tree diff as authoritative, the worker's own memory file, and the original task contract. The new subagent finishes the **same** pass — no "pass N+1" suffix — and sets the appropriate `Status:` line. If the on-disk diff is unsalvageable, escalate to the maintainer rather than guessing at rollback.

## Cross-slice integration pass

After every slice in the spec is checked complete, Worker 1 runs the integration pass and produces `docs/builder/bld-integration.md`.

Before writing `bld-integration.md`, Worker 1 must:

1. Read every prior `docs/builder/bld-slice-*.md` artifact for the build, in slice order. No "as needed" — every artifact is required context for the cross-slice DRY scan.
2. Confirm the static inspection helper has been run, or explicitly skipped with a recorded reason, for every Python file with review-worthy logic touched by the build.
3. Compare the **Repeated string literals** sections across every shadow overview. A literal that appears in two or more files is a cross-slice DRY candidate; record it in the integration artifact.
4. Compare the **Imports** sections across every shadow overview to confirm one-way dependency direction and spot any sibling that has started importing from outside the documented boundary.
5. Walk every accepted slice artifact's `What looks solid` and `DRY findings` sections to catch any deferred follow-up that should land in this pass.

The integration pass itself checks:

- duplicated helpers across slices
- inconsistent naming or error handling between slices
- repeated ORM/queryset patterns that should be centralized
- misplaced responsibilities between modules touched by different slices
- missing or too-broad exports introduced by the build
- repeated string literals / dictionary keys / tuple shapes across slices
- whether comments now tell one coherent story across the new code

If DRY opportunities are found, Worker 1 records them in `bld-integration.md` and asks Worker 0 to dispatch Worker 2 for a consolidation pass and Worker 3 for a review pass. Repeat until clean.

## Final test-run gate

After the integration pass is clean, Worker 1 runs the final test-run gate and produces `docs/builder/bld-final.md`.

The gate is intentionally narrow:

- Run `uv run pytest --no-cov` (full sweep across all three test trees per `AGENTS.md`). The explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov`. Plain `uv run pytest` is a coverage run in this repo and is forbidden by "Coverage is the maintainer's gate, not a worker's tool".
- Run Django's own consistency checks against the example project:
  - `uv run python examples/fakeshop/manage.py check`
  - `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`
  These catch model/admin/url-config drift that `pytest` does not.
- Run the lint/format/diff gate:
  - `uv run ruff format --check .` — fails if any file is not properly formatted (read-only; do NOT pass `--fix`)
  - `uv run ruff check .` — fails on any lint violation (read-only; no `--fix`)
  - `git diff --check` — fails on whitespace errors or conflict markers anywhere in the working tree
  Failures block `final-accepted` unless a pre-flight baseline exception was explicitly recorded in the build plan's preamble.
- The only `pytest`-side requirement is that the existing suite passes. Do NOT inspect or assert line coverage at this stage.

Record each command's pass/fail in `bld-final.md`. If failures appear, re-loop through whichever slice owns the failing behavior (Worker 1 plans the fix, Worker 0 dispatches Worker 2, Worker 0 dispatches Worker 3, Worker 1 re-runs the gate).

`bld-final.md` must also include a `### Deferred work catalog` subsection. Walk every per-slice and integration artifact's spec-reconciliation notes and `What looks solid` / `Notes for Worker 1` sections; surface every item that was explicitly deferred to a future slice, future spec, or maintainer follow-up. One bullet per deferral with the source artifact section, the spec line that licenses the deferral (if any), and a one-line description. If nothing was deferred, write `No deferred work; the build delivered the spec end-to-end.`. The catalog is the next spec author's reading list.

The gate closes the build cycle. Worker 0 then marks the final checkbox `- [x]`.

## Spec reconciliation

The spec is **input** to the build, not output. But implementation routinely reveals:

- gaps in the spec (a Decision that depends on something unstated)
- conflicts between Decisions
- realities of the codebase that the spec didn't anticipate

When this happens, **only Worker 1** may mutate `docs/spec-<NNN>-<topic>-<0_0_X>.md`. Worker 1 records the edit in the active slice artifact under `### Spec changes made (Worker 1 only)` with cited spec line(s), one-line reason per change, and the slice that triggered the change.

Workers 0, 2, and 3 surface spec issues by writing them into the slice artifact under `### Notes for Worker 1 (spec reconciliation)`; they may not edit the spec themselves.

If a spec edit fundamentally changes the slice contract Worker 2 already implemented against, Worker 1 must re-spawn Worker 2 for an adjustment pass before final verification.

### Slice splitting

Worker 1 may also **split a planned slice into sub-slices** (e.g. `5a` / `5b`) when implementation reveals the slice cannot land as a single coherent diff — typical triggers: the diff is too large for sensible review, two halves have independent risk profiles, or one half is blocked while the other can ship. The split is a spec edit (recorded under `Spec changes made (Worker 1 only)` with cited spec lines and a one-line reason). After the spec is updated, Worker 1 returns control to Worker 0 to regenerate the build plan's checklist and dispatch Worker 2 for each sub-slice in sequence. Splits add an extra artifact and an extra full worker cycle (plan → build → review → final-verification), so reserve them for cases where the unsplit slice would harm review quality.

### Spec stays at its working location

Specs are written at `docs/spec-<NNN>-<topic>-<0_0_X>.md` and stay there after the build closes. Closing a build does NOT imply moving the spec to an archive location. Live follow-up state belongs in the durable docs the spec named (`docs/GLOSSARY.md`, `KANBAN.md`, `CHANGELOG.md`).

If a future spec explicitly declares spec archival or relocation as part of its own slice checklist, that is an opt-in lifecycle step the spec itself authorizes. In that case Worker 1 calls the move out in the plan as a Worker 1-owned final-verification step, Worker 2 implements the durable docs / KANBAN / changelog / release-file edits named by the plan but does not move or edit the active spec, and Worker 1 performs the mechanical active-spec move during final verification (recording old and new paths under `Spec changes made (Worker 1 only)`).

## Slice handoff (no maintainer pause between slices)

The build runs end-to-end without pausing for maintainer review between slices. After Worker 0 marks a slice `- [x]` (Worker 1's final-verification pass set the artifact to `final-accepted`), Worker 0 IMMEDIATELY dispatches the next slice's planning pass — or, if every spec slice is complete, the cross-slice integration pass. Worker 1's final-verification IS the per-slice safety net; no additional re-read or maintainer-review step runs between slices.

The maintainer's first touch point is after the final test-run gate sets `bld-final.md` to `final-accepted` and Worker 0 marks the final checkbox `- [x]`. At that point Worker 0 stops driving the cycle and hands off — the maintainer reviews the whole build, then commits the source changes + every `bld-*.md` artifact + spec edits (if any) + the completed plan in one or more commits at the maintainer's discretion. The closeout retrospective (per `## Closeout` below) runs after the maintainer's commit, not before.

If anything goes wrong mid-cycle (an unresolvable spec ambiguity, an unsalvageable diff, a stop-condition in `worker-0.md`), Worker 0 stops and escalates to the maintainer immediately rather than waiting for the end of the build. The non-pause rule applies to the happy path, not to genuine blockers.

Maintainer commit posture (unchanged): only the maintainer commits. Workers never commit, even if asked. Workers also never amend, force-push, or otherwise rewrite git history.

## Closeout

Closeout runs **after** the maintainer has committed the build and supplied (or been asked for) the build-cycle commit range. Workers do not run closeout against an uncommitted working tree; the diff-scan step depends on the commits existing. When all checklist items are marked `- [x]` AND the maintainer has handed back the commit range:

1. Worker 0 scans all build-cycle commit diffs (using the maintainer-provided commit range).
2. Worker 0 reads all four worker-memory files (one-time read at closeout) to surface patterns the workers themselves noticed.
3. Worker 0 identifies recurring DRY patterns, repeated bug classes, and workflow stumbling blocks.
4. Worker 0 provides a brief retrospective to the maintainer.
5. After maintainer approval, Worker 0 updates `docs/builder/BUILD.md` or the worker role files with general retrospective notes — describing recurring patterns and workflow improvements **without naming specific already-shipped fixes**.
6. Worker 0 deletes `docs/shadow/` contents and `docs/builder/temp-tests/` contents after the retrospective is complete. Worker memory may remain long enough for the retrospective; the next build's pre-flight cleanup clears it before any worker reads it.
7. The maintainer commits the updated `docs/builder/` workflow docs along with the now-completed plan and any `bld-*.md` artifacts kept for the just-finished build.

Only the maintainer commits. Workers never commit, even if asked.
