# Review: `django_strawberry_framework/filters/inputs.py`

Status: verified

## Understanding

`django_strawberry_framework/filters/inputs.py` is the input generation, naming, conversion, and normalization engine of the filter subsystem (Layer 4). It bridges `django-filter` filter instances and lookup expressions with Strawberry GraphQL input types, implementing spec-027 Decision 9 module-global input materialization and spec-051 C3 convert/normalize symmetry.

### Key Responsibilities and Symbols:

1. **Module-Global Namespace Lifecycle (spec-027 Decision 9)**:
   - `INPUTS_MODULE_PATH`: `"django_strawberry_framework.filters.inputs"`, the canonical module path for `strawberry.lazy(...)` resolution.
   - `_materialized_names`, `_field_specs`, `_materialize_input`, `_clear_input_namespace`: instantiated via `make_set_input_namespace` (`utils/inputs.py`), managing input classes parked in `inputs.__dict__` and field provenance records.
   - `materialize_input_class`: public wrapper to park generated Strawberry input types in module globals.
   - `clear_filter_input_namespace`: clears materialized type cache and provenance ledger; registered via `register_subsystem_clear(owner="filters.input_namespace", before_bind=True)`.

2. **Logic Operator Descriptors & Q Composition**:
   - `_compose_and`, `_compose_or`, `_compose_not`: composition helpers combining lists of `models.Q` predicates into conjunctions, disjunctions, or negations.
   - `LogicOperatorDescriptor` dataclass: encapsulates `(python_attr, wire_name, is_sequence, compose)`.
   - `LOGIC_OP_AND` (`and_` / `and`), `LOGIC_OP_OR` (`or_` / `or`), `LOGIC_OP_NOT` (`not_` / `not`): immutable descriptors exposed via `LOGIC_OPERATORS`, `LOGIC_OPERATORS_BY_WIRE`, and `LOGIC_OPERATORS_BY_PYTHON_ATTR`.

3. **Lookup Maps & Search Construction**:
   - `LOOKUP_PREFIXES`: maps `^` -> `istartswith`, `=` -> `iexact`, `@` -> `search`, `$` -> `iregex`.
   - `LOOKUP_NAME_MAP`: maps 25 standard Django lookups to `(python_attr, graphql_name)` pairs (e.g. `isnull` -> `("is_null", "isNull")`, `in` -> `("in_", "in")`).
   - `construct_search`: translates lookup prefix keys into django-filter expressions.

4. **Scalar & Choice Type Resolution**:
   - `_pascal_case`: PascalCase identifier converter, raising `ConfigurationError` when input contains no word characters.
   - `_scalar_from_form_field`: maps `django.forms` field types (`NullBooleanField`, `BooleanField`, `IntegerField`, `FloatField`, `DecimalField`, `DateTimeField`, `DateField`, `TimeField`, `UUIDField`, `CharField`) to Python scalar types, with Float/Decimal matched before Integer.
   - `_scalar_from_model_field`: delegates to `scalar_for_field` (`types/converters.py`), defaulting to `str` if model field is `None`.
   - `_choice_enum_from_filter`: derives Strawberry enum types from model field choices via `convert_choices_to_enum`.
   - `_element_annotation`: resolves inner element types prioritizing choice enums, then model field scalars, then form field scalars.

5. **Symmetric Conversion & Normalization (spec-051 C3)**:
   - `_FILTER_INPUT_KIND_TYPES`: single most-specific-first ladder shared between conversion and normalization (`GlobalIDMultipleChoiceFilter`, `GlobalIDFilter`, `BaseCSVFilter`, `(RangeFilter, _DjangoRangeFilter)`, `(ListFilter, ArrayFilter)`, `TypedFilter`, `(ChoiceFilter, TypedChoiceFilter)`, `object`).
   - `convert_filter_to_input_annotation`: converts Filter instances to Strawberry GraphQL annotations, applying optionality (`T | None`) unless `extra["required"]` is `True`.
   - `normalize_input_value`: normalizes incoming Strawberry input values (dataclass instances, dicts, enums, `relay.GlobalID`, or `UNSET`) into django-filter form data.

6. **Range & GlobalID Helpers**:
   - `_encode_global_id_input`: encodes `relay.GlobalID` objects to base64 wire strings.
   - `_unwrap_enum_member`: extracts `.value` from `enum.Enum` instances.
   - `_build_range_input_class`: builds and caches `<FilterSet><Field>RangeInputType` classes keyed by `(filterset_cls, field_name, inner)` on `filter_instance._range_input_classes`.
   - `_normalize_range_value`: creates `{<base>_0, <base>_1}` dictionary patches for range inputs, omitting inactive / `UNSET` axes.

7. **Input Field & Bag Builders**:
   - `_build_logic_fields`: returns Strawberry field triples for `and_`, `or_`, `not_` logic operators with forward references via `strawberry.lazy(INPUTS_MODULE_PATH)`.
   - `_build_input_fields`: groups filterset declared and auto-generated filters, respects `HIDE_FLAT_FILTERS`, mints operator bags for leaves, connects nested `RelatedFilter` relations, and delegates emission to `emit_set_input_field_triples`.
   - `_model_field_for_filter`: resolves Django model fields across multi-hop relation paths.

## Verification

1. **Dependency and Caller Mapping**:
   - `django_strawberry_framework/filters/__init__.py`: verified `filter_input_type` helper and re-exports.
   - `django_strawberry_framework/filters/factories.py`: verified consumption of `_build_input_fields` and `_build_logic_fields` in `FilterArgumentsFactory`.
   - `django_strawberry_framework/filters/sets.py`: verified consumption of `LOGIC_OPERATORS`, `LOOKUP_NAME_MAP`, `_field_specs`, and `normalize_input_value`.
   - `django_strawberry_framework/orders/inputs.py`: verified architectural parity with `orders` input generation.
   - `django_strawberry_framework/utils/inputs.py`: verified shared substrate contracts.

2. **Existing Test Suite Audit**:
   - `tests/filters/test_inputs.py`: read all 1,650+ lines and audited 80 existing tests covering logic operators, bag building, digit boundaries, range class caching, Relay relations, `HIDE_FLAT_FILTERS`, and namespace clear.

3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/filters__inputs/test_scratch_inputs.py` verifying Q object composition (`_compose_and`, `_compose_or`, `_compose_not`), `_element_annotation` choice derivation, `BaseCSVFilter` normalization, `materialize_input_class` module registration, and `model_field=None` fallback paths.
   - Ran scratch tests: 2 passed.

4. **Focused Test Runs**:
   - `uv run pytest tests/filters/test_inputs.py --no-cov`: 84 passed (80 existing + 4 new permanent tests).
   - `uv run pytest tests/filters/ --no-cov`: 546 passed across the filter subsystem.
   - Statement coverage on `django_strawberry_framework/filters/inputs.py`: 100% (262/262 lines).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/filters/inputs.py` is clean, robust, thoroughly tested, and adheres strictly to spec-027 Decision 9, spec-028, and spec-051 C3. No defects or design issues were found. Permanent test coverage was added to `tests/filters/test_inputs.py` to pin `_element_annotation` choice derivation across `TypedFilter`, `ListFilter`, and `BaseCSVFilter`, `BaseCSVFilter` normalization, `materialize_input_class` global registration, and fallback scalar resolution when `model_field` is `None`.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/filters/test_inputs.py`: added imports (`BaseInFilter`, `_element_annotation`, `materialize_input_class`) and 4 permanent test cases:
    - `test_normalize_input_value_base_csv_filter_unwraps_elements`: pins `BaseCSVFilter` element-by-element normalization and enum unwrapping.
    - `test_convert_filter_to_input_annotation_derives_enum_for_choice_fields_on_list_and_csv_filters`: pins choice enum resolution in `_element_annotation` for `TypedFilter`, `ListFilter`, and `BaseCSVFilter`.
    - `test_element_annotation_fallback_branches_when_model_field_is_none`: pins form field resolution and `str` fallback when `model_field` is `None`.
    - `test_materialize_input_class_registers_in_module_globals`: pins `materialize_input_class` module global assignment and `_materialized_names` recording.
- **Permanent tests and pinned behavior:**
  - `tests/filters/test_inputs.py` (84 tests total):
    - Pins logic operator descriptors, mappings, wire names, and `models.Q` composition semantics.
    - Pins `LOOKUP_NAME_MAP` and `LOOKUP_PREFIXES` mappings.
    - Pins `build_input_class` Strawberry input dataclass generation and aliases.
    - Pins `_build_input_fields` grouping, operator bags, camel-case pinning, relation traversal, and declared filter preserved keys.
    - Pins `convert_filter_to_input_annotation` across GlobalID, Range, List, CSV, Typed, and Choice filters.
    - Pins `normalize_input_value` across GlobalID objects, enum members, Range inputs (partial axes, `None`, `UNSET`), and CSV/List elements.
    - Pins `_build_range_input_class` caching and per-filterset qualification preventing schema collisions.
    - Pins `_pascal_case` and `ClassBasedTypeNameMixin.type_name_for` error diagnostics on invalid word tokens.
    - Pins `_scalar_from_form_field` and `_scalar_from_model_field` scalar mappings.
    - Pins `construct_search` prefix translation.
    - Pins `filter_input_type` lazy annotation and helper reference tracking.
    - Pins `clear_filter_input_namespace` resilient submodule lookups.
    - Pins `HIDE_FLAT_FILTERS` setting behaviors.
    - Pins Relay-relation `isNull` Boolean input generation.
- **Scratch verification:**
  - `docs/review/temp-tests/filters__inputs/test_scratch_inputs.py` passed.
  - `uv run pytest tests/filters/test_inputs.py --no-cov` passed (84/84 tests).
  - `uv run pytest tests/filters/ --no-cov` passed (546/546 tests).
- **Formatter and linter results:**
  - `uv run ruff format .` passed.
  - `uv run ruff check --fix .` passed.
  - `uv run python scripts/check_trailing_commas.py` passed.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

- **Target zero-edit check:** Verified `git diff 12779c99 -- django_strawberry_framework/filters/inputs.py` produces empty diff (target production file is zero-edit against baseline `HEAD`).
- **Behavioral re-trace:**
  - Traced logical operator descriptors (`LOGIC_OP_AND`, `LOGIC_OP_OR`, `LOGIC_OP_NOT`) and Q composition semantics (`_compose_and`, `_compose_or`, `_compose_not`). Verified correct handling of empty predicate lists, single predicates, and multiple conjunction/disjunction clauses.
  - Traced module-global namespace lifecycle (`make_set_input_namespace`, `_materialized_names`, `_field_specs`, `materialize_input_class`, `clear_filter_input_namespace`) implementing spec-027 Decision 9. Confirmed cleanup integration through `register_subsystem_clear(before_bind=True)` and `registry.clear()`.
  - Traced scalar and enum type derivation (`_scalar_from_form_field`, `_scalar_from_model_field`, `_choice_enum_from_filter`, `_element_annotation`). Verified choice enums take precedence when model field choices are present, followed by model field scalars, form field scalars, and fallback `str`.
  - Traced symmetric conversion and normalization ladder (`_FILTER_INPUT_KIND_TYPES`, `convert_with_mro`) across Relay GlobalID filters, CSV filters, Range filters, List/Array filters, Typed filters, and Choice filters (spec-051 C3).
  - Traced RangeFilter sub-input caching and per-filterset class naming qualification (`_build_range_input_class`), ensuring schemas do not collide when multiple filtersets share field names.
  - Traced `normalize_input_value` handling of inactive sentinels (`UNSET`, `None`), GlobalID base64 re-encoding, enum unwrapping, and partial range dictionaries (`{field_0, field_1}`).
  - Traced top-level input field emission (`_build_input_fields`, `_model_field_for_filter`, `_build_logic_fields`) and `HIDE_FLAT_FILTERS` configuration filtering.
- **Permanent test audit:**
  - Audited 4 permanent test additions in `tests/filters/test_inputs.py`:
    - `test_normalize_input_value_base_csv_filter_unwraps_elements`: verified CSV filter normalizer unwraps enum elements.
    - `test_convert_filter_to_input_annotation_derives_enum_for_choice_fields_on_list_and_csv_filters`: verified `_element_annotation` resolves GraphQL choice enum for `TypedFilter`, `ListFilter`, and `BaseCSVFilter`.
    - `test_element_annotation_fallback_branches_when_model_field_is_none`: verified fallback resolution through form field and `str` fallback when `model_field` is `None`.
    - `test_materialize_input_class_registers_in_module_globals`: verified module global registration and ledger recording.
- **Independent scratch verification:**
  - Created and ran `docs/review/temp-tests/filters__inputs/test_scratch_worker2.py` (8 test functions) covering:
    - Logic operator descriptors, composition of empty vs multi-predicate Q trees.
    - GlobalID re-encoding and enum member unwrapping (including `None`-valued enum members).
    - Inactive value sentinels (`UNSET`, `None`) and normalization across filter kinds.
    - `RangeFilter` class caching and qualification by owning filterset and scalar type.
    - `_pascal_case` conversion and `ConfigurationError` diagnostics on tokenless inputs.
    - `convert_filter_to_input_annotation` required (`extra={"required": True}`) vs optional (`| None`) annotations and method filter error diagnostics.
    - `_model_field_for_filter` resolution across single-hop and multi-hop foreign key relations.
    - Subsystem clear hook integration with `registry.clear()`.
  - Scratch test execution: 8/8 passed.
- **Focused test runs:**
  - `uv run pytest tests/filters/test_inputs.py --no-cov`: 84 passed.
  - `uv run pytest tests/filters/ --no-cov`: 550 passed.
- **Finding disposition:**
  - No defects, performance issues, or architectural drift identified.
  - Zero open findings. All behaviors strictly adhere to spec-027, spec-028, and spec-051.
- **Conclusion:** Verification complete. Status set to `verified`.
