# Review: `django_strawberry_framework/filters/sets.py`

Status: verified

## DRY analysis

- **Defer-with-trigger — sync/async visibility-derive sibling pair.** `FilterSet._derive_related_visibility_querysets_sync` (`filters/sets.py:974-1004`) and `_derive_related_visibility_querysets_async` (`filters/sets.py:1007-1023`) share the `_iter_visibility_steps` driver and differ only by `apply_type_visibility_sync` + `child_filterset.apply_sync` vs the `await`ed async pair. Collapsing into one maybe-await helper would reintroduce coroutine-color ambiguity (the sync path must raise `SyncMisuseError` synchronously, the async path must `await` before raise) and is exactly the shape the `connection.py` review flagged as the wrong consolidation. **Defer until a maybe-await primitive is introduced package-wide** (the same trigger the connection `_attach_count_sync/_async` pair carries); do not act now.
- **Defer-with-trigger — filter/order apply-pipeline family mirror.** The whole `_run_permission_checks` / `_active_permission_targets` / `_iter_active_related_branches` / `_request_from_info` / `_extract_branch_value` / `_iter_input_items` set already bottoms out in single-sited `utils/permissions.py` cores (`run_active_input_permission_checks`, `active_permission_targets`, `active_related_branches`, `request_from_info`, `extract_branch_value`, `iter_input_items`); the local methods are thin family-config wrappers. The remaining near-duplication is the *apply-pipeline scaffold* (`apply_sync` / `apply_async` / `apply` + `_apply_common_prelude` / `_apply_common_finalize`) shared structurally with `orders/sets.py`. **Defer to the `rev-filters.md` folder pass and `rev-django_strawberry_framework.md` project pass** (cross-family, cross-module); the GLOSSARY (`docs/GLOSSARY.md:971`) already pins the filter/order apply-pair parity as intentional sibling design, so this is forward-looking, not act-now. Trigger: a third `*Set.apply_*` family (e.g. `AggregateSet`) landing — then fold the prelude/finalize/dispatch scaffold through a shared mixin.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The apply pipeline's shared steps are single-sited: permission gates route through `utils/permissions.py::run_active_input_permission_checks` (`filters/sets.py:1219`) / `active_permission_targets` (`:1312`) / `invoke_permission_method` (`:1277`); request resolution through `request_from_info` (`:882`); input traversal through `utils/input_values.py::iter_active_fields` (`:722`) with the module-singleton `_NORMALIZE_TRAVERSAL` (`:100-105`); related-branch listing through `active_related_branches` (`:906`); branch-value extraction through `extract_branch_value` (`:924`); the cardinality classifier through `utils/relations.py::is_many_side_relation_kind(relation_kind(...))` (`:621`); the expansion cache/guard through `sets_mixins.expanded_once` (`:385-391`) keyed off the `SetLifecycleAttrs` descriptor (`:263-267`); related-declaration collection through `sets_mixins.collect_related_declarations` (`:194-201`); and sync-misuse routing through `utils/querysets.py::apply_type_visibility_sync` / `_async`. The depth-cap message is single-sourced in `_raise_logic_depth_exceeded` (`:1026-1038`); the prelude/finalize split (`_apply_common_prelude` `:1662`, `_apply_common_finalize` `:1685`) already dedupes the sync/async apply bodies.
- **New helpers considered.** A unified maybe-await visibility-derive helper was evaluated and rejected (coroutine-color hazard; the sync path's synchronous `SyncMisuseError` raise is load-bearing for `apply`'s catch-rethrow contract). Hoisting the reverse-map (`_FORM_KEY_BY_PYTHON_ATTR` `:86-89`) and the wire-key map (`_LOGIC_WIRE_BY_PYTHON_ATTR` `:94`) to import-time is already done (feedback L2).
- **Duplication risk in the current file.** The `and` / `or` / `not` branch handling repeats across `_run_permission_checks` (`:1231-1259`), `_evaluate_logic_tree` (`:1451-1485`), and `_collect_nested_visibility_querysets_async` (`:1084-1111`). This is intentional sibling design, not extractable: each walk does different work per arm (permission recursion vs `Q`-composition vs visibility pre-derive), and `_evaluate_logic_tree`'s `or`-group builds an OR-disjunction (`or_q |= ...`) while the other two iterate arms independently. The 6x `related_filters` / 3x `FilterSet` / 2x `_owner_definition` / 2x `is_relation` repeated literals (overview "Repeated string literals") are distinct attribute/config references, not consolidation candidates.

### Other positives

- **Correctness of the `or`-group guard.** `_evaluate_logic_tree` (`:1462-1474`) builds the OR sub-`Q` only when `or_branches` is non-empty, so an empty `or: []` does not collapse to `q &= Q()` (a no-op anyway) — and never to a match-nothing predicate. `and` (`:1451`) and `not` (`:1476`) are empty-safe by `.get(...) or []` / `is not None` guards. Empty `Q()` is the correct identity for `qs.filter(...)`.
- **`pk__in` subquery de-duplication.** `_apply_related_constraints` (`:1655-1658`) wraps the many-side relation restriction as `pk__in=<parent-pk subquery>` rather than a direct `<rel>__in=` JOIN, avoiding duplicate parent rows in lists/connections without a consumer-visible `.distinct()` mutation — and matches the `Q(pk__in=...)` shape `_q_for_branch` (`:1567`) emits, so a related branch answers identically directly or nested under logic. The declared-name-vs-ORM-path divergence (`related_filter.field_name`, `:1656`) is handled with a load-bearing comment.
- **Typed-error discipline.** Mixed-model `RelatedFilter(queryset=...)` raises a typed `ConfigurationError` naming both models (`:1613-1625`) instead of Django's opaque `TypeError` from `Query.combine`; the `is`-identity comparison correctly mirrors Django's own `self.model != rhs.model` (proxies / MTI children carry distinct identities). Unresolvable active branches raise rather than silently dropping the constraint (`_iter_visibility_steps` `:961-968`). Unsupported own-PK GlobalID lookups raise (`filter_for_lookup` `:563-567`). The depth cap surfaces a typed `ConfigurationError` (`:1034-1038`) instead of a Python `RecursionError`.
- **Async-only `get_queryset` safety.** `_collect_nested_visibility_querysets_async` (`:1041-1112`) pre-walks every logical arm and awaits each branch's visibility map keyed by `id(child_input)` BEFORE the sync `.qs` read, so `_q_for_branch` (`:1546-1559`) consults the stash instead of the sync derive that would raise `SyncMisuseError` mid-`.qs`. The defensive sync fallback for direct `_q_for_branch` callers is documented and correct. The `_apply_common_finalize` wrap in `sync_to_async(thread_sensitive=True)` (`:1774`) keeps consumer sync hooks off the event loop, mirroring Django's own async-path wrapping.
- **Cache safety.** `_lookups_for_field_class_cache` (`:79`) is keyed by Django field *class* (MRO-stable, survives `registry.clear()`), needs no clear hook, and returns a `list(cached)` copy (`:158`) so a mutating caller cannot corrupt the memo. `get_filters`'s `cls.__dict__`-based guard (`:372`) correctly avoids inheriting a parent's completed cache and avoids caching a half-built result during metaclass-driven creation.
- **GLOSSARY fidelity.** `docs/GLOSSARY.md` is current against every public symbol: `FilterSet` (`:511-519`) matches the `apply_sync`/`apply_async`/`form.is_valid()`/`GraphQLError(extensions={"code":"FILTER_INVALID",...})` contract and the `IS a BaseFilterSet subclass` claim; `check_*_permission` active-input-only scope and explicit-`queryset=` filter-scope (`:515`, `:1049`); `RelatedFilter` (`:1043-1051`); `Meta.filterset_class` phase-2.5 owner binding (`:719-723`); `Meta.search_fields` planned-`0.1.2` (matches the TODO at `:361`); `SyncMisuseError` rewrap by `FilterSet.apply` (`:1332`). No drift.

### Summary

`filters/sets.py` is byte-identical to both the per-cycle baseline (`298690ae`) and `HEAD` — `git diff` empty on both. The maintainer's recent edit to this file is already captured in `HEAD`, so there is no pending change to scope this cycle. The largest filters file remains a disciplined Layer-3/4 + apply-pipeline implementation: every shared concern (permission core, input traversal, cardinality classifier, expansion cache, sync-misuse routing, depth-cap message) routes through a canonical single-sited helper; the sync/async visibility-derive pair and the cross-family apply scaffold are intentional sibling designs deferred with explicit triggers. No High/Medium/Low findings. GLOSSARY prose for every public symbol is accurate. Genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `289 files left unchanged`.
- `uv run ruff check --fix .` — pass; `All checks passed!`.

### Notes for Worker 3
- `git diff 298690aecf51ecfaa917e58cffd3d411fe18d2e4 -- django_strawberry_framework/filters/sets.py` and `git diff HEAD -- django_strawberry_framework/filters/sets.py` both empty (0 lines) — confirmed twice. The file is unchanged this cycle; the maintainer edit named in the dispatch is already in HEAD.
- Static overview regenerated this cycle (`docs/shadow/django_strawberry_framework__filters__sets.overview.md` + `.stripped.py`) per the REVIEW.md `filters/` mandate; shadow is gitignored, not an edit.
- Two DRY bullets, both defer-with-trigger (sync/async visibility-derive pair; cross-family apply-pipeline scaffold forwarded to `rev-filters.md` + `rev-django_strawberry_framework.md`). Neither is act-now.
- No GLOSSARY-only fix in scope. `docs/GLOSSARY.md` is dirty in the working tree, but that pending edit is the `apps.py`/AppConfig patch-modules entry (`docs/GLOSSARY.md:308`) from a prior cycle's apps.py Medium — it touches no FilterSet symbol. Every `filters/sets.py` public symbol's GLOSSARY prose is accurate (`FilterSet` `:511-519`, `RelatedFilter` `:1043-1051`, `Meta.filterset_class` `:719-723`, `Meta.search_fields` `:898-902`, `SyncMisuseError` `:1331-1332`).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

Logic-first review surfaced no findings, so no comment/docstring changes are warranted. The file's docstrings are dense and accurate: the module docstring correctly states it IS a `BaseFilterSet` subclass and names the spec-027 layers; the `get_filters` single-threaded contract, the `_q_for_branch` perf note, the `_apply_related_constraints` `pk__in`-vs-JOIN rationale, and the `_collect_nested_visibility_querysets_async` async-only-`get_queryset` explanation all match the implementation. The lone TODO (`:361`, `Meta.search_fields` card `0.1.2`) is a live, correctly-anchored deferral matching GLOSSARY `:898-902`.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source, test, GLOSSARY, or behavior change this cycle (empty diff vs baseline and HEAD), so there is nothing to record per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_11.md`) prescribes no changelog action for a review-only no-op cycle.

---

## Verification (Worker 3)

Shape #5 no-source-edit cycle, terminal-verify.

### Zero-edit proof
- `git diff 298690aecf51ecfaa917e58cffd3d411fe18d2e4 -- django_strawberry_framework/filters/sets.py` empty; `git diff HEAD -- django_strawberry_framework/filters/sets.py` empty. File byte-identical to both baseline and HEAD.
- `git diff --stat 298690ae -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty this run — fully clean owned-paths stat, no sibling-cycle dirt and no #33 concurrent hunk to attribute. `filters/sets.py` absent from the stat.
- Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern." (Fix report, Comment/docstring pass, Changelog disposition). Confirmed.
- `uv run ruff format --check .` — 289 files already formatted. `uv run ruff check .` — All checks passed.

### Logic verification outcome
All High / Medium / Low are `None.`; independently confirmed genuine, not a skipped defect, by reading the file's substantial surfaces:
- **Metaclass collection** (`FilterSetMetaclass.__new__` `:170-194`): routes related-declaration collection through the shared `sets_mixins.collect_related_declarations` chokepoint (`:194`); no parallel collection logic.
- **`get_filters` cache** (`:354-391`): the `"related_filters" in cls.__dict__` guard (`:372`) avoids caching a parent's completed cache or a half-built result; `expanded_once` reentry returns the unexpanded `super().get_filters` so a self-referential `RelatedFilter` neither recurses infinitely nor caches a partial.
- **Meta validation / GlobalID own-PK** (`:556-567`): unsupported own-PK lookups (anything outside `exact`/`in`/`isnull`) raise a typed `ConfigurationError` naming the field, not Django's opaque default.
- **Sync vs async visibility-derive** (`:973-1023`): the pair shares the `_iter_visibility_steps` driver and differs only by `apply_type_visibility_sync` + `apply_sync` vs the awaited async pair. The sync path's synchronous `SyncMisuseError` raise (via `apply_type_visibility_sync`) is load-bearing for `apply`'s catch-and-rethrow contract (`:1795-1804`, `RuntimeError` with "use apply_async instead") — a maybe-await collapse would reintroduce coroutine-color hazard. Defer correct.
- **Per-field `check_*_permission` active-input-only scope** (`:1218-1259`): `run_active_input_permission_checks` keys on the source field (one fire per field across all lookups); logical `and`/`or`/`not` recurse separately with shared `_fired` dedup; depth-capped via `_raise_logic_depth_exceeded`. Active-input-only + dedup + depth-cap + "checks run only through apply entrypoint" are each pinned by named tests in `tests/filters/test_sets.py` (`test_run_permission_checks_fires_only_for_active_input_fields` :580, `_skips_unset_related_branch` :598, `_recurses_into_active_related_branch` :633, `_recurses_into_logical_branches` :661, `_dedups_child_gate_across_sibling_branches` :712, `_caps_logical_branch_nesting` :755, `test_permission_checks_run_only_through_apply_entrypoint` :860, `_short_circuits_on_none_and_unset` :1404).
- **Optimizer / get_queryset composition** (`:1661-1804`): `_apply_common_prelude`/`_apply_common_finalize` dedup the sync/async apply bodies; `apply_async` awaits the top-level + nested visibility derives BEFORE the `.qs` read then routes finalize through one `sync_to_async(thread_sensitive=True)` (`:1774`); `_apply_related_constraints` wraps the many-side restriction as `pk__in=<parent-pk subquery>` (`:1655-1658`) to de-dup parent rows without a consumer-visible `.distinct()`. All consistent with the artifact.

No false-premise rejections to verify (zero findings).

### DRY findings disposition
Two DRY items, both correctly **defer-with-trigger**, neither act-now:
1. Sync/async visibility-derive sibling pair — deferred until a package-wide maybe-await primitive lands (same trigger as connection.py's `_attach_count_sync/_async`). The coroutine-color hazard is real (verified: sync path's synchronous raise is load-bearing for the `apply` catch-rethrow contract). Correct.
2. Cross-family apply-pipeline scaffold (`apply_sync`/`apply_async`/`apply` + prelude/finalize shared structurally with `orders/sets.py`) — forwarded to the `rev-filters.md` folder pass and `rev-django_strawberry_framework.md` project pass; trigger is a third `*Set.apply_*` family (e.g. `AggregateSet`). GLOSSARY pins the filter/order apply-pair parity as intentional sibling design. Correct cross-module deferral.

### Temp test verification
- None — no temp tests needed; zero-edit cycle verified against live source and the existing permanent suite (`tests/filters/test_sets.py`).
- Disposition: n/a.

### GLOSSARY (#4-vs-#5 gate)
Genuine shape #5, not a missed #4. No GLOSSARY-only fix owed and no drift on filterset public symbols, confirmed by reading the entries against live source:
- `FilterSet` (`:515`): `check_*_permission` **active-input-only scope** and explicit-`queryset=` **filter-scope-not-security** prose matches `run_active_input_permission_checks` (active-input core) and `_apply_related_constraints` (intersect, not a visibility gate). The `apply_sync`/`apply_async` resolver pair, `form.is_valid()`, and `GraphQLError(extensions={"code":"FILTER_INVALID",...})` claims match `_validate_form_or_raise`. The `IS a BaseFilterSet subclass` claim matches the class definition (`:230`).
- `RelatedFilter` (`:1047-1049`), `Meta.filterset_class` (`:723`, phase-2.5 owner binding lives cross-module in `types/finalizer.py` — accurate, out of this file's scope), `Meta.search_fields` planned-`0.1.2` (`:902`, matches the live TODO at `sets.py:361`), `SyncMisuseError` rewrap — all accurate.
- The owned-paths stat was empty this run, so there is no GLOSSARY working-tree hunk to attribute to #33 this cycle.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `filters/sets.py` checklist box in `docs/review/review-0_0_11.md`.
