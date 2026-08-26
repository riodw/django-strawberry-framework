# Review: `django_strawberry_framework/utils/typing.py`

Status: verified

## Understanding

`django_strawberry_framework/utils/typing.py` provides central, cycle-safe type unwrapping helpers, Strawberry-private schema/config accessors, and partial/staticmethod-aware async callable detection across the framework:

1. **Schema & Config Digs (`strawberry_schema_from_schema`, `strawberry_schema_from_info`, `schema_config_from_info`)**:
   - Centralizes the brittle private `_strawberry_schema` and `.config` attribute accessors across resolve-time Strawberry `Info` (where `info.schema` is Strawberry's `Schema` or stubs) and plan-time graphql-core `info` (where `info.schema` is a bare `GraphQLSchema` wrapping `_strawberry_schema`).
   - Safely returns `None` when intermediate schema attributes are missing or stubs lack configuration.

2. **Bounded Type Peeling (`unwrap_graphql_type`, `unwrap_container_type`, `unwrap_return_type`, `_MAX_TYPE_WRAPPER_DEPTH = 64`)**:
   - `unwrap_graphql_type`: Recursively peels `of_type` wrappers (`GraphQLNonNull`, `GraphQLList`, or Strawberry wrappers) down to the leaf GraphQL/Python type.
   - `unwrap_container_type`: Recursively peels Strawberry `StrawberryContainer` instances (`StrawberryList`, `StrawberryOptional`) without descending into leaf classes that happen to define an `of_type` field.
   - `unwrap_return_type`: Peels exactly one layer of list / `StrawberryList` wrapper (`of_type`, `list[T]`, `typing.List[T]`, `list`, `typing.List`), preserving nested inner wrappers for callers.
   - All recursive loops enforce a NASA Power-of-Ten Rule 2 upper bound (`_MAX_TYPE_WRAPPER_DEPTH = 64`), raising `RuntimeError` immediately if a cyclic or corrupted wrapper chain is encountered.

3. **Callable Inspection & Async Predicate (`_callable_inspection_target`, `is_async_callable`)**:
   - `_callable_inspection_target`: Bounded loop peeling `functools.partial` and `staticmethod` descriptor chains so wrapper layers are unwrapped uniformly.
   - `is_async_callable`: Detects coroutine-returning callables across `async def` functions, bound methods, `functools.partial` wrappers, `staticmethod` descriptors, and callable instances with `async def __call__`. Deliberately treats `async def` generator functions as `False` (classified by value at resolve time).

## Verification

1. **Caller Tracing & Invariance**:
   - Traced callers across `connection.py`, `list_field.py`, `mutations/sets.py`, `optimizer/extension.py`, `optimizer/nested_planner.py`, `optimizer/selections.py`, `optimizer/walker.py`, `types/base.py`, and `utils/connections.py`.
   - Verified that all callers rely on centralized `schema_config_from_info`, `unwrap_graphql_type`, `unwrap_container_type`, and `is_async_callable`.
2. **Scratch Probing**:
   - Executed scratch test `docs/review/temp-tests/utils_typing/test_scratch.py` probing edge cases across various types (`None`, `int`, `tuple`, `Union`, `list`, sync/async functions, sync/async generators, class objects vs instances).
   - Discovered that `is_async_callable(AsyncCallableClass)` previously returned `True` for the class object itself because `getattr(AsyncCallableClass, "__call__", None)` retrieved the unbound async method on the class dict, even though calling a class constructor is synchronous.
3. **Existing and Permanent Test Suite**:
   - Evaluated `tests/utils/test_typing.py` (38 test cases) covering one-layer unwrapping, bare list sentinels, deep GraphQL type stacks, cyclic chain detection, container isolation, schema digs, and async callable wrapper shapes.
   - Added permanent parameterized tests pinning class vs instance behavior and `__all__` export verification.
   - Ran `uv run pytest tests/utils/test_typing.py docs/review/temp-tests/utils_typing/test_scratch.py --no-cov` (40 passed in 1.90s).
   - Ran related tests `uv run pytest tests/test_list_field.py tests/test_relay_connection.py tests/types/test_resolvers.py --no-cov` (184 passed in 7.26s).

## Improvements

### High

None.

### Medium

1. **`is_async_callable` misclassified classes with async `__call__` methods as async callables**
   - **Observation:** `is_async_callable(value)` returned `True` when `value` was a class object whose instances implement `async def __call__(self, ...)`.
   - **Evidence:** `getattr(target, "__call__", None)` when `target` is a `type` inspects the unbound method on the class definition, which is an `async def` coroutine function. But calling a class `target(...)` invokes `type.__call__` to construct and initialize an instance synchronously, returning an instance, not a coroutine.
   - **Impact:** Callers (such as `connection.py`, `list_field.py`, or `types/base.py`) passing a class constructor or callable factory would incorrectly treat invocation as yielding a coroutine and attempt to `await` the resulting instance, raising `TypeError: object ... can't be used in 'await' expression` at runtime, or incorrectly fail sync-callable validation in `DjangoType` GlobalID configuration.
   - **Recommendation:** In `is_async_callable`, check `if isinstance(target, type): return False` before inspecting `getattr(target, "__call__", None)`. An instance of `type` is constructed synchronously; only an *instance* of that class (`not isinstance(target, type)`) invokes the instance `__call__` method when called.
   - **Proof:** `tests/utils/test_typing.py::test_is_async_callable_sees_through_supported_wrappers` pins `is_async_callable(_AsyncCallable) is False` and `is_async_callable(functools.partial(_AsyncCallable)) is False`, while `is_async_callable(_AsyncCallable()) is True` and `is_async_callable(functools.partial(_AsyncCallable())) is True`.

### Low

1. **`django_strawberry_framework/utils/typing.py` lacked explicit `__all__` export tuple**
   - **Observation:** Unlike sibling utility modules (`strings.py`, `relations.py`), `utils/typing.py` did not define `__all__` to explicitly declare its public export surface.
   - **Evidence:** Inspection of `django_strawberry_framework/utils/typing.py`.
   - **Impact:** Ambiguous module export surface for wildcard imports and static analysis tooling.
   - **Recommendation:** Define `__all__` explicitly in `django_strawberry_framework/utils/typing.py` listing the 7 public symbols (`is_async_callable`, `schema_config_from_info`, `strawberry_schema_from_info`, `strawberry_schema_from_schema`, `unwrap_container_type`, `unwrap_graphql_type`, `unwrap_return_type`).
   - **Proof:** `tests/utils/test_typing.py::test_typing_exports_all` verifies `__all__`.

## Summary

`django_strawberry_framework/utils/typing.py` centralizes schema digs, GraphQL/Strawberry type unwrapping loops bounded by NASA Power-of-Ten Rule 2, and the partial/staticmethod-aware async callable predicate. We fixed a class-vs-instance classification defect in `is_async_callable` and declared the public export surface via `__all__`.

## Implementation (Worker 1)

- **Changed files:**
  - `django_strawberry_framework/utils/typing.py`: Added `__all__` export tuple; short-circuited `is_async_callable` to `False` when `target` is an instance of `type`.
  - `tests/utils/test_typing.py`: Added `test_typing_exports_all` and parameterized test cases for `_AsyncCallable` and `_SyncCallable` class constructors and partials.
- **Permanent tests and pinned behavior:**
  - `tests/utils/test_typing.py::test_is_async_callable_sees_through_supported_wrappers`: Pins that class objects and partials around class objects are recognized as sync callables (`False`), while instances of classes with async `__call__` are recognized as async callables (`True`).
  - `tests/utils/test_typing.py::test_typing_exports_all`: Pins the module's public `__all__` export contract.
- **Scratch or focused verification:**
  - `docs/review/temp-tests/utils_typing/test_scratch.py`: Probed edge cases across various types (`None`, `int`, `tuple`, `Union`, `list`, sync/async functions, async generators, class objects vs instances).
  - `uv run pytest tests/utils/test_typing.py docs/review/temp-tests/utils_typing/test_scratch.py --no-cov` (40 passed in 1.90s).
  - `uv run pytest tests/test_list_field.py tests/test_relay_connection.py tests/types/test_resolvers.py --no-cov` (184 passed in 7.26s).
- **Formatter and linter results:**
  - `uv run ruff format .` (432 files left unchanged).
  - `uv run ruff check --fix .` (All checks passed).
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — internal bugfix and edge-case hardening for callable shape inspection.

## Independent verification (Worker 2)

- **Behaviors and invariants verified:**
  - **Schema & config accessors:** Verified `strawberry_schema_from_schema`, `strawberry_schema_from_info`, and `schema_config_from_info` safely extract `_strawberry_schema` and `.config` across resolve-time Strawberry `Info` (and test stubs) and plan-time graphql-core `GraphQLSchema`, falling back cleanly to `None` without raising attribute errors.
  - **Bounded type unwrapping:** Verified `unwrap_graphql_type`, `unwrap_container_type`, and `unwrap_return_type` correctly peel wrapper layers (`GraphQLNonNull`, `GraphQLList`, Strawberry container wrappers, native `list[T]`, and `List[T]`) while stopping recursion at leaf nodes and enforcing the NASA Power-of-Ten Rule 2 upper limit (`_MAX_TYPE_WRAPPER_DEPTH = 64`) with `RuntimeError` on cyclic/corrupt chains.
  - **Callable inspection & async predicate:** Verified `_callable_inspection_target` and `is_async_callable` correctly peel `functools.partial` and `staticmethod` chains. Verified that class constructors (`isinstance(target, type)`) return `False` even if the class defines an `async def __call__`, callable instances with `async def __call__` return `True`, and `async def` generator functions return `False` (as intended for value-level resolve-time classification).
  - **Public export contract:** Verified `__all__` explicitly exports all 7 public functions.
- **Scoped diff confirmation:** Verified `git diff 12779c99 -- django_strawberry_framework/utils/typing.py` contains only the intended additions of `__all__` and the `isinstance(target, type)` class constructor short-circuit in `is_async_callable`.
- **Test execution & challenges:**
  - Ran `uv run pytest tests/utils/test_typing.py docs/review/temp-tests/utils_typing/test_scratch.py --no-cov` (40 passed in 1.75s).
  - Ran dependent subsystem tests `uv run pytest tests/test_list_field.py tests/test_connection.py tests/test_keyset_connection.py tests/types/test_base.py tests/optimizer/test_nested_fetch.py tests/optimizer/test_plans.py tests/optimizer/test_selections.py tests/mutations/test_sets.py --no-cov` (581 passed in 9.47s).
- **Outcome:** Verified. All findings disposed, contracts preserved, and test suite green.
