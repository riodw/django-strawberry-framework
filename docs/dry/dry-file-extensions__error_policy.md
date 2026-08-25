# DRY review: `django_strawberry_framework/extensions/error_policy.py`

Status: verified

## System trace

`django_strawberry_framework/extensions/error_policy.py` is the execution-phase and streaming-transport enforcement engine for the framework's secure error policy subsystem ([spec-048][spec-048] Decisions 7–11, 13). It defines [`DjangoErrorPolicyExtension`][extensions-error-policy], a Strawberry [`SchemaExtension`][strawberry-extension] that replaces unhandled exception messages with a stable, neutral client message tagged with a unique hexadecimal correlation identifier, while logging the original exception and traceback server-side under that same identifier. It also provides the module-level masking helpers ([`mask_execution_result`][extensions-error-policy], [`is_maskable_result`][extensions-error-policy], [`masking_is_active`][extensions-error-policy], and [`schema_error_policy`][extensions-error-policy]) shared with the WebSocket streaming transport seam.

The module owns the following core responsibilities:

- **Structural classification of execution errors (spec-048 Decision 8):**
  [`_is_unexpected`][extensions-error-policy] inspects error objects arriving in `result.errors` structurally rather than consulting an error-code allowlist:
  - Non-`GraphQLError` objects: Any arbitrary exception or custom error object present in `errors` is classified as unexpected and masked.
  - `error.original_error is None`: Standard GraphQL parse, syntax, or schema validation errors constructed directly by `graphql-core` without an underlying raised exception (as well as Strawberry's async `PreExecutionError` instances). These describe the client's own document and travel untouched.
  - `isinstance(error.original_error, GraphQLError)`: Deliberate client-facing errors raised by framework boundaries (`GLOBALID_INVALID`, `RESOURCE_LIMIT_EXCEEDED` from `ResourceLimitExceeded`, keyset/pagination/filter rejections, and mutation permission denials `"Not authorized to ..."`) or consumer resolvers explicitly raising `GraphQLError`. These travel untouched.
  - Any other exception: Plain Python exceptions (e.g. `ValueError`, `KeyError`, `ZeroDivisionError`, database errors) that escaped resolvers or value completion phases. Masked.
  The rule reads through `graphql-core`'s `located_error` wrapping, uniformly protecting both the resolve phase and value completion phase (non-nullable null propagation, list item completion, scalar serialization).
- **Client-safe error masking and correlation ID tagging (spec-048 Decision 9):**
  [`_masked`][extensions-error-policy] constructs a client-safe replacement for an unexpected error:
  - Mints a fresh 32-character hexadecimal correlation identifier via [`error_policy.py::new_correlation_id`][error-policy] (`uuid.uuid4().hex`).
  - Logs the unhandled exception server-side via `logger.error` on the package logger (`django_strawberry_framework`) with `exc_info=original_error` and the correlation identifier in the log message.
  - Constructs a fresh `GraphQLError` carrying `policy.message`, `original_error=None`, and `extensions={policy.correlation_extension_key: correlation_id}`.
  - Preserves document location metadata (`nodes`, `source`, `positions`, `path`) so clients can correlate partial errors to specific fields in their request document without disclosing server internals.
- **Multi-tiered fail-closed degradation (spec-048 Decision 9 & 11):**
  - [`_degraded`][extensions-error-policy] provides the floor: returns `GraphQLError(message=policy.message)` with no location or correlation ID if reading the offending error or building extensions raises an unexpected exception.
  - [`_replacement_for`][extensions-error-policy] wraps classification and masking in `try...except Exception`, degrading individual unmaskable errors to [`_degraded`][extensions-error-policy] while allowing sibling errors to be masked normally.
  - [`mask_execution_result`][extensions-error-policy] wraps result-level processing in `try...except Exception`. If an unreadable `errors` iterable or hostile result object raises, it logs the failure and degrades to `StrawberryExecutionResult(data=None, errors=[_degraded(policy)])`, dropping `data` and `extensions` completely so unvouched payloads never reach the wire.
  - [`DjangoErrorPolicyExtension._process_result`][extensions-error-policy] safely adopts masked `data`, `errors`, and `extensions` back onto the transport result, replacing `execution_context.result` entirely with a degraded result if attribute assignment fails on a custom result subclass.
  - [`DjangoErrorPolicyExtension.on_operation`][extensions-error-policy] wraps teardown in top-level `try...except Exception`, ensuring that any runtime crash during teardown safely replaces `execution_context.result` with the degraded fallback.
- **Dual-seam architecture for single-result and streamed operations (spec-048 Decision 11):**
  - Single-result operations (standard queries and mutations executed via `schema.execute` / `execute_sync`): Masked at operation teardown inside [`DjangoErrorPolicyExtension.on_operation`][extensions-error-policy] / [`DjangoErrorPolicyExtension._process_result`][extensions-error-policy].
  - Streamed operations (subscriptions and streamed queries over `graphql-ws` or `graphql-transport-ws` WebSocket protocols): Yielded per event from within the operation lifecycle before operation teardown runs. Masked per-event at the transport result source ([`consumers.py::_stop_aware_results`][consumers]) via [`mask_execution_result`][extensions-error-policy].
  - Non-destructive result copy: [`mask_execution_result`][extensions-error-policy] returns a shallow copy of `ExecutionResult` when errors are replaced, preserving original error objects on `execution_context.result`. This allows upstream extensions (such as [`DjangoDebugExtension`][extensions-debug]) executing in LIFO teardown order to inspect raw `original_error` instances without interference.
  - Idempotent pass-through: If no errors require masking, [`mask_execution_result`][extensions-error-policy] returns the identical `result` instance by reference.
- **Runtime gate and policy resolution (spec-048 Decision 7 & 9):**
  - [`masking_is_active`][extensions-error-policy] evaluates `policy.enabled and settings.DEBUG is not True` per operation, ensuring that development requests under `settings.DEBUG = True` retain full exception details and that malformed truthy strings (e.g. `"False"`) fail closed.
  - [`is_maskable_result`][extensions-error-policy] admits only `graphql.execution.ExecutionResult` and `strawberry.types.execution.ExecutionResult`, excluding unrenderable incremental delivery frames (`@defer` / `@stream`) and early parse/validation returns.
  - [`schema_error_policy`][extensions-error-policy] and [`DjangoErrorPolicyExtension._policy`][extensions-error-policy] retrieve `schema.error_policy` using strict `isinstance(policy, ErrorPolicy)` validation, falling back to [`DEFAULT_ERROR_POLICY`][error-policy] if absent, unreadable, or invalid.
- **Load-bearing extension ordering (spec-048 Decision 10):**
  - [`schema.py::_with_error_policy_extension`][schema] installs [`DjangoErrorPolicyExtension`][extensions-error-policy] at index 0 of `extensions`.
  - Because Strawberry executes `on_operation` teardown hooks in reverse list order (LIFO), index 0 tears down last. This guarantees masking occurs after all diagnostic extensions (such as [`DjangoDebugExtension`][extensions-debug]) have read `original_error`.

Connected behavior examined:
- [`django_strawberry_framework/error_policy.py`][error-policy]: Pure domain model defining `ErrorPolicy` dataclass, `DEFAULT_ERROR_POLICY`, `resolve_error_policy`, and `new_correlation_id`.
- [`django_strawberry_framework/schema.py`][schema]: Automatic installation of `DjangoErrorPolicyExtension` at index 0 via `_with_error_policy_extension` during `DjangoSchema` construction, runtime deduplication of callable factory extensions in `DjangoSchema.get_extensions`.
- [`django_strawberry_framework/consumers.py`][consumers]: WebSocket streaming result source `_stop_aware_results` applying `mask_execution_result` per yielded event under `masking_is_active` and `is_maskable_result`.
- [`django_strawberry_framework/conf.py`][conf]: `error_policy_setting` reading `DJANGO_STRAWBERRY_FRAMEWORK["ERROR_POLICY"]` settings dict.
- [`django_strawberry_framework/extensions/__init__.py`][extensions-init]: Re-exports `DjangoErrorPolicyExtension`.
- [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: Re-exports `DjangoErrorPolicyExtension`, `ErrorPolicy`, `DEFAULT_ERROR_POLICY`, `resolve_error_policy`, `new_correlation_id`.
- [`django_strawberry_framework/extensions/debug.py`][extensions-debug]: `DjangoDebugExtension` reading `original_error` before masking occurs in LIFO unwind order.
- [`django_strawberry_framework/exceptions.py`][exceptions]: `ConfigurationError` and `describe_value`.
- [`django_strawberry_framework/views.py`][views]: `DjangoGraphQLView` and `AsyncDjangoGraphQLView` executing GraphQL requests.
- [`tests/test_error_policy.py`][test-error-policy]: Comprehensive unit test suite covering construction, validation, precedence ladder, correlation ID, install position, fallback, teardown no-ops, fail-closed degrades, and copy contract.
- [`examples/fakeshop/test_query/test_error_policy_api.py`][test-fakeshop-error-policy-api]: Live HTTP acceptance tests covering the 3-column category matrix, completion phase errors, correlation ID uniqueness, logging verification, and `DEBUG` pass-through over `django.test.Client`.
- [`tests/test_routers.py`][test-routers]: WebSocket subscription tests verifying per-event error masking.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/extensions/error_policy.py --include-constants`):
- Parsed 1 target file, 362 lines, 12 definitions:
  - 8 standalone functions: [`_is_unexpected`][extensions-error-policy], [`_masked`][extensions-error-policy], [`_degraded`][extensions-error-policy], [`masking_is_active`][extensions-error-policy], [`is_maskable_result`][extensions-error-policy], [`schema_error_policy`][extensions-error-policy], [`mask_execution_result`][extensions-error-policy], [`_replacement_for`][extensions-error-policy].
  - 1 extension class: [`DjangoErrorPolicyExtension`][extensions-error-policy].
  - 3 methods on [`DjangoErrorPolicyExtension`][extensions-error-policy]: [`DjangoErrorPolicyExtension._policy`][extensions-error-policy], [`DjangoErrorPolicyExtension._process_result`][extensions-error-policy], [`DjangoErrorPolicyExtension.on_operation`][extensions-error-policy].
- Confirmed zero upper-case module constants.
- Verified that all definitions, lifecycle hooks, and error-handling branches are thoroughly exercised across unit tests in [`tests/test_error_policy.py`][test-error-policy], subscription tests in [`tests/test_routers.py`][test-routers], and live HTTP tests in [`examples/fakeshop/test_query/test_error_policy_api.py`][test-fakeshop-error-policy-api].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `DjangoErrorPolicyExtension` and its shared functions (`mask_execution_result`, `is_maskable_result`, `masking_is_active`, `schema_error_policy`) provide the single authoritative error sanitization layer across all GraphQL flavors:
   - Queries and mutations executed synchronously or asynchronously via HTTP views converge on `DjangoErrorPolicyExtension.on_operation` teardown.
   - Subscriptions and streaming queries over WebSocket transports (`graphql-ws` and `graphql-transport-ws`) converge on `consumers.py::_stop_aware_results`, reusing the exact same `mask_execution_result` and `masking_is_active` helpers.
   - Form and serializer mutations (`SerializerMutation`, `DjangoModelFormMutation`) return validation rejections as structured `FieldError` objects in `data` (`data.mutationName.errors`), bypassing `errors` and requiring no redundant masking exceptions.
   - Authorization denies (`mutations/resolvers.py`), GlobalID parsing rejections (`GLOBALID_INVALID`), and resource limit limits (`RESOURCE_LIMIT_EXCEEDED`) raise `GraphQLError` directly, traveling untouched across all execution flavors without flavor-specific adapters.
2. **Sync and async twins:**
   Zero duplication. [`DjangoErrorPolicyExtension.on_operation`][extensions-error-policy] is implemented as a single synchronous generator hook (`yield`). Strawberry executes synchronous generator extensions uniformly across both synchronous (`execute_sync`) and asynchronous (`execute`) operations.
   - Streaming operations in `consumers.py::_stop_aware_results` (an `async` generator) call the exact same synchronous functions [`masking_is_active`][extensions-error-policy], [`is_maskable_result`][extensions-error-policy], and [`mask_execution_result`][extensions-error-policy].
   - Async pre-execution errors (e.g. `PreExecutionError` instances carrying validation errors) and synchronous validation errors both produce `original_error is None`, which [`_is_unexpected`][extensions-error-policy] correctly classifies as non-masked client-side validation errors across both execution colors.
3. **Derived rather than repeated knowledge:**
   - Policy model: [`error_policy.py::ErrorPolicy`][error-policy] is the single definition of policy fields, defaults, and validation invariants.
   - Active state gating: [`masking_is_active`][extensions-error-policy] is the single source of truth for `policy.enabled and settings.DEBUG is not True`. Neither the extension teardown nor the consumer result source duplicates this boolean evaluation.
   - Result shape validation: [`is_maskable_result`][extensions-error-policy] is the single source of truth for admitted execution result types (`GraphQLExecutionResult`, `StrawberryExecutionResult`).
   - Correlation IDs: Generated via [`error_policy.py::new_correlation_id`][error-policy] (`uuid.uuid4().hex`), never re-implemented or derived from request metadata.
   - Default fallback: [`error_policy.py::DEFAULT_ERROR_POLICY`][error-policy] is the authoritative fallback when `schema.error_policy` is absent or invalid.
4. **Inverse and round-trip pairs:**
   - Wire sanitization and server logging: [`_masked`][extensions-error-policy] strips internal exception details and replaces them with a client-safe `GraphQLError` containing `correlation_id` in `extensions[policy.correlation_extension_key]`, while logging the full exception traceback server-side at `ERROR` level tagged with the same `correlation_id`. This creates a deterministic diagnostic pair between client reports and server logs.
   - Shallow copy vs engine context: [`mask_execution_result`][extensions-error-policy] returns a shallow copy of `ExecutionResult` with masked errors, keeping the original unmasked `GraphQLError` objects on `execution_context.result`. This allows upstream extensions (such as [`DjangoDebugExtension`][extensions-debug]) executing in LIFO teardown order to inspect raw exceptions before [`DjangoErrorPolicyExtension._process_result`][extensions-error-policy] applies the masked fields.
5. **Contracts restated in another medium:**
   The error policy contract, structural classification rules, correlation ID tagging, fail-closed degrades, and extension ordering are codified across:
   - Code: [`django_strawberry_framework/extensions/error_policy.py`][extensions-error-policy], [`django_strawberry_framework/error_policy.py`][error-policy], [`django_strawberry_framework/schema.py`][schema], [`django_strawberry_framework/consumers.py`][consumers], [`django_strawberry_framework/conf.py`][conf], [`django_strawberry_framework/extensions/__init__.py`][extensions-init], [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init];
   - Specifications: [`docs/SPECS/spec-048-secure_output_defaults-0_0_14.md`][spec-048] (Decisions 7–11, 13);
   - Test suites: [`tests/test_error_policy.py`][test-error-policy], [`examples/fakeshop/test_query/test_error_policy_api.py`][test-fakeshop-error-policy-api], [`tests/test_routers.py`][test-routers];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`GOAL.md`][goal].

### The single-edit-site test

- **Posited change 1 (Modifying the structural exception classification rule):** Alter which errors are classified as unexpected (e.g. admitting a new deliberate exception base class without masking).
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/error_policy.py::_is_unexpected`][extensions-error-policy].
  - *Site count:* 1.
- **Posited change 2 (Changing the fail-closed fallback message for unreadable error policies):** Modify the fallback message used when a degraded policy lacks a readable `message` attribute.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/error_policy.py::_degraded`][extensions-error-policy].
  - *Site count:* 1.
- **Posited change 3 (Modifying the active masking condition):** Change the runtime gate determining when masking is active across all operation types (queries, mutations, subscriptions).
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/error_policy.py::masking_is_active`][extensions-error-policy].
  - *Site count:* 1.
- **Posited change 4 (Admitting a new execution result shape):** Add support for a new execution result class introduced by a future GraphQL engine release.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/error_policy.py::is_maskable_result`][extensions-error-policy].
  - *Site count:* 1.
- **Posited change 5 (Adjusting error replacement metadata fields):** Add or modify fields copied from the original error to the masked `GraphQLError` (e.g. attaching extra debugging metadata).
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/error_policy.py::_masked`][extensions-error-policy].
  - *Site count:* 1.

### Rejected candidates

1. **Allowlisting error codes via `extensions.code` vs structural classification:**
   - Disproved in [spec-048][spec-048] Decision 8. An allowlist of error codes fails OPEN when a developer adds a new rejection site and forgets to register the code, leaking unhandled exceptions to clients. The structural classification (`original_error is None` or `isinstance(original_error, GraphQLError)`) fails CLOSED by treating any plain Python exception as unexpected while preserving deliberate GraphQL framework and consumer rejections.
2. **Merging `extensions/error_policy.py` into `error_policy.py`:**
   - Disproved. `error_policy.py` is the pure configuration and domain model (`ErrorPolicy`, `DEFAULT_ERROR_POLICY`, `resolve_error_policy`, `new_correlation_id`), with zero dependency on Strawberry schema extensions, AST nodes, or execution results. `extensions/error_policy.py` is the Strawberry runtime integration layer. Separating them keeps configuration lightweight and avoids importing engine execution machinery during schema settings resolution.
3. **Masking in-place in `mask_execution_result` vs returning a shallow copy:**
   - Disproved in [spec-048][spec-048] Decision 11. In-place modification of `result.errors` on streamed subscription events would mutate the underlying `execution_context.result` before other extensions (such as `DjangoDebugExtension`) have executed their teardown hooks, silently clearing exception diagnostics. Returning a shallow copy preserves the engine's original error objects for upstream extension inspection while sending sanitized errors down the wire.
4. **Mutating `GraphQLError` in place in `_masked` instead of instantiating a fresh `GraphQLError`:**
   - Disproved in [spec-048][spec-048] Decision 9. A mutated `GraphQLError` could still be referenced by upstream resolver frames or logging handlers. Constructing a fresh `GraphQLError` with explicit fields ensures `original_error=None` cannot leak exception instances to subsequent handlers or serializers.
5. **Masking at the Django view layer instead of SchemaExtension + transport result source:**
   - Disproved in [spec-048][spec-048] Decisions 10 & 11. View-level masking cannot protect WebSocket streaming transports (subscriptions and streamed queries over `graphql-ws`/`graphql-transport-ws`), nor does it run within the engine's LIFO extension teardown order. Placing masking in `SchemaExtension.on_operation` and `consumers.py::_stop_aware_results` provides uniform protection across all HTTP and WebSocket transports.

## Opportunities

None — `django_strawberry_framework/extensions/error_policy.py` is a clean, 362-line, self-contained implementation. It cleanly encapsulates structural error classification, client-safe error masking, multi-tiered fail-closed degradation, correlation ID logging, and dual-seam execution with zero duplicate logic and zero unowned state.

## Judgment

Zero-edit review. `extensions/error_policy.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. Target file is clean and fully consolidated at root owners. Verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/extensions/error_policy.py --review docs/dry/dry-file-extensions__error_policy.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independently reviewed and verified Worker 1's DRY analysis of [`django_strawberry_framework/extensions/error_policy.py`][extensions-error-policy]:

1. **Error policy boundary and contract verification:**
   - Re-traced the error classification and sanitization pipeline across [`django_strawberry_framework/extensions/error_policy.py`][extensions-error-policy], [`django_strawberry_framework/error_policy.py`][error-policy], [`django_strawberry_framework/schema.py`][schema], [`django_strawberry_framework/consumers.py`][consumers], and [`django_strawberry_framework/extensions/debug.py`][extensions-debug].
   - Validated that [`_is_unexpected`][extensions-error-policy] structurally classifies errors without error-code allowlists, correctly preserving GraphQL parse/validation errors (`original_error is None`) and deliberate domain/framework rejections (`isinstance(original_error, GraphQLError)`), while masking all escaping plain Python exceptions.
   - Validated that [`mask_execution_result`][extensions-error-policy] returns shallow copies when masking errors, preserving unmasked `original_error` objects on `execution_context.result` for upstream extensions executing in LIFO teardown order (specifically [`DjangoDebugExtension`][extensions-debug]).
   - Verified the dual-seam design: single-result operations are masked at operation teardown in [`DjangoErrorPolicyExtension.on_operation`][extensions-error-policy], while streaming transport results (WebSocket subscriptions and streamed queries) are masked per-event at [`consumers.py::_stop_aware_results`][consumers] using the identical shared [`mask_execution_result`][extensions-error-policy] and [`masking_is_active`][extensions-error-policy] functions.
   - Verified multi-tiered fail-closed degradation: all failure modes across classification, masking, and attribute adoption log full server-side tracebacks and degrade to neutral, client-safe error payloads without disclosing server internals or unvalidated data.

2. **Probing matrix & single-edit-site verification:**
   - Verified that all 5 axes of the mandatory probing matrix are fully discharged with concrete evidence.
   - Verified single-edit-site counts across all 5 posited change scenarios; each change requires modifying exactly 1 authoritative site.

3. **Coverage & test validation:**
   - Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/extensions/error_policy.py --review docs/dry/dry-file-extensions__error_policy.md --include-constants`: confirmed all 12 target definitions are covered.
   - Ran test suite across [`tests/test_error_policy.py`][test-error-policy], [`tests/test_routers.py`][test-routers], and [`examples/fakeshop/test_query/test_error_policy_api.py`][test-fakeshop-error-policy-api]: all 240 tests passed with 100% coverage on the target file.

Confirmed zero-edit review. Updated `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../GOAL.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-044]: ../SPECS/spec-044-debug_extension-0_0_14.md
[spec-047]: ../SPECS/spec-047-resource_policy-0_0_14.md
[spec-048]: ../SPECS/spec-048-secure_output_defaults-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[consumers]: ../../django_strawberry_framework/consumers.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[error-policy]: ../../django_strawberry_framework/error_policy.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[extensions-debug]: ../../django_strawberry_framework/extensions/debug.py
[extensions-error-policy]: ../../django_strawberry_framework/extensions/error_policy.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[extensions-resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[schema]: ../../django_strawberry_framework/schema.py
[views]: ../../django_strawberry_framework/views.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-error-policy]: ../../tests/test_error_policy.py
[test-extensions-debug]: ../../tests/extensions/test_debug.py
[test-resource-policy]: ../../tests/test_resource_policy.py
[test-routers]: ../../tests/test_routers.py

<!-- examples/ -->
[test-fakeshop-error-policy-api]: ../../examples/fakeshop/test_query/test_error_policy_api.py

<!-- scripts/ -->

<!-- .venv/ -->
[strawberry-extension]: ../../.venv/lib/python3.14/site-packages/strawberry/extensions/base_extension.py

<!-- External -->
