# Review: `django_strawberry_framework/auth/`

Status: verified

## Understanding

`django_strawberry_framework/auth/` provides the package's opt-in session-authentication subsystem (spec-040). It delivers four field factories (`current_user`, `login_mutation`, `logout_mutation`, `register_mutation`), transport classification and capability guards across Django HTTP and Channels ASGI (HTTP and WebSocket), per-scope concurrency synchronization, permission resolution, and phase-2.5 schema binding.

### Subpackage Architecture & Module Cohesion

1. **Opt-in Boundary (`__init__.py`):**
   - Public API exports: `__all__ = ("current_user", "login_mutation", "logout_mutation", "register_mutation")`.
   - Structural opt-in invariant: deliberately omitted from top-level `django_strawberry_framework.__init__.__all__`. Consumers importing the root package never pay the `django.contrib.auth` import penalty; only consumers explicitly importing `django_strawberry_framework.auth` load the subsystem.

2. **Mutation Factories & Phase-2.5 Bind (`mutations.py`):**
   - Field factories: `login_mutation()`, `logout_mutation()`, and `register_mutation()`.
   - Declaration registry (`_auth_declaration_registry = make_declaration_registry(_AUTH_FAMILY_LABEL)`): registered with `register_subsystem_clear(owner="auth.declarations")` (without `before_bind=True`) so declarations survive pre-bind resets and are cleared only on full `TypeRegistry.clear()`.
   - One-declaration-per-process rule: `_reject_conflicting_permission_classes` caches identical declarations and raises actionable `ConfigurationError` on conflicting `permission_classes`.
   - Fixed auth infrastructure: duck-typed permission holders (`_make_permission_holder`) holding `_AuthMutationMetaSnapshot`, delegating permission checks to `DjangoMutation.check_permission` and `mutations.resolvers.authorize_or_raise`.
   - Field dispatch: `_make_auth_field` routes sync vs async execution per call (`in_async_context()`) with lazy payload type annotations (`_lazy_ref`).
   - Login & logout lifecycle: coordinates with `sessions.py` via `_transport_prologue`. Enforces account-enumeration defenses via byte-identical undifferentiated failed login envelopes (`field_error("", _INCORRECT_CREDENTIALS_MESSAGE)`), lone-surrogate preflight check via `unencodable_text_error`, payload construction before session mutation, and fail-closed rollback/compensation on session persistence failures.
   - Registration rider: synthesizes `Register` inheriting from `DjangoMutation`, pinning public input name to `RegisterInput` and generating `RegisterPayload`. Derives input fields via `derive_register_fields(user_model)` while strictly rejecting privilege/account-control flags (`_REGISTER_PROTECTED_FIELDS`). Intercepts `password` via `_REGISTER_EXCLUDED_INPUT_FIELDS`, validates password with constructed user instance context (`validate_password(raw_password, user)`), and hashes via `user.set_password()` before `full_clean()`.
   - Phase-2.5 auth bind (`bind_auth_mutations`): executed by `types/finalizer.py` before `bind_mutations()`. Resolves user primary type via `_resolve_user_primary_or_raise` with clear diagnostics. Surface-keyed: resolves user type and materializes payloads (`LoginPayload`, `LogoutPayload`, `CurrentUserAlias`) only for declared surfaces, allowing logout-only schemas to bind without any registered user type.

3. **Query Factory & Return Alias (`queries.py`):**
   - Query factory: `current_user()`, returning `CurrentUserAlias | None`.
   - Return-alias namespace: manages `CurrentUserAlias` module global using `make_input_namespace`, registered with `register_subsystem_clear(owner="auth.current_user_alias", before_bind=True)` so emit ledgers drain before each phase-2.5 bind.
   - Actor resolution: `_current_user_resolve_body` resolves the request via `request_from_info` with `_AUTH_FAMILY_LABEL`, obtains actor via `_authenticated_actor_or_none`, evaluates permissions via `authorize_or_raise`, and adheres to the actor-not-lookup rule (returning the authenticated actor directly without `get_queryset` re-run).
   - Async bridging: bridges async execution via `run_in_one_sync_boundary` so lazy `SimpleLazyObject` user evaluation runs safely in a sync worker thread without raising `SynchronousOnlyOperation`.

4. **Transport Classification & Concurrency Boundary (`sessions.py`):**
   - Transport classification (`classify_transport`, `Transport`): resolves request objects to `DJANGO_HTTP`, `CHANNELS_HTTP`, or `CHANNELS_WEBSOCKET` using `isinstance(request, ChannelsRequestAdapter)` first rather than attribute sniffing.
   - Soft dependency: loads `channels` lazily via `require_channels()` with an actionable install hint only when a Channels context is encountered.
   - Session requirement: `require_session` guards against missing `SessionMiddleware` / `AuthMiddlewareStack`, raising actionable `ConfigurationError` containing `"session"`.
   - Per-scope concurrency lock: `scope_session_lock` provides an async context manager acquiring a lazily instantiated, non-reentrant `asyncio.Lock` stored under `_SCOPE_LOCK_KEY` inside the mutable ASGI scope mapping (zero process-global lock state).
   - Capability matrix: restricts login on all WebSockets (`login_supported`) and logout on signed-cookie WebSockets (`logout_supported`).

5. **Cross-Subsystem Finalizer & Resolver Contracts:**
   - In `types/finalizer.py`, `loaded_attr("django_strawberry_framework.auth.mutations", "bind_auth_mutations")` checks if `auth.mutations` is loaded, preserving zero-overhead import isolation for auth-free schemas.
   - The phase-2.5 bind slot is positioned strictly after the pre-bind emit ledger reset and before `bind_mutations()`, ensuring `RegisterInput` and `RegisterPayload` are materialized in proper sequence and user primary resolution errors fire with auth-specific diagnostic messages.

## Verification

1. Examined all individual file review artifacts (`rev-auth__mutations.md`, `rev-auth__queries.md`, `rev-auth__sessions.md`), confirming zero outstanding findings and full verification by Worker 2.
2. Verified holistic cross-module contracts and whole-subpackage behavior:
   - Public API exports in `auth/__init__.py`.
   - Module import isolation (importing package root does not import `auth` or `django.contrib.auth`).
   - Declarations ledger survival across pre-bind resets and full clear upon `registry.clear()`.
   - Surface-keyed schema finalization for logout-only and full auth surfaces.
   - User primary type resolution diagnostics for missing and ambiguous user types.
   - Actor classification cohesion (`_authenticated_actor_or_none`) across Django and Channels requests.
   - Transport classification, session middleware verification, and capability matrix.
3. Focused permanent test suite execution:
   - `uv run pytest tests/auth/ examples/fakeshop/test_query/test_auth_api.py --no-cov` -> 162 passed.
4. Holistic scratch test execution:
   - `docs/review/temp-tests/auth/test_scratch_auth_subpackage.py` -> 8 passed in 2.37s.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The `django_strawberry_framework/auth/` subpackage is an exceptionally cohesive, robust, and secure implementation of session authentication for GraphQL. It exhibits strict module boundaries, clear public vs private symbol separation, disciplined error handling, comprehensive defense-in-depth security invariants (account enumeration defenses, fail-closed session rollback, unicode surrogate preflighting, scope-isolated concurrency locking, and protected field shielding), and clean phase-2.5 finalizer integration.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/auth/test_mutations.py`, `tests/auth/test_queries.py`, `tests/auth/test_sessions.py`, `examples/fakeshop/test_query/test_auth_api.py`) covers all subpackage behavior (162 tests).
- Scratch verification:
  - `docs/review/temp-tests/auth/test_scratch_auth_subpackage.py` passed (8/8 tests) verifying public exports, lazy boundary isolation, declaration lifecycle vs pre-bind clears, surface-keyed binding, diagnostics, actor classification, and transport capabilities.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/auth/ docs/review/temp-tests/auth/test_scratch_auth_subpackage.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/auth/` passed with 0 errors.
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Verified zero-edit scoped diff: confirmed `git diff 12779c99 -- django_strawberry_framework/auth/` is completely empty.
- Re-traced whole-subpackage behavior and subsystem boundaries:
  - Public export invariants in `auth/__init__.py` and structural opt-in isolation preserving zero overhead when `auth` is not imported.
  - Lifecycle invariants of auth declarations across pre-bind emit-ledger clears vs full `TypeRegistry.clear()`.
  - Finalizer phase-2.5 bind sequence in `finalizer.py` executing `bind_auth_mutations()` conditionally via `loaded_attr`.
  - Surface-keyed schema finalization generating only declared type definitions (e.g. logout-only schemas requiring no registered Django user type).
  - Diagnostic clarity for missing and ambiguous user model registrations in `_resolve_user_primary_or_raise`.
  - Cohesion of actor resolution (`_authenticated_actor_or_none`) and permissions checks across Django HTTP, Channels HTTP, and Channels WebSocket.
  - Concurrency management via ASGI scope-isolated session locks (`scope_session_lock`) avoiding global lock contention.
  - Defense-in-depth protections: byte-identical login failure envelopes, lone-surrogate preflight checks, atomic rollback on session persistence failure, and rejection of protected privilege fields during registration derivation.
- Focused verification suite:
  - Ran `uv run pytest tests/auth/ examples/fakeshop/test_query/test_auth_api.py docs/review/temp-tests/auth/test_scratch_auth_subpackage.py --no-cov`.
  - All 170 tests (162 permanent + 8 scratch) passed in 18.04s.
- No new findings discovered; confirmed 0 outstanding findings. Ready for acceptance.
