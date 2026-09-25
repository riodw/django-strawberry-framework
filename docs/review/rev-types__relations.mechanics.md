# Review · Mechanics: `django_strawberry_framework/types/relations.py`

Status: verified
Run: 0.0.15 2026-09-25-2

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=b43e2f2fb07e4c13ee93056c09a5a94ede07065f

## Trace

Target read whole (blob `4098eebc`, identical to the item baseline). Orientation:
`review_inspect.py` at `<root>/mechanics/inspect/` (json `<root>/mechanics/relations.json`).
Producer `django_strawberry_framework/types/base.py::_build_annotations` (one `PendingRelation`
per auto-synthesized relation, `relation_kind=field_meta.relation_kind`,
`nullable=field_meta.nullable` copied from `field_map[field.name]`) and
`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` (appends after
`register_with_definition`). Consumers: `django_strawberry_framework/types/finalizer.py::finalize_django_types`
(Phase 1 loop reads `source_type`, `field_name`, `related_model`, then `definition.field_map`;
rewrite reads `django_field`), `django_strawberry_framework/types/finalizer.py::_format_unresolved_targets_error`
(`source_model`, `field_name`, `related_model`), `django_strawberry_framework/registry.py::TypeRegistry.discard_pending`
(`id()` set), `django_strawberry_framework/registry.py::TypeRegistry.unregister` (`source_type is
not`). `registry.py` imports `PendingRelation` under `TYPE_CHECKING` only. Neither symbol is public
(`types/__init__.py` `__all__` = `DjangoType`, `SyncMisuseError`, `finalize_django_types`; not in
`docs/GLOSSARY.md` or `docs/README.md`; README "finalize ... before the schema is constructed" is
the only contract prose on skipped finalization). `django_strawberry_framework/schema.py::DjangoSchema`
constructor read: no finalize check. Django `ForeignObjectRel.__eq__` / `__hash__` (`identity`,
`make_hashable`) in `.venv`. Tests: `tests/types/test_relations.py` whole,
`tests/test_registry.py` (every `PendingRelation(` site, identity tests),
`tests/types/test_finalizer.py` (three hostile-metadata constructions), `tests/types/test_base.py`
sentinel assertion, `tests/utils/test_relations.py::test_relation_kind_reverse_many_to_one_is_in_literal`.
Other axis records read (Performance `no-findings`, Comments `findings-recorded` F1-F5) with their
handoffs; their two Mechanics leads are M1 below.

Probes, copy `review/types/relations.py/mechanics`, cell `default`:

- `review-20260925T170250-678ab1` (`<root>/mechanics/probe_pending_usage.py`): instruments
  `PendingRelation` construction, `__hash__`, `__eq__` and every field read, imports
  `config.schema` (every fakeshop app declared + finalized). 178 records built, 0 `__hash__`, 0
  `__eq__`, 0 reads of `relation_kind`, `nullable`, `source_model`; `field_name` 534,
  `source_type` 356, `django_field` 178, `related_model` 178; 0 pending left; 0 of 178
  `django_field` values refuse `hash()`; 0 snapshots differ from the live `FieldMeta`. Positive
  control: one `hash`, one `==`, one read of each snapshot field moved every counter by 1.
- `review-20260925T170321-032303` / `review-20260925T170834-619e41`
  (`<root>/mechanics/probe_sentinel_repr.py`): finalize skipped, then (A) `strawberry.Schema`, (B)
  `DjangoSchema`: `TypeError ... Unexpected type '<class ...ItemType>'`, sentinel repr absent,
  `finalize_django_types()` not named; (C) `strawberry.type` applied by hand first: the sentinel
  repr and the finalize hint appear. Same result as the Comments probe `review-20260925T170235-567b47`.
- `review-20260925T170427-664289` and `review-20260925T170436-5116e1`: M1 applied by hand in my
  copy only (`eq=False`, `__hash__` + `_hash_component` deleted). Six PendingRelation-touching
  modules: 3 failed, 349 passed; full suite: 5 failed, 8853 passed, 40 skipped, the 5 being the
  three nodes named under M1 plus the two `tests/test_ci_governance.py` git-census rows a copy
  fails by construction. Copy restored byte-identical (`git hash-object` `4098eebc` both sides).
- `review-20260925T170933-512969` (`<root>/mechanics/probe_proof.py`, the M1/M2 Proof probe):
  before = `fields: source_type,source_model,field_name,django_field,related_model,relation_kind,nullable`,
  `identity hash: False identity eq: False`, `module has _hash_component: True`, 178 added, 0
  remaining.

Cells: `sharded` and `pg` `inapplicable by construction`: the module opens no connection, reads no
alias, runs no query; every input is a Django field object or class at declaration time.

`check_citations.py --cited-by` on every symbol M1 removes: `types/relations.py::_hash_component`
0 citers, `types/relations.py::PendingRelation.__hash__` 0 citers. `PendingRelation` (6 ungated,
all `docs/builder/DONE/`) and `PendingRelationAnnotation` (1 ungated, same) keep their names. One
substring citer rides on M1: `tests/types/test_relations.py` cites
`tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation #"assert record_a == record_b"`,
the line M1 changes.

Fingerprints: `django_strawberry_framework/types/relations.py` 4098eebca9b9fad9e328bdbc920ff863e3a229e9;
`django_strawberry_framework/types/base.py` 49057fad2058ee63635c7951bfcd7ab8d9a0be30;
`django_strawberry_framework/types/finalizer.py` de34ae2aaed10fd664197cc2205c29e7d1927c2d;
`django_strawberry_framework/registry.py` 9cc8bb553fd417fc465809a541769a8383469cda;
`django_strawberry_framework/schema.py` a83ac2de2d84f9bd3b0b0365b36bfd34c24a30b7;
`django_strawberry_framework/utils/relations.py` 8dbc3fe668dda7d57f1e2b2a3af66afdda449ded;
`django_strawberry_framework/types/__init__.py` 1bf69028dbdcac9a42f6b6ba05e1220fdde0a155;
`django_strawberry_framework/optimizer/field_meta.py` 18ea719a6141a5cad8d8b0148f1818f58f97dc23;
`tests/types/test_relations.py` bff8c265cc6baa956feb0a76b5e846c09bb58a42;
`tests/test_registry.py` e330cfb81e4bbe9f4f04bc7e1b30038097a3bb10;
`tests/types/test_finalizer.py` 05e1c9ecf6212fd51577c2aaa7b4b2a0102cdf74;
`tests/types/test_base.py` 0d070aee0513a108e1ad6c03d079896c269fcfab;
`tests/utils/test_relations.py` b82f9cc19345c175882cd44652255779426456c0;
`tests/types/test_definition_order.py` aa9435fd27ad769ff4301747dafe54287fa73c1b;
`tests/types/test_definition_relations.py` 196e783d1d8720ad171eac10fc8b1f1fa38852ee;
`examples/fakeshop/config/schema.py` 303ea2da9df1f8611c02926fd28c59e5ccf9ecac;
`docs/README.md` d7f3b7832066d658ff60c9c60a29214cdd973fc4; probes `probe_pending_usage.py`
13925ee52828d7b1d3da8e8dbf485157fbfb4158, `probe_sentinel_repr.py`
db5f0f7195dbab29ba272f203adf994c6a23d19c, `probe_proof.py` 9d91b8fc62d0c3dea1b21786320c0c22355cb469.

## Findings

### High

None.

### Medium

None.

### Low

#### M1 - value equality and a guarded `__hash__` serve no consumer; the only contract is identity

- **Observation** - `django_strawberry_framework/types/relations.py::PendingRelation` takes
  dataclass value equality (`frozen=True`, default `eq=True`) and overrides `__hash__` with
  `django_strawberry_framework/types/relations.py::_hash_component`, a three-rung ladder that
  catches `BaseException` (so a `KeyboardInterrupt` / `SystemExit` raised inside a field's
  `__hash__` is swallowed). Every consumer matches records by identity:
  `django_strawberry_framework/registry.py::TypeRegistry.discard_pending` (`id()` set, its
  docstring: "does not couple ... to ``PendingRelation``'s hashability"),
  `django_strawberry_framework/registry.py::TypeRegistry.unregister` (`is not`), the finalizer
  keeps records in lists. The ladder also breaks the hash/eq contract it exists for: two records
  whose unhashable `django_field` values compare equal across types hash differently at rung two.
- **Evidence** - `review-20260925T170250-678ab1`: 178 records through a full fakeshop build, 0
  `__hash__`, 0 `__eq__` calls. `review-20260925T170436-5116e1`: with `eq=False` and the hash code
  deleted, the full suite loses exactly
  `tests/types/test_relations.py::test_equal_pending_relations_have_equal_hashes`,
  `tests/types/test_relations.py::test_pending_relation_hash_falls_back_when_value_and_type_hashing_fail`
  (both pin the deleted mechanism) and
  `tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation`
  (fails only at its sanity line `assert record_a == record_b`; the identity contract it pins
  still holds). `test_discard_pending_tolerates_non_hashable_django_field`,
  `test_pending_relation_hash_supports_non_hashable_django_field` and
  `test_pending_relation_is_set_member_with_non_hashable_django_field` keep passing: an identity
  hash never touches the field, so the unhashable-metadata tolerance the ladder bought is kept for
  free. Contract source: the `discard_pending` owner docstring; no other.
- **Impact** - a record type offering value equality invites an equality-based consumer, the
  exact shape `test_discard_pending_uses_identity_match_with_real_pending_relation` says would
  drop both of two equal records; 25 lines of guard code and two tests maintain a behavior no
  package path uses. Cold (declaration / finalize, Performance record).
- **Severity** - Low: cold path, no reachable input produces wrong output today; bounded
  maintainability and a latent trap. Rides on `types/relations.py` and
  `tests/types/test_relations.py`, which Comments F1-F3 (Medium) already change.
- **Recommendation** - owner `django_strawberry_framework/types/relations.py::PendingRelation`:
  `@dataclass(frozen=True, eq=False)`; delete `PendingRelation.__hash__` and `_hash_component`.
  Tests: in `tests/types/test_relations.py` delete
  `test_equal_pending_relations_have_equal_hashes` and
  `test_pending_relation_hash_falls_back_when_value_and_type_hashing_fail`; add
  `test_equal_valued_pending_relations_stay_distinct` (two records from the same kwargs:
  `first != second`, `len({first, second}) == 2`); keep the non-hashable-field hash / set tests
  as identity-hash pins with docstrings saying so (their prose is Comments' to grade). In
  `tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation`
  the sanity line becomes `assert record_a != record_b` (distinct records, same values) and its
  comment drops the equality framing; the `#"assert record_a == record_b"` citation in
  `tests/types/test_relations.py` goes with the test comment that holds it.
- **Must not change** - `discard_pending` removes exactly the instances passed; `unregister`
  drops a type's records; records stay frozen (`FrozenInstanceError`); a record with an
  unhashable or hostile `django_field` still hashes, joins a set and is discarded; the fakeshop
  build adds and discards the same records (178 today, 0 remaining).
- **Proof** - `rg -c "_hash_component|def __hash__" django_strawberry_framework/types/relations.py`
  prints nothing (exit 1); `rg -c "@dataclass\(frozen=True, eq=False\)" django_strawberry_framework/types/relations.py`
  prints `1`; `uv run python scripts/workspace.py run review/types/relations.py/verify-mechanics-<n> -- python /Users/riordenweber/projects/django-strawberry-framework/docs/review/temp-tests/types__relations/mechanics/probe_proof.py`
  prints `identity hash: True identity eq: True`, `module has _hash_component: False`,
  `pending remaining after finalize: 0` (before: `False False`, `True`, 0; run
  `review-20260925T170933-512969`); `uv run python scripts/workspace.py run review/types/relations.py/verify-mechanics-<n> -- pytest tests/types/test_relations.py tests/test_registry.py tests/types/test_finalizer.py tests/types/test_base.py tests/types/test_definition_order.py tests/types/test_definition_relations.py --no-cov -q`
  exit 0 with `0 failed`; `workspace.py prove` with the relations.py `eq=False` hunk reverted
  has `expect_failing` = `test_equal_valued_pending_relations_stay_distinct in
  tests/types/test_relations.py`.
- **Freshness** - Trace fingerprints.

#### M2 - `relation_kind` and `nullable` are a second copy of `FieldMeta` state that nothing reads

- **Observation** - `django_strawberry_framework/types/relations.py::PendingRelation` fields
  `relation_kind` and `nullable` are copied from `DjangoTypeDefinition.field_map[field.name]` in
  `django_strawberry_framework/types/base.py::_build_annotations` and read by no package code (the
  class docstring says so: "the production consumer reads the live ``FieldMeta``"). The owner of
  both is `django_strawberry_framework/optimizer/field_meta.py::FieldMeta`; the finalizer already
  reads it from `definition.field_map[pending.field_name]`. The only other writer is a test:
  `tests/test_registry.py::test_finalize_discards_consumer_authored_pending_relation_without_rewriting_annotation`
  hand-rolls the cardinality-gated nullability rule for the snapshot, citing
  `_record_pending_relation`, a helper that no longer exists.
- **Evidence** - `review-20260925T170250-678ab1`: 0 reads of `relation_kind` / `nullable` over 178
  records (positive control moved both counters); 0 of 178 snapshots differ from the live
  `FieldMeta`, so removing them changes no value anyone sees. DRY change challenge ("reverse
  one-to-one nullability changes"): 1 authoritative definition in the package
  (`FieldMeta.from_django_field`), the record is a projection; the test's hand-rolled rule is a
  second, unowned copy.
- **Impact** - two fields, 13 test constructions (`tests/types/test_relations.py` 3,
  `tests/test_registry.py` 7, two sharing one kwargs dict, `tests/types/test_finalizer.py` 3) and
  a hand-rolled copy of a
  `FieldMeta` rule maintained for state with no reader; a future reader of `pending.nullable`
  would take a snapshot where the owner is one lookup away. Removing them also drops the
  module's only package import (`..utils.relations.RelationKind`).
- **Severity** - Low: cold, maintainability; state owned in two places with zero readers. Rides
  on the files M1 and Comments F1-F3 change.
- **Recommendation** - delete both fields and the `RelationKind` import from `PendingRelation`;
  drop the two kwargs in `_build_annotations`; drop them at the 13 test sites, which removes the
  hand-rolled nullability rule and its stale comment in `tests/test_registry.py`; the
  `relation_kind` import in `tests/test_registry.py` then has no other use (AGENTS.md rule 14
  orphan sweep; ruff `F401` confirms). The class docstring's snapshot sentence goes (Comments).
  Keep `source_model`, `related_model` (rejected below).
- **Must not change** - finalize binds every relation to the same annotation and resolver; the
  unresolved-target and malformed-metadata errors keep their text
  (`tests/types/test_finalizer.py` hostile-metadata tests).
- **Proof** - `rg -c "relation_kind|nullable|RelationKind" django_strawberry_framework/types/relations.py`
  prints nothing (exit 1); the M1 `probe_proof.py` command prints
  `fields: source_type,source_model,field_name,django_field,related_model` and
  `pending remaining after finalize: 0` (before: seven fields, 0); the M1 six-module pytest
  command exit 0 with `0 failed` (a leftover kwarg raises `TypeError` at construction, so every
  construction site is exercised); `uv run ruff check tests/test_registry.py` passes.
- **Freshness** - Trace fingerprints.

## Rejected

- **Skipped-finalize diagnostic unreachable on the supported path.** The sentinel repr claims to
  shape the error "when that rewrite was skipped"; probes A/B show `strawberry.Schema` and
  `DjangoSchema` fail first on the undecorated `DjangoType` with Strawberry's generic
  `Unexpected type`, no finalize hint; only hand-applied `strawberry.type` (C, the API the package
  rejects) shows it. No contract source promises the package diagnoses a skipped finalize (README
  states the ordering rule only; the claim is the sentinel's own prose, which Comments F4 narrows
  to its real reach). Delivering it means a new failure-path translation in
  `django_strawberry_framework/schema.py::DjangoSchema` (re-raise the construction `TypeError` as
  a `ConfigurationError` naming `finalize_django_types()` when the registry holds unfinalized
  definitions): new behavior in another module, a card, not this item. Reopen: a contract source
  (README, GLOSSARY, a card) says `DjangoSchema` names a skipped finalize.
- **Repr string says `strawberry.Schema`, not `DjangoSchema`.** A `DjangoSchema` is a
  `strawberry.Schema`, and path C with plain `strawberry.Schema` is where the string appears.
  Reopen: the string is shown on a `DjangoSchema`-only path.
- **Delete `_PendingRelationAnnotationMeta` (it serves only path C).** Path C is reachable by a
  consumer, the metaclass costs one class, and
  `tests/types/test_relations.py::test_pending_relation_annotation_repr` pins it. Reopen: the
  skipped-finalize translation above lands and covers path C.
- **`related_model` duplicates `django_field.related_model`.** Read on the success path
  (`registry.get`) and the error path; snapshotted after `_build_annotations` rejects a `None`
  related model, and the hostile-metadata finalizer tests build records whose `django_field` is
  `object()`, which the snapshot keeps diagnosable. Reopen: finalize reads it from the field.
- **`source_model` duplicates `definition.model`.** Read only by
  `_format_unresolved_targets_error`, which formats records without a definition lookup. Reopen:
  the formatter takes definitions.
- **`registry.py` imports `PendingRelation` under `TYPE_CHECKING`.** Annotation-only use; a runtime
  import would cycle through `types/__init__` -> `types/base.py` -> `registry.py`, but no runtime
  dependency exists to hide. Reopen: `registry.py` needs the class at runtime (`isinstance`).
- **Finalizer's consumer-authored defense branch** (`finalize_django_types` skips a record whose
  `field_name` is consumer-authored, unreachable from `_build_annotations`): in
  `types/finalizer.py`, outside this item, and reachable by a hand-added record
  (`tests/test_registry.py` pins it). Reopen: a `types/finalizer.py` item.

Looks-for discharge (REVIEW.md "Mechanics"):

- rule at a caller instead of its owner: none; the hand-back-the-same-instance rule is owned and
  documented by `TypeRegistry.discard_pending`, and the finalizer complies.
- policy in an adapter / mechanism in a policy layer: none; the module is data only.
- decision the contract sources make differently from the body: M1 (value semantics vs the
  identity contract); the sentinel's reach (rejected above, prose to Comments F4).
- branch no real path reaches: M1 (`_hash_component`, all three rungs, and `__hash__`).
- mode flag standing in for an adapter: none.
- state owned in two places: M2.
- dependency direction: `types/relations.py` imports only `django.db.models` and
  `utils/relations.py` (lower layer); `TYPE_CHECKING` in `registry.py` rejected above.
- `django.conf.settings` at import: none.
- `__all__` vs public surface: the module has no `__all__` and is not re-exported; none.
- two sites implementing one rule: M2's hand-rolled nullability copy in a test; no package-side
  duplicate.
- sync/async twins: none; no execution path.
- guard one flavor has and a sibling lacks: none; one record type, one sentinel.

## Cross-axis (for Comments)

Prose M1 / M2 make false, for the Comments verifier to grade once they land (no separate
finding; each rides on the Mechanics change):

- `tests/types/test_relations.py` module docstring, first line included ("hash consistency"),
  and the guarded-hash framing Comments F3 rewrites: after M1 the record hashes by identity, so
  F3's text after is superseded; a first-line change is a `docs/TREE.md` render (two rows).
- `tests/types/test_relations.py::test_pending_relation_equality_still_works_with_non_hashable_django_field`
  comment (Comments F5): after M1 value equality across instances no longer exists.
- `django_strawberry_framework/types/relations.py` module docstring ("callers may pass back the
  same object even when ``django_field`` is non-hashable") and `PendingRelation` docstring
  snapshot paragraph ("``nullable`` and ``relation_kind`` are snapshot fields ..."): false after
  M1 / M2; Comments F1 / F2 texts after already drop both, so they stand.
- `tests/utils/test_relations.py::test_relation_kind_reverse_many_to_one_is_in_literal` docstring
  ("``tests/test_registry.py`` constructs a ``PendingRelation`` with this value against the typed
  ``relation_kind`` field"): false after M2; restate the alias check on its own terms.

Handoff: the Performance and Comments handoffs' two Mechanics leads (`_hash_component` catching
`BaseException`; hash with no production caller) are M1. Order for Worker-2: M1 and M2 touch the
same class and the same 13 test constructions, so land them together, then Comments F1-F5 on the
result (F3's and F5's texts after are overtaken by M1; the tests they describe are rewritten or
deleted). Probes and the reverted-copy runs are under `docs/review/temp-tests/types__relations/mechanics/`
(`relations.orig.py` is the byte copy used to restore my copy). `probe_pending_usage.py` reads
`relation_kind` / `nullable` by name, so it does not run after M2; `probe_proof.py` runs on both
sides. The fakeshop count 178 depends on the concurrent library-model edit in the shared tree and
is not a pinned figure. Open lead for `## Decisions`, not a finding: `DjangoSchema` could
translate the skipped-finalize `TypeError` into a `ConfigurationError` naming
`finalize_django_types()` (first rejection above).

## Verification (Mechanics)

Pass 1, address `review/types/relations.py/verify-mechanics-1`, copy fresh at first run.

Diff binding: `git diff b43e2f2f... -- <nine paths>` sha256 `d1dad86b...9664499`, equal to
`<root>/diff/pass-1.diff`.

Proof lines, run verbatim before reading `## Implementation (Worker-2)`:

- M1 `rg -c "_hash_component|def __hash__" .../types/relations.py`: no output, exit 1. Pass.
- M1 `rg -c "@dataclass\(frozen=True, eq=False\)" ...`: `1`. Pass.
- M1/M2 `probe_proof.py`, run `review-20260925T172347-3f3a5a`: `fields: source_type,source_model,field_name,django_field,related_model`,
  `identity hash: True identity eq: True`, `module has _hash_component: False`, 178 added,
  `pending remaining after finalize: 0`. Pass (before `review-20260925T170933-512969`).
- M1/M2 six-module pytest, run `review-20260925T172351-572a9c`: 350 passed, exit 0. Pass.
- M2 `rg -c "relation_kind|nullable|RelationKind" .../types/relations.py`: no output, exit 1. Pass.
- M2 `uv run ruff check tests/test_registry.py`: passes. Pass.
- M1 `workspace.py prove` (`<root>/verify-mechanics-1/prove_m1_verbatim.json`, `eq=False` ->
  `frozen=True`, `expect_failing` = the new test only), run `review-20260925T172453-e4d26c`, exit 1:
  `test_equal_valued_pending_relations_stay_distinct` fails as the Proof expects, and three more
  rows fail beside it (`test_pending_relation_hash_supports_non_hashable_django_field`,
  `test_pending_relation_is_set_member_with_non_hashable_django_field`,
  `test_discard_pending_uses_identity_match_with_real_pending_relation`): a value-`eq` frozen
  dataclass synthesizes a field hash, which raises on the unhashable stand-in. The Proof's
  declared set was mine and under-stated; the landed meaning (the new test fails without
  `eq=False`) holds. Exact set, `<root>/verify-mechanics-1/prove_m1.json` entry 1, run
  `review-20260925T172457-704c5e`: expectation met, restore byte-proved (`5e9b5cdb` both sides).

Numbers reproduced: Worker-2's after figures (five fields, identity True/True, 178, 0) and 350
passed match the runs above; full suite in my copy `review-20260925T172608-82d737`: 8861 passed,
40 skipped, 2 failed = the two `tests/test_ci_governance.py` git-census rows a copy fails by
construction, equal to Worker-2's `review-20260925T171736-510636`.

Whole-diff reading:

- M1 as recommended. The one test deleted beyond M1's list,
  `test_pending_relation_equality_still_works_with_non_hashable_django_field`, asserted
  `pending == pending`; with `eq=False` that is `object.__eq__` reflexivity, which no mutation of
  this module can break, so the test could not fail. Deletion correct; it also carried the
  `#"assert record_a == record_b"` substring citation M1 falsified. 0 citers of it
  (`check_citations.py --cited-by`), 0 `rg` hits outside `docs/review/`.
- M2 as recommended, plus the `_build_annotations` `field_map` parameter removal. Correct and
  in the item's fence: at `ITEM_BASELINE` the parameter's only read was
  `field_meta = field_map[field.name]`, whose only use was the two deleted kwargs, so M2 left a
  required keyword-only parameter no body reads (ruff reports no unused keyword-only argument,
  so only reading catches it). The lookup was no hidden guard: `DjangoType.__init_subclass__`
  builds `field_map` from the same `fields` tuple it passes, unreassigned between, so the lookup
  could not raise; the six test callers built it the same way (`_field_map_for`, or
  `definition.field_map` over `definition.selected_fields`). `field_map` still feeds
  `DjangoTypeDefinition`; `FieldMeta` stays imported in `types/base.py` (three uses). Test-side
  cascade (`_field_map_for`, the `FieldMeta` import, the `relation_kind` import) leaves nothing
  orphaned: `rg` 0 hits, ruff clean.
- No equality consumer exists to be changed by identity semantics: `registry.py` matches by
  `is not` and an `id()` set, the finalizer iterates lists; no `in`, `==`, `.remove` or `.index`
  on records in `registry.py` or `types/finalizer.py`.

Attacks:

- Value equality back with an identity hash (`eq=False` kept; hand `__eq__` over three fields,
  `__hash__ = object.__hash__`), `prove_m1.json` entry 2, run `review-20260925T172457-704c5e`:
  exactly `test_equal_valued_pending_relations_stay_distinct` and
  `test_discard_pending_uses_identity_match_with_real_pending_relation` fail, the hash / set
  tests pass. The new test is the row that sees value equality return while hashing stays
  tolerant. Pass.
- Cells: `sharded` and `pg` stay `inapplicable by construction` (the change removes fields and a
  parameter at declaration time; no alias, query or connection).

Disputes: none.

Tier: package tier is right; record identity and `_build_annotations` arguments are internal to
declaration and finalize, and no GraphQL request observes them.

Lint gates (`--check` forms, the eight `.py` paths): `ruff check` passes; `ruff format --check`
8 already formatted; `check_trailing_commas.py --check` 0 violations; `check_citations.py --check`
`OK: 1287 citations resolve`. `--cited-by` on the deleted `_hash_component` and
`PendingRelation.__hash__` (`types/relations.py`), `_field_map_for`
(`tests/types/test_relay_interfaces.py`) and the three deleted test names: 0 citers each. The
record's own unresolved citations (`check_citations.py --paths`: 6) all name symbols this item
deleted, cited in the review pass before the edit.

Gap for `## Decisions` (not this axis, not `revision-needed`): KANBAN.md card item (c) naming the
stale `_record_pending_relation` comment in
`tests/test_registry.py::test_finalize_discards_consumer_authored_pending_relation_without_rewriting_annotation`
is discharged by M2's deletion of that comment; the board row is Worker-0 / Rio's (DB edit).

Verdict: M1 verified, M2 verified, the `field_map` extension verified, the extra test deletion
verified.

Handoff: read beyond the record `types/base.py` from `DjangoType.__init_subclass__` to the
`_build_annotations` call (the `fields` / `field_map` flow), every `_build_annotations` caller,
and every equality-shaped use of records in `registry.py` and `types/finalizer.py`. The only
imprecision found is in my own review-pass Proof: its `expect_failing` named one node where the
revert fails four; a later pass that reruns it verbatim gets exit 1 and should use
`verify-mechanics-1/prove_m1.json` entry 1 instead. Manifests and runs are under
`docs/review/temp-tests/types__relations/verify-mechanics-1/`.
