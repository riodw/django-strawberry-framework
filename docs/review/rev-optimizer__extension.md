# Review: `django_strawberry_framework/optimizer/extension.py`

Status: verified

## DRY analysis

- Existing patterns reused: `extension.py` delegates the optimizer/resolver context hand-off to `_context.stash_on_context` and shared sentinel keys at `django_strawberry_framework/optimizer/_context.py:34-38` and `django_strawberry_framework/optimizer/_context.py:59-97`; it delegates registry lookups to `registry.model_for_type`, `registry.iter_types`, and `registry.get` at `django_strawberry_framework/registry.py:100-122`; it delegates plan construction and relation decisions to `plan_optimizations` / `plan_relation` at `django_strawberry_framework/optimizer/walker.py:26-62`; it delegates queryset reconciliation and path extraction to `diff_plan_for_queryset`, `lookup_paths`, and `runtime_path_from_info` at `django_strawberry_framework/optimizer/plans.py:147-174` and `django_strawberry_framework/optimizer/plans.py:292-416`.
- New helpers a fix might justify: a single cache-key helper that renders the selected operation together with the fragment definitions reachable from it would serve `_build_cache_key` and keep the directive-variable walk aligned with the planner's fragment expansion; a small root-selection flattener would serve `_optimize` by converting all `info.field_nodes` into one child-selection list instead of hard-coding `selections[0]`.
- Duplication risk in the current file: `_walk_directives` already walks named fragments for cache-key variable extraction at `django_strawberry_framework/optimizer/extension.py:90-136`, but `_build_cache_key` separately renders only `info.operation` at `django_strawberry_framework/optimizer/extension.py:530-546`; those parallel views of the same GraphQL document can drift because the planner sees expanded fragment contents while the cache key does not. The static helper was run with `python scripts/review_inspect.py django_strawberry_framework/optimizer/extension.py --output-dir docs/review/shadow --stdout`; it also surfaced one repeated private literal, `_strawberry_schema`, but that access is already centralized in `_strawberry_schema_from_schema` / `_strawberry_schema_from_info` at `django_strawberry_framework/optimizer/extension.py:176-193`.

## High:

None.

## Medium:

### Plan cache keys ignore named-fragment bodies

`_build_cache_key` uses `print_ast(operation)` as the document component of the plan-cache key. That prints the selected operation node, but not the named fragment definitions that the operation spreads. The planner receives `convert_selections(info, info.field_nodes)` and expands those fragments when building the actual plan, so two executions can share a cache key while needing different plans:

- `query Q { allItems { ...ItemBits } } fragment ItemBits on ItemType { name }`
- `query Q { allItems { ...ItemBits } } fragment ItemBits on ItemType { category { name } }`

The current tests cover distinct operation bodies and directive variable values, but not distinct fragment bodies behind the same operation shape. Reusing an empty/scalar-only cached plan for the relation-selecting document reintroduces N+1 behavior, and under `strictness="raise"` can report an unplanned lazy relation for a query the optimizer should have planned. Build the key from the operation plus the reachable fragment definition text, or otherwise include a stable representation of the fragment definitions consumed by the operation. Add coverage that executes the same operation text with different fragment bodies on the same extension instance and asserts two cache misses / distinct plans.

```django_strawberry_framework/optimizer/extension.py:512:556
        """Build the plan-cache key from resolver info and target model.
...
        operation = info.operation
...
                doc_key = print_ast(operation)
...
        directive_var_names = _collect_directive_var_names(
            operation,
            fragments=info.fragments,
        )
...
        return (doc_key, relevant_vars, target_model, runtime_path_from_info(info))
```

### Multiple field nodes are converted but only the first is planned

GraphQL can merge repeated fields with the same response name into one resolver call while passing all contributing AST nodes in `info.field_nodes`. `_optimize` passes the full list to Strawberry's `convert_selections`, but then plans only `selections[0].selections`. A query such as `{ allItems { name } allItems { category { name } } }` produces two converted root selections; the relation selected by the second node is ignored, so the root queryset is not optimized for `category`. Flatten or merge the child selections from every converted root selection before calling `_get_or_build_plan`. Add an in-process schema test using duplicate root field nodes that proves the relation is planned, preferably with `strictness="raise"` or query-count assertions so the missed plan cannot pass silently.

```django_strawberry_framework/optimizer/extension.py:393:407
        if not info.field_nodes:
            return result
...
        selections = convert_selections(info, info.field_nodes)
        # selections[0] is the root field; its .selections are the
        # children the walker needs.
        plan = self._get_or_build_plan(selections[0].selections, target_model, info)
        self._publish_plan_to_context(plan, info)
```

## Low:

None.

## What looks solid

- The optimizer remains root-gated and preserves sync/async resolver shapes while centralizing the final queryset application in `_optimize`.
- Context publication uses the shared `_context` helpers and keys, so the write side now matches the resolver read side instead of open-coding context mutation in this module.
- Queryset reconciliation is delegated to `diff_plan_for_queryset`, keeping the extension from mutating cached plans when consumers pre-apply `select_related` / `prefetch_related`.
- The static helper found no import-time execution hazards; the only lazy import is the documented Strawberry-internal `convert_selections` import inside `_optimize`.

### Summary

The file has good separation between extension orchestration, registry lookup, walker planning, context hand-off, and queryset diffing. The main remaining risks are both selection-shape cache/planning gaps: named fragment definitions are outside the cache key even though they affect the plan, and repeated root field nodes are converted but not all planned. Both should be fixed with focused optimizer tests before this artifact is verified.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/optimizer/extension.py` — added reachable-fragment rendering to the plan-cache document key, sharing fragment lookup/visited handling with directive-variable traversal; changed `_optimize` to plan the flattened child selections from every converted root field node.
- `tests/optimizer/test_extension.py` — added focused coverage for named-fragment cache-key separation and merged duplicate root field-node planning.

### Tests added or updated

- `tests/optimizer/test_extension.py::test_cache_differentiates_reachable_named_fragment_bodies` — pins identical operation text with different reachable named-fragment bodies producing separate cache misses and distinct plans.
- `tests/optimizer/test_extension.py::test_optimizer_plans_merged_duplicate_root_field_nodes` — pins duplicate merged root field nodes contributing all child selections, with `strictness="raise"` and a one-query assertion.

### Validation run

- `uv run ruff format .` — passed.
- `uv run ruff check --fix .` — passed.
- `uv run pytest tests/optimizer/test_extension.py::test_cache_differentiates_reachable_named_fragment_bodies tests/optimizer/test_extension.py::test_optimizer_plans_merged_duplicate_root_field_nodes` — assertions passed, then exited nonzero on the repo-wide coverage gate as expected for a focused run.
- `uv run pytest tests/optimizer/test_extension.py::test_cache_differentiates_reachable_named_fragment_bodies tests/optimizer/test_extension.py::test_optimizer_plans_merged_duplicate_root_field_nodes --no-cov` — passed, 2 tests.
- `uv run pytest tests/optimizer/test_extension.py --no-cov` — passed, 96 tests.

### Notes for Worker 3

- Used the existing static helper overview at `docs/review/shadow/django_strawberry_framework__optimizer__extension.overview.md`; shadow line numbers are not canonical.
- No findings were intentionally rejected.
- `CHANGELOG.md` was not edited in this logic pass; changelog disposition remains for the later workflow step.

---

## Verification (Worker 3)

### Logic verification outcome

- Medium, `Plan cache keys ignore named-fragment bodies`: addressed. `_build_cache_key` now renders the operation plus fragment definitions reachable from that operation, and the fragment map is normalized to `{}` before both document-key rendering and directive-variable collection. The per-execution memo remains keyed by `id(operation)`, which is acceptable because `info.fragments` is fixed within a single execution and the memo is reset by `on_execute`.
- Medium, `Multiple field nodes are converted but only the first is planned`: addressed. `_optimize` now passes all converted root field-node children into `_get_or_build_plan`, so merged duplicate root field nodes contribute all child selections.
- Low: none.
- High: none.

### DRY findings disposition

- Accepted. Worker 2 split the shared AST child-selection and fragment-definition lookup mechanics into `_child_selections` and `_unvisited_fragment_definition`, then reused those helpers for directive-variable traversal and reachable-fragment rendering. The root-selection merge is isolated in `_root_child_selections`, which keeps the `_optimize` call site small without broadening module responsibilities.

### Temp test verification

- Temp test files used: none.
- Disposition: not applicable. Worker 2 promoted the relevant coverage directly into `tests/optimizer/test_extension.py`.

### Verification outcome

logic accepted; awaiting comment pass.

Validation:

- `uv run pytest tests/optimizer/test_extension.py::test_cache_differentiates_reachable_named_fragment_bodies tests/optimizer/test_extension.py::test_optimizer_plans_merged_duplicate_root_field_nodes --no-cov` — passed, 2 tests.
- `uv run ruff format --check django_strawberry_framework/optimizer/extension.py tests/optimizer/test_extension.py` — passed.
- `uv run ruff check django_strawberry_framework/optimizer/extension.py tests/optimizer/test_extension.py` — passed.

Comment/docstring lifecycle remains open. The module-level `_printed_ast_cache` comments and `_build_cache_key` docstring still describe memoizing/rendering only `print_ast(operation)` instead of the final operation-plus-reachable-fragments document key. Shadow overview line numbers are not canonical; source-file line numbers remain canonical.

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/optimizer/extension.py` — updated the `_printed_ast_cache` comment, `_build_cache_key` docstring, and inline memoization comment to describe the final operation-plus-reachable-fragments document key.

### Tests/comments reviewed

- `tests/optimizer/test_extension.py` — checked the new test docstrings/comments for stale `print_ast(operation)`-only wording; no edits needed.

### Validation run

- `uv run ruff format .` — passed, 92 files left unchanged.
- `uv run ruff check --fix .` — passed.

### Notes for Worker 3

- Logic was not changed in this pass.
- Changelog disposition is not reached until Worker 3 accepts the comment/docstring pass.

---

## Changelog disposition

Warranted. The fixes change optimizer behavior for two user-visible query shapes: reachable named-fragment
bodies now participate in the plan-cache key, and duplicate merged root field nodes now contribute all child
selections to planning. Both can affect query planning, strictness failures, and N+1 avoidance, so they are
release-note-worthy.

No `CHANGELOG.md` edit was made. `AGENTS.md` forbids changelog updates unless explicitly instructed, and the
active review plan did not authorize a changelog edit. The disposition is recorded here for the maintainer to
fold into release notes if desired.

---

## Iteration log

Each Worker 2 re-pass appends a `## Fix report (Worker 2, pass <N>)` section here. Each Worker 3 re-verification appends a `## Verification (Worker 3, pass <N>)` section here. Do not edit prior entries; append.

## Verification (Worker 3, pass 2)

Comment/docstring pass accepted. The `_printed_ast_cache` comment now describes the memoized document key as the selected operation plus reachable named fragment definitions, and `_build_cache_key` now describes and memoizes the same operation-plus-reachable-fragments behavior instead of `print_ast(operation)` alone.

Verification outcome: comments accepted; awaiting changelog disposition.

Validation:

- `uv run ruff format --check django_strawberry_framework/optimizer/extension.py tests/optimizer/test_extension.py docs/review/rev-optimizer__extension.md` — failed because Ruff will not format Markdown without preview mode; the two Python files were already formatted.
- `uv run ruff format --check django_strawberry_framework/optimizer/extension.py tests/optimizer/test_extension.py` — passed, 2 files already formatted.
- `uv run ruff check django_strawberry_framework/optimizer/extension.py tests/optimizer/test_extension.py` — passed.

## Verification (Worker 3, pass 3)

Logic, DRY, comments/docstrings, validation, and changelog disposition accepted.

Verification outcome: cycle accepted; verified.

Changelog disposition: accepted. The behavior is release-note-worthy, but `CHANGELOG.md` was intentionally
left unchanged because `AGENTS.md` forbids changelog edits unless explicitly instructed and the active plan did
not authorize one.

Validation:

- `uv run pytest tests/optimizer/test_extension.py::test_cache_differentiates_reachable_named_fragment_bodies tests/optimizer/test_extension.py::test_optimizer_plans_merged_duplicate_root_field_nodes --no-cov` — passed, 2 tests.
- `uv run ruff format --check django_strawberry_framework/optimizer/extension.py tests/optimizer/test_extension.py` — passed, 2 files already formatted.
- `uv run ruff check django_strawberry_framework/optimizer/extension.py tests/optimizer/test_extension.py` — passed.

## Docstring follow-up (re-pass)

### Findings

The six new private helpers added by the original fix (`_child_selections`, `_unvisited_fragment_definition`,
`_collect_reachable_fragment_definitions`, `_walk_reachable_fragment_definitions`,
`_print_operation_with_reachable_fragments`, `_root_child_selections`) shipped without docstrings, while every
other private helper in `extension.py` (`_unwrap_gql_type`, `_strawberry_schema_from_schema`,
`_strawberry_schema_from_info`, `_collect_schema_reachable_types`, `_resolve_model_from_return_type`,
`_collect_directive_var_names`, `_walk_directives`) carries one. The comment/docstring pass updated the
module-level `_printed_ast_cache` comment and `_build_cache_key` docstring but did not document the new helpers,
leaving the file's docstring discipline inconsistent for the cache-key/fragment walk surface.

### Fix

Added docstrings to the six new helpers describing: what each helper returns, the AST shapes it dispatches on,
the deterministic-order/visited-set invariants (for the fragment walk family), and the load-bearing reason for the
flattening choice (for `_root_child_selections`). Behavior is unchanged.

### Files touched

- `django_strawberry_framework/optimizer/extension.py` — added docstrings to the six new helpers.

### Validation run

- `uv run ruff format django_strawberry_framework/optimizer/extension.py` — passed.
- `uv run ruff check django_strawberry_framework/optimizer/extension.py` — passed.
- `uv run pytest` (full suite, default coverage gate) — 533 passed, 1 skipped; package coverage 100.00%.

### Disposition

cycle accepted; verified. The docstring gap is closed; the original logic, DRY, and changelog dispositions are
unchanged. No `CHANGELOG.md` edit was made for the same `AGENTS.md` reason as the original cycle.
