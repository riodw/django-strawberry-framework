# Review: `django_strawberry_framework/auth/mutations.py`

Status: verified

## Understanding

`django_strawberry_framework/auth/mutations.py` implements the package's opt-in session-authentication mutation factories (`login_mutation()`, `logout_mutation()`, and `register_mutation()`) along with the phase-2.5 auth declaration and bind lifecycle (`bind_auth_mutations()`).

It owns:
1. **Mutation Factories & Declaration Ledger:**
   - Provides `login_mutation()`, `logout_mutation()`, and `register_mutation()` as opt-in factories.
   - Manages the auth declaration registry (`_auth_declaration_registry = make_declaration_registry(_AUTH_FAMILY_LABEL)`), cleared only on full registry reset (`registry.clear()`) via an owner-registered callback (`owner="auth.declarations"`).
   - Enforces the one-declaration-per-process rule via `_reject_conflicting_permission_classes`, caching identical declarations and raising `ConfigurationError` on conflicting `permission_classes`.
   - Re-registers declarations idempotently on reload, surviving pre-bind resets.
   - Rejects late declarations post-finalization with an actionable `ConfigurationError`.
2. **Fixed Auth Mutation Infrastructure:**
   - Synthesizes duck-typed permission holders (`_make_permission_holder`) holding `_AuthMutationMetaSnapshot`, delegating permission checks to `DjangoMutation.check_permission` and `mutations.resolvers.authorize_or_raise`.
   - Constructs Strawberry fields via `_make_auth_field` supporting dual-path dispatch (`in_async_context()`) with lazy payload type annotations (`_lazy_ref`).
3. **Transport Classification & Session Lifecycle Guarding:**
   - Coordinates with `django_strawberry_framework/auth/sessions.py` to classify transports (`DJANGO_HTTP`, `CHANNELS_HTTP`, `CHANNELS_WEBSOCKET`).
   - Runs `_transport_prologue` to enforce transport capabilities (e.g. rejecting login over WebSocket, rejecting logout over signed-cookie WebSocket) and require session middleware.
   - For `login`:
     - Runs permission check, lone-surrogate preflight check on credentials via `unencodable_text_error`, and `auth.authenticate()`.
     - Returns byte-identical failed-login envelope (`field_error("", _INCORRECT_CREDENTIALS_MESSAGE)`) on invalid credentials, inactive users, unstorable text, or unknown users (account-enumeration defense).
     - On success, builds payload before session mutation, establishes session (`auth.login` + `request.session.save()` for Django HTTP; `channels.auth.login` + `session.asave()` under `scope_session_lock` for Channels HTTP), and compensates fail-closed (anonymize actor + flush session) on exception.
   - For `logout`:
     - Captures actor presence (`_authenticated_actor_or_none`) and constructs payload before session mutation.
     - Performs unconditional teardown via `auth.logout()` for Django HTTP; `channels.auth.logout()` under `scope_session_lock` and `actor_transition` for Channels.
     - Returns `{ok: bool, errors: []}` reflecting prior authentication state while ensuring idempotent session cleanup.
4. **Registration Rider (`register_mutation`):**
   - Synthesizes `Register` rider inheriting from `DjangoMutation`, pinning public input name to `RegisterInput` and generating `RegisterPayload`.
   - Derives input fields via `derive_register_fields(user_model)` (`USERNAME_FIELD` + `REQUIRED_FIELDS` + `password`), rejecting account-control/privilege fields (`_REGISTER_PROTECTED_FIELDS`) and delegating field narrowing validation to `editable_input_fields`.
   - Intercepts `password` via `_REGISTER_EXCLUDED_INPUT_FIELDS` during input shape construction and decode (`_register_decode_step`), keeping raw password off model attributes while preserving the provided marker.
   - In `_register_write_step`: performs null and type checks, validates lone-surrogate preflight, executes Django password validation (`validate_password(raw_password, user)` with user instance context), hashes via `user.set_password()`, and delegates to `_model_write_step` (`full_clean` -> `save` -> M2M).
5. **Phase-2.5 Auth Bind (`bind_auth_mutations`):**
   - Executed by `types/finalizer.py` before `bind_mutations()`.
   - Resolves the primary `DjangoType` for `get_user_model()` via `_resolve_user_primary_or_raise`, distinguishing missing type declarations from multiple types without `Meta.primary`.
   - Materializes `LoginPayload`, model-less `LogoutPayload`, and `CurrentUserAlias` surface-by-surface based on active declarations, cleanly supporting partial/logout-only schemas without requiring a registered user type.

## Verification

1. Traced connections across callers, dependencies, and lifecycle points:
   - `django_strawberry_framework/auth/__init__.py`, `django_strawberry_framework/auth/queries.py`, `django_strawberry_framework/auth/sessions.py`
   - `django_strawberry_framework/types/finalizer.py` (`bind_auth_mutations` phase-2.5 invocation)
   - `django_strawberry_framework/mutations/inputs.py` (`build_payload_type`, `materialize_mutation_input_class`, `mutation_input_shape`)
   - `django_strawberry_framework/mutations/sets.py` (`DjangoMutation`, `make_declaration_registry`, `_validate_permission_classes`)
   - `django_strawberry_framework/mutations/resolvers.py` (`authorize_or_raise`, `_model_decode_step`, `_model_write_step`, `run_write_pipeline_sync`)
   - `django_strawberry_framework/utils/sessions.py` (`actor_transition`, `connection_actor_state`)
   - `django_strawberry_framework/utils/permissions.py` (`request_from_info`)
2. Evaluated existing permanent tests in `tests/auth/test_mutations.py` and `examples/fakeshop/test_query/test_auth_api.py`:
   - Declaration ledger survive/clear/reload lifecycles, duplicate declaration conflict raises, and post-finalization declaration rejections.
   - Surface-keyed user type resolution errors (missing user type, ambiguous multiple types).
   - Dual-path sync and async resolver dispatch, SDL signatures, and forward-ref resolution.
   - Transport error guards (WebSocket login rejection, signed-cookie WebSocket logout rejection, missing session middleware).
   - Account enumeration guards with byte-identical undifferentiated envelopes across unknown user, incorrect password, inactive user, and unstorable surrogate inputs.
   - Fail-closed session compensation and rollback on store/signal failures during login establishment and logout.
   - Register input derivation, protected field guards, password exclusion seam, password similarity validation with user context, and plaintext-never-persisted verification.
   - Synchronous permission execution and `SyncMisuseError` rejection on async `has_permission` hooks.
3. Executed focused test runs:
   - `uv run pytest tests/auth/ examples/fakeshop/test_query/test_auth_api.py --no-cov` (162 passed).
4. Executed scratch verification tests `docs/review/temp-tests/auth__mutations/test_scratch_auth_mutations.py`:
   - Verified `_AuthMutationMetaSnapshot` and `_make_permission_holder` metadata and attribute structure.
   - Verified `_declared_auth_surface` lookup, AllowAny default, and `_reject_conflicting_permission_classes` diagnostics.
   - Verified post-finalization declaration rejection.
   - Verified `derive_register_fields` on default model, custom model, duplicate fields, protected fields rejection (`is_active`, `is_staff`, `is_superuser`, `groups`, `user_permissions`), and unknown fields.
   - Verified `_authenticated_actor_or_none` classification across missing `user`, `AnonymousUser`, unauthenticated user, and authenticated user.
   - Verified `_failed_login_payload` shape and undifferentiated message contract.
   - Verified `_register_write_step` defensive checks (None password, non-string password, lone-surrogate password).
   - Verified `_django_http_login_establish` compensation: `request.user` reset to `AnonymousUser`, `session.flush()`, and chained exception propagation via `__context__`.
   - Verified `_django_http_logout` pre-observation capture and error handling.
   - Verified `_resolve_user_primary_or_raise` actionable messages for 0 registered types and multiple types without primary.
   - Verified `bind_auth_mutations` surface-keyed isolation (logout-only schema binding without `UserType`).
   - Result: 11 passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/auth/mutations.py` is an exemplary, secure, and robust implementation of session authentication for GraphQL. It meticulously enforces security invariants including account-enumeration prevention, fail-closed session rollback on transient store failures, transport-capability guards, strict password validation with unsaved instance context, surrogate Unicode protection, and clean lifecycle separation. No defects or design deficiencies found.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/auth/test_mutations.py`, `tests/auth/test_sessions.py`, `tests/auth/test_queries.py`, and `examples/fakeshop/test_query/test_auth_api.py`) comprehensively covers all declaration ledgers, surface-keyed binding, transport classification, enumeration defenses, session mutation atomicity, and registration password pipelines.
- Scratch verification:
  - `docs/review/temp-tests/auth__mutations/test_scratch_auth_mutations.py` passed (11/11 tests) verifying permission holders, conflict detection, post-finalization rejection, field derivation rules, actor classification, login envelope construction, registration validation and encoding defenses, login/logout fail-closed compensation, user primary resolution error diagnostics, and logout-only schema isolation.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/auth/mutations.py docs/review/temp-tests/auth__mutations/test_scratch_auth_mutations.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/auth/mutations.py` passed with 0 errors.
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Verification approach:
  - Confirmed the scoped diff against baseline HEAD (`12779c99`) for `django_strawberry_framework/auth/mutations.py` is empty (zero-edit cycle).
  - Independently re-traced the core auth mutation subsystem behaviors:
    1. Declaration ledger (`_auth_declaration_registry = make_declaration_registry(_AUTH_FAMILY_LABEL)`) with owner callback `owner="auth.declarations"` preserved across pre-bind resets and cleared only on full registry reset.
    2. Duck-typed permission holder synthesis (`_make_permission_holder`) and snapshot metadata (`_AuthMutationMetaSnapshot`) delegating to `DjangoMutation.check_permission` and `authorize_or_raise`.
    3. Transport capabilities prologue and session requirement enforcement (`_transport_prologue`).
    4. Login security architecture: undifferentiated failed login envelopes preventing user enumeration, preflight surrogate rejection, pre-mutation payload construction, and fail-closed session compensation (anonymizing `request.user` + `session.flush()`) with chained exception propagation.
    5. Logout invariants: pre-mutation actor observation, unconditional session flush, and Channels concurrency serialization via `scope_session_lock` outer and `actor_transition` inner locking.
    6. Registration rider (`Register` subclass of `DjangoMutation`): pinned public name `RegisterInput`, field derivation rejecting privilege flags (`_REGISTER_PROTECTED_FIELDS`), password exclusion seam (`_REGISTER_EXCLUDED_INPUT_FIELDS`), validation with user instance context (`validate_password(raw_password, user)`), and pre-clean hashing via `set_password()`.
    7. Phase-2.5 auth bind (`bind_auth_mutations`): primary user type resolution with clear diagnostic errors on missing/ambiguous types, and surface-keyed payload generation cleanly supporting logout-only schemas without registered user types.
- Findings assessment:
  - Confirmed zero findings. All invariants and edge cases are correctly designed and securely implemented.
- Test execution:
  - Executed focused permanent and scratch test suites:
    - `uv run pytest tests/auth/test_mutations.py docs/review/temp-tests/auth__mutations/test_scratch_auth_mutations.py --no-cov` -> 114 passed (103 permanent + 11 scratch).
    - `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov` -> 20 passed.
  - Executed linters and checks:
    - `uv run ruff check django_strawberry_framework/auth/mutations.py docs/review/temp-tests/auth__mutations/test_scratch_auth_mutations.py` -> 0 errors.
    - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/auth/mutations.py` -> 0 errors.
- Conclusion:
  - Verified `django_strawberry_framework/auth/mutations.py` without findings. Status is `verified`.

