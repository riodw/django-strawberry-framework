# DRY review: `django_strawberry_framework/auth/sessions.py`

Status: verified

## System trace

`auth/sessions.py` is the private transport classification and capability boundary of the session-auth subsystem ([spec-040][spec-040] Decisions 3, 5, 11, 12; [spec-046][spec-046] Decisions 10, 11). It provides transport classification, missing-session pre-checking, per-scope session mutation locking, and session-engine capability answering for login and logout state machines. It is deliberately not re-exported by `auth.__all__` or the package root, keeping module imports channels-free until a real Channels scope is classified.

It owns five distinct responsibilities:

- **Transport classification:** [`Transport`][auth-sessions] defines three explicit transport modes: `DJANGO_HTTP`, `CHANNELS_HTTP`, and `CHANNELS_WEBSOCKET`. [`classify_transport`][auth-sessions] inspects the request object resolved by [`utils/permissions.py::request_from_info`][utils-permissions]. It applies an `isinstance(request, ChannelsRequestAdapter)` check first (preventing attribute sniffing failures under `ChannelsRequestAdapter.__getattr__`), triggers lazy soft-dependency verification via [`require_channels`][auth-sessions] with [`_CHANNELS_INSTALL_HINT`][auth-sessions] (delegating to [`utils/imports.py::require_optional_module`][utils-imports]), and maps `scope["type"]` to `CHANNELS_HTTP` or `CHANNELS_WEBSOCKET`. Native Django `HttpRequest` instances map to `DJANGO_HTTP`, while missing or unrecognized scopes raise actionable [`exceptions.py::ConfigurationError`][exceptions].
- **Session requirement validation:** [`require_session`][auth-sessions] checks `getattr(request, "session", None)` before mutation. If absent (e.g. Django `SessionMiddleware` omitted, or Channels scope without session middleware), it raises an actionable `ConfigurationError` referencing the specific transport mode, preventing downstream `AttributeError` failures like `None.cycle_key()`.
- **Per-scope concurrency locking:** [`scope_session_lock`][auth-sessions] provides an asynchronous context manager yielding an `asyncio.Lock` stored under [`_SCOPE_LOCK_KEY`][auth-sessions] (`"__django_strawberry_framework_auth_session_lock__"`) on the Channels scope. [`_require_mutable_scope`][auth-sessions] enforces that the scope is a `MutableMapping`. This guarantees that concurrent operations on the same WebSocket or HTTP connection serialize their session mutations, persistence, and rollbacks atomically without process-global registries or `ContextVar` leaks (Security Invariant 12).
- **Session engine capability queries:** [`uses_signed_cookie_sessions`][auth-sessions] tests whether the configured session engine is or subclasses Django's signed-cookie backend (`SignedCookieSessionStore`) using [`utils/sessions.py::session_store_class`][utils-sessions].
- **Auth transport capability gating:** [`login_supported`][auth-sessions] and [`logout_supported`][auth-sessions] declare whether login and logout can truthfully establish or invalidate sessions on a given transport. Login is unsupported on all WebSockets (established WebSockets cannot set or rotate browser cookies). Logout is supported everywhere except on signed-cookie WebSockets (signed-cookie sessions have no server-side record to revoke and cannot delete client cookies over an open socket).

Connected behavior examined:
- [`auth/mutations.py`][auth-mutations]: Invokes [`classify_transport`][auth-sessions], [`login_supported`][auth-sessions], [`logout_supported`][auth-sessions], [`require_session`][auth-sessions], and [`scope_session_lock`][auth-sessions] during login and logout mutation execution.
- [`utils/sessions.py`][utils-sessions]: Hosts the shared `session_store_class` resolver and connection actor lease primitives (`ConnectionActorState`, `actor_lease`, `actor_transition`, `note_authenticated_actor`, `connection_was_authenticated`). Stored in `utils/sessions.py` rather than `auth/sessions.py` so that [`consumers.py`][consumers] can revalidate WebSocket actor sessions without importing `auth` and prematurely registering GraphQL auth types.
- [`consumers.py`][consumers]: Uses the connection actor lease (`actor_lease`) from `utils/sessions.py` for per-operation actor revalidation, observing the total lock hierarchy: `scope_session_lock` (outer, auth mutation) -> `actor_transition` / `actor_lease` (inner, transport frame send).
- [`routers.py`][routers]: Employs sibling Channels optional import hint patterns (`_CHANNELS_INSTALL_HINT`).
- [`utils/imports.py`][utils-imports]: Shared optional dependency loader (`require_optional_module`).
- [`utils/permissions.py`][utils-permissions]: `ChannelsRequestAdapter` wrapper for ASGI scopes.
- [`tests/auth/test_sessions.py`][test-sessions], [`tests/auth/test_mutations.py`][test-mutations], [`tests/test_routers.py`][test-routers].

## Verification

Static analysis and inventory (`export_dry_review.py check`):
- Parsed 1 target file, 254 lines, 11 definitions (`_CHANNELS_INSTALL_HINT`, `_SCOPE_LOCK_KEY`, `Transport`, `require_channels`, `classify_transport`, `require_session`, `_require_mutable_scope`, `scope_session_lock`, `uses_signed_cookie_sessions`, `login_supported`, `logout_supported`), 6 imports.
- Checked reverse imports and confirmed all 11 definitions are actively used by production auth mutations and test suites.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `auth/sessions.py` provides the single authoritative transport classification and session capability interface for GraphQL auth operations. DRF and Django forms operate strictly on standard `HttpRequest` objects via WSGI/ASGI handlers, where session mutation semantics are handled by Django middleware. GraphQL session mutations support heterogeneous transports (native Django HTTP, Channels HTTP, and Channels WebSocket). Rather than mirroring transport checks inside individual mutation resolvers or across different schema flavors, all transport detection and capability gating are consolidated into [`classify_transport`][auth-sessions], [`login_supported`][auth-sessions], and [`logout_supported`][auth-sessions].
2. **Sync and async twins:**
   Zero duplication. Session mutation locking via [`scope_session_lock`][auth-sessions] is natively asynchronous, operating on the event loop shared by ASGI Channels scopes. Sync execution paths (Django HTTP) run on dedicated threads per request with standard thread isolation and do not require scope locking. Sync-bridged Channels execution paths in [`auth/mutations.py`][auth-mutations] delegate to `_channels_login` and `_channels_logout` which execute natively async under `scope_session_lock`, avoiding parallel sync/async lock implementations.
3. **Derived rather than repeated knowledge:**
   - Session engine subclassing: [`uses_signed_cookie_sessions`][auth-sessions] derives its answer via `issubclass(session_store_class(), SignedCookieSessionStore)` rather than matching engine string literals, automatically supporting custom signed-cookie subclasses.
   - Capability rules: [`logout_supported`][auth-sessions] derives its signed-cookie WebSocket restriction directly from `uses_signed_cookie_sessions()` and `Transport.CHANNELS_WEBSOCKET`, rather than re-reading `settings.SESSION_ENGINE`.
   - Soft dependency hints: [`require_channels`][auth-sessions] delegates directly to [`utils/imports.py::require_optional_module`][utils-imports] with [`_CHANNELS_INSTALL_HINT`][auth-sessions].
   - Unified session check: [`require_session`][auth-sessions] collapses Django `request.session` absence and Channels `adapter.session is None` into a single `getattr(request, "session", None)` validation.
4. **Inverse and round-trip pairs:**
   - Capability pair: [`login_supported`][auth-sessions] (never supported on WebSocket due to inability to rotate cookies over an established socket) and [`logout_supported`][auth-sessions] (supported on WebSocket for server-side engines because deleting backend records invalidates the session without cookie mutation; unsupported only for signed cookies).
   - Lock lifecycle pair: [`scope_session_lock`][auth-sessions] provides safe `async with` acquire/release semantics. Cancelling a holding or waiting task cleanly unwinds or preserves the lock without leaving orphaned or corrupted state (verified in [`tests/auth/test_sessions.py`][test-sessions]).
5. **Contracts restated in another medium:**
   The transport capability contracts, lock hierarchy, and missing-middleware error contracts are codified across:
   - Code: [`django_strawberry_framework/auth/sessions.py`][auth-sessions], [`django_strawberry_framework/auth/mutations.py`][auth-mutations], [`django_strawberry_framework/utils/sessions.py`][utils-sessions], [`django_strawberry_framework/consumers.py`][consumers];
   - Specifications: [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040] (Decisions 3, 5, 11, 12, Root Cause 3), [`docs/SPECS/spec-046-transport_security-0_0_14.md`][spec-046] (Decisions 10, 11, Security Invariant 12);
   - Test suites: [`tests/auth/test_sessions.py`][test-sessions], [`tests/auth/test_mutations.py`][test-mutations], [`tests/test_routers.py`][test-routers];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary].

### The single-edit-site test

- **Posited change 1 (Supporting a new ASGI transport protocol or scope type):** Add a new transport kind (e.g. Server-Sent Events or WebRTC).
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/auth/sessions.py::classify_transport`][auth-sessions] (and the `Transport` enum in the same file).
  - *Site count:* 1.
- **Posited change 2 (Custom session backend capability rules):** Recognize an additional stateless or non-revocable custom session engine backend.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/auth/sessions.py::uses_signed_cookie_sessions`][auth-sessions]. `logout_supported` and all calling mutations inherit the updated capability immediately.
  - *Site count:* 1.
- **Posited change 3 (Missing-session error formatting):** Modify the diagnostic error message or remediation hint when session middleware is missing.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/auth/sessions.py::require_session`][auth-sessions].
  - *Site count:* 1.
- **Posited change 4 (Scope lock key namespacing):** Change the internal ASGI scope lock key.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/auth/sessions.py::_SCOPE_LOCK_KEY`][auth-sessions].
  - *Site count:* 1.

### Rejected candidates

1. **Unifying `_SCOPE_LOCK_KEY` and `_ACTOR_STATE_SCOPE_KEY` into a single monolithic lock:**
   - Disproved. `scope_session_lock` in `auth/sessions.py` serializes session write mutations (login/logout), while `actor_lease` and `ConnectionActorState` in `utils/sessions.py` manage connection actor provenance and WebSocket frame revalidation. Maintaining `scope_session_lock` as the outer lock and `actor_lease` as the inner lock prevents frame serialization from blocking on session mutations and keeps transport consumers decoupled from the auth module.
2. **Moving `uses_signed_cookie_sessions` or capability checks directly into `auth/mutations.py`:**
   - Disproved. Housing transport classification and capability introspection in `auth/sessions.py` isolates transport-specific mechanics and optional `channels` dependency resolution from GraphQL resolver construction.
3. **Merging `auth/sessions.py` into `utils/sessions.py`:**
   - Disproved. `utils/sessions.py` must remain cycle-neutral and channels-free so that `consumers.py` can import `session_store_class` and `actor_lease` without triggering `auth/__init__.py`, which eagerly registers GraphQL auth mutations and queries.

## Opportunities

None — `django_strawberry_framework/auth/sessions.py` is a clean, 254-line, single-responsibility module. It provides authoritative transport classification, capability queries, session validation, and scope-level concurrency control for the auth subsystem. All shared invariants and boundaries are properly partitioned between `auth/sessions.py` and `utils/sessions.py`.

## Judgment

Zero-edit review. `auth/sessions.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/auth/sessions.py --review docs/dry/dry-file-auth__sessions.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Worker 2 independently verified `django_strawberry_framework/auth/sessions.py` against Worker 1's review artifact:

1. **Contract and Boundary Verification:**
   - **Transport Classification:** Confirmed `classify_transport` executes an `isinstance(request, ChannelsRequestAdapter)` check prior to checking scope attributes. This avoids false attribute resolution via `ChannelsRequestAdapter.__getattr__`. Lazy soft-dependency import via `require_channels()` with module-specific `_CHANNELS_INSTALL_HINT` cleanly delegates to `utils.imports.require_optional_module`. Deterministic subprocess isolation test confirms importing `django_strawberry_framework.auth` and `django_strawberry_framework.auth.sessions` remains strictly channels-free until a real Channels scope is handled.
   - **Session Presence Pre-checking:** Confirmed `require_session` collapses native Django missing middleware (`request.session` absent) and Channels missing middleware (`adapter.session is None`) into a single `getattr(request, "session", None)` check that raises a descriptive `ConfigurationError` containing the `"session"` substring.
   - **Concurrency and Lock Isolation:** Confirmed `scope_session_lock` is lazily created and stored under `_SCOPE_LOCK_KEY` on the scope mapping without an `await` between lookup and assignment, guaranteeing atomic lock initialization on the single-threaded asyncio event loop. Enforces `isinstance(scope, MutableMapping)` via `_require_mutable_scope` to prevent silent lock bypass. Structural inspection confirms no module-level global registries or `ContextVar` leaks exist (Security Invariant 12).
   - **Session Engine Capabilities:** Confirmed `uses_signed_cookie_sessions()` inspects `issubclass(session_store_class(), SignedCookieSessionStore)`, properly recognizing custom subclasses. `login_supported` and `logout_supported` truthfully gate operations according to transport characteristics (WebSockets cannot set replacement cookies on login; server-side sessions can invalidate without cookies on logout, whereas signed-cookie WebSockets cannot).
   - **Opt-in Boundary Partitioning with `utils/sessions.py`:** Re-traced the relationship with `utils/sessions.py`. `session_store_class` and connection actor lease mechanisms live in `utils/sessions.py` specifically so `consumers.py` can perform per-operation WebSocket actor revalidation without importing `auth` and inadvertently triggering registration of GraphQL auth fields. The total lock order (`scope_session_lock` outer -> `actor_lease` inner) is verified acyclic.

2. **Probing Matrix and Single-Edit-Site Verification:**
   - All 5 axes of the mandatory probing matrix were re-evaluated and confirmed discharged with sound justifications.
   - All 4 posited single-edit-site changes move exactly 1 site each.

3. **Coverage and Test Gate Execution:**
   - Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/auth/sessions.py --review docs/dry/dry-file-auth__sessions.md --include-constants`: confirmed 11/11 definitions and 0 required topics covered.
   - Executed `uv run pytest tests/auth/test_sessions.py --no-cov`: all 26 unit tests passed.

Worker 2 confirms `django_strawberry_framework/auth/sessions.py` is clean and fully verified. Setting `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md

<!-- docs/SPECS/ -->
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md
[spec-046]: ../SPECS/spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-init]: ../../django_strawberry_framework/auth/__init__.py
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-queries]: ../../django_strawberry_framework/auth/queries.py
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[consumers]: ../../django_strawberry_framework/consumers.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[routers]: ../../django_strawberry_framework/routers.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-sessions]: ../../django_strawberry_framework/utils/sessions.py

<!-- tests/ -->
[test-mutations]: ../../tests/auth/test_mutations.py
[test-queries]: ../../tests/auth/test_queries.py
[test-sessions]: ../../tests/auth/test_sessions.py
[test-routers]: ../../tests/test_routers.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
