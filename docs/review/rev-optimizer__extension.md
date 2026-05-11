# Review: `django_strawberry_framework/optimizer/extension.py`

## High:

None.

## Medium:

### Fragment-spread recursion has no per-operation visited set

`_walk_directives` follows every `FragmentSpreadNode` into its `frag_def` via `fragments.get(frag_name)` but does not track which fragment names it has already descended into for the current walk. A single operation that spreads the same fragment from multiple call sites (a common pattern for shared field sets) will re-walk the fragment definition once per spread; an operation that nests fragments (`...A` referencing `...B` referencing `...A` is rejected by graphql-core validation, but `...A` referenced from two sibling selection-sets is normal) will repeatedly descend the same subtree.

Since this runs on every cache miss to build the cache key, the cost is bounded by the operation tree but is super-linear in fragment depth × spread count. The directive-variable set we ultimately return is a `frozenset`, so the redundant work produces no incorrect output — but it is wasted work directly on the request hot path. Recommend threading a `visited_fragments: set[str]` parameter through `_walk_directives` and skipping when a fragment name has already been expanded.

```django_strawberry_framework/optimizer/extension.py:117:129
    # Recurse into child selections.
    selection_set = getattr(node, "selection_set", None)
    if selection_set is not None:
        for child in selection_set.selections or ():
            _walk_directives(child, names, fragments)
            if isinstance(child, FragmentSpreadNode):
                frag_name = child.name.value if child.name else None
                frag_def = fragments.get(frag_name) if frag_name else None
                if frag_def is not None:
                    _walk_directives(frag_def, names, fragments)
```

### `**kwargs` pass-through in `__init__` silently accepts unknown kwargs

`DjangoOptimizerExtension.__init__(self, strictness: str = "off", **kwargs)` forwards `**kwargs` to `SchemaExtension.__init__`. Strawberry's base `SchemaExtension` accepts at most an `execution_context` kwarg today; in practice consumers configuring the extension via `DjangoOptimizerExtension(strictness="warn", strict=True)` (typo of `strictness`) would have the misspelled kwarg silently delivered to the base class, and depending on the upstream version either ignored or raised as a low-quality error far from the user's mistake. The extension's own surface is `strictness` only — there is no documented contract for forwarding additional kwargs.

Recommend either: (a) drop `**kwargs` entirely and let unexpected names raise `TypeError` at construction with a clear traceback, or (b) keep the parameter but validate that consumers do not pass through anything the extension cannot meaningfully consume. The current shape gives the worst of both worlds: it pretends to be flexible but the only consumer is `SchemaExtension`.

```django_strawberry_framework/optimizer/extension.py:279:288
    def __init__(
        self,
        strictness: str = "off",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if strictness not in ("off", "warn", "raise"):
            msg = f"strictness must be 'off', 'warn', or 'raise', got {strictness!r}"
            raise ValueError(msg)
```

### `check_schema` hint-shape dispatch couples to two distinct contracts

`check_schema` resolves an entry from `_optimizer_hints` and then dispatches on `hint is OptimizerHint.SKIP or hint.skip`. That single line is doing two unrelated things: identity-comparison against an enum member, and attribute access against a `Hints`-like object that exposes a `.skip` boolean. If a future hint shape lands that is neither the enum member nor a `.skip`-carrying record (e.g., a tuple, a callable, a string-keyed dict), this line will raise `AttributeError` deep inside an audit pass that is documented to "never raise."

The docstring promises "Always returns warnings — never raises"; the current dispatch can break that promise if the hint surface grows. Recommend extracting a `_hint_is_skip(hint) -> bool` helper centralized somewhere in `optimizer/hints.py` so the hint-shape contract has one owner, and `check_schema` and any future caller dispatch through it.

```django_strawberry_framework/optimizer/extension.py:471:478
            hints = getattr(type_cls, "_optimizer_hints", {})
            for field_name, meta in field_map.items():
                if not meta.is_relation:
                    continue
                # Skip fields opted out via OptimizerHint.SKIP.
                hint = hints.get(field_name)
                if hint is not None and (hint is OptimizerHint.SKIP or hint.skip):
                    continue
```

### Cache-key entries carry full printed-AST strings; eviction is FIFO regardless of plan size

`_build_cache_key` stores the entire `print_ast(operation)` string in every cache key. For large operations (deep nested fragments, many sibling fields) this is straightforwardly proportional to the document size, and the cache holds up to 256 entries. The current FIFO eviction sweep drops the oldest 64 on overflow, but eviction is triggered only by entry count, not by accumulated memory. A flood of large distinct operations against a server under memory pressure can hold ~256 × (document-size) bytes in `_plan_cache` keys alone before any sweep fires.

This is not a correctness defect and is unlikely to bite small consumers, but the cache-size knob (`_MAX_PLAN_CACHE_SIZE = 256`) does not reflect the actual memory cost; the docstring at lines 494–500 deliberately stores the printed string instead of its hash to avoid 64-bit collisions, which is correct, but worth noting in the artifact for the folder pass to consider whether the cache wants a configurable size or an LFU/LRU eviction.

```django_strawberry_framework/optimizer/extension.py:508:534
        operation = info.operation
        memo = _printed_ast_cache.get()
        if memo is None:
            doc_key = print_ast(operation)
        else:
            op_id = id(operation)
            doc_key = memo.get(op_id)
            if doc_key is None:
                doc_key = print_ast(operation)
                memo[op_id] = doc_key
        # ...
        return (doc_key, relevant_vars, target_model, runtime_path_from_info(info))
```

## Low:

### `_optimizer_active` ContextVar set in `on_execute` is not read in this module

`_optimizer_active` is declared at module scope and toggled in `on_execute`, but no read site exists in `extension.py`. It is presumably consumed by another module (`types/resolvers.py` is the likely candidate per the comment block on line 61–65 about cross-subpackage state). Worth confirming at the folder pass that the consumer still reads it; if no consumer reads it the toggle is dead state.

```django_strawberry_framework/optimizer/extension.py:140:143
_optimizer_active: ContextVar[bool] = ContextVar(
    "django_strawberry_framework_optimizer_active",
    default=False,
)
```

### `_MAX_PLAN_CACHE_SIZE` is a module constant with no settings escape hatch

The plan cache size is hard-coded at 256 and the eviction quarter is hard-coded at `// 4`. Consumers running schemas with very high operation-string cardinality (e.g., per-tenant query templating) have no knob today. Per `AGENTS.md` the rule is "add a settings key only when the feature that needs it lands" — leave the constant as-is for now, but if the project pass surfaces multiple "knob-shaped" constants in the optimizer it is worth grouping them.

```django_strawberry_framework/optimizer/extension.py:59:59
_MAX_PLAN_CACHE_SIZE = 256
```

### `_collect_directive_var_names` accepts `fragments=None` but converts via `or {}`

`_collect_directive_var_names(node, fragments=None)` then passes `fragments or {}` to `_walk_directives`. Empty-dict-ish fallback is the same `or` pattern flagged in the `conf.py` review (see worker-1 memory entry) and silently coerces a legitimately empty dict the same as `None`. Inside this file the input is always either `info.fragments` (always a dict, possibly empty) or `None` at the top-level call, so the behavior is safe today; flag for consistency with the folder-pass `or {}` pattern audit only.

```django_strawberry_framework/optimizer/extension.py:85:87
    names: set[str] = set()
    _walk_directives(node, names, fragments or {})
    return frozenset(names)
```

### `_resolve_model_from_return_type` and `_collect_schema_reachable_types` duplicate the `of_type` peel

Both helpers walk `while hasattr(..., "of_type"): ... = ...of_type` to unwrap graphql-core `GraphQLNonNull` / `GraphQLList`. The two implementations are textually identical at lines 196–197 (`_walk_gql_type`) and 243–244 (`_resolve_model_from_return_type`). Candidate for a tiny module-private helper `_unwrap_gql_type(t)`. Defer the actual move to the folder pass if the same peel appears in `walker.py` or `plans.py`.

```django_strawberry_framework/optimizer/extension.py:243:244
    rt = info.return_type
    while hasattr(rt, "of_type"):
        rt = rt.of_type
```

### `check_schema` iterates the full registry then filters by reachable set

`for _model, type_cls in registry.iter_types(): if type_cls not in reachable: continue` walks every registered type even when only a small subset is reachable. For the foundation slice the registry is small and the cost is negligible; the inverse loop (iterate `reachable` and look up each one's `field_map`) would be more direct and survives registry growth better. Low-priority readability win.

```django_strawberry_framework/optimizer/extension.py:461:464
        for _model, type_cls in registry.iter_types():
            if type_cls not in reachable:
                continue
```

## What looks solid

- Root-gate via `info.path.prev is None` and the `inspect.isawaitable` branch in `resolve` correctly handle both sync and async resolvers without forcing async-everywhere.
- `_printed_ast_cache` ContextVar lifecycle (set in `on_execute`, reset in `finally`) keeps the per-execution memo correctly isolated across concurrent async executions sharing one extension instance.
- The plan-cache key deliberately stores the printed AST string instead of its hash to dodge 64-bit collisions; the rationale is explicit in the docstring and is the right trade-off given plans encode ORM-level prefetch decisions.
- FIFO eviction only triggers for `cacheable` plans, so uncacheable plans (e.g., those depending on un-key-able state) do not churn the cache.
- The `convert_selections` lazy import is well-commented and correctly avoids a hard import-time dependency on Strawberry's internal `strawberry.types.nodes` surface for callers that only instantiate the extension.
- `_publish_plan_to_context` defensively copies `plan.fk_id_elisions` and `plan.planned_resolver_keys` into fresh sets before stashing, so downstream consumers cannot mutate the cached plan's internals.
- The static helper `scripts/review_inspect.py` was run; the Django/ORM markers and control-flow hotspots tables informed the Medium findings above.

---

### Summary:

`extension.py` is the optimizer's root-resolver gate and plan-cache owner; the load-bearing logic (root-gating, sync/async branching, ContextVar lifecycle, plan-cache key construction) is correct and well-documented. The four Medium findings are all hot-path quality issues rather than correctness bugs: fragment-spread re-walk in `_walk_directives`, the over-permissive `**kwargs` pass-through in `__init__`, the multi-contract hint dispatch in `check_schema`, and the un-memory-bounded cache-key strings in `_build_cache_key`. The Low findings (dead-looking `_optimizer_active` toggle, `or {}` pattern reuse, `of_type` peel duplication, registry iteration in `check_schema`) are mostly folder-pass follow-ups — confirm at the folder pass that `_optimizer_active` has a reader in `types/resolvers.py`, audit whether the `of_type` peel pattern appears in sibling files, and watch for repeated wire-key string-literal patterns across `extension.py` / `walker.py` / `plans.py` / `_context.py`.

## Verification

PASS — 2026-05-10.

- Medium 1 (fragment-spread re-walk): addressed. `_walk_directives` now threads `visited_fragments: set[str]`, marks the fragment name before descent, and the public wrapper `_collect_directive_var_names` seeds an empty set. Two new tests in `tests/optimizer/test_extension.py` (`test_walk_directives_visits_each_fragment_once_across_sibling_spreads`, `test_walk_directives_handles_unresolved_fragment_name`) pin both one-visit semantics and the unresolved-name path.
- Medium 2 (`**kwargs` pass-through): addressed. `__init__` signature drops `**kwargs`; `super().__init__()` is called bare with a source comment naming the typo-absorption hazard. `test_extension_rejects_unknown_kwargs_at_construction` pins the `TypeError` surface.
- Medium 3 (hint-shape dispatch coupling): addressed. New `hint_is_skip` helper in `optimizer/hints.py` centralises the dispatch and defensively returns `False` for unknown shapes (preserving the audit's "never raises" contract). `check_schema` dispatches through it. `test_hint_is_skip_handles_sentinel_record_and_unknown_shapes` pins all four shapes including `object()` with no `.skip`.
- Medium 4 (cache-key memory): intentional retain. Artifact text explicitly routes this to the folder pass ("worth noting in the artifact for the folder pass to consider"); deferral matches the contract.
- Low 1–5: intentional retain — each is explicitly tagged as folder-pass follow-up or "leave as-is for now" in the artifact body.
- `uv run pytest tests/optimizer -q`: 223 passed. extension.py reports 100% coverage. The global `fail_under=100` "failure" is the focused-run artifact noted in prior cycles, not a regression.
