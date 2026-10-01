# Spec: Stale placeholder cleanup

Target release: `0.0.4` (per [KANBAN.md][kanban] card `DONE-011-0.0.4`).
Status: shipped. A card-snapshot spec: the file is the card's `SpecDoc` target.
Owner: package maintainer.

Deliberation lives in its companion [rationale file][spec-011-rationale].

## Card snapshot

- Card: `DONE-011-0.0.4`, status `done`, milestone `alpha` (pre-`0.1.0`).
- The card's other board fields — labels, priority, relative size, and its item rows — belong to the Kanban database and are rendered into [KANBAN.md][kanban]. This section identifies the card; it does not restate them.

## Scope

Many-to-many relations and forward references are pinned by tests that run, not by skipped placeholders:

- Many-to-many resolution in both directions is [definition-order][glossary-definition-order-independence] behavior and is pinned by [`tests/types/test_definition_order.py`][test-types-definition-order] `::test_many_to_many_forward_and_reverse_relations_resolve`; the optimizer's planning decision for the same relations is pinned by [`tests/optimizer/test_definition_order.py`][test-optimizer-definition-order] `::test_plan_relation_decisions_match_cardinality_after_finalization`.
- Relation targets declared after their source, same-module string annotations surviving finalization, and cross-module lazy relation overrides are pinned by [`tests/types/test_definition_order.py`][test-types-definition-order]; the schema those graphs produce builds end to end in [`tests/types/test_definition_order_schema.py`][test-types-definition-order-schema].

No unconditional `skip` or `xfail` marker stands in for a test anywhere under `tests/types/` or `tests/optimizer/`.

[Scalar field override semantics][glossary-scalar-field-override-semantics] is a separate concern from definition order — a contest between a consumer's annotation and the synthesized one, not a question of when a type is declared — so it is outside this card's scope. Card `DONE-019-0.0.6` owns it and ships it at `0.0.6`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-scalar-field-override-semantics]: ../GLOSSARY.md#scalar-field-override-semantics

<!-- docs/SPECS/ -->
[spec-011-rationale]: appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->
[test-optimizer-definition-order]: ../../tests/optimizer/test_definition_order.py
[test-types-definition-order]: ../../tests/types/test_definition_order.py
[test-types-definition-order-schema]: ../../tests/types/test_definition_order_schema.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
