# Review: `django_strawberry_framework/filters/sets.py`

Status: verified

> **Re-review after concurrent change.** This artifact previously closed `verified`
> against a baseline where the cycle diff was empty. Commit `79b74b46
> "Refactor permission checks to consolidate active permission targets"` then
> rewrote ~+53 lines (constant hoists + a fused single-pass permission walk),
> re-opening this item. The sections below are rewritten against CURRENT source at
> HEAD (`git diff HEAD -- filters/sets.py` is empty; the maintainer's change is
> committed). The whole file is the review unit; the consolidated permission logic
> got the security-critical attention the dispatch called for. Iteration history is
> preserved by this note + the prior `verified` close (now superseded).

## DRY analysis

- None — the refactor under review IS a DRY consolidation, and it lands the file at its maximally-factored shape. The new `FilterSet._active_permission_targets` (sets.py:1292-1313) is a thin delegate to `utils/permissions.py::active_permission_targets`, which is now the single-sited single-pass classifier that BOTH `_active_permission_field_paths` (sets.py:1273-1289, takes the `LEAF` half) and `active_related_branches` (permissions.py:203-245, takes the `RELATED` half) wrap, and that `run_active_input_permission_checks` (permissions.py:319-337) consumes once per level instead of two full walks. The two new module constants `_LOGIC_WIRE_BY_PYTHON_ATTR` (sets.py:93) and `_NORMALIZE_TRAVERSAL` (sets.py:99-104) collapse per-call rebuilds in `_normalize_input` to import-time singletons. The remaining same-named twins versus `orders/sets.py` (`_iter_input_items`, `_request_from_info`, `_iter_active_related_branches`, `_active_permission_field_paths`, `_active_permission_targets`, `_run_permission_checks` body) are the deliberate two-family wrappers around the shared `utils/permissions.py` core, not duplication — the cross-folder consolidation of these wrappers is already deferred-with-trigger in the cycle-11 (`sets_mixins.py`) / cycle-12 (`filters/base.py`) artifacts ("re-confirm all 3 families share the params when AggregateSet / fieldsets WIP-ALPHA-028 lands"). No new act-now opportunity is unique to this file.

## High:

None.

## Medium:

None.

## Low:

### `_q_for_branch` defensive-fallback sync derive on the async stash-miss path

`_q_for_branch` (sets.py:1486-1563) consults `_nested_qs_by_branch_id` and, on a stash miss under the async path, falls back to `_derive_related_visibility_querysets_sync` — which would re-raise `SyncMisuseError` for an async-only target `get_queryset`. The docstring (sets.py:1496-1519) names this as a deliberate defensive fallback for callers that short-circuit past the `_collect_nested_visibility_querysets_async` pre-walk (e.g. invoking `_q_for_branch` directly). This remains correct: `_collect_nested_visibility_querysets_async` (sets.py:1034-1105) walks every reachable `and` / `or` / `not` arm with the same `_extract_branch_value` dual-key logic `_evaluate_logic_tree` uses and stashes each by `id(child_input)`, so the production async path can never reach the fallback for a branch the sync descent will later visit. Untouched by the refactor. Recorded only to pre-empt re-flagging — NOT a finding needing a fix. Re-examine only if the two walkers' branch-enumeration logic ever diverges (e.g. `_collect_nested_*` stops recursing a branch shape `_evaluate_logic_tree` still descends), at which point the stash-miss fallback would become a reachable async-path `SyncMisuseError`.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_iter_input_items` -> `utils/permissions.py::iter_input_items` (sets.py:659-667); `_request_from_info` -> `request_from_info(..., family_label="FilterSet")` (sets.py:864-875); `_iter_active_related_branches` -> `active_related_branches(...)` (sets.py:878-904); `_extract_branch_value` -> `extract_branch_value(...)` (sets.py:907-917); `_active_permission_targets` -> `active_permission_targets(...)` (sets.py:1305-1313); `_active_permission_field_paths` -> `_active_permission_targets(...)[0]` (sets.py:1289); `_invoke_permission_method` -> `invoke_permission_method(...)` (sets.py:1270); `_run_permission_checks`'s gate core -> `run_active_input_permission_checks(...)` (sets.py:1212-1219); visibility derive -> `apply_type_visibility_sync` / `apply_type_visibility_async`; the lifecycle-attr names + cache/guard via `SetLifecycleAttrs` + `expanded_once`; RelatedFilter collection via `collect_related_declarations` (sets.py:188-201). All single-sited with the order twin.
- **New helpers considered.** The refactor already extracted the right helpers: `active_permission_targets` (permissions.py:153-200) is the single-pass classifier; `_active_permission_field_paths` and `active_related_branches` are now thin wrappers over it so the LEAF/RELATED classification rule stays single-sited. `_LOGIC_WIRE_BY_PYTHON_ATTR` / `_NORMALIZE_TRAVERSAL` (sets.py:93, 99-104) hoist the per-call rebuilds `_normalize_input` paid. `_apply_common_prelude` / `_apply_common_finalize` (sets.py:1658-1698) still collapse the sync/async shared body to one site each; the async-only `_nested_qs_by_branch_id` stash correctly stays inline in `apply_async`. No further helper warranted.
- **Duplication risk in the current file.** The `and` / `or` / `not` three-branch unrolled loops recur in `_collect_nested_visibility_querysets_async`, `_run_permission_checks`, and `_evaluate_logic_tree`, but each unrolls differently (async derive vs perm recursion vs `Q` `&`/`|`/`~` composition with the `or` arm needing its own accumulator and `not` negated) — a shared iterator would obscure the per-branch operator semantics. Correct as intentional sibling shape. The two-call-site fan-out of every delegate (FilterSet here + OrderSet twin) is the deliberate two-family design.

### Other positives

- **The fused permission walk preserves the prior semantics exactly.** `run_active_input_permission_checks` now calls `cls._active_permission_targets(input_value)` ONCE (permissions.py:325) and partitions into `field_paths` (LEAF) + `related_branches` (RELATED), where it previously made two full `iter_active_fields` walks. The `LEAF` half is byte-identical to the old `active_permission_field_paths` (same `django_source_path` / `fallback_path` rule, permissions.py:192-197); the `RELATED` half yields the same `(field_name, related_obj, child_input)` tuples the old `active_related_branches` did (RELATED classification keys only off `related_attr` membership, independent of `field_specs` / `logic_keys`, permissions.py:175-179). `LOGIC` records are dropped by both old and new code. Branch iteration order moved from declared-collection order to input-iteration order, but is documented order-independent (per-class `_fired` dedup, AND-commutative narrowing). The duck-typed contract holds: both FilterSet and OrderSet define `_active_permission_targets` (orders/sets.py:350), so `cls._active_permission_targets` resolves on either family.
- **The two new module constants are import-order-safe.** `_NORMALIZE_TRAVERSAL` (sets.py:99-104) holds `_field_specs` BY REFERENCE inside a frozen `SetInputTraversal` (input_values.py:89-114, no copy), and `iter_active_fields` reads `config.field_specs.get(...)` live at call time (input_values.py:176). `filters/inputs.py` mutates `_field_specs` IN PLACE (`_field_specs[key] = ...`, inputs.py:703,746 — never reassigned, inputs.py:141), so binds that happen after this module imports are observed by the singleton. `_LOGIC_WIRE_BY_PYTHON_ATTR = dict(_LOGIC_KEYS)` (sets.py:93) reproduces the old per-call `dict(_LOGIC_KEYS)` (`_LOGIC_KEYS` is the frozen `(("and_","and"),...)` tuple, inputs.py:130). Both hoists are pure perf with zero behavior change.
- **Denial-before-filter ordering holds (both paths).** `apply_sync` -> `_apply_common_finalize` (sets.py:1681-1698) runs `_run_permission_checks` then `_validate_form_or_raise` BEFORE the `.qs` read, so a permission denial raises before the queryset materializes. `_run_permission_checks` recurses into `and`/`or`/`not` branches (sets.py:1224-1252) and `run_active_input_permission_checks` recurses into child RelatedFilter sets (permissions.py:329-337), so every nested gate fires pre-`.qs`. The async path routes the identical `_apply_common_finalize` through `sync_to_async(thread_sensitive=True)` (sets.py:1745) — same ordering, off-loop. Untouched by the refactor.
- **Queryset-as-scope-boundary is airtight.** `_iter_visibility_steps` (sets.py:920-964) raises `ConfigurationError` for an ACTIVE related branch whose target type / child filterset cannot resolve (sets.py:947-952), rather than skipping it — the load-bearing "skipping silently returns unfiltered rows" guard. `_target_type_for_related_filter` (sets.py:1108-1135) prefers the child filterset's bound `_owner_definition.origin` over a model-only `registry.primary_for` lookup, closing the documented multi-DjangoType silent row-leak. Both untouched by the refactor.
- **ORM correctness.** `_apply_related_constraints` (sets.py:1566-1655) wraps each branch as `pk__in=<parent-pk subquery>` to collapse many-side JOIN duplicates without `.distinct()` (no consumer-visible queryset mutation), keys the final `.filter()` on `related_filter.field_name` (the ORM accessor), and derives the subquery from `constrained` itself so the DB alias / custom-manager scoping carry through. The explicit-`queryset=` × child-qs mixed-model case raises a typed `ConfigurationError` via `is`-identity model comparison.
- **Caches are clear-hook-correct.** `_lookups_for_field_class_cache` keys on the Django field CLASS (stable across `registry.clear()`) so it needs no clear hook — documented (sets.py:71-78); `_lookups_for_field` returns a `list(cached)` copy. `_FORM_KEY_BY_PYTHON_ATTR` built once at import from a `reversed` view so first-match-wins parity holds (sets.py:85-88).
- **Test discipline.** Both `check_permissions` entry paths (explicit `requested_fields` and active-input fallback, sets.py:1315-1335) are pinned; the apply pipeline, Relay-vs-scalar conditional, depth cap, and nested-branch visibility are exercised through the example app and package tests. The fused walk is covered transitively by every existing permission test (the public behavior is unchanged).

### Summary

`filters/sets.py` is the spec-027 FilterSet declaration + apply pipeline (1800 lines), re-reviewed after commit `79b74b46` rewrote the permission-target resolution. The refactor is a clean DRY consolidation: a new single-pass `active_permission_targets` classifier replaces two separate input walks per permission level, with `_active_permission_field_paths` / `active_related_branches` reduced to thin LEAF/RELATED wrappers and `run_active_input_permission_checks` calling the fused `cls._active_permission_targets` once. Both families define the method, preserving the duck-typed core contract. Two module constants (`_LOGIC_WIRE_BY_PYTHON_ATTR`, `_NORMALIZE_TRAVERSAL`) hoist per-call rebuilds to import time and are import-order-safe because `_field_specs` is mutated in place and held by reference. All four security-critical invariants the dispatch named are preserved and were re-derived against current source: denial-before-filter ordering fires on both sync and async paths before `.qs`; an active-but-unresolvable RelatedFilter branch raises rather than silently widening; visibility scoping prefers the bound owner type over a model-only registry lookup (closing the multi-type row-leak); and the `pk__in` subquery shape avoids both JOIN-duplicate corruption and consumer-visible `.distinct()` mutation. No High, no Medium, one no-action Low recorded only to pre-empt re-flagging of the documented async stash-miss defensive fallback. Qualifies as a no-findings + no-source-edit cycle (shapes #1 -> #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 270 files left unchanged.
- `uv run ruff check .` — pass; "All checks passed!" (the COM812/formatter-conflict notice is pre-existing config noise, not a result of this cycle).

### Notes for Worker 3
- Re-review after concurrent change (commit `79b74b46`). `git diff HEAD -- django_strawberry_framework/filters/sets.py` is EMPTY — the maintainer's change is committed; this is standing-code review against HEAD.
- The refactor is behavior-preserving: the fused `active_permission_targets` single walk produces the SAME `LEAF` paths and `RELATED` branch tuples the two prior separate walks did (LEAF/RELATED classification is independent of the dropped LOGIC records; RELATED tuples are field-spec/logic-key independent). Verify by re-deriving from `utils/permissions.py:153-200` against `:248-292` (the LEAF wrapper) and `:203-245` (the RELATED wrapper).
- The two new constants are import-order-safe: `_field_specs` is mutated in place (inputs.py:703,746; never reassigned at :141) and held by reference inside the frozen `SetInputTraversal` (input_values.py:89-114), read live at call time (input_values.py:176).
- Single Low is no-action (documented async stash-miss defensive fallback in `_q_for_branch`); forward-looking re-examination trigger stated inline. No edit warranted.
- No GLOSSARY-only fix in scope: GLOSSARY entries for `FilterSet`, `RelatedFilter`, `Meta.filterset_class`, `SyncMisuseError` carry no symbol-name drift from the refactor (the refactor added/renamed only private `_`-prefixed helpers, none of which are documented public contract).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits warranted — the refactor's new docstrings (`_active_permission_targets`, the updated `_active_permission_field_paths` "thin delegate to `_active_permission_targets`'s `LEAF` half" note) and the two new constant-block comments (sets.py:90-104, both citing feedback L2) are accurate and load-bearing. The `_q_for_branch` fallback rationale, the `pk__in`-vs-direct-JOIN dedup note, and the `get_filters` `cls.__dict__`-guard reasoning all still match the implementation.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_10.md` is silent on changelog edits for review cycles). The maintainer's `79b74b46` refactor predates this review and is the maintainer's to changelog if desired.

---

## Verification (Worker 3)

Terminal-verify of the re-opened cycle (commit `79b74b46` rewrote `filters/sets.py`;
`git diff HEAD -- filters/sets.py` is EMPTY — the change is committed, this is standing-code
review against HEAD). Shape #5 (no this-cycle source edit). All four security-critical
invariants the dispatch named were independently re-derived against current source.

### Logic verification outcome

- **High / Medium: none asserted, none found.** Re-derived the artifact's behavior-preservation
  claim from source rather than trusting it.
- **Single-pass partition is behavior-equivalent to the prior two-walk result.**
  `active_permission_targets` (permissions.py:153-200) runs `iter_active_fields` ONCE and
  partitions by `field.kind`: LEAF -> `leaf_paths` via `spec.django_source_path` else
  `fallback_path(python_attr)` (:192-197); RELATED -> `(python_attr, related_obj, raw_value)`
  (:198-199); LOGIC dropped. The classifier (input_values.py:177-182) keys LOGIC off
  `logic_keys`, then RELATED off `python_attr in related`, then LEAF (else). Independently
  confirmed: (a) the LEAF half uses the full filter config so logic keys are correctly excluded
  as LOGIC and lookup attrs collapse to the source field — byte-identical to old
  `active_permission_field_paths`; (b) the RELATED half is config-independent (related membership
  is checked off `related` alone, and related/logic names are disjoint families), so
  `active_related_branches`'s `field_specs={}, logic_keys=frozenset()` call yields the same
  branch tuples — the empty `logic_keys` only affects LEAF/LOGIC classification, which
  `active_related_branches` discards. Both `_active_permission_field_paths` (sets.py:1289) and
  `active_related_branches` (permissions.py:235) are now thin wrappers; the classification rule
  is single-sited.
- **`run_active_input_permission_checks` calls the fused classifier ONCE** (permissions.py:325
  `cls._active_permission_targets(input_value)`) then fires per-field gates (:326-327) and the
  per-branch / child-set gates (:329-337) — replacing two prior full walks.
- **Denial-before-filter holds on BOTH paths.** `_apply_common_finalize` (sets.py:1696-1698)
  runs `_run_permission_checks` then `_validate_form_or_raise` BEFORE reading `.qs`. `apply_sync`
  (:1722) calls it directly; `apply_async` routes the same call through
  `sync_to_async(thread_sensitive=True)`. A denial raises before the queryset materializes.
- **`_iter_visibility_steps` raises, does not skip** (sets.py:946-961): an ACTIVE related branch
  whose `target_type`/`child_filterset` cannot resolve raises `ConfigurationError` — the
  "skipping silently returns unfiltered rows" guard. Untouched by the refactor.
- **`_target_type_for_related_filter` prefers bound owner over model-only registry**
  (sets.py:1128-1135): returns `child_owner.origin` first, falls back to
  `registry.primary_for(child_model) or registry.get(child_model)` only when unbound — the
  multi-DjangoType silent row-leak guard. Untouched.
- **`pk__in` subquery dedup, no consumer-visible `.distinct()`**: `_apply_related_constraints`
  filters `pk__in=matching_parent_pks` (sets.py:1654), comment at :1643 explicitly avoids
  `.distinct()` to not mutate consumer-visible queryset state; `_q_for_branch` composes
  `Q(pk__in=child_set.qs.values("pk"))` (:1563). Untouched.
- **Two hoisted constants import-order-safe.** `_field_specs` is created once
  (inputs.py:141 `_field_specs = {}`) and only ever mutated by subscript assignment
  (inputs.py:703, 746 `_field_specs[...] = ...` — never reassigned). `filters/sets.py:61`
  imports it by reference and binds it into the frozen `_NORMALIZE_TRAVERSAL` (sets.py:99-104);
  `iter_active_fields` reads `config.field_specs.get(...)` live (input_values.py:176), so binds
  after import are observed. `_LOGIC_WIRE_BY_PYTHON_ATTR = dict(_LOGIC_KEYS)` (sets.py:93)
  snapshots the frozen tuple. Both pure perf, zero behavior change.
- **Duck-typed contract holds on both families.** Both `FilterSet` (sets.py:1292) and `OrderSet`
  (orders/sets.py:350) define `_active_permission_targets`, so the `cls._active_permission_targets`
  call in the shared core resolves on either; `_active_permission_field_paths` on both reduces to
  `[...][0]` (sets.py:1289, orders/sets.py:347).

### DRY findings disposition

No act-now DRY item — the cycle IS a DRY consolidation landing the file at its maximally-factored
shape. The remaining FilterSet/OrderSet wrapper twins are the deliberate two-family design around
the shared `utils/permissions.py` core; cross-folder wrapper consolidation stays deferred-with-trigger
in the cycle-11/12 artifacts (AggregateSet / WIP-ALPHA-028). Carried forward unchanged.

### Low disposition

The single Low (`_q_for_branch` async stash-miss sync-derive defensive fallback, sets.py:1486-1563)
is genuinely no-action: confirmed `_collect_nested_visibility_querysets_async` (sets.py:1034-1105)
pre-walks the same `and`/`or`/`not` arms `_evaluate_logic_tree` descends and stashes by
`id(child_input)`, so the production async path cannot reach the sync fallback. The forward-looking
re-examination trigger (walker branch-enumeration divergence) is stated inline. No edit warranted.

### Temp test verification

- Temp test used: `docs/review/temp-tests/filters/test_active_permission_targets_equiv.py` (gitignored).
  5 tests, all PASS. Independently re-derived the pre-refactor LEAF and RELATED walks (separate
  `iter_active_fields` passes with the old per-walk configs) and asserted the fused
  `active_permission_targets` LEAF half == old LEAF walk and RELATED half == old RELATED walk across
  a mixed input (leaf + lookup-collapse + fallback + related + logic key + inactive/UNSET), plus
  both wrappers (`active_permission_field_paths`, `active_related_branches`) == the fused halves,
  plus inactive-related-branch exclusion. Run: `uv run pytest ... --no-cov -q` -> `5 passed`.
- Disposition: DELETED (executable confirmation of an already-test-covered behavior-preserving
  refactor; the public behavior is unchanged and covered transitively by the existing permission
  suite — not a new behavior gap requiring promotion).

### Shape #5 checks

- Cycle diff for owned paths empty: `git diff HEAD -- filters/sets.py` empty; `git diff --stat HEAD`
  shows only `management/commands/_imports.py`, `export_schema.py`, `inspect_django_type.py`,
  `tests/management/test_imports.py` — all attribute to the CLOSED sibling cycle
  `rev-management__commands.md` (Status: verified, [x] at review-0_0_10.md:90). Not a rejection trigger.
- Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` ✓
- The single Low carries verbatim trigger phrasing; no GLOSSARY-only fix. ✓
- Changelog `Not warranted` with BOTH citations (AGENTS.md + active-plan silence); `git diff -- CHANGELOG.md` empty. ✓
- `uv run ruff format --check` (2 files already formatted) + `uv run ruff check` (All checks passed!) — pass.
  The COM812/formatter-conflict notice is pre-existing config noise.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.
