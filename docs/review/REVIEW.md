# Package review workflow

This document defines the reusable process for reviewing every file under `django_strawberry_framework/`. It does not track a specific review run. A review run is tracked in a versioned plan file under `docs/review/`.

The standing worker instructions live beside this overview:

- [Worker 0: review coordinator](worker-0.md)
- [Worker 1: file and folder reviewer](worker-1.md)
- [Worker 2: fix implementer](worker-2.md)
- [Worker 3: fix verifier](worker-3.md)

The per-release plan file and every per-file / per-folder / project-pass `rev-*.md` review artifact under `docs/review/` are committed to git and kept as the permanent record of the review cycle. They are not deleted at the end of the cycle. The only files under `docs/review/` that are not tracked are static-analysis shadow byproducts under `docs/review/shadow/`, which are gitignored.

`AGENTS.md` and `START.md` still apply during review runs. This review workflow adds the per-worker artifact discipline on top; it does not override standing validation, test-running, commit, or test-placement rules.

## Versioned review plan

Worker 0 creates the active review plan from these instructions and [Worker 0's role instructions](worker-0.md).

1. Read `pyproject.toml` and `django_strawberry_framework/__init__.py`.
2. Confirm both version values match.
3. Convert the release version from dots to underscores.
   - `0.0.3` becomes `0_0_3`.
4. Create `docs/review/review-<0_0_X>.md`.
   - For the current `0.0.3` release, create `docs/review/review-0_0_3.md`.
5. The plan file is the canonical checklist for the whole release review and is committed alongside the review-cycle source changes. It is kept in git as the permanent record of the cycle.

If the version values do not match, stop and record that mismatch in the plan before any file review starts.

## Review scope

The review covers tracked **`.py`** source files under `django_strawberry_framework/`, with two exclusions:

- **Non-Python files are out of scope.** Package marker files (e.g. `py.typed`), data files, and any other non-`.py` file are not reviewed and not listed in the plan checklist. Their behavior is governed by packaging configuration (`pyproject.toml`, `MANIFEST.in`), not by per-file logic review.
- **`__init__.py` files are out of scope.** They are typically thin re-export shims whose surface is more usefully reviewed at the folder pass (where the public-vs-private contract for the subpackage is set) than at the per-file level. Logic that lands in an `__init__.py` is reviewed as part of the folder pass for that subpackage.

The review is folder-by-folder and one file at a time within each folder.

Rules:

- Review only one file or one folder-summary pass at a time.
- Do not start the next file until the current file's review/fix/verification/commit cycle is complete.
- After all in-scope files in a folder are reviewed, perform one folder-level pass using the context gathered from those files. The folder pass also covers the folder's `__init__.py` (re-exports, public-vs-private contract, side-effect-free imports). Before that folder pass, Worker 1 must read every sibling `docs/review/rev-*.md` artifact for the folder.
- The folder-level pass should primarily look for DRY opportunities, duplicated logic, misplaced responsibilities, cross-file inconsistencies, and the subpackage's `__init__.py` re-export contract.
- After all files and folder passes are complete, perform one project-level pass over `django_strawberry_framework/` for DRY and structure opportunities that only become visible with full-package context. The project pass also covers the top-level `django_strawberry_framework/__init__.py` (the package's public-API surface).

## Required plan structure

The generated `docs/review/review-<0_0_X>.md` file must begin with:

- release version
- source root: `django_strawberry_framework/`
- date created
- a short copy of the one-file-at-a-time rule
- a list of every review artifact that will be created

Then it must include a tree-like checklist for the package. Every file and every folder-level pass must have:

- a checkbox
- the source path being reviewed
- the exact review artifact file to create

### Template shape:

```text
# Package review plan: 0.0.3

Source root: `django_strawberry_framework/`
Review rule: one file or folder-summary pass at a time.

## Artifact list

- `docs/review/rev-conf.md`
- `docs/review/rev-optimizer__field_meta.md`
- `docs/review/rev-optimizer.md`
- `docs/review/rev-django_strawberry_framework.md`

## Checklist

- `django_strawberry_framework/`
  - [ ] `django_strawberry_framework/conf.py` -> `docs/review/rev-conf.md`
  - `django_strawberry_framework/optimizer/`
    - [ ] `django_strawberry_framework/optimizer/field_meta.py` -> `docs/review/rev-optimizer__field_meta.md`
    - [ ] folder pass: `django_strawberry_framework/optimizer/` -> `docs/review/rev-optimizer.md`
  - [ ] project-level pass: `django_strawberry_framework/` -> `docs/review/rev-django_strawberry_framework.md`
```

Use the actual on-disk package tree when creating the plan. Do not invent files. Skip every non-`.py` file (e.g. `py.typed`) and every `__init__.py` — they are out of scope per the rules above; the subpackage `__init__.py` and the top-level package `__init__.py` are covered by the folder pass and the project pass respectively. Keep the checklist in review order.

## Review artifact naming

Per-file and per-folder review artifacts are tracked Markdown files under `docs/review/`. They are committed alongside the source changes they describe and form a permanent record of the review cycle.

Naming rules:

- Start with `docs/review/rev-`.
- Use the path relative to `django_strawberry_framework/`.
- Replace `/` with `__`.
- Drop the `.py` suffix.
- End with `.md`.

Examples:

- `django_strawberry_framework/conf.py` -> `docs/review/rev-conf.md`
- `django_strawberry_framework/registry.py` -> `docs/review/rev-registry.md`
- `django_strawberry_framework/optimizer/walker.py` -> `docs/review/rev-optimizer__walker.md`
- `django_strawberry_framework/types/base.py` -> `docs/review/rev-types__base.md`
- folder pass for `django_strawberry_framework/optimizer/` -> `docs/review/rev-optimizer.md`
- project-level pass for `django_strawberry_framework/` -> `docs/review/rev-django_strawberry_framework.md`

`__init__.py` files are out of scope as standalone artifacts; their re-export contract is reviewed inside the folder pass (or the project pass, for `django_strawberry_framework/__init__.py`). Non-`.py` files (e.g. `py.typed`) are out of scope entirely. The generated `docs/review/review-<0_0_X>.md` file must list every artifact before review work starts.

## Output rule for Worker 1

IMPORTANT: after each file or folder review, Worker 1's only output is the review artifact file.

Worker 1 must not:

- modify source code
- update comments
- update `CHANGELOG.md`
- mark the checklist item done
- produce a separate narrative response

Worker 1 creates exactly one `docs/review/rev-<folder__file_name>.md` file for the current file or folder pass, then stops. For low-surface `.py` files (e.g., a pure-class-definition module like `exceptions.py`), that artifact may be a skip artifact explaining why there is no review-worthy logic or comment surface. `__init__.py` files and non-`.py` files are out of scope for per-file artifacts entirely (see Review scope). Worker 1 still does not mark the checklist item done; Worker 3 or the maintainer handles the checkbox after accepting the skip artifact.

## Review artifact template

Every `docs/review/rev-<folder__file_name>.md` file must use this structure:

````text
# Review: `django_strawberry_framework/optimizer/walker.py`

## High:

### Issue name

Issue summary, why it matters, and the recommended change.

```django_strawberry_framework/optimizer/walker.py:02:08
Relevant excerpt or pseudo-diff context.
```

## Medium:

### Issue name

Issue summary, why it matters, and the recommended change.

```django_strawberry_framework/optimizer/walker.py:10:14
Relevant excerpt or pseudo-diff context.
```

## Low:

### Issue name

Issue summary, why it matters, and the recommended change.

```django_strawberry_framework/optimizer/walker.py:20:26
Relevant excerpt or pseudo-diff context.
```

## What looks solid

- List thing one.
- List thing two.

---

### Summary:

Add a short summary here.
````

If a severity has no issues, keep the heading and write `None.` under it. Do not include speculative issues. If a concern depends on package-wide context that is not yet available, put it in the summary as a follow-up for the folder or project-level pass rather than presenting it as a file-local defect.

## Severity definitions

High:

- confirmed correctness bugs
- API contract breakage
- security or data-isolation risk
- Django ORM behavior that can return wrong data
- cache/request-state mutation bugs
- errors that can crash normal consumer usage

Medium:

- likely performance problems
- N+1 risk
- excessive database work
- redundant implementation that should be consolidated
- unclear ownership between modules
- brittle edge-case behavior
- missing tests for important branches

Low:

- small maintainability issues
- naming clarity
- minor typing/API polish
- localized simplification
- comments or docstrings that are stale but not harmful

## What each review checks

### Logic review first

The first pass is a logic check, not a comment check.

Focus on:

- functional correctness and edge cases
- public API behavior and backward compatibility
- exception types and error messages
- Django ORM correctness, lazy evaluation, database routing, relation caches, `select_related`, `prefetch_related`, `Prefetch`, and `only`
- N+1 behavior and optimizer correctness
- async/sync behavior
- cache keys, mutability, request-scope state, and thread/process safety
- performance and memory use
- redundancy and DRY opportunities
- whether responsibilities belong in the current module
- import-time side effects and circular-import risk
- typing quality and runtime annotation behavior
- test coverage needed to prove the change
- Two Scoops of Django structure: small focused modules, explicit queryset boundaries, clear settings boundaries, minimal magic, reusable utilities only when genuinely shared, and code placed where future Django maintainers would expect it

### Static review helper: `scripts/review_inspect.py`

Worker 1 and Worker 2 both use the static helper. It parses the target as text and AST only — it never imports or executes the module — so it is safe to run on files that touch Django settings, the registry, or Strawberry type creation at import time.

#### When to run the helper

Worker 1 **must run** the helper before reviewing any of:

- Any `.py` file with at least 150 source lines.
- Any `.py` file under `django_strawberry_framework/optimizer/` or `django_strawberry_framework/types/`, regardless of length. These are the ORM-heavy and Strawberry-coupled subsystems where the marker and hotspot sections are load-bearing.
- Every in-scope `.py` file in the folder being summarized, before writing the folder-level artifact. The folder-pass repeated-literal and cross-file structural checks rely on having an overview for every sibling.

For the folder pass itself, the helper should also be run on the folder's `__init__.py` so its imports, repeated literals, and any hidden side-effects show up alongside the sibling overviews.

Worker 1 **may skip** the helper for:

- Pure-class-definition modules whose body is only `class` declarations with docstrings (e.g., `exceptions.py`). These will produce a skip artifact regardless.
- Any `.py` file where the per-file artifact will be a "no review-worthy logic" skip artifact.

When the helper is skipped, the `What looks solid` section of the artifact must say so explicitly with a short reason. (Non-`.py` files and standalone `__init__.py` reviews are out of scope per the Review scope rules; the helper question does not apply to them.)

Worker 2 **must re-read** the overview already written by Worker 1 before implementing any non-trivial fix on a file the helper was run against. Worker 2 may re-run the helper with `--strip-docstrings` when the logic is hard to read with docstrings inline; in that case, the shadow file's path is passed to Worker 3 on the first verification pass.

#### How to run

From the repository root:

```shell
python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py
```

Useful flags:

- `--strip-docstrings` — also strip module/class/function docstrings from the shadow file. Use when docstrings obscure the control flow being read.
- `--outline-only` — overview keeps only Imports, Symbols, Control-flow hotspots, and Django/ORM markers. Use for a fast-scan pass on a file you have already reviewed.
- `--stdout` — print the overview to stdout in addition to writing it. Useful for quick triage from the terminal.
- `--marker NAME` — add a custom marker to the Django/ORM marker table. Repeatable. Use when a file traffics in a name (e.g., `Connection`, `relay`) the default marker list does not cover.

#### Output files

Two files land under `docs/review/shadow/<stable-stem>`:

- `<stem>.stripped.py` — target source with `#` comments removed (and docstrings, with `--strip-docstrings`).
- `<stem>.overview.md` — static AST overview with the sections described below.

`docs/review/shadow/` is gitignored: the shadow file and overview are throwaway analysis byproducts. The tracked, committed review artifact is the `docs/review/rev-*.md` file Worker 1 produces.

#### Reading the overview — section-by-section guidance

| Section | Reviewer use |
|---|---|
| **Imports** | Confirm the file's place in the dependency graph: local / first-party / django / strawberry / standard. New cross-folder imports are usually structural changes worth flagging. |
| **Symbols** | Use as a fast table of contents. Jump straight to the function being reviewed. The class/parent column flags methods that may belong elsewhere. |
| **Control-flow hotspots** | Functions over 40 lines or 8 branches surface here. Apply Medium-tier "complexity / branchy" attention to every hotspot. If a hotspot has no test exercising every branch, that is a Medium-tier "missing tests for important branches" finding. |
| **Django / ORM markers** | **Audit checklist for ORM-heavy files.** Every line in this table touches `QuerySet`, `select_related`, `prefetch_related`, `Prefetch`, `only`, `_meta`, `get_queryset`, `_prefetched_objects_cache`, `fields_cache`, `DjangoType`, `OptimizationPlan`, `OptimizerHint`, `dst_optimizer_plan`, or `_optimizer_field_map`. Walk every entry. Each one needs either a one-line justification ("this is correct because …") or a finding. |
| **Calls of interest** | Reflective-access audit: every `getattr` / `hasattr` / `isinstance` / `setattr` and every container-coercion (`dict`, `frozenset`, `iter`, `len`, `list`, `set`, `tuple`) lands here. These are the typical sites of shape-contract bugs and missing defensive defaults. |
| **Comments and docstrings → Docstrings** | Verify every public function/class has a docstring describing the *final* approved behavior (after logic changes are accepted). |
| **Comments and docstrings → TODO comments** | Comment-pass checklist: each TODO must still be actionable and must match its anchored spec; remove the anchor in the same change that ships the slice (per AGENTS.md). |
| **Comments and docstrings → Comment inventory** | Spot stale or restating-the-obvious comments. Comment polish belongs in the comment pass, not the logic pass. |
| **Repeated string literals** | DRY signal. Useful at the per-file pass for catching string-keyed dispatch (e.g., context keys); essential at the folder pass for catching cross-file duplication (`logger = logging.getLogger("django_strawberry_framework")` in three files would surface as the same literal in three overviews). |

#### Folder-pass repeated-literal check

When writing a folder-level artifact, Worker 1 must:

1. Confirm the helper has been run on every Python file in the folder (overviews exist under `docs/review/shadow/`).
2. Compare the **Repeated string literals** sections across sibling overviews. A literal that appears in two or more files is a folder-level DRY candidate; record it in the folder artifact's Medium or Low section depending on severity.
3. Compare the **Imports** sections across sibling overviews to confirm one-way dependency direction inside the folder and to spot a sibling that has started importing from outside the documented boundary.

#### Shadow-file line numbers are NOT canonical

The shadow file strips `#` comments (and optionally docstrings), so its line numbers do not match the original source. Review artifacts, Worker 3 feedback, and source edits must cite **original source-file line numbers**, never shadow-file line numbers. The shadow file is read-only for review purposes; never edit or commit it. If Worker 2 used the shadow file during fix implementation, Worker 3's first verification pass must include the shadow-file caveat (see the `worker-3.md` shadow-file dicta).

If a review identifies coverage that would seem to belong under frozen `tests/base/`, follow `AGENTS.md`: do not add new files there. Route new coverage to the correct existing parallel package test path or extend an allowed existing file only when that matches the standing rules.

### Comment/docstring review second

After logic changes are implemented and approved, review comments and docstrings.

Focus on:

- stale comments
- comments that restate obvious code
- missing comments for non-obvious optimizer/Django behavior
- docstrings that promise behavior the implementation does not provide
- TODOs that are no longer actionable
- references to deleted specs or obsolete planning labels
- public API docstrings that should mention consumer-visible constraints

Do not polish comments before logic is correct. Comments should describe the final approved behavior, not the pre-fix behavior.

## Subagent dispatch and worker memory

Workers 1, 2, and 3 each run as **separate subagent invocations per cycle item**. Worker 0 stays in the main thread as the orchestrator. The split exists so the worker that verifies a fix has no in-context memory of the worker that wrote it — a worker cannot review its own implementation reasoning, just the artifact-and-diff contract handed to it.

### Why subagent dispatch

A single agent role-playing all three workers can convince itself a fix is sufficient because it remembers *why* it implemented the fix that way. Subagent isolation removes that path: Worker 3 starts fresh per cycle, sees only the artifact and the diff, and accepts or rejects on what is actually written down. The artifact and the diff become the contract; nothing flows between workers except those two files (plus the source under review).

### Worker memory

Each worker keeps a private scratch memory file that **persists across cycles within a single release** but is invisible to every other worker:

- `docs/review/worker-memory/worker-1.md` — Worker 1's review notebook
- `docs/review/worker-memory/worker-2.md` — Worker 2's implementation notebook
- `docs/review/worker-memory/worker-3.md` — Worker 3's verification notebook

These files are gitignored. Worker 0 creates the directory at plan time and deletes it at closeout. The tracked permanent record is the `rev-*.md` artifacts, never these notes.

**What a worker writes to its memory.** At the end of each cycle, the worker appends a short entry — typically 3-5 lines — capturing what to carry into the next cycle:

- Worker 1: recurring patterns being flagged, severity calibration ("after seeing this in three files I'm calling it Medium not Low"), reusable phrasing for common findings.
- Worker 2: implementation patterns that worked (validation guard shapes, test scaffolding, comment polish style), maintainer pushback to remember.
- Worker 3: kinds of fixes that passed muster, kinds that bit later, calibration on when to reject vs accept.

Entries are append-only. If a worker's memory exceeds ~50 lines, the worker must consolidate (merge similar entries into a single pattern observation) before adding more — never delete without consolidating first.

**Read isolation rules.** A worker may read **only** its own memory file:

- Worker 1 may not read `worker-2.md` or `worker-3.md`.
- Worker 2 may not read `worker-1.md` or `worker-3.md`. (Worker 2 reads the *artifact* Worker 1 produced — that is the contract — but never Worker 1's running notes.)
- Worker 3 may not read `worker-1.md` or `worker-2.md`. (Worker 3 reads the *artifact* and the *diff* — those are the contract — but never the other workers' running notes.)
- Worker 0 may read all memory files at closeout to seed the retrospective, but never edits them.

**Write isolation rules.** A worker writes only to its own memory file. The main thread (Worker 0) never edits a worker's memory.

**Spawn-per-cycle dispatch.** Worker 0 spawns each worker as a fresh subagent, once per cycle item, in this order:

1. Worker 1 subagent — produces the artifact, appends to `worker-1.md`, returns.
2. Worker 2 subagent — implements fixes, appends to `worker-2.md`, returns.
3. Worker 3 subagent — verifies, marks the checkbox, appends to `worker-3.md`, returns.

Each subagent's prompt must include: standing project docs (`AGENTS.md`, `START.md`, `REVIEW.md`, the worker's own role file), the active plan, the cycle's artifact (Workers 2 and 3) or source target (Worker 1), and the worker's own memory file contents. The subagent's prompt must explicitly forbid reading the other workers' memory files.

**No cross-worker chatter.** Subagents do not message each other directly. All inter-worker information flows through the artifact (`rev-<folder__file_name>.md`) and the diff. If Worker 2 needs to flag something to Worker 3 (e.g., "I used the shadow view"), it goes in the artifact. If Worker 3 wants another Worker 2 pass, it goes in the artifact's verification feedback section.

**Lifecycle.**

- Worker 0 creates `docs/review/worker-memory/` and seeds three empty files (`worker-1.md`, `worker-2.md`, `worker-3.md`) at plan-creation time.
- Workers 1/2/3 read their own file at the start of every spawn and append at the end.
- Worker 0 deletes `docs/review/worker-memory/` at cycle closeout, after the retrospective is written.

## Worker process

### Worker 0: create and maintain the release review plan

Worker 0 reads `docs/review/REVIEW.md`, [Worker 0's role instructions](worker-0.md), and creates `docs/review/review-<0_0_X>.md`.

The plan must include:

- the exact package tree checklist
- the artifact list
- the one-file-at-a-time rule
- the severity definitions
- the logic-first/comment-second rule
- the folder-level and final project-level review requirements

When the full package review is finished, Worker 0 scans the commit diffs from the review cycle and provides final feedback. Worker 0 and the maintainer make any last changes needed. Worker 0 then reads `CHANGELOG.md`, consolidates review-cycle entries if needed, and updates `docs/review/REVIEW.md` or the worker role files with a general retrospective.

The retrospective must be general. It should describe recurring bug types, stumbling blocks, and workflow improvements without naming specific already-fixed issues.

### Worker 1: perform the next unchecked review

Worker 1 runs as a fresh subagent invocation per cycle item (see "Subagent dispatch and worker memory"). It reads `docs/review/review-<0_0_X>.md`, [Worker 1's role instructions](worker-1.md), `docs/review/worker-memory/worker-1.md` (its own running notes from prior cycles in this release), finds the first checklist item not marked `- [x]`, and reviews only that file or folder pass.

Worker 1 creates the required `docs/review/rev-<folder__file_name>.md` artifact, appends a short entry to `docs/review/worker-memory/worker-1.md`, and stops. Worker 1 may not read `worker-memory/worker-2.md` or `worker-memory/worker-3.md`.

### Worker 2: implement fixes

Worker 2 runs as a fresh subagent invocation per cycle item. It reads the current `docs/review/rev-<folder__file_name>.md` file, [Worker 2's role instructions](worker-2.md), `docs/review/worker-memory/worker-2.md` (its own running notes from prior cycles), the target source file, and implements the approved logic changes. Worker 2 may not read `worker-memory/worker-1.md` or `worker-memory/worker-3.md`; the artifact is the only contract Worker 1 hands over.

Worker 2 should:

- use the review artifact as the task list
- use a comment-stripped shadow view when helpful for logic changes
- pass any shadow view used for the fix to Worker 3 for the first verification pass
- make source changes only for the current file/folder scope unless the artifact explicitly identifies a necessary cross-file change
- add or update tests when the logic change needs proof
- run focused validation appropriate to the change

After Worker 3 approves the logic changes, Worker 2 updates comments/docstrings for the reviewed scope. After Worker 3 approves comments, Worker 2 updates `CHANGELOG.md` if the change is user-visible or release-note-worthy. Each Worker 2 pass is a fresh subagent spawn — Worker 2 only knows about the previous pass through what it wrote in the artifact and in `worker-memory/worker-2.md`.

At the end of its final pass for a cycle item, Worker 2 appends a short entry to `docs/review/worker-memory/worker-2.md`.

When a review artifact has no High-severity issues, Worker 2 and Worker 3 may be the same agent invocation if the maintainer explicitly chooses that lower-ceremony path for the item — but this defeats the isolation guarantee and should be reserved for trivial cycles.

### Worker 3: verify fixes

Worker 3 runs as a fresh subagent invocation per cycle item. It reads [Worker 3's role instructions](worker-3.md), `docs/review/worker-memory/worker-3.md` (its own running notes from prior cycles), and reviews Worker 2's diff against the `docs/review/rev-<folder__file_name>.md` artifact. Worker 3 may not read `worker-memory/worker-1.md` or `worker-memory/worker-2.md`. Worker 3 has cycle-spanning history of what kinds of fixes it has accepted before, but no in-context memory of *this* cycle's implementation reasoning — that is the point of the dispatch.

If Worker 2 used a shadow view, Worker 3's first-pass prompt must explicitly say: "The shadow file strips comments and may strip docstrings; its line numbers will not match the original source or the review artifact. Treat original source-file line numbers and the `docs/review/rev-<folder__file_name>.md` line references as canonical. Use the shadow only to understand control flow."

Worker 3 should:

- confirm each High/Medium/Low issue was addressed or intentionally rejected with reason
- check that tests or validation match the risk level
- reject any High-severity fix that does not add or update tests pinning the corrected behavior, unless the artifact explicitly explains why a test is impossible or inappropriate
- review comment/docstring updates after logic is approved
- request another Worker 2 pass if needed (recorded in the artifact's verification feedback section — Worker 3 does not message Worker 2 directly)
- mark the corresponding checkbox `- [x]` in `docs/review/review-<0_0_X>.md` only after logic, comments, validation, and changelog updates are complete
- append a short entry to `docs/review/worker-memory/worker-3.md` capturing what to carry into the next cycle

### Maintainer checkpoint

After Worker 3 marks the item done:

1. The maintainer reviews the result.
2. Worker 1 is informed that the fix was applied.
3. Worker 1 checks the full diff and verifies the reviewed concern is complete.
4. The maintainer commits the source changes together with the corresponding `docs/review/rev-<folder__file_name>.md` artifact and the updated `docs/review/review-<0_0_X>.md` checkbox so the review record is preserved in git.
5. Worker 1 moves to the next unchecked item.

No worker should commit unless the maintainer explicitly asks.

## Folder-level passes

After every file in a folder is complete, Worker 1 reads every sibling `docs/review/rev-*.md` artifact for that folder and creates the folder-level artifact for that folder.

The folder-level pass should check:

- duplicated helpers across files in the folder
- inconsistent naming or error handling
- repeated ORM/queryset patterns that should be centralized
- misplaced responsibilities between sibling modules
- missing package exports or too-broad exports
- circular import risk introduced by fixes
- whether comments now tell one coherent story across the folder

The folder-level artifact uses the same High/Medium/Low template. It may cite multiple files in the same folder, but it should not become a whole-project review.

## Final project-level pass

After every file and folder pass is complete, Worker 1 creates `docs/review/rev-django_strawberry_framework.md`.

This pass should update `docs/review/review-<0_0_X>.md` with any package-wide DRY or structure potentials discovered after seeing the whole project.

Focus on:

- duplicated patterns across folders
- public API/export consistency
- settings and configuration boundaries
- shared utility candidates
- optimizer/type/registry responsibility boundaries
- package-wide test gaps
- recurring bug classes

## Cleanup and closeout

When all checklist items are marked `- [x]`:

1. Worker 0 scans all review-cycle commit diffs.
2. Worker 0 provides final feedback.
3. Worker 0 and the maintainer make any last changes needed.
4. Worker 0 implements approved closeout changes.
5. Worker 0 reads `CHANGELOG.md` and consolidates entries if needed.
6. Worker 0 updates `docs/review/REVIEW.md` or the worker role files with a general retrospective:
   - recurring issue types found
   - workflow stumbling blocks
   - review checklist improvements for the next release
7. The maintainer commits the updated `docs/review/` workflow docs along with the now-completed `docs/review/review-<0_0_X>.md` plan and any remaining `docs/review/rev-*.md` artifacts to finish the review cycle. The plan and artifacts stay in git as the permanent record of the release review.
