# Review: `django_strawberry_framework/auth/sessions.py`

Status: verified

## Understanding

`django_strawberry_framework/auth/sessions.py` implements the private transport classification, session pre-checking, per-scope concurrency synchronization, and session-engine capability evaluation layer for the opt-in session-authentication subsystem.

It owns:
1. **Transport Classification (`classify_transport`, `Transport`):**
   - Resolves a resolved request object into exactly one explicit `Transport` enum variant: `DJANGO_HTTP`, `CHANNELS_HTTP`, or `CHANNELS_WEBSOCKET`.
   - Uses `isinstance(request, ChannelsRequestAdapter)` first rather than attribute sniffing, avoiding misclassification from the adapter's `__getattr__` delegation.
   - Enforces the `channels` soft dependency lazily via `require_channels()` (`utils.imports.require_optional_module`) with an actionable install hint (`_CHANNELS_INSTALL_HINT`) only once a Channels adapter is encountered.
   - Distinguishes Channels HTTP from WebSocket via `scope.get("type")`, rejecting unsupported scope types (`"lifespan"`, `"sse"`, or missing) and unclassifiable request types with an actionable `ConfigurationError`.
2. **Session Pre-Check (`require_session`):**
   - Validates that `request.session` is present and not `None` before authentication or mutation state machines execute.
   - Prevents downstream `AttributeError` (such as `None.cycle_key()`) by converting missing `SessionMiddleware` / `AuthMiddlewareStack` into an actionable `ConfigurationError` containing the `"session"` substring.
3. **Per-Scope Concurrency Serialization (`scope_session_lock`, `_require_mutable_scope`):**
   - Provides an async context manager acquiring a lazily instantiated, non-reentrant `asyncio.Lock` stored under the private key `_SCOPE_LOCK_KEY` (`"__django_strawberry_framework_auth_session_lock__"`) inside the connection's mutable ASGI scope mapping.
   - Enforces security invariant 12: scope-owned serialization with zero process-global state, zero `ContextVar` leakage, and atomic single-event-loop lazy initialization.
   - Validates scope mutability via `_require_mutable_scope`, rejecting immutable mappings with `ConfigurationError`.
4. **Session Engine Capability Evaluation (`uses_signed_cookie_sessions`, `login_supported`, `logout_supported`):**
   - Detects signed-cookie session storage (`uses_signed_cookie_sessions`) by inspecting `issubclass(session_store_class(), SignedCookieSessionStore)` using the shared engine resolver in `utils/sessions.py`.
   - Restricts login over any WebSocket connection (`login_supported`), as established WebSockets cannot transmit rotated session cookies to the browser.
   - Restricts logout over signed-cookie WebSocket connections (`logout_supported`), as signed-cookie engines maintain no server-side records to invalidate.

## Verification

1. Traced connections across callers, dependencies, and lifecycle points:
   - `django_strawberry_framework/auth/mutations.py` (`_transport_prologue`, `_channels_http_login_establish`, `_channels_logout`)
   - `django_strawberry_framework/utils/sessions.py` (`session_store_class`, `actor_transition`, `connection_actor_state`)
   - `django_strawberry_framework/utils/permissions.py` (`ChannelsRequestAdapter`, `request_from_info`)
   - `django_strawberry_framework/utils/imports.py` (`require_optional_module`)
2. Evaluated existing permanent tests in `tests/auth/test_sessions.py` (26 test cases) and `tests/auth/test_mutations.py`:
   - `isinstance`-first classification for Django `HttpRequest` and Channels adapters.
   - Soft-dependency failure isolation and install hints under simulated absence of `channels`.
   - Subprocess verification proving `auth` and `auth.sessions` import without importing `channels`.
   - Missing session middleware detection and error messages.
   - Scope lock lazy instantiation, single-loop contention mutual exclusion, cancelled task lock release/waiter cleanup, cross-scope independence, and absence of process-global lock storage.
   - Session engine subclass detection and capability matrix for login and logout across HTTP and WebSocket transports.
3. Executed focused test runs:
   - `uv run pytest tests/auth/test_sessions.py --no-cov` (26 passed).
   - `uv run pytest tests/auth/ examples/fakeshop/test_query/test_auth_api.py --no-cov` (162 passed).
4. Executed scratch verification tests `docs/review/temp-tests/auth__sessions/test_scratch_auth_sessions.py`:
   - Verified `Transport` enum invariants and member values.
   - Verified `classify_transport` handling of `HttpRequest` subclasses.
   - Verified exact error formatting for unsupported ASGI scope types and invalid request objects.
   - Verified `require_session` error diagnostics across Django and Channels contexts.
   - Verified `scope_session_lock` non-reentrancy on the same task.
   - Verified full capability matrix combinations across session engines and transports.
   - Result: 6 passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/auth/sessions.py` provides a clean, secure, and rigorously isolated transport boundary for session authentication. It correctly handles transport classification, soft-dependency isolation, actionable middleware error diagnostics, scope-bound non-global concurrency locking, and session capability constraints. No defects or design deficiencies found.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/auth/test_sessions.py` with 26 tests) comprehensively covers transport classification, lazy soft-dependency isolation, channels-free import independence, missing session detection, scope-level `asyncio.Lock` lifecycle/contention/cancellation, and session engine capability evaluation.
- Scratch verification:
  - `docs/review/temp-tests/auth__sessions/test_scratch_auth_sessions.py` passed (6/6 tests) verifying `Transport` enum structure, `HttpRequest` inheritance, diagnostic error messaging, lock non-reentrancy, and session capability matrix.
- Formatter and linter results:
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/auth/sessions.py`: 0 errors.
  - `uv run ruff check django_strawberry_framework/auth/sessions.py tests/auth/test_sessions.py`: all checks passed.
  - `uv run ruff format --check django_strawberry_framework/auth/sessions.py tests/auth/test_sessions.py`: all files formatted.
- Rejected findings: None.
- Changelog note: None (zero-edit cycle).

## Independent verification (Worker 2)

- Scoped diff: verified empty against HEAD (`12779c99`).
- Behavior tracing:
  - Transport classification: Confirmed `isinstance`-first matching of `ChannelsRequestAdapter` followed by scope protocol inspection (`"http"` -> `CHANNELS_HTTP`, `"websocket"` -> `CHANNELS_WEBSOCKET`), `HttpRequest` fallback -> `DJANGO_HTTP`, lazy Channels import with install hint, and explicit `ConfigurationError` on unknown objects or unrecognized scope types.
  - Session pre-checking: Verified `require_session` safely catches `None` sessions on both Django requests and Channels adapters, raising an actionable `ConfigurationError` containing `"session"` and transport name, avoiding unhandled `AttributeError` during key rotation.
  - Concurrency serialization: Verified `_require_mutable_scope` rejects non-mutable scopes and accepts custom `MutableMapping` implementations; verified `scope_session_lock` lazy instantiation, non-reentrancy on the same task, lock sharing across adapters wrapping the same scope, cross-scope independence, zero process-global state, and exception/cancellation lock cleanup.
  - Capability evaluation: Verified `uses_signed_cookie_sessions` detection across DB, cache, cached_db, file, signed cookie, and custom subclassed backends; verified `login_supported` restricts all WebSocket connections; verified `logout_supported` permits HTTP and server-side WebSocket while disallowing signed-cookie WebSocket.
- Test execution:
  - Focused permanent suite: `uv run pytest tests/auth/test_sessions.py --no-cov` (26 passed).
  - Auth subsystem & example integration: `uv run pytest tests/auth/ examples/fakeshop/test_query/test_auth_api.py --no-cov` (162 passed).
  - Worker 2 independent scratch tests: `uv run pytest docs/review/temp-tests/auth__sessions/test_independent_scratch_auth_sessions.py --no-cov` (12 passed) verifying custom mutable mappings, immutable scope rejection, falsy session object support, body exception lock release, multi-adapter scope sharing, and session backend capability matrix.
- Conclusion: Fully verified. Zero edits needed.

