# Review: `django_strawberry_framework/filters/sets.py`

Status: verified

## Understanding

`django_strawberry_framework/filters/sets.py` implements the core filterset layer of the filtering subsystem (spec-027 Layers 3 and 4, Decision 4 own-PK & Relay relation handling, and Decision 8 named-helper pipeline decomposition).

Key responsibilities include:
1. **FilterSet Metaclass & Lifecycle (`FilterSetMetaclass`, `promote_set_meta_fields`, `collect_related_declarations`):**
   - Intercepts filter declarations, migrates `Meta.filter_fields` legacy aliases to `Meta.fields` with deprecation guidance, collects `RelatedFilter` definitions into tombstoned descriptors, and stamps declared filters with `declared` provenance.
2. **Filter Snapshot & Provenance (`CandidateFilterMetadata`, `ExpansionSnapshot`, `FilterGenerationProvenance`):**
   - Lazily builds immutable snapshots (`ExpansionSnapshot`) mapping candidate filter names to `CandidateFilterMetadata` (frozen routing bits, relation traversal flags, audited filter profiles).
   - Tracks provenance (`framework_default`, `package_replacement`, `declared`, `override_generated`) and normalized policy baseline entries against `_PUBLIC_PACKAGE_FILTER_DEFAULTS` and `_PACKAGE_POLICY_BASELINE` to fail-closed against custom or monkeypatched filter classes.
3. **Relay & Ownership Awareness (`filter_for_field`, `filter_for_lookup`, `_generation_origin_for_field`, `_is_generation_capable`):**
   - Converts own-PK and Relay-Node relation targets to `GlobalIDFilter` or `GlobalIDMultipleChoiceFilter` depending on cardinality, rejecting non-supported lookups (`exact`, `in`, `isnull`) fail-closed at build time.
   - Cleans model choice extras via `_strip_model_choice_extras` and handles non-PK target relations via `_GLOBALID_RELATION_PK_ATTR`.
4. **Input Normalization & Traversal (`_normalize_input`, `_operator_bag_items`, `_iter_logic_branches`, `_validate_logic_branch_shape`, `_validate_logic_element_shape`):**
   - Deconstructs Strawberry dataclass inputs and operator bags into django-filter form data while stripping nested relation branches (which are handled via explicit subqueries). Validates logical branch shapes fail-closed.
5. **Queryset & Logic Execution Pipeline (`apply_sync`, `apply_async`, `apply`, `filter_queryset`, `_apply_flat_leaves`, `_evaluate_logic_tree`, `_q_for_branch`, `_apply_related_constraints`):**
   - Implements the 8-step Decision 8 execution pipeline: derives visibility querysets, applies `RelatedFilter` constraints via subqueries, validates forms (raising `GraphQLError` with `FILTER_INVALID`), executes flat leaves with correlated-`EXISTS` optimization on routable to-many paths, and composes logical `and`/`or`/`not` trees via `pk__in` subqueries.

## Verification

1. **Existing Test Suite:**
   - Executed `uv run pytest tests/filters/test_sets.py --no-cov` (292 tests passing).
   - Executed `uv run pytest tests/filters/ --no-cov` (550 tests passing across all filter test suites).
   - Verified tests covering: metaclass promotion, cycle-safe related filter expansion, owner-aware Relay vs scalar conversions, logical branch nesting and depth caps (`_MAX_LOGIC_DEPTH = 5`), permission gating, form error formatting, and correlated-`EXISTS` leaf execution.
2. **Scratch Experiments:**
   - Authored `docs/review/temp-tests/filters__sets/test_scratch_sets.py` to probe:
     - `_lookups_for_field` caching and `Transform` exclusion.
     - `_strip_model_choice_extras` dropping model-choice specific keyword arguments.
     - `_release_is_audited` bounds and edge cases.
     - `_validate_logic_branch_shape` fail-closed container/scalar validation.
   - All scratch tests passed without regressions.

## Improvements

### High
None.

### Medium
None.

### Low
None.

## Summary

`django_strawberry_framework/filters/sets.py` provides an exceptionally well-engineered, robust, and fail-closed implementation of the FilterSet architecture. It rigorously isolates framework-generated filters from user overrides, handles Relay node conversions and cardinality seamlessly, enforces strict type and container validation on logical trees, and maintains complete compatibility with django-filter while optimizing to-many traversals with correlated `EXISTS` subqueries. No defects were discovered.

## Implementation (Worker 1)

- **Changed files:** None (target is in pristine condition; verified without requiring code changes).
- **Permanent tests:** Existing comprehensive suite in [tests/filters/test_sets.py](file:///Users/riordenweber/projects/django-strawberry-framework/tests/filters/test_sets.py) (292 tests) covers all contracts.
- **Scratch / focused verification:** Verified with [docs/review/temp-tests/filters__sets/test_scratch_sets.py](file:///Users/riordenweber/projects/django-strawberry-framework/docs/review/temp-tests/filters__sets/test_scratch_sets.py) and focused pytest runs.
- **Formatter / Linter results:** `uv run ruff check django_strawberry_framework/filters/sets.py` passed with 0 errors.
- **Evidence for rejected findings:** Deep-dive analysis and full test suite verification confirmed that ownership tracking, lookup validation, depth capping, and async/sync visibility derivations behave correctly in all documented scenarios.
- **Changelog merit:** No release note needed (no changes to existing behavior).

## Independent verification (Worker 2)

- **Target zero-edit check:** Verified `git diff 12779c99 -- django_strawberry_framework/filters/sets.py` produces an empty diff (target production file is zero-edit against baseline `HEAD`).
- **Behavioral re-trace:**
  - Traced metaclass lifecycle in `FilterSetMetaclass`: legacy `Meta.filter_fields` alias promotion, tombstoning of `RelatedFilter` declarations, and automatic stamping of `FilterGenerationProvenance(origin="declared")` on all declared filter instances.
  - Traced snapshot construction and caching in `ExpansionSnapshot` and `CandidateFilterMetadata`: frozen candidate routing flags, dynamic CSV detection, family profiling against `_FILTER_FAMILY_REGISTRY`, and fail-closed isolation of user customizations and monkeypatched classes.
  - Traced generation origin classification in `_generation_origin_for_field` and generation capability checks in `_is_generation_capable`, ensuring custom hooks, custom initializers, and shadowed defaults drop out of optimization safely.
  - Traced Relay node detection and cardinality mapping in `_is_own_pk_under_relay_owner`, `_relay_filter_class_for_field`, and `filter_for_lookup`: ensures own-PK and Relay relation targets resolve to `GlobalIDFilter` or `GlobalIDMultipleChoiceFilter`, while rejecting unsupported lookups (`gt`, `lt`, `range`, `icontains`) with typed `ConfigurationError`s.
  - Traced input normalization and operator bag extraction in `_normalize_input` and `_operator_bag_items`: maps Strawberry dataclass operator bags to django-filter form keys while stripping nested relations for subquery handling.
  - Traced shape validation in `_validate_logic_branch_shape` and `_validate_logic_element_shape`: validates that logical containers and elements adhere strictly to list/mapping structures, preventing permission and filter bypasses.
  - Traced the Decision 8 execution pipeline (`apply_sync`, `apply_async`, `apply`): verified 8-stage sequence, related visibility derivation with database shard preservation (`parent_db=queryset.db`), single-pass permission check semantics (`run_permissions=False` on recursive sub-derivations), form validation raising `GraphQLError` with `FILTER_INVALID`, correlated-`EXISTS` leaf evaluation via `_apply_flat_leaves` and `_invoke_suppressing_framework_distinct`, and `pk__in` subquery composition under `_evaluate_logic_tree`.
  - Traced depth cap enforcement (`_MAX_LOGIC_DEPTH = 5`) across async visibility collection, permission recursion, and tree evaluation, raising consistent `ConfigurationError`s on excessive nesting.
- **Independent scratch verification:**
  - Created and executed [docs/review/temp-tests/filters__sets/test_independent_scratch_sets.py](file:///Users/riordenweber/projects/django-strawberry-framework/docs/review/temp-tests/filters__sets/test_independent_scratch_sets.py) (9 test functions) covering:
    - `_dynamic_csv_profile_for` base counts, ordering, unaudited scalar bases, and custom method detection.
    - `_is_generation_capable` across clean and overridden subclasses (overridden `filter_for_field`, `filter_for_lookup`, `FILTER_DEFAULTS`, `__init__`).
    - `FilterGenerationProvenance` stamping for declared filters.
    - `_invoke_suppressing_framework_distinct` distinct flag restoration on exceptions.
    - `apply` translation of `SyncMisuseError` into `RuntimeError`.
    - `_validate_form_or_raise` `GraphQLError` formatting on form validation errors.
    - Relay own-PK and relation lookup validation rejecting unsupported lookups.
    - `_MAX_LOGIC_DEPTH` depth cap exceeded error raising.
    - `_apply_related_constraints` model mismatch validation rejecting mismatched explicit querysets.
  - All 9 independent scratch tests passed.
- **Focused test runs:**
  - `uv run pytest tests/filters/test_sets.py --no-cov`: 292 passed.
  - `uv run pytest tests/filters/ --no-cov`: 550 passed across all filter test suites.
  - `uv run pytest docs/review/temp-tests/filters__sets/test_independent_scratch_sets.py --no-cov`: 9 passed.
- **Finding disposition:**
  - No defects, performance issues, or regressions found.
  - Zero open findings. All behaviors strictly adhere to spec-027, spec-028, and spec-051.
- **Conclusion:** Verification complete. Status set to `verified`.

