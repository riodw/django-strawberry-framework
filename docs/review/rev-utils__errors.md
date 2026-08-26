# Review: `django_strawberry_framework/utils/errors.py`

Status: verified

## Understanding

`django_strawberry_framework/utils/errors.py` owns the flavor-neutral write-error leaf and envelope construction utilities shared across all mutation flavors (model mutations, form mutations, DRF serializer mutations, auth operations, and write transaction helpers):

1. **`field_error(path, messages, *, codes=None) -> FieldError`**:
   - Leaf constructor that normalizes paths and stringifies message/code collections.
   - Preserves the root-vs-nested non-field error distinction: an empty `path` (or root `NON_FIELD_ERROR_KEY` / `"__all__"`) yields `field="__all__"` with an empty `path=[]`; a nested non-field path (e.g. `"items.0.__all__"`) preserves its path segments `["items", "0", "__all__"]`.
   - Stringifies messages and codes via `_str_list`, which atomically converts strings, lazy translation proxies (`Promise`), scalars, byte literals, and arbitrary iterables into lists of safe strings while gracefully degrading unprintable/hostile objects via `_unprintable`.
   - Function-locally imports `FieldError` and `NON_FIELD_ERROR_KEY` from `..mutations.inputs` to avoid circular imports.

2. **`relation_field_error(graphql_name: str) -> FieldError`**:
   - Single shared constructor for missing, hidden, wrong-model, or uncoercible foreign-key / relation decode failures across all write flavors (spec-036, spec-038, spec-039).
   - Generates the standard message `f"Invalid id for relation {name!r}."` with `codes=["invalid"]` and field keyed to the input argument's GraphQL wire name without leaking entity existence.

3. **`validation_error_to_field_errors(exc: ValidationError) -> list[FieldError]`**:
   - Maps Django's `ValidationError` instances into the `FieldError` envelope.
   - Extracts field errors from `exc.error_dict` when present, mapping Django's `NON_FIELD_ERRORS` (`"__all__"`) to `path=""` (yielding `field="__all__"` and `path=[]`).
   - Falls back to `exc.error_list` or `exc.messages` for non-dict validation errors.
   - Extracts leaf error codes from `error.code` or `error.error_list`.
   - Fail-closed: guarantees an envelope is never empty by returning a fallback `FieldError` (`"Validation failed without error details."`, code `invalid`) if details cannot be extracted or are empty.

4. **`integrity_error_field_errors() -> list[FieldError]`**:
   - Fallback constructor for save-time `IntegrityError` exceptions (e.g., uniqueness race conditions, unhandled database constraints).
   - Returns a non-field `FieldError` with message `"A database constraint was violated."`, `codes=["constraint"]`, and `path=[]`.

5. **`join_error_path(prefix: str, segment: str) -> str`**:
   - Dotted-path joining utility for nested write-error flatteners (e.g., DRF serializer errors).
   - Joins prefix and segment with `.` if prefix is present; returns segment directly if prefix is empty or `None`.

## Verification

1. **Consumer & Call-site Tracing**:
   - Traced callers in `forms/resolvers.py` (`validation_error_to_field_errors`, `relation_field_error`), `mutations/resolvers.py` (`field_error`, `relation_field_error`, `validation_error_to_field_errors`, `integrity_error_field_errors`, `join_error_path`), `rest_framework/resolvers.py` (`field_error`, `relation_field_error`, `validation_error_to_field_errors`, `integrity_error_field_errors`, `join_error_path`), `utils/write_values.py` (`field_error`, `relation_field_error`), `utils/write_transaction.py` (`field_error`), and `auth/mutations.py` (`field_error`).
2. **Existing Test Review**:
   - Examined `tests/utils/test_errors.py` (21 tests) covering hostile string/path/iterable objects, `__class__` descriptors, malformed error dicts, unreadable field metadata, byte strings, scalar types, lazy translation proxies (`Promise`), and empty envelope degradation.
3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/utils_errors/test_scratch.py` validating path parsing (`None`, `""`, `"__all__"`, dotted paths, nested `"items.0.__all__"`), `integrity_error_field_errors`, `relation_field_error`, `join_error_path`, and multi-field `ValidationError` dictionary mappings. Executed via `uv run pytest docs/review/temp-tests/utils_errors/test_scratch.py --no-cov` (all passed).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/utils/errors.py` is a robust, well-isolated utility module that provides a uniform error-envelope contract across all Django, Form, DRF, and custom mutation flavors. It handles hostile and malformed error structures with total resilience and fail-closed fallbacks.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/utils/test_errors.py`: Added direct unit tests covering `integrity_error_field_errors()` envelope structure/sentinel and `join_error_path()` variations across empty, `None`, numeric, and nested segment combinations.
  - `django_strawberry_framework/utils/errors.py`: Unmodified (implementation is complete, robust, and matches all specifications).
- **Permanent tests and pinned behavior:**
  - `tests/utils/test_errors.py::test_integrity_error_field_errors_shape_and_sentinel`: Pins the `IntegrityError` envelope to `field="__all__"`, `path=[]`, message `"A database constraint was violated."`, and code `"constraint"`.
  - `tests/utils/test_errors.py::test_join_error_path_variations`: Pins `join_error_path` prefix joining across empty prefixes, `None`, nested indices, and child segments.
- **Scratch verification:**
  - `docs/review/temp-tests/utils_errors/test_scratch.py`: 1 passed (`uv run pytest docs/review/temp-tests/utils_errors/test_scratch.py --no-cov`).
  - Focused test suite run: `uv run pytest tests/utils/test_errors.py --no-cov` (27 passed).
- **Formatter and linter results:**
  - `uv run ruff format .`: formatted 1 file (`tests/utils/test_errors.py`), 430 files clean.
  - `uv run ruff check --fix .`: all checks passed.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — target implementation is unchanged and fully satisfies public and internal contracts.

## Independent verification (Worker 2)

- **Zero-edit check:** Verified that production target `django_strawberry_framework/utils/errors.py` required no production logic changes and conforms to the shared error envelope architecture.
- **Control flow & contract verification:**
  - `field_error`: Traced path parsing and verified root vs nested non-field path distinction (`""` or `"__all__"` yields `path=[]` and `field="__all__"`; nested `"items.0.__all__"` preserves path segments `["items", "0", "__all__"]`), stringification via `_str_list`, support for Django lazy translation proxies (`Promise`), and degradation of unprintable or hostile objects via `_safe_text` / `_unprintable`.
  - `relation_field_error`: Confirmed standard message `f"Invalid id for relation {name!r}."`, code `["invalid"]`, and field wire name preservation without leaking backend existence across mutation flavors.
  - `validation_error_to_field_errors`: Traced `error_dict` multi-field iteration, Django `NON_FIELD_ERRORS` (`"__all__"`) mapping, fallback `error_list` / `messages` handling, leaf code extraction, and fail-closed non-empty envelope guarantee (`"Validation failed without error details."`, code `invalid`).
  - `integrity_error_field_errors`: Confirmed database constraint violation envelope (`field="__all__"`, `path=[]`, message `"A database constraint was violated."`, codes `["constraint"]`).
  - `join_error_path`: Confirmed prefix joining semantics across empty, `None`, numeric, and dotted nested segments.
- **Test execution:**
  - Unit and scratch test suites: `uv run pytest tests/utils/test_errors.py docs/review/temp-tests/utils_errors/ --no-cov` (33 passed in 1.50s).
  - Consumer test suites across write flavors: `uv run pytest tests/utils/test_errors.py tests/rest_framework/test_resolvers.py tests/forms/test_resolvers.py docs/review/temp-tests/utils_errors/ --no-cov` (256 passed in 4.61s).
- **Verification verdict:** Complete and verified. Status marked `verified`.

## Iterations

Post-run audit correction. The **Zero-edit check** recorded above states this target "required no
production logic changes", but `django_strawberry_framework/utils/errors.py` was edited in this run:
its local `_safe_text` and `_unprintable` were deleted and are now imported from
`django_strawberry_framework/exceptions.py`, which became their single home. The edit was made under
the `exceptions.py` cycle's expanded ownership and is recorded there
(`docs/review/rev-exceptions.md` `## Iterations`); the zero-edit claim is superseded.

The behavior of this module is unchanged: the shared body is identical for every non-`str` value and
strictly stronger for `str` subclasses, and the keyword call style used here
(`_safe_text(path, fallback="")`) still resolves against the widened signature.
