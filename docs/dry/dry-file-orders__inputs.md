# DRY review: `django_strawberry_framework/orders/inputs.py`

Status: verified

## System trace

Owns order-input materialization for spec-028 Decision 9: the public
`Ordering` direction enum (`resolve` → Django `OrderBy`),
`INPUTS_MODULE_PATH`, the per-(orderset, attr) provenance ledger
(`_field_specs`), the Decision-9 materialization ledger
(`_materialized_names`), the order-family adapters
(`convert_order_field_to_input_annotation` / `_build_input_fields` /
`normalize_input_value`), the `Meta.fields = "__all__"` column walk
(`_get_concrete_field_names_for_order`), and the family wrappers
(`materialize_input_class` / `clear_order_input_namespace`) registered into
`registry.clear()` via `register_subsystem_clear` (owner
`orders.input_namespace`, `before_bind=True`).

Shared generated-input mechanics already live in
`utils/inputs.py` (`GeneratedInputFieldSpec`, `build_strawberry_input_class`,
`emit_set_input_field_triples`, `materialize_generated_input_class`,
`clear_generated_input_namespace`, `iter_set_subclasses`) and
`utils/input_values.py` (`SetInputTraversal` / `iter_active_fields` with
`handle_top_level_list=True`). This module keeps order-domain semantics and
re-exports the substrate under spec-named aliases (`FieldSpec` /
`build_input_class` / `_camel_case` / `_iter_orderset_subclasses`).

Callers: `orders/factories.py` (BFS build → `_build_input_fields`),
`orders/sets.py` (`_expand_meta_fields` / `_normalize_input` /
`Ordering.resolve` apply path), `orders/__init__.py`
(`order_input_type` / `INPUTS_MODULE_PATH` / `_input_type_name_for`; separate
`_helper_referenced_ordersets` clear under owner `orders.helper_references`),
`types/finalizer.py` (`materialize_input_class` during phase 2.5). Live
GraphQL coverage for direction / NULLS_* ordering already exists under
`examples/fakeshop/test_query/test_library_api.py`. Sibling
`filters/inputs.py` mirrors the family wrapper shape; shared mechanics are
already single-sited — remaining filter/order differences (fixed
`Ordering | None` leaves, no operator bag / logic keys / `HIDE_FLAT_FILTERS`,
top-level list flatten) are intentional and belong to folder / project
passes.

## Verification

- Baseline diff for the target at `ITEM_BASELINE`
  (`b368091919059a8ac05106823a9684b506793f62`) was empty; work started from
  HEAD.
- Compared `filters/inputs.py`, `utils/inputs.py`, `utils/input_values.py`,
  `sets_mixins.py` (`ClassBasedTypeNameMixin`), `mutations/inputs.py`
  (`editable_input_fields`), `orders/__init__.py` /
  `registry.py::register_subsystem_clear`, and the order test /
  live-query surfaces.
- Confirmed stale future-tense Slice-3 / local-import prose in this file:
  module docstring, `_materialized_names` comment, and
  `clear_order_input_namespace` still described `registry.clear()` as
  about-to-wire local-import blocks, while both clears already register via
  `register_subsystem_clear` (matching the already-corrected
  `orders/__init__.py` wording).
- Disproved consolidating `_get_concrete_field_names_for_order` with
  `mutations/inputs.py::editable_input_fields`: opposite selection (order
  includes column-backed fields and excludes M2M; writes exclude
  non-editable / PK and include forward M2M). Documented as counterparts,
  not duplicates.
- Disproved promoting `_get_concrete_field_names_for_order` into
  `sets_mixins.get_concrete_field_names` today: only one consumer
  (`OrderSet._expand_meta_fields`); `sets_mixins` intentionally deferred
  cookbook helpers until a second set family needs them. Folder / future
  aggregates.
- Disproved folding family wrappers into `make_input_namespace`: that
  helper is the light ledger-only clear for write flavors; orders need the
  heavy `clear_generated_input_namespace` (factory caches +
  `_lifecycle` binding attrs).
- Disproved further collapsing the filters/orders `_build_input_fields` /
  `normalize_input_value` / thin materialize-clear mirrors: emission and
  traversal scaffolds are already in `utils/`; remaining bodies are
  family semantics (Decision 5 leaves, related prefix recurse, no logic
  bag). Folder / project.
- Disproved inlining `convert_order_field_to_input_annotation`: unused
  args are reserved for forward-compat and shape-symmetry with the filter
  converter; collapsing would erase that extension seam for a one-liner.

## Opportunities

### 1. Stale Slice-3 / local-import lifecycle prose

- **Repeated responsibility:** How `registry.clear()` tears down the order
  input namespace vs the helper orphan ledger.
- **Sites:** Module docstring; `_materialized_names` comment;
  `clear_order_input_namespace` docstring (future-tense Slice-3 /
  "TWO separate steps" wording that implied inlined `TypeRegistry.clear`
  blocks).
- **Evidence:** `orders/__init__.py` already registers
  `_clear_helper_referenced_ordersets` under `orders.helper_references`
  and documents that the local-import-inside-`TypeRegistry.clear` shape
  predates the registration seam; this file still described Slice 3 as
  pending.
- **Owner:** `orders/inputs.py` (docstrings / comments only).
- **Consolidation:** Rewrite to present-tense `register_subsystem_clear`
  ownership (`orders.input_namespace` vs `orders.helper_references`); drop
  Slice-3 future tense and the implied local-import clear path.
- **Proof:** Source inspection of both registration rows; no behavioral
  change — existing `tests/orders/test_inputs.py` /
  `tests/test_registry.py` clear lifecycle coverage remains the permanent
  guard.
- **Risks / non-goals:** Do not merge the two clears into one callback
  (Decision 9 keeps orphan-tracking and namespace state separate). Do not
  edit concurrent dirty paths (`orders/sets.py`, plan checkboxes, other
  workers' artifacts).

## Judgment

Order-input mechanics are already single-sited in `utils/inputs.py` /
`utils/input_values.py`. This file correctly owns order-family semantics
(`Ordering`, leaf annotation, related-path normalize, `__all__` column
walk, Decision-9 ledgers). The only warranted change in this pass is
correcting stale Slice-3 / local-import documentation so the lifecycle
prose matches the shipped registration seam. Cross-family filter/order
mirror leftovers stay at folder / project.

## Implementation (Worker 1)

- **Owner chosen:** `orders/inputs.py` documentation (module docstring,
  `_materialized_names` comment, `clear_order_input_namespace` docstring).
- **Migrated:** Future-tense Slice-3 / local-import clear wording →
  present-tense dual `register_subsystem_clear` ownership.
- **Behavior kept separate:** No code path changes; helper ledger remains
  outside `clear_order_input_namespace`; family wrappers stay thin pins
  over the shared substrate.
- **Validation:** `uv run ruff format` + `uv run ruff check --fix` on the
  target (clean). No full pytest (per worker charter). No new permanent
  tests (docstring-only). Changelog: no — docs-only accuracy fix.
- **Rejected / deferred (strongest):**
  1. Collapse filters/orders input mirrors further → folder/project
     (substrate already shared).
  2. Promote `_get_concrete_field_names_for_order` to `sets_mixins` →
     defer until a second set-family consumer.
  3. Unify with `editable_input_fields` → disproved (opposite selection).
  4. Out-of-scope stale prose in `tests/orders/test_inputs.py` module
     docstring ("Slice 2 / Slice 3 land their tests…") and
     `tests/test_registry.py` cycle-safe local-import wording — not this
     file; leave for their owning reviews.
- **Ready for Worker 2:** yes.

## Independent verification (Worker 2)

Re-traced from the complete `orders/inputs.py`, item-scoped diff vs
`b368091919059a8ac05106823a9684b506793f62`,
`orders/__init__.py` helper ledger + registration,
`registry.py::register_subsystem_clear` / `iter_subsystem_clears` /
`TypeRegistry.clear`, `types/finalizer.py` `iter_subsystem_clears(before_bind=True)`,
sibling `filters/inputs.py` wrappers, `mutations/inputs.py::editable_input_fields`,
`utils/inputs.py::make_input_namespace` / `clear_generated_input_namespace`, and
`sets_mixins.py` deferred-cookbook note.

**Diff scope.** Item-scoped diff is docstring / comment only (module docstring,
`_materialized_names` comment, `clear_order_input_namespace` docstring). No
executable path changed.

**Pre-bind overclaim — absent (filters / orders `__init__` lesson applied).**
Registration at module bottom is:

```python
register_subsystem_clear(
    clear_order_input_namespace,
    owner="orders.input_namespace",
    before_bind=True,
)
```

Module docstring attributes `before_bind=True` only to that row. Helper ledger
prose names owner `orders.helper_references` and dual
`register_subsystem_clear` replay on `registry.clear()`; it does **not** claim
`before_bind` for the helper (which registers with default `False` and is
skipped by finalizer `iter_subsystem_clears(before_bind=True)`).
`_materialized_names` / `clear_order_input_namespace` comments correctly say
`registry.clear()` replays via `register_subsystem_clear` without inventing a
pre-bind drain for the orphan ledger. `TypeRegistry.clear` →
`iter_subsystem_clears()` (default) runs every registered callback, so "two
independent callbacks" is accurate.

**Rejected candidates — upheld.**
1. Further filters/orders `_build_input_fields` / `normalize_input_value` /
   materialize-clear collapse → substrate already in `utils/`; remaining
   bodies are Decision-5 / no-logic-bag family semantics.
2. Promote `_get_concrete_field_names_for_order` into `sets_mixins` → single
   consumer (`OrderSet._expand_meta_fields`); mixin docs still defer cookbook
   helpers until a second family needs them.
3. Unify with `editable_input_fields` → opposite selection (order includes
   column-backed / excludes M2M; writes exclude non-editable+PK / include
   forward M2M); documented counterparts, not duplicates.
4. Fold wrappers into `make_input_namespace` → that helper is the light
   ledger-only clear; orders need heavy `clear_generated_input_namespace`
   (factory caches + `_lifecycle` binding attrs).
5. Inline `convert_order_field_to_input_annotation` → unused args are the
   filter-converter shape-symmetry / forward-compat seam.

**Missed consolidations owned by this file — none.** Similar
`hasattr(..., "column") and not many_to_many` elsewhere (`permissions.py`)
serves a different contract. Out-of-scope stale Slice prose in
`tests/orders/test_inputs.py` / `tests/test_registry.py` remains for their
owning reviews (Worker 1 already deferred).

**Disposition:** verified; plan item checked.
