# DRY review: `django_strawberry_framework/mutations/permissions.py`

Status: verified

## System trace

`django_strawberry_framework/mutations/permissions.py` is the write-side authorization engine and default permission class module of the framework ([spec-036][spec-036] Decision 15, [spec-038][spec-038] Decision 11, [spec-040][spec-040] Decision 5, [spec-046][spec-046]).

It establishes write authorization as a **first-class, independent contract from read-side row visibility** ([`permissions.py::apply_cascade_permissions`][permissions], [spec-036][spec-036] Decision 10):
- `get_queryset` answers *"may this caller see this row"*;
- `check_permission` / [`DjangoModelPermission`][mutations-permissions] answers *"may this caller write it"* ("can view" is never "can write").

1. **Architecture & Enforcement Placement:**
   - **Operation-to-Action Mapping:** Maps GraphQL mutation operations (`"create"`, `"update"`, `"delete"`) to Django model permission action verbs (`"add"`, `"change"`, `"delete"`), single-sited in [`_OPERATION_PERMISSION_ACTION`][mutations-permissions]. Matches Django's standard `Permission` codename format (`<app_label>.<action>_<model_name>`) and DRF's `DjangoModelPermissions` `perms_map` conventions.
   - **Enforcement Pipeline Seam:** Write authorization is evaluated during mutation resolution ([`resolvers.py::authorize_or_raise`][mutations-resolvers], [spec-036][spec-036] Decision 8 step 3):
     - For `create`: evaluated *before* validation or object instantiation;
     - For `update` and `delete`: evaluated *after* object location via visibility-scoped `get_queryset`, ensuring hidden rows return a not-found `FieldError` on `id` rather than leaking existence via an authorization denial signal.
   - **Top-Level Authorization Failures:** A permission denial returns `False` from `check_permission`, which [`authorize_or_raise`][mutations-resolvers] maps directly to a top-level `GraphQLError` (nulling the mutation field), keeping authorization failures strictly separate from the field-keyed [`FieldError`][mutations-inputs] validation error envelope.

2. **Sync-Bool Enforcement & Auth Hardening (0.0.14):**
   - **Strict Result Contract:** [`_require_sync_bool_auth_result`][mutations-permissions] defines the single result validation contract shared across write authorization seams ([`run_permission_classes`][mutations-permissions], [`DjangoModelPermission.has_permission`][mutations-permissions], and [`resolvers.py::authorize_or_raise`][mutations-resolvers]).
   - **Bypass Prevention:** Every permission hook, override, and `user.has_perm` call must return a synchronous `bool`. Under Python truthiness semantics, a coroutine object (`async def`) or non-bool object is truthy; treating a coroutine as truthy would silently interpret an async deny check as "allow" (an authorization bypass).
   - **Recourse & Misuse Handling:** Coroutines and awaitables are intercepted via [`reject_async_in_sync_context`][utils-querysets], closed, and raised as a typed `SyncMisuseError` with actionable remediation guidance from [`_PERMISSION_ASYNC_RECOURSE`][mutations-permissions]. Non-bool return values raise a [`ConfigurationError`][exceptions] with safe representation formatting via `_safe_arg_repr`.

3. **Multi-Flavor Permission Execution:**
   - [`run_permission_classes`][mutations-permissions]: The single execution loop behind the default `check_permission` implementation for both [`DjangoMutation`][mutations-sets] (and its subclasses [`DjangoModelFormMutation`][forms-sets], [`SerializerMutation`][rest-framework-sets]) and [`DjangoFormMutation`][forms-sets] (which does not subclass `DjangoMutation`). It iterates `Meta.permission_classes`, calls `permission_class().has_permission(info, type(mutation_self), operation, data, instance)`, validates each result via [`_require_sync_bool_auth_result`][mutations-permissions], short-circuits to `False` on the first denial, and returns `True` only when all classes allow.

4. **Permission Classes:**
   - [`DjangoModelPermission`][mutations-permissions]: The canonical default member of `Meta.permission_classes` for model-backed writes.
     - [`DjangoModelPermission.has_permission`][mutations-permissions]: Extracts the request via [`request_from_info(info, family_label="DjangoMutation")`][utils-permissions], extracts `request.user` (returning `False` if `None`), resolves the target model via `mutation._resolve_model(mutation.Meta)`, derives the permission codename `f"{model._meta.app_label}.{action}_{model._meta.model_name}"`, invokes `user.has_perm(codename)`, and validates the return value through [`_require_sync_bool_auth_result`][mutations-permissions]. Unauthenticated / `AnonymousUser` callers hold no permissions and are denied by default.
   - [`DenyAll`][mutations-permissions]: The safe deny-by-default permission class for model-less plain form mutations ([`DjangoFormMutation`][forms-sets], [spec-038][spec-038] Decision 11).
     - [`DenyAll.has_permission`][mutations-permissions]: Always returns `False`. Because a plain form has no model, `DjangoModelPermission` cannot resolve a model codename; plain forms default to `[DenyAll]`, requiring explicit consumer opt-in `Meta.permission_classes = []` (AllowAny posture) for public endpoints.

Connected behavior examined:
- [`django_strawberry_framework/mutations/sets.py`][mutations-sets]: Base `DjangoMutation` defining `_validate_permission_classes`, `model_backed_permission_and_lock`, and default `check_permission` delegating to `run_permission_classes`.
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Mutation execution pipelines (`resolve_mutation_sync`, `resolve_mutation_async`) and `authorize_or_raise` invoking `check_permission` and `_require_sync_bool_auth_result`.
- [`django_strawberry_framework/forms/sets.py`][forms-sets]: `DjangoFormMutation` (defaulting `Meta.permission_classes` to `[DenyAll]` and delegating `check_permission` to `run_permission_classes`) and `DjangoModelFormMutation` (subclassing `DjangoMutation` and inheriting `DjangoModelPermission`).
- [`django_strawberry_framework/rest_framework/sets.py`][rest-framework-sets]: `SerializerMutation` subclassing `DjangoMutation` and inheriting `DjangoModelPermission`.
- [`django_strawberry_framework/auth/mutations.py`][auth-mutations]: Session auth mutation factories (`login_mutation`, `logout_mutation`, `register_mutation`) defaulting to `permission_classes = []` (AllowAny inversion) while delegating execution through `resolvers.authorize_or_raise`.
- [`django_strawberry_framework/auth/queries.py`][auth-queries]: `current_user` query factory utilizing `resolvers.authorize_or_raise`.
- [`django_strawberry_framework/utils/permissions.py`][utils-permissions]: Shared `request_from_info` extracting Django `HttpRequest`, Channels ASGI scopes (`ChannelsRequestAdapter`), and mapping contexts across read and write subsystems; `auth_aliases_for_permission_classes` gating auth alias read routing.
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: Shared `reject_async_in_sync_context` helper enforcing synchronous execution contracts.
- [`django_strawberry_framework/exceptions.py`][exceptions]: `ConfigurationError`, `SyncMisuseError`, and safe formatting helper `_safe_arg_repr`.
- [`tests/mutations/test_permissions.py`][test-mutations-permissions]: Unit and schema integration tests for `DjangoModelPermission`, operation mapping, anonymous denial, existence leak protection, async hook rejection, and hostile `__repr__` handling.
- [`tests/mutations/test_write_transaction.py`][test-mutations-write-transaction]: Transaction and auth-alias isolation tests during write authorization.
- [`tests/forms/test_sets.py`][test-forms-sets] & [`tests/forms/test_resolvers.py`][test-forms-resolvers]: Form mutation permission tests pinning `DenyAll` defaults and `AllowAny` opt-ins.
- [`tests/auth/test_mutations.py`][test-auth-mutations]: Auth mutation tests verifying permission overrides and AllowAny defaults.
- [`examples/fakeshop/test_query/test_products_api.py`][test-products-api]: End-to-end GraphQL API tests verifying live permission enforcement.

## Verification

Static analysis and inventory (`docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/permissions.py --review docs/dry/dry-file-mutations__permissions.md --include-constants`):
- Parsed 1 target file, 213 lines, 8 target definitions:
  - 2 module constants ([`_OPERATION_PERMISSION_ACTION`][mutations-permissions], [`_PERMISSION_ASYNC_RECOURSE`][mutations-permissions]);
  - 2 module functions ([`_require_sync_bool_auth_result`][mutations-permissions], [`run_permission_classes`][mutations-permissions]);
  - 2 classes ([`DjangoModelPermission`][mutations-permissions], [`DenyAll`][mutations-permissions]);
  - 2 class methods ([`DjangoModelPermission.has_permission`][mutations-permissions], [`DenyAll.has_permission`][mutations-permissions]).
- Verified reverse references across `django_strawberry_framework/__init__.py`, `django_strawberry_framework/mutations/__init__.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/auth/mutations.py`, and test suites.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   The framework supports four distinct mutation write flavors:
   - **Model mutations ([`mutations/sets.py`][mutations-sets]):** Model-backed writes (`DjangoMutation`) default `Meta.permission_classes` to `[DjangoModelPermission]`.
   - **ModelForm mutations ([`forms/sets.py`][forms-sets]):** Subclasses [`DjangoMutation`][mutations-sets], resolves its model from `form_class._meta.model`, and inherits `[DjangoModelPermission]` unchanged.
   - **Serializer mutations ([`rest_framework/sets.py`][rest-framework-sets]):** Subclasses [`DjangoMutation`][mutations-sets], resolves its model from `serializer_class.Meta.model`, and inherits `[DjangoModelPermission]` unchanged.
   - **Model-less plain form mutations ([`forms/sets.py`][forms-sets]):** `DjangoFormMutation` has no model and cannot query model permissions; it installs [`DenyAll`][mutations-permissions] as its default (`unset_default=(DenyAll,)`), denying unconfigured plain writes by default while supporting `Meta.permission_classes = []` for public access.
   - **Single-Sited Class Execution:** Despite `DjangoFormMutation` not subclassing `DjangoMutation`, both classes execute their permission classes through the exact same helper [`run_permission_classes`][mutations-permissions], preventing authorization logic divergence across flavor hierarchies.
   - **Unified Request Extraction Across Read and Write:** Read-side permission gates ([`FilterSet`][filters-sets], [`OrderSet`][orders-sets]) and write-side mutations share the exact same [`request_from_info`][utils-permissions] extractor with duck-typed Channels ASGI adapter support ([`ChannelsRequestAdapter`][utils-permissions]).
   - **Consistent Async Misuse Guarding:** Read-side field gates ([`utils/permissions.py::invoke_permission_method`][utils-permissions]) and write-side authorization seams ([`_require_sync_bool_auth_result`][mutations-permissions]) both route through [`reject_async_in_sync_context`][utils-querysets] to reject coroutines with typed `SyncMisuseError` exceptions.

2. **Sync and async twins:**
   Zero duplicate permission class hierarchies.
   - Mutation write authorization executes synchronously within both sync and async execution pipelines (`DjangoMutation.resolve_sync` and `DjangoMutation.resolve_async` both invoke synchronous authorization before database operations).
   - Because write authorization is strictly synchronous, `async def has_permission`, `async def check_permission`, or awaitable `user.has_perm` returns an un-awaited coroutine object. Under Python truthiness rules, `bool(coroutine)` evaluates to `True`, which would silently allow unauthorized requests (an authorization bypass).
   - [`_require_sync_bool_auth_result`][mutations-permissions] intercepts coroutines via [`reject_async_in_sync_context`][utils-querysets], safely closes them, and raises `SyncMisuseError` with [`_PERMISSION_ASYNC_RECOURSE`][mutations-permissions]. Non-bool returns raise `ConfigurationError`.
   - No parallel async permission classes (`AsyncDjangoModelPermission`, `AsyncDenyAll`) exist or are needed.

3. **Derived rather than repeated knowledge:**
   All authorization metadata is derived dynamically from model and mutation declarations:
   - Django permission codenames are constructed dynamically as `f"{model._meta.app_label}.{action}_{model._meta.model_name}"` using model metadata and [`_OPERATION_PERMISSION_ACTION`][mutations-permissions].
   - Target models are resolved dynamically via `mutation._resolve_model(mutation.Meta)`, allowing model mutations, form mutations, and serializer mutations to share identical model permission checks.
   - The operation action verb (`add`, `change`, `delete`) is derived from `operation` via [`_OPERATION_PERMISSION_ACTION`][mutations-permissions], avoiding scattered mapping dicts.
   - Request user resolution derives directly from `info.context` via [`request_from_info`][utils-permissions].

4. **Inverse and round-trip pairs:**
   - **Deny-by-Default & Allow-All Opt-In Pairing:** Model mutations default to [`DjangoModelPermission`][mutations-permissions] and plain form mutations default to [`DenyAll`][mutations-permissions] (both deny unauthenticated callers by default). The explicit inversion is `Meta.permission_classes = []` (AllowAny posture), which skips permission class iteration and authorizes the request.
   - **Visibility (Read) vs Authorization (Write) Pairing:** [`permissions.py::apply_cascade_permissions`][permissions] enforces read-side visibility scoping ("may this caller *see* this row"), while [`DjangoModelPermission`][mutations-permissions] enforces write authorization ("may this caller *write* it"). On `update` and `delete`, visibility scoping runs first; if the row is invisible to the caller, it fails with a not-found `FieldError` on `id` before any permission check runs, ensuring no existence leaks.
   - **Authorization Check & Resolver Error Mapping Pairing:** [`check_permission`][mutations-sets] returns a strict boolean (`True`/`False`), and [`resolvers.py::authorize_or_raise`][mutations-resolvers] maps `False` to a top-level `GraphQLError` (nulling the field payload before validation/write execution).

5. **Contracts restated in another medium:**
   The write authorization contracts are documented and pinned across:
   - Code: [`django_strawberry_framework/mutations/permissions.py`][mutations-permissions], [`django_strawberry_framework/mutations/sets.py`][mutations-sets], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/forms/sets.py`][forms-sets], [`django_strawberry_framework/rest_framework/sets.py`][rest-framework-sets], [`django_strawberry_framework/auth/mutations.py`][auth-mutations], [`django_strawberry_framework/auth/queries.py`][auth-queries], [`django_strawberry_framework/utils/permissions.py`][utils-permissions], [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init];
   - Specifications: [`docs/SPECS/spec-036-mutations-0_0_11.md`][spec-036] (Decisions 8, 10, 15), [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038] (Decision 11), [`docs/SPECS/spec-039-serializer_mutations-0_0_13.md`][spec-039], [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040] (Decision 5), [`docs/SPECS/spec-041-channels_router-0_0_14.md`][spec-041], [`docs/SPECS/spec-046-transport_security-0_0_14.md`][spec-046];
   - Test suites: [`tests/mutations/test_permissions.py`][test-mutations-permissions], [`tests/mutations/test_sets.py`][test-mutations-sets], [`tests/mutations/test_resolvers.py`][test-mutations-resolvers], [`tests/mutations/test_write_transaction.py`][test-mutations-write-transaction], [`tests/forms/test_sets.py`][test-forms-sets], [`tests/forms/test_resolvers.py`][test-forms-resolvers], [`tests/rest_framework/test_resolvers.py`][test-rest-framework-resolvers], [`tests/auth/test_mutations.py`][test-auth-mutations], [`examples/fakeshop/test_query/test_products_api.py`][test-products-api];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/COOKBOOK.md`][cookbook], [`docs/TREE.md`][tree], [`TODAY.md`][today], [`LIFECYCLE.html`][lifecycle].

### The single-edit-site test

- **Posited change 1 (Adding a new mutation operation kind, e.g. `upsert` or `bulk_create`):** Map a new operation string to its corresponding Django model-permission action verb (e.g. `"upsert": "change"` or `"bulk_create": "add"`).
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/mutations/permissions.py::_OPERATION_PERMISSION_ACTION`][mutations-permissions].
  - *Site count:* 1.
- **Posited change 2 (Hardening / changing auth result validation contract):** Update validation rules or error formatting for permission hook return values across all write-auth seams.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/permissions.py::_require_sync_bool_auth_result`][mutations-permissions].
  - *Site count:* 1.
- **Posited change 3 (Updating async misuse remediation guidance for write-auth):** Modify the explanation and recourse text appended to `SyncMisuseError` when an async hook is provided.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/mutations/permissions.py::_PERMISSION_ASYNC_RECOURSE`][mutations-permissions].
  - *Site count:* 1.
- **Posited change 4 (Modifying permission class execution and short-circuit semantics):** Alter how `Meta.permission_classes` are evaluated (e.g., collecting denial audit reasons) across all mutation flavors.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/mutations/permissions.py::run_permission_classes`][mutations-permissions].
  - *Site count:* 1.

### Rejected candidates

1. **Creating separate permission runners for `DjangoMutation` and `DjangoFormMutation`:**
   - Disproved per [spec-038][spec-038] Decision 11. Although `DjangoFormMutation` does not subclass `DjangoMutation`, both share the identical class-based permission execution semantics. Single-siting [`run_permission_classes`][mutations-permissions] prevents authorization execution drift between model and form mutations.
2. **Creating an explicit `AllowAny` permission class:**
   - Disproved per [spec-036][spec-036] Decision 15 and [spec-040][spec-040] Decision 5. An empty sequence `Meta.permission_classes = []` already serves as the clean, zero-allocation AllowAny opt-in: `run_permission_classes` iterates zero classes and returns `True`, avoiding unnecessary class instantiation and request user inspection.
3. **Re-exporting `DenyAll` from `django_strawberry_framework/__init__.py`:**
   - Disproved per [spec-038][spec-038] Decision 11. `DenyAll` is an internal safe default automatically installed when `Meta.permission_classes` is unset on a model-less plain form. Consumers never need to import or name `DenyAll` directly.
4. **Coercing non-bool permission hook results via `bool(result)`:**
   - Disproved per [spec-046][spec-046] auth hardening. Truthiness coercion is dangerous in Python because coroutine objects (`async def`) and unprintable hostile objects evaluate to `True`. Requiring an explicit `bool` instance prevents silent authorization bypasses.

## Opportunities

None — `django_strawberry_framework/mutations/permissions.py` is fully consolidated, single-sited, and strictly adheres to repository DRY principles. Operation mapping, strict sync-bool validation, permission class execution, model-backed defaults, and model-less deny defaults are factored cleanly at their root owners.

## Judgment

Zero-edit review. `django_strawberry_framework/mutations/permissions.py` contains zero duplicate logic, unowned policy, or cross-flavor drift. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/permissions.py --review docs/dry/dry-file-mutations__permissions.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

I independently verified Worker 1's DRY review for `django_strawberry_framework/mutations/permissions.py`.

### Verification Scope and Connected Behavior

1. **Write Authorization vs. Read-Side Row Visibility Boundary:**
   - Re-traced the strict separation between read-side visibility scoping ([`permissions.py::apply_cascade_permissions`][permissions]) and write-side authorization ([`DjangoModelPermission`][mutations-permissions]).
   - Verified the execution order on mutating operations (`update` and `delete`): object location resolves through visibility-scoped `get_queryset` before authorization evaluation occurs. If an object is hidden from a caller, the resolver emits a not-found `FieldError` on `id` rather than reaching authorization denial, preventing existence probing and information leakage.

2. **Equivalence & Flavor Hierarchy Challenges:**
   - *Challenge 1 (Single-sited class evaluation loop across flavor split):* Investigated the split between `DjangoMutation` (model mutations, `DjangoModelFormMutation`, `SerializerMutation`) and `DjangoFormMutation` (plain form mutations without a model). Re-verified that despite `DjangoFormMutation` having an independent metaclass and inheritance tree, both write bases route their default `check_permission` directly through [`run_permission_classes`][mutations-permissions]. Iteration order, short-circuit denial, hook argument passing `(info, mutation_cls, operation, data, instance)`, and async-rejection validation are 100% unified.
   - *Challenge 2 (Deny-by-default vs. AllowAny opt-in symmetry):* Re-verified `DenyAll` and `DjangoModelPermission` safe-by-default postures. Unauthenticated callers hold no permissions and fail `user.has_perm`, denying model writes. Model-less plain forms default to `[DenyAll]`, denying unconfigured plain writes. Public opt-in is cleanly achieved via `Meta.permission_classes = []` (AllowAny inversion), which runs zero classes and immediately allows writes without extra classes or user lookups.
   - *Challenge 3 (Shared request extraction):* Confirmed `DjangoModelPermission.has_permission` invokes [`request_from_info(info, family_label="DjangoMutation")`][utils-permissions], maintaining a single request and ASGI adapter resolution seam across both read and write subsystems.

3. **Auth Result Validation Hardening (`_require_sync_bool_auth_result`):**
   - Verified that all three write authorization seams—[`run_permission_classes`][mutations-permissions] (iterating `Meta.permission_classes`), [`DjangoModelPermission.has_permission`][mutations-permissions] (evaluating `user.has_perm(codename)`), and [`resolvers.py::authorize_or_raise`][mutations-resolvers] (evaluating `check_permission`)—enforce strict sync boolean return types through [`_require_sync_bool_auth_result`][mutations-permissions].
   - Coroutines (`async def` methods or awaitables) are intercepted via [`reject_async_in_sync_context`][utils-querysets], closed, and raised as typed `SyncMisuseError` exceptions with [`_PERMISSION_ASYNC_RECOURSE`][mutations-permissions] guidance. Non-boolean returns raise `ConfigurationError` with safe representation formatting (`_safe_arg_repr`), preventing silent authorization bypasses via truthiness coercion.

4. **Mandatory 5-Axis Matrix Discharge:**
   - Axis 1 (Cross-flavor policy mirroring): Verified uniform execution via `run_permission_classes`, model-backed defaults (`DjangoModelPermission`), and model-less defaults (`DenyAll`).
   - Axis 2 (Sync and async twins): Mutation write authorization is strictly synchronous in both sync and async resolver pipelines; coroutines are explicitly rejected rather than coerced. No duplicate async permission classes exist.
   - Axis 3 (Derived rather than repeated knowledge): Dynamic permission codename assembly via `_OPERATION_PERMISSION_ACTION` and model metadata, dynamic model resolution via `mutation._resolve_model`, and dynamic request user extraction via `request_from_info`.
   - Axis 4 (Inverse and round-trip pairs): Deny-by-default paired with `[]` AllowAny opt-in; read visibility scoping paired with write authorization checking; boolean check paired with top-level `GraphQLError` raise.
   - Axis 5 (Contracts restated in another medium): Cross-referenced across specifications ([spec-036][spec-036], [spec-038][spec-038], [spec-039][spec-039], [spec-040][spec-040], [spec-041][spec-041], [spec-046][spec-046]), test suites, and documentation.

5. **Single-Edit-Site Counts:**
   - Confirmed all 4 posited changes require exactly 1 edit site at canonical root owners.

6. **Tool & Suite Verification:**
   - Verified full target definitions coverage with `export_dry_review.py check` (8 definitions covered, 0 missing topics).
   - Executed `tests/mutations/test_permissions.py` (20 passed), `tests/mutations/` (325 passed), and connected suites in `tests/forms/`, `tests/rest_framework/`, and `tests/auth/` (801 passed).

Review verified with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[lifecycle]: ../../LIFECYCLE.html
[today]: ../../TODAY.md

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutations-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md
[spec-041]: ../SPECS/spec-041-channels_router-0_0_14.md
[spec-046]: ../SPECS/spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-queries]: ../../django_strawberry_framework/auth/queries.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[permissions]: ../../django_strawberry_framework/permissions.py
[rest-framework-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->
[test-auth-mutations]: ../../tests/auth/test_mutations.py
[test-forms-resolvers]: ../../tests/forms/test_resolvers.py
[test-forms-sets]: ../../tests/forms/test_sets.py
[test-mutations-permissions]: ../../tests/mutations/test_permissions.py
[test-mutations-resolvers]: ../../tests/mutations/test_resolvers.py
[test-mutations-sets]: ../../tests/mutations/test_sets.py
[test-mutations-write-transaction]: ../../tests/mutations/test_write_transaction.py
[test-rest-framework-resolvers]: ../../tests/rest_framework/test_resolvers.py

<!-- examples/ -->
[test-products-api]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
