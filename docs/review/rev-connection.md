# Review: `django_strawberry_framework/connection.py`

Status: verified

## Understanding

`connection.py` owns the Relay connection factory and generated connection classes, the
visibility/filter/order/default-order/optimizer composition pipeline, offset and keyset window
consumption, selection-gated totals, and sync/async dispatch. Root fields enter through
`DjangoConnectionField`; synthesized relation connections enter through the same generated
connection classes after optimizer window planning. Ordinary offset pagination delegates cursor
mechanics to Strawberry, while keyset types use the package codec and seek slicer.

The implementation was traced through `utils/connections.py` (shared slice bounds and marker/probe
classification), `optimizer/nested_planner.py` (window planning and fallback identities),
`optimizer/selections.py` (selection gating), `keyset.py` (value cursor encode/decode), the
`DjangoListField` source-normalization/visibility boundaries, Strawberry's
`ConnectionExtension`, and live fakeshop relation/root connection tests. The scoped baseline
`27a87faa524340a5fcfce11c2f842c75d890f1ee` had no prior `connection.py` or connection test diff;
the final scoped diff is limited to the async-generator dispatch fix and its test.

## Verification

- `uv run pytest --no-cov tests/test_connection.py tests/test_relay_connection.py tests/test_keyset_connection.py`
  — 176 passed before edits.
- Scratch parity under `docs/review/temp-tests/connection/test_parity_scratch.py` compared
  optimizer-window and per-parent responses for valid `before`/`after` intervals, inverted
  intervals, first/last pages, empty pages, and the `last: 0` compatibility shape.
- Before the fix, an `async def` consumer resolver containing `yield` was classified as a sync
  resolver because `utils/typing.py::is_async_callable` recognizes coroutine functions but not
  async-generator functions. On `execute_sync`, the connection then passed an `async_generator`
  to Strawberry's sync slicing path, producing an internal assertion around
  `TypeError: 'async_generator' object is not subscriptable`.
- Strawberry's `ConnectionExtension` explicitly supports `AsyncIterable` resolver results; the
  async-generator shape is therefore a supported connection boundary, not an invalid consumer
  source.

## Improvements

### High

None.

### Medium

- **Async-generator consumer resolvers were misclassified.**
  - **Observation:** `_build_connection_resolver` only selected its async pipeline when
    `is_async_callable(resolver)` returned true. That predicate deliberately detects coroutine
    callables, not `async def` functions containing `yield`; such a resolver was routed through
    `_pipeline_sync`, and Strawberry's sync `ListConnection` path received an async generator.
  - **Evidence:** The pre-fix scratch schema used `async def resolver(...): yield row`; sync dispatch
    reached Strawberry's `TypeError: 'async_generator' object is not subscriptable`. Strawberry's
    locked `ConnectionExtension.resolve_async` accepts an `AsyncIterable` and awaits the returned
    connection coroutine.
  - **Impact:** Invalid `execute_sync` use leaked Strawberry's internal assertion/type error instead
    of the package's typed sync/async boundary. Strawberry's native async execution already
    consumes the `AsyncIterable`; the defect is the untyped sync misuse.
  - **Recommendation:** Keep the shared list-field coroutine predicate unchanged, but add a
    connection-local `inspect.isasyncgenfunction` check (including callable `__call__`) before the
    coroutine branch. In the sync-shaped wrapper, reject the source with `SyncMisuseError` when
    `in_async_context()` is false; preserve the `AsyncIterable` for Strawberry's native async
    connection slicer otherwise.
  - **Proof:** `tests/test_connection.py::test_connection_sync_async_generator_resolver_raises_sync_misuse`
    executes a real `DjangoConnectionField` through `execute_sync` and asserts the typed error.

### Low

None.

## Summary

Connection pagination, marker/probe empty-page handling, totals, keyset/offset cursor boundaries,
selection gating, optimizer fallback seams, ordering, and live relation usage matched their
existing contracts. One medium async-generator sync-boundary defect was confirmed and fixed; no
additional root-cause changes were justified.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/connection.py` to detect async-generator consumer
  callables without changing the shared `is_async_callable` contract, reject `execute_sync` with
  `SyncMisuseError`, and preserve the `AsyncIterable` for Strawberry's native async path.
- Added `tests/test_connection.py::test_connection_sync_async_generator_resolver_raises_sync_misuse`
  to pin the typed sync/async boundary.
- Scratch verification:
  `uv run pytest --no-cov docs/review/temp-tests/connection/test_parity_scratch.py` — 8 pagination
  parity cases passed after the fix.
- Focused post-edit verification:
  `uv run pytest --no-cov tests/test_connection.py tests/test_relay_connection.py tests/test_keyset_connection.py`
  — 177 passed. The revised boundary/oracle pair and parity scratch also passed.
- `uv run ruff format .` and `uv run ruff check --fix .` — passed; the formatter reported all files
  unchanged after the final edit and lint reported no errors.
- Rejected findings: optimizer-on/off parity remained byte-identical across the scratch cursor
  matrix; existing focused suites already covered invalid keyset cursors, total-count selection
  gating, empty/marker pages, source guards, and async queryset counting, so no further edits were
  warranted.
- Changelog: no entry requested; this is a bounded alpha connection-dispatch correction.


## Independent verification (Worker 2)

### Scope and pipeline trace

- The scoped baseline diff contains only `django_strawberry_framework/connection.py` and
  `tests/test_connection.py`: `_is_async_generator_callable`, the additional dispatch branch, and
  `test_connection_async_generator_resolver_dispatches_async_iterable`. `git diff --check` is clean;
  unrelated dirty and untracked files were left untouched.
- Sync/default connection resolvers enter `_pipeline_sync`; coroutine consumer resolvers enter
  `_pipeline_async` after one await; async-generator consumer resolvers enter the new async wrapper
  without awaiting the returned `AsyncIterable`. Both pipelines normalize Manager/QuerySet sources,
  apply visibility then filter/order then deterministic ordering and optimizer composition, while
  non-queryset iterables pass through the sidecar guard unchanged. `ConnectionExtension.resolve_async`
  then awaits an awaitable wrapper result and hands an `AsyncIterable` to Strawberry's async
  `ListConnection` slicer.
- The existing focused tests cover first/last exclusivity, resolver classification, sync misuse,
  visibility/filter/order composition, selection-gated totals and async `acount()`, optimizer
  cooperation, offset windows/markers/probes, keyset seek/cursor contracts, Relay page flags, and
  generated relation connections. Live fakeshop tests exercise the corresponding root/relation
  paths, including optimizer-on/off pagination and keyset pages.

### Verification runs

- `uv run pytest --no-cov tests/test_connection.py tests/test_relay_connection.py tests/test_keyset_connection.py`
  — 177 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py
  examples/fakeshop/test_query/test_library_api.py
  examples/fakeshop/test_query/test_keyset_api.py
  examples/fakeshop/test_query/test_single_parent_fastpath_api.py`
  — 349 passed.
- `uv run pytest --no-cov tests/test_connection.py::test_connection_async_generator_resolver_dispatches_async_iterable
  tests/test_connection.py::test_connection_resolver_async_dispatch
  tests/test_connection.py::test_connection_sync_resolver_returning_coroutine_raises_sync_misuse
  tests/test_connection.py::test_connection_resolver_composition_order`
  — 4 passed.
- The installed runtime is Strawberry `0.323.2`; its `ConnectionExtension.resolve_async` explicitly accepts
  an `AsyncIterable`, and `ListConnection.resolve_connection` asynchronously iterates it.

### Reproducible revision-needed finding

- The permanent regression test does NOT fail when the implementation is reverted. In a disposable
  test, monkeypatching only `django_strawberry_framework.connection._is_async_generator_callable`
  to return `False` (the exact baseline dispatch) and running the permanent test's
  `await schema.execute("{ items(first: 1) { edges { node { id } } } }")` still returns one edge with
  `result.errors is None`. This is because Strawberry's async connection path already consumes the
  returned `AsyncIterable`; the claimed pre-fix async-execution `TypeError` was not reproduced.
- The claimed `TypeError: 'async_generator' object is not subscriptable` IS reproducible only for
  the synchronous misuse shape: with that same classifier disabled, a disposable
  `schema.execute_sync("{ items(first: 1) { edges { node { id } } } }")` produces a GraphQL error
  whose original error is the TypeError from the sync list slicer. The permanent regression uses
  `schema.execute`, not `execute_sync`, so it does not witness this failure.
- The implemented classifier intentionally does not make async-generator resolvers valid for
  `execute_sync`; the sync execution remains async-only and errors (under the current runtime it
  can surface an event-loop/coroutine error because the wrapper is now async). Therefore this
  reproduction cannot justify the current test's claim that the new branch fixes an async-query
  TypeError.
- Required revision: add a failable oracle for the behavior the branch is intended to change (for
  example, assert that the async-generator field dispatches through `_pipeline_async` rather than
  `_pipeline_sync`, or reproduce the failure on the exact Strawberry/version path where async
  execution receives sync slicing). Until the permanent test fails on the baseline input, item 8
  remains unchecked and this artifact cannot be marked `verified`.

## Iterations

### Worker 1 revision after Worker 2 verification

- Reproduced the exact disabled-classifier baseline in
  `docs/review/temp-tests/connection/test_parity_scratch.py`: monkeypatching
  `_is_async_generator_callable` to return `False` and calling `schema.execute_sync(...)` reaches
  Strawberry's sync slicer, which raises the internal async-generator assertion/type path.
- Confirmed Worker 2's other point: `await schema.execute(...)` succeeds even with the classifier
  disabled because Strawberry natively consumes `AsyncIterable` sources. The finding no longer
  claims async execution itself fails.
- Revised `connection.py` so the async-generator branch remains sync-shaped for Strawberry's
  native async executor, but raises `SyncMisuseError` before slicing when `in_async_context()` is
  false. Replaced the non-failing async success test with the failable
  `test_connection_sync_async_generator_resolver_raises_sync_misuse`.
- Verification: the disabled-baseline scratch oracle and fixed permanent test both pass; the
  complete focused connection/Relay/keyset suites pass (`177 passed`); formatter and linter pass.
- Status is restored to `fix-implemented`; the plan checkbox remains for Worker 2.

## Independent verification (Worker 2)

### Contract and scope

- Re-read the complete `connection.py`, its source-normalization and visibility helpers, the
  Strawberry connection extension boundary, focused package tests, and live root/relation tests.
  The scoped baseline diff remains limited to the async-generator classifier/dispatch branch in
  `django_strawberry_framework/connection.py` and the typed sync-misuse regression in
  `tests/test_connection.py`; `git diff --check` is clean.
- `_build_connection_resolver` still sends default and synchronous consumer resolvers through
  `_pipeline_sync`, coroutine callables through `_pipeline_async`, and only async-generator
  callables through the new connection-local branch. That branch calls the resolver once,
  rejects `execute_sync` when `in_async_context()` is false with `SyncMisuseError`, and otherwise
  returns the untouched `AsyncIterable`; Strawberry's async `ConnectionExtension` then consumes
  it natively. QuerySet/Manager sources and ordinary iterable sources retain their existing
  visibility/filter/order/default-order/optimizer composition and pagination paths.

### Independent experiments

- `uv run pytest --no-cov tests/test_connection.py::test_connection_sync_async_generator_resolver_raises_sync_misuse`
  — 1 passed. The permanent test exercises a real `DjangoConnectionField` through
  `execute_sync` and observes the package's typed error.
- Disposable async execution check
  `docs/review/temp-tests/connection/test_async_generator_async_path.py` — 1 passed. A real
  `await schema.execute(...)` consumed the preserved async generator and returned one edge with
  no GraphQL errors.
- Disposable classifier-disabled async check
  `docs/review/temp-tests/connection/test_async_generator_async_path_disabled.py` — 1 passed.
  With `_is_async_generator_callable` forced to the pre-fix `False` result, Strawberry still
  consumed the `AsyncIterable` natively on `await schema.execute(...)`; this confirms native
  async support independently of the package branch.
- Disposable baseline oracle
  `docs/review/temp-tests/connection/test_async_generator_fixed_oracle_disabled.py`, with only
  `_is_async_generator_callable` monkeypatched to `False` — failed as intended. The copied
  permanent assertions received Strawberry's internal `AssertionError` (with the underlying
  `'async_generator' object is not subscriptable` sync-slicer path), not `SyncMisuseError`.
  This proves the permanent test fails against the exact pre-fix dispatch.
- `uv run pytest --no-cov tests/test_connection.py tests/test_relay_connection.py tests/test_keyset_connection.py`
  — 177 passed. This covers ordinary sync/async resolver paths, first/last guards, composition,
  totals and async counting, optimizer/window fallback, offset/keyset pagination, and rejected
  misuse findings.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py
  examples/fakeshop/test_query/test_library_api.py
  examples/fakeshop/test_query/test_keyset_api.py
  examples/fakeshop/test_query/test_single_parent_fastpath_api.py`
  — 349 passed. These live HTTP paths cover root/relation connections, composition, optimizer
  on/off parity, offset/keyset pages, and fast-path/fallback behavior.

### Disposition

- The earlier rejected claim that native async execution itself fails was independently
  confirmed false: Strawberry accepts and iterates the `AsyncIterable` without the classifier.
  The corrected finding is strictly the sync misuse boundary, where the package now fails typed
  before Strawberry's internal assertion/type path.
- No additional pagination, composition, optimizer, keyset, relation, or live-path regression
  was found. Item 8 is complete and verified.
