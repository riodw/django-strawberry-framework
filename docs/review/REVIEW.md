# Package review workflow

Reusable process for reviewing every file under `django_strawberry_framework/`. A specific run is tracked in a versioned plan file (`docs/review/review-<0_0_X>.md`). Per-worker operational details live in `worker-{0,1,2,3}.md`; this doc is the canonical workflow spec.

!!IMPORTANT!!
Begin by reading README.md and docs/README.md and docs/TREE.md and docs/GLOSSARY.md and GOAL.md

!!IMPORTANT — DRY FIRST!!
Every review pass, fix, and verification must answer: **is the change moving the package toward the maximally DRY shape that stays readable?** Duplicated logic, parallel data flows, near-copies, and repeated string/key/tuple literals are review-time defects. Worker 1 flags DRY opportunities; Worker 2 implements them like any other finding; Worker 3 enforces DRY before accepting.

Worker docs:

- [Worker 0: review coordinator](worker-0.md)
- [Worker 1: file and folder reviewer](worker-1.md)
- [Worker 2: fix implementer](worker-2.md)
- [Worker 3: fix verifier](worker-3.md)

Tracked under `docs/review/`: `REVIEW.md`, `worker-*.md`, `review-*.md`, every `rev-*.md`. Untracked scratch: `docs/shadow/`, `docs/review/worker-memory/`, `docs/review/temp-tests/`. `AGENTS.md` and `START.md` apply during review runs. Only the maintainer commits.

## Required reading per worker

| Document | W0 | W1 | W2 | W3 |
|---|---|---|---|---|
| `AGENTS.md` | yes | yes | yes | yes |
| `docs/review/REVIEW.md` | yes | yes | — | — |
| `docs/review/worker-N.md` (own) | yes | yes | yes | yes |
| `pyproject.toml` | plan + closeout | — | — | — |
| `django_strawberry_framework/__init__.py` | plan + closeout | — | — | — |
| `CHANGELOG.md` | closeout only | — | when authorized | — (use `git diff -- CHANGELOG.md`) |
| active `docs/review/review-<0_0_X>.md` | yes (owns) | yes | — | yes (marks checkbox) |
| current `docs/review/rev-*.md` | read-only | yes (owns) | yes (writes fix sections) | yes (writes verification) |
| sibling `docs/review/rev-*.md` | — | folder/project pass | — | — |
| `docs/review/worker-memory/worker-N.md` (own) | yes | yes | yes | yes |
| target source/tests | — | yes (read-only) | yes (writes) | yes (read-only) |
| Worker 2's diff | — | — | — | yes |

Workers 2 and 3 do **not** read `REVIEW.md` — their role files are self-contained references. Keep `worker-2.md` / `worker-3.md` in sync with REVIEW.md when editing either.

## Versioned review plan

Worker 0 reads `pyproject.toml` and `django_strawberry_framework/__init__.py`; versions must match. Path: `docs/review/review-<release-underscored>.md` (e.g. `0.0.6` → `review-0_0_6.md`). If the plan already exists, stop; do not overwrite. If versions differ, record the mismatch in the plan before any review starts.

At plan creation, Worker 0 clears `docs/shadow/`, `docs/review/worker-memory/`, and `docs/review/temp-tests/` (never recursively wipe `docs/review/` itself — permanent artifacts live there).

## Review scope

Tracked **`.py`** source files under `django_strawberry_framework/`, with two exclusions:

- Non-`.py` files (e.g. `py.typed`) — packaging config, not per-file review.
- `__init__.py` files — covered in the folder pass (subpackages) or project pass (top-level).

Order: folder-by-folder, one file at a time. After all in-scope files in a folder, one folder pass. After all folder passes, one project-level pass. Finally the test-run gate.

## Required plan structure

Plan header includes release version, source root, date created, the one-file-at-a-time rule, the DRY-first rule, and a full artifact list. Each checklist item names its exact `rev-*.md` artifact.

```text
# Package review plan: 0.0.6

Source root: `django_strawberry_framework/`
Review rule: one file or folder-summary pass at a time.
DRY rule: every `rev-*.md` artifact must include a `## DRY analysis` section before merging.

## Artifact list

- `docs/review/rev-conf.md`
- `docs/review/rev-optimizer__field_meta.md`
- `docs/review/rev-optimizer.md`
- `docs/review/rev-django_strawberry_framework.md`
- `docs/review/rev-final.md`

## Checklist

- `django_strawberry_framework/`
  - [ ] `django_strawberry_framework/conf.py` -> `docs/review/rev-conf.md`
  - `django_strawberry_framework/optimizer/`
    - [ ] `django_strawberry_framework/optimizer/field_meta.py` -> `docs/review/rev-optimizer__field_meta.md`
    - [ ] folder pass: `django_strawberry_framework/optimizer/` -> `docs/review/rev-optimizer.md`
  - [ ] project-level pass: `django_strawberry_framework/` -> `docs/review/rev-django_strawberry_framework.md`
- [ ] final test-run gate: `uv run pytest` -> `docs/review/rev-final.md`
```

## Review artifact naming

- Start with `docs/review/rev-`.
- Use the path relative to `django_strawberry_framework/`.
- Replace `/` with `__`.
- Drop the `.py` suffix.
- End with `.md`.

Examples: `conf.py` → `rev-conf.md`; `optimizer/walker.py` → `rev-optimizer__walker.md`; folder pass for `optimizer/` → `rev-optimizer.md`; project pass → `rev-django_strawberry_framework.md`.

## Review artifact template

Every `docs/review/rev-<folder__file_name>.md` uses this structure. The artifact is the inter-worker contract.

````text
# Review: `django_strawberry_framework/optimizer/walker.py`

Status: under-review | fix-implemented | revision-needed | verified

## DRY analysis

Actionable DRY consolidation candidates only. Each top-level bullet is one opportunity a future DRY cycle could pick up — act-now or defer-with-trigger. The DRY-cycle export script (`docs/dry/export_dry_review.py`) extracts every top-level bullet here as a finding, so non-actionable bullets become noise.

Each bullet must:

- name the consolidation shape (helper signature, shared dataclass, named constant, or specific duplication to remove)
- cite the call sites involved (`path/file.py:NN-MM`)
- state whether to act now OR defer with an explicit trigger condition (e.g. "Defer until a third walker lands; ...")

If no real opportunities exist, write a single bullet `- None — <one sentence why the current factoring is correct>`. Do NOT include recap bullets like "Existing patterns reused" or "No new helpers needed" here — that audit trail belongs in `## What looks solid` under `### DRY recap`. Silence on DRY is not acceptance.

## High:

### Issue name

Issue summary, why it matters, recommended change.

```django_strawberry_framework/optimizer/walker.py:02:08
Relevant excerpt or pseudo-diff context.
```

## Medium:

### Issue name

Issue summary, why it matters, recommended change.

## Low:

### Issue name

Issue summary, why it matters, recommended change.

## What looks solid

Positive audit trail, split into two H3 subsections (exact headings, no variation):

### DRY recap

- **Existing patterns reused.** Which canonical helpers the file already reuses; cite `path/file.py:NN-MM`.
- **New helpers considered.** Candidates evaluated and rejected (or deferred without trigger conditions); state why.
- **Duplication risk in the current file.** Repeated literals / near-copies that are intentional sibling design; state why correct.

Drop a bullet if its category is genuinely empty rather than writing "None." — recap is audit trail, not a checklist.

### Other positives

- Design choices, test discipline, error-handling shapes, etc.

### Summary

Worker 1's short summary (one paragraph).

---

## Fix report (Worker 2)

### Files touched
- `path/to/file.py:NN-MM` — what changed and why

### Tests added or updated
- `tests/path/test_x.py::test_name` — what it pins

### Validation run
- `uv run ruff format .` — pass/no-changes
- `uv run ruff check --fix .` — pass/no-changes
- Focused tests if applicable

### Notes for Worker 3
Shadow file path if used; false-premise rejections with contradicting evidence; deferred findings.

---

## Verification (Worker 3)

### Logic verification outcome
Every High/Medium/Low: addressed, or intentionally rejected with **contradicting evidence cited** (test name, file/line). Bare "rejected" is grounds for `revision-needed`.

### DRY findings disposition
How the DRY analysis items were resolved or carried forward.

### Temp test verification
- Files used (cite paths under `docs/review/temp-tests/<scope>/`).
- Disposition: promoted, deleted, or flagged Medium for promotion.

### Verification outcome
One of:
- `logic accepted; awaiting comment pass` — interim; `Status:` does NOT advance.
- `comments accepted; awaiting changelog disposition` — interim.
- `cycle accepted; verified` — terminal; sets `Status: verified` and marks the checklist box.
- `revision-needed` — terminal; sets `Status: revision-needed`.

---

## Comment/docstring pass

Worker 2 fills after Worker 3 records `logic accepted; awaiting comment pass`. Ends with `Status: fix-implemented`.

---

## Changelog disposition

Worker 2 records one of three states (per `worker-2.md` "Changelog dicta"):

- **Not warranted** — internal-only edits; cite AGENTS.md + plan silence.
- **Warranted and edited** — only when explicitly authorized; record what was added.
- **Warranted but deferred to maintainer** — preserve maintainer-ready entry text verbatim.

---

## Iteration log

Worker 2 re-pass: append `## Fix report (Worker 2, pass <N>)`. Worker 3 re-verify: append `## Verification (Worker 3, pass <N>)`. Append-only.
````

If a severity has no issues, keep the heading and write `None.` Do not include speculative defects. If a concern needs package-wide context, name it as a folder-pass or project-pass follow-up rather than a local defect.

## Artifact `Status:` legend

Ownership:

- `under-review` — Worker 1 sets when creating the artifact. Never starts empty.
- `fix-implemented` — **Worker 2** sets at the end of every pass (logic, comment, changelog, no-op).
- `revision-needed` — Worker 3 sets on rejection (or Worker 1 in the cycle-closing re-check).
- `verified` — Worker 3 sets terminally; Worker 3 marks the checkbox. Exception: `rev-final.md` is set by Worker 1 and the checkbox is marked by Worker 0.

Worker 0 never writes `Status:`; it reads to drive dispatch.

## Subagent dispatch

Workers 1, 2, and 3 each run as a fresh subagent invocation per cycle item. Worker 0 stays in the main thread as orchestrator. The split is non-waivable — combining Workers 2 and 3 would let the agent that wrote the fix approve it.

For each unchecked checklist item, Worker 0 reads `Status:` and dispatches:

- no artifact → spawn **Worker 1** → produces artifact with `under-review`
- `under-review` → spawn **Worker 2** → implements; sets `fix-implemented`
- `fix-implemented` → spawn **Worker 3** → verifies; sets `verified` / `revision-needed` / interim `awaiting X`
- `revision-needed` → re-spawn Worker 2
- interim `awaiting comment pass` / `awaiting changelog disposition` → spawn Worker 2 for the next sub-pass

Each subagent gets the docs marked `yes` for its column in the matrix above. Subagent prompts must forbid reading other workers' memory files. The artifact and the diff are the only inter-worker contract; subagents do not message each other directly.

After a cycle item reaches `verified`:

1. Maintainer is notified.
2. **Worker 1 re-check** on the diff (skip when the cycle produced no source/test diff; confirm via `git diff --stat -- django_strawberry_framework/ tests/ CHANGELOG.md`).
3. If clean, maintainer commits source + artifact + checklist update.

Autonomous-mode override: when the maintainer explicitly authorizes Worker 0 to run multiple cycles without per-cycle pauses, Worker 0 still runs the Worker 1 re-check for source-bearing cycles and appends a one-line note to `worker-memory/worker-0.md` per closure; the maintainer is notified at autonomous-mode boundaries only.

## Worker memory

Private scratch under `docs/review/worker-memory/worker-N.md` (gitignored). Persists across cycles within a release. A worker reads only its own file; Worker 0 reads all four once at closeout for the retrospective. Append-only; consolidate when **approaches ~45 lines**. Worker 0 deletes at closeout.

## Severity definitions

**High:** confirmed correctness bugs; API contract breakage; security or data-isolation risk; Django ORM returning wrong data; cache/request-state mutation; errors that crash normal consumer usage.

**Medium:** performance / N+1 / excessive DB work; redundant implementation needing consolidation; unclear ownership between modules; brittle edge-case behavior; missing tests for important branches.

**Low:** small maintainability issues; naming clarity; minor typing/API polish; localized simplification; stale-but-harmless comments/docstrings.

### Deferral idioms

For Lows correct today but actionable under a future condition, use **trigger-condition phrasing** and quote the trigger verbatim:

- ✓ "Defer until a third walker lands; then fold all three through a shared visitor."
- ✓ "Defer until the planner gains an 11th argument; the dataclass collapses the call sites at that point."
- ✗ "Defer; cosmetic." (the next reviewer cannot tell when to revisit)

## Review focus

### Logic first

- correctness and edge cases
- public API behavior and backward compatibility
- exception types and error messages
- Django ORM correctness, `select_related`, `prefetch_related`, `Prefetch`, `only`
- N+1 behavior and optimizer correctness
- async/sync behavior
- cache keys, mutability, request-scope state, thread/process safety
- performance and memory use
- redundancy and DRY opportunities
- module responsibility (Two Scoops of Django structure)
- import-time side effects and circular-import risk
- typing quality and runtime annotation behavior
- tests needed to prove a recommended change

### Comment/docstring second

After logic is approved:

- stale comments; comments restating obvious code
- missing comments for non-obvious Django/optimizer behavior
- docstrings promising behavior the implementation does not provide
- obsolete TODOs / deleted-spec references
- public API docstrings needing consumer-visible constraints

Do not polish comments before logic is correct.

## Static review helper: `scripts/review_inspect.py`

Parses target as text and AST only; safe on Django-touching files. Worker 0 typically runs `--all` at plan time so an overview exists for every in-scope file under `docs/shadow/`.

### When to run

Worker 1 **must run** the helper before reviewing:

- any `.py` file ≥150 source lines
- any `.py` file under `optimizer/` or `types/`, regardless of length
- every in-scope `.py` file in the folder being summarized (folder passes need an overview for every sibling, including the folder's `__init__.py`)

Worker 1 **may skip** for pure-class-definition modules (`exceptions.py`) or any file destined for a skip artifact; record the skip and reason in `## What looks solid`.

Worker 2 must re-read the overview Worker 1 produced before any non-trivial fix. If Worker 2 re-runs the helper, pass the shadow path to Worker 3 via `## Notes for Worker 3`.

### How to run

```shell
python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
```

Refresh all at once:

```shell
python scripts/review_inspect.py --all --output-dir docs/shadow
```

Every review-cycle invocation must pass `--output-dir docs/shadow`. Useful flags: `--outline-only`, `--stdout`, `--marker NAME`, `--long-function-lines N`, `--long-function-branches N`, `--first-party-prefix PREFIX`, `--literal-min-length N`.

### Output files

Two files land under `docs/shadow/<stable-stem>`:

- `<stem>.stripped.py` — `#` comments removed; string-literal tokens (including docstrings) replaced by `...`. With `--strip-docstrings`, docstring statements removed entirely.
- `<stem>.overview.md` — static AST overview.

`docs/shadow/` is gitignored. Tracked artifact = the `rev-*.md` Worker 1 produces.

### Reading the overview

| Section | Reviewer use |
|---|---|
| **Quick scan** | Count summary; decides which detailed sections need attention. |
| **Imports** | Dependency graph (local / first-party / django / strawberry / standard). New cross-folder imports are usually structural. |
| **Symbols** | Fast table of contents. |
| **Control-flow hotspots** | Functions over 40 lines or 8 branches; apply Medium-tier complexity attention. Missing branch tests → Medium finding. |
| **Django / ORM markers** | Executable-code matches for `QuerySet`, `select_related`, `prefetch_related`, `Prefetch`, `only`, `_meta`, `get_queryset`, `_prefetched_objects_cache`, `fields_cache`, `DjangoType`, `OptimizationPlan`, `OptimizerHint`, `dst_optimizer_plan`, `_optimizer_field_map`. Walk every entry — each needs justification or a finding. |
| **Calls of interest** | Reflective-access audit (every `getattr` / `hasattr` / `isinstance` / `setattr` and container-coercions). |
| **Comments and docstrings** | Docstrings (comment-pass coverage); TODO anchor check (per AGENTS.md); inventory (spot stale/restating). |
| **Repeated string literals** | DRY signal. Per-file: string-keyed dispatch. Folder pass: cross-file duplication. Docstrings excluded. |

### Folder-pass repeated-literal check

When writing a folder artifact:

1. Confirm the helper ran on every `.py` file in the folder (overviews exist under `docs/shadow/`).
2. Compare **Repeated string literals** across siblings — a literal in two+ files is a folder-level DRY candidate.
3. Compare **Imports** across siblings to confirm one-way dependency direction.

### Shadow line numbers are NOT canonical

The shadow file's line numbers do not match the original source. Cite **original source-file line numbers** in artifacts, Worker 3 feedback, and source edits. Never edit or commit the shadow file.

## Folder and project passes

After every file in a folder is complete, Worker 1 reads every sibling `rev-*.md` for the folder and creates the folder artifact. Check: duplicated helpers, naming/error-handling drift, repeated ORM/queryset patterns, misplaced responsibilities, export issues, circular-import risk, comment consistency. Same High/Medium/Low template; do not become a whole-project review.

After all folder passes, the project pass produces `rev-django_strawberry_framework.md` and covers the top-level `__init__.py`. Findings go in `rev-django_strawberry_framework.md`, never in the plan file. Per-file artifacts forward package-wide concerns by citing `rev-django_strawberry_framework.md` by path in the relevant Low/Medium body; the project-pass spawn collects these forwards.

## No-op / skip / consolidated single-spawn cycles

Four shapes collapse to a single Worker 2 spawn + single Worker 3 verification:

1. **No-findings file** — all severities `None.`; Worker 2 records a no-op `Fix report` plus the two ruff runs.
2. **Skip artifact** — pure-class-definition module; `What looks solid` explains the skip.
3. **No-findings folder/project pass** — same shape as #1.
4. **All-Lows-forward-looking or DRY-equivalent** — every Low is explicitly forward-looking, OR every edit is a DRY delegation against a canonical helper (semantics preserved). Worker 2 records `Fix report`, `Comment/docstring pass`, AND `Changelog disposition` together; Worker 3 verifies once and writes `cycle accepted; verified`.

Do NOT collapse when any High or substantive Medium requires real behavior change, or when two dispositions interact. Full detail: `worker-2.md` "Consolidated single-spawn pass".

## Temp tests

Worker 3 may create files under `docs/review/temp-tests/<scope>/` (gitignored; NOT permanent). If a temp test catches a real bug, flag it as Medium/High so Worker 2 promotes it to the permanent suite under the correct `AGENTS.md` test tree. Worker 0 deletes the directory at closeout.

## Final test-run gate

After every per-file, folder, and project checkbox is `- [x]`, Worker 0 spawns Worker 1 for `docs/review/rev-final.md`:

- Run `uv run pytest` once (full sweep across all three test trees per `AGENTS.md`).
- **Do NOT inspect line coverage** — coverage gating belongs to CI and the maintainer.
- Coverage-shortfall pytest exit codes are NOT test failures — parse the `=== N passed ... ===` summary line; record coverage notes as follow-up signals only.
- Worker 1 sets `Status: verified` on `rev-final.md` when tests pass. **Worker 0** marks the final checklist box (the only box Worker 0 marks directly).
- On failure, re-loop through the owning cycle item.

Worker 2 and Worker 3 are not involved in this gate.

## Closeout

Owned by Worker 0 (full procedure: `worker-0.md` "Closeout job"). Worker 0 reads all four worker-memory files (one-time read), provides a brief retrospective, and after maintainer approval applies general retrospective edits to `REVIEW.md` or `worker-*.md` — recurring patterns and workflow improvements only, never names of specific already-fixed defects. Worker 0 then deletes `docs/shadow/`, `docs/review/worker-memory/`, and `docs/review/temp-tests/`. The tracked permanent record is the `rev-*.md` artifacts, the plan, and the source/test changes.
