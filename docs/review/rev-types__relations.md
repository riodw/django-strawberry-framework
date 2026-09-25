# Review: `django_strawberry_framework/types/relations.py`

Status: verified
Run: 0.0.15 2026-09-25-2
Path class: cold — records are built once per relation field at `DjangoType` declaration and read once per `finalize_django_types()`; nothing runs per request, resolver or row

## Implementation (Worker-2)

Attribution: every path touched was clean against `HEAD` 4cc95b77 and `ITEM_BASELINE` b43e2f2f
before the first edit (blobs equal to the records' fingerprints); no hunk to attribute. Concurrent
dirty paths (`optimizer/walker.py`, `tests/optimizer/`, `tests/optimizer/test_walker.py`,
`examples/fakeshop/`, `KANBAN.*`, `docs/bug_hunt/`, `docs/dry/`) were not opened for edit.
Pre-existing failures: none (`review-20260925T171504-468163`, before copy, the eight affected
modules: 619 passed).

### Performance

No findings (record `no-findings`); nothing implemented. No bench figure moves: the change removes
two fields and a hash method from a cold, declaration-time record.

### Mechanics

- **M1 (Low) - implemented.** `django_strawberry_framework/types/relations.py::PendingRelation` is
  `@dataclass(frozen=True, eq=False)`; `PendingRelation.__hash__` and `_hash_component` deleted.
  Tests: `tests/types/test_relations.py` loses `test_equal_pending_relations_have_equal_hashes` and
  `test_pending_relation_hash_falls_back_when_value_and_type_hashing_fail` (both pinned the deleted
  mechanism) and gains `test_equal_valued_pending_relations_stay_distinct` (`replace(first)`:
  `first != second`, `len({first, second}) == 2`); the non-hashable hash / set tests stay as
  identity-hash pins. `tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation`
  sanity line is `assert record_a != record_b`, docstring "two records from the same values",
  comment restated. Beyond the Recommendation:
  `test_pending_relation_equality_still_works_with_non_hashable_django_field` is deleted, not
  rewritten: with `eq=False` there is no synthesized `__eq__` to "survive", and reflexive
  `pending == pending` is `object.__eq__`, which pins nothing of this module (Comments F5 rides on
  it, below).
- **M2 (Low) - implemented.** `relation_kind` and `nullable` fields and the `RelationKind` import
  deleted from `PendingRelation`; the two kwargs dropped in
  `django_strawberry_framework/types/base.py::_build_annotations`; the 13 test constructions
  (`tests/types/test_relations.py` via `_build_pending`, `tests/test_registry.py` 7,
  `tests/types/test_finalizer.py` 3) drop them, which removes the hand-rolled nullability rule and
  its stale `_record_pending_relation` comment, the `kind` / `field` locals it fed, and the orphan
  `relation_kind` import in `tests/test_registry.py` (rule 14; `ruff check` clean). Beyond the
  Recommendation, the cascade the removal leaves dead: `_build_annotations` read its `field_map`
  parameter only for the two snapshot kwargs (`field_meta = field_map[field.name]` was its sole
  use), so the parameter, that local and the `field_map=field_map` argument in
  `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` are deleted too (the
  `field_map` local there still feeds `register_with_definition` and `DjangoTypeDefinition`);
  test callers `tests/types/test_definition_order.py` (2 sites) and
  `tests/types/test_relay_interfaces.py` (4 sites) drop the argument, and the then-unused
  `_field_map_for` helper and `FieldMeta` import in `tests/types/test_relay_interfaces.py` go
  (`check_citations.py --cited-by` on `_field_map_for`: 0 citers). Leaving the parameter would have
  been a caller-supplied value no body reads. The finalizer keeps reading `FieldMeta` from
  `definition.field_map[pending.field_name]`, unchanged.

Proof lines (shared tree, static):
`rg -c "_hash_component|def __hash__" django_strawberry_framework/types/relations.py` exit 1, no
output; `rg -c "@dataclass\(frozen=True, eq=False\)" ...` `1`;
`rg -c "relation_kind|nullable|RelationKind" ...` exit 1; `uv run ruff check tests/test_registry.py`
passes.

Before / after, `python /Users/riordenweber/projects/django-strawberry-framework/docs/review/temp-tests/types__relations/mechanics/probe_proof.py`:

- before `review-20260925T171456-5f8867` (`workspace.py run review/types/relations.py/before -- python <probe>`):
  `fields: source_type,source_model,field_name,django_field,related_model,relation_kind,nullable`,
  `identity hash: False identity eq: False`, `module has _hash_component: True`, 176 added, 0
  remaining (the before copy synced 17:00, before the concurrent library model; the reviewer's 178
  is the later tree).
- after `review-20260925T171715-9462ff` (`workspace.py run review/types/relations.py/implement --fresh -- python <probe>`):
  `fields: source_type,source_model,field_name,django_field,related_model`,
  `identity hash: True identity eq: True`, `module has _hash_component: False`, 178 added, 0
  remaining.

Tests, at the address `review/types/relations.py/implement` (package tier: nothing a GraphQL
request observes; the record identity is internal to declaration / finalize):

- the Proof's six-module command
  `pytest tests/types/test_relations.py tests/test_registry.py tests/types/test_finalizer.py tests/types/test_base.py tests/types/test_definition_order.py tests/types/test_definition_relations.py --no-cov -q`:
  `review-20260925T171720-f00ebf`, 350 passed, exit 0;
- `pytest tests/types/test_relay_interfaces.py tests/utils/test_relations.py --no-cov -q`:
  `review-20260925T171724-77a6c3`, 267 passed;
- full suite `pytest --no-cov -q -p no:randomly`: `review-20260925T171736-510636`, 8861 passed,
  40 skipped, 2 failed = the two `tests/test_ci_governance.py` git-census rows a copy fails by
  construction (`test_the_sweep_corpus_covers_every_committable_python_file`,
  `test_the_git_oracle_enumerates_this_module`);
- shared tree, focused: `uv run pytest tests/types/test_relations.py tests/test_registry.py tests/types/test_finalizer.py tests/types/test_base.py tests/types/test_definition_order.py tests/types/test_definition_relations.py tests/types/test_relay_interfaces.py tests/utils/test_relations.py --no-cov -q`
  617 passed (619 before: -3 deleted, +1 new).

Failability, `workspace.py prove review/types/relations.py/implement /Users/riordenweber/projects/django-strawberry-framework/docs/review/temp-tests/types__relations/implement/prove_m1.json`,
run `review-20260925T172025-057e3c`, exit 0, scope the six modules + `--no-cov --show-capture=no`,
restore byte-proved both entries:

1. the Proof's mutation, `@dataclass(frozen=True, eq=False)` -> `@dataclass(frozen=True)`: pinned,
   4 rows = declared set: `tests/types/test_relations.py::test_equal_valued_pending_relations_stay_distinct`,
   `::test_pending_relation_hash_supports_non_hashable_django_field`,
   `::test_pending_relation_is_set_member_with_non_hashable_django_field` (a synthesized field hash
   raises on the unhashable field) and
   `tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation`.
   The Proof names only the first; the other three fail for the same reason and are listed so
   the declared set is exact.
2. value `__eq__` beside a guarded `__hash__` (the pre-M1 semantics on the post-M2 fields,
   `eq=False` kept): pinned, 2 rows = `test_equal_valued_pending_relations_stay_distinct` and the
   registry identity test; the hash / set tests pass, so the new test is the one that sees value
   equality return while hashing stays tolerant.

M2 relies on no gate a mutation can remove: a stored field with no reader cannot fail a test;
its Proof is the static `rg`, the probe's field list and the pytest exit (a leftover kwarg at any
construction site raises `TypeError`, so exit 0 over the six modules exercises every site).

### Comments

- **F1 (Medium) - implemented** with the text after verbatim: module body rewritten, first line
  unchanged.
- **F2 (Medium) - implemented, text improved.** First line and constructor paragraph as proposed;
  the identity paragraph restated for M1 ("Records compare and hash by identity (``eq=False``) ...
  ``TypeRegistry.discard_pending()`` removes exactly the instances finalization hands back"), since
  "an equal copy is never discarded in their place" presumes value equality M1 removed. The
  `field_name` paragraph keeps its sentence and replaces the M2-falsified snapshot sentence with
  "finalization reads the relation's ``FieldMeta`` (cardinality, nullability) from that map, so the
  record carries none of it".
- **F3 (Medium) - implemented, text superseded by M1** (Mechanics cross-axis): the module docstring
  first paragraph states identity semantics and keeps F3's true reason for the unhashable input
  (malformed metadata, a custom field class defining `__eq__` without `__hash__`);
  `_NonHashableField` docstring as proposed; the hash test docstring says records hash by identity
  and "non-hashable relation metadata". First line changed (it said "hash consistency"): now
  "PendingRelation tests for identity semantics, frozen fields and the sentinel annotation repr.";
  `docs/TREE.md` re-rendered, two rows, both this change.
- **F4 (Low) - implemented** (rides on the file F1/F2 change): comment block in
  `_PendingRelationAnnotationMeta` deleted, `PendingRelationAnnotation` docstring = text after; the
  repr string byte-identical (`test_pending_relation_annotation_repr` passes).
- **F5 (Low) - discharged by M1**: the test holding the comment is deleted (above), and with it the
  `#"assert record_a == record_b"` substring citation.
- Cross-axis (Mechanics for Comments), all landed: the `relations.py` module and class prose M1/M2
  falsified (via F1/F2); `tests/types/test_relations.py` module docstring (via F3);
  `tests/utils/test_relations.py::test_relation_kind_reverse_many_to_one_is_in_literal` docstring
  restated on its own terms ("``relation_kind`` returns this value for a reverse foreign key, so
  the alias that types its return must list it").

Proof lines: `rg -c "not yet registered|until the target type registers|spec-0|import-order trap|may pass back"`,
`rg -c "was not registered|not yet registered"`, `rg -c "rewrite was skipped|was skipped and"` on
the target, `rg -c "rel descriptor"` and `rg -c "Identity equality|the existing"` on
`tests/types/test_relations.py`: all exit 1, no output. `build_tree_md.py --list-docstrings` on
all eight touched modules: 0 breaking the first-line rule.

Inverse proof. The F1/F2/F4 Proofs name `--code-digest b43e2f2f...:<target> <target>` exit 0;
that cannot hold once M1/M2 moved code in the same file (it prints `dec4dd9b...` vs
`dfc00e12...`, exit 1). The equivalent identity, that the Comments edits moved no code:
`uv run python scripts/review_inspect.py --code-digest docs/review/temp-tests/types__relations/implement/relations.mechanics_only.py django_strawberry_framework/types/relations.py`
exit 0, both `sha256:dfc00e12...`, where `relations.mechanics_only.py` is the item-baseline file
(`relations.item_baseline.py`, `git show b43e2f2f:<target>`) with only the M1/M2 code edits applied
by exact-match string replacement and every original docstring and comment kept. The same for F3
is subsumed by M1's rewrite of `tests/types/test_relations.py` (code there moved by M1, graded by
the Mechanics verifier). `tests/utils/test_relations.py`, prose only:
`--code-digest b43e2f2fb07e4c13ee93056c09a5a94ede07065f:tests/utils/test_relations.py tests/utils/test_relations.py`
exit 0, `57f02395...` both.

### Lint and render

`uv run ruff check --fix`, `uv run python scripts/check_trailing_commas.py`, `uv run ruff format`
on the eight paths below: 0 fixes, 0 violations, 8 unchanged; then `ruff check`, `ruff format
--check`, `check_trailing_commas.py --check` pass, `check_citations.py --check` `OK: 1287 citations
resolve`. `uv run python scripts/build_tree_md.py` wrote `docs/TREE.md`; its diff is the two
`test_relations.py` rows only.

Diff check: `git diff b43e2f2fb07e4c13ee93056c09a5a94ede07065f --` the nine paths below shows only
this pass's hunks; no new files.

Scratch: `docs/review/temp-tests/types__relations/implement/` (`prove_m1.json`,
`relations.item_baseline.py`, `relations.mechanics_only.py`); proof JSON in the workspace evidence
folder `proofs/types__relations.py/implement/review-20260925T172025-057e3c.json`.

Fingerprints (`git hash-object`, after): `django_strawberry_framework/types/relations.py`
5e9b5cdbc7fb919f15afef090a2aae5c7663b706; `django_strawberry_framework/types/base.py`
dda91365a7e8cb146d718b6f61b95e4821d6a555; `tests/types/test_relations.py`
2e18880ad7f4f816ee74327c2c128f6fab3398bc; `tests/test_registry.py`
8b33f291ed66eee76ca6209ebd76ffb04f9d1b76; `tests/types/test_finalizer.py`
ad82b908d77b2e2b7c5757f556605727da01a2e9; `tests/types/test_definition_order.py`
aff87c5211e97940781d03d3bc2b43fb3bb83fff; `tests/types/test_relay_interfaces.py`
515ebce54705de09907ed16b7bc2d8b3f3014976; `tests/utils/test_relations.py`
e51cebaa4a9b16745eb8f5357c782880f136e6d4; `docs/TREE.md` 5d5627339ba1d22ea2fc96e60163ab4808caa8d2;
read unchanged: `django_strawberry_framework/types/finalizer.py`
de34ae2aaed10fd664197cc2205c29e7d1927c2d, `django_strawberry_framework/registry.py`
9cc8bb553fd417fc465809a541769a8383469cda.

Proposed owned changes:

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/types/relations.py` | types/relations.py | Mechanics, Comments | `PendingRelation` (`eq=False`; fields `relation_kind`, `nullable` removed; `__hash__` removed; docstring); `_hash_component` removed; `RelationKind` import removed; `_PendingRelationAnnotationMeta` comment removed; `PendingRelationAnnotation` docstring; module docstring |
| `django_strawberry_framework/types/base.py` | types/relations.py | Mechanics | `_build_annotations` (`field_map` parameter, `field_meta` local and the two snapshot kwargs removed); `DjangoType.__init_subclass__` (`field_map` argument removed) |
| `tests/types/test_relations.py` | types/relations.py | Mechanics, Comments | module docstring (first line); `_NonHashableField` docstring; `_build_pending`; `test_pending_relation_hash_supports_non_hashable_django_field` docstring; `test_equal_valued_pending_relations_stay_distinct` (new); `test_pending_relation_equality_still_works_with_non_hashable_django_field`, `test_equal_pending_relations_have_equal_hashes`, `test_pending_relation_hash_falls_back_when_value_and_type_hashing_fail` removed |
| `tests/test_registry.py` | types/relations.py | Mechanics | `test_finalize_discards_consumer_authored_pending_relation_without_rewriting_annotation`, `test_discard_pending_uses_identity_match_with_real_pending_relation` (docstring, comment, sanity assert), `test_discard_pending_tolerates_non_hashable_django_field`, `test_mutators_reject_calls_after_mark_finalized`, `test_unregister_removes_pending_relations_sourced_from_type`; `relation_kind` import removed |
| `tests/types/test_finalizer.py` | types/relations.py | Mechanics | `test_unresolved_relation_diagnostic_survives_hostile_model_name`, `test_malformed_pending_field_name_is_rejected_before_relation_lookup`, `test_pending_relation_without_source_definition_is_typed` |
| `tests/types/test_definition_order.py` | types/relations.py | Mechanics | `test_annotation_only_scalar_override_does_not_emit_synthesized_annotation`, `test_auto_annotation_emits_synthesized_annotation` |
| `tests/types/test_relay_interfaces.py` | types/relations.py | Mechanics | `_field_map_for` removed; `FieldMeta` import removed; `test_relay_node_strips_django_id_annotation`, `test_extended_node_interface_subclass_suppresses_id_annotation`, `test_non_relay_type_keeps_id_int`, `test_direct_relay_node_inheritance_suppresses_id_annotation` (`field_map=` argument removed) |
| `tests/utils/test_relations.py` | types/relations.py | Comments | `test_relation_kind_reverse_many_to_one_is_in_literal` docstring |
| `docs/TREE.md` | types/relations.py | Comments | `tests/types/test_relations.py` rows (two) |

Handoff: read beyond the records `_build_annotations` whole, `DjangoType.__init_subclass__`'s
`field_map` flow, the finalizer Phase 1 loop, and every `_build_annotations` caller in the repo
(`rg`, 1 production + 6 test sites). The one step past the Recommendations is the `field_map`
parameter removal, which M2 made dead; the Mechanics verifier should grade it (reverting it alone
leaves ruff quiet on a keyword-only parameter, so only reading shows it). The relation-branch
history comment in `_build_annotations` ("The earlier eager-bind branch ... spec-018") sits two
lines above an edited hunk and was left: it is routed to the `types/base.py` item under
`## Decisions` and this change does not make it false. KANBAN.md card TODO-ALPHA-053 item (c)
names the stale `_record_pending_relation` comment in
`tests/test_registry.py::test_finalize_discards_consumer_authored_pending_relation_without_rewriting_annotation`;
that comment is gone with M2, so the card item is discharged (board DB, Worker-0 / Rio). The
fixture count 176 vs 178 is the concurrent library model, not this change.

## Iterations

### Implement pass 2

Re-dispatch: revision-needed, Comments `## Verification (Comments)` gaps V1 and V2 (Performance and
Mechanics verified). Prose only; no code moved, so no before / after, permanent test or
failability.

Attribution: `django_strawberry_framework/registry.py` clean at `HEAD` 4cc95b77 (blob `9cc8bb55`,
equal to `ITEM_BASELINE`); `tests/test_registry.py` blob `8b33f291` = this item's pass-1 file
(the verifier's `verify-comments-1/test_registry.pass1.py`), so every hunk is this item's. The
other seven item paths and `docs/TREE.md` still hash to the pass-1 fingerprints; not touched.
`check_citations.py --cited-by django_strawberry_framework/registry.py::TypeRegistry.discard_pending`:
0 citers; `rg` for the two removed phrases outside `docs/review/rev-*`: hits only in the edited
lines themselves.

- **V1 (Medium) - implemented**, text after verbatim:
  `tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation`
  second paragraph is now "Builds two records from the same values and asserts that discarding one
  leaves the other in place." (rewrapped to the line length); first line, the "Registry lifecycle"
  paragraph and the sanity comment unchanged.
- **V2 (Medium) - implemented**, text after verbatim:
  `django_strawberry_framework/registry.py::TypeRegistry.discard_pending` docstring second paragraph
  is now "Identity-matched (``id()``): the finalizer hands back the very ``PendingRelation``
  instances it received from ``iter_pending_relations``, and matching by ``id()`` keeps this module
  independent of ``PendingRelation``'s equality and hashability.", wrapped at the file's existing
  docstring width; first line unchanged. This adds `registry.py` to the item diff.

Proof lines, shared tree:

- V1 `rg -c "Pins the identity-based contract" tests/test_registry.py`: no output, exit 1;
  `uv run python scripts/review_inspect.py --code-digest docs/review/temp-tests/types__relations/verify-comments-1/test_registry.pass1.py tests/test_registry.py`:
  exit 0, `sha256:1cda0e26...` both.
- V2 `rg -c "stronger contract" django_strawberry_framework/registry.py`: no output, exit 1;
  `uv run python scripts/review_inspect.py --code-digest b43e2f2fb07e4c13ee93056c09a5a94ede07065f:django_strawberry_framework/registry.py django_strawberry_framework/registry.py`:
  exit 0, `sha256:ac9a0c24...` both.
- `build_tree_md.py --list-docstrings` on both paths: 2 modules, 0 breaking; neither first line
  changed, so no TREE.md render.

Lint, on `django_strawberry_framework/registry.py tests/test_registry.py`: `ruff check --fix`,
`check_trailing_commas.py`, `ruff format` (0 fixes, 0 violations, 2 unchanged); then `ruff check`,
`ruff format --check`, `check_trailing_commas.py --check` pass; `check_citations.py --check`
`OK: 1287 citations resolve`.

Diff check: `git diff b43e2f2fb07e4c13ee93056c09a5a94ede07065f -- django_strawberry_framework/registry.py`
is the one docstring hunk; `diff` of `verify-comments-1/test_registry.pass1.py` against
`tests/test_registry.py` is the one docstring hunk. No new files. No run ids this pass (nothing
imported the package or opened a database).

Fingerprints (`git hash-object`, after): `django_strawberry_framework/registry.py`
81bd561c99cb364cb2bd90b10b67c719a42c5d47; `tests/test_registry.py`
48af782ff707baaf1619da26d2e286d2ba5178f4; unchanged since pass 1: `types/relations.py` 5e9b5cdb,
`types/base.py` dda91365, `tests/types/test_relations.py` 2e18880a,
`tests/types/test_finalizer.py` ad82b908, `tests/types/test_definition_order.py` aff87c52,
`tests/types/test_relay_interfaces.py` 515ebce5, `tests/utils/test_relations.py` e51cebaa,
`docs/TREE.md` 5d562733.

Proposed owned changes (rows this pass adds or changes):

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/registry.py` | types/relations.py | Comments | `TypeRegistry.discard_pending` (docstring) |
| `tests/test_registry.py` | types/relations.py | Mechanics, Comments | pass-1 row plus `test_discard_pending_uses_identity_match_with_real_pending_relation` docstring (Comments) |

Handoff: read beyond the V1/V2 records only the `discard_pending` body and the identity test body
to confirm the new text; nothing else opened. Both edits are prose-only with `--code-digest`
identity, so per REVIEW.md "Worker-0 closes the item" this re-pass owes Comments alone. The
verifier's Mechanics lead (the `assert record_a != record_b` sanity line now pins `eq=False` a
second time) was not acted on: it is not a Comments gap and the verifier graded it not a defect.
The two `tests/types/test_relay_interfaces.py` provenance leads stay outside this item.
