# Rationale: spec-011 — stale placeholder cleanup (deliberation, rejected alternatives)

Deliberative companion to [`spec-011-stale_placeholder_cleanup-0_0_4.md`][spec-011]. The spec is the
contract; this file records why it has the shape it has. The spec has no numbered Decisions, so each
entry is keyed to a spec section.

## Why the spec is a card snapshot

Bears on [Card snapshot][spec-011-card-snapshot].

The file is the card's `SpecDoc` target, which the kanban app requires of every `done` card
(`examples/fakeshop/apps/kanban/signals.py::_validate_done_card_has_spec`). Expanding it into a
builder-format spec with slices and a test plan would present an inferred deliberation as a
contract. The snapshot names only the card: labels, priority, relative size, and item rows are
rendered into [KANBAN.md][kanban] from the Kanban database, and a hand copy drifts on the next board
edit.

## Why `## Scope` names the tests that pin each subject

Bears on [Scope][spec-011-scope].

The card's contract is that many-to-many relations and forward references are pinned by tests that
run rather than by skipped placeholders. The spec therefore names, for each subject, the test that
pins it, and closes with one checkable negative: no unconditional `skip` or `xfail` marker stands in
for a test under `tests/types/` or `tests/optimizer/`.

- **Name the removed placeholders instead.** Rejected: a `path::QualifiedName` citation asserts its
  symbol exists, and the citation gate fails a citation to a deleted test. The removed names belong
  to git.
- **Why the negative is stated.** It is the one sentence a future change can falsify without editing
  this spec, and that is the point: a skip landing in either directory has to face the card's
  contract.
- **The pinning tests run against real models.** The definition-order tests use the managed
  `library` example app (`apps.library.models`), whose `ManyToManyField` columns are migrated, so the
  optimizer's cardinality decisions are asserted against real relations rather than test-only
  fixtures.

## Why scalar override semantics is outside the card

Bears on [Scope][spec-011-scope], closing paragraph.

Scalar field override semantics is a contest between a consumer's class-level annotation and the
synthesized one, independent of when a type is declared, so it is not a definition-order concern.
Card `DONE-019-0.0.6` owns it; its tests live beside the definition-order tests in
`tests/types/test_definition_order.py` (for example
`tests/types/test_definition_order.py::test_annotation_only_scalar_field_override_wins_over_synthesized`).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../../KANBAN.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-011]: ../spec-011-stale_placeholder_cleanup-0_0_4.md
[spec-011-card-snapshot]: ../spec-011-stale_placeholder_cleanup-0_0_4.md#card-snapshot
[spec-011-scope]: ../spec-011-stale_placeholder_cleanup-0_0_4.md#scope

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
