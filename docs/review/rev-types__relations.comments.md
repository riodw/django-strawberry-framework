# Review · Comments: `django_strawberry_framework/types/relations.py`

Status: verified
Run: 0.0.15 2026-09-25-2

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=b43e2f2fb07e4c13ee93056c09a5a94ede07065f

## Trace

Read the whole target (module docstring, 6 symbol docstrings, one 5-line comment block in
`_PendingRelationAnnotationMeta`) and its own test module `tests/types/test_relations.py` (module
docstring, 7 test docstrings, `_NonHashableField` docstring, one comment block). One real caller per
symbol, body read: producer `django_strawberry_framework/types/base.py::_build_annotations` (the
relation branch appends a `PendingRelation` and installs the sentinel for every relation not in
`consumer_authored_fields`, with no registration check); consumer
`django_strawberry_framework/types/finalizer.py::finalize_django_types` (reads
`definition.field_map[pending.field_name]`, never `pending.nullable` / `pending.relation_kind`;
rewrites `source_type.__annotations__` via `resolved_relation_annotation`; hands the same records
to `discard_pending`); `django_strawberry_framework/registry.py::TypeRegistry.discard_pending`
(`id()` set, no `==`, no `hash`). Other test prose about the target's symbols:
`tests/test_registry.py` (identity tests at `test_discard_pending_uses_identity_match_with_real_pending_relation`,
`test_discard_pending_tolerates_non_hashable_django_field`), `tests/types/test_finalizer.py`,
`tests/types/test_base.py`, `tests/utils/test_relations.py` (all true or not about this file's
claims). `docs/GLOSSARY.md` "Definition-order independence" (concept only; neither symbol is public:
`types/__init__.py` `__all__` is `DjangoType`, `SyncMisuseError`, `finalize_django_types`). Django
`ForeignObjectRel.__hash__` / `Field.__hash__` in `.venv` (6.1) and in the uv cache
(5.2.17; floor pin `Django>=5.2.16`): both define `__hash__` (`hash(self.identity)`,
`hash(self.creation_counter)`).

Instruments: `review_inspect.py` (`<root>/comments/relations.json`; census 7 entries, every symbol
docstringed bar the private `_PendingRelationAnnotationMeta.__repr__`); `build_tree_md.py
--list-docstrings` on the target and on `tests/types/test_relations.py`: both `ok`;
`check_citations.py --paths <target> --substrings --json`: 4 citations, all resolve;
`--paths tests/types/test_relations.py --substrings`: 2, both resolve; provenance `rg`: 4 hits
(`spec-010`, `spec-018` -> F1; two `discard_pending` substring hits on `card`, false positives).

Probes (workspace, cell `default`; the target's prose reaches no database, alias or dialect
decision, so `sharded` / `pg` are inapplicable by construction):

- `review-20260925T170235-567b47` (`<root>/comments/probe_sentinel.py`): a `DjangoType` over
  `Branch` installs the sentinel on 6 relations. (A) `strawberry.Schema` over the unfinalized type
  raises `TypeError ... Unexpected type '<class '__main__.ProbeBranchType'>'`, no sentinel repr;
  (B) `strawberry.type(ProbeBranchType2)` applied by hand before finalize, then a schema, raises
  `TypeError ProbeBranchType2 fields cannot be resolved. Unexpected type '<unfinalized DjangoType
  relation; ...>'`. The repr surfaces only when Strawberry decorates a type whose finalization
  never ran.
- `review-20260925T170306-eaa8ff` (`<root>/comments/probe_rel_hash.py`): every relation field and
  rel on every installed fakeshop model, `get_fields(include_hidden=True)`: 303 examined, 0 refuse
  `hash()` (Django 6.1).

Fingerprints: `django_strawberry_framework/types/relations.py`
4098eebca9b9fad9e328bdbc920ff863e3a229e9; `tests/types/test_relations.py`
bff8c265cc6baa956feb0a76b5e846c09bb58a42; `django_strawberry_framework/types/base.py`
49057fad2058ee63635c7951bfcd7ab8d9a0be30; `django_strawberry_framework/types/finalizer.py`
de34ae2aaed10fd664197cc2205c29e7d1927c2d; `django_strawberry_framework/registry.py`
9cc8bb553fd417fc465809a541769a8383469cda; `django_strawberry_framework/utils/relations.py`
8dbc3fe668dda7d57f1e2b2a3af66afdda449ded; `tests/test_registry.py`
e330cfb81e4bbe9f4f04bc7e1b30038097a3bb10; `tests/utils/test_relations.py`
b82f9cc19345c175882cd44652255779426456c0; `docs/GLOSSARY.md`
b8b68f465d03880af31a25817f94fed374249a21.

## Findings

### High

None.

### Medium

#### F1 - module docstring says records exist only for unregistered targets (stale), cites bare specs

- **Observation** - `django_strawberry_framework/types/relations.py` module docstring body. It
  describes `PendingRelation` as "capturing a relation field whose target ``DjangoType`` was not
  yet registered at collection time" and the sentinel as installed "until the target type
  registers"; two sentences later it says every auto-synthesized relation is routed through them
  "unconditionally". The producer records every auto-synthesized relation whether or not its target
  is registered, and the sentinel stays until `finalize_django_types` rewrites it, not until the
  target registers. `(spec-010)` and `(spec-018)` are bare spec pointers (provenance), and "closes
  the import-order trap" narrates a fix instead of stating the rule. The last three sentences
  restate the `PendingRelation` class docstring and `TypeRegistry.discard_pending`'s own docstring;
  "callers may pass back the same object" inverts the contract (they must: an equal copy is never
  discarded).
- **Evidence** - `django_strawberry_framework/types/base.py::_build_annotations` relation branch
  (append + sentinel with no `registry.get` check; its comment "Always defer auto-synthesized
  relation annotations"); `django_strawberry_framework/types/finalizer.py::finalize_django_types`
  rewrite loop; `django_strawberry_framework/registry.py::TypeRegistry.discard_pending` (`id()`).
- **Impact** - a reader believes a relation whose target is already registered is bound eagerly,
  the exact eager-bind the module exists to forbid; the two framings contradict each other in one
  docstring.
- **Severity** - Medium: stale prose on internal code (neither symbol is exported or documented as
  public).
- **Recommendation** - rewrite the body; first line unchanged (no `docs/TREE.md` row moves).
  Text after:

  ```text
  Pending relation records for definition-order-independent ``DjangoType`` finalization.

  ``_build_annotations`` (``types/base.py::_build_annotations``) records a ``PendingRelation``
  for every auto-synthesized relation field and installs ``PendingRelationAnnotation`` as its
  annotation, whether or not the target ``DjangoType`` is registered yet, so the relation binds
  to the target model's primary type whatever order the types are declared in.
  ``finalize_django_types`` (``types/finalizer.py::finalize_django_types``) replaces each
  sentinel with ``resolved_relation_annotation`` and hands the resolved records back to
  ``TypeRegistry.discard_pending``.
  ```
- **Must not change** - n/a.
- **Proof** - `rg -c "not yet registered|until the target type registers|spec-0|import-order trap|may pass back" django_strawberry_framework/types/relations.py`
  prints nothing (exit 1); `uv run python scripts/review_inspect.py --code-digest b43e2f2fb07e4c13ee93056c09a5a94ede07065f:django_strawberry_framework/types/relations.py django_strawberry_framework/types/relations.py`
  exit 0; `uv run python scripts/build_tree_md.py --list-docstrings django_strawberry_framework/types/relations.py`
  `ok` with the unchanged first line; the module docstring grades true against the three bodies in
  Evidence.
- **Freshness** - Trace fingerprints.

#### F2 - `PendingRelation` docstring: constructed only when the target is unregistered (stale)

- **Observation** - `django_strawberry_framework/types/relations.py::PendingRelation`. First line
  "Relation field whose target ``DjangoType`` was not registered during collection." and "Constructed
  by ``_build_annotations`` ... when a relation target type is not yet registered" are false: every
  auto-synthesized relation field gets a record. The identity paragraph is true but is where the
  must-hand-back-the-same-instance requirement belongs (F1 removes the module's copy).
- **Evidence** - as F1; `field_name` paragraph checked true (`_build_annotations` keys
  `field_map[field.name]`; finalizer reads `definition.field_map[pending.field_name]`; no package
  reader of `pending.nullable` / `pending.relation_kind`, `rg` over `django_strawberry_framework/`).
- **Impact** - same misreading as F1 at the symbol a reader of the finalizer lands on.
- **Severity** - Medium: stale docstring on internal code.
- **Recommendation** - Text after (the `field_name` paragraph unchanged):

  ```text
  Auto-synthesized relation field awaiting its target ``DjangoType`` at finalization.

  Constructed by ``_build_annotations`` (``types/base.py::_build_annotations``) for every
  auto-synthesized relation field, registered target or not; resolved by
  ``finalize_django_types`` (``types/finalizer.py::finalize_django_types``) after every
  ``DjangoType`` has registered. Finalization hands the same record instances back to
  ``TypeRegistry.discard_pending()``, which removes them by identity, so an equal copy is never
  discarded in their place.
  ```
- **Must not change** - n/a.
- **Proof** - `rg -c "was not registered|not yet registered" django_strawberry_framework/types/relations.py`
  prints nothing (exit 1); the F1 `--code-digest` command exit 0; the docstring grades true against
  `django_strawberry_framework/types/base.py::_build_annotations` and
  `django_strawberry_framework/registry.py::TypeRegistry.discard_pending`.
- **Freshness** - Trace fingerprints.

#### F3 - test module states a false reason for the guarded hash (Django rels "whose `__hash__` is None")

- **Observation** - `tests/types/test_relations.py` module docstring ("``django_field`` may be a
  Django rel descriptor whose ``__hash__`` is ``None`` (non-hashable)"), `_NonHashableField`
  docstring ("Stand-in for a Django rel descriptor whose ``__hash__`` is ``None``") and
  `test_pending_relation_hash_supports_non_hashable_django_field` docstring ("for a non-hashable
  rel descriptor"). Django's relation fields and rels all define `__hash__`, and a
  `ForeignObjectRel` is not a descriptor (the descriptor is the model-class accessor). The source's
  own framing, `_hash_component` "malformed unhashable metadata", is the true one.
- **Evidence** - `review-20260925T170306-eaa8ff`: 303 real relation fields / rels, 0 unhashable;
  Django 6.1 `.venv` and 5.2.17 (uv cache) `reverse_related.py` `ForeignObjectRel.__hash__` returns
  `hash(self.identity)`, `fields/__init__.py` `Field.__hash__` returns `hash(self.creation_counter)`.
- **Impact** - a wrong stated reason (DRY principle 10): a reader "fixing" the guard for Django
  compatibility, or deleting it once they find Django rels hash, acts on a false premise; the real
  input is consumer-supplied field metadata (a custom field class that defines `__eq__` without
  `__hash__` has `__hash__ = None`).
- **Severity** - Medium: a false stated reason in the target's own test module.
- **Recommendation** - Text after, module docstring first paragraph:

  ```text
  The ``@dataclass(frozen=True)`` decorator synthesizes value-based equality.
  Django's own relation fields and rels hash, but ``django_field`` may be
  malformed metadata that refuses ``hash()`` (a custom field class defining
  ``__eq__`` without ``__hash__``), so ``PendingRelation.__hash__`` uses guarded
  hash components that keep equal records equal in sets without requiring the
  field to be hashable. ``TypeRegistry.discard_pending`` still matches records
  by identity, independently of equality or hashing.
  ```

  `_NonHashableField`: "Stand-in for relation metadata whose ``__hash__`` is ``None``."; in the
  test docstring, "for a non-hashable rel descriptor" -> "for non-hashable relation metadata".
  First line unchanged (no `docs/TREE.md` row moves).
- **Must not change** - n/a.
- **Proof** - `rg -c "rel descriptor" tests/types/test_relations.py` prints nothing (exit 1);
  `uv run python scripts/review_inspect.py --code-digest b43e2f2fb07e4c13ee93056c09a5a94ede07065f:tests/types/test_relations.py tests/types/test_relations.py`
  exit 0; the rewritten text grades true against the Django sources named in Evidence.
- **Freshness** - Trace fingerprints.

#### V1 (verify 1) - registry identity test docstring claims a pin M1 took away (stale)

- **Observation** - `tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation`
  docstring, second paragraph: "Pins the identity-based contract so this module does not couple to
  ``PendingRelation``'s ``__eq__``/``__hash__`` semantics." Worker-2 rewrote the next sentence of
  this paragraph and left this one. At `ITEM_BASELINE` it was true: records were value-equal, so an
  equality-based `discard_pending` would drop both records and fail the test. After M1
  (`eq=False`) `PendingRelation.__eq__` is identity, so an equality-based `discard_pending` passes
  this test, and the test cannot tell identity matching from equality matching.
- **Evidence** - `workspace.py prove`, manifest
  `docs/review/temp-tests/types__relations/verify-comments-1/prove_eq_discard.json`, run
  `review-20260925T173151-17cfec`: `TypeRegistry.discard_pending` changed to
  `pending not in list(resolved)` (list membership = `==`). Scope `tests/test_registry.py
  tests/types/test_relations.py tests/types/test_finalizer.py`: 102 passed mutated, 102 unmutated,
  `expect_failing: []` met, restore byte-proved (`9cc8bb55` both sides). This test is among them.
- **Impact** - the docstring says the test guards a registry design choice it can no longer see; a
  maintainer who trusts it will not notice that the registry could switch to equality matching
  unobserved. (No behavior differs today; the observation is about the prose.)
- **Severity** - Medium: stale docstring on internal test code, made false by this item's change.
- **Recommendation** - delete that sentence. Text after, second paragraph: "Builds two records from
  the same values and asserts that discarding one leaves the other in place." (first line and the
  "Registry lifecycle" paragraph unchanged; the sanity comment stays as it is).
- **Must not change** - n/a.
- **Proof** - `rg -c "Pins the identity-based contract" tests/test_registry.py` prints nothing
  (exit 1); `uv run python scripts/review_inspect.py --code-digest docs/review/temp-tests/types__relations/verify-comments-1/test_registry.pass1.py tests/test_registry.py`
  exit 0 (the pre-image is the pass-1 file, blob `8b33f291`); the whole docstring grades true
  against the test body.
- **Freshness** - `tests/test_registry.py` 8b33f291ed66eee76ca6209ebd76ffb04f9d1b76;
  `django_strawberry_framework/registry.py` 9cc8bb553fd417fc465809a541769a8383469cda.

#### V2 (verify 1) - `discard_pending` gives a reason M1 made false ("identity is a stronger contract than `__eq__`")

- **Observation** - `django_strawberry_framework/registry.py::TypeRegistry.discard_pending`
  docstring: "the finalizer hands back the very ``PendingRelation`` instances it received from
  ``iter_pending_relations``, so identity is a stronger contract than ``__eq__`` and avoids
  coupling this module to ``PendingRelation``'s hashability." After M1 `PendingRelation.__eq__` is
  `object.__eq__`, which is identity, so the comparison it rests on no longer holds. The second
  reason (independence from the record's hashability) still holds. `registry.py` is not in the
  item diff. This goes on the item under REVIEW.md "Worker-1 verifies" because this item's change
  made the text false.
- **Evidence** - `django_strawberry_framework/types/relations.py::PendingRelation`
  (`@dataclass(frozen=True, eq=False)`); the V1 prove run shows equality matching and identity
  matching behave the same now.
- **Impact** - a wrong stated reason (DRY principle 10): it tells a reader that records carry a
  value equality weaker than identity, which is the semantics M1 removed.
- **Severity** - Medium: stale docstring on internal code.
- **Recommendation** - Text after (first line unchanged):

  ```text
  Drop pending records that have been resolved successfully.

  Identity-matched (``id()``): the finalizer hands back the very ``PendingRelation``
  instances it received from ``iter_pending_relations``, and matching by ``id()`` keeps
  this module independent of ``PendingRelation``'s equality and hashability.
  ```
- **Must not change** - n/a.
- **Proof** - `rg -c "stronger contract" django_strawberry_framework/registry.py` prints nothing
  (exit 1); `uv run python scripts/review_inspect.py --code-digest b43e2f2fb07e4c13ee93056c09a5a94ede07065f:django_strawberry_framework/registry.py django_strawberry_framework/registry.py`
  exit 0; the docstring grades true against the body and `PendingRelation`.
- **Freshness** - as V1.

### Low

#### F4 - sentinel comment and docstring: "skipped" overstates when the repr fires; the two restate each other

- **Observation** - `django_strawberry_framework/types/relations.py::_PendingRelationAnnotationMeta`
  comment block ("... fires when that rewrite was skipped") and
  `django_strawberry_framework/types/relations.py::PendingRelationAnnotation` docstring ("raised
  when ``finalize_django_types()`` was skipped and Strawberry sees the un-rewritten sentinel") say
  the same thing twice. Skipping finalization alone never shows the repr: Strawberry rejects the
  undecorated `DjangoType` class first. The repr surfaces only when `strawberry.type` decorates a
  `DjangoType` before finalization ran (`finalize_django_types` is the package's only
  `strawberry.type` call).
- **Evidence** - `review-20260925T170235-567b47` paths A and B.
- **Impact** - a maintainer debugging a "finalize skipped" report looks for the sentinel repr that
  path never produces.
- **Severity** - Low: bounded clarity; duplicated prose on private scaffolding.
- **Recommendation** - delete the comment block in `_PendingRelationAnnotationMeta` (its
  docstring stays); `PendingRelationAnnotation` text after:

  ```text
  Sentinel annotation ``finalize_django_types()`` replaces before ``strawberry.type`` runs.

  Strawberry meets it only when a ``DjangoType`` is decorated with ``strawberry.type`` before
  finalization ran; ``_PendingRelationAnnotationMeta`` then makes the schema-construction
  ``TypeError`` name the missing ``finalize_django_types()`` call instead of printing
  ``<class '...PendingRelationAnnotation'>``.
  ```
- **Must not change** - n/a (the repr string is code and stays byte-identical;
  `tests/types/test_relations.py::test_pending_relation_annotation_repr` pins it).
- **Proof** - `rg -c "rewrite was skipped|was skipped and" django_strawberry_framework/types/relations.py`
  prints nothing (exit 1); the F1 `--code-digest` command exit 0; the docstring grades true against
  the two probe paths.
- **Freshness** - Trace fingerprints.

#### F5 - equality test comment misdescribes `discard_pending` and another test

- **Observation** - `tests/types/test_relations.py::test_pending_relation_equality_still_works_with_non_hashable_django_field`
  comment: "Identity equality (used by ``discard_pending``)" (`discard_pending` compares `id()`
  values in a set, never `==`), and "the existing ... test relies on value equality across two
  distinct instances" describes another module's test, not the reflexive `pending == pending` this
  test asserts ("existing" is provenance wording). Value equality across two instances is pinned
  here by `tests/types/test_relations.py::test_equal_pending_relations_have_equal_hashes`.
- **Evidence** - `django_strawberry_framework/registry.py::TypeRegistry.discard_pending` body; the
  test body.
- **Impact** - the comment sends a reader to the wrong test and the wrong mechanism.
- **Severity** - Low: stale comment in a test.
- **Recommendation** - replace the comment with: "Reflexive equality holds through the synthesized
  ``__eq__``; value equality across two instances is pinned by
  ``test_equal_pending_relations_have_equal_hashes``."
- **Must not change** - n/a.
- **Proof** - `rg -c "Identity equality|the existing" tests/types/test_relations.py` prints nothing
  (exit 1); the F3 `--code-digest` command exit 0.
- **Freshness** - Trace fingerprints.

## Rejected

- Module first line, `review_inspect` "Pending relation records for definition-order-independent
  ``DjangoType`` finalization.": true and rule-clean. Reopen: the module gains a non-record symbol.
- `PendingRelation` `field_name` / snapshot-fields paragraph: true (Trace). Reopen: a package
  reader of `pending.nullable` or `pending.relation_kind` appears.
- `django_strawberry_framework/types/relations.py::_hash_component` docstring: true (three rungs;
  "malformed" matches 0/303 real rels unhashable). Reopen: a supported Django version ships an
  unhashable rel.
- `django_strawberry_framework/types/relations.py::PendingRelation.__hash__` docstring: true for
  records whose equal fields share a type. Whether equal-but-differently-typed unhashable values
  break hash/eq consistency is behavior, not prose (Handoff lead for Mechanics). Reopen: that
  behavior changes.
- `_PendingRelationAnnotationMeta` docstring: true. Its `__repr__` has no docstring: a private
  metaclass dunder whose class docstring owns it, not a public symbol. Reopen: the metaclass is
  exported.
- `tests/types/test_relations.py` first line "PendingRelation tests for hash consistency and
  dataclass field contracts." omits the one `PendingRelationAnnotation` repr test; true for 6 of 7
  tests, and rewording it is a TREE.md edit for a completeness nit. Reopen: the module gains more
  sentinel tests.
- Remaining test docstrings (`test_pending_relation_is_set_member_*`, `test_equal_*`,
  `test_pending_relation_hash_falls_back_*`, `test_pending_relation_annotation_repr`,
  `test_pending_relation_is_frozen_dataclass`, the module's live-tier pointer): true against their
  bodies; none opens "Tests that" / "Ensures". Reopen: a body changes.
- Citations: 4 in the target, 2 in the test module, all resolve; no line-number reference.
  Reopen: a cited symbol is renamed.
- Looks-for "intentional separation not recorded at the owner": `discard_pending`'s identity choice
  is recorded at its owner (`TypeRegistry.discard_pending` docstring). Nothing else applies.

## Handoff

Beyond the trace: the sentinel repr string itself ("call finalize_django_types() before
constructing strawberry.Schema") is code, out of this axis; on the only path that reaches it (a
consumer applying `strawberry.type` to a `DjangoType`, the decorator API the package rejects) the
advice is incomplete. Mechanics lead, no contract row found, not a finding here. Also for Mechanics:
nothing in the package hashes a `PendingRelation` (lists + `id()`), so the custom `__hash__` and
`_hash_component` serve only set membership in tests; and `_hash_component` catches
`BaseException`. Routed (other items' prose about this file's symbols):
`Routed: django_strawberry_framework/types/base.py::_build_annotations - relation-branch comment narrates history ("The earlier eager-bind branch ...", "closed by spec-018"); restate as the rule`;
`Routed: django_strawberry_framework/types/base.py - module docstring step 4 "records unresolved relations as pending records" is stale; every auto-synthesized relation is recorded`;
`Routed: django_strawberry_framework/utils/relations.py::relation_kind - "the registry's typed PendingRelation sentinel": PendingRelation is a record in types/relations.py, the sentinel is PendingRelationAnnotation`.
F1-F5 are prose-only: every Proof pairs an `rg` with `--code-digest` identity; no test, no
failability owed.

## Verification (Comments)

Pass 1, address `review/types/relations.py/verify-comments-1`.

Diff binding: `git diff b43e2f2fb07e4c13ee93056c09a5a94ede07065f --` the nine item paths hashes
`d1dad86b...67664499`, equal to `docs/review/temp-tests/types__relations/diff/pass-1.diff`.

Proof lines, run verbatim before reading `## Implementation (Worker-2)`:

- F1 `rg -c "not yet registered|until the target type registers|spec-0|import-order trap|may pass back"`
  on the target: no output, exit 1. Pass. `build_tree_md.py --list-docstrings` on the target: `ok`,
  first line unchanged. Pass.
- F2 `rg -c "was not registered|not yet registered"`: exit 1. Pass.
- F3 `rg -c "rel descriptor" tests/types/test_relations.py`: exit 1. Pass.
- F4 `rg -c "rewrite was skipped|was skipped and"`: exit 1. Pass.
- F5 `rg -c "Identity equality|the existing" tests/types/test_relations.py`: exit 1. Pass.
- F1/F2/F4 `--code-digest b43e2f2f...:django_strawberry_framework/types/relations.py <target>`:
  exit 1 (`dec4dd9b` vs `dfc00e12`). F3/F5 `--code-digest` on `tests/types/test_relations.py`:
  exit 1 (`946fdf82` vs `ecd88d8b`). Both were expected: M1/M2 moved code in these files. Judged
  below.
- Mechanics `## Cross-axis (for Comments)`, four entries, graded under "Whole-diff reading".

Substitute inverse proof, judged. Worker-2 compared the live target's digest with
`implement/relations.mechanics_only.py`. I checked that file with `diff` against `git show
b43e2f2f:<target>`. It differs only by the M1/M2 code: the `RelationKind` import, `_hash_component`
(with its own docstring), `eq=False`, the two fields and `__hash__` (with its own docstring). Every
docstring and comment that stays is byte-identical to the baseline. So it is a valid code-only
pre-image. I also built my own, without using theirs:
`verify-comments-1/relations.code_only.py`, which applies the same four code edits to the
baseline by anchored cuts. Its digest is `dfc00e12`, equal to the live file, exit 0. Worker-2's gave
the same, exit 0. Conclusion: the Comments edits in `types/relations.py` moved no code. For
`tests/types/test_relations.py` no digest applies, since M1 deleted two tests and added one. I read
its stripped-code diff (`verify-comments-1/diff/diff/tests__types__test_relations.diff`) instead:
every code hunk there is M1/M2 (`replace` import, dropped kwargs, the three removed tests, the new
test), and the Mechanics verifier graded all of it. No prose hunk hides code. `tests/utils/test_relations.py`,
prose only: `--code-digest b43e2f2f...` exit 0, `57f02395` both. In `types/base.py`, `test_registry.py`,
`test_finalizer.py`, `test_definition_order.py` and `test_relay_interfaces.py` the digest moves
(exit 1 each). Their prose diffs show changes only where M2 code changed too, and the
`test_relay_interfaces.py` hunk is the deleted `_field_map_for` helper with its docstring. The
substitute holds.

Whole-diff reading (prose diff from REVIEW.md "Comments" command, eight `--path`s, output
`verify-comments-1/diff/`). Each rewritten docstring graded as a whole:

- `types/relations.py` module docstring: true. `_build_annotations` records every non-consumer
  relation with no registration check. `finalize_django_types` resolves through `registry.get`
  (primary), rewrites via `resolved_relation_annotation`, and passes `resolved_pending` to
  `discard_pending`. First line unchanged, TREE.md row unmoved.
- `PendingRelation`: true. The identity paragraph matches `eq=False`. "finalization reads the
  relation's ``FieldMeta`` (cardinality, nullability)" matches `finalize_django_types` reading
  `definition.field_map[pending.field_name]` into `resolved_relation_annotation`, which branches on
  `meta.is_many_side` / `meta.nullable`. Worker-2 improved on F2's text after, because "an equal
  copy is never discarded" presumed the value equality M1 removed. Improvement accepted.
- `_PendingRelationAnnotationMeta` comment deleted and docstring kept; `PendingRelationAnnotation`
  docstring = F4 text after. True per probes `review-20260925T170235-567b47` and Mechanics
  `review-20260925T170834-619e41` (path C only). The repr string is byte-identical.
- `tests/types/test_relations.py` module docstring (first line included): true. The Mechanics
  prove run shows reverting `eq=False` fails the two non-hashable tests, which is what the "still
  hashes and joins a set" clause claims. A custom field class defining `__eq__` without
  `__hash__` gets `__hash__ = None` (Python data model). The live pointer
  `examples/fakeshop/test_query/test_library_api.py` exists. The first line is one sentence ending
  in `.` and `--list-docstrings` gives `ok`. `docs/TREE.md` changes in exactly its two rows
  (`git diff b43e2f2f -- docs/TREE.md`), both this row.
- `_NonHashableField`, `test_pending_relation_hash_supports_non_hashable_django_field` (whole
  docstring), and the new `test_equal_valued_pending_relations_stay_distinct` (states the behavior,
  does not open "Tests that"): true against their bodies.
- F5: discharged by M1. Deleting the test is correct (Mechanics verifier), and its comment and
  stale substring citation went with it.
- Cross-axis: the `tests/utils/test_relations.py::test_relation_kind_reverse_many_to_one_is_in_literal`
  docstring is true (`relation_kind` returns `"reverse_many_to_one"` for a reverse FK). The
  other three entries landed through F1/F2/F3 above.
- `tests/test_registry.py`: the deleted hand-rolled nullability comment went with M2. The rewritten
  sanity comment and "two records from the same values" are true. Its sibling sentence is not: new
  finding V1.
- Touched symbols whose prose the change did not edit: `_build_annotations` docstring (it never
  documented `field_map`, and nothing in it is false after the parameter removal), the 14 touched
  test functions in the other test modules (docstrings and comments read whole via AST, none
  mentions `field_map`, snapshots, hashing or equality), and `DjangoType.__init_subclass__` at the
  call. None was made false. The `_build_annotations` relation-branch history comment was routed
  before the change (plan `## Decisions`) and the change did not make it false.
- Provenance / `we` / line numbers: 64 added lines scanned with the REVIEW.md provenance `rg` plus
  `\bwe\b|\byou\b|\.py:[0-9]|existing|earlier`. Four hits, all `discard`/`cardinality` substrings.
  No provenance.
- Citations: `check_citations.py --paths <f> --substrings --json` on all eight `.py` files: all
  resolve (4, 0, 26, 0, 5, 0, 4, 1). Outside `docs/review/`, `rg` finds no live prose that still
  describes value equality, snapshots or the guarded hash. The remaining hits are CHANGELOG
  (maintainer-owned), archived `docs/SPECS/spec-016`, `docs/builder/DONE/`, and
  `registry.py::TypeRegistry.discard_pending` (V2).

Attack, a caller Worker-2 did not name: the registry-side prose that describes records' equality
(`discard_pending` docstring, the identity test's docstring). I swapped `discard_pending` to
equality membership in my copy (`prove_eq_discard.json`, run `review-20260925T173151-17cfec`,
`expect_failing: []`). It passes all 102 rows in scope, so it changes nothing observable. That
makes the two sentences claiming identity is stronger than or distinct from `__eq__` false after
M1: V1, V2 (Medium, `verify 1`). The same manifest ran a second time (identical invocation,
extraction only). Both runs are in the evidence folder.

Cells: `sharded`, `pg` `inapplicable by construction` (prose; the target reaches no alias or
dialect decision).

Disputes: none on this axis.

Fingerprints (`git hash-object`): `types/relations.py` 5e9b5cdb..., `types/base.py` dda91365...,
`tests/types/test_relations.py` 2e18880a..., `tests/test_registry.py` 8b33f291...,
`tests/types/test_finalizer.py` ad82b908..., `tests/types/test_definition_order.py` aff87c52...,
`tests/types/test_relay_interfaces.py` 515ebce5..., `tests/utils/test_relations.py` e51cebaa...,
`docs/TREE.md` 5d562733... (all equal to Worker-2's after list); read unchanged
`django_strawberry_framework/registry.py` 9cc8bb553fd417fc465809a541769a8383469cda,
`django_strawberry_framework/types/finalizer.py` de34ae2aaed10fd664197cc2205c29e7d1927c2d,
`django_strawberry_framework/types/converters.py` 058f10813927c0691ba658d7d388820bd07cd52a,
`django_strawberry_framework/utils/relations.py` 8dbc3fe668dda7d57f1e2b2a3af66afdda449ded;
scratch `relations.code_only.py` 1a052c7e..., `test_registry.pass1.py` 8b33f291...,
`prove_eq_discard.json` a345e894....

Verdict: revision-needed. F1-F4 verified, F5 verified as discharged by M1, the four cross-axis
entries verified. Gaps: V1 (`tests/test_registry.py`, one sentence deleted) and V2
(`django_strawberry_framework/registry.py`, docstring rewrite; adds `registry.py` to the item
diff and the ledger). Both are prose-only, so the re-pass owes Comments alone, and each Proof
carries its own `--code-digest` identity.

Handoff: I read beyond the record the finalizer's Phase 1 loop and `resolved_pending`,
`converters.py::resolved_relation_annotation`, `registry.py::TypeRegistry.discard_pending`, and
the docstrings and comments of all 15 touched test functions via AST. Lead for Mechanics, not
this axis: after M1 the sanity line `assert record_a != record_b` in the registry identity test
pins `eq=False` a second time (`test_equal_valued_pending_relations_stay_distinct` already does),
and no test can see identity matching versus equality matching in `discard_pending`, because the
two no longer behave differently. That is not a defect. Leads outside this item, pre-existing and
not made false here: `test_non_relay_type_keeps_id_int` ("``0.0.4``-identical path",
provenance) and `test_extended_node_interface_subclass_suppresses_id_annotation` ("The bug
surfaces when ...", past narrative) in `tests/types/test_relay_interfaces.py`. For the re-pass:
V1's pre-image is `verify-comments-1/test_registry.pass1.py`. Keep the scratch until the item
closes.

## Verification (Comments) pass 2

Address `review/types/relations.py/verify-comments-2`. Prose-only re-pass; no command imported the
package or opened a database, so no run ids.

Diff binding: `git diff b43e2f2fb07e4c13ee93056c09a5a94ede07065f --` the ten item paths hashes
`d3d0702a...b6d36225`, equal to `docs/review/temp-tests/types__relations/diff/pass-2.diff`.

Proof lines, run verbatim before reading `## Iterations`:

- F1-F5 `rg -c` lines: exit 1 each, no output. Pass. F1 `--list-docstrings` on the target: `ok`,
  first line unchanged. Pass. F1/F2/F4 and F3/F5 `--code-digest` against `ITEM_BASELINE`: exit 1
  with `dec4dd9b`/`dfc00e12` and `946fdf82`/`ecd88d8b`, the same pairs pass 1 recorded and judged
  (M1/M2 code); both files hash to their pass-1 fingerprints (`5e9b5cdb`, `2e18880a`), so pass 1's
  substitute identity stands unchanged.
- V1 `rg -c "Pins the identity-based contract" tests/test_registry.py`: exit 1. Pass.
  `--code-digest verify-comments-1/test_registry.pass1.py tests/test_registry.py`: exit 0,
  `1cda0e26` both. Pass.
- V2 `rg -c "stronger contract" django_strawberry_framework/registry.py`: exit 1. Pass.
  `--code-digest b43e2f2f...:django_strawberry_framework/registry.py <same>`: exit 0, `ac9a0c24`
  both. Pass.
- Mechanics `## Cross-axis (for Comments)`, four entries: verified at pass 1; their files
  (`types/relations.py`, `tests/types/test_relations.py`, `tests/utils/test_relations.py`) are
  byte-unchanged since, and their prose diffs are identical to pass 1's (`cmp`). Stand.

Whole-diff reading. Prose diff from the REVIEW.md "Comments" command, nine `--path`s (TREE.md is
not Python), output `verify-comments-2/diff/`. Seven of nine `.prose.diff` files are
byte-identical to pass 1's; `tests__test_registry.prose.diff` differs only by the V1 hunk;
`django_strawberry_framework__registry.prose.diff` is new and holds the one V2 hunk, and its
stripped-code `registry.diff` is empty.

- V2, `django_strawberry_framework/registry.py::TypeRegistry.discard_pending`, whole docstring:
  true. The body builds an `id()` set and filters by it; every record in the finalizer's
  `resolved_pending` (`consumer_authored` plus resolved) comes from `iter_pending_relations`; no
  `==` or `hash` on a record. The false comparison is gone, and the reason that remains is the
  true one. First line unchanged. Verified.
- V1, `tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation`,
  whole docstring: true. It states what the body does (two records from one kwargs dict, discard
  one, the other remains, `is record_b`), and no longer claims to pin identity against equality.
  The sanity comment and "Registry lifecycle" paragraph are pass-1 text, graded true then.
  Verified.
- Touched-symbol sweep: `registry.py` module docstring (names `discard_pending` as a finalize-loop
  call only), `iter_pending_relations` docstring, and `rg -i "equal|__eq__|hashab"` over
  `registry.py`, `tests/test_registry.py`, `types/finalizer.py`: no remaining prose sets identity
  against record equality. The two `finalizer.py` "strict-equality" hits are the filterset owner
  check, not records.
- Provenance / `we` / line numbers: the two new hunks carry none.

Record checks: `check_citations.py --paths` on this record: 32 checked, 4 unresolved, all in the
review pass's F5 and `## Rejected` text (`_hash_component`, `PendingRelation.__hash__` and two
deleted tests), which describe the `ITEM_BASELINE` tree; M1 deleted those symbols on purpose, and
nothing from that text lands in code or a standing doc. Left as written. `docs/TREE.md` unchanged since
pass 1 (`5d562733`), and neither pass-2 edit touches a module first line.

Cells: `sharded`, `pg` `inapplicable by construction` (prose only).

Disputes: none.

Fingerprints (`git hash-object`): `django_strawberry_framework/registry.py`
81bd561c99cb364cb2bd90b10b67c719a42c5d47; `tests/test_registry.py`
48af782ff707baaf1619da26d2e286d2ba5178f4 (both equal to Worker-2's pass-2 after list); the other
eight item paths equal their pass-1 fingerprints; read unchanged
`django_strawberry_framework/types/finalizer.py` de34ae2aaed10fd664197cc2205c29e7d1927c2d.

Verdict: verified. F1-F4 verified (pass 1), F5 discharged by M1 (pass 1), V1 and V2 verified, the
four cross-axis entries stand.

Handoff: read beyond the record only the finalizer's `consumer_authored` / `resolved_pending`
construction and the `registry.py` module docstring. Open leads carried from pass 1, unchanged
and outside this axis: the redundant `assert record_a != record_b` (Mechanics, graded not a
defect) and the two `tests/types/test_relay_interfaces.py` provenance docstrings (outside the
item). Scratch: `docs/review/temp-tests/types__relations/verify-comments-2/diff/`.
