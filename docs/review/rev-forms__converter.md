# Review: `django_strawberry_framework/forms/converter.py`

Status: verified

## Understanding

`django_strawberry_framework/forms/converter.py` is the form-field-to-Strawberry conversion
and reverse-map kind resolution engine for model-less `forms.Form` fields and extra
`ModelForm` fields (spec-038 Decision 7).

### Key Responsibilities and Architecture:

1. **Model-Less Conversion Engine (`convert_form_field`)**:
   - Implements `forms.Field` dispatch for fields lacking a Django model column (e.g. captcha,
     confirmation fields, non-model inputs).
   - Backed by `convert_with_mro` from `utils/converters.py`, preserving strict MRO traversal
     order, exact-type checks, and fail-loud fallthrough.
   - Distinct from read-side model converters in `types/converters.py`: model-backed `ModelForm`
     fields resolve scalar/enum/relation GraphQL types via `model_column_input_annotation` in
     `forms/inputs.py`, while `converter.py` handles model-less scalar annotations and write
     kinds (`RELATION_SINGLE`, `RELATION_MULTI`, `FILE`, `SCALAR`).

2. **Single-Sited Requiredness Authority (`form_field_required`)**:
   - Single authority for form field input requiredness across both column-backed and
     column-less paths.
   - For standard `forms.Field` instances, delegates to `field.required`.
   - For `NullBooleanField`, forces requiredness to `False` by default (since
     `forms.NullBooleanField` has a no-op `validate`), while correctly preserving
     `field.required` when:
     - The field is a custom subclass overriding validation; or
     - The field is backed by a non-nullable model column (`column.null == False`).

3. **Dispatch Order and Fail-Loud Registry**:
   - `isinstance_prechecks`:
     1. `forms.ModelMultipleChoiceField` -> `RELATION_MULTI`
     2. `forms.ModelChoiceField` -> `RELATION_SINGLE`
     3. `forms.FileField` / `forms.ImageField` -> `FILE`
     4. `forms.MultipleChoiceField` / `forms.TypedMultipleChoiceField` -> `SCALAR` (`list[str]`)
     5. `forms.Field` (exact type only via `_bare_form_field`) -> `SCALAR` (`str`)
   - `_SCALAR_FORM_FIELDS` MRO walk:
     - `CharField`, `EmailField`, `SlugField`, `URLField`, `RegexField`,
       `GenericIPAddressField` -> `str`
     - `ChoiceField`, `TypedChoiceField`, `FilePathField` -> `str`
     - `IntegerField` -> `int`
     - `FloatField` -> `float`
     - `DecimalField` -> `decimal.Decimal`
     - `BooleanField` -> `bool`
     - `NullBooleanField` -> `bool | None` (or `bool` if validating subclass)
     - `UUIDField` -> `uuid.UUID`
     - `JSONField` -> `strawberry.scalars.JSON`
     - `DateTimeField` -> `datetime.datetime`
     - `DateField` -> `datetime.date`
     - `TimeField` -> `datetime.time`
   - Fallthrough (`_unsupported_form_field`):
     - Unsupported form field types (e.g. `DurationField`, `MultiValueField`,
       `SplitDateTimeField`, `ComboField`, or custom unregistered subclasses) raise
       `ConfigurationError`.
     - Diagnostic formatting is safeguarded with `_safe_type_name` and `_safe_arg_repr` against
       hostile `__repr__` / `__name__` / metaclass traps.

4. **Value Objects and Re-exports**:
   - `FormFieldConversion`: Value object subclassing `FieldConversionBase` with `__slots__ = ()`
     carrying `(annotation, kind, required)`.
   - Re-exports `FILE`, `RELATION_MULTI`, `RELATION_SINGLE`, and `SCALAR` from
     `utils/inputs.py` for direct consumption by form resolvers, input builders, and tests.

## Verification

1. **Caller and Dependency Audit**:
   - Audited imports and usage across `django_strawberry_framework/forms/inputs.py`,
     `django_strawberry_framework/forms/resolvers.py`,
     `django_strawberry_framework/utils/converters.py`, and
     `django_strawberry_framework/utils/inputs.py`.
   - Confirmed architectural symmetry with DRF serializer converter
     (`rest_framework/serializer_converter.py`).

2. **Existing Test Suite Audit**:
   - Audited all existing tests in `tests/forms/test_converter.py` and
     `tests/forms/test_inputs.py`.
   - Confirmed full test coverage of scalar types, relation kinds, `NullBooleanField`
     nuances, exact `Field` handling, and hostile `__repr__` safety.

3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/forms_converter/inspect_form_fields.py`: inspected all 30
     concrete `forms.Field` classes in Django and their MRO hierarchies.
   - Created `docs/review/temp-tests/forms_converter/test_all_form_fields.py`: verified all 30
     Django form field classes (26 supported mapping correctly, 4 unsupported raising
     `ConfigurationError`).
   - Created `docs/review/temp-tests/forms_converter/test_edge_cases.py`: verified custom field
     subclasses across scalar and precheck kinds, column nullability variations on
     `form_field_required`, non-field input rejections, and `FormFieldConversion` slots.
   - All scratch tests passed (100%).

4. **Focused Test Execution**:
   - `uv run pytest tests/forms/test_converter.py --no-cov`: 36 passed (29 baseline + 7 added
     parameterizations/test functions).
   - `uv run pytest tests/forms/ --no-cov`: 228 passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/forms/converter.py` is compact, robust, well-specified, and
strictly follows spec-038 Decision 7. Its MRO dispatch and precheck ordering correctly handle
all Django form field types, enforce single-sited requiredness via `form_field_required`, and
fail loud with diagnostic safety when encountering unsupported field types.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/forms/test_converter.py`:
    - Added `TypedChoiceField`, `TypedMultipleChoiceField`, `GenericIPAddressField`, and
      `FilePathField` to `test_scalar_field_annotations`.
    - Added `test_form_field_required_column_backed_variations` testing column nullability
      variations (`column=None`, `column.null=True`, `column.null=False`) for `NullBooleanField`
      and standard fields.
    - Added `test_custom_subclasses_of_precheck_kinds` testing custom subclasses of
      `ModelChoiceField`, `ModelMultipleChoiceField`, `FileField`, `ImageField`, and
      `MultipleChoiceField`.
    - Added `test_unsupported_django_form_fields_raise` testing fail-loud `ConfigurationError`
      on unsupported Django form fields (`DurationField`, `MultiValueField`,
      `SplitDateTimeField`, `ComboField`).
- **Scoped diff against HEAD (`12779c99`):**
  - `django_strawberry_framework/forms/converter.py`: empty (zero-edit).
- **Permanent tests and pinned behavior:**
  - `tests/forms/test_converter.py` (36 tests total):
    - Pins scalar conversion for all 20 Django scalar form field variants (`CharField`,
      `EmailField`, `SlugField`, `URLField`, `RegexField`, `ChoiceField`, `TypedChoiceField`,
      `FilePathField`, `GenericIPAddressField`, `Field`, `IntegerField`, `FloatField`,
      `DecimalField`, `BooleanField`, `UUIDField`, `DateField`, `DateTimeField`, `TimeField`,
      `MultipleChoiceField`, `TypedMultipleChoiceField`).
    - Pins `NullBooleanField` optionality and validating subclass requiredness.
    - Pins `JSONField` mapping to `strawberry.scalars.JSON`.
    - Pins `ModelChoiceField` -> `RELATION_SINGLE` and `ModelMultipleChoiceField` ->
      `RELATION_MULTI`.
    - Pins `FileField` and `ImageField` -> `FILE`.
    - Pins exact `forms.Field` -> `SCALAR` `str` special-case.
    - Pins fail-loud `ConfigurationError` on unknown custom subclasses and hostile `__repr__`
      fields.
    - Pins `form_field_required` column nullability logic for `NullBooleanField` and standard
      form fields.
    - Pins custom subclasses of relation, file, and multi-choice precheck kinds.
    - Pins typed `ConfigurationError` on unsupported Django form fields (`DurationField`,
      `MultiValueField`, `SplitDateTimeField`, `ComboField`).
- **Scratch verification:**
  - `docs/review/temp-tests/forms_converter/inspect_form_fields.py`: passed.
  - `docs/review/temp-tests/forms_converter/test_all_form_fields.py`: passed.
  - `docs/review/temp-tests/forms_converter/test_edge_cases.py`: passed.
- **Formatter and linter results:**
  - `uv run ruff format .` passed.
  - `uv run ruff check --fix .` passed.
  - `uv run python scripts/check_trailing_commas.py --check tests/forms/test_converter.py` passed.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No (zero-edit target file, existing behavior unchanged).

## Independent verification (Worker 2)

- **System behavior re-traced:**
  - `django_strawberry_framework/forms/converter.py` operates as the single conversion and
    reverse-map kind authority for model-less `forms.Form` fields and extra fields on `ModelForm`.
  - Audited full flow through input class construction in `forms/inputs.py` (`build_form_input_class`,
    `_input_field_for_form_field`, `_guard_dropped_required_fields`), mutation decoding and relation
    resolution in `forms/resolvers.py` (`_decode_form_input_value`, `decode_visible_relation_ids`),
    and shared converter mechanics in `utils/converters.py` (`convert_with_mro`, `finish_field_conversion`).
  - Confirmed `form_field_required` correctly establishes a single source of truth for requiredness
    across both column-backed and column-less fields, accounting for `NullBooleanField` validation
    nuances and non-nullable model column overrides.
  - Confirmed fail-loud dispatch properly catches unregistered `forms.Field` subclasses and unsupported
    built-in Django form fields with `ConfigurationError`, preventing silent fallback to `str` / `String`.

- **Zero-edit confirmation:**
  - Scoped diff against baseline `HEAD` (`12779c99`):
    `git diff 12779c99 -- django_strawberry_framework/forms/converter.py` is empty (zero-edit confirmed).

- **Independent scratch experiments:**
  - Created `docs/review/temp-tests/forms_converter/test_independent_scratch_forms_converter.py`
    to challenge boundaries and edge cases:
    1. Precheck precedence: `ModelMultipleChoiceField` (`RELATION_MULTI`) over `ModelChoiceField`
       (`RELATION_SINGLE`) over `ChoiceField` (`SCALAR` / `str`); `MultipleChoiceField` and
       `TypedMultipleChoiceField` (`list[str]`) over `ChoiceField` (`str`); `FileField` and `ImageField`
       (`FILE`).
    2. Inheritance and MRO resolution: custom mixins with supported fields, MRO walks for `FloatField`,
       `DecimalField`, `UUIDField`, `JSONField`.
    3. Exact `forms.Field` (`str`) vs custom subclasses raising `ConfigurationError` (confirming no
       silent catch-all).
    4. Metaclass safety: classes with broken `__repr__`, unhashable metaclasses, blocked `__mro__`
       access via `__getattribute__` safely raise `ConfigurationError` without unhandled exceptions.
    5. `NullBooleanField` variations: built-in field default optionality (`bool | None`, `required=False`),
       backing column `null=False` override (`bool`, `required=True`), validating custom subclasses
       (`bool`, `required=True`).
    6. Unsupported built-ins: fail-loud `ConfigurationError` for `DurationField`, `MultiValueField`,
       `SplitDateTimeField`, `ComboField`.
    7. Full end-to-end input generation with `build_form_input_class` across 14 diverse form field types.
  - Result: all 8 independent scratch tests passed (`uv run pytest docs/review/temp-tests/forms_converter/test_independent_scratch_forms_converter.py --no-cov`).

- **Permanent test suite execution:**
  - `uv run pytest tests/forms/test_converter.py --no-cov`: 36 passed.
  - `uv run pytest tests/forms/ --no-cov`: 228 passed.

- **Findings disposition:**
  - No findings raised by Worker 1; all behaviors independently verified to be correct, robust, and
    complete.

