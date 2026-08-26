# Review: `django_strawberry_framework/schema.py`

Status: verified

## Understanding

`django_strawberry_framework/schema.py` provides the package's primary schema class (`DjangoSchema`) and mutation execution context (`DjangoMutationExecutionContext`), along with alias-scoped async mutexes (`_AsyncAliasLock`, `_AcquireHandoff`, `_async_mutation_lock`) for completion-spanning database transaction management.

It owns:
1. **`DjangoMutationExecutionContext`**:
   - Subclasses `graphql.execution.execute.ExecutionContext`.
   - Intercepts top-level mutation fields via `_marked_mutation_class(parent_type, field_nodes)`.
   - Identifies whether a field is a framework mutation by checking if `parent_type` is the schema's `mutation_type`, extracting `strawberry-definition` from `GraphQLField.extensions`, and reading `MUTATION_CLASS_MARKER` (`_django_mutation_cls`) stamped on the resolver by `DjangoMutationField`.
   - Binds the write alias via `resolve_write_alias(model)`.
   - In synchronous execution (`_execute_mutation_field_sync`): opens `transaction.atomic(using=alias)` and `managed_write_transaction(alias)`, runs `super().execute_field()`, detects collected execution errors across graphql-core versions via `_execution_errors()`, and marks rollback with `transaction.set_rollback(True, using=alias)` before atomic exit if any field or completion errors were recorded. Unhandled escaping exceptions cleanly trigger `atomic.__exit__` before re-raising.
   - In asynchronous execution (`_execute_mutation_field_async`): serializes per-alias mutation windows with `_async_mutation_lock(alias)`, dispatches `atomic.__enter__` into the thread-sensitive worker via `run_in_one_sync_boundary`, holds the atomic transaction open across value completion (`await result`), catches exceptions or detects recorded errors, invokes `set_rollback(True)` if needed, and closes the atomic block on the thread-sensitive worker connection via `atomic.__exit__`.
2. **`_AcquireHandoff` and `_AsyncAliasLock`**:
   - Manages process-wide mutexes per write database alias to prevent concurrent async requests on the shared `thread_sensitive=True` worker connection from creating interleaved, nested savepoints.
   - Resilient against task cancellation: `_AcquireHandoff` coordinates between the executor thread and the awaiting task under a mutex guard. If the awaiting task is cancelled while the worker thread is blocked in `threading.Lock.acquire()`, the cancellation hand-off ensures that whichever side observes the abandonment immediately releases the mutex, preventing stranded locks or deadlocks.
3. **`DjangoSchema`**:
   - Subclasses `strawberry.Schema` to install `DjangoMutationExecutionContext` by default if `execution_context_class` is omitted.
   - Resolves and validates `resource_policy` at construction time via `resolve_resource_policy()`, failing fast at deployment startup on invalid configuration with `ConfigurationError`.
   - Resolves and validates `error_policy` at construction time via `resolve_error_policy()`, similarly failing fast on invalid options.
   - Automatically injects `DjangoResourcePolicyExtension` at the end of the `extensions` list (via `_with_resource_policy_extension`) unless explicitly provided by the consumer.
   - Automatically prepends `DjangoErrorPolicyExtension` at the start of the `extensions` list (via `_with_error_policy_extension`) unless explicitly provided, ensuring error masking executes last during LIFO teardown.
   - Overrides `get_extensions()` to deduplicate the automatic error policy extension when a consumer-supplied factory callable produces an explicit `DjangoErrorPolicyExtension` instance at runtime.

## Verification

1. Traced callers, dependencies, and integration seams:
   - `django_strawberry_framework/__init__.py`: exports `DjangoSchema` and `DjangoMutationExecutionContext`.
   - `django_strawberry_framework/mutations/fields.py`: stamps `MUTATION_CLASS_MARKER` on mutation resolvers.
   - `django_strawberry_framework/utils/write_transaction.py`: provides `managed_write_transaction`, `resolve_write_alias`, and `_MANAGED_WRITE_ALIAS`.
   - `django_strawberry_framework/utils/querysets.py`: provides `run_in_one_sync_boundary` for thread-sensitive worker dispatch.
   - `django_strawberry_framework/extensions/error_policy.py` & `django_strawberry_framework/extensions/resource_policy.py`: extensions installed and ordered by `DjangoSchema`.
2. Examined test suites:
   - `tests/test_schema.py`: tested schema initialization with None/iterables, extension resolution, deduplication, adversarial metaclass checking in `_extension_entry_matches`, `_marked_mutation_class` edge cases, and basic query execution.
   - `tests/mutations/test_write_transaction.py`: tested `_AsyncAliasLock` cancellation resilience, concurrent async transaction serialization, and sync/async execution context error handling.
   - `examples/fakeshop/test_query/test_mutation_atomicity.py`: live HTTP GraphQL acceptance tests for completion-spanning rollback on create, update, delete, and scalar mutations.
3. Scratch experiments (`docs/review/temp-tests/schema/test_schema_scratch.py`):
   - Verified that GraphQL aliased mutations (e.g. `myAlias: updateItem(...)`) correctly resolve their underlying schema field name and open managed transactions.
   - Verified schema construction validation for `ResourcePolicy` and `ErrorPolicy` (rejecting invalid bounds/options with `ConfigurationError`).
   - Verified `_async_mutation_lock` returns identical mutex instances for matching aliases and distinct mutexes for different aliases.
   - Verified that unhandled escaping exceptions during sync and async mutation execution properly trigger `atomic.__exit__` transaction rollback.
4. Focused test executions:
   - `uv run pytest tests/test_schema.py --no-cov`: 19 passed.
   - `uv run pytest tests/mutations/test_write_transaction.py --no-cov`: 53 passed (72 total across both test files).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/schema.py` is well-architected, robust, and correctly enforces the write atomicity, alias locking, cancellation hand-off, and extension lifecycle contracts. Permanent behavioral tests were added to `tests/test_schema.py` to directly pin schema configuration validation, per-alias async mutex caching, and execution-context exception-handling rollback paths.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/test_schema.py`: added 5 permanent behavioral tests (`test_schema_policy_resolution_and_validation`, `test_async_mutation_lock_caching_per_alias`, `test_async_alias_lock_context_manager`, `test_execute_mutation_field_sync_exception_rolls_back`, `test_execute_mutation_field_async_exception_rolls_back`).
- **Permanent tests and pinned behavior:**
  - `tests/test_schema.py` (19 tests) pins schema instantiation, policy normalization and failure validation, extension ordering and factory deduplication, `_AsyncAliasLock` alias isolation and context management, `_marked_mutation_class` node inspection, and sync/async execution context error/exception rollback handling.
- **Scratch verification:**
  - `docs/review/temp-tests/schema/test_schema_scratch.py` passed (5/5 tests).
  - `uv run pytest tests/test_schema.py --no-cov` passed (19/19 tests).
  - `uv run pytest tests/test_schema.py tests/mutations/test_write_transaction.py --no-cov` passed (72/72 tests).
- **Formatter and linter results:**
  - `uv run ruff format .` passed with 0 errors.
  - `uv run ruff check --fix .` passed with 0 errors.
  - `python3 scripts/check_trailing_commas.py --check django_strawberry_framework/schema.py tests/test_schema.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

- **System and behavior re-traced:**
  - `DjangoMutationExecutionContext`: Verified write alias resolution via `resolve_write_alias(model)`, sync execution transaction wrapping around `super().execute_field()`, error detection via `_execution_errors()`, and async execution boundary dispatch via `run_in_one_sync_boundary` holding `atomic` transactions open across value completion.
  - `_AsyncAliasLock` & `_AcquireHandoff`: Re-traced process-wide mutex caching per write alias, serialization of async completion windows across event loops, and cancellation hand-off safety preventing stranded locks.
  - `DjangoSchema`: Re-traced startup policy resolution and validation (`resolve_resource_policy`, `resolve_error_policy`), automatic extension injection ordering (error policy prepended for LIFO teardown masking, resource policy appended for pre-execution gating), and runtime deduplication of error policy extensions when instantiated via custom factories.
- **Scoped diff reviewed:**
  - `git diff 12779c99 -- django_strawberry_framework/schema.py tests/test_schema.py` reviewed. Zero diff on `django_strawberry_framework/schema.py`; `tests/test_schema.py` adds 5 permanent behavioral tests.
- **Independent scratch verification (`docs/review/temp-tests/schema/test_worker2_scratch.py`):**
  - Verified async alias lock FIFO concurrency ordering across tasks.
  - Verified `get_extensions` idempotency on repeated calls across sync and async contexts.
  - Verified deduplication of auto error policy extension when custom factory returns instance.
  - Verified sync and async execution context error rollback on custom database aliases.
  - 5/5 passed (`uv run pytest docs/review/temp-tests/schema/test_worker2_scratch.py --no-cov`).
- **Focused test suite executions:**
  - `tests/test_schema.py` & `tests/mutations/test_write_transaction.py`: 72/72 passed.
  - `examples/fakeshop/test_query/test_mutation_atomicity.py`: 6/6 passed.
- **Findings disposition:**
  - Confirmed 0 High, 0 Medium, 0 Low findings; behavior is correct, robust, and cleanly tested.
- **Quality and hygiene:**
  - `uv run ruff check django_strawberry_framework/schema.py tests/test_schema.py` passed with 0 errors.
  - `python3 scripts/check_trailing_commas.py --check django_strawberry_framework/schema.py tests/test_schema.py` passed with 0 errors.
  - Unrelated files preserved.

