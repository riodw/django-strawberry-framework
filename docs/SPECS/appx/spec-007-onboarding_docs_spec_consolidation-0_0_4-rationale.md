# Rationale: spec-007 — 0.0.4 onboarding docs and spec consolidation (deliberation, rejected alternatives)

Deliberative companion to [`spec-007-onboarding_docs_spec_consolidation-0_0_4.md`][spec-007]. The
spec is the contract; this file records why it has the shape it has. The spec has no numbered
Decisions, so each entry is keyed to a spec section.

## Why the spec is a card snapshot

Bears on [Card snapshot][spec-007-card-snapshot].

The card's work is documentation, and the spec identifies the card rather than planning slices.

- **Expand it into a full builder-format spec.** Rejected. The card shipped no package surface, so
  there is nothing for slices, tests, or Decisions to describe; an expansion would present an
  inferred deliberation in the shape readers trust as a contract.
- **Delete the file.** Refused by the kanban app. A `done` card cannot be saved without a linked
  `SpecDoc` (`examples/fakeshop/apps/kanban/signals.py::_validate_done_card_has_spec`) or without a
  glossary link (`examples/fakeshop/apps/kanban/signals.py::_validate_done_card_has_glossary_link`),
  and neither can be deleted off a done card
  (`examples/fakeshop/apps/kanban/signals.py::protect_done_card_spec`,
  `examples/fakeshop/apps/kanban/signals.py::protect_done_card_glossary_link`). This file is the
  `SpecDoc` target, and its `-terms.csv` row is what `manage.py import_spec_terms` reconciles into the
  card's glossary link.

*Why the snapshot names only the card.* Labels, priority, relative size, and the card's item rows are
rendered into [KANBAN.md][kanban] from the Kanban database on every board edit. A hand-copied render
in a file nothing re-renders drifts on the next edit, so the spec states only the card's identity,
the one board fact a `SpecDoc` target is entitled to state.

## Why `## Scope` states roles, not contents

Bears on [Scope][spec-007-scope].

Each bullet says which question a file answers (map, usage, contributing, catalog, layout, release
record), never what the file contains. Content inventories of the documentation set go stale with
every card that writes into those files, while the division of responsibility holds.

- **Rewrite `## Scope` as a current inventory** of each file's sections. Rejected: it owes a
  reconciliation at every release and duplicates the map the root [`README.md`][root-readme] owns.
- **Restate the spec lifecycle** (filename pattern, fold-in targets, archival) in the spec.
  Rejected: [`AGENTS.md`][agents] and [`BUILD.md`][build] `## Spec and build-plan filename pattern`
  own it, and a borrowed copy goes stale while the owners move. The fold-in bullet points at them.
- **The glossary link sits in the `docs/README.md` bullet** because runtime behavior, optimizer
  behavior included, is what that file documents for consumers. It is the spec's only glossary
  carrier, so the `-terms.csv` row depends on it.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[kanban]: ../../../KANBAN.md
[root-readme]: ../../../README.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-007]: ../spec-007-onboarding_docs_spec_consolidation-0_0_4.md
[spec-007-card-snapshot]: ../spec-007-onboarding_docs_spec_consolidation-0_0_4.md#card-snapshot
[spec-007-scope]: ../spec-007-onboarding_docs_spec_consolidation-0_0_4.md#scope

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
