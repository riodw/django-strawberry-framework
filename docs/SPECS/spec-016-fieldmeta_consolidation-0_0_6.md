# Spec: FieldMeta single-source-of-truth consolidation and mirror retirement

Target release: `0.0.6` (per [KANBAN.md][kanban] card `DONE-016-0.0.6`).
Status: shipped.
Owner: package maintainer.

Deliberation and this spec's change record live in its companion [rationale file][spec-016-rationale]: which two commits the card actually shipped, why three of the reader sites this spec once named were stale on the day it shipped, what the two bounded exceptions to the single-source rule buy and what they cost, why the free relation classifiers are deliberately still called on raw Django fields, and every claim this spec once made and may no longer make.

## Card snapshot

- Card: `DONE-016-0.0.6`, status `done`, milestone `alpha` (pre-`0.1.0`).
- The card's other board fields — labels, priority, relative size, and its item rows — belong to the Kanban database and are rendered into [KANBAN.md][kanban]. This section identifies the card; it does not restate them.

## Scope

### Single source of truth

`FieldMeta` on `DjangoTypeDefinition.field_map` is the canonical store of relation shape — cardinality, nullability, `attname`, `related_model`, FK target columns — for every registered [`DjangoType`][glossary-djangotype]. It is built once per type at class-creation time. No consumer of [relation shape][glossary-relation-handling] re-derives that shape from raw `getattr` reads on a Django field descriptor when a canonical `FieldMeta` is reachable.

Seven reader sites hold that rule, three in `types/` and four in `optimizer/`:

- `django_strawberry_framework/types/base.py::_build_annotations` #"field_meta = field_map[snake_case(field.name)]" — reads the canonical entry and carries `relation_kind` / `nullable` onto the `PendingRelation` record.
- `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"field_meta = definition.field_map[snake_case(pending.field_name)]" — performs the canonical read and passes it explicitly into `django_strawberry_framework/types/converters.py::resolved_relation_annotation` via its keyword-only `field_meta` parameter. `resolved_relation_annotation` itself reads only `meta.is_many_side` / `meta.nullable` and derives nothing.
- `django_strawberry_framework/types/resolvers.py::_field_meta_for_resolver` — resolves `registry.get_definition(parent_type)` then `definition.field_map.get(field.name)`; `::_make_relation_resolver` consumes the returned `FieldMeta`'s `relation_kind`, `is_many_side`, `related_model`, and `attname`. Production callers MUST pass `parent_type=cls`.
- `django_strawberry_framework/optimizer/walker.py::_resolve_field_map` — resolves the registered `DjangoType` and returns `definition.field_map`. This is the walker's only field-map source; the brittle Django-private `_meta` access is centralized here.
- `django_strawberry_framework/optimizer/walker.py::_resolve_optimizer_hints` — returns `definition.optimizer_hints or {}`. It is called by `::_walk_selections` and is **injected** into the nested-connection planner (`walker.py` #"resolve_optimizer_hints=_resolve_optimizer_hints" consumed at `django_strawberry_framework/optimizer/nested_planner.py` #"hints_map = resolve_optimizer_hints(definition)"), so the planner inherits the canonical read rather than opening a second source.
- `django_strawberry_framework/optimizer/extension.py::_collect_schema_reachable_types` — gates schema reachability on `registry.get_definition(origin) is not None`.
- `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema` — reads `definition.field_map` and `definition.optimizer_hints` for every schema-reachable type.

### Bounded exceptions to the single-source rule

Two exceptions exist by design. Both are documented at their site, and neither is drift:

- **The walker's dual contract.** `optimizer/walker.py::_resolve_field_map` returns `FieldMeta` values for a model with a registered `DjangoType` and **raw Django field objects** from a `model._meta.get_fields()` walk for a model without one. `name` and `is_relation` are guaranteed on both shapes (`optimizer/field_meta.py::_DjangoFieldLike`) and are read directly; any other attribute is read directly only where both shapes carry it, and a `FieldMeta`-only attribute must never be read off that map without a `getattr(..., default)`. That rule, not a blanket `getattr` discipline, is what makes the two shapes safe to coexist. The site's docstring is the standing statement of this contract. `types/resolvers.py::_field_meta_for_resolver` shares the policy (prefer the canonical definition-backed metadata, fall back when it is unreachable) but not this dual return shape: it returns a `FieldMeta` unconditionally, so its callers read every attribute directly.
- **Test-double fallbacks.** `types/resolvers.py::_field_meta_for_resolver` falls back to `FieldMeta._from_field_shape(field, is_relation=True)` for a descriptor lacking `is_relation`, else to `FieldMeta.from_django_field(field)`; `types/converters.py::resolved_relation_annotation` re-derives via `FieldMeta.from_django_field` when its `field_meta` argument is `None`. Both paths exist ONLY for direct callers exercising cardinality branches without a registered `DjangoType`, and both produce a `FieldMeta` observably identical to the canonical builder's on the same descriptor. No production call site reaches either.

### Mirror retirement

`DjangoType.__init_subclass__` writes no legacy class-attribute mirror of the field map or the optimizer hints. `cls._optimizer_field_map` and `cls._optimizer_hints` do not exist as declarations or as reads anywhere in the package, its tests, the example project, or `scripts/`; the optimizer resolves metadata through `registry.get_definition(...)` at every site listed above. A class-attribute mirror survives `registry.clear()`, so its absence is what makes the registry the only lifetime that field metadata has.

No `TODO(spec-fieldmeta-ssot)` or `TODO(spec-fieldmeta-mirror-retirement)` anchor remains in source.

### Out of scope

Calling the shared classifiers `relation_kind(field)` / `is_many_side_relation_kind(...)` from `django_strawberry_framework/utils/relations.py` on a **raw Django field descriptor** was never in this card's scope and is still correct. Those helpers are the one implementation of the classification, and `FieldMeta.relation_kind` / `FieldMeta.is_many_side` delegate to them rather than duplicating the ladder. This card's contract is narrower and specific: where relation shape is needed for a field belonging to a registered `DjangoType`, read the `FieldMeta` the definition already holds instead of re-deriving it. A site that classifies a raw descriptor it obtained outside a definition — a filter-set builder, a join-taxonomy walk, a connection-shape check — is not a duplicated reader and does not fall under this rule.

## Why it matters

- Re-deriving relation shape at each reader multiplies the drift surface of every future relation flag or descriptor-attribute change by the reader count. One canonical `FieldMeta` read makes that a one-site change.
- Two parallel metadata stores with no enforced consistency is a correctness hazard rather than a tidiness one: the class-attribute mirrors survived `registry.clear()`, so a cleared registry and a live mirror could disagree about the same type's fields with nothing to detect it.
- The consolidation is a prerequisite for any later feature that reads per-field metadata — cost analysis, resource policy weighting, new relation kinds — each of which would otherwise widen the duplication before narrowing it.

## Change population

The card shipped in two commits: `de35a622` (implementation) and `2bd7cb84` (documentation and board graduation). Together they touched:

- **Package source (6):** `optimizer/extension.py`, `optimizer/field_meta.py`, `optimizer/walker.py`, `types/base.py`, `types/converters.py`, `types/resolvers.py`.
- **Tests (6):** `tests/optimizer/test_definition_order.py`, `tests/optimizer/test_extension.py`, `tests/optimizer/test_field_meta.py`, `tests/optimizer/test_walker.py`, `tests/types/test_relay_interfaces.py`, `tests/types/test_resolvers.py`. Existing tests did **not** pass unmodified: the consolidation changed the internal seams those files assert against, and the same change re-pinned them.
- **Standing docs:** `CHANGELOG.md` (under `[Unreleased]` -> `Changed`), `KANBAN.md`, plus four per-cycle review documents under `docs/` that closed with their own cycle.

Neither commit touched `django_strawberry_framework/__init__.py`, so the change added, removed, or renamed no public export. Both landed under the repository's standing `fail_under = 100` coverage gate (`pyproject.toml` `[tool.coverage.report]`), which CI enforces on every push.

## Compatibility

Internal metadata-architecture refactor. No `Meta` key added, removed, or re-interpreted; no public surface change; no consumer-visible behavior change. The retired class attributes were private by name and undocumented, so nothing supported depended on them.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: ../../BACKLOG.md
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
