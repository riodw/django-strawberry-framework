# DRY review: `django_strawberry_framework/mutations/inputs.py`

Status: verified

## System trace

`django_strawberry_framework/mutations/inputs.py` is the foundational write-side input and payload generation substrate of the framework ([spec-036][spec-036] Decisions 4, 6, 7; [spec-037][spec-037]; [spec-038][spec-038] Decision 6; [spec-039][spec-039] Decisions 2, 7; [spec-040][spec-040] Decision 6).

It is pure, finalizer-free machinery: given a Django model, an operation kind (`CREATE` or `PARTIAL`), an effective field set (post `Meta.fields` / `Meta.exclude`), and the resolved primary `DjangoType`, it dynamically generates `<Model>Input` (create) and `<Model>PartialInput` (update) `@strawberry.input` dataclasses, the shared public [`FieldError`][mutations-inputs] `@strawberry.type` validation error envelope, and generated `<Name>Payload` `@strawberry.type` classes.

1. **Architecture & Module Namespace Lifecycle:**
   - **Pure Generation Substrate:** No metaclass, no resolver, and no finalizer wiring lives in this module; those responsibilities live in [`django_strawberry_framework/mutations/sets.py`][mutations-sets] (the base mutation classes and the phase-2.5 bind) and [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers] + [`django_strawberry_framework/mutations/fields.py`][mutations-fields]. The generators here are callable and unit-testable in isolation.
   - **Parked Globals Lifecycle:** Generated input and payload classes MUST become real module globals of `django_strawberry_framework.mutations.inputs` so that `strawberry.lazy("django_strawberry_framework.mutations.inputs")` forward-reference resolution functions during GraphQL schema construction. The module-level ledger trio (`_materialized_names`, `_materialize_input`, `_clear_input_namespace`) is single-sited via [`make_input_namespace`][utils-inputs].
   - **Wire Symmetry by Construction:** Scalar and enum conversions route through the same read-side converters in [`django_strawberry_framework/types/converters.py`][types-converters], ensuring that a Django model column maps to the byte-identical GraphQL scalar or enum type on both the read `DjangoType` output and the write input ([spec-036][spec-036] Decision 6).

2. **Target Symbols and Responsibilities:**
   - [`INPUTS_MODULE_PATH`][mutations-inputs]: Pinned string constant (`"django_strawberry_framework.mutations.inputs"`) referenced by `strawberry.lazy(...)` forward references across mutation fields and payload return types.
   - [`NON_FIELD_ERROR_KEY`][mutations-inputs]: Pinned constant re-exporting Django's `NON_FIELD_ERRORS` (`"__all__"`), serving as the single source of truth for model-wide and multi-field-constraint validation errors across all mutation resolvers.
   - [`EXCLUDED`][mutations-inputs]: Model-local decode kind sentinel (`"excluded"`) capturing provided input attributes excluded from direct model construction (the [spec-040][spec-040] D6 exclusion seam, e.g. the registration mutation's `password` attribute).
   - [`CREATE`][mutations-inputs]: Operation kind sentinel (`"create"`) instructing the generator to enforce declared field requiredness rules via [`input_field_required`][mutations-inputs].
   - [`PARTIAL`][mutations-inputs]: Operation kind sentinel (`"partial"`) instructing the generator to force every field optional with `UNSET` default (the update/partial shape).
   - [`FieldError`][mutations-inputs]: The single public `@strawberry.type` exported by this module. Standardized validation error envelope returned across all mutation flavors (model mutations, form mutations, serializer mutations, and session auth mutations), carrying `field: str`, `messages: list[str]`, `codes: list[str]`, and `path: list[str]`.
   - [`_audit_mutation_input_surface`][mutations-inputs]: Audits the final Strawberry field surface of an input class, raising a fail-loud [`ConfigurationError`][exceptions] if consumer-authored fields and generated fields map distinct Python attributes to identical GraphQL camelCase field names.
   - [`materialize_mutation_input_class`][mutations-inputs]: Audits the input class surface via [`_audit_mutation_input_surface`][mutations-inputs] and registers `input_cls` into module globals under `name`, delegating to the `_materialize_input` helper created by [`make_input_namespace`][utils-inputs].
   - [`clear_mutation_input_namespace`][mutations-inputs]: Clears the `_materialized_names` tracking ledger on `registry.clear()` while intentionally leaving class objects parked in `module.__dict__` so lazy references remain valid across schema reloads.
   - Registered pre-bind clear: Wires [`clear_mutation_input_namespace`][mutations-inputs] into the global registry via [`register_subsystem_clear`][registry] (`owner="mutations.input_namespace"`, `before_bind=True`).
   - [`editable_input_fields`][mutations-inputs]: Inspects a Django model's `_meta.get_fields()`, selecting concrete editable columns (`editable=True`, excluding primary key and `editable=False` auto-timestamps) plus forward `ManyToManyField`s with `editable=True`. Narrows selections by `fields` / `exclude` tuples and validates against unknown field names, freezing input sequences to prevent one-shot generator exhaustion.
   - [`input_field_required`][mutations-inputs]: Evaluates create-time requiredness for a Django `models.Field`: returns `True` only when a field lacks a default (`not field.has_default()`), is not nullable (`not field.null`), and is not blank (`not field.blank`).
   - [`relation_id_scalar`][mutations-inputs]: Resolves the GraphQL ID scalar for a write-side relation to `related_model`: returns `relay.GlobalID` if the related model's primary `DjangoType` implements Relay Node via [`implements_relay_node`][types-relay]; otherwise falls back to the model's raw primary key scalar via [`scalar_for_field`][types-converters].
   - [`relation_id_annotation`][mutations-inputs]: Wraps [`relation_id_scalar`][mutations-inputs] with `list[...]` when `many=True`.
   - [`related_model_of_queryset`][mutations-inputs]: Safely returns `getattr(queryset, "model", None)` for column-less relation fields (`ModelChoiceField`, `PrimaryKeyRelatedField`).
   - [`require_queryset_related_model`][mutations-inputs]: Resolves `queryset.model` via [`related_model_of_queryset`][mutations-inputs] or raises a caller-provided [`ConfigurationError`][exceptions] diagnostic if missing.
   - [`annotate_queryset_relation`][mutations-inputs]: Types column-less relation fields across form and serializer flavors, resolving the target model via [`require_queryset_related_model`][mutations-inputs], primary type annotation, and cardinality via [`relation_id_annotation`][mutations-inputs].
   - [`relation_input_annotation`][mutations-inputs]: Maps a model relation field to its `(python_attr, graphql_name, annotation)` triple: forward FK / OneToOne becomes `<field.name>_id` with camelCase GraphQL name; forward M2M keeps plain field name with `list[<id_scalar>]`.
   - [`model_column_write_kind`][mutations-inputs]: Classifies a `models.Field` into write-side decode kinds: `RELATION_MULTI`, `RELATION_SINGLE`, `FILE`, or `SCALAR`.
   - [`_relation_field_index`][mutations-inputs]: Indexes forward FK/OneToOne concrete relations (by `<field>_id`) and forward M2M relations (by field name), explicitly excluding virtual relations (`GenericForeignKey`).
   - [`mutation_input_field_specs`][mutations-inputs]: Builds the complete list of [`InputFieldSpec`][utils-inputs] reverse-map descriptors and Django field mappings for an input class, tagging attributes in `excluded_attrs` with kind `EXCLUDED`.
   - [`model_column_write_annotation`][mutations-inputs]: Resolves GraphQL annotations for model columns without naming: relations route to [`relation_id_annotation`][mutations-inputs], `FileField`/`ImageField` map to [`Upload`][scalars], and scalars route to [`convert_scalar`][types-converters] (`force_nullable=False`).
   - [`model_column_input_annotation`][mutations-inputs]: Maps a model column to its `(python_attr, graphql_name, annotation)` triple, shared by model and form input generators.
   - [`mutation_input_type_name`][mutations-inputs]: Generates deterministic input type names by delegating to [`name_set_input_type_name`][utils-inputs]: full shapes receive canonical `<Model>Input` / `<Model>PartialInput`; narrowed shapes receive deterministic token-suffixed names.
   - [`MutationInputShape`][mutations-inputs]: `NamedTuple` bundling the single derived identity of a mutation shape: `(model, operation_kind, selected, full_field_names, effective_field_names, type_name, cache_key)`.
   - [`mutation_input_shape`][mutations-inputs]: Factory function computing [`MutationInputShape`][mutations-inputs], unifying the field selection walk, name generation, and bind cache key.
   - [`_GeneratedInputFieldName`][mutations-inputs]: `NamedTuple` recording `(input_attr, graphql_name, model_field_name)` for collision auditing.
   - [`_reject_generated_input_collisions`][mutations-inputs]: Audits generated input field names using [`iter_input_field_collisions`][utils-inputs], raising [`ConfigurationError`][exceptions] on Python attribute or GraphQL name collisions.
   - [`build_mutation_input`][mutations-inputs]: Main builder function producing an unmaterialized `@strawberry.input` class from a [`MutationInputShape`][mutations-inputs], handling create requiredness, M2M optionality, consumer overrides, collision detection, and empty input rejection.
   - [`payload_object_slot`][mutations-inputs]: Determines the uniform payload object slot name for a mutation: `"node"` for Relay Node primary types, `"result"` otherwise.
   - [`build_payload_type`][mutations-inputs]: Synthesizes `<Name>Payload` `@strawberry.type` classes for both model-backed mutations (`<object_slot>: object_type | None`, `errors: list[FieldError]`) and model-less mutations (`ok: bool`, `errors: list[FieldError]`).

Connected behavior examined:
- [`django_strawberry_framework/mutations/sets.py`][mutations-sets]: Base `DjangoMutation` classes consuming `mutation_input_shape`, `build_mutation_input`, `materialize_mutation_input_class`, `build_payload_type`, and `mutation_input_field_specs`.
- [`django_strawberry_framework/mutations/fields.py`][mutations-fields]: Field factory consuming `INPUTS_MODULE_PATH`, `payload_object_slot`, and `FieldError`.
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Mutation execution pipelines consuming `InputFieldSpec`, `NON_FIELD_ERROR_KEY`, and `FieldError`.
- [`django_strawberry_framework/forms/inputs.py`][forms-inputs]: Form input generation consuming `CREATE`, `PARTIAL`, `annotate_queryset_relation`, `model_column_input_annotation`, and `model_column_write_kind`.
- [`django_strawberry_framework/forms/converter.py`][forms-converter]: Form field converter mapping form fields and requiredness.
- [`django_strawberry_framework/forms/sets.py`][forms-sets]: Form mutation sets consuming `PARTIAL` and payload synthesis.
- [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers]: Form mutation resolvers consuming `NON_FIELD_ERROR_KEY` and `FieldError`.
- [`django_strawberry_framework/rest_framework/inputs.py`][rest-framework-inputs]: Serializer input generation consuming `CREATE` and `PARTIAL`.
- [`django_strawberry_framework/rest_framework/serializer_converter.py`][rest-framework-serializer-converter]: Serializer converter consuming `annotate_queryset_relation`, `model_column_write_annotation`, and `model_column_write_kind`.
- [`django_strawberry_framework/rest_framework/resolvers.py`][rest-framework-resolvers]: Serializer resolvers consuming `NON_FIELD_ERROR_KEY` and `FieldError`.
- [`django_strawberry_framework/auth/mutations.py`][auth-mutations]: Auth mutation classes consuming `CREATE`, `INPUTS_MODULE_PATH`, `build_mutation_input`, `build_payload_type`, `editable_input_fields`, `materialize_mutation_input_class`, `mutation_input_field_specs`, `mutation_input_shape`, and `payload_object_slot`.
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Central root owner for `InputFieldSpec`, `build_strawberry_input_class`, `guard_dropped_required`, `iter_input_field_collisions`, `make_input_namespace`, `name_set_input_type_name`, `optional_input_field`, and `pascalize_token`.
- [`django_strawberry_framework/utils/errors.py`][utils-errors]: Error utilities consuming `NON_FIELD_ERROR_KEY` and `FieldError`.
- [`django_strawberry_framework/utils/write_values.py`][utils-write-values]: Write value decoding consuming `FieldError`.
- [`django_strawberry_framework/scalars.py`][scalars]: `Upload` scalar definition for file/image fields.
- [`django_strawberry_framework/types/converters.py`][types-converters]: Read-side scalar and enum converters (`convert_scalar`, `scalar_for_field`).
- [`django_strawberry_framework/types/relay.py`][types-relay]: Relay interface inspector (`implements_relay_node`).
- [`django_strawberry_framework/registry.py`][registry]: Global registry and lifecycle hook management (`register_subsystem_clear`, `registry`).
- [`tests/mutations/test_inputs.py`][test-mutations-inputs]: Comprehensive test suite covering field discovery, input class synthesis, Relay ID mapping, file uploads, name collisions, and payload generation.
- [`tests/mutations/test_sets.py`][test-mutations-sets]: Integration tests for model mutation sets and shape cache deduping.
- [`tests/mutations/test_resolvers.py`][test-mutations-resolvers]: Mutation resolver tests verifying argument decoding and error formatting.
- [`tests/forms/test_inputs.py`][test-forms-inputs]: Form input tests verifying shared model column mapping.
- [`tests/rest_framework/test_inputs.py`][test-rest-framework-inputs]: Serializer input tests verifying shared write primitives.

## Verification

Static analysis and inventory (`uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/inputs.py --review docs/dry/dry-file-mutations__inputs.md --include-constants`):
- Parsed 1 target file, 923 lines, 30 target definitions (5 constants, 3 classes, 22 functions).
- Verified reverse references across `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/mutations/fields.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/forms/resolvers.py`, `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/utils/write_values.py`, and test suites.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - **Write Subsystem Input Generation:** The framework supports multiple mutation flavors: model mutations ([`mutations/inputs.py`][mutations-inputs]), form mutations ([`forms/inputs.py`][forms-inputs]), DRF serializer mutations ([`rest_framework/inputs.py`][rest-framework-inputs]), and session auth mutations ([`auth/mutations.py`][auth-mutations]).
   - **Centralized Substrate in `utils/inputs.py`:** All write flavors leverage the shared input primitives in [`django_strawberry_framework/utils/inputs.py`][utils-inputs]:
     - Namespace lifecycle management is single-sited in [`make_input_namespace`][utils-inputs];
     - Dataclass synthesis is single-sited in [`build_strawberry_input_class`][utils-inputs];
     - Deterministic shape naming is single-sited in [`name_set_input_type_name`][utils-inputs];
     - Field attribute and GraphQL name collision auditing is single-sited in [`iter_input_field_collisions`][utils-inputs];
     - Optional field widening (`T | None`, `UNSET` default, `name=` alias) is single-sited in [`optional_input_field`][utils-inputs];
     - Injective token casing is single-sited in [`pascalize_token`][utils-inputs];
     - Reverse-map specifications are standardized via [`InputFieldSpec`][utils-inputs].
   - **Write-Side Domain Owners in `mutations/inputs.py`:** Core write-side domain logic shared across model, form, serializer, and auth flavors is centralized in `mutations/inputs.py`:
     - [`FieldError`][mutations-inputs]: The byte-identical public `@strawberry.type` validation envelope reused across all write flavors;
     - [`NON_FIELD_ERROR_KEY`][mutations-inputs]: The unified `"__all__"` non-field error sentinel;
     - [`relation_id_scalar`][mutations-inputs] and [`relation_id_annotation`][mutations-inputs]: Single source of truth for Relay `GlobalID` vs raw PK scalar resolution;
     - [`annotate_queryset_relation`][mutations-inputs] and [`require_queryset_related_model`][mutations-inputs]: Shared spine for column-less relation typing (used by form `ModelChoiceField` and serializer `PrimaryKeyRelatedField`);
     - [`model_column_write_kind`][mutations-inputs], [`model_column_write_annotation`][mutations-inputs], and [`model_column_input_annotation`][mutations-inputs]: Shared column typing ensuring strict wire symmetry with read-side `DjangoType` outputs;
     - [`payload_object_slot`][mutations-inputs] and [`build_payload_type`][mutations-inputs]: Unified payload wrapper synthesis for model-backed (`node`/`result`) and model-less (`ok`) mutations.
2. **Sync and async twins:**
   - Zero duplication. `django_strawberry_framework/mutations/inputs.py` executes exclusively during schema build and mutation binding (generating `@strawberry.input` and `@strawberry.type` classes and reverse-map specs). It contains no execution logic or sync/async branching.
   - Synchronous and asynchronous runtime mutation executions are completely isolated in [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers] (`resolve_mutation_sync` and `resolve_mutation_async`), [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers], and [`django_strawberry_framework/rest_framework/resolvers.py`][rest-framework-resolvers].
3. **Derived rather than repeated knowledge:**
   - **Editable Field Discovery:** [`editable_input_fields`][mutations-inputs] derives editable columns directly from Django's `model._meta.get_fields()`, selecting concrete editable columns and forward M2Ms while dropping primary keys and `editable=False` timestamp columns.
   - **Create Requiredness:** [`input_field_required`][mutations-inputs] derives create-input requiredness purely from Django field definitions (`not field.has_default() and not field.null and not field.blank`).
   - **Single Derived Shape Identity:** [`mutation_input_shape`][mutations-inputs] bundles all shape-derived properties into a [`MutationInputShape`][mutations-inputs] `NamedTuple` (`selected`, `full_field_names`, `effective_field_names`, `type_name`, `cache_key`), preventing drift between the input generator, the bind cache, and merged input overrides.
   - **Uniform Payload Object Slot:** [`payload_object_slot`][mutations-inputs] derives `"node"` vs `"result"` directly from [`implements_relay_node`][types-relay], ensuring the schema builder and resolver access the identical payload field name.
   - **Relation Field Indexing:** [`_relation_field_index`][mutations-inputs] derives forward relation mapping from model metadata, excluding virtual relations (`GenericForeignKey`).
4. **Inverse and round-trip pairs:**
   - **Schema Input Generation and Resolver Decoding Pairing:**
     - `mutations/inputs.py` assigns decode kinds (`SCALAR`, `RELATION_SINGLE`, `RELATION_MULTI`, `FILE`, `EXCLUDED`) and emits [`InputFieldSpec`][utils-inputs] instances;
     - `mutations/resolvers.py::decode_provided_fields` unpacks GraphQL input arguments against these `InputFieldSpec` records, reconstructing model kwargs, handling file uploads, and decoding Relay `GlobalID`s or raw PKs.
   - **Parked Globals Lifecycle Round-Trip:**
     - [`materialize_mutation_input_class`][mutations-inputs] registers generated classes in `django_strawberry_framework.mutations.inputs` module globals;
     - [`clear_mutation_input_namespace`][mutations-inputs] resets the internal tracking ledger on `registry.clear()` while leaving parked classes in `__dict__` so lazy GraphQL references remain resolvable until overwritten during the next schema build.
5. **Contracts restated in another medium:**
   - The mutation input generation contract is codified across:
     - Production code: [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs], [`django_strawberry_framework/mutations/sets.py`][mutations-sets], [`django_strawberry_framework/mutations/fields.py`][mutations-fields], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/forms/inputs.py`][forms-inputs], [`django_strawberry_framework/rest_framework/inputs.py`][rest-framework-inputs], [`django_strawberry_framework/utils/inputs.py`][utils-inputs], [`django_strawberry_framework/types/converters.py`][types-converters];
     - Specifications: [`docs/SPECS/spec-036-mutation_sets-0_0_11.md`][spec-036] (Decisions 4, 6, 7, 12), [`docs/SPECS/spec-037-file_upload_support-0_0_12.md`][spec-037], [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038] (Decisions 6, 7), [`docs/SPECS/spec-039-drf_serializer_mutations-0_0_13.md`][spec-039] (Decisions 2, 7), [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040] (Decision 6);
     - Test suites: [`tests/mutations/test_inputs.py`][test-mutations-inputs], [`tests/mutations/test_sets.py`][test-mutations-sets], [`tests/mutations/test_resolvers.py`][test-mutations-resolvers], [`tests/forms/test_inputs.py`][test-forms-inputs], [`tests/rest_framework/test_inputs.py`][test-rest-framework-inputs], [`tests/auth/test_mutations.py`][test-auth-mutations];
     - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Modifying the write-side relation ID scalar rule between Relay GlobalID and raw pk):** Alter the logic determining when a relation input uses `relay.GlobalID` vs raw pk scalar.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/inputs.py::relation_id_scalar`][mutations-inputs]. Model, form, and serializer relation annotations inherit the update immediately.
  - *Site count:* 1.
- **Posited change 2 (Altering create-input field requiredness rules):** Modify the conditions under which a model field is required in a create input.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/inputs.py::input_field_required`][mutations-inputs].
  - *Site count:* 1.
- **Posited change 3 (Modifying the payload object slot naming convention):** Change `"node"` / `"result"` to another slot name (e.g., `"record"`).
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/inputs.py::payload_object_slot`][mutations-inputs]. Both [`build_payload_type`][mutations-inputs] and mutation resolvers consume this single helper.
  - *Site count:* 1.
- **Posited change 4 (Adding a new structured field to the public validation error envelope):** Add an additional field (e.g., `severity: str`) to [`FieldError`][mutations-inputs].
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/inputs.py::FieldError`][mutations-inputs]. All mutation flavors (model, form, serializer, auth) immediately expose the updated envelope.
  - *Site count:* 1.
- **Posited change 5 (Modifying model column write decode kind classification):** Add or adjust classification logic for custom Django field types in [`model_column_write_kind`][mutations-inputs].
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/inputs.py::model_column_write_kind`][mutations-inputs].
  - *Site count:* 1.
- **Posited change 6 (Modifying the input class naming convention or shape token hashing):** Alter how shape tokens are derived for narrowed input dataclasses.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py::name_set_input_type_name`][utils-inputs].
  - *Site count:* 1.

### Rejected candidates

1. **Moving `relation_id_scalar`, `relation_id_annotation`, `annotate_queryset_relation`, `model_column_write_kind`, `model_column_write_annotation`, and `model_column_input_annotation` into `utils/inputs.py`:**
   - Disproved. `utils/inputs.py` is model-agnostic and Django-independent (owning dataclass synthesis, namespace materialization, string token naming, and collision auditing). Model-aware and GraphQL-converter-aware logic belongs in `mutations/inputs.py` as the canonical write-side domain root owner. Form and serializer flavors import these utilities from `mutations/inputs.py`.
2. **Merging `_relation_field_index` with read-side relation discovery:**
   - Disproved. Write-side input mapping only accepts forward concrete relations (`ForeignKey`, `OneToOneField`) and forward `ManyToManyField`s, mapping them to `<field>_id` / field name. Read-side relation discovery traverses reverse relations, GenericForeignKeys, and connection fields. Merging them would compromise write-side type safety.
3. **Merging `editable_input_fields` with `orders/inputs.py::_get_concrete_field_names_for_order`:**
   - Disproved per [spec-036][spec-036] Decision 6. The write side excludes read-only timestamps (`auto_now`, `auto_now_add` where `editable=False`), drops primary keys, and includes forward M2M. The order side includes read-only timestamps and pk, and excludes M2M. They have opposite semantic policies.

## Opportunities

None — `django_strawberry_framework/mutations/inputs.py` is a clean, 923-line write-side input and payload generation substrate. All shared namespace materialization, dataclass synthesis, collision auditing, and shape naming mechanisms are consolidated at root owners in [`django_strawberry_framework/utils/inputs.py`][utils-inputs]. Write-side relation ID typing, model column classification, and payload synthesis are cleanly centralized in `mutations/inputs.py` and reused across all write flavors.

## Judgment

Zero-edit review. `django_strawberry_framework/mutations/inputs.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/inputs.py --review docs/dry/dry-file-mutations__inputs.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

I independently verified Worker 1's DRY review for `django_strawberry_framework/mutations/inputs.py`.

### Verification Scope and Connected Behavior

1. **Write-Side Domain Root Ownership:**
   - Evaluated the complete surface of `django_strawberry_framework/mutations/inputs.py` across all 30 target definitions (5 constants, 3 classes, 22 functions).
   - Traced all call sites across [`django_strawberry_framework/mutations/sets.py`][mutations-sets], [`django_strawberry_framework/mutations/fields.py`][mutations-fields], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/forms/inputs.py`][forms-inputs], [`django_strawberry_framework/forms/sets.py`][forms-sets], [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers], [`django_strawberry_framework/rest_framework/inputs.py`][rest-framework-inputs], [`django_strawberry_framework/rest_framework/serializer_converter.py`][rest-framework-serializer-converter], [`django_strawberry_framework/rest_framework/resolvers.py`][rest-framework-resolvers], [`django_strawberry_framework/auth/mutations.py`][auth-mutations], [`django_strawberry_framework/utils/errors.py`][utils-errors], and [`django_strawberry_framework/utils/write_values.py`][utils-write-values].
   - Verified that all mutation flavors (model, form, serializer, and auth) share the exact same validation error envelope ([`FieldError`][mutations-inputs]) and non-field error sentinel ([`NON_FIELD_ERROR_KEY`][mutations-inputs]).

2. **Equivalence & Boundary Challenges:**
   - *Challenge 1 (Separation of model-aware write typing from `utils/inputs.py`):* Confirmed that `utils/inputs.py` remains strictly model-agnostic and Django-free (owning generic namespace materialization, dataclass assembly, token casing, and collision auditing), whereas `mutations/inputs.py` serves as the write-side domain root owner knowing Django model fields, converters, and write semantics. Form and serializer adapters consume write typing primitives from `mutations/inputs.py` without duplication.
   - *Challenge 2 (Non-equivalence of write column selection vs. read/order field discovery):* Re-verified the boundary between [`editable_input_fields`][mutations-inputs] and `orders/inputs.py::_get_concrete_field_names_for_order`. Write inputs exclude `primary_key`, exclude `editable=False` columns (auto timestamps), and include forward `ManyToManyField`s; ordering includes primary keys and auto timestamps while rejecting M2Ms. The inverted semantic requirements justify distinct, dedicated selectors.
   - *Challenge 3 (Virtual relation exclusion):* Verified that `_relation_field_index` and `mutation_input_field_specs` deliberately exclude `GenericForeignKey` and column-less virtual relations from write-side FK/M2M resolution, preventing runtime mapping failures.
   - *Challenge 4 (Unified payload wrapper synthesis):* Verified that [`build_payload_type`][mutations-inputs] and [`payload_object_slot`][mutations-inputs] correctly handle both model-backed (`node`/`result`) and model-less (`ok`) payload structures with zero drift in the `errors: list[FieldError]` wire envelope.

3. **Mandatory 5-Axis Matrix Discharge:**
   - All 5 axes are fully addressed and legitimately discharged with concrete architectural justifications:
     - Axis 1 (Cross-flavor policy mirroring): Verified consolidation of shared write primitives in `mutations/inputs.py` and substrate utilities in `utils/inputs.py`.
     - Axis 2 (Sync and async twins): Verified that `mutations/inputs.py` is pure schema-time generation machinery with zero execution runtime or sync/async branching.
     - Axis 3 (Derived rather than repeated knowledge): Verified single derivation of field requiredness, editable field discovery, payload object slots, and shape descriptors via [`MutationInputShape`][mutations-inputs].
     - Axis 4 (Inverse and round-trip pairs): Verified schema-time input generation against resolver-time `InputFieldSpec` argument decoding, as well as parked globals registration and clean pre-bind lifecycle resetting.
     - Axis 5 (Contracts restated in another medium): Verified alignment across specifications ([spec-036][spec-036], [spec-037][spec-037], [spec-038][spec-038], [spec-039][spec-039], [spec-040][spec-040]), test suites, and documentation.

4. **Single-Edit-Site Counts:**
   - Confirmed all 6 posited modifications require exactly 1 edit site.

5. **Tool & Suite Verification:**
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/inputs.py --review docs/dry/dry-file-mutations__inputs.md --include-constants`: confirmed 30 target definitions covered with 0 missing topics.
   - Executed `uv run pytest tests/mutations/`: 325 mutation tests passed cleanly.

Review verified with zero code modifications needed. Updating status to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutation_sets-0_0_11.md
[spec-037]: ../SPECS/spec-037-file_upload_support-0_0_12.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-drf_serializer_mutations-0_0_13.md
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-framework-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rest-framework-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rest-framework-serializer-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[scalars]: ../../django_strawberry_framework/scalars.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[utils-errors]: ../../django_strawberry_framework/utils/errors.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-auth-mutations]: ../../tests/auth/test_mutations.py
[test-forms-inputs]: ../../tests/forms/test_inputs.py
[test-mutations-inputs]: ../../tests/mutations/test_inputs.py
[test-mutations-resolvers]: ../../tests/mutations/test_resolvers.py
[test-mutations-sets]: ../../tests/mutations/test_sets.py
[test-rest-framework-inputs]: ../../tests/rest_framework/test_inputs.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
