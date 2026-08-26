# Review: `django_strawberry_framework/orders/inputs.py`

Status: verified

## Understanding

`django_strawberry_framework/orders/inputs.py` defines the ordering subsystem's input types, direction enum, input-data adapters, and module-level materialization namespace per spec-028 (Decisions 5, 8, 9, and 13).

### Key Responsibilities and Symbols:
1. **`Ordering` Enum**:
   - Direction enum decorated with `@strawberry.enum` for GraphQL schema integration.
   - Defines six members: `ASC`, `DESC`, `ASC_NULLS_FIRST`, `ASC_NULLS_LAST`, `DESC_NULLS_FIRST`, `DESC_NULLS_LAST`.
   - `is_ascending` property discriminates ascending directions based on the `ASC` name prefix.
   - `resolve(value: str) -> OrderBy` converts directions into Django `OrderBy(F(value), ...)` expressions, applying `nulls_first` / `nulls_last` sentinels or leaving them as `None` for backend defaults.
2. **Materialization Namespace & Ledger**:
   - `INPUTS_MODULE_PATH = "django_strawberry_framework.orders.inputs"`.
   - Uses `make_set_input_namespace` (`utils/inputs.py`) to manage `_materialized_names`, `_field_specs`, `_materialize_input`, and `_clear_input_namespace`.
   - `materialize_input_class(name, input_cls)` parks generated GraphQL input classes in `module.__dict__` for `strawberry.lazy` resolution.
   - `clear_order_input_namespace()` clears ledgers and lifecycle attributes across all `OrderSet` subclasses on `registry.clear()` (registered with `before_bind=True`).
3. **Field Adapters & Helpers**:
   - `_get_concrete_field_names_for_order(model)`: inspects `model._meta.get_fields()` for `Meta.fields = "__all__"` expansion, selecting column-backed concrete fields and excluding M2M managers and virtual descriptors.
   - `convert_order_field_to_input_annotation(model_field, owner_definition)`: always returns `Ordering | None` per spec-028 Decision 5.
   - `_build_input_fields(orderset_cls, owner_definition)`: maps `orderset_cls.get_fields()` into input triples via `emit_set_input_field_triples` (`utils/inputs.py`), populating `_field_specs`.
   - `normalize_input_value(orderset_cls, input_value)`: flattens top-level lists, dataclasses, and dicts into `[(field_path, direction), ...]`, validating directions against `Ordering`, skipping inactive / `None` / `UNSET` entries, and prefixing nested `RelatedOrder` paths.
   - `_ensure_field_specs(orderset_cls, input_value)`: lazily triggers `_build_input_fields` for direct mapping callers if specs are not yet populated.

## Verification

1. **Dependency and Caller Mapping**:
   - `django_strawberry_framework/orders/sets.py`: verified usage of `Ordering`, `normalize_input_value`, `_ensure_field_specs`, `_get_concrete_field_names_for_order`, and `_field_specs` in `OrderSet.get_fields`, `_normalize_input`, and `_resolve_order_expressions`.
   - `django_strawberry_framework/orders/factories.py`: verified delegation of `OrderArgumentsFactory._build_input_triples` to `_build_input_fields`.
   - `django_strawberry_framework/orders/__init__.py`: verified re-exports of `Ordering`, `INPUTS_MODULE_PATH`, `_input_type_name_for`, and integration with `order_input_type`.
   - `django_strawberry_framework/registry.py`: verified registration of `clear_order_input_namespace` via `register_subsystem_clear`.
2. **Existing Test Suite Audit**:
   - `tests/orders/test_inputs.py`: read all tests covering module path, `Ordering` enum, `materialize_input_class`, `convert_order_field_to_input_annotation`, `normalize_input_value`, `build_input_class`, `_field_specs`, `clear_order_input_namespace`, `order_input_type`, and `registry.clear()`.
   - `tests/orders/test_sets.py`: verified integration of `_get_concrete_field_names_for_order` and normalized order expressions.
3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/orders__inputs/test_scratch_inputs.py` testing `Ordering.resolve` nulls flag branches, `_get_concrete_field_names_for_order` with model and non-model inputs, 3-tier deep nested `RelatedOrder` normalization (`Book -> Shelf -> Section`), and unfinalized direct dict normalization.
   - Ran `uv run pytest docs/review/temp-tests/orders__inputs/test_scratch_inputs.py --no-cov`: 4 passed.
4. **Focused Test Runs**:
   - `uv run pytest tests/orders/test_inputs.py --no-cov`: 48 passed.
   - `uv run pytest tests/orders/ --no-cov`: 168 passed across the entire ordering subsystem.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/orders/inputs.py` is well-architected, robust, and cleanly delegates neutral traversal and namespace lifecycle operations to `django_strawberry_framework/utils/inputs.py` and `django_strawberry_framework/utils/input_values.py`. The production code is sound with zero defects found. Permanent test coverage was added in `tests/orders/test_inputs.py` to directly pin NULLS resolve variants on `Ordering`, concrete field extraction with non-model rejection, and 3-tier deep nested `RelatedOrder` normalization.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/orders/test_inputs.py`: added permanent unit tests covering `Ordering.resolve` for all `NULLS_FIRST` and `NULLS_LAST` variants, direct testing of `_get_concrete_field_names_for_order` (including non-model rejection), and 3-tier deep nested `RelatedOrder` normalization.
  - Scoped diff against baseline `12779c99` for `django_strawberry_framework/orders/inputs.py` is zero-edit (0 diff).
- **Permanent tests and pinned behavior:**
  - `tests/orders/test_inputs.py`:
    - `test_ordering_resolve_nulls_variants`: pins `nulls_first` and `nulls_last` flags on `OrderBy` for `ASC_NULLS_FIRST`, `ASC_NULLS_LAST`, `DESC_NULLS_FIRST`, and `DESC_NULLS_LAST`.
    - `test_get_concrete_field_names_for_order_direct`: pins extraction of column-backed model fields (scalars and ForeignKey `_id` columns) and rejection of non-model inputs with `ConfigurationError`.
    - `test_normalize_input_value_handles_3_tier_deep_related_order_chain`: pins recursive path prefixing across 3 tiers of `RelatedOrder` nesting (`shelf__tier3__room`).
- **Scratch or focused verification:**
  - `docs/review/temp-tests/orders__inputs/test_scratch_inputs.py` passed (4/4 tests).
  - `uv run pytest tests/orders/test_inputs.py --no-cov` passed (48/48 tests).
  - `uv run pytest tests/orders/ --no-cov` passed (168/168 tests).
- **Formatter and linter results:**
  - `uv run ruff format .` passed with 0 errors.
  - `uv run ruff check --fix .` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No.

## Independent verification (Worker 2)

- **Target production file diff:**
  - `git diff 12779c99 -- django_strawberry_framework/orders/inputs.py` is zero-edit (0 diff against baseline `12779c99`).
- **Independent behavior re-tracing:**
  - **`Ordering` Enum**: Verified all 6 enum members, `is_ascending` discriminator property based on `ASC` prefix, and `resolve()` mapping to Django `OrderBy(F(val))` with proper `nulls_first` / `nulls_last` boolean vs `None` sentinels.
  - **Input Materialization Namespace & Ledger**: Verified `INPUTS_MODULE_PATH`, `make_set_input_namespace` instantiation, `materialize_input_class` behavior (writing to module globals for `strawberry.lazy` resolution and raising on distinct-class collisions), and `clear_order_input_namespace` lifecycle hook registered with `before_bind=True` in `registry.py`.
  - **Adapters & Normalization**:
    - `_get_concrete_field_names_for_order`: Verified inspection of `model._meta.get_fields()`, exclusion of M2M managers and virtual descriptors lacking real columns, and raising `ConfigurationError` on non-model types.
    - `convert_order_field_to_input_annotation`: Verified invariant return of `Ordering | None`.
    - `_build_input_fields`: Verified delegation to `emit_set_input_field_triples`, proper lazy-reference formatting for `RelatedOrder` branches, and populating `_field_specs`.
    - `normalize_input_value`: Verified traversal using `iter_active_fields`, lazy spec building via `_ensure_field_specs`, handling of lists, dicts, dataclasses, UNSET sentinels, strict validation raising `ConfigurationError` for non-`Ordering` values, and recursive path prefixing across multi-tier `RelatedOrder` nesting.
- **Findings and Improvements audit:**
  - Independently confirmed zero defects or open improvements.
- **Test execution:**
  - `uv run pytest tests/orders/test_inputs.py --no-cov`: 48 passed.
  - `uv run pytest tests/orders/ --no-cov`: 168 passed.
  - Linters and formatting: `ruff check`, `ruff format --check`, and `check_trailing_commas.py` all passed clean with 0 errors.
- **Conclusion:** Verification complete. Status set to `verified`.
