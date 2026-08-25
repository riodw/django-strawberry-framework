# DRY review: `django_strawberry_framework/auth/`

Status: verified

## System trace

`django_strawberry_framework/auth/` is the opt-in session-authentication subpackage ([spec-040][spec-040], [spec-046][spec-046]). It provides GraphQL field factories and runtime execution machinery for session-based user authentication across heterogeneous transports (Django HTTP, Channels HTTP, Channels WebSocket). The package root deliberately avoids importing or re-exporting `auth` to ensure that consumers who do not use authentication never pay the cost of importing `django.contrib.auth` or initializing auth subsystems.

The subpackage comprises four modules whose responsibilities and inter-module boundaries are strictly partitioned:

1. [`auth/__init__.py`][auth-init]: The public opt-in export facade. Re-exports the four public GraphQL field factories: [`login_mutation`][auth-mutations], [`logout_mutation`][auth-mutations], [`register_mutation`][auth-mutations], and [`current_user`][auth-queries]. Contains zero runtime logic or global state.
2. [`auth/mutations.py`][auth-mutations]: Session-auth mutation factories, mutation pipeline integration, declaration ledgers, and phase-2.5 schema binding:
   - **Fixed auth declaration ledger & conflict management:** Manages `_auth_declaration_registry` ([`_AUTH_FAMILY_LABEL`][auth-mutations]) via [`mutations/sets.py::make_declaration_registry`][mutations-sets], exporting [`register_auth_mutation`][auth-mutations], [`clear_auth_mutation_registry`][auth-mutations], [`iter_auth_mutations`][auth-mutations], and storing declarations in `_auth_declarations`. Enforces single-declaration-per-process semantics via [`_declared_auth_surface`][auth-mutations] and [`_reject_conflicting_permission_classes`][auth-mutations] (citing [`_SURFACE_FACTORY_NAMES`][auth-mutations]). Synthesizes lightweight permission carriers via [`_AuthMutationMetaSnapshot`][auth-mutations] ([`_AuthMutationMetaSnapshot.__init__`][auth-mutations]), [`_make_permission_holder`][auth-mutations], [`_declare_auth_surface`][auth-mutations], and [`_declare_fixed_auth_surface`][auth-mutations].
   - **Unified field construction & async dispatch:** [`_make_auth_field`][auth-mutations] constructs Strawberry fields with signatures built via [`mutations/fields.py::build_lazy_field_signature`][mutations-fields] and [`mutations/fields.py::_lazy_ref`][mutations-fields]. Bridges sync bodies to async workers via [`_sync_bridged_async_body`][auth-mutations] utilizing [`utils/querysets.py::run_in_one_sync_boundary`][utils-querysets].
   - **Anonymity evaluation & error envelopes:** Evaluates actor presence via [`_authenticated_actor_or_none`][auth-mutations]. Constructs undifferentiated failed-login envelopes ([`_INCORRECT_CREDENTIALS_MESSAGE`][auth-mutations]) via [`_failed_login_payload`][auth-mutations] and [`_login_result_payload`][auth-mutations] using [`mutations/resolvers.py::field_error`][mutations-resolvers] and [`mutations/resolvers.py::build_payload`][mutations-resolvers].
   - **Login & logout state machines:** Enforces transport classification and session presence via [`_transport_prologue`][auth-mutations] (raising [`_WEBSOCKET_LOGIN_UNSUPPORTED`][auth-mutations] or [`_WEBSOCKET_LOGOUT_UNSUPPORTED`][auth-mutations]). Coordinates synchronous authentication via [`_login_authenticate`][auth-mutations], establishing sessions via [`_django_http_login_establish`][auth-mutations] and [`_channels_http_login_establish`][auth-mutations] under [`_login_resolve_body`][auth-mutations] and [`_login_resolve_body_async`][auth-mutations]. Coordinates logout state via [`_logout_prologue`][auth-mutations], capturing pre-teardown state via [`_logout_observation`][auth-mutations], executing teardown via [`_django_http_logout`][auth-mutations] and [`_channels_logout`][auth-mutations] under [`_logout_resolve_body`][auth-mutations] and [`_logout_resolve_body_async`][auth-mutations]. Exposes [`login_mutation`][auth-mutations] and [`logout_mutation`][auth-mutations].
   - **Registration rider (`DjangoMutation` integration):** Derives model fields via [`derive_register_fields`][auth-mutations] (protecting [`_REGISTER_PROTECTED_FIELDS`][auth-mutations] and delegating to [`mutations/inputs.py::editable_input_fields`][mutations-inputs]). Implements [`_register_decode_step`][auth-mutations] (excluding [`_REGISTER_EXCLUDED_INPUT_FIELDS`][auth-mutations] via [`mutations/resolvers.py::_model_decode_step`][mutations-resolvers]), [`_register_write_step`][auth-mutations] (validating and hashing passwords), [`_run_register_pipeline_sync`][auth-mutations] (riding [`mutations/resolvers.py::run_write_pipeline_sync`][mutations-resolvers]), and [`_synthesize_register_rider`][auth-mutations] (pinning [`_REGISTER_INPUT_NAME`][auth-mutations] and generating inputs via [`mutations/inputs.py::build_mutation_input`][mutations-inputs]). Exposes [`register_mutation`][auth-mutations].
   - **Phase-2.5 schema binding:** [`bind_auth_mutations`][auth-mutations] resolves the primary user type via [`_resolve_user_primary_or_raise`][auth-mutations] and materializes `LoginPayload`, `LogoutPayload` via [`mutations/inputs.py::build_payload_type`][mutations-inputs] and [`mutations/inputs.py::materialize_mutation_input_class`][mutations-inputs], and the query alias via [`auth/queries.py::materialize_current_user_alias`][auth-queries].
3. [`auth/queries.py`][auth-queries]: The read-side session actor field factory:
   - Provides [`current_user`][auth-queries] query field returning nullable primary user `DjangoType` forward-referenced via [`CURRENT_USER_ALIAS_NAME`][auth-queries] within [`AUTH_QUERIES_MODULE_PATH`][auth-queries].
   - Implements [`_current_user_resolve_body`][auth-queries] evaluating [`utils/permissions.py::request_from_info`][utils-permissions], [`auth/mutations.py::_authenticated_actor_or_none`][auth-mutations], and [`mutations/resolvers.py::authorize_or_raise`][mutations-resolvers] without executing `get_queryset` or database queries (the actor-not-lookup rule, [spec-040][spec-040] D-N1).
   - Manages parked-global alias namespace trio (`_current_user_alias_names`, [`materialize_current_user_alias`][auth-queries], [`clear_current_user_alias_namespace`][auth-queries]) via [`utils/inputs.py::make_input_namespace`][utils-inputs], registered with [`registry.py::register_subsystem_clear`][registry] (`before_bind=True`).
4. [`auth/sessions.py`][auth-sessions]: Transport classification, capability boundary, and scope-level concurrency control:
   - Defines [`Transport`][auth-sessions] (`DJANGO_HTTP`, `CHANNELS_HTTP`, `CHANNELS_WEBSOCKET`).
   - Classifies request objects via [`classify_transport`][auth-sessions], lazily resolving Channels via [`require_channels`][auth-sessions] with [`_CHANNELS_INSTALL_HINT`][auth-sessions] via [`utils/imports.py::require_optional_module`][utils-imports].
   - Validates session middleware via [`require_session`][auth-sessions].
   - Manages ASGI scope concurrency locking via [`scope_session_lock`][auth-sessions] and [`_require_mutable_scope`][auth-sessions] under [`_SCOPE_LOCK_KEY`][auth-sessions].
   - Introspects session engine backend capabilities via [`uses_signed_cookie_sessions`][auth-sessions] and provides capability predicates [`login_supported`][auth-sessions] and [`logout_supported`][auth-sessions].

Connected subsystem integration examined:
- [`types/finalizer.py`][types-finalizer]: Injects phase-2.5 schema binding via `loaded_attr("django_strawberry_framework.auth.mutations", "bind_auth_mutations")`, preserving the zero-import opt-in invariant while guaranteeing auth payloads and aliases are materialized before `bind_mutations()` and `strawberry.Schema` build.
- [`utils/sessions.py`][utils-sessions]: Houses engine lookup (`session_store_class`) and WebSocket connection actor lease mechanics (`ConnectionActorState`, `actor_lease`, `actor_transition`, `note_authenticated_actor`, `connection_was_authenticated`) separately from `auth/sessions.py` so that [`consumers.py`][consumers] can validate WebSocket connection actor leases without importing `auth` and inadvertently triggering GraphQL schema registration.
- [`consumers.py`][consumers]: Uses connection actor leasing for frame revalidation, strictly maintaining the acyclic total lock order: `scope_session_lock` (outer, auth mutation) -> `actor_transition` / `actor_lease` (inner, frame transmission).
- [`mutations/`][mutations-resolvers]: Shared field construction (`build_lazy_field_signature`, `_lazy_ref`), mutation pipeline (`run_write_pipeline_sync`, `_model_decode_step`, `_model_write_step`), permission checking (`authorize_or_raise`), and payload construction (`build_payload`, `field_error`).
- [`utils/write_values.py`][utils-write-values]: Preflight storability error validation (`unencodable_text_error`) shared across login credentials and registration password inputs.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/auth/ --include-constants`):
- Parsed 4 target files (`__init__.py`, `mutations.py`, `queries.py`, `sessions.py`), 1,657 total lines.
- Inventoried 45 code definitions and 20 module-level constants; confirmed all definitions and reverse imports across production, test suites, and examples.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - *Fixed auth fields vs model/form mutations:* Fixed auth fields (`login`, `logout`, `current_user`) share declaration resolution ([`_declare_auth_surface`][auth-mutations]), holder synthesis ([`_make_permission_holder`][auth-mutations]), and lazy field signature generation ([`_make_auth_field`][auth-mutations]) with zero redundant mutation-set boilerplate. `register_mutation` integrates seamlessly as a `DjangoMutation` rider ([`_synthesize_register_rider`][auth-mutations]) reusing the model decode/write pipeline while isolating password hashing and protection rules ([`_REGISTER_PROTECTED_FIELDS`][auth-mutations]).
   - *Actor resolution vs querysets:* `current_user` evaluates session identity directly via [`_authenticated_actor_or_none`][auth-mutations], obeying the actor-not-lookup rule ([spec-040][spec-040] D-N1) without re-running `get_queryset` or duplicating model query resolution.
   - *Error handling & permission gates:* All auth surfaces reuse [`mutations/resolvers.py::authorize_or_raise`][mutations-resolvers] and [`mutations/resolvers.py::field_error`][mutations-resolvers], adhering to the package's unified GraphQL error format.
2. **Sync and async twins:**
   - *Async resolver bridging:* `current_user` and `register_mutation` use a single synchronous resolver body bridged to async execution via [`_sync_bridged_async_body`][auth-mutations] and [`utils/querysets.py::run_in_one_sync_boundary`][utils-querysets]. This runs Django's `SimpleLazyObject` evaluation inside a thread-sensitive worker, eliminating `SynchronousOnlyOperation` without maintaining duplicate async resolver implementations.
   - *Transport-specific login/logout flows:* The preflight, permission, and authentication prologues ([`_login_authenticate`][auth-mutations], [`_logout_prologue`][auth-mutations]) are 100% shared synchronous pipelines. Native Channels asynchronous execution paths (`_channels_http_login_establish`, `_channels_logout`) operate directly on the event loop under [`scope_session_lock`][auth-sessions], while sync execution bridges via `async_to_sync` at the transport edge, avoiding parallel sync/async lock implementations.
3. **Derived rather than repeated knowledge:**
   - *Single anonymity definition:* [`_authenticated_actor_or_none`][auth-mutations] is the sole authority for request anonymity across all auth fields, eliminating redundant `getattr(request, "user", None)` and `.is_authenticated` checks.
   - *Family label:* [`_AUTH_FAMILY_LABEL`][auth-mutations] (`"AuthMutation"`) provides unified naming for request resolution (`request_from_info`) and declaration ledgers.
   - *User type resolution:* Primary `DjangoType` resolution is derived once via [`_resolve_user_primary_or_raise`][auth-mutations] during phase 2.5 schema binding ([`bind_auth_mutations`][auth-mutations]) and distributed across `LoginPayload`, `RegisterPayload`, and `CurrentUserAlias`.
   - *Registration field derivation:* [`derive_register_fields`][auth-mutations] computes `USERNAME_FIELD` + `REQUIRED_FIELDS` + `"password"`, validating against `_REGISTER_PROTECTED_FIELDS` and delegating field sanity checks to [`mutations/inputs.py::editable_input_fields`][mutations-inputs].
   - *Session capabilities:* [`uses_signed_cookie_sessions`][auth-sessions] derives engine properties via `issubclass(session_store_class(), SignedCookieSessionStore)`, and [`logout_supported`][auth-sessions] gates WebSocket logout directly from that derived property.
4. **Inverse and round-trip pairs:**
   - *Declaration & emit ledger lifecycles:* `_auth_declaration_registry` registers a full-clear callback surviving pre-bind resets, while `CurrentUserAlias` registers a pre-bind clear callback ([`clear_current_user_alias_namespace`][auth-queries]), ensuring clean re-materialization during schema rebuilds without ledger leakage.
   - *Session lifecycle round-trip:* `login_mutation` authenticates and establishes sessions (`_django_http_login_establish` / `_channels_http_login_establish`), `current_user` observes authenticated actors, and `logout_mutation` tears down sessions (`_django_http_logout` / `_channels_logout`), returning subsequent `current_user` calls to `None`.
   - *Scope lock lifecycle:* [`scope_session_lock`][auth-sessions] guarantees balanced `async with` acquire/release semantics over `_SCOPE_LOCK_KEY`.
5. **Contracts restated in another medium:**
   - The auth subsystem contracts are consistently documented and verified across:
     - Specifications: [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040] (Decisions 3, 5, 6, 7, 8, 9, 11, 12, 13) and [`docs/SPECS/spec-046-transport_security-0_0_14.md`][spec-046] (Decisions 10, 11, Security Invariant 12);
     - Code implementations: [`django_strawberry_framework/auth/`][auth-init], [`django_strawberry_framework/utils/sessions.py`][utils-sessions], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/consumers.py`][consumers];
     - Comprehensive test suites: [`tests/auth/test_mutations.py`][test-mutations], [`tests/auth/test_queries.py`][test-queries], [`tests/auth/test_sessions.py`][test-sessions], [`tests/test_routers.py`][test-routers];
     - Example applications: [`examples/fakeshop/apps/accounts/schema.py`][accounts-schema], [`examples/fakeshop/test_query/test_auth_api.py`][test-auth-api];
     - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary].

### The single-edit-site test

- **Posited change 1 (Anonymity classification):** Update the definition of an unauthenticated actor (e.g. supporting an additional custom anonymous user type).
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/auth/mutations.py::_authenticated_actor_or_none`][auth-mutations]. All read/write auth fields inherit the update immediately.
  - *Site count:* 1.
- **Posited change 2 (Auth family label & request resolution):** Modify the family label used for auth request resolution and declaration tracking.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/auth/mutations.py::_AUTH_FAMILY_LABEL`][auth-mutations].
  - *Site count:* 1.
- **Posited change 3 (Primary user type resolution in schema binding):** Adjust how primary user `DjangoType` ambiguity is reported or resolved during schema finalize.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/auth/mutations.py::_resolve_user_primary_or_raise`][auth-mutations].
  - *Site count:* 1.
- **Posited change 4 (Transport classification & soft dependency loading):** Add a new ASGI protocol kind or change the Channels installation diagnostic hint.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/auth/sessions.py::classify_transport`][auth-sessions] / [`django_strawberry_framework/auth/sessions.py::_CHANNELS_INSTALL_HINT`][auth-sessions].
  - *Site count:* 1.
- **Posited change 5 (Registration account-control field protection):** Add an additional account-control flag (e.g. `is_verified`) to server-protected fields disallowed from client registration inputs.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS`][auth-mutations].
  - *Site count:* 1.

### Rejected candidates

1. **Merging `auth/sessions.py` into `utils/sessions.py`:**
   - Disproved. `utils/sessions.py` must remain lightweight and channels-free so that `consumers.py` can import `session_store_class` and `actor_lease` without importing `auth` (which would eagerly register GraphQL auth mutations and types before the consumer opts in).
2. **Merging `auth/queries.py` into `auth/mutations.py`:**
   - Disproved. Keeping `current_user` in `queries.py` preserves a clean separation between read queries and write mutations, mirrors GraphQL schema conventions, and isolates the `CurrentUserAlias` return namespace.
3. **Consolidating `_SCOPE_LOCK_KEY` and connection `actor_lease` into a single global lock:**
   - Disproved. `scope_session_lock` in `auth/sessions.py` serializes session write mutations (outer lock), while `actor_lease` in `utils/sessions.py` manages transport frame revalidation (inner lock). Merging them would cause frame sending to block unnecessarily on long-running session operations and introduce circular dependencies between auth and consumers.

## Opportunities

None — The folder integration of `django_strawberry_framework/auth/` is architecturally clean, robustly tested, and fully consolidated at root owners. Cross-file boundaries between `__init__.py`, `mutations.py`, `queries.py`, and `sessions.py`, as well as integration boundaries with `utils/sessions.py`, `consumers.py`, `types/finalizer.py`, and `mutations/`, are strictly defined and honor all repository and security invariants.

## Judgment

Zero-edit folder integration review. All 4 files in `django_strawberry_framework/auth/` operate in total structural alignment. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. Subpackage folder integration verified clean and complete. Checked with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/auth/ --review docs/dry/dry-folder-auth.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification conducted by Worker 2 on 2026-08-24.

### Trace and boundary audit

1. **Subpackage Boundary Isolation and Zero-Import Guarantee:**
   - [`auth/__init__.py`][auth-init] acts purely as an export facade re-exporting [`login_mutation`][auth-mutations], [`logout_mutation`][auth-mutations], [`register_mutation`][auth-mutations], and [`current_user`][auth-queries]. It contains zero global state or runtime logic.
   - The package root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] strictly omits importing `auth`, ensuring that projects not using GraphQL auth mutations never incur the cost of importing `django.contrib.auth` or registering auth types.
   - [`types/finalizer.py`][types-finalizer] accesses phase-2.5 schema binding via `loaded_attr("django_strawberry_framework.auth.mutations", "bind_auth_mutations")`, perfectly preserving the zero-import opt-in contract while guaranteeing that when auth is imported, its payloads (`LoginPayload`, `LogoutPayload`) and return alias (`CurrentUserAlias`) materialize prior to `bind_mutations()` and `strawberry.Schema` compilation.

2. **Cross-Subsystem Cleanliness (`utils/sessions.py` vs `auth/sessions.py`):**
   - Re-verified the separation of `utils/sessions.py` and `auth/sessions.py`. `utils/sessions.py` owns the engine lookup (`session_store_class`) and WebSocket connection actor lease mechanics (`ConnectionActorState`, `actor_lease`, `actor_transition`, `note_authenticated_actor`, `connection_was_authenticated`).
   - This architectural split allows [`consumers.py`][consumers] to perform WebSocket connection actor revalidation without importing `auth` and inadvertently triggering GraphQL schema mutation registrations.
   - The lock hierarchy across subsystems is strictly acyclic and total: `scope_session_lock` (outer, auth mutation) -> `actor_transition` / `actor_lease` (inner, frame send). Revalidation checkpoints in `consumers.py` never request `scope_session_lock`, making deadlock impossible.

3. **Duplication Probing Matrix Verification:**
   - **Axis 1 (Cross-flavor policy mirroring):** Fixed auth fields (`login`, `logout`, `current_user`) share declaration resolution ([`_declare_auth_surface`][auth-mutations]), holder synthesis ([`_make_permission_holder`][auth-mutations]), and lazy field signature generation ([`_make_auth_field`][auth-mutations]). `register_mutation` integrates cleanly as a `DjangoMutation` rider ([`_synthesize_register_rider`][auth-mutations]), reusing the model decode/write pipeline while isolating password hashing and protection rules. `current_user` queries session identity directly via [`_authenticated_actor_or_none`][auth-mutations] obeying the actor-not-lookup rule ([spec-040][spec-040] D-N1). Error envelopes and permission gates reuse [`mutations/resolvers.py::authorize_or_raise`][mutations-resolvers] and [`mutations/resolvers.py::field_error`][mutations-resolvers].
   - **Axis 2 (Sync and async twins):** Synchronous resolver bodies for `current_user` and `register_mutation` are bridged to async via [`_sync_bridged_async_body`][auth-mutations] and [`utils/querysets.py::run_in_one_sync_boundary`][utils-querysets], eliminating code duplication while keeping lazy object evaluation safely inside thread-sensitive workers. Login and logout flows share 100% of their synchronous preflight and authentication pipelines ([`_login_authenticate`][auth-mutations], [`_logout_prologue`][auth-mutations]), with native Channels async paths ([`_channels_http_login_establish`][auth-mutations], [`_channels_logout`][auth-mutations]) operating under [`scope_session_lock`][auth-sessions] and sync execution bridging at the transport boundary via `async_to_sync`.
   - **Axis 3 (Derived rather than repeated knowledge):** Single anonymity definition at [`_authenticated_actor_or_none`][auth-mutations]; single auth family label at [`_AUTH_FAMILY_LABEL`][auth-mutations]; primary user `DjangoType` derived once at [`_resolve_user_primary_or_raise`][auth-mutations]; registration fields derived via [`derive_register_fields`][auth-mutations]; session engine backend capabilities derived via [`uses_signed_cookie_sessions`][auth-sessions].
   - **Axis 4 (Inverse and round-trip pairs):** Declaration and emit ledger lifecycles properly partitioned between pre-bind and full-clear registrations; full session lifecycle round-trip (login establish -> current_user observe -> logout teardown) verified; scope lock context management verified.
   - **Axis 5 (Contracts restated across media):** Verified consistency across specifications ([spec-040][spec-040], [spec-046][spec-046]), code implementations, test suites ([test-mutations][test-mutations], [test-queries][test-queries], [test-sessions][test-sessions]), examples ([accounts-schema][accounts-schema], [test-auth-api][test-auth-api]), and standing documentation ([readme][readme], [glossary][glossary]).

4. **Single-Edit-Site Test Confirmation:**
   - Anonymity classification: 1 site ([`_authenticated_actor_or_none`][auth-mutations]).
   - Auth family label: 1 site ([`_AUTH_FAMILY_LABEL`][auth-mutations]).
   - Primary user type resolution: 1 site ([`_resolve_user_primary_or_raise`][auth-mutations]).
   - Transport classification & soft-dependency loading: 1 site ([`classify_transport`][auth-sessions] / [`_CHANNELS_INSTALL_HINT`][auth-sessions]).
   - Registration account-control field protection: 1 site ([`_REGISTER_PROTECTED_FIELDS`][auth-mutations]).

5. **Tooling & Test Suite Pass:**
   - Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/auth/ --review docs/dry/dry-folder-auth.md --include-constants` -> Passed (57 target definitions, 0 required topics covered).
   - Ran full test suite -> All 5,529 tests passed.

### Conclusion

Worker 1's DRY review for the folder integration of `django_strawberry_framework/auth/` is thorough, accurate, and completely verified. Zero code edits required. Marking review `Status: verified`.

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
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[routers]: ../../django_strawberry_framework/routers.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-sessions]: ../../django_strawberry_framework/utils/sessions.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-mutations]: ../../tests/auth/test_mutations.py
[test-queries]: ../../tests/auth/test_queries.py
[test-sessions]: ../../tests/auth/test_sessions.py
[test-routers]: ../../tests/test_routers.py

<!-- examples/ -->
[accounts-schema]: ../../examples/fakeshop/apps/accounts/schema.py
[test-auth-api]: ../../examples/fakeshop/test_query/test_auth_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
