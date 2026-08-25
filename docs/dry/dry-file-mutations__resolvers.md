# DRY review: `django_strawberry_framework/mutations/resolvers.py`

Status: verified

## System trace

`django_strawberry_framework/mutations/resolvers.py` is the runtime write-orchestration engine of the framework ([spec-036][spec-036], [spec-037][spec-037], [spec-038][spec-038], [spec-039][spec-039], [spec-040][spec-040], [spec-047][spec-047]). It implements the shared synchronous and asynchronous write execution pipeline ([`run_write_pipeline_sync`][mutations-resolvers], [`run_pipeline_async`][mutations-resolvers], [`make_resolver_entries`][mutations-resolvers]), server-side Relay GlobalID coercion and lookup ([`coerce_lookup_id`][mutations-resolvers], [`locate_instance`][mutations-resolvers]), authorize-before-decode security lifecycle enforcement ([`authorize_or_raise`][mutations-resolvers]), relation input decoding ([`_decode_relations`][mutations-resolvers], [`_decode_single_relation_id`][mutations-resolvers], [`_decode_relation_id_list`][mutations-resolvers]), partial-update uniqueness constraint exclude calculation ([`_unprovided_exclude`][mutations-resolvers], [`_unique_constraint_groups`][mutations-resolvers]), model validation and persistence ([`_model_decode_step`][mutations-resolvers], [`_model_write_step`][mutations-resolvers], [`_full_clean_or_field_errors`][mutations-resolvers], [`save_or_field_errors`][mutations-resolvers], [`forced_save_or_field_errors`][mutations-resolvers]), pre-delete snapshot capture and deletion ([`_run_delete`][mutations-resolvers], [`_delete_write_step`][mutations-resolvers], [`_delete_or_field_errors`][mutations-resolvers]), post-write optimizer-planned re-fetching ([`refetch_optimized`][mutations-resolvers]), and standardized rollback-aware error payload construction ([`error_payload_builder`][mutations-resolvers], [`build_payload`][mutations-resolvers], [`payload_cls_for`][mutations-resolvers], [`not_found_error`][mutations-resolvers], [`_invalid_lookup_id_error`][mutations-resolvers], [`_relation_null_error`][mutations-resolvers], [`_explicit_null_error`][mutations-resolvers], [`_make_aware_if_naive`][mutations-resolvers], [`_assign_m2m`][mutations-resolvers], [`_provided_attr_names`][mutations-resolvers], [`_run_pipeline_sync`][mutations-resolvers], [`_MUTATION_ASYNC_RECOURSE`][mutations-resolvers]).

1. **Write-Pipeline Orchestration and Security Invariants ([spec-036][spec-036] Decision 8, [spec-047][spec-047]):**
   - The write execution pipeline enforces the strict sequence:
     `(update/delete) locate -> authorize -> decode -> validate -> write -> re-fetch/snapshot -> payload`
   - **Deadline Preflight ([spec-047][spec-047]):** [`run_write_pipeline_sync`][mutations-resolvers] invokes `check_deadline(info)` before opening database transactions, refusing operations whose cooperative budget has expired before partial transaction allocation.
   - **Pinned Write-Pipeline Boundary:** Database interactions run inside `open_write_pipeline(mutation_cls)` which pins execution to the router's designated write alias `using` and ensures schema-level transaction atomicity.
   - **Authorize-Before-Decode Security Order ([spec-036][spec-036] Decision 8 step 3, Decision 15):** Authorization via [`authorize_or_raise`][mutations-resolvers] executes strictly before flavor `decode_step`. Because relation decoding queries related-model visibility querysets, executing decode prior to authorization would allow unauthorized callers to probe related-row existence and visibility by ID.
   - **Immutable Auth Snapshot and Substitution Rejection:** Immediately following instance location, the target PK is captured as an immutable snapshot in `pipeline_context.authorized_pk` and `pipeline_context.target_state`. Downstream steps verify row identity via `reject_substituted_row`, preventing consumer hooks or write steps from swapping the mutable model instance to a different PK.
   - **Phased Alias Guarding:** Database connections are guarded by `pipeline_alias_guard(mutation_cls.__name__, using)` across all phases. Read-only permissions on auth aliases are isolated to `authorization_phase(auth_aliases)`, while mutating SQL operations are strictly confined to `pipeline_write_phase()`.

2. **Server-Side Relay GlobalID Lookup and Row Locking ([spec-036][spec-036] Decision 10):**
   - [`coerce_lookup_id`][mutations-resolvers]: Type-checks and decodes incoming `id: ID!` strings against the target model via `decode_model_global_id`. Unresolvable or mismatched model IDs map to [`_invalid_lookup_id_error`][mutations-resolvers] (`"Invalid id."`, code `"invalid"`), while invalid PK literals map to [`not_found_error`][mutations-resolvers] (`"No matching row found."`, code `"not_found"`), preventing model schema and column type leakage.
   - [`locate_instance`][mutations-resolvers]: Resolves the target row through the target type's primary visibility queryset (`apply_type_visibility_sync`), pinned to the write alias via `pin_write_queryset`. Missing or hidden rows return `None` (mapped to [`not_found_error`][mutations-resolvers] without leaking existence). Under `select_for_update=True`, acquires row-level locks via `base_locked_queryset` using a PK subquery inside the active transaction.

3. **Relation Decoding and Value Sanitation ([spec-036][spec-036] Decision 8 step 1, [spec-037][spec-037], [spec-040][spec-040] D6):**
   - [`_decode_relations`][mutations-resolvers]: Iterates bind-time `InputFieldSpec` records using `decode_provided_fields` to partition inputs into `scalar_and_fk_attrs`, `m2m_pks`, and `excluded_values`.
   - [`_explicit_null_error`][mutations-resolvers]: Rejects explicit `null` on `null=False` scalar and FK columns before `full_clean()`, preventing Django's `blank=True` empty-value bypass from causing un-attributed NOT NULL `IntegrityError` failures at save time.
   - [`_make_aware_if_naive`][mutations-resolvers]: Sanitizes naive `datetime` objects to timezone-aware instances under `settings.USE_TZ=True`.
   - [`_decode_single_relation_id`][mutations-resolvers] & [`_decode_relation_id_list`][mutations-resolvers]: Decode FK and M2M relation IDs via `decode_visible_relation_ids`. M2M inputs reject explicit `null` via [`_relation_null_error`][mutations-resolvers] (directing clients to send `[]` to clear relations).
   - [`_assign_m2m`][mutations-resolvers]: Executes `getattr(instance, m2m_name).set(pks)` for provided M2M assignments inside the write phase.

4. **Partial-Update Constraint Validation ([spec-036][spec-036] Decision 8 step 4, M3-1):**
   - [`_provided_attr_names`][mutations-resolvers]: Maps decoded attributes back to Django model field names using `mutation_cls._model_fields_by_attr` to prevent substring-stripping corruption on fields named `object_id`.
   - [`_unique_constraint_groups`][mutations-resolvers]: Gathers uniqueness constraint sets from `model._meta.constraints` (`UniqueConstraint`), `model._meta.unique_together`, and single-field `field.unique` columns.
   - [`_unprovided_exclude`][mutations-resolvers]: Calculates the exclude set for partial update `full_clean(exclude=...)`, excluding unprovided fields while preserving validation on any unprovided field that co-participates in a uniqueness group with a provided field.

5. **Model Write Pipeline and Concurrency Hardening ([spec-036][spec-036] Decision 8 step 4):**
   - [`_model_decode_step`][mutations-resolvers]: Decodes input attributes, instantiates new model instances (create) or updates existing instances (update), and computes partial validation exclusions. Preserves `EXCLUDED` spec markers (spec-040 D6) for custom flavor handling.
   - [`_model_write_step`][mutations-resolvers]: Executes [`_full_clean_or_field_errors`][mutations-resolvers] to map `ValidationError` to field errors via `validation_error_to_field_errors`. In the write phase, invokes [`save_or_field_errors`][mutations-resolvers] for create or [`forced_save_or_field_errors`][mutations-resolvers] (`force_update=True`) for update, followed by M2M assignment.
   - [`forced_save_or_field_errors`][mutations-resolvers]: Runs `target.save(force_update=True)` in a dedicated savepoint, mapping constraint collisions to `integrity_error_field_errors()` and missing-row concurrency races (`Model.NotUpdated` / zero-row updates) to `forced_update_conflict_errors`.

6. **Snapshot-Before-Delete Deletion Rider ([spec-036][spec-036] Decision 8 step 5, Decision 9):**
   - [`_run_delete`][mutations-resolvers]: Configures [`run_write_pipeline_sync`][mutations-resolvers] with a no-op decode step, [`_delete_write_step`][mutations-resolvers], and a snapshot-returning tail step.
   - [`_delete_write_step`][mutations-resolvers]: Captures a fully materialized instance snapshot via [`refetch_optimized`][mutations-resolvers] (`force_load=True`) before executing `instance.delete()`. Deleting against `instance` ensures the snapshot retains its PK and ID for client cache eviction.
   - [`_delete_or_field_errors`][mutations-resolvers]: Executes `instance.delete()`, mapping `ProtectedError` / `RestrictedError` to a protected-relation `FieldError` envelope, `IntegrityError` to constraint errors, and zero-row deletions to conflict errors.

7. **Optimized Re-fetching, Error Envelopes, and Async/Sync Twins ([spec-036][spec-036] Decisions 7, 8, 9, [spec-039][spec-039] M1a):**
   - [`refetch_optimized`][mutations-resolvers]: Re-fetches written rows by PK on the pinned write alias without re-evaluating visibility filters, using `apply_connection_optimization` configured with `mutation_payload_child_selections(slot)`.
   - [`error_payload_builder`][mutations-resolvers]: Constructs error response closures that invoke `transaction.set_rollback(True, using=using)` before returning `{ ok: false, errors }` or `{ node/result: None, errors }` payload objects.
   - [`build_payload`][mutations-resolvers] & [`payload_cls_for`][mutations-resolvers]: Materialize mutation return payloads dynamically via `inputs.<Name>Payload`.
   - [`authorize_or_raise`][mutations-resolvers]: Evaluates `mutation_cls().check_permission(...)`, enforcing `_require_sync_bool_auth_result` and raising top-level `GraphQLError` on denial.
   - [`run_pipeline_async`][mutations-resolvers] & [`make_resolver_entries`][mutations-resolvers]: Mint synchronous (`resolve_mutation_sync` / `resolve_sync`) and asynchronous (`resolve_mutation_async` / `resolve_async`) resolver entry pairs. The async twin wraps the entire synchronous pipeline in `run_in_one_sync_boundary` (`sync_to_async(thread_sensitive=True)`), preventing interleaved async execution during ORM transactions.
   - [`_MUTATION_ASYNC_RECOURSE`][mutations-resolvers]: Recourse message generated via `sync_pipeline_recourse("DjangoMutation")` attached to `SyncMisuseError` when an async `get_queryset` is met.

Connected behavior examined:
- [`django_strawberry_framework/mutations/sets.py`][mutations-sets]: `DjangoMutation` base class configuring `_mutation_meta`, `_primary_type`, `_input_field_specs`, and `_model_fields_by_attr`.
- [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs]: `FieldError`, `payload_object_slot`, `EXCLUDED`, and payload classes.
- [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions]: `_require_sync_bool_auth_result` write authorization validator.
- [`django_strawberry_framework/mutations/fields.py`][mutations-fields]: `DjangoMutationField` factory wiring `resolve_mutation_sync` and `resolve_mutation_async`.
- [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers]: Form mutation pipeline riding `run_write_pipeline_sync`, `save_or_field_errors`, `make_resolver_entries`, `payload_cls_for`.
- [`django_strawberry_framework/rest_framework/resolvers.py`][rest-framework-resolvers]: Serializer mutation pipeline riding `run_write_pipeline_sync`, `make_resolver_entries`, `payload_cls_for`, `save_or_field_errors`.
- [`django_strawberry_framework/auth/mutations.py`][auth-mutations]: Session auth mutation pipelines riding `run_write_pipeline_sync`, `_model_decode_step`, `_model_write_step`.
- [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction]: `open_write_pipeline`, `require_write_pipeline`, `pipeline_write_phase`, `authorization_phase`, `pipeline_alias_guard`, `check_instance_write_alias`, `reject_substituted_row`, `snapshot_target_state`, `base_locked_queryset`, `conflict_error`, `forced_update_conflict_errors`, `not_updated_exceptions`.
- [`django_strawberry_framework/utils/write_values.py`][utils-write-values]: `decode_provided_fields`, `decode_scalar_leaf`, `decode_visible_relation_ids`, `decoded_into`, `relation_into`.
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: `apply_type_visibility_sync`, `initial_queryset`, `model_for`, `run_in_one_sync_boundary`, `sync_pipeline_recourse`.
- [`django_strawberry_framework/utils/errors.py`][utils-errors]: `field_error`, `integrity_error_field_errors`, `validation_error_to_field_errors`.
- [`django_strawberry_framework/relay.py`][relay]: `GlobalIDDecode`, `decode_model_global_id`.
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]: `apply_connection_optimization`, `mutation_payload_child_selections`.
- [`django_strawberry_framework/resource_policy.py`][resource-policy]: `check_deadline`.
- [`tests/mutations/test_resolvers.py`][test-mutations-resolvers]: Comprehensive test suite covering sync/async execution, GlobalID validation, visibility filtering, transaction atomicity, partial updates, M2M assignments, and concurrency conflict handling.

## Verification

Static analysis and symbol inventory (`docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/resolvers.py --review docs/dry/dry-file-mutations__resolvers.md --include-constants`):
- Parsed 1 target file, 1332 lines, 1 constant ([`_MUTATION_ASYNC_RECOURSE`][mutations-resolvers]), 31 functions ([`run_write_pipeline_sync`][mutations-resolvers], [`error_payload_builder`][mutations-resolvers], [`_decode_relations`][mutations-resolvers], [`_explicit_null_error`][mutations-resolvers], [`_make_aware_if_naive`][mutations-resolvers], [`_decode_single_relation_id`][mutations-resolvers], [`_decode_relation_id_list`][mutations-resolvers], [`_relation_null_error`][mutations-resolvers], [`locate_instance`][mutations-resolvers], [`_provided_attr_names`][mutations-resolvers], [`_unprovided_exclude`][mutations-resolvers], [`_unique_constraint_groups`][mutations-resolvers], [`_assign_m2m`][mutations-resolvers], [`refetch_optimized`][mutations-resolvers], [`build_payload`][mutations-resolvers], [`_run_pipeline_sync`][mutations-resolvers], [`_model_decode_step`][mutations-resolvers], [`_model_write_step`][mutations-resolvers], [`forced_save_or_field_errors`][mutations-resolvers], [`_run_delete`][mutations-resolvers], [`_delete_write_step`][mutations-resolvers], [`_delete_or_field_errors`][mutations-resolvers], [`authorize_or_raise`][mutations-resolvers], [`_full_clean_or_field_errors`][mutations-resolvers], [`save_or_field_errors`][mutations-resolvers], [`coerce_lookup_id`][mutations-resolvers], [`not_found_error`][mutations-resolvers], [`_invalid_lookup_id_error`][mutations-resolvers], [`payload_cls_for`][mutations-resolvers], [`run_pipeline_async`][mutations-resolvers], [`make_resolver_entries`][mutations-resolvers]), plus module entrypoints `resolve_mutation_sync` and `resolve_mutation_async`.
- Verified reverse references across `django_strawberry_framework/forms/resolvers.py`, `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/mutations/fields.py`, `tests/mutations/test_resolvers.py`, and `examples/fakeshop/test_query/test_products_api.py`.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - **Write Subsystem Execution Pipelines:** The framework provides multiple write mutation flavors: model mutations ([`mutations/resolvers.py`][mutations-resolvers]), form mutations ([`forms/resolvers.py`][forms-resolvers]), DRF serializer mutations ([`rest_framework/resolvers.py`][rest-framework-resolvers]), and session auth mutations ([`auth/mutations.py`][auth-mutations]).
   - **Unified Shared Pipeline Skeleton:** All write flavors share the root write orchestration runner [`run_write_pipeline_sync`][mutations-resolvers]:
     - Centralized transaction management via `open_write_pipeline(mutation_cls)`;
     - Strict execution order: `(update/delete locate) -> authorize -> decode -> validate -> write -> re-fetch/snapshot -> payload`;
     - Pre-decode permission validation (`authorize_or_raise`) preventing relation-existence probing;
     - Immutable auth snapshot verification (`reject_substituted_row`) preventing mutable instance swapping;
     - Database connection pinning and phased alias isolation via `pipeline_alias_guard`, `authorization_phase`, and `pipeline_write_phase`;
     - Post-write optimized instance re-fetching (`refetch_optimized`) bypassing visibility filters under the G2 mutation optimizer plan;
     - Centralized error rollback closures via [`error_payload_builder`][mutations-resolvers];
     - Shared `IntegrityError` envelope translation via [`save_or_field_errors`][mutations-resolvers];
     - Dynamic payload class discovery via [`payload_cls_for`][mutations-resolvers];
     - Identical sync/async resolver pair generation via [`make_resolver_entries`][mutations-resolvers].
   - **Neutral Value Decoding Substrate:** Write values unpack through shared primitives in [`django_strawberry_framework/utils/write_values.py`][utils-write-values] (`decode_provided_fields`, `decode_scalar_leaf`, `decode_visible_relation_ids`).
   - **Model Flavor Specialization:**
     - `_model_decode_step` translates input attributes directly into model fields and M2M sets;
     - `_explicit_null_error` rejects explicit nulls on non-nullable scalar/FK columns before `full_clean()`;
     - `_make_aware_if_naive` normalizes naive datetimes under `USE_TZ=True`;
     - `_unprovided_exclude` preserves co-participating uniqueness constraint fields for partial updates;
     - `_model_write_step` validates with `full_clean(exclude=exclude)`, saves with `forced_save_or_field_errors` on update, and assigns M2Ms;
     - `_run_delete` captures pre-delete snapshots with loaded relations and deletes the located instance so snapshot PKs survive for client cache eviction.

2. **Sync and async twins:**
   - Zero duplication. Both synchronous (`resolve_mutation_sync`) and asynchronous (`resolve_mutation_async`) resolvers are instantiated as a unified pair via [`make_resolver_entries(_run_pipeline_sync)`][mutations-resolvers].
   - The entire write pipeline executes synchronously inside a single `sync_to_async(thread_sensitive=True)` call ([`run_pipeline_async`][mutations-resolvers] delegating to `run_in_one_sync_boundary`), preventing interleaved async execution and connection contention during ORM transactions.
   - `SyncMisuseError` discipline is enforced uniformly: an `async def get_queryset` encountered during sync pipeline execution raises `SyncMisuseError` with [`_MUTATION_ASYNC_RECOURSE`][mutations-resolvers] single-sourced via `sync_pipeline_recourse("DjangoMutation")`.
   - `authorize_or_raise` verifies permissions via `_require_sync_bool_auth_result`, preventing async permission coroutines from evaluating as truthy bypasses.

3. **Derived rather than repeated knowledge:**
   - **Payload Slots:** Derived via `payload_object_slot(primary_type)` (`"node"` for Relay Node targets, `"result"` otherwise).
   - **Payload Classes:** Resolved dynamically via [`payload_cls_for`][mutations-resolvers] from `mutation_cls._payload_type_name`.
   - **Target Models:** Extracted via `model_for(primary_type)`.
   - **Model Fields Index:** Sourced directly from `mutation_cls._model_fields_by_attr` stashed during mutation binding.
   - **Constraint Groups:** Derived dynamically in [`_unique_constraint_groups`][mutations-resolvers] by inspecting `model._meta.constraints`, `model._meta.unique_together`, and `field.unique`.
   - **Attribute Name Reversal:** [`_provided_attr_names`][mutations-resolvers] looks up field names from `model_fields[attr].name`, avoiding blind string manipulation that would corrupt columns like `object_id`.
   - **Auth Aliases:** Extracted from `auth_aliases_for_permission_classes(meta.permission_classes)`.
   - **Error Envelopes:** Standard field errors derive directly from `validation_error_to_field_errors`, `integrity_error_field_errors`, and `field_error`.

4. **Inverse and round-trip pairs:**
   - **Relay GlobalID Encoding <-> GlobalID Server-Side Decoding:**
     - Query outputs encode Relay GlobalIDs via `to_global_id(target_model, pk)`.
     - Update and delete input lookups decode and validate GlobalIDs server-side via [`coerce_lookup_id`][mutations-resolvers] and `decode_model_global_id`.
     - Relation arguments decode and validate via [`_decode_single_relation_id`][mutations-resolvers] and [`_decode_relation_id_list`][mutations-resolvers].
   - **Schema Input Construction <-> Resolver Input Decoding:**
     - Input types are synthesized in `mutations/inputs.py` with `InputFieldSpec` definitions.
     - [`_decode_relations`][mutations-resolvers] decomposes GraphQL input dataclasses according to those exact specs.
   - **Instance State Deconstruction & Exclude Calculation <-> Model Re-validation:**
     - [`_provided_attr_names`][mutations-resolvers] and [`_unprovided_exclude`][mutations-resolvers] identify untouched fields to exclude from `full_clean(exclude=...)` while keeping co-constrained fields for joint uniqueness validation.
   - **Pre-Delete Snapshot <-> Cache Eviction:**
     - Pre-delete snapshots load model relations and retain `snapshot.pk` / `snapshot.id` for GraphQL client cache eviction after `instance.delete()` zeroes `instance.pk`.

5. **Contracts restated in another medium:**
   - The mutation resolver contract is codified across:
     - Code: [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/mutations/sets.py`][mutations-sets], [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs], [`django_strawberry_framework/mutations/fields.py`][mutations-fields], [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers], [`django_strawberry_framework/rest_framework/resolvers.py`][rest-framework-resolvers], [`django_strawberry_framework/auth/mutations.py`][auth-mutations], [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction], [`django_strawberry_framework/utils/write_values.py`][utils-write-values], [`django_strawberry_framework/utils/querysets.py`][utils-querysets], [`django_strawberry_framework/utils/errors.py`][utils-errors];
     - Specifications: [`docs/SPECS/spec-036-mutations-0_0_11.md`][spec-036] (Decisions 7, 8, 9, 10, 15), [`docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md`][spec-037], [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038] (Decision 8), [`docs/SPECS/spec-039-serializer_mutations-0_0_13.md`][spec-039] (Decision 8, M1a, Md2), [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040] (D6, Revision-7), [`docs/SPECS/spec-046-transport_security-0_0_14.md`][spec-046], [`docs/SPECS/spec-047-resource_policy-0_0_14.md`][spec-047];
     - Test suites: [`tests/mutations/test_resolvers.py`][test-mutations-resolvers], [`tests/mutations/test_sets.py`][test-mutations-sets], [`tests/mutations/test_write_transaction.py`][test-mutations-write-transaction], [`tests/forms/test_resolvers.py`][test-forms-resolvers], [`tests/rest_framework/test_resolvers.py`][test-rest-framework-resolvers], [`tests/auth/test_mutations.py`][test-auth-mutations], [`examples/fakeshop/test_query/test_products_api.py`][test-products-api];
     - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Modifying the write-pipeline security lifecycle order or transaction boundary):** Alter how `check_deadline` or `open_write_pipeline` opens the transaction boundary across all mutation flavors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`][mutations-resolvers].
  - *Site count:* 1.
- **Posited change 2 (Modifying rollback error payload envelope generation):** Alter how `set_rollback(True)` is invoked or how `FieldError` payloads are structured upon write/validation failure.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/mutations/resolvers.py::error_payload_builder`][mutations-resolvers].
  - *Site count:* 1.
- **Posited change 3 (Modifying the sync/async resolver entry pair factory):** Change argument normalization for `resolve_sync` / `resolve_async` across all write flavors.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/resolvers.py::make_resolver_entries`][mutations-resolvers].
  - *Site count:* 1.
- **Posited change 4 (Modifying relation GlobalID decode and type-check error policy for model mutations):** Change the error message or code when an explicit `null` is provided to a multi-relation field.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/mutations/resolvers.py::_relation_null_error`][mutations-resolvers].
  - *Site count:* 1.
- **Posited change 5 (Modifying model partial update constraint exclude computation):** Alter how `UniqueConstraint` or `unique_together` groups are discovered or excluded during partial `full_clean`.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/mutations/resolvers.py::_unprovided_exclude`][mutations-resolvers] (or [`_unique_constraint_groups`][mutations-resolvers]).
  - *Site count:* 1.
- **Posited change 6 (Modifying disappearing-row concurrency handling during forced updates):** Change how `forced_save_or_field_errors` wraps `target.save(force_update=True)` in a savepoint before delegating to `forced_update_conflict_errors`.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/mutations/resolvers.py::forced_save_or_field_errors`][mutations-resolvers].
  - *Site count:* 1.
- **Posited change 7 (Modifying protected reference error handling on delete):** Update the diagnostic message returned when `ProtectedError` / `RestrictedError` is caught during delete.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/mutations/resolvers.py::_delete_or_field_errors`][mutations-resolvers].
  - *Site count:* 1.
- **Posited change 8 (Modifying top-level GlobalID decode error mapping for update/delete lookups):** Change how `DECODE_FAILED` / `WRONG_MODEL` maps to `_invalid_lookup_id_error` vs `UNCOERCIBLE_PK` to `not_found_error`.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/mutations/resolvers.py::coerce_lookup_id`][mutations-resolvers].
  - *Site count:* 1.

### Rejected candidates

1. **Moving `run_write_pipeline_sync` into `utils/write_transaction.py`:**
   - Disproved. [`run_write_pipeline_sync`][mutations-resolvers] is the domain-level GraphQL write orchestrator that constructs `Payload` classes, coordinates flavor decode/write hooks, and interfaces with Strawberry Info and GraphQL Errors. [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction] owns pure database transaction and connection-pinning primitives (`open_write_pipeline`, `pipeline_alias_guard`, `pipeline_write_phase`, `reject_substituted_row`). Keeping them separated avoids coupling the low-level transaction manager to GraphQL schema payloads.
2. **Inlining delete logic into `run_write_pipeline_sync`:**
   - Disproved. Delete has fundamentally different data and write lifecycles (no input data, no field decode, pre-delete snapshot evaluation before row destruction, protected-reference exception handling). Modeling delete as a specialized rider via [`_run_delete`][mutations-resolvers] using `tail_step` and [`_delete_write_step`][mutations-resolvers] reuses the exact same transaction, authorization, and alias guard skeleton without cluttering create/update paths with conditional branching.
3. **Unifying `_model_decode_step` with form data reconstruction:**
   - Disproved per [spec-038][spec-038] Decision 8. Model mutations unpack input specs directly into `setattr` / `model(**attrs)` kwargs and rely on partial `full_clean(exclude=...)`, whereas form mutations require reconstructing full bound form mappings (`data=`, `files=`) because Django forms validate full payloads.
4. **Performing GlobalID decoding in Strawberry field arguments rather than server-side `coerce_lookup_id`:**
   - Disproved per [spec-036][spec-036] Decision 10. Server-side decode allows distinguished `FieldError` items (`"id": "Invalid id."` vs `"id": "No matching row found."`) without leaking whether a row of another model exists, and avoids raw GraphQL execution aborts.

## Opportunities

None — `django_strawberry_framework/mutations/resolvers.py` is the central, single-sited write-pipeline engine for the entire framework. All cross-flavor pipeline orchestration ([`run_write_pipeline_sync`][mutations-resolvers]), transaction boundary management, rollback error envelope closures ([`error_payload_builder`][mutations-resolvers]), sync/async resolver pair generation ([`make_resolver_entries`][mutations-resolvers]), server-side GlobalID coercion ([`coerce_lookup_id`][mutations-resolvers]), and optimizer re-fetching ([`refetch_optimized`][mutations-resolvers]) are cleanly consolidated at their root owners with zero duplicate policy.

## Judgment

Zero-edit review. `django_strawberry_framework/mutations/resolvers.py` contains zero duplicate logic or unowned policy. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/resolvers.py --review docs/dry/dry-file-mutations__resolvers.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

I have independently verified Worker 1's DRY review of `django_strawberry_framework/mutations/resolvers.py`.

### Independent Observations and Code Analysis

1. **Write-Pipeline Orchestration and Security Invariants (`run_write_pipeline_sync`):**
   - Verified that [`run_write_pipeline_sync`][mutations-resolvers] provides the single orchestration skeleton for all mutation flavors (model create/update/delete, form mutations, serializer mutations, and session auth mutations).
   - Validated that cooperative deadline preflight (`check_deadline(info)`) executes prior to transaction initialization, aborting timed-out requests without transaction overhead.
   - Validated that execution is pinned to the single write alias designated by the database router (`open_write_pipeline(mutation_cls)`).
   - Confirmed the critical security order: `locate -> authorize -> decode -> validate -> write -> re-fetch/snapshot -> payload`. Authorizing before decoding (`authorize_or_raise`) prevents unauthorized callers from probing related-model visibility querysets via relation IDs.
   - Confirmed that row identity is protected against mutable instance swapping via `authorized_pk` snapshotting and `reject_substituted_row`.
   - Verified that `pipeline_alias_guard`, `authorization_phase`, and `pipeline_write_phase` strictly isolate connection access: auth backend reads are confined to the authorization phase, and mutating SQL statements are restricted to the write phase.

2. **Server-Side Relay GlobalID Coercion and Row Locking (`coerce_lookup_id`, `locate_instance`):**
   - Verified that [`coerce_lookup_id`][mutations-resolvers] decodes Relay GlobalIDs server-side via `decode_model_global_id`.
   - Confirmed that wrong-model or malformed IDs map to `_invalid_lookup_id_error` (`"Invalid id."`, code `"invalid"`) before any database read occurs, while uncoercible PK literals map to `not_found_error` (`"No matching row found."`, code `"not_found"`), avoiding schema and column type leaks.
   - Confirmed that [`locate_instance`][mutations-resolvers] evaluates the target type's primary visibility queryset (`apply_type_visibility_sync`), pinned to the write alias via `pin_write_queryset`. Missing or invisible rows return `None` (mapped to `not_found_error` with zero existence leakage).
   - Confirmed that under `select_for_update=True` (default), `base_locked_queryset` applies `SELECT ... FOR UPDATE` via a PK subquery against the base manager, preventing joins/unions from invalidating the lock clause.

3. **Relation Decoding, Value Sanitation, and Exclude Computation (`_decode_relations`, `_unprovided_exclude`):**
   - Verified that [`_decode_relations`][mutations-resolvers] drives `decode_provided_fields` with specialized handlers for scalars, FK relations, M2M sets, files, and excluded values.
   - Confirmed that explicit `null` on `null=False` scalar or FK columns is rejected pre-validation by `_explicit_null_error` (codes `"null"`), avoiding un-attributed constraint errors.
   - Confirmed that explicit `null` on M2M relations is rejected by `_relation_null_error` with instructions to provide `[]` to clear the relation.
   - Confirmed that naive datetimes are converted to timezone-aware timestamps under `USE_TZ=True` via `_make_aware_if_naive`.
   - Confirmed that [`_unprovided_exclude`][mutations-resolvers] and [`_unique_constraint_groups`][mutations-resolvers] compute the partial update exclude set (`full_clean(exclude=...)`), retaining validation on any unprovided field that co-participates in a `UniqueConstraint`, `unique_together`, or `field.unique` check with a provided field.

4. **Model Write and Snapshot-Before-Delete Cycles (`_model_write_step`, `_run_delete`):**
   - Verified that [`_model_write_step`][mutations-resolvers] executes `full_clean(exclude=exclude)`, maps validation errors via `validation_error_to_field_errors`, runs `forced_save_or_field_errors` (`force_update=True` in a savepoint) for updates, and sets M2M relations via `_assign_m2m`.
   - Confirmed that [`forced_save_or_field_errors`][mutations-resolvers] isolates zero-row updates and constraint collisions to conflict/integrity error envelopes.
   - Confirmed that [`_run_delete`][mutations-resolvers] and [`_delete_write_step`][mutations-resolvers] capture pre-delete snapshots via `refetch_optimized(..., force_load=True)` with relations loaded before invoking `instance.delete()`, ensuring snapshot PKs survive for GraphQL client cache eviction.
   - Confirmed that `_delete_or_field_errors` maps `ProtectedError` / `RestrictedError` to a protected `FieldError` envelope and zero target row deletion to conflict errors.

5. **Post-Write Re-fetching and Error Envelopes (`refetch_optimized`, `error_payload_builder`):**
   - Verified that [`refetch_optimized`][mutations-resolvers] re-fetches written rows by PK without visibility filtering, leveraging `apply_connection_optimization` with slot-aware child selections (`mutation_payload_child_selections(slot)`).
   - Confirmed that [`error_payload_builder`][mutations-resolvers] systematically invokes `transaction.set_rollback(True, using=using)` across all error branches before constructing `{ ok: false, errors }` or `{ node/result: None, errors }` payload objects.

6. **Async/Sync Twins and Misuse Discipline (`run_pipeline_async`, `make_resolver_entries`):**
   - Verified that [`make_resolver_entries`][mutations-resolvers] creates `(resolve_sync, resolve_async)` pairs from a single sync pipeline body.
   - Confirmed that [`run_pipeline_async`][mutations-resolvers] encapsulates the entire sync pipeline inside one `run_in_one_sync_boundary` (`sync_to_async(thread_sensitive=True)`), preventing interleaved async execution during ORM transactions.
   - Confirmed that `_MUTATION_ASYNC_RECOURSE` single-sources the async `get_queryset` guidance via `sync_pipeline_recourse("DjangoMutation")`.

### Duplication Matrix and Single-Edit-Site Verification

- **Axis 1 (Cross-Flavor Policy):** Discharged. All mutation flavors share `run_write_pipeline_sync`, `open_write_pipeline`, `error_payload_builder`, `make_resolver_entries`, `payload_cls_for`, and `save_or_field_errors`.
- **Axis 2 (Sync/Async Twins):** Discharged. Synchronous and asynchronous resolver pairs are minted from the exact same sync body via `make_resolver_entries`, with async execution wrapped in `run_pipeline_async`.
- **Axis 3 (Derived Knowledge):** Discharged. Payload classes, slots, target models, model field indices, and uniqueness groups are derived dynamically without hardcoded constants.
- **Axis 4 (Inverse/Round-Trip Pairs):** Discharged. GlobalID encoding/decoding, input specification unpacking/dataclass decomposition, and pre-delete snapshotting/cache eviction are symmetric.
- **Axis 5 (Cross-Medium Documentation):** Discharged. Invariants match specifications in `spec-036`, `spec-037`, `spec-038`, `spec-039`, `spec-040`, `spec-046`, and `spec-047`.
- **Single-Edit-Site Counts:** Confirmed all 8 posited change scenarios require exactly 1 site to modify.

### Symbol Coverage Check

Ran verification script:
`uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/resolvers.py --review docs/dry/dry-file-mutations__resolvers.md --include-constants`
Result: `OK: 32 target definition(s) and 0 required topic(s) are covered.`

Zero-edit review verified. Marking `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-036]: ../SPECS/spec-036-mutations-0_0_11.md
[spec-037]: ../SPECS/spec-037-upload_file_image_mapping-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md
[spec-046]: ../SPECS/spec-046-transport_security-0_0_14.md
[spec-047]: ../SPECS/spec-047-resource_policy-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[relay]: ../../django_strawberry_framework/relay.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[rest-framework-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[utils-errors]: ../../django_strawberry_framework/utils/errors.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-write-transaction]: ../../django_strawberry_framework/utils/write_transaction.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-auth-mutations]: ../../tests/auth/test_mutations.py
[test-forms-resolvers]: ../../tests/forms/test_resolvers.py
[test-mutations-resolvers]: ../../tests/mutations/test_resolvers.py
[test-mutations-sets]: ../../tests/mutations/test_sets.py
[test-mutations-write-transaction]: ../../tests/mutations/test_write_transaction.py
[test-rest-framework-resolvers]: ../../tests/rest_framework/test_resolvers.py

<!-- examples/ -->
[test-products-api]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
