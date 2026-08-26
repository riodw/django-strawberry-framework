# Review: `django_strawberry_framework/registry.py`

Status: verified

## Understanding

`django_strawberry_framework/registry.py` implements the process-global singleton `TypeRegistry` (exposed as `registry`) and subsystem lifecycle coordination hooks (`register_subsystem_clear`, `iter_subsystem_clears`). It serves as the single source of truth for `DjangoType` definitions, model-to-type mappings, primary type declarations for multi-type models, choice-field `Enum` reuse caches, pending relation resolution records, and per-type / subsystem lifecycle teardown callbacks.

It owns:
1. **Model & Type Registrations:**
   - `_types: dict[type[models.Model], list[type]]` maintains registered `DjangoType` classes per `models.Model` in registration order.
   - `_primaries: dict[type[models.Model], type]` tracks explicitly declared primary types (`primary=True`), used for canonical relation-target resolution.
   - `_models: dict[type, type[models.Model]]` provides 1-to-1 reverse lookup (`model_for_type`), used by `DjangoOptimizerExtension` and query planners to resolve GraphQL types back to Django models.
   - Rejects reverse-collisions (same class registered against multiple models) and duplicate primaries with clear, diagnostic `ConfigurationError`s.
2. **Atomic Definition Binding & Rollback:**
   - `register_definition` records collected `DjangoTypeDefinition` instances for concrete `DjangoType` subclasses.
   - `register_with_definition` provides an atomic pair of `register` + `register_definition`. If `register_definition` raises, any state appended by that call is rolled back and pre-existing primaries are preserved.
3. **Relay GlobalID Type Name Resolution:**
   - `definition_for_graphql_name(name)` inverts Relay-Node type name encoding during GlobalID decoding, scanning definitions for unique matches on `definition.graphql_type_name` while ignoring non-Node types and raising on miss or ambiguity.
   - `_globalid_setting_snapshot` holds the validated `RELAY_GLOBALID_STRATEGY` setting for the active build (initialized to `GLOBALID_SETTING_UNSET` and reset on `clear()`).
4. **Choice Enum Caching:**
   - `_enums: dict[tuple[type[models.Model], str], type[Enum]]` caches choice enums by `(model, field_name)`, ensuring enum reuse across multiple `DjangoType` subclasses reading the same column while rejecting conflicting enum definitions.
5. **Pending Relation Lifecycle:**
   - `add_pending_relation`, `iter_pending_relations`, and `discard_pending` manage unresolved relation records (`PendingRelation`) during type construction. `discard_pending` uses identity matching (`id()`) so non-hashable Django fields do not break resolution.
6. **Finalization Boundary & Immutability:**
   - `_finalized` flag and `_check_mutable()` guard prevent out-of-band mutation after `finalize_django_types()` runs, protecting runtime lookup caches.
7. **Subsystem Teardown & Test Isolation:**
   - Per-type teardown callbacks (`register_type_teardown`) run in LIFO order upon `unregister()` or `clear()`. Failed callbacks remain queued for retry.
   - Subsystem-wide teardown hooks (`register_subsystem_clear`) allow modules to declare their own state resets without coupling `registry.py` to concrete submodules, supporting `before_bind=True` pre-bind clearing and full test teardown.
   - `unregister(type_cls)` cleanly purges a type from all internal maps, pending relations, and evicts connection-class caches via best-effort `_clear_if_importable`.
   - `clear()` resets all internal dictionaries, snapshots, and triggers all registered subsystem teardowns.

## Verification

1. **Traced connections across callers and consumers:**
   - `django_strawberry_framework/types/base.py`: registers classes and definitions via `register_with_definition`.
   - `django_strawberry_framework/types/finalizer.py`: drives the pending relation resolution loop (`iter_pending_relations`, `discard_pending`), audits ambiguity (`models_with_multiple_types`), reads `GLOBALID_SETTING_UNSET`, and invokes `iter_subsystem_clears(before_bind=True)`.
   - `django_strawberry_framework/types/converters.py`: resolves relation targets via `registry.get()` and caches enums via `register_enum` / `get_enum`.
   - `django_strawberry_framework/types/relay.py` & `django_strawberry_framework/testing/relay.py`: decodes GlobalID type names via `registry.definition_for_graphql_name()`.
   - `django_strawberry_framework/optimizer/extension.py` & `django_strawberry_framework/optimizer/walker.py`: inspects models via `registry.model_for_type()`.
   - Subsystems (`auth`, `connection`, `filters`, `forms`, `mutations`, `orders`, `relay`, `rest_framework`): register teardown callbacks via `register_subsystem_clear`.
2. **Examined existing test suites:**
   - `tests/test_registry.py` (80 tests): thoroughly tests type registration, primary flags, duplicate collision handling, reverse lookups, choice enum caching, atomic rollbacks, pending relation identity discards, finalization guards, `unregister` semantics, and subsystem clear resiliency under unimportable modules.
   - `tests/types/test_relay_interfaces.py` (526 tests): tests `definition_for_graphql_name`, GlobalID decoding strategies, and build-level setting snapshots.
3. **Focused test execution:**
   - `uv run pytest tests/test_registry.py --no-cov` passed (80 passed).
   - `uv run pytest tests/types/ --no-cov` passed (526 passed, 2 skipped).
   - Line coverage on `django_strawberry_framework/registry.py` is 100% (143/143 statements).
4. **Scratch verification:**
   - `docs/review/temp-tests/registry/test_registry_scratch.py` passed (3/3 tests), probing `_clear_if_importable`, subsystem clear overwrites, full registration/teardown/unregister/finalize lifecycle, and mutability guards.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/registry.py` provides a robust, fail-closed, and well-isolated registry for types, models, definitions, enums, pending relations, and lifecycle teardowns. The architecture cleanly separates registration-time mutation from post-finalization immutability, provides atomic definition registration with rollback, and enables decoupled subsystem teardown without circular dependencies. Test coverage is 100% with no defects or design improvements identified.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/registry.py` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/test_registry.py` (80 tests) and `tests/types/test_relay_interfaces.py` pin all registry behaviors, error paths, lookup behaviors, multi-type primary semantics, atomic definition rollback, globalid strategy caching, teardown callbacks, and unimportable module tolerance.
- **Scratch verification:**
  - `docs/review/temp-tests/registry/test_registry_scratch.py` passed (3/3 tests).
  - Focused pytest suite passed (80 unit tests in `tests/test_registry.py`, 526 in `tests/types/`).
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/registry.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/registry.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- **Behavior and Path Re-tracing:**
  - Re-traced model and type registration state (`_types`, `_primaries`, `_models`), verifying reverse-collision detection (same type registered across different models), primary uniqueness per model, and immutability of primary declarations under idempotent re-registration.
  - Re-traced atomic registration rollback in `register_with_definition`, verifying that failed `register_definition` calls cleanly detach newly added types via `_detach_type_from_model` and restore pre-existing primary flags.
  - Re-traced Relay GlobalID type-name resolution in `definition_for_graphql_name`, verifying that it filters by `implements_relay_node(type_cls)` against `definition.graphql_type_name`, correctly rejecting non-Node types, unknown type names, and ambiguous duplicate type names.
  - Re-traced Choice Enum caching (`register_enum`, `get_enum`), confirming that identical enum classes are reused across types and conflicting enum registrations fail loud.
  - Re-traced pending relation lifecycle (`add_pending_relation`, `iter_pending_relations`, `discard_pending`), confirming identity matching (`id()`) so non-hashable Django fields are safely handled.
  - Re-traced immutability boundaries (`_finalized` flag and `_check_mutable()` defense-in-depth guard), confirming that post-finalization mutation attempts in `register`, `register_type_teardown`, `unregister`, `register_definition`, `add_pending_relation`, `discard_pending`, and `register_enum` raise `ConfigurationError`.
  - Re-traced subsystem and per-type teardown mechanics (`register_subsystem_clear`, `iter_subsystem_clears`, `register_type_teardown`, `_run_type_teardowns`), confirming LIFO per-type teardown execution with retry queueing on failure, lazy decoupled subsystem clears supporting `before_bind=True` filtering, and safe connection-class cache eviction via `_clear_if_importable`.
- **Scoped Diff Verification:**
  - Verified empty diff against baseline `12779c99` (`git diff 12779c99 -- django_strawberry_framework/registry.py`).
- **Test Executions:**
  - `uv run pytest tests/test_registry.py --no-cov`: 80/80 passed.
  - `uv run pytest docs/review/temp-tests/registry/test_registry_scratch.py --no-cov`: 3/3 passed.
  - `uv run pytest tests/types/test_relay_interfaces.py --no-cov`: 141/141 passed.
- **Disposition:**
  - Zero findings confirmed. Implementation is robust, well-architected, and fully verified. Status set to `verified`.

