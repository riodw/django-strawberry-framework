# DRY review: `django_strawberry_framework/forms/sets.py`

Status: verified

## System trace

`django_strawberry_framework/forms/sets.py` implements the declarative base classes, `Meta` validation, form declaration registry, input materialization, resolver seams, and phase-2.5 schema binding for Django form-backed GraphQL mutations ([spec-038][spec-038] Decisions 6, 7, 8, 10, 11, 13). It provides the form write surface riding the mutation architecture defined in [`django_strawberry_framework/mutations/sets.py`][mutations-sets].

1. **Two-Flavor Mutation Base Architecture ([spec-038][spec-038] Decision 6):**
   - [`DjangoModelFormMutation`][forms-sets]: Subclasses [`DjangoMutation`][mutations-sets] for `forms.ModelForm`-backed mutations. It reuses the [`DjangoMutation`][mutations-sets] metaclass, declaration registry, and [`bind_mutations`][mutations-sets] phase-2.5 bind pipeline. It binds a model-backed `<Name>Payload` (with `node` / `result` object slot) and overrides key seams:
     - [`DjangoModelFormMutation._resolve_model`][forms-sets]: Resolves the model from `Meta.form_class._meta.model` via [`resolve_meta_model`][mutations-sets].
     - [`DjangoModelFormMutation._validate_meta`][forms-sets]: Validates the `ModelForm` configuration matrix against [`_ALLOWED_MODELFORM_META_KEYS`][forms-sets].
     - [`DjangoModelFormMutation.build_input`][forms-sets]: Materializes form-derived inputs into `django_strawberry_framework.forms.inputs` and stashes reverse-map specs.
     - [`DjangoModelFormMutation.input_type_name`][forms-sets]: Computes the canonical `<FormClass>Input` or `<FormClass>PartialInput` name.
     - `resolve_sync` and `resolve_async`: Delegated to [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers] via [`resolver_seams`][mutations-sets].
   - [`DjangoFormMutation`][forms-sets]: The model-less sibling for plain `forms.Form`-backed mutations. Because it operates without a Django ORM model or `DjangoType` object slot, it uses its own dedicated metaclass ([`DjangoFormMutationMetaclass`][forms-sets] minted via [`make_meta_validating_metaclass`][mutations-sets]), its own disjoint declaration registry ([`_form_mutation_declaration_registry`][forms-sets]), and its own phase-2.5 binding function ([`bind_form_mutations`][forms-sets]). It overrides seams:
     - [`DjangoFormMutation._validate_meta`][forms-sets]: Enforces model-less form rules against [`_ALLOWED_PLAIN_FORM_META_KEYS`][forms-sets], rejecting any `Meta.operation` and requiring plain `forms.Form`.
     - [`DjangoFormMutation.build_input`][forms-sets]: Materializes the plain form input with the fixed `FORM` sentinel shape.
     - [`DjangoFormMutation.input_type_name`][forms-sets]: Returns the canonical input name for the plain form shape.
     - [`DjangoFormMutation.perform_mutate`][forms-sets]: Overridable hook for custom model-less execution (invoking `form.save()` if present).
     - [`DjangoFormMutation.check_permission`][forms-sets]: Write authorization seam delegating to [`run_permission_classes`][mutations-permissions].
     - `resolve_sync` and `resolve_async`: Minted via [`resolver_seams`][mutations-sets] with `with_id=False` (no instance locator needed).

2. **Disjoint Meta Validation Matrices ([spec-038][spec-038] Decisions 6, 10, 11):**
   - [`_ALLOWED_MODELFORM_META_KEYS`][forms-sets]: Allowed keys for `DjangoModelFormMutation` (`form_class`, `operation`, `fields`, `exclude`, `permission_classes`, `select_for_update`).
   - [`_ALLOWED_PLAIN_FORM_META_KEYS`][forms-sets]: Allowed keys for `DjangoFormMutation` (`form_class`, `fields`, `exclude`, `permission_classes`).
   - **Typo Guards:** [`reject_unknown_meta_keys`][mutations-sets] validates own-keys on `Meta` against the allowed keys set.
   - **Subclass Enforcement:** [`require_backing_class`][mutations-sets] and [`require_subclass`][mutations-sets] enforce that `form_class` is a `forms.ModelForm` for `DjangoModelFormMutation` and a `forms.Form` for `DjangoFormMutation`.
   - **Targeted Edge Case Diagnostics:**
     - On `DjangoFormMutation`, `hasattr(meta, "operation")` is rejected with a targeted diagnostic explaining that model-less forms have no model operation.
     - Passing a `forms.ModelForm` to `DjangoFormMutation` triggers a targeted error redirecting the user to `DjangoModelFormMutation`.
     - Passing a [`DjangoModelPermission`][mutations-permissions] to a plain `DjangoFormMutation` is rejected at class creation because model-less forms lack an ORM model.
   - **Operation Restriction:** [`DjangoModelFormMutation._validate_meta`][forms-sets] uses [`require_non_delete_operation`][mutations-sets] to restrict `Meta.operation` strictly to `{"create", "update"}` (`"delete"` is rejected).
   - **Field Selection Normalization:** [`_normalized_form_field_selection`][forms-sets] normalizes `Meta.fields` / `Meta.exclude` via [`normalize_meta_field_selection`][mutations-sets] and validates them against [`_resolve_effective_form_field_names`][forms-sets] (which delegates to [`resolve_effective_form_fields`][forms-inputs]).
   - **Permission and Lock Normalization:** `DjangoModelFormMutation` runs [`model_backed_permission_and_lock`][mutations-sets] (defaulting to [`DjangoModelPermission`][mutations-permissions]), while `DjangoFormMutation` defaults to [`DenyAll`][mutations-permissions] unless explicitly set to `[]`.

3. **Input Construction, Shape Caching, and Reverse Mapping ([spec-038][spec-038] Decisions 7, 8):**
   - [`_form_shape_build_cache`][forms-sets] and [`clear_form_shape_build_cache`][forms-sets]: Created via [`make_shape_build_cache`][utils-inputs] and registered with [`register_subsystem_clear`][registry] to cache built input types across mutation declarations within a finalization pass.
   - [`_default_mutation_get_form_fields`][forms-sets], [`_mutation_form_fields`][forms-sets], and [`_form_input_hook_identity`][forms-sets]: Resolve the form field mapping from `get_form_fields` and provide cache discrimination for overridden hooks.
   - [`_resolve_effective_form_field_names`][forms-sets]: Resolves effective field names after `fields`/`exclude` filtering.
   - [`_form_kwargs_overridden`][forms-sets]: Checks if a mutation class overrides `get_form_kwargs` or `get_form` using [`_hook_overridden`][mutations-sets]. When overridden, the create-required narrowing guard is waived.
   - [`_cached_build_form_input`][forms-sets]: Uses [`cached_build_input`][mutations-sets] to run the required-fields guard ([`guard_create_required_fields`][forms-inputs] or [`guard_partial_required_column_less_fields`][forms-inputs]) per-declaration before performing cache lookup by shape identity `(form_class, operation_kind, frozenset(effective), hook_identity)`. Delegates input class generation to [`build_form_input_class`][forms-inputs] or [`build_form_inputs`][forms-inputs].
   - [`_build_and_stash_form_input`][forms-sets]: Calls [`build_and_stash_input`][mutations-sets] with [`materialize_form_input_class`][forms-inputs] to materialize the `@strawberry.input` class into `django_strawberry_framework.forms.inputs` and stash the reverse-map `field_specs` on `cls._input_field_specs` for runtime decoding.
   - [`_form_input_type_name_for`][forms-sets]: Derives the GraphQL input type name via [`form_input_type_name`][forms-inputs].

4. **Form Instantiation Seams and Hooks ([spec-038][spec-038] Decision 8):**
   - [`_default_get_form_kwargs`][forms-sets]: Returns constructor kwargs via [`construction_kwargs(data=data, files=files, instance=instance)`][mutations-sets].
   - [`_default_get_form`][forms-sets]: Instantiates `form_class(**self.get_form_kwargs(...))`.

5. **Declaration Registry and Finalizer Phase-2.5 Integration ([spec-038][spec-038] Decisions 6, 13):**
   - [`_form_mutation_declaration_registry`][forms-sets]: Created via [`make_declaration_registry("DjangoFormMutation")`][mutations-sets], exporting `register_form_mutation`, `clear_form_mutation_registry`, `iter_form_mutations`, and `_form_mutation_registry`.
   - [`bind_form_mutations`][forms-sets]: Called during Phase 2.5 finalization in [`django_strawberry_framework/types/finalizer.py`][types-finalizer] alongside [`bind_mutations`][mutations-sets]. It calls [`bind_write_declarations`][mutations-sets] over `iter_form_mutations` with `resolve_object_type=lambda _mutation_cls, _meta: None`, materializing plain form inputs and pinned `{ ok errors }` payload types.

Connected behavior examined:
- [`django_strawberry_framework/forms/inputs.py`][forms-inputs]: Input generation building `@strawberry.input` classes, field name derivation, and required-field guards.
- [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers]: Sync and async form execution pipeline consuming stashed `_input_field_specs`.
- [`django_strawberry_framework/mutations/sets.py`][mutations-sets]: Shared mutation infrastructure (`DjangoMutation`, `bind_write_declarations`, `build_and_stash_input`, `cached_build_input`, `make_declaration_registry`, `make_meta_validating_metaclass`, `resolver_seams`, `reject_unknown_meta_keys`, `normalize_meta_field_selection`, `require_non_delete_operation`, `construction_kwargs`, `model_backed_permission_and_lock`).
- [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions]: Permission classes `DjangoModelPermission`, `DenyAll`, and execution walk `run_permission_classes`.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Schema finalization orchestrator calling `bind_mutations` and `bind_form_mutations` in Phase 2.5.
- [`django_strawberry_framework/registry.py`][registry]: Subsystem clear coordinator managing `clear_form_mutation_registry` and `clear_form_shape_build_cache`.
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Shape build cache factory `make_shape_build_cache` and sequence normalizer `normalize_field_name_sequence`.
- [`tests/forms/test_sets.py`][test-forms-sets]: Test suite verifying form mutation validation matrices, input generation, registry isolation, and binding.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/forms/sets.py --review docs/dry/dry-file-forms__sets.md --include-constants`):
- Parsed 1 target file, 1014 lines, 23 target definitions:
  - 2 constants: [`_ALLOWED_MODELFORM_META_KEYS`][forms-sets], [`_ALLOWED_PLAIN_FORM_META_KEYS`][forms-sets]
  - 11 functions: [`_default_mutation_get_form_fields`][forms-sets], [`_mutation_form_fields`][forms-sets], [`_form_input_hook_identity`][forms-sets], [`_cached_build_form_input`][forms-sets], [`_resolve_effective_form_field_names`][forms-sets], [`_normalized_form_field_selection`][forms-sets], [`_form_kwargs_overridden`][forms-sets], [`_default_get_form_kwargs`][forms-sets], [`_default_get_form`][forms-sets], [`_build_and_stash_form_input`][forms-sets], [`_form_input_type_name_for`][forms-sets], [`bind_form_mutations`][forms-sets]
  - 4 [`DjangoModelFormMutation`][forms-sets] methods: [`DjangoModelFormMutation._resolve_model`][forms-sets], [`DjangoModelFormMutation._validate_meta`][forms-sets], [`DjangoModelFormMutation.build_input`][forms-sets], [`DjangoModelFormMutation.input_type_name`][forms-sets]
  - 5 [`DjangoFormMutation`][forms-sets] methods: [`DjangoFormMutation._validate_meta`][forms-sets], [`DjangoFormMutation.build_input`][forms-sets], [`DjangoFormMutation.perform_mutate`][forms-sets], [`DjangoFormMutation.check_permission`][forms-sets], [`DjangoFormMutation.input_type_name`][forms-sets]
- Verified reverse references across `django_strawberry_framework/forms/__init__.py`, `django_strawberry_framework/types/finalizer.py`, `tests/forms/test_sets.py`, and `tests/forms/test_resolvers.py`.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - **Mutation Declarative Surfaces:** The framework provides three write mutation flavors: model mutations ([`mutations/sets.py`][mutations-sets]), form mutations ([`forms/sets.py`][forms-sets]), and DRF serializer mutations ([`rest_framework/sets.py`][rest-framework-sets]).
   - **Shared Metaclass and Registry Factories:** `DjangoFormMutationMetaclass` and `_form_mutation_declaration_registry` are instantiated using single-sourced factories [`make_meta_validating_metaclass`][mutations-sets] and [`make_declaration_registry`][mutations-sets], ensuring identical registration, deduplication, and post-finalize rejection across subsystems.
   - **Shared Validation Primitives:** All write flavors leverage common validation helpers in [`django_strawberry_framework/mutations/sets.py`][mutations-sets]:
     - Typo checking via [`reject_unknown_meta_keys`][mutations-sets];
     - Subclass type checking via [`require_backing_class`][mutations-sets] and [`require_subclass`][mutations-sets];
     - Model validation via [`require_model_class`][mutations-sets] and [`resolve_backed_model_or_raise`][mutations-sets];
     - Operation validation via [`require_non_delete_operation`][mutations-sets] and [`NON_DELETE_OPERATION_INPUT_KIND`][mutations-sets];
     - Permission and lock normalization via [`model_backed_permission_and_lock`][mutations-sets] and [`_validate_permission_classes`][mutations-sets];
     - Field list normalization via [`normalize_meta_field_selection`][mutations-sets].
   - **Shared Input Materialization & Caching:** Shape cache creation uses [`make_shape_build_cache`][utils-inputs], input deduplication and guard ordering uses [`cached_build_input`][mutations-sets], and the materialize-and-stash workflow uses [`build_and_stash_input`][mutations-sets].
   - **Shared Finalizer Binding:** Both [`bind_mutations`][mutations-sets] and [`bind_form_mutations`][forms-sets] route through the shared binding loop [`bind_write_declarations`][mutations-sets].
   - **Shared Construction and Permission Primitives:** Constructor kwarg packaging is single-sourced in [`construction_kwargs`][mutations-sets], and permission checking delegates to [`run_permission_classes`][mutations-permissions].
2. **Sync and async twins:**
   - Zero duplication. Both `resolve_sync` and `resolve_async` resolver seams on [`DjangoModelFormMutation`][forms-sets] and [`DjangoFormMutation`][forms-sets] are generated via [`resolver_seams`][mutations-sets].
   - The generated resolver seams use function-local lazy imports of `django_strawberry_framework.forms.resolvers` (`resolve_form_sync` / `resolve_form_async`), preventing circular import dependencies at module load time.
   - `DjangoFormMutation` passes `with_id=False` to [`resolver_seams`][mutations-sets] to produce signatures matching model-less mutation requirements (`(info, *, data)` instead of `(info, id, *, data)`).
3. **Derived rather than repeated knowledge:**
   - **Model Resolution:** `DjangoModelFormMutation._resolve_model` dynamically inspects `Meta.form_class._meta.model` via [`resolve_meta_model`][mutations-sets].
   - **Field Discovery:** Form fields are dynamically introspected from `form_class` via [`get_form_fields`][forms-inputs] or custom `get_form_fields` hooks.
   - **Input Type Naming:** Generated `@strawberry.input` class names derive deterministically from `form_class.__name__` and the effective field set via [`form_input_type_name`][forms-inputs].
   - **Reverse-Map Specs:** Reverse field specifications (`_input_field_specs`) are derived during input generation in [`forms/inputs.py`][forms-inputs] and stashed on the mutation class during [`build_input`][forms-sets] for runtime consumption by resolvers.
   - **Cache Keys:** Form shape cache keys compose `(form_class, operation_kind, frozenset(effective), hook_identity)` dynamically.
4. **Inverse and round-trip pairs:**
   - **Meta Configuration <-> Input Shape Narrowing:**
     - Declarations `Meta.fields` / `Meta.exclude` validated in [`_normalized_form_field_selection`][forms-sets] are consumed and resolved by [`resolve_effective_form_fields`][forms-inputs].
   - **Input Build-and-Stash <-> Resolver Argument Decoding:**
     - [`_build_and_stash_form_input`][forms-sets] stashes `cls._input_field_specs` on the mutation class.
     - [`forms/resolvers.py`][forms-resolvers] consumes `mutation_cls._input_field_specs` to decode GraphQL input objects into form-ready `data=` and `files=` dictionaries.
   - **Constructor Kwarg Packaging <-> Form Construction:**
     - [`_default_get_form_kwargs`][forms-sets] bundles `{"data": data, "files": files, "instance": instance}`.
     - [`_default_get_form`][forms-sets] unbundles these kwargs via `form_class(**self.get_form_kwargs(...))`.
   - **Declaration Registration <-> Phase 2.5 Binding & Clear:**
     - Concrete `DjangoFormMutation` classes are registered in `_form_mutation_declaration_registry` during class definition.
     - [`bind_form_mutations`][forms-sets] drains the registry during schema finalization, and [`clear_form_mutation_registry`][forms-sets] co-clears the registry on test reset.
5. **Contracts restated in another medium:**
   - The form mutation declarative contract is codified across:
     - Production code: [`django_strawberry_framework/forms/sets.py`][forms-sets], [`django_strawberry_framework/forms/inputs.py`][forms-inputs], [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers], [`django_strawberry_framework/mutations/sets.py`][mutations-sets], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/registry.py`][registry];
     - Specifications: [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038] (Decisions 6, 7, 8, 10, 11, 13), [`docs/SPECS/spec-036-mutation_sets-0_0_11.md`][spec-036], [`docs/SPECS/spec-039-drf_serializer_mutations-0_0_13.md`][spec-039];
     - Test suites: [`tests/forms/test_sets.py`][test-forms-sets], [`tests/forms/test_inputs.py`][test-forms-inputs], [`tests/forms/test_resolvers.py`][test-forms-resolvers];
     - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Modifying the declaration registry lifecycle or deduplication rules):** Change registration deduplication, post-finalization lockouts, or iteration semantics across mutation declaration registries.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::make_declaration_registry`][mutations-sets].
  - *Site count:* 1.
- **Posited change 2 (Modifying Meta typo detection and reporting):** Alter how unknown `Meta` keys are computed and formatted across write mutation flavors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::reject_unknown_meta_keys`][mutations-sets].
  - *Site count:* 1.
- **Posited change 3 (Modifying non-delete operation validation or diagnostic messages):** Update error text or supported operation checking for create/update-only write flavors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::require_non_delete_operation`][mutations-sets] or [`django_strawberry_framework/mutations/sets.py::non_delete_operation_error`][mutations-sets].
  - *Site count:* 1.
- **Posited change 4 (Modifying default constructor kwargs packaging):** Alter how `data`, `files`, and `instance` are structured when passed to form or serializer constructors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::construction_kwargs`][mutations-sets].
  - *Site count:* 1.
- **Posited change 5 (Modifying the resolver seam generation factory):** Change the lazy import wrapper generation for `resolve_sync` and `resolve_async` seams across mutation bases.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::resolver_seams`][mutations-sets].
  - *Site count:* 1.
- **Posited change 6 (Modifying the phase-2.5 write declaration binding loop):** Alter the binding sequence, type resolution, or payload materialization across mutation declaration registries.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::bind_write_declarations`][mutations-sets].
  - *Site count:* 1.
- **Posited change 7 (Modifying the form input build-and-stash workflow):** Change how input classes are materialized and how reverse-map `_input_field_specs` are stashed on the mutation class.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::build_and_stash_input`][mutations-sets].
  - *Site count:* 1.
- **Posited change 8 (Modifying the permission execution walk on model-less forms):** Change how `check_permission` executes permission classes and guards against coroutine leaks in sync context.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/permissions.py::run_permission_classes`][mutations-permissions].
  - *Site count:* 1.
- **Posited change 9 (Modifying allowed Meta keys for DjangoModelFormMutation):** Add or remove a supported configuration option on `DjangoModelFormMutation.Meta`.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/forms/sets.py::_ALLOWED_MODELFORM_META_KEYS`][forms-sets].
  - *Site count:* 1.
- **Posited change 10 (Modifying allowed Meta keys for DjangoFormMutation):** Add or remove a supported configuration option on `DjangoFormMutation.Meta`.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/forms/sets.py::_ALLOWED_PLAIN_FORM_META_KEYS`][forms-sets].
  - *Site count:* 1.
- **Posited change 11 (Modifying the targeted ModelForm rejection diagnostic on DjangoFormMutation):** Update the error message when a `ModelForm` is passed to `DjangoFormMutation`.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/forms/sets.py::DjangoFormMutation._validate_meta`][forms-sets].
  - *Site count:* 1.

### Rejected candidates

1. **Merging `DjangoFormMutation` into `DjangoModelFormMutation` / `DjangoMutation`:**
   - Disproved per [spec-038][spec-038] Decision 6 & Decision 10. `DjangoFormMutation` represents a model-less write mutation (plain `forms.Form`). It has no associated Django ORM model, no `DjangoType` object slot, no model-derived permissions default, and no model operation. Forcing plain forms into `DjangoMutation` would require nullable model branches throughout `mutations/sets.py`, breaking the model-backed mutation contract.
2. **Merging form shape caching with model mutation input generation:**
   - Disproved per [spec-038][spec-038] Decision 7. Form inputs derive from `forms.Field` instances with distinct requiredness rules and reverse-map specs (`InputFieldSpec`), whereas model mutations derive from Django model fields and serializer mutations derive from DRF fields. However, the caching *plumbing* (`make_shape_build_cache` and `cached_build_input`) is already single-sourced.
3. **Unifying `get_form_kwargs` waiver with DRF serializer waiver:**
   - Disproved per [spec-038][spec-038] Decision 7 and [spec-039][spec-039] Decision 7. Forms waive the create-required narrowing guard when a consumer overrides `get_form_kwargs` / `get_form` (injecting external kwargs into form instantiation). Serializer mutations deliberately reject constructor-hook waivers and instead require explicit, auditable `Meta.injected_fields` declarations.

## Opportunities

None — `django_strawberry_framework/forms/sets.py` is a clean, 1014-line module. All reusable metaclass generation, declaration registry management, shape cache primitives, `Meta` validation rules, resolver seam generation, construction kwarg packaging, and phase-2.5 binding orchestration are consolidated at root owners in [`django_strawberry_framework/mutations/sets.py`][mutations-sets], [`django_strawberry_framework/forms/inputs.py`][forms-inputs], [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions], and [`django_strawberry_framework/utils/inputs.py`][utils-inputs]. Form-specific validation matrices and model-less plain form semantics are precisely bounded.

## Judgment

Zero-edit review. `django_strawberry_framework/forms/sets.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/forms/sets.py --review docs/dry/dry-file-forms__sets.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent review completed. Worker 1's findings are confirmed, all boundaries and equivalence claims were challenged and verified, and all 25 target definitions (constants, helper functions, and class methods) are fully accounted for.

### 1. Behavior Trace & Subsystem Boundaries Verification
- **Two-Flavor Mutation Base Architecture ([spec-038][spec-038] Decision 6):**
  - **`DjangoModelFormMutation`:** Correctly subclasses [`DjangoMutation`][mutations-sets] and overrides model resolution ([`DjangoModelFormMutation._resolve_model`][forms-sets] via [`resolve_meta_model`][mutations-sets]), class validation ([`DjangoModelFormMutation._validate_meta`][forms-sets]), input materialization ([`DjangoModelFormMutation.build_input`][forms-sets]), and input type naming ([`DjangoModelFormMutation.input_type_name`][forms-sets]). It rides [`DjangoMutationMetaclass`][mutations-sets], the shared mutation declaration registry, and [`bind_mutations`][mutations-sets] phase-2.5 binding, materializing model-backed `<Name>Payload` types with standard `node` / `result` slots.
  - **`DjangoFormMutation`:** Confirmed as an independent model-less base class (not subclassing `DjangoMutation`). It correctly mints its own metaclass ([`DjangoFormMutationMetaclass`][forms-sets] via [`make_meta_validating_metaclass`][mutations-sets]), uses its own dedicated registry ([`_form_mutation_declaration_registry`][forms-sets] via [`make_declaration_registry`][mutations-sets]), and is bound in Phase 2.5 via [`bind_form_mutations`][forms-sets] to emit pinned `{ ok errors }` payload types without model slots ([spec-038][spec-038] Decision 6 & 13).
- **Disjoint Meta Validation Matrices & Fail-Loud Diagnostics ([spec-038][spec-038] Decisions 6, 10, 11):**
  - **Plain Form Matrix (`DjangoFormMutation._validate_meta`):**
    - Key presence check `hasattr(meta, "operation")` rejects any declared or inherited `Meta.operation` upfront with a targeted diagnostic explaining that model-less form mutations have no model operation (spec-038 Decision 10).
    - Targeted diagnostic intercepts `issubclass(form_class, forms.ModelForm)` before generic `forms.Form` validation, cleanly directing developers to `DjangoModelFormMutation`.
    - Permission classes default to `(DenyAll,)` via [`_validate_permission_classes`][mutations-sets] unless explicitly opted out with `[]` ([spec-038][spec-038] Decision 11). Any subclass of [`DjangoModelPermission`][mutations-permissions] is caught at class creation time and rejected fail-loud.
  - **ModelForm Matrix (`DjangoModelFormMutation._validate_meta`):**
    - Restricts `Meta.operation` strictly to `{"create", "update"}` via [`require_non_delete_operation`][mutations-sets].
    - Validates `form_class` via [`require_backing_class`][mutations-sets] and [`require_subclass`][mutations-sets] for `forms.ModelForm`.
    - Validates model class via [`require_model_class`][mutations-sets] and [`resolve_backed_model_or_raise`][mutations-sets].
    - Normalizes permissions and `select_for_update` locking via [`model_backed_permission_and_lock`][mutations-sets].
- **Input Generation, Caching & Reverse Mapping ([spec-038][spec-038] Decisions 7, 8):**
  - **Shape Cache Isolation:** [`_form_shape_build_cache`][forms-sets] is built using [`make_shape_build_cache`][utils-inputs] and registered with [`register_subsystem_clear`][registry]. Cache keys incorporate `(form_class, operation_kind, frozenset(effective), hook_identity)`.
  - **Guard-Before-Cache Ordering:** [`_cached_build_form_input`][forms-sets] executes [`guard_create_required_fields`][forms-inputs] (or [`guard_partial_required_column_less_fields`][forms-inputs]) per-declaration before performing cache lookup, ensuring a waiving declaration never bypasses required field validation for subsequent non-waiving declarations sharing the same shape.
  - **Reverse Map Stashing:** Reverse field specifications (`InputFieldSpec`) survive cache deduplication and are stashed on `cls._input_field_specs` via [`build_and_stash_input`][mutations-sets] for resolver argument decoding.
- **Construction Hooks & Waiver Mechanics ([spec-038][spec-038] Decision 7, 8):**
  - Confirmed [`_default_get_form_kwargs`][forms-sets] routes through [`construction_kwargs`][mutations-sets], packaging `{"data": data, "files": files, "instance": instance}`.
  - Confirmed [`_form_kwargs_overridden`][forms-sets] detects overrides on `get_form_kwargs` or `get_form` using [`_hook_overridden`][mutations-sets] and waives the create-required narrowing guard.
- **Seam Synthesis & Zero Load-Time Cycles:**
  - Resolver seams `resolve_sync` and `resolve_async` on both bases are minted via [`resolver_seams`][mutations-sets], using function-local lazy imports of [`forms/resolvers.py`][forms-resolvers] (`resolve_form_sync` and `resolve_form_async`) to keep `forms/sets.py` free of circular load-time dependencies.

### 2. Probing Matrix & Single-Edit-Site Verification
- **5-Axis Probing Matrix:** All 5 axes verified and discharged (Cross-flavor policy mirroring across mutation flavors, Sync/async resolver generation, Derived knowledge across forms/inputs/resolvers, Inverse/round-trip pairs across declaration-to-runtime pipelines, and Multi-medium contract consistency).
- **Single-Edit-Site Counts:** All 11 posited changes verified to have exact site counts of 1 at their designated root owners.

### 3. Automated Validation & Test Suite
- Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/forms/sets.py --review docs/dry/dry-file-forms__sets.md --include-constants`: confirmed 25 target definitions covered with 0 errors.
- Ran test suite `uv run pytest tests/forms/ -v`: all 221 tests passed cleanly.

Status updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutation_sets-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-drf_serializer_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-framework-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rest-framework-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rest-framework-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[scalars]: ../../django_strawberry_framework/scalars.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py
[utils-errors]: ../../django_strawberry_framework/utils/errors.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py
[utils-write-transaction]: ../../django_strawberry_framework/utils/write_transaction.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-forms-converter]: ../../tests/forms/test_converter.py
[test-forms-inputs]: ../../tests/forms/test_inputs.py
[test-forms-resolvers]: ../../tests/forms/test_resolvers.py
[test-forms-sets]: ../../tests/forms/test_sets.py
[test-mutations-inputs]: ../../tests/mutations/test_inputs.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
