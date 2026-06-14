# Review: `django_strawberry_framework/optimizer/extension.py`

Status: verified

> Supersedes the stale 0.0.7 `Status: verified` artifact that pre-existed on disk
> (its line cites — `_walk_directives` 92-128, `_strawberry_schema_from_schema`
> 299-306, FIFO eviction 650-658 — do not match current source). Active plan box
> `review-0_0_9.md:92` was unchecked. Replaced wholesale per the recurring
> stale-artifact pattern; live source diffed before reuse — the prior artifact's
> `_walk_directives`/`_walk_pagination_vars` split is GONE (unified into
> `_walk_cache_relevant_vars` by the 0.0.9 DRY pass), so its DRY bullet #1 is
> already merged and is NOT re-raised.

## DRY analysis

- **Defer-until-third-selection-walker:** `_walk_cache_relevant_vars` (`extension.py::_walk_cache_relevant_vars`) and `_walk_reachable_fragment_definitions` (`extension.py::_walk_reachable_fragment_definitions`) are two cycle-guarded recursive selection-set + fragment-spread descents that already share `_child_selections` (= `selections.ast_child_selections`) and `_unvisited_fragment_definition` (= `selections.resolve_unvisited_fragment`). The only divergence is the per-node side effect (collect directive/pagination names + a depth axis vs. append fragment-def to a list, no depth). A `_walk_selection_tree(node, fragments, visited, on_node)` higher-order primitive in `selections.py` could carry both, with the depth bookkeeping passed through `on_node`. Defer: collapsing now would force the depth axis into the fragment-collector's callback for no benefit and the two side effects do not currently rhyme. Trigger: a **third** cycle-guarded recursive selection-set walker lands under `optimizer/` (e.g. a future schema-audit selection-aware mode), at which point design the shared visitor once across three sites.
- **Defer-until-third-Strawberry-schema-reach:** `_strawberry_schema_from_schema` (`extension.py::_strawberry_schema_from_schema`, fallback = the input itself) and `_strawberry_schema_from_info` (`extension.py::_strawberry_schema_from_info`, fallback = `None`) both read the private `_strawberry_schema` attribute but on different access shapes and with different miss-fallbacks. A single `_strawberry_schema_of(obj, *, default)` would carry both via the `default` arg. Defer until a third reach site needs the private attribute. Trigger: a third consumer of `schema._strawberry_schema` under `optimizer/`.
- **Defer-until-fragment-walk-needs-depth:** `_collect_reachable_fragment_definitions` / `_walk_reachable_fragment_definitions` and the `_collect_cache_var_families` / `_walk_cache_relevant_vars` pair are near-parallel "thin collector + recursive workhorse" twin shapes (same `set()`-seed-then-recurse, same visited-fragment guard threading). They are NOT collapsed because the var-walk carries a `depth` axis and a two-set accumulator while the fragment-walk carries a single list and no depth. Subsumed by the first bullet's trigger; listed separately only to note the second twin pair exists. Trigger: same as bullet 1.

## High:

None.

## Medium:

None.

## Low:

### Stale-prone version-pin in the pagination-arg comment

`extension.py #"a future ``search:`` extension (``0.1.2``)"` (the `_PAGINATION_ARG_NAMES` comment, src ~95-96) hard-codes a future release number against a hypothetical `search:` extension. Per the carried calibration (worker-memory: "version-pinned docstring labels rot every release"; cf. `exceptions.py::OptimizerError` "raise sites in 0.0.7"), an inline future-version pin in a comment is a maintainability snag — it will read as stale the moment `0.1.2` ships without the `search:` family, or if the family lands earlier/later. Forward-looking Low: the comment is correct **today** and the named release has not shipped. Recommend, when next touched, version-agnostic wording ("a future `search:` extension would extend the family here") rather than re-pinning. Trigger: any edit to the `_PAGINATION_ARG_NAMES` block, OR the `search:` extension landing — re-word then rather than re-pin.

### `_root_child_selections` `# noqa: ARG001` documents the uniform-signature contract only by suppression

`extension.py::_root_child_selections` ignores its `info` arg (`# noqa: ARG001`, src 332) to satisfy the `SelectionExtractor = Callable[[list[Any], Any], list[Any]]` protocol that `_connection_node_child_selections` *does* use `info` for (it threads `runtime_path_from_info(info)` into the edge/node prefixes). The `noqa` is correct and minimal, but the WHY (uniform extractor signature so `apply_to` can dispatch either via the `selection_extractor=` kwarg) lives only implicitly. Forward-looking Low, comment-tier: a one-line "info unused here; present to match the `SelectionExtractor` protocol the connection extractor consumes" would stop a future maintainer from "simplifying" the signature and breaking the `apply_to(..., selection_extractor=)` seam. Trigger: a third `SelectionExtractor` implementation lands, OR any edit to the `_root_child_selections` signature.

## What looks solid

### DRY recap

- **Existing patterns reused.** The selection-traversal primitives are sourced from `optimizer/selections.py` via the underscore aliases (`_child_selections`, `_unvisited_fragment_definition`, `_named_children`, `_node_children_with_runtime_prefix`, `_response_key`, src 83-87) — the 0.0.9 DRY pass (`docs/feedback.md` Major 2) removed the reverse `extension <- walker` dependency; both modules now source from `selections`. `directive_variable_names` is the single shared `@skip`/`@include` extractor (`selections.py::directive_variable_names`). The Manager-coercion + is-queryset decision is the shared `utils/querysets.py::normalize_query_source` contract (Major 1), so the middleware path (`_optimize`, src 730) never re-decides it. `runtime_path_from_info`, `lookup_paths`, `diff_plan_for_queryset` are imported from `plans.py`, not re-spelled. `_stash_on_context` / `_get_context_value` are re-exported from `_context.py` for cross-subpackage reuse with the read-side consumed by `types/resolvers.py`.
- **New helpers considered.** The unified `_walk_cache_relevant_vars` (replacing the prior `_walk_directives` / `_walk_pagination_vars` split) is the correct act-now consolidation the 0.0.9 pass already landed — two collection RULES on different axes (directive-on-every-node vs. pagination-on-field-at-depth>=1) sharing one child-traversal + fragment-spread + cycle-guard descent, so a future fragment-depth or cycle fix lands on one path. `_collect_cache_var_families` is the single AST-walk-once entry the thin family wrappers (`_collect_directive_var_names`, `_collect_nested_pagination_var_names`) and the union collector (`_collect_cache_relevant_var_names`) share. The remaining selection-walker / Strawberry-schema-reach collapses are correctly deferred (see DRY analysis) — extracting now is net-negative.
- **Duplication risk in the current file.** `_PAGINATION_ARG_NAMES` is the single source of truth for the four Relay pagination arg names — no inline re-spelling (the `directive_variable_names`-style `("skip", "include")` literal lives once in `selections.py`). The only repeated literal flagged by the static helper is `_strawberry_schema` (2x), which is the deliberate two-access-shape pair (`_strawberry_schema_from_schema` / `_from_info`) with divergent fallbacks — intentional sibling design, captured as a deferred DRY bullet.

### Other positives

- **Root-gating is correct and minimal.** `resolve` gates on `info.path.prev is not None -> return result` (src 694) before any optimization work, so only the operation's root resolver triggers a plan; nested relations ride the root prefetch chain via Django `__`-chains. Sync/async fork is the package-standard intentional twin (`_async_optimize` awaits then `_optimize`) — do NOT extract.
- **Pagination-aware cache key (NEW 0.0.9) is correct.** Depth semantics verified by hand: `_collect_cache_var_families` seeds the walk at `depth=0` on `info.operation` (an `OperationDefinitionNode`, not a `FieldNode`, so `child_depth` stays 0); the operation's root fields are therefore visited at depth 0 and their `first`/`last` are NOT collected (root slicing is post-plan in `ConnectionExtension`), while a root field *is* a `FieldNode` so its children deepen to depth 1 and a nested connection's `first`/`last` IS collected. This matches every docstring claim ("root pagination stays out", "nested pagination keys the cache"). The collection is a deliberate syntactic superset (over-collection = cheap duplicate entries; under-collection = wrong data) — pinned by `test_pagination_var_collection_is_syntactic_superset`, `test_nested_pagination_variable_keys_cache`, `test_root_pagination_variable_shares_cache`, `test_root_fragment_pagination_variable_shares_cache`, `test_fragment_carried_nested_pagination_variable_collected`, `test_collect_nested_pagination_var_names_all_arg_names`, and the two-window correctness test `test_nested_pagination_variable_two_plans_two_windows`. Wrong-key = stale/wrong plan served was the headline data-correctness risk here; the gating is sound.
- **`edges { node }` root-seam extractor (NEW 0.0.9) is correct.** `_connection_node_child_selections` recomputes `root_path = runtime_path_from_info(info)` from the *connection's* raw info, then threads `(*root_path, edges_key, node_key)` runtime prefixes into the node children via `selections.node_children_with_runtime_prefix`, so the walker sees the same child list a list-field-over-the-node-type would, but with selection-specific prefixes for strictness and FK-id-elision resolver keys. Uses `_named_children` (fragment-recursing) for `edges` and `node`, so fragment-wrapped `edges`/`node` still unwrap. The `is_fragment` discriminator is shared with the walker and `direct_child_selected` so the three cannot drift. Pinned by `test_node_children_with_runtime_prefix_skips_excluded_and_clones_fragments` and exercised end-to-end via the fakeshop live connection tests (`test_genre_connection_full_round_trip`, `test_genre_connection_order_by_to_many_no_node_multiplication`, backward/forward pagination).
- **Queryset cooperation does not clobber consumer entries.** `apply_to` runs `diff_plan_for_queryset(plan, queryset)` (src 802) before `plan.apply` — drops exact-match entries, avoids "lookup already seen", and losslessly upgrades a consumer's plain string to a richer `Prefetch`; returns a fresh plan so the cached plan (B1) is never mutated. Cache-immutability is the stated Plan-cache contract.
- **Nested-fallback sentinel coexistence (spec-033 Decision 8).** `_publish_plan_to_context` UNIONs the FK-id-elision / planned / lookup-path frozensets via `_stash_union` rather than overwriting, so a nested fallback connection pipeline's per-parent publish does not destroy the parent plan's sentinel sets (critical under `"warn"`, where execution continues). `DST_OPTIMIZER_PLAN` is correctly kept last-wins introspection (NOT unioned). `_stash_union`'s `isinstance(existing, (frozenset, set))` guard is defensive-coerce consistent with the file's stance. Pinned by `test_publish_plan_to_context_unions_parent_and_nested_sentinel_sets` and `test_nested_connection_fallback_publish_unions_parent_planned_set_end_to_end`.
- **Per-execution memo lifecycle is async-safe.** `_printed_ast_cache` and `_pagination_var_names_cache` are per-execution `ContextVar` dicts set to `{}` in `on_execute` and `reset` in the `finally` (LIFO reset order mirrors set order), so async executions sharing one extension instance stay isolated. Both memos key off `id(operation)` and fall back to recomputation when `None` (direct test-only callers outside an `on_execute` lifecycle) — the memoization is a hit-rate optimization, never a correctness gate. Memoization-for-nested-fallbacks pinned by `test_cache_key_variable_name_collection_memoized_for_nested_fallbacks`.
- **LRU plan cache is correctness-safe under concurrency.** `_get_or_build_plan` is the sole insertion site (root-only). `move_to_end` promotion is wrapped in `suppress(KeyError)` for the concurrent-eviction race (a lost promotion is harmless), batched quarter-eviction amortizes cost, and only `plan.cacheable` plans are inserted (request-scoped `get_queryset` results stay out). `cache_info` honestly documents the best-effort counter caveat. Cache key folds `(doc_key, relevant_vars, target_model, root_runtime_path, origin)` — the `origin` leg gives primary/secondary-return separation (`test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model`); the printed-string `doc_key` (not its hash) eliminates the 64-bit-collision wrong-plan risk; multi-operation documents never collide (`test_cache_key_differs_for_named_operations_in_same_document`); reachable fragment bodies are appended so same-body-different-fragment operations key apart (`test_cache_differentiates_reachable_named_fragment_bodies`).
- **`apply_connection_optimization` follows the opt-in contract.** Returns the queryset unoptimized when `target_type` has no registered model OR when `_active_optimizer` is `None` (no installed extension / outside `on_execute`) — it does NOT fabricate a throwaway optimizer, keeping connection fields consistent with the middleware's opt-in. The `getattr(info, "_raw_info", info)` unwrap correctly feeds the plan machinery the raw graphql-core info while remaining usable from a direct test passing raw info. Pinned by `test_apply_connection_optimization_uses_active_optimizer_cache`. Caller is `connection.py::_finalize_queryset` (step 6 of the Decision 7 pipeline), invoked after deterministic ordering and before `ConnectionExtension` slicing.
- **`check_schema` audit scoping is sound.** Walks only root-reachable `DjangoType`s (orphan `types=[]` excluded to avoid false-positive warnings), descends through object fields, union members, and interface implementations (so an interface-only-reachable type still participates), dedupes `(source_model, field_name)` to avoid multi-type double-warning, and honors `OptimizerHint.SKIP` + hidden-field exclusion. Always returns warnings, never raises — the caller owns the raise decision. Matches GLOSSARY `#schema-audit` prose exactly.
- **GLOSSARY accurate.** `#djangooptimizerextension` (373-404), `#plan-cache` (947-964), and `#schema-audit` (1165-1167) all match live source. The `#plan-cache` "Variable filtering" bullet (956) was already updated for the 0.0.9 nested-vs-root pagination refinement ("variables feeding a **nested** connection's `first`/`last`/`before`/`after` ARE hashed ... while variables feeding **root** pagination arguments stay out ... including through root-level fragments") — verbatim-consistent with `_build_cache_key` and `_collect_nested_pagination_var_names`. No drift; no GLOSSARY edit in scope.

### Summary

Core N+1 + plan-cache-correctness review of the optimizer schema extension. The two flagged 0.0.9 surfaces — the pagination-aware plan-cache keys and the `edges { node }` root-seam extractor — are both correct: the cache-key depth gating cleanly separates root (depth 0, slicing post-plan) from nested (depth >= 1, values baked into windowed prefetch) pagination args, eliminating the stale-plan data-correctness risk; the connection extractor threads the right runtime prefixes so the walker sees a list-field-shaped node selection while preserving strictness / FK-id-elision resolver keys. Queryset cooperation never clobbers consumer entries (`diff_plan_for_queryset` + cached-plan immutability), nested-fallback sentinel publishes union rather than overwrite (spec-033 Decision 8), and the per-execution memos plus LRU cache are async/concurrency-safe (correctness-neutral by design). No High, no Medium. Two forward-looking Lows (a `0.1.2` version-pin in the pagination-arg comment that will rot; a `noqa`-only documentation of the uniform `SelectionExtractor` signature) — both comment-tier, both trigger-gated, neither warrants a source edit this cycle. GLOSSARY clean. Shape #5 no-source-edit cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, `265 files left unchanged` (no edits this cycle).
- `uv run ruff check --fix .` — pass, `All checks passed!`.

### Notes for Worker 3
- Low 1 (`0.1.2` version-pin in `_PAGINATION_ARG_NAMES` comment): forward-looking, comment-tier, trigger-gated (edit to block OR `search:` extension lands). No edit this cycle.
- Low 2 (`_root_child_selections` `# noqa: ARG001` uniform-signature documentation): forward-looking, comment-tier, trigger-gated (third `SelectionExtractor` OR signature edit). No edit this cycle.
- No GLOSSARY-only fix in scope — `#djangooptimizerextension`, `#plan-cache`, `#schema-audit` all verified accurate vs live source (including the 0.0.9 pagination-refinement bullet at GLOSSARY:956).
- Stale 0.0.7 `Status: verified` artifact was replaced wholesale; prior DRY bullet #1 (`_walk_directives`/`_walk_reachable_fragment_definitions` collapse) is ALREADY MERGED (unified `_walk_cache_relevant_vars`) — not re-raised.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits in scope — the two Lows are forward-looking and trigger-gated; docstrings on the NEW 0.0.9 surfaces (pagination depth gating, edges-node extractor) are accurate vs verified behavior.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted** — zero edits to any tracked file. Per AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") and active-plan silence (`review-0_0_9.md` carries no changelog directive for this item).

---

## Verification (Worker 3)

### Logic verification outcome
No High/Medium. Both Lows are forward-looking comment-tier, trigger-gated, correctly deferred (no source edit): Low 1 (`0.1.2` version-pin in `_PAGINATION_ARG_NAMES` comment, src ~95-96 — confirmed present, correct today, named release unshipped); Low 2 (`_root_child_selections` `# noqa: ARG001`, src 332 — confirmed present, uniform `SelectionExtractor` protocol contract real, `_connection_node_child_selections` does consume `info` for `runtime_path_from_info`). Neither warrants an edit this cycle.

**Riskiest claim independently verified (no-DB repro):** pagination-aware plan-cache key cannot serve a stale/wrong plan. Drove `_collect_cache_var_families` + `DjangoOptimizerExtension._build_cache_key` on hand-parsed AST (graphql-core `parse`, FakeInfo shim, memos `None` → recompute path):
- ROOT `first:$n` at depth 0 → `pagination_names == set()` (root slicing post-plan; no page-fragmentation). Root pagination with two distinct `$n` (5 vs 99) → SAME key (page-invariant).
- NESTED `first:$n` at depth >=1 → `{'n'}` collected. Two distinct nested page values ($n=5 vs $n=20) → two distinct keys (`relevant_vars` `{('n',5)}` vs `{('n',20)}`) → two windows. Same value → same key (cache hits, no over-fragmentation).
- Fragment-carried nested pagination inherits spread-site depth → collected; root pagination inside a root-level fragment stays out (spread-site depth 0). Confirms Decision-7 "depth at the spread site" claim.
Depth gating (`child_depth = depth+1 if isinstance(node, FieldNode) else depth`, src 167; operation seeds depth 0 as a non-FieldNode) cleanly separates root depth-0 post-plan slicing from nested depth>=1 values baked into the windowed prefetch. Verified at source against `selections.py` primitives.

Other claims confirmed at source: root-gating (`info.path.prev is not None -> return result`, src 694) is minimal/correct; `edges{node}` extractor (src 353-375) recomputes `root_path` and threads `(*root_path, edges_key, node_key)` via `node_children_with_runtime_prefix`, fragment-recursing via `_named_children` (selections.py:191/229 confirmed); queryset cooperation (`diff_plan_for_queryset`, src 802) returns a fresh plan so the cached plan is never clobbered/mutated; `_stash_union` (src 891-905) unions frozensets and keeps `DST_OPTIMIZER_PLAN` last-wins; request-scope memos set `{}` in `on_execute` / reset LIFO in `finally` (src 656-670), `None` fallback recomputes (async-safe).

### DRY findings disposition
3 DRY bullets all correctly deferred-until-third (selection-tree visitor; `_strawberry_schema_of`; fragment-walk-needs-depth twin). Triggers unfired — no edits.

### Temp test verification
- `docs/review/temp-tests/optimizer_extension/repro_cache_key.py` — 6-case depth-gating + two-window repro, ALL ASSERTIONS PASSED.
- Disposition: deleted at cycle closeout (gitignored scratch); behavior already pinned by the permanent suite the artifact cites (`test_nested_pagination_variable_two_plans_two_windows`, `test_root_pagination_variable_shares_cache`, `test_root_fragment_pagination_variable_shares_cache`, `test_fragment_carried_nested_pagination_variable_collected`). Not the sole proof of shipped behavior — no promotion needed.

### Shape #5 no-source-edit checks
- `git diff --stat <baseline> -- optimizer/extension.py` empty (byte-unchanged). Baseline `0872a20...`; HEAD `692ef0b...`.
- Full owned-scope diff (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) dirty only at conf.py, exceptions.py, filters/factories.py, filters/sets.py, list_field.py, management/commands/inspect_django_type.py, tests/management/test_inspect_django_type.py, docs/GLOSSARY.md — each attributes to a CLOSED sibling cycle (all `[x]` at review-0_0_9.md:70/72/73/80/82/87; GLOSSARY hunks = rev-connection / rev-filters / inspect siblings per prior verified cycles). NOT a rejection trigger; "Files touched: None" holds for this cycle.
- Each Worker 2 section starts with `Filled by Worker 1 per no-source-edit cycle pattern.`
- Both Lows carry verbatim trigger phrasing; no GLOSSARY-only fix in scope.
- Changelog `Not warranted`, both citations (AGENTS.md + active-plan silence); `git diff -- CHANGELOG.md` empty. Internal-only framing honest (zero edits).
- Ruff: `check` clean, `format --check` clean on extension.py (COM812 warning is the standing config note, not a failure).

### Verification outcome
cycle accepted; verified

---

## Iteration log
