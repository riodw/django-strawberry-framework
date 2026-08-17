# Review: `django_strawberry_framework/filters/inputs.py`

Status: verified

## Understanding

`filters/inputs.py` owns the filter input vocabulary and conversion boundary: lookup-to-Python/GraphQL names, scalar/choice/GlobalID/CSV/list/range annotations, enum/GlobalID/range normalization, operator-bag and logical-field generation, per-filter `FieldSpec` provenance, search-prefix translation, and generated-input namespace materialization. The shared construction and lifecycle mechanics are in `utils/inputs.py`; active-value and dict/dataclass traversal is in `utils/input_values.py`.

The traced production path is `filter_input_type(...)` → finalizer phase 2.5 owner binding/orphan validation → `FilterArgumentsFactory` BFS → `_build_input_fields` / `_build_logic_fields` → `build_strawberry_input_class` and `materialize_input_class`. Runtime input follows `FilterSet._normalize_input` → `normalize_input_value` → django-filter form data → `FilterSet.apply_sync` / `apply_async`; related visibility and logical branches are re-entered through `FilterSet` in `filters/sets.py`.

I compared the target with the shared order input builder, form/mutation/write input substrates, finalizer binding, registry clear callbacks, public `filter_input_type`, and fakeshop’s live library/products/kanban GraphQL filter APIs. Existing coverage exercises lookup naming, empty/UNSET values, enums, GlobalIDs and type strategies, CSV/range/list shapes, malformed logic, lazy references, materialization collisions, cache reset, owner binding, and live HTTP filtering.

## Verification

- Reproduced the defect with a real django-filter declaration before the fix: `CharFilter(field_name="name", lookup_expr="icontains")` generated the `custom` input field but `_normalize_input({"custom": {"i_contains": "foo"}})` returned `{"custom__icontains": "foo"}`; django-filter registers the declared field under `custom`, so that unknown key is silently ignored.
- Re-ran the same runtime reproduction after the fix; normalization returned `{"custom": "foo"}`.
- Existing tests examined: `tests/filters/test_inputs.py`, `tests/filters/test_sets.py`, `tests/filters/test_factories.py`, `tests/filters/test_finalizer.py`, `tests/filters/test_base.py`, `tests/utils/test_inputs.py`, `tests/utils/test_input_values.py`, and live `examples/fakeshop/test_query/test_library_api.py`.
- Ran `uv run ruff format .` and `uv run ruff check --fix .`; both passed.
- Ran `uv run python -m compileall -q django_strawberry_framework/filters/inputs.py django_strawberry_framework/filters/sets.py tests/filters/test_inputs.py`; passed.
- Per repository rule, pytest was not run after edits. A later fresh Django setup was also blocked by unrelated concurrent dirty work in `django_strawberry_framework/forms/sets.py` (`register_subsystem_clear` is currently undefined); that file was not changed or reverted.

## Improvements

### High

#### Declared non-exact filters were normalized under an unknown form key

- **Observation:** `_build_input_fields` preserved a declared filter’s class-attribute name as its source path, but `FilterSet._normalize_input` appended `__<lookup>` for every non-`exact` operator. A declaration such as `custom = CharFilter(field_name="name", lookup_expr="icontains")` therefore generated a valid-looking GraphQL input while submitting `custom__icontains`, which django-filter does not own.
- **Evidence:** The focused runtime reproduction above showed the bad `{"custom__icontains": "foo"}` output. The existing declared `name__exact` regression covered only the exact/suffixed special case and did not cover a normal declared non-exact attribute.
- **Impact:** The filter silently applies nothing, widening results and violating the public filter contract. This is especially dangerous when a consumer relies on a declared filter as a scope or validation boundary.
- **Recommendation:** At the `FilterSet._normalize_input` owner, detect a `base_path` present in `declared_filters` and use that declared form key for every lookup; retain generated-filter suffixing for auto-generated fields.
- **Proof:** `tests/filters/test_inputs.py::test_declared_non_exact_filter_keeps_its_form_key` now asserts the generated input normalizes to `{"custom": "alpha"}`.

### Medium

None.

### Low

None.

## Implementation (Worker 1)

- Updated `django_strawberry_framework/filters/sets.py::FilterSet._normalize_input` so declared operator-bag fields use their declared django-filter form key for all lookup expressions.
- Added `tests/filters/test_inputs.py::test_declared_non_exact_filter_keeps_its_form_key`.
- Preserved all unrelated dirty work and left the review-plan checkbox untouched.

## Summary

The target’s converter, normalization, builder, materialization, lifecycle, shared substrate, sibling surfaces, and live GraphQL integration are otherwise coherent and covered. One silent correctness defect in declared non-exact filter normalization was fixed at the owning normalizer with permanent regression coverage; formatting, lint, and syntax validation pass, while pytest remains intentionally unrun and a concurrent forms-module error blocks broader runtime validation.

## Independent verification (Worker 2)

- Re-traced the dispatch-baseline delta at `a4344a3e4873beb5d45708623b5d843aaef3790e`: before the fix, every non-`exact` operator bag selected `<base_path>__<lookup>`; the current `FilterSet._normalize_input` selects the literal `declared_filters` key when the source path is declared and retains the generated suffix rule otherwise.
- Confirmed the complete declared path with a real fakeshop Django setup: `CharFilter(field_name="name", lookup_expr="icontains")` declared as `custom_key` normalizes to `{"custom_key": "alpha"}`, its bound django-filter form exposes `custom_key`, validates, and produces the expected `LIKE` predicate. A generated `Meta.fields = {"name": ["icontains"]}` filter remains `{"name__icontains": "alpha"}` and produces the same predicate under its generated form key.
- Confirmed `None`, `{}`, and non-walkable input return `{}`; unknown operator-bag keys retain the existing passthrough behavior (`{"unknown": {"i_contains": "x"}}` becomes `{"unknown__icontains": "x"}`). `None`/`UNSET` inner bag values are skipped by the existing focused coverage.
- Confirmed both `FilterSet.apply_sync` and `FilterSet.apply_async` traverse the shared normalizer and emit filtered SQL for the generated exact field. Focused executable coverage (run before this documentation-only edit) passed 8 tests: the declared non-exact and suffix-named declared regressions, generated lookup naming, empty/`None`/`UNSET` handling, unknown lookup passthrough, and async apply.
- The permanent regression uses the actual `FilterSet`, django-filter `CharFilter`, example `Category` model, input builder, and `_normalize_input` contract; the live form probe additionally verified that the normalized declared key is consumed rather than merely asserted as a string. Django setup was not blocked in this checkout. The unrelated `forms/sets.py` work was left untouched and was not treated as filters behavior.
- No additional correctness, contract, call-site, or test-placement defect remains. The revision is verified.
