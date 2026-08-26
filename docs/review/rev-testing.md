# Review: `django_strawberry_framework/testing/`

Status: verified

## Understanding

`django_strawberry_framework/testing/` provides the consumer-facing test suite ergonomics and harness utilities across three distinct modules:

1. **GraphQL Test Client Family (`client.py`)**:
   - `TestClient` / `AsyncTestClient`: Thin wrappers over Django's `django.test.Client` / `django.test.AsyncClient` that post GraphQL operations (JSON or multipart), decode responses via the engine's `_decode`, and return typed `Response` objects carrying the raw `django.http.HttpResponse`.
   - `GraphQLTestMixin` / `GraphQLTestCase` / `GraphQLTransactionTestCase`: Graphene-Django-shaped unittest family delegating execution to `TestClient` over `self.client`, providing `assertResponseNoErrors` and `assertResponseHasErrors`.
   - Endpoint precedence ladder: per-call `query(..., url=...)` > constructor `TestClient(path=...)` > class attribute `GraphQLTestMixin.GRAPHQL_URL` > `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]` > `"/graphql/"` default.
   - Uniform multipart upload mapping (`map[key] = ["variables." + key]`), strict dotted variable path validation, decimal list index validation, and envelope collision guards against reserved fields (`operations`, `map`).
   - `__test__ = False` collection guards on client classes preventing spurious pytest test suite collection.
   - Symmetric sync and async `login(user)` context managers guaranteeing `logout()` execution via `finally` blocks upon block exit or exception.

2. **Connection Wrapping & Trac #37064 Defense (`_wrap.py`)**:
   - `safe_wrap_connection_method(connection, method_name, wrapper)`: Wrap-time defense-in-depth utility for consumer test instrumentation swapping database connection methods (e.g. `cursor`, `chunked_cursor`, `create_cursor`) between `setUpClass` and `tearDownClass`.
   - Coordinates with `django_strawberry_framework._django_patches._is_database_failure` to decline wrapping when Django's `_DatabaseFailure` wrapper is already in place, preventing `tearDownClass` unwrap crashes.
   - Enforces callable validation up front to catch call-site typos early.

3. **Relay GlobalID Testing Helpers (`relay.py`)**:
   - `global_id_for(type_cls, id)`: Mints strategy-aware base64-encoded `relay.GlobalID` strings for finalized Relay-Node `DjangoType` classes (`"model"`, `"type"`, `"type+model"`). Enforces strict registration, finalization, and strategy gates.
   - `decode_global_id(gid)`: Public re-export resolving encoded GlobalIDs back to `(target_type, node_id)` pairs, preserving the secondary-emitter model label decode asymmetry.

4. **Public Export Boundary & Import Isolation (`__init__.py`)**:
   - Re-exports `TestClient`, `AsyncTestClient`, `Response`, `GraphQLTestMixin`, `GraphQLTestCase`, `GraphQLTransactionTestCase`, and `safe_wrap_connection_method`.
   - Deliberately does NOT re-export `relay.py` helpers (`global_id_for`, `decode_global_id`) at the `testing` package root, keeping `import django_strawberry_framework.testing` lightweight and isolating `types` machinery imports to suites that explicitly use `django_strawberry_framework.testing.relay`.
   - Testing symbols are completely excluded from the top-level `django_strawberry_framework` namespace, enforcing clean separation between runtime application code and test harnesses.

## Verification

1. Examined all individual file review artifacts (`rev-testing___wrap.md`, `rev-testing__client.md`, `rev-testing__relay.md`), confirming zero outstanding findings and full verification by Worker 2.
2. Verified holistic cross-module contracts and whole-subpackage behavior:
   - Export surface consistency between `testing/__init__.py` and `testing/relay.py`.
   - Import isolation: root package does not export testing utilities, and `testing/__init__.py` does not eagerly load `relay.py` / `types` machinery.
   - Pytest collection guard (`__test__ = False`) on `TestClient` and `AsyncTestClient`.
   - Cross-subsystem integration between `_wrap.py` and `_django_patches.py`.
3. Focused permanent test suite execution:
   - `uv run pytest tests/testing/ --no-cov` -> 58 passed.
   - `uv run pytest examples/fakeshop/test_query/test_client_api.py --no-cov` -> 11 passed.
4. Holistic scratch test execution:
   - `docs/review/temp-tests/testing/test_scratch.py` -> 2 passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The `django_strawberry_framework/testing/` subsystem provides a clean, well-isolated, and comprehensive test suite toolkit. Module boundaries are disciplined, public exports strictly match design specifications, import costs are minimized through selective submodule exposure, and sync/async symmetry is rigorously maintained.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/testing/test_client.py`, `tests/testing/test_relay.py`, `tests/testing/test_wrap.py`, `examples/fakeshop/test_query/test_client_api.py`) covers all subpackage behavior (71 tests total).
- Scratch verification:
  - `docs/review/temp-tests/testing/test_scratch.py` passed (2/2 tests) verifying public exports, submodule isolation, and pytest collection guards.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/testing/ tests/testing/` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/testing/ tests/testing/` passed (8 files clean).
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

### Re-traced behaviors and contracts

1. **Scoped Diff Baseline**: Confirmed that `git diff HEAD -- django_strawberry_framework/testing/` is completely empty (zero-edit review cycle).
2. **Endpoint Precedence Ladder & Dispatch Hierarchy**:
   - Per-call `url` in `TestClient.query` and `AsyncTestClient.query` overrides all else for that single invocation without mutating instance attributes.
   - Constructor `path` overrides settings and defaults.
   - `GraphQLTestMixin.GRAPHQL_URL` overrides settings and defaults.
   - Fallback hierarchy checks `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]` before defaulting to `"/graphql/"`.
3. **Uniform Multipart Upload Protocol & Strict Validation**:
   - Uniform mapping rule: `map[key] = ["variables." + key]`.
   - Dotted variable paths descend into nested dictionaries and canonical decimal list indices.
   - Strict placeholder validations ensure every file key targets a `None` placeholder.
   - Reserved multipart keys (`"operations"`, `"map"`) are proactively rejected with `AssertionError`.
4. **Operation Name & Error Assertions**:
   - `operation_name=None` omits the `operationName` field in the payload to avoid schema multi-operation validation errors.
   - Explicit `operation_name=""` sends `{"operationName": ""}` as a provided malformed string for server-side GraphQL validation.
   - Explicit `assert_no_errors=True` in `TestClient` / `AsyncTestClient` raises `AssertionError` with the list of errors on failure, surviving `python -O`.
   - `GraphQLTestMixin.query` defaults to `assert_no_errors=False` for graphene-compatible test flows.
5. **Sync & Async `login(user)` Context Managers**:
   - Confirmed `force_login` on entry and guaranteed `logout` in `finally` blocks under both sync and async execution paths.
6. **Trac #37064 Defense-in-Depth (`safe_wrap_connection_method`)**:
   - Early `TypeError` validation on non-callable wrappers.
   - Wrap-time check coordinates with `_is_database_failure` to decline wrapping when Django's `_DatabaseFailure` wrapper is already in place.
7. **Relay GlobalID Test Helpers (`relay.py`)**:
   - `global_id_for` strictly enforces `DjangoType` subclassing, active registration, finalization, Relay-Node stamping, and string strategy compliance (`"model"`, `"type"`, `"type+model"`), while rejecting unfinalized types and `callable`/`custom` strategies.
   - `decode_global_id` cleanly re-exports the engine-level decoder, preserving the secondary-emitter model label decode asymmetry.
8. **Export Boundary & Import Isolation**:
   - Root `testing/__init__.py` re-exports the client suite, `Response`, and `safe_wrap_connection_method`.
   - `relay.py` helpers are isolated to `django_strawberry_framework.testing.relay` and excluded from `testing/__init__.__all__` to avoid eager loading of `types` machinery.
   - Top-level `django_strawberry_framework` namespace strictly excludes all testing symbols.
   - `TestClient` and `AsyncTestClient` define `__test__ = False` to prevent spurious pytest collection.

### Test Execution

- Executed targeted permanent and scratch test suites:
  - `uv run pytest tests/testing/ examples/fakeshop/test_query/test_client_api.py docs/review/temp-tests/testing/test_scratch.py --no-cov` -> 71 passed.

