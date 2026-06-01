# Spec: 0.0.4 onboarding docs and spec consolidation

Target release: `0.0.4` (per [KANBAN.md][kanban] card `DONE-007-0.0.4`).
Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.
Owner: package maintainer.

This file is intentionally lightweight. It preserves the card scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable repository file. Before implementation work starts from this file, expand it into the full builder-format spec described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`.

## Card snapshot

- Card: `DONE-007-0.0.4`
- Status: `done` / Done
- Milestone: `alpha` / Alpha (pre-0.1.0)
- Priority: Medium
- Severity: Low
- Planning state: Shipped
- Relative size: S
- Labels: `docs`, `release`

## Planning note

shipped

## Scope

- Root `README.md` is the canonical documentation map and operational entry point.
- `docs/README.md` is code-first: quickstart, three-minute path, optimizer behavior, and status.
- `docs/GLOSSARY.md` is the capability catalog with value-led optimizer language and comparison table.
- `docs/TREE.md` is the detailed layout/test-tree reference.
- `CHANGELOG.md` is condensed and no longer relies on design-doc pointers for release context.
- Completed design-doc content is folded into durable docs, while remaining specs preserve design history and follow-up work.

## Other

- internal docs cleanup / spec consolidation — no upstream-parity surface.
- onboarding-doc consolidation across README / docs / CHANGELOG; completed spec content folded into durable docs.
- `README.md`
- `docs/README.md`
- `docs/GLOSSARY.md`
- `docs/TREE.md`
- `CHANGELOG.md`
- Future in-flight design docs use the `docs/spec-<NNN>-<topic>-<0_0_X>.md` convention (NNN matches the KANBAN card number; see `docs/builder/BUILD.md` "Spec filename pattern"), then get folded into durable docs when shipped.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../BACKLOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
