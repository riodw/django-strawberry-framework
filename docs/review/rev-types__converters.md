# Review: `django_strawberry_framework/types/converters.py`

Status: verified

## Understanding

`django_strawberry_framework/types/converters.py` owns the mapping and conversion of Django model fields to Python/Strawberry types for GraphQL read output, scalar lookup, choice enum generation, and relation annotation rendering.

### Key Responsibilities & Traced Behavior:
1. **Field Read Output Conversion (`convert_field_output`, `_field_output_type_for`)**:
   - `types/base.py:_build_annotations` delegates non-relation field conversion to `convert_field_output`.
   - Routes `FileField` and `ImageField` through `FIELD_OUTPUT_TYPE_MAP` to structured read-output objects (`DjangoFileType`, `DjangoImageType`).
   - File/image fields default to nullable (`<object> | None`) to accommodate empty/falsy `FieldFile` descriptor states, while allowing explicit narrowing via `force_nullable=False` (`Meta.required_overrides`).
   - `expose_filesystem_path=True` swaps standard file output objects for their security-gated opt-in counterparts (`DjangoFilePathType`, `DjangoImagePathType`) via `FILESYSTEM_PATH_OUTPUT_TYPE_MAP`.
   - Delegates all non-file fields to `convert_scalar`.
2. **Structured File/Image Types & Storage Guard (`_safe_file_attr`)**:
   - `DjangoFileType` defines resolver-backed `name` (non-null string), `size`, and `url`.
   - `DjangoImageType` subclasses `DjangoFileType`, adding `width` and `height`.
   - `_FileSystemPathFields` defines opt-in `path` with security description warnings.
   - `_safe_file_attr` guards property access against storage backend errors (`ValueError`, `OSError`, `NotImplementedError`), returning `None` instead of failing the entire GraphQL query, while allowing security violations (`SuspiciousFileOperation`) and unexpected bugs to propagate.
3. **Scalar Mapping & Tri-state Nullability (`convert_scalar`, `scalar_for_field`, `SCALAR_MAP`)**:
   - `SCALAR_MAP` maps standard Django model fields (e.g. `AutoField`, `CharField`, `DateTimeField`, `DecimalField`, `JSONField`, `UUIDField`, `BigIntegerField` -> `BigInt`, etc.) to Python types.
   - Mutable, last-write-wins design allowing consumer extension.
   - `scalar_for_field` performs MRO traversal against `SCALAR_MAP`, shared across type definition and filter/mutation inputs (`filters.inputs`, `mutations.inputs`).
   - `convert_scalar` computes `effective_null` from the `force_nullable` tri-state (`None` follows `field.null`, `True` widens, `False` narrows).
   - Handles soft-imported PostgreSQL field sentinels (`_ARRAY_FIELD_CLS` -> `list[inner]`, `_HSTORE_FIELD_CLS` -> `JSON`), rejecting nested arrays and outer choice definitions.
4. **Choice Enum Conversion (`convert_choices_to_enum`, `build_enum_from_choices`, `_sanitize_member_name`, `_is_enum_reserved_member`)**:
   - `convert_choices_to_enum` consults and populates `registry` enum cache keyed by `(model, field_name)` ensuring enum reuse across multiple `DjangoType`s.
   - `build_enum_from_choices` provides the shared enum construction core reused by DRF serializer conversions (`rest_framework/serializer_converter.py`).
   - Validates choice sequences, rejects empty sequences and Django's nested-tuple grouped-choices form.
   - Sanitizes member names from choice values (non-ASCII identifier replacement, leading digit `MEMBER_` prefix, Python keyword `_` prefix, GraphQL reserved `true`/`false`/`null` `MEMBER_` prefix, and Python `enum` reserved words/sunders/private mangling `MEMBER_` prefix).
   - Detects and rejects collisions where distinct choice values sanitize to identical enum members.
5. **Relation Annotation Rendering (`resolved_relation_annotation`)**:
   - Evaluates `FieldMeta` cardinality and nullability to return `list[target_type]`, `target_type | None`, or `target_type`.
   - Reused during deferred type finalization in `types/finalizer.py`.

## Verification

1. **Static and Structural Audit**:
   - Examined all 808 lines of `django_strawberry_framework/types/converters.py`.
   - Traced callers across `types/base.py`, `types/finalizer.py`, `types/resolvers.py`, `filters/inputs.py`, `mutations/inputs.py`, and `rest_framework/serializer_converter.py`.
   - Verified that `_safe_file_attr` catches only `(ValueError, OSError, NotImplementedError)`.
   - Verified `_is_enum_reserved_member` and `_sanitize_member_name` edge-case handling against Python `enum` internals and GraphQL specifications.
2. **Existing Test Suite Audit**:
   - `tests/types/test_converters.py` (74 tests covering choice enum generation, registry caching, grouped choices rejection, member sanitization, collision detection, subclass MRO resolution, BigInt contract, ArrayField/HStoreField sentinels, relation annotation, force_nullable tri-state, file/image output objects, and filesystem path opt-in).
3. **Scratch Experiments**:
   - Executed `docs/review/temp-tests/types_converters/test_scratch.py` verifying:
     - `_safe_file_attr` storage degradation and unexpected exception propagation.
     - `_sanitize_member_name` against exhaustive identifier, keyword, and reserved member shapes.
     - `resolved_relation_annotation` across `is_many_side` and `nullable` permutations.
4. **Focused Test Run**:
   - Executed `uv run pytest tests/types/test_converters.py docs/review/temp-tests/types_converters/ --no-cov` (77 passed, 2 skipped in 1.83s).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/types/converters.py` is well-architected, resilient, and comprehensive. Its field conversions, choice enum builders, defensive file attribute getters, and MRO-based lookups strictly adhere to framework invariants and are supported by extensive test coverage.

## Implementation (Worker 1)

None — zero-edit cycle

## Independent verification (Worker 2)

- **Independent Behavior Retracing**:
  - Verified `convert_field_output`: maps `FileField` and `ImageField` to `DjangoFileType` / `DjangoImageType` (or `DjangoFilePathType` / `DjangoImagePathType` with `expose_filesystem_path=True`), default nullable with explicit narrowing support via `force_nullable=False`, and delegates non-file columns to `convert_scalar`.
  - Verified `_safe_file_attr`: defensive attribute retrieval degrading storage backend errors (`ValueError`, `OSError`, `NotImplementedError`) to `None`, while properly propagating security exceptions like `SuspiciousFileOperation` and unexpected exceptions (`RuntimeError`).
  - Verified `convert_scalar`, `scalar_for_field`, and `SCALAR_MAP`: MRO traversal on field inheritance hierarchies, tri-state `force_nullable` logic (`None` follows `field.null`, `True` widens, `False` narrows), and PostgreSQL soft-imported sentinel types (`ArrayField`, `HStoreField`).
  - Verified `convert_choices_to_enum` & `build_enum_from_choices`: enum caching by `(model, field_name)` on registry, choice sequence normalization, member name sanitization (`_sanitize_member_name`), collision detection, and rejection of empty or grouped choices.
  - Verified `resolved_relation_annotation`: produces `list[target_type]`, `target_type | None`, or `target_type` based on `FieldMeta` cardinality and nullability.
- **Verification Experiments & Tests**:
  - Authored and ran `docs/review/temp-tests/types_converters/test_independent_scratch.py` covering:
    - Storage error degradation vs security / runtime exception propagation in `_safe_file_attr`.
    - Field output conversion with standard vs opt-in filesystem path types and `force_nullable` narrowing.
    - Scalar conversion MRO resolution and tri-state nullability.
    - Sanitization rules across regular values, leading digits, Python keywords, GraphQL reserved words, and Python `enum` internal attributes.
    - Choice enum construction, duplicate collision detection, empty choice rejection, grouped choice rejection, and registry caching.
    - Relation annotation resolution for many-to-many and foreign key relations.
  - Executed focused test runs:
    - `uv run pytest docs/review/temp-tests/types_converters/ tests/types/test_converters.py --no-cov` (84 passed, 2 skipped).
    - `uv run pytest tests/types/ --no-cov` (530 passed, 2 skipped).
- **Target File Status**:
  - Production file `django_strawberry_framework/types/converters.py` verified zero-edit in this review cycle.
- **Conclusion**:
  - `django_strawberry_framework/types/converters.py` satisfies all framework contracts, exhibits strict defensive boundaries, and is fully verified.

