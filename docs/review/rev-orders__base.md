# Review: `django_strawberry_framework/orders/base.py`

Status: verified

## Understanding

`django_strawberry_framework/orders/base.py` is the foundational primitive layer of the ordering subsystem (Layer 1 of spec-028). It owns the nested-path ordering primitive `RelatedOrder`.

### Key Responsibilities and Symbols:
1. **`RelatedOrder`**:
   - Single-symbol consumer-facing class enabling nested-relation ordering across `OrderSet`s (spec-028 Decision 2).
   - Inherits from `RelatedSetTargetMixin` (from `django_strawberry_framework.sets_mixins`), configuring `_target_attr = "_orderset"` and `_owner_attr = "bound_orderset"`.
   - Constructor `__init__(orderset: str | type, field_name: str | None = None)` accepts an `OrderSet` class, an absolute import string path, an unqualified class name string (resolved relative to `bound_orderset.__module__`), or a callable factory. `field_name` is optional (defaults to `None`) for ergonomic collection mutation.
   - `bind_orderset(orderset)`: Idempotent owner binding delegating to `_bind_owner`.
   - `orderset` property / setter: Lazily resolves string / callable targets on first access via `_resolved_target` / `LazyRelatedClassMixin.resolve_lazy_class`, caching the resolved class back into `_orderset`. Setter delegates to `_set_target`.
   - Free of operator bags, lookup expressions, and form validation machinery per spec-028 Decision 8.

## Verification

1. **Dependency and Caller Mapping**:
   - `django_strawberry_framework/orders/__init__.py`: verified public re-export in `__all__`.
   - `django_strawberry_framework/orders/sets.py`: verified metaclass collection via `collect_related_declarations(..., declaration_type=RelatedOrder, collection_attr="related_orders")` and nested traversal during `OrderSet.get_fields()`.
   - `django_strawberry_framework/orders/factories.py`: verified `OrderArgumentsFactory` inspection of `related_order.orderset` to build `LazyType` fields.
   - `django_strawberry_framework/orders/inputs.py`: verified `normalize_input_value` traversal through `related_order.orderset`.
   - `django_strawberry_framework/types/finalizer.py`: verified `_expand_orderset` accessing `related.orderset` for early Layer-2 lazy resolution error surfacing.
2. **Existing Test Suite Audit**:
   - `tests/orders/test_base.py`: read existing tests verifying class reference, absolute import path, unqualified name resolution, unresolvable import error, `bind_orderset` idempotency, mixin provenance from `sets_mixins`, and `orderset` property setter.
3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/orders__base/test_scratch_orders__base.py` verifying callable factory target resolution with single-invocation caching, default `field_name=None`, unbound unqualified string error propagation, and unbound absolute import path resolution.
   - Ran `uv run pytest docs/review/temp-tests/orders__base/test_scratch_orders__base.py --no-cov`: 4 passed.
4. **Focused Test Runs**:
   - `uv run pytest tests/orders/test_base.py --no-cov`: 16 passed.
   - `uv run pytest tests/orders/ --no-cov`: 161 passed across the ordering subsystem.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/orders/base.py` is clean, robust, and completely adheres to spec-028 architecture and `RelatedSetTargetMixin` contracts. Permanent edge-case coverage was added in `tests/orders/test_base.py` pinning callable factory memoization, default `field_name` optionality, and unbound absolute import path resolution.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/orders/test_base.py`: added permanent tests pinning callable target factory resolution & memoization, default `field_name=None`, and unbound absolute import path resolution.
  - Scoped source diff for `django_strawberry_framework/orders/base.py` against cycle baseline (`12779c99`): 0 diff (zero-edit on production target).
- **Permanent tests and pinned behavior:**
  - `tests/orders/test_base.py` (16 tests total):
    - `test_related_order_accepts_class_reference`: pins direct class target passing.
    - `test_related_order_accepts_absolute_import_path_string`: pins absolute import resolution.
    - `test_related_order_accepts_unqualified_name_in_same_module`: pins unqualified name fallback against owner module.
    - `test_related_order_unresolved_target_raises_importerror_through_lazy_mixin`: pins raw `ImportError` propagation.
    - `test_related_order_bind_orderset_is_idempotent`: pins owner binding idempotency.
    - `test_related_order_imports_lazy_mixin_from_sets_mixins_not_filters_base`: pins decoupling of orders from filters.
    - `test_meta_orderset_class_is_in_allowed_meta_keys`: pins `orderset_class` in `ALLOWED_META_KEYS`.
    - `test_meta_orderset_class_is_not_in_deferred_meta_keys`: pins promotion out of `DEFERRED_META_KEYS`.
    - `test_validate_orderset_class_returns_none_for_missing_value`: pins validator omission handling.
    - `test_validate_orderset_class_accepts_order_set_subclass`: pins validator acceptance of `OrderSet` subclass.
    - `test_validate_orderset_class_rejects_non_order_set`: pins validator rejection of non-`OrderSet`.
    - `test_validate_orderset_class_uses_local_import`: pins cycle avoidance via local import.
    - `test_related_order_orderset_setter_assigns_underscore_orderset`: pins setter write-through to `_orderset`.
    - `test_related_order_accepts_callable_factory`: pins zero-arg callable target factory resolution and single-invocation caching.
    - `test_related_order_default_field_name_is_none`: pins optional `field_name` defaulting to `None`.
    - `test_related_order_unbound_absolute_import_path_resolves`: pins absolute path resolution without requiring `bound_orderset`.
- **Scratch verification:**
  - `docs/review/temp-tests/orders__base/test_scratch_orders__base.py` passed (4/4 tests).
  - `uv run pytest tests/orders/test_base.py --no-cov` passed (16/16 tests).
  - `uv run pytest tests/orders/ --no-cov` passed (161/161 tests).
- **Formatter and linter results:**
  - `uv run ruff format .` passed with 0 errors.
  - `uv run ruff check --fix .` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

- **Scoped baseline verification:**
  - Confirmed `git diff 12779c99 -- django_strawberry_framework/orders/base.py` is zero-edit (0 diff).
- **Behaviors and paths traced:**
  - `RelatedOrder`: Verified clean inheritance from `RelatedSetTargetMixin` with `_target_attr = "_orderset"` and `_owner_attr = "bound_orderset"`.
  - Lazy Resolution Contract: Traced lazy target resolution for class reference, absolute import path string, unqualified class name string relative to `bound_orderset.__module__`, and callable zero-arg factory with caching back to `_orderset`.
  - Property Getter & Setter: Traced `orderset.fget` resolving and caching the target class, and `orderset.fset` delegating to `_set_target` to allow target override.
  - Owner Binding: Traced `bind_orderset` idempotent binding delegating to `_bind_owner`.
  - Decoupling from Filters: Verified `RelatedOrder` imports `RelatedSetTargetMixin` from `sets_mixins` without touching the filter subsystem.
- **Independent scratch tests:**
  - Created and executed `docs/review/temp-tests/orders__base/test_scratch_worker2.py` (5 tests) verifying mixin parameterization, property setter reassignments, `field_name` mutation, binding idempotency across distinct target sets, and `ImportError` propagation for unresolvable attributes in existing modules.
  - Executed `docs/review/temp-tests/orders__base/test_scratch_orders__base.py` (4 tests).
- **Test execution:**
  - `uv run pytest tests/orders/test_base.py docs/review/temp-tests/orders__base/test_scratch_orders__base.py docs/review/temp-tests/orders__base/test_scratch_worker2.py --no-cov`: 25/25 passed.
  - `uv run pytest tests/orders/ --no-cov`: 161/161 passed.
- **Findings disposition:**
  - `django_strawberry_framework/orders/base.py` is clean, robust, and completely satisfies spec-028 design requirements and `RelatedSetTargetMixin` integration contracts. No defects found.
