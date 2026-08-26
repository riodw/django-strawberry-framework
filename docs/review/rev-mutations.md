# Review: `django_strawberry_framework/mutations/`

Status: verified

## Understanding

`django_strawberry_framework/mutations/` implements the core write subsystem for the framework (spec-036, spec-037, spec-038, spec-039, spec-040, spec-051). It provides declarative base classes, input generation, validation, authorization, execution pipelines, and typed GraphQL field/payload wrappers across all write flavors:
- Declarative model mutations (`DjangoMutation` for create, update, delete)
- Form mutations (`DjangoModelFormMutation`, `DjangoFormMutation`)
- Serializer mutations (`DjangoSerializerMutation` / `SerializerMutation`)
- Authentication mutations (`Register`, `Login`, `Logout`, `ChangePassword`, `ResetPasswordRequest`, `ResetPasswordConfirm`)

### Subpackage Architecture & Module Topology

The subpackage is organized into 6 cohesive modules:

1. **`operations.py` (Canonical Operation Descriptors)**: Single source of truth for mutation operation descriptors (`MutationOperationDescriptor`), canonical singletons (`OPERATION_CREATE`, `OPERATION_UPDATE`, `OPERATION_DELETE`, `OPERATION_FORM`), argument presence predicates (`operation_takes_id`, `operation_takes_data`), permission action verbs (`add`, `change`, `delete`), and shared error diagnostics (`non_delete_operation_error`).
2. **`inputs.py` (Input Generation & Payloads)**: Generates input dataclasses (`<Model>Input`, `<Model>PartialInput`) with relation typing (`relay.GlobalID` for Node-shaped types, pk scalars otherwise), field selection (`editable_input_fields`), create-requiredness rules, collision detection (`iter_input_field_collisions`), the public `FieldError` type, and payload type builders (`build_payload_type`) supporting both model-backed (`node`/`result` slot + `errors`) and model-less (`ok: bool` + `errors`) mutations.
3. **`sets.py` (Declarative Surface, Metaclass & Phase-2.5 Bind)**: Defines `DjangoMutation`, its metaclass validation (`_validate_meta`), identity-deduplicated declaration registry (`_mutation_declaration_registry`), shape build caching (`_shape_build_cache`), and phase-2.5 schema binding (`bind_mutations`, `bind_write_declarations`, `bind_mutation_outputs`). Exports shared write foundations reused by forms, serializers, and auth mutations.
4. **`permissions.py` (Write-Side Authorization Primitives)**: Implements the write-auth execution engine (`run_permission_classes`), sync boolean authorization validation (`_require_sync_bool_auth_result`), DRF-inspired `DjangoModelPermission` evaluating `user.has_perm`, and the fail-closed `DenyAll` sentinel for model-less mutations.
5. **`resolvers.py` (Shared Runtime Write Execution Pipeline)**: Orchestrates the synchronous and asynchronous execution pipelines (`run_write_pipeline_sync`, `run_pipeline_async`). Governs transaction boundaries (`open_write_pipeline`), visibility-scoped instance locating (`locate_instance`), server-side GlobalID decoding (`coerce_lookup_id`), anti-drift pk validation (`reject_substituted_row`), constraint-aware partial update exclude computation (`_unprovided_exclude`), concurrency locking (`base_locked_queryset`), snapshot-before-delete, and atomic rollback error handling (`error_payload_builder`).
6. **`fields.py` (Root Field Factory & Async Context Dispatch)**: Exposes `DjangoMutationField` for root mutation types (`@strawberry.type class Mutation`), building argument signatures with lazy forward references (`_lazy_ref`) to `<Name>Payload`, duck-typing mutation targets (`_validate_mutation_target`), stamping transaction markers (`MUTATION_CLASS_MARKER`), and routing sync/async calls via `strawberry.utils.inspect.in_async_context()`.

### Execution Pipeline Invariants

The write subsystem enforces critical lifecycle and security invariants across all mutation flavors:
1. **Single Atomic Transaction & Thread Safety**: Wraps pipeline execution in a single `transaction.atomic(using=using)` on the pinned write alias. Async execution runs the synchronous pipeline within a single `sync_to_async(thread_sensitive=True)` call.
2. **Authorize-Before-Decode Invariant**: Authorization checks (`check_permission`) run strictly after instance location/locking and *before* input decoding or relation resolution. Unauthorized callers cannot probe entity visibility or leak existence.
3. **Visibility-Scoped Locate & Relation Resolution**: Instance lookups on `update` and `delete` query primary `DjangoType.get_queryset`, returning identical not-found errors for hidden and non-existent rows. Single and multi-relations are type-checked and filtered through `decode_visible_relation_ids`.
4. **Server-Side GlobalID Decode**: IDs are validated against target models server-side, mapping malformed/wrong-model IDs to `invalid` errors and uncoercible literals to `not_found` errors without leaking raw Django exceptions.
5. **Anti-Drift & Anti-Substitution Protection**: Captures immutable `authorized_pk` and `target_state` snapshots before consumer permission hooks execute, raising errors if primary keys are swapped during authorization or write steps.
6. **Snapshot-Before-Delete**: Materializes optimized snapshots before executing `instance.delete()`, preserving node IDs on detached instances for client cache eviction.
7. **Atomic Rollback on Error**: `error_payload_builder` marks `transaction.set_rollback(True, using=using)` on validation, decode, or conflict failures before building error envelopes.

---

## Verification

1. **Subsystem Test Matrix**:
   - `tests/mutations/test_fields.py` (14 tests): Argument signature synthesis, lazy payload references, sync/async dispatch, construction-time target validation, metadata passthrough.
   - `tests/mutations/test_inputs.py` (66 tests): Input shape generation, requiredness rules, GlobalID vs pk typing, collision guards, model-backed and model-less payloads.
   - `tests/mutations/test_operations.py` (7 tests): Immutability of operation descriptors, presence predicates, derived mappings.
   - `tests/mutations/test_permissions.py` (20 tests): Django model permissions, `DenyAll`, anonymous user handling, sync bool enforcement, coroutine rejection.
   - `tests/mutations/test_resolvers.py` (74 tests): CRUD happy paths, timezone awareness, partial update constraint carve-outs, anti-drift protection, concurrency locking, conflict envelopes, snapshot retention.
   - `tests/mutations/test_sets.py` (103 tests): `Meta` validation matrix, shape caching, relation override type locks, registration idempotency.
   - `tests/mutations/test_write_transaction.py` (63 tests): Read-only write barriers, alias guards, atomic rollback, and completion-spanning transaction handling.
   - **Total mutation tests passing**: 347 passed.

2. **Cross-Subsystem Verification**:
   - Ran 778 tests across `tests/forms/`, `tests/auth/test_mutations.py`, and `tests/rest_framework/` confirming seamless interoperability of shared mutation bases, operation descriptors, input builders, and execution pipelines.

3. **Scratch Integration Verification**:
   - Created and executed end-to-end integration probes under `docs/review/temp-tests/mutations/` exercising full declarative CRUD lifecycle, GlobalID decoding, authorize-before-decode security ordering, and async execution under `DjangoSchema`.

---

## Improvements

### High

None.

### Medium

None.

### Low

#### 1. Document `operations.py` in package docstring (`mutations/__init__.py`)

- **Observation:** `django_strawberry_framework/mutations/__init__.py` described the package as a five-module subpackage (`inputs`, `sets`, `permissions`, `resolvers`, `fields`), omitting `operations.py` which was introduced as the single source of truth for mutation operation descriptors.
- **Evidence:** `mutations/operations.py` defines `MutationOperationDescriptor` and operation predicates used across all write flavors.
- **Impact:** Documentation accuracy and maintainability for developers navigating the subpackage structure.
- **Recommendation:** Update `mutations/__init__.py` module docstring to describe the six-module architecture including `operations.py`.
- **Proof:** `django_strawberry_framework/mutations/__init__.py` docstring updated and verified.

---

## Summary

The `django_strawberry_framework/mutations/` subpackage represents a comprehensive, cohesive, and battle-hardened write subsystem. Its single-sited pipelines, strict authorize-before-decode invariant, server-side GlobalID validation, concurrency hardening, and phase-2.5 bind coordination provide robust, unified write mechanics across all mutation flavors. The package docstring was updated to accurately reflect all six component modules.

---

## Implementation (Worker 1)

- **Changed files**:
  - `django_strawberry_framework/mutations/__init__.py`: Updated module docstring to document the six-module subpackage architecture including `operations.py`.
- **Permanent tests**:
  - Existing test suite (347 mutation tests and 778 cross-flavor tests) comprehensively pins all write subsystem invariants. Prior per-file passes added permanent tests pinning metadata passthrough (`test_fields.py`), model-less payload structures (`test_inputs.py`), and parameterized flavor diagnostic prefixes (`test_sets.py`).
- **Scratch or focused verification**:
  - Executed `uv run pytest tests/mutations/ --no-cov` (347 passed).
  - Executed `uv run pytest tests/forms/ tests/auth/test_mutations.py tests/rest_framework/ --no-cov` (778 passed).
  - Executed scratch integration tests verifying end-to-end CRUD, authorize-before-decode, GlobalID decode, and async execution.
- **Formatter and linter results**:
  - `uv run ruff format .` ran cleanly.
  - `uv run ruff check --fix .` passed with 0 errors.
- **Evidence for rejected findings**:
  - No findings were rejected; the write subsystem operates in complete alignment with specifications.
- **Changelog entry**:
  - None — docstring clarity update and verification only; no public behavioral or API breaking changes.

---

## Independent verification (Worker 2)

### Verification Paths & Invariants Checked

1. **Subpackage Module Topology & Exports**:
   - Verified clean separation of concerns and single-sited responsibilities across all 6 modules: [operations.py](file:///Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/mutations/operations.py), [inputs.py](file:///Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/mutations/inputs.py), [sets.py](file:///Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/mutations/sets.py), [permissions.py](file:///Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/mutations/permissions.py), [resolvers.py](file:///Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/mutations/resolvers.py), and [fields.py](file:///Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/mutations/fields.py).
   - Re-verified public exports (`DjangoModelPermission`, `DjangoMutation`, `DjangoMutationField`, `FieldError`) and package docstring update in [__init__.py](file:///Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/mutations/__init__.py).

2. **Execution Pipeline Lifecycle & Security Invariants**:
   - **Authorize-before-decode invariant**: Probed that write authorization (`check_permission` / `Meta.permission_classes`) runs strictly prior to input decoding or relation resolution, raising `GraphQLError` immediately upon denial and preventing entity visibility probing or decode error leakage.
   - **Locate & Locking**: Verified `select_for_update` default on update/delete operations (`base_locked_queryset`), lock bypass opt-outs (`select_for_update = False`), and visibility-scoped lookup consistency via `DjangoType.get_queryset`.
   - **Anti-drift & Anti-substitution protection**: Confirmed primary key snapshotting (`authorized_pk`) before permission checks and write execution, rejecting row substitutions.
   - **Snapshot-before-delete**: Materializes optimized snapshots prior to deletion, preserving node IDs and scalar attributes on detached instances for client cache updates.
   - **Transaction boundaries & atomic rollback**: Enforces atomic transaction boundaries on the managed write alias (`open_write_pipeline`), setting `transaction.set_rollback(True)` on validation, decode, or constraint failures.
   - **Async execution dispatch**: Verified transparent bridging to synchronous execution via `in_async_context()` and `sync_to_async(thread_sensitive=True)` under `DjangoSchema`.

3. **Scratch Probes & Test Suites**:
   - Executed focused test suites:
     - `tests/mutations/` (347 passed)
     - `tests/forms/`, `tests/auth/test_mutations.py`, `tests/rest_framework/` (778 passed)
   - Created and ran disposable scratch test suite `docs/review/temp-tests/mutations/test_w2_mutations_verification.py` (5 passed) independently verifying:
     - Operation descriptors and argument presence predicates.
     - Model-backed (`result`/`node`) and model-less (`ok: bool`) payload type synthesis.
     - Authorize-before-decode lifecycle enforcement under GraphQL query execution.
     - Anti-drift snapshot-before-delete lifecycle and DB row removal.
     - Async mutation pipeline execution under async runner.

### Disposition

- Low finding 1 ([`mutations/__init__.py`](file:///Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/mutations/__init__.py)) docstring update verified.
- Subsystem architecture, cross-flavor write contracts, security ordering, and transaction safety are fully verified.
- Status: **verified**.
