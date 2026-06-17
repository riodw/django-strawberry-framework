# Review: `django_strawberry_framework/optimizer/extension.py`

Status: verified

Reviewed against current HEAD source (empty this-cycle diff, as expected). Focused
scrutiny on the spec-035 G1 change (commit `d1dea2fd`, `_optimize` evaluated-queryset
guard), plus the prompt-named hotspots: `_stash_union` union-accumulation, the plan
cache, per-request `ContextVar` isolation, and cache-key correctness / mutability.

## DRY analysis

- None — the module already routes every shared mechanism through a single owner:
  the Manager-coercion + is-queryset decision is `utils/querysets.py::normalize_query_source`
  (`extension.py::DjangoOptimizerExtension._optimize` #"normalize_query_source(result)"),
  the stash get/set pair is the `_context.py` helpers re-aliased here
  (`extension.py` #"from ._context import (" import block), the selection-traversal
  primitives are `selections.py` re-aliased under `_`-names
  (`extension.py` #"_child_selections = ast_child_selections"), and the plan-build /
  plan-apply tail is single-sited in `apply_to`, consumed by BOTH the middleware path
  (`_optimize`) and the connection path (`apply_connection_optimization`). The five
  `DST_OPTIMIZER_*` keys are single-sourced in `_context.py`. The four pagination arg
  names are single-sourced in module-level `_PAGINATION_ARG_NAMES`
  (`extension.py` #"_PAGINATION_ARG_NAMES = frozenset"). No remaining duplicated
  literal, near-copy walker, or parallel data flow inside this file.

## High:

None.

## Medium:

None.

## Low:

### Connection path's G1 exemption rests on a slightly imprecise rationale (forward-looking, not a defect in this file)

spec-035 Decision 3 (`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` #"Scope is the
`_optimize` middleware path only") scopes the G1 evaluated-queryset guard to `_optimize`
and exempts the connection path, justifying the exemption as: the connection field's
queryset "is **framework-built** and never consumer-evaluated." That rationale is exact
for the *default* connection resolver (`initial_queryset`), but a consumer-supplied
connection `resolver=` CAN return an already-evaluated queryset, which flows through
`connection.py::_pipeline_sync` → `_finalize_queryset` → `apply_connection_optimization`
→ `apply_to` → `plan.apply(queryset)` (a `.only()` / `select_related` clone that
re-executes evaluated SQL). What actually makes the connection path safe is *upstream of
the optimizer*: `apply_type_visibility_sync` (a `.filter()` clone when `get_queryset`
narrows) and `deterministic_order` (an `.order_by()` clone) already re-execute an evaluated
consumer queryset before `apply_connection_optimization` ever runs, so the re-execution is
structural to the connection pipeline and a G1-style optimizer guard there would not change
the outcome. Net: the scope decision is correct, but the spec's "framework-built" framing
under-describes the consumer-`resolver=` case. No change to `extension.py` is warranted —
this is a doc-precision note. Defer until the connection-pipeline doc or spec-035 is next
revised; then tighten the exemption rationale to "the connection pipeline re-executes an
evaluated consumer queryset at its visibility / order steps regardless, so an optimizer-level
G1 guard is moot there" rather than "never consumer-evaluated."

## What looks solid

### DRY recap

- **Existing patterns reused.** Manager-coercion + is-queryset gate via
  `utils/querysets.py::normalize_query_source` (`_optimize` #"normalize_query_source(result)");
  the stash get/set helpers and the five `DST_OPTIMIZER_*` keys via `_context.py`
  re-aliases (`extension.py` #"from ._context import ("); the selection primitives via
  `selections.py` re-aliases (`extension.py` #"_child_selections = ast_child_selections");
  `runtime_path_from_info` / `lookup_paths` / `diff_plan_for_queryset` via `plans.py`;
  `plan_optimizations` / `plan_relation` via `walker.py`. The plan-build-and-apply tail is
  single-sited in `apply_to` and shared by `_optimize` and `apply_connection_optimization`
  (Decision 11) — no parallel implementation.
- **New helpers considered.** The G1 guard could be hoisted into `apply_to` so both the
  middleware and connection paths share it; rejected, and correctly so — spec-035
  Decision 3 deliberately keeps it in `_optimize` only (the connection path can never be
  reached with a guard-relevant queryset, see the Low above), and hoisting would add a
  per-connection-row `getattr` for zero behavior change.
- **Duplication risk in the current file.** The four "read `plan.finalized_*`, fall back to
  recompute" blocks in `_publish_plan_to_context`
  (`extension.py::DjangoOptimizerExtension._publish_plan_to_context`) and the two
  near-identical "memo lookup or recompute" blocks in `_build_cache_key` (printed-AST memo
  vs pagination-var-names memo) are intentional sibling design: each fallback recomputes a
  *different* quantity (fk-id-elisions / planned-resolver-keys / lookup-paths; doc key vs
  var-name set) through a *different* helper, so a shared mini-helper would only abstract the
  `if x is None: x = recompute()` shape over heterogeneous bodies — net negative readability.
  Leaving them flat is correct.

### Other positives

- **G1 guard placement is load-bearing and tested in both directions.** The
  `getattr(result, "_result_cache", None) is not None` early-return sits AFTER
  `normalize_query_source` (so a coerced `Model.objects.all()` is a fresh unevaluated qs and
  still optimizes) and BEFORE return-type resolution / `apply_to` (so the evaluated qs is
  never cloned). Both directions are pinned:
  `test_optimizer_still_optimizes_manager_after_evaluated_queryset_guard` (Manager path still
  builds a plan, 1 query) vs `test_optimizer_passes_through_consumer_evaluated_queryset`
  (evaluated path, 1 query, 0 plan misses) and the instance-identity pin
  `test_optimize_returns_same_instance_for_evaluated_queryset`. The `is not None` (not
  truthiness) choice correctly handles an evaluated-but-empty queryset whose `_result_cache`
  is `[]`.
- **Async path inherits the guard for free.** `resolve` awaits then calls the same
  `_optimize`, so `_async_optimize` routes the evaluated qs through G1; pinned by
  `test_resolve_async_passes_through_evaluated_queryset` with a `_resolve_model_from_return_type`
  tripwire proving the short-circuit fires before return-type resolution.
- **`_stash_union` is the correct foundation for nested-connection coexistence.** It UNIONs
  correctness sentinels (planned / fk-id-elision / lookup-paths) rather than overwriting, so a
  nested fallback connection pipeline's re-publish does not destroy the parent plan's sets
  (spec-033 Decision 8) — critical under `"warn"` where execution continues past the nested
  connection. `DST_OPTIMIZER_PLAN` is correctly excluded from the union (last-wins
  introspection data, not a correctness sentinel). The `isinstance(existing, (frozenset, set))`
  guard makes a non-set / absent existing value fall back to `new` defensively.
- **Per-request / per-execution isolation is `ContextVar`-based and reset in `finally`.**
  `_optimizer_active`, `_active_optimizer`, `_printed_ast_cache`, `_pagination_var_names_cache`
  are all set in `on_execute` and reset in `finally` in reverse order, so concurrent / async
  executions sharing one extension instance stay isolated. The two memo dicts are keyed by
  `id(operation)` and live only for the execution, with a documented `None`-default fallback
  to recompute when called outside an `on_execute` lifecycle (direct test callers).
- **Plan cache is explicitly correctness-neutral and the race windows are documented.** The
  `move_to_end` LRU promotion is wrapped in `suppress(KeyError)` against a concurrent eviction
  dropping the key between `get` and promotion; the docstring and `cache_info` are honest that
  hit/miss counters and `size` are best-effort under unlocked concurrent access while the cache
  itself can never return wrong data. Plans are only inserted when `plan.cacheable`, and the
  cached plan is never mutated (`diff_plan_for_queryset` returns a fresh plan).
- **Cache key is value-stable, collision-resistant, and hashable by construction.** It stores
  the printed AST string (not its 64-bit hash) to avoid silent hash collisions; appends
  reachable fragment definitions so same-body operations with different fragment bodies key
  apart; includes target model, root response path, and origin type. The variable component is
  narrowed to `@skip`/`@include` (Boolean) and pagination (`first`/`last`/`before`/`after` —
  Int / cursor String) variable names only, all of which are scalar by GraphQL type, so the
  `frozenset` of `(name, value)` pairs can never receive an unhashable list / object variable —
  the narrowing is what makes the frozenset safe, and root pagination is correctly excluded
  (root slicing is post-plan).
- **`check_schema` dedupes multi-type warnings without skipping secondaries.** Keyed on
  `(source_model, field_name)` so multi-type models do not double-warn, while still auditing
  every reachable type (a secondary may expose a relation the primary hides). Always returns,
  never raises — the caller owns the raise/warn decision.

### Summary

The spec-035 G1 change is a minimal, well-placed, well-documented, and fully-tested early
return: it sits exactly between the Manager-coercion gate and the cloning `apply_to` tail,
uses the `is not None` signal upstream uses, and four tests pin the sync optimize / async
optimize / Manager-still-optimizes / instance-identity contracts. The prompt-named hotspots
(`_stash_union` union accumulation, plan-cache interaction, `ContextVar` isolation, cache-key
mutability) are all correct: union-not-overwrite preserves nested-connection sentinels, the
cache is correctness-neutral with documented race windows, memos are per-execution `ContextVar`
dicts reset in `finally`, and the cache key is hashable by construction because the variable
component is narrowed to scalar-typed names. No logic finding. The single Low is a
forward-looking doc-precision note about the connection path's G1 exemption rationale (the
exemption is correct; the spec's "framework-built" wording under-describes the
consumer-`resolver=` case) and warrants no edit to `extension.py`. Landed as a no-source-edit
cycle (shape #5): bare `Status: fix-implemented`, Worker 2 sections filled inline, both
ruff commands run.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 270 files left unchanged.
- `uv run ruff check --fix .` — all checks passed (only the pre-existing
  COM812-vs-formatter config warning, unrelated to this file).

### Notes for Worker 3
- Shadow overview used: `docs/shadow/django_strawberry_framework__optimizer__extension.overview.md`
  (+ `.stripped.py`); not regenerated this cycle (plan-time `--all` sweep, source unchanged
  since baseline `14910230` except the already-reviewed spec-035 commit `d1dea2fd`).
- Low disposition: forward-looking, no edit. It concerns the spec / connection-pipeline doc
  precision, not `extension.py` source; deferred with the explicit trigger "until the
  connection-pipeline doc or spec-035 is next revised." No source change in scope.
- No GLOSSARY-only fix in scope: GLOSSARY lines 419-422 describe G1 as scoped to `_optimize`
  ("if the consumer's root resolver already evaluated the queryset … `_optimize` returns it
  unchanged"), which is accurate to the shipped code — not stale.
- Empty this-cycle diff confirmed (`git diff HEAD -- django_strawberry_framework/optimizer/extension.py`).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring defects: the G1
guard's inline comment and `_optimize` docstring step 3 accurately describe the placement
rationale (after coercion, before clone) and the `is not None`-vs-truthiness choice. No stale
TODOs, no spec references to deleted slices, no docstring promising behavior the code does not
provide.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source edit this cycle (review-only). Per `AGENTS.md` #"Do not update
CHANGELOG.md unless explicitly instructed" and the active plan `docs/review/review-0_0_10.md`
which records no CHANGELOG authorization for this item.

---

## Verification (Worker 3)

Terminal-verify of a no-source-edit cycle (shape #5). Baseline HEAD `5724429c`.
`git diff HEAD -- django_strawberry_framework/optimizer/extension.py` is empty;
the file's only post-`14910230` hunk is the spec-035 G1 commit `d1dea2fd`
(already-shipped contract record per Decision 3 Status line, not this-cycle work).
`git diff -- CHANGELOG.md` empty. Ruff format `--check` = "1 file already
formatted"; ruff `check` = "All checks passed!" (only the pre-existing
COM812-vs-formatter config warning, exactly as the Validation section claims).

### Logic verification outcome

Re-derived each high-risk claim against current-HEAD source, not just the artifact:

- **G1 early-return placement (High-risk, the spec-035 change).** Confirmed at
  `extension.py::DjangoOptimizerExtension._optimize` #"if getattr(result, "_result_cache"":
  the guard sits AFTER `normalize_query_source(result)` (line 787-789) and BEFORE
  `_resolve_model_from_return_type` / `apply_to` (lines 803-811). So a coerced
  `Model.objects` (Manager -> fresh unevaluated `.all()`, `_result_cache is None`)
  still optimizes, while a consumer-evaluated qs short-circuits before the cloning
  tail. `is not None` (not truthiness) correctly passes an evaluated-but-empty qs
  (`_result_cache == []`). `apply_to` would re-execute: it clones via
  `diff_plan_for_queryset` + `plan.apply` (lines 873-874) unless `plan.is_empty`
  (lines 863-864) — so the guard genuinely prevents a doubled query when relations
  are selected.
- **Both directions pinned and PASSING (ran them).**
  `uv run pytest tests/optimizer/test_extension.py --no-cov -k "<the four>"` =
  4 passed. `test_optimizer_passes_through_consumer_evaluated_queryset` (1 query,
  `cache_info().misses == 0` — guard fired before plan build),
  `test_optimizer_still_optimizes_manager_after_evaluated_queryset_guard` (1 query,
  `misses == 1` — Manager path still plans), `test_optimize_returns_same_instance_for_evaluated_queryset`
  (`_optimize(qs, ...) is qs`), `test_resolve_async_passes_through_evaluated_queryset`
  (async await->`_optimize` inherits the guard; `_resolve_model_from_return_type`
  tripwire proves short-circuit before return-type resolution). No temp test needed
  — the permanent suite already pins every load-bearing behavioral claim.
- **`_stash_union` unions, not overwrites.** Read `extension.py::DjangoOptimizerExtension._stash_union`
  #"merged = existing | new": `existing | new` when existing is a `frozenset`/`set`,
  else `new`. A nested fallback connection re-publish therefore preserves the parent's
  planned / fk-id-elision / lookup-path sentinels (spec-033 Decision 8).
  `DST_OPTIMIZER_PLAN` correctly bypasses the union via `_stash_on_context` (line 946,
  last-wins introspection data).
- **ContextVar per-execution state reset in `finally`.** `on_execute` (lines 704-718)
  sets `_optimizer_active` / `_active_optimizer` / `_printed_ast_cache` /
  `_pagination_var_names_cache` and resets all four in `finally` in reverse order via
  token `.reset()`. No cross-request leak; the two memo dicts are fresh `{}` per
  execution and `None`-default to recompute for direct test callers (lines 1071-1098).
- **Cache key hashable by construction.** `_build_cache_key` (lines 1100-1102) folds
  `frozenset((k, variable_values[k]) for k in relevant_var_names ...)`.
  `relevant_var_names` comes only from `_collect_cache_relevant_var_names` ->
  `_collect_cache_var_families` (lines 165-173), which collects (a) `@skip`/`@include`
  directive `if`-arg variables (`Boolean!` by GraphQL spec) and (b) `first`/`last`/
  `before`/`after` pagination-arg variables (Int / cursor String) — all scalar by
  GraphQL type. The narrowing is exactly what guarantees `variable_values[k]` is never
  a list / input object, so the `(name, value)` frozenset can never receive an
  unhashable member. Root pagination is correctly excluded (depth >= 1 guard, line 170).

### DRY findings disposition

DRY analysis: None, accepted. Spot-checked the claim — the Manager-coercion gate routes
through `normalize_query_source`, the stash helpers / five `DST_OPTIMIZER_*` keys come
from `_context.py` re-aliases, and the plan-build-apply tail is single-sited in `apply_to`
shared by `_optimize` and `apply_connection_optimization`. `_PAGINATION_ARG_NAMES` is the
single source for the four pagination names (lines 99-106, used at line 172). No remaining
duplicated literal or parallel walker in this file.

### Temp test verification

- None created. The four named permanent tests (`tests/optimizer/test_extension.py`)
  cover every behavioral claim (sync pass-through, instance identity,
  Manager-still-optimizes, async mirror) and pass on this HEAD, so no executable
  confirmation gap remained.
- Disposition: n/a — no temp tests written.

### Low disposition (independent assessment)

The single Low (connection-path G1 exemption rests on a slightly imprecise "framework-built"
rationale) is genuinely forward-looking and warrants NO `extension.py` edit — confirmed,
with one nuance I record for the audit trail. I traced the connection pipeline:
`connection.py::_pipeline_sync` -> `apply_type_visibility_sync` (line 867) ->
`_finalize_queryset` -> `deterministic_order`/`order_by` (lines 805-807) ->
`apply_connection_optimization` (line 808). The Low's *headline* (the spec's
"never consumer-evaluated" wording under-describes a consumer `resolver=` returning an
evaluated qs) is correct and confirmed against spec-035 Decision 3 (`docs/SPECS/spec-035-…`
lines 33/79/176/183) and GLOSSARY 419-422 (accurate to shipped scope, not stale). I note
the Low's *supporting* rationale ("`apply_type_visibility_sync` and `deterministic_order`
already re-execute regardless") is itself slightly stronger than the source warrants:
`apply_type_visibility_sync` calls `type_cls.get_queryset` which is identity by default
(`utils/querysets.py::apply_type_visibility_sync` #"result = type_cls.get_queryset"), and
`order_by` only fires when `ordered != effective` (connection.py line 806) — so neither
upstream step is *guaranteed* to clone. A narrow connection-path doubled-query is therefore
theoretically reachable (consumer `resolver=` returns an evaluated qs, default identity
`get_queryset`, ordering already ending in a unique column, relations selected). This does
NOT reopen the cycle: it is the SAME forward-looking concern the Low already flags, and the
root-cause fix (whether the connection path warrants its own G1 guard, or hoisting G1 into
`apply_to`) is a spec-035 / `connection.py` design decision that Decision 3 deliberately and
explicitly rejected (Decision 3 alternatives) — it lives outside `extension.py`. `extension.py`
itself is correct: G1 is scoped to `_optimize` exactly as Decision 3 prescribes. Carried
forward as the doc-precision note with Worker 2's trigger ("until the connection-pipeline doc
or spec-035 is next revised"); I additionally recommend the next reviser sharpen the
exemption to acknowledge the connection re-execution is conditional, not structural.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
`optimizer/extension.py` checklist box in `docs/review/review-0_0_10.md`.

Shape #5 disqualifier sweep: empty cycle diff ✓; each Worker 2 section opens with
"Filled by Worker 1 per no-source-edit cycle pattern." ✓; the Low carries verbatim
forward-looking trigger phrasing and is NOT a GLOSSARY-only fix (Worker 2 confirms GLOSSARY
419-422 is accurate, not stale) ✓; changelog `Not warranted` cites BOTH AGENTS.md and the
active plan's silence ✓; ruff format-check + check pass ✓.

---

## Iteration log

(none)
