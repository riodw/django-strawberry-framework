# Review: `django_strawberry_framework/optimizer/plans.py`

Status: verified

(Supersedes the stale 0.0.7-era artifact that carried `Status: verified`; the active plan box `review-0_0_9.md:95` was unchecked. Replaced wholesale per the recurring stale-artifact pattern. Live source diffed; no findings re-raised from the prior cycle.)

## DRY analysis

- **Defer — `_IndexedList.append_unique`/`.append` `with contextlib.suppress(TypeError)` index maintenance vs the module-level `append_unique`/`append_prefetch_unique` `isinstance(values, _IndexedList)` fast-path branch.** The two free functions (`plans.py::append_unique` 353-365, `plans.py::append_prefetch_unique` 373-389) each open with the same `isinstance(values, _IndexedList): values.append_unique(...); return` short-circuit, then fall through to a list-membership scan for the non-indexed `MutableSequence` case. This is correct dual-path design (the walker uses `_IndexedList`; manual/defensive plans may hand a bare list), not act-now duplication. Defer until a third `append_*_unique` free function lands on the plan shape; then extract a single `_dispatch_unique(values, value, *, path_key=None)` that routes indexed vs membership-scan once. Trigger: a third module-level `append_*_unique` mutator.
- **Defer — `_lookup_paths_from_parts` recomputation in `lookup_paths`.** `plans.py::lookup_paths` (832-836) returns `set(plan.finalized_lookup_paths)` when finalized, else recomputes via `_lookup_paths_from_parts`; `finalize()` (233-235) already calls `_lookup_paths_from_parts` to populate `finalized_lookup_paths`. One construction-time computation, one finalized read — correctly single-sited through `_lookup_paths_from_parts`, no duplication today. Defer until a second consumer needs construction-time lookup paths without going through `finalize()`; no trigger fires at 0.0.9.

## High:

None.

## Medium:

None.

## Low:

### `apply_window_pagination` forward-branch `limit >= 0` clause is unreachable-but-harmless (recorded intent)

`plans.py::apply_window_pagination #"limit is not None and limit >= 0 and limit != sys.maxsize"` (656) guards the forward upper-bound `__lte` filter with three conditions. The `limit >= 0` clause cannot be false in practice: `limit` is sourced from `utils/connections.py::derive_connection_window_bounds` (`slice_meta.expected` for the forward branch), which `SliceMetadata.from_arguments` never produces negative (it gates `first`/`last` against `0` and `max_results`). The clause is a defensive belt-and-suspenders against a hand-constructed negative `limit` — harmless (a negative `limit` would otherwise produce `__lte offset+limit < offset`, an always-empty window, which is a benign over-filter not a crash). Recorded intent, not a defect; no source edit. Trigger to revisit: a second caller of `apply_window_pagination` that does not route through `derive_connection_window_bounds` and could legitimately pass a negative `limit` — at that point the clause needs either a docstring note or removal as genuinely dead.

### `_consumer_prefetch_lookups` trailing `or ()` is documented dead-under-real-QuerySet (forward-looking, already annotated in source)

`plans.py::_consumer_prefetch_lookups #"or ()"` (407) is a paranoid guard for a non-`QuerySet` input whose `_prefetch_related_lookups` attribute is present but `None`. The source comment (393-406) already names this as dead code under a real `QuerySet` (stock Django always stores a tuple; `prefetch_related(None)` resets to `()`) and records its own removal trigger verbatim: *"a real consumer surfaces a `None` lookups attribute or the test-double case is otherwise retired."* No action — the deferral is already encoded in source. Listed here only so the next reviewer does not re-discover it as untriaged.

## What looks solid

### DRY recap

- **Existing patterns reused.** Window-math helpers are correctly hoisted to ONE home shared by plan-time and resolve-time: `ends_in_unique_column` / `deterministic_order` live here (481-539) and `connection.py` imports them back (`connection.py:64-65`, `_ends_in_unique_column = ends_in_unique_column` at 90) — the spec-033 Decision 11 cursor-parity invariant has a single implementation. `apply_window_pagination` / `window_partition_for_prefetch` (582-657, 542-579) are the sole window-prefetch mechanism, consumed by `walker.py::_plan_connection_relation` (1209, 1261-1268). The `_dst_*` annotation-name constants (`WINDOW_ROW_NUMBER` / `WINDOW_TOTAL_COUNT` / `WINDOW_ROW_NUMBER_REVERSED`, 476-478) are imported by both `walker.py` and `connection.py` rather than re-spelled — the namespace contract cannot drift.
- **New helpers considered.** `_lookup_path` (53-60) and `_consumer_prefetch_lookups` (392-407) already centralize the two brittle Django-private contracts (`Prefetch.prefetch_to`, `QuerySet._prefetch_related_lookups`) so a future Django rename has one fix-site each — the correct factoring; no further extraction warranted. The `append_*_unique` family's dual indexed/membership path was evaluated and left as intentional dual-path design (see DRY analysis defer bullet).
- **Duplication risk in the current file.** The two repeated string literals the shadow flags (`"prefetch_to"` 2x, `"queryset"` 2x) are reflective-access keys on distinct Django objects (`Prefetch.prefetch_to`, `Prefetch.queryset` / `query` attrs) read via `getattr` in different helpers — not a dispatch-key or constant candidate; hoisting them would obscure the Django attribute names they mirror. Correct as-is.

### Other positives

- **Window SQL math verified correct in both directions.** Forward branch (582-657): offset filter `_dst_row_number__gt offset` drops rows `1..offset`; upper bound `__lte offset+limit` keeps exactly `limit` rows `offset+1..offset+limit`. Reverse (last-only) branch keeps `_dst_row_number` FORWARD and adds a separate `_dst_row_number_reversed` window (reversed order) filtered `__lte limit` to keep the trailing `limit` rows — so `connection.py::_resolve_from_window` (171-255) reads forward row numbers for cursors (`_dst_row_number - 1`, 230) and forward page flags (`first_rn > 1`, `last_rn < total`, 249-250) identically in both branches. The forward order is `.order_by(*order_by)`-applied to the queryset itself in BOTH branches (627), so prefetched-instance return order matches the window order — the fast path cannot diverge from the fallback pipeline. Pinned by `tests/optimizer/test_plans.py::TestApplyWindowPagination` (forward offset+upper-bound `704`, reversed `__lte 2` over-fetch guard `721`, `None`/`sys.maxsize` no-upper-bound `735`/`746`/`752`, `.only()` composition `757`).
- **`offset`/`limit`/`reverse` contract matches the bounds source by construction.** `apply_window_pagination`'s parameters map exactly onto `ConnectionWindowBounds` (`utils/connections.py:70-126`): `offset = SliceMetadata.start`, forward `limit = SliceMetadata.expected`, reverse `limit = literal last` (because `SliceMetadata` sets `end = sys.maxsize` / `expected is None` for last-only). The `limit is None` / `sys.maxsize` "no upper bound" handling (650-651, 655-656) and the comment at 653-654 are consistent with the bounds doc. In the reverse branch `limit` is provably non-`None` (the bounds `reverse` predicate is `isinstance(last, int)`), so the `limit is not None` guard at 650 is correctly defensive, not load-bearing.
- **`window_partition_for_prefetch` raises `OptimizerError` for exactly the non-windowable kinds.** Guards both a single-valued forward relation (kind not in the windowable set, 566-571) and a windowable kind whose `remote_field` resolves neither `attname` nor `name` (574-578). The PARENT-side partition correctly diverges from the instance accessor for forward-M2M without `related_name` (reverse query name off `remote_field`, per docstring 555-563). `walker.py::_plan_connection_relation` catches the raise (1212-1213) to leave the selection unplanned and fall back per-parent — the documented fail-soft contract. Both raise paths pinned (`test_forward_single_relation_raises` 812, `test_windowable_kind_without_remote_field_keys_raises` 818).
- **`_reverse_order_by` does not mutate the caller's order tuple.** Verified live: `OrderBy.copy()` returns an independent clone (`clone = entry.copy() if hasattr(entry, "copy")`, 681), so flipping `clone.descending` and swapping `nulls_first`/`nulls_last` (682-686) cannot corrupt the `order_by` tuple the walker reuses for `deterministic_order` and the forward window. A bare `F` (no `descending` attr) hits the `descending is None` branch (678-679) and is appended unchanged — correct, a directionless ref has nothing to flip. The NULLS-positioning swap mirrors Django's `.reverse()` so a consumer ordering with explicit NULLS placement reverses the same way the resolve-time pipeline does.
- **`finalize()` immutability + cache isolation is sound.** Swaps the five directive lists to tuples and the three `finalized_*` fields to frozensets (222-236) so post-handoff `.append()` raises `AttributeError` (pinned `test_finalize_blocks_post_handoff_append_on_cache_isolation` 204); idempotent on re-finalize (`test_finalize_is_idempotent` 214); `dataclasses.replace` is the documented derive path. The `cacheable` bool's post-handoff immutability is correctly documented as a single-writer convention (the class docstring records the explicit `@dataclass(frozen=True)` migration trigger, 143-145) — recorded intent, not a gap.
- **`deterministic_order` / `ends_in_unique_column` total-order logic is correct.** pk / `pk.attname` / `unique=True` / `primary_key` terminal columns are recognised as already-total (509-523); a relation traversal (`"__"` in ref, 511-516) and an annotation alias / unknown field (`FieldDoesNotExist`, 517-522) are conservatively treated as non-unique so the pk is appended as a terminal tiebreaker — guaranteeing the positional offset cursors are stable across requests. String `-`-prefix stripping and `OrderBy`/`F` `.expression.name` extraction both handled (503-506). Parity pinned `TestDeterministicOrderHoistParity` (834).
- **`diff_plan_for_queryset` reconciliation is conservative and copy-only.** The plan is only ever `replace`d, never mutated (B1 cache stays intact); the consumer-wins rules for `select_related` (exact-path drop, wildcard-`True`-is-no-overlap), `only_fields` (dropped wholesale when the consumer applied `.only()`, because Django's `.only().only()` replaces rather than merges and could drop a permission-boundary projection, 712-720), and `prefetch_related` (lossless-absorb only when the optimizer `Prefetch` carries a queryset, every consumer match is a bare string, and every consumer path is covered, 441-468) all correctly favour preserving consumer data over optimizing. The `prefetch_related(None)` reset-then-rebuild idiom (821-827) is the documented Django reset. Extensive table-driven coverage (`tests/optimizer/test_plans.py` 397-622).
- **`runtime_path_from_path` cycle cap is well-reasoned.** The `_MAX_PATH_DEPTH = 1024` bound (288) turns a corrupt/cyclic `prev` chain into a loud `RuntimeError` (314-317) rather than an infinite hang, with a thorough comment (277-287) justifying why the ceiling sits far above any real query (graphql-core recurses one Python frame per level). Pinned `test_raises_on_cyclic_path` (660).
- **GLOSSARY accurate.** No dedicated backticked entry for any of `apply_window_pagination` / `window_partition_for_prefetch` / `deterministic_order` / `ends_in_unique_column` / `OptimizationPlan`; the "Connection-aware optimizer planning" prose (GLOSSARY:235) describes the `_dst_row_number`/`_dst_total_count` window mechanism, pk-terminal deterministic order, and `.distinct()` fallback — all matching live source. The one `OptimizationPlan.apply` reference (GLOSSARY:864, multi-DB `.using(alias)` `_db` preservation) is accurate: `apply()` (238-253) chains `.only()`/`.select_related()`/`.prefetch_related()` which all preserve `_db`, with no `using()` re-pin. No drift, no replacement text needed.

### Summary

`plans.py` is the optimizer's plan dataclass plus the window-pagination + deterministic-order helpers the walker applies. Logic is clean — no High, no Medium. The window SQL math (forward `__gt offset` + `__lte offset+limit`; reverse forward-row-number-kept + separate reversed `__lte limit`), the `offset`/`limit`/`reverse` contract against `derive_connection_window_bounds`, the `OptimizerError` raise conditions in `window_partition_for_prefetch`, the deterministic pk-terminal total order, queryset/order-tuple immutability (`OrderBy.copy()` clone verified live), and `finalize()` cache isolation all verified correct and well-pinned by `tests/optimizer/test_plans.py`. Two Lows are both recorded-intent / already-annotated-in-source, no edit. Two DRY items are both defer-with-trigger. No GLOSSARY drift. No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format --check django_strawberry_framework/optimizer/plans.py` — `1 file already formatted`.
- `uv run ruff check django_strawberry_framework/optimizer/plans.py` — `All checks passed!`.

### Notes for Worker 3
- Low (forward-branch `limit >= 0` clause): recorded intent, defensive-but-unreachable under the sole caller; explicit revisit trigger stated (a second caller bypassing `derive_connection_window_bounds`). No edit.
- Low (`_consumer_prefetch_lookups` trailing `or ()`): forward-looking, removal trigger already encoded in the source comment. No edit.
- No GLOSSARY-only fix in scope — the connection-optimizer prose (GLOSSARY:235) and the `OptimizationPlan.apply` multi-DB reference (GLOSSARY:864) both match live source.
- Cross-file contract verified read-only against `connection.py` (cursor/page-flag consumption of forward `_dst_row_number`), `walker.py::_plan_connection_relation` (window construction call site), and `utils/connections.py::derive_connection_window_bounds` (offset/limit/reverse source) — all consistent. No cross-file follow-up beyond the deferred DRY items, which belong to a future DRY cycle, not the folder/project pass.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No stale or misleading comments/docstrings found. The version/spec references (spec-033 Decision 4/11) are design-doc anchors, not version-pinned label rot. The `_consumer_prefetch_lookups` dead-code comment and the `OptimizationPlan`/`is_empty`/`apply` docstrings accurately describe live behavior (verified against source). No edit.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source/test/GLOSSARY/CHANGELOG edits in this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; the active `review-0_0_9.md` plan records no changelog directive for this item).

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit cycle (shape #5) on a DATA-CORRECTNESS file; owned diff confirmed empty (`git diff --stat 0872a20 -- django_strawberry_framework/optimizer/plans.py` empty; `git diff -- CHANGELOG.md` empty). Independently re-verified the window-pagination SQL math LIVE (`docs/review/temp-tests/optimizer_plans/`, fakeshop `config.settings`, keyed filters by annotation-expr identity to the `_dst_*` alias):

- **Forward** offset=2 limit=3 → `_dst_row_number__gt 2` AND `_dst_row_number__lte 5` (offset+limit), no reversed annotation/filter. offset=4 limit=None → only `__gt 4`, no upper bound. offset=0 limit=`sys.maxsize` → no `__gt`, no `__lte` (both gates suppressed).
- **Reverse** last=2 → keeps the FORWARD `_dst_row_number` annotation, adds `_dst_row_number_reversed` window, filters `_dst_row_number_reversed__lte 2`, and applies NO forward `__lte` (early `return` before the forward upper-bound). offset=3 last=2 → forward `__gt 3` still applies + reversed `__lte 2`. Both `_dst_row_number` and `_dst_row_number_reversed` present in annotations on the reverse branch.
- **offset/limit/reverse mapping** onto `derive_connection_window_bounds` confirmed at source (`utils/connections.py:124-126`): `reverse = isinstance(last,int) and not isinstance(first,int) and before is None`; `limit = last if reverse else slice_meta.expected`; offset = `slice_meta.start`. The reverse branch's `limit` is provably non-`None` (int `last`), so the `limit is not None` guard at line 650 is defensive, not load-bearing.
- **Cursor/page-flag parity** confirmed at source consumer `connection.py::_resolve_from_window`: reads forward `WINDOW_ROW_NUMBER` for cursors (`getattr(node, WINDOW_ROW_NUMBER) - 1`, :230) and page flags (`first_rn > 1` :249, `getattr(last_row, WINDOW_ROW_NUMBER) < total` :250), identically in both branches — because `apply_window_pagination` keeps `_dst_row_number` forward in both. `.order_by(*order_by)` applied to the queryset itself in both branches (:627) so prefetched-instance return order matches the window order.
- **`_reverse_order_by` non-mutating**: drove `OrderBy(F("name"), descending=False, nulls_first=True)` through it — the original's `(descending, nulls_first, nulls_last)` snapshot is byte-identical before/after; `rev[0] is orig` is False (`OrderBy.copy()` clones); clone has `descending=True, nulls_first=None, nulls_last=True` (direction flipped + NULLS positioning swapped, mirroring Django `.reverse()`). String entries `("name","-pk")` → `["-name","pk"]`; bare `F` (no `descending`) appended unchanged by identity. (Note: Django stores the unset NULLS side as `None`, not `False` — does not affect correctness.)
- **Both `OptimizerError` raise conditions** in `window_partition_for_prefetch`: (1) single-valued forward relation (`Item.category`, kind `forward_single`) raises; (2) a windowable kind (`many`) whose `remote_field` resolves neither `attname` nor `name` raises (crafted stand-in). A genuine windowable reverse-FK (`Category.items`) returns partition `'category_id'`, proving the guard set is exactly the three windowable kinds. `walker.py::_plan_connection_relation` (:1212-1213) catches the raise to fall back per-parent — the documented fail-soft contract.

High/Medium: none, confirmed. Two Lows both forward-looking:
- `apply_window_pagination` forward-branch `limit >= 0` clause (plans.py:655): defensive-unreachable under the sole caller `derive_connection_window_bounds` (never yields negative `limit`); explicit revisit trigger stated (a second caller bypassing the bounds source). Verified `sys.maxsize` path correctly suppresses the upper bound regardless. No edit.
- `_consumer_prefetch_lookups` trailing `or ()` (plans.py:407): dead-under-real-QuerySet, removal trigger already encoded verbatim in the source comment (393-406). No edit.

### DRY findings disposition
Both DRY items are defer-with-trigger and correctly carried forward, not actioned: (1) `append_*_unique` indexed/membership dual-path — trigger is a third module-level `append_*_unique` mutator; (2) `_lookup_paths_from_parts` single-sited through `finalize()`/`lookup_paths` — trigger is a second construction-time consumer. Neither fires at 0.0.9.

### Temp test verification
- Temp files: `docs/review/temp-tests/optimizer_plans/repro.py` (window math), `repro3.py` (non-mutation inspection), `repro4.py` (raise conditions). All gitignored.
- Disposition: deleted at cycle closeout (Worker 0). The shipped window-math is already pinned by `tests/optimizer/test_plans.py::TestApplyWindowPagination` (forward offset+upper-bound, reversed over-fetch guard, None/maxsize no-upper-bound, `.only()` composition) and the raise paths by `test_forward_single_relation_raises` / `test_windowable_kind_without_remote_field_keys_raises` — temp tests are not the sole proof.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box. Owned-path diff empty (byte-unchanged baseline 0872a20); no GLOSSARY-only fix in scope; changelog Not-warranted with both citations and matching empty diff; ruff format-check + check pass (COM812 standing notice).

---

## Iteration log

(none)
