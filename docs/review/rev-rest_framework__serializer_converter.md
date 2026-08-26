# Review: `django_strawberry_framework/rest_framework/serializer_converter.py`

Status: verified

## Understanding

`django_strawberry_framework/rest_framework/serializer_converter.py` is the DRF serializer-field to Strawberry annotation conversion and reverse-map metadata engine (spec-039).

### Key Responsibilities and Architecture:

1. **Serializer Field Dispatch (`convert_serializer_field`)**:
   - Maps DRF `serializers.Field` instances to Strawberry GraphQL annotations and decode kinds (`SCALAR`, `RELATION_SINGLE`, `RELATION_MULTI`, `FILE`).
   - Uses `convert_with_mro` from `utils/converters.py` for dispatch:
     1. Prechecks:
        - `(BaseSerializer, ListSerializer)` -> rejected by `_reject_nested_serializer` (nested writes are opt-in only).
        - `ManyRelatedField` -> kind `RELATION_MULTI` (enforces `PrimaryKeyRelatedField` child).
        - `RelatedField` -> kind `RELATION_SINGLE` (enforces `PrimaryKeyRelatedField`).
        - `FileField` -> kind `FILE`.
        - `ListField` -> `list[<child scalar>]` (scalar child required; relations/nested serializers rejected).
        - `MultipleChoiceField` -> `list[str]` (subclasses `ChoiceField`).
     2. MRO walk over `_SERIALIZER_FIELD_CONVERTERS`:
        - Built-in mappings: `CharField` (`str`), `ChoiceField` (`str`), `IntegerField` (`int`), `FloatField` (`float`), `DecimalField` (`decimal.Decimal`), `BooleanField` (`bool`), `UUIDField` (`uuid.UUID`), `DateTimeField` (`datetime.datetime`), `DateField` (`datetime.date`), `TimeField` (`datetime.time`), `JSONField` (`JSON`), `DictField` (`JSON`, covering `HStoreField`), `IPAddressField` (`str`), `FilePathField` (`str`), `DurationField` (`str`), `ModelField` (via wrapped `model_field`).
     3. Fallthrough (`_unsupported_serializer_field`):
        - Unregistered `serializers.Field` subclass with no supported ancestor raises fail-loud `ConfigurationError` (no silent `String` fallback).
   - Finishes conversions via `_finish_serializer_conversion` ensuring registered converters return a valid `SerializerFieldConversion` with kind `SCALAR`.

2. **Public Converter Registry (`register_serializer_field_converter`)**:
   - Sanctioned extension point for consumer `serializers.Field` subclasses.
   - Enforces type safety (`issubclass(field_class, serializers.Field)`), callable validation, and duplicate registration protection (`override=True` required to replace).

3. **Field Resolution and Reverse Mapping (`resolve_serializer_field`)**:
   - Resolves one serializer field into `(python_attr, annotation, InputFieldSpec)`.
   - **Model-backed path (`backing_model_field(model, field)` is not None)**:
     - Resolves column via 1-segment `source` (rejects dotted `source` or `source="*"`).
     - Relation columns enforce `PrimaryKeyRelatedField` and cardinality agreement (`_reject_relation_cardinality_mismatch`), resolving primary `DjangoType` via `_require_relation_primary`.
     - File columns resolve `Upload` annotation.
     - Scalar columns route through `_model_backed_scalar_annotation`: consumer-declared fields are checked for scalar agreement against the model column (failing loud on conflict), while consumer-declared `ChoiceField` generates a serializer-only enum.
   - **Column-less path**:
     - Finalizes `FILE` (`Upload`), relation annotations via `serializer_only_relation_annotation` (resolving target model from `field.queryset.model`), and scalar choices into generated enums (`_serializer_choice_enum`).
   - Naming rules (`serializer_field_graphql_name`): derived from declared serializer field name via the id-like-suffix rule (no doubled `...IdId` / `...PkId`).

4. **DRF Field Metadata to GraphQL Description (`serializer_field_description`)**:
   - Converts DRF `help_text` and validation constraints (`min_length`, `max_length`, `min_value`, `max_value`, `allow_blank`, `allow_empty`) into SDL field documentation.
   - Safely guards against hostile metadata descriptors.

5. **Serializer Choice Enum Management (`_SERIALIZER_CHOICE_ENUMS`)**:
   - Generates, caches, and deduplicates enums for serializer-only choice fields using `types/converters.py::build_enum_from_choices`.
   - Rejects colliding enum names with differing member sets.
   - Registers `clear_serializer_choice_enums` with `register_subsystem_clear`.

## Verification

1. **Caller and Dependency Audit**:
   - Audited all usages across `django_strawberry_framework/rest_framework/inputs.py` (`_resolve_nested_field`, `_injected_specs`, `_build_serializer_input_class`), `django_strawberry_framework/rest_framework/resolvers.py` (`_assert_runtime_serializer_agreement`), and `django_strawberry_framework/utils/inputs.py`.
   - Verified that `resolve_serializer_field` correctly populates `InputFieldSpec` with `target_name`, `source`, `kind`, `related_model`, `input_attr`, and `graphql_name`.

2. **Existing Test Suite Audit**:
   - Audited `tests/rest_framework/test_converter.py` (88 tests) and `tests/rest_framework/test_inputs.py` (93 tests).
   - Confirmed comprehensive coverage of all scalar types, precheck dispatch, MRO walk, custom registrations, enum generation/deduping, hostile repr safety, relation cardinality checks, and source validation.

3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/serializer_converter/test_serializer_converter_scratch.py`: verified all 14 built-in scalar converters, choice enum deduplication across multiple serializer classes, and conflicting choice enum member set rejection.
   - Scratch tests executed and passed (100%).

4. **Focused Test Execution**:
   - `uv run pytest tests/rest_framework/test_converter.py --no-cov`: 91 passed.
   - `uv run pytest tests/rest_framework/ --no-cov`: 447 passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/rest_framework/serializer_converter.py` is robust, complete, and thoroughly tested. Its fail-loud MRO dispatch, choice enum generation, type-override conflict checking, relation cardinality validation, and metadata extraction adhere strictly to spec-039.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/rest_framework/test_converter.py`: Added direct unit tests for `resolve_serializer_field` with model-backed `FileField` over a `models.FileField` column, `resolve_serializer_field` with column-less `FileField`, and `backing_model_field` returning `None` when handling `FieldDoesNotExist`.
- **Scoped diff against HEAD (`12779c99`):**
  - `django_strawberry_framework/rest_framework/serializer_converter.py`: empty (zero-edit target file).
- **Permanent tests and pinned behavior:**
  - `tests/rest_framework/test_converter.py`:
    - `test_backing_model_field_nonexistent_column_returns_none`: pins `backing_model_field` returning `None` when a field's source is not on the model.
    - `test_resolve_serializer_field_model_backed_file_field`: pins `resolve_serializer_field` returning `Upload` annotation and `kind=FILE` for model-backed file fields.
    - `test_resolve_serializer_field_column_less_file_field`: pins `resolve_serializer_field` returning `Upload` annotation and `kind=FILE` for column-less file fields.
- **Scratch verification:**
  - `docs/review/temp-tests/serializer_converter/test_serializer_converter_scratch.py`: passed (2 tests).
- **Formatter and linter results:**
  - `uv run ruff format .` passed.
  - `uv run ruff check --fix .` passed.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No (zero-edit target file, existing behavior unchanged).

## Independent verification (Worker 2)

- **System behavior re-traced:**
  - Audited `convert_serializer_field`: verified `convert_with_mro` dispatch sequence comprising ordered prechecks (`(BaseSerializer, ListSerializer)` nested rejection, `ManyRelatedField`, `RelatedField`, `FileField`, `ListField` child scalar validation, `MultipleChoiceField`), the live `_SERIALIZER_FIELD_CONVERTERS` MRO walk (all 16 built-in scalar converters including `DictField`/`HStoreField` -> `JSON`, `DurationField`/`IPAddressField`/`FilePathField` -> `str`, `ModelField` column unwrapping), and fail-loud `_unsupported_serializer_field` fallthrough returning `ConfigurationError` without silent `String` fallback.
  - Audited `register_serializer_field_converter`: verified extension registration validation (`issubclass(field_class, serializers.Field)`, callable check, and `override=True` duplicate guard).
  - Audited `resolve_serializer_field`: verified model-backed vs column-less path resolution, 1-segment `source` enforcement via `require_one_segment_source`, relation cardinality checks against backing model column (`_reject_relation_cardinality_mismatch`), relation target `DjangoType` enforcement (`_require_relation_primary`), file upload resolution (`Upload` annotation, `kind=FILE`), consumer-declared scalar type agreement check (`_model_backed_scalar_annotation`), choice enum generation and deduplication (`_serializer_choice_enum`), and the id-like suffix naming rules (`serializer_field_graphql_name`).
  - Audited `serializer_field_description`: verified metadata extraction (`help_text`, constraints `min_length`, `max_length`, `min_value`, `max_value`, `allow_blank`, `allow_empty`) and hostile descriptor exception handling.
  - Audited `clear_serializer_choice_enums`: verified cache reset and registered subsystem clear hook.

- **Zero-edit confirmation:**
  - Scoped diff against baseline `HEAD` (`12779c99`):
    `git diff 12779c99 -- django_strawberry_framework/rest_framework/serializer_converter.py` is empty (zero-edit confirmed).

- **Independent scratch experiments:**
  - Created `docs/review/temp-tests/serializer_converter/test_independent_scratch_serializer_converter.py`:
    1. Prechecks and unsupported handling: nested serializer rejection for single and `many=True` fields, unsupported relation type rejection (`SlugRelatedField`, `ManyRelatedField` wrapping `SlugRelatedField`), `ListField` invalid child handling (missing child, nested serializer child, relation child), and unmapped custom field `ConfigurationError`.
    2. Converter registration and `ModelField`: registration validation (type check, callable check, duplicate without override check, re-registration with override), `ModelField` unwrapping and missing `model_field` attribute rejection.
    3. Cardinality and relations: single relation to FK resolution, cardinality mismatch rejection (`ManyRelatedField` over FK, single `PrimaryKeyRelatedField` over reverse relation), and column-less relation without registered primary `DjangoType` rejection.
    4. Scalar conflict and naming: consumer-declared scalar type mismatch rejection, id-like suffix rule checks (`item_id` -> `itemId`, `item_pk` -> `itemPk`, `item` -> `itemId`, `items` -> `items`, `user_name` -> `userName`, `doc_file` -> `docFile`).
    5. Description and hostile metadata: description formatting with constraints and exception safety on hostile descriptors.
  - Result: all 5 independent scratch tests passed (`uv run pytest docs/review/temp-tests/serializer_converter/test_independent_scratch_serializer_converter.py --no-cov`).
  - Combined scratch test execution: all 7 tests passed (`uv run pytest docs/review/temp-tests/serializer_converter/ --no-cov`).

- **Permanent test suite execution:**
  - `uv run pytest tests/rest_framework/test_converter.py --no-cov`: 91 passed.
  - `uv run pytest tests/rest_framework/test_converter.py tests/rest_framework/test_inputs.py --no-cov`: 184 passed.

- **Findings disposition:**
  - No findings raised; all behaviors verified robust, complete, and fully conforming to spec-039.

