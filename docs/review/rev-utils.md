# Review: `django_strawberry_framework/utils/`

Status: verified

## Understanding

### Collective Purpose & Architecture
The `django_strawberry_framework/utils/` subpackage forms the cross-cutting, cycle-safe utility substrate for the entire framework. Rather than a monolithic utility module, it is organized into 15 focused, highly cohesive submodules and a package root. Each submodule encapsulates a specific domain-neutral mechanic or contract required by higher-level subsystems (resolvers, optimizer, types, filters, orders, mutations, forms, serializers, transport, and testing) without introducing cyclic dependencies or leaking business logic across architectural boundaries:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer 4: Execution, Permissions & State Substrates                          │
│   • querysets.py: Sealed execution queryset boundary, sync/async            │
│     get_queryset visibility routing, manager coercion, value decoding       │
│   • permissions.py: Set-input permission traversal, Channels context adapter│
│   • write_transaction.py: Managed mutation transaction, alias pinning, row │
│     locks, disappearing-row conflict detection, write pipeline context      │
│   • write_values.py: Neutral write decoding, surrogate rejection, choice    │
│     unwrapping, raw relation pk coercion, structural relation ID check      │
│   • sessions.py: Session engine resolution, WebSocket actor lease & state    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 3: Traversal, Converter & Pagination Machinery                        │
│   • connections.py: Relay window bounds derivation, probe vs count fetch    │
│     modes, sidecar argument handling (filter, order_by/orderBy), row split  │
│   • input_values.py: Set-input graph traversal (active values, items)       │
│   • inputs.py: Generated input class factory, namespace lifecycles, caching │
│   • converters.py: Fail-loud MRO converter skeleton for forms / serializers │
│   • errors.py: Neutral FieldError construction, ValidationError mapping     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 2: Reflection, Type Inspection & Context Handling                     │
│   • relations.py: Django relation classification, model field & path decode │
│   • context.py: Shape-agnostic context read/write/clear (dict, obj, slots)  │
│   • typing.py: Strawberry / GraphQL type unwrapping, async callable check,   │
│     schema / config introspection                                           │
│   • strings.py: Case conversion (snake, pascal, camel), path flattening     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 1: Core Primitives & Dynamic Import Seams                             │
│   • imports.py: Best-effort, loaded-only, strict, and soft dependency imports│
│   • __init__.py: Curated package export boundary                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Subsystem Dynamics & Module Cohesion
1. **Queryset Security & Visibility (`querysets.py`)**:
   - Implements the hardened sealed-execution-queryset boundary (`_seal_or_defect`), reconstructing querysets from immutable query state to neutralize hostile method shadowing or instance overrides.
   - Centralizes `DjangoType.get_queryset` sync and async visibility routing (`apply_type_visibility_sync`, `apply_type_visibility_async`).
   - Standardizes `sync_to_async` execution via `run_in_one_sync_boundary`.
2. **Mutation & Write Plumbing (`write_transaction.py`, `write_values.py`, `errors.py`)**:
   - Enforces the managed transaction requirement (`require_managed_write`), pinning database operations to the router write alias (`resolve_write_alias`, `pin_write_queryset`) and acquiring base manager row locks (`base_locked_queryset`).
   - Handles disappearing-row conflicts safely (`forced_update_conflict_errors`).
   - Normalizes write decoding, rejects lone Unicode surrogates (`unencodable_text_error`), unwraps choice enums (`raw_choice_value`), and standardizes `FieldError` construction across model, form, and serializer write flavors.
3. **Set Input & Permission Substrate (`input_values.py`, `inputs.py`, `permissions.py`, `strings.py`)**:
   - Dispatches graph traversal across filter and order inputs without coupling to family-specific ASTs.
   - Generates Strawberry input classes with lifecycle caching and registry clears.
   - Traverses active input permission gates, adapting Django HTTP and Channels WebSocket requests symmetrically.
4. **Relay & Connection Subsystem (`connections.py`, `typing.py`, `context.py`)**:
   - Derives slice window bounds for offset and keyset pagination, coordinating probe-based `hasNextPage` checks and marker row insertion for ambiguous empty windows.
   - Unifies sidecar argument reading (`filter`, `order_by`, `orderBy`) between the optimizer walker and Relay connection resolvers.
5. **Transport, Auth Seam & Dynamic Imports (`sessions.py`, `imports.py`, `relations.py`)**:
   - Resolves `SESSION_ENGINE` storage lazily without eagerly loading the opt-in `auth` package.
   - Manages WebSocket connection actor leases (`ConnectionActorState`, `actor_lease`, `actor_transition`) to prevent race conditions during auth transitions.
   - Provides safe reflection over Django models and dynamic imports.

---

## Verification

### Mapping of Callers & Consumers
- **Resolvers & Fields (`connection.py`, `list_field.py`, `relay.py`, `keyset.py`)**: Rely on `connections.py`, `querysets.py`, `typing.py`, and `context.py` for pagination bounds, visibility routing, and type introspection.
- **Optimizer Subsystem (`optimizer/`)**: Employs `connections.py`, `relations.py`, `strings.py`, `typing.py`, and `context.py` for plan creation, join taxonomy, hint parsing, and row partitioning.
- **Filter & Order Subsystems (`filters/`, `orders/`)**: Depend on `inputs.py`, `input_values.py`, `permissions.py`, `querysets.py`, `converters.py`, and `strings.py` for input synthesis, normalization, and permission enforcement.
- **Mutation & Form Subsystems (`mutations/`, `forms/`, `rest_framework/`)**: Utilize `write_transaction.py`, `write_values.py`, `errors.py`, and `converters.py` for atomic execution, input decoding, and error formatting.
- **Transport & Auth (`consumers.py`, `auth/`)**: Consume `sessions.py`, `permissions.py`, and `imports.py` across the opt-in auth boundary.

### Subsystem Verification & Test Coverage
- Executed all 762 permanent tests across `tests/utils/`:
  - `tests/utils/test_connections.py` (50 passed): Window bounds, sidecar kwargs extraction, probe vs count mutual exclusivity, marker row handling, keyset bounds.
  - `tests/utils/test_context.py` (22 passed): Context read/write/clear across dicts, objects, slots, frozen instances.
  - `tests/utils/test_converters.py` (14 passed): Fail-loud MRO conversion, scalar registry resolution, sentinel continuation.
  - `tests/utils/test_errors.py` (37 passed): FieldError construction, non-field root error handling, error path joining, ValidationError formatting.
  - `tests/utils/test_imports.py` (19 passed): Best-effort, loaded-only, strict, and optional module imports.
  - `tests/utils/test_input_values.py` (23 passed): Active field traversal, dataclass/dict normalization, depth limits.
  - `tests/utils/test_inputs.py` (81 passed): Strawberry input class generation, namespace management, caching.
  - `tests/utils/test_permissions.py` (42 passed): Permission method derivation, Channels request adaptation, active input permission execution.
  - `tests/utils/test_querysets.py` (257 passed): Queryset normalization, sealed execution boundary, AST/where-tree inspection, visibility runners.
  - `tests/utils/test_relations.py` (39 passed): Relation kind classification, reverse relations, model path resolution.
  - `tests/utils/test_sessions.py` (22 passed): Session store class resolution, actor lease synchronization, actor transitions.
  - `tests/utils/test_strings.py` (33 passed): Bidirectional case conversion, lookup path flattening.
  - `tests/utils/test_typing.py` (44 passed): GraphQL type unwrapping, async-callable detection, schema config retrieval.
  - `tests/utils/test_write_values.py` (41 passed): Unicode surrogate rejection, choice unwrapping, relation decoding.
  - `tests/utils/test_policies.py` (38 passed): Policy derivation, bounds resolution.
  - Executed: `uv run pytest tests/utils/ --no-cov` (762 passed in 5.85s).
- Scratch verification:
  - Created `docs/review/temp-tests/utils/test_utils_subsystem.py` (6 tests) verifying public exports, cross-module string/input lookup flattening, context/connections cooperation, error envelope/write values validation, import/session resolution, and MRO converter dispatch.
  - Executed: `uv run pytest docs/review/temp-tests/utils/test_utils_subsystem.py --no-cov` (6 passed in 2.14s).

---

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The `django_strawberry_framework/utils/` subpackage represents an exceptionally well-engineered, layered utility foundation. Module boundaries are clean, imports are cycle-safe, public exports are minimal and intentional, and defensive contracts (such as sealed querysets, managed write transactions, and Unicode surrogate rejection) fail closed with precision. All cross-module contracts are strictly tested and verified across 762 focused unit tests and multi-module integration tests.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/utils/` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/utils/` (762 tests) exhaustively covers the entire utils foundation, pinning queryset sealing, transaction management, pagination bounds, permission traversal, MRO conversion, string casing, type unwrapping, and session actor leasing.
- **Scratch verification:**
  - `docs/review/temp-tests/utils/test_utils_subsystem.py` passed (6/6 tests), confirming cross-module integration across naming, context, errors, write validation, imports, sessions, and converter dispatch.
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/utils/` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/utils/` passed with all 17 files formatted.
- **Evidence for rejected findings:**
  - No defects or architectural regressions found; all 15 submodules uphold their architectural and safety invariants.
- **Changelog:**
  - No changelog entry required (zero-edit review cycle).

## Independent verification (Worker 2)

### Verification Summary
- **Layered Architecture & Cycle Freedom**: Independently verified that `django_strawberry_framework/utils/` implements a strictly stratified, 4-tier utility hierarchy with zero cyclic imports across all 15 submodules (`connections.py`, `context.py`, `converters.py`, `errors.py`, `imports.py`, `input_values.py`, `inputs.py`, `permissions.py`, `policies.py`, `querysets.py`, `relations.py`, `sessions.py`, `strings.py`, `typing.py`, `write_transaction.py`, `write_values.py`).
- **Defensive Invariants & Boundaries**:
  1. *Sealed Execution Queryset*: Reconstructed querysets from immutable query state (`_seal_or_defect`), neutralizing hostile method shadowing or instance overrides.
  2. *Managed Write Pipelines*: Enforced transaction guarantees (`require_managed_write`), router alias pinning (`resolve_write_alias`), base row locking, and disappearing-row conflict detection.
  3. *Surrogate & Scalar Validation*: Verified lone Unicode surrogate rejection (`unencodable_text_error`), choice enum unwrapping, and relation pk coercion.
  4. *Fail-Loud Converter Dispatch*: Verified MRO-based converter dispatch with fail-loud diagnostics.
  5. *Active-Input Traversal & Permission Gates*: Verified set-input traversal with symmetric HTTP/Channels permission handling.
  6. *Session & Actor Lease Synchronization*: Verified atomic WebSocket connection actor leasing and state transitions.
- **Export Boundaries**: Confirmed `django_strawberry_framework/utils/__init__.py` exposes only curated, high-level primitives (`RelationKind`, `is_many_side_relation_kind`, `pascal_case`, `relation_kind`, `snake_case`, `unwrap_graphql_type`, `unwrap_return_type`), and each submodule defines explicit, tight `__all__` boundaries.
- **Test Execution**:
  - `uv run pytest tests/utils/ --no-cov` (762 passed in 6.52s).
  - `uv run pytest docs/review/temp-tests/utils/test_utils_subsystem.py --no-cov` (6 passed in 1.58s).
- **Static Analysis & Formatting**:
  - `uv run ruff check django_strawberry_framework/utils/` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/utils/` passed cleanly on all 17 files.
- **Diff Hygiene**: Confirmed zero unintended modifications or scope creep against cycle baseline `HEAD` (`12779c99`).

