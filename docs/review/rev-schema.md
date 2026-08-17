# Review: `django_strawberry_framework/schema.py`

Status: verified

## Understanding

`DjangoSchema` owns the package's schema-construction boundary: it resolves and exposes the immutable resource/error policies, installs their per-operation extensions, and defaults Strawberry to `DjangoMutationExecutionContext`. The execution context recognizes only marked generated mutation fields at the GraphQL mutation root, opens one `transaction.atomic(using=...)` around resolve plus value completion, publishes the managed write alias, and marks rollback when GraphQL adds a located error. Sync execution keeps that window on the calling thread; async execution enters, runs ORM work, awaits completion, and exits through `utils/querysets.py::run_in_one_sync_boundary`, so all ORM calls use one thread-sensitive Django connection.

The scoped baseline `84046e486c51e50861ea95eb7e1da73bfb1fb6b1` had no `schema.py` diff before this implementation. Connected mutation resolvers use the managed alias and their own nested atomic/savepoint for in-band `FieldError` rollback; policy extensions run at operation lifecycle boundaries; the fakeshop aggregate schema constructs `DjangoSchema` for generated mutations.

## Verification

- Traced marker production in `mutations/fields.py::DjangoMutationField`, marker recognition in `schema.py::DjangoMutationExecutionContext._marked_mutation_class`, GraphQL's `execute_field` completion behavior, sync/async error-list handling, alias routing, nested mutation atomics, and schema extension ordering.
- Existing focused coverage passed before the change: `uv run pytest --no-cov tests/mutations/test_write_transaction.py tests/test_error_policy.py tests/test_resource_policy.py -q` — 175 passed.
- Disposable `docs/review/temp-tests/schema/test_concurrent_transactions.py` forced two concurrent `schema.execute` calls to suspend while the first completion-spanning atomic remained open. Before the fix, the shared asgiref worker observed savepoint depths `(True, 0)` then `(True, 1)`, proving the second request nested on the first request's connection. After the fix, the observations are `(True, 0)` and `(True, 0)` with no teardown warnings.
- Final focused validation passed: `uv run pytest tests/mutations/test_write_transaction.py examples/fakeshop/test_query/test_mutation_atomicity.py tests/test_error_policy.py tests/test_resource_policy.py --no-cov -q` — 183 passed.

## Improvements

### High

- **Observation:** Concurrent async generated mutations could enter nested transactions on one shared Django connection.
- **Evidence:** `DjangoMutationExecutionContext._execute_mutation_field_async` held `transaction.atomic()` across an `await` while every `run_in_one_sync_boundary` call used `thread_sensitive=True`. Without an explicit `ThreadSensitiveContext`, asgiref's default is one process-wide worker. The disposable concurrent schema probe reproduced savepoint depth `0` for request one and `1` for request two before either completion finished.
- **Impact:** The second request's write was inside the first request's outer transaction rather than an independent transaction. A later completion failure or rollback in request one could erase request two's apparently successful write; request two could also be committed only when request one committed. This violated request/operation isolation and the documented independent transaction contract.
- **Recommendation:** Serialize only completion-spanning mutation windows per effective write alias with a process-wide mutex whose blocking acquisition runs outside the Django worker. Keep the existing shared thread-sensitive worker and transaction lifecycle; different aliases retain independent concurrency across event loops.
- **Proof:** `tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_do_not_nest_transactions`, `tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_across_event_loops_do_not_nest_transactions`, and the disposable schema probe assert both operations observe an outer transaction with zero nested savepoints. Existing async commit/rollback and live completion-failure tests continue to pass.

### Medium

None.

### Low

None.

## Summary

The schema correctly owns mutation transaction completion, policy resolution/extension lifecycle, marker gating, sync/async execution, and error rollback. One high-severity async isolation defect was confirmed with a deterministic concurrent schema execution probe and fixed at the execution-context boundary by alias-scoped async serialization. No other schema finding was justified.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/schema.py`: added a process-wide effective-alias mutex with a threading guard and non-Django-worker acquisition, then acquired it around each async generated-mutation resolve-to-completion transaction. This prevents shared-worker savepoint nesting across same or different event loops while preserving alias-level concurrency. Updated the execution-mode documentation.
- Changed `tests/mutations/test_write_transaction.py`: added same-loop and cross-event-loop concurrency regressions, both pinning zero nested savepoints.
- Scratch verification: `docs/review/temp-tests/schema/test_concurrent_transactions.py` reproduced the pre-fix nested savepoint and passed after the lock fix.
- Focused validation: `uv run pytest tests/mutations/test_write_transaction.py examples/fakeshop/test_query/test_mutation_atomicity.py tests/test_error_policy.py tests/test_resource_policy.py --no-cov -q` — 183 passed.
- Formatter/linter: `uv run ruff format .` and `uv run ruff check --fix .` passed.
- Rejected findings: no changes were made to sync transaction handling, GraphQL error-list compatibility, marker/root-field recognition, policy precedence, extension ordering, resource/error masking, or live HTTP completion rollback; connected source tracing and focused tests support those contracts.
- Changelog: no entry added; this is an alpha correctness and isolation fix.

## Iterations

### Worker 1 revision after Worker 2 verification

- Reproduced the test-oracle gap: the original same-loop regression released the first operation immediately after scheduling the second, so replacing `_async_mutation_lock` with a no-op allowed the second to enter without the test asserting overlap.
- Revised `tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_do_not_nest_transactions` and `docs/review/temp-tests/schema/test_concurrent_transactions.py` to hold the first completion, assert the second has not entered while the mutex is active, release the first, then release the second independently. A temporary no-lock harness now fails at the pre-entry assertion; lock-enabled execution passes.
- Reproduced the additional cross-event-loop gap: a `WeakKeyDictionary` keyed by event loop did not coordinate two loops that still share asgiref's process-wide thread-sensitive worker.
- Changed `django_strawberry_framework/schema.py` to use a process-wide mutex per effective write alias. Blocking mutex acquisition runs through each loop's ordinary executor (never the Django worker), so separate loops serialize the shared connection without deadlocking the worker; distinct aliases remain independent.
- Added `tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_across_event_loops_do_not_nest_transactions`, which drives two `asyncio.run` calls in separate threads and pins zero nested savepoints.
- Focused revision validation: same-loop and cross-loop regressions passed; the no-lock same-loop harness failed as expected. Full mutation/live/policy focused validation and formatter/linter are rerun after this revision below.

## Independent verification (Worker 2)

### Scope and connected behavior traced

- Compared `django_strawberry_framework/schema.py` and `tests/mutations/test_write_transaction.py` against scoped baseline `84046e486c51e50861ea95eb7e1da73bfb1fb6b1`; the implementation change is the async lock map and its use around the existing transaction window, with the new permanent concurrency test.
- Re-traced `DjangoMutationExecutionContext.execute_field` marker gating, `resolve_write_alias`, `transaction.atomic` enter/exit, `managed_write_transaction`, `run_in_one_sync_boundary` (`sync_to_async(thread_sensitive=True)`), GraphQL completion/error rollback, mutation resolver pipeline alias pinning, and the sync path. Existing policy/resource extensions and live completion-failure behavior remain outside the lock.
- Same-loop lock behavior is alias-scoped: a held `default` lock blocks a second `default` acquisition, while a `shard_b` acquisition enters concurrently.

### Verification evidence

- `uv run pytest tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_do_not_nest_transactions --no-cov -q` — 1 passed.
- `uv run pytest tests/mutations/test_write_transaction.py examples/fakeshop/test_query/test_mutation_atomicity.py tests/test_error_policy.py tests/test_resource_policy.py --no-cov -q` — 182 passed.
- `uv run pytest docs/review/temp-tests/schema/test_concurrent_transactions.py --no-cov -q` — 1 passed.
- A disposable no-lock variant replaced `schema._async_mutation_lock` with a no-op and ran the permanent test unchanged; it still passed because the test sets `release_first` immediately after scheduling the second operation. The first operation can therefore close its atomic before the second enters, so the permanent test does not fail on the pre-fix implementation.
- A corrected disposable no-lock probe that waits until the second field has entered before releasing the first observed the shared worker/connection at `(in_atomic_block=True, savepoint depth=0)` and `(True, 1)`, and failed the no-nesting assertion. The permanent test needs an explicit overlap barrier that remains satisfiable with the real lock.
- `asgiref 3.11.1` inspection and a two-event-loop disposable probe confirmed the default `thread_sensitive=True` executor is process-wide. The current `WeakKeyDictionary[event_loop][alias]` lock map allowed two event loops to enter `default` concurrently; actual `transaction.atomic` windows then observed the same worker and nested savepoint depth 1 in both windows. This is a same-alias isolation defect when one process hosts more than one event loop.

### Required revisions

1. Make the permanent regression test force the second transaction to overlap the first without deadlocking the fixed implementation, then run it with the lock disabled and record the expected nested-depth failure.
2. Guard same-alias async windows across event loops sharing asgiref's process-wide thread-sensitive worker, while retaining independent concurrency for different aliases. A process-wide alias guard that can be awaited without blocking the event loop, or an equivalent connection-isolating design that preserves SQLite behavior, needs a focused cross-loop regression test.

Until those revisions land, the transaction lifecycle and same-loop alias behavior are supported by the focused suite, but item 20 is not verified.

## Iterations

### Worker 1 revision after Worker 2 verification (final)

- Reworked `_async_mutation_lock` from a `WeakKeyDictionary` keyed by event loop to a process-wide `_AsyncAliasLock` keyed by effective write alias. The mutex uses `asyncio.to_thread` for blocking acquisition, never blocking the shared Django worker; cancellation waits for acquisition, releases ownership, and preserves cancellation.
- Added `tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_across_event_loops_do_not_nest_transactions`, running two `asyncio.run` executions in separate threads. The test holds the first completion, proves the second cannot enter before release, then releases each operation independently and asserts `(True, 0)` savepoint depth for both.
- The same-loop regression now uses separate release events and asserts the second field has not entered while the first holds the lock. A temporary no-lock harness fails the pre-entry assertion, proving the oracle rejects the old implementation; lock-enabled same-loop and cross-loop regressions pass.
- Focused validation: `uv run pytest tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_do_not_nest_transactions tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_across_event_loops_do_not_nest_transactions --no-cov -q` — 2 passed; `uv run pytest docs/review/temp-tests/schema/test_concurrent_transactions.py --no-cov -q` — 1 passed; full focused mutation/live/policy command — 183 passed.
- Formatter/linter rerun: `uv run ruff format .` and `uv run ruff check --fix .` passed.
- Status is now `fix-implemented`; the plan checkbox remains untouched for Worker 2.

## Independent verification (Worker 2, pass 2)

### Scope and lifecycle re-trace

- Re-checked `django_strawberry_framework/schema.py` and `tests/mutations/test_write_transaction.py` against scoped baseline `84046e486c51e50861ea95eb7e1da73bfb1fb6b1`; no unrelated target behavior was absorbed. Re-traced the marker gate in `DjangoMutationExecutionContext._marked_mutation_class`, sync and async `transaction.atomic` enter/exit, `managed_write_transaction`, alias resolution, `run_in_one_sync_boundary` (`sync_to_async(thread_sensitive=True)`), GraphQL completion-error rollback, and the mutation resolver's pinned write pipeline. Connected resource/error policy extensions remain schema-construction concerns and do not alter the transaction window.
- The final `_async_mutation_lock` implementation is process-wide per effective alias, uses a guarded map, and blocks only in `asyncio.to_thread`; the Django thread-sensitive worker is not used for mutex acquisition. `threading.Lock` ownership is released on normal `__aexit__` and on cancellation after the executor-side acquire is drained.

### Verification evidence

- `uv run pytest tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_do_not_nest_transactions tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_across_event_loops_do_not_nest_transactions docs/review/temp-tests/schema/test_concurrent_transactions.py --no-cov -q` — 3 passed.
- `uv run pytest tests/mutations/test_write_transaction.py examples/fakeshop/test_query/test_mutation_atomicity.py tests/test_error_policy.py tests/test_resource_policy.py --no-cov -q` — 183 passed.
- An in-process no-op replacement of `schema._async_mutation_lock`, with xdist disabled so the patched module was exercised, failed the permanent same-loop regression at its overlap assertion (`assert not second_started.is_set()`), proving the release barrier forces the old behavior to fail.
- The current process-wide alias map passed disposable probes for queued-task cancellation cleanup and concurrent `default` / `shard_b` windows. A disposable schema probe using the rejected event-loop-keyed map allowed cross-loop entry and observed `[(True, 0), (True, 1)]` on asgiref's shared worker; the permanent cross-loop regression passes with the process-wide map and asserts `[(True, 0), (True, 0)]`.

### Remaining revision

- **Medium — stale behavior comment:** `django_strawberry_framework/schema.py::DjangoMutationExecutionContext._execute_mutation_field_async` still says the mutex is “scoped to this event loop and effective write alias,” while `_async_mutation_lock` and the module contract make it process-wide per alias specifically to coordinate separate event loops sharing asgiref's worker. This is directly misleading for maintainers auditing the isolation boundary.
- **Required fix:** update that comment to say “process-wide per effective write alias” (and retain the distinct-alias concurrency statement), then rerun the focused item-20 tests. No source edit was made in this verification pass per the Worker 2 constraint.

Until that comment is corrected, item 20 remains `revision-needed` and its plan checkbox stays unchecked.

## Iterations

### Worker 1 revision after Worker 2 verification (comment correction)

- Corrected `django_strawberry_framework/schema.py::DjangoMutationExecutionContext._execute_mutation_field_async` so the lifecycle comment now accurately says the mutex is process-wide per effective write alias, while preserving the statement that different aliases remain independent.
- Focused validation: `uv run pytest tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_do_not_nest_transactions tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_across_event_loops_do_not_nest_transactions --no-cov -q` — 2 passed; `uv run pytest tests/mutations/test_write_transaction.py examples/fakeshop/test_query/test_mutation_atomicity.py tests/test_error_policy.py tests/test_resource_policy.py --no-cov -q` — 183 passed.
- Formatter/linter rerun: `uv run ruff format .` and `uv run ruff check --fix .` passed; scoped `git diff --check` is clean.
- Status is `fix-implemented`; the plan checkbox remains untouched for Worker 2.

## Independent verification (Worker 2, pass 3)

### Scope and comment verification

- Re-traced `DjangoMutationExecutionContext._execute_mutation_field_async` through `_async_mutation_lock`, `resolve_write_alias`, the completion-spanning `transaction.atomic`, `managed_write_transaction`, and `run_in_one_sync_boundary`; the mutex is process-wide per effective write alias and acquisition remains outside the Django thread-sensitive worker, while distinct aliases remain independent.
- Confirmed the corrected lifecycle comment says “process-wide per effective write alias” and contains no stale event-loop-scoped description. The module contract, lock map, and same-loop/cross-loop regression assertions agree.
- Compared `django_strawberry_framework/schema.py` and `tests/mutations/test_write_transaction.py` against baseline `84046e486c51e50861ea95eb7e1da73bfb1fb6b1`; the scoped implementation remains limited to the alias mutex and its two isolation regressions. The unrelated dirty `examples/fakeshop/db.sqlite3` path was not edited or absorbed.

### Verification evidence

- `uv run pytest tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_do_not_nest_transactions tests/mutations/test_write_transaction.py::test_concurrent_async_mutations_across_event_loops_do_not_nest_transactions docs/review/temp-tests/schema/test_concurrent_transactions.py --no-cov -q` — 3 passed.
- `uv run pytest tests/mutations/test_write_transaction.py examples/fakeshop/test_query/test_mutation_atomicity.py tests/test_error_policy.py tests/test_resource_policy.py --no-cov -q` — 183 passed.
- `git --no-pager diff --check -- django_strawberry_framework/schema.py tests/mutations/test_write_transaction.py docs/review/rev-schema.md` — clean; final source inspection found no stale lock-scope wording.

### Outcome

No findings remain. Item 20 is independently verified: same-alias mutation windows cannot overlap on the shared thread-sensitive connection across either same or separate event loops, distinct aliases retain concurrency, completion rollback coverage remains green, and the final comment accurately documents the process-wide per-effective-write-alias scope.
