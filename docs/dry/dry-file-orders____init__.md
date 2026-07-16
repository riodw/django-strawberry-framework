# DRY review: `django_strawberry_framework/orders/__init__.py`

Status: verified

## System trace

`orders/__init__.py` is the consumer entry point for the ordering
subsystem. It owns three responsibilities:

1. **Public re-export surface** — `RelatedOrder` from `orders/base.py`,
   `OrderSet` / `OrderSetMetaclass` from `sets.py`, `Ordering` from
   `inputs.py`, and the Decision-11 helper `order_input_type`.
   `OrderArgumentsFactory` is intentionally absent (advanced consumers
   import `orders.factories` directly). `INPUTS_MODULE_PATH` and
   `_input_type_name_for` stay module-scoped but out of `__all__`,
   mirroring `filters/__init__.py`.
2. **Decision-11 helper** — `order_input_type(orderset_class)` validates
   eagerly, records the class on `_helper_referenced_ordersets`, and
   returns the Strawberry
   `Annotated[<Name>OrderInputType, strawberry.lazy(...)]` forward-ref
   (element type; consumers wrap as `list[...] | None`). Body already
   delegates to `utils/inputs.py::build_lazy_input_annotation`
   (0.0.9 DRY pass).
3. **Helper-ledger lifecycle** — `_helper_referenced_ordersets` lives
   co-located with its only writer (`order_input_type`);
   `_clear_helper_referenced_ordersets` registers via
   `registry.py::register_subsystem_clear(owner="orders.helper_references")`
   with default `before_bind=False`. Finalizer phase 2.5
   (`types/finalizer.py::_bind_ordersets`) reads the ledger for orphan
   checks against `Meta.orderset_class`; `connection.py` calls
   `order_input_type` when synthesizing connection `orderBy:` args so
   orphans stay ledgered. Namespace drain
   (`clear_order_input_namespace`, `before_bind=True`) lives in
   `orders/inputs.py` — a separate registered row, not this file.

Consumers: fakeshop / package tests use `OrderSet` / `Ordering` /
`order_input_type`; finalizer / connection / tests reach the private
ledger for orphan and clear contracts. Sibling `filters/__init__.py`
mirrors the helper + ledger + clear shape with `FilterSet` /
`filter_input_type` / `_helper_referenced_filtersets`.

## Verification

- Item-scoped diff vs `8980ca5f06b1c60b4e575cba5f14c137a2877c07` was
  empty before this pass; only the docstring / ledger-comment edits
  below change.
- Compared `order_input_type` to `filters/__init__.py::filter_input_type`:
  both are thin wrappers over the same
  `build_lazy_input_annotation` owner with family-specific
  `expected_base` / `family_name` / `expected_label` / `ledger` /
  `input_type_name_for` / `module_path`. No residual duplicated helper
  body remains in this file.
- Traced ledger readers/writers: only `order_input_type` adds;
  `_clear_helper_referenced_ordersets` + `register_subsystem_clear` own
  teardown; `types/finalizer.py` imports `_helper_referenced_ordersets`
  for the orphan check; `tests/orders/test_inputs.py::
  test_registry_clear_clears_helper_referenced_ordersets` pins clear via
  `registry.clear()`. No second ledger implementation.
- Confirmed registration has no `before_bind=` kwarg → defaults `False`
  → skipped by finalizer `iter_subsystem_clears(before_bind=True)`;
  included by `TypeRegistry.clear` → `iter_subsystem_clears()`. Helper
  ledger must survive finalize so phase 2.5 can read it.
- Found divergent knowledge in-file: module docstring claimed
  "Slice 3 will wire `registry.clear()` … via the local-import dance"
  and the ledger comment claimed "cycle-safe local import … SEPARATE
  block from `clear_order_input_namespace()`", while the next lines
  already register `register_subsystem_clear(...)`. Twin of the
  filters/`__init__.py` staleness that `dry-file-filters____init__.md`
  corrected; that pass deferred this file's prose to this item.
- Rejected extracting a shared
  `make_helper_ledger(owner=...)` with `filters/__init__.py`: the
  ledger+clear+register triple is ~6 lines of family-named surface
  (different set types, owner strings, helper names) that both specs
  require co-located with the Decision-11 writer. A factory would hide
  that ownership for no behavioral gain. Cross-family filters↔orders
  packaging of this idiom belongs to the folder / project pass —
  forward, do not preempt.
- Rejected re-exporting `OrderArgumentsFactory` through this entry
  point: deliberate advanced-import boundary (spec-028 Decision 2),
  not accidental omission.
- Rejected editing stale Slice-3 / local-import phrasing in
  `orders/inputs.py::clear_order_input_namespace` docstring from this
  item — that file owns its prose under `dry-file-orders__inputs.md`.

## Opportunities

**1. Divergent clear-lifecycle description next to the registration**

- **Repeated responsibility:** how `_helper_referenced_ordersets` is
  drained on `registry.clear()` / how phase 2.5 uses the ledger.
- **Sites:** module docstring (forward-looking Slice-3 local-import
  dance) and the ledger comment above `_helper_referenced_ordersets`
  (claimed cycle-safe local import inside `TypeRegistry.clear`) vs the
  actual `register_subsystem_clear(_clear_helper_referenced_ordersets,
  owner="orders.helper_references")` immediately below.
- **Evidence:** same lifecycle rule, incompatible descriptions in one
  file; the registration seam is what `registry.clear()` /
  `iter_subsystem_clears()` actually replay. Filters twin was fixed in
  `dry-file-filters____init__.md` and deferred this file.
- **Owner:** module docstring + comment co-located with the ledger and
  clear callback in this file.
- **Consolidation:** rewrite both to name `register_subsystem_clear`
  and `registry.clear()` for drain, describe phase 2.5 as an orphan
  *reader* (not a drain), and retire the local-import / Slice-3-will
  claims. Do not claim finalizer pre-bind replays this row
  (`before_bind` defaults false — lesson from filters W2).
- **Proof:** the registration call site three lines below is the
  permanent contract; `tests/orders/test_inputs.py::
  test_registry_clear_clears_helper_referenced_ordersets` already pins
  ledger clear via `registry.clear()`.
- **Risks / non-goals:** do not invent a shared clear-factory across
  families here; do not edit `orders/inputs.py` namespace-clear prose
  from this item; do not claim pre-bind drain.

## Judgment

One in-file knowledge fix (stale clear-lifecycle docstring + ledger
comment). No further consolidation: the Decision-11 body is already at
`build_lazy_input_annotation`, the public export list is a deliberate
curated surface, and the filters↔orders ledger/clear mirror is
intentional family parallelism for a later folder/project judgment.

## Implementation (Worker 1)

- **Owner:** module docstring and ledger comment in
  `orders/__init__.py` beside `_helper_referenced_ordersets` /
  `_clear_helper_referenced_ordersets` / `register_subsystem_clear`.
- **Migrated:** comment/docstring text only — now names
  `register_subsystem_clear(owner="orders.helper_references")` and
  states that `registry.clear()` replays the callback; local-import /
  Slice-3-will claims retired; phase 2.5 described as orphan
  comparison (reader), not drain. No pre-bind claim.
- **Left separate:** `orders/inputs.py` twin Slice-3 phrasing (sibling
  file item); ledger+clear+register triple vs filters
  (folder/project); public `__all__` curation vs factories.
- **Validation:** `uv run ruff format` + `uv run ruff check --fix`.
  No pytest (per assignment).
- **Changelog:** no — comment/docstring-only accuracy fix, no behavior
  change.

## Independent verification (Worker 2)

Re-traced from the complete `orders/__init__.py`, the item-scoped diff vs
`8980ca5f06b1c60b4e575cba5f14c137a2877c07`, sibling `filters/__init__.py`,
`registry.py::register_subsystem_clear` / `iter_subsystem_clears` /
`TypeRegistry.clear`, `types/finalizer.py` pre-bind + `_bind_ordersets`,
`orders/inputs.py::clear_order_input_namespace` (`before_bind=True`),
`connection.py::_synthesized_signature` (calls `order_input_type` for
ledger honesty), and
`tests/orders/test_inputs.py::test_registry_clear_clears_helper_referenced_ordersets`.

**Pre-bind overclaim — absent (filters lesson applied).** Registration is:

```python
register_subsystem_clear(_clear_helper_referenced_ordersets, owner="orders.helper_references")
```

No `before_bind=` kwarg → defaults `False` → skipped by finalizer
`iter_subsystem_clears(before_bind=True)`; included by
`TypeRegistry.clear` → `iter_subsystem_clears()`. The rewritten ledger
comment names only `register_subsystem_clear` + `registry.clear()` for
drain, retires the local-import shape, and describes phase 2.5 as orphan
comparison (reader) that may raise `ConfigurationError` — matching
`_bind_ordersets` / the shared sidecar binding pipeline. Module docstring
likewise describes the orphan check only; neither site claims finalizer
pre-bind drains the helper ledger. Contrast
`orders/inputs.py::clear_order_input_namespace` (`before_bind=True`), a
separate registered row correctly left out of this file's prose.

**filters↔orders mirror — deferral upheld.** `order_input_type` is already
a thin `build_lazy_input_annotation` wrapper; the ledger+clear+register
triple is family-named surface co-located with the Decision-11 writer.
A shared `make_helper_ledger` would hide ownership for no change axis.
Sibling `filters/__init__.py` carries the same accurate clear-lifecycle
shape after its W2 revision cycle; this item closed the deferred twin
prose without inventing a cross-family owner.

**Stale Slice-3 phrasing in `orders/inputs.py`** — still present in
`clear_order_input_namespace`'s docstring; owned by
`dry-file-orders__inputs.md`, correctly left alone here.

**Out-of-scope stale representation (non-blocking):**
`tests/test_registry.py::test_clear_tolerates_unimportable_order_submodules`
docstring still narrates cycle-safe local imports inside `clear()` for the
order co-clear. Not this file's comment-fix scope; registry / folder /
that test's own item should retire the prose when touched.

**Missed consolidations owned by this file — none beyond the comment fix.**
Public `__all__` matches the intentional surface; `OrderArgumentsFactory`
remains a deliberate non-export; single writer (`order_input_type`) and
single orphan reader (`finalizer.py::_bind_ordersets`) for
`_helper_referenced_ordersets`.

**Disposition:** verified. Plan item checked.
