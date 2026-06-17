# Review: `django_strawberry_framework/optimizer/plans.py`

Status: verified

## DRY analysis

- **`_consumer_prefetch_lookups` already centralises the `_prefetch_related_lookups` private-contract read; `_lookup_path` already centralises the `prefetch_to` private-contract read.** No further consolidation needed — these two helpers are the single source for the two brittle Django-private prefetch contracts and are reused at every call site (`plans.py::_diff_prefetch_related` #"consumer_pf = _consumer_prefetch_lookups", `plans.py::_prefetch_lookup_paths` #"inner_lookups = _consumer_prefetch_lookups", `plans.py::append_prefetch_unique` #"lookup_path = _lookup_path(prefetch)", `plans.py::_diff_prefetch_related` #"_lookup_path(entry): entry"). Recorded as act-now-not-needed; this is the correct factoring.
- **`deterministic_order` + `ends_in_unique_column` are the spec-033 Decision-11 cursor-parity single-source, imported back by `connection.py`.** `connection.py` re-aliases `ends_in_unique_column` to `_ends_in_unique_column` (`connection.py:90`) and calls `deterministic_order` at `connection.py:805`; walker calls both (`walker.py:1442`, and via `apply_window_pagination`). No duplication to remove — the cross-module reuse is the intended shape; do NOT fold the alias away (it preserves the historic private name without re-implementing).
- **Forwarded from `field_meta.py` cycle (build-time-vs-walk-time FK-id-elision DRY):** `plans.py` does NOT participate in FK-id-elision computation or stamping — it only stores `fk_id_elisions` as an opaque resolver-key sequence (`OptimizationPlan.fk_id_elisions`) and freezes it in `finalize()` (`plans.py::OptimizationPlan.finalize` #"finalized_fk_id_elisions=frozenset"). The elision-eligibility logic lives in `field_meta.py` (producer) and `walker.py` (consumer twins); `plans.py` is a passive carrier. No FK-id-elision DRY item belongs to this file. Confirmed inert for the optimizer folder pass — nothing to forward onward from `plans.py` on that axis.

## High:

None.

## Medium:

None.

## Low:

### `append_unique` / `append_unique_many` module-level helpers are now thin shims over `_IndexedList`, narrowing toward dead generality

`append_unique(values, value)` and `append_unique_many` (`plans.py::append_unique`, `plans.py::append_unique_many`) accept any `MutableSequence`, branching on `isinstance(values, _IndexedList)` and falling back to a linear `value not in values` scan for a plain list. Every live writer now uses `_IndexedList`-backed plan fields (the dataclass `default_factory`s are `_indexed_list` / `_prefetch_indexed_list`), so the plain-`MutableSequence` fallback branch exists only for hypothetical manual/test callers. This is correct and tested today (`tests/optimizer/test_plans.py::TestAppendUnique::test_append_unique_skips_existing_value`, `test_append_unique_many_iterates_tuple`), and the helper docstring frames it as a plan-shape mutator deliberately living next to the plan. Defer consolidation until the last non-`_IndexedList` caller is removed; trigger: a grep of `append_unique(` / `append_unique_many(` shows every argument is a known `_IndexedList`-typed plan field, at which point the `isinstance`-branch and the linear fallback can collapse into direct `.append_unique` calls and the module-level shims retire. No action now — the generic signature is the public plan-mutator contract the walker relies on.

### `_consumer_prefetch_lookups` trailing `or ()` is documented dead code under a real `QuerySet`

`_consumer_prefetch_lookups` (`plans.py::_consumer_prefetch_lookups` #"or ()") guards a `None`-valued `_prefetch_related_lookups` attribute that stock Django never produces (it always stores a tuple). The docstring already names this as a paranoid guard for test-double/custom-manager inputs and states the revisit trigger verbatim ("a real consumer surfaces a `None` lookups attribute or the test-double case is otherwise retired"). Honest and self-documenting; no change. Listed only so the folder pass sees it is already dispositioned with a trigger.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_lookup_path` (`plans.py:53-60`) and `_consumer_prefetch_lookups` (`plans.py:392-407`) are the single-source wrappers for the two Django-private prefetch contracts (`Prefetch.prefetch_to`, `QuerySet._prefetch_related_lookups`); `_consumer_only_fields` (`plans.py:410-438`) is the single-source wrapper for `query.deferred_loading`. `_lookup_paths_from_parts` (`plans.py:839-846`) is shared by `finalize()` (`plans.py:233-235`) and `lookup_paths()` (`plans.py:832-836`), so the finalized-vs-construction-time path-flatten logic has exactly one implementation. `deterministic_order` / `ends_in_unique_column` (`plans.py:481-539`) are the cursor-parity single-source imported back by `connection.py` (spec-033 D11).
- **New helpers considered.** A shared `if x is None: x = recompute()` mini-helper for the `finalized_* or recompute` reads in `finalize`/`lookup_paths` was considered and rejected — the bodies are heterogeneous (different recompute calls and return types) and folding loses readability for no win, matching the calibration carried forward from `extension.py`. Collapsing `append_unique`/`append_unique_many` into `_IndexedList` methods was considered and deferred with an explicit trigger (see Low).
- **Duplication risk in the current file.** The `2x prefetch_to` / `2x queryset` repeated string literals flagged by the shadow are not real duplication: `prefetch_to` appears once inside `_lookup_path`'s `getattr` and once in `_prefetch_lookup_paths`'s nested-Prefetch branch (the latter cannot route through `_lookup_path` because it must distinguish a missing `prefetch_to` via the `None` sentinel for the `continue`), and `queryset` is a parameter name. Both are intentional.

### Other positives

- **Cache-isolation invariant is enforced structurally, not by convention, for the five directive fields.** `finalize()` swaps the mutable `_IndexedList`s for `tuple`s (and the three `finalized_*` for `frozenset`s) via `dataclasses.replace`, so a post-handoff `plan.prefetch_related.append(...)` raises `AttributeError` rather than silently poisoning the extension plan cache across requests. Pinned by `tests/optimizer/test_plans.py::TestFinalize::test_finalize_blocks_post_handoff_append_on_cache_isolation`. The one remaining convention-only field (`cacheable`) has its single-writer rationale and a documented trigger to move to `@dataclass(frozen=True)`. This is exactly the request-scope/cache-mutation safety the optimizer review focus calls for.
- **`diff_plan_for_queryset` never mutates the input plan** — it copies via `replace(...).finalize()` and returns the original unchanged when nothing diffs (`plans.py:753-759` early `return plan, queryset`), keeping the extension's B1 plan cache intact. The consumer-wins reconciliation (drop optimizer `only_fields` whenever the consumer applied `.only()`; drop optimizer prefetch entries on any subtree the optimizer cannot losslessly absorb) is the conservative, data-loss-avoiding choice and is comprehensively tested across the absorb/upgrade/consumer-wins/only-fields matrix (`tests/optimizer/test_plans.py` `TestDiffPrefetchAbsorb`, `TestDiffOnlyFields`, etc.).
- **The downgrade-to-`Prefetch` / `get_queryset` request-scope rule is respected at the plan level via `cacheable`** — the field docstring explicitly ties O6 `Prefetch` downgrades embedding `DjangoType.get_queryset(...)` querysets to non-cacheability because `info.context` may carry user/tenant/permission state. `is_empty` deliberately excludes `cacheable` and documents the consequence plus a revisit trigger.
- **`runtime_path_from_path` bounds its linked-list walk** with `_MAX_PATH_DEPTH = 1024` and raises `RuntimeError` on overrun, converting a would-be infinite hang on a cyclic/corrupt `prev` chain into a loud, statically-bounded failure (NASA Power-of-Ten Rule 2). The generous ceiling and its safety argument are documented; cyclic-path failure pinned by `test_raises_on_cyclic_path`.
- **`apply()` ordering is justified** (`only()` -> `select_related()` -> `prefetch_related()`) with the reason inline (select_related narrows only() column lists; prefetch carries nested Prefetch querysets with their own only()), and is empty-tolerant. `_db` / `.using(alias)` preservation is inherent to the QuerySet cloning `apply()` performs — GLOSSARY "Multi-database cooperation" item 2 anchoring `OptimizationPlan.apply` is accurate, not stale.
- **`apply_window_pagination` sources window order and return order from one `order_by` tuple by construction** (applied via `.order_by(*order_by)` AND inside the `RowNumber()` window) so the fast-path cursors cannot drift from the fallback pipeline (spec-033 D11). The `reverse` / unbounded-limit / `sys.maxsize` branches are each individually pinned (`TestApplyWindowPagination`). `_reverse_order_by` correctly mirrors Django's `.reverse()` for string and `OrderBy`/expression shapes including NULLS-position swap.
- **Defensive `getattr` style is consistent and intentional** across the consumer-introspection helpers (treat a non-`QuerySet` input as having no existing select_related/prefetch/only), enabling test doubles without weakening the real-`QuerySet` path. Reflective access audited against the shadow's 24 `getattr` / 8 `isinstance` entries — every one is either a Django-private-contract read with a centralising wrapper or a documented defensive shim.

### Summary

`plans.py` is clean, well-documented, and unchanged since baseline `14910230` (`git log 14910230..HEAD` and `git diff HEAD` both empty, as the change context predicted — not in the spec-035 changed set). The plan's correctness-critical invariants — post-handoff immutability for cache isolation, copy-never-mutate reconciliation, consumer-wins `only`/`prefetch` reconciliation that avoids silent data loss, the `cacheable` request-scope flag for `get_queryset` downgrades, and the cursor-parity single-source `order_by` — are all sound and thoroughly tested in `tests/optimizer/test_plans.py`. No High/Medium findings; two forward-looking Lows already self-documented with triggers. The forwarded FK-id-elision DRY item does not touch this file (passive carrier only). Qualifies as a no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 270 files unchanged.
- `uv run ruff check --fix .` — all checks passed (only the pre-existing COM812-vs-formatter config-compatibility notice).

### Notes for Worker 3
- Shadow used: `docs/shadow/django_strawberry_framework__optimizer__plans.overview.md` (+ `.stripped.py`). Not regenerated this cycle (source unchanged since plan-time `--all` sweep).
- Low #1 (`append_unique`/`append_unique_many` shim collapse): forward-looking, trigger quoted verbatim in the body. No source edit.
- Low #2 (`_consumer_prefetch_lookups` `or ()` dead-code guard): already dispositioned in-source with a verbatim revisit trigger. No source edit.
- No GLOSSARY-only fix in scope — GLOSSARY references (`#djangooptimizerextension` anchor for `OptimizationPlan.apply` line 888; `_dst_row_number`/`_dst_total_count` line 253; `fk_id_elisions` line 563; uncacheable-plan line 987) all check out accurate against current source.
- FK-id-elision DRY forward from `field_meta.py` cycle: confirmed NOT applicable to `plans.py` (passive carrier); nothing to forward to the `optimizer/` folder pass from this file on that axis.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits — the module's docstrings and inline comments are accurate and current (TODO count 0 per shadow; the `_MAX_PATH_DEPTH`, `_dst_*` namespace, and consumer-wins reconciliation comments all match the implementation exactly).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (review-only). Per `AGENTS.md` #21 (do not update CHANGELOG.md unless explicitly instructed) and the active plan `review-0_0_10.md` (silent on changelog edits for review cycles).

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit cycle (shape #5). Independently re-derived the three correctness-critical invariants from source:

- **(a) copy-never-mutate / cache isolation.** `finalize()` (`plans.py::OptimizationPlan.finalize`) builds a NEW instance via `dataclasses.replace` and never mutates `self`; it swaps the five directive fields to `tuple` and the three `finalized_*` to `frozenset`, so a post-handoff `plan.prefetch_related.append(...)` raises `AttributeError`. Pinned by `tests/optimizer/test_plans.py::TestFinalize::test_finalize_blocks_post_handoff_append_on_cache_isolation` (line 204). `diff_plan_for_queryset` only ever copies: it returns `(plan, queryset)` unchanged on the no-diff early-out (`plans.py #"return plan, queryset"`) and otherwise emits `replace(plan, ...).finalize()`. No in-place mutation of the input plan exists anywhere in the module.
- **(b) consumer-wins reconciliation for `only` / `prefetch_related`.** `only_fields` is dropped entirely when `_consumer_only_fields(queryset) is not None` (`plans.py::diff_plan_for_queryset #"drop_only_fields"`); the helper correctly gates on `deferred_loading` with `defer_flag is False` AND a non-empty field set, so only a real consumer `.only()` triggers the drop (`.defer()` composes cleanly and is excluded). Prefetch reconciliation absorbs the consumer subtree ONLY under the three lossless conditions in `_optimizer_can_absorb` (opt entry is a `Prefetch` with a queryset; every matching consumer entry is a bare string; every matching consumer path is covered by the optimizer's own lookup tree); otherwise the optimizer entry is dropped (`plans.py::_diff_prefetch_related #"else: consumer wins"`). Both branches avoid silent data loss.
- **(c) `cacheable` request-scope guard prevents cross-request `get_queryset` leakage.** Confirmed `plans.py` NEVER writes `cacheable` — the flag's only writers are in `walker.py` (lines 568/647/727/1416/1436), corroborating the passive-carrier claim and the docstring's single-writer (`walker.py::plan_optimizations`) rationale. `walker.py:722-727` flips `plan.cacheable = False` precisely for consumer-supplied `Prefetch` downgrades that commonly close over request/user-scoped querysets (matching the `has_custom_get_queryset` discipline). The extension consumes it correctly: a non-cacheable plan is NEVER inserted into `_plan_cache` (`extension.py:922 #"if plan.cacheable:"`, and the eviction gate at line 914), so one request's `get_queryset`-derived queryset can never be served to another. The data-isolation risk is structurally closed, not convention-bound.

Both Lows confirmed genuinely no-action with valid, falsifiable in-source triggers:

- **Low #1 (`append_unique`/`append_unique_many` shim collapse).** The shims' `isinstance(values, _IndexedList)` else-branch (the linear `value not in values` fallback) is LIVE, not dead: `walker.py:977 columns: list[str] = []` and `walker.py:1015 fields: list[str] = []` are plain lists passed to `append_unique(columns, ...)` / `append_unique(fields, ...)` (walker.py:983/985/1016/1019/1021), exercising the fallback. So the trigger ("a grep shows every argument is a known `_IndexedList`-typed plan field") is genuinely unmet today — deferral is correct.
- **Low #2 (`_consumer_prefetch_lookups` trailing `or ()`).** Dead-code-under-real-`QuerySet` (stock Django always stores a tuple); the docstring frames it as a paranoid guard for present-but-`None` attrs on test doubles/custom managers and states the verbatim revisit trigger. No-action, correctly dispositioned.

The forwarded FK-id-elision DRY item genuinely does NOT apply: `plans.py` stores `fk_id_elisions` only as opaque resolver-key strings and freezes them in `finalize()` (`#"finalized_fk_id_elisions=frozenset"`); no elision-eligibility computation lives here. Passive carrier confirmed.

### DRY findings disposition
All three DRY items in the artifact re-confirmed. `_lookup_path` / `_consumer_prefetch_lookups` / `_consumer_only_fields` are the single-source wrappers for the three Django-private contracts; `_lookup_paths_from_parts` is shared by `finalize()` and `lookup_paths()`; `deterministic_order` / `ends_in_unique_column` are the cursor-parity single-source imported back by `connection.py` (spec-033 D11). The rejected `if x is None: x = recompute()` mini-helper and the deferred-with-trigger `append_unique` collapse are both sound. No DRY item to forward from this file.

### Temp test verification
- No temp test required: all three invariants are statically provable from source and pinned by existing named tests (`test_finalize_blocks_post_handoff_append_on_cache_isolation`, `test_cacheable_flag_does_not_affect_empty_state`, `test_raises_on_cyclic_path` all confirmed present in `tests/optimizer/test_plans.py`). The cacheable cross-request claim required cross-file inspection (walker writers + extension cache-insert gate), not executable confirmation.
- Disposition: none created.

### Shape #5 protocol checks
- `git diff HEAD -- django_strawberry_framework/optimizer/plans.py` empty; `git log 14910230..HEAD -- plans.py` empty. Cycle diff for the owned path is clean.
- Diff-stat dirty paths (`management/commands/_imports.py`, `export_schema.py`, `inspect_django_type.py`, `tests/management/test_imports.py`) attribute to the CLOSED sibling cycle `rev-management__commands.md` (verified, `[x]` in `review-0_0_10.md`) — not a rejection trigger.
- Every Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.`
- Both Lows carry verbatim in-source trigger phrasing; neither is a GLOSSARY-only fix.
- Changelog: `git diff -- CHANGELOG.md` empty; disposition cites BOTH `AGENTS.md` #21 and the active plan's silence. `Not warranted` is correct (review-only cycle, no public-API surface change).
- `uv run ruff format --check` and `uv run ruff check` both pass on `plans.py`.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box at `review-0_0_10.md:97`.

---

## Iteration log

(none)
