# Spec: 0.0.4 version and release alignment

Target release: `0.0.4` (per [KANBAN.md][kanban] card `DONE-012-0.0.4`).
Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.
Owner: package maintainer.

Deliberation and this spec's change record live in its companion [rationale file][spec-012-rationale]: what the release commit actually touched, why four of the five version surfaces were already aligned before it ran, and every claim this spec once made and may no longer make.

## Card snapshot

- Card: `DONE-012-0.0.4`, status `done`, milestone `alpha` (pre-`0.1.0`).
- The card's other board fields — labels, priority, relative size, and its item rows — belong to the Kanban database and are rendered into [KANBAN.md][kanban]. This section identifies the card; it does not restate them.

## Scope

A release cut of this package aligns **five** surfaces on one version string. The `0.0.4` cut carries `0.0.4` on every one of them:

- [`pyproject.toml`][pyproject] `#"version = "` — the distribution version.
- [`django_strawberry_framework/__init__.py`][init] `#"__version__ = "` — the runtime version the [`DjangoType`][glossary-djangotype] surface ships under.
- [`uv.lock`][uv-lock], on its `django-strawberry-framework` root entry.
- [`tests/base/test_init.py`][test-init] `::test_version`, which pins the runtime version as a literal string.
- [`CHANGELOG.md`][changelog], whose `## [0.0.4]` entry is dated 2026-05-08 and covers the commit range through that date.

Alignment is a **per-release obligation, not a standing property of these five files**: every later release moves all five together, so at any commit the five agree on whatever version the package is then at — never on `0.0.4` in perpetuity. `AGENTS.md` rule 31 carries the `pyproject.toml` / `__init__.py` half of that pairing as standing **prose** policy; `::test_version` pins the runtime literal alone and no test compares the two files.

The `0.0.4` changelog entry is the condensed alpha-release form — five `### Added` bullets, six `### Changed`, four `### Fixed`, one `### Removed` — and it is the entry of record for the release: no later commit rewrites it.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../BACKLOG.md
[changelog]: ../../CHANGELOG.md
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[uv-lock]: ../../uv.lock

<!-- docs/ -->
[glossary-djangotype]: ../GLOSSARY.md#djangotype

<!-- docs/SPECS/ -->
[spec-012-rationale]: appx/spec-012-version_release_alignment-0_0_4-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[init]: ../../django_strawberry_framework/__init__.py

<!-- tests/ -->
[test-init]: ../../tests/base/test_init.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
