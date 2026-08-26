# Review: `django_strawberry_framework/optimizer/_context.py`

Status: verified

## Understanding

`django_strawberry_framework/optimizer/_context.py` owns the optimizer-to-resolver context hand-off key vocabulary, ContextVar execution state isolation, and start-of-execution context reset:

1. **Stash Key Vocabulary**: Defines canonical string constants used to communicate optimization metadata on GraphQL request contexts (`DST_OPTIMIZER_PLAN`, `DST_OPTIMIZER_FK_ID_ELISIONS`, `DST_OPTIMIZER_PLANNED`, `DST_OPTIMIZER_LOOKUP_PATHS`, `DST_OPTIMIZER_STRICTNESS`), grouped in `DST_OPTIMIZER_KEYS`.
2. **Context Helpers Re-export**: Re-exports `get_context_value` and `stash_on_context` from `django_strawberry_framework.utils.context` to maintain backward-compatible import paths for optimizer subsystems and tests.
3. **Start-of-Execution Reset**: `clear_optimizer_context(context)` clears all `DST_OPTIMIZER_KEYS` from the supplied context (handling `None`, objects, dicts, `__slots__` mappings, and read-only/frozen mapping shapes via `clear_context_key`). This prevents reused request contexts from leaking stale FK-id elision stubs or planned-relation sentinels across operations.
4. **Execution-Scoped Relations State**: Manages `_scoped_relations` via a `ContextVar[set[str] | None]` with lifecycle functions `begin_scoped_relations()`, `end_scoped_relations(token)`, `publish_scoped_relations(keys)`, and `relation_is_optimizer_scoped(key)`. This provides task-local tracking of relations planned by the optimizer during the active execution without relying on mutable request context availability.
5. **Execution Strictness State**: Manages `_active_strictness` via a `ContextVar[str | None]` with lifecycle functions `begin_strictness(strictness)`, `end_strictness(token)`, and `active_strictness()`, guaranteeing N+1 strictness enforcement remains armed across root planning variations and context-less executions.

## Verification

1. **Existing Test Suite**: Examined and executed the suite in `tests/optimizer/test_extension.py`:
   - `test_optimizer_context_all_exports`: Confirms all 16 symbols are exported and listed in `__all__`.
   - `test_clear_optimizer_context_removes_all_keys_from_object_and_dict`: Confirms clear drops all 5 keys from object and dict contexts.
   - `test_clear_optimizer_context_clears_slots_mapping_via_item_delete`: Validates `del` item fallback for slots mappings.
   - `test_clear_optimizer_context_none_and_frozen_are_noops`: Confirms safe handling for `None` and `MappingProxyType`.
   - `test_clear_optimizer_context_locked_querydict_is_noop`: Confirms immutable `QueryDict` does not raise.
   - `test_publish_scoped_relations_handles_falsy_and_none_when_active_and_inactive`: Confirms safe no-op on falsy inputs and proper consumption of iterables/generators.
   - `test_relation_is_optimizer_scoped_unhashable_fail_closed`: Verifies unhashable objects return `False` rather than raising `TypeError`.
   - `test_strictness_and_scoped_relations_reentrant_isolation`: Verifies re-entrant nested executions isolate strictness and scoped relations and restore cleanly.
2. **Cross-Subsystem Integration**: Traced consumption in `django_strawberry_framework/optimizer/extension.py` (start-of-execution clear and plan publication) and `django_strawberry_framework/types/resolvers.py` (checking scoped relations and active strictness).
3. **Scratch Verification**: Created and executed `docs/review/temp-tests/optimizer/_context/test_scratch.py` validating cumulative publishes, re-entrant context isolation, and clearing behaviors (1 passed).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/optimizer/_context.py` is a clean, well-factored internal module providing execution-isolated context state and reset helpers for the optimizer. Contracts are sound, robust against edge cases (such as unhashable inputs, missing contexts, and frozen mappings), and comprehensively tested.

## Implementation (Worker 1)

None — zero-edit cycle

- **Changed files**: None.
- **Permanent tests**: Existing test coverage in `tests/optimizer/test_extension.py` lines 3880–4110 comprehensively pins all constants, exports, error boundaries, and ContextVar lifecycles.
- **Scratch verification**: `docs/review/temp-tests/optimizer/_context/test_scratch.py` passed (1 test, 0 failures).
- **Formatter and linter**: Zero-edit cycle (no code modifications made).
- **Evidence for rejected findings**: No findings raised or rejected; all investigated code paths behave according to design and specifications.
- **Changelog**: Does not merit a changelog entry (zero-edit cycle).

## Independent verification (Worker 2)

- **Baseline confirmation**: Zero diff against cycle baseline `12779c99` confirmed via `git diff 12779c99 -- django_strawberry_framework/optimizer/_context.py`.
- **Behavior re-trace**:
  - `DST_OPTIMIZER_KEYS` tuple and stash key constants (`DST_OPTIMIZER_PLAN`, `DST_OPTIMIZER_FK_ID_ELISIONS`, `DST_OPTIMIZER_PLANNED`, `DST_OPTIMIZER_LOOKUP_PATHS`, `DST_OPTIMIZER_STRICTNESS`) accurately capture all optimizer stash keys across the extension, walker, nested planner, and resolvers.
  - `clear_optimizer_context` cleanly dispatches key deletion via `utils/context.py::clear_context_key`, robustly handling `None`, dicts, arbitrary objects, `__slots__` mappings, and read-only/frozen mapping types without exceptions.
  - ContextVar lifecycle management for `_scoped_relations` (`begin_scoped_relations`, `end_scoped_relations`, `publish_scoped_relations`, `relation_is_optimizer_scoped`) correctly enforces operation isolation, cumulative unions across nested connections, fail-closed handling for unhashable lookups, and safe no-ops when inactive or given falsy inputs.
  - ContextVar lifecycle management for `_active_strictness` (`begin_strictness`, `end_strictness`, `active_strictness`) guarantees execution-scoped strictness tracking even across operations with untyped root resolvers or missing context objects.
  - Re-exports of `get_context_value` and `stash_on_context` from `django_strawberry_framework.utils.context` maintain complete backward compatibility, and `__all__` correctly contains all 16 symbols.
- **Test execution**: Ran focused tests in `tests/optimizer/test_extension.py` matching context lifecycle and clearing behaviors (`8 passed in 3.22s`).
- **Disposition**: Zero findings. Verified complete.
