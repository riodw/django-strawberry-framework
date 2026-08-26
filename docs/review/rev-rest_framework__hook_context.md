# Review: `django_strawberry_framework/rest_framework/hook_context.py`

Status: verified

## Understanding

`django_strawberry_framework/rest_framework/hook_context.py` defines the frozen context and descriptor data structures for serializer mutation hooks, implementing the write pipeline hardening layer (spec-039).

### Key Responsibilities and Symbols:
1. **`SerializerHookContext`**:
   - Slotted, frozen dataclass (`@dataclass(frozen=True, slots=True)`).
   - Attributes:
     - `operation: str`: The declared mutation operation kind (`"create"` or `"update"`).
     - `write_alias: str`: Pinned database alias for the write pipeline transaction.
     - `instance_pk: Any`: Immutable snapshot of the authorized target's primary key (captured immediately post-locate, or `None` on create).
   - Passed to consumer hooks (`get_serializer_kwargs`, `get_serializer_injected_data`, `get_serializer_save_kwargs`) in place of the live located model instance. This closes the pre-save attack surface where an override could mutate unvalidated fields or repoint `pk` to an unauthorized row before `serializer.save()`.
2. **`UploadMetadata`**:
   - Slotted, frozen dataclass (`@dataclass(frozen=True, slots=True)`).
   - Attributes:
     - `name: str | None`: Upload file name if available.
     - `size: int | None`: Upload file size in bytes if available.
     - `content_type: str | None`: MIME type if available.
   - Stands in for stateful `UploadedFile` objects in hook data views (`_frozen_hook_view`). Prevents hooks from consuming or exhausting the underlying stream before DRF validation runs.

### System Integration:
- **`django_strawberry_framework/__init__.py`**: Re-exported as lazy DRF soft exports (`_DRF_SOFT_EXPORTS`) accessible via module `__getattr__` guarded by `require_drf()`.
- **`django_strawberry_framework/rest_framework/resolvers.py`**:
  - `_upload_metadata(item)`: Builds `UploadMetadata` from incoming upload objects, tolerating missing/broken properties.
  - `resolve_serializer_mutation`: Instantiates `SerializerHookContext` with the pinned write alias and snapshotted `authorized_pk`.
  - `_guarded_serializer_write`: Threads `hook_context` and frozen upload descriptors into consumer hooks.
- **`django_strawberry_framework/rest_framework/sets.py`**: Documents the hook contract on `SerializerMutation`.

## Verification

1. **Dependency and Caller Mapping**:
   - Audited root package exports in `django_strawberry_framework/__init__.py`.
   - Traced all callers in `resolvers.py` and `sets.py`.
2. **Existing Test Suite Audit**:
   - `tests/base/test_init.py`: `test_dynamic_drf_soft_exports_via_getattr` verifies lazy export resolution.
   - `tests/rest_framework/test_resolvers.py`:
     - `test_frozen_hook_view_rejects_cycles_preserves_sharing_and_freezes_uploads` verifies upload conversion to `UploadMetadata`.
     - `test_upload_metadata_tolerates_a_sizeless_file` and `test_upload_metadata_tolerates_raising_name_and_content_type` verify resilient descriptor construction.
3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/rest_framework/test_hook_context_scratch.py` verifying `FrozenInstanceError` on mutation, absence of `__dict__` (slots), value equality, and hashability.
   - Executed: `uv run pytest docs/review/temp-tests/rest_framework/test_hook_context_scratch.py --no-cov` (2 passed).
4. **Focused Test Runs**:
   - `uv run pytest tests/rest_framework/test_resolvers.py tests/base/test_init.py --no-cov` (169 passed).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/rest_framework/hook_context.py` is clean, robust, and correctly implements the immutable hook context and upload descriptor contracts required by the hardened write pipeline. Permanent test coverage was added in `tests/rest_framework/test_resolvers.py` pinning immutability, slotted attributes, and value equality.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/rest_framework/test_resolvers.py`: added `test_hook_context_and_upload_metadata_invariants` pinning `FrozenInstanceError` on attribute assignment, slots verification (no `__dict__`), equality, and hashing for `SerializerHookContext` and `UploadMetadata`.
  - Scoped source diff for `django_strawberry_framework/rest_framework/hook_context.py` against cycle baseline (`12779c99`): 0 diff (zero-edit on production target).
- **Permanent tests and pinned behavior:**
  - `tests/rest_framework/test_resolvers.py::test_hook_context_and_upload_metadata_invariants`:
    - Pins `SerializerHookContext` frozenness, slots, field snapshots, equality, and hashability.
    - Pins `UploadMetadata` frozenness, slots, field values, equality, and hashability.
- **Scratch verification:**
  - `docs/review/temp-tests/rest_framework/test_hook_context_scratch.py` (2 passed).
  - `uv run pytest tests/rest_framework/test_resolvers.py -k test_hook_context_and_upload_metadata_invariants --no-cov` (1 passed).
  - `uv run pytest tests/rest_framework/test_resolvers.py tests/base/test_init.py --no-cov` (170 passed).
- **Formatter and linter results:**
  - `uv run ruff format .` passed (0 errors).
  - `uv run ruff check --fix .` passed (0 errors).
  - `uv run python scripts/check_trailing_commas.py` passed (0 errors).
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

- **Target production file diff:**
  - `git diff 12779c99 -- django_strawberry_framework/rest_framework/hook_context.py` is zero-edit (0 diff against baseline `12779c99`).
- **Independent behavior re-tracing:**
  - **`SerializerHookContext`**:
    - Slotted, frozen dataclass with `operation: str`, `write_alias: str`, and `instance_pk: Any`.
    - Immutability verified: `setattr` raises `FrozenInstanceError`, instances are hashable and slotted (`__dict__` absent).
    - Verified consumer hook boundary in `django_strawberry_framework/rest_framework/resolvers.py`: instantiated in `resolve_serializer_mutation` (`hook_context = SerializerHookContext(operation=operation, write_alias=write_alias, instance_pk=authorized_pk)`) and passed to `get_serializer_kwargs`, `get_serializer_injected_data`, and `get_serializer_save_kwargs` via `_guarded_serializer_write`.
    - Protects the pre-save attack surface by passing an immutable snapshot rather than a live, mutable model instance.
  - **`UploadMetadata`**:
    - Slotted, frozen dataclass with `name: str | None`, `size: int | None`, and `content_type: str | None`.
    - Immutability verified: `setattr` raises `FrozenInstanceError`, instances are hashable and slotted (`__dict__` absent).
    - Verified construction in `_upload_metadata(item)` in `resolvers.py`, with safe attribute access for `name`, `size`, and `content_type`.
    - Verified integration with `_frozen_hook_view` preventing consumer hooks from consuming underlying file streams before DRF validation.
  - **Dynamic Soft Exports**:
    - Verified `SerializerHookContext` and `UploadMetadata` in `django_strawberry_framework/__init__.py::_DRF_SOFT_EXPORTS`, lazily resolved via module `__getattr__` protected by `require_drf()`.
- **Finding disposition and verification tests:**
  - Zero defects identified. All contracts conform to write pipeline hardening specifications.
  - Verified scratch test `docs/review/temp-tests/rest_framework/test_hook_context_scratch.py` (2 passed).
  - Verified permanent test `tests/rest_framework/test_resolvers.py::test_hook_context_and_upload_metadata_invariants` (1 passed).
  - Focused suite `uv run pytest tests/rest_framework/test_resolvers.py tests/base/test_init.py --no-cov` passed (170 passed).
- **Code hygiene & repository invariants:**
  - Target production file has zero diff against baseline.
  - `uv run ruff check .` passed with 0 errors.
  - `uv run ruff format --check .` and `uv run python scripts/check_trailing_commas.py` passed with 0 errors.

