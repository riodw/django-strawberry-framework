# Review: `django_strawberry_framework/keyset.py`

Status: verified

## Understanding

`django_strawberry_framework/keyset.py` implements the keyset (value-encoded) stable cursor subsystem for Relay connections opted in via `Meta.cursor_field` (e.g. `cursor_field = ("-created_at", "id")`). It replaces positional `arrayconnection:N` offset cursors with value-encoded tuple-comparison seeks (`WHERE (created_at, id) > (%s, %s)`), providing insert- and delete-safe pagination without cursor drift and eliminating offset scan overhead.

It owns:
1. **Namespace Isolation & Token Format:**
   - Defines `KEYSET_CURSOR_PREFIX = "dstcursor"`.
   - Distinct prefix from Strawberry's `arrayconnection` and `strawberry-graphql-django`'s `orderedcursor`, making cursor vocabularies mutually rejecting.
2. **Confidential & Authenticated Codec:**
   - Cursors are authenticated-encrypted using AES-SIV with a key derived from Django's `SECRET_KEY` via HMAC-SHA512 domain separation (`_CURSOR_ENCRYPTION_SALT`, `_CURSOR_ENCRYPTION_CONTEXT`).
   - Supports key rotation: attempts `settings.SECRET_KEY` and all entries in `settings.SECRET_KEY_FALLBACKS` on decryption.
   - Uniform error handling: `_invalid_cursor_error` maps all tampering, decoding, json, format, or fingerprint mismatches into a uniform `GraphQLError` to prevent oracle or timing disclosures.
   - Deterministic ciphertext: identical ordering values under the same order produce identical ciphertext across fetch strategies (windowed, lateral, fallback, root).
   - Soft dependency: `cryptography` is loaded lazily on demand via `require_optional_module` with an actionable install hint.
3. **Field Serialization & Deserialization:**
   - Serializes ordering values using Django's `models.Field.value_to_string` and deserializes with `models.Field.to_python`.
   - Enforces a strict round-trip canonical check (`serialize_cursor_value(field, value) == raw`) to reject non-canonical representations before reaching SQL.
   - Rejects `None` ordering values to avoid `value_to_string` converting `None` to the string `"None"`.
4. **Column Specification & Validation:**
   - `split_order_ref`: Single syntax owner for cursor order references (optional leading `-`, local field name, no relation traversal).
   - `validate_cursor_field_references`: Checks non-empty sequences and prevents duplicate column names.
   - `validate_cursor_field_columns`: Enforces the v1 column contract at schema finalization (local, concrete, non-nullable columns, exclusion of `JSONField`, terminal column is unique/pk).
   - `cursor_columns_for`: Resolves validated references into immutable `CursorColumn` dataclasses.
5. **Seek Planning & Dual Renderers:**
   - `keyset_seek_greater`: Canonical direction calculation across ascending/descending and forward/backward (`flip`) pagination.
   - `build_keyset_seek_plan`: Builds dialect-agnostic `KeysetSeekPlan` carrying direction booleans and bind values.
   - `keyset_seek_q`: ORM `models.Q` renderer producing the redundant leading bound (`col0 >= v0` or `col0 <= v0`) ANDed with the per-column OR-expansion (`col0 > v0 OR (col0 = v0 AND col1 < v1)...`) for composite index access.
   - `keyset_seek_sql`: Raw-SQL parameterized renderer producing native row-value comparisons `(a, b) > (%s, %s)` when directions are uniform or redundant-leading-bound OR-expansions when directions are mixed.
6. **Order Fingerprinting:**
   - `order_fingerprint`: Embeds effective ordering in payload to reject cross-order cursor replay.

## Verification

1. **Traced connections across callers and consumers:**
   - `connection.py` (`_resolve_keyset_connection`, `_keyset_order_state`, `encode_keyset_cursor`, `decode_keyset_cursor`, `KeysetSeek`).
   - `types/base.py` (`_validate_cursor_field` at class declaration time).
   - `types/finalizer.py` (`validate_cursor_field_columns` at schema finalization time).
   - `optimizer/lateral_fetch.py` (`keyset_seek_sql`, `_keyset_seek_quals_match`).
   - `optimizer/nested_fetch.py` & `optimizer/nested_planner.py` (`KeysetSeek`, `_keyset_cursor_context`, `_keyset_window_slice_from_arguments`, `_extend_only_projection`).
   - `optimizer/plans.py` (window keyset seek count annotation and marker row semantics).
   - `utils/connections.py` (`derive_keyset_window_bounds`, `window_range_plan`).
2. **Examined existing test suites:**
   - `tests/test_keyset.py` (48 tests): covers `split_order_ref`, `validate_cursor_field_columns`, crypto caching, secret rotation fallbacks, soft dependency handling, codec round-trips, tampering rejection, direction tables, `KeysetSeekPlan`, `keyset_seek_sql`, `keyset_seek_q`, window pagination, and lateral SQL generation.
   - `tests/test_keyset_connection.py` (28 tests): covers keyset context caching, slicer guards, async execution, deferred column restoration, backward window fallback, and order state derivation error arms.
   - `examples/fakeshop/test_query/test_keyset_api.py` (34 tests): live GraphQL HTTP acceptance tests covering end-to-end cursor round-tripping, mutation resilience, pre-seek total count stability, tamper/offset rejection, backward pagination, nested batched windows, non-lazy-loaded cursor column queries, and permission-aware decoding.
3. **Focused test execution:**
   - `uv run pytest tests/test_keyset.py tests/test_keyset_connection.py examples/fakeshop/test_query/test_keyset_api.py --no-cov` passed (110/110 passed).
   - Scoped line coverage on `django_strawberry_framework/keyset.py` is 100% (216/216 statements).
4. **Scratch verification:**
   - `docs/review/temp-tests/keyset/test_keyset_scratch.py` passed (8/8 tests), probing `split_order_ref` error branches, duplicate column detection, comprehensive column validation, multi-field serialization/deserialization canonical checks, 3-column mixed seek SQL and Q generation, uniform descending SQL rendering, plan guard checks, and non-canonical float repr rejection.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/keyset.py` is a robust, secure, and well-architected module. It enforces strong cryptographic confidentiality, strict column constraints, index-friendly SQL/Q seek predicates, and complete cross-strategy parity. Test coverage is 100% with no defects or design improvements identified.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/keyset.py` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/test_keyset.py` (48 tests), `tests/test_keyset_connection.py` (28 tests), and `examples/fakeshop/test_query/test_keyset_api.py` (34 tests) comprehensively pin all keyset codec, validation, seek planning, ORM/SQL rendering, window integration, and live GraphQL HTTP pagination behaviors.
- **Scratch verification:**
  - `docs/review/temp-tests/keyset/test_keyset_scratch.py` passed (8/8 tests).
  - Focused pytest suite passed (110/110 tests).
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/keyset.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/keyset.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- **Scoped diff verification:**
  - Verified that `git diff 12779c99 -- django_strawberry_framework/keyset.py` is completely empty (zero edits in this cycle).
- **Independent behavior re-tracing and boundary analysis:**
  - Validated declaration-time syntax validation (`types/base.py`) and schema finalization column verification (`types/finalizer.py`).
  - Validated resolver seek orchestration, cursor minting, and error masking in `connection.py`.
  - Validated optimizer planner integration (`optimizer/nested_planner.py`), window partition slicing (`optimizer/nested_fetch.py`), lateral SQL seek qual compilation (`optimizer/lateral_fetch.py`), and window bounds derivation (`utils/connections.py`).
  - Confirmed strict cryptographic confidentiality, key rotation via `SECRET_KEY_FALLBACKS`, tampering rejection, and uniform error reporting to eliminate oracle disclosures.
  - Confirmed index-friendly redundant leading bound construction in both `keyset_seek_q` and `keyset_seek_sql`.
- **Independent scratch testing:**
  - Executed `docs/review/temp-tests/keyset/test_keyset_scratch.py` (8/8 passed).
  - Authored and executed `docs/review/temp-tests/keyset/test_keyset_independent_verifier.py` (5/5 passed), probing:
    - Multi-secret rotation across `SECRET_KEY` and `SECRET_KEY_FALLBACKS`, bit-flip ciphertext tampering, and invalid base64 payloads.
    - Uniform rejection of foreign cursor prefixes (`arrayconnection`, `orderedcursor`), malformed payloads, non-dict payloads, arity mismatches, and cross-ordering replay via fingerprint check.
    - Null-value rejection at serialization boundary (`serialize_cursor_value`) and encoding boundary (`encode_keyset_cursor`).
    - Complete direction truth table for `keyset_seek_greater` across all permutations of `descending` and `flip`.
    - Exact parity between raw-SQL parameterized seeks (`keyset_seek_sql`) and ORM `models.Q` seeks (`keyset_seek_q`) across single, uniform compound, and mixed-direction composite orderings.
- **Focused test execution:**
  - `uv run pytest tests/test_keyset.py tests/test_keyset_connection.py examples/fakeshop/test_query/test_keyset_api.py --no-cov` (110/110 passed).
- **Conclusion:**
  - The implementation is completely verified, robust, secure, and adheres strictly to the repository architecture and contracts. No defects or regressions were found.
