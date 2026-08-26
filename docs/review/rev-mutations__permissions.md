# Review: `django_strawberry_framework/mutations/permissions.py`

Status: verified

## Understanding

`django_strawberry_framework/mutations/permissions.py` implements the write-side authorization primitives and execution engine for mutations across model and form flavors (spec-036 Decision 15, spec-038 Decision 11):

1. **Write-Auth Execution Engine (`run_permission_classes`)**:
   - Iterates through `Meta.permission_classes` on the mutation class.
   - Instantiates each permission class and invokes `has_permission(info, mutation_cls, operation, data, instance)`.
   - Passes each result through `_require_sync_bool_auth_result` to reject truthy coroutines/awaitables (preventing async authorization bypass) and non-boolean returns.
   - Short-circuits on the first `False` return, returning `True` only when all classes allow.
   - Single-sited implementation shared between `DjangoMutation.check_permission` and `DjangoFormMutation.check_permission`.

2. **Sync Boolean Authorization Guard (`_require_sync_bool_auth_result`)**:
   - Enforces the strict synchronous boolean contract across write authorization seams (`has_permission`, `check_permission`, and `user.has_perm`).
   - Delegates awaitable rejection to `reject_async_in_sync_context`, appending `_PERMISSION_ASYNC_RECOURSE` and closing/disposing dangling coroutines before raising `SyncMisuseError`.
   - Requires `isinstance(value, bool)`, raising `ConfigurationError` for non-bool returns (e.g., integers, strings, `None`) to prevent truthiness coercion bypasses.

3. **Default Model Permission Class (`DjangoModelPermission`)**:
   - DRF-inspired write-permission class installed as default on `DjangoMutation` and `DjangoModelFormMutation`.
   - Extracts `request` via `request_from_info(info, family_label="DjangoMutation")`.
   - Extracts `request.user`; returns `False` if `user is None`.
   - Resolves target model via `mutation._resolve_model(mutation.Meta)`.
   - Maps mutation operation to Django permission action verb via `_OPERATION_PERMISSION_ACTION` (`create -> add`, `update -> change`, `delete -> delete`).
   - Evaluates `user.has_perm(f"{app_label}.{action}_{model_name}")` guarded by `_require_sync_bool_auth_result`. Unauthenticated/anonymous callers hold no permissions and are denied by default.

4. **Model-less Deny-by-Default Sentinel (`DenyAll`)**:
   - Fail-closed permission class installed as the default unset `permission_classes` for plain `DjangoFormMutation` (which lacks model metadata).
   - `has_permission` returns `False` unconditionally for every operation without touching model or user attributes.
   - Public plain form access requires explicit opt-in via `permission_classes = []`.

## Verification

1. **Existing Test Suite**:
   - Reviewed `tests/mutations/test_permissions.py` (20 existing tests) verifying:
     - `AnonymousUser` rejection and missing user attribute handling.
     - Permission checking for `create`, `update`, `delete` operations with appropriate Django model permission grants.
     - Top-level `GraphQLError` emission on auth denial (null payload without leaking field validation envelope).
     - Ordering guarantee: row visibility check runs before update authorization to prevent existence leaks.
     - Custom permission class override support (`AllowAll`, custom deny) and explicit empty permission list (`[]`) bypassing auth lookup.
     - Awaitable/coroutine rejection for `has_permission`, `check_permission`, and `user.has_perm` raising `SyncMisuseError`.
     - Hostile `__repr__` resilience on invalid non-bool returns raising `ConfigurationError`.
   - Reviewed `tests/forms/test_sets.py` and `tests/forms/test_resolvers.py` verifying `DenyAll` assignment and deny-by-default execution on plain form mutations.

2. **Scratch Probes (`docs/review/temp-tests/mutations_permissions/test_scratch.py`)**:
   - Probed `_require_sync_bool_auth_result` across valid booleans, truthy/falsy non-booleans (`1`, `0`, `"true"`, `None`, object), and coroutines.
   - Probed `DenyAll.has_permission` across multiple operations (`create`, `form`, etc.).
   - Probed `run_permission_classes` short-circuit behavior ensuring later classes are not evaluated once a denial occurs.

3. **Coverage & Subsystem Runs**:
   - `uv run pytest tests/mutations/test_permissions.py --cov=django_strawberry_framework.mutations.permissions --cov-fail-under=0`: 30 passed, 100% line coverage (34/34 statements).
   - `uv run pytest tests/mutations/ --no-cov`: 346 passed across all mutation subsystem tests.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/mutations/permissions.py` is a robust, fail-closed authorization engine ensuring strict sync boolean returns, preventing async bypass vulnerabilities, and cleanly separating model-backed permission checks from model-less plain form defaults. Permanent tests were added to `tests/mutations/test_permissions.py` to directly pin `DenyAll`, multi-class evaluation short-circuiting, and non-bool reject matrices.

## Implementation (Worker 1)

- **Changed files and necessity:**
  - `tests/mutations/test_permissions.py`: Added direct unit tests for `DenyAll.has_permission`, `run_permission_classes` evaluation short-circuiting, and `_require_sync_bool_auth_result` non-bool parameterization to ensure full test self-containment within `tests/mutations/`.
- **Permanent tests and pinned behavior:**
  - `tests/mutations/test_permissions.py::test_deny_all_always_returns_false`: Pins that `DenyAll.has_permission` returns `False` unconditionally across all mutation operations without reading model/user attributes.
  - `tests/mutations/test_permissions.py::test_run_permission_classes_short_circuits_on_first_denial`: Pins sequential execution and short-circuit evaluation in `run_permission_classes`.
  - `tests/mutations/test_permissions.py::test_require_sync_bool_auth_result_rejects_non_bool_values`: Pins rejection of integers, strings, `None`, empty collections, and arbitrary objects with `ConfigurationError`.
- **Scratch / focused verification:**
  - Ran scratch tests in `docs/review/temp-tests/mutations_permissions/test_scratch.py` (11 passed).
  - Ran `uv run pytest tests/mutations/test_permissions.py --no-cov` (30 passed).
  - Ran `uv run pytest tests/mutations/ --no-cov` (346 passed).
- **Formatter and linter results:**
  - `uv run ruff format .` and `uv run ruff check --fix .` passed cleanly with 0 errors.
  - `python3 scripts/check_trailing_commas.py --check` passed cleanly.
- **Evidence for rejected findings:**
  - None.
- **Changelog:**
  - Does not merit a changelog entry (zero functional changes to production source; test strengthening only).

## Independent verification (Worker 2)

- **Trace paths and behavioral contracts:**
  - Traced `run_permission_classes`: iterates `Meta.permission_classes`, instantiates each class, invokes `has_permission(info, mutation_cls, operation, data, instance)`, validates return via `_require_sync_bool_auth_result`, and short-circuits on first `False`.
  - Traced `_require_sync_bool_auth_result`: rejects awaitables/coroutines via `reject_async_in_sync_context` (closing dangling coroutines and raising `SyncMisuseError` with actionable recourse), enforces strict `isinstance(value, bool)` rejecting any non-bool (integers, strings, `None`, collections, objects) with `ConfigurationError` to prevent truthiness coercion bypasses.
  - Traced `DjangoModelPermission`: safely resolves request and user, returns `False` when `user is None` (anonymous/unauthenticated caller), maps operation verb to Django permission codename (`create -> add`, `update -> change`, `delete -> delete`), and validates `user.has_perm` return through `_require_sync_bool_auth_result`.
  - Traced `DenyAll`: fail-closed sentinel unconditionally returning `False` without accessing any request, model, or user attributes.
- **Diff & Zero-Edit Confirmation:**
  - Confirmed `git diff 12779c99 -- django_strawberry_framework/mutations/permissions.py` is empty (zero production edits).
- **Probing & Test Execution:**
  - Executed focused test suite: `uv run pytest tests/mutations/test_permissions.py --no-cov` (30 passed).
  - Executed independent probe tests in `docs/review/temp-tests/mutations_permissions/test_worker2_verification.py` (7 passed) covering coroutine closure on misuse, truthy/falsy non-boolean rejection, empty permission classes, sequential multi-class evaluation, `DenyAll` argument resilience, and `DjangoModelPermission` handling of async/invalid `has_perm` returns.
  - Line coverage for `django_strawberry_framework/mutations/permissions.py`: 100% (34/34 statements).
- **Outcome:**
  - Verified. All write-authorization semantics, fail-closed guards, and error paths are correct and completely tested.

