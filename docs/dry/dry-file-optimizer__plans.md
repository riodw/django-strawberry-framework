# DRY review: `django_strawberry_framework/optimizer/plans.py`

Status: verified

## System trace

The target owns the **optimizer plan shape and the shared plan-time helpers**
the walker emits and the extension / fetch strategies consume:

- `OptimizationPlan` — construction-time mutable directives
  (`select_related` / `prefetch_related` / `only_fields` /
  `fk_id_elisions` / `planned_resolver_keys` + path→key coupling maps),
  `finalize()` tuple/frozenset handoff, `apply()`, and the
  `merge_from` / `merge_metadata_from` construction-time commit seam
  (field-inventory guard).
- Plan-list mutators — `_IndexedList`, `append_unique` /
  `append_unique_many` / `append_prefetch_unique`, `_lookup_path`
  (Django-private `Prefetch.prefetch_to`).
- B8 reconciliation — `prune_unsupportable_select_related`,
  `diff_plan_for_queryset`, consumer projection readers
  (`deferred_loading_of`, `_consumer_only_fields`, `_consumer_projection`,
  `_consumer_prefetch_lookups`), lookup-path flatteners.
- Resolver identity — `resolver_key`, `runtime_path_from_info` /
  `runtime_path_from_path`.
- Cursor-parity order vocabulary — `order_entry_name_and_direction`,
  `ends_in_unique_column`, `deterministic_order` (hoisted from
  `connection.py` so plan-time windows and resolve-time pipelines share
  one total-order rule).
- Windowed-prefetch mechanism — `_dst_*` annotation constants,
  `window_partition_for_prefetch` (raise-contract shim over
  `join_taxonomy.classify_relation_join`), `apply_window_pagination` /
  `_apply_keyset_counted_window` / `_reverse_order_by` (ORM `Q`
  rendering of `utils.connections.window_range_plan`).

Connected behavior examined (evidence; siblings not edited):

- `optimizer/walker.py` — builds plans; consumes append helpers,
  `resolver_key`, runtime path; re-exports nested_planner order helpers
  under historical names for tests.
- `optimizer/extension.py` — `prune_unsupportable_select_related` +
  `diff_plan_for_queryset` before apply; publishes finalized lookup
  paths.
- `optimizer/nested_fetch.py` — `attach_windowed_prefetch` →
  `apply_window_pagination` + `append_prefetch_unique` (floor every
  strategy shares).
- `optimizer/nested_planner.py` — `deterministic_order`,
  `order_entry_name_and_direction` (via `_order_entry_field_name`),
  `deferred_loading_of`; `join.windowable` gate (AND-merged) vs this
  file's dual-raise partition shim.
- `optimizer/lateral_fetch.py` — second window dialect (raw SQL); shares
  annotation names, `order_entry_name_and_direction`,
  `deferred_loading_of`, `window_range_plan` decisions; keeps separate
  renderers.
- `optimizer/join_taxonomy.py` — `WINDOWABLE_RELATION_KINDS` +
  `classify_relation_join`; shim already imports the exported set
  (sibling consolidation present at ITEM_BASELINE / working tree).
- `connection.py` — resolve-time consumer of window annotations /
  `deterministic_order` / `order_entry_name_and_direction`; re-exports
  `_ends_in_unique_column` as the hoisted symbol.
- `keyset.py::split_order_ref` — configuration-time `cursor_field`
  syntax twin of the string branch of `order_entry_name_and_direction`
  (re-evaluated below).
- `utils/connections.py` — `window_range_plan` /
  `assert_window_fetch_mode` / `split_window_rows` (range decisions and
  sentinel split; not reimplemented here).
- Pins: `tests/optimizer/test_plans.py` (plan shape, B8, window, order
  hoist, reverse); walker / extension / lateral / keyset suites;
  live nested-connection / keyset HTTP under
  `examples/fakeshop/test_query/` (behavior unchanged by this pass — no
  new live pin earnable for a proved zero-edit).
- Baseline
  `git diff 328aebac56f46abf3cdfc3b4f6df677d7cf75f5b -- …/plans.py`
  was empty. Concurrent dirty optimizer / docs / test paths left
  untouched (including the working-tree WINDOWABLE import already at
  baseline).

## Verification

Searches:

- `order_entry_name_and_direction` / `split_order_ref` /
  `deterministic_order` / `ends_in_unique_column` /
  `apply_window_pagination` / `window_partition_for_prefetch` /
  `WINDOWABLE_RELATION_KINDS` / `deferred_loading_of` /
  `diff_plan_for_queryset` / `prune_unsupportable_select_related` /
  `_reverse_order_by` / `append_prefetch_unique` / `_lookup_path` /
  `RowNumber` / `_dst_row_number` — package-wide.
- Optional
  `export_dry_review.py audit --target …/plans.py --stdout`: 43
  definitions; reverse imports match walker / extension / nested_* /
  lateral / connection / types.resolvers / tests. Exact-duplicate body
  groups are test fixtures and unrelated packages — no production twin
  of plan helpers.
- Scratch contract table (interpreters side-by-side) for the two order
  parsers on `name` / `-name` / `-` / `--name` / `` / `shelf__code` /
  `pk` / `F(...).asc()` / non-string — see rejected candidate 1.

Disproved / rejected candidates:

1. **Unify `order_entry_name_and_direction` with
   `keyset.split_order_ref`.** Fresh re-evaluation. Same leading-dash
   shape on the happy path; opposite contracts elsewhere:
   - `split_order_ref` raises `ConfigurationError` (schema /
     `Meta.cursor_field`), rejects `--name`, bare `-`, empty string, and
     `__` relation traversal.
   - `order_entry_name_and_direction` returns `None` for unresolvable /
     empty entries (caller chooses fallback), accepts `__` paths
     (`connection._resolve_order_path_field`), accepts `OrderBy`/`F`
     expressions, and treats `--name` as name `"-name"` descending.
   Merging would need mode flags or dual return/raise shapes and would
   couple configuration-time loud failure to query-time fallback.
   Rejected.

2. **Route `_reverse_order_by`'s string arm through
   `order_entry_name_and_direction`.** The string flip is the inverse of
   parse-then-reencode, not a second parser of the deterministic-order
   vocabulary; `OrderBy` / NULLS swapping has no home in the parser.
   Bare `-` currently becomes `""`; forcing the parser's `None` path
   needs a special case. Rejected (helper would obscure, not own).

3. **Replace shim membership test with `descriptor.windowable`.**
   Disproved by the classifier contract:
   `windowable = (kind in WINDOWABLE_RELATION_KINDS) and partition is not None`.
   That AND-merge collapses the shim's dual `OptimizerError` messages
   (wrong kind vs unresolved partition) pinned in
   `TestWindowPartitionForPrefetch`. Sibling join_taxonomy review
   already exported the frozenset; this file already consumes it at
   ITEM_BASELINE. Rejected / already landed.

4. **Inline / delete `window_partition_for_prefetch`.** Rejected: owns
   the historical raise contract; classification never raises. Same
   judgment as join_taxonomy (shim kept).

5. **Merge ORM window `Q` rendering with lateral SQL window / seek
   renderers.** Rejected: range/seek *decisions* already live once in
   `window_range_plan` / `keyset` seek plan; remaining work is
   dialect-shaped. Confirmed by lateral_fetch sibling review.

6. **Unify `_concrete_order_columns` (nested_planner) with lateral
   `_order_columns`.** Evidence only for nested_planner / already
   rejected by lateral_fetch: different failure postures (skip for
   `.only()` projection vs `None` downgrade vs `ConfigurationError`).
   String parse already shared via `order_entry_name_and_direction`.

7. **Extract shared range-`Q` builder between
   `apply_window_pagination` and `_apply_keyset_counted_window`.**
   Lower-bound optionality and marker annotation
   (`WINDOW_ROW_NUMBER` vs `WINDOW_ROW_NUMBER_ABS`) differ; a helper
   needs mode flags. Rejected.

8. **Touch `nested_planner` / `walker` / `lateral_fetch` /
   `connection` in this item.** Deferred to those open/verified plan
   items. Thin shims (`_order_entry_field_name`,
   `_connector_only_field`) already delegate here or to join_taxonomy.

Focused experiments: interpreter contract table for the two order
parsers (above). No permanent code/test edits — no new behavior to pin.

## Opportunities

None — prior consolidations already place shared responsibilities at
their owners (`deterministic_order` / order parser here; window range
in `utils.connections`; join membership in `join_taxonomy`; window
attach floor in `nested_fetch`; seek structure in `keyset`). Remaining
lookalikes fail the same-contract / same-change-axis test (see
Verification).

## Judgment

`plans.py` is the correct home for plan shape, B8 reconciliation,
cursor-parity order, and ORM window rendering. Fresh review finds no
further consolidation that would improve ownership without collapsing
distinct error or dialect contracts. Zero-edit. Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced `plans.py` as owner of plan shape / B8 / cursor-parity order /
ORM window `Q` rendering. Consumers (walker, extension, nested_planner /
nested_fetch, lateral_fetch, connection, types.resolvers) import these
helpers; no second production twin of the plan mutators, B8 readers, or
window annotation constants.

**Zero-edit scoped diff.** Re-ran
`git diff 328aebac56f46abf3cdfc3b4f6df677d7cf75f5b -- django_strawberry_framework/optimizer/plans.py`
→ empty. Working tree matches ITEM_BASELINE (including
`WINDOWABLE_RELATION_KINDS` import). HEAD lacks that import; the dirty
`M` vs HEAD is concurrent restore-to-baseline, not cycle work. Left alone.

**Challenge — unify `order_entry_name_and_direction` with
`split_order_ref`.** Independently re-ran the contract table (happy path
agrees; everything else diverges):

| entry | `order_entry…` | `split_order_ref` |
| --- | --- | --- |
| `name` / `-name` / `pk` | `(name, dir)` | same |
| `-` / `` | `None` | `ConfigurationError` |
| `--name` | `("-name", True)` | `ConfigurationError` |
| `shelf__code` | accepted | `ConfigurationError` (`__`) |
| non-str / `OrderBy` | `None` / parse | must-be-string raise / N/A |

Tried the wrap shape (`split` → parse via `order_entry` then raise on
`None` / leading `-` / `__`): it would couple config-time loud failure to
query-time fallback acceptance and freeze `--name` / `__` policy into the
wrong owner. A shared two-line dash-strip helper is Django's `order_by`
convention, not a shared invariant. **Rejection upheld.**

**Other rejections re-challenged (all upheld):**

1. `_reverse_order_by` via the parser — string flip is inverse re-encode;
   bare `-` → `""` today; `OrderBy` NULLS swap has no home in the parser.
2. `descriptor.windowable` for the shim membership test — classifier
   AND-merges kind∩partition (`join_taxonomy.py::classify_relation_join`
   return); collapses the dual `OptimizerError` pins.
3. Delete `window_partition_for_prefetch` — historical raise contract over
   never-raising classifier.
4. ORM `Q` ↔ lateral SQL window renderers — decisions already shared via
   `window_range_plan`; dialects stay separate.
5. Shared range-`Q` helper between `apply_window_pagination` and
   `_apply_keyset_counted_window` — marker annotation and lower-bound
   optionality differ; needs mode flags.

**Missed-opportunity search.** Package-wide: only three `startswith("-")`
sites (the two parsers + `_reverse_order_by` flip — not a third parser).
`deferred_loading_of` / `WINDOW_*` constants / `append_prefetch_unique` /
`deterministic_order` have single owners. Walker’s
`prefetch_to or prefetch_through` fallback is a different posture from
`_lookup_path` (index key vs. hint attribution with through fallback) —
not a second `_lookup_path`. No consolidation that improves ownership.

**Verdict.** Zero-edit verified. Plan item checked.
