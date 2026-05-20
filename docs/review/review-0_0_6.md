# Package review plan: 0.0.6

Source root: `django_strawberry_framework/`
Date created: 2026-05-19
Release version: `0.0.6` (matches `pyproject.toml` and `django_strawberry_framework/__init__.py`)

Standing workflow docs:

- [docs/review/REVIEW.md](REVIEW.md) — review workflow
- [docs/review/worker-0.md](worker-0.md) — coordinator role
- [docs/review/worker-1.md](worker-1.md) — reviewer role
- [docs/review/worker-2.md](worker-2.md) — fix implementer role
- [docs/review/worker-3.md](worker-3.md) — verifier role

## Review rules (short copies)

- **One file or folder-summary pass at a time.** Do not start the next file until the current file's review / fix / verification cycle reaches top-level `Status: verified`.
- **DRY-first.** Every `rev-*.md` artifact must include a `## DRY analysis` section before merging. Worker 1 flags DRY findings in every artifact; Worker 2 implements them; Worker 3 enforces DRY before accepting a fix; Worker 1 re-checks DRY across files at every folder pass and at the project pass.
- **Logic review first, comment/docstring review second.** Comments describe the final approved behavior, not the pre-fix shape.
- **Shadow-file line numbers are NOT canonical.** Review artifacts, Worker 3 feedback, and source edits must cite original source-file line numbers, never shadow-file line numbers.
- **High-severity test requirement.** Worker 3 must reject any High-severity fix that does not add or update tests pinning the corrected behavior, unless the artifact explicitly explains why a test is impossible or inappropriate.
- **No-commit rule.** Only the maintainer commits. Workers never commit, even if asked.

## Severity definitions

- **High** — confirmed correctness bugs, API contract breakage, security or data-isolation risk, Django ORM behavior that can return wrong data, cache/request-state mutation bugs, errors that can crash normal consumer usage.
- **Medium** — likely performance problems, N+1 risk, excessive database work, redundant implementation that should be consolidated, unclear ownership between modules, brittle edge-case behavior, missing tests for important branches.
- **Low** — small maintainability issues, naming clarity, minor typing/API polish, localized simplification, comments or docstrings that are stale but not harmful.

## Pass requirements

- **Per-file pass** — logic check, then comment/docstring check, then changelog disposition. Artifact uses the template in `REVIEW.md`.
- **Folder-level pass** — runs after every in-scope file in the folder is `verified`. Covers the folder's `__init__.py` (re-exports, public-vs-private contract, side-effect-free imports), duplicated helpers, repeated literals across siblings, misplaced responsibilities, and one-way dependency direction.
- **Project-level pass** — runs after every folder pass is `verified`. Covers `django_strawberry_framework/__init__.py` (public API surface) and package-wide DRY / structure / responsibility findings. Findings live in `rev-django_strawberry_framework.md`, never in this plan file.
- **Final test-run gate** — `uv run pytest`. Worker 1 owns end-to-end; Worker 0 marks the final checklist box. Coverage is NOT inspected at this gate (CI gates `fail_under = 100`).

## Out of scope

- Every `__init__.py` is out of scope as a standalone artifact. The subpackage `__init__.py` is reviewed inside its folder pass; the top-level `django_strawberry_framework/__init__.py` is reviewed inside the project pass.
- Non-`.py` files (e.g. `py.typed`) are out of scope entirely; their behavior is governed by packaging configuration.

## Artifact list

- `docs/review/rev-conf.md`
- `docs/review/rev-exceptions.md`
- `docs/review/rev-registry.md`
- `docs/review/rev-scalars.md`
- `docs/review/rev-optimizer___context.md`
- `docs/review/rev-optimizer__extension.md`
- `docs/review/rev-optimizer__field_meta.md`
- `docs/review/rev-optimizer__hints.md`
- `docs/review/rev-optimizer__plans.md`
- `docs/review/rev-optimizer__walker.md`
- `docs/review/rev-optimizer.md`
- `docs/review/rev-types__base.md`
- `docs/review/rev-types__converters.md`
- `docs/review/rev-types__definition.md`
- `docs/review/rev-types__finalizer.md`
- `docs/review/rev-types__relations.md`
- `docs/review/rev-types__relay.md`
- `docs/review/rev-types__resolvers.md`
- `docs/review/rev-types.md`
- `docs/review/rev-utils__relations.md`
- `docs/review/rev-utils__strings.md`
- `docs/review/rev-utils__typing.md`
- `docs/review/rev-utils.md`
- `docs/review/rev-django_strawberry_framework.md`
- `docs/review/rev-final.md`

## Checklist

- `django_strawberry_framework/`
  - [x] `django_strawberry_framework/conf.py` -> `docs/review/rev-conf.md`
  - [x] `django_strawberry_framework/exceptions.py` -> `docs/review/rev-exceptions.md`
  - [x] `django_strawberry_framework/registry.py` -> `docs/review/rev-registry.md`
  - [x] `django_strawberry_framework/scalars.py` -> `docs/review/rev-scalars.md`
  - `django_strawberry_framework/optimizer/`
    - [x] `django_strawberry_framework/optimizer/_context.py` -> `docs/review/rev-optimizer___context.md`
    - [x] `django_strawberry_framework/optimizer/extension.py` -> `docs/review/rev-optimizer__extension.md`
    - [x] `django_strawberry_framework/optimizer/field_meta.py` -> `docs/review/rev-optimizer__field_meta.md`
    - [x] `django_strawberry_framework/optimizer/hints.py` -> `docs/review/rev-optimizer__hints.md`
    - [x] `django_strawberry_framework/optimizer/plans.py` -> `docs/review/rev-optimizer__plans.md`
    - [x] `django_strawberry_framework/optimizer/walker.py` -> `docs/review/rev-optimizer__walker.md`
    - [x] folder pass: `django_strawberry_framework/optimizer/` -> `docs/review/rev-optimizer.md`
  - `django_strawberry_framework/types/`
    - [x] `django_strawberry_framework/types/base.py` -> `docs/review/rev-types__base.md`
    - [x] `django_strawberry_framework/types/converters.py` -> `docs/review/rev-types__converters.md`
    - [x] `django_strawberry_framework/types/definition.py` -> `docs/review/rev-types__definition.md`
    - [x] `django_strawberry_framework/types/finalizer.py` -> `docs/review/rev-types__finalizer.md`
    - [x] `django_strawberry_framework/types/relations.py` -> `docs/review/rev-types__relations.md`
    - [x] `django_strawberry_framework/types/relay.py` -> `docs/review/rev-types__relay.md`
    - [x] `django_strawberry_framework/types/resolvers.py` -> `docs/review/rev-types__resolvers.md`
    - [x] folder pass: `django_strawberry_framework/types/` -> `docs/review/rev-types.md`
  - `django_strawberry_framework/utils/`
    - [x] `django_strawberry_framework/utils/relations.py` -> `docs/review/rev-utils__relations.md`
    - [x] `django_strawberry_framework/utils/strings.py` -> `docs/review/rev-utils__strings.md`
    - [x] `django_strawberry_framework/utils/typing.py` -> `docs/review/rev-utils__typing.md`
    - [x] folder pass: `django_strawberry_framework/utils/` -> `docs/review/rev-utils.md`
  - [x] project-level pass: `django_strawberry_framework/` -> `docs/review/rev-django_strawberry_framework.md`
- [x] final test-run gate: `uv run pytest` -> `docs/review/rev-final.md`
