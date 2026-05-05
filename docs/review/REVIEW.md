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

The review covers every tracked file under `django_strawberry_framework/`, including package marker files such as `py.typed`. Python files get the full logic/comment review. Non-Python package files get a narrower packaging/API-contract review.

The review is folder-by-folder and one file at a time within each folder.

Rules:

- Review only one file or one folder-summary pass at a time.
- Do not start the next file until the current file's review/fix/verification/commit cycle is complete.
- After all files in a folder are reviewed, perform one folder-level pass using the context gathered from those files. Before that folder pass, Worker 1 must read every sibling `docs/review/rev-*.md` artifact for the folder.
- The folder-level pass should primarily look for DRY opportunities, duplicated logic, misplaced responsibilities, and cross-file inconsistencies.
- After all files and folder passes are complete, perform one project-level pass over `django_strawberry_framework/` for DRY and structure opportunities that only become visible with full-package context.

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

- `docs/review/rev-__init__.md`
- `docs/review/rev-conf.md`
- `docs/review/rev-optimizer____init__.md`
- `docs/review/rev-optimizer__field_meta.md`
- `docs/review/rev-optimizer.md`
- `docs/review/rev-django_strawberry_framework.md`

## Checklist

- `django_strawberry_framework/`
  - [ ] `django_strawberry_framework/__init__.py` -> `docs/review/rev-__init__.md`
  - [ ] `django_strawberry_framework/conf.py` -> `docs/review/rev-conf.md`
  - `django_strawberry_framework/optimizer/`
    - [ ] `django_strawberry_framework/optimizer/__init__.py` -> `docs/review/rev-optimizer____init__.md`
    - [ ] `django_strawberry_framework/optimizer/field_meta.py` -> `docs/review/rev-optimizer__field_meta.md`
    - [ ] folder pass: `django_strawberry_framework/optimizer/` -> `docs/review/rev-optimizer.md`
  - [ ] project-level pass: `django_strawberry_framework/` -> `docs/review/rev-django_strawberry_framework.md`
```

Use the actual on-disk package tree when creating the plan. Do not invent files. Keep the checklist in review order.

## Review artifact naming

Per-file and per-folder review artifacts are tracked Markdown files under `docs/review/`. They are committed alongside the source changes they describe and form a permanent record of the review cycle.

Naming rules:

- Start with `docs/review/rev-`.
- Use the path relative to `django_strawberry_framework/`.
- Replace `/` with `__`.
- Drop the `.py` suffix for Python files.
- Keep dunder names readable even if they produce multiple underscores.
- End with `.md`.

Examples:

- `django_strawberry_framework/__init__.py` -> `docs/review/rev-__init__.md`
- `django_strawberry_framework/conf.py` -> `docs/review/rev-conf.md`
- `django_strawberry_framework/optimizer/__init__.py` -> `docs/review/rev-optimizer____init__.md`
- `django_strawberry_framework/optimizer/walker.py` -> `docs/review/rev-optimizer__walker.md`
- folder pass for `django_strawberry_framework/optimizer/` -> `docs/review/rev-optimizer.md`
- project-level pass for `django_strawberry_framework/` -> `docs/review/rev-django_strawberry_framework.md`

The generated `docs/review/review-<0_0_X>.md` file must list every artifact before review work starts.

## Output rule for Worker 1

IMPORTANT: after each file or folder review, Worker 1's only output is the review artifact file.

Worker 1 must not:

- modify source code
- update comments
- update `CHANGELOG.md`
- mark the checklist item done
- produce a separate narrative response

Worker 1 creates exactly one `docs/review/rev-<folder__file_name>.md` file for the current file or folder pass, then stops. For low-surface files such as `py.typed` or a trivial re-export-only `__init__.py`, that artifact may be a skip artifact explaining why there is no review-worthy logic or comment surface. Worker 1 still does not mark the checklist item done; Worker 3 or the maintainer handles the checkbox after accepting the skip artifact.

## Review artifact template

Every `docs/review/rev-<folder__file_name>.md` file must use this structure:

````text
# Review: `django_strawberry_framework/optimizer/__init__.py`

## High:

### Issue name

Issue summary, why it matters, and the recommended change.

```django_strawberry_framework/optimizer/__init__.py:02:08
Relevant excerpt or pseudo-diff context.
```

## Medium:

### Issue name

Issue summary, why it matters, and the recommended change.

```django_strawberry_framework/optimizer/__init__.py:10:14
Relevant excerpt or pseudo-diff context.
```

## Low:

### Issue name

Issue summary, why it matters, and the recommended change.

```django_strawberry_framework/optimizer/__init__.py:20:26
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

When reviewing Python logic, Worker 2 may use a temporary comment-stripped shadow view when helpful. Worker 3 should receive that shadow view on the first verification pass when it was used to implement the fix. The shadow view is only an aid for reading control flow; never edit or commit it, and always cite line numbers from the original file.

The comment-stripped pass should remove `#` comments from the view so logic can be read without explanatory text. It may leave docstrings in place unless docstrings obscure the control flow being checked. Shadow-file line numbers are not authoritative because comments may be stripped. Review artifacts and Worker 3 feedback must use original source-file line numbers, not shadow-file line numbers. Worker 3 feedback should be placed in the `docs/review/rev-<folder__file_name>.md` file.

Use the static review helper from the project root:

```shell
python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py
```

By default it writes:

- `docs/review/shadow/<target>.stripped.py` — target source with `#` comments removed
- `docs/review/shadow/<target>.overview.md` — static AST overview with imports, symbols, control-flow hotspots, Django/ORM markers, comments, docstrings, calls of interest, and repeated literals

Useful options:

- `--strip-docstrings` also strips docstrings from the shadow file
- `--outline-only` keeps the overview focused on imports, symbols, hotspots, and markers
- `--stdout` prints the overview while still writing the generated files

The helper never imports or executes the target module. Generated files under `docs/review/shadow/` are static-analysis byproducts and are ignored by git; the `.md` review artifacts and plan file under `docs/review/` are tracked.

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

Worker 1 reads `docs/review/review-<0_0_X>.md`, [Worker 1's role instructions](worker-1.md), finds the first checklist item not marked `- [x]`, and reviews only that file or folder pass.

Worker 1 creates the required `docs/review/rev-<folder__file_name>.md` artifact and stops.

### Worker 2: implement fixes

Worker 2 reads the current `docs/review/rev-<folder__file_name>.md` file, [Worker 2's role instructions](worker-2.md), reviews the target source file, and implements the approved logic changes.

Worker 2 should:

- use the review artifact as the task list
- use a comment-stripped shadow view when helpful for logic changes
- pass any shadow view used for the fix to Worker 3 for the first verification pass
- make source changes only for the current file/folder scope unless the artifact explicitly identifies a necessary cross-file change
- add or update tests when the logic change needs proof
- run focused validation appropriate to the change

After Worker 3 approves the logic changes, Worker 2 updates comments/docstrings for the reviewed scope. After Worker 3 approves comments, Worker 2 updates `CHANGELOG.md` if the change is user-visible or release-note-worthy.

When a review artifact has no High-severity issues, Worker 2 and Worker 3 may be the same agent invocation if the maintainer explicitly chooses that lower-ceremony path for the item.

### Worker 3: verify fixes

Worker 3 reads [Worker 3's role instructions](worker-3.md) and reviews Worker 2's diff against the `docs/review/rev-<folder__file_name>.md` artifact.

If Worker 2 used a shadow view, Worker 3's first-pass prompt must explicitly say: "The shadow file strips comments and may strip docstrings; its line numbers will not match the original source or the review artifact. Treat original source-file line numbers and the `docs/review/rev-<folder__file_name>.md` line references as canonical. Use the shadow only to understand control flow."

Worker 3 should:

- confirm each High/Medium/Low issue was addressed or intentionally rejected with reason
- check that tests or validation match the risk level
- reject any High-severity fix that does not add or update tests pinning the corrected behavior, unless the artifact explicitly explains why a test is impossible or inappropriate
- review comment/docstring updates after logic is approved
- request another Worker 2 pass if needed
- mark the corresponding checkbox `- [x]` in `docs/review/review-<0_0_X>.md` only after logic, comments, validation, and changelog updates are complete

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
