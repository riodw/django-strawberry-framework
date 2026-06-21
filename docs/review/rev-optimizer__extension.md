# Review: `django_strawberry_framework/optimizer/extension.py`

Status: verified

Reviewed against current HEAD source. Per-cycle baseline SHA `ead8597d`. `git diff ead8597d -- django_strawberry_framework/optimizer/extension.py` is EMPTY and `git diff HEAD -- ...` is EMPTY — no source change since the prior verified cycle. Static overview re-run this cycle (`docs/shadow/django_strawberry_framework__optimizer__extension.overview.md`) per REVIEW.md's optimizer-file requirement; 35 symbols, 9 control-flow hotspots, 4 ORM markers (all `models.QuerySet` annotations on `apply_to` / `apply_connection_optimization`), 1 repeated literal (`_strawberry_schema` ×2, intentional twin getattr in the schema-vs-info unwrappers). Genuine **shape #5 no-source-edit cycle**: no High, no behavior-changing Medium, every Low forward-looking; zero tracked edits.

Focused scrutiny on the prompt-named load-bearing surface: cache-key correctness (doc key + reachable-fragment append + relevant-var-name fold), request-scope `ContextVar` state (`_optimizer_active` / `_active_optimizer` / `_printed_ast_cache` / `_pagination_var_names_cache` all set+reset in `on_execute`'s try/finally), sync/async branch in `resolve`, the 0.0.10 guards (G1 evaluated-queryset pass-through; G2 `.only()`-on-non-QUERY is owned by `plans`/`walker`, not this file), FK-id elision stash, `get_queryset`→`Prefetch` downgrade (delegated to `walker.plan_relation`), and the mutation/connection operation guards (`apply_connection_optimization` / `mutation_payload_child_selections`).

## DRY analysis

- None — the module already routes every shared mechanism through a single owner. Manager-coercion + is-queryset decision is `utils/querysets.py::normalize_query_source` (`extension.py::DjangoOptimizerExtension._optimize` #"result, is_queryset = normalize_query_source(result)"); the stash get/set pair is the `_context.py` helpers re-aliased here (`extension.py` #"from ._context import (" import block at lines 52-64); the selection-traversal primitives are `selections.py` symbols re-aliased under `_`-names (`extension.py` #"_child_selections = ast_child_selections" lines 85-89), consumed both internally (`_connection_node_child_selections`, `mutation_payload_child_selections`, the two fragment walkers) and by `tests/optimizer/test_extension.py:54-55`; the plan-build / plan-apply tail is single-sited in `apply_to` (`extension.py::DjangoOptimizerExtension.apply_to`), consumed by BOTH the middleware path (`_optimize`) and the connection/mutation path (`apply_connection_optimization`); the five `DST_OPTIMIZER_*` keys are single-sourced in `_context.py`; the four pagination arg names are single-sourced in module-level `_PAGINATION_ARG_NAMES` (`extension.py` #"_PAGINATION_ARG_NAMES = frozenset"). The previously-separate `_walk_directives` / `_walk_pagination_vars` walkers were already collapsed into the single `_walk_cache_relevant_vars` traversal (one AST descent, two families) — the DRY resolution is in place, not a candidate. No remaining duplicated literal, near-copy walker, or parallel data flow inside this file.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `normalize_query_source` for the Manager/queryset decision (`_optimize`, lines 817-819); the `_context.py` stash helpers re-aliased (`_get_context_value` / `_stash_on_context`, lines 59-64) and consumed by `_stash_union` (lines 1004-1006); the `selections.py` AST primitives re-aliased under `_`-names (lines 85-89); `plans.diff_plan_for_queryset` / `lookup_paths` / `runtime_path_from_info` and `walker.plan_optimizations` / `plan_relation` are the single owners of plan diffing, lookup-path derivation, and the relation-strategy decision respectively. `apply_to` is the single plan-build+apply tail shared by the middleware and connection/mutation entry points.
- **New helpers considered.** None warranted — the single-AST-descent collector (`_walk_cache_relevant_vars` + `_collect_cache_var_families`) already unifies the directive and pagination families; splitting the thin per-family wrappers (`_collect_directive_var_names` / `_collect_nested_pagination_var_names`) back apart was rejected by design (the docstring at lines 159-163 records the rationale: keeping them apart risked a future fragment-depth/cycle fix landing on only one path).
- **Duplication risk in the current file.** The lone repeated literal `_strawberry_schema` (lines 519, 529) is the intentional twin between `_strawberry_schema_from_schema` (schema arg) and `_strawberry_schema_from_info` (info.schema arg) — two distinct attribute-access shapes centralizing the same brittle Strawberry-private contract; not extractable without losing the per-caller fallback semantics (`schema` itself vs `None`).

### Other positives

- **Request-scope isolation is airtight.** All four module-level `ContextVar`s default safely (`False` / `None`) and are set+reset symmetrically in `on_execute`'s try/finally (lines 736-748), so async executions sharing one extension instance stay isolated and an exception mid-yield still resets. The two per-execution memos (`_printed_ast_cache`, `_pagination_var_names_cache`) read `None`-outside-lifecycle and recompute, so direct test-only callers of `_build_cache_key` are correctness-safe (lines 1101-1128).
- **Cache key is correctness-first.** Stores the printed document string (not a 64-bit hash) to eliminate hash-collision plan sharing (docstring lines 1075-1077); appends reachable fragment bodies so same-shaped operations with different fragment bodies do not collide (`_print_operation_with_reachable_fragments`); keys on `(doc, relevant_vars, model, runtime_path, origin)` so multi-operation documents, multiple root fields returning the same model, and primary-vs-secondary origin types each separate. Nested pagination variables are a deliberate syntactic superset (over-collection costs duplicate entries, under-collection would serve wrong data — Decision 7).
- **Concurrency posture documented and safe.** `cache_info` and the class docstring spell out that hit/miss/size counters and eviction are best-effort under unlocked concurrent access but the cache is correctness-neutral (a missed insert / double-evict only reduces hit rate). The LRU `move_to_end` on a cache hit is `suppress(KeyError)`-guarded against a concurrent eviction sweep, once-per-request not per-row (lines 939-940).
- **G1 evaluated-queryset guard placement is load-bearing in both directions.** Sits AFTER Manager coercion (a coerced `.all()` is always fresh+unevaluated) and BEFORE return-type resolution / `apply_to` clone; uses `_result_cache is not None` (not truthiness) so an evaluated-but-empty queryset is handled correctly (lines 820-832). Matches GLOSSARY G1 prose verbatim.
- **`_stash_union` correctly preserves nested-fallback-connection parent plans.** Unions correctness sentinels (FK-id elisions, planned keys, lookup paths) into any existing frozenset rather than overwriting, while `DST_OPTIMIZER_PLAN` stays last-wins introspection data (spec-033 Decision 8). Pinned by the `test_extension.py` stash tests.
- **`check_schema` dedupe is a multi-type artifact, not generic defensiveness.** `seen` set on `(model, field_name)` prevents multi-type field-map overlap from double-warning; every reachable type is still audited (secondaries may expose relations the primary hides). `_collect_schema_reachable_types` descends through object fields, union members, and interface implementations (graphql-core `get_implementations`, `hasattr`-guarded for cross-version safety). Matches GLOSSARY:1218.
- **Anonymous-inline-fragment crash avoided.** `apply_to` uses the package-owned `ast_to_converted_selections` adapter instead of Strawberry's `convert_selections`, whose `InlineFragment.from_node` crashes on a valid anonymous inline fragment (`... { f }`, `type_condition=None`) — docstring lines 875-883.
- **GLOSSARY clean, no drift.** Verified all public-contract symbols against the source: `DjangoOptimizerExtension` (GLOSSARY:416-451, incl. G1/G2 shipped-behavior bullets), `cache_info` (1014), Plan cache (1000-1018, selection-shape keys + variable filtering + multi-operation/named-fragment/request-scope/immutability), Strictness mode (1305-1323, off/warn/raise + connection participation), FK-id elision (575-592, incl. 0.0.10 non-QUERY-with-loaded-check), only() projection G2 (927, attributed to plan-build not this file), Schema audit / `check_schema` (1218), Connection-aware planning (262/326). No documented public-contract symbol drifted; ran the grep-GLOSSARY step (the #4-vs-#5 separator) — genuine #5, not #4.
- **All cross-module refs live.** `_context` exports all five `DST_OPTIMIZER_*` keys + `get_context_value` / `stash_on_context`; `walker` exports `plan_optimizations` / `plan_relation`; `plans` exports `diff_plan_for_queryset` / `lookup_paths` / `runtime_path_from_info`. `apply_connection_optimization` consumed by `connection.py:835` + `mutations/resolvers.py:775`; `mutation_payload_child_selections` consumed by `mutations/resolvers.py:779`. The lines-80-81 underscore-alias comment claim (tests import `_named_children` / `_node_children_with_runtime_prefix` from this module) is ACCURATE — both are imported at `tests/optimizer/test_extension.py:54-55`.

### Summary

`extension.py` is the optimizer's root-gated planning surface and a mature, heavily-reviewed module. Source is byte-identical vs both the cycle baseline (`ead8597d`) and HEAD. Every load-bearing claim re-verified against the source: request-scope `ContextVar` lifecycle, the correctness-first plan cache key (printed doc string + reachable fragments + relevant-var fold), the G1 evaluated-queryset guard, FK-id-elision / strictness sentinel union, sync/async resolver split, and the connection/mutation operation guards via the shared `apply_to` tail. GLOSSARY carries no drift on any public-contract symbol; all cross-module imports and consumers resolve; the single repeated literal is an intentional twin. Zero findings → genuine no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `289 files left unchanged` (no changes).
- `uv run ruff check --fix .` — `All checks passed!` (no changes).

### Notes for Worker 3
- No GLOSSARY-only fix in scope — grep-GLOSSARY across all public-contract symbols (`DjangoOptimizerExtension`, `cache_info`, Plan cache, Strictness mode, FK-id elision, only() projection / G2, Schema audit / `check_schema`, Connection-aware planning) showed no drift; source is byte-identical vs baseline `ead8597d` AND HEAD.
- No High / Medium / Low findings to disposition — all three severity headings are `None.`; every potential nit was verified non-actionable (the lines-80-81 underscore-alias comment is accurate per `tests/optimizer/test_extension.py:54-55`; the `_strawberry_schema` ×2 literal is an intentional twin).
- Static overview regenerated this cycle at `docs/shadow/django_strawberry_framework__optimizer__extension.overview.md` (+ `.stripped.py`).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits — the module's comments and docstrings were audited (35 docstrings; comment inventory in the overview) and found accurate: the underscore-alias provenance comment (lines 78-89), the `_PAGINATION_ARG_NAMES` future-`search:` note (lines 93-98), the G1 placement rationale (lines 820-830), and the Decision-7 / Decision-8 / Decision-11 cross-references all match the implementation and the standing GLOSSARY prose. No stale TODO anchors (overview: 0 TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source, test, or doc edit this cycle (AGENTS.md #21 "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_11.md` is silent on any changelog entry for this item).

---

## Verification (Worker 3)

### Logic verification outcome

Genuine shape #5 no-source-edit cycle. Zero-edit proof confirmed three ways: `git diff ead8597d -- django_strawberry_framework/optimizer/extension.py` EMPTY, `git diff HEAD -- ...` EMPTY, and `git show HEAD:...optimizer/extension.py | diff -` reports IDENTICAL. The owned-paths `git diff --stat ead8597d -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` is EMPTY of source/test changes (the lone working-tree GLOSSARY hunk vs HEAD is at line 305, relation-cardinality validation = the recurring AGENTS.md #33 concurrent-maintainer work, not an optimizer/extension.py-owned edit). All three severity headings are `None.`; each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern." No High/Medium/Low to disposition, no GLOSSARY-only fix (which would be disqualifying for #5).

Independently re-verified the prompt-named load-bearing surface against live source — every claim genuine, not a skipped defect:

- **Request-scope `ContextVar` isolation** — all four module-level vars (`_optimizer_active` False, `_active_optimizer`/`_printed_ast_cache`/`_pagination_var_names_cache` None) are set in `on_execute` (lines 736-741) and reset in `finally` in reverse order (745-748), so an exception mid-yield still resets and async executions sharing one instance stay isolated. Pinned by `test_on_execute_sets_and_resets_context_var` (test_extension.py:955).
- **Correctness-first plan cache key** — `_build_cache_key` stores the printed document STRING (`_print_operation_with_reachable_fragments`), not a 64-bit hash (docstring 1074-1077), appends reachable fragment bodies, and keys on `(doc, relevant_vars, model, runtime_path, origin)`. Pinned by `test_cache_differentiates_reachable_named_fragment_bodies`, `test_cache_key_includes_root_runtime_path_for_same_model_fields`, `test_cache_key_differs_for_named_operations_in_same_document`.
- **G1 evaluated-queryset guard** — `if getattr(result, "_result_cache", None) is not None: return result` (line 831), placed AFTER Manager coercion (820-830) and BEFORE return-type resolution / `apply_to` clone. The `is not None` (not truthiness) is load-bearing: an evaluated-but-empty queryset has `_result_cache = []` (falsy, non-None) and must still short-circuit. Pinned by `test_optimize_returns_same_instance_for_evaluated_queryset` (identity), `test_optimizer_passes_through_consumer_evaluated_queryset` (single-query end-to-end), `test_optimizer_still_optimizes_manager_after_evaluated_queryset_guard` (placement-after-coercion), `test_resolve_async_passes_through_evaluated_queryset` (async branch).
- **Strictness mode** — `__init__` rejects any value not in `("off","warn","raise")` with `ValueError` (705-707); `_publish_plan_to_context` stashes planned/lookup/strictness sentinels only when `!= "off"` (981-990). Pinned by the `test_strictness_*` family (invalid_value_raises, warn_logs, off_does_not_stash, warn_stashes, raise paths).
- **FK-id elision incl. 0.0.10 non-QUERY no-`.only()` guard** — extension.py stashes `DST_OPTIMIZER_FK_ID_ELISIONS` via `_stash_union` (977-980); the G2 `.only()` suppression itself is owned by `walker.py::_enable_only_for_operation` (lines 65-83: `operation is None or operation is OperationType.QUERY`), confirmed at source — MUTATION/SUBSCRIPTION leave `plan.only_fields` untouched (walker.py:413-418). Correctly attributed to plan-build (walker), not this file, matching GLOSSARY:927/445.
- **`get_queryset`→Prefetch downgrade** — delegated to `walker.plan_relation` via the thin instance-method seam `DjangoOptimizerExtension.plan_relation` (1141-1158); confirmed the module-level `plan_relation` is imported from `.walker` (line 76).
- **`_stash_union` parent-plan preservation** — unions into existing frozenset/set, else stashes new alone (1004-1006); `DST_OPTIMIZER_PLAN` stays last-wins (not unioned).

GLOSSARY optimizer prose verified accurate vs live source (#4-vs-#5 separator): G1 (444), G2 (445/927), FK-id elision (575-592), Strictness (142), Plan cache + cache_info (1000-1014), Connection-aware planning (256-264), DjangoOptimizerExtension (416-451) — none touched by the diff and none drifted. Genuine #5, not a missed #4.

Cross-module consumers resolve: `apply_connection_optimization` consumed by `connection.py:835` + `mutations/resolvers.py:775`; `mutation_payload_child_selections` by `mutations/resolvers.py:779`; the underscore aliases `_named_children` / `_node_children_with_runtime_prefix` imported at `tests/optimizer/test_extension.py:54-55`.

### DRY findings disposition

No DRY items — the artifact's `## DRY analysis` records `None` with the routing rationale (every shared mechanism single-owned: `normalize_query_source`, the `_context.py` stash helpers, the `selections.py` AST primitives, the single `apply_to` plan-build+apply tail shared by middleware and connection/mutation paths, the collapsed `_walk_cache_relevant_vars` traversal). Confirmed no remaining duplicated literal or near-copy walker inside the file; nothing to forward.

### Temp test verification

- None used. The 134 named tests in `tests/optimizer/test_extension.py` already pin every load-bearing claim; no behavior suspicion required a temp test.
- Disposition: n/a.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `optimizer/extension.py` checklist box. Validation: `uv run ruff format --check` reports "1 file already formatted"; `uv run ruff check` reports "All checks passed!". Changelog "Not warranted" disposition cites BOTH AGENTS.md #21 and the active plan's silence; `git diff -- CHANGELOG.md` empty.

---

## Iteration log

(none)
