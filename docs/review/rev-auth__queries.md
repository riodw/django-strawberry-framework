# Review: `django_strawberry_framework/auth/queries.py`

Status: verified

## Understanding

`django_strawberry_framework/auth/queries.py` implements the `current_user()` query-field factory and its return-alias namespace `CurrentUserAlias` (spec-040 Decision 7).

It owns:
1. **Query-Field Factory (`current_user`):**
   - Declares the read-side auth member as a fixed Strawberry query field returning the consumer's primary user `DjangoType | None`.
   - Records/re-records the declaration via `_declare_fixed_auth_surface("current_user", "CurrentUser", permission_classes)` into the auth declaration ledger with `AllowAny` default semantics and one-declaration-per-process conflict enforcement.
   - Attaches a lazy forward-reference return annotation `_lazy_ref(CURRENT_USER_ALIAS_NAME, AUTH_QUERIES_MODULE_PATH) | None` that resolves to the concrete `UserType` during schema construction.
2. **Return-Alias Namespace (`CurrentUserAlias`):**
   - Manages the `CurrentUserAlias` module global using the canonical `make_input_namespace` trio (`_current_user_alias_names`, `materialize_current_user_alias`, `clear_current_user_alias_namespace`).
   - Registers `clear_current_user_alias_namespace` as a pre-bind subsystem clear (`owner="auth.current_user_alias"`, `before_bind=True`) so the emit ledger is drained before each phase-2.5 bind (`bind_auth_mutations()`) re-pins the alias to the resolved user primary type.
3. **Actor Resolution & Permission Gating (`_current_user_resolve_body`):**
   - Resolves the request from `info` via `request_from_info(info, family_label=_AUTH_FAMILY_LABEL)`.
   - Determines the session actor via `_authenticated_actor_or_none(request)`, treating unauthenticated sessions, anonymous users, or absent request users as `None`.
   - Executes permission checks via `mutations.resolvers.authorize_or_raise(holder_cls, info, "current_user", None, instance=actor)`, raising a top-level `GraphQLError("Not authorized to current_user <UserType>.")` on denial.
   - Follows the actor-not-lookup rule (Decision 7, D-N1): returns the authenticated actor directly with no `get_queryset` re-run, so directory-level visibility hooks do not hide the logged-in user from themselves.
4. **Dual-Path Sync & Async Dispatch:**
   - On the sync path, executes `_current_user_resolve_body` directly.
   - On the async path, executes via `_sync_bridged_async_body` inside `run_in_one_sync_boundary`, ensuring lazy `SimpleLazyObject` user evaluation and permission gates execute cleanly in the sync worker thread without raising Django's `SynchronousOnlyOperation`.

## Verification

1. Traced connections across callers, dependencies, and lifecycle points:
   - `django_strawberry_framework/auth/__init__.py` (re-exports `current_user`)
   - `django_strawberry_framework/auth/mutations.py` (`_declare_fixed_auth_surface`, `_make_auth_field`, `_sync_bridged_async_body`, `_authenticated_actor_or_none`, `bind_auth_mutations`)
   - `django_strawberry_framework/types/finalizer.py` (phase-2.5 auth bind invocation)
   - `django_strawberry_framework/utils/inputs.py` (`make_input_namespace`, parked-global lifecycle)
   - `django_strawberry_framework/utils/permissions.py` (`request_from_info`)
   - `django_strawberry_framework/mutations/resolvers.py` (`authorize_or_raise`)
2. Evaluated existing permanent tests in `tests/auth/test_queries.py` and `examples/fakeshop/test_query/test_auth_api.py`:
   - `CurrentUserAlias` namespace lifecycle (`make_input_namespace` + pre-bind `register_subsystem_clear` row).
   - Injected lazy return annotation resolving to concrete `UserType` in SDL (`me: UserT`).
   - Surface-keyed `current_user`-only bind emitting no orphan login/logout payloads.
   - Missing user type / ambiguous primary type diagnostic error handling.
   - One-declaration-per-process conflict error on conflicting permission classes.
   - Sync and async resolver execution, spy verification, and `SimpleLazyObject` evaluation inside the sync boundary.
   - AllowAny default returning `null` for anonymous / absent request users and user instance for authenticated users.
   - Custom permission gates (`_IsAuthenticated`, etc.) denying anonymous callers with the exact pinned `GraphQLError` string.
   - Composition with `login_mutation` and verification that `get_queryset` visibility hooks do not hide the logged-in actor.
   - Live HTTP acceptance tests against fakeshop schema.
3. Executed focused test runs:
   - `uv run pytest tests/auth/test_queries.py examples/fakeshop/test_query/test_auth_api.py --no-cov` (33 passed).
4. Executed scratch verification tests `docs/review/temp-tests/auth__queries/test_scratch_auth_queries.py`:
   - Verified module constants and subsystem clear registration.
   - Verified `materialize_current_user_alias` and `clear_current_user_alias_namespace` parked-global semantics.
   - Verified `current_user` field construction with presentation kwargs (`description`, `deprecation_reason`).
   - Verified `_current_user_resolve_body` with anonymous, authenticated, and missing users.
   - Verified permission gate rejection and acceptance with custom permission classes.
   - Result: 5 passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/auth/queries.py` is a compact, robust, and well-designed query field factory. It cleanly delegates namespace management to `make_input_namespace`, authorization to `authorize_or_raise`, and async bridging to `_sync_bridged_async_body`, while strictly adhering to the actor-not-lookup rule (Decision 7). No defects or design deficiencies found.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/auth/test_queries.py` and `examples/fakeshop/test_query/test_auth_api.py`) thoroughly pins all behaviors: return-alias namespace lifecycle, SDL lazy forward-ref resolution, surface-keyed binding, sync/async execution, `SimpleLazyObject` forcing, AllowAny nullability contract, and custom permission gates.
- Scratch verification:
  - `docs/review/temp-tests/auth__queries/test_scratch_auth_queries.py` passed (5/5 tests) verifying subsystem clears, parked-global lifecycle, field metadata pass-through, direct resolve body execution across actor states, and gate evaluation.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/auth/queries.py docs/review/temp-tests/auth__queries/test_scratch_auth_queries.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/auth/queries.py` passed with 0 errors.
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Scoped diff verification:
  - Checked `git diff 12779c99 -- django_strawberry_framework/auth/queries.py`: confirmed empty diff against baseline HEAD (`12779c99`).
- Behavioral re-tracing:
  - Traced `current_user()` factory contract, parameter forwarding (`permission_classes`, `description`, `deprecation_reason`, `directives`), and lazy forward return annotation (`_lazy_ref(CURRENT_USER_ALIAS_NAME, AUTH_QUERIES_MODULE_PATH) | None`).
  - Traced return-alias namespace lifecycle managed by `make_input_namespace`, pre-bind subsystem clear registration (`owner="auth.current_user_alias"`, `before_bind=True`), and phase-2.5 bind materialization in `mutations.py` (`bind_auth_mutations`).
  - Traced actor resolution & authorization (`_current_user_resolve_body`), handling unauthenticated/absent/anonymous request users as `None`, evaluating permission gates via `authorize_or_raise`, and returning actor directly without re-querying (actor-not-lookup rule, spec-040 Decision 7, D-N1).
  - Traced async execution bridge via `_sync_bridged_async_body` inside `run_in_one_sync_boundary`, ensuring `SimpleLazyObject` resolution and permission checks occur cleanly without `SynchronousOnlyOperation`.
- Test execution:
  - Focused permanent suite + scratch suite: `uv run pytest tests/auth/test_queries.py examples/fakeshop/test_query/test_auth_api.py docs/review/temp-tests/auth__queries/test_scratch_auth_queries.py --no-cov` (38 passed in 17.84s).
  - Scratch tests verified parked-global lifecycle, subsystem clear registration, direct `_current_user_resolve_body` dispatch across actor states, and custom permission gates.
- Quality gates:
  - `uv run ruff check django_strawberry_framework/auth/queries.py docs/review/temp-tests/auth__queries/test_scratch_auth_queries.py` (passed, 0 errors).
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/auth/queries.py` (passed, 0 errors).
- Disposition:
  - Zero defects identified. All behavior and contracts verified independently. Review complete.

