# Review: `django_strawberry_framework/utils/converters.py`

Status: verified

## Understanding

`django_strawberry_framework/utils/converters.py` is the single owner of the fail-loud converter dispatch skeleton shared across write-field converters (`forms/converter.py`, `rest_framework/serializer_converter.py`) and filter-input converters (`filters/inputs.py`). It enforces the GOAL-mandated contract that unmapped fields raise a typed `ConfigurationError` rather than silently defaulting to a fallback scalar (spec-039 Decision 4, spec-051 C3).

It owns:
1. **Sentinel Dispatch Control**:
   - `_MroContinue` / `MRO_CONTINUE`: lightweight sentinel with `__slots__ = ()` allowing an `isinstance` precheck handler to signal that dispatch should proceed along the MRO walk rather than terminating early (e.g., bare `forms.Field` exact-type check allowing subclasses to pass through to the scalar registry, or `TypedFilter` normalize skipping convert-only kinds). `None` is explicitly treated as a valid return value (e.g., filter `normalize_input_value` unwrapping an enum member whose `.value` is `None`).
2. **Fail-Loud MRO Dispatch Skeleton**:
   - `convert_with_mro(field, *, isinstance_prechecks, scalar_registry, fallthrough_error_factory)`:
     - **Step 1: Ordered `isinstance` prechecks**: checks each `(types, handler)` in order, returning `handler(field)` unless it returns `MRO_CONTINUE`. Ensures relation, file, and collection kinds take precedence over base scalar mappings (e.g., `ModelChoiceField` before `ChoiceField`).
     - **Step 2: Scalar registry MRO walk**: walks `type.__getattribute__(type(field), "__mro__")` against `scalar_registry` using class identity (`registered is klass`), resolving the most-specific registered class regardless of insertion order while remaining immune to hostile metaclass `__getattribute__` or `__hash__` overrides.
     - **Step 3: Raising fallthrough**: raises `fallthrough_error_factory(field)` when no precheck or scalar registry class matches, ensuring unknown field types fail loudly.
3. **Conversion Value Helpers**:
   - `make_kind_converter(conversion_cls, kind, *, annotation=None, required_of=None)`: builds a closure emitting a `conversion_cls` instance for a fixed decode kind, dynamically evaluating field requiredness (supporting custom predicates such as `form_field_required`).
   - `make_scalar_converter(conversion_cls, annotation, *, required_of=None)`: convenience wrapper over `make_kind_converter` configuring `SCALAR` kind for Python / Strawberry type annotations.
   - `finish_field_conversion(result, field)`: post-walk invocation helper returning precheck-instantiated `FieldConversionBase` instances directly or invoking registry-returned converter callables with `field`.

## Verification

1. **Traced callers and dependencies across the codebase**:
   - `forms/converter.py`: `convert_form_field` uses `convert_with_mro` with prechecks for `ModelMultipleChoiceField`, `ModelChoiceField`, `FileField`, `MultipleChoiceField`, and exact `forms.Field`, backed by `_SCALAR_FORM_FIELDS` and `_unsupported_form_field`.
   - `rest_framework/serializer_converter.py`: `convert_serializer_field` uses `convert_with_mro` with prechecks for `BaseSerializer`/`ListSerializer` (nested rejection), `ManyRelatedField`, `RelatedField`, `FileField`, `ListField`, and `MultipleChoiceField`, backed by `_SERIALIZER_FIELD_CONVERTERS` and `_unsupported_serializer_field`.
   - `filters/inputs.py`: `convert_filter_to_input_annotation` and `normalize_input_value` ride `convert_with_mro` using shared `_filter_input_prechecks` to ensure symmetric conversion and normalization ladders across GlobalID, CSV, Range, List, Typed, and Choice filters.
2. **Examined existing test suite**:
   - `tests/utils/test_converters.py` (15 tests): verifies precheck match precedence over registry, precheck execution order, `MRO_CONTINUE` traversal, `None` value preservation, MRO most-specific class resolution over parent classes, unregistered subclass resolution, unhandled field exception raising, hostile metaclass attribute access and hash resistance, `make_scalar_converter` / `make_kind_converter` construction, `finish_field_conversion` dispatch, and code object sharing with form and serializer converter registries.
   - Executed: `uv run pytest tests/utils/test_converters.py --no-cov` (15 passed).
   - Executed: `uv run pytest tests/forms/test_converter.py tests/rest_framework/test_converter.py tests/filters/test_inputs.py --no-cov` (211 passed).
3. **Scratch verification**:
   - Created `docs/review/temp-tests/utils_converters/test_converters_scratch.py` (7 tests) verifying `MRO_CONTINUE` sentinel properties, diamond inheritance MRO linearization against out-of-order registries, tuple precheck type matching, multiple precheck chaining with `MRO_CONTINUE`, empty registry fallthrough raising, kind/scalar converter factories, and `finish_field_conversion` instance/callable polymorphism.
   - Executed: `uv run pytest docs/review/temp-tests/utils_converters/test_converters_scratch.py --no-cov` (7 passed).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/utils/converters.py` provides a robust, fail-loud dispatch skeleton and value factory for field conversions across forms, serializers, and filter inputs. Its design guarantees that unmapped types fail loudly with actionable `ConfigurationError`s, protects against hostile metaclasses, and keeps scalar and kind conversion value construction single-sited without coupling key spaces. No defects or design improvements were identified.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/utils/converters.py` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/utils/test_converters.py` (15 tests) comprehensively pins `convert_with_mro` precheck and MRO dispatch mechanics, sentinel handling, hostile metaclass resilience, and `make_scalar_converter` / `make_kind_converter` / `finish_field_conversion` value factories.
- **Scratch verification:**
  - `docs/review/temp-tests/utils_converters/test_converters_scratch.py` passed (7/7 tests), verifying sentinel invariants, diamond inheritance MRO resolution, multi-precheck continue flow, empty registry fallthrough, and conversion finishing.
- **Formatter and linter results:**
  - Zero-edit cycle; existing target code is clean and properly formatted.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- **Zero-edit check:** Verified with `git diff 12779c99 -- django_strawberry_framework/utils/converters.py` (clean, 0 changes against cycle baseline).
- **Control flow & contract verification:**
  - Traced `convert_with_mro` ordered `isinstance` prechecks, `MRO_CONTINUE` sentinel flow, and `type.__getattribute__(type(field), "__mro__")` linear walk using identity lookup against `scalar_registry`.
  - Confirmed fail-loud raising via `fallthrough_error_factory` on unmapped field instances, fulfilling spec-039 Decision 4 and spec-051 C3.
  - Verified `make_kind_converter`, `make_scalar_converter`, and `finish_field_conversion` closures and polymorphism across `forms/converter.py`, `rest_framework/serializer_converter.py`, and `filters/inputs.py`.
- **Test execution:**
  - Executed unit and scratch tests: `uv run pytest tests/utils/test_converters.py docs/review/temp-tests/utils_converters/test_converters_scratch.py --no-cov` (22 passed in 1.68s).
  - Executed consumer test suites: `uv run pytest tests/forms/test_converter.py tests/rest_framework/test_converter.py tests/filters/test_inputs.py --no-cov` (211 passed in 3.45s).
- **Verification verdict:** Complete and verified. Status marked `verified`.
