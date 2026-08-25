# DRY review: `django_strawberry_framework/utils/input_values.py`

Status: verified

## System trace

`django_strawberry_framework/utils/input_values.py` implements the centralized set-input traversal substrate shared by FilterSets (`filters/sets.py`, `filters/inputs.py`), OrderSets (`orders/sets.py`, `orders/inputs.py`), and sidecar permissions (`utils/permissions.py`) ([spec-051][spec-051]).

It owns the following architectural responsibilities:

1. **Classification Kinds & Input Helpers:**
   - Constants: [`DEFAULT_SET_INPUT_TRAVERSAL_DEPTH`][utils-input-values], [`LOGIC`][utils-input-values], [`RELATED`][utils-input-values], and [`LEAF`][utils-input-values].
   - Key & error normalization: [`_field_name`][utils-input-values] and [`_walk_error`][utils-input-values].
   - Input shape inspectors: [`iter_input_items`][utils-input-values] (`django_strawberry_framework/utils/input_values.py::iter_input_items`), [`input_field_value`][utils-input-values] (`django_strawberry_framework/utils/input_values.py::input_field_value`), and [`is_inactive_value`][utils-input-values] (`django_strawberry_framework/utils/input_values.py::is_inactive_value`).

2. **Traversal Configuration & Active Field Generator:**
   - Traversal config: [`SetInputTraversal`][utils-input-values] (`django_strawberry_framework/utils/input_values.py::SetInputTraversal` with attributes `field_specs`, `related_attr`, `logic_keys`, `unset_sentinel`, `handle_top_level_list`).
   - Classified field record: [`ActiveField`][utils-input-values] (`django_strawberry_framework/utils/input_values.py::ActiveField` with attributes `python_attr`, `raw_value`, `spec`, `kind`, `related_obj`).
   - Active field iterator: [`iter_active_fields`][utils-input-values] (`django_strawberry_framework/utils/input_values.py::iter_active_fields`).

Connected behavior examined:
- [`django_strawberry_framework/filters/sets.py`][filters-sets]: FilterSet input normalization using `iter_active_fields`.
- [`django_strawberry_framework/orders/inputs.py`][orders-inputs]: OrderSet input normalization using `iter_active_fields`.
- [`django_strawberry_framework/utils/permissions.py`][utils-permissions]: Sidecar permission path checking using `iter_active_fields` and `iter_input_items`.
- [`tests/utils/`][tests-utils]: Test coverage for input traversal utilities.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/input_values.py --include-constants`):
- Parsed 1 target file, 282 lines.
- Complete inventory across all 12 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/input_values.py` unifies input traversal across dicts, dataclasses, and top-level lists. Single-siting `iter_input_items` and `is_inactive_value` guarantees that FilterSet normalizers, OrderSet normalizers, and permission walkers evaluate active values (`None` vs `strawberry.UNSET`) identically.

2. **Sync and async twins:**
   Input value traversal and field classification are synchronous CPU operations shared across sync and async execution pipelines.

3. **Derived rather than repeated knowledge:**
   `SetInputTraversal` decouples family-specific metadata (such as `related_filters` vs `related_orders` or `logic_keys`) from the underlying tree walk.

4. **Inverse and round-trip pairs:**
   `iter_input_items` and `input_field_value` provide symmetrical, safe introspection over heterogeneous input representations.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/input_values.py`][utils-input-values], [`django_strawberry_framework/utils/permissions.py`][utils-permissions], [`django_strawberry_framework/filters/sets.py`][filters-sets], [`django_strawberry_framework/orders/inputs.py`][orders-inputs];
   - Specifications: [`docs/SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md`][spec-051];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/filters/`][tests-filters], [`tests/orders/`][tests-orders];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Altering dataclass inspection or key validation across input values):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/input_values.py`][utils-input-values] ([`iter_input_items`][utils-input-values] / [`_field_name`][utils-input-values]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying the inactive sentinel definition or check):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/input_values.py`][utils-input-values] ([`is_inactive_value`][utils-input-values]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Changing field classification precedence between logic and related fields):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/input_values.py`][utils-input-values] ([`iter_active_fields`][utils-input-values]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Inlining input inspection loops in `filters/sets.py` and `orders/inputs.py`:**
   - Disproved per [spec-051][spec-051]. Inlined loops allow active-input rules (`UNSET` handling, list flattening) to drift, causing silent permission bypassing or wrong queryset compilation.

## Opportunities

None — `django_strawberry_framework/utils/input_values.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/input_values.py` exhibits zero duplicate code and complete policy consolidation across input traversal and active field classification. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/input_values.py --review docs/dry/dry-file-utils__input_values.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/input_values.py`][utils-input-values] and Worker 1's DRY review.

1. **Traversal Architecture & Input Safety:**
   - Confirmed `iter_input_items` safely handles dicts and Strawberry dataclass inputs using `__dataclass_fields__` introspection without invoking hostile descriptors.
   - Confirmed `iter_active_fields` cleanly categorizes fields into `LOGIC`, `RELATED`, and `LEAF` across all sidecar flavors.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/input_values.py --review docs/dry/dry-file-utils__input_values.md --include-constants`. 100% coverage across all 12 definitions / constants.

Confirmed: `django_strawberry_framework/utils/input_values.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-051]: ../SPECS/spec-051-finalizer_sidecar_dry-0_0_14.md

<!-- package source -->
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[utils-input-values]: ../../django_strawberry_framework/utils/input_values.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py

<!-- tests -->
[tests-filters]: ../../tests/filters/
[tests-orders]: ../../tests/orders/
[tests-utils]: ../../tests/utils/
