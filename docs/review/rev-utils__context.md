# Review: `django_strawberry_framework/utils/context.py`

Status: verified

## Understanding

`django_strawberry_framework/utils/context.py` defines shape-agnostic read, write, and clear helpers (`get_context_value`, `stash_on_context`, `clear_context_key`) for Strawberry's `info.context`. It provides a centralized dispatch boundary across divergent context shapes (`None`, standard objects, plain `dict`s, `dict` subclasses with attribute access or locked state like `QueryDict`, `__slots__` mapping adapters like `StrawberryDjangoContext`, and frozen containers like `MappingProxyType` or frozen dataclasses).

It is consumed symmetrically across the package:
1. **Optimizer context stash & lifecycle** (`optimizer/_context.py`, `optimizer/extension.py`):
   - Re-exports `get_context_value` and `stash_on_context` for internal optimizer state management.
   - Clears execution-scoped stashes (`DST_OPTIMIZER_PLAN`, `DST_OPTIMIZER_PLANNED`, `DST_OPTIMIZER_FK_ID_ELISIONS`, `DST_OPTIMIZER_LOOKUP_PATHS`, `DST_OPTIMIZER_STRICTNESS`) across reused contexts via `clear_context_key`.
   - `types/resolvers.py` reads strictness, planned keys, and FK elisions via `get_context_value`.
2. **Resource policy enforcement** (`resource_policy.py`, `extensions/resource_policy.py`):
   - Reads request-level limits and execution deadlines (`DST_RESOURCE_POLICY`, `DST_RESOURCE_DEADLINE`) from `info.context` fail-closed via `get_context_value`.
   - Manages policy stashing and start-of-execution clearing via `stash_on_context` and `clear_context_key`.

Core behavioral contracts owned by the target:
- **`get_context_value(context, key, default=None)`**:
  - Short-circuits `context is None` to `default`.
  - For `dict` instances (and subclasses), uses mapping lookup via `context.get(key, default)` first, ensuring `dict` subclasses with attribute storage round-trip through their item mapping.
  - For non-`dict` objects, attempts attribute access first (`getattr(context, key, _MISSING)`), distinguishing an explicitly stashed `None` from an absent attribute.
  - Falls through to `context[key]` for non-dict mapping objects (`__slots__` classes or bridged contexts).
  - Swallows all standard access exceptions (`KeyError`, `TypeError`, `AttributeError`, hostile descriptor errors) fail-closed, returning `default`.
- **`stash_on_context(context, key, value)`**:
  - Silently skips when `context is None`.
  - For non-`dict` objects, attempts `setattr(context, key, value)` first, falling back to `context[key] = value` on `(AttributeError, TypeError)` (e.g. `__slots__` mappings).
  - For `dict` instances, writes via `context[key] = value` directly.
  - Absorbs read-only mapping exceptions (`TypeError` on `MappingProxyType`, `AttributeError` on locked `QueryDict`) without crashing the resolver chain.
- **`clear_context_key(context, key)`**:
  - Silently skips when `context is None`.
  - For non-`dict` objects, attempts `delattr(context, key)`, catching `(AttributeError, TypeError)` to fall through to `del context[key]`.
  - For mappings, deletes via `del context[key]`, silently swallowing `KeyError`, `TypeError`, and `AttributeError` (locked `QueryDict`).

## Verification

1. **Traced all consumers**:
   - `django_strawberry_framework/optimizer/_context.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/resource_policy.py`, and `django_strawberry_framework/extensions/resource_policy.py`.
2. **Examined existing test coverage**:
   - `tests/optimizer/test_extension.py` (31 context & stash tests): verifies plan stashes on plain dicts, dict subclasses, slotted non-dict mappings, `None` context, read-only `MappingProxyType`, locked `QueryDict`, and `clear_optimizer_context` lifecycle.
   - `tests/utils/test_context.py` (7 tests): verifies round-tripping across objects, dicts, slotted mappings, hostile attributes/descriptors, bridged `__getitem__`, `MappingProxyType`, `None` context, explicit `None` stashed values, and locked `dict` subclasses.
3. **Scratch verification**:
   - Created `docs/review/temp-tests/utils_context/test_context_scratch.py` (7 tests) probing `None` context, plain dict, plain object, frozen dataclass (`FrozenInstanceError`), `MappingProxyType`, `__slots__` mapping with `__delitem__`, and hostile property falling through to mapping.
   - Executed: `uv run pytest docs/review/temp-tests/utils_context/test_context_scratch.py --no-cov` (7 passed).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/utils/context.py` is a concise, robust, and well-designed utility module. It provides full symmetry between attribute-based and mapping-based context interactions, handles all supported and hostile context shapes with fail-closed semantics, and ensures that resource policies and optimizer hints degrade safely without crashing GraphQL requests.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/utils/test_context.py`: Added direct unit tests covering `None` context handling across all three helper functions, explicit `None` stashed value preservation vs `_MISSING` sentinels, and locked `dict` subclasses (e.g. `QueryDict`) for `stash_on_context` and `clear_context_key`.
  - `django_strawberry_framework/utils/context.py`: Unmodified (implementation is complete and correct).
- **Permanent tests and pinned behavior:**
  - `tests/utils/test_context.py::test_context_none_short_circuits_and_skips_writes_and_clears`: pins `None` handling in `get_context_value`, `stash_on_context`, and `clear_context_key`.
  - `tests/utils/test_context.py::test_context_distinguishes_explicit_none_from_missing_sentinel`: pins that stashing `None` returns `None` rather than falling back to `default`.
  - `tests/utils/test_context.py::test_locked_dict_subclass_stash_and_clear_are_noops`: pins that immutable `dict` subclasses swallow `AttributeError` on both `__setitem__` and `__delitem__`.
- **Scratch verification:**
  - `docs/review/temp-tests/utils_context/test_context_scratch.py`: 7 passed (`uv run pytest docs/review/temp-tests/utils_context/test_context_scratch.py --no-cov`).
  - Focused test suite run: `uv run pytest tests/utils/test_context.py --no-cov` (7 passed).
- **Formatter and linter results:**
  - `uv run ruff format .`: formatted 1 file (`tests/utils/test_context.py`), all files clean.
  - `uv run ruff check --fix .`: all checks passed.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — target implementation is unchanged and already satisfied existing contracts.

## Independent verification (Worker 2)

### Verification scope and checks performed
1. **Target zero-edit confirmation**:
   - Confirmed `git diff 12779c99 -- django_strawberry_framework/utils/context.py` is empty (zero production edits relative to cycle baseline HEAD `12779c99`).
2. **Contract and behavioral trace**:
   - Traced `get_context_value`, `stash_on_context`, and `clear_context_key` implementations across all target context shapes:
     - `None` context (short-circuits read to `default`, write/clear are silent no-ops).
     - Standard objects with attributes / descriptors (reads via `getattr(context, key, _MISSING)` before falling through to `__getitem__`, writes via `setattr`, clears via `delattr`).
     - Plain `dict`s and `dict` subclasses (reads via `context.get(key, default)`, writes via `context[key] = value`, clears via `del context[key]`).
     - Slotted non-dict mappings (e.g. `__slots__` classes where `setattr` fails with `AttributeError`/`TypeError`, falling back cleanly to `__setitem__` / `__delitem__` / `__getitem__`).
     - Frozen containers (e.g. `MappingProxyType`, frozen dataclasses raising `FrozenInstanceError`, locked `QueryDict` raising `AttributeError` from `__setitem__`/`__delitem__`), verifying fail-closed error suppression without crashing resolver chains or masking unrelated errors.
   - Verified distinction between an explicitly stashed `None` value and `_MISSING` sentinel.
3. **Focused and scratch test execution**:
   - Ran scratch test suite `docs/review/temp-tests/utils_context/test_context_scratch.py`: 7 passed (`uv run pytest docs/review/temp-tests/utils_context/test_context_scratch.py --no-cov`).
   - Ran permanent unit test suite `tests/utils/test_context.py`: 7 passed (`uv run pytest tests/utils/test_context.py --no-cov`).
   - Ran related consumer test suites `tests/optimizer/test_extension.py` (166 passed) and `tests/test_resource_policy.py` (111 passed).
4. **Findings disposition**:
   - All findings checked against implementation; verified that no open defects exist and permanent test coverage pins the required edge cases.

### Disposition
Status: `verified`.
