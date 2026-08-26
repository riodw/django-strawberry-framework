# Review: `django_strawberry_framework/resource_policy.py`

Status: verified

## Understanding

`django_strawberry_framework/resource_policy.py` implements the one immutable execution resource budget for a GraphQL request (`ResourcePolicy`), along with schema-construction policy resolution (`resolve_resource_policy`), request context threading utilities (`stash_resource_policy`, `clear_resource_context`, `policy_from_info`), cooperative wall-clock deadline enforcement (`check_deadline`), collection row bounding (`bounded_rows`, `bounded_rows_async`), and field-level bound helpers (`validate_collection_bound`, `effective_bound`).

It owns:
1. **Immutable Resource Budget (`ResourcePolicy`):**
   - A frozen dataclass defining 20 execution bounds covering:
     - Document budget: `max_document_tokens`, `max_depth`, `max_selections`, `max_aliases`, `max_collection_cost`.
     - Value budget: `max_input_nodes`, `max_container_width`, `max_value_depth`, `max_membership_items`, `max_node_ids`, `max_relation_ids_per_mutation`, `max_relation_ids_total`, `max_nested_rows`, `max_upload_count`, `max_upload_file_bytes`, `max_upload_total_bytes`, `max_scalar_bytes`.
     - Collection bounds: `max_page_size`, `max_list_rows`.
     - Execution deadline: `execution_deadline_seconds` (optional float/int).
   - `__post_init__` validates every bound at construction: integers must be positive (rejecting booleans and values < 1); `execution_deadline_seconds` must be `None` or a finite positive number.
   - `narrowed(**overrides)` creates a tightened copy, strictly disallowing any bound widening or restoring `None` deadline.
2. **Schema Resolution and Precedence Ladder:**
   - `resolve_resource_policy(explicit)` normalizes the deployment's policy once at schema initialization (`DjangoSchema`).
   - Precedence: explicit `ResourcePolicy` instance > explicit mapping > `DJANGO_STRAWBERRY_FRAMEWORK["RESOURCE_POLICY"]` setting > `DEFAULT_RESOURCE_POLICY`.
   - Validates mapping keys against known `ResourcePolicy` fields, rejecting unrecognized bounds with a clear diagnostic.
3. **Fail-Closed Context Threading:**
   - `stash_resource_policy(context, policy)` writes `DST_RESOURCE_POLICY` and computes monotonic `DST_RESOURCE_DEADLINE`.
   - `clear_resource_context(context)` clears both keys to prevent deadline leakage across reused contexts.
   - `policy_from_info(info)` extracts the stashed policy or safely falls back to `DEFAULT_RESOURCE_POLICY` on missing or unwritable contexts.
4. **Cooperative Wall-Clock Deadline (`check_deadline`):**
   - Checked at collection pre-query seams before database execution (`bounded_rows`, `connection.py::DjangoConnection`, `relay.py::DjangoNodeField`/`DjangoNodesField`, `mutations/resolvers.py::run_write_pipeline_sync`).
   - Raises `ResourceLimitExceeded` reporting configured seconds (not internal clock timestamps) when the deadline has elapsed.
5. **Collection Row Bounding (`bounded_rows`, `bounded_rows_async`):**
   - Applies the tighter of `ResourcePolicy.max_list_rows` and field `declared` max rows (unless `trusted=True`).
   - Synchronous `bounded_rows` slices `QuerySet` (generating SQL `LIMIT`) or falls back to `islice` on non-subscriptable iterables.
   - `bounded_rows_async` preserves synchronous iterable slicing for lazy querysets while consuming and early-closing pure async iterators, cleanly chaining cleanup errors into `__notes__` when primary iteration fails.
6. **Wire-Visible Error Identity (`ResourceLimitExceeded`):**
   - Subclasses `GraphQLError` and `DjangoStrawberryFrameworkError`, carrying `RESOURCE_LIMIT_ERROR_CODE` (`"RESOURCE_LIMIT_EXCEEDED"`), `bound`, `limit`, and `charged` extensions for consistent transport rendering.
   - Implements `__reduce__` for full pickle and copy fidelity.

## Verification

1. **Traced connections across callers and consumers:**
   - `django_strawberry_framework/__init__.py`: exports `ResourcePolicy`, `DEFAULT_RESOURCE_POLICY`, `ResourceLimitExceeded`, and `RESOURCE_LIMIT_ERROR_CODE`.
   - `schema.py`: `DjangoSchema.__init__` calls `resolve_resource_policy` and installs `DjangoResourcePolicyExtension`.
   - `extensions/resource_policy.py`: enforces document and value budgets during `on_operation` and `on_execute`.
   - `list_field.py`: uses `validate_collection_bound`, `bounded_rows`, and `bounded_rows_async`.
   - `connection.py`: calls `check_deadline` during connection resolution and `effective_bound` against `max_page_size`.
   - `relay.py`: calls `check_deadline` before executing single/batch node refetch queries.
   - `mutations/resolvers.py`: calls `check_deadline` before opening mutation write transaction pipelines.
   - `types/resolvers.py`: uses `bounded_rows` and `bounded_rows_async` on many-relation fields.
2. **Examined existing test suites:**
   - `tests/test_resource_policy.py` (110 tests): Unit tests covering policy construction, domain validation, narrowing rules, context threading, deadline calculation, async row bounding cleanup, and value walker edge cases.
   - `examples/fakeshop/test_query/test_resource_policy_api.py` (37 tests): Live HTTP `/graphql/` acceptance tests verifying text scanning (tokens, depth), expanded AST budget (selections, aliases, collection cost), variable value budget (node IDs, membership items, relation IDs, container width, value depth, input nodes, upload bytes), collection bounds, cooperative deadline rejections, and zero ORM work on rejection.
3. **Focused test execution:**
   - `uv run pytest tests/test_resource_policy.py --no-cov` passed (111/111 passed).
   - `uv run pytest examples/fakeshop/test_query/test_resource_policy_api.py --no-cov` passed (37/37 passed).
   - `uv run pytest docs/review/temp-tests/resource_policy/test_resource_policy_scratch.py --no-cov` passed (9/9 passed).
   - Package coverage on `django_strawberry_framework/resource_policy.py` is 100% (163/163 statements).
4. **Scratch verification:**
   - `docs/review/temp-tests/resource_policy/test_resource_policy_scratch.py` verified immutability, all narrowing edge cases, settings resolution branches, context lifecycle (dict, object, None), deadline branches (future, past, unconfigured), sync/async row bounding, collection bound validation, and effective bound combinations.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/resource_policy.py` provides a comprehensive, immutable, and fail-closed resource budget model for request execution. All bounds are validated at construction, narrowed strictly, and threaded safely through request contexts without leaking across operations. Cooperative deadlines and collection row bounds are enforced consistently across sync and async execution paths. Test coverage is 100% with no defects or design improvements identified.

## Implementation (Worker 1)

- **Changed files and necessity:**
  - `tests/test_resource_policy.py`: Added `test_bounded_rows_async_exhausted_iterator_without_truncation` to pin the behavior where an async iterator exhausts naturally before reaching the row limit without triggering early `aclose()`.
  - `django_strawberry_framework/resource_policy.py`: None (zero-edit cycle on target file). Scoped diff against cycle baseline (`HEAD` = `12779c99`) is empty.
- **Permanent tests and pinned behavior:**
  - `tests/test_resource_policy.py::test_bounded_rows_async_exhausted_iterator_without_truncation` pins async iterator natural exhaustion without truncation.
  - Existing suite of 110 unit tests in `tests/test_resource_policy.py` and 37 live HTTP tests in `examples/fakeshop/test_query/test_resource_policy_api.py` comprehensively pin all `ResourcePolicy` invariants.
- **Scratch or focused verification:**
  - `docs/review/temp-tests/resource_policy/test_resource_policy_scratch.py` passed (9/9 tests).
  - `tests/test_resource_policy.py` passed (111/111 tests).
  - `examples/fakeshop/test_query/test_resource_policy_api.py` passed (37/37 tests).
- **Formatter and linter results:**
  - `uv run ruff format .` and `uv run ruff check --fix .` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check tests/test_resource_policy.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle on production source, existing behavior unchanged.

## Independent verification (Worker 2)

- **Traced paths and lifecycle boundaries:**
  - `ResourcePolicy` construction, domain validation (positive integers, finite positive float/int or `None` deadline), and strict narrowing invariants via `narrowed()`.
  - Schema-level policy resolution ladder (`resolve_resource_policy`) against `ResourcePolicy` instances, dictionary mappings, `DJANGO_STRAWBERRY_FRAMEWORK["RESOURCE_POLICY"]` settings, and `DEFAULT_RESOURCE_POLICY`.
  - Fail-closed context lifecycle (`stash_resource_policy`, `clear_resource_context`, `policy_from_info`) across dict and object contexts, preventing deadline leaks across reused contexts and ensuring fail-closed fallback to `DEFAULT_RESOURCE_POLICY`.
  - Cooperative wall-clock deadline checks (`check_deadline`) across collection resolution seams, refetch fields, and write pipelines.
  - Collection row bounding (`bounded_rows`, `bounded_rows_async`) across lazy QuerySets, sequence slices, unsliceable iterators, and pure async generators. Verified proper natural exhaustion vs early truncation with `aclose()` cleanup and exception note preservation.
  - Field-level bound helpers (`validate_collection_bound`, `effective_bound`) enforcing constructor-time validation and narrowing/trusted widening opt-in.
  - Wire-visible error identity (`ResourceLimitExceeded`), inheritance (`GraphQLError`, `DjangoStrawberryFrameworkError`), extensions payload (`code`, `bound`, `limit`, `charged`), and copy/pickle serialization fidelity.
- **Verification experiments and test runs:**
  - Executed focused unit test suite: `uv run pytest tests/test_resource_policy.py --no-cov` (111 passed in 1.95s).
  - Executed live GraphQL test suite: `uv run pytest examples/fakeshop/test_query/test_resource_policy_api.py --no-cov` (37 passed in 15.60s).
  - Authored and executed Worker 2 scratch test suite: `docs/review/temp-tests/resource_policy/test_worker2_verification.py` covering pickle/copy roundtrips, invalid value validation, narrowing boundaries, settings fallback, context cleanup, armed/unarmed deadline branches, async iterator cleanup, and collection bound combinations (9 passed in 1.86s).
  - Confirmed `tests/test_resource_policy.py::test_bounded_rows_async_exhausted_iterator_without_truncation` correctly pins async iterator natural exhaustion without early `aclose()`.
- **Disposition of findings:**
  - Zero-edit review cycle on production target `django_strawberry_framework/resource_policy.py`. Scoped diff against cycle baseline (`HEAD` = `12779c99`) confirmed empty for production code.
  - All findings disposed and verified complete.

