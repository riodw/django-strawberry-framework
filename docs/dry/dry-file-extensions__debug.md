# DRY review: `django_strawberry_framework/extensions/debug.py`

Status: verified

## System trace

`django_strawberry_framework/extensions/debug.py` is the framework's in-response GraphQL debug and diagnostic subsystem ([spec-044][spec-044], [spec-048][spec-048]). It defines [`DjangoDebugExtension`][extensions-debug], a Strawberry [`SchemaExtension`][strawberry-extension] that captures Django-recorded query-log SQL statements and execution exceptions for the in-flight GraphQL operation and attaches them to `response.extensions["debug"]`. This provides the in-response counterpart to the server-side debug-toolbar middleware ([`middleware/debug_toolbar.py`][middleware-debug-toolbar]), porting the debugging capabilities of `graphene-django`'s `DjangoDebug` subsystem (`DjangoDebugMiddleware` / `_debug` field) into the engine's native response-extensions seam.

The module owns the following core responsibilities:

- **Fail-closed security gate under non-debug deployments (spec-048 Decision 5):**
  [`DjangoDebugExtension`][extensions-debug] is off by default and fails closed when `settings.DEBUG` is not `True`. In [`DjangoDebugExtension.__init__`][extensions-debug], the `allow_unsafe_production` parameter defaults to `False`. The constructor validates `isinstance(allow_unsafe_production, bool)`, rejecting truthy non-booleans with [`exceptions.py::ConfigurationError`][exceptions] (using [`exceptions.py::describe_value`][exceptions]) so that environment variable strings (e.g. `"0"`, `"false"`) cannot accidentally arm the production disclosure. In [`DjangoDebugExtension._disclosure_permitted`][extensions-debug], the extension evaluates `self.allow_unsafe_production or settings.DEBUG is True` per operation. When disclosure is refused, [`DjangoDebugExtension.on_operation`][extensions-debug] logs a warning and yields without acquiring cursor brackets or building payloads, ensuring [`DjangoDebugExtension.get_results`][extensions-debug] returns `{}`. The request execution itself is not interrupted.
- **Reference-counted, overlap-safe cursor coordinator:**
  The module defines [`_ActiveCapture`][extensions-debug] (frozen dataclass tracking `saved_force_debug_cursor` and `depth`), [`_CaptureToken`][extensions-debug] (frozen dataclass holding `database_connection`), and [`_CursorCaptureCoordinator`][extensions-debug]. The coordinator manages bracketed database connections across operations without global flag corruption. In [`_CursorCaptureCoordinator.__init__`][extensions-debug], a threading lock (`self._lock`) and an active map (`self._active`) are initialized. In [`_CursorCaptureCoordinator.acquire`][extensions-debug], the coordinator keys on the concrete `BaseDatabaseWrapper` instance identity, saves the initial `connection.force_debug_cursor`, sets `force_debug_cursor = True`, and increments `depth`. In [`_CursorCaptureCoordinator.release`][extensions-debug], `depth` is decremented; when depth reaches 0, the exact saved flag is restored and the connection is removed from `_active`.
- **Query log snapshotting and extraction:**
  [`_ConnectionSnapshot`][extensions-debug] captures a `BaseDatabaseWrapper` reference and `query_log_start` integer. [`_query_log_entries_since`][extensions-debug] materializes the connection's bounded deque (`queries_log`) and slices from `snapshot.query_log_start`, tolerating resets (`reset_queries()`) and handling bounded rollover gracefully.
- **SQL serialization and graphene wire compatibility:**
  [`_DebugSQLRow`][extensions-debug] defines the wire schema (`vendor`, `alias`, `sql`, `duration`, `isSlow`, `isSelect`). [`_serialize_sql_row`][extensions-debug] formats each query-log entry into these exact literals. Constant [`_SLOW_QUERY_SECONDS`][extensions-debug] (`10`) defines the slow-query threshold for `isSlow = duration > _SLOW_QUERY_SECONDS`. `isSelect` is derived directly via `sql.lower().strip().startswith("select")`.
- **Exception chain unwrapping and serialization:**
  [`_DebugExceptionRow`][extensions-debug] defines the exception wire schema (`excType`, `message`, `stack`). Constant [`_MAX_ORIGINAL_ERROR_HOPS`][extensions-debug] (`64`) bounds the unwrapping depth for nested `GraphQLError.original_error` chains. [`_terminal_original_error`][extensions-debug] walks the `original_error` chain using identity cycle detection and the hop ceiling, returning the terminal exception without failing the response. [`_serialize_exception`][extensions-debug] formats the exception type, string message, and traceback using `traceback.format_exception(type(e), e, e.__traceback__)`. [`_collect_exceptions`][extensions-debug] filters `execution_result.errors` for items with non-None `original_error` and serializes the terminal exceptions.
- **Deterministic payload bounding and caps (spec-048 Decision 6):**
  Constants [`_MAX_SQL_ROWS`][extensions-debug] (`100`), [`_MAX_EXCEPTION_ROWS`][extensions-debug] (`25`), [`_MAX_SQL_TEXT_CHARS`][extensions-debug] (`4096`), [`_MAX_EXCEPTION_MESSAGE_CHARS`][extensions-debug] (`4096`), [`_MAX_EXCEPTION_STACK_CHARS`][extensions-debug] (`16384`), and [`_MAX_PAYLOAD_TEXT_CHARS`][extensions-debug] (`262144`) define immutable response budgets. Constant [`_TRUNCATION_MARKER`][extensions-debug] (`"... [truncated]"`) marks truncated strings. [`_truncate`][extensions-debug] trims text exceeding character limits. [`_row_cost`][extensions-debug] sums the character lengths of string values in a row. [`_apply_payload_caps`][extensions-debug] processes rows in three deterministic passes: (1) per-row string truncation, (2) row-count bounding preserving earliest rows, and (3) shared text budget allocation admitting exception rows first, then SQL rows until `_MAX_PAYLOAD_TEXT_CHARS` is reached.
- **Robust assembly and independent degradation:**
  [`_DebugPayload`][extensions-debug] defines the payload structure (`sql: list[_DebugSQLRow]`, `exceptions: list[_DebugExceptionRow]`). [`_build_payload`][extensions-debug] coordinates SQL and exception collection in independent `try...except Exception` blocks, degrading SQL to partial rows collected so far and exceptions to `[]` on error while logging warnings server-side.
- **SchemaExtension lifecycle and engine integration:**
  [`DjangoDebugExtension`][extensions-debug] class defines `_payload = None` as class-level sentinel. In [`DjangoDebugExtension.on_operation`][extensions-debug], pre-yield logic validates `_disclosure_permitted()` and uses `ExitStack` to acquire bracket tokens across `connections.all()`. Post-yield inside `finally`, if `self.execution_context.result` is an instance of `GraphQLExecutionResult`, `_build_payload` assigns `self._payload`. Sync parse/validation errors leave `result` as `None` and async pre-execution errors produce `PreExecutionError`, neither of which populates `_payload`. [`DjangoDebugExtension.get_results`][extensions-debug] returns `{"debug": self._payload}` if `self._payload` is present, else `{}`.

Connected behavior examined:
- [`django_strawberry_framework/extensions/__init__.py`][extensions-init]: Re-exports `DjangoDebugExtension`, `DjangoErrorPolicyExtension`, and `DjangoResourcePolicyExtension`.
- [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: Deliberately excludes `DjangoDebugExtension` from root exports ([spec-044][spec-044] Decision 11) to avoid accidental production exposure.
- [`django_strawberry_framework/extensions/error_policy.py`][extensions-error-policy]: `DjangoErrorPolicyExtension` sanitizes execution errors into stable correlation codes. Documented to run before `DjangoDebugExtension` in `extensions=[...]` so LIFO teardown allows `DjangoDebugExtension` to read raw `original_error` objects before masking.
- [`django_strawberry_framework/extensions/resource_policy.py`][extensions-resource-policy]: Pre-parse and AST validation limits.
- [`django_strawberry_framework/middleware/debug_toolbar.py`][middleware-debug-toolbar]: Sibling server-side HTML/JSON debug toolbar middleware for `django-debug-toolbar`.
- [`django_strawberry_framework/exceptions.py`][exceptions]: `ConfigurationError` and `describe_value`.
- [`django_strawberry_framework/schema.py`][schema]: `DjangoSchema` extension ordering and automatic installation of default policy extensions.
- [`tests/extensions/test_debug.py`][test-extensions-debug]: Comprehensive 1215-line test suite verifying serialization, cursor refcounting, fail-closed gates, concurrency, caps, and ordering.
- [`examples/fakeshop/test_query/test_debug_extension_api.py`][test-fakeshop-debug-api]: Live HTTP tests verifying in-response debug payloads via probe URLconfs.
- [`examples/fakeshop/test_query/test_multi_db.py`][test-fakeshop-multi-db]: Multi-database query capture across connection aliases.
- [`tests/base/test_init.py`][test-base-init]: Packaging boundary verification.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/extensions/debug.py --include-constants`):
- Parsed 1 target file, 677 lines, 33 definitions:
  - 9 constants: [`_SLOW_QUERY_SECONDS`][extensions-debug], [`_MAX_ORIGINAL_ERROR_HOPS`][extensions-debug], [`_MAX_SQL_ROWS`][extensions-debug], [`_MAX_EXCEPTION_ROWS`][extensions-debug], [`_MAX_SQL_TEXT_CHARS`][extensions-debug], [`_MAX_EXCEPTION_MESSAGE_CHARS`][extensions-debug], [`_MAX_EXCEPTION_STACK_CHARS`][extensions-debug], [`_MAX_PAYLOAD_TEXT_CHARS`][extensions-debug], [`_TRUNCATION_MARKER`][extensions-debug].
  - 7 classes / typed records: [`_DebugSQLRow`][extensions-debug], [`_DebugExceptionRow`][extensions-debug], [`_DebugPayload`][extensions-debug], [`_CaptureToken`][extensions-debug], [`_ConnectionSnapshot`][extensions-debug], [`_ActiveCapture`][extensions-debug], [`_CursorCaptureCoordinator`][extensions-debug].
  - 3 methods on [`_CursorCaptureCoordinator`][extensions-debug]: [`_CursorCaptureCoordinator.__init__`][extensions-debug], [`_CursorCaptureCoordinator.acquire`][extensions-debug], [`_CursorCaptureCoordinator.release`][extensions-debug].
  - 9 standalone functions: [`_serialize_sql_row`][extensions-debug], [`_serialize_exception`][extensions-debug], [`_terminal_original_error`][extensions-debug], [`_collect_exceptions`][extensions-debug], [`_query_log_entries_since`][extensions-debug], [`_truncate`][extensions-debug], [`_row_cost`][extensions-debug], [`_apply_payload_caps`][extensions-debug], [`_build_payload`][extensions-debug].
  - 1 extension class: [`DjangoDebugExtension`][extensions-debug].
  - 4 methods on [`DjangoDebugExtension`][extensions-debug]: [`DjangoDebugExtension.__init__`][extensions-debug], [`DjangoDebugExtension._disclosure_permitted`][extensions-debug], [`DjangoDebugExtension.on_operation`][extensions-debug], [`DjangoDebugExtension.get_results`][extensions-debug].
- Verified that all definitions, lifecycle hooks, and error handling paths are exercised across `tests/extensions/test_debug.py` and live fakeshop suites.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `DjangoDebugExtension` is a generic Strawberry [`SchemaExtension`][strawberry-extension] applicable to any GraphQL schema configuration. It works identically for plain `strawberry.Schema` and `DjangoSchema` instances. Unlike Django REST Framework (which lacks an in-response SQL debugging envelope) or `graphene-django` (which relied on stacked field decorators and resolver middleware), `django-strawberry-framework` models debug introspection purely as an engine-native `SchemaExtension` passed in `extensions=[...]`. No resolver-level wrapping, field AST mutation, or duplicate flavor-specific adapters exist.
2. **Sync and async twins:**
   Zero duplication. [`DjangoDebugExtension.on_operation`][extensions-debug] is implemented as a single synchronous generator hook (`yield` within `with ExitStack()`). Strawberry executes synchronous generator extensions uniformly across both synchronous (`execute_sync`) and asynchronous (`execute`) operations.
   - Exception capture is completely color-agnostic: `execution_context.result.errors` contains all GraphQL execution errors regardless of execution color.
   - SQL capture across colors: In sync execution, database queries execute on the same thread as the extension bracket, capturing all ORM operations. In async execution, Django ORM operations dispatched via `sync_to_async` execute on worker threads with separate thread-local connection state; as documented in [spec-044][spec-044], event-loop brackets safely restore flags without cross-thread interference, returning an empty `sql` list as expected.
   - Concurrency safety: [`_CursorCaptureCoordinator`][extensions-debug] protects state transitions with `threading.Lock()`, ensuring that overlapping operations across sync threads or async tasks increment depth safely and restore exact flags without race conditions.
3. **Derived rather than repeated knowledge:**
   - Wire contract alignment: Graphene wire dictionary keys (`vendor`, `alias`, `sql`, `duration`, `isSlow`, `isSelect`, `excType`, `message`, `stack`) are explicit literals preserving client compatibility.
   - Derived metrics: `isSlow` is computed directly from `duration > _SLOW_QUERY_SECONDS` (10-second threshold); `isSelect` is derived directly via `sql.lower().strip().startswith("select")`.
   - String truncation: [`_truncate`][extensions-debug] is the single source of truth for string truncation and suffixing with [`_TRUNCATION_MARKER`][extensions-debug].
   - Text budgeting: [`_row_cost`][extensions-debug] computes character size dynamically by summing `isinstance(value, str)` lengths across dictionary values, ensuring consistent budgeting for both SQL and exception rows.
   - Cap constants: Module constants ([`_MAX_SQL_ROWS`][extensions-debug], [`_MAX_EXCEPTION_ROWS`][extensions-debug], [`_MAX_SQL_TEXT_CHARS`][extensions-debug], [`_MAX_EXCEPTION_MESSAGE_CHARS`][extensions-debug], [`_MAX_EXCEPTION_STACK_CHARS`][extensions-debug], [`_MAX_PAYLOAD_TEXT_CHARS`][extensions-debug]) define non-configurable package invariants (spec-048 Decision 6).
   - Unwrapping ceiling: [`_MAX_ORIGINAL_ERROR_HOPS`][extensions-debug] (`64`) is defined locally because its failure policy (best-effort return of the last candidate) differs from [`utils/typing.py::_MAX_TYPE_WRAPPER_DEPTH`][utils-typing] (which raises `TypeError`).
4. **Inverse and round-trip pairs:**
   - Bracket acquire and release: [`_CursorCaptureCoordinator.acquire`][extensions-debug] saves initial state and increments depth; [`_CursorCaptureCoordinator.release`][extensions-debug] decrements depth and restores exact initial state on final release. In [`DjangoDebugExtension.on_operation`][extensions-debug], `stack.callback(_coordinator.release, token)` guarantees that every acquired connection is released via `ExitStack` unwinding, even if subsequent acquisitions or operation yields raise exceptions.
   - Payload state lifecycle: [`DjangoDebugExtension`][extensions-debug] defines `_payload = None` as an immutable class default. Instances shadow `self._payload` upon successful completion of `on_operation` teardown. [`DjangoDebugExtension.get_results`][extensions-debug] performs a pure, idempotent read of `self._payload` without mutating or popping state.
5. **Contracts restated in another medium:**
   The debug payload shape, fail-closed security posture, payload caps, and cursor coordinator lifecycle are codified across:
   - Code: [`django_strawberry_framework/extensions/debug.py`][extensions-debug], [`django_strawberry_framework/extensions/__init__.py`][extensions-init], [`django_strawberry_framework/extensions/error_policy.py`][extensions-error-policy], [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init];
   - Specifications: [`docs/SPECS/spec-044-debug_extension-0_0_14.md`][spec-044] (Decisions 1–12), [`docs/SPECS/spec-048-secure_output_defaults-0_0_14.md`][spec-048] (Decisions 5, 6);
   - Test suites: [`tests/extensions/test_debug.py`][test-extensions-debug], [`examples/fakeshop/test_query/test_debug_extension_api.py`][test-fakeshop-debug-api], [`examples/fakeshop/test_query/test_multi_db.py`][test-fakeshop-multi-db], [`tests/base/test_init.py`][test-base-init];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`GOAL.md`][goal].

### The single-edit-site test

- **Posited change 1 (Modifying the slow-query threshold):** Change the duration threshold at which queries are flagged as slow (e.g. from 10s to 5s).
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/debug.py::_SLOW_QUERY_SECONDS`][extensions-debug].
  - *Site count:* 1.
- **Posited change 2 (Adjusting payload budget caps or per-row limits):** Increase the maximum allowed SQL rows or payload text budget.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/debug.py`][extensions-debug] (the respective module constants [`_MAX_SQL_ROWS`][extensions-debug] or [`_MAX_PAYLOAD_TEXT_CHARS`][extensions-debug]).
  - *Site count:* 1.
- **Posited change 3 (Modifying the truncation marker):** Change the suffix marker appended to truncated strings.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/debug.py::_TRUNCATION_MARKER`][extensions-debug].
  - *Site count:* 1.
- **Posited change 4 (Adjusting the nested original error hop ceiling):** Increase or decrease the maximum allowed depth for unwrapping nested `GraphQLError.original_error` instances.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/debug.py::_MAX_ORIGINAL_ERROR_HOPS`][extensions-debug].
  - *Site count:* 1.
- **Posited change 5 (Modifying wire payload field keys):** Alter the wire schema field names in SQL or exception dictionary outputs.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/debug.py`][extensions-debug] ([`_DebugSQLRow`][extensions-debug] / [`_serialize_sql_row`][extensions-debug] or [`_DebugExceptionRow`][extensions-debug] / [`_serialize_exception`][extensions-debug]).
  - *Site count:* 1.

### Rejected candidates

1. **Unifying `_MAX_ORIGINAL_ERROR_HOPS` with `utils/typing.py::_MAX_TYPE_WRAPPER_DEPTH`:**
   - Disproved. While both constants define recursion depth ceilings (`64`), their failure policies are fundamentally different. `utils/typing.py` raises `TypeError` when unwrapping type annotations exceeds the ceiling (fail-loud at schema build time). `extensions/debug.py` terminates traversal and returns the best-effort terminal exception candidate so that unexpected runtime exception cycles never crash the GraphQL response (fail-safe at runtime). Keeping `_MAX_ORIGINAL_ERROR_HOPS` local in `debug.py` correctly decouples runtime diagnostic degradation from type reflection bounds.
2. **Subclassing `django.test.utils.CaptureQueriesContext` for cursor management:**
   - Disproved. `CaptureQueriesContext` in Django is designed for test context managers; it mutates `force_debug_cursor` without concurrency locks, assumes sequential single-threaded test execution, and does not support overlapping multi-operation async execution. [`_CursorCaptureCoordinator`][extensions-debug] provides thread-safe, lock-protected, reference-counted bracket management keyed on concrete wrapper identity.
3. **Global per-process debug cursor enablement:**
   - Disproved. Globally setting `force_debug_cursor = True` across worker processes introduces query logging overhead for all requests and risks leaking connection query logs across unrelated tenants. Scoping brackets strictly to operation lifecycle via `ExitStack` is necessary for security and memory isolation.
4. **Deriving wire dictionary keys dynamically via case conversion helpers:**
   - Disproved. The wire contract keys (`vendor`, `alias`, `sql`, `duration`, `isSlow`, `isSelect`, `excType`, `message`, `stack`) are fixed graphene-compatible literals. Deriving them dynamically through camel-case utility functions adds unnecessary runtime overhead and risks unintentional schema changes if casing rules evolve.
5. **Re-exporting `DjangoDebugExtension` from package root `django_strawberry_framework/__init__.py`:**
   - Disproved. Deliberately rejected by [spec-044][spec-044] Decision 11 and verified by [`tests/base/test_init.py`][test-base-init]. `DjangoDebugExtension` exposes unmasked tracebacks and interpolated SQL. Requiring explicit import from `django_strawberry_framework.extensions` provides a visible boundary ensuring developers do not inadvertently install it in production schemas.

## Opportunities

None — `django_strawberry_framework/extensions/debug.py` is a clean, 677-line, self-contained implementation. It cleanly encapsulates cursor bracket coordination, query-log slicing, error unwrapping, deterministic payload bounding, and fail-closed security gating with zero duplicate logic and zero unowned state.

## Judgment

Zero-edit review. `extensions/debug.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. Target file is clean and fully consolidated at root owners. Verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/extensions/debug.py --review docs/dry/dry-file-extensions__debug.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Worker 2 independently analyzed [`django_strawberry_framework/extensions/debug.py`][extensions-debug] and verified the findings recorded by Worker 1:

1. **Security Gate and Validation (spec-048 Decision 5):**
   - Verified that [`DjangoDebugExtension.__init__`][extensions-debug] enforces strict boolean type validation on `allow_unsafe_production` via `isinstance(allow_unsafe_production, bool)`, failing with [`ConfigurationError`][exceptions] (using [`describe_value`][exceptions]) on truthy strings (e.g., `"false"`, `"0"`).
   - Confirmed [`DjangoDebugExtension._disclosure_permitted`][extensions-debug] evaluates `self.allow_unsafe_production or settings.DEBUG is True` per operation.
   - Confirmed [`DjangoDebugExtension.on_operation`][extensions-debug] fails closed when disclosure is prohibited: logs a warning, skips cursor acquisition, snapshots no queries, and yields pre-bracket so that [`DjangoDebugExtension.get_results`][extensions-debug] returns `{}` while the GraphQL operation executes unimpeded.

2. **Concurrency-Safe Cursor Capture Coordinator:**
   - Verified that [`_CursorCaptureCoordinator`][extensions-debug] is keyed on concrete `BaseDatabaseWrapper` instance identities under `threading.Lock()`, maintaining immutable [`_ActiveCapture`][extensions-debug] records tracking `saved_force_debug_cursor` and active nesting `depth`.
   - Confirmed that [`DjangoDebugExtension.on_operation`][extensions-debug] manages cursor acquisition across `connections.all()` inside an `ExitStack`, guaranteeing that all bracketed tokens are safely released via `stack.callback(_coordinator.release, token)` on normal exit or early exception.
   - Verified that the final overlapping release restores the exact saved `force_debug_cursor` flag, correctly preserving enclosing capture contexts.

3. **Query Log Slicing and SQL Serialization:**
   - Confirmed [`_query_log_entries_since`][extensions-debug] materializes the connection's `queries_log` deque and slices from `snapshot.query_log_start`, tolerating `reset_queries()` resets.
   - Confirmed [`_serialize_sql_row`][extensions-debug] formats query entries into graphene-compatible literals (`vendor`, `alias`, `sql`, `duration`, `isSlow`, `isSelect`), computing `isSlow` via `duration > _SLOW_QUERY_SECONDS` (10s) and `isSelect` via SQL prefix.

4. **Exception Unwrapping and Serialization:**
   - Verified that [`_terminal_original_error`][extensions-debug] traverses nested `GraphQLError.original_error` chains with cycle identity tracking and bounded by [`_MAX_ORIGINAL_ERROR_HOPS`][extensions-debug] (`64`), deterministically returning terminal exceptions without failing the GraphQL operation.
   - Confirmed [`_serialize_exception`][extensions-debug] explicitly formats exception type, message, and traceback from `exception.__traceback__` using `traceback.format_exception`, preserving diagnostic information after graphql-core ambient exception state clears.
   - Confirmed [`_collect_exceptions`][extensions-debug] filters for execution errors having non-None `original_error`.

5. **Deterministic Payload Bounding and Independent Degradation (spec-048 Decision 6):**
   - Verified 3-pass deterministic bounding in [`_apply_payload_caps`][extensions-debug]: (1) string truncation via [`_truncate`][extensions-debug] with [`_TRUNCATION_MARKER`][extensions-debug] against [`_MAX_SQL_TEXT_CHARS`][extensions-debug] (`4096`), [`_MAX_EXCEPTION_MESSAGE_CHARS`][extensions-debug] (`4096`), and [`_MAX_EXCEPTION_STACK_CHARS`][extensions-debug] (`16384`); (2) row-count bounding preserving earliest rows via [`_MAX_SQL_ROWS`][extensions-debug] (`100`) and [`_MAX_EXCEPTION_ROWS`][extensions-debug] (`25`); (3) shared text budget allocation via [`_MAX_PAYLOAD_TEXT_CHARS`][extensions-debug] (`262144`) prioritizing whole exception rows before whole SQL rows.
   - Confirmed that [`_build_payload`][extensions-debug] isolates SQL and exception collection in independent `try...except Exception` blocks, degrading SQL to partial rows serialized so far and exceptions to `[]` on error.

6. **SchemaExtension Lifecycle and Idempotence:**
   - Confirmed class-level default `_payload = None` is shadowed on the instance only upon completing execution teardown when `execution_context.result` is an instance of `GraphQLExecutionResult`.
   - Verified that parse/validation early-returns leave `_payload` as `None`, ensuring unexecuted operations publish no `debug` key via [`DjangoDebugExtension.get_results`][extensions-debug] returning `{}`.

7. **Probing Matrix, Single-Edit-Site Invariant, and Test Suite:**
   - Verified that all 5 axes of the mandatory duplication matrix are discharged with sound technical justifications.
   - Confirmed that single-edit-site invariants 1–5 hold at count 1.
   - Verified target definitions coverage with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/extensions/debug.py --review docs/dry/dry-file-extensions__debug.md --include-constants` (33 target definitions, 0 missing).
   - Verified test suite: all 76 tests in [`tests/extensions/test_debug.py`][test-extensions-debug], [`examples/fakeshop/test_query/test_debug_extension_api.py`][test-fakeshop-debug-api], and [`examples/fakeshop/test_query/test_multi_db.py`][test-fakeshop-multi-db] pass with 100% statement coverage on `extensions/debug.py`.

Target is confirmed clean, sound, and adhering to all repository DRY principles. Status updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../GOAL.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-044]: ../SPECS/spec-044-debug_extension-0_0_14.md
[spec-048]: ../SPECS/spec-048-secure_output_defaults-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[extensions-debug]: ../../django_strawberry_framework/extensions/debug.py
[extensions-error-policy]: ../../django_strawberry_framework/extensions/error_policy.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[extensions-resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[middleware-debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[schema]: ../../django_strawberry_framework/schema.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-extensions-debug]: ../../tests/extensions/test_debug.py

<!-- examples/ -->
[test-fakeshop-debug-api]: ../../examples/fakeshop/test_query/test_debug_extension_api.py
[test-fakeshop-multi-db]: ../../examples/fakeshop/test_query/test_multi_db.py

<!-- scripts/ -->

<!-- .venv/ -->
[strawberry-extension]: ../../.venv/lib/python3.14/site-packages/strawberry/extensions/base_extension.py

<!-- External -->
