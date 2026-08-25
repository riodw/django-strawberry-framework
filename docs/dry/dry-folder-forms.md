# DRY review: `django_strawberry_framework/forms/`

Status: verified

## System trace

`django_strawberry_framework/forms/` is the declarative Django `Form` and `ModelForm` write mutation subsystem ([spec-038][spec-038]). It provides GraphQL mutation base classes, form field type conversion, automatic `@strawberry.input` dataclass generation, reverse-mapped input decoding, and synchronous/asynchronous execution pipelines for Django forms.

The subpackage implements a layered write pipeline partitioned across five modules:

1. [`forms/__init__.py`][forms-init]: The public subpackage export facade:
   - **Public Export Surface:** Re-exports the declarative mutation base classes [`DjangoFormMutation`][forms-sets] (for plain, model-less `django.forms.Form` mutations) and [`DjangoModelFormMutation`][forms-sets] (for `django.forms.ModelForm` mutations) in [`__all__`][forms-init] ([spec-038][spec-038] Decisions 1, 2, 4).
   - **Package Root Re-Export:** Both mutation base classes are re-exported at the package root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] and included in the top-level `__all__`.
   - **Encapsulation:** Compiler internals (conversion registry, input materializers, namespace lifecycle hooks, and resolver execution pipelines) are strictly encapsulated and deliberately excluded from [`__all__`][forms-init] per [spec-038][spec-038] Decision 4.

2. [`forms/converter.py`][forms-converter]: Model-less form field conversion registry and decode kind constants:
   - **Value Object & Requiredness:** Defines [`FormFieldConversion`][forms-converter] (subclassing [`FieldConversionBase`][utils-inputs]) carrying the resolved `(annotation, kind, required)` triple, and [`form_field_required`][forms-converter] as the single authority for form field requiredness (handling `forms.NullBooleanField` requiredness rules).
   - **Converter Factories:** [`_scalar_converter`][forms-converter] (wrapping [`make_scalar_converter`][utils-converters]), [`_kind_converter`][forms-converter] (wrapping [`make_kind_converter`][utils-converters]), and [`_null_boolean_converter`][forms-converter] for specialized boolean handling.
   - **Scalar Registry & Prechecks:** Static scalar mapping dictionary [`_SCALAR_FORM_FIELDS`][forms-converter] binding supported `forms.Field` classes, exact-type handler [`_bare_form_field`][forms-converter] returning [`MRO_CONTINUE`][utils-converters] for subclasses, and kind converter constants [`_CONVERT_RELATION_MULTI`][forms-converter], [`_CONVERT_RELATION_SINGLE`][forms-converter], [`_CONVERT_FILE`][forms-converter], and [`_CONVERT_MULTIPLE_CHOICE`][forms-converter].
   - **MRO Conversion Dispatch & Fail-Loud Error:** [`convert_form_field`][forms-converter] executing the shared [`convert_with_mro`][utils-converters] engine and [`finish_field_conversion`][utils-converters] over ordered prechecks (`ModelMultipleChoiceField`, `ModelChoiceField`, `FileField`, `MultipleChoiceField`, bare `forms.Field`), the scalar table walk, and the raising fallthrough [`_unsupported_form_field`][forms-converter] (which constructs a fail-loud [`ConfigurationError`][exceptions] via [`_safe_type_name`][exceptions] and [`_safe_arg_repr`][exceptions]).
   - **Re-Exported Decode Kinds:** Re-exports [`SCALAR`][forms-converter], [`RELATION_SINGLE`][forms-converter], [`RELATION_MULTI`][forms-converter], and [`FILE`][forms-converter] from [`django_strawberry_framework/utils/inputs.py`][utils-inputs].

3. [`forms/inputs.py`][forms-inputs]: Strawberry input dataclass generation and namespace lifecycle:
   - **Namespace Scaffolding & Operation Kinds:** Pinned namespace constant [`INPUTS_MODULE_PATH`][forms-inputs] (`"django_strawberry_framework.forms.inputs"`), fixed model-less operation sentinel [`FORM`][forms-inputs] (`"form"`), and create-shaped kind group [`CREATE_SHAPED_KINDS`][forms-inputs] (`frozenset({CREATE, FORM})`).
   - **Namespace Lifecycle:** Input materialization via [`materialize_form_input_class`][forms-inputs] (powered by [`make_input_namespace`][utils-inputs]) and [`clear_form_input_namespace`][forms-inputs] registered with [`register_subsystem_clear`][registry] (`owner="forms.input_namespace"`, `before_bind=True`).
   - **Field Discovery & Basis Normalization:** [`get_form_fields`][forms-inputs] reading declared `form_class.base_fields` without instantiating the form, [`_form_field_basis`][forms-inputs] validating dictionary mappings, and [`normalize_form_field_basis`][forms-inputs] validating mutation hook returns.
   - **Field Narrowing & Input Naming:** [`resolve_effective_form_fields`][forms-inputs] delegating to [`resolve_effective_fields`][utils-inputs], and [`form_input_type_name`][forms-inputs] delegating to [`name_set_input_type_name`][utils-inputs] (`<FormClass>Input`, `<FormClass>PartialInput`, or deterministic shape tokens).
   - **Field Resolution & Model Separation:** [`_model_column_for`][forms-inputs] resolving backing model columns (excluding reverse relations, `GenericForeignKey`, `GenericRelation`), [`_model_less_relation_annotation`][forms-inputs] mapping column-less relations via [`annotate_queryset_relation`][mutations-inputs], [`_simple_triple`][forms-inputs] formatting field tuples, and [`_field_triple_and_spec`][forms-inputs] resolving `(python_attr, base_annotation, InputFieldSpec, required)` using [`model_column_input_annotation`][mutations-inputs] and [`convert_form_field`][forms-converter].
   - **Collision Guards & Dataclass Builders:** [`_guard_input_attr_collisions`][forms-inputs] using [`iter_input_field_collisions`][utils-inputs], [`build_form_input_class`][forms-inputs] using [`optional_input_field`][utils-inputs] and [`build_strawberry_input_class`][utils-inputs], [`_required_form_field_names`][forms-inputs] computing required field sets, [`guard_create_required_fields`][forms-inputs] and [`guard_partial_required_column_less_fields`][forms-inputs] delegating to [`guard_dropped_required`][utils-inputs], and public builder [`build_form_inputs`][forms-inputs] creating create/partial input class pairs.

4. [`forms/resolvers.py`][forms-resolvers]: Sync and async form mutation execution pipeline:
   - **Recourse & Value Formatting:** Async recourse diagnostic [`_FORM_ASYNC_RECOURSE`][forms-resolvers] generated via [`sync_pipeline_recourse`][utils-querysets], [`_to_form_key_value`][forms-resolvers] extracting `to_field_name` serializable values or primary keys, and [`_is_empty_form_value`][forms-resolvers] checking `field.empty_values`.
   - **Relation Decoding:** [`_decode_form_relation_single`][forms-resolvers] decoding single relation IDs via [`decode_visible_relation`][utils-write-values] and [`_decode_form_relation_multi`][forms-resolvers] decoding relation ID lists.
   - **Form Data Decoding & Partial Reconstruction:** [`_decode_form_data`][forms-resolvers] unpacking arguments into separate `provided_data` and `provided_files` dictionaries via [`decode_field_handlers`][utils-write-values] and [`decode_provided_fields`][utils-write-values], and [`_reconstruct_partial_data`][forms-resolvers] synthesizing full bound datasets for partial `ModelForm` updates from database instances.
   - **Form Validation & Error Mapping:** [`_bound_form_or_field_errors`][forms-resolvers] instantiating forms and running `is_valid()`, and [`_form_errors_to_field_errors`][forms-resolvers] converting `form.errors.as_data()` via [`validation_error_to_field_errors`][utils-errors].
   - **Write Steps & Execution Pipeline:** [`_modelform_decode_step`][forms-resolvers] combining decoding and partial reconstruction, [`_modelform_write_step`][forms-resolvers] executing `form.save()` wrapped in [`pipeline_write_phase`][utils-write-transaction] and [`save_or_field_errors`][mutations-resolvers], [`_plain_form_write_step`][forms-resolvers] executing `holder.perform_mutate(form, info)` wrapped in [`save_or_field_errors`][mutations-resolvers], [`_run_form_pipeline_sync`][forms-resolvers] orchestrating the pipeline via [`run_write_pipeline_sync`][mutations-resolvers], and public entry points [`resolve_form_sync`][forms-resolvers] and [`resolve_form_async`][forms-resolvers] generated via [`make_resolver_entries`][mutations-resolvers].

5. [`forms/sets.py`][forms-sets]: Declarative mutation bases, `Meta` validation, form declaration registries, input materialization, and phase-2.5 schema binding:
   - **Meta Key Configurations:** Allowed key sets [`_ALLOWED_MODELFORM_META_KEYS`][forms-sets] (`form_class`, `operation`, `fields`, `exclude`, `permission_classes`, `select_for_update`) and [`_ALLOWED_PLAIN_FORM_META_KEYS`][forms-sets] (`form_class`, `fields`, `exclude`, `permission_classes`).
   - **Declaration Registry & Shape Build Cache:** Model-less registry `_form_mutation_declaration_registry` instantiated via [`make_declaration_registry`][mutations-sets], exporting `register_form_mutation`, `clear_form_mutation_registry`, `iter_form_mutations`, and backing store `_form_mutation_registry` (registered with [`register_subsystem_clear`][registry], `owner="forms.declarations"`). Per-pass shape build cache `_form_shape_build_cache` and `clear_form_shape_build_cache` created via [`make_shape_build_cache`][utils-inputs] (registered with [`register_subsystem_clear`][registry], `owner="forms.shape_cache"`).
   - **Field Discovery & Caching Hooks:** [`_default_mutation_get_form_fields`][forms-sets], [`_mutation_form_fields`][forms-sets], and [`_form_input_hook_identity`][forms-sets] resolving field bases and cache discriminators.
   - **Input Caching & Narrowing:** [`_resolve_effective_form_field_names`][forms-sets] resolving field names, [`_normalized_form_field_selection`][forms-sets] normalizing declarations via [`normalize_meta_field_selection`][mutations-sets], [`_form_kwargs_overridden`][forms-sets] detecting `get_form_kwargs` / `get_form` overrides via [`_hook_overridden`][mutations-sets], [`_cached_build_form_input`][forms-sets] executing [`cached_build_input`][mutations-sets] with per-declaration guards before per-shape cache lookups, [`_build_and_stash_form_input`][forms-sets] executing [`build_and_stash_input`][mutations-sets] with [`materialize_form_input_class`][forms-inputs], and [`_form_input_type_name_for`][forms-sets] deriving names via [`form_input_type_name`][forms-inputs].
   - **Default Construction Hooks:** [`_default_get_form_kwargs`][forms-sets] delegating to [`construction_kwargs`][mutations-sets], and [`_default_get_form`][forms-sets] calling `form_class(**self.get_form_kwargs(...))`.
   - **ModelForm Mutation Base ([`DjangoModelFormMutation`][forms-sets]):** Subclasses [`DjangoMutation`][mutations-sets], overriding [`DjangoModelFormMutation._resolve_model`][forms-sets] (via [`resolve_meta_model`][mutations-sets]), [`DjangoModelFormMutation._validate_meta`][forms-sets] (using [`reject_unknown_meta_keys`][mutations-sets], [`require_backing_class`][mutations-sets], [`require_subclass`][mutations-sets], [`require_model_class`][mutations-sets], [`resolve_backed_model_or_raise`][mutations-sets], [`require_non_delete_operation`][mutations-sets], [`model_backed_permission_and_lock`][mutations-sets]), [`DjangoModelFormMutation.build_input`][forms-sets], [`DjangoModelFormMutation.input_type_name`][forms-sets], class attributes [`DjangoModelFormMutation.get_form_fields`][forms-sets], [`DjangoModelFormMutation.input_module_path`][forms-sets], [`DjangoModelFormMutation._input_field_specs`][forms-sets], [`DjangoModelFormMutation.get_form_kwargs`][forms-sets], [`DjangoModelFormMutation.get_form`][forms-sets], and resolver seams [`DjangoModelFormMutation.resolve_sync`][forms-sets] / [`DjangoModelFormMutation.resolve_async`][forms-sets] generated via [`resolver_seams`][mutations-sets].
   - **Plain Form Mutation Base ([`DjangoFormMutation`][forms-sets]):** Model-less mutation base with metaclass [`DjangoFormMutationMetaclass`][forms-sets] (minted via [`make_meta_validating_metaclass`][mutations-sets]), stashing [`DjangoFormMutation._mutation_meta`][forms-sets], [`DjangoFormMutation._primary_type`][forms-sets] (`None`), [`DjangoFormMutation._input_class`][forms-sets], [`DjangoFormMutation._payload_type_name`][forms-sets], [`DjangoFormMutation._input_field_specs`][forms-sets], and [`DjangoFormMutation.input_module_path`][forms-sets]. Overrides [`DjangoFormMutation._validate_meta`][forms-sets] (rejecting `Meta.operation`, enforcing `forms.Form`, rejecting `ModelForm` with targeted redirect, requiring non-model permissions via [`_validate_permission_classes`][mutations-sets] with [`DenyAll`][mutations-permissions] default, rejecting [`DjangoModelPermission`][mutations-permissions]), [`DjangoFormMutation.build_input`][forms-sets], [`DjangoFormMutation.perform_mutate`][forms-sets] (invoking `form.save()` if present), [`DjangoFormMutation.check_permission`][forms-sets] (delegating to [`run_permission_classes`][mutations-permissions]), [`DjangoFormMutation.input_type_name`][forms-sets], class attributes [`DjangoFormMutation.get_form_fields`][forms-sets], [`DjangoFormMutation.get_form_kwargs`][forms-sets], [`DjangoFormMutation.get_form`][forms-sets], and resolver seams [`DjangoFormMutation.resolve_sync`][forms-sets] / [`DjangoFormMutation.resolve_async`][forms-sets] generated via [`resolver_seams`][mutations-sets] with `with_id=False`.
   - **Phase-2.5 Schema Binding:** [`bind_form_mutations`][forms-sets] called during finalization in [`django_strawberry_framework/types/finalizer.py`][types-finalizer], executing [`bind_write_declarations`][mutations-sets] over `iter_form_mutations` to materialize inputs into `django_strawberry_framework.forms.inputs` and mint pinned `{ ok errors }` payload types.

Connected behavior examined:
- [`django_strawberry_framework/mutations/sets.py`][mutations-sets]: Base mutation primitives, declaration registries, shape caches, and `bind_write_declarations`.
- [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs]: Mutation input generator and relation annotation helpers (`annotate_queryset_relation`, `model_column_input_annotation`, `model_column_write_kind`, `CREATE`, `PARTIAL`).
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Shared write pipeline runner `run_write_pipeline_sync`, entry factory `make_resolver_entries`, and save wrapper `save_or_field_errors`.
- [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions]: Permission classes `DjangoModelPermission`, `DenyAll`, and permission runner `run_permission_classes`.
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Canonical root owner of `InputFieldSpec`, `FieldConversionBase`, `build_strawberry_input_class`, `guard_dropped_required`, `iter_input_field_collisions`, `make_input_namespace`, `make_shape_build_cache`, `name_set_input_type_name`, `optional_input_field`, and `resolve_effective_fields`.
- [`django_strawberry_framework/utils/converters.py`][utils-converters]: Shared MRO conversion dispatch engine (`convert_with_mro`, `finish_field_conversion`, `make_kind_converter`, `make_scalar_converter`, `MRO_CONTINUE`).
- [`django_strawberry_framework/utils/write_values.py`][utils-write-values]: Flavor-neutral argument decoding primitives (`decode_provided_fields`, `decode_field_handlers`, `decode_visible_relation`, `decode_scalar_leaf`).
- [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction]: Database alias isolation and `pipeline_write_phase` context manager.
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: Relation visibility helpers (`visible_related_object`, `visible_related_objects`, `sync_pipeline_recourse`).
- [`django_strawberry_framework/utils/errors.py`][utils-errors]: Error mapping helpers (`validation_error_to_field_errors`).
- [`django_strawberry_framework/types/converters.py`][types-converters]: Read-side model field converters (`convert_scalar`, `convert_choices_to_enum`).
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Phase 2.5 schema finalizer executing `bind_mutations` and `bind_form_mutations`.
- [`django_strawberry_framework/registry.py`][registry]: Global registry maintaining subsystem lifecycle clearing hooks (`register_subsystem_clear`).
- Test suites: [`tests/forms/test_converter.py`][test-forms-converter], [`tests/forms/test_inputs.py`][test-forms-inputs], [`tests/forms/test_resolvers.py`][test-forms-resolvers], [`tests/forms/test_sets.py`][test-forms-sets], [`tests/base/test_init.py`][test-base-init].

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/forms/ --review docs/dry/dry-folder-forms.md --include-constants`):
- Parsed 5 target files (`__init__.py`, `converter.py`, `inputs.py`, `resolvers.py`, `sets.py`), 2,715 total lines.
- Inventoried 71 definitions and module constants across the subpackage:
  - `forms/__init__.py`: 1 constant ([`__all__`][forms-init]), 2 re-exports ([`DjangoFormMutation`][forms-sets], [`DjangoModelFormMutation`][forms-sets]);
  - `forms/converter.py`: 13 definitions/constants ([`FormFieldConversion`][forms-converter], [`form_field_required`][forms-converter], [`_null_boolean_converter`][forms-converter], [`_scalar_converter`][forms-converter], [`_kind_converter`][forms-converter], [`_SCALAR_FORM_FIELDS`][forms-converter], [`_bare_form_field`][forms-converter], [`_CONVERT_RELATION_MULTI`][forms-converter], [`_CONVERT_RELATION_SINGLE`][forms-converter], [`_CONVERT_FILE`][forms-converter], [`_CONVERT_MULTIPLE_CHOICE`][forms-converter], [`convert_form_field`][forms-converter], [`_unsupported_form_field`][forms-converter]);
  - `forms/inputs.py`: 18 definitions/constants ([`INPUTS_MODULE_PATH`][forms-inputs], [`FORM`][forms-inputs], [`CREATE_SHAPED_KINDS`][forms-inputs], [`materialize_form_input_class`][forms-inputs], [`clear_form_input_namespace`][forms-inputs], [`get_form_fields`][forms-inputs], [`_form_field_basis`][forms-inputs], [`normalize_form_field_basis`][forms-inputs], [`resolve_effective_form_fields`][forms-inputs], [`form_input_type_name`][forms-inputs], [`_model_column_for`][forms-inputs], [`_model_less_relation_annotation`][forms-inputs], [`_simple_triple`][forms-inputs], [`_field_triple_and_spec`][forms-inputs], [`_guard_input_attr_collisions`][forms-inputs], [`build_form_input_class`][forms-inputs], [`_required_form_field_names`][forms-inputs], [`guard_create_required_fields`][forms-inputs], [`guard_partial_required_column_less_fields`][forms-inputs], [`build_form_inputs`][forms-inputs]);
  - `forms/resolvers.py`: 15 definitions/constants ([`_FORM_ASYNC_RECOURSE`][forms-resolvers], [`_to_form_key_value`][forms-resolvers], [`_is_empty_form_value`][forms-resolvers], [`_decode_form_relation_single`][forms-resolvers], [`_decode_form_relation_multi`][forms-resolvers], [`_decode_form_data`][forms-resolvers], [`_reconstruct_partial_data`][forms-resolvers], [`_form_errors_to_field_errors`][forms-resolvers], [`_modelform_decode_step`][forms-resolvers], [`_bound_form_or_field_errors`][forms-resolvers], [`_modelform_write_step`][forms-resolvers], [`_plain_form_write_step`][forms-resolvers], [`_run_form_pipeline_sync`][forms-resolvers], [`resolve_form_sync`][forms-resolvers], [`resolve_form_async`][forms-resolvers]);
  - `forms/sets.py`: 23 definitions/constants ([`_ALLOWED_MODELFORM_META_KEYS`][forms-sets], [`_ALLOWED_PLAIN_FORM_META_KEYS`][forms-sets], [`_default_mutation_get_form_fields`][forms-sets], [`_mutation_form_fields`][forms-sets], [`_form_input_hook_identity`][forms-sets], [`_cached_build_form_input`][forms-sets], [`_resolve_effective_form_field_names`][forms-sets], [`_normalized_form_field_selection`][forms-sets], [`_form_kwargs_overridden`][forms-sets], [`_default_get_form_kwargs`][forms-sets], [`_default_get_form`][forms-sets], [`_build_and_stash_form_input`][forms-sets], [`_form_input_type_name_for`][forms-sets], [`DjangoModelFormMutation`][forms-sets], [`DjangoModelFormMutation._resolve_model`][forms-sets], [`DjangoModelFormMutation._validate_meta`][forms-sets], [`DjangoModelFormMutation.build_input`][forms-sets], [`DjangoModelFormMutation.input_type_name`][forms-sets], [`DjangoFormMutation`][forms-sets], [`DjangoFormMutation._validate_meta`][forms-sets], [`DjangoFormMutation.build_input`][forms-sets], [`DjangoFormMutation.perform_mutate`][forms-sets], [`DjangoFormMutation.check_permission`][forms-sets], [`DjangoFormMutation.input_type_name`][forms-sets], [`bind_form_mutations`][forms-sets]).
- Confirmed zero missing definitions across all five files.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - **Write Subsystem Symmetry:** The framework provides three write mutation flavors: model mutations ([`mutations/`][mutations-sets]), form mutations ([`forms/`][forms-sets]), and DRF serializer mutations ([`rest_framework/`][rest-framework-sets]).
   - **Unified Metaclass & Registry Infrastructure:** `DjangoFormMutationMetaclass` and `_form_mutation_declaration_registry` are constructed using single-sourced factories [`make_meta_validating_metaclass`][mutations-sets] and [`make_declaration_registry`][mutations-sets] from `mutations/sets.py`, ensuring identical registration deduplication, post-finalization lockouts, and clear mechanics across subsystems.
   - **Unified Input Generation Primitives:** All write flavors leverage canonical primitives in [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: namespace management ([`make_input_namespace`][utils-inputs]), input dataclass construction ([`build_strawberry_input_class`][utils-inputs]), field narrowing ([`resolve_effective_fields`][utils-inputs]), required field drop guards ([`guard_dropped_required`][utils-inputs]), attribute/wire collision auditing ([`iter_input_field_collisions`][utils-inputs]), optional field widening ([`optional_input_field`][utils-inputs]), shape build caching ([`make_shape_build_cache`][utils-inputs]), and reverse map records ([`InputFieldSpec`][utils-inputs]).
   - **Unified MRO Conversion Dispatch:** Both form converters ([`forms/converter.py`][forms-converter]) and serializer converters ([`rest_framework/serializer_converter.py`][rest-framework-serializer-converter]) share the MRO dispatch skeleton in [`django_strawberry_framework/utils/converters.py`][utils-converters] ([`convert_with_mro`][utils-converters], [`finish_field_conversion`][utils-converters], [`make_scalar_converter`][utils-converters], [`make_kind_converter`][utils-converters]).
   - **Unified Execution Runtime:** Form mutations share the promoted write pipeline runner [`mutations/resolvers.py::run_write_pipeline_sync`][mutations-resolvers], resolver pair factory [`make_resolver_entries`][mutations-resolvers], save exception wrapper [`save_or_field_errors`][mutations-resolvers], transactional isolation [`pipeline_write_phase`][utils-write-transaction], and value decoding utilities in [`django_strawberry_framework/utils/write_values.py`][utils-write-values].
   - **Strict Key Space & Contract Separation:** `forms.Field`, `serializers.Field`, and `models.Field` hierarchies remain cleanly partitioned. When a `ModelForm` field has a backing model column, [`forms/inputs.py`][forms-inputs] routes resolution through [`model_column_input_annotation`][mutations-inputs] and [`convert_choices_to_enum`][types-converters], guaranteeing symmetric wire contracts with read-side `DjangoType` outputs, while column-less fields route to [`convert_form_field`][forms-converter].
2. **Sync and async twins:**
   - **Zero Logic Duplication:** Both synchronous ([`resolve_form_sync`][forms-resolvers]) and asynchronous ([`resolve_form_async`][forms-resolvers]) entry points are generated simultaneously via [`make_resolver_entries(_run_form_pipeline_sync)`][mutations-resolvers].
   - **Single Sync Execution Body:** The entire mutation pipeline executes synchronously within a single `transaction.atomic()` transaction. On async resolvers, `resolve_form_async` executes this pipeline inside a single `sync_to_async(thread_sensitive=True)` worker call, preventing interleaved async coroutines during ORM writes.
   - **Resolver Seams Generation:** Resolver seams on [`DjangoModelFormMutation`][forms-sets] and [`DjangoFormMutation`][forms-sets] are generated via [`resolver_seams`][mutations-sets] using function-local imports to prevent circular load-time dependencies.
3. **Derived rather than repeated knowledge:**
   - **Declared Field Discovery:** [`get_form_fields`][forms-inputs] discovers fields directly from `form_class.base_fields` without instantiating the form, ensuring deterministic, request-independent schema representation.
   - **Input Type Naming:** Generated input class names derive deterministically via [`form_input_type_name`][forms-inputs] (using [`name_set_input_type_name`][utils-inputs]).
   - **Requiredness Authority:** Form field requiredness derives from [`form_field_required`][forms-converter] across both column-backed and column-less paths.
   - **Reverse-Map Specs:** Derived during input compilation in [`forms/inputs.py`][forms-inputs], stashed on `cls._input_field_specs` in [`forms/sets.py`][forms-sets], and consumed by [`forms/resolvers.py`][forms-resolvers] for argument decoding.
   - **Error Extraction:** [`_form_errors_to_field_errors`][forms-resolvers] extracts `form.errors.as_data()` and delegates to [`validation_error_to_field_errors`][utils-errors], deriving standard field paths and mapping non-field errors to `"__all__"` without duplicate formatting logic.
4. **Inverse and round-trip pairs:**
   - **Input Compilation <-> Resolver Argument Decoding:**
     - [`forms/inputs.py`][forms-inputs] categorizes fields into decode kinds ([`SCALAR`][forms-converter], [`RELATION_SINGLE`][forms-converter], [`RELATION_MULTI`][forms-converter], [`FILE`][forms-converter]) and emits [`InputFieldSpec`][utils-inputs] records.
     - [`forms/resolvers.py`][forms-resolvers] unpacks GraphQL arguments against these specs, reconstructing `form.data` and `form.files`.
   - **Relation Key Projection <-> Form Field Parsing:**
     - [`_to_form_key_value`][forms-resolvers] projects resolved relation instances to `obj.serializable_value(to_field_name)` or `obj.pk`.
     - Django's `ModelChoiceField.to_python` receives this exact form key and loads the related instance.
   - **Declaration Registration <-> Phase 2.5 Binding & Clear:**
     - Concrete `DjangoFormMutation` classes register in `_form_mutation_declaration_registry`.
     - [`bind_form_mutations`][forms-sets] drains the registry during schema finalization, and [`clear_form_mutation_registry`][forms-sets] co-clears the registry on test reset.
   - **Namespace Lifecycle:** [`materialize_form_input_class`][forms-inputs] parks class objects in `forms.inputs` module globals, and [`clear_form_input_namespace`][forms-inputs] resets the internal ledger on `registry.clear()` while preserving parked classes for lazy reference safety.
5. **Contracts restated in another medium:**
   - The form mutation contracts are codified and verified across:
     - Specifications: [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038] (Decisions 1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 13), [`docs/SPECS/spec-036-mutation_sets-0_0_11.md`][spec-036], [`docs/SPECS/spec-039-drf_serializer_mutations-0_0_13.md`][spec-039];
     - Production code: [`django_strawberry_framework/forms/`][forms-init], [`django_strawberry_framework/mutations/`][mutations-sets], [`django_strawberry_framework/utils/`][utils-inputs], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/registry.py`][registry];
     - Comprehensive test suites: [`tests/forms/test_converter.py`][test-forms-converter], [`tests/forms/test_inputs.py`][test-forms-inputs], [`tests/forms/test_resolvers.py`][test-forms-resolvers], [`tests/forms/test_sets.py`][test-forms-sets], [`tests/base/test_init.py`][test-base-init];
     - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Supporting a new Django built-in form field, e.g. `forms.ComboField` -> `str`):** Add `forms.ComboField` to the scalar table.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/forms/converter.py`][forms-converter] in [`_SCALAR_FORM_FIELDS`][forms-converter].
  - *Site count:* 1.
- **Posited change 2 (Modifying form field requiredness rules, e.g. updating `NullBooleanField` policy):** Update the requiredness predicate.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/forms/converter.py`][forms-converter] in [`form_field_required`][forms-converter]. Both `convert_form_field` and `forms/inputs.py` immediately reflect the change.
  - *Site count:* 1.
- **Posited change 3 (Modifying MRO dispatch or converter factories across all write flavors):** Enhance or alter the fail-loud dispatch algorithm.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/converters.py`][utils-converters] in [`convert_with_mro`][utils-converters].
  - *Site count:* 1.
- **Posited change 4 (Altering required-field drop detection logic across write flavors):** Modify how dropped required fields are computed when applying `Meta.fields` / `Meta.exclude`.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py::guard_dropped_required`][utils-inputs]. Both form and serializer create/partial guards immediately inherit the change.
  - *Site count:* 1.
- **Posited change 5 (Modifying the declaration registry lifecycle or deduplication rules):** Change registration deduplication or post-finalization lockouts across mutation declaration registries.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py::make_declaration_registry`][mutations-sets].
  - *Site count:* 1.
- **Posited change 6 (Altering write pipeline orchestration, transaction isolation, or error handling):** Update transaction management or error catching across all write flavors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`][mutations-resolvers].
  - *Site count:* 1.
- **Posited change 7 (Adding a new public form mutation base, e.g. `DjangoWizardFormMutation`):** Introduce a new form-driven mutation base class.
  - *Sites that must move:* Exactly 2 sites: [`django_strawberry_framework/forms/sets.py`][forms-sets] (definition) and [`django_strawberry_framework/forms/__init__.py`][forms-init] (public export).
  - *Site count:* 2.

### Rejected candidates

1. **Merging `forms/converter.py` with `types/converters.py::SCALAR_MAP` or DRF `_SERIALIZER_FIELD_CONVERTERS`:**
   - Disproved per [spec-038][spec-038] Decision 7 and [spec-039][spec-039] Decision 4. `django.forms.Field`, `rest_framework.serializers.Field`, and `django.db.models.Field` are completely distinct type hierarchies with unique inheritance chains and validation lifecycles. Merging them into a single polymorphic registry would introduce accidental cross-subsystem coupling, obscure ownership, and risk silent mis-mappings.
2. **Merging `DjangoFormMutation` and `DjangoModelFormMutation` into a single unified class:**
   - Disproved per [spec-038][spec-038] Decision 6. Model-backed mutations require model resolution, model permissions, instance resolution, `form.save()` lifecycles, and model-typed return payloads (`{ ok, errors, node }`), while plain form mutations are strictly model-less, requiring deny-by-default permissions, custom `perform_mutate` hooks, and pinned `{ ok, errors }` payloads. Splitting them into distinct bases preserves strict type safety, eliminates confusing runtime branching, and prevents model-less mutations from accidentally invoking model methods.
3. **Inlining MRO dispatch, input dataclass construction, or write pipeline orchestration in `forms/`:**
   - Disproved per [spec-038][spec-038] and [spec-039][spec-039]. Dispatch control flow is single-sited in `utils/converters.py`, input primitives are single-sited in `utils/inputs.py`, and write execution is single-sited in `mutations/resolvers.py`.

## Opportunities

None — The folder integration of `django_strawberry_framework/forms/` is architecturally clean, robustly tested, and fully consolidated at root owners. Cross-module boundaries between `__init__.py`, `converter.py`, `inputs.py`, `resolvers.py`, and `sets.py`, as well as integration boundaries with `mutations/`, `utils/inputs.py`, `utils/converters.py`, `utils/write_values.py`, `types/converters.py`, `types/finalizer.py`, and `registry.py`, are strictly partitioned and honor all repository laws.

## Judgment

Zero-edit review. The `django_strawberry_framework/forms/` subpackage contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged across the subpackage boundary. Single-edit-site counts are 1 across all posited changes (and 2 for adding a new public mutation base).

## Implementation (Worker 1)

No tracked code changes needed. The target folder is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/forms/ --review docs/dry/dry-folder-forms.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification conducted by Worker 2 for `django_strawberry_framework/forms/`.

### Independent behavioral trace and boundary challenge

1. **Subpackage Architecture and Cross-File Partitioning:**
   - Audited all five modules in `django_strawberry_framework/forms/` (`__init__.py`, `converter.py`, `inputs.py`, `resolvers.py`, `sets.py`).
   - Verified that `forms/__init__.py` cleanly bounds the public API surface in `__all__` to `("DjangoFormMutation", "DjangoModelFormMutation")`, strictly encapsulating compiler internals per [spec-038][spec-038] Decision 4.
   - Verified that `forms/converter.py` isolates model-less `forms.Field` conversion via `convert_form_field`, utilizing the shared `utils/converters.py::convert_with_mro` engine without contaminating model or serializer key spaces.
   - Verified that `forms/inputs.py` discovers declared fields from `form_class.base_fields` without form instantiation, delegating column-backed fields to `model_column_input_annotation` and column-less fields to `convert_form_field`.
   - Verified that `forms/resolvers.py` executes under a single `transaction.atomic()` transaction, separates `data=` and `files=`, reconstructs partial datasets for `ModelForm` updates, and projects relation keys via `_to_form_key_value`.
   - Verified that `forms/sets.py` enforces disjoint `_validate_meta` matrices for `DjangoModelFormMutation` and `DjangoFormMutation`, manages declaration registries and shape caches via promoted factories, and integrates into Phase 2.5 finalization via `bind_form_mutations()`.

2. **Cross-Subsystem Flavor Symmetry and Root Ownership:**
   - Verified full alignment with sibling write subsystems (`mutations/` and `rest_framework/`), confirming that all cross-flavor mechanics (metaclass validation, declaration registration, input dataclass minting, shape caching, narrowing validation, reverse-map stashing, transaction management, and error mapping) are single-sited in canonical root owners (`mutations/sets.py`, `mutations/resolvers.py`, `utils/inputs.py`, `utils/converters.py`, `utils/write_values.py`, `utils/errors.py`).

3. **Duplication Probing Matrix and Single-Edit-Site Counts:**
   - Re-audited all 5 axes of the probing matrix and confirmed zero duplication across policy, execution paths, derived knowledge, inverse pairs, and medium representations.
   - Confirmed single-edit-site counts across all posited architectural changes.

4. **Verification Tooling & Test Suite Run:**
   - Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/forms/ --review docs/dry/dry-folder-forms.md --include-constants` — 100% target coverage confirmed across all 71 definitions.
   - Ran forms test suite (`tests/forms/`) and base test suite (`tests/base/test_init.py`) — 232 tests passing.

Conclusion: Verified. The review is comprehensive, accurate, and zero edits are required on the target folder.

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
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-framework-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rest-framework-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rest-framework-serializer-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[rest-framework-sets]: ../../django_strawberry_framework/rest_framework/sets.py
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
[test-base-init]: ../../tests/base/test_init.py
[test-forms-converter]: ../../tests/forms/test_converter.py
[test-forms-inputs]: ../../tests/forms/test_inputs.py
[test-forms-resolvers]: ../../tests/forms/test_resolvers.py
[test-forms-sets]: ../../tests/forms/test_sets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
