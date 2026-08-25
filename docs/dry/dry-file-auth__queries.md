# DRY review: `django_strawberry_framework/auth/queries.py`

Status: verified

## System trace

`auth/queries.py` is the read-side member of the opt-in session-auth surface ([spec-040][spec-040] Decision 7). It provides the `current_user()` query-field factory, its resolver body `_current_user_resolve_body`, and the `CurrentUserAlias` bind-materialized return-type namespace via `AUTH_QUERIES_MODULE_PATH`. It owns three distinct responsibilities:

- **The `current_user` query field factory:** Declares the module-internal `CurrentUser` permission holder through [`auth/mutations.py::_declare_fixed_auth_surface`][auth-mutations] and synthesizes the field through [`auth/mutations.py::_make_auth_field`][auth-mutations]. It configures zero arguments and returns a nullable lazy forward-reference to [`CURRENT_USER_ALIAS_NAME`][auth-queries] (`_lazy_ref(CURRENT_USER_ALIAS_NAME, AUTH_QUERIES_MODULE_PATH) | None`), which Strawberry resolves to the primary user `DjangoType` at schema build.
- **The nullable-actor resolver body:** `_current_user_resolve_body` resolves the active request via [`utils/permissions.py::request_from_info`][utils-permissions] under `_AUTH_FAMILY_LABEL`, extracts the actor via [`auth/mutations.py::_authenticated_actor_or_none`][auth-mutations], runs permission gating via [`mutations/resolvers.py::authorize_or_raise`][mutations-resolvers] (`instance=actor`), and returns `actor` (the authenticated user instance or `None`). It enforces the actor-not-lookup rule ([spec-040][spec-040] D-N1): zero `get_queryset` re-runs and zero redundant ORM queries.
- **The `CurrentUserAlias` return namespace:** Creates the parked-global namespace trio `(_current_user_alias_names, materialize_current_user_alias, clear_current_user_alias_namespace)` via [`utils/inputs.py::make_input_namespace`][utils-inputs] using [`AUTH_QUERIES_MODULE_PATH`][auth-queries]. Registers `clear_current_user_alias_namespace` as a pre-bind clear callback via [`registry.py::register_subsystem_clear`][registry] (`before_bind=True`) so that the ledger is drained before phase-2.5 bind ([`auth/mutations.py::bind_auth_mutations`][auth-mutations]) pins the alias to the consumer's primary user `DjangoType`.

Connected behavior examined:
- [`auth/mutations.py`][auth-mutations]: Shared constants (`_AUTH_FAMILY_LABEL`), anonymity evaluation ([`_authenticated_actor_or_none`][auth-mutations]), fixed surface declaration ([`_declare_fixed_auth_surface`][auth-mutations]), unified field dispatch ([`_make_auth_field`][auth-mutations]), async boundary bridging ([`_sync_bridged_async_body`][auth-mutations]), and phase-2.5 schema binding ([`bind_auth_mutations`][auth-mutations]), which lazy-imports [`CURRENT_USER_ALIAS_NAME`][auth-queries] and `materialize_current_user_alias`.
- [`auth/sessions.py`][auth-sessions]: Transport classification and session validation.
- [`mutations/fields.py`][mutations-fields]: `_lazy_ref` and `build_lazy_field_signature`.
- [`mutations/resolvers.py`][mutations-resolvers]: `authorize_or_raise` and `run_in_one_sync_boundary`.
- [`utils/inputs.py`][utils-inputs]: `make_input_namespace` (single shared factory for parked-global class registries).
- [`utils/permissions.py`][utils-permissions]: `request_from_info`.
- [`registry.py`][registry]: `register_subsystem_clear`.
- [`tests/auth/test_queries.py`][test-queries], [`tests/auth/test_mutations.py`][test-mutations], [`examples/fakeshop/apps/accounts/schema.py`][accounts-schema], [`examples/fakeshop/test_query/test_auth_api.py`][test-auth-api].

## Verification

Static analysis and inventory (`export_dry_review.py audit`):
- Parsed 1 target file, 122 lines, 4 definitions (`AUTH_QUERIES_MODULE_PATH`, `CURRENT_USER_ALIAS_NAME`, `_current_user_resolve_body`, `current_user`), 9 imports.
- Checked reverse imports and confirmed all 4 definitions are referenced by production code and test suites.

Resolution of prior 0.0.13 deferral:
- In the 0.0.13 DRY review, a 2-line idiom (`getattr(request, "user", None)` and `.is_authenticated` checking) was identified across `_logout_resolve_body` and `_current_user_resolve_body` and deferred to the folder integration pass.
- In 0.0.14, that consolidation was completed at the root owner [`auth/mutations.py`][auth-mutations] via `_authenticated_actor_or_none(request)`. `_current_user_resolve_body` in this file and `_logout_resolve_body` in `mutations.py` both invoke `_authenticated_actor_or_none`, providing a single authoritative source of truth for request anonymity across the entire auth subsystem.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `current_user()` is the read-side counterpart of `login_mutation()` and `logout_mutation()`. It reuses the exact same declaration mechanism ([`_declare_fixed_auth_surface`][auth-mutations]), field construction ([`_make_auth_field`][auth-mutations]), lazy forward reference ([`_lazy_ref`][mutations-fields]), and permission gate evaluation ([`authorize_or_raise`][mutations-resolvers]). Unlike model query fields (which query querysets and execute `get_queryset`), `current_user` evaluates the session actor directly without queryset re-runs, adhering strictly to the actor-not-lookup rule ([spec-040][spec-040] D-N1).
2. **Sync and async twins:**
   Zero duplication. Both execution paths route through `_current_user_resolve_body`. The async resolver body is mechanically derived via [`_sync_bridged_async_body`][auth-mutations] using `run_in_one_sync_boundary(sync_body, info, **kwargs)`. This guarantees that forcing Django's `SimpleLazyObject` (`request.user`) inside `_current_user_resolve_body` runs within a single `sync_to_async(thread_sensitive=True)` worker, preventing `SynchronousOnlyOperation` without any parallel async resolver code.
3. **Derived rather than repeated knowledge:**
   The user model type is not hardcoded or redundantly queried at definition time. It is represented as a lazy forward reference to `CURRENT_USER_ALIAS_NAME` within `AUTH_QUERIES_MODULE_PATH`. During phase-2.5 schema finalization ([`auth/mutations.py::bind_auth_mutations`][auth-mutations]), the primary user `DjangoType` is resolved once via `_resolve_user_primary_or_raise` across all user-typed auth surfaces (`login`, `register`, `current_user`) and materialized into `CurrentUserAlias`. Anonymity is derived once via `_authenticated_actor_or_none`.
4. **Inverse and round-trip pairs:**
   Lifecycle pairing: `materialize_current_user_alias` sets the module global, while `clear_current_user_alias_namespace` drains it before re-binding (`register_subsystem_clear(before_bind=True)`).
   Auth session round-trip: `login_mutation` populates the session actor, `current_user` returns the authenticated actor, `logout_mutation` flushes the session, and subsequent `current_user` invocations return `None`. Verified in [`tests/auth/test_queries.py`][test-queries] and [`examples/fakeshop/test_query/test_auth_api.py`][test-auth-api].
5. **Contracts restated in another medium:**
   The `current_user` contract (nullable primary user type, AllowAny default, permission gating, no `get_queryset` rerun) is represented in:
   - Code: [`django_strawberry_framework/auth/queries.py`][auth-queries];
   - Specifications: [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040] (Decision 7, Decision 9, Decision 13);
   - Test suites: [`tests/auth/test_queries.py`][test-queries], [`examples/fakeshop/test_query/test_auth_api.py`][test-auth-api], [`tests/test_routers.py`][test-routers];
   - Example applications: [`examples/fakeshop/apps/accounts/schema.py`][accounts-schema];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary].

### The single-edit-site test

- **Posited change 1 (Anonymity classification):** Change how an unauthenticated request is detected (e.g. supporting an additional custom `AnonymousUser` protocol).
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/auth/mutations.py::_authenticated_actor_or_none`][auth-mutations]. Both `queries.py` and `mutations.py` inherit the change automatically.
  - *Site count:* 1.
- **Posited change 2 (Permission holder synthesis):** Modify how fixed auth surfaces declare or cache permission holders.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/auth/mutations.py::_declare_auth_surface`][auth-mutations].
  - *Site count:* 1.
- **Posited change 3 (Parked-global namespace management):** Update how input/alias class namespace trios are materialized or cleared.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/utils/inputs.py::make_input_namespace`][utils-inputs].
  - *Site count:* 1.
- **Posited change 4 (Query field signature & nullability):** Change `current_user()` presentation metadata or argument handling.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/auth/queries.py::current_user`][auth-queries].
  - *Site count:* 1.

### Rejected candidates

1. **Replacing `AUTH_QUERIES_MODULE_PATH` literal with `__name__`:**
   Disproved. `AUTH_QUERIES_MODULE_PATH = "django_strawberry_framework.auth.queries"` is a static module-level constant used for `make_input_namespace` and `_lazy_ref`. Six sibling modules use similar module-path constants. Each module path is an independent self-reference for `strawberry.lazy` / `sys.modules` lookups. Replacing it with `__name__` at one site without a package-wide pattern change provides no DRY consolidation benefit.
2. **Moving `CurrentUserAlias` namespace declaration into `auth/mutations.py`:**
   Disproved. `CurrentUserAlias` is a return-type alias specific to `current_user()`. Housing its parked-global namespace in `queries.py` keeps the read-side query field decoupled from the write mutations, avoiding unnecessary circular dependencies during module loading.
3. **Adding queryset filtering / `get_queryset` evaluation to `_current_user_resolve_body`:**
   Disproved. [spec-040][spec-040] Decision 7 and D-N1 explicitly establish that `current_user` returns the session actor already populated on the request, not an arbitrary model lookup. Re-running `get_queryset` would erroneously cause a logged-in user to receive `null` if directory visibility rules hide the user row.

## Opportunities

None — `django_strawberry_framework/auth/queries.py` is an exemplary 122-line implementation of the read-side session-auth query field. All shared invariants (field construction, lazy type references, permission authorization, async bridging, anonymity classification, and namespace lifecycle) are delegated to single authoritative owners ([`auth/mutations.py`][auth-mutations], [`mutations/fields.py`][mutations-fields], [`mutations/resolvers.py`][mutations-resolvers], [`utils/inputs.py`][utils-inputs], [`registry.py`][registry]).

## Judgment

Zero-edit review. `auth/queries.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/auth/queries.py --review docs/dry/dry-file-auth__queries.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent review and verification conducted on `django_strawberry_framework/auth/queries.py`:

1. **Connected behavior & subsystem contracts re-traced:**
   - **`current_user()` factory:** Verified that declaration metadata, permission holder construction (`CurrentUser`), and Strawberry field generation rely entirely on [`auth/mutations.py::_declare_fixed_auth_surface`][auth-mutations] and [`auth/mutations.py::_make_auth_field`][auth-mutations]. Zero duplication with mutation builders.
   - **`_current_user_resolve_body` resolver:** Verified extraction of the active request via [`utils/permissions.py::request_from_info`][utils-permissions] and authenticated actor resolution via [`auth/mutations.py::_authenticated_actor_or_none`][auth-mutations]. The actor-not-lookup rule ([spec-040][spec-040] D-N1) was challenged against potential model-query consolidation: confirmed that `current_user` must not execute `get_queryset` or query filters, preserving the actor contract even under restrictive directory visibility hooks (tested in [`tests/auth/test_queries.py::test_me_composes_with_login_in_one_schema_without_visibility_rerun`][test-queries]).
   - **Async boundary & lazy evaluation:** Verified that `_sync_bridged_async_body` ensures `_current_user_resolve_body` executes inside `run_in_one_sync_boundary`, resolving Django's `SimpleLazyObject` within the worker thread to eliminate `SynchronousOnlyOperation` without parallel async logic.
   - **`CurrentUserAlias` namespace lifecycle:** Re-traced `make_input_namespace(AUTH_QUERIES_MODULE_PATH, _AUTH_FAMILY_LABEL)` and pre-bind hook registration via [`registry.py::register_subsystem_clear`][registry] (`owner="auth.current_user_alias", before_bind=True`). Pre-bind clearing prevents stale alias objects across multiple schema builds and test isolation cycles.

2. **Duplication matrix & single-edit-site counts verified:**
   - All 5 axes of the mandatory duplication probing matrix were evaluated and confirmed to be fully discharged.
   - Posited single-edit-site counts for anonymity classification, permission holder synthesis, namespace management, and query signature modifications were verified at exactly 1 site each.
   - Rejected candidates 1 through 3 were independently verified as sound design decisions.

3. **Tool check and test suite execution:**
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/auth/queries.py --review docs/dry/dry-file-auth__queries.md --include-constants`, confirming all 4 definitions are covered with 0 missing topics.
   - Executed full test suite (`pytest`), with 6,450 passed tests and 100.0% coverage maintained.

Review verified. Updating `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md

<!-- docs/SPECS/ -->
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-init]: ../../django_strawberry_framework/auth/__init__.py
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-queries]: ../../django_strawberry_framework/auth/queries.py
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py

<!-- tests/ -->
[test-mutations]: ../../tests/auth/test_mutations.py
[test-queries]: ../../tests/auth/test_queries.py
[test-routers]: ../../tests/test_routers.py

<!-- examples/ -->
[accounts-schema]: ../../examples/fakeshop/apps/accounts/schema.py
[test-auth-api]: ../../examples/fakeshop/test_query/test_auth_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
