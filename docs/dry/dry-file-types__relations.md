# DRY review: `django_strawberry_framework/types/relations.py`

Status: verified

## System trace

This module owns the **collection→finalization scaffolding** for auto-synthesized
relation fields (spec-010 / definition-order independence):

| Symbol | Role |
| --- | --- |
| `PendingRelation` | Frozen record: source type/model, raw Django `field_name`, `django_field`, `related_model`, plus snapshot `relation_kind` / `nullable` |
| `PendingRelationAnnotation` + `_PendingRelationAnnotationMeta` | Class-as-sentinel installed in `cls.__annotations__` until rewrite; metaclass `__repr__` shapes the Strawberry `TypeError` if finalize was skipped |

Lifecycle (single producer / single consumer):

1. **Produce** — `types/base.py::_build_annotations` always appends a
   `PendingRelation` and sets `PendingRelationAnnotation` for every
   auto-synthesized relation (consumer-authored names short-circuit; no
   eager bind — import-order trap closed by spec-018).
2. **Store** — `DjangoType.__init_subclass__` →
   `TypeRegistry.add_pending_relation`; discard by identity via
   `discard_pending` (uses `id()`, not `__eq__`/`__hash__`).
3. **Consume** — `types/finalizer.py::finalize_django_types` Phase 1 classifies
   unresolved / consumer_authored / resolved; rewrite is the sole
   `__annotations__[field] = …` site, calling
   `types/converters.py::resolved_relation_annotation` with live
   `FieldMeta` from `definition.field_map[snake_case(pending.field_name)]`,
   then `discard_pending` on the original record instances.

Connected surfaces traced as evidence (not reopened):

- `types/base.py::_build_annotations` — producer (verified earlier).
- `types/finalizer.py::finalize_django_types` — consumer + rewrite (verified).
- `registry.py` — list storage / identity discard; does not own the record type.
- `types/converters.py::resolved_relation_annotation` — annotation *shape*
  owner (list / nullable / bare); not scaffolding.
- `utils/relations.py::relation_kind` — GraphQL/runtime cardinality classifier
  shared by FieldMeta / optimizer; different module name, different concern.
- `optimizer/join_taxonomy.py` — plan-time join taxonomy from
  `relation_kind(field)`; never touches pending records.
- Tests: `tests/types/test_relations.py` (identity `__hash__`),
  `tests/test_registry.py` (sentinel + discard identity),
  definition-order / base collection pins.

Item-scoped baseline `fd8aadc831692a459f33c22e94d858ead47bcc06`:
`git diff … -- django_strawberry_framework/types/relations.py` empty at review
start and after judgment (proved zero-edit).

## Verification

Searches (package-wide): `PendingRelation`, `PendingRelationAnnotation`,
`_PendingRelationAnnotationMeta`, `resolved_relation_annotation`,
`add_pending_relation` / `iter_pending_relations` / `discard_pending`,
`__hash__ = object.__hash__`, `__annotations__[…] =`,
`pending.relation_kind` / `pending.nullable`, `unfinalized DjangoType relation`,
`lazy_ref` / parallel deferred-relation shapes.

Optional `export_dry_review.py audit --target …/types/relations.py`: reverse
imports match the producer/consumer/registry/test graph above; no exact-body
duplicate of the scaffolding types. Orientation only.

Contract comparisons that disproved consolidation:

1. **`types/relations.py` vs `utils/relations.py`** — Scaffolding record+sentinel
   vs cardinality/path taxonomy. Same English word “relations”; different
   change axes. `PendingRelation.relation_kind` is a typed slot of
   `RelationKind`; the classifier stays in utils. Merging modules would couple
   type-collection lifecycle to optimizer/filter path walking.

2. **`resolved_relation_annotation` living in converters (not here)** — Read
   annotation shape is converters’ job (already verified with
   `relation_input_annotation`). Moving it beside the sentinel would either
   pull FieldMeta into scaffolding or split annotation policy across two
   owners. Finalizer correctly bridges record → converter.

3. **Snapshot `relation_kind` / `nullable` on `PendingRelation` vs live
   `FieldMeta`** — Production Phase 1 never reads `pending.relation_kind` or
   `pending.nullable` (confirmed: zero attribute reads under package/tests/
   examples). Rewrite always re-reads `definition.field_map`. Snapshots are
   intentional self-contained introspection fields from the foundation shape
   (spec-010), not a second rewrite policy. Removing them is dead-slot cleanup
   / public dataclass shrink, not consolidating two active owners of one rule.
   Drift risk is theoretical: nothing updates FieldMeta between collection and
   finalize in a way these snapshots participate in.

4. **`PendingRelation.__hash__ = object.__hash__` vs `discard_pending`’s
   `id()` filter** — Complementary, not duplicated. Discard deliberately avoids
   hash/eq; the override keeps the frozen dataclass set-membership-safe when
   `django_field` is unhashable (pinned by `tests/types/test_relations.py`).
   Collapsing to one mechanism would either break set use or re-couple discard
   to dataclass hashing.

5. **Other package “sentinels” / lazy forward-refs** — Mutation/filter/order
   `strawberry.lazy` / `_lazy_ref`, UNSET, probe rows, etc. are different
   domains. Only one class-as-annotation placeholder exists for unfinalized
   DjangoType relations; error repr string is unique.

6. **`optimizer/join_taxonomy.py`** — Consumes `relation_kind` at plan time for
   join shapes; no pending-record parallel and no annotation rewrite.

7. **Folding `PendingRelation` into `registry.py`** — Registry stores and
   discards; type-system producer/consumer own construction and rewrite.
   Moving the dataclass into the registry would invert the types→registry
   dependency direction the folder already documents.

## Opportunities

None — producer, storage, rewrite, and annotation-shape owners are already
single-sited; apparent neighbors encode distinct contracts (taxonomy vs
scaffolding, read annotation vs write id annotation, live FieldMeta vs
unused introspection snapshots).

## Judgment

`types/relations.py` is a narrow, correctly owned scaffolding module: one
record type, one sentinel, one producer, one rewrite consumer, one identity
discard path. No consolidation is warranted. Strongest rejected candidates are
(1) merging with `utils/relations.py`, (2) relocating
`resolved_relation_annotation` here, and (3) deleting unused snapshot slots as
a “DRY” move.

**Deferred / out of scope**

- `registry.py` module docstring still names
  `types.finalizer.resolved_relation_annotation`; the function lives in
  `types/converters.py`. Stale cross-path text on an already-reviewed sibling —
  not fixed in this item (concurrent/out of scope; no pytest).
- No permanent test or production edits; no deferred pytest for this item.

**Scoped diff statement:** relative to item baseline
`fd8aadc831692a459f33c22e94d858ead47bcc06`, the only path this worker adds is
`docs/dry/dry-file-types__relations.md`.
`django_strawberry_framework/types/relations.py` is unchanged. Ready for
Worker 2.

## Independent verification (Worker 2)

**Outcome: verified** (zero-edit claim stands).

**Scoped diff.**
`git diff fd8aadc831692a459f33c22e94d858ead47bcc06 -- django_strawberry_framework/types/relations.py`
is empty. Working tree has no modifications to the target; only this artifact
and the plan checkbox are Worker 2 touches for the item.

**Re-traced lifecycle (independent of Worker 1 narrative).**

1. Produce — `types/base.py::_build_annotations` relation branch always
   `PendingRelation(...)` + `annotations[field.name] = PendingRelationAnnotation`
   for non-consumer-authored auto-synthesized relations (eager bind gone).
2. Store — `DjangoType.__init_subclass__` loops `registry.add_pending_relation`.
3. Rewrite — sole `__annotations__[…] =` site is
   `types/finalizer.py::finalize_django_types` Phase 1 calling
   `types/converters.py::resolved_relation_annotation(..., field_meta=…)` from
   `definition.field_map[snake_case(pending.field_name)]`, then
   `discard_pending` by `id()`.
4. Shape policy — `resolved_relation_annotation` lives only in converters;
   finalizer imports it, does not redefine it.

**Challenges to rejected candidates (source evidence).**

1. **Merge with `utils/relations.py`.** That module owns `relation_kind` /
   path taxonomy for FieldMeta, resolvers, optimizer (`RelationKind`,
   `classify_path`, etc.). This module owns collection→finalize scaffolding
   only and merely *types* a snapshot slot as `RelationKind`. Same English
   word; different change axes. Merge would couple type-collection lifecycle
   to optimizer/filter path walking. Rejection stands.

2. **Move `resolved_relation_annotation` here.** Function body is list /
   nullable / bare annotation from `FieldMeta` — same family as other
   converters annotation builders. Finalizer is the bridge; moving the helper
   beside the sentinel would either pull FieldMeta into scaffolding or split
   annotation policy. Rejection stands.

3. **Drop unused `relation_kind` / `nullable` snapshot slots as a DRY fix.**
   Package-wide: zero `pending.relation_kind` / `pending.nullable` *reads*;
   only construction writes in `_build_annotations`. Production rewrite uses
   live `FieldMeta`. Removing slots is dead-field / public-shape cleanup, not
   consolidating two active owners of one rewrite rule. Rejection stands for
   this DRY item.

4. **`__hash__ = object.__hash__` vs `discard_pending` `id()`.** Complementary:
   discard never hashes; override keeps frozen dataclass set-safe when
   `django_field` is unhashable (`tests/types/test_relations.py`). Not
   duplicated policy.

5. **Fold record into `registry.py`.** Registry stores/discards; producer and
   rewrite consumer are in `types/`. Moving the dataclass would invert the
   types→registry dependency the folder already documents. Rejection stands.

6. **Other deferred/lazy shapes (`strawberry.lazy` / `_lazy_ref`, UNSET, etc.).**
   Different domains; only one class-as-annotation placeholder for unfinalized
   DjangoType relations (unique error repr). Rejection stands.

**Missed-consolidation search.** Also checked: sole annotation rewrite site;
   no second pending-record type; `PendingRelation` not re-exported from package
   `__init__`; optimizer `join_taxonomy` consumes `relation_kind(field)` only —
   never pending records. No additional consolidation opportunity found.

**Deferred registry docstring.** `registry.py` module docstring still names
`types.finalizer.resolved_relation_annotation`; import/definition are in
`types/converters.py` (finalizer only imports). That is cross-path text on the
already-verified `registry.py` plan item — correctly not this item’s ownership
or checkbox.

**Checkbox.** Plan item marked `[x]`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
