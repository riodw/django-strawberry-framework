# Review: `django_strawberry_framework/sets_mixins.py`

Status: verified

## Understanding

`django_strawberry_framework/sets_mixins.py` is the root neutral foundation for lifecycle, lazy relation resolution, schema naming, and input permission machinery shared across set families (`FilterSet`, `OrderSet`, and future `AggregateSet` / `FieldSet`).

It owns 8 symbols exported in `__all__`:
1. **`ClassBasedTypeNameMixin`**:
   - Generates consistent GraphQL schema type names via `type_name_for(field_path=None)`.
   - Uses `pascal_case_or_raise` to validate and PascalCase field paths, appending `_field_type_suffix` (e.g. `FooFilter` + `category` -> `FooFilterCategoryFilterInputType`) or `_root_type_suffix` for top-level set inputs.
2. **`LazyRelatedClassMixin`**:
   - Implements `resolve_lazy_class(class_ref, bound_class)` to break circular import dependencies.
   - Resolves absolute dotted string import paths, relative / unqualified class names evaluated against `bound_class.__module__`, or 0-argument factory callables (`lambda: TargetSet`).
3. **`RelatedSetTargetMixin`**:
   - Subclasses `LazyRelatedClassMixin` to provide the shared target binding and resolution engine for `RelatedFilter` and `RelatedOrder`.
   - Implements idempotent `_bind_owner(owner)` ensuring metaclass re-binds on subclass creation never clobber explicit overrides.
   - Implements `_resolved_target()` with automatic caching on the instance, and `_set_target(value)` for dynamic substitution.
4. **`collect_related_declarations`**:
   - Metaclass helper building an `OrderedDict` of related set declarations (`RelatedFilter` / `RelatedOrder`).
   - Supports both explicit base inheritance (`inherit_from_bases=True` on `OrderSet`) and django-filter-managed declarations (`inherit_from_bases=False` on `FilterSet`).
   - Correctly resolves diamond inheritance hierarchies and attribute shadowing, stripping declarations overridden by class-body non-declarations or tombstones in earlier bases.
   - Automatically binds `new_class` as the owner on each collected declaration.
5. **`expanded_once`**:
   - Reentry-guarded class-level cache driver.
   - Inspects `cls.__dict__[cache_attr]` directly (bypassing `getattr` so subclasses never inherit a parent class's completed cache via MRO).
   - Manages `guard_attr` within a `try ... finally` block, supporting `on_reentry()` fallback callbacks for self-referential / circular relation graphs.
6. **`should_cache_expansion`**:
   - Gate verifying that `related_attr` exists directly in `cls.__dict__` and all targets are resolved classes (no unresolved string forward references remain) before caching expansion results.
7. **`SetLifecycleAttrs`**:
   - Frozen dataclass storing the binding attribute names `(owner, cache, guard, *extra)` used by `utils/inputs.py::clear_generated_input_namespace` on `registry.clear()`.
8. **`ActiveInputPermissionAttrs` & `ActiveInputPermissionMixin`**:
   - Decision 8 permission facade single-siting the active-input permission protocol across `FilterSet` and `OrderSet`.
   - Delegates to `utils/permissions.py` helpers (`request_from_info`, `extract_branch_value`, `active_related_branches`, `invoke_permission_method`, `active_permission_targets`, `run_active_input_permission_checks`), parameterized by each family's `_permission` configuration.

## Verification

1. Traced callers, dependencies, and integration seams:
   - `django_strawberry_framework/filters/sets.py`: inherits `ClassBasedTypeNameMixin`, `ActiveInputPermissionMixin`, calls `collect_related_declarations`, `expanded_once`, `should_cache_expansion`, and registers `SetLifecycleAttrs`.
   - `django_strawberry_framework/filters/base.py`: `RelatedFilter` inherits `RelatedSetTargetMixin` and delegates `.filterset` resolution.
   - `django_strawberry_framework/orders/sets.py`: inherits `ClassBasedTypeNameMixin`, `ActiveInputPermissionMixin`, calls `collect_related_declarations`, `expanded_once`, `should_cache_expansion`, and registers `SetLifecycleAttrs`.
   - `django_strawberry_framework/orders/base.py`: `RelatedOrder` inherits `RelatedSetTargetMixin` and delegates `.orderset` resolution.
   - `django_strawberry_framework/utils/permissions.py`: provides underlying permission traversal and invocation mechanics consumed by `ActiveInputPermissionMixin`.
   - `django_strawberry_framework/utils/inputs.py`: consumes `SetLifecycleAttrs.binding_attrs` to clean up class-level state on `registry.clear()`.
2. Examined test suites:
   - `tests/test_sets_mixins.py`: verified unit tests for all exports, mixins, lifecycle descriptors, and hook interfaces.
   - `tests/orders/test_base.py` & `tests/orders/test_composition.py`: verified `RelatedOrder` lazy target resolution, owner binding, and composition with `FilterSet`.
3. Scratch experiments (`docs/review/temp-tests/sets_mixins/test_scratch_sets_mixins.py`):
   - Probed `collect_related_declarations` with multi-level diamond inheritance and base precedence.
   - Probed `LazyRelatedClassMixin` with zero-arg callables, class objects, and non-class values.
   - Probed `RelatedSetTargetMixin` with custom slots, idempotency of `_bind_owner`, and setter overrides.
   - Probed `expanded_once` error handling verifying `finally` guard cleanup.
   - 5/5 passed (`uv run pytest docs/review/temp-tests/sets_mixins/test_scratch_sets_mixins.py --no-cov`).
4. Focused test executions:
   - `uv run pytest tests/test_sets_mixins.py --no-cov`: 18 passed.
   - `uv run pytest tests/test_sets_mixins.py tests/orders/test_base.py tests/orders/test_composition.py --no-cov`: 33 passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/sets_mixins.py` provides a clean, well-factored, cycle-safe foundation for filter and order set lifecycles. All 8 exported components are strictly isolated, robust against diamond inheritance and recursive expansion, and adhere to package invariants. Permanent tests have been expanded in `tests/test_sets_mixins.py` to pin exception guard cleanup, lazy resolution fallbacks, diamond tombstone shadowing, and active permission facade delegations.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/test_sets_mixins.py`: added 4 permanent behavioral test functions (`test_lazy_related_class_mixin_fallback_and_non_class_types`, `test_expanded_once_resets_guard_on_exception`, `test_active_input_permission_mixin_delegates_and_fires_checks`, `test_collect_related_declarations_diamond_tombstone`).
- **Permanent tests and pinned behavior:**
  - `tests/test_sets_mixins.py` (18 tests total):
    - Pins `ClassBasedTypeNameMixin` root and field-path pascal-case formatting and invalid character rejection.
    - Pins `LazyRelatedClassMixin` absolute import, relative import against `bound_class`, callable factory, non-string value passthrough, and failed import exception bubbling.
    - Pins `RelatedSetTargetMixin` idempotent owner binding, cached lazy target resolution, and target setter.
    - Pins `collect_related_declarations` base inheritance, direct-base precedence, diamond hierarchy tombstone resolution, and automatic owner binding.
    - Pins `expanded_once` cache retrieval, reentry callback execution, and `finally` guard clearing on exception.
    - Pins `should_cache_expansion` gating on own `__dict__` attribute ownership and non-string target types.
    - Pins `SetLifecycleAttrs` dataclass fields and `binding_attrs` property.
    - Pins `ActiveInputPermissionMixin` method delegations (`_request_from_info`, `_extract_branch_value`, `_permission_fallback_path`, `_run_permission_checks`).
- **Scratch verification:**
  - `docs/review/temp-tests/sets_mixins/test_scratch_sets_mixins.py` passed (5/5 tests).
  - `uv run pytest tests/test_sets_mixins.py --no-cov` passed (18/18 tests).
  - `uv run pytest tests/test_sets_mixins.py tests/orders/test_base.py tests/orders/test_composition.py --no-cov` passed (33/33 tests).
- **Formatter and linter results:**
  - `uv run ruff format .` passed with 0 errors.
  - `uv run ruff check --fix .` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

- **Behaviors and paths traced:**
  - `ClassBasedTypeNameMixin`: Verified root naming (`cls.__name__` + `_root_type_suffix`) and field-path pascal-cased naming (`_field_type_suffix`). Verified input validation rejection via `pascal_case_or_raise` for non-word / blank inputs.
  - `LazyRelatedClassMixin`: Verified direct class resolution, zero-argument factory callable invocation, absolute dotted string imports, bound-class module-relative imports, and failed import exception bubbling.
  - `RelatedSetTargetMixin`: Verified single-owner binding idempotency, cached lazy resolution into instance slot, and target override setter.
  - `collect_related_declarations`: Traced base declaration collection, direct class item overrides, diamond inheritance base precedence, tombstone shadowing across ancestor MRO, and automatic owner binding.
  - `expanded_once`: Traced own-`__dict__` cache isolation (preventing subclass cache leakage), reentry-guard fallback invocation, and exception cleanup in `finally` block.
  - `should_cache_expansion`: Traced gate requiring own `__dict__` declaration ownership and non-string resolved targets.
  - `SetLifecycleAttrs`: Traced dataclass fields and `binding_attrs` tuple consumed by `utils/inputs.py::clear_generated_input_namespace`.
  - `ActiveInputPermissionMixin`: Traced delegation to `utils/permissions.py` helpers, active-field traversal, inactive value short-circuiting, and permission hook interfaces.
- **Independent scratch tests:**
  - Created and executed `docs/review/temp-tests/sets_mixins/test_scratch_worker2.py` (6 tests). Probed custom type name suffixes, subclass cache inheritance isolation in `expanded_once`, comprehensive resolution matrix in `LazyRelatedClassMixin`, owner-bind idempotency and target cache in `RelatedSetTargetMixin`, multi-level diamond tombstone shadowing in `collect_related_declarations`, and inactive vs active check execution in `ActiveInputPermissionMixin`. All 6/6 scratch tests passed.
- **Test execution:**
  - `uv run pytest tests/test_sets_mixins.py --no-cov`: 18/18 passed.
  - `uv run pytest tests/orders/test_base.py tests/orders/test_composition.py tests/orders/test_sets.py tests/filters/test_sets.py --no-cov`: 361/361 passed.
  - `uv run pytest docs/review/temp-tests/sets_mixins/test_scratch_worker2.py --no-cov`: 6/6 passed.
- **Findings disposition:** All 8 exports are robust, correctly factored, and covered by strong permanent unit tests. No defects or regressions found.

