# Review: `django_strawberry_framework/extensions/`

Status: verified

## Understanding

`django_strawberry_framework/extensions/` provides the schema-level runtime extensions for request budgeting, production error sanitization, and development database/exception diagnostics (`spec-047`, `spec-048`, graphene-django `DjangoDebug` parity).

### Subpackage Architecture & Module Cohesion

1. **Subpackage Boundary & Root Exports (`__init__.py`):**
   - Public API exports: `__all__ = ["DjangoDebugExtension", "DjangoErrorPolicyExtension", "DjangoResourcePolicyExtension"]`.
   - Structural boundary rationale:
     - `DjangoDebugExtension` is deliberately **excluded** from top-level `django_strawberry_framework.__init__.__all__` because it is an opt-in, development-only diagnostic tool that discloses sensitive parameter bindings and server-side stack traces.
     - `DjangoErrorPolicyExtension` and `DjangoResourcePolicyExtension` **are** exported from `django_strawberry_framework.__init__.__all__` because `DjangoSchema` installs both by default on every schema it builds.

2. **Development Query Log & Exception Diagnostics (`debug.py`):**
   - Implements `DjangoDebugExtension` (subclass of `strawberry.extensions.SchemaExtension`).
   - Owns `_CursorCaptureCoordinator` providing thread-safe, lock-protected reference counting for `force_debug_cursor` across active database connections (`connections.all()`). Uses `ExitStack` in `on_operation` to ensure fail-loud, partial-acquisition unwind safety.
   - Fail-closed security gate: Strictly inert when `settings.DEBUG` is not `True` unless explicitly constructed with `allow_unsafe_production=True` (strictly validated as `isinstance(..., bool)` to reject truthy string values like `"false"`). Emits a single warning and withholds the `debug` payload in production without disrupting request execution.
   - Deterministic wire payload serialization: SQL rows with graphene-compatible keys (`vendor`, `alias`, `sql`, `duration`, `isSlow`, `isSelect`), unmasked exception tracebacks, terminal exception chain unrolling with cycle defense and a 64-hop recursion limit (`_MAX_ORIGINAL_ERROR_HOPS = 64`), and multi-pass payload budgeting (`_MAX_PAYLOAD_TEXT_CHARS = 262144`).
   - Pure, idempotent `get_results()` read returning `{"debug": self._payload}` or `{}`.

3. **Production Error Masking & Wire Sanitization (`error_policy.py`):**
   - Implements `DjangoErrorPolicyExtension` (subclass of `strawberry.extensions.SchemaExtension`).
   - Response-side enforcement of `ErrorPolicy` under `settings.DEBUG is not True`.
   - Structural error classification (`_is_unexpected`):
     - Syntax, parse, and document validation errors (`original_error is None`) are preserved unmasked.
     - Deliberate framework and consumer rejections (`isinstance(original_error, GraphQLError)`) are preserved unmasked.
     - Unhandled execution exceptions escaping resolvers or value-completion routines (non-null propagation, list completion, scalar serialization) are classified as unexpected and masked with a stable message and correlation ID.
   - Safe replacement (`_masked` & `_degraded`): logs original exceptions with tracebacks and correlation IDs to `logger.error`, while returning sanitized `GraphQLError` with client location retention.
   - Pure copy semantics in `mask_execution_result`: returns a shallow copy of the result when masked, leaving `execution_context.result` unchanged so preceding LIFO extension hooks observe original unmasked exceptions.
   - Provides streaming result masking seam for subscription consumers (`consumers.py`).

4. **Request Resource Budgeting & Pre-Parse Defense (`resource_policy.py`):**
   - Implements `DjangoResourcePolicyExtension` (subclass of `strawberry.extensions.SchemaExtension`).
   - Three-phase request budget evaluation:
     1. Pre-Parse Lexer Scan (`scan_document_text` in `on_operation`): counts raw tokens (`max_document_tokens`) and structural bracket nesting depth (`max_depth`) across `{}`, `()`, and `[]` before graphql-core's recursive-descent parser runs.
     2. AST Document Budget (`charge_document` in `on_execute`): non-recursive iterative traversal expanding fragment definitions and inline fragments with cycle guards (`frozenset[str]`), charging selections (`max_selections`), aliases (`max_aliases`), and multiplicative collection costs (`max_collection_cost`).
     3. Value Budget (`_ValueBudget` in `on_execute`): non-recursive stack traversal over argument literals and variables, cycle-guarded by container object identity (`is`), bounding input nodes, depth, container width, nested rows, relation IDs, membership items, scalar byte sizes, and file uploads.
   - Context threading: stashes resolved policy and deadline under `DST_RESOURCE_POLICY` / `DST_RESOURCE_DEADLINE`, guaranteed to restore prior context state in `on_operation`'s `finally` block.

5. **Cross-Extension Execution Lifecycle & Schema Integration:**
   - Extension installation order in `DjangoSchema`:
     - `DjangoErrorPolicyExtension` is prepended at index 0 (`_with_error_policy_extension`).
     - `DjangoResourcePolicyExtension` is appended at the end (`_with_resource_policy_extension`).
     - Consumer-supplied extensions (such as `DjangoDebugExtension`) sit naturally between them: `[DjangoErrorPolicyExtension, ..., DjangoDebugExtension, ..., DjangoResourcePolicyExtension]`.
   - Lifecycle phases:
     - Setup & Pre-Parse: `DjangoResourcePolicyExtension` scans raw document tokens and bracket depth before AST parsing.
     - Pre-Execution: `DjangoResourcePolicyExtension` evaluates document and value budgets in `on_execute`. Rejections raise `ResourceLimitExceeded`, aborting execution with zero database work.
     - Execution: Resolvers execute; database queries and unhandled exceptions are logged.
     - Teardown (LIFO unwinding): `DjangoResourcePolicyExtension` unwinds first to restore context; `DjangoDebugExtension` unwinds next to read original unmasked exceptions from `execution_context.result` and drain query logs; `DjangoErrorPolicyExtension` unwinds last to mask unexpected errors on the wire result.
     - Response assembly: `DjangoDebugExtension.get_results()` merges debug logs into `extensions["debug"]`.

## Verification

1. **Holistic Subpackage Architecture Review:**
   - Verified module cohesion and clean separation of concerns across `__init__.py`, `debug.py`, `error_policy.py`, and `resource_policy.py`.
   - Confirmed public symbol export contracts: `__all__` definitions match documented surfaces.
   - Traced cross-extension execution order, LIFO teardown mechanics, and subscription streaming seams in `consumers.py`.
   - Validated fail-closed security invariants across production and development modes.

2. **Permanent Test Suite Execution:**
   - Ran all permanent test suites covering the subpackage:
     - `tests/extensions/test_debug.py`
     - `tests/test_error_policy.py`
     - `tests/test_resource_policy.py`
     - `examples/fakeshop/test_query/test_debug_extension_api.py`
     - `examples/fakeshop/test_query/test_error_policy_api.py`
     - `examples/fakeshop/test_query/test_resource_policy_api.py`
   - Result: 298 passed in 51.88s.

3. **Subpackage Scratch Verification (`docs/review/temp-tests/extensions/test_scratch_extensions_subpackage.py`):**
   - Verified subpackage `__all__` exports and object identities.
   - Verified `schema_error_policy` safe policy extraction, fallback to `DEFAULT_ERROR_POLICY`, and resilience against hostile property access.
   - Verified LIFO teardown ordering: unhandled resolver exceptions are captured unmasked in `extensions["debug"]["exceptions"]` while being masked in the public `errors` envelope.
   - Verified resource policy rejections (`ResourceLimitExceeded`) pass unmasked through error policy and skip debug payload creation.
   - Verified debug extension payload withholding under production settings (`DEBUG=False`).
   - Verified `DjangoSchema` extension deduplication and automatic ordering (`[ErrorPolicy, ..., ResourcePolicy]`).
   - Result: 6 passed in 2.44s.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The `django_strawberry_framework/extensions/` subpackage is an exceptionally well-engineered, secure, and cohesive component of the framework. It provides robust request-level resource protection, fail-closed production error sanitization, and rich development-time diagnostics. Cross-extension lifecycle phases and LIFO teardown ordering are strictly coordinated, with complete test coverage across both unit and live HTTP acceptance layers.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files and necessity:**
  - None (zero-edit cycle).
  - Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/extensions/` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/extensions/test_debug.py` & `examples/fakeshop/test_query/test_debug_extension_api.py`: pin debug cursor coordinator reference counting, overlap safety, unmasked exception serialization, payload caps, and fail-closed production withholding.
  - `tests/test_error_policy.py` & `examples/fakeshop/test_query/test_error_policy_api.py`: pin index 0 schema placement, structural error classification matrix, copy semantics, correlation ID logging, and completion-phase masking.
  - `tests/test_resource_policy.py` & `examples/fakeshop/test_query/test_resource_policy_api.py`: pin pre-parse lexer scanning, iterative AST document budgeting, non-recursive value budget traversal, upload validation, and context threading.
- **Scratch or focused verification:**
  - `docs/review/temp-tests/extensions/test_scratch_extensions_subpackage.py` passed (6/6 tests), verifying whole-subpackage export identities, schema policy resolution fallbacks, cross-extension LIFO teardown unmasking vs masking interactions, `ResourceLimitExceeded` pass-through, production debug withholding, and schema extension deduplication.
  - Full focused suite passed (298/298 permanent tests).
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/extensions/ docs/review/temp-tests/extensions/test_scratch_extensions_subpackage.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/extensions/` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

### 1. Scoped Diff Baseline Verification

Confirmed that `git diff 12779c99 -- django_strawberry_framework/extensions/` is completely empty. This zero-edit subpackage review cycle introduces no modifications to the production source code.

### 2. Subpackage Architecture & Behavior Tracing

- **Module Boundaries & Root Exports (`__init__.py`):**
  - Confirmed `__all__ = ["DjangoDebugExtension", "DjangoErrorPolicyExtension", "DjangoResourcePolicyExtension"]`.
  - Re-verified intentional design where `DjangoDebugExtension` is excluded from top-level `django_strawberry_framework.__init__.__all__` to prevent accidental production enablement, whereas `DjangoErrorPolicyExtension` and `DjangoResourcePolicyExtension` are root-exported because `DjangoSchema` installs both by default.
- **Development Query Log & Diagnostic Capture (`debug.py`):**
  - Traced `_CursorCaptureCoordinator` reference counting across multiple database connections (`connections.all()`), confirming thread-safe lock management and proper `ExitStack` unwinding even under partial acquisition failures.
  - Re-verified strict `allow_unsafe_production` boolean type validation (`isinstance(..., bool)`), preventing string truthiness bypasses.
  - Traced exception serialization with graphene parity, 64-hop recursion limit with identity set cycle defense (`_MAX_ORIGINAL_ERROR_HOPS`), and 3-pass payload budgeting (`_MAX_PAYLOAD_TEXT_CHARS = 262144`).
- **Production Error Sanitization & Masking (`error_policy.py`):**
  - Traced structural error classification matrix (`_is_unexpected`): client document syntax/parse/validation errors (`original_error is None`) and intentional `GraphQLError` rejections pass unmasked, while unhandled resolver/completion exceptions are masked with correlation IDs and server logging.
  - Re-verified non-mutating copy semantics in `mask_execution_result`, preserving the unmasked error on `execution_context.result` so preceding LIFO extension teardown hooks observe original exceptions.
  - Verified shared streaming seam (`is_maskable_result`, `mask_execution_result`) used by subscriptions in `consumers.py`.
- **Resource Budgeting & Pre-Parse Defenses (`resource_policy.py`):**
  - Traced three-phase budgeting:
    1. Pre-parse lexer scanning (`scan_document_text`) counting raw lexical tokens and bracket nesting depth before AST parsing.
    2. Non-recursive AST document traversal (`charge_document`) with fragment spread cycle guards (`frozenset[str]`), charging selections, aliases, and multiplicative collection costs.
    3. Non-recursive stack traversal in value budget (`_ValueBudget`), cycle-guarded by container object identity (`is`), bounding input nodes, depth, container width, nested rows, relation IDs, membership items, scalar byte sizes, and file uploads.
  - Verified context threading with guaranteed `finally` restoration of prior context values for `DST_RESOURCE_POLICY` and `DST_RESOURCE_DEADLINE`.
- **Cross-Extension Lifecycle Invariants:**
  - Verified `DjangoSchema` extension ordering `[DjangoErrorPolicyExtension, ..., DjangoResourcePolicyExtension]` and deduplication.
  - Verified LIFO unwinding: `DjangoResourcePolicyExtension` teardown restores context -> `DjangoDebugExtension` teardown collects unmasked exceptions from `execution_context.result` -> `DjangoErrorPolicyExtension` teardown masks unexpected errors on wire result.

### 3. Test Verification & Scratch Suite Execution

- Executed the full focused test suite including permanent unit/API tests and the subpackage scratch test:
  - `tests/extensions/test_debug.py`
  - `tests/test_error_policy.py`
  - `tests/test_resource_policy.py`
  - `examples/fakeshop/test_query/test_debug_extension_api.py`
  - `examples/fakeshop/test_query/test_error_policy_api.py`
  - `examples/fakeshop/test_query/test_resource_policy_api.py`
  - `docs/review/temp-tests/extensions/test_scratch_extensions_subpackage.py`
  - Result: 304 passed in 37.26s.
- Executed linters and code style checks:
  - `uv run ruff check django_strawberry_framework/extensions/ docs/review/temp-tests/extensions/test_scratch_extensions_subpackage.py`: 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/extensions/`: 0 errors.

### 4. Conclusion & Status

All contracts, security boundaries, and cross-module interactions are robust, fully tested, and cleanly separated.
Status is set to `verified`.
