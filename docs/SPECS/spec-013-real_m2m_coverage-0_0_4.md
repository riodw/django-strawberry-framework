# Spec: Real M2M coverage

Target release: `0.0.4` (per [KANBAN.md][kanban] card `DONE-013-0.0.4`).
Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.
Owner: package maintainer.

This file is intentionally lightweight. It preserves the card scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable repository file. Before implementation work starts from this file, expand it into the full builder-format spec described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`.

## Card snapshot

- Card: `DONE-013-0.0.4`
- Status: `done` / Done
- Milestone: `alpha` / Alpha (pre-0.1.0)
- Priority: Medium
- Severity: Low
- Planning state: Shipped
- Relative size: S
- Labels: `example-app`, `m2m`, `tests`

## Planning note

shipped

## Scope

- Replaced test-only M2M/cardinality fixtures with real managed models in the `library` example app.
- Added package-level and HTTP-level coverage for [M2M traversal][glossary-relation-handling] and optimizer planning.

## Other

- test hygiene.
- replace test-only M2M / cardinality fixtures with real `library` models; add package + HTTP coverage.
- `examples/fakeshop/apps/library/models.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `tests/types/test_definition_order.py`
- `tests/optimizer/test_definition_order.py`

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../BACKLOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
