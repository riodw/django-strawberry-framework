# Spec: FieldMeta single-source-of-truth consolidation and mirror retirement

Target release: `0.0.6` (per [KANBAN.md][kanban] card `DONE-016-0.0.6`).
Status: shipped.
Owner: package maintainer.

Why relation shape has one store, what the bounded exception to that rule buys and costs, and why the free relation classifiers are deliberately called on raw Django fields lives in its companion [rationale file][spec-016-rationale].

## Card snapshot

- Card: `DONE-016-0.0.6`, status `done`, milestone `alpha` (pre-`0.1.0`).
- The card's other board fields — labels, priority, relative size, and its item rows — belong to the Kanban database and are rendered into [KANBAN.md][kanban]. This section identifies the card; it does not restate them.

## Scope

### Single source of truth

`FieldMeta` on `DjangoTypeDefinition.field_map` is the canonical store of relation shape — cardinality, nullability, `attname`, `related_model`, FK target columns, a link's carrier columns and the columns they target (`link_carrier_attnames` / `link_target_attnames`, for a forward single relation and a reverse FK / reverse OneToOne), and the non-pk source columns a reverse, M2M or generic link targets (`source_target_attnames`), all three read through `django_strawberry_framework/utils/relations.py::relation_link` — for every registered [`DjangoType`][glossary-djangotype]. It is built once per type at class-creation time. No consumer of [relation shape][glossary-relation-handling] re-derives that shape from raw `getattr` reads on a Django field descriptor when a canonical `FieldMeta` is reachable.

Six reader sites hold that rule, two in `types/` and four in `optimizer/`. `django_strawberry_framework/types/base.py::_build_annotations` reads none: the `PendingRelation` record it builds for each auto-synthesized relation carries only the raw `field_name` that keys `field_map`, and no cardinality or nullability.

- `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"field_meta = definition.field_map[pending.field_name]" — performs the canonical read and passes it explicitly into `django_strawberry_framework/types/converters.py::resolved_relation_annotation` via its keyword-only `field_meta` parameter. `resolved_relation_annotation` itself reads only `meta.is_many_side` / `meta.nullable` and derives nothing.
- `django_strawberry_framework/types/resolvers.py::_field_meta_for_resolver` — resolves `registry.get_definition(parent_type)` then `definition.field_map.get(field.name)`; `::_make_relation_resolver` consumes the returned `FieldMeta`'s `relation_kind`, `is_many_side`, `related_model`, and `attname`. Production callers MUST pass `parent_type=cls`.
- `django_strawberry_framework/optimizer/walker.py::_resolve_field_map` — resolves the registered `DjangoType` and returns `definition.field_map`. When no type is registered, the same helper stamps `FieldMeta.from_django_field` over `model._meta.get_fields()`, keyed by raw `f.name`. Both paths yield `FieldMeta`; the brittle Django-private `_meta` access is centralized here.
- `django_strawberry_framework/optimizer/walker.py::_resolve_optimizer_hints` — returns `definition.optimizer_hints or {}`. It is called by `::_walk_selections` and is **injected** into the nested-connection planner (`django_strawberry_framework/optimizer/walker.py` #"resolve_optimizer_hints=_resolve_optimizer_hints," consumed at `django_strawberry_framework/optimizer/nested_planner.py` #"hints_map = resolve_optimizer_hints(definition)"), so the planner inherits the canonical read rather than opening a second source.
- `django_strawberry_framework/optimizer/extension.py::_collect_schema_reachable_types` — gates schema reachability on `registry.get_definition(origin) is not None`.
- `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema` — reads `definition.field_map` and `definition.optimizer_hints` for every schema-reachable type.

### Bounded exceptions to the single-source rule

One exception exists by design. It is documented at its site, and is not drift:

- **Test-double fallbacks.** `types/resolvers.py::_field_meta_for_resolver` falls back to `FieldMeta._from_field_shape(field, is_relation=True)` for a descriptor lacking `is_relation`, else to `FieldMeta.from_django_field(field)`; `types/converters.py::resolved_relation_annotation` re-derives via `FieldMeta.from_django_field` when its `field_meta` argument is `None`. Both paths exist ONLY for direct callers exercising cardinality branches without a registered `DjangoType`, and both produce a `FieldMeta` observably identical to the canonical builder's on the same descriptor. No production call site reaches either.

Unregistered-model planning is not an exception: `optimizer/walker.py::_resolve_field_map` stamps the fallback map through `FieldMeta.from_django_field` over every `get_fields()` entry, a multi-column forward `ForeignObject` included (only `DjangoType` declaration refuses one; `tests/optimizer/test_walker.py::test_unregistered_field_map_stamps_a_multi_column_forward_foreign_object`), so walker callers read the same shape as the registered path. The nested-connection window partition re-fetches the live descriptor via `optimizer/nested_planner.py::_raw_relation_field` because the forward-M2M reverse query name lives only on the descriptor's `remote_field`, which `FieldMeta` does not carry.

### No class-attribute mirror

`DjangoType.__init_subclass__` writes no class-attribute mirror of the field map or the optimizer hints; the optimizer resolves metadata through `registry.get_definition(...)` at every site listed above. A class-attribute mirror survives `registry.clear()`, so its absence is what makes the registry the only lifetime that field metadata has.

### Out of scope

Calling the shared classifiers `relation_kind(field)` / `is_many_side_relation_kind(...)` from `django_strawberry_framework/utils/relations.py` on a **raw Django field descriptor** is outside this card's scope and is correct. Those helpers are the one implementation of the classification, and `FieldMeta.relation_kind` / `FieldMeta.is_many_side` delegate to them rather than duplicating the ladder. This card's contract is narrower and specific: where relation shape is needed for a field belonging to a registered `DjangoType`, read the `FieldMeta` the definition already holds instead of re-deriving it. A site that classifies a raw descriptor it obtained outside a definition — a filter-set builder, a join-taxonomy walk, a connection-shape check — is not a duplicated reader and does not fall under this rule.

## Why it matters

- Re-deriving relation shape at each reader multiplies the drift surface of every future relation flag or descriptor-attribute change by the reader count. One canonical `FieldMeta` read makes that a one-site change.
- Two parallel metadata stores with no enforced consistency is a correctness hazard rather than a tidiness one: a class-attribute mirror survives `registry.clear()`, so a cleared registry and a live mirror could disagree about the same type's fields with nothing to detect it.
- The consolidation is a prerequisite for any later feature that reads per-field metadata — cost analysis, resource policy weighting, new relation kinds — each of which would otherwise widen the duplication before narrowing it.

## Compatibility

Internal metadata architecture. No `Meta` key and no public export is involved, and there is no consumer-visible behavior: the field map and optimizer hints are read only through `registry.get_definition(...)`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling

<!-- docs/SPECS/ -->
[spec-016-rationale]: appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
