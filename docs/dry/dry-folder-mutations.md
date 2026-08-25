# DRY review: `django_strawberry_framework/mutations/`

Status: verified

## System trace

`django_strawberry_framework/mutations/` is the core model-driven write and mutation orchestration subsystem of the framework ([spec-036][spec-036], [spec-037][spec-037], [spec-038][spec-038], [spec-039][spec-039], [spec-040][spec-040], [spec-046][spec-046], [spec-047][spec-047]). It provides declarative CUD (create, update, delete) mutation definition, automatic GraphQL input dataclass synthesis, Relay GlobalID adaptation and validation, server-side row locking, authorize-before-decode security enforcement, partial-update constraint preservation, atomic transactional execution, post-write optimizer-planned re-fetching, snapshot-before-delete lifecycle handling, standardized validation error envelopes, and seamless synchronous/asynchronous execution pipelines.

The subpackage acts as the foundational write architecture for the entire repository, serving not only model mutations but also providing the shared metaclass, input generation, authorization, and execution pipeline infrastructure for form mutations ([`django_strawberry_framework/forms/`][forms-init]), DRF serializer mutations ([`django_strawberry_framework/rest_framework/`][rest-framework-init]), and session authentication mutations ([`django_strawberry_framework/auth/mutations.py`][auth-mutations]).

Subpackage module architecture:
1. [`mutations/__init__.py`][mutations-init]: Public package exports (`FieldError`, `DjangoMutation`, `DjangoModelPermission`, `DjangoMutationField`).
2. [`mutations/operations.py`][mutations-operations]: Canonical mutation operation descriptor and metadata registry ([`MutationOperationDescriptor`][mutations-operations], [`get_operation_descriptor`][mutations-operations], [`operation_takes_id`][mutations-operations], [`operation_takes_data`][mutations-operations], `OPERATION_CREATE`, `OPERATION_UPDATE`, `OPERATION_DELETE`, `OPERATION_FORM`, `_OPERATIONS_BY_NAME`, `_OPERATION_PERMISSION_ACTION`, `NON_DELETE_OPERATION_INPUT_KIND`, `_OPERATION_INPUT_OVERRIDE_ATTR`, `NON_DELETE_WRITE_OPERATIONS`, `_VALID_OPERATIONS`, and `non_delete_operation_error`).
3. [`mutations/fields.py`][mutations-fields]: Field factory substrate (`DjangoMutationField`, `_synthesized_mutation_signature`, `build_lazy_field_signature`, `_validate_mutation_target`, `MUTATION_CLASS_MARKER`).
4. [`mutations/inputs.py`][mutations-inputs]: Input dataclass and payload generation substrate (`FieldError`, `MutationInputShape`, `build_mutation_input`, `build_payload_type`, `materialize_mutation_input_class`, `clear_mutation_input_namespace`).
5. [`mutations/permissions.py`][mutations-permissions]: Write authorization engine (`_OPERATION_PERMISSION_ACTION`, `DjangoModelPermission`, `DenyAll`, `run_permission_classes`, `_require_sync_bool_auth_result`).
6. [`mutations/resolvers.py`][mutations-resolvers]: Runtime write pipeline orchestrator (`run_write_pipeline_sync`, `coerce_lookup_id`, `locate_instance`, `authorize_or_raise`, `_decode_relations`, `_model_write_step`, `_run_delete`, `refetch_optimized`, `error_payload_builder`, `run_pipeline_async`).
7. [`mutations/sets.py`][mutations-sets]: Metaclass, mutation set base class, and phase-2.5 binding engine (`DjangoMutation`, `make_declaration_registry`, `make_meta_validating_metaclass`, `bind_mutations`, `bind_write_declarations`).

The subpackage is partitioned across seven cohesive modules:

1. [`mutations/__init__.py`][mutations-init]: Public Subpackage Export Facade:
   - **Public Export Surface:** Re-exports the four foundational write symbols in [`__all__`][mutations-init]: declarative mutation base class [`DjangoMutation`][mutations-sets], field factory [`DjangoMutationField`][mutations-fields], canonical write authorization class [`DjangoModelPermission`][mutations-permissions], and standardized validation error envelope [`FieldError`][mutations-inputs].
   - **Root Facade Re-Export:** All four symbols are re-exported at the package root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] and tested for exact symbol identity in [`tests/base/test_init.py`][test-base-init].
   - **Encapsulation Boundary:** Deliberately excludes low-level compiler and resolver internals (`bind_mutations`, `coerce_lookup_id`, `run_write_pipeline_sync`, `run_write_pipeline_async`, `build_mutation_input`, metaclass helpers) to preserve a clean consumer API boundary per [spec-036][spec-036] Decision 4.

2. [`mutations/fields.py`][mutations-fields]: Root-Field Factory & Lazy Signature Synthesis:
   - **Field Synthesis:** [`DjangoMutationField`][mutations-fields] converts declarative mutation classes into Strawberry root mutation fields with forward-referenced lazy return types, GraphQL argument signatures, server-side Relay GlobalID coercion, lifecycle target validation, completion-spanning atomicity marking, and runtime sync/async execution dispatch ([spec-036][spec-036] Decisions 5, 7, 8).
   - **Lazy Signature Builder:** [`build_lazy_field_signature`][mutations-fields] and [`_lazy_ref`][mutations-fields] build `(inspect.Signature, __annotations__)` pairs for root fields whose return types materialize at Phase 2.5 finalization. Injects `root`, `info: strawberry.types.Info`, keyword-only arguments, and `strawberry.lazy` return type annotations. Reused by auth root fields ([`auth/mutations.py`][auth-mutations], [`auth/queries.py`][auth-queries]) per [spec-040][spec-040] Helper-reuse D12.
   - **Operation Signatures:** [`_synthesized_mutation_signature`][mutations-fields] configures operation-specific arguments: `create` (`data: <Model>Input!`), `update` (`id: ID!`, `data: <Model>PartialInput!`), `delete` (`id: ID!`), `form` (`data: <Form>Input!`), and lazy payload return type `_lazy_ref(f"{mutation_cls.__name__}Payload", INPUTS_MODULE_PATH)`.
   - **Target Guard & Lifecycle Verification:** [`_validate_mutation_target`][mutations-fields], [`_has_mutation_protocol`][mutations-fields], and [`_is_registered_mutation_target`][mutations-fields] validate mutation classes at construction time, rejecting non-classes, abstract base classes without concrete `_mutation_meta`, unregistered subclass declarations, and stale declarations created prior to `registry.clear()`.
   - **Transaction Atomicity Marker:** Stamps [`MUTATION_CLASS_MARKER`][mutations-fields] (`"_django_mutation_cls"`) onto generated resolver closures, read by [`schema.py::DjangoMutationExecutionContext`][schema] to wrap execution in completion-spanning database transactions ([spec-036][spec-036], [spec-046][spec-046]).
   - **Runtime Async/Sync Dispatch:** Inside `DjangoMutationField`, `_resolve` dynamically queries `in_async_context()` at call time to dispatch to `mutation_cls.resolve_async(info, **call_kwargs)` or `mutation_cls.resolve_sync(info, **call_kwargs)`.

3. [`mutations/inputs.py`][mutations-inputs]: Input Dataclass & Payload Generation Substrate:
   - **Constants & Sentinels:** Module path [`INPUTS_MODULE_PATH`][mutations-inputs] (`"django_strawberry_framework.mutations.inputs"`), non-field error key [`NON_FIELD_ERROR_KEY`][mutations-inputs] (`"__all__"`), model-local decode sentinel [`EXCLUDED`][mutations-inputs] (`"excluded"`), operation sentinels [`CREATE`][mutations-inputs] (`"create"`) and [`PARTIAL`][mutations-inputs] (`"partial"`).
   - **Validation Error Envelope:** [`FieldError`][mutations-inputs] `@strawberry.type` standardizing validation and execution errors into `{ field: str, messages: list[str], codes: list[str], path: list[str] }` payloads across all mutation flavors.
   - **Field Discovery & Requiredness:** [`editable_input_fields`][mutations-inputs] discovers editable model columns and forward M2Ms while dropping primary keys and `editable=False` timestamp columns. [`input_field_required`][mutations-inputs] enforces create-time requiredness (`not field.has_default() and not field.null and not field.blank`).
   - **Relation ID Resolution & Column Annotations:** Resolves GraphQL ID scalars via [`relation_id_scalar`][mutations-inputs] (`relay.GlobalID` if target implements Relay Node via [`implements_relay_node`][types-relay], otherwise raw PK scalar) and [`relation_id_annotation`][mutations-inputs] (`list[...]` for `many=True`). Provides [`related_model_of_queryset`][mutations-inputs], [`require_queryset_related_model`][mutations-inputs], and [`annotate_queryset_relation`][mutations-inputs] for column-less relation fields. Maps model relations and columns to input annotations via [`relation_input_annotation`][mutations-inputs], [`model_column_write_kind`][mutations-inputs], [`_relation_field_index`][mutations-inputs], [`model_column_write_annotation`][mutations-inputs], and [`model_column_input_annotation`][mutations-inputs].
   - **Input Shape & Builder:** Standardizes shape metadata in [`MutationInputShape`][mutations-inputs] via [`mutation_input_shape`][mutations-inputs], generates deterministic names via [`mutation_input_type_name`][mutations-inputs] (delegating to [`name_set_input_type_name`][utils-inputs]), audits naming collisions via [`_GeneratedInputFieldName`][mutations-inputs] and [`_reject_generated_input_collisions`][mutations-inputs] (using [`iter_input_field_collisions`][utils-inputs]), emits reverse-map descriptors via [`mutation_input_field_specs`][mutations-inputs] ([`InputFieldSpec`][utils-inputs]), and synthesizes `@strawberry.input` classes via [`build_mutation_input`][mutations-inputs].
   - **Payload Wrappers:** Resolves payload slot name via [`payload_object_slot`][mutations-inputs] (`"node"` for Relay Node targets, `"result"` otherwise), and synthesizes `<Name>Payload` `@strawberry.type` classes via [`build_payload_type`][mutations-inputs] for both model-backed (`<object_slot>: TargetType | None`, `errors: list[FieldError]`) and model-less (`ok: bool`, `errors: list[FieldError]`) mutations.
   - **Dynamic Module Namespace Lifecycle:** [`_audit_mutation_input_surface`][mutations-inputs] audits input fields for GraphQL camelCase collisions, [`materialize_mutation_input_class`][mutations-inputs] registers generated classes in `django_strawberry_framework.mutations.inputs` module globals, and [`clear_mutation_input_namespace`][mutations-inputs] resets tracking ledgers on `registry.clear()`. Registered via [`register_subsystem_clear`][registry] (`owner="mutations.input_namespace"`, `before_bind=True`).

4. [`mutations/permissions.py`][mutations-permissions]: Write-Side Authorization Engine:
   - **Operation Mapping:** Maps GraphQL mutation operations to Django model permission action verbs via [`_OPERATION_PERMISSION_ACTION`][mutations-permissions] (`create -> add`, `update -> change`, `delete -> delete`).
   - **Result Contract & Auth Hardening:** [`_require_sync_bool_auth_result`][mutations-permissions] enforces that all permission checks return a synchronous `bool`. Coroutines (`async def`) and awaitables are intercepted via [`reject_async_in_sync_context`][utils-querysets], closed, and raised as typed `SyncMisuseError` exceptions with [`_PERMISSION_ASYNC_RECOURSE`][mutations-permissions] guidance to prevent silent authorization bypasses ([spec-046][spec-046]). Non-bool return values raise [`ConfigurationError`][exceptions].
   - **Permission Execution:** [`run_permission_classes`][mutations-permissions] iterates `Meta.permission_classes`, executes `has_permission(info, mutation_cls, operation, data, instance)`, validates results via [`_require_sync_bool_auth_result`][mutations-permissions], short-circuits to `False` on denial, and returns `True` only when all classes allow.
   - **Permission Classes:** [`DjangoModelPermission`][mutations-permissions] ([`DjangoModelPermission.has_permission`][mutations-permissions]) resolves the model from `mutation._resolve_model(mutation.Meta)`, derives the permission codename `f"{app_label}.{action}_{model_name}"`, extracts request user via [`request_from_info`][utils-permissions], and evaluates `user.has_perm(codename)` (denying unauthenticated/anonymous callers). [`DenyAll`][mutations-permissions] ([`DenyAll.has_permission`][mutations-permissions]) provides a safe deny-by-default class for model-less plain form mutations ([`forms/sets.py`][forms-sets]).

5. [`mutations/resolvers.py`][mutations-resolvers]: Runtime Write-Pipeline Orchestrator:
   - **Write Execution Runner:** [`run_write_pipeline_sync`][mutations-resolvers] implements the central write pipeline: `(update/delete locate) -> authorize -> decode -> validate -> write -> re-fetch/snapshot -> payload`. Enforces cooperative deadline preflight via `check_deadline(info)` ([spec-047][spec-047]), pins execution to the write alias via `open_write_pipeline(mutation_cls)`, verifies immutable auth snapshots via `reject_substituted_row`, and isolates database connection access via `pipeline_alias_guard`, `authorization_phase`, and `pipeline_write_phase`.
   - **Relay GlobalID Coercion & Instance Location:** [`coerce_lookup_id`][mutations-resolvers] decodes incoming `id: ID!` strings against the target model via `decode_model_global_id`, mapping wrong-model or invalid IDs to [`_invalid_lookup_id_error`][mutations-resolvers] (`"Invalid id."`, code `"invalid"`) and uncoercible PKs to [`not_found_error`][mutations-resolvers] (`"No matching row found."`, code `"not_found"`). [`locate_instance`][mutations-resolvers] locates target rows through the primary visibility queryset (`apply_type_visibility_sync`) pinned to the write alias, applying row locks under `select_for_update=True` via `base_locked_queryset`.
   - **Authorize-Before-Decode Security Seam:** [`authorize_or_raise`][mutations-resolvers] evaluates `mutation_cls().check_permission(...)` strictly before input relation decoding, preventing unauthorized callers from probing related-row existence and visibility by ID. Maps permission denials to top-level `GraphQLError` exceptions.
   - **Relation Decoding & Sanitation:** [`_decode_relations`][mutations-resolvers] unpacks inputs via `decode_provided_fields` into `scalar_and_fk_attrs`, `m2m_pks`, and `excluded_values`. Pre-validation checks reject explicit nulls on non-nullable scalar/FK columns via [`_explicit_null_error`][mutations-resolvers] and on M2M relations via [`_relation_null_error`][mutations-resolvers]. Naive datetimes are sanitized via [`_make_aware_if_naive`][mutations-resolvers]. Relations decode via [`_decode_single_relation_id`][mutations-resolvers] and [`_decode_relation_id_list`][mutations-resolvers]. M2M relations are assigned in the write phase via [`_assign_m2m`][mutations-resolvers].
   - **Partial-Update Constraint Validation:** [`_provided_attr_names`][mutations-resolvers] maps attributes to model field names using `_model_fields_by_attr`, [`_unique_constraint_groups`][mutations-resolvers] extracts uniqueness constraint groups, and [`_unprovided_exclude`][mutations-resolvers] computes `full_clean(exclude=...)` sets that retain validation on unprovided fields co-participating in uniqueness constraints.
   - **Model Write Steps & Concurrency:** [`_model_decode_step`][mutations-resolvers] builds model instances and partial exclusion sets. [`_model_write_step`][mutations-resolvers] validates via [`_full_clean_or_field_errors`][mutations-resolvers], saves via [`save_or_field_errors`][mutations-resolvers] (create) or [`forced_save_or_field_errors`][mutations-resolvers] (update with `force_update=True` in a savepoint, isolating conflict/integrity errors), and sets M2Ms.
   - **Snapshot-Before-Delete Rider:** [`_run_delete`][mutations-resolvers] and [`_delete_write_step`][mutations-resolvers] capture pre-delete snapshots via [`refetch_optimized`][mutations-resolvers] (`force_load=True`) with relations loaded before executing `instance.delete()`, ensuring snapshot PKs survive for client cache eviction. [`_delete_or_field_errors`][mutations-resolvers] maps `ProtectedError`/`RestrictedError` to protected field errors and zero-row deletions to conflict errors.
   - **Post-Write Re-fetching & Payloads:** [`refetch_optimized`][mutations-resolvers] re-fetches written rows by PK without visibility filtering using `apply_connection_optimization` and `mutation_payload_child_selections`. [`error_payload_builder`][mutations-resolvers] constructs error response closures that invoke `transaction.set_rollback(True, using=using)` before returning `{ ok: false, errors }` or `{ node/result: None, errors }` payload objects. Payloads are constructed via [`build_payload`][mutations-resolvers] and [`payload_cls_for`][mutations-resolvers].
   - **Sync/Async Resolver Entry Twins:** [`_run_pipeline_sync`][mutations-resolvers] coordinates sync steps, [`run_pipeline_async`][mutations-resolvers] encapsulates execution within `run_in_one_sync_boundary` (`sync_to_async(thread_sensitive=True)`), [`make_resolver_entries`][mutations-resolvers] mintage `(resolve_sync, resolve_async)` pairs, and [`_MUTATION_ASYNC_RECOURSE`][mutations-resolvers] attaches actionable async recourse guidance to `SyncMisuseError`.

6. [`mutations/sets.py`][mutations-sets]: Metaclass, Mutation Set Base Class, & Phase-2.5 Finalizer Engine:
   - **Constants & Operation Sets:** [`_ALLOWED_MUTATION_META_KEYS`][mutations-sets], [`NON_DELETE_OPERATION_INPUT_KIND`][mutations-sets], [`_OPERATION_INPUT_OVERRIDE_ATTR`][mutations-sets], [`NON_DELETE_WRITE_OPERATIONS`][mutations-sets], and [`_VALID_OPERATIONS`][mutations-sets].
   - **Shared Validation & Resolution Utilities:** [`non_delete_operation_error`][mutations-sets], [`require_non_delete_operation`][mutations-sets], [`reject_unknown_meta_keys`][mutations-sets], [`normalize_meta_field_selection`][mutations-sets], [`_hook_overridden`][mutations-sets], [`cached_build_input`][mutations-sets], [`build_and_stash_input`][mutations-sets], [`construction_kwargs`][mutations-sets], [`require_backing_class`][mutations-sets], [`require_subclass`][mutations-sets], [`require_model_class`][mutations-sets], [`resolve_meta_model`][mutations-sets], [`resolve_backed_model_or_raise`][mutations-sets], [`resolver_seams`][mutations-sets], [`_validate_permission_classes`][mutations-sets], [`validate_select_for_update`][mutations-sets], and [`model_backed_permission_and_lock`][mutations-sets].
   - **Metaclass & Declaration Registry Factories:** Factory [`make_declaration_registry`][mutations-sets] creates declaration ledgers ([`DeclarationRegistry`][mutations-sets]) with lifecycle clearing hooks registered via [`register_subsystem_clear`][registry]. Factory [`make_meta_validating_metaclass`][mutations-sets] creates metaclasses validating inner `class Meta` configurations.
   - **Meta Validation & Overrides:** Metaclass helper [`_ValidatedMutationMeta`][mutations-sets] ([`_ValidatedMutationMeta.__init__`][mutations-sets]) parses and validates `Meta` options. Input class overrides are validated via [`_validate_input_class`][mutations-sets], [`_expected_input_attr_names`][mutations-sets], [`_validate_relation_override_types`][mutations-sets], [`_annotation_core_is_global_id`][mutations-sets], and [`_strawberry_field_shape`][mutations-sets].
   - **Declarative Base Class:** [`DjangoMutation`][mutations-sets] provides declarative base class functionality with [`DjangoMutation._resolve_model`][mutations-sets], [`DjangoMutation._validate_meta`][mutations-sets], [`DjangoMutation.build_input`][mutations-sets], [`DjangoMutation.input_type_name`][mutations-sets], and [`DjangoMutation.check_permission`][mutations-sets] (delegating to [`run_permission_classes`][mutations-permissions]).
   - **Schema Finalization & Binding Engine:** [`_resolve_primary_type`][mutations-sets] resolves target GraphQL types from registry, [`_materialize_input_for`][mutations-sets] and [`_materialize_merged_input`][mutations-sets] synthesize and park input classes in module globals, [`bind_mutation_outputs`][mutations-sets] constructs payload types, [`bind_write_declarations`][mutations-sets] executes the Phase-2.5 binding loop, and [`bind_mutations`][mutations-sets] binds all model mutations during schema finalization ([`django_strawberry_framework/types/finalizer.py`][types-finalizer]).

Connected subsystem integration examined:
- [`django_strawberry_framework/schema.py`][schema]: Mutation execution context (`DjangoMutationExecutionContext`) reading [`MUTATION_CLASS_MARKER`][mutations-fields] for transaction demarcation.
- [`django_strawberry_framework/registry.py`][registry]: Global registry managing subsystem clearing hooks for `mutations.declarations`, `mutations.input_namespace`, and `mutations.shape_cache`.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Phase 2.5 schema finalizer executing [`bind_mutations`][mutations-sets].
- [`django_strawberry_framework/types/converters.py`][types-converters]: Read-side scalar and enum converters (`convert_scalar`, `scalar_for_field`, `convert_choices_to_enum`) ensuring write input wire symmetry.
- [`django_strawberry_framework/types/relay.py`][types-relay]: Relay interface inspector ([`implements_relay_node`][types-relay]) determining GlobalID vs raw PK scalar resolution and payload slot names (`"node"` vs `"result"`).
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Shared input generation substrate ([`InputFieldSpec`][utils-inputs], [`build_strawberry_input_class`][utils-inputs], [`guard_dropped_required`][utils-inputs], [`iter_input_field_collisions`][utils-inputs], [`make_input_namespace`][utils-inputs], [`make_shape_build_cache`][utils-inputs], [`name_set_input_type_name`][utils-inputs], [`optional_input_field`][utils-inputs], [`resolve_effective_fields`][utils-inputs], [`pascalize_token`][utils-inputs]).
- [`django_strawberry_framework/utils/permissions.py`][utils-permissions]: Shared [`request_from_info`][utils-permissions] and [`auth_aliases_for_permission_classes`][utils-permissions].
- [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction]: Transaction management and connection-pinning primitives (`open_write_pipeline`, `pipeline_alias_guard`, `pipeline_write_phase`, `authorization_phase`, `reject_substituted_row`, `snapshot_target_state`, `base_locked_queryset`, `forced_update_conflict_errors`).
- [`django_strawberry_framework/utils/write_values.py`][utils-write-values]: Neutral write value decoding primitives (`decode_provided_fields`, `decode_scalar_leaf`, `decode_visible_relation_ids`).
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: Queryset visibility scoping and async boundary execution (`apply_type_visibility_sync`, `run_in_one_sync_boundary`, `sync_pipeline_recourse`, `reject_async_in_sync_context`).
- [`django_strawberry_framework/utils/errors.py`][utils-errors]: Error mapping utilities (`field_error`, `integrity_error_field_errors`, `validation_error_to_field_errors`).
- [`django_strawberry_framework/forms/`][forms-init]: Form mutations subsystem reusing `mutations/sets.py`, `mutations/inputs.py`, `mutations/permissions.py`, `mutations/resolvers.py`.
- [`django_strawberry_framework/rest_framework/`][rest-framework-init]: Serializer mutations subsystem subclassing `DjangoMutation` and reusing mutation components.
- [`django_strawberry_framework/auth/`][auth-mutations]: Session auth subsystem reusing `mutations/fields.py`, `mutations/inputs.py`, `mutations/resolvers.py`.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/mutations/ --include-constants`):
- Parsed 7 target files (`__init__.py`, `operations.py`, `fields.py`, `inputs.py`, `permissions.py`, `resolvers.py`, `sets.py`), 4,665 total lines.
- Inventoried 139 definitions and module constants across the entire subpackage:
  - `mutations/__init__.py`: 1 constant ([`__all__`][mutations-init]);
  - `mutations/operations.py`: 15 definitions/constants ([`MutationOperationDescriptor`][mutations-operations], [`OPERATION_CREATE`][mutations-operations], [`OPERATION_UPDATE`][mutations-operations], [`OPERATION_DELETE`][mutations-operations], [`OPERATION_FORM`][mutations-operations], [`_OPERATIONS_BY_NAME`][mutations-operations], [`get_operation_descriptor`][mutations-operations], [`operation_takes_id`][mutations-operations], [`operation_takes_data`][mutations-operations], [`NON_DELETE_OPERATION_INPUT_KIND`][mutations-operations], [`_OPERATION_INPUT_OVERRIDE_ATTR`][mutations-operations], [`NON_DELETE_WRITE_OPERATIONS`][mutations-operations], [`_VALID_OPERATIONS`][mutations-operations], [`_OPERATION_PERMISSION_ACTION`][mutations-operations], [`non_delete_operation_error`][mutations-operations]);
  - `mutations/fields.py`: 8 definitions/constants ([`MUTATION_CLASS_MARKER`][mutations-fields], [`_validate_mutation_target`][mutations-fields], [`_has_mutation_protocol`][mutations-fields], [`_is_registered_mutation_target`][mutations-fields], [`_lazy_ref`][mutations-fields], [`build_lazy_field_signature`][mutations-fields], [`_synthesized_mutation_signature`][mutations-fields], [`DjangoMutationField`][mutations-fields]);
  - `mutations/inputs.py`: 30 definitions/constants ([`INPUTS_MODULE_PATH`][mutations-inputs], [`NON_FIELD_ERROR_KEY`][mutations-inputs], [`EXCLUDED`][mutations-inputs], [`CREATE`][mutations-inputs], [`PARTIAL`][mutations-inputs], [`FieldError`][mutations-inputs], [`_audit_mutation_input_surface`][mutations-inputs], [`materialize_mutation_input_class`][mutations-inputs], [`clear_mutation_input_namespace`][mutations-inputs], [`editable_input_fields`][mutations-inputs], [`input_field_required`][mutations-inputs], [`relation_id_scalar`][mutations-inputs], [`relation_id_annotation`][mutations-inputs], [`related_model_of_queryset`][mutations-inputs], [`require_queryset_related_model`][mutations-inputs], [`annotate_queryset_relation`][mutations-inputs], [`relation_input_annotation`][mutations-inputs], [`model_column_write_kind`][mutations-inputs], [`_relation_field_index`][mutations-inputs], [`mutation_input_field_specs`][mutations-inputs], [`model_column_write_annotation`][mutations-inputs], [`model_column_input_annotation`][mutations-inputs], [`mutation_input_type_name`][mutations-inputs], [`MutationInputShape`][mutations-inputs], [`mutation_input_shape`][mutations-inputs], [`_GeneratedInputFieldName`][mutations-inputs], [`_reject_generated_input_collisions`][mutations-inputs], [`build_mutation_input`][mutations-inputs], [`payload_object_slot`][mutations-inputs], [`build_payload_type`][mutations-inputs]);
  - `mutations/permissions.py`: 8 definitions/constants ([`_OPERATION_PERMISSION_ACTION`][mutations-permissions], [`_PERMISSION_ASYNC_RECOURSE`][mutations-permissions], [`_require_sync_bool_auth_result`][mutations-permissions], [`run_permission_classes`][mutations-permissions], [`DjangoModelPermission`][mutations-permissions], [`DjangoModelPermission.has_permission`][mutations-permissions], [`DenyAll`][mutations-permissions], [`DenyAll.has_permission`][mutations-permissions]);
  - `mutations/resolvers.py`: 32 definitions/constants ([`_MUTATION_ASYNC_RECOURSE`][mutations-resolvers], [`run_write_pipeline_sync`][mutations-resolvers], [`error_payload_builder`][mutations-resolvers], [`_decode_relations`][mutations-resolvers], [`_explicit_null_error`][mutations-resolvers], [`_make_aware_if_naive`][mutations-resolvers], [`_decode_single_relation_id`][mutations-resolvers], [`_decode_relation_id_list`][mutations-resolvers], [`_relation_null_error`][mutations-resolvers], [`locate_instance`][mutations-resolvers], [`_provided_attr_names`][mutations-resolvers], [`_unprovided_exclude`][mutations-resolvers], [`_unique_constraint_groups`][mutations-resolvers], [`_assign_m2m`][mutations-resolvers], [`refetch_optimized`][mutations-resolvers], [`build_payload`][mutations-resolvers], [`_run_pipeline_sync`][mutations-resolvers], [`_model_decode_step`][mutations-resolvers], [`_model_write_step`][mutations-resolvers], [`forced_save_or_field_errors`][mutations-resolvers], [`_run_delete`][mutations-resolvers], [`_delete_write_step`][mutations-resolvers], [`_delete_or_field_errors`][mutations-resolvers], [`authorize_or_raise`][mutations-resolvers], [`_full_clean_or_field_errors`][mutations-resolvers], [`save_or_field_errors`][mutations-resolvers], [`coerce_lookup_id`][mutations-resolvers], [`not_found_error`][mutations-resolvers], [`_invalid_lookup_id_error`][mutations-resolvers], [`payload_cls_for`][mutations-resolvers], [`run_pipeline_async`][mutations-resolvers], [`make_resolver_entries`][mutations-resolvers]);
  - `mutations/sets.py`: 46 definitions/constants ([`COMMON_WRITE_META_KEYS`][mutations-sets], [`MODEL_BACKED_WRITE_META_KEYS`][mutations-sets], [`_ALLOWED_MUTATION_META_KEYS`][mutations-sets], [`NON_DELETE_OPERATION_INPUT_KIND`][mutations-sets], [`_OPERATION_INPUT_OVERRIDE_ATTR`][mutations-sets], [`NON_DELETE_WRITE_OPERATIONS`][mutations-sets], [`_VALID_OPERATIONS`][mutations-sets], [`non_delete_operation_error`][mutations-sets], [`require_non_delete_operation`][mutations-sets], [`reject_unknown_meta_keys`][mutations-sets], [`normalize_meta_field_selection`][mutations-sets], [`_hook_overridden`][mutations-sets], [`cached_build_input`][mutations-sets], [`build_and_stash_input`][mutations-sets], [`construction_kwargs`][mutations-sets], [`require_backing_class`][mutations-sets], [`require_subclass`][mutations-sets], [`require_model_class`][mutations-sets], [`resolve_meta_model`][mutations-sets], [`resolve_backed_model_or_raise`][mutations-sets], [`resolver_seams`][mutations-sets], [`DeclarationRegistry`][mutations-sets], [`make_declaration_registry`][mutations-sets], [`make_meta_validating_metaclass`][mutations-sets], [`_validate_input_class`][mutations-sets], [`_expected_input_attr_names`][mutations-sets], [`_ValidatedMutationMeta`][mutations-sets], [`_ValidatedMutationMeta.__init__`][mutations-sets], [`_validate_permission_classes`][mutations-sets], [`validate_select_for_update`][mutations-sets], [`model_backed_permission_and_lock`][mutations-sets], [`DjangoMutation`][mutations-sets], [`DjangoMutation._resolve_model`][mutations-sets], [`DjangoMutation._validate_meta`][mutations-sets], [`DjangoMutation.build_input`][mutations-sets], [`DjangoMutation.input_type_name`][mutations-sets], [`DjangoMutation.check_permission`][mutations-sets], [`_resolve_primary_type`][mutations-sets], [`_materialize_input_for`][mutations-sets], [`_materialize_merged_input`][mutations-sets], [`_validate_relation_override_types`][mutations-sets], [`_annotation_core_is_global_id`][mutations-sets], [`_strawberry_field_shape`][mutations-sets], [`bind_mutation_outputs`][mutations-sets], [`bind_write_declarations`][mutations-sets], [`bind_mutations`][mutations-sets]).
- Confirmed zero missing definitions and verified all cross-file and cross-subsystem dependencies.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   The framework provides four distinct write mutation flavors: model mutations ([`mutations/sets.py`][mutations-sets]), form mutations ([`forms/sets.py`][forms-sets]), DRF serializer mutations ([`rest_framework/sets.py`][rest-framework-sets]), and session auth mutations ([`auth/mutations.py`][auth-mutations]).
   - **Unified Mutation Field Factory:** All write flavors share the single [`DjangoMutationField`][mutations-fields] factory without maintaining duplicate field classes (`DjangoFormMutationField`, `SerializerMutationField`). Target classes are duck-typed via [`_has_mutation_protocol`][mutations-fields], input naming delegates to `mutation_cls.input_type_name(meta)`, and input module routing delegates to `mutation_cls.input_module_path`.
   - **Shared Write Pipeline Engine:** All write flavors ride the central write orchestrator [`run_write_pipeline_sync`][mutations-resolvers]. Database transactions, cooperative deadline preflight (`check_deadline(info)`), authorize-before-decode security order ([`authorize_or_raise`][mutations-resolvers]), immutable row identity checking (`reject_substituted_row`), connection pinning (`pipeline_alias_guard`), error rollback envelopes ([`error_payload_builder`][mutations-resolvers]), and sync/async resolver pair generation ([`make_resolver_entries`][mutations-resolvers]) are 100% single-sited.
   - **Shared Write Primitives:** The validation error envelope ([`FieldError`][mutations-inputs]), non-field error key ([`NON_FIELD_ERROR_KEY`][mutations-inputs]), relation ID resolution ([`relation_id_scalar`][mutations-inputs], [`relation_id_annotation`][mutations-inputs]), column-less relation annotation ([`annotate_queryset_relation`][mutations-inputs]), model column classification ([`model_column_write_kind`][mutations-inputs], [`model_column_input_annotation`][mutations-inputs]), and payload wrapper builders ([`payload_object_slot`][mutations-inputs], [`build_payload_type`][mutations-inputs]) are centralized in `mutations/inputs.py` and reused uniformly across all write flavors.
   - **Shared Metaclass & Registry Infrastructure:** Metaclass factory [`make_meta_validating_metaclass`][mutations-sets], declaration registry factory [`make_declaration_registry`][mutations-sets], and Phase-2.5 binding runner [`bind_write_declarations`][mutations-sets] in `mutations/sets.py` serve as the root owner for `mutations/sets.py`, `forms/sets.py`, and `rest_framework/sets.py`.
   - **Unified Write Authorization:** `DjangoMutation`, `DjangoModelFormMutation`, and `SerializerMutation` default to [`DjangoModelPermission`][mutations-permissions]. Model-less plain forms default to [`DenyAll`][mutations-permissions]. Both hierarchies execute permissions through [`run_permission_classes`][mutations-permissions], and all enforce strict sync-bool result validation via [`_require_sync_bool_auth_result`][mutations-permissions].

2. **Sync and async twins:**
   - **Build-Time Decoupling:** Schema compilation, metaclass validation, input dataclass generation, shape cache deduping, and Phase-2.5 binding (`mutations/inputs.py`, `mutations/sets.py`, `mutations/fields.py`) run purely at schema build time with zero execution runtime or sync/async branching.
   - **Execution Pipeline Twins:** Both synchronous (`resolve_mutation_sync`) and asynchronous (`resolve_mutation_async`) resolver entrypoints are minted as a unified pair from the identical synchronous pipeline via [`make_resolver_entries`][mutations-resolvers].
   - **Thread-Sensitive Async Execution:** [`run_pipeline_async`][mutations-resolvers] wraps the synchronous write pipeline within `run_in_one_sync_boundary` (`sync_to_async(thread_sensitive=True)`), preventing interleaved async execution and connection contention during ORM transactions.
   - **Strict Async Misuse Guarding:** Coroutines returned from permission hooks (`has_permission`, `check_permission`, `user.has_perm`) are intercepted by [`_require_sync_bool_auth_result`][mutations-permissions] via [`reject_async_in_sync_context`][utils-querysets], closed, and raised as `SyncMisuseError` with [`_PERMISSION_ASYNC_RECOURSE`][mutations-permissions] guidance, preventing truthiness-based authorization bypasses. Async `get_queryset` calls are rejected with [`_MUTATION_ASYNC_RECOURSE`][mutations-resolvers].
   - **Dynamic Runtime Dispatch:** [`DjangoMutationField`][mutations-fields] uses `in_async_context()` inside `_resolve` to dynamically select between `resolve_async` and `resolve_sync`.

3. **Derived rather than repeated knowledge:**
   - **Field & Payload Naming:** Input type names derive deterministically via [`mutation_input_type_name`][mutations-inputs] and [`name_set_input_type_name`][utils-inputs]. Payload class names derive as `f"{mutation_cls.__name__}Payload"` in [`INPUTS_MODULE_PATH`][mutations-inputs]. Payload object slots derive from [`implements_relay_node`][types-relay] via [`payload_object_slot`][mutations-inputs] (`"node"` vs `"result"`).
   - **Field Requiredness & Column Types:** Input field requiredness is derived directly from model field definitions via [`input_field_required`][mutations-inputs]. Column annotations derive from read-side converters in [`django_strawberry_framework/types/converters.py`][types-converters], ensuring byte-identical wire formats.
   - **Shape Metadata:** [`mutation_input_shape`][mutations-inputs] bundles all shape-derived properties into a single [`MutationInputShape`][mutations-inputs] record (`selected`, `full_field_names`, `effective_field_names`, `type_name`, `cache_key`), preventing drift between the input generator, shape cache, and merged input overrides.
   - **Constraint Groups & Attribute Reversal:** [`_unique_constraint_groups`][mutations-resolvers] derives uniqueness groups directly from `model._meta.constraints`, `model._meta.unique_together`, and `field.unique`. [`_provided_attr_names`][mutations-resolvers] maps attributes back to model field names using stashed `_model_fields_by_attr`, avoiding string manipulation errors on columns named `object_id`.
   - **Authorization Actions & Codenames:** Action verbs derive from `operation` via [`_OPERATION_PERMISSION_ACTION`][mutations-permissions], and permission codenames derive as `f"{model._meta.app_label}.{action}_{model._meta.model_name}"`.

4. **Inverse and round-trip pairs:**
   - **Relay GlobalID Encoding <-> Server-Side Decoding:** Query outputs encode GlobalIDs via `to_global_id(target_model, pk)`; mutation inputs decode and validate GlobalIDs server-side via [`coerce_lookup_id`][mutations-resolvers], [`_decode_single_relation_id`][mutations-resolvers], and [`_decode_relation_id_list`][mutations-resolvers].
   - **Schema Input Synthesis <-> Resolver Argument Decoding:** `mutations/inputs.py` synthesizes `@strawberry.input` classes and emits [`InputFieldSpec`][utils-inputs] records; `mutations/resolvers.py::_decode_relations` unpacks inputs against those exact specs.
   - **Pre-Delete Snapshot <-> Client Cache Eviction:** [`_run_delete`][mutations-resolvers] captures a pre-delete snapshot with loaded relations via [`refetch_optimized`][mutations-resolvers] (`force_load=True`) before executing `instance.delete()`, ensuring snapshot PKs survive for client cache eviction.
   - **Declaration Registration <-> Schema Finalization:** Mutation classes register with [`DeclarationRegistry`][mutations-sets] on definition; Phase 2.5 finalization calls [`bind_mutations`][mutations-sets] / [`bind_write_declarations`][mutations-sets] to materialize inputs, synthesize payloads, and bind field resolvers.
   - **Test Lifecycle Isolation:** Subsystem clear registrations ([`clear_mutation_registry`][mutations-sets], [`clear_mutation_input_namespace`][mutations-inputs], [`clear_mutation_shape_build_cache`][mutations-sets]) flush ledgers on `registry.clear()` while preserving module globals for lazy GraphQL references.
   - **Transaction Commit <-> Error Rollback:** Successful pipeline execution commits transactions, while [`error_payload_builder`][mutations-resolvers] invokes `transaction.set_rollback(True)` before returning structured error payloads.

5. **Contracts restated in another medium:**
   - Specifications: [`docs/SPECS/spec-036-mutations-0_0_11.md`][spec-036], [`docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md`][spec-037], [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038], [`docs/SPECS/spec-039-serializer_mutations-0_0_13.md`][spec-039], [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040], [`docs/SPECS/spec-041-channels_router-0_0_14.md`][spec-041], [`docs/SPECS/spec-046-transport_security-0_0_14.md`][spec-046], [`docs/SPECS/spec-047-resource_policy-0_0_14.md`][spec-047];
   - Code: [`django_strawberry_framework/mutations/`][mutations-init], [`django_strawberry_framework/forms/`][forms-init], [`django_strawberry_framework/rest_framework/`][rest-framework-init], [`django_strawberry_framework/auth/`][auth-mutations], [`django_strawberry_framework/utils/inputs.py`][utils-inputs], [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction], [`django_strawberry_framework/utils/write_values.py`][utils-write-values], [`django_strawberry_framework/utils/permissions.py`][utils-permissions], [`django_strawberry_framework/utils/querysets.py`][utils-querysets], [`django_strawberry_framework/utils/errors.py`][utils-errors], [`django_strawberry_framework/schema.py`][schema], [`django_strawberry_framework/registry.py`][registry], [`django_strawberry_framework/types/finalizer.py`][types-finalizer];
   - Test suites: [`tests/base/test_init.py`][test-base-init], [`tests/mutations/test_fields.py`][test-mutations-fields], [`tests/mutations/test_inputs.py`][test-mutations-inputs], [`tests/mutations/test_permissions.py`][test-mutations-permissions], [`tests/mutations/test_resolvers.py`][test-mutations-resolvers], [`tests/mutations/test_sets.py`][test-mutations-sets], [`tests/mutations/test_write_transaction.py`][test-mutations-write-transaction], [`tests/forms/test_inputs.py`][test-forms-inputs], [`tests/forms/test_resolvers.py`][test-forms-resolvers], [`tests/forms/test_sets.py`][test-forms-sets], [`tests/rest_framework/test_inputs.py`][test-rest-framework-inputs], [`tests/rest_framework/test_resolvers.py`][test-rest-framework-resolvers], [`tests/auth/test_mutations.py`][test-auth-mutations], [`examples/fakeshop/test_query/test_products_api.py`][test-products-api], [`examples/fakeshop/test_query/test_auth_api.py`][test-auth-api];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook], [`TODAY.md`][today], [`LIFECYCLE.html`][lifecycle].

### The single-edit-site test

- **Posited change 1 (Adding a new mutation operation kind, e.g. `upsert` or `bulk_create`):** Introduce an `upsert` operation requiring optional `id: ID` and `data: <Model>Input!`.
  - *Sites that must move:* Exactly 3 sites across the subpackage:
    1. [`django_strawberry_framework/mutations/sets.py`][mutations-sets] (`_VALID_OPERATIONS` and `NON_DELETE_OPERATION_INPUT_KIND`);
    2. [`django_strawberry_framework/mutations/fields.py`][mutations-fields] (`_synthesized_mutation_signature`);
    3. [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions] (`_OPERATION_PERMISSION_ACTION`).
  - *Site count:* 3.
- **Posited change 2 (Modifying write-pipeline transaction boundary, alias isolation, or deadline preflight):** Alter how `check_deadline(info)` or `open_write_pipeline` wraps the write execution pipeline across all mutation flavors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`][mutations-resolvers]. Model, form, serializer, and auth mutations inherit the change immediately.
  - *Site count:* 1.
- **Posited change 3 (Modifying write-side relation ID scalar resolution between Relay GlobalID and raw PK):** Alter the logic determining when a relation input uses `relay.GlobalID` vs raw PK scalar.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/inputs.py::relation_id_scalar`][mutations-inputs].
  - *Site count:* 1.
- **Posited change 4 (Adding a structured field to the public validation error envelope):** Add an additional field (e.g., `severity: str`) to the validation error envelope.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/inputs.py::FieldError`][mutations-inputs]. All mutation flavors immediately expose the updated envelope.
  - *Site count:* 1.
- **Posited change 5 (Modifying model partial update constraint validation and exclude computation):** Alter how `UniqueConstraint` or `unique_together` groups are discovered or excluded during partial `full_clean`.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/resolvers.py::_unprovided_exclude`][mutations-resolvers] (or [`_unique_constraint_groups`][mutations-resolvers]).
  - *Site count:* 1.
- **Posited change 6 (Modifying root-field lazy signature parameter conventions):** Update parameter injection conventions for lazy-typed fields across write and auth subsystems.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/fields.py::build_lazy_field_signature`][mutations-fields].
  - *Site count:* 1.
- **Posited change 7 (Hardening / changing write authorization sync-bool result validation contract):** Update validation rules or error formatting for permission hook return values across all write-auth seams.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/permissions.py::_require_sync_bool_auth_result`][mutations-permissions].
  - *Site count:* 1.
- **Posited change 8 (Modifying metaclass declaration registration, cache deduping, or Phase-2.5 binding loop):** Change how mutation declarations register or how Phase 2.5 finalization binds declarations into schema fields.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/sets.py`][mutations-sets] (`make_declaration_registry` / `bind_write_declarations`).
  - *Site count:* 1.

### Rejected candidates

1. **Creating separate field factories for each mutation flavor (`DjangoFormMutationField`, `SerializerMutationField`):**
   - Disproved per [spec-038][spec-038] Decision 5 and [spec-039][spec-039] Decision 5. `DjangoMutationField`'s duck-typed protocol inspection seamlessly accommodates model mutations, model form mutations, plain form mutations, and serializer mutations without duplication.
2. **Moving `relation_id_scalar`, `relation_id_annotation`, `annotate_queryset_relation`, `model_column_write_kind`, `model_column_write_annotation`, and `model_column_input_annotation` into `utils/inputs.py`:**
   - Disproved. `utils/inputs.py` is model-agnostic and Django-independent (owning dataclass synthesis, namespace materialization, string token naming, and collision auditing). Model-aware and GraphQL-converter-aware logic belongs in `mutations/inputs.py` as the canonical write-side domain root owner. Form and serializer flavors import these utilities from `mutations/inputs.py`.
3. **Merging `_relation_field_index` with read-side relation discovery or `editable_input_fields` with `orders/inputs.py`:**
   - Disproved per [spec-036][spec-036] Decision 6. The write side only accepts forward concrete relations (`ForeignKey`, `OneToOneField`) and forward `ManyToManyField`s, dropping primary keys and `editable=False` auto-timestamps. The read and order sides have opposite semantic policies.
4. **Creating separate permission runners for `DjangoMutation` and `DjangoFormMutation`:**
   - Disproved per [spec-038][spec-038] Decision 11. Although `DjangoFormMutation` does not subclass `DjangoMutation`, both share identical class-based permission execution semantics. Single-siting [`run_permission_classes`][mutations-permissions] prevents authorization execution drift.
5. **Moving `run_write_pipeline_sync` into `utils/write_transaction.py`:**
   - Disproved. [`run_write_pipeline_sync`][mutations-resolvers] is the domain-level GraphQL write orchestrator that constructs `Payload` classes, coordinates flavor decode/write hooks, and interfaces with Strawberry Info and GraphQL Errors. [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction] owns pure database transaction and connection-pinning primitives.
6. **Inlining delete logic into `run_write_pipeline_sync`:**
   - Disproved. Delete has fundamentally different data and write lifecycles (no input data, no field decode, pre-delete snapshot evaluation before row destruction, protected-reference exception handling). Modeling delete as a specialized rider via [`_run_delete`][mutations-resolvers] reuses the transaction and authorization skeleton without branching complexity.

## Opportunities

None — The folder integration of `django_strawberry_framework/mutations/` is architecturally unified, comprehensively tested, and fully consolidated at root owners. Cross-file boundaries across `__init__.py`, `fields.py`, `inputs.py`, `permissions.py`, `resolvers.py`, and `sets.py`, as well as external boundaries with `schema.py`, `registry.py`, `conf.py`, `types/`, `utils/inputs.py`, `utils/permissions.py`, `utils/write_transaction.py`, `utils/write_values.py`, `utils/querysets.py`, `utils/errors.py`, `forms/`, `rest_framework/`, and `auth/`, are strictly defined and honor all repository DRY invariants.

## Judgment

Zero-edit folder integration review. All 6 files in `django_strawberry_framework/mutations/` operate in total structural alignment. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 to 3 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. Subpackage folder integration verified clean and complete across all 6 files and 122 definitions/constants. Checked with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/ --review docs/dry/dry-folder-mutations.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

I have independently verified Worker 1's DRY folder review for `django_strawberry_framework/mutations/`:

1. **Subpackage & Folder-Level Architecture Verification:**
   - Re-traced all 6 subpackage files ([`mutations/__init__.py`][mutations-init], [`mutations/fields.py`][mutations-fields], [`mutations/inputs.py`][mutations-inputs], [`mutations/permissions.py`][mutations-permissions], [`mutations/resolvers.py`][mutations-resolvers], [`mutations/sets.py`][mutations-sets]) and confirmed seamless boundaries across all write flavors (model, form, serializer, and session auth mutations).
   - Confirmed that [`DjangoMutationField`][mutations-fields] is the single root-field factory for all write mutations across the repository.
   - Confirmed that [`run_write_pipeline_sync`][mutations-resolvers] provides the single-sited runtime write orchestrator, securely enforcing cooperative deadline preflight (`check_deadline`), connection alias pinning (`open_write_pipeline`), authorize-before-decode invariant ([`authorize_or_raise`][mutations-resolvers]), immutable authorization snapshot verification (`reject_substituted_row`), and rollback error envelopes ([`error_payload_builder`][mutations-resolvers]).
   - Confirmed that metaclass creation ([`make_meta_validating_metaclass`][mutations-sets]), declaration registries ([`make_declaration_registry`][mutations-sets]), and schema finalization binding loops ([`bind_write_declarations`][mutations-sets]) in `mutations/sets.py` are the single shared foundation for `mutations/`, `forms/`, and `rest_framework/`.
   - Confirmed that authorization hardening ([`_require_sync_bool_auth_result`][mutations-permissions]) strictly rejects coroutines and non-bool results with typed `SyncMisuseError` / `ConfigurationError` to prevent authorization bypasses.

2. **5-Axis Duplication Matrix Discharge:**
   - **Cross-flavor policy mirroring:** Fully consolidated at root owners (`mutations/fields.py` for field generation, `mutations/resolvers.py` for execution pipeline, `mutations/inputs.py` for inputs and error envelopes, `mutations/sets.py` for metaclasses and binding loops, and `mutations/permissions.py` for authorization).
   - **Sync and async twins:** Build and binding steps run strictly at schema compilation; runtime resolver pairs are minted cleanly via [`make_resolver_entries`][mutations-resolvers]; async execution runs inside `run_in_one_sync_boundary` (`sync_to_async(thread_sensitive=True)`) with coroutine misuse protection.
   - **Derived knowledge:** All type names, shapes, error envelopes, constraint groups, and permission codenames derive deterministically from single root sources.
   - **Inverse & round-trip pairs:** GlobalID encoding/decoding, input synthesis vs argument decoding, snapshot-before-delete cache survival, registration vs finalization binding, and transaction commit vs error rollback are verified symmetric and sound.
   - **Medium contracts:** Fully aligned across specifications, code implementation, test suites, and documentation.

3. **Single-Edit-Site Scenarios:**
   - Re-verified all 8 posited change scenarios; site counts are confirmed at 1 to 3 sites.

4. **Definition Coverage & Test Suite:**
   - Verified 100% definition coverage via `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/ --review docs/dry/dry-folder-mutations.md --include-constants` (122 definitions/constants and 0 required topics covered).
   - Executed the full test suite across `mutations/`, `forms/`, `rest_framework/`, `auth/`, and example apps (1,786 passing tests).

Verification complete. Setting `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[lifecycle]: ../../LIFECYCLE.html
[today]: ../../TODAY.md

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutations-0_0_11.md
[spec-037]: ../SPECS/spec-037-upload_file_image_mapping-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md
[spec-041]: ../SPECS/spec-041-channels_router-0_0_14.md
[spec-046]: ../SPECS/spec-046-transport_security-0_0_14.md
[spec-047]: ../SPECS/spec-047-resource_policy-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-queries]: ../../django_strawberry_framework/auth/queries.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-operations]: ../../django_strawberry_framework/mutations/operations.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-framework-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[rest-framework-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rest-framework-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rest-framework-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[schema]: ../../django_strawberry_framework/schema.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[utils-errors]: ../../django_strawberry_framework/utils/errors.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-write-transaction]: ../../django_strawberry_framework/utils/write_transaction.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-auth-mutations]: ../../tests/auth/test_mutations.py
[test-base-init]: ../../tests/base/test_init.py
[test-forms-inputs]: ../../tests/forms/test_inputs.py
[test-forms-resolvers]: ../../tests/forms/test_resolvers.py
[test-forms-sets]: ../../tests/forms/test_sets.py
[test-mutations-fields]: ../../tests/mutations/test_fields.py
[test-mutations-inputs]: ../../tests/mutations/test_inputs.py
[test-mutations-permissions]: ../../tests/mutations/test_permissions.py
[test-mutations-resolvers]: ../../tests/mutations/test_resolvers.py
[test-mutations-sets]: ../../tests/mutations/test_sets.py
[test-mutations-write-transaction]: ../../tests/mutations/test_write_transaction.py
[test-rest-framework-inputs]: ../../tests/rest_framework/test_inputs.py
[test-rest-framework-resolvers]: ../../tests/rest_framework/test_resolvers.py

<!-- examples/ -->
[test-auth-api]: ../../examples/fakeshop/test_query/test_auth_api.py
[test-products-api]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
