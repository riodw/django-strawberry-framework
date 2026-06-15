# Review: `django_strawberry_framework/filters/sets.py`

Status: verified

## DRY analysis

- None — the file is already the apply-pipeline DRY chokepoint: every traversal/permission/visibility primitive is a thin delegate to a single-sited helper in `utils/permissions.py`, `utils/input_values.py`, `utils/querysets.py`, or `sets_mixins.py` (the 0.0.9 `docs/feedback.md` Major 1 + 3 pass), and the only sync/async divergence (`apply_sync` vs `apply_async`) is already factored through the shared `_apply_common_prelude` / `_apply_common_finalize` pair. The remaining same-named-helper twins versus `orders/sets.py` (`_iter_input_items`, `_request_from_info`, `_iter_active_related_branches`, `_active_permission_field_paths`, `_run_permission_checks` body) are deliberate two-family wrappers around a shared core, not duplication — confirmed in cycle-11 (`sets_mixins.py`) and cycle-12 (`filters/base.py`). The cross-folder consolidation of these wrappers is already deferred-with-trigger in those artifacts ("re-confirm all 3 families share the params when AggregateSet / fieldsets WIP-ALPHA-028 lands"); no new act-now opportunity is unique to this file.

## High:

None.

## Medium:

None.

## Low:

### `_q_for_branch` defensive-fallback sync derive on the async stash-miss path

`_q_for_branch` (lines 1517-1530) consults `_nested_qs_by_branch_id` and, on a stash miss under the async path, falls back to `_derive_related_visibility_querysets_sync` — which would re-raise `SyncMisuseError` for an async-only target `get_queryset`. The docstring (lines 1517-1524) names this as a deliberate defensive fallback for callers that short-circuit past the `_collect_nested_visibility_querysets_async` pre-walk (e.g. invoking `_q_for_branch` directly). This is correct today: `_collect_nested_visibility_querysets_async` walks every reachable `and` / `or` / `not` arm with the same `_extract_branch_value` dual-key (`and_`/`and`) logic `_evaluate_logic_tree` uses, so the production async path can never reach the fallback for a branch that `_evaluate_logic_tree` will later visit. Recorded only to pre-empt re-flagging — NOT a finding needing a fix. Re-examine only if the two walkers' branch-enumeration logic ever diverges (e.g. `_collect_nested_*` stops recursing a branch shape `_evaluate_logic_tree` still descends), at which point the stash-miss fallback would become a reachable async-path `SyncMisuseError` rather than a pure defensive guard.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_iter_input_items` -> `utils/permissions.py::iter_input_items` (sets.py:651); `_request_from_info` -> `request_from_info(..., family_label="FilterSet")` (sets.py:866); `_iter_active_related_branches` -> `active_related_branches(...)` (sets.py:890-895); `_extract_branch_value` -> `extract_branch_value(...)` (sets.py:908); `_normalize_input`'s active-field walk -> `iter_active_fields(cls, input_value, config)` (sets.py:706); `_run_permission_checks`'s gate core -> `run_active_input_permission_checks(...)` (sets.py:1203-1210); `_active_permission_field_paths` -> `active_permission_field_paths(...)` (sets.py:1280-1288); `_invoke_permission_method` -> `invoke_permission_method(...)` (sets.py:1261); visibility derive -> `apply_type_visibility_sync` / `apply_type_visibility_async` (sets.py:986, 1005); the lifecycle-attr names + cache/guard via `SetLifecycleAttrs` + `expanded_once` (sets.py:246-250, 368-374); RelatedFilter collection via `collect_related_declarations` (sets.py:177-184). All single-sited with the order twin.
- **New helpers considered.** `_raise_logic_depth_exceeded` (sets.py:1010-1022) is itself the act-now consolidation of the depth-cap message across `_collect_nested_visibility_querysets_async`, `_run_permission_checks`, and `_evaluate_logic_tree` — already extracted. `_apply_common_prelude` / `_apply_common_finalize` (sets.py:1633-1673) already collapse the sync/async shared body to one site each; the async-only `_nested_qs_by_branch_id` stash correctly stays inline in `apply_async` (no sync analog). No further helper warranted.
- **Duplication risk in the current file.** The `and` / `or` / `not` three-branch unrolled loops recur in `_collect_nested_visibility_querysets_async`, `_run_permission_checks`, and `_evaluate_logic_tree`, but each unrolls differently (async derive vs perm recursion vs `Q` `&`/`|`/`~` composition with the `or` arm needing its own accumulator and `not` negated) — a shared iterator would obscure the per-branch operator semantics. Correct as intentional sibling shape. The two-call-site fan-out of every delegate (FilterSet here + OrderSet twin) is the deliberate two-family design, not a near-copy.

### Other positives

- **Denial-before-filter ordering holds.** `apply_sync` -> `_apply_common_finalize` runs `_run_permission_checks(input_value, request)` and `_validate_form_or_raise` BEFORE the `.qs` read (sets.py:1671-1673), so a permission denial raises before the queryset materializes. `_run_permission_checks` itself recurses into logical branches (sets.py:1215-1243) and `run_active_input_permission_checks` recurses into child RelatedFilter sets, so every nested gate fires pre-`.qs`. The async path routes the identical `_apply_common_finalize` through `sync_to_async(thread_sensitive=True)` (sets.py:1745) — same ordering, off-loop.
- **Queryset-as-scope-boundary is airtight.** `_iter_visibility_steps` (sets.py:911-955) raises `ConfigurationError` for an ACTIVE related branch whose target type / child filterset cannot resolve, rather than skipping it — the load-bearing "skipping silently returns unfiltered rows" guard. `_target_type_for_related_filter` (sets.py:1099-1126) prefers the child filterset's bound `_owner_definition.origin` over a model-only `registry.primary_for` lookup, closing the documented multi-DjangoType silent row-leak (wrong `get_queryset` against a non-primary's filterset).
- **ORM correctness.** `_apply_related_constraints` wraps each branch as `pk__in=<parent-pk subquery>` (sets.py:1626-1629) to collapse many-side JOIN duplicates without `.distinct()` (no consumer-visible queryset mutation), keys the final `.filter()` on `related_filter.field_name` (the ORM accessor) not the declared attr name, and derives the subquery from `constrained` itself so the DB alias / custom-manager scoping carry through. The explicit-`queryset=` × child-qs mixed-model case raises a typed `ConfigurationError` via `is`-identity model comparison mirroring Django's own `Query.combine` (sets.py:1584-1596).
- **Caches are clear-hook-correct.** `_lookups_for_field_class_cache` keys on the Django field CLASS (stable across `registry.clear()`, which never recreates Django field classes) so it needs no clear hook — documented (sets.py:71-78); `_lookups_for_field` returns a `list(cached)` copy so a mutating caller cannot corrupt it. `_FORM_KEY_BY_PYTHON_ATTR` built once at import from a `reversed` view so first-match-wins parity holds (sets.py:85-88).
- **Reentrancy / cycle safety.** `get_filters`'s `cls.__dict__`-based guard (not `getattr`) prevents a subclass inheriting a parent's `_expanded_filters` and prevents the in-flight metaclass class caching a half-built result (sets.py:298-374); the single-threaded contract is documented with an explicit "do not introduce `threading.local` without a real consumer call path" trigger.
- **Test discipline.** Both `check_permissions` entry paths (explicit `requested_fields` and active-input fallback) are pinned (`tests/filters/test_sets.py:1424`, `:1811`); the file's apply pipeline, Relay-vs-scalar conditional, depth cap, and nested-branch visibility are exercised through the example app and package tests.

### Summary

`filters/sets.py` is the spec-027 FilterSet declaration + apply pipeline — a large (1776-line) but maximally-factored module whose every traversal, permission, and visibility primitive delegates to a single-sited shared helper, with the only sync/async divergence collapsed through `_apply_common_prelude` / `_apply_common_finalize`. The security-critical invariants all hold: permission denial fires before `.qs` materialization on both paths; an active-but-unresolvable RelatedFilter branch raises rather than silently widening; visibility scoping prefers the bound owner type over a model-only registry lookup (closing the multi-type row-leak); and the `pk__in` subquery shape avoids both JOIN-duplicate corruption and consumer-visible `.distinct()` mutation. The cycle diff against the baseline is empty (standing-code re-review). No High, no Medium, one no-action Low recorded only to pre-empt re-flagging of the documented async stash-miss defensive fallback. Qualifies as a no-findings + no-source-edit cycle (shapes #1 -> #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 267 files left unchanged.
- `uv run ruff check --fix .` — pass; All checks passed (COM812/formatter-conflict warning is pre-existing config noise, not a result).

### Notes for Worker 3
- Single Low is no-action (documented async stash-miss defensive fallback in `_q_for_branch`); forward-looking re-examination trigger stated inline. No edit warranted.
- No GLOSSARY-only fix in scope: GLOSSARY entries for `FilterSet` (482-492), `RelatedFilter` (1010-1018), `Meta.filterset_class` (688-701), `SyncMisuseError` (1295-1299) all verified accurate against source — no drift.
- Cycle diff `git diff 6f290c21c630ffb25fb41ce5eac2acac6cac90bb -- django_strawberry_framework/filters/sets.py` is EMPTY (file unchanged since baseline; standing-code re-review).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits warranted — docstrings are accurate and load-bearing (notably the `_q_for_branch` fallback rationale, the `pk__in`-vs-direct-JOIN dedup note, and the `get_filters` `cls.__dict__`-guard reasoning all match the implementation).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_10.md` is silent on changelog edits for review cycles).

---

## Verification (Worker 3)

### Logic verification outcome
No-findings + no-source-edit cycle (shape #5). High 0 / Medium 0 / Low 1 — verified each independently against source, not the artifact prose.

Re-derived the four security invariants the dispatch named:

- **(a) Denial-before-filter ordering on BOTH paths.** `_apply_common_finalize` (sets.py:1671-1673) runs `_run_permission_checks` -> `_validate_form_or_raise` -> `filterset_instance.qs` in that order; the `.qs` read is the final statement, so a permission denial or invalid-form error raises before the queryset materializes. `apply_sync` (sets.py:1697) calls `_apply_common_finalize` directly; `apply_async` (sets.py:1745) wraps the SAME `_apply_common_finalize` in `sync_to_async(thread_sensitive=True)` — identical ordering off-loop. Confirmed.
- **(b) `_iter_visibility_steps` raises, not skips, an unresolvable active branch.** sets.py:937-952 — `if target_type is None or child_filterset is None:` raises `ConfigurationError` (no `continue`). An ACTIVE related branch (consumer supplied input) cannot silently drop its constraint and return unfiltered parent rows. Confirmed.
- **(c) `_target_type_for_related_filter` prefers bound owner over model-only registry lookup.** sets.py:1118-1126 — reads `child_filterset._owner_definition` -> `child_owner.origin`, returns `owner_type` when non-None; only the unbound case falls to `registry.primary_for(child_model) or registry.get(child_model)`. Closes the multi-DjangoType silent row-leak (model-only lookup would run the PRIMARY type's `get_queryset` against a non-primary's filterset). Confirmed.
- **(d) `pk__in` subquery dedup without consumer-visible `.distinct()`.** sets.py:1626-1629 — `matching_parent_pks = constrained.filter(**{f"{related_filter.field_name}__in": intersected}).values("pk")` then `constrained.filter(pk__in=matching_parent_pks)`. No `.distinct()` anywhere in the file. Keys on `related_filter.field_name` (ORM accessor, not the declared attr name); subquery derives from `constrained` itself so DB alias / custom-manager scoping carry through. Confirmed.

The single Low (`_q_for_branch` async stash-miss sync-derive fallback, sets.py:1517-1530) is genuinely no-action: the async pre-walk `_collect_nested_visibility_querysets_async` (sets.py:1068-1095) enumerates every `and`/`or`/`not` child via the same `_LOGIC_KEYS` dual-key (`and_`/`and`) `_extract_branch_value` logic that `_evaluate_logic_tree` (sets.py:1422-1456) later descends, and stashes each by `id(child_input)` (object identity preserved through `_normalize_input`'s verbatim dict copy). So on the production async path `_nested_qs_by_branch_id.get(id(child_input))` is always populated for any branch the sync descent visits; the sync-derive fallback is reachable only for a direct `_q_for_branch` caller that bypasses the pre-walk. The forward-looking re-examination trigger (re-flag if the two walkers' branch-enumeration ever diverges) is correctly stated inline. `_LOGIC_KEYS` definition confirmed at inputs.py:130. No fix warranted.

### DRY findings disposition
DRY = None, sound. Every traversal/permission/visibility primitive is a thin single-sited delegate to `utils/permissions.py` / `utils/input_values.py` / `utils/querysets.py` / `sets_mixins.py`; the only sync/async divergence is already collapsed through `_apply_common_prelude` / `_apply_common_finalize` with the async-only `_nested_qs_by_branch_id` stash correctly inline. The same-named order-family twins are the deliberate two-family design (deferred-with-trigger in the cycle-11/12 artifacts), not duplication. No act-now opportunity unique to this file.

### Temp test verification
- None — no behavioral suspicion to prove; the Low is unreachable-by-inspection and verifiable from source + the two walkers' enumeration logic.
- Disposition: n/a.

### Shape #5 gate confirmation
1. `git diff 6f290c21c630ffb25fb41ce5eac2acac6cac90bb -- django_strawberry_framework/filters/sets.py` is EMPTY; `git diff --stat <baseline> -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` is EMPTY over owned paths. Dirty working-tree files (`__init__.py`, `dicta.md`, `pyproject.toml`, `uv.lock`) are diff-empty vs the baseline SHA — pre-baseline / concurrent-maintainer (AGENTS.md #33), not this item's edits.
2. Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` — confirmed.
3. The single Low carries verbatim trigger phrasing; no GLOSSARY-only fix in scope (Worker 2's four GLOSSARY entries verified, no source drift).
4. Changelog `Not warranted` cites BOTH AGENTS.md and the active plan's silence; `git diff -- CHANGELOG.md` empty.
5. `uv run ruff format --check` -> "1 file already formatted"; `uv run ruff check` -> "All checks passed!" (COM812 warning is documented pre-existing config noise).

Shadow overview (`docs/shadow/django_strawberry_framework__filters__sets.overview.md`) matches source: 41 symbols, 1 TODO (anchored `Meta.search_fields` future-wiring, sets.py:344), 4 benign repeated literals. Both `check_permissions` test pins exist at the cited lines (`tests/filters/test_sets.py:1424` explicit `requested_fields`, `:1811` active-input fallback).

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `filters/sets.py` checklist box in `docs/review/review-0_0_10.md`.
