# DRY review: folder `django_strawberry_framework/forms/`

Status: verified

Iteration 2026-07-16: re-run after centralizing the permission-class/auth-alias
gate in `utils/permissions.py::auth_aliases_for_permission_classes`; independent
folder verification is complete (Worker 2 below), disposition verified.

## System trace

`forms/` is the Django-`Form` / `ModelForm` write component (spec-038): declared
form fields become GraphQL mutation inputs, bind through phase 2.5, and run a
construct → `is_valid()` → write → payload pipeline.

Folder shape after the five verified file reviews:

- `__init__.py` — public re-exports of `DjangoFormMutation` /
  `DjangoModelFormMutation` only.
- `converter.py` — model-less `forms.Field` → annotation + decode kind
  (`convert_form_field`, `form_field_required`, kind constant re-exports from
  `utils/inputs`).
- `inputs.py` — Slice-1 generators (`build_form_input_class` /
  `build_form_inputs`), effective-field narrowing, create / partial-required
  guards, materialize + `clear_form_input_namespace` (clear owner
  `forms.input_namespace`, `before_bind=True`).
- `sets.py` — two bases + disjoint Meta matrices, plain-form declaration
  registry (`forms.declarations`), per-pass shape cache (`forms.shape_cache`),
  construction hooks, `bind_form_mutations()`.
- `resolvers.py` — form-keyed decode, partial reconstruction, ModelForm path on
  `run_write_pipeline_sync`, plain-form local orchestration with shared
  BETA-055 phase helpers.

Connected behavior re-traced for this folder pass (not inherited as proven):
`mutations/sets.py` (metaclass, `make_declaration_registry`,
`cached_build_input` / `build_and_stash_input`, `resolver_seams`,
`construction_kwargs`); `mutations/resolvers.py::run_write_pipeline_sync` +
plain-form F6 scope-out; `rest_framework/sets.py` / `resolvers.py` (serializer
rides `DjangoMutation` metaclass + the same write skeleton; construction waiver
via `Meta.injected_fields`, not form hooks); `utils/inputs.py` /
`utils/write_values.py` / `utils/write_transaction.py`; finalizer phase-2.5
`bind_form_mutations`; live fakeshop form mutations under
`examples/fakeshop/test_query/` (`submitContact` / `submitPing`, library
ModelForm + plain multi-row writes) and `apps/*/forms.py` + schema sites;
package `tests/forms/`.

Folder-level axes examined: duplicated policy across modules, state ownership
(three clear owners), competing helpers, public export flavor, lifecycle work
repeated at several phases, and the two assignment-named deferrals
(plain-form skeleton fold; metaclass factory).

## Verification

- Item-scoped baseline `eefc2704e45bcdc3ea08d66634d4582f60a51b7d`: working
  tree matched baseline for `forms/` at pass start (empty item-scoped diff).
  Concurrent dirt vs HEAD on all five `forms/` modules is pre-baseline WIP
  (InputFieldSpec migration, plain-form BETA-055 phase adoption, related
  file-pass consolidations) — left untouched. Concurrent dirty paths outside
  this item (`docs/GLOSSARY.md`, `docs/dry/dry-0_0_13.md`, other dry artifacts,
  `examples/fakeshop/db.sqlite3`, auth / permissions / orders / mutations WIP)
  left untouched. Plan checkbox not edited.
- Re-read all five forms sources end-to-end. Grepped package for
  `run_write_pipeline_sync`, `_run_plain_form_pipeline_sync`,
  `DjangoFormMutationMetaclass` / `DjangoMutationMetaclass`,
  `register_subsystem_clear` owners under `forms.`, `form_field_required`,
  `get_form_fields`, `_form_kwargs_overridden`, and construct/`is_valid` sites.
- Compared `rest_framework/` as connected evidence: `SerializerMutation`
  subclasses `DjangoMutation` (one metaclass, one model declaration registry);
  no plain-form twin; write path already shares `run_write_pipeline_sync`.
  Form↔serializer remaining parallels are flavor matrices (form `base_fields`
  + column routing vs serializer declared fields; form construction-hook waiver
  vs `injected_fields`), not a second owner of one rule inside `forms/`.
- Independently re-traced assignment-named deferrals from source (below). Did
  not concatenate file artifacts; used their deferred labels only as search
  flags.
- No production edit warranted; no focused pytest (zero-edit). No full pytest.
  Item-scoped diff remains empty aside from this artifact.

## Opportunities

None — folder-visible responsibilities that should change together already
have one owner after the file-pass consolidations sitting in the baseline WIP
(`form_field_required`, `InputFieldSpec`, `convert_with_mro`,
`decode_provided_fields`, `make_input_namespace` / `make_shape_build_cache`,
`cached_build_input` / `build_and_stash_input`, ModelForm
`run_write_pipeline_sync` decode/write steps, plain-form shared phase helpers).
No competing helper layer remains *inside* `forms/` analogous to the filters
folder's private path-walk vs `get_model_field` case.

### Rejected / deferred (re-proved)

1. **Fold plain-form body onto `run_write_pipeline_sync`
   (`mutations/resolvers.py`).** Re-proved: skeleton docstring scopes F6 to
   model-backed create/update; plain path has no locate, no `primary_type`, no
   object-slot refetch, and builds `{ ok, errors }` via `payload_cls(ok=…)`
   rather than `build_payload(slot, …)`. Alias / auth / write-phase invariants
   already share `pipeline_alias_guard` / `authorization_phase` /
   `pipeline_write_phase` / `require_managed_write` — the remaining parallel is
   orchestration shape, not a second incomplete encoding of those invariants.
   Absorbing the plain body would require model-less / ok-payload seams on the
   skeleton (owner `mutations/resolvers.py`, still an open plan item). Defer.

2. **`make_meta_validating_metaclass(register)` beside
   `make_declaration_registry` (`mutations/sets.py`).** Re-proved: after
   normalizing the register name, `DjangoMutationMetaclass.__new__` and
   `DjangoFormMutationMetaclass.__new__` are structural twins (build → skip
   abstract `Meta is None` → `_validate_meta` → register). No third Meta-
   validating twin (auth synthesizes holders; FilterSet/OrderSet metaclasses
   collect related declarations). Owner is `mutations/sets.py` (open plan item
   + later mutations folder pass), not a forms-local factory. Implementing
   here would force a mutations edit without a forms-owned rule change.
   Defer.

3. **Extract shared `get_form` + `is_valid` glue between ModelForm write step
   and plain body.** Two call sites in `resolvers.py` share construct/validate
   sequencing but differ on mutation-instance retention (`perform_mutate` needs
   the instance; ModelForm write uses a throwaway + `form.save`) and on how
   errors enter the envelope (`list[FieldError]` return vs `_error_payload`).
   A helper would obscure flavor ownership for two lines. Reject.

4. **Unify ModelForm / plain `_validate_meta` via shared helper.** Opposite
   matrices on operation presence, Form vs ModelForm type gates, DenyAll vs
   DjangoModelPermission default, and model-permission reject. Mode flags
   would hide Decision 6/10/11. Reject.

5. **Fold `_bind_form_mutation` into `_bind_mutation`.** Decision 6: plain bind
   keeps `_primary_type=None`, different `build_input` arity, and
   `build_payload_type(object_type=None)`. Must not leak into the model bind.
   Reject.

6. **Triple clear owners (`forms.input_namespace` / `forms.declarations` /
   `forms.shape_cache`).** Intentional: rebuild bookkeeping (`before_bind=True`)
   vs declaration ledger vs per-pass build cache. Same pattern as filters'
   dual clears. Not consolidation candidates.

7. **`CREATE_SHAPED_KINDS` unused constant.** Defined in `inputs.py`, never
   consulted; create-vs-partial branching is the `operation_kind == PARTIAL`
   check at the build sites. Unused vocabulary is cleanup, not a second
   implementation of a rule that should change together. Out of scope for this
   DRY item.

8. **Public flavor.** Package `__all__` exports only the two consumer bases;
   advanced entry points (`bind_form_mutations`, converters, guards) stay
   submodule imports. Matches the DRF-first / Meta-class public surface.
   Consistent.

9. **Alias `DjangoFormMutation.check_permission` onto `DjangoMutation`.**
   Walk already single-sited in `run_permission_classes`; aliasing would couple
   public bases across the intentional non-inheritance boundary. Reject.

## Judgment

Folder ownership is already layered correctly: converter owns model-less
annotation + requiredness; inputs owns generation + guards + namespace;
sets owns Meta/bind/construction + plain declaration ledger; resolvers own
runtime decode/write with ModelForm on the shared skeleton and plain form on
shared phase helpers. The two real structural twins that remain
(metaclass factory; plain-form skeleton fold) are correctly parked on open
`mutations/` plan items, not solo consolidations this folder should absorb.
Ready for Worker 2.

## Implementation (Worker 1)

- **Zero-edit.** No production, test, or export changes.
- **Owner chosen:** n/a — no accepted consolidation.
- **Kept separate / deferred:** plain-form ↔ `run_write_pipeline_sync` (owner
  `mutations/resolvers.py`); metaclass factory (owner `mutations/sets.py`);
  construct/`is_valid` glue; Meta matrices; plain vs model bind; triple clear
  owners; unused `CREATE_SHAPED_KINDS` cleanup.
- **Validation:** item-scoped `git diff eefc2704… -- django_strawberry_framework/forms/`
  empty at finish (artifact-only). No ruff (no Python edits). No pytest.
- **Changelog:** no.
- **Concurrent paths preserved:** edits only this artifact. Pre-existing WIP
  under `forms/` and other packages left alone. Plan checkbox not touched.

## Independent verification (Worker 2)

Re-traced `forms/` as one component (all five modules + public re-export
surface) against connected `mutations/sets.py` / `mutations/resolvers.py`,
`rest_framework/sets.py` / `resolvers.py`, `utils/inputs.py` /
`utils/write_values.py` / `utils/write_transaction.py`, and finalizer
phase-2.5 `bind_form_mutations`. Did not treat Worker 1 findings as proven.
Item-scoped `git diff eefc2704e45bcdc3ea08d66634d4582f60a51b7d --
django_strawberry_framework/forms/` is empty; working-tree dirt vs HEAD on
all five modules matches baseline (concurrent WIP) and was left untouched.

**Folder ownership.** Converter owns model-less annotation + the single
`form_field_required` rule; inputs owns generation / guards / namespace;
sets owns Meta / bind / construction + the plain declaration ledger; resolvers
own runtime decode/write. Triple clear owners
(`forms.input_namespace` `before_bind=True`, `forms.declarations`,
`forms.shape_cache`) match distinct lifecycle roles. Package `__all__` exports
only the two consumer bases. No competing helper layer remains inside the
folder analogous to the filters private path-walk case.

**Challenged deferral 1 — fold plain-form onto `run_write_pipeline_sync`.**
**Deferral stands.** Skeleton docstring and body are F6-scoped to
model-backed create/update: they require `primary_type`, update locate,
`refetch_optimized`, and `build_payload(slot, …)`. Plain path has
`_primary_type is None`, no `id`, builds `{ ok, errors }` via
`payload_cls(ok=…)`, and retains `perform_mutate`. Alias / auth / write-phase
invariants already share `pipeline_alias_guard` / `authorization_phase` /
`pipeline_write_phase` / `require_managed_write` — remaining parallel is
orchestration shape, not a second incomplete encoding of those invariants.
Owner is `mutations/resolvers.py` (open plan item); a forms-local fold would
invent seams the skeleton does not own.

**Challenged deferral 2 — `make_meta_validating_metaclass(register)`.**
**Deferral stands.** After normalizing the register name,
`DjangoMutationMetaclass.__new__` and `DjangoFormMutationMetaclass.__new__`
are structural twins (build → skip abstract `Meta is None` → `_validate_meta`
→ register). No third Meta-validating twin (auth synthesizes holders;
FilterSet/OrderSet metaclasses collect related declarations). Owner is
`mutations/sets.py` beside `make_declaration_registry`, not a forms-local
factory. Implementing here would force a mutations edit without a forms-owned
rule change.

**Rejected candidates re-checked.** (3) construct/`is_valid` glue — ModelForm
write uses throwaway + `form.save` + `list[FieldError]` return; plain retains
mutation instance for `perform_mutate` and `_error_payload`. (4) Meta matrices
— opposite operation / Form-vs-ModelForm / DenyAll-vs-DjangoModelPermission /
model-permission-reject gates (Decisions 6/10/11). (5) `_bind_form_mutation`
vs `_bind_mutation` — Decision 6 arity and object-slot differences. (6) triple
clears — intentional. (7) unused `CREATE_SHAPED_KINDS` — vocabulary/cleanup,
not a second rule encoding (`operation_kind == PARTIAL` is the live split).
(8) public flavor — consistent. (9) `check_permission` alias across the
non-inheritance boundary — reject; walk already single-sited in
`run_permission_classes`.

**Missed folder-level consolidations.** Searched remaining construct/validate
sites, Meta-validation twins, clear owners, bind paths, and form↔serializer
parallels *inside* `forms/`. Create-path `build_form_inputs` discarding the
partial is wasted work, not duplicated policy. Form↔serializer remaining
parallels are flavor matrices (construction-hook waiver vs `injected_fields`;
`base_fields` vs declared serializer fields) — project-pass / open
`mutations/` / `rest_framework/` items, not solo consolidations this folder
should absorb. No additional cross-module policy warrants a production edit.

**Scope.** No production edits by Worker 2. Plan item checked. Concurrent WIP
outside the empty item-scoped diff left untouched.

**Disposition:** verified.
