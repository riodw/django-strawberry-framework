# Rationale: spec-016 — FieldMeta single-source-of-truth consolidation and mirror retirement (deliberation, rejected alternatives)

Deliberative companion to [`spec-016-fieldmeta_consolidation-0_0_6.md`][spec-016]. The spec is the
contract; this file records why relation shape has the one store it has. The spec has no numbered
Decisions, so each entry is keyed to a spec section.

## Why the spec is a card snapshot

Bears on [Card snapshot][spec-016-card-snapshot].

The file is the card's `SpecDoc` target, which the kanban app requires of every `done` card
(`examples/fakeshop/apps/kanban/signals.py::_validate_done_card_has_spec`). The snapshot names only
the card: labels, priority, relative size, and item rows are rendered into [KANBAN.md][kanban] from
the Kanban database, and a hand copy drifts on the next board edit.

## Why relation shape has one store

Bears on [Single source of truth][spec-016-ssot] and [No class-attribute mirror][spec-016-mirror].

`FieldMeta` on `DjangoTypeDefinition.field_map` is built once per type, so a new relation flag or a
change to a Django descriptor attribute is a one-site change. A second store on the class would
outlive `registry.clear()`, and a cleared registry with a live class attribute is two answers for
one type with nothing to reconcile them, so the registry is the only lifetime field metadata has.

- **Every reader site is named by `path::QualifiedName`.** An audit that finds a re-derivation inside
  a cited function can then tell drift from design: the spec lists the readers and the one bounded
  exception, so anything else is drift.
- **`_build_annotations` is not a reader.** The pending record carries only the raw field name that
  keys `field_map`; finalization reads cardinality and nullability from the map, so the record cannot
  hold a stale copy.
- **Unregistered-model planning stamps `FieldMeta` too.** The walker's fallback builds the map
  through `FieldMeta.from_django_field`, so every walker consumer reads one shape whether or not the
  model has a registered type.

## Why the test-double fallbacks are a bounded exception

Bears on [Bounded exceptions to the single-source rule][spec-016-exceptions].

The fallbacks in `types/resolvers.py::_field_meta_for_resolver` and
`types/converters.py::resolved_relation_annotation` let unit tests exercise the cardinality branches
without constructing a registered `DjangoType`. They stay honest because
`FieldMeta._from_field_shape` is the canonical builder's own shape helper, so the fallback yields the
value the canonical path would yield on the same descriptor. Production callers pass
`parent_type=cls` and never reach them.

## Why the classifiers are called on raw descriptors

Bears on [Out of scope][spec-016-out-of-scope] and [Why it matters][spec-016-why].

The duplication the card removed is re-deriving shape for a field a registered definition already
describes, not the use of `utils/relations.py::relation_kind`. That classifier is the one
implementation of the classification: `FieldMeta.relation_kind` and `FieldMeta.is_many_side`
delegate to it, and sites that classify a descriptor obtained outside any definition (filter-set
builders, join taxonomy, connection-shape checks) call it directly by design. Framing the
duplication as "calls to `relation_kind(field)`" would make those sites read as a regression.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../../KANBAN.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-016]: ../spec-016-fieldmeta_consolidation-0_0_6.md
[spec-016-card-snapshot]: ../spec-016-fieldmeta_consolidation-0_0_6.md#card-snapshot
[spec-016-exceptions]: ../spec-016-fieldmeta_consolidation-0_0_6.md#bounded-exceptions-to-the-single-source-rule
[spec-016-mirror]: ../spec-016-fieldmeta_consolidation-0_0_6.md#no-class-attribute-mirror
[spec-016-out-of-scope]: ../spec-016-fieldmeta_consolidation-0_0_6.md#out-of-scope
[spec-016-ssot]: ../spec-016-fieldmeta_consolidation-0_0_6.md#single-source-of-truth
[spec-016-why]: ../spec-016-fieldmeta_consolidation-0_0_6.md#why-it-matters

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
