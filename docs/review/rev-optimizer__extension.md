# Review: `django_strawberry_framework/optimizer/extension.py`

## High:

None.

## Medium:

### Plan-cache key uses `hash(print_ast(operation))` rather than the printed string

`_build_cache_key` reduces the operation AST to `hash(print_ast(operation))`. `hash()` of a string is process-stable but bounded to 64 bits, which means two distinct operations whose printed AST happens to collide will share a cached plan. The probability is astronomically small under SipHash, but the cost of a collision is "wrong queryset optimization applied" — which is the kind of bug that only surfaces in production with a synthetic-looking failure. Storing the printed string itself (or `id(operation)` for the same parsed-document instance plus a string fallback) eliminates the risk for what is in practice a kilobyte-or-so cache key.

Recommended: change the first key component from `hash(print_ast(operation))` to the `print_ast(operation)` string. The cache is bounded by `_MAX_PLAN_CACHE_SIZE = 256` entries with eviction, so the memory cost is small. If string memory becomes a concern, intern via `sys.intern` or hash with `hashlib.blake2b(..., digest_size=16)` for a wider hash. Add a unit test that constructs two operations whose `hash(print_ast(...))` collide (or simulate via monkeypatch on `hash`) and asserts they get distinct plans.

```django_strawberry_framework/optimizer/extension.py:437:448
operation = info.operation
doc_hash = hash(print_ast(operation))
...
return (doc_hash, relevant_vars, target_model, runtime_path_from_info(info))
```

### `print_ast(operation)` runs on every root resolver call, including cache hits

Every root resolver call computes `print_ast(operation)` to build the cache key, even when the same operation has already produced a plan. For large operations this is non-trivial CPU cost on the hot path — the very work the plan cache is meant to avoid. Memoizing the printed AST (or its hash) on the operation node identity (`id(operation)`) makes the second-and-onward call O(1).

Recommended: cache the printed AST keyed on `id(operation)` for the lifetime of one execution. A `WeakValueDictionary` keyed on the operation node, or a small `info.context`-scoped dict, both work. A simple alternative: precompute the hash once per operation in `on_execute` and stash it on `info.context`, then read it in `_build_cache_key`. Add a perf-shaped test only if feasible; otherwise document as a hot-path optimization.

```django_strawberry_framework/optimizer/extension.py:336:344
cache_key = self._build_cache_key(info, target_model)
cached_plan = self._plan_cache.get(cache_key)
if cached_plan is not None:
    self._cache_hits += 1
    plan = cached_plan
else:
    plan = plan_optimizations(selections[0].selections, target_model, info=info)
```

### `_stash_on_context` only catches `AttributeError`, not `TypeError`

`_stash_on_context` falls back to `__setitem__` when `setattr` raises `AttributeError`. That is correct for dict-like contexts and for plain objects, but a frozen object (e.g., `types.MappingProxyType`, a `pydantic.BaseModel` with `model_config = {"frozen": True}`, a `@dataclass(frozen=True)`) raises `TypeError` or `dataclasses.FrozenInstanceError` (a subclass of `AttributeError` in 3.11+, but `TypeError` historically). Strawberry consumers do pass frozen-attrs / pydantic models as context. A `TypeError` here aborts the entire resolver chain rather than silently skipping the stash.

Recommended: catch `(AttributeError, TypeError)` and silently skip in both fallback failures, with a single `logger.debug` for diagnosability. Add a unit test passing a `types.MappingProxyType({})` (read-only mapping) as context and assert the resolver still completes.

```django_strawberry_framework/optimizer/extension.py:52:68
def _stash_on_context(context: Any, key: str, value: Any) -> None:
    ...
    if context is None:
        return
    try:
        setattr(context, key, value)
    except AttributeError:
        context[key] = value
```

## Low:

### `check_schema` is `@classmethod` but never uses `cls`

`check_schema` is decorated `@classmethod` but the body only uses module-level helpers and the global `registry`. It should be `@staticmethod`. Mostly a clarity nit, but `@classmethod` invites future maintainers to assume per-subclass behaviour that does not exist.

```django_strawberry_framework/optimizer/extension.py:381:415
@classmethod
def check_schema(cls, schema: Any) -> list[str]:
    ...
    for _model, type_cls in registry.iter_types():
```

### `logger = logging.getLogger("django_strawberry_framework")` is hand-rolled package name

The package name is a string literal in this file; if the package is ever renamed, this logger silently keeps writing under the old name. Use `logging.getLogger(__name__.partition(".")[0])` or `logging.getLogger(__package__.split(".")[0])` so the binding tracks the actual package. The trade-off: literal is more obviously the framework-wide logger when reading the file. Comment polish — defer.

```django_strawberry_framework/optimizer/extension.py:71:71
logger = logging.getLogger("django_strawberry_framework")
```

### `plan_relation` instance method is a thin pass-through

`DjangoOptimizerExtension.plan_relation` is a one-line delegate to the module-level `plan_relation` function. Either remove it (callers can import the module-level helper directly) or comment why the instance method exists (likely "override seam for tests/subclasses"). The current state — undocumented thin delegate — invites both confusion and accidental removal.

```django_strawberry_framework/optimizer/extension.py:450:461
def plan_relation(
    self,
    field: Any,
    target_type: type,
    info: Any,
) -> tuple[str, str]:
    ...
    return plan_relation(field, target_type, info)
```

### `from strawberry.types.nodes import convert_selections` is a lazy import without comment

The lazy import inside `_optimize` is unusual; lazy imports usually exist to avoid circular imports or import-time cost. If the reason is "Strawberry's API surface is not stable here," that is worth a comment. Otherwise, hoist it to the module top. Comment polish — defer.

```django_strawberry_framework/optimizer/extension.py:332:332
from strawberry.types.nodes import convert_selections
```

### `_plan_cache` eviction is FIFO, comment says "oldest"

The eviction strategy iterates from the start of the dict and removes the first 25% of entries. Python dicts iterate in insertion order, so this is FIFO, not LRU. The current comment "Remove the oldest quarter" is accurate, but a future maintainer reading "cache hit" plus "eviction" may assume LRU. Either rename `_cache_hits`/`_cache_misses` interactions to make the FIFO nature explicit, or change the comment to "FIFO eviction" and note that hits do not refresh recency. Comment polish — defer.

```django_strawberry_framework/optimizer/extension.py:346:352
if plan.cacheable and len(self._plan_cache) >= _MAX_PLAN_CACHE_SIZE:
    # Remove the oldest quarter to amortize eviction cost.
    to_remove = _MAX_PLAN_CACHE_SIZE // 4
    for _ in range(to_remove):
        self._plan_cache.pop(next(iter(self._plan_cache)))
```

## What looks solid

- Root-gate via `info.path.prev is None` is the right idiom — it's the same pattern strawberry-graphql-django uses, and it correctly defers nested optimization to Django's `__`-chain through `prefetch_related`.
- Sync/async handling in `resolve` is clean: `inspect.isawaitable(result)` plus a small async wrapper is the minimal correct shape.
- `on_execute` uses a `ContextVar` token-based set/reset pattern — safe under concurrent async operations.
- Strictness validation in `__init__` rejects bad input early with a clear `ValueError`.
- `_resolve_model_from_return_type` correctly peels `of_type` wrappers and falls back to `None` for unregistered types, matching the registry's `model_for_type(None) -> None` shortcut.
- `cache_info()` matches the `functools.lru_cache` shape so consumers familiar with stdlib caches get a predictable API.
- Cache-key components are well-justified in the docstring (operation hash, directive vars only, target model, runtime path) — directive-variable extraction is a real correctness fix for `@skip`/`@include` selection-set divergence.
- `_collect_schema_reachable_types` correctly excludes orphan `types=[...]` registrations that never appear in the schema's reachable graph, preventing audit false positives.
- Plan cache is opt-in via `plan.cacheable`, so plans that depend on per-call state are never cached.
- `_stash_on_context(None, ...)` short-circuits silently; documented behavior for callers who pass `context_value=None`.
- Module imports are sorted; no circular-import surface back into the package.
- 18% line coverage in this file under the package suite (extensive integration coverage in `tests/optimizer/`); 100% gate is met across the whole package.

---

### Summary:

The extension is the largest single file in the optimizer subsystem and gets the most consumer-visible behavior right (root gating, sync/async handling, ContextVar lifecycle, cache-key directive variables). The Medium items are all "narrow correctness/perf footguns on the cache key path": move from `hash(print_ast(...))` to the printed string (or a wider hash) to eliminate the hash-collision risk; memoize the printed AST per operation so cache hits are O(1); broaden the `_stash_on_context` exception catch to include `TypeError` for frozen contexts. Low items are clarity/comment polish (`@classmethod` → `@staticmethod`, hand-rolled logger name, undocumented thin pass-through, lazy import without comment, FIFO-vs-LRU naming). No High issues; the architecture mirrors strawberry-graphql-django's well-trodden path and the visibility-leak fix (O6) is correctly summarised in the module docstring.

---

### Worker 3 verification

- Medium fix 1 (cache key): `_build_cache_key` now stores `print_ast(operation)` as a string instead of `hash(print_ast(...))`. Plan-cache key tuple shape changed from `(int, frozenset, type, tuple)` to `(str, frozenset, type, tuple)`. Existing tests that assert on `key[2]` (target_model) and `key[3]` (path tuple) keep passing because positions and types of those components are unchanged.
- Medium fix 2 (memoize print_ast on cache hits): **deferred**. Reason: the safe implementation requires a per-execution cache that is async-safe (a `ContextVar` set in `on_execute`), and there is no measured perf regression today — `print_ast` is fast enough on the small operations our test suite exercises. Recommend tracking as a separate perf-pass item; the reviewer artifact's recommendation stands.
- Medium fix 3 (broaden `_stash_on_context` exception catch): `_stash_on_context` now catches `(AttributeError, TypeError)` on `setattr` and `(TypeError, KeyError)` on `__setitem__`, silently skipping when both fail. Two tests added: `test_stash_on_read_only_mapping_is_silent` (covers `MappingProxyType` — both paths raise `TypeError`) and `test_stash_falls_back_to_setitem_on_typeerror` (covers an object whose `__setattr__` raises `TypeError`, exercising the `setattr → setitem` fallback through the new catch).
- Low fixes (comment polish):
  - Lazy `convert_selections` import now has a comment explaining the deliberate avoidance of a hard import-time dependency on `strawberry.types.nodes`.
  - FIFO eviction comment now says "FIFO" explicitly and notes hits do not refresh recency.
  - `plan_relation` instance method now has a docstring explaining it is an override seam for subclasses and tests.
- Low items not addressed in this cycle (deferred to maintainer):
  - `check_schema` `@classmethod` → `@staticmethod`: kept as classmethod to preserve subclass-override behavior. The `cls` parameter is currently unused; renaming would be a backward-compat hazard for any consumer who already overrode it. Maintainer can revisit before 1.0.
  - Hand-rolled `logger = logging.getLogger("django_strawberry_framework")`: kept as literal. Switching to `__name__.partition(".")[0]` introduces a runtime dependency on the package's import path which has no current breakage; defer until the package is renamed (if ever).
- Validation: `uv run ruff format` and `uv run ruff check` clean; `uv run pytest -q` -> 345 passed, 4 skipped, 100% coverage (gain of 2 tests in `tests/optimizer/test_extension.py`).
- CHANGELOG: not updated. The cache-key change is consumer-invisible (cache is internal); the stash broadening is a defensive bug fix for an unhit code path; AGENTS.md forbids changelog edits without explicit instruction.
- Scope: changes confined to `django_strawberry_framework/optimizer/extension.py` and `tests/optimizer/test_extension.py`.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.

---

### Helper-surfaced follow-ups (post-cycle audit)

This section was added after the cycle was reviewed. The original review was written without running `scripts/review_inspect.py`; running it post-cycle surfaced three additional follow-ups for the next release. They are not in scope for the 0.0.3 cycle but should be tracked.

- **Repeated literal `_strawberry_schema` (2x).** Lines 152 (`_collect_schema_reachable_types`) and 213 (`_resolve_model_from_return_type`) both do `getattr(<schema-or-info>, "_strawberry_schema", ...)`. This is the brittle Strawberry-private-API access already noted in the per-file Low items, but the helper made the duplication concrete: a single `_get_strawberry_schema(...)` helper would centralize the fragility so a future Strawberry rename has one fix, not two.
- **`_optimize` is a hotspot at 80 lines / 10 branches.** The function does QuerySet short-circuit + model resolution + walker call + cache lookup/insert/eviction + plan stash + strictness sentinel stash + plan-empty short-circuit + diff + apply. Each step is small but the sequential combination makes the function the longest method in the file. Decomposition into a private `_run_walker_with_cache` (cache lookup + walker + insert + eviction) and a `_publish_plan_to_context` (sentinel stash) would cut the call site to ~20 lines and isolate the cache invariants from the per-request stash logic.
- **`_walk_directives` is a hotspot at 28 lines / 15 branches.** The branch density is intrinsic to the AST shape (directives + arguments + selection-set recursion + fragment-spread descent), but it would benefit from a brief comment naming the four shapes the function handles so future readers see the structure at a glance.

**Status (post-audit implementation pass):** all three follow-ups addressed.

- `_strawberry_schema_from_schema(schema)` and `_strawberry_schema_from_info(info)` helpers added; both `_collect_schema_reachable_types` and `_resolve_model_from_return_type` now call the helpers instead of doing the `getattr` literal. Two helpers because the two call sites have different fallback semantics (schema-shape returns input on miss; info-shape returns `None` on miss); a single helper would have to overload, which would be less clear.
- `_optimize` decomposed into `_get_or_build_plan(self, selections, target_model, info)` (cache lookup + walker + eviction + insert) and `_publish_plan_to_context(self, plan, info)` (B5 stash + B3 strictness sentinel stash). `_optimize` is now ~30 lines of orchestration; the cache-management and context-stash logic each live in their own focused methods.
- `_walk_directives` docstring now enumerates the four AST shapes (directives on current node, selection-set children, FragmentSpreadNode descent, regular field children) so the branch density reads as a guided dispatch rather than dense recursion.
- Validation: `uv run pytest -q` -> 354 passed, 100% coverage; `uv run ruff format / check` clean.
