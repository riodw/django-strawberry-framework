# DRY review: `django_strawberry_framework/forms/sets.py`

Status: verified

## System trace

`forms/sets.py` owns the form-mutation write **declaration** surface
(spec-038 Slice 2 + Slice 3 seams):

- **`DjangoModelFormMutation`** — subclasses `DjangoMutation`; overrides
  `_resolve_model` (`Meta.form_class._meta.model`), `_validate_meta` (ModelForm
  matrix), `build_input` / `input_type_name` / `input_module_path` (form-input
  namespace), `resolve_*` (form pipeline). Rides the model metaclass,
  `_mutation_registry`, and `bind_mutations()` unchanged for the model-backed
  `<Name>Payload`.
- **`DjangoFormMutation`** — model-less plain `forms.Form` sibling: own
  `DjangoFormMutationMetaclass` built via
  `mutations/sets.py::make_meta_validating_metaclass(register_form_mutation,
  name="DjangoFormMutationMetaclass", module=__name__)`, disjoint declaration
  ledger via `make_declaration_registry("DjangoFormMutation")`, and
  `bind_form_mutations()` materializing form input + pinned `{ ok errors }`
  payload (`build_payload_type(object_type=None)`).
- **Shared form helpers (module-local)** — `_cached_build_form_input` (guard
  before shape cache), `_form_kwargs_overridden` / `_default_get_form_kwargs` /
  `_default_get_form`, `_build_and_stash_form_input`,
  `_form_input_type_name_for`, `_resolve_effective_form_field_names`.
- **Already-promoted owners (not re-owned here)** — `mutations/sets.py`
  (`reject_unknown_meta_keys`, `require_backing_class`,
  `resolve_meta_model` / `resolve_backed_model_or_raise`,
  `NON_DELETE_*`, `non_delete_operation_error`, `_hook_overridden`,
  `cached_build_input`, `build_and_stash_input`, `construction_kwargs`,
  `resolver_seams`, `_validate_permission_classes`, `_ValidatedMutationMeta`);
  `mutations/permissions.py::run_permission_classes`;
  `utils/inputs.py::make_shape_build_cache`; Slice-1
  `forms/inputs.py` narrowing / guards / materialize.

Connected behavior examined:

- `mutations/sets.py` — model bind, metaclass, shared Meta/build primitives
- `rest_framework/sets.py` — serializer sibling (ModelSerializer rides
  `DjangoMutation`; no plain-form twin; construction-hook waiver deliberately
  absent — `injected_fields` only)
- `forms/inputs.py` / `forms/resolvers.py` — generator + runtime pipeline the
  seams call
- `types/finalizer.py` — phase-2.5 `bind_form_mutations()` after
  `bind_mutations()`
- `mutations/fields.py` — `iter_form_mutations` for field factory routing
- `registry.py` — co-clear of form declaration registry + shape cache
- Tests — `tests/forms/test_sets.py` (Meta / registry / bind / waiver /
  perform_mutate); live wire via `examples/fakeshop/test_query/` form mutations
  (`createItemViaForm` / `updateItemViaForm` / `submitContact` / …)

ITEM_BASELINE `df330d6657016a890fead777e4016a9752525a85`: cycle introduced no
edits. Concurrent dirty on the target is a one-line docstring
`FormInputFieldSpec` → `utils/inputs.py::InputFieldSpec` rename note (InputFieldSpec
migration already landed elsewhere); left untouched.

## Verification

Searches: every public/private definition in the target; sibling
`SerializerMutation` / `DjangoMutation` Meta + bind + construction hooks;
`make_declaration_registry` consumers (mutations / forms / auth); exact-body
audit hit on `check_permission`; live products form mutation names.

Compared contracts:

- **ModelForm vs plain Meta matrices** — disjoint allowed keys, opposite
  `operation` rules, opposite Form/ModelForm type gates, DenyAll vs
  `DjangoModelPermission` defaults, plain-only model-permission reject. Same
  *mechanics* already call shared primitives; rules must not merge.
- **Form vs serializer `build_input` / cache** — form keys shape
  pre-build `(form_class, kind, effective names)` and uses
  `cached_build_input`; serializer keys post-build `SerializerInputShape` and
  cannot. Documented in serializer `build_input` (P1.7 partial reuse).
- **Form vs serializer construction waiver** — form waives create-required via
  `get_form_kwargs` / `get_form` override; serializer never does (injected_fields
  only). Distinct Decision-7 contracts.
- **`_bind_form_mutation` vs `_bind_mutation`** — shared stash shape; differ on
  primary resolve, `build_input` arity, payload object slot. Folding needs a
  model-less bind seam owned by `mutations/sets.py` (Decision 6 rejects
  relaxing `_bind_mutation`).
- **Metaclass `__new__` twin** — byte-similar validate+register; differ only
  in register target. Natural factory owner is `mutations/sets.py` beside
  `make_declaration_registry`, not this file.
- **`check_permission` bodies** — both call `run_permission_classes` (A5). Walk
  already single-sited; remaining methods are per-base override seams across
  the intentional non-inheritance boundary.

Optional audit (`export_dry_review.py audit --stdout`) used only for
orientation; every candidate reconciled against behavior above. No scratch
tests required — contracts are pinned by `tests/forms/test_sets.py` and live
form queries.

Candidates (item 1 now implemented; rest rejected / deferred):

1. **Extract shared Meta-validating metaclass factory**
   (`DjangoMutationMetaclass` ↔ `DjangoFormMutationMetaclass`) — true
   structural twin; owner is `mutations/sets.py`. **Implemented** (not deferred):
   `mutations/sets.py::make_meta_validating_metaclass(register, *, name, module)`
   now owns the validate-then-register lifecycle, and this file's
   `DjangoFormMutationMetaclass` is a factory-call assignment over the disjoint
   plain-form ledger. The `name` / `module` arguments pin the produced
   metaclass's public identity (`__name__` / `__qualname__` / `__module__`) so
   the shared function-local class does not leak into either public surface.
   Consolidated at the owner beside `make_declaration_registry`, as this file's
   review predicted — the assignment rule (siblings consolidate only when the
   shared piece is owned elsewhere) held.
2. **Fold `_bind_form_mutation` into `_bind_mutation`** — Decision 6 explicit
   reject (model-less branch must not leak into the model bind). Defer.
3. **Alias `DjangoFormMutation.check_permission = DjangoMutation.check_permission`**
   — eliminates a thin wrapper already delegating to
   `run_permission_classes`. Would couple the public plain-form base to the
   model base across the non-inheritance boundary; auth's alias is for a
   synthesized holder, not a consumer base. Reject.
4. **Unify ModelForm / plain `_validate_meta` via shared helper** — would need
   mode flags for operation / type-gate / permission default / model-permission
   reject. Obscures ownership. Reject.
5. **Derive `_ALLOWED_PLAIN_FORM_META_KEYS` from ModelForm set** — keys must
   change independently. Reject.
6. **Promote `_form_kwargs_overridden` to mutations/sets** — serializer no
   longer uses construction-hook waiver; sole consumer is form. Keep local.
   Reject.
7. **Force serializer through `cached_build_input`** — wrong key timing;
   serializer docs already explain. Reject (sibling-owned).
8. **Move `_resolve_effective_form_field_names` into `forms/inputs.py`** —
   thin tuple wrapper for cache/name/validate; sets is the consumer owner.
   Reject.
9. **Shared `input_module_path` / `_input_field_specs` mixin across form
   bases** — two lines of slot init on intentionally separate bases; a mixin
   for attribute defaults adds hierarchy without a shared rule. Reject.

## Opportunities

None — form Meta/bind/construction responsibilities that should change together
already live at `mutations/sets.py`, `mutations/permissions.py`,
`utils/inputs.py`, and `forms/inputs.py`. Remaining parallels with
`mutations/sets.py` / `rest_framework/sets.py` are intentional flavor matrices
or sibling-owned seams this file must not absorb.

## Judgment

The ~925-line file is mostly two disjoint Meta matrices plus thin seam
overrides over already-promoted shared plumbing. The one structural twin the
earlier cut deferred — `make_meta_validating_metaclass(register)` beside
`make_declaration_registry` in `mutations/sets.py` — has since landed at that
owner (with a `name` / `module` identity pin), and this file now consumes it
via a factory-call assignment; the remaining candidates stay rejected. Ready
for Worker 2.

## Independent verification (Worker 2)

Re-traced `forms/sets.py` through `mutations/sets.py` (metaclass, bind,
`check_permission`, shared Meta/build primitives), `rest_framework/sets.py`
(serializer construction / `injected_fields` vs form waiver), `forms/inputs.py`
+ `forms/resolvers.py`, `types/finalizer.py` (`bind_form_mutations`),
`mutations/fields.py` (`iter_form_mutations`), `registry.py` co-clear, and
`auth/mutations.py` (permission-holder alias of `DjangoMutation.check_permission`).
Scoped production diff vs ITEM_BASELINE
`df330d6657016a890fead777e4016a9752525a85` was empty for this file's own item.
The metaclass consolidation owned by `mutations/sets.py` later edited this file
too (the `DjangoFormMutationMetaclass` class body became a
`make_meta_validating_metaclass(...)` assignment plus its import + docstring) —
an owner-driven change, not a forms-item edit. Other concurrent dirt on the
target is the one-line docstring `FormInputFieldSpec` →
`utils/inputs.py::InputFieldSpec` rename — left untouched, not cycle work.

### Challenges

1. **Metaclass factory — consolidated at the owner.** `DjangoMutationMetaclass.__new__`
   and `DjangoFormMutationMetaclass.__new__` were structural twins (build → skip
   abstract `Meta is None` → `_validate_meta` → register), differing only in the
   register ledger. The factory has since landed at
   `mutations/sets.py::make_meta_validating_metaclass` beside
   `make_declaration_registry` — the correct owner, not this file — and this
   file's `DjangoFormMutationMetaclass` is now a factory-call assignment. The
   factory takes keyword-only `name` / `module` and pins `__name__` /
   `__qualname__` / `__module__` on the produced class, so neither public
   metaclass inherits the shared `<locals>` identity (which would have broken
   addressability / introspection / reference pickling). No third Meta-
   validating twin (auth synthesizes holders; FilterSet/OrderSet metaclasses
   collect related declarations, different contract). Consolidating here would
   have inverted ownership; the owner-side consolidation is what shipped.

2. **Fold `_bind_form_mutation` into `_bind_mutation`?** **Reject stands.**
   Model bind resolves primary + `build_input(meta, primary_type)` + object-slot
   payload; plain bind keeps `_primary_type=None`, `build_input(meta)` arity,
   and `build_payload_type(object_type=None)`. Decision 6 forbids leaking the
   model-less branch into the model bind. Shared stash shape is already
   intentional parallelism, not a missing helper in this file.

3. **Alias `DjangoFormMutation.check_permission`?** **Reject stands.** Both
   bodies already call `run_permission_classes` (A5). Auth's
   `check_permission=DjangoMutation.check_permission` is for a synthesized
   holder, not a consumer-facing base across the intentional non-inheritance
   boundary. Aliasing would couple public bases without consolidating policy.

4. **Unify Meta matrices / derive plain keys / promote
   `_form_kwargs_overridden` / force serializer through `cached_build_input` /
   move `_resolve_effective_form_field_names` / mixin for
   `input_module_path`?** **All rejects stand.** Matrices are opposite on
   operation / Form vs ModelForm gates / DenyAll vs DjangoModelPermission /
   model-permission reject. Serializer waives via auditable
   `Meta.injected_fields`, not construction-hook override; key timing for
   serializer cache is post-build. Effective-name helper is a thin sets-side
   cache/name consumer of Slice-1 narrowing. Attribute defaults on intentionally
   separate bases do not justify a mixin.

### Missed opportunities

None that this file should absorb. Shared Meta/build/permission/cache
mechanics already live at `mutations/sets.py`, `mutations/permissions.py`,
`utils/inputs.py`, and `forms/inputs.py`. Remaining form↔mutation /
form↔serializer parallels are flavor matrices or sibling-owned seams; the one
real structural twin (metaclass factory) has landed at its owner
`mutations/sets.py` and is now consumed here by assignment.

### Disposed findings

- Concurrent docstring dirt ≠ cycle edit; scoped baseline diff empty.
- Exact-body `check_permission` similarity is already single-sited walk policy.
- `get_form_kwargs` / `get_form` dual assignment is shared module defaults, not
  duplicated bodies.

Status: verified.

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
