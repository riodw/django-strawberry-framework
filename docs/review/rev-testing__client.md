# Review: `django_strawberry_framework/testing/client.py`

Status: verified

## Understanding

`django_strawberry_framework/testing/client.py` provides the consumer-facing GraphQL test client and test case mixin family specified in spec-043:
1. `TestClient` and `AsyncTestClient`: Thin wrappers over Django's `django.test.Client` and `django.test.AsyncClient` that post GraphQL operations (JSON or multipart), decode the response via the engine's `_decode`, and return a typed `Response` dataclass.
2. `Response`: Subclasses `strawberry.test.client.Response` (`errors`, `data`, `extensions`) and attaches `response: Any = None` to carry the underlying raw `django.http.HttpResponse` for HTTP status, header, and cookie assertions without separate raw requests.
3. `GraphQLTestMixin`: A state-free mixin providing `self.query(...)`, `assertResponseNoErrors(resp, msg=None)`, and `assertResponseHasErrors(resp, msg=None)` delegating to `TestClient` over `self.client`.
4. `GraphQLTestCase` and `GraphQLTransactionTestCase`: Concrete unittest combinations over `django.test.TestCase` and `django.test.TransactionTestCase`.

### Key Architectural Invariants & Behavior:
- **Endpoint Precedence Ladder**: Highest to lowest: per-call `query(..., url=...)` > constructor `TestClient(path=...)` > class attribute `GraphQLTestMixin.GRAPHQL_URL` > `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]` setting > `"/graphql/"` default.
- **Multipart Upload Map & Placeholder Validation**: Shadows the Strawberry base's flawed folder heuristic with a uniform path-keyed file mapping (`map[key] = ["variables." + key]`). Validates dotted variable paths with canonical decimal list indexing and rejects collisions with reserved multipart envelope fields (`operations`, `map`) at the source.
- **Explicit `operation_name` Semantics**: `operation_name=None` omits the `operationName` field entirely, preventing multi-operation validation errors, while an explicit `operation_name=""` sends the empty string for server-side rejection.
- **Authentication Lifecycle**: `login(user)` context manager on `TestClient` (sync) and `AsyncTestClient` (async via `sync_to_async`) forces authentication on enter and guarantees logout on exit even when unhandled exceptions occur.
- **Pytest Collection Guard**: `__test__ = False` on `TestClient` and `AsyncTestClient` prevents pytest from attempting to collect the classes as test suites under `-W error`.

## Verification

1. **Static and Structural Audit**:
   - Reviewed all 541 lines of `django_strawberry_framework/testing/client.py` against spec-043 design decisions and upstream parity (`strawberry_django.test.client` and `graphene_django.utils.testing`).
   - Verified export surface in `django_strawberry_framework/testing/__init__.py` and absence of root exports in `django_strawberry_framework/__init__.py`.

2. **Existing Test Suite Audit**:
   - `tests/testing/test_client.py`: 31 DB-free unit tests covering endpoint precedence, multipart body construction, placeholder path validation, non-canonical list indices, reserved field collision guards, empty files payload JSON fallback, `Response.extensions`, `__test__ = False` guard, falsy client preservation, testing root exports, mixin delegation, and assertion helper failure directions.
   - `examples/fakeshop/test_query/test_client_api.py`: 11 live acceptance tests covering default `assert_no_errors=True` error raising, non-JSON 404 handling, `AsyncTestClient` queries, async login brackets, async nested multipart uploads, and `GraphQLTestCase` / `GraphQLTransactionTestCase` end-to-end execution.
   - `examples/fakeshop/test_query/test_products_api.py`: Additional live coverage for sync `login()` brackets and `operation_name` dispatch.

3. **Scratch Experiments**:
   - Created and executed `docs/review/temp-tests/client/test_scratch.py` to probe sync and async `login()` exception safety under simulated failures. Both passed cleanly.

4. **Permanent Tests & Test Suite Run**:
   - Added permanent DB-free unit tests in `tests/testing/test_client.py`:
     - `test_sync_login_bracket_guarantees_logout_on_exception`
     - `test_async_login_bracket_guarantees_logout_on_exception`
     - `test_assert_response_no_errors_fails_with_custom_msg`
     - `test_assert_response_has_errors_fails_with_custom_msg`
   - Focused test runs:
     - `uv run pytest tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py --no-cov`: 46 passed.
     - Coverage verification across client suites: 100% statement coverage (110/110 statements) on `django_strawberry_framework/testing/client.py`.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/testing/client.py` is a robust, well-engineered, and feature-complete testing client implementation. It fulfills all requirements of spec-043 with strict placeholder validation, proper endpoint hierarchy, and clean async/sync symmetry.

## Implementation (Worker 1)

- **changed files and why each was necessary:**
  - `tests/testing/test_client.py`: Added permanent unit tests pinning the sync and async `login()` context manager exception cleanup guarantees and custom message formatting on assertion helpers.
  - `django_strawberry_framework/testing/client.py`: 0 diff against cycle baseline HEAD (`12779c99`); existing production implementation is correct and complete.
- **permanent tests and the behavior they pin:**
  - `test_sync_login_bracket_guarantees_logout_on_exception`: Pins that `TestClient.login(user)` calls `force_login` on entry and reliably calls `logout` on exit even if an exception is raised in the context block.
  - `test_async_login_bracket_guarantees_logout_on_exception`: Pins that `AsyncTestClient.login(user)` calls `force_login` on entry and reliably calls `logout` on exit even if an exception is raised in the async context block.
  - `test_assert_response_no_errors_fails_with_custom_msg`: Pins that `GraphQLTestMixin.assertResponseNoErrors` includes custom `msg` in assertion failures.
  - `test_assert_response_has_errors_fails_with_custom_msg`: Pins that `GraphQLTestMixin.assertResponseHasErrors` includes custom `msg` in assertion failures.
- **scratch or focused verification and its result:**
  - Executed `docs/review/temp-tests/client/test_scratch.py` (2 passed).
  - Executed `uv run pytest tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py --no-cov` (46 passed).
  - Executed coverage run reaching 100% coverage on `testing/client.py`.
- **formatter and linter results:**
  - Executed `uv run ruff format .` and `uv run ruff check --fix .` (clean, 0 errors).
- **evidence for any rejected finding:**
  - No findings were rejected; implementation is robust and fully verified.
- **whether the completed behavior merits a changelog entry:**
  - No (test additions only; zero production code diff).

## Independent verification (Worker 2)

- **Target Scoped Diff & Baseline Check:**
  - `git diff 12779c99 -- django_strawberry_framework/testing/client.py`: confirmed clean (0 diff / zero-edit against baseline).
- **Behavioral Re-tracing & Invariant Verification:**
  - `TestClient` / `AsyncTestClient`: verified full symmetry between sync and async transport callers.
  - Endpoint Precedence Ladder: verified highest-to-lowest order (`query(..., url=...)` > `TestClient(path=...)` > `GraphQLTestMixin.GRAPHQL_URL` > `TESTING_ENDPOINT` > `"/graphql/"`). Verified that per-call `url=` does not mutate client state.
  - Multipart Upload Map & Placeholder Validation: verified dotted path validation, list index validation (canonical non-negative decimal string conversion), dict descent, scalar barrier errors, `None` placeholder verification, and reserved multipart envelope key guard (`operations`, `map`).
  - `operation_name` Semantics: verified that `operation_name=None` omits `operationName` entirely, while `operation_name=""` sends `""` for server-side rejection.
  - Authentication Lifecycle: verified sync and async `login(user)` context manager contracts reliably force login on enter and guarantee logout on exit even when unhandled exceptions occur in the block.
  - `Response` & Test Case Classes: verified typed `Response` dataclass with `response: Any = None` raw response ride-along, `GraphQLTestMixin` delegation to `self.client`, `GraphQLTestCase` / `GraphQLTransactionTestCase` class hierarchies, and `__test__ = False` collection guards.
- **Challenge Tests:**
  - Executed independent challenge test suite `docs/review/temp-tests/client/test_independent_scratch_client.py` (6 passed).
  - Executed focused permanent test suites: `uv run pytest tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py --no-cov` (46 passed).
- **Conclusion:**
  - All findings, contracts, and zero-edit status verified. No defects or regressions found.

