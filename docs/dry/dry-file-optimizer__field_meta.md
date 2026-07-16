# DRY review: `django_strawberry_framework/optimizer/field_meta.py`

Status: verified

## System trace

The target owns the **precomputed Django field snapshot** used for
optimizer planning and type annotation: frozen `FieldMeta`, the guarded
builder (`from_django_field` / `_from_field_shape`), and defensive
`_target_pk_name` for related-model PK resolution (including lightweight
stand-ins without `_meta`).

Owned responsibility:

- one relation-shape snapshot (`is_relation`, cardinality flags, `nullable`,
  `attname`, target columns, `accessor_name`, `concrete`, `auto_created`);
- one cardinality-gated nullable rule (many-side → `False`; reverse O2O →
  `True`; else `field.null`);
- one FK-id-elision eligibility predicate stamped as
  `fk_id_elision_eligible` (forward single, local attname, PK `to_field`,
  non-composite target PK);
- thin `relation_kind` / `is_many_side` properties that delegate to
  `utils.relations` so GraphQL cardinality classification stays single-sited.

Connected behavior examined:

- `types/base.py` — builds `DjangoTypeDefinition.field_map` via
  `FieldMeta.from_django_field` at class-creation time (B7).
- `optimizer/walker.py` — consumes `field_map` / dual-contract
  `FieldMeta | raw Django field`; its `_can_elide_fk_id` /
  `_target_pk_name` now delegate to the `FieldMeta.can_elide_fk_id` /
  `FieldMeta.target_pk_name_of` readers added to this file this pass
  (no independent predicate). Driven by the sibling walker DRY item.
- `types/resolvers.py` — `_field_meta_for_resolver` prefers registered
  `field_map`, else `_from_field_shape` / `from_django_field`; runtime
  elision uses stamped `attname` / `related_model`.
- `types/converters.py::resolved_relation_annotation` — annotation shape
  from `is_many_side` + `nullable`.
- `types/finalizer.py` / `management/commands/inspect_django_type.py` —
  readers of registered `field_map`.
- `optimizer/join_taxonomy.py` — classifies **raw** Django descriptors
  (needs `remote_field`); FieldMeta attrs only as synthetic test-double
  fallbacks. Sibling still open; not a FieldMeta owner.
- `utils/relations.py` — owns `relation_kind`, `instance_accessor`,
  `has_composite_pk` (shared by FieldMeta build and walker fallback through
  FieldMeta).
- Pins: `tests/optimizer/test_field_meta.py`; walker / extension elision
  plan pins; live HTTP coverage in
  `examples/fakeshop/test_query/test_scalars_api.py`
  (`test_scalars_optimizer_fk_id_elision_*`).
- Baseline
  `git diff f46b0a33d6cfce2edc84c24b309b480d7692a71f -- …/optimizer/field_meta.py`
  adds the two dual-contract classmethods `can_elide_fk_id` /
  `target_pk_name_of` (below) and nothing else. Concurrent dirty optimizer
  siblings left untouched.

## Verification

Searches:

- `fk_id_elision_eligible` / elision boolean expression — **sole production
  writer** is `_from_field_shape`. Walker `_can_elide_fk_id` is a stamped-or-
  rebuild adapter; resolvers consume plan sentinels, not the predicate.
- `_target_pk_name` — module helper takes a **model**; walker
  `_target_pk_name` takes a **field** and now delegates to
  `FieldMeta.target_pk_name_of` (isinstance-trust for stamped
  `target_pk_name` including `None`, else the defensive model helper).
  Same name, different contracts.
- `nullable` cardinality gate — only in this module; converters/finalizer
  read the stamped flag.
- Optional `export_dry_review.py audit --target …/field_meta.py`: 7
  definitions; reverse imports match base / walker / converters / resolvers /
  finalizer / inspect / tests. Static similarity did not surface a second
  elision predicate.

Rejected / deferred candidates (tried to disprove shared ownership):

1. **Historical FK-id-elision recompute twin with `walker.py`.** Disproved
   on current code: eligibility is computed only in
   `FieldMeta._from_field_shape`. The dual-contract reader
   `FieldMeta.can_elide_fk_id` returns the stamped
   `field.fk_id_elision_eligible` when the value is a `FieldMeta` (or a
   duck-typed stamp), else `_from_field_shape(...).fk_id_elision_eligible`.
   FieldMeta is the true owner; no second predicate remains.
   (`utils.relations.has_composite_pk` docstring still names both call
   paths; both reach the same FieldMeta predicate.)

2. **Move walker `_can_elide_fk_id` / `_target_pk_name` into FieldMeta as
   dual-contract classmethods.** Implemented this pass (driven by the
   sibling `walker.py` DRY item): `FieldMeta.can_elide_fk_id` /
   `FieldMeta.target_pk_name_of` now own the `FieldMeta | raw Django field`
   dual-contract read, and the walker helpers are one-line delegates.
   `target_pk_name_of` uses `isinstance(FieldMeta)` so a stamped `None`
   `target_pk_name` is trusted rather than treated as "unstamped" and
   rebuilt (which raised on a meta-less `related_model` stand-in); the
   always-bool `fk_id_elision_eligible` slot is unambiguous either way.
   The module `_target_pk_name(model)` stays the defensive model helper.

3. **Fold join-taxonomy connector reads into FieldMeta slots.** Disproved:
   join classification needs live `remote_field` / through naming that
   FieldMeta intentionally does not snapshot; join_taxonomy docs state
   raw-field ownership.

4. **Inline `relation_kind` / `is_many_side` instead of delegating to
   `utils.relations`.** Disproved: would re-split cardinality classification;
   properties are the correct consumer surface over the shared owner.

## Opportunities

1. **Dual-contract FK-id / target-pk readers land on `FieldMeta`.** The
   `FieldMeta | raw Django field` slot reads that formerly lived on the
   walker (`_can_elide_fk_id` / `_target_pk_name`) now belong to
   `FieldMeta.can_elide_fk_id` / `FieldMeta.target_pk_name_of` — the stamp
   owner — so the eligibility predicate and PK resolution cannot drift from
   the stamper and stamped `None` is trusted (isinstance path). Proof:
   dual-contract pins in `tests/optimizer/test_field_meta.py` (including
   stamped-`None`); live HTTP elision pins remain the behavioral surface.
   Driven and cross-referenced by the sibling walker DRY item.

Otherwise none — FieldMeta remains the single writer of relation-shape
snapshots and the FK-id-elision predicate; walker/resolver dual-contract
paths read the stamp or rebuild through `_from_field_shape` rather than
re-encoding the rules.

## Judgment

The two dual-contract readers (`can_elide_fk_id` / `target_pk_name_of`)
are added to this file so FieldMeta owns the `FieldMeta | raw Django field`
read; the walker's same-named helpers become one-line delegates. No second
elision predicate or nullable gate is introduced. Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced `FieldMeta` ownership through builders, walkers, resolvers,
converters, join taxonomy, and `utils.relations`. Confirmed the scoped diff
vs `f46b0a33d6cfce2edc84c24b309b480d7692a71f` adds only the two
dual-contract classmethods `can_elide_fk_id` / `target_pk_name_of`.

Challenged consolidations:

1. **FK-id-elision twin with walker** — Confirmed sole production writer of
   `fk_id_elision_eligible=` is `_from_field_shape`.
   `FieldMeta.can_elide_fk_id` is stamped-or-rebuild only (isinstance /
   `getattr` then `_from_field_shape(...).fk_id_elision_eligible`). No
   second predicate remains.
2. **Move walker dual-contract adapters into FieldMeta** — Implemented at
   this owner. `FieldMeta.can_elide_fk_id` / `FieldMeta.target_pk_name_of`
   own the `FieldMeta | raw Django field` read; walker helpers delegate.
   `target_pk_name_of` uses `isinstance(FieldMeta)`, so a stamped `None`
   is trusted rather than rebuilt (old `getattr`-then-rebuild raised on a
   meta-less `related_model` stand-in — scratch-proved in the walker item);
   the always-bool `fk_id_elision_eligible` slot is unambiguous either way.
3. **Fold join-taxonomy into FieldMeta slots** — Rejected. Classifier needs
   live `remote_field` / through naming FieldMeta does not snapshot.
4. **Inline `relation_kind` / `is_many_side`** — Rejected. Would re-split
   cardinality ownership out of `utils.relations`.
5. **Stale `has_composite_pk` docstring naming "two elision deciders"** —
   Disposed. Doc drift in `utils/relations.py` only; both named paths already
   reach FieldMeta. Not a FieldMeta consolidation; wording cleanup belongs with
   the relations / walker siblings if desired.
6. **Walker `_target_pk_name` vs module `_target_pk_name`** — Same name,
   different contracts (field dual-contract vs defensive model helper). Not a
   shared FieldMeta rule to fold here.

Missed opportunities: none for this target. Nullable cardinality gate and
elision boolean stay single-sited; consumers now read the stamp through the
`FieldMeta` dual-contract readers or rebuild.

Verdict: verified.
