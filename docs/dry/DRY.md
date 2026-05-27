# DRY consolidation workflow

This document defines the reusable process for **acting on DRY recommendations** left behind by a closed build or review cycle. It does not track a specific DRY pass — a pass is tracked in `docs/dry/dry-<0_0_X>.md`.

The DRY workflow runs **after** a build (`docs/builder/BUILD.md`) or review (`docs/review/REVIEW.md`) cycle closes. Each closed cycle emits per-artifact DRY analysis sections describing existing patterns reused, helper opportunities, and duplication risks. This workflow gathers those into one consolidated plan and dispatches workers to dispose of each opportunity — implement it, confirm it has already been addressed, or remove it as a false positive.

The standing worker instructions live beside this overview:

- [Worker 0: dispatcher](worker-0.md)
- [Worker 1: investigator + implementer](worker-1.md)
- [Worker 2: scaffolder + verifier + tester](worker-2.md)

There is no Worker 3.

Permanent files under `docs/dry/` are tracked: `DRY.md`, `worker-*.md`, `export_dry_review.py`, and every `dry-<0_0_X>.md` plan file.

`AGENTS.md` and `START.md` still apply during DRY runs. This workflow adds the per-worker artifact discipline on top.

Only the maintainer commits. Workers never commit, even if asked.

## Required reading per worker

Every worker reads the standing project docs and its own role file before acting. This matrix is the single source of truth; the worker role files reference it.

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
| active `docs/dry/dry-<0_0_X>.md` | yes (whole file: state inspection + finding-section computation) | yes (only the finding section W0 names) | yes (only the finding section W0 names) |
| source artifacts (`bld-*.md` / `rev-*.md`) | — | yes (read-only) | yes (read-only) |
| relevant source / tests | — | yes (writes during Implementation) | yes (writes during TODO scaffold + Verification) |
| finding-scoped diff (`git diff $FINDING_BASELINE -- …`) | — | yes (Implementation re-pass) | yes (Verification pass) |

**Worker 0 does NOT read source code, tests, or source artifacts during the cycle.** Worker 0's window into the work is `dry-<0_0_X>.md`. The plan artifact is the inter-worker contract.

There is no worker-memory in this workflow. All cross-pass carry-forward happens through sub-bullets under the active finding in `dry-<0_0_X>.md`.

## Pre-flight checks

Before Worker 0 generates the plan:

1. **Source cycle is closed.** The build / review cycle whose findings drive this pass must already be `final-accepted` / `verified` end-to-end.
2. **Working tree is clean OR baseline is explicit.** Run `git status --short`. If unrelated uncommitted changes exist, commit them, set them aside, or explicitly include them in the baseline.
3. **`docs/dry/export_dry_review.py` runs.** Smoke invocation: `uv run python docs/dry/export_dry_review.py --help`. If broken, escalate.
4. **Planned plan path is free.** `docs/dry/dry-<0_0_X>.md` must not already exist.

Record the outcome in the plan file's preamble (`Pre-flight: passed; baseline: clean` or `Pre-flight: <issue>, resolved by <action>`).

## Generating the plan

Worker 0 runs:

```shell
uv run python docs/dry/export_dry_review.py --source-dir <docs/builder|docs/review>
```

The script:

- **infers the target release** by scanning `--source-dir` for a `*-X_X_X.md` file. Exits with an error if zero or multiple distinct versions are present; in the multi-version case Worker 0 must pass `--target-release <X.X.X>` explicitly.
- scans every `*.md` file in `--source-dir`,
- finds each file's `DRY analysis` heading (any ATX level) and extracts the content beneath it up to the next heading at the same or higher level,
- is **code-fence-aware** — headings inside fenced code blocks are ignored,
- prefixes every top-level bullet in the extracted content with `- [ ]` so Worker 0 can tick it,
- writes `docs/dry/dry-<release-underscored>.md` with a plan header + a `## Findings` section.

## Plan structure

The generated `dry-<0_0_X>.md` file begins with target release, source directory, generation date, and the one-line workflow rule. Then `## Findings`, with one `## <Artifact title>` per source artifact. Under each artifact, every top-level DRY bullet is prefixed `- [ ]`.

Each `- [ ]` is a **finding**. As the cycle progresses, workers append sub-bullets under the finding with their work product. When the finding is complete or skipped, Worker 0 ticks `- [x]`. **The bullet text stays visible whether the finding was completed, skipped, or judged not real** — `- [x]` is the universal closed marker and the sub-bullets explain why.

Worker 1 may minimally correct a finding's `- [ ]` text in place if it cited stale symbol names or out-of-date substring anchors. Worker 0 may correct an obvious typo. Otherwise the script-generated structure stays as-is.

## Dispatch mode and baseline

Default mode is **autonomous** — Worker 0 continues finding-to-finding, notifying the maintainer only at run boundaries (start, end, fatal blockers, two consecutive `revision-needed` outcomes on the same finding). Maintainer-pause mode is opt-in via "one finding at a time" / "pause after each finding" / a single named finding in the dispatch prompt.

### Per-finding baseline

```shell
FINDING_BASELINE=$(git stash create)  # at start of each finding; empty SHA if working tree clean
```

Worker 0 captures the baseline before dispatching Worker 1 Investigation (step B) and passes the SHA to every subagent dispatch for that finding. Finding-scoped diffs use `git diff "$FINDING_BASELINE" -- …` (empty SHA → use `HEAD`). The baseline isolates each finding's diff from prior findings' accumulated changes — the maintainer commits once at cycle close, so the working tree accumulates across findings. Stash-create commits don't appear on the stash stack; Git reflog-GCs them.

## Finding lifecycle

Findings are processed one at a time, in declared order. The per-finding loop has up to six passes:

```
A. Worker 0 pre-triage              (no subagent)
B. Worker 1 Investigation           (subagent)
C. Worker 2 TODO scaffold           (subagent)  ─┐
D. Worker 1 Implementation          (subagent)   ├─ skipped if B returns
E. Worker 2 Verification + test     (subagent)   │  already-addressed / not-real
F. Worker 0 ticks `- [x]`           (no subagent)─┘
```

### A. Worker-0 pre-triage

Worker 0 reads the finding's `- [ ]` text in `dry-<0_0_X>.md` (no source code). Worker 0 may pre-triage as `- [x]` **only if the bullet text itself contains explicit "no opportunity" / "defer to later cycle" language that does not require code inspection to verify**. Common shapes that qualify:

- Opens with **"None —"** (the source-artifact recap of "no opportunity here").
- Opens with **"Defer until …"** with the trigger condition stated as unfired in the bullet text.
- States the finding is **"already tracked elsewhere at <other artifact>"**.

If pre-triaged, Worker 0 appends:

```
  - **Pre-triage (Worker 0):** Skipped — <one line: quoted reason from the bullet>.
```

…and ticks `- [x]`. Advance.

Otherwise, dispatch Worker 1 (step B). **Any finding whose bullet asserts a concrete extraction or behavior change in current source must be dispatched, even if it looks small.** Worker 0 does not investigate.

### B. Worker-1 Investigation

Worker 0 re-reads the plan, locates the active finding's section, and captures `FINDING_BASELINE=$(git stash create)`. Dispatch a fresh Worker 1 subagent with the finding-section locator, baseline SHA, and role.

Worker 1:

- Reads the named finding section of the plan, the source artifact named in the `_Source:_` line, and the cited source / tests.
- Decides disposition:
  - **Real opportunity** — appends an Investigation sub-bullet with a one-paragraph summary AND a pseudo-code block showing the intended shape; may minimally correct the `- [ ]` text if stale. Returns `real`.
  - **Already addressed** — appends an Investigation sub-bullet citing the resolution. Returns `already-addressed`.
  - **Not a real opportunity** — appends an Investigation sub-bullet with a one-line reason. Returns `not-real`.

### C. Worker-2 TODO scaffold

Only runs when B returns `real`. If B returned `already-addressed` or `not-real`, Worker 0 ticks `- [x]` and advances.

Worker 0 re-reads the plan, relocates the finding section, dispatches a fresh Worker 2 subagent.

Worker 2:

- Reads the named finding section + source artifact + cited source / tests.
- Adds `# TODO(dry-<0_0_X>): <one-line>` comments in source at every site that will change in the Implementation pass. The TODO text names the helper / consolidation shape from Worker 1's pseudo-code.
- Appends a TODO scaffold sub-bullet listing every TODO added, plus any corrections to Worker 1's pseudo-code or call-site list.
- May minimally edit Worker 1's pseudo-code block in the Investigation sub-bullet if scaffold-time inspection finds a concrete error in it (e.g., wrong signature). The edit is marked `Pseudo-code (corrected by Worker 2)`. Larger drift goes in the TODO scaffold sub-bullet as a deviation note.
- Does NOT run ruff, does NOT run tests. The TODOs are scaffolding; the Implementation pass owns formatting and lint.

### D. Worker-1 Implementation

Worker 0 re-reads the plan, relocates the finding section, dispatches a fresh Worker 1 subagent.

Worker 1:

- Reads the named finding section (now containing Investigation + TODO scaffold) + cited source (now containing `# TODO(dry-<0_0_X>):` comments).
- Replaces each TODO with the actual consolidation. Adds / extends the helper. Updates each call site. **Removes every `# TODO(dry-<0_0_X>):` comment as the corresponding edit lands.**
- Runs `uv run ruff format .` then `uv run ruff check --fix .`. Reverts any tool-induced drift in files outside the finding's scope via `git checkout -- <path>`.
- Appends an Implementation sub-bullet listing files touched, the helper signature, every call site updated, and ruff results.

### E. Worker-2 Verification + test

Worker 0 re-reads the plan, relocates the finding section, dispatches a fresh Worker 2 subagent.

Worker 2:

- Reads the named finding section + Worker 1's diff + cited source / tests.
- Confirms the helper lives where the Investigation prescribed, every cited call site routes through it, **no `# TODO(dry-<0_0_X>):` comments remain**, and tests pin the consolidated behavior.
- Runs focused tests with `--no-cov` (per the coverage gate rule below).
- Adds a permanent test pinning the consolidation if one is missing.
- Returns `verified` (appending a Verification sub-bullet citing the helper location, call-site count, and test) or `revision-needed` (appending a Verification sub-bullet with specific feedback).

### F. Worker-0 closes the finding

- On `verified`: tick `- [x]`. Advance.
- On `revision-needed`: re-dispatch Worker 1 Implementation (step D) — the new Worker 1 spawn writes `Implementation (Worker 1, pass N):` rather than editing the prior one. After re-implementation, re-dispatch Worker 2 Verification (step E).

Only Worker 0 ticks `- [x]`. Workers 1 and 2 NEVER mark a finding closed.

## Finding-section delegation

Each subagent dispatch from Worker 0 names the active finding's section in `dry-<0_0_X>.md` by a substring anchor unique to that finding's `- [ ]` bullet (e.g., `the bullet under «source artifact» starting with «first 8-15 words of the finding text»`). The subagent uses `Grep` to locate the bullet, then `Read` to load only that section of the plan plus its sub-bullets — alongside the standing required reading and the source / artifact references for its pass. This keeps subagent context narrow as the plan grows with sub-bullets. Per the per-cycle scratchpad exemption in `AGENTS.md` #"Source references in docs and code comments", Worker 0 *may* additionally pass a line offset / limit it computed locally as an optimization, but the substring anchor is the authoritative locator — if the offset has drifted, the substring still finds the right bullet.

**Worker 0 re-reads the plan to relocate the active finding section before EVERY dispatch** because edits from prior passes shift offsets. The section starts at the `- [ ]` (or `- [x]`) bullet line and runs to the line before the next bullet at the same indent OR the next `##`/`###` heading.

If a subagent's prompt names a stale locator (the plan changed mid-pass for reasons outside Worker 0's control), the subagent must stop and report rather than guess.

## Roles, in one sentence

- **Worker 0** (main thread): dispatcher and state manager. Owns the `- [x]` checkboxes. Owns finding-section computation. Does not read source code.
- **Worker 1** (subagent): investigator and implementer. Decides whether a finding is real, writes the summary + pseudo-code, later replaces TODOs with actual code.
- **Worker 2** (subagent): scaffolder, verifier, and tester. Adds TODO comments at the call sites, later reviews the diff and runs / adds tests.

## Subagent dispatch and isolation

Workers 1 and 2 each run as **separate subagent invocations per pass**. The worker that verifies a fix has no in-context memory of the worker that wrote it.

A single agent role-playing every worker can convince itself a consolidation is sufficient because it remembers _why_ it implemented it that way. Subagent isolation removes that path: the verifying Worker 2 sees only the sub-bullet trail and the diff.

Each subagent's prompt must include: standing project docs (`AGENTS.md`, `START.md`, `DRY.md`, the worker's own role file), the active plan path, the **finding section** of the active finding, the worker's role for this pass (Investigation / TODO scaffold / Implementation / Verification / final gate), and any pass-specific source-artifact citation.

No cross-worker chatter. All inter-worker information flows through the plan artifact and the finding-scoped diff.

### Recovery from interrupted subagent runs

If a subagent fails mid-pass (transient API errors, network failures, time-outs), Worker 0 dispatches a fresh subagent of the same role with explicit "pick up where the prior pass left off" context. The new subagent's prompt names the partial sub-bullet (if any), the finding-scoped diff (`git diff "$FINDING_BASELINE" -- …`), and the active finding section.

The recovery finishes the original pass's sub-bullet; it does NOT start a "pass N+1" sub-bullet.

If the on-disk diff is unsalvageable, Worker 0 escalates to the maintainer rather than guessing at rollback.

## Coverage is the maintainer's gate, not a worker's tool

Workers do not run `pytest` with coverage flags. `--cov=...`, `--cov-report=...`, `--cov-config=...`, and equivalents are forbidden in every DRY pass — Investigation, TODO scaffold, Implementation, Verification, and the final test-run gate. `--no-cov` is the only permitted coverage-shaped flag (required because `pytest.ini`'s `addopts` auto-applies `--cov`). Coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`) and the maintainer's job.

If a worker believes coverage data is necessary to resolve a finding, the answer is to add the missing test that pins the consolidated behavior — not to run coverage to discover what is missing.

## Final test-run gate

After every finding is `- [x]`, Worker 0 spawns Worker 2 for the final test-run gate. Worker 2 runs, in order:

1. `uv run pytest --no-cov` — full sweep across all test trees.
2. `uv run python examples/fakeshop/manage.py check` — Django system check.
3. `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — migration consistency.
4. `uv run ruff format --check .` — read-only; no `--fix`.
5. `uv run ruff check .` — read-only; no `--fix`.
6. `git diff --check` — whitespace / conflict-marker check.

Worker 2 appends a `## Final test-run gate` section at the end of the plan recording each command's pass/fail. Failures block closeout; the failing item is routed back through the owning finding's loop (re-dispatch Worker 1 for that finding's Implementation, then Worker 2 for Verification). If no single finding owns the failure, escalate to the maintainer.

## Closeout

When every finding is `- [x]` and the final test-run gate is `pass` end-to-end:

1. Worker 0 reports the cycle complete to the maintainer.
2. The maintainer commits `docs/dry/dry-<0_0_X>.md` together with the cycle's source / test changes.

If the maintainer notices recurring patterns across the cycle worth encoding, they edit `DRY.md` or the worker role files directly. There is no separate retrospective artifact and no worker-memory to consolidate.

## Spec / artifact reconciliation

If a finding's Investigation reveals that the source artifact (`bld-*.md` or `rev-*.md`) overstated or understated the duplication, the DRY workflow does NOT mutate that artifact — the source cycle is closed and its artifacts are the historical record. Worker 1 captures the reconciliation in the Investigation sub-bullet so the disposition is auditable.

If a finding's Implementation surfaces a deeper architectural question that warrants a new spec, Worker 1 records it in the Investigation sub-bullet (or in `### Notes for maintainer` inside the sub-bullet if larger) and Worker 0 escalates. Do not expand DRY-cycle scope to a full feature build; spawn a separate spec cycle if the work warrants it.
