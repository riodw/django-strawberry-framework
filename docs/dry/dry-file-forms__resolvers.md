# DRY review: `django_strawberry_framework/forms/resolvers.py`

Status: verified

## System trace

`django_strawberry_framework/forms/resolvers.py` implements the sync and async form-mutation execution pipeline ([spec-038][spec-038] Decisions 6, 7, 8, 9, 10, 11). It serves as the form-flavor counterpart to model mutations ([`mutations/resolvers.py`][mutations-resolvers]) and DRF serializer mutations ([`rest_framework/resolvers.py`][rest-framework-resolvers]).

1. **Pipeline Architecture and Security Invariants ([spec-038][spec-038] Decision 8):**
   - The write pipeline follows the strict order:
     `(update) locate -> authorize -> decode -> construct + validate-once -> write -> (ModelForm) re-fetch -> payload`
   - **Authorize-Before-Decode Ordering:** Authorize runs before relation decoding. Because relation decoding issues visibility-scoped `get_queryset` queries against the database, running decode before authorization would allow unauthorized callers to probe related-object existence and visibility via relation IDs.
   - **Unified Synchronization Boundary:** Both synchronous and asynchronous executions share a single sync execution body ([`_run_form_pipeline_sync`][forms-resolvers]) orchestrated by [`run_write_pipeline_sync`][mutations-resolvers]. Asynchronous resolver execution ([`resolve_form_async`][forms-resolvers]) runs this entire sync pipeline in a single `sync_to_async(thread_sensitive=True)` worker call without interleaving async await boundaries inside ORM transactions.
   - **Async Recourse Discipline:** Encountering an `async def get_queryset` during sync execution triggers a `SyncMisuseError` appended with [`_FORM_ASYNC_RECOURSE`][forms-resolvers] (single-sourced via [`sync_pipeline_recourse`][utils-querysets]).

2. **Form-Keyed Data and Upload Container Separation ([spec-038][spec-038] Decision 8 Step 1):**
   - In contrast to model mutations (which populate model instance attributes) and serializer mutations (which pass files within `data`), Django forms strictly separate form field values (`data=`) from file uploads (`files=`).
   - [`_decode_form_data`][forms-resolvers] uses the bind-stashed reverse map (`mutation_cls._input_field_specs`, containing [`InputFieldSpec`][utils-inputs] records) to decode GraphQL arguments into separate `provided_data` (for `SCALAR`, `RELATION_SINGLE`, and `RELATION_MULTI`) and `provided_files` (for `FILE`) dictionaries via [`decode_field_handlers`][utils-write-values] and [`decode_provided_fields`][utils-write-values].

3. **Visibility-Checked Relation Decoding and Form-Key Projection ([spec-038][spec-038] Decision 7, Decision 8 Step 1):**
   - [`_to_form_key_value`][forms-resolvers]: Converts a resolved related model instance to its expected form-key representation. If the form field specifies `to_field_name`, `obj.serializable_value(to_field_name)` is extracted; otherwise, `obj.pk` is returned.
   - [`_is_empty_form_value`][forms-resolvers]: Evaluates whether a candidate value matches the form field's `empty_values` tuple (defaulting to `(None, "", [], (), {})`), catching `TypeError` safely for unhashable values.
   - [`_decode_form_relation_single`][forms-resolvers]: Decodes a single relation ID (either a Relay `GlobalID` or a raw PK) via [`decode_visible_relation`][utils-write-values]. Empty values pass through unmolested so bound form validation determines requiredness. Invalid, uncoercible, hidden, or wrong-model IDs convert to field-keyed `FieldError` items without leaking object existence.
   - [`_decode_form_relation_multi`][forms-resolvers]: Decodes a sequence of M2M relation IDs by mapping [`_decode_form_relation_single`][forms-resolvers] over each element. Explicit empty values or `null` return `[]` to allow form-level requiredness validation.

4. **Partial Update Reconstruction ([spec-038][spec-038] Decision 8 Step 4):**
   - Django forms validate entire bound datasets rather than partial changes. For partial updates on `DjangoModelFormMutation`, [`_reconstruct_partial_data`][forms-resolvers] synthesizes a complete bound `data=` mapping by combining unprovided stored attributes from the database `instance` with `provided_data`:
     - Scalars and standard FKs (without `to_field_name`) are extracted via `model_to_dict(instance, fields=scalar_names)`.
     - FKs with `to_field_name` set are resolved from `getattr(instance, name)` and projected via [`_to_form_key_value`][forms-resolvers].
     - M2M relations are resolved from `getattr(instance, name).all()` and projected via [`_to_form_key_value`][forms-resolvers].
     - File fields are omitted from reconstructed `data=` and preserved via `form_class(instance=instance)` initial values.
   - This ensures full form revalidation: unchanged stored values that no longer satisfy form validators fail cleanly before write.

5. **Form Construction, Validation, and Error Mapping ([spec-038][spec-038] Decision 8 Steps 4 & 5):**
   - [`_bound_form_or_field_errors`][forms-resolvers]: Instantiates the form once via the overridable `holder.get_form(info, data=form_data, files=provided_files, instance=instance)` hook and executes `form.is_valid()`.
   - [`_form_errors_to_field_errors`][forms-resolvers]: Transforms `form.errors.as_data()` into a standard `ValidationError` and delegates to [`validation_error_to_field_errors`][utils-errors], mapping `NON_FIELD_ERRORS` to the `"__all__"` sentinel.
   - [`_modelform_write_step`][forms-resolvers]: Validates the bound form, enters the write phase via [`pipeline_write_phase`][utils-write-transaction], executes `form.save()` wrapped in [`save_or_field_errors`][mutations-resolvers] (mapping `IntegrityError` to `FieldError`), and returns `form.instance` for optimizer re-fetching.
   - [`_plain_form_write_step`][forms-resolvers]: Validates the bound form, enters [`pipeline_write_phase`][utils-write-transaction], executes `holder.perform_mutate(form, info)` wrapped in [`save_or_field_errors`][mutations-resolvers], and returns `True` to trigger the `{ ok: true }` payload.
   - [`_modelform_decode_step`][forms-resolvers]: Combines [`_decode_form_data`][forms-resolvers] and [`_reconstruct_partial_data`][forms-resolvers] for consumption by the shared pipeline skeleton.
   - [`_run_form_pipeline_sync`][forms-resolvers]: Wires `decode_step` and `write_step` into [`run_write_pipeline_sync`][mutations-resolvers].
   - [`resolve_form_sync`][forms-resolvers] & [`resolve_form_async`][forms-resolvers]: Public resolver entry points generated via [`make_resolver_entries`][mutations-resolvers].

Connected behavior examined:
- [`django_strawberry_framework/forms/sets.py`][forms-sets]: Base classes `DjangoFormMutation` and `DjangoModelFormMutation` configuring reverse-map specs and delegating resolver seams.
- [`django_strawberry_framework/forms/inputs.py`][forms-inputs]: Input generation building `@strawberry.input` classes and `InputFieldSpec` lists.
- [`django_strawberry_framework/forms/converter.py`][forms-converter]: Form field type converters and kind constants (`SCALAR`, `RELATION_SINGLE`, `RELATION_MULTI`, `FILE`).
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Shared write pipeline runner `run_write_pipeline_sync`, entry factory `make_resolver_entries`, and save wrapper `save_or_field_errors`.
- [`django_strawberry_framework/utils/write_values.py`][utils-write-values]: Flavor-neutral write primitives (`decode_provided_fields`, `decode_field_handlers`, `decode_visible_relation`, `type_check_relation_id`, `coerce_relation_pk_or_none`, `decode_scalar_leaf`).
- [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction]: Database alias guarding and `pipeline_write_phase` context manager.
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: Queryset visibility helpers (`visible_related_object`, `visible_related_objects`, `apply_type_visibility_sync`, `sync_pipeline_recourse`).
- [`django_strawberry_framework/utils/errors.py`][utils-errors]: Error mapping helpers (`validation_error_to_field_errors`, `field_error`, `relation_field_error`).
- [`tests/forms/test_resolvers.py`][test-forms-resolvers]: Test suite covering sync/async form resolution, relation visibility, partial updates, file uploads, and error envelopes.
- [`tests/forms/test_sets.py`][test-forms-sets]: Integration tests for form mutation sets.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/forms/resolvers.py --review docs/dry/dry-file-forms__resolvers.md --include-constants`):
- Parsed 1 target file, 619 lines, 13 target definitions (1 constant, 12 functions) plus module entrypoints `resolve_form_sync` and `resolve_form_async`.
- Verified reverse references across `django_strawberry_framework/forms/sets.py`, `tests/forms/test_resolvers.py`, and `tests/forms/test_sets.py`.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - **Write Subsystem Execution Pipelines:** The framework provides three write mutation flavors: model mutations ([`mutations/resolvers.py`][mutations-resolvers]), form mutations ([`forms/resolvers.py`][forms-resolvers]), and DRF serializer mutations ([`rest_framework/resolvers.py`][rest-framework-resolvers]).
   - **Unified Shared Skeleton:** All three flavors share the promoted orchestration runtime in [`django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`][mutations-resolvers]:
     - Centralized `transaction.atomic()` transaction management;
     - Fixed security lifecycle enforcing `locate -> authorize -> decode -> validate -> write -> re-fetch/snapshot -> payload`;
     - Pre-decode permission checking preventing relation-existence probing;
     - Post-write optimized instance re-fetching (`refetch_optimized`) via the G2 optimizer gate without re-applying visibility filters;
     - Standardized `IntegrityError` envelope mapping via [`save_or_field_errors`][mutations-resolvers];
     - Phased database alias isolation via [`pipeline_write_phase`][utils-write-transaction];
     - Identical sync/async resolver pair generation via [`make_resolver_entries`][mutations-resolvers].
   - **Shared Value Decoding:** All three write flavors leverage the neutral value decoding substrate in [`django_strawberry_framework/utils/write_values.py`][utils-write-values]:
     - `InputFieldSpec` iteration and dispatch via [`decode_provided_fields`][utils-write-values];
     - Standard handler generation via [`decode_field_handlers`][utils-write-values];
     - Scalar leaf sanitization (lone surrogate preflight + choice enum unwrapping) via [`decode_scalar_leaf`][utils-write-values];
     - Relation ID type checking (GlobalID vs raw PK) via [`type_check_relation_id`][utils-write-values] and [`coerce_relation_pk_or_none`][utils-write-values];
     - Visibility-scoped related object resolution via [`visible_related_object`][utils-querysets] and [`visible_related_objects`][utils-querysets].
   - **Flavor-Specific Invariants:**
     - In `forms/resolvers.py`, file uploads are separated into `provided_files` (`files=`) rather than mixed into `data=`;
     - Relation values project through [`_to_form_key_value`][forms-resolvers] to support form `to_field_name` keys;
     - Partial model-form updates reconstruct complete bound datasets via [`_reconstruct_partial_data`][forms-resolvers] because Django forms lack native partial validation;
     - Plain form mutations execute `perform_mutate` and return model-less `{ ok: true }` payloads.
2. **Sync and async twins:**
   - Zero duplication. Both sync ([`resolve_form_sync`][forms-resolvers]) and async ([`resolve_form_async`][forms-resolvers]) resolvers are minted simultaneously via [`make_resolver_entries(_run_form_pipeline_sync)`][mutations-resolvers].
   - The entire pipeline executes synchronously under one `transaction.atomic()` block. On the async GraphQL surface, `resolve_form_async` wraps `_run_form_pipeline_sync` in a single `sync_to_async(thread_sensitive=True)` worker call, preventing interleaved coroutine context switches during ORM transactions.
   - `SyncMisuseError` discipline is enforced uniformly: an async `get_queryset` encountered during execution raises `SyncMisuseError` with [`_FORM_ASYNC_RECOURSE`][forms-resolvers] generated by [`sync_pipeline_recourse("form mutation")`][utils-querysets].
3. **Derived rather than repeated knowledge:**
   - **Reverse Map Specs:** Field routing derives directly from `mutation_cls._input_field_specs` stashed during mutation binding in [`forms/sets.py`][forms-sets].
   - **Target Relation Models:** `spec.related_model` is pre-computed at schema build time, avoiding runtime inspection of `form_field.queryset.model` (which is `None` for forms initialized with request-scoped choices).
   - **Form Field Discovery:** Read once per decode/reconstruction via `mutation_cls.get_form_fields()`.
   - **Model Inspection:** Concrete model metadata (`model._meta.many_to_many`, `model._meta.concrete_fields`) is inspected dynamically via `mutation_cls._mutation_meta.model._meta`.
   - **Error Envelopes:** [`_form_errors_to_field_errors`][forms-resolvers] extracts `form.errors.as_data()` and delegates to [`validation_error_to_field_errors`][utils-errors], deriving standard field paths and mapping non-field errors to `"__all__"` without parallel conversion logic.
4. **Inverse and round-trip pairs:**
   - **Schema Input Generation <-> Resolver Argument Decoding:**
     - [`forms/inputs.py`][forms-inputs] constructs `@strawberry.input` types and records `InputFieldSpec(input_attr, graphql_name, target_name, kind, related_model)`.
     - [`forms/resolvers.py`][forms-resolvers] consumes `InputFieldSpec` records to unpack GraphQL input dataclasses back into form-field-keyed `provided_data` and `provided_files`.
   - **Relation Key Projection <-> Form Field Parsing:**
     - [`_to_form_key_value`][forms-resolvers] projects resolved relation instances to `obj.serializable_value(to_field_name)` or `obj.pk`.
     - Django's `ModelChoiceField.to_python` receives this exact form key and queries the database for the matching related instance.
   - **Instance Decomposition <-> Form Data Recomposition:**
     - In partial updates, [`_reconstruct_partial_data`][forms-resolvers] decomposes existing instance state (scalars via `model_to_dict`, M2M and FK relations via `_to_form_key_value`), overlays `provided_data`, and feeds the reconstructed mapping to `form_class(data=form_data, files=provided_files, instance=instance)`.
5. **Contracts restated in another medium:**
   - The form mutation resolver contract is consistently codified across:
     - Production code: [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers], [`django_strawberry_framework/forms/sets.py`][forms-sets], [`django_strawberry_framework/forms/inputs.py`][forms-inputs], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/utils/write_values.py`][utils-write-values], [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction];
     - Specifications: [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038] (Decisions 6, 7, 8, 9, 10, 11), [`docs/SPECS/spec-036-mutation_sets-0_0_11.md`][spec-036], [`docs/SPECS/spec-039-drf_serializer_mutations-0_0_13.md`][spec-039];
     - Test suites: [`tests/forms/test_resolvers.py`][test-forms-resolvers], [`tests/forms/test_sets.py`][test-forms-sets], [`examples/fakeshop/test_query/test_products_api.py`][test-products-api];
     - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Modifying the invalid Unicode text preflight or scalar leaf sanitization):** Alter how lone surrogate code points or choice enums are sanitized on scalar write inputs.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/write_values.py::decode_scalar_leaf`][utils-write-values].
  - *Site count:* 1.
- **Posited change 2 (Modifying relation GlobalID type checking or raw-PK coercion logic):** Change structural validation or PK coercion for relation arguments across all write flavors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/write_values.py::type_check_relation_id`][utils-write-values] or [`django_strawberry_framework/utils/write_values.py::coerce_relation_pk_or_none`][utils-write-values].
  - *Site count:* 1.
- **Posited change 3 (Modifying sync/async resolver pair generation or signature normalization):** Change how `resolve_sync` and `resolve_async` normalize default `UNSET` arguments or delegate to the async boundary.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/resolvers.py::make_resolver_entries`][mutations-resolvers].
  - *Site count:* 1.
- **Posited change 4 (Altering the write pipeline orchestration or phase-gating sequence):** Modify the execution lifecycle (e.g. locate, authorize, decode, write, re-fetch) or transaction boundary across mutation flavors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`][mutations-resolvers].
  - *Site count:* 1.
- **Posited change 5 (Modifying the async pipeline recourse error message template):** Update diagnostic messages when an `async def get_queryset` is encountered in a sync pipeline.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/querysets.py::sync_pipeline_recourse`][utils-querysets].
  - *Site count:* 1.
- **Posited change 6 (Altering form validation error envelope conversion):** Adjust how Django `ValidationError` instances are transformed into GraphQL `FieldError` structures.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/errors.py::validation_error_to_field_errors`][utils-errors].
  - *Site count:* 1.
- **Posited change 7 (Adjusting partial ModelForm data reconstruction for to_field_name relations):** Change how unprovided `ModelChoiceField` attributes with custom `to_field_name` are extracted from the located instance.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/forms/resolvers.py::_reconstruct_partial_data`][forms-resolvers].
  - *Site count:* 1.
- **Posited change 8 (Adjusting form relation multi empty_values clearing behavior):** Change how empty lists or `null` M2M inputs clear form values.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/forms/resolvers.py::_decode_form_relation_multi`][forms-resolvers].
  - *Site count:* 1.

### Rejected candidates

1. **Merging `_reconstruct_partial_data` with model mutation partial update logic:**
   - Disproved per [spec-038][spec-038] Decision 8. Model mutations perform partial updates by directly executing `setattr` on the located model instance and passing `exclude=...` to `full_clean()`. In contrast, Django `ModelForm` classes validate the entire form payload as a unit and do not support partial validation; thus, unprovided fields must be explicitly reconstructed into a full bound `data=` dictionary. Merging them would break Django form validation semantics.
2. **Unifying `_decode_form_data` file handling with DRF serializer file decoding:**
   - Disproved per [spec-038][spec-038] Decision 8 step 1 and [spec-039][spec-039] Decision 8 step 1. Django `Form` instances require file uploads to be passed via `files=`, whereas DRF serializers read file uploads directly from `data=`. Attempting to unify their destination dictionaries would cause Django forms to ignore file uploads.
3. **Inlining `run_write_pipeline_sync` or `make_resolver_entries` inside `forms/resolvers.py`:**
   - Disproved per [spec-039][spec-039] M1a. Transaction management, locate-authorize-decode ordering, optimizer re-fetching, and sync/async boundary execution are consolidated at root owners in [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers].

## Opportunities

None — `django_strawberry_framework/forms/resolvers.py` is a clean, 619-line form mutation resolver pipeline. All cross-flavor pipeline orchestration, transaction management, sync/async entry generation, error mapping, and scalar/relation decoding primitives are consolidated at root owners in [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/utils/write_values.py`][utils-write-values], [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction], and [`django_strawberry_framework/utils/querysets.py`][utils-querysets]. Form-specific data/files separation, `to_field_name` projection, and partial update data reconstruction are precisely bounded.

## Judgment

Zero-edit review. `django_strawberry_framework/forms/resolvers.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/forms/resolvers.py --review docs/dry/dry-file-forms__resolvers.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification conducted on `django_strawberry_framework/forms/resolvers.py`:

1. **System trace & boundary challenge:**
   - Re-traced the execution lifecycle across `DjangoFormMutation` and `DjangoModelFormMutation`:
     `(update) locate -> authorize -> decode -> construct + validate-once -> write -> (ModelForm) re-fetch -> payload`
   - Verified that authorize strictly precedes relation decoding (`_decode_form_data`). Because relation decoding resolves related instances through visibility-scoped querysets (`apply_type_visibility_sync`), pre-decode authorization prevents unauthorized callers from probing related object existence or visibility by ID.
   - Verified that `_run_form_pipeline_sync` cleanly delegates pipeline orchestration, transaction management (`transaction.atomic()`), permission checking, locate preamble, and G2 optimizer re-fetching (`refetch_optimized`) to [`django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`][mutations-resolvers].
   - Verified that `resolve_form_sync` and `resolve_form_async` are minted as twins via [`django_strawberry_framework/mutations/resolvers.py::make_resolver_entries`][mutations-resolvers]. The async resolver wraps the synchronous pipeline in a single `sync_to_async(thread_sensitive=True)` worker call, preventing interleaved async execution inside ORM transactions.
   - Verified `SyncMisuseError` handling: encountering an `async def get_queryset` raises `SyncMisuseError` with single-sourced recourse text [`_FORM_ASYNC_RECOURSE`][forms-resolvers] generated by [`sync_pipeline_recourse("form mutation")`][utils-querysets].
   - Verified form-specific invariants:
     - `_decode_form_data` routes scalar/relation values to `provided_data` and file uploads to `provided_files` via [`decode_field_handlers`][utils-write-values] and [`decode_provided_fields`][utils-write-values], respecting Django form `files=` separation.
     - `_to_form_key_value` projects related instances to `obj.serializable_value(to_field_name)` when `to_field_name` is configured, or `obj.pk` otherwise, ensuring exact parity with `ModelChoiceField.to_python`.
     - `_decode_form_relation_single` delegates to [`decode_visible_relation`][utils-write-values], skipping empty form values and projecting via `_to_form_key_value`.
     - `_decode_form_relation_multi` maps single relation decoding across elements, permitting `null` / empty lists to clear M2M fields so form-level requiredness rules govern validation.
     - `_reconstruct_partial_data` synthesizes a complete bound `data=` dictionary for `ModelForm` updates, preserving unprovided scalars, FKs (including `to_field_name` variants), and M2Ms from the existing instance while omitting files (preserved via `form_class(instance=...)`), ensuring full form revalidation.
     - `_bound_form_or_field_errors` constructs the form once and executes `is_valid()` once, mapping errors via `_form_errors_to_field_errors` and [`validation_error_to_field_errors`][utils-errors] with `"__all__"` sentinel preservation.
     - `_modelform_write_step` and `_plain_form_write_step` isolate write operations within [`pipeline_write_phase`][utils-write-transaction] and wrap execution in [`save_or_field_errors`][mutations-resolvers] to map `IntegrityError` to `FieldError`.

2. **Mandatory probing matrix:**
   - All 5 axes are verified and discharged with valid justifications. Cross-flavor execution, sync/async pairing, derived metadata, inverse transformations, and cross-medium codification are strictly observed with zero policy duplication.

3. **Single-edit-site verification:**
   - Evaluated posited changes 1 through 8. Confirmed that all change scenarios isolate to exactly 1 site at their canonical root owners.

4. **Coverage check:**
   - Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/forms/resolvers.py --review docs/dry/dry-file-forms__resolvers.md --include-constants` and confirmed 100% target coverage (13 target definitions covered).

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
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-framework-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rest-framework-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[scalars]: ../../django_strawberry_framework/scalars.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
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
[test-products-api]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
