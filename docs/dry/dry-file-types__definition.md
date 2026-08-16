# DRY review: `django_strawberry_framework/types/definition.py`

Status: verified

## System trace

`DjangoTypeDefinition` is the canonical metadata record for a collected
`DjangoType` subclass. Single construction site:
`types/base.py::DjangoType.__init_subclass__` → `DjangoTypeDefinition(...)` →
`registry.register_with_definition` + `cls.__django_strawberry_definition__`.

**Owned slots (construction-time, treated immutable by readers):**
`origin`, `model`, `name`, `description`, `fields_spec`, `exclude_spec`,
`selected_fields`, `field_map` (`FieldMeta` map), `optimizer_hints`,
`has_custom_get_queryset`, the four `consumer_*_fields` frozensets +
`consumer_authored_fields`, `primary`, `interfaces`, sidecars
(`filterset_class` / `orderset_class` / `fields_class`), `connection`,
`cursor_field`, `relation_shapes`, `globalid_strategy`.

**Finalization-time writers (documented invariants):**
- `types/finalizer.py` → `relation_connections`, `finalized`
- `types/relay.py::install_globalid_typename_resolver` →
  `effective_globalid_strategy`

**Owned behavior on the record:**
- `graphql_type_name` — single derivation rule (`Meta.name` or
  `origin.__name__`)
- `related_target_for` — registry-aware relation target lookup + post-finalize
  memo cache
- `has_custom_id_resolver_for` / module helpers
  (`origin_has_custom_id_resolver`, `_resolves_id_off_pk`, …) — shared custom-id
  predicate for the registered path and the walker's definition-less fallback

**Primary readers:** registry decode / inspect, finalizer (sidecar bind +
relation synthesis), optimizer walker / plans, filters/orders owner binding,
connection / relay GlobalID, resolvers, `inspect_django_type`.

Connected surfaces read for this item: `types/base.py` (construction +
`DEFAULT_RELATION_SHAPE` / `_ValidatedMeta`), `types/finalizer.py`,
`optimizer/field_meta.py`, `optimizer/hints.py`, `registry.py`,
`types/relations.py` (`PendingRelation`), `types/relay.py`.

Item-scoped baseline `d92598c0a5e1be3ec798c6648dd3fbfb42b1e953`: empty for
`definition.py` at review start.

## Verification

Searches: `DjangoTypeDefinition`, `DjangoTypeDefinition(`,
`relation_shapes`, `DEFAULT_RELATION_SHAPE`, `FieldMeta.from_django_field`,
`related_target_for`, `origin_has_custom_id_resolver`, `graphql_type_name`,
`definition.(finalized|relation_connections|effective_globalid_strategy)\s*=`,
parallel `@dataclass` / `*Definition` / `*Meta` shapes.

Live default proof (hand-off from `types/base.py`, re-checked independently):

- Docstring (pre-fix) claimed absent `relation_shapes` keys default to
  `"both"`.
- `types/base.py` sets `DEFAULT_RELATION_SHAPE = "connection"` (spec-047
  Decision 5).
- `types/finalizer.py::_synthesize_relation_connections` resolves
  `shapes.get(name, DEFAULT_RELATION_SHAPE)` and documents that default.
- No second hardcoded `"both"` default in production read paths.

Rejected candidates (same-responsibility disproved):

1. **`_ValidatedMeta` vs `DjangoTypeDefinition`** — Transient NamedTuple
   snapshot from `_validate_meta` so gates run once; durable registry record
   adds model/fields/field_map/caches/finalization slots. Different lifetime
   and ownership. Folding would couple construction validation to the
   post-finalize record.

2. **`PendingRelation` vs definition slots** — Collection-time scaffolding for
   unresolved relation targets; production consumers read live `FieldMeta`
   from `field_map`. Intentional dual representation (spec-010 / import-order).

3. **`FieldMeta` rebuilds in converters/resolvers** — Canonical map is built
   once in `base.py`. Fallbacks exist when a parent type has no registered map;
   walker documents the dual `FieldMeta | raw` contract. Not a second
   definition shape; ownership stays in `optimizer/field_meta.py`.

4. **`definition.primary` vs `registry._primaries`** — Write-once introspection
   mirror vs runtime `primary_for` predicate; already documented. Collapsing
   would remove the consumer introspection channel or force every reader
   through registry.

5. **`has_custom_id_resolver_for` + `origin_has_custom_id_resolver`** — Already
   the correct split (memoized method + shared free function for the
   definition-less fallback). Further merge would reintroduce drift risk the
   free function was added to prevent.

6. **Class attribute `__django_strawberry_definition__` + registry map** —
   Dual pointer for hot-path attribute access vs model-keyed registry APIs.
   Same object identity; not duplicated state to consolidate.

## Opportunities

### 1. Stale `relation_shapes` absent-key default in class docstring

- **Repeated responsibility:** Documented default for absent
  `Meta.relation_shapes` keys must match the live synthesis default.
- **Sites:** `DjangoTypeDefinition` class docstring (stale `"both"`); live
  owner `types/base.py::DEFAULT_RELATION_SHAPE`; consumer
  `finalizer.py::_synthesize_relation_connections`.
- **Evidence:** Pre-fix docstring text vs `DEFAULT_RELATION_SHAPE =
  "connection"` and `shapes.get(name, DEFAULT_RELATION_SHAPE)`. Spec-047
  Decision 5 flipped the default; docstring was left behind.
- **Owner:** This file's docstring (docs on the definition record). The
  constant itself correctly lives in `types/base.py`.
- **Consolidation:** Point the invariant at `DEFAULT_RELATION_SHAPE` and the
  current `"connection"` / spec-047 value — no code-path change.
- **Proof:** Diff is docstring-only. Behavioral coverage of the default already
  lives with finalizer / resource-policy tests (e.g. live sibling-list
  expectations under the `"connection"` default). No new permanent test for
  docstring text.
- **Risks / non-goals:** Do not move `DEFAULT_RELATION_SHAPE` into
  `definition.py`; vocabulary ownership stays in `base.py`.

## Judgment

One confirmed doc-truth fix on the owner; no structural consolidations.
`DjangoTypeDefinition` is already the single canonical metadata record with a
single construction site and narrow finalization writers. Parallel-looking
dataclasses and FieldMeta fallbacks are intentional lifecycle / dual-contract
splits.

## Implementation (Worker 1)

- Updated the `relation_shapes` invariant in
  `django_strawberry_framework/types/definition.py` so absent keys default to
  `DEFAULT_RELATION_SHAPE` from `types/base.py` (currently `"connection"`,
  spec-047 Decision 5).
- Ran `uv run ruff format` / `uv run ruff check --fix` on the edited file.
- Deferred pytest: none run (docstring-only; autonomous DRY item). Behavioral
  default already covered elsewhere.
- Changelog: not warranted (docstring truth only); no CHANGELOG edit.
- Concurrent work: ignored; no reverts; no commit.

Scoped diff vs `ITEM_BASELINE` `d92598c0a5e1be3ec798c6648dd3fbfb42b1e953`:

```text
django_strawberry_framework/types/definition.py
  — docstring: absent relation_shapes keys → DEFAULT_RELATION_SHAPE / "connection"
docs/dry/dry-file-types__definition.md
  — this artifact (new)
```

Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced construction, default ownership, and rejected candidates against
present-day source. Item-scoped diff vs
`d92598c0a5e1be3ec798c6648dd3fbfb42b1e953` is docstring-only (absent
`relation_shapes` keys → `DEFAULT_RELATION_SHAPE` / `"connection"` /
spec-047). No unrelated absorption.

**Live default matches docstring**

- `types/base.py::DEFAULT_RELATION_SHAPE = "connection"` (spec-047 Decision 5).
- `types/finalizer.py::_synthesize_relation_connections` resolves
  `shapes.get(name, DEFAULT_RELATION_SHAPE)`.
- Production package has no second hardcoded `"both"` absent-key default;
  historical `"both"` mentions remain only in shipped specs / kanban narrative.

**Rejected candidates (challenged; still separate)**

1. `_ValidatedMeta` — NamedTuple validation snapshot from `_validate_meta`;
   lacks `field_map`, caches, finalization writers. Durable record is
   `DjangoTypeDefinition` built once in `__init_subclass__`.
2. `PendingRelation` — collection/finalization scaffolding; live readers use
   `field_map` `FieldMeta` (`types/relations.py` documents the split).
3. `FieldMeta` rebuilds — canonical map owned at construction; resolver/
   converter fallbacks are dual-contract / test-double paths, not a second
   definition shape.
4. `definition.primary` vs `registry._primaries` / `primary_for` — write-once
   introspection mirror vs runtime predicate; package code uses registry.
5. `has_custom_id_resolver_for` + `origin_has_custom_id_resolver` — memoized
   method delegates to the free function; walker definition-less fallback
   imports the same free function (`optimizer/walker.py::_has_custom_id_resolver`).
6. `__django_strawberry_definition__` + registry map — dual pointer, same
   object identity; not duplicated state.

**Missed consolidations:** none for this target. `graphql_type_name` remains
the single derivation owner; callers already read the property.

Plan checkbox marked `[x]`. No commit; no pytest; concurrent work untouched.
