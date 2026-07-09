# Spec: 0.0.4 version and release alignment

Target release: `0.0.4` (per [KANBAN.md][kanban] card `DONE-012-0.0.4`).
Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.
Owner: package maintainer.

This file is intentionally lightweight. It preserves the card scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable repository file. Before implementation work starts from this file, expand it into the full builder-format spec described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`.

## Card snapshot

- Card: `DONE-012-0.0.4`
- Status: `done` / Done
- Milestone: `alpha` / Alpha (pre-0.1.0)
- Priority: Low
- Relative size: XS
- Labels: `release`, `versioning`

## Planning note

shipped

## Scope

- Package metadata for the [`DjangoType`][glossary-djangotype] release line, runtime version, lockfile, tests, and changelog now agree on `0.0.4`.
- The changelog entry is condensed for the alpha release and covers the actual commit range through 2026-05-08.

## Other

- release housekeeping (version alignment).
- align package metadata / runtime version / lockfile / tests / changelog on `0.0.4`.
- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../BACKLOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-djangotype]: ../GLOSSARY.md#djangotype

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
