# Spec: 0.0.4 version and release alignment

Target release: `0.0.4` (per [KANBAN.md][kanban] card `DONE-012-0.0.4`).
Status: shipped. A card-snapshot spec: the file is the card's `SpecDoc` target.
Owner: package maintainer.

Why the version has one source, and why the spec states the release obligation rather than a version, lives in its companion [rationale file][spec-012-rationale].

## Card snapshot

- Card: `DONE-012-0.0.4`, status `done`, milestone `alpha` (pre-`0.1.0`).
- The card's other board fields — labels, priority, relative size, and its item rows — belong to the Kanban database and are rendered into [KANBAN.md][kanban]. This section identifies the card; it does not restate them.

## Scope

A release cut sets the package version in **one** place, and two hand-maintained surfaces move with it:

- [`django_strawberry_framework/__init__.py`][init] `#"__version__ = "` — the single version source: the runtime version the [`DjangoType`][glossary-djangotype] surface ships under.
- [`pyproject.toml`][pyproject] `#"dynamic = ["version"]"` — the distribution version is derived, not declared: `[tool.hatch.version]` points hatchling at the package init, so sdist and wheel metadata cannot disagree with `__version__`. The editable root entry in [`uv.lock`][uv-lock] carries no version.
- [`tests/base/test_init.py`][test-init] `::test_version` pins the runtime version as a literal string, so a bump updates it in the same change.
- [`CHANGELOG.md`][changelog] gains the release's entry. The `0.0.4` entry is dated 2026-05-08 and is the condensed alpha-release form — five `### Added` bullets, six `### Changed`, four `### Fixed`, one `### Removed`.

Alignment is a **per-release obligation, not a fixed value**: at any commit the init literal, the test literal, and the newest changelog entry agree on whatever version the package is then at.

<!-- LINK DEFINITIONS -->

<!-- Root -->
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
