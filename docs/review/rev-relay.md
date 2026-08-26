# Review: `django_strawberry_framework/relay.py`

Status: verified

## Understanding

`django_strawberry_framework/relay.py` implements the consumer-facing root Relay refetch fields (`DjangoNodeField` and `DjangoNodesField`), the mutation/form/serializer typed GlobalID decoding primitive (`decode_model_global_id`), and refetch dispatch lifecycle utilities (`_stamp_node_type`, `_interleave`, `_check_nodes_result`, `_coerce_pk_or_none`, `_resolve_real_pk`).

It owns:
1. **Root Refetch Field Factories:**
   - `DjangoNodeField(target_type=None, ...)` produces a `strawberry.field(resolver=...)` resolving the root Relay `node(id: ID!)` query.
   - `DjangoNodesField(target_type=None, ...)` produces a `strawberry.field(resolver=...)` resolving the root batch Relay `nodes(ids: [ID!]!)` query.
   - Both support the **Bare** form (`node: relay.Node | None = DjangoNodeField()`, resolving any registered Node type) and the **Typed** form (`genre: GenreType | None = DjangoNodeField(GenreType)`, validating the target at construction and rejecting mismatched ids at runtime with a descriptive `GraphQLError`).
   - Both enforce cooperative resource deadlines via `check_deadline(info)` before query execution.
2. **Nullable-by-Contract Resolution & Failure Families:**
   - Malformed GlobalIDs (invalid base64, missing delimiter, unresolvable type/model, or strategy violation) raise `GraphQLError` carrying the `GLOBALID_INVALID` extension code (`_decode_or_graphql_error`).
   - Uncoercible primary keys (e.g., non-integer literals against integer pk columns) return `None` (single) or a positional `None` null-hole (batch) with zero database queries issued (`_coerce_pk_or_none`).
   - Hidden rows (filtered out by `get_queryset` or cascade permissions) and nonexistent IDs resolve to `None` with equal query counts to prevent existence oracles.
   - Batch queries decode all IDs before executing any queries: a malformed or wrong-type ID anywhere fails the entire field, while valid missing/hidden/uncoercible IDs produce positional `null` holes.
3. **Multi-Type Model Routing & Stamp Isolation:**
   - `_stamp_node_type(resolved_type, node)` shallow-copies model instances and sets `_NODE_TYPE_HINT_ATTR` so GraphQL type resolution (`is_type_of`) disambiguates models registered under multiple `DjangoType` definitions based on the decoded GlobalID type, while preventing hint leakage across shared or reused ORM objects.
4. **Batch Gathering & Custom Overrides Contract:**
   - In async contexts, `DjangoNodesField` gathers batch queries per distinct decoded type into a single coroutine using sequential awaits for database safety.
   - In sync contexts, `reject_async_in_sync_context` rejects coroutine returns from consumer `resolve_node` / `resolve_nodes` overrides under `schema.execute_sync` with `SyncMisuseError`.
   - `_check_nodes_result` enforces that custom `resolve_nodes` returns are 1:1 in length with the requested IDs (accepting materialized generators), raising `ConfigurationError` on length mismatch.
   - `_interleave` reassembles grouped per-type results into the exact input order with positional `None` entries for uncoercible IDs.
5. **Typed GlobalID Decoding for Mutations and Relations:**
   - `decode_model_global_id(value, expected_model, *, using=None)` serves as the single source for decoding typed IDs across root mutation lookups, forms, serializer inputs, and relation assignments.
   - Returns structured `DecodeResult(status, pk, resolved_type)` where `status` is a `GlobalIDDecode` enum (`OK`, `DECODE_FAILED`, `WRONG_MODEL`, `UNCOERCIBLE_PK`).
   - Maps non-pk `NodeID` attributes to actual model primary keys via `_resolve_real_pk` using the default manager (or active write transaction pipeline alias).
6. **Subsystem Lifecycle & Target Validation:**
   - `_node_fields_declared` tracks declared node fields and is co-cleared with `registry.clear()` via `register_subsystem_clear(_clear_node_fields_declared, owner="relay.node_fields")`.
   - Target types are validated via `_validate_node_target` (wrapping `_validate_relay_djangotype_target`) to ensure targets are registered Relay-Node-shaped `DjangoType` subclasses.

## Verification

1. **Traced connections across callers and consumers:**
   - `django_strawberry_framework/types/finalizer.py`: inspects `_node_fields_declared` during schema finalization to ensure registered Node types exist if node fields are declared.
   - `django_strawberry_framework/mutations/resolvers.py`: calls `decode_model_global_id` and `coerce_lookup_id` for mutation instance lookup and relation decoding.
   - `django_strawberry_framework/forms/resolvers.py`: imports `GlobalIDDecode` and `decode_model_global_id` for form relation decoding.
   - `django_strawberry_framework/rest_framework/resolvers.py` & `django_strawberry_framework/utils/write_values.py`: consumes `decode_model_global_id` for serializer and relation inputs.
   - `examples/fakeshop/apps/library/schema.py`: exposes root `node`, `nodes`, and typed `genre` fields over the live GraphQL schema.
2. **Examined existing test suites:**
   - `examples/fakeshop/test_query/test_library_api.py`: live HTTP tests covering round-trip `node(id:)` refetch, typed `genre(id:)` refetch, typed mismatch `GraphQLError`, in-band `GLOBALID_INVALID`, uncoercible pk `null`, batch `nodes(ids:)` ordering, null-holes, and duplicates.
   - `tests/test_relay_node_field.py` (47 tests): comprehensive package-tier tests covering model-label vs type-name strategy routing, multi-type model typename routing, `_stamp_node_type` ORM instance copy isolation, custom `relay.NodeID[...]` attributes with real pk mapping, exact query counts on hidden/missing paths, malformed ID error codes, batch grouping, construction-time guards, finalize-time ledger check, async gathering, sync misuse rejection, generator returns, cascade permissions, and sealed-execution boundary with hostile QuerySet subclasses.
3. **Focused test execution:**
   - `uv run pytest tests/test_relay_node_field.py --no-cov` passed (47/47 passed).
   - `uv run pytest docs/review/temp-tests/relay/test_relay_scratch.py --no-cov` passed (6/6 passed).
   - Package coverage on `django_strawberry_framework/relay.py` is 100% (166/166 statements).
4. **Scratch verification:**
   - `docs/review/temp-tests/relay/test_relay_scratch.py` verified all `decode_model_global_id` enum status branches (`OK`, `DECODE_FAILED`, `WRONG_MODEL`, `UNCOERCIBLE_PK`), `_check_typed_match` mismatch message formatting, `_check_nodes_result` generator materialization and error formatting, `_interleave` positional null-hole reassembly, `_node_fields_declared` ledger clear on `registry.clear()`, active `write_pipeline` alias recovery in `_resolve_real_pk`, and plain object passthrough in `_stamp_node_type`.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/relay.py` provides a secure, fail-closed, and highly compliant implementation of Relay root refetch fields and typed GlobalID decoding. It cleanly separates decode validation from execution dispatch, prevents existence leaks through uniform query counts and positional null-holes, isolates multi-type model routing via instance copying, and provides a robust single-sourced decoding primitive for mutations, forms, and serializers. Test coverage is 100% with no defects or design improvements identified.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/relay.py` is empty.
- **Permanent tests and pinned behavior:**
  - `examples/fakeshop/test_query/test_library_api.py` pins live HTTP root refetch (`node`, `nodes`, typed `genre`), error codes (`GLOBALID_INVALID`), and batch null-hole behavior.
  - `tests/test_relay_node_field.py` (47 tests) pins model-label vs type strategy routing, multi-type model typename disambiguation, `_stamp_node_type` instance copy isolation, custom `NodeID` non-pk attribute mapping, query count equality on null paths, construction/finalize guards, async gathering, `SyncMisuseError` discrimination, cascade permissions, and hostile QuerySet sealing.
- **Scratch verification:**
  - `docs/review/temp-tests/relay/test_relay_scratch.py` passed (6/6 tests).
  - Focused pytest suite passed (47 unit tests in `tests/test_relay_node_field.py`).
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/relay.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/relay.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- **Behavior and Path Re-tracing:**
  - Re-traced `DjangoNodeField` factory lifecycle: validated construction-time target checks (`_validate_node_target`), cooperative deadline checks (`check_deadline`), narrow `ConfigurationError` to `GraphQLError` (`GLOBALID_INVALID`) conversion in `_decode_or_graphql_error`, and typed match validation (`_check_typed_match`).
  - Re-traced nullable-by-contract resolution and zero-query early returns for uncoercible PK literals (`_coerce_pk_or_none`), ensuring identical query count parity across missing, hidden, and permission-denied rows to eliminate existence oracles.
  - Re-traced multi-type model typename routing and copy isolation in `_stamp_node_type`: confirmed shallow-copying of model instances before setting `_NODE_TYPE_HINT_ATTR` prevents routing hint pollution across shared/reused instances while gracefully handling unstamped/non-model/custom-slotted objects.
  - Re-traced `DjangoNodesField` batch execution lifecycle: confirmed empty input list short-circuits with zero queries before deadline checks; confirmed all IDs are decoded and validated before queries issue; confirmed batch gathering into sequential awaits in async context and sync misuse detection (`reject_async_in_sync_context`) in sync context.
  - Re-traced `_check_nodes_result` and `_interleave` reassembly contracts: verified 1:1 length enforcement against custom `resolve_nodes` overrides, handling both list and generator outputs, and exact positional mapping with positional `None` holes for uncoercible literals.
  - Re-traced typed GlobalID decoding (`decode_model_global_id`): confirmed structured `DecodeResult` returns across `OK`, `DECODE_FAILED`, `WRONG_MODEL`, and `UNCOERCIBLE_PK` statuses. Confirmed `_resolve_real_pk` maps non-pk `NodeID` attributes to actual model primary keys using the default manager or the active `write_pipeline` transaction alias context.
  - Re-traced module-level ledger `_node_fields_declared` and co-clearing with `registry.clear()` via `register_subsystem_clear`.
- **Scoped Diff Verification:**
  - Verified empty diff against cycle baseline `12779c99` (`git diff 12779c99 -- django_strawberry_framework/relay.py`).
- **Test Executions:**
  - `uv run pytest tests/test_relay_node_field.py --no-cov`: 47/47 passed.
  - `uv run pytest docs/review/temp-tests/relay/test_relay_scratch.py --no-cov`: 6/6 passed.
  - `uv run pytest examples/fakeshop/test_query/test_library_api.py --no-cov`: 202/202 passed.
- **Disposition:**
  - Zero findings confirmed. Implementation is robust, fully compliant, and verified. Status set to `verified`.

