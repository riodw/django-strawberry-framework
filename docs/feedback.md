# DRY review: connection optimizer follow-up

## Executive verdict

All four proposed DRY opportunities are real. The strongest two are the duplicated slice-window derivation and the re-spelled connection sidecar argument names. Those are worth fixing because they sit on optimizer correctness boundaries: plan-time window shape must match resolve-time consumption, and planner/resolver sidecar detection must never drift.

The sync/async pipeline duplication is also real, but the right fix is deliberately small: extract source normalization and sidecar-input helpers, while keeping the sync and async hook application explicit. The cache-key AST traversal duplication is valid too, but it is first-call and maintainability work because the combined result is already memoized per operation during execution.

Recommended order:

1. Extract the window-bound derivation helper.
2. Centralize sidecar kwarg names and sidecar-input predicates.
3. Use those sidecar helpers to lightly reduce sync/async pipeline duplication.
4. Merge the directive and nested-pagination variable collectors into one AST traversal.

## 1. Slice-window derivation

Verdict: valid, highest priority.

Current duplication:

- `django_strawberry_framework/optimizer/walker.py::_connection_window_slice`
- `django_strawberry_framework/connection.py::_consume_window`

Both call `SliceMetadata.from_arguments`, derive the same `reverse` predicate, use `slice_meta.start` as `offset`, and choose `limit = last if reverse else slice_meta.expected`. The comments explicitly say the resolver mirrors the walker, which is the smell: this is not merely similar code, it is a correctness contract split across two modules.

Why it matters:

The walker decides what rows to prefetch. The connection class later decides whether the annotated rows can be consumed and how to compute cursors/page flags. If the two copies diverge, optimizer-on and optimizer-off behavior can split even when every individual branch looks locally reasonable. The recent last-only and malformed-slice fixes are exactly the kind of change that would be easy to land in one copy and miss in the other.

Best fix:

Extract a private neutral helper that returns a small immutable value object, for example `ConnectionWindowBounds(offset, limit, reverse)`. Put it somewhere both `connection.py` and `optimizer/walker.py` can import without cycles, such as a new private utility module under `django_strawberry_framework/utils/` or another neutral package-private module. Do not put it in `connection.py` or `optimizer/walker.py`.

Suggested shape:

- `derive_connection_window_bounds(info, *, before, after, first, last, max_results) -> ConnectionWindowBounds`
- The helper should call `SliceMetadata.from_arguments` and own the reverse/limit rule.
- The walker should keep a thin adapter that reads `sel.arguments`, uses `_relay_max_results_from_info`, applies walker-only int coercion, catches `ValueError` / `TypeError`, and returns `None` for the malformed-slice fallback.
- The resolver should call the same helper with already-coerced Strawberry resolver arguments and should continue to let pagination errors propagate.

Do not hide the walker-only `_coerce_pagination_int` behavior inside the shared helper unless the helper makes that coercion an explicit option. Resolve-time arguments are already coerced by Strawberry; plan-time converted AST literals are not.

Tests to keep/add:

- Preserve the existing walker tests for inline int literals, variables, over-cap values, malformed cursors, and last-only reverse windows.
- Add a direct unit test for the shared helper proving `last`-only returns `limit == last`, not `slice_meta.expected`.
- Keep at least one through-schema parity test for last-only windows so the helper remains tied to real Relay output, not just tuple math.

## 2. Connection sidecar argument names

Verdict: valid, high priority.

Current duplication:

- `django_strawberry_framework/optimizer/walker.py::_CONNECTION_SIDECAR_ARGS`
- `django_strawberry_framework/connection.py::_pipeline_sync`
- `django_strawberry_framework/connection.py::_pipeline_async`
- `django_strawberry_framework/connection.py::_build_connection_resolver`
- `django_strawberry_framework/connection.py::_build_relation_connection_resolver`

The Python kwarg names `"filter"` and `"order_by"` are repeatedly spelled, and the predicate "does this request carry sidecar input?" is reimplemented as either `filter_input is not None or order_by_input is not None` or `kwargs.get("filter") is None and kwargs.get("order_by") is None`.

Why it matters:

This is a planner/resolver contract. The walker refuses to window-plan sidecar-bearing nested connections; the resolver refuses to consume a window if sidecar kwargs are present. Those two decisions must always use the same kwarg family. A future sidecar such as `search` would currently require synchronized edits in several places, and missing one would risk serving an unfiltered/unsearched prefetch through the fast path.

Best fix:

Centralize the Python kwarg names and the sidecar predicate in a cycle-safe private module. The module should have no dependency on `connection.py` or `optimizer/walker.py`.

Suggested shape:

- `CONNECTION_FILTER_KWARG = "filter"`
- `CONNECTION_ORDER_KWARG = "order_by"`
- `CONNECTION_SIDECAR_KWARGS = (CONNECTION_FILTER_KWARG, CONNECTION_ORDER_KWARG)`
- `connection_sidecar_inputs_from_kwargs(kwargs) -> tuple[Any, Any]`
- `has_connection_sidecar_input(*, filter_input, order_by_input) -> bool`
- Optionally `has_connection_sidecar_kwargs(kwargs) -> bool`

Then:

- The walker uses `CONNECTION_SIDECAR_KWARGS` for fallback detection.
- `_build_connection_resolver` and `_build_relation_connection_resolver` use the extraction helper instead of repeated `kwargs.get(...)`.
- `_pipeline_sync` and `_pipeline_async` use the predicate helper.
- `_synthesized_signature` uses the same constants when adding parameters and annotations.

Keep the distinction between Python kwarg names and GraphQL names explicit. The Python name is `order_by`; Strawberry exposes that as `orderBy`. Do not centralize only the display string and then derive the Python kwarg by convention.

Tests to keep/add:

- Existing sidecar SDL tests should continue to prove `filter:` / `orderBy:` are exposed.
- Existing sidecar fallback tests should continue to prove sidecar input prevents window consumption.
- Add one focused private-helper test if the helper has branching behavior; otherwise existing integration tests are enough.

## 3. Sync and async connection pipelines

Verdict: valid, but fix narrowly.

Current duplication:

- `django_strawberry_framework/connection.py::_pipeline_sync`
- `django_strawberry_framework/connection.py::_pipeline_async`

Both functions repeat manager coercion, sidecar-input detection, non-queryset guarding, visibility hook application, filter hook application, order hook application, and finalization. Some duplication is legitimate because sync and async hook application really is different: `_apply_get_queryset_sync` vs `_apply_get_queryset_async`, `apply_sync` vs `apply_async`, and explicit awaits on the async path.

Best fix:

Do not force the whole pipeline through a generic "maybe await" abstraction. That would obscure the sync/async contract and make `SyncMisuseError` behavior harder to audit. Instead extract only the pure or color-agnostic pieces:

- A source normalizer: Manager -> QuerySet, other values unchanged.
- A sidecar extraction/predicate helper from item 2.
- A guard helper that applies `_guard_sidecar_input_against_non_queryset` and returns early for non-querysets.
- Keep `_finalize_queryset` as the already-shared tail.

After that, `_pipeline_sync` and `_pipeline_async` should still visibly show their colored steps:

- sync: `_apply_get_queryset_sync`, `filterset_class.apply_sync`, `orderset_class.apply_sync`
- async: `await _apply_get_queryset_async`, `await filterset_class.apply_async`, `await orderset_class.apply_async`

This gives the maintainability win without turning a clear pipeline into an abstraction that hides where async work occurs.

Tests to keep/add:

- Existing sync resolver and async resolver tests should stay the primary proof.
- Add no test-only abstraction tests unless a new helper has a meaningful branch.
- Ensure non-queryset iterable plus sidecar input still raises the same `GraphQLError` message.

## 4. Cache-key variable collection AST walks

Verdict: valid, lower runtime priority, useful maintainability cleanup.

Current duplication:

- `django_strawberry_framework/optimizer/extension.py::_collect_cache_relevant_var_names`
- `django_strawberry_framework/optimizer/extension.py::_walk_directives`
- `django_strawberry_framework/optimizer/extension.py::_walk_pagination_vars`

The result is memoized per operation by `_pagination_var_names_cache`, so nested fallback rows do not repeatedly pay the full traversal. However, the first cache-key build still walks the operation/fragments once for directive variables and once for nested pagination variables. More importantly, both walkers own similar child traversal, fragment-spread descent, and cycle-guard plumbing.

Why it matters:

The two collection rules differ, but the traversal mechanics are the same. Keeping separate walkers makes future fragment-depth or cycle fixes easier to apply to only one path by accident. A single traversal better matches the intended "collect cache-relevant variables for this operation" concept.

Best fix:

Replace the two recursive walkers with one internal traversal that collects both families:

- Directive variables: collect `@skip` / `@include` variable references on every node, independent of depth.
- Nested pagination variables: collect `first` / `last` / `before` / `after` variable references only when the current node is a `FieldNode` at response-path depth >= 1.
- Fragment spread directives must still be collected on the spread node itself.
- Fragment definitions must still be traversed at the spread-site depth, not at raw fragment-definition nesting depth.
- The visited-fragment cycle guard must remain shared within the traversal.

Preserve thin wrappers for `_collect_directive_var_names` and `_collect_nested_pagination_var_names` if keeping the existing private tests stable is useful. Those wrappers can call the unified collector and return one side of the result. Then `_collect_cache_relevant_var_names` returns the union from a single traversal.

Do not fold `_collect_reachable_fragment_definitions` / `_print_operation_with_reachable_fragments` into this pass unless there is a measured reason. That path has a different output contract: deterministic printed document text, not variable names.

Tests to keep/add:

- Existing directive-variable tests.
- Existing nested-pagination variable tests, especially root-vs-nested fragment depth.
- Existing memoization test should be updated to count the unified collector rather than only `_collect_nested_pagination_var_names`.
- Add one mixed test where the same operation has both a directive variable and a nested pagination variable through a fragment spread, proving one traversal returns both.

## Areas not worth spending time on

These "do not spend time" claims are accurate:

- `_response_key` is already single-sited in `optimizer/walker.py`, with `optimizer/extension.py` importing it.
- `_relation_connection_to_attr` is already the single `_dst_<field>_connection` builder.
- Window annotation names are centralized in `optimizer/plans.py`.
- Deterministic ordering is centralized in `optimizer/plans.py::deterministic_order`.
- Strictness is centralized through `types/resolvers.py::_check_n1`; `connection.py` does not implement a second checker.
- The `append_unique` shape is not a DRY problem. `_IndexedList.append_unique` is the optimized indexed method, while module-level `append_unique` is the generic mutator wrapper for callers that only know they have a mutable sequence.

## Implementation guidance

Land this as small mechanical slices, not one broad refactor. The first two items are foundational and should come before pipeline cleanup because they give the later edits a stable vocabulary. Keep each slice covered by behavior tests that exercise real optimizer paths, not just private helper units.

Avoid introducing public API. These helpers are internal contracts between planner and resolver code. Names should be private or package-internal, and docs should reference spec decisions or symbol-qualified paths rather than line numbers.
