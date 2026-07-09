# Spec: `FieldMeta` single-source-of-truth consolidation and mirror retirement

Target release: `0.0.6` (per [KANBAN.md][kanban] card `DONE-016-0.0.6`).
Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.
Owner: package maintainer.

This file is intentionally lightweight. It preserves the card scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable repository file. Before implementation work starts from this file, expand it into the full builder-format spec described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`.

## Card snapshot

- Card: `DONE-016-0.0.6`
- Status: `done` / Done
- Milestone: `alpha` / Alpha (pre-0.1.0)
- Priority: Medium
- Relative size: M
- Labels: `cleanup`, `field-meta`, `metadata`, `optimizer`, `types`

## Planning note

shipped

## Scope

- **SSoT consolidation.** Three reader sites now read `FieldMeta` from the canonical source on `[DjangoType][glossary-djangotype]Definition.field_map`:
- `django_strawberry_framework/types/base.py:_record_pending_relation`
- `django_strawberry_framework/types/converters.py:resolved_relation_annotation`
- `django_strawberry_framework/types/resolvers.py:_make_relation_resolver`
- **Mirror retirement.** `DjangoType.__init_subclass__` no longer writes the legacy class-attribute mirrors. The optimizer reads from `registry.get_definition(type_cls)` directly at all four former reader sites:
- `optimizer/walker.py:_resolve_field_map`
- `optimizer/walker.py:_walk_selections` (hints read)
- `optimizer/extension.py:_collect_schema_reachable_types`
- `optimizer/extension.py:check_schema`
- All `TODO(spec-fieldmeta-*)` source anchors removed.
- 100% package coverage maintained; no consumer-visible API change.

## Why it matters

- Three reader sites were re-deriving [relation shape][glossary-relation-handling] via `relation_kind(field)` + raw `getattr(field, ...)` instead of reading the `FieldMeta` already on `DjangoTypeDefinition.field_map` — duplicating logic and creating drift surface for any future relation-flag addition.
- `DjangoType.__init_subclass__` was writing legacy class-attribute mirrors (`cls._optimizer_field_map`, `cls._optimizer_hints`) that survived `registry.clear()`, then four optimizer sites read those mirrors instead of the canonical `DjangoTypeDefinition`. Two parallel sources of field metadata with no enforced consistency.

## Other

- internal metadata-architecture refactor; no consumer-visible API change.
- consolidate field metadata onto `DjangoTypeDefinition` (single source of truth) and retire legacy class-attribute mirrors across ~7 reader sites.
- Commit `de35a62` (`refactor(types,optimizer): consolidate metadata onto DjangoTypeDefinition`).
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/extension.py`
- `CHANGELOG.md` (under `[Unreleased] → Changed`)
- Originally tracked as `BACKLOG.md` item 35 ("`FieldMeta` single-source-of-truth consolidation and mirror retirement"). Promoted to a DONE card and removed from `BACKLOG.md` when the work shipped — per `BACKLOG.md`'s "graduate into a `KANBAN.md` card when scheduled" workflow. This is the first `BACKLOG.md` item to graduate; the precedent for shipped items: strike-through with SHIPPED status is fine while the item awaits a release; once a release is imminent, move the item to a `KANBAN.md` `DONE` card and delete it from `BACKLOG.md` so the strategic-differentiation file doesn't keep pointing at completed architecture debt.
- The consolidation eliminates ~7 sites of duplicated relation-shape logic and removes legacy class-attribute residue that previously survived `registry.clear()`. Single source of truth for field metadata reduces drift surface whenever Django adds a new relation flag or changes a descriptor attribute.
- Internal refactor only; no `Meta` key changes, no public surface changes, no consumer-visible behavior changes. Existing tests pass without modification.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../BACKLOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
