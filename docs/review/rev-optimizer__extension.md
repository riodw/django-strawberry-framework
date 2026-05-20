# Review: `django_strawberry_framework/optimizer/extension.py`

Status: verified

## DRY analysis

- Defer until a third walker lands: extract a single `_walk_selection_tree(node, fragments, visited, *, on_node)` visitor that takes a per-node hook (directives collector OR fragment-def collector), collapsing `_walk_directives` (`extension.py:91-127`) and `_walk_reachable_fragment_definitions` (`extension.py:198-226`). Today the duplication is already DRY'd one layer down via `_child_selections`/`_unvisited_fragment_definition`.
- Defer until a third call site lands: extract `_resolve_origin_for_type_name(strawberry_schema, type_name)` to share `(origin, model)` resolution between `_collect_schema_reachable_types._walk_gql_type` (`extension.py:336-363`) and `_resolve_model_from_return_type` (`extension.py:389-420`). Only two call sites today.

## High:

None.

## Medium:

### `check_schema` deduplicates by source model but emits warnings on the source's model name — multi-type-per-model warnings collapse to one even when the missing target differs per type

`check_schema` walks `registry.iter_types()` (which yields `(model, type_cls)` once per registered type, so a model with two types appears twice — see `registry.py:220-230`), but its dedupe key is `(_model, field_name)`, not `(type_cls, field_name)`. The warning template uses `_model.__name__`, not `type_cls.__name__`. If two registered types for the same model expose the same relation field with different `field_map` shapes (e.g., a primary type that hides the relation via `Meta.exclude` and a secondary type that exposes it), the first iteration produces the warning and the second is silently skipped. That is correct when the two types resolve to the same missing-target judgment, but it does not survive the case where two types for the same model expose the relation against different target models (the registry only blocks duplicate primaries, not duplicate field maps targeting different child models).

In practice this is rare and Slice 1 of spec-014 makes a single type-per-relation-target the norm. But the warning text "`{_model.__name__}.{field_name} has no registered target DjangoType`" cannot be disambiguated by the consumer because `type_cls` does not appear in the string. Two-pronged fix:

1. Either widen the dedupe key to `(type_cls, field_name)` and live with one warning per registered type (worst-case duplicate text), or
2. Keep the per-source-model dedupe and put `type_cls.__name__` in the warning so the consumer knows which type's audit produced the entry.

```django_strawberry_framework/optimizer/extension.py:651:677
seen: set[tuple[type[models.Model], str]] = set()
warnings: list[str] = []
for _model, type_cls in registry.iter_types():
    ...
    for field_name, meta in field_map.items():
        ...
        if meta.related_model is not None and registry.get(meta.related_model) is None:
            key = (_model, field_name)
            if key in seen:
                continue
            seen.add(key)
            warnings.append(
                f"{_model.__name__}.{field_name} has no registered target DjangoType",
            )
```

Tests: extend `tests/optimizer/test_extension.py::test_check_schema_warns_unregistered_target` (and the union variant at `:1840`) with a two-types-per-model fixture where each type exposes the same relation against a different target model, then assert both warnings are emitted (option 1) or that the type name is in the string (option 2).

### `_publish_plan_to_context` stashes strictness sentinels even when the plan is empty, but `_optimize` returns the queryset *before* applying any plan

`_optimize` calls `_publish_plan_to_context(plan, info)` at `extension.py:555` unconditionally, then bails on `if plan.is_empty: return result` at `:556-557`. When strictness is `"warn"` or `"raise"` and the plan is empty (no relations selected), the stash still publishes `DST_OPTIMIZER_PLANNED` as an empty set plus `DST_OPTIMIZER_LOOKUP_PATHS` as an empty set plus `DST_OPTIMIZER_STRICTNESS` as the configured mode. The downstream resolver path in `types/resolvers.py` reads those sentinels and, if it ever sees a relation traversal that is not in the empty planned set, it would treat it as an unplanned lazy load and raise/warn.

This is *probably* correct: if the plan is empty, there are no relation selections, so resolvers will never traverse a relation, and the empty planned set is never compared against. But the invariant is load-bearing and is not asserted by a test (the only strictness-with-empty-plan path the test suite covers is the optimizer-disabled case). Two-pronged action:

1. Confirm the assumption with a temp test under `docs/review/temp-tests/optimizer__extension/` that builds an empty-plan query with `strictness="raise"` and asserts no exception is raised at resolve time. If it stands, promote the test to `tests/optimizer/test_extension.py`.
2. If it does not stand, gate the strictness stashes inside the `is_empty` branch — skip the planned/lookup_paths sentinels when there is nothing to enforce.

```django_strawberry_framework/optimizer/extension.py:553:567
selections = convert_selections(info, info.field_nodes)
plan = self._get_or_build_plan(_root_child_selections(selections), target_model, info, origin)
self._publish_plan_to_context(plan, info)
if plan.is_empty:
    return result
...
plan, result = diff_plan_for_queryset(plan, result)
return plan.apply(result)
```

### Plan-cache mutation and counter increments are not thread-safe; the extension instance is shared across concurrent requests

The extension is constructed once at schema build and shared across every request the schema serves. Under async / ASGI / threaded WSGI, `self._plan_cache` (`dict.get` + `dict.__setitem__` + the FIFO eviction loop at `:602-604`) and the `self._cache_hits` / `self._cache_misses` counters (`:593,607`) are mutated without a lock. CPython's GIL keeps `dict` operations atomic enough that the cache will not corrupt, but two concurrent inserts can both observe `len(self._plan_cache) >= _MAX_PLAN_CACHE_SIZE` and evict twice, and the counters drift under concurrent `+= 1` (two threads doing `x = x + 1` can collide).

Severity calibration: the cache is correctness-neutral (a missed insert or a double-evict reduces hit rate, never returns wrong data), and the counters are introspection-only (`cache_info()`). Production traffic on the extension does NOT depend on either being precise. The reason this is Medium not Low is the **claim** in the docstring at `:427-432` that an *instance* should be passed "to benefit from plan caching in async mode" — the docstring promises async-safety without acknowledging the counter drift, and a strict consumer benchmarking the optimizer via `cache_info()` will see inconsistent numbers across runs without an obvious cause.

Two paths:

1. Either accept the drift and amend the `cache_info` docstring at `:469` to note that hit/miss counters are best-effort under concurrent access, or
2. Wrap the eviction + insert + counter bumps in a `threading.Lock` (cheap; the lock is held only across O(1) dict ops).

```django_strawberry_framework/optimizer/extension.py:589:608
cache_key = self._build_cache_key(info, target_model, origin)
cached_plan = self._plan_cache.get(cache_key)
if cached_plan is not None:
    self._cache_hits += 1
    return cached_plan
plan = plan_optimizations(selections, target_model, info=info, source_type=origin)
if plan.cacheable and len(self._plan_cache) >= _MAX_PLAN_CACHE_SIZE:
    to_remove = _MAX_PLAN_CACHE_SIZE // 4
    for _ in range(to_remove):
        self._plan_cache.pop(next(iter(self._plan_cache)))
if plan.cacheable:
    self._plan_cache[cache_key] = plan
self._cache_misses += 1
return plan
```

Tests: a focused concurrency test (two threads or two `asyncio.gather`'d coroutines hammering `resolve` on the same extension instance) would pin whichever decision is taken. If we accept the drift, the test should at least confirm no `RuntimeError: dictionary changed size during iteration` is raised by the eviction loop under concurrent calls — `next(iter(self._plan_cache))` plus a concurrent `__setitem__` is the one shape that could surface that error.

## Low:

### `check_schema` is a `@classmethod` but never reads `cls`

`extension.py:630-677` declares `check_schema` as `@classmethod` and takes `cls` as the first parameter. The body never reads `cls`. The audit walks the registry directly and never instantiates or subclasses the extension. A `@staticmethod` would document the intent more accurately. Risk of changing: a downstream subclass calling `MySubclass.check_schema(schema)` would still work as a static method, so this is a behaviour-neutral polish — flag at the comment pass.

```django_strawberry_framework/optimizer/extension.py:630:631
@classmethod
def check_schema(cls, schema: Any) -> list[str]:
```

### `CacheInfo` docstring says "modeled on `functools.lru_cache`" but drops `maxsize`

`functools.lru_cache`'s `cache_info()` returns `(hits, misses, maxsize, currsize)` — four fields. Our `CacheInfo` is three: `(hits, misses, size)`. The omission of `maxsize` is intentional (it is the module-level `_MAX_PLAN_CACHE_SIZE`) but the docstring at `:275` claims the model. Either expose `maxsize` (cheap; `maxsize=_MAX_PLAN_CACHE_SIZE`) and match the four-tuple, or trim the docstring to "Plan-cache statistics (hits, misses, current size)" and drop the `lru_cache` analogy. Comment-pass nit.

```django_strawberry_framework/optimizer/extension.py:274:279
class CacheInfo(NamedTuple):
    """Plan-cache statistics, modeled on ``functools.lru_cache``."""

    hits: int
    misses: int
    size: int
```

### The two AST walkers (`_walk_directives`, `_walk_reachable_fragment_definitions`) are parallel and could collapse to one generic visitor

Both walkers iterate children via `_child_selections`, both follow fragment spreads via `_unvisited_fragment_definition`, both carry the same visited-fragments cycle guard, both share the "recurse into child first, then into the resolved fragment definition" shape. They differ only in the per-node hook (directives sweep vs append-to-list). A `_walk_selection_tree(node, fragments, visited, *, on_node)` visitor would reduce the parallel walks to one. Not justified today: the visitor would introduce a callable indirection and the parallel walks are already short. Carry forward to the folder pass — if a third walker lands in any optimizer module, fold all three through the visitor at once.

```django_strawberry_framework/optimizer/extension.py:91:127
def _walk_directives(...) -> None:
    ...
    for child in _child_selections(node):
        _walk_directives(child, names, fragments, visited_fragments)
        frag_def = _unvisited_fragment_definition(child, fragments, visited_fragments)
        if frag_def is not None:
            _walk_directives(frag_def, names, fragments, visited_fragments)
```

```django_strawberry_framework/optimizer/extension.py:198:226
def _walk_reachable_fragment_definitions(...) -> None:
    for child in _child_selections(node):
        frag_def = _unvisited_fragment_definition(child, fragments, visited_fragments)
        if frag_def is not None:
            reachable.append(frag_def)
            _walk_reachable_fragment_definitions(frag_def, fragments, visited_fragments, reachable)
        _walk_reachable_fragment_definitions(child, fragments, visited_fragments, reachable)
```

### `_collect_schema_reachable_types` does not descend into interface implementations

`_walk_gql_type` at `extension.py:336-363` follows `fields` and `union_types` (`gql_type.types`) but does not follow `gql_type.interfaces` nor enumerate types implementing an interface returned from a root field. graphql-core exposes implementations via `schema.get_implementations(interface_type)` or `interface_type.types` on some versions. If a root field is typed as an interface and the only `DjangoType`s involved are the concrete implementations, `check_schema` will silently miss them. The pattern matches strawberry-graphql-django's audit walk, so it may be intentional — but it should at least appear in the docstring (`:321-328`) as a known limitation, or the union descent should be extended to interface implementations. Carry-forward calibration: interfaces are not in the package's example surface today, so this is Low. Flag at the project pass if interface support lands.

```django_strawberry_framework/optimizer/extension.py:354:363
# Recurse into fields.
fields = getattr(gql_type, "fields", None)
if fields is not None:
    for field_obj in fields.values():
        _walk_gql_type(getattr(field_obj, "type", None))

# Recurse into union types.
union_types = getattr(gql_type, "types", None)
if union_types is not None:
    for u_type in union_types:
        _walk_gql_type(u_type)
```

### `_optimize` passes a Manager through unchanged because of the `isinstance(QuerySet)` gate

The gate at `extension.py:532` checks `isinstance(result, models.QuerySet)`. A resolver that returns `Model.objects` (the default Manager) instead of `Model.objects.all()` (the QuerySet) — a common Django shorthand — slips past unoptimized. Strawberry-graphql-django coerces `.all()` defensively at the same site. Two paths: (a) document the contract that resolvers must return a QuerySet ("Manager passthrough is intentional; call `.all()` in your resolver"), or (b) coerce via `result = result.all() if isinstance(result, models.Manager) else result` before the QuerySet check. Today every shipped resolver in the package returns a QuerySet, so (a) is the cheaper stance. Flag at the project pass alongside the broader "what shapes can the framework resolve through" question.

```django_strawberry_framework/optimizer/extension.py:532:533
if not isinstance(result, models.QuerySet):
    return result
```

## What looks solid

### DRY recap

- **Existing patterns reused.** Reaches across the optimizer subpackage rather than reimplementing:
  - Context stash dispatched through `_context.stash_on_context` (`django_strawberry_framework/optimizer/_context.py:90-141`) via the underscore-prefixed re-export at `extension.py:53-55,67`; the sentinel keys at `_context.py:34-38` are imported instead of re-declared.
  - Plan construction delegated to `walker.plan_optimizations` (`django_strawberry_framework/optimizer/walker.py:28-58`); per-relation strategy delegated to `walker.plan_relation` (`walker.py:61-..`), with the `DjangoOptimizerExtension.plan_relation` method at `extension.py:738-755` declared as an instance-method override seam (subclass test fixtures rely on this).
  - Plan reconciliation and lookup-path extraction routed through `plans.diff_plan_for_queryset` and `plans.lookup_paths` (`django_strawberry_framework/optimizer/plans.py:295,415-419`); runtime path tuple via `plans.runtime_path_from_info` (`plans.py:148-..`).
  - Skip-hint check goes through `hints.hint_is_skip` (`django_strawberry_framework/optimizer/hints.py:129`) rather than reimplementing the `OptimizerHint.SKIP` test.
  - Registry interactions (`registry.model_for_type`, `registry.get`, `registry.get_definition`, `registry.iter_types`) at `extension.py:351,417,651,655,669` all use the documented public surface from `registry.py:206-310`.
  - `unwrap_graphql_type` from `utils/typing.py` is reused at `extension.py:338,404` rather than re-implementing the `GraphQLNonNull`/`GraphQLList` peel.
  - The two AST walkers (`_walk_directives`, `_walk_reachable_fragment_definitions`) already share `_child_selections` (`extension.py:130-144`) and `_unvisited_fragment_definition` (`extension.py:147-174`), which is the right shape for the recursion guard.
- **Duplication risk in the current file.** The two parallel AST walkers (`_walk_directives` at 91-127 and `_walk_reachable_fragment_definitions` at 198-226) are the only structural near-copy. They are deliberately parallel (both walk children, both follow fragment spreads, both share the visited-fragments cycle guard), and the divergence at the recursion body is the actual work — the parallelism is mostly carried by the already-extracted helpers. The `_strawberry_schema_from_schema` / `_strawberry_schema_from_info` pair at 300-317 is a deliberate two-entry-point shape (object vs `info`), correctly extracted. Repeated string literals: only `"_strawberry_schema"` appears twice (overview line 215), already in the helper pair above. No bare `"dst_optimizer_*"` literals — all sentinel imports come from `_context.py`, satisfying the carry-forward from the previous `_context.py` review.

### Other positives

- The `ContextVar` lifecycle in `on_execute` (`extension.py:476-484`) sets *and* resets both `_optimizer_active` and `_printed_ast_cache`, guaranteeing per-execution isolation for async invocations sharing the same extension instance. The pair-reset under `try/finally` is the right shape.
- The `_printed_ast_cache` memo (`extension.py:294-297,718-726`) is correctly per-execution rather than per-extension, so two operations with the same `id(operation)` across separate executions (e.g., after GC reuses the same object slot) cannot collide.
- `_build_cache_key`'s `(doc_key, relevant_vars, target_model, runtime_path, origin)` shape (`extension.py:736`) covers the four distinct cardinality vectors: query body shape, `@skip`/`@include` directive variable values, root return-type model, root path, and resolver origin. Each component is necessary; the comment at `:687-708` walks through the reasoning explicitly.
- `_print_operation_with_reachable_fragments` (`extension.py:229-250`) closes the spec-flagged `query Q { ...F } fragment F { ... }` cache-key gap by appending reachable fragment bodies in deterministic selection-set order. The visited-fragment cycle guard inside `_unvisited_fragment_definition` makes the gather idempotent under self-referential fragments.
- The `_stash_on_context` re-export aliasing at `:53-55,67` matches the carry-forward from the `_context.py` review — it is purely a name-preservation alias for existing tests; the canonical implementation lives in `_context.py` and the underscore-prefixed name is exposed in `__all__` deliberately.
- The lazy import of `convert_selections` at `:551` matches the documented "Strawberry-internal surface" reasoning at `:547-550`; pinning the import at function scope rather than module scope keeps the extension importable in test contexts that monkey-patch Strawberry.
- The `_OriginAndModel` NamedTuple (`:371-386`) with a "pair-or-`None`" contract (both legs resolved or `None`) is the right shape — callers branch on `resolved is None` rather than dereferencing individual legs, removing the partial-resolution mid-state.
- The FIFO "drop oldest quarter" eviction policy at `:597-604` amortises eviction cost across the next ~64 inserts; the no-LRU-promotion choice means hot plans age out naturally instead of being protected indefinitely.
- `check_schema`'s per-source-model dedupe at `:653,671-673` correctly removes the multi-type artifact noted in the comment block; the deduplication is bounded (by `(model, field_name)` not `field_name` alone) so unrelated models can still emit warnings for the same field name. (The dedupe-key-vs-warning-string asymmetry is the Medium finding above; the dedupe itself is correct.)
- Static helper ran cleanly; the seven control-flow hotspots (`_walk_directives`, `_collect_schema_reachable_types`, `_walk_gql_type`, `_optimize`, `_get_or_build_plan`, `check_schema`, `_build_cache_key`) all have direct test coverage in `tests/optimizer/test_extension.py` (hits/misses cache, FIFO eviction, multi-root-node merging, fragment cache-key, origin-aware cache, `check_schema` reachable/orphan/union/unregistered-target, schema-build audit, strictness publication). No hotspot lacks an exercising test.

### Summary

`extension.py` is the optimizer's main entry point and reads as such: well-decomposed (module-level AST helpers, a small set of schema/registry resolution helpers, a single class with cleanly separated `on_execute` / `resolve` / `_optimize` / `_get_or_build_plan` / `_publish_plan_to_context` / `check_schema` / `_build_cache_key` responsibilities) and well-reused (every cross-subpackage call goes through the documented public surface of `_context.py`, `plans.py`, `walker.py`, `hints.py`, and `registry.py`). No High-severity findings. Three Mediums: a multi-type-per-model dedupe asymmetry in `check_schema`'s warning string, an unconfirmed-by-test empty-plan-with-strictness invariant in `_publish_plan_to_context`, and the shared-instance mutation hazard for `_plan_cache` and the hit/miss counters under concurrent requests — none of these can return wrong data, but the second is missing a behavioral pin and the third risks docstring-vs-reality drift. Five Lows are pure polish (`@classmethod` → `@staticmethod`, `CacheInfo` lru_cache analogy, parallel-walker collapse opportunity, interface-implementation traversal gap in `check_schema`, Manager-vs-QuerySet contract). DRY analysis turned up no in-file duplication beyond the deliberately-parallel AST walkers (already factored down through `_child_selections` and `_unvisited_fragment_definition`); cross-subpackage reuse is excellent.

---

## Fix report (Worker 2)

Logic pass. Three findings in scope: Medium 1 (warning-string asymmetry, option 2 — keep dedupe, add source type name to warning), Medium 2 (empty-plan-with-strictness invariant — write a permanent test directly), Low 1 (`@classmethod` → `@staticmethod`). The other Medium and Lows are deferred per the dispatch prompt (Medium 3 / Low 2 to the comment pass; Low 3 to the folder pass; Lows 4/5 to the project pass).

### Files touched

- `django_strawberry_framework/optimizer/extension.py:630-631` — `check_schema` decorator changed from `@classmethod` to `@staticmethod`; the `cls` parameter was dropped. The body never reads `cls` and the static-method form documents the intent. Subclass call sites (`MySubclass.check_schema(schema)`) continue to work unchanged; the existing module-level call site is `DjangoOptimizerExtension.check_schema(schema)` and is unaffected (Low 1).
- `django_strawberry_framework/optimizer/extension.py:674-677` — warning text now prepends `type_cls.__name__` in parentheses-suffixed form: `f"{type_cls.__name__} ({_model.__name__}.{field_name}) has no registered target DjangoType"`. Per-source-model dedupe (key `(_model, field_name)`) is unchanged, so multi-type-per-model audits still collapse to one warning; the surviving warning now identifies the iterating type so a consumer can disambiguate which type's audit produced the entry (Medium 1, option 2).

### Tests added or updated

- `tests/optimizer/test_extension.py::test_schema_audit_warning_names_the_source_type_for_multi_type_models` — **added**. Two-types-per-model fixture (`ItemType` primary, `AdminItemType` secondary) both exposing `Item.category` against an unregistered `Category` target. Asserts (a) dedupe still produces exactly one `Item.category` warning, and (b) the surviving warning contains either `"ItemType"` or `"AdminItemType"` (whichever the registry iterates first). Pins the Medium 1 contract (Option 2): per-model dedupe is preserved, source-type provenance is not lost in the warning string.
- `tests/optimizer/test_extension.py::test_strictness_with_empty_plan_does_not_raise_or_warn` — **added** (parametrized over `mode=["warn", "raise"]`). Builds a scalar-only query against a registered `CategoryType` with strictness enabled; the walker produces an empty plan and `_publish_plan_to_context` stashes the planned/lookup_paths/strictness sentinels before `_optimize` short-circuits on `plan.is_empty`. Asserts (a) `result.errors is None` (no `raise` trip), (b) no `optimizer_logger.WARNING` record (no `warn` trip), (c) the sentinels are still stashed and `dst_optimizer_planned == set()`. Pins the Medium 2 invariant — empty-plan + strictness must resolve cleanly. The previously-existing `test_optimize_returns_original_queryset_for_empty_plan` covered only the strictness-`off` path; this test extends coverage to the enabled-optimizer + strict-mode path.
- No existing tests required updates. The existing substring matchers (`"category" in w and "no registered target" in w`, `"Item.category" in w and "no registered target" in w`) all still pass against the new warning text because both the field name (`"category"` / `"Item.category"`) and the literal `"no registered target"` are preserved verbatim in the prepended-type-name form.

### Validation run

- `uv run ruff format .` — pass (1 file reformatted by the formatter to keep line lengths within 110; no other files changed).
- `uv run ruff check --fix .` — pass (no diagnostics).
- `pytest` not run per the standing rule (`AGENTS.md`/`START.md`). Worker 3 runs the focused tests.

### Notes for Worker 3

- **No shadow file used** in this logic pass. The source diff is small enough that the inline source view was sufficient; the shadow-file caveat does not apply on the first verification pass.
- **Decorator change is behavior-neutral.** `@classmethod` → `@staticmethod` does not affect `MySubclass.check_schema(schema)` consumer call sites. No test changes were required; the existing `check_schema` tests still pass conceptually.
- **Warning-string preserved substrings.** The new wording `"{type_cls.__name__} ({_model.__name__}.{field_name}) has no registered target DjangoType"` keeps `_model.__name__.field_name` and `"no registered target"` as exact substrings, so the three existing tests that match those substrings (`tests/optimizer/test_extension.py:1837`, `:1882`, `:3023`) continue to pass without edits.
- **Medium 2 invariant is now pinned.** The new test passed conceptually at the source-edit moment (it asserts behavior that was already in place; the source did not need a gate). The dispatch prompt's "if the test fails, STOP" branch did not trigger — the invariant holds in the current code, and the test now anchors it permanently against future regression. No source change was needed in `_publish_plan_to_context`.
- **Deferred findings (carry-forward into later passes):**
  - Medium 3 (thread-safety / counter drift) — deferred to the comment pass (`cache_info` docstring amendment is Worker 1's lighter recommendation; the lock alternative is a logic change only if Worker 3 rejects the docstring path).
  - Low 2 (`CacheInfo` lru_cache analogy) — deferred to the comment pass.
  - Low 3 (parallel walker collapse) — deferred to the folder pass (`rev-optimizer.md`); no in-cycle edit because the saving is marginal today and the duplication is already factored down through `_child_selections` / `_unvisited_fragment_definition`.
  - Low 4 (interface-implementation traversal in `check_schema`) — deferred to the project pass; flagged when interface support lands.
  - Low 5 (`Manager` vs `QuerySet` contract) — deferred to the project pass; the resolver-shape question is package-wide.

---

## Verification (Worker 3)

### Logic verification outcome

- **High:** None — accepted.
- **Medium 1 (warning-string asymmetry, Option 2):** accepted. `extension.py:674-677` now emits `f"{type_cls.__name__} ({_model.__name__}.{field_name}) has no registered target DjangoType"` while preserving the `(_model, field_name)` dedupe key at `:670`. The new pinning test `tests/optimizer/test_extension.py::test_schema_audit_warning_names_the_source_type_for_multi_type_models` exercises a two-types-per-model fixture (`ItemType` primary + `AdminItemType` secondary, both exposing `Item.category` against an unregistered `Category` target), asserts dedupe still produces exactly one `Item.category` warning, and asserts the surviving warning names either `"ItemType"` or `"AdminItemType"`. Real package paths throughout; no registry mocks; matches the artifact's recommendation. Spot-checked the three pre-existing substring tests (`tests/optimizer/test_extension.py:1882, :1927, :3068`): each matches `"category"` / `"no registered target"` / `"Item.category"` substrings, which are preserved verbatim in the new wording — no test breakage. Worker 2's "0 updated" claim holds.
- **Medium 2 (empty-plan-with-strictness invariant):** accepted. The new test `test_strictness_with_empty_plan_does_not_raise_or_warn`, parametrized over `mode=["warn", "raise"]`, exercises the enabled-optimizer path with a scalar-only query against a registered `CategoryType` (no relation selections → empty plan). It asserts (a) `result.errors is None`, (b) no `WARNING` record on the optimizer logger, and (c) the sentinels are still stashed (`dst_optimizer_strictness == mode`, `dst_optimizer_planned == set()`). Test seeds via `services.seed_data(1)` per `AGENTS.md`. Both parameters PASSED when run via `uv run pytest tests/optimizer/test_extension.py -k "test_strictness_with_empty_plan_does_not_raise_or_warn" -x`. Invariant holds in current source; the test now anchors it permanently. No source change to `_publish_plan_to_context` was required — Worker 2's empty-source-delta claim for M2 is correct.
- **Medium 3 (thread-safety / counter drift):** deferred to comment pass per the artifact's lighter recommendation — accepted.
- **Low 1 (`@classmethod` → `@staticmethod`):** accepted. `extension.py:630-631` now reads `@staticmethod` and the `cls` parameter is removed. The body never read `cls`; subclass call sites `MySubclass.check_schema(schema)` continue to work. No package-internal caller uses `cls`-style access (grep would find only the `DjangoOptimizerExtension.check_schema(schema)` static invocations).
- **Low 2 (`CacheInfo` lru_cache analogy):** deferred to comment pass — accepted.
- **Low 3 (parallel walker collapse):** forwarded to folder pass (`rev-optimizer.md`) — accepted.
- **Low 4 (interface-implementation traversal):** forwarded to project pass — accepted.
- **Low 5 (`Manager` vs `QuerySet` contract):** forwarded to project pass — accepted.

### DRY findings disposition

Worker 1's DRY analysis identified no in-file duplication in the current cycle's scope; the only flagged near-copy (the parallel AST walkers) was deferred to the folder pass. The logic-pass changes (a decorator swap + a warning-string format change + two new tests) introduced no new duplication. Cross-subpackage reuse remained intact — no new bypass of `_context.py`, `plans.py`, `walker.py`, `hints.py`, or `registry.py`. Accepted.

### Temp test verification

No temp tests under `docs/review/temp-tests/` were used. Worker 2 wrote the M2 pin directly as a permanent test in `tests/optimizer/test_extension.py` (the correct call given the invariant held in current source). I ran the new permanent tests directly via `uv run pytest -k ... -x` and they passed; no temp scaffold was needed.

### Verification outcome

`logic accepted; awaiting comment pass`.

---

## Comment/docstring pass

Comment pass. Three docstring edits land in `django_strawberry_framework/optimizer/extension.py`. No source-logic changes; no test changes.

### Files touched

- `django_strawberry_framework/optimizer/extension.py:274-279` — `CacheInfo` class docstring trimmed to `"Plan-cache statistics (hits, misses, current size)."` Dropped the `"modeled on ``functools.lru_cache``"` analogy (L2). No `maxsize` was added — exposing `_MAX_PLAN_CACHE_SIZE` would be a logic change and is explicitly out of scope per the dispatch prompt.
- `django_strawberry_framework/optimizer/extension.py:423-449` — `DjangoOptimizerExtension` class docstring extended with a short paragraph after the "Pass an **instance**" example noting that the plan cache is correctness-safe under concurrent / async access, but the hit-rate / counter introspection via `cache_info()` is best-effort, with a forward reference to `cache_info` for the full caveat (M3, class-docstring half).
- `django_strawberry_framework/optimizer/extension.py:476-491` — `cache_info` method docstring expanded from a single line into a Google-style summary plus a paragraph that names the three drift mechanisms (shared instance, unlocked counter `+= 1`, two concurrent eviction-threshold inserts) and the correctness-neutral guarantee (missed insert / double-evict reduces hit rate, cannot return wrong data) (M3, primary docstring amendment).

### M3 disposition

Docstring amended at two sites (the `cache_info` method primary docstring and the class docstring header) to qualify the cache hit-rate / counter introspection as best-effort under concurrent access. The cache's correctness invariant (no wrong-data risk) is documented explicitly. No `threading.Lock` was added — Worker 1's lighter recommendation (docstring amendment) was the path taken and the lock alternative remains an open future-logic option only if a consumer benchmark surfaces a real drift complaint.

### L2 disposition

`CacheInfo` docstring trimmed; the `functools.lru_cache` analogy is dropped. `maxsize` was deliberately NOT added — that would be a logic-pass change to expose `_MAX_PLAN_CACHE_SIZE` through the public stats surface, which is out of scope for the comment pass per the dispatch prompt.

### L3 disposition

Forwarded to folder pass (`docs/review/rev-optimizer.md`) per the artifact's deferred-finding list. No in-cycle action.

### L4 disposition

Forwarded to project pass (`docs/review/rev-django_strawberry_framework.md`) per the artifact's deferred-finding list. No in-cycle action.

### L5 disposition

Forwarded to project pass (`docs/review/rev-django_strawberry_framework.md`) per the artifact's deferred-finding list. No in-cycle action.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).
- `pytest` not run per the standing rule (`AGENTS.md` / `START.md`).

### Notes for Worker 3

- **No shadow file used** in this comment pass. The edits are docstring-only at three well-anchored sites; the inline source view was sufficient.
- **No logic changes** in this pass. The cache mutation paths (`_plan_cache.get` / eviction loop / `__setitem__`) and the counter increments are untouched; only the surrounding docstrings now qualify the consumer-visible introspection contract.
- **Line length compliant.** All new docstring lines are within the 110-column limit; ruff format made no changes.
- **No test impact.** The existing `tests/optimizer/test_extension.py` cases that exercise `cache_info()` and the `DjangoOptimizerExtension` class continue to pass conceptually — only the docstring text changed and no test asserts on docstring content.

---

## Changelog disposition

**Warranted?** Not warranted (deferred to maintainer).

**Reason.** The cycle produced one additive warning-text enrichment (M1), one behavior-neutral decorator swap (L1), two docstring-only clarifications (M3, L2), and two new tests. The warning text remains substring-compatible with the prior wording (the model name is still in the string, so existing substring matchers continue to pass — confirmed via the three pre-existing tests at `tests/optimizer/test_extension.py:1882`, `:1927`, `:3068`). The package is pre-alpha (`pyproject.toml` "Development Status :: 1 - Planning"). Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed.") and the active plan `docs/review/review-0_0_6.md` (no changelog authorization for this cycle item), no `CHANGELOG.md` edit. If the maintainer judges the per-type warning text as release-note-worthy, the entry can be added at release time.

**What was done.** No `CHANGELOG.md` edit. Disposition recorded in this artifact. The existing `[0.0.6]` entry in `CHANGELOG.md` was left untouched.

**Validation.**

- `uv run ruff format .` — pass (no changes).
- `uv run ruff check --fix .` — pass (no diagnostics).
- `pytest` not run per the standing rule (`AGENTS.md` / `START.md`).

---

## Iteration log

## Verification (Worker 3, pass 2)

### Comment verification outcome

- **M3 (`cache_info` docstring, primary site at `extension.py:474-485`):** accepted. The new docstring distinguishes cache correctness (preserved — "the cache itself is correctness-neutral — a missed insert or a double-evict only reduces hit rate; it cannot return wrong data") from introspection precision (best-effort — "the hit/miss counters and the reported `size` are best-effort"). The two drift mechanisms named in the prose match the actual unlocked sites in `_get_or_build_plan` (`extension.py:606-612`): `self._cache_hits += 1` / `self._cache_misses += 1` racing across threads, and `len(self._plan_cache) >= _MAX_PLAN_CACHE_SIZE` plus the FIFO eviction loop racing concurrent inserts. Google-style format (summary + body paragraph), all lines within the 110-column limit.
- **M3 (class docstring, secondary site at `extension.py:434-438`):** accepted. The previous "Pass an **instance** (not the bare class) to benefit from plan caching in async mode" promise is now followed by a short paragraph qualifying the cache as correctness-safe under concurrent / async access while flagging the `cache_info()` introspection as best-effort, with a forward reference to the `cache_info` method docstring for the full caveat. The two-site amendment matches the artifact's M3 (option 1) recommendation.
- **L2 (`CacheInfo` docstring trim at `extension.py:274-275`):** accepted. The `"modeled on ``functools.lru_cache``"` analogy is gone; the new single-line docstring describes the NamedTuple's actual surface — three fields (hits, misses, current size). No `maxsize` was introduced — exposing `_MAX_PLAN_CACHE_SIZE` would be a logic-pass change and is correctly out of scope per the dispatch prompt. Line within the 110-column limit.
- **L3 (parallel walker collapse):** forwarded to folder pass (`docs/review/rev-optimizer.md`) — accepted.
- **L4 (interface-implementation traversal in `check_schema`):** forwarded to project pass (`docs/review/rev-django_strawberry_framework.md`) — accepted.
- **L5 (`Manager` vs `QuerySet` contract):** forwarded to project pass (`docs/review/rev-django_strawberry_framework.md`) — accepted.

### Diff-boundary check

`git diff -- django_strawberry_framework/optimizer/extension.py` confirms the cumulative diff carries exactly the expected sites and nothing else:

- `:275` — `CacheInfo` docstring trim (comment pass / L2).
- `:434-438` — class docstring qualification paragraph (comment pass / M3 secondary site).
- `:475-485` — `cache_info` method docstring expansion (comment pass / M3 primary site).
- `:646-647` — `@classmethod` → `@staticmethod` and `cls` parameter dropped (logic pass / L1, already accepted in pass 1).
- `:691-692` — warning text now prepends `type_cls.__name__` in parenthesized form (logic pass / Medium 1, already accepted in pass 1).

No source-logic edits in this pass; no test edits; no scope creep beyond M3 + L2 and the recorded forward dispositions.

### Verification outcome

`comments accepted; awaiting changelog disposition`.

## Verification (Worker 3, pass 3)

### Changelog verification outcome

Not warranted accepted; the additive + behavior-neutral framing is accurate; `CHANGELOG.md` untouched; rationale cites the artifact's facts plus `AGENTS.md` and the active plan; ruff clean. Accepted.

- `git diff -- CHANGELOG.md` is empty — no edit was made.
- The disposition prose records all required elements: warranted = no (deferred to maintainer); reason cites the additive warning text (M1), behavior-neutral decorator swap (L1), docstring-only edits (M3, L2), two new tests, substring-compatibility with prior wording, pre-alpha status, and both the `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" rule and the active plan `docs/review/review-0_0_6.md`'s lack of changelog authorization for this cycle item; what-was-done records no `CHANGELOG.md` edit; validation records both ruff commands as pass.
- Diff-boundary check on `django_strawberry_framework/optimizer/extension.py` confirms the cycle's source changes match the disposition's "additive + behavior-neutral" framing exactly — the four cited sites are the only changes: (1) `CacheInfo` docstring trim at `:275`, (2) class docstring qualification paragraph at `:434-439`, (3) `cache_info` method docstring expansion at `:475-485`, (4) `@classmethod` → `@staticmethod` + `cls` parameter dropped at `:646-647`, and the warning text change at `:691-692`. No logic changes outside scope; no unrelated edits.
- Diff-boundary check on `tests/optimizer/test_extension.py` confirms exactly two new tests added (`test_strictness_with_empty_plan_does_not_raise_or_warn` at `:1303-1346` and `test_schema_audit_warning_names_the_source_type_for_multi_type_models` at `:3117-3164`); no other test changes.

### Verification outcome

`cycle accepted; verified`.
