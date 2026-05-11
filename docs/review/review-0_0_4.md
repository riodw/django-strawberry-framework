# Package review plan: 0.0.4

Source root: `django_strawberry_framework/`
Date created: 2026-05-10
Review rule: one file or folder-summary pass at a time. Do not start the next cycle item until the current cycle's review/fix/verification is complete.

Standing docs:

- [`docs/review/REVIEW.md`](REVIEW.md)
- [`docs/review/worker-0.md`](worker-0.md)
- [`docs/review/worker-1.md`](worker-1.md)
- [`docs/review/worker-2.md`](worker-2.md)
- [`docs/review/worker-3.md`](worker-3.md)

## Review order rules

- Logic review first, comment/docstring review second.
- Folder pass after all in-scope `.py` files in the folder; folder pass also covers the folder's `__init__.py`.
- One final project-level pass after all folder passes; covers the top-level `__init__.py`.
- `__init__.py` files and non-`.py` files (e.g. `py.typed`) are out of scope as standalone artifacts.
- Shadow files under `docs/review/shadow/` are gitignored; their line numbers are NOT canonical — cite original source-file line numbers.
- High-severity fixes must add or update tests pinning the corrected behavior unless the artifact explicitly explains why a test is impossible.
- No worker commits unless the maintainer explicitly asks.

## Severity definitions

High: confirmed correctness bugs, API contract breakage, security/data-isolation risk, ORM behavior returning wrong data, cache/request-state mutation bugs, errors that crash normal usage.

Medium: likely performance problems, N+1 risk, excessive DB work, redundant implementation, unclear ownership, brittle edge-case behavior, missing tests for important branches.

Low: small maintainability issues, naming, minor typing/API polish, localized simplification, stale-but-harmless comments/docstrings.

## Artifact list

- `docs/review/rev-conf.md`
- `docs/review/rev-exceptions.md`
- `docs/review/rev-registry.md`
- `docs/review/rev-optimizer__context.md`
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

## Checklist

- `django_strawberry_framework/`
  - [x] `django_strawberry_framework/conf.py` -> `docs/review/rev-conf.md`
  - [x] `django_strawberry_framework/exceptions.py` -> `docs/review/rev-exceptions.md`
  - [x] `django_strawberry_framework/registry.py` -> `docs/review/rev-registry.md`
  - `django_strawberry_framework/optimizer/`
    - [x] `django_strawberry_framework/optimizer/_context.py` -> `docs/review/rev-optimizer__context.md`
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
