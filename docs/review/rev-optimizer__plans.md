# Review: `django_strawberry_framework/optimizer/plans.py`

Status: verified

## DRY analysis

- None — the file already single-sources every duplication-prone seam. `_lookup_path` / `_lookup_paths_from_parts` / `_prefetch_lookup_paths` centralize the brittle Django-private `prefetch_to` contract (the only repeated literal, `prefetch_to`, is the Django attribute name surfaced through `getattr`, intentionally re-spelled at `_lookup_path` and `_prefetch_lookup_paths` where each reads a *different* object shape). `_IndexedList` + the three module-level `append_unique*` shims are the one dedupe discipline shared with the walker (`walker.py` imports `append_unique` / `append_unique_many`). `ends_in_unique_column` / `deterministic_order` are explicitly hoisted here so `connection.py` imports them *back* (cursor-parity invariant, spec-033 Decision 11) — that is the resolution of a cross-module duplication, not a new candidate. `_dst_*` window constants are single-sourced and consumed by `connection.py` / `walker.py`.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_IndexedList.append_unique` + module-level `append_unique` / `append_unique_many` / `append_prefetch_unique` (`plans.py:353-389`) are the one plan-shape dedupe discipline, imported by `optimizer/walker.py:27-37` (`append_unique`, `append_unique_many`) rather than re-spelled — confirmed by grep. `relation_kind` is reused from `utils/relations.py` (`plans.py:45`, `:565`) instead of re-deriving relation taxonomy. `OptimizerError` is the shared optimizer exception (`plans.py:44`, raised at `:567`/`:575`).
- **New helpers considered.** No new helper is warranted at this granularity. `_lookup_path` (`plans.py:53-60`) and the recursive `_prefetch_lookup_paths` (`plans.py:849-866`) already abstract the only candidate (the Django `prefetch_to` private contract); folding them further would couple the flat first-seen-path dedupe to the recursive nested-tree flatten, which read distinct object shapes.
- **Duplication risk in the current file.** The static overview flags `prefetch_to` (2x) and `queryset` (2x) as repeated literals. Both are Django private-attribute names surfaced via `getattr` at sites that inspect different objects (`_lookup_path` reads a plan/consumer entry; `_prefetch_lookup_paths` reads a nested `Prefetch`); they are intentional sibling reads of the same Django contract, already centralized where it matters, not accidental copies.

### Other positives

- **Copy-never-mutate cache discipline is airtight.** `finalize()` (`plans.py:206-236`) and `diff_plan_for_queryset` (`plans.py:691-768`) both go through `dataclasses.replace`; `finalize()` is idempotent (re-finalising tuple-backed fields is a no-op) and `diff_plan_for_queryset` returns the *original* `(plan, queryset)` unchanged when nothing was dropped (`plans.py:753-759`), so a cache-hit plan is never copied unnecessarily and never mutated in place — matches the GLOSSARY "Cache immutability" contract.
- **`finalized_*` frozensets are derived from one source.** `finalize()` builds `finalized_lookup_paths` from `_lookup_paths_from_parts(select_related, prefetch_related)` (`plans.py:233-235`); `lookup_paths()` (`plans.py:832-836`) returns the finalized set when present and falls back to recomputing from the same helper, so the cache-hit and construction-time paths cannot drift. `extension.py:982-989` consumes exactly this fallback pattern (`finalized_planned_resolver_keys` else `frozenset(plan.planned_resolver_keys)`).
- **`window_partition_for_prefetch` fails loud, not silent.** Raises `OptimizerError` for a non-windowable relation kind or an unresolvable partition (`plans.py:566-578`) so `walker._plan_connection_relation` leaves the selection unplanned and falls back per-parent rather than emitting a wrong partition. Correctly takes the *raw* Django field (the forward-M2M reverse query name lives only on `field.remote_field`, not on `FieldMeta`).
- **`_MAX_PATH_DEPTH` cycle guard is principled.** The 1024 bound on `runtime_path_from_path` (`plans.py:288`, `:307-317`) catches a cyclic/corrupt `prev` chain in fixed iterations while sitting far above any query graphql-core could execute (it recurses one frame per level first) — a NASA-Power-of-Ten Rule-2 bounded loop with a documented rationale, not an arbitrary magic number.
- **`is_empty` semantics are pinned and documented.** Excludes `cacheable` from the emptiness check with the test name cited inline (`test_cacheable_flag_does_not_affect_empty_state`) and a precise trigger condition for revisiting (`plans.py:182-204`).
- **`_reverse_order_by` mirrors Django's `.reverse()`** for both string and `OrderBy`/expression shapes including NULLS-positioning swap (`plans.py:660-688`), keeping the backward-window order parity with the resolve-time `.reverse()` pipeline.
- **Defensive `getattr` style is consistent** across consumer-queryset introspection (`_consumer_prefetch_lookups`, `_consumer_only_fields`, `_diff_select_related`) with each paranoid guard's reachability documented (e.g. the `or ()` dead-code-under-real-QuerySet note at `plans.py:392-407`).

### Summary

`plans.py` is the `OptimizationPlan` data shape plus the plan-mutation, finalize/diff, and windowed-prefetch helpers the walker emits and the extension/connection consume. Plan structure, the copy-never-mutate finalize/replace cache invariant, the `append_unique*` merge discipline, and `window_partition_for_prefetch` all verify correct against the source and against every cross-module consumer (`walker.py`, `extension.py`, `connection.py`, `types/resolvers.py`). The cycle diff is empty against both the per-cycle baseline (`b16dde4a`) and HEAD; GLOSSARY prose for the contract-level symbols (`OptimizationPlan.apply` under multi-DB cooperation, `fk_id_elisions` on the plan, cacheable/request-scope safety, the `_dst_*` window annotations) is accurate and abstracts correctly over the internals. No High/Medium/Low findings; no DRY candidates. Genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (289 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3
- Cycle diff empty against both baseline `b16dde4a13859cfdf606fee34a4b809393338df5` and HEAD (`git diff` both empty).
- Zero findings (High/Medium/Low all `None.`), zero DRY candidates.
- No GLOSSARY-only fix in scope — the contract-level GLOSSARY prose for `OptimizationPlan.apply`, `fk_id_elisions`, cacheable/request-scope safety, and the `_dst_*` annotations is accurate; the file's other public symbols (`window_partition_for_prefetch`, `deterministic_order`, `ends_in_unique_column`, `resolver_key`, `runtime_path_from_*`, `diff_plan_for_queryset`, `lookup_paths`) are internal optimizer symbols with no `__all__` export and correctly carry no GLOSSARY entry.
- Cross-module load-bearing claims re-verified by grep: `connection.py` imports `deterministic_order` / `ends_in_unique_column` back (`:64-65`, alias `:91`, call `:833`); `walker.py` consumes `window_partition_for_prefetch` (`:1379`) + `apply_window_pagination` (`:1437`) + `append_unique*`; `extension.py` reads `finalized_*` with construction-time fallback (`:982-989`).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits. Docstrings and the two block comments (`_MAX_PATH_DEPTH` rationale at `plans.py:277-287`; `_dst_*` namespace rationale at `plans.py:471-475`) are accurate, non-restating, and TODO-free (static overview: 0 TODO comments). The inline cross-module claims ("`connection.py` imports this back", spec-033 Decision references) were grep-verified accurate.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source edit this cycle (review-only). Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_11.md`) which is silent on changelog edits for review cycles.

---

## Verification (Worker 3)

### Logic verification outcome
All findings are `None.` (High/Medium/Low) — a genuine no-source-edit cycle. Independently confirmed each load-bearing positive claim:

- **Zero-edit proof (shape #5).** `git diff b16dde4a13859cfdf606fee34a4b809393338df5 -- django_strawberry_framework/optimizer/plans.py` empty; `git diff HEAD -- <target>` empty; owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) empty; target absent from `git status --porcelain`. No sibling-cycle attribution needed (clean stat). `git diff -- CHANGELOG.md` empty.
- **Each Worker 2 section** opens `Filled by Worker 1 per no-source-edit cycle pattern.` — gate satisfied.
- **Copy-never-mutate finalize/diff invariant.** `finalize()` (`plans.py::OptimizationPlan.finalize`) routes through `dataclasses.replace`; idempotent (re-finalising tuple-backed fields is a no-op) — pinned by `test_finalize_is_idempotent`. `diff_plan_for_queryset` returns the *original* `(plan, queryset)` unchanged on the no-op path (`plans.py #"return plan, queryset"`) — doubly pinned: `test_returns_same_instances_when_nothing_to_drop` asserts `delta_plan is plan` AND `delta_qs is qs`; `test_drops_select_related_already_on_queryset` asserts the dropped-entry path returns a NEW plan (`delta_plan is not plan`) while the original list stays `["category"]` (the B1 cross-request cache-isolation canary).
- **`append_unique*` merge discipline.** `walker.py:30-31` imports `append_unique` / `append_unique_many` from `plans.py` (consumed at `:406/:418/:515/:517/:571/:613`) rather than re-spelling — confirmed by grep. `_IndexedList.append_unique` sidecar-index dedupe + the three module shims (`append_unique` / `append_unique_many` / `append_prefetch_unique`) are the single plan-shape dedupe discipline.
- **`window_partition_for_prefetch`.** Both fail-loud arms test-pinned: forward-single-FK raises `OptimizerError` matching "no windowable parent partition" (`test_forward_single_relation_raises`); malformed windowable descriptor with no resolvable partition raises matching "could not resolve a parent partition" (`test_windowable_kind_without_remote_field_keys_raises`). Forward-M2M divergence (partition = reverse query name `"books"`, NOT accessor `"genres"`) read off `field.remote_field` — pinned by `test_forward_m2m_partition_diverges_from_accessor`. Correctly takes the raw Django field.

### DRY findings disposition
DRY analysis is `None`. Independently confirmed the "this file IS the DRY resolution" claims: `append_unique` / `append_unique_many` have exactly one importing consumer chain (`walker.py`), `deterministic_order` / `ends_in_unique_column` are hoisted here and imported BACK by `connection.py:64-65` (alias `_ends_in_unique_column` at `:91`, call at `:833`) — the spec-033 Decision 11 cursor-parity resolution, not a new candidate. The `prefetch_to` literal is the Django private-attribute name surfaced via `getattr` at two distinct object shapes (`_lookup_path` vs `_prefetch_lookup_paths`) — intentional sibling reads, already centralized.

Content-not-identifier note (#27): the artifact references `connection.py` by bare name; the file lives at the package root (`django_strawberry_framework/connection.py`), not under `optimizer/`. The path label is cosmetic; the load-bearing import-back claim was verified against live source by grepping the quoted symbols.

### Temp test verification
- No temp tests required — the existing permanent suite (`tests/optimizer/test_plans.py`) already pins every claimed invariant.
- Disposition: none created.

### #4-vs-#5 gate (GLOSSARY plan-contract prose)
Genuine #5, not a missed #4. GLOSSARY prose for the contract-level symbols verified accurate vs live source: `OptimizationPlan.apply` under Multi-database cooperation (`.using(alias)` `_db` preservation, axis 2; request-scope cacheable, the "Request-scope safety" line), `fk_id_elisions` on the plan (`info.context` tuple + standalone set), the `_dst_row_number` / `_dst_total_count` window annotations (the windowed-connection fast-path prose). The file's other public symbols (`window_partition_for_prefetch`, `deterministic_order`, `ends_in_unique_column`, `resolver_key`, `runtime_path_from_*`, `diff_plan_for_queryset`, `lookup_paths`) are internal optimizer symbols (no `__all__` in `plans.py`, confirmed by grep) and correctly carry no GLOSSARY entry — absence is not drift. No GLOSSARY-only fix in scope (would be disqualifying).

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `optimizer/plans.py` checklist box in `docs/review/review-0_0_11.md`.
