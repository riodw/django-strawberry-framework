# Review: `django_strawberry_framework/list_field.py`

Status: verified

## Understanding

`DjangoListField` is a factory that validates an own-class registered `DjangoType`, captures its
model target, and returns a Strawberry field whose resolver is driven by the consumer's class
annotation. The default resolver starts from `model._default_manager.all()`, applies the target
visibility hook through the shared sync/async sealed-queryset boundary, and applies the raw-list
resource bound after visibility. A custom resolver is classified at construction as sync or async;
`Manager` / `QuerySet` results are normalized and visibility-scoped, while deliberate plain
iterables bypass queryset visibility but remain row-bounded.

`max_rows` narrows the request's `ResourcePolicy.max_list_rows`; `trusted_max_rows=True` is the
explicit widening declaration. The field does not add filtering or ordering arguments: unlike
`DjangoConnectionField`, a raw list has no cursor contract and does not promise deterministic
ordering. The optimizer's resolve hook is root-gated; when a root list resolver returns a queryset,
the optimizer plans selected relations, while generated relation-list resolvers use their own
bounded raw-list path. Strawberry reads outer nullability from the consumer annotation
(`list[T]` versus `list[T] | None`), and its async executor accepts `AsyncIterable` list results.

Representative live usage in `examples/fakeshop/apps/library/schema.py` and
`examples/fakeshop/test_query/test_library_api.py` covers the default list resolver, consumer
Manager coercion, optimizer behavior, nullable outer annotations, and nested relation output.

The assigned baseline had no `list_field.py` diff. The final scoped implementation expands the
shared resource-policy collection boundary because the list field's async path must cap async-only
iterables before handing them to GraphQL.

## Verification

- Read the complete target, the list-field specification, queryset visibility/sealing helpers,
  resource policy, optimizer root gate, relation resolvers, type finalization, package tests, and
  live fakeshop list-field usage.
- Scratch reproduction in `docs/review/temp-tests/list_field/async_iterable_cap.py`: before the
  fix, `bounded_rows(async_generator, ..., 2)` raised `TypeError: 'async_generator' object is not
  iterable` after its slicing fallback.
- Strawberry's installed graphql-core `ExecutionContext.complete_list_value` accepts
  `AsyncIterable` results and materializes them asynchronously, confirming the source shape is
  valid and the failure occurred in the package's pre-completion row-bound step.
- `uv run pytest tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_async_iterable_is_bounded --no-cov`
  — 1 passed.
- `uv run pytest tests/test_list_field.py --no-cov` — 44 passed before artifact creation.

## Improvements

### High

None.

### Medium

- **Async-only iterable custom resolvers were rejected by the mandatory row cap.**
  - **Observation:** Async custom resolvers returning a valid `AsyncIterable` reached
    `bounded_rows`, whose synchronous `result[:limit]` / `islice` fallback cannot consume an async
    generator. Direct `async def ...: yield ...` resolvers were additionally misclassified by
    `is_async_callable`, which intentionally recognizes coroutine functions but not async-generator
    functions.
  - **Evidence:** The preserved scratch reproduction raised `TypeError` before graphql-core
    completion; graphql-core's list completion explicitly supports `AsyncIterable`. The direct
    async-generator shape followed the same failing synchronous wrapper.
  - **Impact:** A valid async `DjangoListField` resolver failed instead of returning data, and
    bypassing the bound would have violated the raw-list resource contract. Sync misuse also
    surfaced as an internal slicing/type error instead of the package's typed boundary.
  - **Recommendation:** Keep lazy synchronous iterables (including Django `QuerySet`) on
    `bounded_rows`, add an async-aware policy helper that consumes only the effective prefix of
    async-only iterables and closes the iterator, and dispatch async-generator callables through a
    sync-shaped guard plus async capped wrapper. Detect a plain sync resolver's async-only result
    at runtime, and route all async results through the helper after visibility processing.
  - **Proof:** `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_async_iterable_is_bounded`,
    `tests/test_list_field.py::test_djangolistfield_async_generator_resolver_is_bounded`,
    `tests/test_list_field.py::test_djangolistfield_partial_async_generator_resolver_is_bounded`,
    `tests/test_list_field.py::test_djangolistfield_sync_resolver_returning_async_iterable_is_bounded`, and
    `tests/test_list_field.py::test_djangolistfield_sync_async_generator_resolver_raises_sync_misuse`
    execute real GraphQL fields and pin direct/partial async-generator caps plus the typed
    sync/async boundary.

### Low

None.

## Summary

The factory's validation, target/model inference, default and custom resolver composition,
visibility sealing, row caps, root optimizer integration, lack of list filter/order arguments,
sync/async dispatch, iterable pass-through, annotation-driven nullability, and live fakeshop usage
match their contracts. One medium correctness defect spanning async-only iterable bounds and
async-generator dispatch was confirmed and fixed; no additional root-cause changes were justified.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/resource_policy.py` to add `bounded_rows_async`, preserving
  SQL slicing for synchronous QuerySets while safely consuming and closing async-only iterables
  within the effective raw-list bound.
- Changed `django_strawberry_framework/list_field.py` so the async default/custom-resolver branches
  await the async-aware bound after visibility processing, async-generator callables use the same
  native async path with a typed sync-execution guard, and sync resolvers that return async-only
  iterables are detected at runtime.
- Added `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_async_iterable_is_bounded`,
  `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_async_iterable_can_exhaust_before_bound`,
  `tests/test_list_field.py::test_djangolistfield_async_generator_resolver_is_bounded`,
  `tests/test_list_field.py::test_djangolistfield_partial_async_generator_resolver_is_bounded`,
  `tests/test_list_field.py::test_djangolistfield_sync_resolver_returning_async_iterable_is_bounded`,
  and
  `tests/test_list_field.py::test_djangolistfield_sync_async_generator_resolver_raises_sync_misuse`
  to pin async-generator GraphQL completion, early iterator closing, natural exhaustion, the
  `max_rows` cap, and the sync/async misuse boundary.
- Scratch verification: the pre-fix reproduction failed with the expected `TypeError`; the focused
  permanent regression passed after the fix.
- Focused verification: `uv run pytest tests/test_list_field.py --no-cov` — 44 passed.
- `uv run ruff format .` and `uv run ruff check --fix .` — passed. `git diff --check` is clean.
- Rejected findings: no filtering/order composition belongs on this non-Relay list surface; list
  ordering is intentionally database-dependent, and outer nullability is intentionally owned by
  the consumer annotation. Existing package/live tests cover those contracts.
- Changelog: no entry requested; this is a bounded alpha async-iterable correctness correction.

## Independent verification (Worker 2)

- Re-read the complete target and expanded ownership: `django_strawberry_framework/list_field.py::DjangoListField`,
  `django_strawberry_framework/resource_policy.py::bounded_rows_async`, the shared visibility
  runners in `django_strawberry_framework/utils/querysets.py`, generated relation resolvers,
  `DjangoOptimizerExtension.resolve`, the list-field specification, package/live tests, and the
  fakeshop library schema.
- Reproduced the pre-fix failure with
  `uv run python docs/review/temp-tests/list_field/async_iterable_cap.py`: the old
  `bounded_rows` slicing and `islice` fallback both raise `TypeError` for an async-only
  generator before graphql-core completion.
- Independently exercised `bounded_rows_async` with an async-only iterator: it consumed exactly
  the declared prefix, awaited `aclose()` after an early cap, left a naturally exhausted iterator
  untouched, and kept a dual-protocol iterable on the synchronous slicing path. A real GraphQL
  schema also returned one row for a partial-wrapped async-generator callable instance with
  `max_rows=1`.
- Verified queryset laziness directly: `bounded_rows` left `_result_cache` unset and applied
  `query.high_mark=2`; a real GraphQL field with request `max_list_rows=1` returned one row when
  untrusted `max_rows=3` was declared and three rows with `trusted_max_rows=True`.
- Focused evidence:
  - `uv run pytest tests/test_list_field.py --no-cov` — 43 passed.
  - `uv run pytest tests/test_list_field.py -k 'async_iterable or async_generator' --no-cov` — 5 passed.
  - `uv run pytest tests/test_list_field.py -k 'async_get_queryset or default_resolver_works_under_sync_and_async or root_position_is_optimized or hostile_hook or cascade' --no-cov` — 6 passed.
  - `uv run pytest tests/test_resource_policy.py -k 'bounded_rows or effective_bound' --no-cov` — 4 passed.
  - `uv run pytest examples/fakeshop/test_query/test_library_api.py -k djangolistfield --no-cov` — 3 passed over live `/graphql/`.
  - `git diff --check 0884f9385503ce03c456a4b383b47653c28fcec6 -- django_strawberry_framework/list_field.py django_strawberry_framework/resource_policy.py tests/test_list_field.py docs/review/rev-list_field.md docs/review/review-0_0_14.md` — clean.
- The async-only iterable bound, closure, sync/async dispatch, visibility sealing, resource
  narrowing/trusted widening, queryset laziness, root optimizer planning, relation output, and
  live fakeshop behavior are complete. No additional finding remains.

## Iterations

- Rechecked the concurrent follow-up that routes async-only iterables returned by an otherwise
  synchronous resolver through the async bounded path and centralizes the sync-execution guard.
  Direct async generators, partial-wrapped callable instances, and async-only iterables returned
  from sync callables all remain capped and typed at the boundary.
- Latest focused evidence: `uv run pytest tests/test_list_field.py --no-cov` — 44 passed;
  `uv run pytest tests/test_list_field.py -k 'async_iterable or async_generator' --no-cov` — 6
  passed; `uv run pytest examples/fakeshop/test_query/test_library_api.py -k djangolistfield
  --no-cov` — 3 passed. No new finding.

## Iterations

### Worker 1 revision after Worker 2 verification

- Re-read the shared `django_strawberry_framework/list_field.py` after Worker 2 reported a transient
  duplicate-wrapper indentation problem during concurrent follow-up edits. The current source has
  one coherent sync wrapper, one coroutine wrapper, one async-generator wrapper, and one runtime
  async-iterable branch; `python -m py_compile django_strawberry_framework/list_field.py` passes.
- Completed the direct async-generator revision: async-generator callables (including partial
  callable instances) now use the native async cap, while a sync execution raises the typed
  `SyncMisuseError`. A plain sync resolver returning an async-only iterable is detected at runtime
  and follows the same cap/guard path.
- Added and verified
  `tests/test_list_field.py::test_djangolistfield_sync_resolver_returning_async_iterable_is_bounded`;
  the complete focused suite now passes with 44 tests.
- `uv run pytest tests/test_list_field.py --no-cov` — 44 passed; targeted direct/partial/runtime
  async-iterable and sync-misuse cases also passed.
- `uv run ruff format .` and `uv run ruff check --fix .` — passed; `git diff --check` is clean.
- Status remains `fix-implemented`; the plan checkbox remains for Worker 2.

## Independent verification (Worker 2, pass 2)

- Re-read the current parseable implementations and retraced every affected route: default
  queryset/lazy resolver, sync and native async consumer resolvers, direct async-generator
  functions, callable instances, partial-wrapped async functions and generators, and a plain sync
  resolver returning an async-only iterable. `list_field.py` has exactly one coherent wrapper for
  each route (sync, coroutine, async-generator) plus the one runtime async-iterable branch;
  `python -m py_compile django_strawberry_framework/list_field.py django_strawberry_framework/resource_policy.py`
  and an AST parse both pass.
- Verified the shared visibility boundary remains before every row cap: queryset and Manager
  results are normalized/sealed through `post_process_queryset_result_sync` /
  `_async`, while deliberate plain iterables bypass visibility but still enter the appropriate
  synchronous or asynchronous bound. Native async execution returns capped rows, and sync
  execution of direct async-generator resolvers raises the typed `SyncMisuseError`; callable
  instance and partial-wrapped generator paths are covered by the same behavior.
- Directly exercised `bounded_rows_async` with tracked async iterators: an early cap consumed only
  the effective prefix and awaited `aclose()`, natural exhaustion returned without closing, and a
  dual-protocol iterable stayed on the synchronous slicing path. A direct queryset probe kept
  `_result_cache` unset and applied the SQL `high_mark`; untrusted declarations narrowed to the
  request `max_list_rows`, while `trusted=True` widened to the explicit field declaration.
- Focused evidence on the current checkout:
  `python -m py_compile django_strawberry_framework/list_field.py django_strawberry_framework/resource_policy.py`;
  `uv run pytest tests/test_list_field.py --no-cov` — 44 passed;
  `uv run pytest tests/test_resource_policy.py -k 'bounded_rows or effective_bound' --no-cov` — 4
  passed; and
  `uv run pytest examples/fakeshop/test_query/test_library_api.py -k djangolistfield --no-cov`
  — 3 live `/graphql/` tests passed. The preserved scratch probe still demonstrates the old
  synchronous helper's async-generator `TypeError`, while the repaired field routes around it.
- Failability proof against a disposable archive of baseline
  `0884f9385503ce03c456a4b383b47653c28fcec6`: running the copied current regression tests with
  imports forced from that archive made all six async iterable/generator cases fail at the old
  `bounded_rows` `islice` fallback with `TypeError: 'async_generator' object is not iterable`;
  the same six current tests pass above. The scoped `git diff --check` is clean, and no source,
  permanent test, or changelog file was edited during this pass.
- No additional finding remains. Status is `verified`; item 13 remains checked in
  `docs/review/review-0_0_14.md`.
