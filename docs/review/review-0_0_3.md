# Package review plan: 0.0.3

Release version: `0.0.3`
Source root: `django_strawberry_framework/`
Date created: 2026-05-06
Review rule: review only one file or one folder-summary pass at a time. Do not start the next item until the current item's review/fix/verification cycle is complete.

Reference docs:

- [docs/review/REVIEW.md](REVIEW.md)
- [Worker 0](worker-0.md)
- [Worker 1](worker-1.md)
- [Worker 2](worker-2.md)
- [Worker 3](worker-3.md)

Versions checked:

- `pyproject.toml` -> `0.0.3`
- `django_strawberry_framework/__init__.py` -> `0.0.3`
- Match: yes.

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

## Review order

1. Logic review first — focus on correctness, ORM behavior, async/sync, caches, performance, redundancy, typing, test gaps, Two Scoops structure.
2. Comment/docstring review second — only after logic changes are approved.

## Folder-level and project-level passes

After every file in a folder is reviewed, Worker 1 reads every sibling `docs/review/rev-*.md` artifact for that folder and creates the folder-level artifact. After every file and folder pass is complete, Worker 1 creates the project-level artifact `docs/review/rev-django_strawberry_framework.md`.

## Shadow-file caveat

Shadow files under `docs/review/shadow/` strip `#` comments (and optionally docstrings); their line numbers do not match the original source. Review artifacts and Worker 3 feedback must cite original source-file line numbers, never shadow-file line numbers.

## High-severity test requirement

Worker 3 must reject any High-severity fix that does not add or update a test pinning the corrected behavior, unless the artifact explicitly explains why a test is impossible or inappropriate.

## No-commit rule

No worker commits source or artifacts unless the maintainer explicitly asks. The maintainer commits each cycle's source changes, the corresponding `docs/review/rev-*.md` artifact, and the updated checkbox in this plan together.

## Artifact list

- `docs/review/rev-__init__.md`
- `docs/review/rev-conf.md`
- `docs/review/rev-exceptions.md`
- `docs/review/rev-py.typed.md`
- `docs/review/rev-registry.md`
- `docs/review/rev-optimizer____init__.md`
- `docs/review/rev-optimizer__extension.md`
- `docs/review/rev-optimizer__field_meta.md`
- `docs/review/rev-optimizer__hints.md`
- `docs/review/rev-optimizer__plans.md`
- `docs/review/rev-optimizer__walker.md`
- `docs/review/rev-optimizer.md`
- `docs/review/rev-types____init__.md`
- `docs/review/rev-types__base.md`
- `docs/review/rev-types__converters.md`
- `docs/review/rev-types__resolvers.md`
- `docs/review/rev-types.md`
- `docs/review/rev-utils____init__.md`
- `docs/review/rev-utils__strings.md`
- `docs/review/rev-utils__typing.md`
- `docs/review/rev-utils.md`
- `docs/review/rev-django_strawberry_framework.md`

## Checklist

- `django_strawberry_framework/`
  - [x] `django_strawberry_framework/__init__.py` -> `docs/review/rev-__init__.md`
  - [x] `django_strawberry_framework/conf.py` -> `docs/review/rev-conf.md`
  - [x] `django_strawberry_framework/exceptions.py` -> `docs/review/rev-exceptions.md`
  - [x] `django_strawberry_framework/py.typed` -> `docs/review/rev-py.typed.md`
  - [x] `django_strawberry_framework/registry.py` -> `docs/review/rev-registry.md`
  - `django_strawberry_framework/optimizer/`
    - [x] `django_strawberry_framework/optimizer/__init__.py` -> `docs/review/rev-optimizer____init__.md`
    - [x] `django_strawberry_framework/optimizer/extension.py` -> `docs/review/rev-optimizer__extension.md`
    - [x] `django_strawberry_framework/optimizer/field_meta.py` -> `docs/review/rev-optimizer__field_meta.md`
    - [x] `django_strawberry_framework/optimizer/hints.py` -> `docs/review/rev-optimizer__hints.md`
    - [x] `django_strawberry_framework/optimizer/plans.py` -> `docs/review/rev-optimizer__plans.md`
    - [x] `django_strawberry_framework/optimizer/walker.py` -> `docs/review/rev-optimizer__walker.md`
    - [x] folder pass: `django_strawberry_framework/optimizer/` -> `docs/review/rev-optimizer.md`
  - `django_strawberry_framework/types/`
    - [x] `django_strawberry_framework/types/__init__.py` -> `docs/review/rev-types____init__.md`
    - [x] `django_strawberry_framework/types/base.py` -> `docs/review/rev-types__base.md`
    - [x] `django_strawberry_framework/types/converters.py` -> `docs/review/rev-types__converters.md`
    - [x] `django_strawberry_framework/types/resolvers.py` -> `docs/review/rev-types__resolvers.md`
    - [x] folder pass: `django_strawberry_framework/types/` -> `docs/review/rev-types.md`
  - `django_strawberry_framework/utils/`
    - [x] `django_strawberry_framework/utils/__init__.py` -> `docs/review/rev-utils____init__.md`
    - [x] `django_strawberry_framework/utils/strings.py` -> `docs/review/rev-utils__strings.md`
    - [x] `django_strawberry_framework/utils/typing.py` -> `docs/review/rev-utils__typing.md`
    - [x] folder pass: `django_strawberry_framework/utils/` -> `docs/review/rev-utils.md`
  - [x] project-level pass: `django_strawberry_framework/` -> `docs/review/rev-django_strawberry_framework.md`
