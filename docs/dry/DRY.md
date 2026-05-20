# DRY consolidation workflow

This document defines the reusable process for **acting on DRY recommendations** left behind by a closed build or review cycle. It does not track a specific DRY pass. A DRY pass is tracked in a per-cycle plan file under `docs/dry/dry-<0_0_X>.md`.

The DRY workflow runs **after** a build cycle (`docs/builder/BUILD.md`) or review cycle (`docs/review/REVIEW.md`) closes. Each closed cycle emits per-artifact DRY analysis sections describing existing patterns reused, helper opportunities, and duplication risks. This workflow gathers those into one consolidated plan and dispatches workers to dispose of each opportunity — either implement it, confirm it has already been addressed, or remove it as a false positive.

The standing worker instructions live beside this overview:

- [Worker 0: project manager](worker-0.md)
- [Worker 1: triage and verifier](worker-1.md)
- [Worker 2: fix implementer](worker-2.md)

There is **no Worker 3** in this workflow. Worker 1 plays both roles a reviewer would normally split — the pre-implementation triage and the post-implementation verification — because each finding is a small, contained consolidation rather than a full feature slice.

Permanent workflow files under `docs/dry/` are tracked: `DRY.md`, `worker-*.md`, and every `dry-<0_0_X>.md` plan file. They are committed to git as the permanent record of the DRY cycle. The only intentionally untracked path is `docs/dry/worker-memory/`.

`AGENTS.md` and `START.md` still apply during DRY runs. This workflow adds the per-worker artifact discipline on top.

Only the maintainer commits. Workers never commit, even if asked.

## Required reading per worker

Every worker reads the standing project docs and its own role file before acting. The matrix below is the single source of truth; worker role sections and the standalone `worker-*.md` files reference it instead of re-listing.

| Document | W0 | W1 | W2 |
|---|---|---|---|
| `AGENTS.md` | yes | yes | yes |
| `START.md` | yes | yes | yes |
| `docs/dry/DRY.md` | yes | yes | yes |
| `docs/dry/worker-0.md` | yes | — | — |
| `docs/dry/worker-1.md` | — | yes | — |
| `docs/dry/worker-2.md` | — | — | yes |
| `pyproject.toml` | yes (plan + closeout) | — | — |
| `django_strawberry_framework/__init__.py` | yes (plan + closeout) | — | — |
| `GOAL.md` | yes | yes | — |
| `docs/GLOSSARY.md` | yes | yes | — |
| active `docs/dry/dry-<0_0_X>.md` | yes (owns boxes + deletions) | yes (appends Triage / Verification sub-bullets) | yes (appends Implementation sub-bullets) |
| source artifacts the plan extracted from (`bld-*.md` / `rev-*.md`) | yes (read-only, when dispatching) | yes (read-only) | yes (read-only) |
| relevant source / tests | — | yes (read-only) | yes (writes) |
| Worker 2's diff | — | yes (during verification pass) | — |
| own `docs/dry/worker-memory/worker-N.md` | yes | yes | yes |

Workers never read another worker's memory file during the cycle; see "Subagent dispatch and worker memory" below. The plan artifact (`dry-<0_0_X>.md`) plus the working-tree diff are the inter-worker contract.

## Pre-flight checks

Before Worker 0 generates the plan, verify the cycle preconditions:

1. **Source cycle is closed.** The build or review cycle whose findings will drive this DRY pass must already be `final-accepted` / `verified` end-to-end. Open cycles produce stale recommendations.
2. **Working tree is clean OR baseline is explicit.** Run `git status --short`. If unrelated uncommitted changes exist, commit them, set them aside, or explicitly include them in the baseline before the plan is written. The script's output and per-finding diffs are only useful when everyone agrees which changes predate the cycle.
3. **`docs/dry/export_dry_review.py` runs.** Smoke invocation: `uv run python docs/dry/export_dry_review.py --help`. Confirm the help text prints. If the script is broken, escalate before continuing.
4. **Planned plan path is free.** `docs/dry/dry-<0_0_X>.md` must not already exist; an existing plan from a prior cycle should be committed (if it is a finished record) or moved aside before the new pass starts.
5. **`docs/dry/worker-memory/` is fresh or intentionally cleared.** Worker 0 creates the directory at plan time and (re-)seeds the three files empty. Confirm `.gitignore` lists this path.

Record the outcome in the plan file's preamble (`Pre-flight: passed on YYYY-MM-DD; baseline: clean` or `Pre-flight: <issue>, resolved by <action>; baseline: <summary>`). If any check fails and can't be resolved without maintainer input, escalate before generating the plan.

## Generating the plan

Worker 0 runs:

```shell
uv run python docs/dry/export_dry_review.py --source-dir <docs/builder|docs/review>
```

The script:

- **infers the target release** by scanning `--source-dir` for a `*-X_X_X.md` file (e.g. `review-0_0_5.md`, `build-014-foo-0_0_6.md`). Exits with an error if zero or multiple distinct versions are present; in the multi-version case Worker 0 must pass `--target-release <X.X.X>` explicitly to disambiguate.
- scans every `*.md` file in `--source-dir`,
- finds each file's `DRY analysis` heading (any ATX level — `## DRY analysis`, `### DRY analysis`, etc.) and extracts the content beneath it up to the next heading at the same or higher level,
- is **code-fence-aware** — headings inside fenced code blocks (e.g. template snippets in `BUILD.md` / `REVIEW.md` / worker role docs) are ignored, so only real DRY analysis sections become findings,
- prefixes every top-level bullet in the extracted content with `- [ ]` so Worker 0 can tick it,
- writes `docs/dry/dry-<release-underscored>.md` with a plan header + a `## Findings` section containing one `## <file H1 title>` per finding.

If `--output` is supplied explicitly, the script writes there instead. The plan file is the canonical checklist for the cycle and is committed alongside the source changes the cycle produces.

## Plan structure

The generated `dry-<0_0_X>.md` file begins with:

- the target release version
- the source directory the script scanned
- the generation date
- a one-line description of the cycle rule (W0 dispatches > W1 triages > W2 implements > W1 verifies > W0 ticks)

Then a `## Findings` section. Under it, one `## <Artifact title>` block per source artifact. Each block contains:

- a `_Source:_` line citing the source artifact path
- the artifact's DRY bullets, every top-level bullet prefixed `- [ ]`

Each `- [ ]` bullet is a finding. Workers append nested sub-bullets under each finding as the cycle progresses (Triage, Implementation, Verification — see "Finding lifecycle" below).

Worker 0 may append a free-form preamble note after the script writes (e.g. extra baseline context). Workers never edit the script-generated heading or the `_Source:_` lines.

## Finding lifecycle

Findings are processed one at a time, in declared order.

For each `- [ ]` finding:

1. **Triage pass.** Worker 0 dispatches Worker 1 with the finding text and a citation to the source artifact. Worker 1 reads the source artifact, the cited code, and any related tests, then chooses one disposition:
   - **Real and unaddressed.** Worker 1 appends a `Triage` sub-bullet under the finding with disposition + extra context (call sites, recommended consolidation shape, any constraints Worker 2 should respect). The finding stays `- [ ]`. Worker 1 returns `real` to Worker 0.
   - **Already addressed.** A subsequent commit or follow-up already consolidated this. Worker 1 appends a `Triage` sub-bullet citing the resolution. Worker 1 returns `already-addressed` to Worker 0. Worker 0 deletes the finding's bullet (and any sub-bullets) from the plan.
   - **Not a real opportunity.** False positive (e.g. the "duplication" is intentional sibling design, or extracting the helper would be premature abstraction at N=2). Worker 1 appends a `Triage` sub-bullet with the reason. Worker 1 returns `not-real` to Worker 0. Worker 0 deletes the finding's bullet.
2. **Implementation pass.** Worker 0 dispatches Worker 2 with the triaged finding. Worker 2 reads the Triage sub-bullet, makes the consolidation in source (and tests), runs `ruff format` and `ruff check --fix`, classifies and reverts any unrelated tool-induced drift via `git status --short`, and appends an `Implementation` sub-bullet under the finding. The finding stays `- [ ]`.
3. **Verification pass.** Worker 0 dispatches Worker 1 with the implemented finding. Worker 1 reads Worker 2's diff, the Triage, and the Implementation, then chooses:
   - **Verified.** The consolidation matches the Triage's intent, tests pass focused, and no regression is visible. Worker 1 appends a `Verification` sub-bullet. Worker 1 returns `verified` to Worker 0. Worker 0 marks the finding `- [x]`.
   - **Revision needed.** Something is missing, partial, or regressed. Worker 1 appends a `Verification` sub-bullet stating exactly what's missing or broken. Worker 1 returns `revision-needed` to Worker 0. Worker 0 re-dispatches Worker 2 (back to step 2).

Worker 0 dispatches one finding at a time. Parallel dispatch is allowed only when the maintainer explicitly authorizes it — most DRY findings touch shared helpers and serial dispatch avoids surprising interactions between half-landed consolidations.

## Subagent dispatch and worker memory

Workers 1 and 2 each run as **separate subagent invocations per pass**. Worker 0 stays in the main thread as the dispatcher. The split exists so the worker that verifies a fix has no in-context memory of the worker that wrote it — even within a single finding, the verifier starts fresh and sees only the plan artifact and the diff.

### Why subagent dispatch

A single agent role-playing every worker can convince itself a consolidation is sufficient because it remembers _why_ it implemented it that way. Subagent isolation removes that path: the verifying Worker 1 sees only the Triage note, the Implementation note, and the diff.

### Worker memory

Each worker keeps a private scratch memory file that **persists across findings within a single DRY cycle** but is invisible to every other worker:

- `docs/dry/worker-memory/worker-0.md` — Worker 0's coordination notebook
- `docs/dry/worker-memory/worker-1.md` — Worker 1's triage / verification notebook
- `docs/dry/worker-memory/worker-2.md` — Worker 2's implementation notebook

These files are gitignored. Worker 0 creates the directory at plan time and (re-)seeds the three files empty, truncating any prior-cycle content. The directory persists after closeout — the files stay on disk as the workers' own running record, available for the maintainer to inspect later. The tracked permanent record is the `dry-<0_0_X>.md` plan, not these notes.

**What a worker writes to its memory.** At the end of each pass, the worker appends a short entry — typically 3-5 lines — capturing what to carry into the next pass:

- Worker 0: which finding closed (verified / removed), friction noticed in dispatch.
- Worker 1: triage signals (classes of false positive / already-addressed worth flagging early), verification patterns that worked.
- Worker 2: consolidation patterns that worked, test patterns worth carrying forward, verification pushback applied if this was a re-pass.

Entries are append-only. If a worker's memory exceeds ~50 lines, the worker must consolidate (merge similar entries into a single pattern observation) before adding more — never delete without consolidating first.

**Read isolation rules.** A worker may read **only** its own memory file:

- Worker 0 may not read worker-1/2 memory during the cycle (it may read all three at closeout for the retrospective).
- Worker 1 may not read worker-0/2 memory.
- Worker 2 may not read worker-0/1 memory.

**Write isolation rules.** A worker writes only to its own memory file. Worker 0 never edits another worker's memory.

**Spawn-per-pass dispatch.** Worker 0 spawns the workers in this order per finding:

1. Worker 1 subagent (triage pass) — appends the Triage sub-bullet under the finding, appends to `worker-1.md`, returns the disposition.
2. If `real`: Worker 2 subagent (implementation pass) — appends the Implementation sub-bullet, appends to `worker-2.md`, returns.
3. Worker 1 subagent (verification pass) — appends the Verification sub-bullet, appends to `worker-1.md`, returns `verified` or `revision-needed`.
4. If `revision-needed`: Worker 0 re-spawns Worker 2 (back to step 2). Repeat until `verified`.
5. Worker 0 marks the finding `- [x]` (or, for `already-addressed` / `not-real` dispositions in step 1, deletes the finding from the plan) and appends progress to `worker-0.md`.

Each subagent's prompt must include: standing project docs (`AGENTS.md`, `START.md`, `DRY.md`, the worker's own role file), the active plan, the specific finding being processed (with its existing sub-bullets), the source-artifact citation, and the worker's own memory file contents. The subagent's prompt must explicitly forbid reading the other workers' memory files.

**No cross-worker chatter.** Subagents do not message each other directly. All inter-worker information flows through the plan artifact (`dry-<0_0_X>.md`) and the working-tree diff.

**Lifecycle.**

- Worker 0 creates `docs/dry/worker-memory/` and (re-)seeds three empty files (`worker-0.md`, `worker-1.md`, `worker-2.md`) at plan-creation time, truncating any prior-cycle content.
- Workers read their own file at the start of every spawn and append at the end.
- The directory persists after closeout. The files stay on disk as the maintainer's reference; the next cycle's Worker 0 re-seeds them empty at plan-creation time. Worker 0 does NOT delete the directory at closeout.

### Recovery from interrupted subagent runs

If a subagent fails mid-pass (transient API errors, network failures, time-outs), Worker 0 dispatches a **fresh subagent of the same role** with explicit "pick up where the prior pass left off" context. The new subagent's prompt names the partial sub-bullet (if any), the current working-tree diff, the worker's own memory file (the prior pass may have appended), and the finding's existing context.

The recovery finishes the original pass's sub-bullet; it does NOT start a "pass N+1" sub-bullet.

If the on-disk diff is unsalvageable, Worker 0 escalates to the maintainer rather than guessing at rollback.

## Coverage is the maintainer's gate, not a worker's tool

Workers do not run `pytest` with coverage flags. `--cov=...`, `--cov-report=...`, `--cov-config=...`, and equivalents are forbidden in every DRY pass — triage, implementation, verification, and the final test-run gate. `--no-cov` is permitted (and is the only permitted coverage-shaped flag) when `pytest.ini`'s `addopts` auto-applies `--cov`. Coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`) and the maintainer's job.

If a worker believes coverage data is necessary to resolve a finding, the answer is to add the missing test that pins the consolidated behavior — not to run coverage to discover what is missing.

## Final test-run gate

After every finding is `- [x]` or removed, Worker 0 spawns Worker 1 once more for the final test-run gate. Worker 1 runs, in order:

1. `uv run pytest --no-cov` — full sweep across all three test trees. The explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov`. Do not inspect line coverage.
2. `uv run python examples/fakeshop/manage.py check` — Django's system check.
3. `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — confirms model state is migration-consistent.
4. Lint / format / diff gate, in order:
   - `uv run ruff format --check .` (read-only; no `--fix`)
   - `uv run ruff check .` (read-only; no `--fix`)
   - `git diff --check` (whitespace and conflict-marker check)

Worker 1 appends a `## Final test-run gate` section at the end of the plan, recording each command's pass/fail. Failures block closeout; the failing item is routed back through the owning finding's implementation / verification loop. If a failure surfaces something none of the findings own (e.g. a baseline regression that existed before the cycle), Worker 1 escalates to Worker 0, who escalates to the maintainer.

## Closeout

When every finding is `- [x]` or removed and the final test-run gate is `pass` end-to-end:

1. Worker 0 scans the DRY-cycle commit diffs (using the maintainer-provided commit range).
2. Worker 0 reads all three worker-memory files (one-time read at closeout) to surface patterns the workers themselves noticed across the cycle.
3. Worker 0 identifies recurring consolidation patterns, classes of false positive worth pre-flagging, and workflow stumbling blocks.
4. Worker 0 provides a brief retrospective to the maintainer.
5. After maintainer approval, Worker 0 updates `docs/dry/DRY.md` or the worker role files with general retrospective notes — describing recurring patterns and workflow improvements **without naming specific already-shipped fixes**.
6. Worker 0 leaves `docs/dry/worker-memory/` on disk. The directory is gitignored and persists across cycles; the next Worker 0 re-seeds the memory files at plan-creation time. The tracked permanent record remains the `dry-<0_0_X>.md` plan and the source/test changes — not the scratch contents.
7. The maintainer commits the updated `docs/dry/` workflow docs along with the now-completed `docs/dry/dry-<0_0_X>.md` plan to finish the DRY cycle.

## Spec / artifact reconciliation

If a finding's triage reveals that the source artifact (`bld-*.md` or `rev-*.md`) overstated or understated the duplication, the DRY workflow does NOT mutate that artifact — the build / review cycle that produced it is closed and its artifacts are the historical record. Worker 1 captures the reconciliation in the Triage sub-bullet so the finding's disposition is auditable.

If a finding's implementation surfaces a deeper architectural question that warrants a new spec, Worker 1 records it in the Triage sub-bullet (or in `Notes for maintainer` if larger) and Worker 0 escalates. Do not expand DRY-cycle scope to a full feature build; spawn a separate spec cycle if the work warrants it.
