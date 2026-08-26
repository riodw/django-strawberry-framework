# Review: `django_strawberry_framework/orders/sets.py`

Status: verified

## Understanding

`django_strawberry_framework/orders/sets.py` defines `OrderSetMetaclass` and `OrderSet`, providing the declarative specification, validation, and resolver apply pipeline for order sets (Layers 3, 4, and 7 per spec-028).

### Key Responsibilities and Symbols:
1. **`OrderSetMetaclass`**:
   - Discovers and collects `RelatedOrder` declarations across the inheritance hierarchy using `collect_related_declarations` from `django_strawberry_framework.sets_mixins`.
   - Binds each collected `RelatedOrder` to the created class via `bind_orderset`.
   - Promotes `Meta.fields` using `promote_set_meta_fields` (`utils/inputs.py`).
2. **`OrderSet` Foundation**:
   - Inherits `type_name_for` from `ClassBasedTypeNameMixin` (generating `{cls.__name__}InputType` for root and related fields).
   - Inherits the permission facade from `ActiveInputPermissionMixin` (`_permission` configured with `family_label="OrderSet"`, `related_attr="related_orders"`, `target_attr="orderset"`, and `handle_top_level_list=True`).
   - Maintains lifecycle attributes (`_owner_definition`, `_expanded_fields`, `_is_expanding_fields`) mapped via `_lifecycle = SetLifecycleAttrs(...)`.
3. **Field Expansion & Caching (`get_fields` / `_expand_meta_fields`)**:
   - Expands `Meta.fields` (supporting list/tuple of paths or `"__all__"` derived via `_get_concrete_field_names_for_order`).
   - Validates each declared field path against the model using `classify_path`, raising framework `ConfigurationError` on invalid paths.
   - Merges declared `related_orders` on top of model fields.
   - Enforces cycle-safe expansion caching via `expanded_once` and `should_cache_expansion` (caching only when `related_orders` is defined directly on the class and all lazy references have resolved to real classes).
4. **Apply Pipeline (`apply_sync` / `apply_async` / `_apply_orderings` / `_resolve_order_expressions`)**:
   - Classmethod pair `apply_sync` and `apply_async` extract request context via `_request_from_info` and execute active-input permission checks before any queryset mutation.
   - `apply_async` wraps permission checks in `run_in_one_sync_boundary` so synchronous consumer permission checks do not block the event loop.
   - `_resolve_order_expressions` transforms normalized `(field_path, direction)` pairs into Django `OrderBy` expressions.
   - Automatically detects to-many relations (reverse FK / M2M) via `_path_traverses_to_many`. For to-many relations, orders via row-preserving `Min` (for ascending) or `Max` (for descending) aggregate annotations (`_dst_order_{index}_{flatten_lookup_path(path)}`), eliminating fan-out duplicate rows while maintaining connection pagination invariants.
   - Direct scalar and to-one relation paths order directly without aggregation.
   - Re-validates field paths at execution against the concrete `queryset.model`.

## Verification

1. **Dependency and Caller Mapping**:
   - `django_strawberry_framework/orders/__init__.py`: verified public export of `OrderSet` and `OrderSetMetaclass`.
   - `django_strawberry_framework/types/finalizer.py`: verified phase 2.5 sidecar set binding and `_expand_orderset`.
   - `django_strawberry_framework/orders/factories.py`: verified BFS input construction via `_build_input_fields` and `OrderArgumentsFactory`.
   - `django_strawberry_framework/orders/inputs.py`: verified integration of `_field_specs`, `normalize_input_value`, and `clear_order_input_namespace`.
2. **Existing Test Suite Audit**:
   - `tests/orders/test_sets.py`: reviewed all 54 existing tests covering metaclass declaration collection, inheritance overrides, `None` tombstones, class slot defaults, `Meta.fields` list and `"__all__"` expansion, invalid path rejections, `apply_sync` / `apply_async`, permission deduplication, `_request_from_info` parsing, and to-many aggregate ordering.
3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/orders__sets/test_scratch_sets.py` verifying multiple to-many order terms with distinct indexed aliases, subclass lifecycle cache resetting via `clear_order_input_namespace()`, and sync/async permission enforcement.
   - Executed `uv run pytest docs/review/temp-tests/orders__sets/test_scratch_sets.py --no-cov`: 3 passed.
4. **Focused Test Runs**:
   - `uv run pytest tests/orders/test_sets.py --no-cov`: 57 passed.
   - `uv run pytest tests/orders/ --no-cov`: 171 passed across the ordering subsystem.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/orders/sets.py` is clean, robust, and completely satisfies spec-028 architectural requirements and `ActiveInputPermissionMixin` / `ClassBasedTypeNameMixin` contracts. The production code is defect-free. Permanent tests were added to `tests/orders/test_sets.py` pinning multiple to-many sync ordering execution, lifecycle cache clearing across subclasses, and mixin naming defaults.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/orders/test_sets.py`: added permanent unit tests covering multiple to-many order terms under `apply_sync` with database verification, lifecycle cache clearing across subclasses via `clear_order_input_namespace`, and `OrderSet.type_name_for` naming behavior.
  - Scoped diff against baseline `12779c99` for `django_strawberry_framework/orders/sets.py` is zero-edit (0 diff).
- **Permanent tests and pinned behavior:**
  - `tests/orders/test_sets.py`:
    - `test_orderset_apply_sync_annotates_multiple_to_many_orders`: pins that applying multiple to-many orderings in sync mode generates separate Min/Max aggregate annotations with distinct indexed aliases (`_dst_order_0_...`) and executes correctly against the database.
    - `test_orderset_clear_order_input_namespace_clears_subclass_caches`: pins that `clear_order_input_namespace()` clears `_expanded_fields` on both base and subclass `OrderSet` instances.
    - `test_orderset_type_name_for_inherits_mixin_naming_convention`: pins that `OrderSet.type_name_for` inherits `ClassBasedTypeNameMixin` defaulting to `<Class>InputType` for root and field contexts.
- **Scratch or focused verification:**
  - `docs/review/temp-tests/orders__sets/test_scratch_sets.py` passed (3/3 tests).
  - `uv run pytest tests/orders/test_sets.py --no-cov` passed (57/57 tests).
  - `uv run pytest tests/orders/ --no-cov` passed (171/171 tests).
- **Formatter and linter results:**
  - `uv run ruff format .` passed with 0 errors.
  - `uv run ruff check --fix .` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

- **Target production file diff:**
  - `git diff 12779c99 -- django_strawberry_framework/orders/sets.py` is zero-edit (0 diff against baseline `12779c99`).
- **Independent behavior re-tracing:**
  - **`OrderSetMetaclass`**:
    - Verified `promote_set_meta_fields` call for class `Meta.fields` normalization.
    - Verified `collect_related_declarations` with `declaration_type=RelatedOrder`, `collection_attr="related_orders"`, and `inherit_from_bases=True` correctly honoring MRO inheritance and subclass overrides.
  - **`OrderSet` Foundation & Lifecycle**:
    - Verified `_owner_definition` default (`None`), `_expanded_fields` cache default (`None`), and `_is_expanding_fields` recursion guard default (`False`), mapped via `_lifecycle = SetLifecycleAttrs(...)`.
    - Verified `_permission = ActiveInputPermissionAttrs(...)` facade mapping with `handle_top_level_list=True` and `field_specs=_field_specs`.
    - Verified `type_name_for` inherited from `ClassBasedTypeNameMixin`.
  - **Expansion and Cache Writing (`get_fields` / `_expand_meta_fields`)**:
    - Verified `get_fields` caching gated on `should_cache_expansion(cls, related_attr="related_orders", target_slot="_orderset")` which prevents caching when unresolved lazy forward references exist.
    - Verified list/tuple `Meta.fields` validation via `classify_path`, raising `ConfigurationError` on invalid paths.
    - Verified `Meta.fields = "__all__"` expansion deriving concrete column-backed field names via `_get_concrete_field_names_for_order(model)`.
  - **Apply Pipeline (`apply_sync` / `apply_async` / `_apply_orderings` / `_resolve_order_expressions`)**:
    - Verified `_request_from_info` extracting request context for permission checks.
    - Verified synchronous `apply_sync` and async `apply_async` (wrapping `_run_permission_checks` in `run_in_one_sync_boundary`) active permission enforcement before any queryset mutation.
    - Verified `_resolve_order_expressions` transforming `(field_path, direction)` into `OrderBy` expressions.
    - Verified to-many path detection via `_path_traverses_to_many(model, field_path)` generating `Min` (for ASC) or `Max` (for DESC) aggregate annotations (`_dst_order_{index}_{flatten_lookup_path(path)}`), preventing row fan-out and cursor corruption in connection pagination.
- **Findings and Improvements audit:**
  - Independently confirmed zero defects or open improvements.
- **Test execution:**
  - `uv run pytest docs/review/temp-tests/orders__sets/test_scratch_sets.py --no-cov`: 3 passed.
  - `uv run pytest tests/orders/test_sets.py --no-cov`: 57 passed.
  - `uv run pytest tests/orders/ --no-cov`: 171 passed.
  - Linters and formatting: `ruff check`, `ruff format --check`, and `check_trailing_commas.py` all passed clean with 0 errors.
- **Conclusion:** Verification complete. Status set to `verified`.

