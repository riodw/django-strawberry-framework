# Spec: Stale placeholder cleanup

Target release: `0.0.4` (per [KANBAN.md][kanban] card `DONE-011-0.0.4`).
Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.
Owner: package maintainer.

This file is intentionally lightweight. It preserves the card scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable repository file. Before implementation work starts from this file, expand it into the full builder-format spec described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`.

## Card snapshot

- Card: `DONE-011-0.0.4`
- Status: `done` / Done
- Milestone: `alpha` / Alpha (pre-0.1.0)
- Priority: Low
- Severity: Low
- Planning state: Shipped
- Relative size: XS
- Labels: `cleanup`, `docs`, `tests`

## Planning note

shipped

## Scope

- Replaced stale M2M and forward-reference skips with [definition-order][glossary-definition-order-independence] tests.
- Kept the remaining scalar override skip documented as a separate [scalar-field][glossary-scalar-field-override-semantics] concern under `DONE-019-0.0.6`.

## Other

- internal test/doc cleanup.
- replace stale M2M / forward-reference skips with definition-order tests.
- `tests/types/test_definition_order.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_definition_order.py`
- `DONE-019-0.0.6`

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../BACKLOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-scalar-field-override-semantics]: ../GLOSSARY.md#scalar-field-override-semantics

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
