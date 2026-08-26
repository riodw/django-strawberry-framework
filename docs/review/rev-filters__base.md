# Review: `django_strawberry_framework/filters/base.py`

Status: verified

## Understanding

`django_strawberry_framework/filters/base.py` is the foundational primitive layer of the filter subsystem (Layer 3). It owns custom filter classes, form fields, method dispatchers, validation guards, and strategy-aware GlobalID resolution consumed across `django_strawberry_framework/filters/`, `types/finalizer.py`, and schema generation.

### Key Responsibilities and Symbols:
1. **`TypedFilter`**:
   - Base filter marker for Strawberry-side filter input generation; intentionally dropped Graphene's legacy `input_type` property and constructor kwarg.
2. **`_EmptyListAwareFilterMethod` / `ArrayFilterMethod` / `ListFilterMethod` / `_install_empty_list_aware_method`**:
   - Single-sited `FilterMethod` hierarchy ensuring `[]` is treated as a valid filter value for array- and list-shaped filters rather than short-circuiting like django-filter's `EMPTY_VALUES` check. Only `None` short-circuits.
3. **Lookup & Restrictive Matching Helpers (`_apply_lookups`, `_apply_lookup_predicate`, `_match_none_queryset`)**:
   - Unified helpers that bind whole-list predicates in a single `filter`/`exclude` call, honor `distinct=True`, and return `qs.none()` (or `qs` if `exclude=True`) for restrictive-empty predicates.
4. **Relation PK Target Detection (`_relation_uses_non_pk_to_field`, `_marked_pk_field_name`)**:
   - Identifies relations targeting non-pk `to_field` and derives `f"{field_name}__pk"` dynamically from the live filter instance at filter time, surviving `_expand_related_filter` rebasing.
5. **`ArrayFilter`**:
   - Filter for PostgreSQL `ArrayField` columns; preserves `[]` as a real value and swaps in `ArrayFilterMethod`.
6. **`validate_range` / `RangeField` / `RangeFilter`**:
   - 2-element sequence validation and custom Django form field with `empty_values = [None]`.
7. **`ListFilter`**:
   - List-shaped lookup filter short-circuiting `[]` to `qs.none()` (or `qs` when `exclude=True`).
8. **Integer Bounds Protection (`_coerce_int_in_members`, `IntegerInFilter`, `IntegerRangeFilter`)**:
   - `IntegerInFilter`: coerces elements via `coerce_field_value_or_none`, drops out-of-range values, matches nothing if all elements drop from non-empty input, and keeps default skip on `in: []`.
   - `IntegerRangeFilter`: decomposes `__range` into a single-predicate `gte` + `lte` conjunction to prevent SQLite/PostgreSQL integer overflow errors.
9. **Strategy-Aware GlobalID Resolution (`resolve_globalid_target_definition`, `_target_definition_for`, `_accepted_globalid_type_names`, `_decode_and_validate_global_id`)**:
   - Iteratively resolves multi-hop relation paths (`shelf__branch__id`) and own-PK filters to the target `DjangoTypeDefinition`.
   - Validates GlobalID payloads against the target type's `effective_globalid_strategy` (`model`, `type`, `type+model`), fail-closing on encode-only strategies (`callable`, `custom`) or unrecorded strategies.
   - Enforces non-empty `node_id` and coerces against target PK model field types.
10. **`GlobalIDFilter` & `GlobalIDMultipleChoiceFilter`**:
    - Single and multi-value GlobalID filters; `_AbsentGlobalIDMultipleChoiceWidget` distinguishes key omission (skip) from explicit `in: []` (match nothing).
11. **`RelatedFilter`**:
    - Cross-FilterSet traversal primitive inheriting `RelatedSetTargetMixin` from `sets_mixins.py` with idempotent owner binding, cached lazy target resolution, and auto-derived queryset from the target model.

## Verification

1. **Dependency and Caller Mapping**:
   - `django_strawberry_framework/filters/__init__.py`: verified all public exports and re-exports.
   - `django_strawberry_framework/filters/inputs.py`: verified consumption of `TypedFilter`, `ArrayFilter`, `ListFilter`, `RangeFilter`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`, and `RelatedFilter`.
   - `django_strawberry_framework/filters/sets.py`: verified consumption of `_GLOBALID_RELATION_PK_ATTR`, `_relation_uses_non_pk_to_field`, `IntegerInFilter`, `IntegerRangeFilter`, `RelatedFilter`, and family profile registrations.
   - `django_strawberry_framework/types/finalizer.py`: verified build-time audit calling `resolve_globalid_target_definition` and checking `ENCODE_ONLY_GLOBALID_STRATEGIES`.
   - `django_strawberry_framework/orders/base.py`: verified architectural parity between `RelatedFilter` and `RelatedOrder` using `RelatedSetTargetMixin`.
2. **Existing Test Suite Audit**:
   - `tests/filters/test_base.py`: read all 1,277 lines and verified test assertions across all filter types, method setters, integer bounds, GlobalID validation, and lazy target resolution.
3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/filters__base/test_scratch_filters__base.py` testing `IntegerInFilter` bound parent behavior, `ListFilter` sequence handling, relation helper edge cases, and `RelatedFilter.get_queryset` target model absence.
   - Ran `uv run pytest docs/review/temp-tests/filters__base/test_scratch_filters__base.py --no-cov`: 3 passed.
4. **Focused Test Runs**:
   - `uv run pytest tests/filters/test_base.py --no-cov`: 106 passed.
   - `uv run pytest tests/filters/ --no-cov`: 542 passed across the filter subsystem.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/filters/base.py` is robust, clean, well-tested, and adheres strictly to all architectural specifications (spec-027, spec-028, spec-031 Decision 13). Edge case coverage was permanently expanded in `tests/filters/test_base.py` for relation helper predicates, marked pk attributes, and `RelatedFilter.get_queryset` when target filtersets lack model metadata.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/filters/test_base.py`: added edge case tests covering `_relation_uses_non_pk_to_field`, `_marked_pk_field_name`, and `RelatedFilter.get_queryset` with target FilterSet without model.
- **Permanent tests and pinned behavior:**
  - `tests/filters/test_base.py` (106 tests total):
    - Pins `TypedFilter` interface contract.
    - Pins `ArrayFilter` empty list preservation, `ArrayFilterMethod` dispatch, and distinct flag handling.
    - Pins `RangeField` and `validate_range` length-2 sequence constraints.
    - Pins `IntegerRangeFilter` gte/lte decomposition, exclude negation, and malformed value handling.
    - Pins `ListFilter` empty list match-none short-circuiting, exclude compliment, and `ListFilterMethod` dispatch.
    - Pins `IntegerInFilter` range coercion, out-of-range member dropping, all-dropped match-none, and `in: []` skip preservation.
    - Pins `GlobalIDFilter` decoding, empty node id rejection, and marked pk field redirection.
    - Pins `GlobalIDMultipleChoiceFilter` batch decoding, indexed error messages, single-predicate `in` lookup, and `_AbsentGlobalIDMultipleChoiceWidget` omission preservation.
    - Pins `RelatedFilter` lazy target resolution, explicit vs auto-derived querysets, and `RelatedSetTargetMixin` binding.
    - Pins `resolve_globalid_target_definition` multi-hop and own-PK resolution across strategy profiles (`model`, `type`, `type+model`, fail-closed encode-only).
- **Scratch verification:**
  - `docs/review/temp-tests/filters__base/test_scratch_filters__base.py` passed (3/3 tests).
  - `uv run pytest tests/filters/test_base.py --no-cov` passed (106/106 tests).
  - `uv run pytest tests/filters/ --no-cov` passed (542/542 tests).
- **Formatter and linter results:**
  - `uv run ruff format .` passed with 0 errors.
  - `uv run ruff check --fix .` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

- **Scoped baseline verification:**
  - Confirmed `git diff 12779c99 -- django_strawberry_framework/filters/base.py` is zero-edit (0 diff).
- **Behaviors and paths traced:**
  - `TypedFilter`: Verified interface contract as base marker for GraphQL filter input generation without legacy Graphene `input_type` property.
  - `_EmptyListAwareFilterMethod` & `_install_empty_list_aware_method`: Verified `[]` is preserved as a valid filter value reaching custom methods for `ArrayFilterMethod` and `ListFilterMethod` while only `None` short-circuits.
  - `_apply_lookups`, `_apply_lookup_predicate`, `_match_none_queryset`: Traced single-predicate binding, `distinct=True` handling, and restrictive-empty queryset handling (`qs.none()` or `qs` on `exclude=True`).
  - `ArrayFilter`: Traced empty list preservation across array lookups (`contains`, `overlap`, `contained_by`), `method` setter swapping in `ArrayFilterMethod`.
  - `RangeFilter` & `validate_range`: Traced 2-element sequence validation, rejection of non-sequences / lengths != 2, and `RangeField` clean behavior.
  - `ListFilter`: Traced `[]` short-circuiting to `qs.none()` / `qs` on exclude, non-empty list delegation, and `ListFilterMethod` swapping.
  - `IntegerInFilter` & `IntegerRangeFilter`: Traced integer range coercion, dropping of out-of-range elements, `qs.none()` when non-empty input fully drops, `in: []` skip preservation, and range decomposition to single `gte` + `lte` predicate.
  - Strategy-Aware GlobalID Resolution: Traced `_decode_and_validate_global_id`, `resolve_globalid_target_definition`, `_target_definition_for`, `_accepted_globalid_type_names`, fail-closing on `callable`/`custom` or unrecorded `None` strategy (`GLOBALID_UNVALIDATABLE`), type mismatch detection, and non-empty node ID enforcement (`GLOBALID_INVALID`).
  - `GlobalIDFilter` & `GlobalIDMultipleChoiceFilter`: Traced single and multi-value decoding, `_AbsentGlobalIDMultipleChoiceWidget` omission preservation, `_GlobalIDMultipleChoiceField` choice validation bypass, and dynamic `_marked_pk_field_name` (`f"{field_name}__pk"`) derivation surviving `_expand_related_filter` rebasing.
  - `RelatedFilter`: Traced `lookups=` kwarg rejection, lazy target resolution via `RelatedSetTargetMixin`, and auto-derived queryset from target `_meta.model`.
- **Independent scratch tests:**
  - Created and executed `docs/review/temp-tests/filters__base/test_scratch_worker2.py` (5 tests) verifying custom method dispatch with `[]`, list filter exclusion, range field validation, integer in/range boundaries, and related filter contracts.
  - Executed `docs/review/temp-tests/filters__base/test_scratch_filters__base.py` (5 tests) covering bound integer in filter, list filter scalars, relation helper edge cases, and absent GlobalID widget/field behaviors.
- **Test execution:**
  - `uv run pytest tests/filters/test_base.py docs/review/temp-tests/filters__base/test_scratch_filters__base.py docs/review/temp-tests/filters__base/test_scratch_worker2.py --no-cov`: 114/114 passed.
  - `uv run pytest tests/filters/ --no-cov`: 543/543 passed.
- **Findings disposition:**
  - All symbols, helper functions, and classes in `django_strawberry_framework/filters/base.py` are robust, strictly comply with specifications (spec-027, spec-028, spec-031 Decision 13), and have extensive test coverage. No defects or regressions found.

