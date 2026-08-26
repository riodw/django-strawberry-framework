# Review: `django_strawberry_framework/error_policy.py`

Status: verified

## Understanding

`django_strawberry_framework/error_policy.py` defines the core data model and normalization entry point for the production error masking subsystem (`spec-048`). It establishes the fail-closed contract that unexpected exceptions in production (`settings.DEBUG is False`) are masked on the wire into a stable client message and a unique correlation identifier.

It owns:
1. **`ErrorPolicy` frozen dataclass**:
   - Represents the immutable production error policy for a schema.
   - Fields:
     - `enabled` (`bool`, default `True`): whether unexpected exceptions are masked.
     - `message` (`str`, default `"An unexpected error occurred."`): the verbatim neutral string returned on masked GraphQL errors.
     - `correlation_extension_key` (`str`, default `"correlationId"`): the key in the GraphQL error `extensions` mapping carrying the correlation identifier.
   - `__post_init__` strict validation:
     - Rejects non-`bool` `enabled` values (e.g. `1`, `0`, `"yes"`, `None`) via `isinstance(self.enabled, bool)` to prevent truthiness coercion bugs.
     - Rejects non-string and empty string values for `message` and `correlation_extension_key`.
     - Formats diagnostics with `describe_value` and raises `ConfigurationError`.
   - `frozen=True` guarantees that resolvers and middleware cannot mutate or widen the policy at request time.
2. **`DEFAULT_ERROR_POLICY` singleton**:
   - The fail-closed baseline instance with default arguments, used whenever neither constructor arguments nor Django settings supply overrides.
3. **`resolve_error_policy` normalization helper**:
   - Normalizes error policy configuration once at schema construction (`schema.py::DjangoSchema.__init__`), failing fast at startup rather than on request execution.
   - Precedence order (highest to lowest):
     1. Explicit `ErrorPolicy` instance passed to `DjangoSchema(error_policy=...)` (returned as-is).
     2. Explicit `Mapping` passed to `DjangoSchema(error_policy={...})` (applied over `DEFAULT_ERROR_POLICY` defaults).
     3. Django settings `DJANGO_STRAWBERRY_FRAMEWORK["ERROR_POLICY"]` mapping retrieved via `conf.error_policy_setting()`.
     4. `DEFAULT_ERROR_POLICY` fallback when no configuration is provided.
   - Validates that non-`None` inputs are `Mapping` instances.
   - Validates mapping keys against known `ErrorPolicy` dataclass fields, rejecting unrecognized options with a sorted list of invalid keys and the valid vocabulary.
   - Sits as the structural twin of `resource_policy.py::resolve_resource_policy`.
4. **`new_correlation_id` generation helper**:
   - Produces a fresh 32-character lowercase hexadecimal string (`uuid.uuid4().hex`).
   - Minted per masked error (not per operation) to ensure unambiguous server-side log correlation with the original exception and traceback.
5. **System integration**:
   - Read and resolved at schema initialization in `schema.py::DjangoSchema.__init__`, storing the normalized `ErrorPolicy` on `schema.error_policy`.
   - Consumed by `extensions/error_policy.py` (`DjangoErrorPolicyExtension`, `schema_error_policy`, `mask_execution_result`, `masking_is_active`) during operation teardown.
   - Consumed by `consumers.py::_stop_aware_results` for per-event subscription masking.
   - Exposed on the public package surface via `django_strawberry_framework/__init__.py`.

## Verification

1. Traced connections across the codebase:
   - `schema.py`: verified schema initialization precedence, `schema.error_policy` attribute storage, and `DjangoErrorPolicyExtension` front-of-list installation.
   - `extensions/error_policy.py`: verified consumption of `DEFAULT_ERROR_POLICY`, `ErrorPolicy`, and `new_correlation_id` in error masking and fail-closed degradation.
   - `conf.py`: verified `ERROR_POLICY_KEY` and `error_policy_setting()`.
   - `consumers.py`: verified `schema_error_policy` resolution and subscription stream masking.
2. Examined test suites:
   - `tests/test_error_policy.py` (38 tests): covers `ErrorPolicy` construction, field type validation, immutability, precedence ladder, settings parsing, correlation ID formatting/uniqueness, extension install position, and fail-closed degradation.
   - `examples/fakeshop/test_query/test_error_policy_api.py` (36 tests): covers live `/graphql/` production error masking matrix, completion phase masking, path retention, logger correlation ID emission, deliberate `GraphQLError` preservation, and opt-outs.
3. Test executions:
   - `uv run pytest tests/test_error_policy.py examples/fakeshop/test_query/test_error_policy_api.py --no-cov` (74 passed).
4. Scratch tests:
   - `docs/review/temp-tests/error_policy/test_scratch_error_policy.py` (34 passed): verified `ErrorPolicy` defaults, frozen mutation rejections, pickle roundtrips, invalid type/empty string rejections, `resolve_error_policy` precedence matrix (instance, None, settings, explicit mapping, empty mapping, invalid types, unknown keys), and correlation ID character/length/uniqueness properties.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/error_policy.py` is concise, robust, and correctly implements the core data structures and normalization logic required by `spec-048`. It enforces strict fail-closed validation, frozen immutability, unambiguous error correlation ID generation, and deterministic startup resolution matching `resource_policy.py`. No bugs, design flaws, or regressions were found.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/error_policy.py` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/test_error_policy.py` (38 tests) pins `ErrorPolicy` construction, strict field validation, immutability, resolution precedence, and correlation ID formatting.
  - `examples/fakeshop/test_query/test_error_policy_api.py` (36 tests) pins end-to-end HTTP/GraphQL error masking against Django views.
- **Scratch verification:**
  - `docs/review/temp-tests/error_policy/test_scratch_error_policy.py` passed (34/34 tests), challenging `ErrorPolicy` immutability, pickle serialization, type rejections, resolution ladder, unknown option handling, and correlation ID uniqueness.
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/error_policy.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/error_policy.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

Independently traced and verified the production error masking data model, validation contracts, normalization precedence ladder, correlation ID generation, and schema/extension integration in `django_strawberry_framework/error_policy.py`.

### 1. Scoped diff and zero-edit confirmation
- Target: `django_strawberry_framework/error_policy.py`
- Baseline: `HEAD` (`12779c99`)
- Scoped diff: `git diff 12779c99 -- django_strawberry_framework/error_policy.py` is empty.

### 2. Behavioral re-trace and contracts verified
- **`ErrorPolicy` frozen dataclass**:
  - Confirmed strict validation in `__post_init__`: `enabled` must be an exact `bool` (rejecting truthy/falsy ints, strings, and other types to avoid accidental masking opt-in/opt-out bugs); `message` and `correlation_extension_key` must be non-empty strings.
  - Confirmed `ConfigurationError` diagnostics via `describe_value`.
  - Confirmed immutability via `frozen=True`, preventing request-time mutation or widening.
- **`DEFAULT_ERROR_POLICY` singleton**:
  - Confirmed fail-closed default instance (`enabled=True`, `message="An unexpected error occurred."`, `correlation_extension_key="correlationId"`).
- **`resolve_error_policy` normalization helper**:
  - Confirmed deterministic precedence ladder: `ErrorPolicy` instance > explicit `Mapping` > Django settings `DJANGO_STRAWBERRY_FRAMEWORK["ERROR_POLICY"]` > `DEFAULT_ERROR_POLICY`.
  - Confirmed rejection of non-Mapping types for configuration overrides.
  - Confirmed strict vocabulary validation against known `ErrorPolicy` dataclass fields, rejecting unrecognized keys with helpful diagnostic naming.
  - Confirmed symmetry with `resource_policy.py::resolve_resource_policy`.
- **`new_correlation_id` generation helper**:
  - Confirmed generation of fresh 32-character lowercase hexadecimal UUIDs (`uuid.uuid4().hex`), minted per masked error to avoid log ambiguity.
- **System integration**:
  - Traced resolution at schema initialization (`schema.py::DjangoSchema.__init__`), fail-closed schema fallback (`extensions/error_policy.py::schema_error_policy`), and subscription masking (`consumers.py::_stop_aware_results`).

### 3. Test executions and scratch tests
- **Focused & permanent tests**:
  - `uv run pytest tests/test_error_policy.py examples/fakeshop/test_query/test_error_policy_api.py --no-cov` (74 passed).
- **Scratch tests**:
  - `docs/review/temp-tests/error_policy/test_scratch_error_policy.py` (34 passed), covering dataclass defaults, immutability under assignment, pickle roundtrips, invalid type and empty string rejections, resolution precedence matrix, invalid type/unknown option rejections, and correlation ID uniqueness across 2,000 samples.
  - Total combined test run: 108 passed.
- **Linters**:
  - `uv run ruff check django_strawberry_framework/error_policy.py` (passed, 0 errors).
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/error_policy.py` (passed, 0 errors).

### 4. Disposition of findings
- High / Medium / Low findings: None.
- All contracts, fail-closed guarantees, and structural constraints are fully upheld.
- Review complete; verified.

