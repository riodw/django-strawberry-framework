# Review: `django_strawberry_framework/utils/permissions.py`

Status: verified

## Understanding

`django_strawberry_framework/utils/permissions.py` single-sites the neutral active-input permission mechanics and Django/Channels request-context resolution shared across set families (`FilterSet` and `OrderSet`), mutation hooks (`mutations/resolvers.py`), and transport layers (`consumers.py`, `write_transaction.py`):

1. **Request and Channels Context Decoding (`request_from_info`, `_request_from_context`, `ChannelsRequestAdapter`)**:
   - Resolves the Django request from `info.context` across supported execution contexts: direct `HttpRequest`, `info.context.request` attributes, mapping contexts with `request` key, and Strawberry Channels HTTP/WebSocket consumer contexts.
   - Wraps Channels consumer contexts in `ChannelsRequestAdapter` exposing `.user`, `.session`, and `.scope` while duck-typing all other attributes to the wrapped request/consumer without requiring a mandatory `channels` dependency.
   - Fails closed with typed `ConfigurationError` when context is missing, malformed, or unresolvable, clearly naming the calling `family_label`.

2. **Authorization Aliases Identification (`resolve_auth_aliases`, `auth_aliases_for_permission_classes`)**:
   - Queries Django's database router (`router.db_for_read`) for auth models queried during permission evaluation (`AUTH_USER_MODEL`, `auth.Permission`, `auth.Group`, `contenttypes.ContentType`) to derive read aliases allowed during write transactions.
   - Skips uninstalled models safely via `_safe_get_model` and gates alias resolution on `bool(permission_classes)`.

3. **Active-Input Permission Traversal & Gate Dispatch (`run_active_input_permission_checks`, `active_permission_targets`, `invoke_permission_method`)**:
   - Consolidates leaf and related branch classification into a single traversal via `active_permission_targets` backed by `utils/input_values.py::iter_active_fields`.
   - Fires `check_<field>_permission(request)` methods on bare instances (`object.__new__(cls)`), deduping calls within the request lifecycle via a shared per-class `fired` set.
   - Enforces synchronous gate execution via `reject_async_in_sync_context`, loudly rejecting async gates with `SyncMisuseError` to prevent silent authorization bypasses.
   - Walks flat relation paths via `_fire_flat_relation_path_gates`, matching ORM field names (including composite multi-hop prefixes) against declared related sets (`_related_declarations`) and firing the exact intermediate and terminal gate chain that nested branches fire.
   - Recursively checks child sets while enforcing the traversal budget (`depth + 1 <= _MAX_LOGIC_DEPTH` or `DEFAULT_SET_INPUT_TRAVERSAL_DEPTH`), raising `ConfigurationError` on excessive nesting.

## Verification

1. **Call-site and Contract Tracing**:
   - Traced all callers: `sets_mixins.py` (`ActiveInputPermissionMixin`), `filters/sets.py`, `orders/sets.py`, `mutations/resolvers.py`, `consumers.py`, and `utils/write_transaction.py`.
   - Verified that `ActiveInputPermissionAttrs` parameterization accurately isolates family-specific traits (`unset_sentinel`, `handle_top_level_list`, `logic_keys`, `field_specs`, `related_attr`, `target_attr`) while keeping traversal mechanics unified.
2. **Existing Test Review**:
   - Reviewed `tests/utils/test_permissions.py` (52 existing test cases) covering `request_from_info`, Channels HTTP/WS adapters, hostile property handling, async gate rejection, flat relation path gate cascades, and recursion depth caps.
3. **Focused Verification**:
   - Ran `uv run pytest tests/utils/test_permissions.py tests/test_sets_mixins.py --no-cov` (71 passed in 3.21s).

## Improvements

### High

None.

### Medium

None.

### Low

- **Observation:** `resolve_auth_aliases` was defined as a public top-level utility function but was omitted from module `__all__`.
  - **Evidence:** `utils/permissions.py` defines `resolve_auth_aliases` without a leading underscore; it is tested directly in `tests/utils/test_permissions.py`, and referenced in cross-module docstrings (`consumers.py`, `utils/write_transaction.py`).
  - **Impact:** `from django_strawberry_framework.utils.permissions import *` omitted `resolve_auth_aliases`, leaving `__all__` incomplete relative to the module's public interface.
  - **Recommendation:** Add `"resolve_auth_aliases"` to `__all__` in `django_strawberry_framework/utils/permissions.py`.
  - **Proof:** `test_permissions_all_exports_are_complete` verifies that `resolve_auth_aliases` is in `__all__` and that every exported symbol exists on the module.

## Summary

`django_strawberry_framework/utils/permissions.py` provides a robust, secure, and fail-closed substrate for active-input permission traversal and Channels/Django request resolution. Adding `resolve_auth_aliases` to `__all__` completes the module export contract.

## Implementation (Worker 1)

- **Changed files:**
  - `django_strawberry_framework/utils/permissions.py`: Added `"resolve_auth_aliases"` to `__all__` in alphabetical order.
  - `tests/utils/test_permissions.py`: Added `test_permissions_all_exports_are_complete` asserting all symbols in `__all__` exist and that `resolve_auth_aliases` is present.
- **Permanent tests and pinned behavior:**
  - `tests/utils/test_permissions.py::test_permissions_all_exports_are_complete`: Pins that `resolve_auth_aliases` is exported in `__all__` and every symbol in `__all__` is defined on `django_strawberry_framework.utils.permissions`.
- **Scratch or focused verification:**
  - Focused test suite: `uv run pytest tests/utils/test_permissions.py tests/test_sets_mixins.py --no-cov` (71 passed in 3.21s).
- **Formatter and linter results:**
  - `uv run ruff format .`: formatted 2 files (`django_strawberry_framework/utils/permissions.py`, `tests/utils/test_permissions.py`), 429 files unchanged.
  - `uv run ruff check --fix .`: all checks passed.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — export list completeness update is internal maintenance.

## Independent verification (Worker 2)

- **Paths and behaviors traced:**
  - `request_from_info` and `_request_from_context`: Validated context resolution hierarchy across bare `HttpRequest`, object attributes (`info.context.request`), mapping contexts (`info.context["request"]`), and Strawberry Channels HTTP/WS consumer contexts. Verified that `ChannelsRequestAdapter` duck-types attributes and safely evaluates `.user` and `.session` mapping reads. Confirmed fail-closed `ConfigurationError` behavior on missing or unresolvable context.
  - `resolve_auth_aliases` and `auth_aliases_for_permission_classes`: Re-traced dynamic alias resolution via Django database router (`router.db_for_read`) across core auth models (`AUTH_USER_MODEL`, `auth.Permission`, `auth.Group`, `contenttypes.ContentType`) with safe model discovery. Verified that empty `permission_classes` correctly acts as an authorization opt-out yielding `frozenset()`.
  - Active-input permission traversal (`run_active_input_permission_checks`, `active_permission_targets`, `invoke_permission_method`): Verified single-pass active input partitioning between leaf paths and related branches via `iter_active_fields`. Confirmed synchronous enforcement via `reject_async_in_sync_context` raising `SyncMisuseError` on coroutine return values to prevent authorization bypass. Verified `_fire_flat_relation_path_gates` recursively walking ORM relation hops (including multi-hop and renamed declarations) to fire intermediate branch and terminal target set gates. Confirmed traversal budget enforcement (`next_depth > cap` raising `ConfigurationError`).
- **Diff and findings verification:**
  - Checked `git diff 12779c99 -- django_strawberry_framework/utils/permissions.py` against cycle baseline HEAD (12779c99): Scoped diff contains only adding `"resolve_auth_aliases"` to `__all__`.
  - Checked `git diff 12779c99 -- tests/utils/test_permissions.py`: Verified permanent test `test_permissions_all_exports_are_complete` validates that `resolve_auth_aliases` is in `__all__` and all exported symbols resolve on the module.
- **Focused test execution:**
  - Ran `uv run pytest tests/utils/test_permissions.py tests/test_sets_mixins.py --no-cov` (71 passed in 3.29s).
- **Conclusion:** Verification complete. All active-input permission mechanisms, Channels/Django request resolutions, and export contracts are solid and verified.

