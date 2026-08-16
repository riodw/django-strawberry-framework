# DRY review: `django_strawberry_framework/utils/relations.py`

Status: verified

## System trace

Package owner of Django relation-shape facts shared by converters, resolvers,
filters/orders, mutations, and the optimizer:

1. **Cardinality taxonomy** — `RelationKind`, `relation_kind`,
   `MANY_SIDE_RELATION_KINDS`, `is_many_side_relation_kind`. Distinguishes
   forward M2M, `GenericRelation`, reverse FK, reverse O2O, and forward
   single (FK / O2O / MTI `<parent>_ptr`). Many-side set is the GraphQL-list
   answer (`many` / `reverse_many_to_one` / `generic`); reverse O2O stays
   single-valued.
2. **Strict ORM path classification** — `ClassifiedPath` / `RelationPathHop`,
   `classify_path` (LOOKUP_SEP walk, `pk` alias, traversable `path_infos`
   guard, `PathInfo.m2m` for hop cardinality). Hot path caches via
   `_classify_path_cached`; public `classify_path` stays uncached for
   unhashable doubles.
3. **To-many probe** — `path_traverses_to_many` (strict
   `first_many_index is not None`, fail-open `_lenient_traverses_to_many` on
   `PathResolutionError`). Deliberate divergence on unique reverse FK:
   `PathInfo.m2m` corrects the old `relation_kind`-based True.
4. **Lookup-expr validation** — `validate_lookup_expr` (transform chain +
   trailing-transform→`exact`). Contract separate from path classification;
   production call sites not yet wired (tests pin it).
5. **Write-surface forward-M2M predicate** — `is_forward_many_to_many`
   (cardinality `"many"` cannot split forward vs reverse M2M).
6. **Instance accessor** — `instance_accessor` (FieldMeta slot /
   `get_accessor_name` / `name`).
7. **Composite PK gate** — `has_composite_pk` for FK-id elision eligibility.

Connected surfaces re-checked from this file's side:

- `types/relations.py` — `PendingRelation` scaffolding; imports `RelationKind`
  only. Different lifecycle concern.
- `optimizer/join_taxonomy.py` — join/window/lateral vocabulary layered on
  `relation_kind`; `WINDOWABLE_RELATION_KINDS` deliberately wider than
  `MANY_SIDE_RELATION_KINDS` (includes `reverse_one_to_one`).
- `permissions.py::_is_cascadable_edge` — `isinstance(ForeignKey) + column`.
- `connection.py::_resolve_order_path_field` — keyset order-path walk using
  `relation_kind == "forward_single"` + non-null mid hops.
- Filters / orders / walker / resolvers / `FieldMeta` — already consume the
  shared taxonomy / accessor / composite-pk helpers.
- Mutations inputs/resolvers — already consume `is_forward_many_to_many`.
- DRF `_attestable_m2m_fields` — was the leftover inline forward-M2M filter.

Item baseline `5f73d59053f950ed58da1c0b97db312c8e58a082`: target file matched
baseline before this pass (empty item-scoped diff).

## Verification

Searches: `relation_kind`, `is_many_side_relation_kind`, `classify_path`,
`path_traverses_to_many`, `LOOKUP_SEP` walks, `path_infos`,
`content_type_field_name` / `object_id_field_name`, `get_accessor_name`,
`pk_fields`, `auto_created`+`many_to_many`, MTI/`_ptr`,
`is_forward_many_to_many` call sites.

Strongest rejected candidates (re-proved this pass):

- **Merge `types/relations.py` into this module.** PendingRelation /
  PendingRelationAnnotation own definition-order finalization scaffolding;
  this module owns runtime field/path taxonomy. Shared token is only the
  `RelationKind` type alias — already imported one-way. Merging would couple
  type-system lifecycle to ORM helpers.
- **Substitute `relation_kind == "forward_single"` for
  `_is_cascadable_edge`.** Cascadable needs `isinstance(ForeignKey) and
  column`. `relation_kind` falls through a forward `GenericForeignKey` to
  `"forward_single"` (no dedicated forward-GFK kind), so the substitution
  would wrongly cascade GFK edges. MTI ptr correctly lands in both as
  forward-single / ForeignKey, but that overlap does not make the predicates
  interchangeable.
- **Fold `connection._resolve_order_path_field` into `classify_path`.** Same
  LOOKUP_SEP/`get_field`/`pk` skeleton, different acceptance contract:
  keyset walk is fail-open `None`, mid hops must be non-null
  `forward_single` only, terminal must be concrete non-relation.
  `ClassifiedPath` does not carry per-hop nullability/field objects; forcing
  it would need mode flags or a second plan shape. Keep local.
- **Unify `_lenient_traverses_to_many` with `classify_path`.** Documented
  fail-open fallback for garbage tails the strict classifier rejects
  (`genres__nonexistent` → True). Cardinality rule also differs on unique
  reverse FK (`PathInfo.m2m` vs `relation_kind`). Intentional dual.
- **Collapse `WINDOWABLE_RELATION_KINDS` into `MANY_SIDE_RELATION_KINDS`.**
  Windowable includes `reverse_one_to_one` (child carries parent id);
  many-side GraphQL lists do not. Different change axes.
- **`optimizer/plans.py` defer/only path walk.** Projection membership walk,
  not relation taxonomy — unrelated.
- **`utils/permissions.py` flat-path gate walk.** Walks declared
  RelatedFilter/RelatedOrder maps by `field_name`, not model `_meta` —
  authorization twin of nested gates, not ORM classification.
- **`forms/inputs` / `serializer_converter` `RELATION_MULTI` via
  `many_to_many`.** Input-shape vocabulary for form/serializer columns
  (always forward-bound); not the write-surface forward-vs-reverse M2M
  predicate.
- **Inline `one_to_many` / `many_to_many` reads in `join_taxonomy`.** Join
  column selection needs raw Django flags alongside an already-computed
  `kind`; not a second classifier.

## Opportunities

### 1. DRF attestation must use `is_forward_many_to_many`

- **Repeated responsibility:** "Is this a forward, writable
  `ManyToManyField` (not a reverse M2M accessor)?"
- **Sites:** `is_forward_many_to_many` (owner);
  `mutations/inputs.py::_select_editable_fields` and
  `mutations/resolvers.py::_index_relation_fields` (already migrated);
  `rest_framework/resolvers.py::_attestable_m2m_fields` (was
  `many_to_many and not auto_created`).
- **Evidence:** Same exclude-reverse-M2M contract; docstring claimed
  single-siting across mutation surfaces while DRF re-spelled a near-twin
  that can drift if the concrete/`auto_created` rule evolves.
- **Owner:** `utils/relations.py::is_forward_many_to_many`.
- **Consolidation:** DRF call site delegates to the helper; docstring lists
  the third consumer.
- **Proof:** New permanent pins in `tests/utils/test_relations.py`
  (SyntheticNamespace + stock `Book.genres` / `Genre.books`). Existing DRF
  attestation coverage remains the integration surface (deferred pytest).
- **Risks / non-goals:** Helper is slightly more defensive than bare
  `not auto_created` (`concrete or not auto_created`); stock Django forward
  / reverse M2M shapes agree. Does not change form/serializer
  `RELATION_MULTI` mapping.

## Judgment

`utils/relations.py` already owns the package relation taxonomy, strict path
plan, to-many probe, accessor name, and composite-PK gate. The one remaining
same-contract duplicate was the DRF forward-M2M attestation filter; it now
routes through `is_forward_many_to_many`. Neighboring LOOKUP_SEP walks and
cascadable/windowable predicates look similar but encode distinct policies
and must stay separate.

## Implementation (Worker 1)

- Migrated `rest_framework/resolvers.py::_attestable_m2m_fields` to
  `is_forward_many_to_many`.
- Updated `is_forward_many_to_many` docstring to name the three write
  surfaces.
- Permanent tests:
  `test_is_forward_many_to_many_accepts_concrete_forward_m2m`,
  `test_is_forward_many_to_many_rejects_reverse_m2m_accessor`,
  `test_is_forward_many_to_many_rejects_non_m2m`,
  `test_is_forward_many_to_many_stock_book_genres`.
- `uv run ruff format .` + `uv run ruff check --fix .` — clean.
- Deferred pytest (cycle policy). No CHANGELOG.

### Deferred findings

- `validate_lookup_expr` has no production importer yet (tests +
  `exceptions.py` docs only). Not a DRY consolidation; leave for the
  consumer that needs lookup-expr validation (likely filter leaf binding).

Item-scoped diff vs `5f73d59053f950ed58da1c0b97db312c8e58a082`:
`django_strawberry_framework/utils/relations.py` (docstring),
`django_strawberry_framework/rest_framework/resolvers.py` (import + call),
`tests/utils/test_relations.py` (four permanent tests). Artifact is new.

Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced `utils/relations.py` end-to-end and challenged the consolidation
plus each material rejection against present-day source. Verdict: verified.

### Consolidation holds

- All three write surfaces now call `is_forward_many_to_many`:
  `mutations/inputs.py::_select_editable_fields`,
  `mutations/resolvers.py::_index_relation_fields`,
  `rest_framework/resolvers.py::_attestable_m2m_fields`. No leftover
  `many_to_many and not auto_created` / `auto_created` M2M filter in
  production (package-wide `auto_created` grep: only this helper and
  `optimizer/field_meta.py` snapshots).
- Item-scoped diff vs baseline is exactly the claimed three paths
  (docstring, DRF import+call, four permanent tests). No unrelated
  absorption.
- Stock library flags agree with both the old DRF predicate and the
  helper: `Book.genres` → True (`many_to_many=True`, `concrete=False`,
  `auto_created=False`); `Genre.books` → False (`auto_created=True`).
  Note: Django forward M2M is **not** `concrete` (through table); the
  helper's `concrete or not auto_created` still accepts it via
  `not auto_created`. The docstring's "is concrete" shorthand is
  imprecise but pre-existing and not load-bearing — the stock pin
  protects the real contract.
- Remaining raw `many_to_many` reads elsewhere are different contracts:
  already-selected fields (`mutations/inputs` annotation/required),
  `RELATION_MULTI` form/serializer column tagging (always forward-bound
  columns), `model._meta.many_to_many` in `forms/resolvers` (Django's
  forward-only Options collection), join-column selection, cascade
  unsupported-edge exclusion, orderable-column exclusion.

### Rejected candidates re-proved

- **`types/relations.py`:** only imports `RelationKind`; owns
  `PendingRelation` / annotation scaffolding — different lifecycle.
- **Cascadable vs `relation_kind == "forward_single"`:** live
  `TaggedItem.content_object` (GFK) classifies as `"forward_single"` but
  `isinstance(..., ForeignKey)` is False and `column` is None —
  `_is_cascadable_edge` correctly excludes it. Substitution would cascade
  GFK edges.
- **Keyset `_resolve_order_path_field` vs `classify_path`:** fail-open
  `None`, mid-hop `forward_single` + non-null, concrete non-relation
  terminal — acceptance contract `ClassifiedPath` does not encode.
- **Lenient vs strict to-many:** documented fail-open +
  `PathInfo.m2m` vs `relation_kind` divergence retained.
- **`WINDOWABLE_RELATION_KINDS - MANY_SIDE_RELATION_KINDS`** ==
  `{"reverse_one_to_one"}` — confirmed live; different change axes.
- **`validate_lookup_expr`:** still tests + `exceptions.py` docs only;
  deferred correctly (not a same-contract duplicate).

### Missed consolidations

None found. No further same-contract forward-M2M write-surface twin;
neighboring LOOKUP_SEP walks and many-side vocabularies stay intentionally
separate.

Checkbox marked `[x]` on `docs/dry/dry-0_0_13.md`.
