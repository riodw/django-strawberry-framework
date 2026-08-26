# Review: `django_strawberry_framework/optimizer/nested_fetch.py`

Status: verified

## Understanding

`django_strawberry_framework/optimizer/nested_fetch.py` defines the pluggable nested-connection fetch strategy seam. It decouples strategy-independent query planning (performed by `optimizer/nested_planner.py`) from concrete fetch execution backends (`WindowedPrefetchStrategy`, `LateralPrefetchStrategy`, `AutoNestedConnectionStrategy`).

Key responsibilities and traced behaviors:
- **`unwindowable_child_queryset_reason`**: The strategy-independent safety gate called during planning and fetch-time extraction. Classifies queryset shapes that cannot be windowed safely (`sliced`, `select_for_update`, `combined`, `distinct`, `values`), falling back to unplanned per-parent execution or windowed fallback.
- **`RecognizedFetchQuerySet`**: Common base `QuerySet` subclass for `LateralQuerySet` and `SingleParentWindowQuerySet`. Implements `rebind()`, clones `_dst_spec_attr` and `_dst_window_signature`, and overrides `_fetch_all()` to execute recognized row fetching or fallback to superclass execution.
- **`NestedConnectionRequest`**: Frozen dataclass carrying complete relation, join taxonomy, ordering, slicing, probe, and keyset seek metadata. Enforces fetch-mode invariants via `assert_window_fetch_mode_for(self)`.
- **`NestedConnectionStrategy` & `StrategySelection`**: Protocol and union type accepted by `DjangoOptimizerExtension`, `OptimizerHint.strategy()`, and settings.
- **`attach_windowed_prefetch`**: Shared floor applying window pagination via `apply_window_pagination` and attaching `Prefetch(..., to_attr=request.to_attr)` to an `OptimizationPlan`.
- **`WindowedPrefetchStrategy` & `AutoNestedConnectionStrategy`**: Default and backend-neutral strategy implementations.
- **`resolve_strategy` & `active_strategy`**: Resolution from name, settings, or custom instance, with ContextVar propagation across `DjangoOptimizerExtension.on_execute()`.

## Verification

- Examined test suite `tests/optimizer/test_nested_fetch.py` (16 tests verifying plan result acceptance, windowed strategy prefetch attachment, count/probe mutual exclusion, registry immutability, strategy resolution, ContextVar lifecycle, and unwindowable reason classification).
- Examined related test suites `tests/optimizer/test_lateral_fetch.py` and `tests/optimizer/test_single_parent_fetch.py` (130 tests passing).
- Executed scratch test verifying that custom `ModelIterable` subclasses were incorrectly classified as `"values"` by `unwindowable_child_queryset_reason`.

## Improvements

### High

None.

### Medium

None.

### Low

- **Observation:** `unwindowable_child_queryset_reason` checked `getattr(queryset, "_iterable_class", ModelIterable) is not ModelIterable` using strict identity equality.
- **Evidence:** Querysets using a custom subclass of `ModelIterable` (e.g. for custom instance hydration or caching) were classified as `"values"` and excluded from windowed planning, even though they produce valid model instances that safely carry `_dst_row_number` and `_dst_total_count`.
- **Impact:** Unnecessarily prevented windowed prefetch optimization for valid custom model iterables.
- **Recommendation:** Check whether `_iterable_class` is a subclass of `ModelIterable` (`isinstance(iterable_class, type) and issubclass(iterable_class, ModelIterable)`), returning `"values"` only when it is not a `ModelIterable` subclass.
- **Proof:** `tests/optimizer/test_nested_fetch.py::test_unwindowable_child_queryset_reason_matrix` pins that `CustomModelIterable(ModelIterable)` returns `None` while `ValuesIterable` and invalid types return `"values"`.

## Summary

The strategy seam is well-designed, modular, and cleanly separates planner decisions from fetch backends. Updating `unwindowable_child_queryset_reason` to support `ModelIterable` subclasses improves extensibility without compromising safety.

## Implementation (Worker 1)

- Changed files:
  - `django_strawberry_framework/optimizer/nested_fetch.py`: Updated `unwindowable_child_queryset_reason` to check `isinstance(iterable_class, type) and issubclass(iterable_class, ModelIterable)`.
  - `tests/optimizer/test_nested_fetch.py`: Added test assertions verifying `ModelIterable` subclasses and non-type/invalid iterable classes in `test_unwindowable_child_queryset_reason_matrix`.
- Permanent tests:
  - `tests/optimizer/test_nested_fetch.py::test_unwindowable_child_queryset_reason_matrix`
- Focused verification:
  - `uv run pytest tests/optimizer/test_nested_fetch.py --no-cov` (16 passed in 1.45s)
  - `uv run pytest tests/optimizer/test_lateral_fetch.py tests/optimizer/test_single_parent_fetch.py --no-cov` (130 passed in 3.65s)
- Formatter and linter results:
  - `uv run ruff format .` (1 file reformatted, 428 left unchanged)
  - `uv run ruff check --fix .` (All checks passed)
- Rejected findings: None.
- Changelog: Does not merit a separate changelog entry (internal refinement to query classifier).

## Independent verification (Worker 2)

- Verified the complete target `django_strawberry_framework/optimizer/nested_fetch.py` and its callers across `optimizer/nested_planner.py`, `optimizer/lateral_fetch.py`, `optimizer/single_parent_fetch.py`, `optimizer/extension.py`, and `optimizer/walker.py`.
- Re-traced core behaviors:
  - `unwindowable_child_queryset_reason`: Checked classification of `sliced`, `select_for_update`, `combined`, `distinct`, and `values`. Verified that the updated check `isinstance(iterable_class, type) and issubclass(iterable_class, ModelIterable)` correctly accepts `ModelIterable` and arbitrary subclasses thereof while rejecting `ValuesIterable`, `ValuesListIterable`, `NamedValuesListIterable`, `FlatValuesListIterable`, invalid non-type objects, and unrelated types.
  - `RecognizedFetchQuerySet`: Checked `rebind()` clone mechanics, `_dst_spec_attr` setting, `_dst_window_signature` capture via `window_predicate_signature()`, and `_clone()` fidelity.
  - `NestedConnectionRequest`: Verified frozen dataclass invariants and post-init validation via `assert_window_fetch_mode_for(self)` enforcing strict mutual exclusion between count calculations and next-page probes.
  - `attach_windowed_prefetch`: Verified propagation of window pagination arguments to `apply_window_pagination`, optional wrapping via `wrap`, and unique prefetch registration into `OptimizationPlan`.
  - `WindowedPrefetchStrategy` & `AutoNestedConnectionStrategy`: Verified single parent detection wrap delegation and lateral backend delegation for auto routing.
  - Strategy resolution & contextvar isolation: Verified immutable built-in registry caching, string name and instance resolution with fail-loud validation on bad types/names, and contextvar lifecycle during `DjangoOptimizerExtension.on_execute()`.
- Verified focused test suite:
  - `uv run pytest tests/optimizer/test_nested_fetch.py tests/optimizer/test_lateral_fetch.py tests/optimizer/test_single_parent_fetch.py --no-cov` (146 passed).
  - Scratch testing confirmed behavior with additional iterable classes and probe invariants.
- No remaining defects or regressions found. All contracts and findings verified.
