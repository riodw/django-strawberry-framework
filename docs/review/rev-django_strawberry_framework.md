# Review: `django_strawberry_framework/`

Status: verified

## Understanding

`django_strawberry_framework/` is a DRF-inspired Django integration for Strawberry GraphQL. The project-level pass examines the end-to-end cohesion across all 14 subpackages and 24 root modules:

- **Root Modules & Public Surface:**
  - `__init__.py`: Serves as the package entrypoint, declares canonical logger (`"django_strawberry_framework"`), pins `__all__` containing all hard-dependency exports, and implements PEP 562 `__getattr__` for dynamic, non-memoizing access to soft-dependency DRF symbols (`SerializerMutation`, `register_serializer_field_converter`, `SerializerFieldConversion`, `describe_serializer_input`, `NestedSerializerConfig`, `SerializerHookContext`, `UploadMetadata`).
  - `apps.py`: Declares `DjangoStrawberryFrameworkConfig` AppConfig and coordinates application initialization.
  - `conf.py`: Implements typed configuration management for `DJANGO_STRAWBERRY_FRAMEWORK` settings.
  - `consumers.py` & `routers.py`: ASGI Channels integration supporting `graphql-ws` and `graphql-transport-ws` WebSocket subprotocols with connection lifecycle handling, per-operation re-auth / session tracking, and fail-closed soft-dependency guards.
  - `connection.py` & `keyset.py`: Relay connection specification, cursor encoding, window slicing, sidecar kwarg handling, and keyset-based pagination with ordering validation.
  - `error_policy.py` & `resource_policy.py`: Production error masking, status code mapping, GraphQL error extension formatting, query complexity, max depth, timeout enforcement, and node limit bounding.
  - `exceptions.py`: Cohesive framework exception hierarchy (`FrameworkError`, `ConfigurationError`, `ExecutionError`, `FieldLookupError`, `SyncMisuseError`, `ResourceLimitExceeded`).
  - `list_field.py`: `DjangoListField` supporting non-Relay list queries with optimizer integration, filtering, ordering, and pagination.
  - `permissions.py`: Depth-1 recursive forward-relation cascade visibility (`apply_cascade_permissions` / `aapply_cascade_permissions`) with cycle detection, single-database pinning, and fail-closed validation.
  - `registry.py`: Central `TypeRegistry` and lifecycle clear hooks (`register_subsystem_clear`) ensuring test isolation and clean state resets.
  - `relay.py`: `DjangoNodeField`, `DjangoNodesField`, global ID resolution, and Relay Node interface binding.
  - `scalars.py`: Custom scalar serializers and re-exports (`BigInt`, `Upload`, `strawberry_config`).
  - `schema.py`: `DjangoSchema` wrapping Strawberry's `Schema` to inject default schema extensions (`DjangoResourcePolicyExtension`, `DjangoErrorPolicyExtension`, `DjangoOptimizerExtension`) and `DjangoMutationExecutionContext` managing transaction lifetimes.
  - `sets_mixins.py`: Declarative base mixins for `FilterSet`, `OrderSet`, and mutation sets.
  - `views.py`: `GraphQLView` (sync) and `AsyncGraphQLView` (async) HTTP views supporting batching, multipart upload parsing, and debug toolbar integration.
  - Compatibility & patch modules (`_boundary_ordering.py`, `_cross_web_patches.py`, `_django_patches.py`, `_request_body.py`, `_strawberry_patches.py`): Encapsulate engine-level shims, request body caching, and patch isolation.

- **Subpackages:**
  - `auth/`: Opt-in session-based authentication mutations (`login_mutation`, `logout_mutation`, `register_mutation`) and queries (`current_user`).
  - `extensions/`: Schema extensions (`DjangoDebugExtension`, `DjangoErrorPolicyExtension`, `DjangoResourcePolicyExtension`).
  - `filters/`: Declarative `FilterSet`, filter factories, dynamic input generation, and resolver binding.
  - `forms/`: Form mutation write subsystem (`DjangoFormMutation`, `DjangoModelFormMutation`, `convert_form_field`, form input generation).
  - `management/`: Management commands (`export_schema`, `inspect_django_type`).
  - `middleware/`: HTTP middlewares (`DebugToolbarMiddleware`, request body streaming).
  - `mutations/`: Standard model mutation write subsystem (`DjangoMutation`, `DjangoMutationField`, `DjangoModelPermission`, operation descriptors).
  - `optimizer/`: N+1 query planning (`DjangoOptimizerExtension`, AST walker, selections, optimizer hints, join taxonomy, lateral/nested fetch).
  - `orders/`: Declarative `OrderSet`, ordering factories, input generation, and resolver binding.
  - `rest_framework/`: DRF serializer mutation write subsystem (`SerializerMutation`, field converter registry, nested serializer inputs, frozen hook context).
  - `testing/`: Test clients (`TestClient`, `AsyncTestClient`, `GraphQLTestCase`, `GraphQLTransactionTestCase`, `Response`), connection wrapper, Relay test helpers.
  - `types/`: Type definition (`DjangoType`), converters, relation resolvers, Relay interface attachment, multi-phase finalizer (`finalize_django_types`).
  - `utils/`: Cross-cutting utility modules (context, converters, errors, imports, inputs, input values, permissions, policies, querysets, relations, sessions, strings, typing, write transactions, write values).

- **Lifecycle Phases:**
  1. *Definition Time:* Model types, filtersets, ordersets, and mutation sets are declared declaratively with metadata stored without premature DB evaluation. Subsystem clear hooks are registered with `registry.register_subsystem_clear`.
  2. *Schema Construction / Finalization:* `DjangoSchema` or `finalize_django_types()` runs through 5 idempotent phases (Phase 1: model & scalar fields, Phase 2: relations, Phase 2.5: sets/mutations/forms/serializers, Phase 3: optimizer hints, Phase 4: Relay node validation).
  3. *Execution Planning:* Request enters view/consumer; `DjangoOptimizerExtension` walks the GraphQL AST, compiles optimizer hints, resolves join taxonomies, plans lateral and windowed prefetches, and stashes plans in request context.
  4. *Execution & Resolution:* Resolvers execute queries, connections, list fields, or mutations with transaction management (`DjangoMutationExecutionContext`), cascade visibility (`apply_cascade_permissions` / `aapply_cascade_permissions`), and resource limits (`DjangoResourcePolicyExtension`).
  5. *Response Completion & Post-Processing:* Error formatting and policy masking (`DjangoErrorPolicyExtension`), debug metadata attachment (`DjangoDebugExtension`), and transaction commit/rollback.

## Verification

- **Package Initialization & Root Exports:**
  - Ran `uv run pytest --no-cov tests/base/test_init.py` (10 passed in 1.83s), verifying `__version__`, logger singleton identity, public API `__all__` pinning, file upload type exports, dynamic DRF soft export resolution via `__getattr__`, non-memoization, unknown attribute handling, star import hygiene, and identity of re-exported types from subpackages.
- **Cross-Subsystem Integration Suite:**
  - Ran focused integration tests covering schema construction, views, Relay connections, type definitions, and the query optimizer:
    `uv run pytest --no-cov tests/test_schema.py tests/test_views.py tests/test_relay_connection.py tests/types/test_base.py tests/optimizer/test_extension.py` (671 passed in 16.22s).
- **Soft Dependency & Namespace Isolation:**
  - Verified that soft dependencies (`djangorestframework`, `channels`, `django-debug-toolbar`) are guarded through `utils/imports.py::require_optional_module`, raise descriptive install hints when accessed, and do not pollute `__all__` or trigger eager imports during package load.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The `django_strawberry_framework` package demonstrates architectural cohesion across its 14 subpackages and 24 root modules. Lifecycle phases (definition time, multi-phase schema finalization, query optimization, execution with transaction atomicity, and post-processing) integrate seamlessly. Public APIs strictly uphold the DRF-first Meta pattern, async/sync parity is maintained across all resolver and testing interfaces, request isolation is preserved via `ContextVar` boundaries, and optional dependencies are safely isolated behind raising soft-dependency guards.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Permanent tests: Verified across comprehensive package test suites (`tests/base/test_init.py`, `tests/test_schema.py`, `tests/test_views.py`, `tests/test_relay_connection.py`, `tests/types/test_base.py`, `tests/optimizer/test_extension.py`).
- Scratch / focused verification: All 10 package-root tests and 671 core integration tests passed without regressions.
- Formatter / linter: Not run (zero-edit cycle).
- Rejected findings: None.
- Changelog entry: Not warranted (zero-edit cycle).

None — zero-edit cycle

## Independent verification (Worker 2)

### Verification Methodology & Lifecycle Tracing

Independently traced end-to-end framework execution lifecycles and verified architectural contracts across root modules and all 14 subpackages:

1. **Root Module Exports & Soft-Dependency Isolation:**
   - Verified that `django_strawberry_framework/__init__.py` pins `__all__` to only hard-dependency exports while delegating DRF-specific symbols (`SerializerMutation`, `register_serializer_field_converter`, `SerializerFieldConversion`, `describe_serializer_input`, `NestedSerializerConfig`, `SerializerHookContext`, `UploadMetadata`) dynamically via PEP 562 `__getattr__` without caching or module namespace mutation.
   - Verified that Channels (`consumers.py`, `routers.py`), DRF (`rest_framework/`), and django-debug-toolbar (`middleware/debug_toolbar.py`, `extensions/debug.py`) remain cleanly isolated behind `require_optional_module()`.

2. **Schema Construction & Multi-Phase Finalization:**
   - Traced definition-time registration through `registry.py` and `sets_mixins.py` (lazy type binding, subsystem clear hooks) to `DjangoSchema` construction and `finalize_django_types` 5-phase finalization.
   - Verified correct dependency ordering across scalar field registration, relation resolution, set/mutation factories, optimizer hints, and Relay Node interface binding.

3. **Query Execution, Optimization & Resource Limits:**
   - Traced execution path through `GraphQLView` (sync) and `AsyncGraphQLView` (async) into AST walk / query plan compilation (`DjangoOptimizerExtension`), request context isolation, and execution across Relay connection slicing (`connection.py`, `keyset.py`) and non-Relay list fields (`list_field.py`).
   - Verified resource policy enforcement (`DjangoResourcePolicyExtension` for complexity, max depth, timeout, node limits) and error policy masking (`DjangoErrorPolicyExtension`).

4. **Mutation Execution, Transaction Boundaries & Cascade Visibility:**
   - Traced mutation execution through `DjangoMutationExecutionContext` and atomic transaction lifecycles across model mutations (`mutations/`), form mutations (`forms/`), serializer mutations (`rest_framework/`), and session auth mutations (`auth/`).
   - Confirmed depth-1 recursive forward-relation cascade visibility (`apply_cascade_permissions` / `aapply_cascade_permissions`) cycle detection, single-database pinning, and fail-closed security guarantees.

5. **Async/Sync Parity & ContextVar Safety:**
   - Verified sync and async execution parity across resolvers, field factories, testing clients (`TestClient`, `AsyncTestClient`), and connection actors.
   - Verified that re-entrant and concurrent executions preserve ContextVar boundaries without cross-operation leakage.

### Test Execution & Results

- **Core Package & Root Integration:**
  `uv run pytest --no-cov tests/base/test_init.py tests/test_schema.py tests/test_views.py tests/test_relay_connection.py tests/types/test_base.py tests/optimizer/test_extension.py`
  -> **681 passed in 13.31s**
- **Broad Subsystem Integration:**
  `uv run pytest --no-cov tests/auth/ tests/filters/ tests/forms/ tests/mutations/ tests/orders/ tests/rest_framework/ tests/testing/`
  -> **1,958 passed in 16.85s**

### Zero-Edit Status

- Confirmed zero edits for the project-level pass.
- All collective contracts, subsystem integrations, and lifecycle phases verified healthy.

Status: verified
