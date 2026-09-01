# Build: R1b — conformance audit: the `DjangoMutation` base, `Meta` validation, finalizer binding

Spec reference: `docs/SPECS/spec-036-mutations-0_0_11.md` — Slice 2 of `## Slice checklist`; Decisions 3, 4, 11, 12; `## Definition of done` item 3; the `## Edge cases and constraints` bullets on `finalize_django_types()` ordering, "No `DjangoType` `Meta` key added", "A mutation field with no `Mutation` type wired", and "Two mutations over one model share input types".
Rationale companion: `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md` — Decisions 3, 4, 5, 11, 12 read in full.
Build plan: `docs/builder/build-036-mutations-0_0_11.md`
Status: final-accepted

## Method

**Every grade below measures `HEAD` = `7426e7e7d8aa447e89fee75088447d6a506dec12`,** read from the read-only snapshot at
`/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4a12072-1e3a-4913-8249-dd800f1972ce/scratchpad/head-036/`
(abbreviated `<HEAD>` in citations below). Snapshot fidelity proved for both dirty territory files:

```shell
git show HEAD:django_strawberry_framework/mutations/sets.py | cmp - <HEAD>/django_strawberry_framework/mutations/sets.py   # exit 0
git show HEAD:django_strawberry_framework/types/finalizer.py | cmp - <HEAD>/django_strawberry_framework/types/finalizer.py # exit 0
```

No `git stash` / `git checkout` / `git restore` / `git worktree` was used anywhere in this pass.

**No test was run.** A run would exercise the dirty tree and so could not verify a `HEAD` claim; nothing in this pass rests on a run.

**No failability mutation was performed.** Both mutating candidates — `mutations/sets.py` (`+96` lines dirty) and `types/finalizer.py` (`+32` lines dirty) — are on the plan's `### Baseline-dirty out-of-scope files` never-edit / never-revert list, and the concurrent session is actively landing a `0.0.15` authorization-hardening seal inside the exact metaclass I would have had to mutate. Per the task's own carve-out proviso I judged the mutation too risky and skipped it rather than performing it carelessly. Where a boundary's pinning is in question I established it by reading plus a mechanical grep of the harness's own fixture vocabulary (see Medium-1), which is the instrument `docs/builder/worker-3.md` `### Suspect the fixture before accepting "untestable"` prescribes.

**Live-tree comparison (context only, never a grade).** `git diff --stat HEAD --` over the whole territory:

```
django_strawberry_framework/mutations/sets.py  | 96 +++++++++++++++---
django_strawberry_framework/types/finalizer.py | 32 ++++++---
tests/mutations/test_sets.py                   | 16 ++---
tests/types/test_finalizer.py                  | 31 +++++++
```

`mutations/operations.py`, `types/base.py`, `registry.py`, `tests/mutations/test_operations.py`, `tests/test_registry.py` are clean at `HEAD`. The concurrent session's `sets.py` work is a `0.0.15` authorization-hardening seal — `_mutation_meta` becomes write-once via metaclass `__setattr__` / `__delattr__`, `_ValidatedMutationMeta` gains `_sealed`, and `permission_classes` normalizes to an immutable `tuple` instead of a `list`. Its `finalizer.py` work is sidecar-set owner-binding hardening (a non-class `Meta.model` no longer leaks `issubclass`'s raw `TypeError`) and does not touch the mutation bind. **Neither changes any grade below**, but it does mean one HEAD detail I grade — the `list`-typed normalized `permission_classes` — is being re-typed in flight; R2 should not write "list" into the spec.

**Anchor discipline.** Every spec phrase quoted in `### Notes for Worker 1` is quoted **as of `HEAD`, pre-R2-edit**, and several are the exact phrases R2 will rewrite. They are cited with a stable neighbourhood (the owning Decision / DoD item / edge-case bullet heading) so the citation survives the fix.

---

## Review (Worker 3)

### Graded contract inventory

64 rows. `path #"substring"` / `path::QualifiedName` citations per `AGENTS.md` rule 27; no `path:NN` in this table.

#### A. Slice 2 of `## Slice checklist`

| # | Contract (spec) | Grade | `HEAD` evidence |
|---|---|---|---|
| A1 | `mutations/sets.py` ships `DjangoMutation` + its metaclass | CONFORMS | `django_strawberry_framework/mutations/sets.py::DjangoMutation`; metaclass at `mutations/sets.py #"DjangoMutationMetaclass = make_meta_validating_metaclass("` |
| A2 | `Meta` collects `model` | CONFORMS | `mutations/sets.py::DjangoMutation._resolve_model` |
| A3 | `Meta` collects `operation` | CONFORMS | `mutations/sets.py::DjangoMutation._validate_meta #"operation = getattr(meta, \"operation\", None)"` |
| A4 | `Meta` optionally collects `input_class` / `partial_input_class` / `fields` / `exclude` / `permission_classes` | CONFORMS | all five are slots on `mutations/sets.py::_ValidatedMutationMeta` and validated in `_validate_meta` |
| A5 | The accepted `Meta` key set is exactly those seven keys | **SUPERSEDED** | `mutations/sets.py #"_ALLOWED_MUTATION_META_KEYS: frozenset[str] = MODEL_BACKED_WRITE_META_KEYS"` composes to **8** keys; the extra is `select_for_update`. See Notes N1. |
| A6 | Unknown `Meta` key -> `ConfigurationError` at class creation | CONFORMS | `mutations/sets.py::reject_unknown_meta_keys`; pinned `tests/mutations/test_sets.py::test_meta_unknown_key_raises` |
| A7 | No resolvable model (in `0.0.11` a missing `Meta.model`) -> `ConfigurationError`, via the overridable `_resolve_model` seam | CONFORMS | `mutations/sets.py::DjangoMutation._validate_meta #"declares no resolvable model; set Meta.model."`; pinned `tests/mutations/test_sets.py::test_meta_without_model_raises` |
| A8 | The `_resolve_model` seam exists **and is actually overridden by the `038` / `039` flavors** (Medium-5's whole point) | CONFORMS | `django_strawberry_framework/forms/sets.py::DjangoModelFormMutation._resolve_model` (`Meta.form_class._meta.model`) and `django_strawberry_framework/rest_framework/sets.py::SerializerMutation._resolve_model` (`Meta.serializer_class.Meta.model`), both via `mutations/sets.py::resolve_meta_model`; pinned `tests/mutations/test_sets.py::test_resolve_model_seam_lets_subclass_supply_model_without_meta_model` |
| A9 | `operation` not in `{"create", "update", "delete"}` -> `ConfigurationError` | **RENAMED** | The rejection holds (`mutations/sets.py::DjangoMutation._validate_meta #"Meta.operation must be one of"`), but the vocabulary the spec inlines now lives at `django_strawberry_framework/mutations/operations.py #"_VALID_OPERATIONS: frozenset[str] = frozenset("`, derived from `MutationOperationDescriptor.supports_model_mutation`. See Notes N2. |
| A10 | `input_class` that is not a `@strawberry.input`-decorated type -> `ConfigurationError` | CONFORMS | `mutations/sets.py::_validate_input_class #"must be a "`; pinned `tests/mutations/test_sets.py::test_meta_input_class_not_strawberry_input_raises` |
| A11 | A custom `input_class` whose field names diverge from the generated scheme (AR-M2) -> `ConfigurationError` | CONFORMS | `mutations/sets.py::_validate_input_class` + `mutations/sets.py::_expected_input_attr_names` (single-sourced with the generator through `editable_input_fields` + `relation_input_annotation`); pinned `tests/mutations/test_sets.py::test_meta_input_class_diverging_field_names_raises` and `::test_meta_input_class_following_scheme_validates_clean` |
| A12 | `permission_classes` defaults to `[DjangoModelPermission]` | CONFORMS | `mutations/sets.py::_validate_permission_classes #"unset_default: tuple[Any, ...] = (DjangoModelPermission,)"` reached via `mutations/sets.py::model_backed_permission_and_lock`; pinned `tests/mutations/test_sets.py::test_permission_classes_defaults_to_django_model_permission` |
| A13 | Register the mutation | CONFORMS | `mutations/sets.py::make_declaration_registry` + `mutations/sets.py #"register_mutation = _mutation_declaration_registry.register"`; pinned `tests/mutations/test_sets.py::test_concrete_mutation_registers_abstract_base_does_not`, `::test_registration_is_idempotent` |
| A14 | Bind it at `finalize_django_types` phase 2.5 | CONFORMS | `django_strawberry_framework/types/finalizer.py::finalize_django_types #"bind_mutations()"`, inside the phase-2.5 window |
| A15 | The bind resolves the model's primary type | CONFORMS | `mutations/sets.py::bind_mutations` -> `mutations/sets.py::_resolve_primary_type` |
| A16 | The bind materializes the generated input / payload classes before `strawberry.Schema(...)` | CONFORMS | `mutations/sets.py::bind_write_declarations` + `mutations/sets.py::bind_mutation_outputs`; pinned `tests/mutations/test_sets.py::test_bind_materializes_input_and_payload_globals` (asserts the `_materialized_names` ledger, not `hasattr`) |
| A17 | Duplicate generated name -> `ConfigurationError` (AR-M6) | CONFORMS | raised at `materialize_mutation_input_class`; pinned `tests/mutations/test_sets.py::test_bind_duplicate_payload_name_distinct_shapes_raises` and `::test_bind_merged_and_generated_same_shape_distinct_representations_raise` |
| A18 | No change to `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS`; a mutation `Meta` is its own validation namespace | CONFORMS | `mutations/sets.py` imports nothing from `types/base.py`; the sets across the `036` build are byte-identical (see Notes N7 for the measurement) |
| A19 | Package coverage in `tests/mutations/test_sets.py` — `Meta` validation matrix, registration, finalizer binding, the no-registered-primary-type error | CONFORMS | all four present; `tests/mutations/test_sets.py` is 2,135 lines / 83 test functions at `HEAD` (`grep -c '^def test\|^async def test'`) |

#### B. Decision 3 — `class Meta` surface, not decorators

| # | Contract | Grade | `HEAD` evidence |
|---|---|---|---|
| B1 | A `DjangoMutation` is a base class with a nested `class Meta`, declared like every other consumer surface | CONFORMS | `mutations/sets.py::DjangoMutation` |
| B2 | It is **not** a Strawberry / strawberry-django decorator or field verb | CONFORMS | no `create()` / `update()` / `delete()` field-verb factory and no consumer-facing decorator exists in `mutations/`; the field factory is the class-attribute `DjangoMutationField(CreateItem)` form |

#### C. Decision 4 — Module and test locations

| # | Contract | Grade | `HEAD` evidence |
|---|---|---|---|
| C1 | Source lives at `django_strawberry_framework/mutations/` | CONFORMS | directory exists, 7 `.py` files |
| C2 | The subpackage is "split four ways" into `inputs.py` / `sets.py` / `resolvers.py` / `fields.py` | **STALE-DESCRIPTION** | `mutations/permissions.py` was added by the `036` build itself (commit `4b26b94e` "Finish docs/spec-036-mutations-0_0_11.md", 2026-06-18) and the spec's own `## Implementation plan` Slice-2 row names it `(new)`. Decision 4's enumeration is therefore incomplete about `036`'s own deliverables. See Notes N3. |
| C3 | ...and nothing has been added to that split since | **SUPERSEDED** | `mutations/operations.py` added by commit `7ff97021` "refactor(mutations): introduce canonical mutation operation descriptors" (2026-08-24, `__version__ = "0.0.14"`). See Notes N3. |
| C4 | "It reuses `sets_mixins.py` where the lifecycle machinery is genuinely shared" | **STALE-DESCRIPTION** | **0** occurrences of `sets_mixins` anywhere under `django_strawberry_framework/mutations/` at `HEAD`. The shared write-flavor lifecycle machinery does exist and lives inside `mutations/sets.py` itself (`::make_declaration_registry`, `::make_meta_validating_metaclass`) plus `utils/inputs.py` (`make_shape_build_cache`). See Notes N4 and DRY-1. |
| C5 | Tests live at `tests/mutations/` | CONFORMS | directory exists |
| C6 | The test-module set is `test_inputs.py` / `test_sets.py` / `test_resolvers.py` / `test_fields.py` "per the one-to-one rule" | **STALE-DESCRIPTION** | `tests/mutations/test_permissions.py` was added by the same `036` commit `4b26b94e`, and the spec's Slice-3 checklist and Implementation plan both name it. Decision 4's list omits it. |
| C7 | ...and nothing has been added since | **SUPERSEDED** | `tests/mutations/test_operations.py` (commit `f233cdb7`, 2026-08-25, `0.0.14`) and `tests/mutations/test_write_transaction.py` (the `0.0.14` write-transaction hardening). 7 `test_*.py` modules at `HEAD` against the 4 enumerated. |
| C8 | "composition pins that belong to other surfaces extend those surfaces' files ... `tests/test_permissions.py` for the lookup-scoping pin" | **RENAMED** | `tests/test_permissions.py` at `HEAD` carries **no** such pin — only a live `# TODO(spec-036 Slice 3)` anchor plus its `Pseudocode:` block. The behavior IS pinned, at `tests/mutations/test_resolvers.py::test_hidden_row_update_is_not_found_no_existence_leak` and `tests/mutations/test_permissions.py::test_hidden_row_is_not_found_before_auth_signal_no_existence_leak`. Not SKIPPED — the contract landed at a different path. See Notes N5 and High-1. |
| C9 | "`tests/optimizer/test_walker.py` for the G2 plan-shape" pin | CONFORMS | `tests/optimizer/test_walker.py` carries 22 `mutation` occurrences at `HEAD`. Content graded by R1d (Decision 9 / AR-M7); only the *location* claim is graded here. |

#### D. Decision 5 — the clauses this cohort owns (`Meta` validation, the `_resolve_model` seam, the internal symbol-count contradiction)

| # | Contract | Grade | `HEAD` evidence |
|---|---|---|---|
| D1 | The operation is selected by `Meta.operation` (a single string key), not a separate base class per operation | CONFORMS | one `DjangoMutation` base; `_VALID_OPERATIONS` selects |
| D2 | Write authorization is `Meta.permission_classes` (default `[DjangoModelPermission]`) plus an overridable `check_permission(self, info, operation, data, instance=None)` | CONFORMS | `mutations/sets.py::DjangoMutation.check_permission` — signature matches the spec character for character |
| D3 | It is the mutation's own `Meta` / method namespace, not a `DjangoType` `Meta` key | CONFORMS | pinned `tests/mutations/test_sets.py::test_mutation_meta_key_rejected_on_django_type_meta` |
| D4 | Model resolution raises `ConfigurationError` only when **no** model can be resolved, through `_resolve_model(meta)` | CONFORMS | `mutations/sets.py::DjangoMutation._validate_meta`; the base does not require the literal attribute |
| D5 | Decision 5's own justification: "keeps the public symbol count at three" vs the Decision body's and DoD item 8's four | **STALE-DESCRIPTION** | `django_strawberry_framework/__init__.py.__all__` at `HEAD` carries **all four** (`DjangoModelPermission`, `DjangoMutation`, `DjangoMutationField`, `FieldError`) of 37 entries — so the body is right and the justification's numeral is wrong. The justification now lives in the rationale companion, which **already self-documents the defect** under Decision 5 `### Changes this Decision underwent`. See Notes N6. |

#### E. Decision 11 — primary-type resolution

| # | Contract | Grade | `HEAD` evidence |
|---|---|---|---|
| E1 | The return-payload object type resolves the model's **primary** `DjangoType` | CONFORMS | `mutations/sets.py::_resolve_primary_type` -> `bind_mutation_outputs(object_type=...)` |
| E2 | ...through `registry.py::TypeRegistry.get(model)` / `primary_for(model)` | **STALE-DESCRIPTION** | `_resolve_primary_type` calls `registry.get(model)` and, for the message split only, `registry.types_for(model)`. It **never** calls `registry.primary_for`. See Notes N8. |
| E3 | The primary type also fixes the relation-id strategy (`GlobalID` vs raw pk, and which type a relation `GlobalID` is type-checked against, AR-H4) | CONFORMS | `mutations/sets.py::_validate_relation_override_types #"related_primary_type=registry.get(field.related_model),"` -> `mutations/inputs.py::relation_id_scalar` gating on `implements_relay_node` |
| E4 | The primary type is **not** the source of the generated input field set (Low-1) | CONFORMS | the field set comes from `mutations/inputs.py::editable_input_fields`; `primary_type` is threaded only into the relation-id annotation |
| E5 | Multiple registered types and no declared primary -> `ConfigurationError` at finalization | CONFORMS | `mutations/sets.py::_resolve_primary_type #"multiple registered DjangoTypes and no declared primary"`; pinned `tests/mutations/test_sets.py::test_bind_resolve_primary_distinguishes_ambiguous_from_zero_type` |
| E6 | No registered type at all -> a finalize-time "no type to return" error (loud, at finalization, not at request time) | CONFORMS | `mutations/sets.py::_resolve_primary_type #"the mutation has no type to return."`; pinned `tests/mutations/test_sets.py::test_bind_no_registered_type_raises_no_type_to_return` |

#### F. Decision 12 — the finalization seam

| # | Contract | Grade | `HEAD` evidence |
|---|---|---|---|
| F1 | A subclass registers itself at class creation (its metaclass records the `Meta`) | CONFORMS | `mutations/sets.py::make_meta_validating_metaclass #"new_class._mutation_meta = new_class._validate_meta(meta)"` then `register(new_class)` |
| F2 | It binds at `finalize_django_types` **phase 2.5** | CONFORMS | `types/finalizer.py::finalize_django_types #"bind_mutations()"`; the module docstring's phase-2.5 description and `sets.py`'s own `bind_mutations` docstring agree. "Phase 2.5" is a real, findable phase, not a spec fiction. |
| F3 | ...the same seam that binds `FilterSet` / `OrderSet` sidecars | CONFORMS | `bind_mutations()` sits immediately before `_bind_filtersets()` / `_bind_ordersets()` in the same window. `mutations/sets.py`'s module docstring records the deliberate divergence: the bind iterates the *mutation-declaration registry*, not `registry.iter_definitions()`, so it is a placement sibling of `_bind_filtersets`, not a `_bind_sidecar_sets` consumer. |
| F4 | Binding resolves the model's primary type | CONFORMS | as E1 |
| F5 | Binding generates / materializes `Input` / `PartialInput` / `<Name>Payload` as module globals of `mutations/inputs.py` | CONFORMS | `mutations/sets.py::_materialize_input_for` + `::bind_mutation_outputs`, both through `materialize_mutation_input_class`; `mutations/sets.py #"input_module_path: str = INPUTS_MODULE_PATH"` |
| F6 | Binding validates the resolved target | CONFORMS | `_resolve_primary_type` + `_validate_relation_override_types` |
| F7 | ...all before `strawberry.Schema(...)` runs | CONFORMS | phase 2.5 precedes Phase 3's `strawberry.type(...)`, which itself precedes any `Schema(...)`; pinned by the ledger assertion in `test_bind_materializes_input_and_payload_globals` |
| F8 | No change to `DEFERRED_META_KEYS` or `ALLOWED_META_KEYS` | CONFORMS | see Notes N7 for the falsifiable measurement across the `036` build |

#### G. `## Definition of done` item 3

| # | Contract | Grade | `HEAD` evidence |
|---|---|---|---|
| G1 | `mutations/sets.py` ships `DjangoMutation` + its metaclass with the full `Meta` validation matrix | CONFORMS | rows A6–A11 |
| G2 | `Meta.permission_classes` defaults to `[DjangoModelPermission]` **and an invalid entry is rejected** (AR-H3) | CONFORMS | `mutations/sets.py::_validate_permission_classes` rejects a bare `str`/`bytes`/class, a non-iterable, an instance entry, and a class without a callable `has_permission`; five pinning rows (`test_permission_classes_bare_class_raises`, `::_bare_string_raises`, `::_instance_entry_raises`, `::_entry_without_has_permission_raises`, `::test_meta_permission_classes_non_iterable_raises`) |
| G3 | "**registration** and phase-2.5 binding land in `types/finalizer.py`" | **STALE-DESCRIPTION** | Registration lands in `mutations/sets.py`'s metaclass at class creation; only the *bind* lands in `types/finalizer.py`. Decision 12 states the split correctly, so DoD item 3 contradicts its own Decision. See Notes N9. |
| G4 | A model with no registered primary type fails loudly at finalization | CONFORMS | as E6 |
| G5 | Two distinct shapes colliding on one generated name (AR-M6) fails loudly at finalization | CONFORMS | as A17 |
| G6 | `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` are unchanged | CONFORMS | as F8 / Notes N7 |

#### H. `## Edge cases and constraints`

| # | Contract | Grade | `HEAD` evidence |
|---|---|---|---|
| H1 | `finalize_django_types()` ordering: mutation binding runs in phase 2.5 **after** all `DjangoType`s are registered and their relations resolved, so the primary-type lookup and relation-id shaping see a fully-resolved registry | CONFORMS | `bind_mutations()` runs after Phase 1's `registry.discard_pending(resolved_pending)`, after Phase 2's resolver attach, and after the phase-2.5 `apply_interfaces` / `install_relay_node_resolvers` / `_synthesize_relation_connections` / `_audit_model_label_routing` steps. The ordering is load-bearing, not decorative: `mutations/inputs.py::relation_id_scalar` gates `relay.GlobalID` on `implements_relay_node(related_primary_type)`, which reads an MRO that `apply_interfaces` mutates. Pinned — but only at the live tier; see Medium-1. |
| H2 | Declaring a mutation after finalization raises `ConfigurationError` (same as declaring a `DjangoType` late) | CONFORMS | `mutations/sets.py::make_declaration_registry #"after finalization; "`; pinned `tests/mutations/test_sets.py::test_late_declaration_after_finalize_raises` and `::test_make_declaration_registry_dedupes_and_rejects_post_finalize` |
| H3 | "No `DjangoType` `Meta` key added. `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` **are byte-unchanged**" | **STALE-DESCRIPTION** | True of the `036` build; **false as a present-tense statement about `HEAD`.** `ALLOWED_META_KEYS` has since gained `cursor_field` (commit `51421e54`, keyset value-encoded cursors / BACKLOG-39) and `filesystem_path_fields` (commit `567cc6d0`, the security program / `0.0.14`). `DEFERRED_META_KEYS` is genuinely byte-unchanged. See Notes N7. |
| H4 | The `Meta` validation matrix lives on the mutation metaclass, isolated from `DjangoType.__init_subclass__` | CONFORMS | `mutations/sets.py` imports nothing from `types/base.py`; `registry.py` carries no mutation-specific key (its only coupling is the generic `register_subsystem_clear` / `iter_subsystem_clears` hook, which the mutation subsystem registers into twice: `owner="mutations.shape_cache"` and `owner="mutations.declarations"`) |
| H5 | A `DjangoMutation` declared but never exposed via `DjangoMutationField` is inert (registered, never resolved) | CONFORMS | no resolution path exists without a field; `mutations/sets.py`'s module docstring states it as a contract. Pinned incidentally but broadly — every bind test in `tests/mutations/test_sets.py` declares mutations with no field and finalizes successfully. |
| H6 | A `DjangoMutationField` on a model with no registered primary type fails at finalization, not at request time | CONFORMS | the raise is inside the bind (`_resolve_primary_type`), which runs whether or not a field exists, so the field-present variant cannot diverge; pinned by `test_bind_no_registered_type_raises_no_type_to_return` |
| H7 | `CreateItem` / `UpdateItem` over one model resolve to the canonical `ItemInput` / `ItemPartialInput` module globals for the canonical full shape | CONFORMS | pinned `tests/mutations/test_sets.py::test_bind_dedupes_identical_full_shapes` (two creates share one `ItemInput`) and `::test_bind_dedupes_full_set_fields_with_bare_create`. Wording note in Low-2: the dedupe key is `(model, operation kind, frozenset(effective names))`, so a create and an update never share **one** class — they share the canonical naming. |
| H8 | Two mutations that narrow to *different* shapes get distinct shape-derived names | CONFORMS | `mutations/sets.py::_materialize_input_for` via `mutation_input_shape(...).type_name`; pinned `::test_bind_dedupes_fields_with_complementary_exclude` (which also proves the key is the *effective* set, not the `(fields, exclude)` spelling) |
| H9 | A name clash between distinct shapes is a finalize-time `ConfigurationError` (AR-H1 / AR-M6) | CONFORMS | as A17 |

### Summary counts (re-derived from the tables above, not asserted)

| | rows |
|---|---|
| **Total rows** | **64** |
| CONFORMS | 52 |
| SUPERSEDED | 3 |
| STALE-DESCRIPTION | 7 |
| RENAMED | 2 |
| **SKIPPED** | **0** |

Derivation, section by section (CONFORMS / SUPERSEDED / STALE / RENAMED / SKIPPED):
A 19 rows = 17/1/0/1/0 · B 2 = 2/0/0/0/0 · C 9 = 3/2/3/1/0 · D 5 = 4/0/1/0/0 · E 6 = 5/0/1/0/0 · F 8 = 8/0/0/0/0 · G 6 = 5/0/1/0/0 · H 9 = 8/0/1/0/0.
Column sums: 17+2+3+4+5+8+5+8 = **52**; 1+2 = **3**; 3+1+1+1+1 = **7**; 1+1 = **2**; **0**. Row sum 19+2+9+5+6+8+6+9 = **64** = 52+3+7+2+0.

**No SKIPPED row.** Every contract Slice 2, Decisions 3/4/11/12, DoD item 3 and the four edge-case bullets state is implemented at `HEAD`. The four surfaces I expected a gap on and did not find one, each with where I looked:

- **The `_resolve_model` forward-compat seam** (Medium-5). Could plausibly have been collapsed once `038`/`039` shipped. Grepped `_resolve_model` across the whole package: 26 occurrences, with genuine classmethod overrides in `forms/sets.py` and `rest_framework/sets.py`. Present and load-bearing.
- **The custom-`input_class` naming-scheme check** (AR-M2). Grepped for a `pass` / `TODO` stub in `_validate_input_class`: none; the expected-name set is derived from the generator's own two functions.
- **The duplicate-generated-name `ConfigurationError`** (AR-M6). Two distinct pinning rows, on two distinct collision shapes (merged-vs-generated, and distinct-shapes-same-payload-name).
- **`Meta.permission_classes` invalid-entry rejection** (AR-H3). Five rejection branches, five pinning rows.

### High:

#### High-1: two undischarged `TODO(spec-036 Slice N)` anchors survive in shipped test source at `HEAD`

`AGENTS.md` ("the staged anchor is removed in the change that ships the slice") and `docs/builder/BUILD.md` `## Cross-slice integration pass` step 6 both make a `TODO(spec-036 …)` still present in shipped source after the card is Done an obligation the build owes. The card is `DONE-036-0.0.11`; two anchors remain.

Measurement (occurrences, not matching lines, on the shortest distinctive token):

```shell
grep -rIo 'TODO(spec-036' <HEAD> --include='*.py' | wc -l      # 2
grep -rIn 'TODO(spec-036' <HEAD> --include='*.py'
#   tests/test_permissions.py:43:  # TODO(spec-036 Slice 3): add the package-level permission pin for mutation
#   tests/mutations/__init__.py:3: # TODO(spec-036 Slice 1): keep mutation package tests in this mirror package.
```

1. `tests/test_permissions.py #"TODO(spec-036 Slice 3)"` — "add the package-level permission pin for mutation update/delete lookups", with a five-line `Pseudocode:` block. **The work landed, elsewhere** (`tests/mutations/test_resolvers.py::test_hidden_row_update_is_not_found_no_existence_leak`, `tests/mutations/test_permissions.py::test_hidden_row_is_not_found_before_auth_signal_no_existence_leak`), so this is a stranded anchor, not unbuilt work — which is why row C8 is RENAMED and not SKIPPED. Discharge = delete the anchor and its `Pseudocode:` block (or replace with non-`TODO` provenance pointing at the two landed rows).
2. `tests/mutations/__init__.py #"TODO(spec-036 Slice 1)"` — "keep mutation package tests in this mirror package". This is a *convention note* wearing the staged-work grammar; the mirror package exists and holds 7 test modules. Discharge = rewrite as plain provenance prose in the module docstring, or delete.

**Severity.** High because an anchor that names a shipped card is a false staging claim in shipped source: a future reader (or the integration-pass sweep) reads `TODO(spec-036 Slice 3)` as "Slice 3 never shipped this", and the second one will keep re-surfacing in every `TODO(spec-` sweep this repo runs.

**Scope note.** Neither file is in any R1 cohort's declared list (R1c owns `tests/mutations/test_permissions.py`, not `tests/test_permissions.py`; `tests/mutations/__init__.py` is nobody's). Both are `.py` test files and so inside this cycle's maintainer-set scope. Routed to R3 in Notes N5. **Neither is on the plan's baseline-dirty list** — `git status --short` reports both clean at `HEAD` — so a repair here would not collide with the concurrent session.

### Medium:

#### Medium-1: the package mutation suite is structurally blind to a phase-2.5 ordering regression (H1)

The ordering contract in H1 is load-bearing through exactly one mechanism: `mutations/inputs.py::relation_id_scalar` returns `relay.GlobalID` only when `implements_relay_node(related_primary_type)` is true, and for a type that declares Relay-ness through `Meta.interfaces = (relay.Node,)` that predicate becomes true only after `types/finalizer.py::finalize_django_types` calls `apply_interfaces`, in the same phase-2.5 window and *before* `bind_mutations()`. Hoist `bind_mutations()` above that loop and every `Meta.interfaces`-declared relation target silently degrades from `GlobalID` to a raw pk input — a wire-contract change and, because `utils/write_values.py::decode_visible_relation_ids` only visibility-checks the `GlobalID` shape, a relation-visibility bypass.

The package suite cannot see it. Measurement:

```shell
grep -rIo 'interfaces' <HEAD>/tests/mutations/*.py | wc -l   # 0
grep -rIo 'relay\.Node'  <HEAD>/tests/mutations/*.py | wc -l # 72
```

Zero occurrences of `interfaces` across all 7 `tests/mutations/` modules; all 72 Relay-target declarations use direct `class X(DjangoType, strawberry.relay.Node)` inheritance, for which `implements_relay_node` is true from class creation and the ordering is irrelevant. This is the `### Suspect the fixture before accepting "untestable"` case: an area where nothing can fail, and the finding is about the fixture.

It is **not unpinned overall** — the live tier catches it, because all four `examples/fakeshop/apps/products/schema.py` types declare `interfaces = (relay.Node,)` while products is also the live mutation surface, so a hoist would break the live `GlobalID` rows. So this is Medium, not High. But the spec's own `## Test plan` ownership split (AR-M7) assigns "Relay-vs-non-Relay id type" to the **package** tier, and the package tier tests only the ordering-insensitive spelling.

**Recommended change:** one row in `tests/mutations/test_sets.py` (or `test_inputs.py`) whose relation target declares `class Meta: interfaces = (relay.Node,)` instead of inheriting `relay.Node`, asserting the generated `<field>_id` annotation is `relay.GlobalID`. That row fails if the bind is ever hoisted above `apply_interfaces`. I did **not** demonstrate this by mutation: `types/finalizer.py` is on the plan's never-edit/never-revert baseline-dirty list and the concurrent session is inside it.

#### Medium-2: `mutations/sets.py` has become the cross-flavor write substrate, and 6 of its helpers have no caller in their own subpackage

The spec describes `mutations/sets.py` as "`DjangoMutation` + metaclass + `Meta` validation + finalizer binding". At `HEAD` it is 1,606 lines and also the shared substrate three *other* subpackages build on. Measurement by AST over the importing modules:

```
forms/sets.py           23 symbols from ..mutations.sets  (3 private: _hook_overridden, _validate_permission_classes, _ValidatedMutationMeta)
rest_framework/sets.py  17 symbols from ..mutations.sets  (2 private: _ValidatedMutationMeta, _validate_permission_classes)
auth/mutations.py        4 symbols from ..mutations.sets  (1 private: _validate_permission_classes)
=> 25 distinct symbols exported out of mutations/sets.py to non-mutations modules; 4 of them private-by-name.
```

And six of those module-level helpers have **zero** caller anywhere under `django_strawberry_framework/mutations/` — the definition is the only occurrence:

| helper | in-`mutations/` occurrences | real callers |
|---|---|---|
| `mutations/sets.py::_hook_overridden` | 1 (the `def`) | `forms/sets.py` only |
| `mutations/sets.py::construction_kwargs` | 1 | `forms/`, `rest_framework/` |
| `mutations/sets.py::cached_build_input` | 1 | `forms/`, `rest_framework/` |
| `mutations/sets.py::resolve_meta_model` | 1 | both flavors' `_resolve_model` overrides |
| `mutations/sets.py::resolve_backed_model_or_raise` | 1 | `forms/`, `rest_framework/` |
| `mutations/sets.py::require_non_delete_operation` | 1 | `forms/`, `rest_framework/` |

Re-derive with `grep -o "\b<name>\b" <HEAD>/django_strawberry_framework/mutations/*.py | wc -l`.

Two concrete consequences, both `BUILD.md`-Medium ("unclear ownership between modules"):

- Four private-by-name symbols cross subpackage boundaries. `_ValidatedMutationMeta` in particular is the *model* flavor's validated-snapshot record, and `rest_framework/sets.py` and `forms/sets.py` construct it directly — which is why its `__slots__` carries `form_class`, `serializer_class`, `optional_fields`, `schema_fingerprint`, `injected_fields`, `nested_fields`: six slots the model flavor never reads, living on the model flavor's record.
- `NON_DELETE_OPERATION_INPUT_KIND` is imported by `forms/sets.py` and `rest_framework/sets.py` **from `mutations.sets`**, while `mutations/sets.py` itself imports it from `mutations/operations.py`. `mutations/sets.py` is acting as a re-export hop past the constant's canonical home.

**Recommended change (mechanical, no behavior):** have `forms/` and `rest_framework/` import `NON_DELETE_OPERATION_INPUT_KIND` from `..mutations.operations` directly. The larger question — whether the flavor-neutral substrate should move to a neutral home at all — is an existence/placement challenge and not a worker's call; see DRY-1 and Notes N10.

### Low:

#### Low-1: repeated `Meta`-key and flavor-label literals in `mutations/sets.py`

From `scripts/review_inspect.py`'s **Repeated string literals** section for `mutations/sets.py` (run against the `HEAD` snapshot, output at `docs/shadow/django_strawberry_framework__mutations__sets.overview.md`):

```
17x `DjangoMutation`   5x `input_class`   5x `partial_input_class`   4x `operation`
 3x `permission_classes`   3x `select_for_update`   2x `is_relation`
```

- `"DjangoMutation"` 17x is the flavor label. Most helpers already thread it as `base_label=` / `flavor=`, but `DjangoMutation._validate_meta` hard-spells it at each raise site. A module-level `_FLAVOR_LABEL = "DjangoMutation"` would single-source it — with the caveat that the label is load-bearing in pinned error text (`mutations/sets.py::require_model_class`'s docstring says the message must stay byte-identical), so this is a rename-the-literal change, not a reword.
- `"input_class"` / `"partial_input_class"` 5x each is the more interesting one, because `mutations/operations.py::_OPERATION_INPUT_OVERRIDE_ATTR` already owns the operation-to-override-attribute mapping — yet `mutations/sets.py::_materialize_merged_input`'s call site re-spells it as `attr_name="input_class" if operation_kind == CREATE else "partial_input_class"`, keyed on the *operation kind* rather than the operation name. Two spellings of one mapping, differing only in their key. Fix: key `_OPERATION_INPUT_OVERRIDE_ATTR` by kind as well, or resolve the attr name from `meta.operation` at that site (which is in scope).

#### Low-2: the "two mutations share input types" edge case is ambiguous about *what* is shared

"`CreateItem` and `UpdateItem` resolve to the same materialized `ItemInput` / `ItemPartialInput` module globals when both take the canonical full shape" reads as though a create and an update share a class. They cannot: the shape key is `(model, operation kind, frozenset(effective names))`, so `CREATE` and `PARTIAL` are always distinct types. What `HEAD` actually guarantees, and what the tests pin, is that two mutations *of the same operation kind* over one model with one effective shape share one class object (`test_bind_dedupes_identical_full_shapes`). Graded CONFORMS because the "/" plausibly distributes across the two operations, but R2 should disambiguate. Suggested rewrite in Notes N11.

### DRY findings

- **DRY-1 (the existence / placement challenge, escalated).** `mutations/sets.py` at `HEAD` owns two responsibilities the spec names one of: the `DjangoMutation` model flavor, and the flavor-neutral write substrate that `forms/`, `rest_framework/`, and `auth/` are all built on (25 symbols out, 6 helpers with no in-subpackage caller — Medium-2). The package already has the exact precedent for the alternative: `sets_mixins.py` sits at the package root **specifically** so `filters/` and `orders/` import shared set machinery "from one neutral home rather than from each other" (its own module docstring). Decision 4 even predicted `mutations/` would reuse that home; instead the substrate accreted inside one flavor's module. What would break if the flavor-neutral block moved to a neutral module (`write_mixins.py` at the root, mirroring `sets_mixins.py`): nothing functionally — the moved symbols have no `mutations/`-local caller, and the change is import rewrites in three modules. What it buys: `forms/` and `rest_framework/` stop importing four private-by-name symbols out of a sibling flavor. **Not a worker's call** (`docs/builder/worker-3.md` `### The existence challenge`) — escalated in Notes N10, and this unit is not held at `revision-needed` on it.
- **DRY-2.** The `mutations/sets.py::validate_select_for_update` / `::_validate_permission_classes` / `::model_backed_permission_and_lock` trio is well factored: one validator per key, one pair helper, and the serializer flavor deliberately calls the two primitives in its own order rather than the pair. The pair helper's docstring states exactly why the serializer does not ride it. No finding — recorded because it is the shape the rest of this module should look like.
- **DRY-3 (pre-existing, not `036`'s).** `types/finalizer.py::finalize_django_types` spans **326 lines with 29 branch nodes** — the largest hotspot in the helper's output for that file, and phase 2.5 is an inline statement sequence rather than named phase functions. `036`'s contribution is 5 statements plus a ~30-line comment block (a comment-to-code ratio of roughly 6:1 at that site). Flagging the function, not the slice: the accretion is many cards' and extracting phase 2.5 into named steps is a plan-level call for a future spec. Recorded for the deferred-work catalog.
- **DRY-4.** `mutations/operations.py` is the right shape for what it does — one frozen dataclass, four module-level descriptors, and every derived collection (`NON_DELETE_OPERATION_INPUT_KIND`, `_OPERATION_INPUT_OVERRIDE_ATTR`, `NON_DELETE_WRITE_OPERATIONS`, `_VALID_OPERATIONS`, `_OPERATION_PERMISSION_ACTION`) built by comprehension over `_OPERATIONS_BY_NAME` rather than re-spelled. The single leak is the `_materialize_merged_input` re-spelling in Low-1. No consolidation finding.
- **Cross-cohort duplication review.** Not applicable in the usual sense: all four R1 cohorts are read-only and land no source, so there are no convergent added guards to compare. The one cross-cohort observation is recorded as Notes N12.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** (`git status --short` on that path is also empty), so `__all__` and the re-export list are unchanged by this pass — as required: R1b writes exactly one file, its own artifact.

Separately, as evidence for row D5, `__all__` at `HEAD` was read (not diffed): 37 entries, all four of `036`'s net-new symbols present. R1d owns the export pin itself (`tests/base/test_init.py`); this cohort used the reading only to settle Decision 5's internal contradiction.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (This cycle's maintainer-set scope excludes all of them.)

### Static helper use

`scripts/review_inspect.py` was **mandatory** for this cohort on two counts — `types/finalizer.py` is under `types/`, and `mutations/sets.py` is far past the 150-line threshold — and was run, against the `HEAD` snapshot rather than the dirty working file so its output matches the graded tree:

```shell
uv run python scripts/review_inspect.py <HEAD>/django_strawberry_framework/mutations/sets.py       --root <HEAD> --output-dir docs/shadow  # exit 0
uv run python scripts/review_inspect.py <HEAD>/django_strawberry_framework/mutations/operations.py --root <HEAD> --output-dir docs/shadow  # exit 0
uv run python scripts/review_inspect.py <HEAD>/django_strawberry_framework/types/finalizer.py      --root <HEAD> --output-dir docs/shadow  # exit 0
```

Outputs: `docs/shadow/django_strawberry_framework__mutations__{sets,operations}.overview.md`, `docs/shadow/django_strawberry_framework__types__finalizer.overview.md` (+ their `.stripped.py` siblings). Every line number cited in this artifact is an original-source symbol reference, never a shadow line.

Sections read, and what each yielded:

- **Repeated string literals** — `sets.py`: 8 entries, driving Low-1. `finalizer.py`: 15 entries, all sidecar-family / diagnostic vocabulary (`Cannot finalize` 8x, `FilterSet` 5x, `filterset_class` 3x), none from the mutation bind. `operations.py`: none.
- **Control-flow hotspots** — `sets.py`: 11, of which `DjangoMutation._validate_meta` (155 lines / 15 branches) and `_validate_relation_override_types` (83 / 9) are the two that matter. `_validate_meta` is a linear validation matrix with one raise per rule and no nesting, which is the readable shape for a matrix; I am not flagging it. `finalizer.py`: 16, driving DRY-3.
- **Imports** — `sets.py`'s 15 are all one-way (`..exceptions`, `..registry`, `..utils.*`, `.inputs`, `.operations`, `.permissions`); no sibling-subpackage import, so the *outbound* direction is clean and the boundary problem is entirely inbound (Medium-2). `finalizer.py` carries 36, of which 11 are function-local cycle guards including `from ..mutations.sets import bind_mutations` — deliberate and documented at the site.
- **Django / ORM markers** — `sets.py`: none. Nothing to justify.

Skips: none in this territory. `mutations/permissions.py`, `mutations/inputs.py`, `mutations/fields.py`, `mutations/resolvers.py` overviews were also present in `docs/shadow` from sibling cohorts' runs and were not re-generated by me — I read `permissions.py`'s source directly for rows A12 / G2 rather than relying on a shadow file another cohort produced.

### What looks solid

- **The `Meta` validation matrix is the strongest surface in the territory.** Eleven distinct rejection rules, every one raising `ConfigurationError` at class creation rather than deferring to bind or request time, and every one with at least one pinning row. Two go beyond the spec in the right direction: the non-model-`Meta.model` gate (`require_model_class`) that stops a raw `AttributeError` at bind, and the inapplicable-override gate (`input_class` on a non-create) that stops a valid-looking customization being silently discarded.
- **Hostile-input containment is systematic, and not spec-mandated.** **Ten** rows in `tests/mutations/test_sets.py` drive hostile `__repr__`, hostile metaclasses, non-string dict keys, non-class `Meta`, and unhashable `Meta.operation` values through the validators, confirming every diagnostic renders via `_safe_arg_repr` / `_safe_class_name` rather than letting a broken value replace the `ConfigurationError`. Re-derive with `grep -c '^def test.*hostile\|^def test.*unhashable\|^def test.*non_string\|^def test.*non_class'`. Nothing in `spec-036` asked for this.
- **The shape-identity key is right, and its tests prove the hard case.** Keying on the *effective* field set rather than the raw `(fields, exclude)` spelling is what makes `fields=("name",)` and the complementary `exclude=(...)` dedupe instead of colliding, and there is a row for exactly that (`test_bind_dedupes_fields_with_complementary_exclude`) plus one for a `fields` list naming the full editable set deduping with a bare create. Those are the two cases a naive declaration-keyed cache gets wrong.
- **`test_bind_materializes_input_and_payload_globals` asserts the right thing.** It checks the `_materialized_names` ledger rather than `hasattr(module, "ItemInput")`, and its docstring says why: materialized classes stay parked in `__dict__` across a `registry.clear()`, so a `hasattr` assertion would pass on a prior test's leftovers. That is a non-distinguishing assertion someone caught and fixed.
- **The retry-idempotency row is a real bug's regression test.** `test_bind_is_retry_idempotent_after_fixable_later_phase_failure` pins the documented recover-in-place path against a spurious distinct-class collision that used to mask the original error. The fix (resetting the materialization ledgers once in `finalize_django_types` before the bind sequence, not per-binder) is correctly placed — a per-pass clear inside either binder would wipe the sibling pass's entries, and the comment at the site says so.
- **`registry.py` carries no mutation-specific coupling.** The subsystem registers into the generic `register_subsystem_clear` hook twice, by owner name. The `Meta`-namespace isolation Decision 12 promises holds at the registry level too, not just at `types/base.py`.
- **`_resolve_model` earned its keep.** A forward-compat seam added speculatively in `0.0.11` for flavors that did not exist yet, and both flavors do override it, with the same shared `resolve_meta_model` chain. Medium-5 was a correct call.

### Temp test verification

No temp tests were created under `docs/builder/temp-tests/036/`. Every question this pass raised was settled by reading `HEAD` plus a mechanical grep of the harness's fixture vocabulary; the one question a temp test could have answered (Medium-1's ordering dependency) needs a `types/finalizer.py` mutation, which the baseline-dirty rule forbids. Disposition: none created, none to promote.

---

### Notes for Worker 1 (spec reconciliation)

Every SUPERSEDED / STALE-DESCRIPTION / RENAMED row from the inventory appears below with the **exact `HEAD` spec text** and what it should say. Quotes are pre-R2-edit by construction.

**N1 — row A5 · SUPERSEDED · Slice 2, first sub-bullet · `Meta` key enumeration grew by one**

Current text (Slice 2, first sub-bullet): *"collect `Meta` (`model`, `operation`, optional `input_class` / `partial_input_class` / `fields` / `exclude` / `permission_classes`)"*. Decision 5's body carries the same closed list (*"optional `input_class` / `partial_input_class` / `fields` / `exclude` / `permission_classes`"*).

At `HEAD` the accepted set is 8 keys, not 7. Re-derivation from `mutations/sets.py`'s own composition:

```
COMMON_WRITE_META_KEYS      = {fields, exclude, permission_classes}
MODEL_BACKED_WRITE_META_KEYS = COMMON | {operation, select_for_update}
_ALLOWED_MUTATION_META_KEYS  = MODEL_BACKED | {model, input_class, partial_input_class}   -> 8 keys
spec enumeration                                                                          -> 7 keys
HEAD minus spec = ['select_for_update'] ;  spec minus HEAD = []
```

`select_for_update` occurrences in the spec: **0**. In the rationale companion: **0**.

**Attribution.** It entered `mutations/sets.py` on 2026-07-01 (commit `951945b7`, `__version__ = "0.0.12"`) as a *serializer-flavor* key (the code comment there reads "the serializer-flavor `Meta.select_for_update` (spec-039 …)"), then was promoted to every model-backed flavor — `DjangoMutation` included — by commit `1b06c39e` "feat(mutations): span mutation transactions through response completion (BETA-055)" (2026-07-15, `__version__ = "0.0.13"`), which introduced `mutations/sets.py::validate_select_for_update`. That is the `0.0.14` write-transaction hardening the build plan names in its known-divergence list.

Should say: add `select_for_update` to both enumerations, with its contract as `HEAD` states it — a base-manager `SELECT ... FOR UPDATE` row lock on the update / delete locate and every relation-target check, constrained by the visibility pk subquery inside the write transaction; **default `True`**; an explicit `False` opts into weaker concurrency, surfacing as the in-band `conflict` envelope instead of waiting on the lock; a non-bool is a class-creation `ConfigurationError`; on a backend without `FOR UPDATE` (sqlite) Django skips the clause silently, so `True` is safe on any backend. Companion gets a `**Post-ship:**` bullet under Decision 5 (and cross-referenced from Decision 15, R1c's territory) naming `1b06c39e` / BETA-055.

Also note for R2's own bookkeeping: the enumeration is genuinely **closed** in code (`reject_unknown_meta_keys` over `_ALLOWED_MUTATION_META_KEYS`), so this one addition is the entire drift. There is no silently-grown tail.

**N2 — row A9 · RENAMED · Slice 2, first sub-bullet · the operation vocabulary moved**

Current text: *"`operation` not in `{"create", "update", "delete"}`"* (Slice 2 sub-bullet), and Decision 5's *"`Meta.operation` ∈ `{"create", "update", "delete"}` (a single string key)"*.

The rejection is unchanged. The vocabulary now lives at `django_strawberry_framework/mutations/operations.py #"_VALID_OPERATIONS: frozenset[str] = frozenset("`, derived from `MutationOperationDescriptor.supports_model_mutation` over four descriptors (`create`, `update`, `delete`, plus a `form` sentinel that is `supports_model_mutation=False` and so excluded). `mutations/sets.py` imports the constant.

Should say: keep the literal set for readability and add the symbol citation, e.g. "`operation` not in the three model-flavor values `mutations/operations.py::_VALID_OPERATIONS` derives (`create` / `update` / `delete`)". Companion `**Post-ship:**` under Decision 4 or 5 naming commit `7ff97021`.

**N3 — rows C2 + C3 · STALE-DESCRIPTION + SUPERSEDED · Decision 4 · the module inventory**

Current text (Decision 4, Source bullet): *"the subpackage directory `docs/TREE.md`'s target layout reserves, split four ways in the spirit of the `filters/` / `orders/` subpackages (a four-module declarative-set shape, though the module names differ — `inputs` / `sets` / `resolvers` / `fields` here vs. `base` / `factories` / `inputs` / `sets` there …): `inputs.py` (input + payload + `FieldError` generation), `sets.py` (`DjangoMutation` + metaclass + `Meta` validation + finalizer binding), `resolvers.py` (the sync + async write pipeline), and `fields.py` (`DjangoMutationField`)."*

`HEAD` ships **6** non-`__init__` modules under `django_strawberry_framework/mutations/`, not 4:

| module | added by | version at that commit | disposition |
|---|---|---|---|
| `inputs.py`, `sets.py`, `resolvers.py`, `fields.py` | `00618519` (2026-06-17) | pre-cut | the four Decision 4 names |
| `permissions.py` | `4b26b94e` "Finish docs/spec-036-mutations-0_0_11.md" (2026-06-18) | `0.0.10`, pre-cut | **a `036` deliverable Decision 4 omits.** The spec's own `## Implementation plan` Slice-2 row already names it `(new — DjangoModelPermission)`, so this is an internal inconsistency, not later drift. |
| `operations.py` | `7ff97021` "refactor(mutations): introduce canonical mutation operation descriptors" (2026-08-24) | `0.0.14` | a later-card extraction |

Should say: the split is **five** modules as `036` shipped it (`inputs` / `sets` / `resolvers` / `fields` / `permissions`, the last owning `DjangoModelPermission` + the shared `run_permission_classes` walk), with `operations.py` (the canonical operation-descriptor vocabulary) added by the `0.0.14` refactor. Two separate edits: the `permissions.py` omission is a *correction* to what `036` shipped; `operations.py` is a `**Post-ship:**` bullet.

**N4 — row C4 · STALE-DESCRIPTION · Decision 4 · the `sets_mixins.py` reuse prediction**

Current text (Decision 4, end of the Source bullet): *"It reuses `sets_mixins.py` where the lifecycle machinery is genuinely shared."*

At `HEAD`: `grep -rno 'sets_mixins' <HEAD>/django_strawberry_framework/mutations/` returns **0 occurrences**. The importers of `sets_mixins` are `filters/{base,inputs,sets}.py`, `orders/{base,inputs,sets}.py`, `utils/permissions.py`, `utils/strings.py` — no mutation module.

This is a **falsified prediction**, and `docs/builder/BUILD.md` `### `## Current state`: observations stand, predictions do not` says a falsified prediction is rewritten. The clause was vacuously true at `0.0.11` (there was no sibling write flavor, so nothing was "genuinely shared"); the sharing arrived with `038` / `039` and landed **inside `mutations/sets.py`** instead — `::make_declaration_registry`, `::make_meta_validating_metaclass`, `::resolver_seams`, `::bind_write_declarations` — plus `utils/inputs.py::make_shape_build_cache` / `::get_or_store_shape_build`. `sets_mixins.py`'s own machinery is set-family-specific (`RelatedSetTargetMixin`, `collect_related_declarations`, `expanded_once`, `ActiveInputPermissionMixin`) and genuinely does not fit a mutation.

Should say: state that the mutation subsystem does **not** ride `sets_mixins.py` (whose machinery is `RelatedFilter` / `RelatedOrder`-shaped), and that the write-flavor lifecycle substrate the `038` / `039` flavors share lives in `mutations/sets.py` itself. Companion `**Post-ship:**` under Decision 4 recording that the predicted reuse never materialized and where the sharing actually landed, cross-referencing N10's open placement question.

**N5 — row C8 · RENAMED · Decision 4 · the lookup-scoping pin's home, plus the stranded anchor**

Current text (Decision 4, Tests bullet): *"composition pins that belong to other surfaces extend those surfaces' files (`tests/optimizer/test_walker.py` for the G2 plan-shape, `tests/test_permissions.py` for the lookup-scoping pin)"*.

`tests/test_permissions.py` at `HEAD` carries no such pin — only the anchor at `tests/test_permissions.py #"TODO(spec-036 Slice 3)"` and its `Pseudocode:` block. The pin landed at `tests/mutations/test_resolvers.py::test_hidden_row_update_is_not_found_no_existence_leak` and `tests/mutations/test_permissions.py::test_hidden_row_is_not_found_before_auth_signal_no_existence_leak`.

Should say: name those two paths instead of `tests/test_permissions.py`. Keep the `tests/optimizer/test_walker.py` half — it holds.

**Routed to R3 (code repair), inside this cycle's `.py` scope, neither file baseline-dirty:** delete both undischarged anchors (High-1) — `tests/test_permissions.py #"TODO(spec-036 Slice 3)"` with its `Pseudocode:` block, and `tests/mutations/__init__.py #"TODO(spec-036 Slice 1)"` with its `Pseudocode:` block, the latter rewritten as plain provenance in the module docstring. **Repair, not new test authoring** — the pinned behavior already exists, so this is anchor discharge, not a SKIPPED contract, and it owes no hot-path number and no floor run (test files only, per the plan's conditional declarations).

**N6 — row D5 · STALE-DESCRIPTION · Decision 5's internal contradiction · the public-symbol count**

`django_strawberry_framework/__init__.py.__all__` at `HEAD` carries 37 entries including all four of `DjangoModelPermission`, `DjangoMutation`, `DjangoMutationField`, `FieldError`. So Decision 5's body ("Four net-new public symbols") and DoD item 8 ("The four net-new public symbols") are both correct, and the losing text is the justification bullet — now living in the companion at Decision 5 `### Justification (moved from the spec)`, *"One `operation` key over three base classes … keeps the public symbol count at three"*.

**The companion already discloses this**, in Decision 5 `### Changes this Decision underwent` under "Revision 3 (AR-H3)": *"The justification above went stale in one numeral and was moved as written … The argument stands — one selector key against three per-operation base classes — and only the count is wrong; it is recorded here rather than silently repaired inside moved text."*

So R2's decision is narrow and is a judgement, not a fix I can hand over: either (a) leave the moved text verbatim and rely on the existing disclosure, which is the precedent Slice 0 deliberately set, or (b) repair the numeral in place to "at one base class" (which is what the argument actually claims — one `Meta.operation` key instead of three base classes — and sidesteps the export count entirely) and shorten the disclosure to record that the numeral was corrected. **(b) is my recommendation:** the argument's real content is "one selector key beats three base classes", and pinning it to an export count that four later symbols already invalidated makes it rot again the next time the surface grows. Either way, **no spec-side edit is needed** — the spec body and DoD are already right.

**N7 — row H3 (+ F8, G6) · STALE-DESCRIPTION · Edge cases · "byte-unchanged" is false in the present tense**

Current text (`## Edge cases and constraints`, last bullet): *"**No `DjangoType` `Meta` key added.** `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` are byte-unchanged; the `Meta` validation matrix this card adds lives on the mutation metaclass, isolated from `DjangoType.__init_subclass__`."*

I tested the falsifiable half rather than resting on `git log -S`, which `docs/builder/BUILD.md` and prior cycles both flag as fail-open for "when did this change". Method: extract both frozenset literals by regex from `types/base.py` at three commits spanning the `036` build and compare the extracted text.

```
00618519^ (before the 036 build)  DEFERRED = {aggregate_class, fields_class, search_fields}
                                  ALLOWED  = {connection, description, exclude, fields, filterset_class,
                                              globalid_strategy, interfaces, model, name, nullable_overrides,
                                              optimizer_hints, orderset_class, primary, relation_shapes,
                                              required_overrides}                       (15 keys)
00618519  (036 TODO anchors)      identical to the above
4b26b94e  (036 shipped)           identical to the above
```

So **the `036` card changed neither set** — the claim is true about the card, and rows F8 / G6 are CONFORMS.

But at `HEAD` `ALLOWED_META_KEYS` holds **17** keys: `cursor_field` (commit `51421e54`, "feat(relay): keyset value-encoded cursors via Meta.cursor_field (idea #3 / BACKLOG-39)") and `filesystem_path_fields` (commit `567cc6d0`, "feat(security): bound execution resources, fail closed on disclosure, and pin the supply chain") were added by later cards. `DEFERRED_META_KEYS` is unchanged to this day. Read as the present-tense statement about the current tree that its grammar makes it, the sentence is false for `ALLOWED_META_KEYS`.

Should say: re-tense the claim to what it actually contracts — "**this card adds no `DjangoType` `Meta` key**: `DEFERRED_META_KEYS` and `ALLOWED_META_KEYS` are unchanged by it, and the `Meta` validation matrix lives on the mutation metaclass over its own `mutations/sets.py::_ALLOWED_MUTATION_META_KEYS`, isolated from `DjangoType.__init_subclass__`." Note for R2: `types/base.py` itself already carries a standing comment at the ALLOWED literal listing which later cards added which key and asserting "`DEFERRED_META_KEYS` stays unchanged", so the correction has a maintained source to agree with. No `**Post-ship:**` bullet is needed for `036`'s own claim; if R2 wants provenance, the two later keys belong to those cards' specs, not this one.

**N8 — row E2 · STALE-DESCRIPTION · Decision 11 · `primary_for` is never called**

Current text (Decision 11, first sentence): *"resolves the model's **primary** `DjangoType` through `registry.py::TypeRegistry`​`.get(model)` / `primary_for(model)` — the same primary lookup auto-synthesized relation fields and the cascade helper use"*.

`mutations/sets.py::_resolve_primary_type` calls `registry.get(model)`, then `registry.types_for(model)` purely to split the two error messages (zero-type vs multiple-types-no-primary). It never calls `registry.primary_for`. The two are not interchangeable: `TypeRegistry.get`'s own docstring gives three return states and returns the lone type for the single-type-no-`primary`-flag case, while `TypeRegistry.primary_for` is a strict `_primaries` lookup returning `None` there. The behavior `HEAD` implements — and that the mutation tests rely on — is `get`'s permissive form.

Should say: *"through `registry.py::TypeRegistry.get(model)` (whose single-registered-type case resolves without an explicit `Meta.primary` flag), with `types_for(model)` distinguishing the zero-type error from the ambiguous-multiple-types error"*. Drop `primary_for` from the citation.

**N9 — row G3 · STALE-DESCRIPTION · DoD item 3 · registration does not land in the finalizer**

Current text (DoD item 3): *"registration and phase-2.5 binding land in `types/finalizer.py`"*.

Registration happens at class creation, in `mutations/sets.py`'s metaclass (`make_meta_validating_metaclass` -> `register(new_class)` onto the ledger `make_declaration_registry` owns). Only the **bind** lands in `types/finalizer.py`, as one `bind_mutations()` call. Decision 12's own heading — "register at class creation, bind at phase 2.5" — states the split correctly, so DoD item 3 contradicts the Decision it cites.

Should say: *"registration lands at class creation in `mutations/sets.py`'s metaclass and the phase-2.5 bind is invoked from `types/finalizer.py`"*.

**N10 — Escalated (maintainer decision, DRY-1 / Medium-2): should `mutations/sets.py` own the cross-flavor write substrate?**

`docs/builder/worker-3.md` `### The existence challenge` and `docs/builder/BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch` both make this not a worker's call, so it is escalated rather than actioned, and this unit is **not** held at `revision-needed` on it.

Evidence: 25 distinct symbols are imported out of `mutations/sets.py` by `forms/sets.py` (23), `rest_framework/sets.py` (17) and `auth/mutations.py` (4); **4** of them are private-by-name (`_ValidatedMutationMeta`, `_validate_permission_classes`, `_hook_overridden`); and **6** module-level helpers there have zero caller inside `mutations/` (`_hook_overridden`, `construction_kwargs`, `cached_build_input`, `resolve_meta_model`, `resolve_backed_model_or_raise`, `require_non_delete_operation`). `_ValidatedMutationMeta.__slots__` carries six slots the model flavor never reads (`form_class`, `serializer_class`, `optional_fields`, `schema_fingerprint`, `injected_fields`, `nested_fields`).

Resolution paths, for the maintainer to pick between:

1. **Leave it.** The docstrings are unusually good about *why* each helper is shared and which flavor deliberately does not ride it; the coupling is documented, not accidental. Cost: `forms/` and `rest_framework/` keep importing private symbols from a sibling flavor, and `mutations/sets.py` keeps growing as flavor four arrives.
2. **Move the flavor-neutral block to a neutral home** (`write_mixins.py` at the package root, exactly mirroring why `sets_mixins.py` lives there for `filters/` / `orders/` — and the home Decision 4 originally predicted). No functional change: the six zero-caller helpers have nothing local to break, and the edit is import rewrites in three modules plus test imports. This is the path Decision 4's own text points at.
3. **Narrower, mechanical, and independent of 1-vs-2:** have `forms/` and `rest_framework/` import `NON_DELETE_OPERATION_INPUT_KIND` from `..mutations.operations` (its canonical home) instead of from `..mutations.sets` (a re-export hop). Worth doing under either of the above.

Whichever is chosen, Decision 4's Source bullet needs to say it (see N4) — right now the spec predicts option 2 and the code does option 1.

**N11 — Low-2 · Decision-level wording, R2's call · the shared-input edge case**

Current text (`## Edge cases and constraints`): *"**Two mutations over one model share input types — for the same shape.** `CreateItem` and `UpdateItem` resolve to the same materialized `ItemInput` / `ItemPartialInput` module globals when both take the canonical full shape …"*.

Suggested rewrite: *"Two mutations over one model **and one operation kind** share an input type when their effective field sets match: two `create`s over the full editable shape resolve to the same materialized `ItemInput`, two `update`s to the same `ItemPartialInput`. The identity is `(model, operation kind, frozenset(effective field names))`, so a create and an update never share one class — `CreateItem` takes `ItemInput` and `UpdateItem` takes `ItemPartialInput` — and two narrowings that reach one effective set by different `fields` / `exclude` spellings still dedupe."* Graded CONFORMS, so this is a clarity edit, not a correction.

**N12 — cross-cohort observations (not this cohort's to grade)**

- **To R1c (Decision 10 / 15).** `mutations/sets.py::DjangoMutation.check_permission`'s docstring records an authorization-bypass shape worth confirming is closed on the enforcement side: an `async def has_permission` entry returns a truthy coroutine, so a naive `if not has_permission(...)` would read a *deny* as an *allow*. `HEAD` closes it by closing the coroutine and raising `SyncMisuseError` inside `mutations/permissions.py::run_permission_classes`, with the resolver's `authorize_or_raise` catching an async `check_permission` override one level up. Both halves are R1c's territory; flagging only that the seam is named here and its enforcement lives there.
- **To R1c (Decision 15).** The `select_for_update` key I graded SUPERSEDED at the *declaration* layer (N1) has its enforcement in `utils/write_transaction.py` / `mutations/resolvers.py`. R1c owns the lock semantics and the retryable `conflict` `FieldError`; N1 covers only the `Meta` surface and its validator.
- **To R1a (Decision 6).** `mutations/sets.py::_expected_input_attr_names` and `::_validate_relation_override_types` both re-derive "what the generator would emit" by calling `mutations/inputs.py::editable_input_fields` + `::relation_input_annotation` rather than duplicating the rule. If R1a finds a naming-scheme divergence in `inputs.py`, these two validators inherit it automatically — which is the intended coupling, but it means an `inputs.py` finding is also a `sets.py` finding.
- **To Worker 1, for the deferred-work catalog.** DRY-3: `types/finalizer.py::finalize_django_types` is 326 lines / 29 branches with phase 2.5 as an inline statement sequence. Not `036`'s to fix and not in this cycle's scope; a candidate for a future finalizer-decomposition spec.

### Review outcome

`review-accepted`.

This is a read-only conformance audit that lands no source, so the acceptance gate reduces to: the inventory covers the declared territory contract by contract, every grade cites `HEAD`, and every routable row reaches R2 on disk. All three hold. Findings are escalated rather than blocking, per `docs/builder/worker-3.md` `### Acceptance gate`'s Medium-or-higher escalation clause:

- **High-1** (two undischarged `TODO(spec-036)` anchors) is real work, but it is *repair* routed to R3, not a defect in this pass's own output. Recorded in N5 with both paths, both already verified clean at `HEAD` so a repair cannot collide with the concurrent session.
- **Medium-1** (the package suite cannot see a phase-2.5 ordering regression) is a fixture finding whose demonstration would require mutating a baseline-dirty file. Escalated with the exact test that would close it.
- **Medium-2 / DRY-1** is contract-level (whether an abstraction should exist and where), so by `### The existence challenge` it is the maintainer's call and cannot hold this unit at `revision-needed`. Escalated in N10 with three resolution paths.

Nothing found in the graded territory is SKIPPED: `036`'s Slice 2 shipped every contract it declared. The cycle's yield here is 12 routable spec-side rows — 3 SUPERSEDED, 7 STALE-DESCRIPTION, 2 RENAMED — and the reason the SKIPPED column is empty is not thin searching but that the base / `Meta` / finalizer surface is the best-pinned part of `spec-036`: 83 test functions over 2,135 lines in `tests/mutations/test_sets.py` alone, several of them regression tests for bugs found after the card shipped.

---

## Final verification (Worker 1)

Performed in the R2 pass, `docs/builder/bld-036-review-2-spec_reconciliation.md`, which combines spec
reconciliation with this cohort's final verification — the same combined role the precedent cycle's R2
performed. The audit's own contract is `docs/builder/build-036-mutations-0_0_11.md` `## Conformance
grading vocabulary`; there is no `### Spec slice checklist (verbatim)` and no diff to audit, because
every R1 cohort is read-only over source and tests.

**Counts re-derived, not accepted.** Each cohort's grade tally was recomputed by parsing this file's
own inventory table row by row (row-id pattern per cohort, grade cell normalized), off the rendered
table rather than from the summary paragraph:

```
rows=64  CONFORMS=52  SUPERSEDED=3  STALE-DESCRIPTION=7  RENAMED=2  SKIPPED=0
```

Matches this file's stated table exactly, and 52+3+7+2 = 64 = the row count.

**The `A5` / `select_for_update` finding is correct and was acted on**, with one correction to its
evidence: **Decision 5's body carries no `Meta`-key enumeration.**
`grep -c 'optional \`input_class\` / \`partial_input_class\` / \`fields\` / \`exclude\` /
\`permission_classes\`'` over the spec returns **1**, the Slice 2 sub-bullet, so N1's "Decision 5's
body carries the same closed list" describes a site that does not exist. The grade and the fix are
unaffected — one enumeration, one edit. Attribution accepted as given (`951945b7` then `1b06c39e`
BETA-055); the key is now named with its `True` default and the non-bool rejection, while its full lock
semantics are deferred as unowned `0.0.14` machinery per the maintainer's decision.

**`C8` is graded correctly as RENAMED rather than SKIPPED, and I verified the discriminating fact
myself:** `git show 4b26b94e:tests/mutations/test_resolvers.py` and
`git show 4b26b94e:tests/mutations/test_permissions.py` both already contain the two hidden-row rows, in
**this card's own shipping commit**, while `git show 4b26b94e:tests/test_permissions.py` still carries
the `TODO(spec-036 Slice 3)` anchor. So the pin landed elsewhere in the same card and the anchor is
residue — the disposition is anchor removal, not test authoring. R1a's row 82 does not actually conflict
with this: it grades the `tests/mutations/__init__.py` Slice-1 anchor and explicitly routes the Slice-3
one to R1c without grading it.

**N6's recommendation (b) was considered and declined, with the reason recorded**: the public-symbol
numeral inside the companion's **moved** Decision-5 justification stays verbatim, because moved text
staying verbatim is the precedent Slice 0 set deliberately and the existing disclosure one line below
already states exactly the right thing. This cohort's own conclusion — "no spec-side edit is needed" —
is the operative half, and it holds.

**H3's method is the right one and is worth carrying forward:** the frozenset literals were extracted at
three commits and compared as text rather than resting on `git log -S`, which is fail-open for "when did
this ship". All 12 routable rows are discharged in the spec.


**Method audited and accepted.** Every grade cites the read-only `HEAD` snapshot at
`7426e7e7d8aa447e89fee75088447d6a506dec12` or a `git show HEAD:<path>` read; no `git stash` /
`git checkout` / `git restore` / `git worktree` appears anywhere in the pass; the decision to decline a
failability mutation on baseline-dirty territory files is recorded with its reason rather than skipped
silently, and is the right call under `AGENTS.md` rule 34 — a `cp`-and-restore round trip spanning a
pytest run would have reverted any concurrent write landing inside the window.

**Every routable row reached R2 on disk** under `### Notes for Worker 1 (spec reconciliation)`, with the
pre-fix spec text and a recommended replacement — which is the obligation
`docs/builder/BUILD.md` `### Cohorting, naming, and closure` records two prior builders as having
missed. Nothing had to be re-derived from a return report.

Final status: `final-accepted`.

