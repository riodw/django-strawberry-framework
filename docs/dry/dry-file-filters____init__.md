# DRY review: `django_strawberry_framework/filters/__init__.py`

Status: verified

## System trace

`filters/__init__.py` is the consumer entry point for the filtering
subsystem. It owns three responsibilities:

1. **Public re-export surface** — curated primitives from `filters/base.py`
   (`Filter` as the plain `django_filters.Filter` re-export, `TypedFilter` /
   `ArrayFilter` / `RangeFilter` / `ListFilter` + method helpers, `RangeField` /
   `validate_range`, `GlobalID*` filters, `RelatedFilter`, and
   `LazyRelatedClassMixin` via `base.py`'s re-export from `sets_mixins`),
   plus `FilterSet` / `FilterSetMetaclass` from `sets.py`.
   `FilterArgumentsFactory` is intentionally absent (advanced consumers
   import `filters.factories` directly); `IntegerInFilter` /
   `IntegerRangeFilter` stay in `base.py` as `FILTER_DEFAULTS` internals,
   not public surface.
2. **Decision-11 helper** — `filter_input_type(filterset_class)` validates
   eagerly, records the class on `_helper_referenced_filtersets`, and
   returns the Strawberry
   `Annotated[<Name>FilterInputType, strawberry.lazy(...)]` forward-ref.
   Body already delegates to
   `utils/inputs.py::build_lazy_input_annotation` (0.0.9 DRY pass).
3. **Helper-ledger lifecycle** — `_helper_referenced_filtersets` lives
   co-located with its only writer (`filter_input_type`);
   `_clear_helper_referenced_filtersets` registers via
   `registry.py::register_subsystem_clear(owner="filters.helper_references")`.
   Finalizer phase 2.5 (`types/finalizer.py`) reads the ledger for orphan
   checks; `connection.py` calls `filter_input_type` when synthesizing
   connection `filter:` args so orphans stay ledgered.

Consumers: fakeshop `*/filters.py` import `FilterSet` / `RelatedFilter`;
fakeshop `*/schema.py` and package tests use `filter_input_type`;
finalizer / connection / tests reach the private ledger for orphan and
clear contracts. Sibling `orders/__init__.py` mirrors the helper + ledger
+ clear shape with `OrderSet` / `order_input_type` /
`_helper_referenced_ordersets`.

## Verification

- Item-scoped diff vs `211a0fc253c919c91fc90f7a6564267976963c5a` was empty
  before this pass; only the ledger comment below changes.
- Compared `filter_input_type` to `orders/__init__.py::order_input_type`:
  both are thin wrappers over the same
  `build_lazy_input_annotation` owner with family-specific
  `expected_base` / `family_name` / `expected_label` / `ledger` /
  `input_type_name_for` / `module_path`. No residual duplicated helper
  body remains in this file.
- Traced ledger readers/writers: only `filter_input_type` adds;
  `_clear_helper_referenced_filtersets` + `register_subsystem_clear` own
  teardown; `types/finalizer.py` imports `_helper_referenced_filtersets`
  for the orphan check; tests assert recording / clear / orphan raises.
  No second ledger implementation.
- Confirmed `__all__` is 1:1 with the intentional public imports (private
  `INPUTS_MODULE_PATH` / `_input_type_name_for` stay module-scoped but
  out of `__all__`, matching the convention `orders/__init__.py`
  documents as mirroring this file).
- Found divergent knowledge in-file: the ledger comment still claimed
  "`registry.clear()` clears this set via a cycle-safe local import per
  spec-027 Decision 9", while the next lines register
  `register_subsystem_clear(...)`. `docs/dry/dry-file-registry.md`
  already flagged this exact pre-seam phrasing in sibling files and
  deferred edits to the owning file — this is that owning file.
- Rejected extracting a shared
  `make_helper_ledger(owner=...)` with `orders/__init__.py`: the
  ledger+clear+register triple is ~6 lines of family-named surface
  (different set types, owner strings, helper names) that both specs
  require co-located with the Decision-11 writer. A factory would hide
  that ownership for no behavioral gain. Cross-family filters↔orders
  packaging of this idiom belongs to the folder / project pass if it
  ever warrants a shared constructor — forward, do not preempt.
- Rejected re-exporting `IntegerInFilter` / `IntegerRangeFilter` or
  `FilterArgumentsFactory` through this entry point: deliberate
  non-public / advanced-import boundaries, not accidental omission.
- Rejected moving `LazyRelatedClassMixin` import from `base` to
  `sets_mixins` here: `base.py` already re-exports the mixin so the
  filters public surface stays stable; changing the hop is cosmetic
  import churn owned by neither DRY need.

## Opportunities

**1. Divergent clear-lifecycle description next to the registration**

- **Repeated responsibility:** how `_helper_referenced_filtersets` is
  drained on `registry.clear()` / finalizer pre-bind.
- **Sites:** the ledger comment above `_helper_referenced_filtersets`
  (claimed cycle-safe local import inside `TypeRegistry.clear`) vs the
  actual `register_subsystem_clear(_clear_helper_referenced_filtersets,
  owner="filters.helper_references")` immediately below.
- **Evidence:** same lifecycle rule, two incompatible descriptions in
  one file; the registration seam is what `registry.clear()` /
  `iter_subsystem_clears()` actually replay. `dry-file-registry.md`
  recorded this staleness and deferred it to this file.
- **Owner:** the comment co-located with the ledger and clear callback
  in this file.
- **Consolidation:** rewrite the comment to name
  `register_subsystem_clear` and explicitly retire the local-import
  claim.
- **Proof:** the registration call site three lines below is the
  permanent contract; `tests/filters/test_finalizer.py` already pins
  ledger clear via `registry.clear()`.
- **Risks / non-goals:** do not edit the twin stale phrasing in
  `orders/__init__.py` from this item (that file owns its comment);
  do not invent a shared clear-factory across families here.

## Judgment

One in-file knowledge fix (stale clear-lifecycle comment). No further
consolidation: the Decision-11 body is already at
`build_lazy_input_annotation`, the public export list is a deliberate
curated surface, and the filters↔orders ledger/clear mirror is
intentional family parallelism for a later folder/project judgment.

## Implementation (Worker 1)

- **Owner:** ledger comment in `filters/__init__.py` beside
  `_helper_referenced_filtersets` / `_clear_helper_referenced_filtersets`
  / `register_subsystem_clear`.
- **Migrated:** comment text only — now names
  `register_subsystem_clear(owner="filters.helper_references")` and
  states the local-import shape is obsolete.
- **Left separate:** `orders/__init__.py` twin comment (sibling file);
  ledger+clear+register triple vs orders (folder/project); public
  `__all__` curation vs factories / integer filters.
- **Validation:** `uv run ruff format` + `uv run ruff check --fix` on
  the edited module. No pytest (per assignment).
- **Changelog:** no — comment-only accuracy fix, no behavior change.

## Independent verification (Worker 2)

Re-traced from the complete `filters/__init__.py`, the item-scoped diff vs
`211a0fc253c919c91fc90f7a6564267976963c5a`, sibling `orders/__init__.py`,
`registry.py::register_subsystem_clear` / `iter_subsystem_clears` /
`TypeRegistry.clear`, `types/finalizer.py` pre-bind + `_bind_filtersets`,
`utils/inputs.py::build_lazy_input_annotation`, and
`tests/filters/test_finalizer.py::test_registry_clear_clears_filter_input_namespace_and_helper_set`.

**Comment-only consolidation — right kind, wrong text.** Aligning the
ledger comment with the real clear seam is genuine in-file knowledge DRY
(one lifecycle rule, previously two incompatible descriptions). It is not
a false abstraction. The code path was already consolidated at
`register_subsystem_clear`; only the prose needed to catch up. No further
behavioral consolidation belongs in this file for that seam.

**Implemented comment overclaims pre-bind.** The rewritten block says
``registry.clear()`` *and* "the finalizer's pre-bind drain replay the
callback". Registration is:

```python
register_subsystem_clear(
    _clear_helper_referenced_filtersets,
    owner="filters.helper_references",
)
```

`before_bind` defaults to `False`. Finalizer pre-bind uses
`iter_subsystem_clears(before_bind=True)`, which therefore **skips** this
row. Contrast `filters/inputs.py::clear_filter_input_namespace`
(`before_bind=True`). The helper ledger must survive finalize passes so
phase 2.5 orphan checks can read it; only full `registry.clear()` drains
it (pinned by `test_registry_clear_clears_filter_input_namespace_and_helper_set`).
The new comment replaces one stale mechanism claim with another inaccurate
lifecycle claim. **Worker 1 must drop the pre-bind sentence** and state
only that `registry.clear()` replays the registered callback (and that
the local-import shape is obsolete).

**filters↔orders mirror — deferral upheld.** `order_input_type` is already
a thin `build_lazy_input_annotation` wrapper; the ledger+clear+register
triple is family-named surface that specs keep co-located with each
Decision-11 writer. A shared `make_helper_ledger` would hide ownership for
no change axis. Twin stale phrasing in `orders/__init__.py` (still
"cycle-safe local import" / Slice-3 local-import dance) is owned by that
file's plan item / folder pass — correctly left alone here.

**Missed consolidations owned by this file — none beyond the comment fix.**
Public `__all__` matches the intentional import set; `FilterArgumentsFactory`
/ `IntegerInFilter` / `IntegerRangeFilter` remain deliberate non-exports;
`LazyRelatedClassMixin` via `base` is a stable hop, not dual policy; single
writer (`filter_input_type`) and single reader
(`finalizer.py::_bind_filtersets`) for `_helper_referenced_filtersets`.

**Disposition:** revision-needed. Plan item left unchecked.

## Iterations

### Worker 1 revision (pre-bind overclaim)

Verified W2 against source:

- `filters/__init__.py` registers
  `register_subsystem_clear(_clear_helper_referenced_filtersets,
  owner="filters.helper_references")` with no `before_bind=` kwarg.
- `registry.py::register_subsystem_clear` defaults `before_bind=False`.
- `types/finalizer.py` drains via
  `iter_subsystem_clears(before_bind=True)`, which skips this row.
- `TypeRegistry.clear` drains via `iter_subsystem_clears()` (all rows),
  so only full registry clear empties the helper ledger.
- Contrast: `filters/inputs.py::clear_filter_input_namespace` registers
  with `before_bind=True`.

Fixed the ledger comment: dropped every pre-bind claim; it now names
only `register_subsystem_clear` + `registry.clear()` and retires the
local-import shape. Ruff format/check clean. Ready for re-verification.

## Independent verification (Worker 2) — re-verification pass

Re-read current `filters/__init__.py` ledger comment against
`register_subsystem_clear` / `iter_subsystem_clears` /
`TypeRegistry.clear`, finalizer `iter_subsystem_clears(before_bind=True)`
+ `_bind_filtersets` orphan read of `_helper_referenced_filtersets`, and
the item-scoped diff vs `211a0fc253c919c91fc90f7a6564267976963c5a`.

**Prior blocking issue — resolved.** The ledger comment no longer claims
finalizer pre-bind drains the helper ledger. It names only the
`register_subsystem_clear` row (`owner="filters.helper_references"`) and
states that `registry.clear()` replays the callback; the local-import
shape is explicitly retired. Phase 2.5 is described as comparing the set
for orphans — a reader, not a drain — which matches
`_bind_filtersets` / the shared binding pipeline.

**Registration vs drain seams — still accurate.** Call site has no
`before_bind=` kwarg → defaults `False` → skipped by finalizer
`iter_subsystem_clears(before_bind=True)`; included by
`TypeRegistry.clear` → `iter_subsystem_clears()`. No new lifecycle
overclaim.

**New issues — none** for this item's Opportunities / Implementation
scope. (Pre-existing "subpass 4" orphan numbering in the comment was
already present at ITEM_BASELINE and is outside the clear-lifecycle
knowledge fix.)

**Disposition:** verified. Plan item checked.
