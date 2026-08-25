# DRY review: `django_strawberry_framework/extensions/`

Status: verified

## System trace

`django_strawberry_framework/extensions/` is the schema-level runtime lifecycle and policy enforcement subpackage ([spec-044][spec-044], [spec-047][spec-047], [spec-048][spec-048]). It provides first-party Strawberry [`SchemaExtension`][strawberry-extension] implementations that guard GraphQL schema execution at the request perimeter, sanitize responses, and provide opt-in developer diagnostics across heterogeneous execution transports (Django HTTP, Channels HTTP, Channels WebSocket).

The subpackage comprises four modules whose responsibilities and inter-module boundaries are strictly partitioned:

1. [`extensions/__init__.py`][extensions-init]: The subpackage export facade. Defines `__all__` re-exporting the three first-party schema extensions: [`DjangoDebugExtension`][extensions-debug], [`DjangoErrorPolicyExtension`][extensions-error-policy], and [`DjangoResourcePolicyExtension`][extensions-resource-policy]. It contains zero runtime logic, global state, or helper functions.
2. [`extensions/debug.py`][extensions-debug]: The development-only in-response GraphQL query-log and exception diagnostic subsystem ([spec-044][spec-044], [spec-048][spec-048] Decisions 5, 6):
   - **Fail-closed security gate under non-debug deployments:** [`DjangoDebugExtension`][extensions-debug] is off by default and fails closed when `settings.DEBUG` is not `True`. In [`DjangoDebugExtension.__init__`][extensions-debug], `allow_unsafe_production` defaults to `False` and validates `isinstance(allow_unsafe_production, bool)`, raising [`exceptions.py::ConfigurationError`][exceptions] on truthy non-booleans (via [`exceptions.py::describe_value`][exceptions]). In [`DjangoDebugExtension._disclosure_permitted`][extensions-debug], it evaluates `self.allow_unsafe_production or settings.DEBUG is True` per operation. When disclosure is prohibited, [`DjangoDebugExtension.on_operation`][extensions-debug] logs a warning and yields without acquiring cursor brackets or snapshotting query logs, ensuring [`DjangoDebugExtension.get_results`][extensions-debug] returns `{}`.
   - **Overlap-safe, reference-counted cursor coordinator:** [`_CursorCaptureCoordinator`][extensions-debug] coordinates bracketed database connections across overlapping operations without global flag corruption. In [`_CursorCaptureCoordinator.__init__`][extensions-debug], a lock (`self._lock`) and active map (`self._active`) are initialized. In [`_CursorCaptureCoordinator.acquire`][extensions-debug], the coordinator keys on concrete `BaseDatabaseWrapper` instance identity, creates an immutable [`_ActiveCapture`][extensions-debug] record saving `connection.force_debug_cursor` and setting `depth = 1`, and returns a [`_CaptureToken`][extensions-debug]. Overlapping acquires increment `depth`. In [`_CursorCaptureCoordinator.release`][extensions-debug], `depth` is decremented; when depth reaches 0, the saved flag is restored and the connection is removed from `_active`.
   - **Query log snapshotting and SQL serialization:** [`_ConnectionSnapshot`][extensions-debug] captures a database wrapper and start index. [`_query_log_entries_since`][extensions-debug] slices the connection's bounded `queries_log` deque from `snapshot.query_log_start`, tolerating `reset_queries()` resets. [`_serialize_sql_row`][extensions-debug] formats entries into graphene-compatible [`_DebugSQLRow`][extensions-debug] dictionaries (`vendor`, `alias`, `sql`, `duration`, `isSlow`, `isSelect`), computing `isSlow` via `duration > _SLOW_QUERY_SECONDS` (10s threshold) and `isSelect` via SQL prefix.
   - **Exception chain unwrapping and serialization:** [`_terminal_original_error`][extensions-debug] walks nested `GraphQLError.original_error` chains with cycle identity tracking bounded by [`_MAX_ORIGINAL_ERROR_HOPS`][extensions-debug] (`64`), deterministically returning terminal exceptions. [`_serialize_exception`][extensions-debug] formats [`_DebugExceptionRow`][extensions-debug] entries (`excType`, `message`, `stack`) from `exception.__traceback__` using `traceback.format_exception`. [`_collect_exceptions`][extensions-debug] filters `execution_result.errors` for non-None `original_error` items and serializes them.
   - **Deterministic payload bounding and independent degradation:** Module constants [`_MAX_SQL_ROWS`][extensions-debug] (`100`), [`_MAX_EXCEPTION_ROWS`][extensions-debug] (`25`), [`_MAX_SQL_TEXT_CHARS`][extensions-debug] (`4096`), [`_MAX_EXCEPTION_MESSAGE_CHARS`][extensions-debug] (`4096`), [`_MAX_EXCEPTION_STACK_CHARS`][extensions-debug] (`16384`), [`_MAX_PAYLOAD_TEXT_CHARS`][extensions-debug] (`262144`), and [`_TRUNCATION_MARKER`][extensions-debug] (`"... [truncated]"`) define immutable budgets. [`_truncate`][extensions-debug] trims oversized strings. [`_row_cost`][extensions-debug] sums character lengths of string values in a row. [`_apply_payload_caps`][extensions-debug] enforces 3-pass bounding: (1) string truncation, (2) earliest row preservation, and (3) shared text budget prioritizing exceptions before SQL. [`_build_payload`][extensions-debug] coordinates collection into a [`_DebugPayload`][extensions-debug] map in independent `try...except Exception` blocks, degrading SQL to partial rows and exceptions to `[]` on error.
   - **Packaging isolation:** Deliberately NOT re-exported from the package root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] ([spec-044][spec-044] Decision 11, [`tests/base/test_init.py`][test-base-init]) to avoid accidental production exposure of unmasked tracebacks and interpolated SQL.
3. [`extensions/error_policy.py`][extensions-error-policy]: The execution-phase and streaming-transport enforcement engine for `ErrorPolicy` ([spec-048][spec-048] Decisions 7–11, 13):
   - **Structural error classification:** [`_is_unexpected`][extensions-error-policy] inspects error objects structurally: non-`GraphQLError` objects and plain Python exceptions escaping resolvers or value completion phases (`located_error` unwrapping) are classified as unexpected and masked; parse/syntax errors (`original_error is None`) and deliberate GraphQL domain rejections (`isinstance(original_error, GraphQLError)`) travel untouched.
   - **Client-safe error masking and correlation tagging:** [`_masked`][extensions-error-policy] mints a 32-character hexadecimal correlation ID via [`error_policy.py::new_correlation_id`][error-policy], logs the unhandled exception server-side at `ERROR` level with `exc_info` and the correlation ID, and returns a fresh `GraphQLError` carrying `policy.message`, preserved document location metadata (`nodes`, `source`, `positions`, `path`), and `extensions={policy.correlation_extension_key: correlation_id}`.
   - **Multi-tiered fail-closed degradation:** [`_degraded`][extensions-error-policy] provides the floor: returns `GraphQLError(message=policy.message)`. [`_replacement_for`][extensions-error-policy] wraps classification and masking in `try...except Exception`, degrading unmaskable errors to `_degraded(policy)`. [`mask_execution_result`][extensions-error-policy] wraps result-level processing in `try...except Exception`, degrading unreadable error iterables to `StrawberryExecutionResult(data=None, errors=[_degraded(policy)])`. [`DjangoErrorPolicyExtension._process_result`][extensions-error-policy] safely adopts masked fields back onto the transport result, replacing `execution_context.result` entirely on failure. [`DjangoErrorPolicyExtension.on_operation`][extensions-error-policy] wraps teardown in top-level `try...except Exception`, guaranteeing that runtime teardown crashes replace `execution_context.result` with the degraded fallback.
   - **Dual-seam architecture:** Single-result operations are masked at operation teardown in [`DjangoErrorPolicyExtension.on_operation`][extensions-error-policy] / [`DjangoErrorPolicyExtension._process_result`][extensions-error-policy]. Streamed operations (subscriptions and streamed queries over WebSocket protocols) are masked per-event at the transport result source ([`consumers.py::_stop_aware_results`][consumers]) via [`mask_execution_result`][extensions-error-policy]. [`mask_execution_result`][extensions-error-policy] returns a shallow copy of `ExecutionResult` when errors are replaced, preserving original error objects on `execution_context.result` for upstream extensions (such as `DjangoDebugExtension`) executing in LIFO teardown order.
   - **Runtime gate and policy resolution:** [`masking_is_active`][extensions-error-policy] evaluates `policy.enabled and settings.DEBUG is not True`. [`is_maskable_result`][extensions-error-policy] admits `GraphQLExecutionResult` and `StrawberryExecutionResult`. [`schema_error_policy`][extensions-error-policy] and [`DjangoErrorPolicyExtension._policy`][extensions-error-policy] retrieve `schema.error_policy` with strict `isinstance(policy, ErrorPolicy)` validation, falling back to [`DEFAULT_ERROR_POLICY`][error-policy].
   - **Load-bearing installation position:** Installed at index 0 of `extensions` during `DjangoSchema` construction ([`schema.py::_with_error_policy_extension`][schema]) so that LIFO extension teardown unwinds it last, after diagnostic extensions have read raw `original_error` instances.
4. [`extensions/resource_policy.py`][extensions-resource-policy]: The request-time enforcement engine for `ResourcePolicy` ([spec-047][spec-047] Decisions 2–4, 7–11, 13):
   - **Pre-parse document text scan:** [`scan_document_text`][extensions-resource-policy] performs a single lexical sweep over raw document text in [`DjangoResourcePolicyExtension.on_operation`][extensions-resource-policy] using `graphql.language.lexer.Lexer` before recursive-descent parsing. Charges tokens against [`ResourcePolicy.max_document_tokens`][resource-policy] and structural depth against [`ResourcePolicy.max_depth`][resource-policy] by tracking opening delimiter kinds ([`_OPEN_TOKEN_KINDS`][extensions-resource-policy] = `BRACE_L`, `PAREN_L`, `BRACKET_L`) and closing delimiter kinds ([`_CLOSE_TOKEN_KINDS`][extensions-resource-policy] = `BRACE_R`, `PAREN_R`, `BRACKET_R`) derived from [`_STRUCTURAL_DELIMITER_PAIRS`][extensions-resource-policy].
   - **Context lifecycle and deadline management:** [`DjangoResourcePolicyExtension.on_operation`][extensions-resource-policy] coordinates operation lifecycle: resolves policy from an explicit instance passed to [`DjangoResourcePolicyExtension.__init__`][extensions-resource-policy] or via [`DjangoResourcePolicyExtension._resolved_policy`][extensions-resource-policy] (falling back to [`DEFAULT_RESOURCE_POLICY`][resource-policy]), sets monotonic deadlines under [`DST_RESOURCE_DEADLINE`][resource-policy], stashes active policy under [`DST_RESOURCE_POLICY`][resource-policy] via [`stash_resource_policy`][resource-policy], and restores exact previous context state in `finally` using [`_MISSING_CONTEXT_VALUE`][extensions-resource-policy] via [`DjangoResourcePolicyExtension._restore_context_value`][extensions-resource-policy].
   - **Iterative document AST walk and structural budgets:** [`charge_document`][extensions-resource-policy] walks the AST in [`DjangoResourcePolicyExtension.on_execute`][extensions-resource-policy] using an explicit stack: resolves root types via [`_root_type`][extensions-resource-policy]; expands fragments at every spread site with stack-tracked paths terminating cycles; charges selections and aliases via [`_DocumentBudget`][extensions-resource-policy] ([`_DocumentBudget.__init__`][extensions-resource-policy], [`_DocumentBudget.charge_selection`][extensions-resource-policy]) against [`ResourcePolicy.max_selections`][resource-policy] and [`ResourcePolicy.max_aliases`][resource-policy]; charges compounding collection costs via [`_DocumentBudget.charge_collection`][extensions-resource-policy] against [`ResourcePolicy.max_collection_cost`][resource-policy] using [`_collection_rows`][extensions-resource-policy] and [`_page_bound`][extensions-resource-policy]; exempts Relay connection `edges` lists via [`_is_connection_type`][extensions-resource-policy] requiring [`_CONNECTION_MARKER_FIELD`][extensions-resource-policy] (`"edges"`) and [`_EDGE_MARKER_FIELDS`][extensions-resource-policy] (`{"node", "cursor"}`); resolves introspection meta-fields ([`_SCHEMA_META_FIELD`][extensions-resource-policy] = `"__schema"`, [`_TYPE_META_FIELD`][extensions-resource-policy] = `"__type"`, [`_TYPENAME_META_FIELD`][extensions-resource-policy] = `"__typename"`) via [`_field_definition`][extensions-resource-policy].
   - **Value cardinality and input budget walker:** [`_ValueBudget`][extensions-resource-policy] ([`_ValueBudget.__init__`][extensions-resource-policy]) bounds variable payloads and argument trees: resets per-mutation counters via [`_ValueBudget.begin_mutation_field`][extensions-resource-policy]; traverses input value graphs iteratively in [`_ValueBudget.charge`][extensions-resource-policy] checking [`ResourcePolicy.max_input_nodes`][resource-policy] and [`ResourcePolicy.max_value_depth`][resource-policy]; raises [`ResourceLimitExceeded`][resource-policy] via [`_ValueBudget._reject`][extensions-resource-policy]; bounds container width in [`_ValueBudget._charge_container`][extensions-resource-policy] against [`ResourcePolicy.max_container_width`][resource-policy] with cycle detection via [`_closes_a_cycle`][extensions-resource-policy]; classifies list families in [`_ValueBudget._charge_list_family`][extensions-resource-policy] (nested input objects against [`ResourcePolicy.max_nested_rows`][resource-policy], mutation relation IDs recognized via [`_ID_SCALAR_NAME`][extensions-resource-policy] (`"ID"`) against [`ResourcePolicy.max_relation_ids_per_mutation`][resource-policy] and [`ResourcePolicy.max_relation_ids_total`][resource-policy], query node IDs under argument [`_NODE_IDS_ARGUMENT`][extensions-resource-policy] (`"ids"`) against [`ResourcePolicy.max_node_ids`][resource-policy], and membership items against [`ResourcePolicy.max_membership_items`][resource-policy]); charges scalar byte sizes in [`_ValueBudget._charge_leaf`][extensions-resource-policy] against [`ResourcePolicy.max_scalar_bytes`][resource-policy]; enforces upload limits for [`_UPLOAD_SCALAR_NAME`][extensions-resource-policy] (`"Upload"`) in [`_ValueBudget._charge_upload`][extensions-resource-policy] against [`ResourcePolicy.max_upload_count`][resource-policy], [`ResourcePolicy.max_upload_file_bytes`][resource-policy], and [`ResourcePolicy.max_upload_total_bytes`][resource-policy].
   - **Installation position:** Appended to `extensions` during `DjangoSchema` construction ([`schema.py::_with_resource_policy_extension`][schema]) so that its pre-execution hooks execute first.

Connected subsystem integration examined:
- [`django_strawberry_framework/schema.py`][schema]: Coordinates extension installation ordering: `DjangoErrorPolicyExtension` at index 0 (unwinds last) and `DjangoResourcePolicyExtension` at the end (executes first). Deduplicates extensions in `DjangoSchema.get_extensions`.
- [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: Root re-export surface exposing `DjangoErrorPolicyExtension` and `DjangoResourcePolicyExtension` for plain `strawberry.Schema` consumers, while isolating `DjangoDebugExtension`.
- [`django_strawberry_framework/consumers.py`][consumers]: WebSocket streaming result source `_stop_aware_results` applying `mask_execution_result` per yielded event under `masking_is_active` and `is_maskable_result`.
- [`django_strawberry_framework/error_policy.py`][error-policy]: Pure configuration and domain model defining `ErrorPolicy`, `DEFAULT_ERROR_POLICY`, `resolve_error_policy`, and `new_correlation_id`.
- [`django_strawberry_framework/resource_policy.py`][resource-policy]: Pure configuration and domain model defining `ResourcePolicy`, `DEFAULT_RESOURCE_POLICY`, `resolve_resource_policy`, `stash_resource_policy`, `check_deadline`, `bounded_rows`, and `ResourceLimitExceeded`.
- [`django_strawberry_framework/optimizer/__init__.py`][optimizer-init]: Sibling subsystem exporting `DjangoOptimizerExtension`, kept distinct because query planning owns a cross-request plan cache.
- [`django_strawberry_framework/middleware/debug_toolbar.py`][middleware-debug-toolbar]: Server-side debug toolbar middleware sibling to in-response `DjangoDebugExtension`.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/extensions/ --include-constants`):
- Parsed 4 target files (`__init__.py`, `debug.py`, `error_policy.py`, `resource_policy.py`), 1,928 total lines.
- Inventoried 84 definitions: 22 module constants, 7 classes / typed records, 24 methods, 31 standalone functions / facades.
- Confirmed zero missing definitions and verified all reverse imports across production, test suites, and examples.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - *Uniform SchemaExtension integration:* All three extensions operate as standard Strawberry `SchemaExtension` instances passed via `extensions=[...]`. They integrate identically with `DjangoSchema` and plain `strawberry.Schema` without resolver-level monkeypatching, field decorators, or flavor-specific wrappers.
   - *Uniform request perimeter & response sanitization:* `DjangoResourcePolicyExtension` enforces lexical, AST structural, and value-cardinality limits uniformly across all operation types (queries, mutations, subscriptions). `DjangoErrorPolicyExtension` sanitizes unexpected errors across HTTP sync, HTTP async, and WebSocket streaming transports using shared functions ([`mask_execution_result`][extensions-error-policy], [`masking_is_active`][extensions-error-policy]).
   - *Domain error pass-through:* Deliberate GraphQL errors from mutations (authorization denials), relay (invalid GlobalIDs), and resource limits (`RESOURCE_LIMIT_EXCEEDED`) travel untouched across all flavors without separate adapters.
2. **Sync and async twins:**
   - *Synchronous generator hooks:* All three extension classes implement their lifecycle hooks ([`DjangoDebugExtension.on_operation`][extensions-debug], [`DjangoErrorPolicyExtension.on_operation`][extensions-error-policy], [`DjangoResourcePolicyExtension.on_operation`][extensions-resource-policy], [`DjangoResourcePolicyExtension.on_execute`][extensions-resource-policy]) as synchronous generator functions (`yield`). Strawberry executes synchronous generator extensions uniformly across both synchronous (`execute_sync`) and asynchronous (`execute`) operations.
   - *Shared streaming result masking:* Asynchronous WebSocket streaming generators in [`consumers.py::_stop_aware_results`][consumers] call the exact same synchronous functions ([`mask_execution_result`][extensions-error-policy], [`masking_is_active`][extensions-error-policy], [`is_maskable_result`][extensions-error-policy]), eliminating parallel async masking implementations.
   - *Color-agnostic diagnostics & concurrency:* Exception capture in `DjangoDebugExtension` is completely color-agnostic. Overlapping operations across threads and async tasks increment depth safely under `_CursorCaptureCoordinator`'s `threading.Lock()`, restoring exact flags without race conditions.
3. **Derived rather than repeated knowledge:**
   - *Facade re-exports:* `extensions/__init__.py` derives its public surface directly from member modules by importing classes and declaring `__all__`.
   - *Policy domain separation:* Configuration models and defaults are defined once in domain modules ([`error_policy.py::ErrorPolicy`][error-policy], [`resource_policy.py::ResourcePolicy`][resource-policy]); extensions derive limits and defaults directly from active instances.
   - *Derived wire metrics:* `isSlow` is derived from `duration > _SLOW_QUERY_SECONDS` (10s threshold); `isSelect` is derived from `sql.lower().strip().startswith("select")`.
   - *Structural classification:* [`_is_unexpected`][extensions-error-policy] derives error unexpectedness from object structure (`isinstance(error, GraphQLError)` and `original_error`) rather than maintaining a fragile error-code allowlist.
   - *Structural connection detection:* [`_is_connection_type`][extensions-resource-policy] detects Relay connections structurally via `_CONNECTION_MARKER_FIELD` ("edges") and `_EDGE_MARKER_FIELDS` ({"node", "cursor"}).
4. **Inverse and round-trip pairs:**
   - *Cursor acquire and release:* [`_CursorCaptureCoordinator.acquire`][extensions-debug] saves initial flag state and increments depth; [`_CursorCaptureCoordinator.release`][extensions-debug] decrements depth and restores exact saved state on final release. `DjangoDebugExtension.on_operation` guarantees release via `ExitStack.callback`.
   - *Context stash and restore:* [`DjangoResourcePolicyExtension.on_operation`][extensions-resource-policy] stashes active policy and deadline on entry and restores previous context state (or clears keys) in `finally` using [`_restore_context_value`][extensions-resource-policy] with sentinel [`_MISSING_CONTEXT_VALUE`][extensions-resource-policy], ensuring clean isolation for nested schema executions.
   - *Wire sanitization and server logging:* [`DjangoErrorPolicyExtension`][extensions-error-policy] replaces internal exception messages on the wire with a stable message and correlation ID in `extensions[policy.correlation_extension_key]`, while logging the full exception traceback server-side tagged with the identical correlation ID.
   - *Non-destructive shallow copy:* [`mask_execution_result`][extensions-error-policy] returns a shallow copy with masked errors, keeping original unmasked errors on `execution_context.result` so upstream extensions (`DjangoDebugExtension`) executing in LIFO teardown order can inspect raw exceptions.
5. **Contracts restated in another medium:**
   - The extensions subpackage contracts are consistently documented and verified across:
     - Specifications: [`docs/SPECS/spec-044-debug_extension-0_0_14.md`][spec-044], [`docs/SPECS/spec-047-resource_policy-0_0_14.md`][spec-047], [`docs/SPECS/spec-048-secure_output_defaults-0_0_14.md`][spec-048];
     - Code implementations: [`django_strawberry_framework/extensions/`][extensions-init], [`django_strawberry_framework/schema.py`][schema], [`django_strawberry_framework/consumers.py`][consumers], [`django_strawberry_framework/error_policy.py`][error-policy], [`django_strawberry_framework/resource_policy.py`][resource-policy], [`django_strawberry_framework/conf.py`][conf];
     - Comprehensive test suites: [`tests/extensions/test_debug.py`][test-extensions-debug], [`tests/test_error_policy.py`][test-error-policy], [`tests/test_resource_policy.py`][test-resource-policy], [`tests/base/test_init.py`][test-base-init], [`tests/test_routers.py`][test-routers];
     - Example applications: [`examples/fakeshop/test_query/test_debug_extension_api.py`][test-fakeshop-debug-api], [`examples/fakeshop/test_query/test_error_policy_api.py`][test-fakeshop-error-policy-api], [`examples/fakeshop/test_query/test_resource_policy_api.py`][test-fakeshop-resource-policy-api], [`examples/fakeshop/test_query/test_multi_db.py`][test-fakeshop-multi-db];
     - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`GOAL.md`][goal].

### The single-edit-site test

- **Posited change 1 (Adding a new first-party schema extension):** Introduce a new schema extension class (e.g. `DjangoTracingExtension` in `extensions/tracing.py`).
  - *Sites that must move:* Exactly 1 site in the subpackage facade: [`django_strawberry_framework/extensions/__init__.py`][extensions-init] (importing and adding to `__all__`).
  - *Site count:* 1.
- **Posited change 2 (Adjusting cursor bracket coordination logic):** Modify how database wrapper `force_debug_cursor` flags are saved, nested, or restored.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/debug.py::_CursorCaptureCoordinator`][extensions-debug].
  - *Site count:* 1.
- **Posited change 3 (Modifying the structural exception classification rule):** Alter which execution errors are classified as unexpected across all HTTP and WebSocket execution paths.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/error_policy.py::_is_unexpected`][extensions-error-policy].
  - *Site count:* 1.
- **Posited change 4 (Adjusting pre-parse lexical token scanning):** Support a new syntax delimiter or adjust token budget charging before document parsing.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/resource_policy.py::_STRUCTURAL_DELIMITER_PAIRS`][extensions-resource-policy] (or [`scan_document_text`][extensions-resource-policy]).
  - *Site count:* 1.
- **Posited change 5 (Modifying value budget input list classification):** Change how argument lists are classified into nested rows, mutation relation IDs, query node IDs, or membership items.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/resource_policy.py::_ValueBudget._charge_list_family`][extensions-resource-policy].
  - *Site count:* 1.
- **Posited change 6 (Modifying debug payload caps or truncation markers):** Update the response text budget limit or string truncation marker in the debug extension.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/debug.py`][extensions-debug] ([`_MAX_PAYLOAD_TEXT_CHARS`][extensions-debug] / [`_TRUNCATION_MARKER`][extensions-debug]).
  - *Site count:* 1.

## Rejected candidates

1. **Merging `extensions/error_policy.py` into `error_policy.py` (or `extensions/resource_policy.py` into `resource_policy.py`):**
   - Disproved. Domain modules (`error_policy.py`, `resource_policy.py`) provide lightweight, framework-agnostic data models, defaults, and resolution logic without importing GraphQL AST or Strawberry extension machinery. Keeping runtime enforcement extensions in `extensions/` preserves decoupling and prevents importing heavy AST execution machinery during settings or schema configuration.
2. **Merging `extensions/debug.py` into `middleware/debug_toolbar.py`:**
   - Disproved. `middleware/debug_toolbar.py` integrates with `django-debug-toolbar` to render HTML/JSON panels on server-side requests. `extensions/debug.py` operates directly on the GraphQL response extensions seam (`response.extensions["debug"]`) using Strawberry's `SchemaExtension` lifecycle. Merging them would blur the boundary between Django HTTP middleware and engine-native GraphQL extensions.
3. **Re-exporting `DjangoDebugExtension` from package root `django_strawberry_framework/__init__.py`:**
   - Disproved by [spec-044][spec-044] Decision 11 and pinned by [`tests/base/test_init.py`][test-base-init]. `DjangoDebugExtension` exposes unmasked tracebacks and interpolated SQL. Requiring explicit import from `django_strawberry_framework.extensions` ensures developers do not inadvertently install development-only diagnostics in production schemas.
4. **Unifying `_MAX_ORIGINAL_ERROR_HOPS` with `utils/typing.py::_MAX_TYPE_WRAPPER_DEPTH`:**
   - Disproved. While both constants define recursion depth ceilings (`64`), their failure policies are fundamentally different. `utils/typing.py` raises `TypeError` on exceed (fail-loud schema build), whereas `extensions/debug.py` returns the best-effort terminal exception to avoid crashing GraphQL responses (fail-safe runtime diagnostic).
5. **Re-exporting `DjangoOptimizerExtension` from `django_strawberry_framework/extensions/__init__.py`:**
   - Disproved. While `DjangoOptimizerExtension` is a `SchemaExtension`, it is the entry point of the dedicated query-planning optimizer subsystem (`django_strawberry_framework/optimizer/`). It is canonically exported from `django_strawberry_framework.optimizer` and root `django_strawberry_framework`. Creating an alias in `extensions/` would produce redundant import paths and obscure optimizer subsystem ownership.

## Opportunities

None — The folder integration of `django_strawberry_framework/extensions/` is architecturally clean, robustly tested, and fully consolidated at root owners. Cross-file boundaries between `__init__.py`, `debug.py`, `error_policy.py`, and `resource_policy.py`, as well as integration boundaries with `schema.py`, `consumers.py`, `conf.py`, `error_policy.py`, and `resource_policy.py`, are strictly defined and honor all repository and security invariants.

## Judgment

Zero-edit folder integration review. All 4 files in `django_strawberry_framework/extensions/` operate in total structural alignment. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. Subpackage folder integration verified clean and complete. Checked with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/extensions/ --review docs/dry/dry-folder-extensions.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent re-trace and verification of `django_strawberry_framework/extensions/` folder integration completed:

1. **Subsystem boundaries and structural decomposition:**
   - Verified the clean separation of concerns between domain policy configuration (`error_policy.py`, `resource_policy.py`) and runtime schema enforcement extensions (`extensions/error_policy.py`, `extensions/resource_policy.py`). The domain modules remain lightweight, purely data- and logic-driven with no AST or Strawberry dependencies, allowing configuration resolution and setting parsing at startup without loading heavy execution machinery.
   - Re-traced the strict lifecycle ordering enforced by `schema.py`:
     - `DjangoResourcePolicyExtension` appended at the end of `extensions` so its `on_operation` / `on_execute` pre-execution hooks fire first.
     - `DjangoErrorPolicyExtension` prepended at index 0 of `extensions` so Strawberry's LIFO `on_operation` teardown executes last, guaranteeing diagnostic readers (such as `DjangoDebugExtension`) see raw `original_error` objects before masking occurs.
   - Verified the packaging isolation of `DjangoDebugExtension` in `extensions/`: deliberately withheld from root `django_strawberry_framework/__init__.py` to prevent accidental production exposure of unmasked tracebacks and interpolated SQL, while `DjangoErrorPolicyExtension` and `DjangoResourcePolicyExtension` are root-exported as default recipes for plain schemas.
2. **Dual-seam error masking architecture:**
   - Confirmed that single-result operations (HTTP sync/async) and streaming operations (`consumers.py::_stop_aware_results` over WebSockets) share the exact same masking implementations ([`mask_execution_result`][extensions-error-policy], [`masking_is_active`][extensions-error-policy], [`is_maskable_result`][extensions-error-policy]).
   - Re-verified that `mask_execution_result` returns a shallow copy of `ExecutionResult` when errors are replaced, preserving unmasked error objects on the engine's `execution_context.result` for upstream extensions in the LIFO teardown stack.
3. **Resource policy enforcement mechanics:**
   - Re-traced lexical pre-parse scan (`scan_document_text`), AST walk (`charge_document`), and value cardinality checks (`_ValueBudget`).
   - Confirmed that Relay connection `edges` lists are structurally exempted from redundant list row cost via `_is_connection_type` (requiring `_CONNECTION_MARKER_FIELD = "edges"` and `_EDGE_MARKER_FIELDS = {"node", "cursor"}`).
   - Verified that `DjangoResourcePolicyExtension.on_operation` safely manages the context lifecycle using `_restore_context_value` and `_MISSING_CONTEXT_VALUE`, preventing key leakage across nested operations.
4. **Mandatory 5-axis duplication probing matrix:**
   - Discharged all 5 axes with full evidence:
     1. Cross-flavor policy mirroring (uniform `SchemaExtension` contracts across HTTP, WebSocket queries, and subscriptions).
     2. Sync and async twins (color-neutral generator hooks, shared streaming result masking, thread-safe cursor capture coordinator).
     3. Derived rather than repeated knowledge (facade re-exports, structural unexpectedness classification, structural Relay connection detection).
     4. Inverse and round-trip pairs (cursor bracket acquire/release reference counting, context stash/restore, wire masking paired with server-side correlation logging, non-destructive shallow copies).
     5. Contracts restated across media (specifications, implementations, tests, and documentation).
5. **Single-edit-site verification:**
   - Re-evaluated all posited changes (adding new extensions, cursor coordinator updates, exception classification rules, pre-parse lexer updates, value budget list classification, debug payload caps); confirmed all single-edit-site counts are exactly 1.
6. **Automated inventory check:**
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/extensions/ --review docs/dry/dry-folder-extensions.md --include-constants` and confirmed 100% definition coverage across all 4 files (84 target definitions covered, 0 missing).
   - Status updated to `verified`.

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
[connection]: ../../django_strawberry_framework/connection.py
[consumers]: ../../django_strawberry_framework/consumers.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[error-policy]: ../../django_strawberry_framework/error_policy.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[extensions-debug]: ../../django_strawberry_framework/extensions/debug.py
[extensions-error-policy]: ../../django_strawberry_framework/extensions/error_policy.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[extensions-resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[list-field]: ../../django_strawberry_framework/list_field.py
[middleware-debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[optimizer-init]: ../../django_strawberry_framework/optimizer/__init__.py
[relay]: ../../django_strawberry_framework/relay.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[schema]: ../../django_strawberry_framework/schema.py
[utils-context]: ../../django_strawberry_framework/utils/context.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py
[views]: ../../django_strawberry_framework/views.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-error-policy]: ../../tests/test_error_policy.py
[test-extensions-debug]: ../../tests/extensions/test_debug.py
[test-resource-policy]: ../../tests/test_resource_policy.py
[test-routers]: ../../tests/test_routers.py

<!-- examples/ -->
[test-fakeshop-debug-api]: ../../examples/fakeshop/test_query/test_debug_extension_api.py
[test-fakeshop-error-policy-api]: ../../examples/fakeshop/test_query/test_error_policy_api.py
[test-fakeshop-multi-db]: ../../examples/fakeshop/test_query/test_multi_db.py
[test-fakeshop-resource-policy-api]: ../../examples/fakeshop/test_query/test_resource_policy_api.py

<!-- scripts/ -->

<!-- .venv/ -->
[strawberry-extension]: ../../.venv/lib/python3.14/site-packages/strawberry/extensions/base_extension.py

<!-- External -->
