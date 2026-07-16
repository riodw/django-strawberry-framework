# DRY review: `django_strawberry_framework/orders/sets.py`

Status: verified

ITEM_BASELINE: `0e19b14684c5b784f6719fd3b4fffcee2a86677d`

## System trace

`orders/sets.py` owns the consumer-facing `OrderSet` / `OrderSetMetaclass`
surface for spec-028:

- **Declaration / metaclass.** `OrderSetMetaclass` discovers `RelatedOrder`
  declarations via `sets_mixins.collect_related_declarations`
  (`inherit_from_bases=True` — plain `type` metaclass has no django-filter
  MRO merge).
- **Layer-4 expansion.** `get_fields` / `_expand_meta_fields` expand
  list-form and `"__all__"` `Meta.fields`, merge `related_orders`, and cache
  through `expanded_once` + `should_cache_expansion` + `SetLifecycleAttrs`.
- **Permission duck-typed facade.** Thin classmethods
  (`_request_from_info`, `_extract_branch_value`, `_active_permission_*`,
  `_invoke_permission_method`, `_run_permission_checks`) configure and
  delegate to `utils/permissions.py` — the API
  `run_active_input_permission_checks` re-enters via
  `cls._active_permission_targets` / `cls._invoke_permission_method` /
  child `_run_permission_checks`.
- **Apply pipeline.** `apply_sync` / `apply_async` (no `apply` dispatcher):
  request → permission gate → `_apply_orderings` (normalize →
  `get_flat_orders` → `_resolve_order_expressions` → annotate / `order_by`).
  Async wraps only `_run_permission_checks` in
  `utils/querysets.py::run_in_one_sync_boundary` (already migrated; preserved).
- **To-many ordering.** `_resolve_order_expressions` aggregates reverse-FK /
  M2M paths with `Min` / `Max` so parent rows are not multiplied (P1-B).

Connected surfaces: `orders/inputs.py` (`Ordering`, `normalize_input_value`,
`_get_concrete_field_names_for_order`, `_field_specs`), `orders/base.py`,
`sets_mixins.py`, `utils/permissions.py`, `utils/querysets.py`,
`utils/relations.py::path_traverses_to_many`, `connection.py` (sync/async
apply call sites), `types/finalizer.py` (phase-2.5 `_owner_definition`
bind), `filters/sets.py` (sibling apply / permission shape),
`tests/orders/test_sets.py`, live GraphQL under
`examples/fakeshop/test_query/test_library_api.py` (sync `apply_sync` via
HTTP Client; async unit-tier).

Baseline scoped diff for the target at ITEM_BASELINE was empty; working
tree already carried the uncommitted `run_in_one_sync_boundary` migration
from the verified `filters/sets.py` item — preserved, not reverted.

## Verification

1. **`run_in_one_sync_boundary`.** Already single-sited in
   `utils/querysets.py`; this file imports and uses it. **Preserve** —
   no further move.

2. **Filter/order apply-pipeline family mirror.** Both normalize →
   permission → family tail; shared request / active-input mechanics
   already live in `utils/permissions.py`. Orders has no related-visibility
   derive, nested async pre-walk, form validate, or `.qs` materialization —
   its shared tail is `_apply_orderings`, not filter finalize. Collapsing
   the two apply graphs needs mode flags across distinct contracts.
   **Rejected at file scope** — folder / project may re-check after both
   family files are verified; this file does not own a missing shared
   piece beyond the sync-boundary primitive already consolidated.

3. **Permission thin wrappers.** Required duck-typed re-entry surface for
   `run_active_input_permission_checks`; filter side mirrors the same
   shape with different config (`UNSET`, logic keys, `related_filters`).
   Deleting them would force utils to know family internals.
   **Rejected.**

4. **`get_flat_orders` nearly identity when `prefix=""``.** Cookbook-shaped
   public helper + prefix API for partial subtree walks; normalize already
   flattens nested `RelatedOrder` paths. Not a second implementation of
   normalize. **Rejected** — keep as intentional seam.

5. **`_expand_meta_fields` vs filter field expansion.** Different
   `Meta.fields` contracts (order list / `"__all__"` column walk vs filter
   lookup bags). `"__all__"` helper ownership already settled at
   `orders/inputs.py` (inputs review deferred `sets_mixins` promotion).
   **Rejected.**

6. **Ascending / descending discrimination
   (`"ASC" in direction.name`).** Confirmed real repeated responsibility
   with `Ordering.resolve` (`"ASC" in self.name`). Same change axis when
   direction variants grow; both pick ascending vs descending semantics
   (F.asc/desc vs Min/Max). **Accepted** — see Opportunities.

7. **Obsolete deferred local import of
   `_get_concrete_field_names_for_order`.** Module already top-level-imports
   other `.inputs` symbols; `inputs.py` only TYPE_CHECKING-imports
   `OrderSet`. The local-import "cycle dodge" was a false parallel path.
   **Accepted** as delete-obsolete-path (not a new abstraction).

8. **Stale Slice-1/2/3 delivery prose in module / `_owner_definition`
   comments.** Weaker than the inputs-file ownership-of-`registry.clear`
   finding; binding already lives in `types/finalizer.py`. **Deferred** —
   folder polish, not a behavioral consolidation.

## Opportunities

### 1. Single-site ascending discrimination on `Ordering.is_ascending`

- **Repeated responsibility:** Whether an `Ordering` member is ascending
  (including NULLS variants) vs descending.
- **Sites:** `orders/inputs.py::Ordering.resolve`
  (`"ASC" in self.name` → `.asc` / `.desc`);
  `orders/sets.py::OrderSet._resolve_order_expressions`
  (`"ASC" in direction.name` → `Min` / `Max` for to-many aggregates).
- **Evidence:** Byte-parallel substring rule; identical variant set
  (ASC / ASC_NULLS_* / DESC / DESC_NULLS_*); a new direction member would
  have to update both sites or silently mis-aggregate.
- **Owner:** `orders/inputs.py::Ordering.is_ascending`.
- **Consolidation:** Add `is_ascending` property; `resolve` and
  `_resolve_order_expressions` both consume it.
- **Proof:** `tests/orders/test_inputs.py::test_ordering_is_ascending_classifies_all_six_members`;
  existing resolve + to-many Min/Max pins (`test_resolve_order_expressions_*`,
  live `test_library_api` to-many `orderBy`) keep behavioral coverage.
  Live GraphQL already earns sync ASC/DESC aggregate paths; property pin
  is unit-tier (enum API, not a new resolver branch).
- **Risks / non-goals:** Do not invent a membership table or fold NULLS
  positioning into the same property (NULLS_* substring checks remain
  resolve-only, single site). Do not merge filter/order apply graphs.

### 2. Promote `_get_concrete_field_names_for_order` to module-level import

- **Repeated responsibility:** How this module reaches the `"__all__"`
  column walk (false "must defer for cycle" knowledge).
- **Sites:** Local import inside `_expand_meta_fields` vs existing
  top-level `.inputs` imports.
- **Evidence:** `inputs.py` never runtime-imports `sets`; cycle claim is
  obsolete.
- **Owner:** `orders/sets.py` import block.
- **Consolidation:** Top-level import; drop deferred local import.
- **Proof:** Existing `"__all__"` expansion tests in `tests/orders/test_sets.py`.
- **Risks / non-goals:** Do not move the helper into `sets_mixins` (inputs
  review already deferred that until a second set family needs it).

## Judgment

The order apply pipeline is already well-factored against shared
substrate (`sets_mixins`, `utils/permissions`, `utils/querysets`). The
one fresh code-level duplication this file still participated in was the
ASC/DESC name substring rule shared with `Ordering.resolve`; consolidating
that on `Ordering.is_ascending` and deleting the obsolete local import are
the root-cause fixes owned here. Filter/order apply-graph merge stays
folder / project.

## Implementation (Worker 1)

- **Owner chosen:** `orders/inputs.py::Ordering.is_ascending`.
- **Migrated:** `Ordering.resolve`;
  `orders/sets.py::OrderSet._resolve_order_expressions` (Min/Max branch).
- **Also:** promoted `_get_concrete_field_names_for_order` to module-level
  import; removed deferred local import.
- **Preserved (no revert):** `run_in_one_sync_boundary` import +
  `apply_async` call (concurrent uncommitted filters/sets DRY migration).
- **Left untouched:** `orders/__init__.py` concurrent docstring WIP;
  other concurrent dirty trees outside this item.
- **Tests:** `test_ordering_is_ascending_classifies_all_six_members` in
  `tests/orders/test_inputs.py`. Live library `orderBy` / to-many aggregate
  coverage already earns the sync apply path.
- **Validation:** `uv run ruff format .` and `uv run ruff check --fix .`
  (run after edits). Full pytest not run (Worker 1 file item).
- **Changelog:** no — internal ownership of an existing discrimination
  rule; no public API break (`is_ascending` is additive).
- **Rejected / deferred retained:** filter/order apply-graph merge
  (folder/project); permission wrapper collapse; `get_flat_orders`
  inlining; Slice delivery-prose polish; `sets_mixins` promotion of
  `_get_concrete_field_names_for_order`.

## Independent verification (Worker 2)

Re-traced `OrderSet` ownership (metaclass / Layer-4 expansion / permission
duck-typed facade / apply pipeline / to-many aggregates) through
`orders/inputs.py`, `utils/permissions.py`, `utils/querysets.py`,
`filters/sets.py` sibling apply graph, `tests/orders/`, and live library
`orderBy` consumers. No production edits.

### Consolidation 1 — `Ordering.is_ascending`

**Challenge:** Is a shared property justified, or should Min/Max keep a
local rule / grow an `aggregate_for_to_many` on `Ordering`?

**Verdict: accepted.** Grep shows the old `"ASC" in …name` rule had exactly
two production consumers (`Ordering.resolve`,
`OrderSet._resolve_order_expressions`); both now read `is_ascending`. The
property body anchors on the member-name prefix (`self.name.startswith("ASC")`,
not substring membership) so every `ASC*` member classifies ascending and
every `DESC*` member descending, and the rule stays precise if a future
member embeds `ASC` elsewhere in its name. Putting Min/Max selection *on*
`Ordering` would couple the
direction enum to Django aggregates — worse ownership. NULLS positioning
correctly remains resolve-only (single site). Owner
`orders/inputs.py::Ordering.is_ascending` is clearer than dual substring
checks.

### Consolidation 2 — promote `_get_concrete_field_names_for_order` import

**Challenge:** Was the deferred local import still needed for a runtime
cycle?

**Verdict: accepted.** `inputs.py` only TYPE_CHECKING-imports `OrderSet`;
module-level import of the helper alongside `Ordering` / `_field_specs` /
`normalize_input_value` succeeds (import smoke). Local-import comment was
obsolete parallel knowledge; delete-obsolete-path, not a new abstraction.
`sets_mixins` promotion correctly left deferred (one consumer family).

### `run_in_one_sync_boundary` preserved

**Confirmed.** Import at `orders/sets.py` + sole `apply_async` wrap of
`_run_permission_checks` unchanged vs ITEM_BASELINE (already present at
baseline; not introduced by this item). Owner remains
`utils/querysets.py::run_in_one_sync_boundary`. Filter side still wraps a
larger finalize blob — intentional family difference, not drift.

*Artifact narrative note (disposed):* claiming this wrap was only
"concurrent uncommitted filters work" is slightly off for *this* file — it
was already at ITEM_BASELINE — but the preserve-not-revert outcome is
correct.

### Deferred filter/order apply-pipeline merge

**Challenge:** Should file scope have collapsed the apply graphs anyway?

**Verdict: deferral stands.** Filter `apply_*` owns visibility derive,
related constraints, form validate, `.qs`, nested async pre-walk, and
`run_permissions`/`_depth` re-entry; order `apply_*` is request →
permission → `_apply_orderings` (normalize / flat / resolve / annotate /
`order_by`) with async wrapping **only** the permission step. Shared
substrate already lives in `utils/permissions.py` +
`run_in_one_sync_boundary`. A merged driver would need mode flags across
distinct contracts. Folder/project may re-check; no missing shared piece
owned by this file.

### Other rejected candidates (re-checked)

| Candidate | Worker 2 disposition |
| --- | --- |
| Permission thin wrappers | Keep — duck-typed re-entry for `run_active_input_permission_checks`; filter config differs (`UNSET`, logic keys, `related_filters`). |
| `get_flat_orders` nearly identity | Keep — cookbook-shaped public seam + `prefix` API; not a second normalize. |
| `_expand_meta_fields` vs filter expansion | Keep — different `Meta.fields` contracts. |
| Slice delivery-prose / comment polish | Deferred polish — not behavioral DRY. |

### Tests

- New: `tests/orders/test_inputs.py::test_ordering_is_ascending_classifies_all_six_members`
- Existing Min/Max pins still cover the migrated aggregate branch:
  `test_resolve_order_expressions_aggregates_to_many_orders_scalar_directly`,
  `test_resolve_order_expressions_uses_max_for_descending_to_many`
- Focused run (5 tests): all passed (coverage fail_under expected on
  partial suite).

### Missed opportunities

None material at file scope. GLOSSARY does not yet name `is_ascending`
(additive internal discriminator); standing-doc polish is outside this
item's consolidation contract. The direction rule is now single-sited on
`Ordering.is_ascending`; no third production site duplicates it.

### Blockers

None.

**Status: verified.** Plan item may be checked.
