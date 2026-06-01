# Review: `django_strawberry_framework/filters/factories.py`

Status: verified

## DRY analysis

- **Collapse the pure-passthrough list comprehension in `FilterArgumentsFactory._build_class_type` (factories.py:176-179) to a direct splat.** The comprehension `[(python_attr, annotation, kwargs) for python_attr, annotation, kwargs in (*input_field_triples, *logic_field_triples)]` iterates over a chained-splat sequence and rebuilds each tuple verbatim — it produces a list of the exact same triple objects, just with a wider declared annotation (`dict[str, Any] | None` vs the upstream helpers' `dict[str, Any]`). Both `_build_input_fields` (inputs.py:620) and `_build_logic_fields` (inputs.py:600) already return `list[tuple[str, Any, dict[str, Any]]]`; the call site can simply pass `[*input_field_triples, *logic_field_triples]` to `build_input_class`. **Act-now opportunity** — single call site, zero behavioural change, removes a misleading "this loop must be doing something" reading prompt. The widened-`| None` annotation is also a static-type-precision drop (`build_input_class`'s parameter accepts `dict[str, Any] | None` per inputs.py:561, so the splat retains type compatibility without restating the union). The fix is a three-line shrink.
- **Hoist the `{"model", "fields"}` carve-out set in `_make_cache_key` (factories.py:245) to a module-level `_PRIMARY_META_KEYS` constant alongside `_RESERVED_FACTORY_KEYS` (factories.py:52).** The literal set is used in one place today, but its meaning ("the two keys handled positionally by the cache-key tuple — everything else goes into `extra`") is load-bearing for the cache-key contract. **Defer until a second carve-out site lands** (e.g. a future "build a debug-only canonical-string form of the cache key" helper that also needs to know which keys are positional vs. extras). Today one site is the right cost-floor for an inline literal.
- **Collapse `_make_hashable`'s three-branch isinstance ladder (factories.py:202-208) by promoting it to a registry-style mapping IFF a fourth container type lands.** The ladder is the right shape at three types (`dict` -> sorted tuple, `set/frozenset` -> sorted-by-repr tuple, `list/tuple` -> tuple); the per-branch behaviour diverges enough that a mapping table would not save lines. **Defer until a fourth container-type branch lands** (e.g. `collections.OrderedDict`, `MappingProxyType`, or a custom upstream wrapper). The cookbook upstream (`/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/filterset_factories.py` same-named helper) ships the same three-branch shape and has not grown a fourth in years.

## High:

None.

## Medium:

None.

## Low:

### `FilterArgumentsFactory._build_class_type` field_specs comprehension is a pure pass-through

`factories.py:176-179` builds `field_specs` via a list comprehension that re-binds each triple verbatim:

```django_strawberry_framework/filters/factories.py:176-179
        field_specs: list[tuple[str, Any, dict[str, Any] | None]] = [
            (python_attr, annotation, kwargs)
            for python_attr, annotation, kwargs in (*input_field_triples, *logic_field_triples)
        ]
        input_cls = build_input_class(type_name, field_specs)
```

The comprehension produces the same triple objects (no transformation, no filtering, no normalization) and the only effect is the widened-`| None` element annotation. Both source helpers return `dict[str, Any]` (no `None`): `_build_input_fields` at `inputs.py:620-623` and `_build_logic_fields` at `inputs.py:600`. The `build_input_class` callee (`inputs.py:561`) accepts `dict[str, Any] | None`, so a splat-form `[*input_field_triples, *logic_field_triples]` passes the type-checker unchanged. Recommended shape:

```python
input_cls = build_input_class(
    type_name,
    [*input_field_triples, *logic_field_triples],
)
```

This is a small simplification Low — the present shape reads like "we are normalizing the triples" when in fact nothing is normalized. Comment-pass territory in isolation, but it's a logic-shape simplification rather than a docstring tweak, so Worker 2 owns it. Two acceptable shapes:

1. Splat-form as above — single statement, no intermediate binding.
2. Keep the intermediate binding but drop the comprehension: `field_specs = [*input_field_triples, *logic_field_triples]`. Useful if a future caller wants to log / inspect the merged list pre-build.

Recommend (1) — the intermediate binding has no current readers.

### `_make_hashable` dict branch sorts by `(key, value)` tuples; mixed-type keys raise TypeError

`factories.py:202-203`:

```django_strawberry_framework/filters/factories.py:202-203
    if isinstance(v, dict):
        return tuple(sorted((k, _make_hashable(val)) for k, val in v.items()))
```

The `sorted(...)` call sorts a generator of `(k, _make_hashable(val))` tuples by Python's default tuple comparison. When two keys in the same dict have mutually-unorderable types (e.g. `{"a": 1, 0: 2}` mixing `str` and `int`), Python's `<` raises `TypeError: '<' not supported between instances of 'int' and 'str'`. The `set/frozenset` branch directly below at `factories.py:204-205` explicitly defends against this by sorting via `key=repr` — the docstring at `factories.py:198-200` calls out the mixed-type defence ("stays total-ordered even for mixed, mutually-unorderable member types (e.g. `{1, "a"}`)") for the set branch, but the dict branch does not get the same treatment.

In practice, `Meta.fields` declared as `dict` carries `str` keys uniformly (Django field names), so the bug is unreachable from the supported `Meta.fields` shapes. However, `_make_hashable` is recursive and `safe_meta`'s top-level pass through `_make_cache_key` at `factories.py:245` iterates ALL items (model/fields excluded, but any custom `**meta` extra dict with mixed-type keys would reach `_make_hashable`). The cookbook upstream (`/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/filterset_factories.py`'s same-named helper) ships the same shape and the same latent crash.

This is Low not Medium because:
- the documented `Meta.fields` shapes (per spec-027 Decision 2 and `tests/filters/test_factories.py:304-383`) all carry `str` keys at every level today;
- the test suite does not exercise a mixed-key-type `Meta.extra_opt` (the closest test is `test_get_filterset_class_supports_unhashable_meta_values` at `tests/filters/test_factories.py:439-465`, which passes a uniformly-`str`-keyed nested dict);
- the loud-fail (`TypeError`) is in fact a better failure mode than silent same-slot collision, so the consumer notices when they hit it.

Two acceptable shapes:
1. **Apply the same `key=repr` defence to the dict branch.** Symmetric with `set/frozenset` at `factories.py:204-205`; one-character change to `sorted(... , key=repr)`. Add a regression test pinning a mixed-key-type `**meta` extra. Costs: O(n) `repr` calls per dict.
2. **Document the str-key requirement on `_make_hashable`'s docstring** as a precondition. Loud-fail framing matches the rest of the package; consumer-facing call surface (`get_filterset_class(**meta)`) does not advertise mixed-type keys as supported.

Recommend (1) — symmetric with the `set/frozenset` branch already in the same function, and the docstring at `factories.py:198-200` already names the mixed-type defence as a property of `_make_hashable` (not just the set branch). The current shape is inconsistent with its own documentation: a reader expects the mixed-type defence applies to the function, not just one branch of it.

### `_create_dynamic_filterset_class` leaks `model` into `Meta` class attrs without dedicated handling

`factories.py:266-269`:

```django_strawberry_framework/filters/factories.py:266-269
    meta_attrs = dict(safe_meta)
    name = f"{model.__name__}AutoFilter"
    meta_class = type("Meta", (object,), meta_attrs)
    return type(name, (FilterSet,), {"Meta": meta_class})
```

`meta_attrs` is `dict(safe_meta)`, which already contains `"model"` (the `model = safe_meta.get("model")` read at `factories.py:260` was an existence check, not a pop). The `Meta` class therefore carries `Meta.model` AND every other key from `safe_meta` — which is the correct shape for `django-filter`'s `FilterSet.Meta`. No bug, but two minor sharpening opportunities:

1. The `dict(safe_meta)` copy is defensive against the (theoretical) case where `_create_dynamic_filterset_class` later mutates `meta_attrs`. Today it does not, and the caller `get_filterset_class` already builds `safe_meta` as a fresh dict at `factories.py:296` (`{k: v for k, v in meta.items() if k not in _RESERVED_FACTORY_KEYS}`). The copy is therefore a redundant second copy. A future refactor that hoists the safe-meta filter into a shared helper might drop the explicit copy and rely on the upstream filter pass.
2. The synthetic-class `__name__` is `f"{model.__name__}AutoFilter"` (line 267). When two distinct `Meta`-dict shapes for the same model land via different connection fields, the BFS factory's `_type_filterset_registry` will raise the collision check at `factories.py:151-158` because both classes share `__name__`. The dynamic cache (`_dynamic_filterset_cache`) is the documented break-glass for this exact case (docstring at `factories.py:33-46`), and the docstring at `factories.py:289-292` explicitly says "two callers with equivalent declarations get the same `__name__` (preventing the BFS factory's duplicate-name collision check from firing)". The unwritten part is the inverse: two callers with **distinct** declarations targeting the same model also share `__name__` and so WILL collide through the BFS factory. The cache key embeds `(model, fields_key, extra)`, so the cache returns the same class only when the declarations match — so a distinct declaration produces a fresh `type(name, (FilterSet,), ...)` with the same `__name__`, then the BFS factory's collision check raises `ConfigurationError`.

For Low #3 sub-point (2), the right fix is to spell the contract out in the docstring: distinct-meta-same-model is a collision case that the consumer must resolve via an explicit `filterset_class=` per the spec-027 "consumer-defined" path. The current docstring at `factories.py:273-293` is consumer-facing and silent on this case. Worker 2 should append one sentence to the `Returns:` paragraph:

```
Two callers with **distinct** Meta declarations against the same model
will land at the same generated ``__name__`` and so collide through the
BFS factory's ``_type_filterset_registry`` collision check; resolve by
declaring an explicit ``filterset_class=`` at one of the two call sites.
```

No test change needed — the BFS collision raise at `factories.py:151-158` already governs this, and `test_filter_arguments_factory_collision_raises_on_distinct_class_with_same_name` at `tests/filters/test_factories.py:142-169` pins the BFS-level behaviour.

### `_RESERVED_FACTORY_KEYS` carries one entry — Low forward-look for a TypeAlias and a public re-export hook

`factories.py:52`:

```django_strawberry_framework/filters/factories.py:50-52
# Reserved kwargs stripped from ``get_filterset_class``'s meta input to
# prevent keyword collisions with the dynamic-class factory below.
_RESERVED_FACTORY_KEYS: frozenset[str] = frozenset({"filterset_base_class"})
```

Today the set has exactly one entry, and `filterset_base_class` is not yet consumed by the factory (the `_create_dynamic_filterset_class` body at `factories.py:251-269` always extends `FilterSet` directly per the hard-coded `(FilterSet,)` bases tuple at line 269). The reserved kwarg exists so a future `filterset_base_class=MyCustomFilterSet` can land without colliding with `Meta`'s namespace — it's a forward-compatibility seam, not a present feature. **Defer until** either (a) a second reserved kwarg lands (then the frozenset reads as an extensible policy registry rather than a one-element corner case) or (b) the `filterset_base_class` extension point is actually wired up at `factories.py:269` (then this Low collapses naturally — the reserved-set becomes the per-kwarg consumption table). Citation hygiene only today; do not bump.

### `Slice 3's finalizer materializes the built classes as module globals` docstring claim is now shipped behaviour

`factories.py:13` says:

```django_strawberry_framework/filters/factories.py:12-13
(Decision 4 H1 / spec-021 lines 579-584). Slice 3's finalizer materializes
the built classes as module globals; Slice 2 only builds them.
```

The "Slice 3's finalizer" language frames the materialization as future work, but `types/finalizer.py:521` (`from ..filters.factories import FilterArgumentsFactory`) and `types/finalizer.py:591` (`factory = FilterArgumentsFactory(filterset_cls)`) already wire the factory in and Slice 3 is shipped at 0.0.7 per the active plan (`docs/review/review-0_0_7.md`). The docstring should be updated to past-tense ("Slice 3's finalizer materializes ..." → "Slice 3's finalizer materializes ... at finalize time; this module owns build-only") OR drop the slice-numbering and frame as "the finalizer materializes ... at finalize time; this module owns build-only". Same severity calibration as the previous cycles' citation-drift Lows (`list_field.py` `spec-016` → `spec-020`, `scalars.py` `TODO-ALPHA-028` → `TODO-ALPHA-035-0.0.11`) — comment-pass hygiene, the policy text is itself correct against the shipped behaviour; only the tense rotted.

### GLOSSARY coverage gap for `FilterArgumentsFactory`, `get_filterset_class`, `_dynamic_filterset_cache`, `_make_cache_key` is forwarded, not a local fix

`grep -n "FilterArgumentsFactory\|get_filterset_class\|_dynamic_filterset_cache\|_make_cache_key" docs/GLOSSARY.md` returns zero matches. `FilterArgumentsFactory` is the named factory in spec-027 Decision 3 Layer 5 — it's not (directly) exported through `filters/__init__.py`'s public surface (per `filters/__init__.py:91-107` which exports `filter_input_type`, the user-facing helper) but it IS a consumer-visible symbol via the `factories.FilterArgumentsFactory` path that tests at `tests/filters/test_factories.py:25-30` import directly, and is named in the docstring of `filter_input_type` (`__init__.py`) as the underlying mechanism. `get_filterset_class` is the connection-field-facing entry point named in spec-027 with the "connection-field surface owning this entry point lands in 0.0.9" deferral at `factories.py:279`.

The same forward-treatment as `rev-filters__base.md` Low #5 applies here: these symbols are part of the filters-subsystem first-cohort GLOSSARY documentation gap (paired with `TypedFilter`, `ArrayFilter`, `RangeFilter`, `ListFilter`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`, `LazyRelatedClassMixin`, `ClassBasedTypeNameMixin`, `FilterSet`, `Meta.filterset_class`). **Forwarded to `rev-django_strawberry_framework.md`** — the project pass owns this cross-file coverage call so the filter-subsystem entries can be authored together at version-bump time per the joint-cut deferral pattern in spec-027 Decision 10. No in-cycle GLOSSARY edit recommended.

### `spec-021` source citations in this file (factories.py:3, factories.py:12, factories.py:98)

`factories.py` cites `spec-021` three times (module docstring lines 3 and 12, `__init_subclass__` docstring line 98). Per the dispatch prompt, this drift is already documented in `rev-filters__base.md` Low #2 with the full subpackage-wide scope, and forwarded to the folder pass `docs/review/rev-filters.md` as a single mass-rewrite candidate. **No re-file here** — consolidate by referencing the existing forward. Worker 2 must NOT sweep these citations in the `factories.py` cycle in isolation, since doing so would create internal inconsistency vs the four sibling files (`base.py`, `inputs.py`, `sets.py`, `__init__.py`) until the folder pass picks them up together. The folder-pass author owns the cross-file sweep.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_build_class_type` (factories.py:170-182) delegates name resolution to `_input_type_name_for` (inputs.py:183) and per-field/per-logic triple construction to `_build_input_fields` (inputs.py:620) and `_build_logic_fields` (inputs.py:600), and class assembly to `build_input_class` (inputs.py:561) — no duplication of the per-field annotation logic. `arguments` property reads back through the shared `input_object_types` class-level cache (factories.py:84) using the canonical `filter_input_type_name` slot established at `__init__` time (factories.py:118). The `get_filterset_class` early-return at `factories.py:294-295` mirrors the cookbook upstream's same-named helper shape exactly.
- **New helpers considered.** Considered (a) hoisting the `{"model", "fields"}` carve-out set in `_make_cache_key` (factories.py:245) to a module-level constant — deferred at one site per `## DRY analysis`; (b) collapsing `_make_hashable`'s three-branch isinstance ladder (factories.py:202-208) into a mapping table — deferred at three branches per `## DRY analysis`; (c) extracting an `_input_class_for_filterset(fs_class)` helper that wraps the `getattr(fs_class, "_owner_definition", None)` + `_build_input_fields` + `_build_logic_fields` + `build_input_class` chain at `factories.py:170-182` — rejected, the chain is read-once-top-to-bottom and a wrapping helper would just add an indirection. The pure-pass-through list comp at `factories.py:176-179` is the act-now simplification per `## Low`.
- **Duplication risk in the current file.** `_make_hashable`'s `tuple(_make_hashable(item) for item in ...)` shape repeats across three branches (factories.py:205, 207, 240); they are intentional sibling design (each branch's surrounding "key shape" differs: sorted-by-repr for unordered containers, order-preserving for ordered containers, sorted-by-(k,v)-tuple for dicts). The `tuple(...)` constructor reads inline at each site and abstracting it would obscure the per-branch ordering contract.

### Other positives

- **`FilterArgumentsFactory.__init_subclass__` raises `TypeError` at class-creation time** (factories.py:91-107) with a precise consumer-facing error message that names the base class, the offending subclass, the root cause ("class-level caches are shared mutable dicts a subclass would inherit rather than isolate, silently cross-contaminating builds"), AND the supported alternative ("Extend it by composition (wrap an instance), not inheritance"). The class-creation-time gate is the right shape: subclassing is rejected loudly before any cross-contamination can happen. Pinned by `test_filter_arguments_factory_rejects_subclassing` at `tests/filters/test_factories.py:467-480`.
- **BFS dedup is double-guarded.** The enqueue-time `target not in seen` gate at `factories.py:167` catches cycles (`A -> B -> A`) AND the pop-time `if fs_class in seen: continue` at `factories.py:145-146` catches diamonds (`A -> {B, C} -> D` where D is enqueued from both B and C before being popped). Both branches are independently pinned: `test_filter_arguments_factory_bfs_handles_cycle` at `tests/filters/test_factories.py:78-90` (cycle) and `test_filter_arguments_factory_dedupes_target_enqueued_twice` at `tests/filters/test_factories.py:93-139` (diamond). The two-guard design is the right shape — a single guard could not catch both.
- **`RelatedFilter(None, ...)` placeholder is silently skipped at `factories.py:165-168`** with an inline citation to cookbook lines 124-130 so the silent-skip behaviour traces back to the upstream port verbatim. The branch is exercised indirectly through `tests/filters/test_factories.py:78-90`'s self-referential cycle fixture (the `RelatedFilter("SelfReferentialBranchFilter")` string-form which resolves through `LazyRelatedClassMixin.resolve_lazy_class`).
- **Collision detection raises a structured `ConfigurationError`** at `factories.py:152-158` with both colliding classes named in full module-qualified form (`existing_owner.__module__`.`existing_owner.__qualname__` vs ...). The error names the input type name, both filterset classes, AND the actionable consumer fix ("Rename one filterset so its class-derived input type name is unique"). Pinned by `test_filter_arguments_factory_collision_raises_on_distinct_class_with_same_name` at `tests/filters/test_factories.py:142-169`.
- **`_make_hashable` set/frozenset branch sorts by `key=repr`** (factories.py:205) so mixed-type members (e.g. `{1, "a"}`) produce a stable canonical order. The docstring at `factories.py:198-200` explicitly calls out the mixed-type defence as a property of the function. (See Low #2 for the dict-branch asymmetry — the docstring promises this defence applies more broadly than the implementation honours.)
- **`_make_cache_key` distinguishes `dict` / sequence / scalar `fields` shapes with discriminator strings (`"dict"`, `"seq"`, `"raw"`)** at `factories.py:232-242`. The discriminators prevent cross-shape collisions: a `fields=("name",)` declaration cannot accidentally key-collide with `fields={"name": ...}` because the outer tuple shape carries a different first element. Pinned by `test_make_cache_key_normalizes_dict_fields_shape`, `_normalizes_list_fields_shape`, `_normalizes_scalar_all_fields_shape` at `tests/filters/test_factories.py:304-319`.
- **`get_filterset_class` cache write is unconditional after the miss check** (`factories.py:301-302`) — there is no read-then-conditional-write race window because the function runs at finalize / schema-build time (single-threaded by spec). The cache is module-global and process-local; `tests/filters/test_factories.py:36-48` clears it per-test via the autouse `_isolate_state` fixture so test isolation is honoured.
- **Type-checking-only import for `django.db.models`** (factories.py:29-30) is correctly guarded with `# pragma: no cover - type-checking-only imports.` per `AGENTS.md` "pragma no cover is only for branches genuinely unreachable under the test runner".
- **`_dynamic_filterset_cache` lifecycle comment** (factories.py:40-46) names the M-filters-3 review's accepted-as-is decision verbatim, cites the test-isolation-nicety framing, AND names the trigger condition for adding a clear hook ("if a consumer reload path ever demands it"). This is the right shape for a deferred-policy comment: future authors know exactly when to re-open the decision.
- **Test discipline is strong.** `tests/filters/test_factories.py` exercises every branch in the BFS (cycle, diamond, collision, idempotence, Relay vs non-Relay target), every cache-key shape (dict / seq / raw / extras / mixed surface shapes), `_RESERVED_FACTORY_KEYS` stripping, the `model` requirement loud-fail, and the unhashable-meta-values support path. The 23+ test functions pin the consumer-visible contract end-to-end against real example-project models (no mocks, no ad-hoc filtersets — all use `apps.library.models` and `apps.products.models` per `AGENTS.md` test placement).

### Summary

`factories.py` is a 303-line port of the cookbook's `FilterArgumentsFactory` (BFS layer) + `get_filterset_class` / `_make_cache_key` / `_create_dynamic_filterset_class` (dynamic-FilterSet cache layer) per spec-027 Decision 3 Layers 5 and 6. The BFS factory is correctly subclass-rejected at class-creation time, the dedup is double-guarded (enqueue-time `seen` for cycles + pop-time `seen` for diamonds), and the collision-detection raise is structured with both classes named. The dynamic-cache path key-shape disambiguates `dict` / sequence / scalar `fields` declarations to prevent cross-shape slot collisions, and `_make_hashable` correctly normalizes unordered containers via sort-by-`repr` so structurally-equal inputs collapse to one key. Zero High / zero Medium. Six Lows: one logic-shape simplification (`_build_class_type`'s pure-pass-through list comprehension), one parity gap (`_make_hashable`'s dict branch lacks the same mixed-key-type defence the set/frozenset branch carries, despite the docstring promising the defence is a property of the function), one consumer-facing docstring sharpening (`_create_dynamic_filterset_class` should spell the distinct-meta-same-model collision case out in `get_filterset_class`'s docstring), one forward-looking deferral (`_RESERVED_FACTORY_KEYS` becomes more useful at two entries), one tense fix on a Slice-3-now-shipped docstring claim, and one GLOSSARY-coverage forward to the project pass. The `spec-021` → `spec-027` citation drift in this file (factories.py:3, 12, 98) is consolidated under `rev-filters__base.md` Low #2's subpackage-wide forward to the folder pass — no re-file here per the dispatch prompt. Standard three-spawn cycle: Lows #1, #2, #3, and #5 all need real source edits at comment-pass time, so shape-#5 is disqualified.

---

## Fix report (Worker 2)

Logic pass only. Comment-pass items (Lows #3, #5) and forwarded items (Lows #4, #6) are not touched here.

### Files touched

- `django_strawberry_framework/filters/factories.py:170-178` — Low #1: collapsed the pure-pass-through list comprehension in `FilterArgumentsFactory._build_class_type`. The intermediate `field_specs` binding and its triple-rebuilding comprehension are removed; the call site now splats `[*input_field_triples, *logic_field_triples]` directly into `build_input_class`. `build_input_class`'s parameter type accepts `dict[str, Any] | None` per `inputs.py::build_input_class`, so type compatibility is preserved without restating the union. Zero behaviour change — the comprehension produced the same triple objects in the same order.
- `django_strawberry_framework/filters/factories.py:202-204` — Low #2: applied `key=repr` to the `dict` branch of `_make_hashable` for parity with the `set` / `frozenset` branch directly below. Mixed-type dict keys (e.g. `{"a": 1, 0: 2}`) no longer raise `TypeError: '<' not supported between instances of 'int' and 'str'` when sorted; the function's docstring at `factories.py::_make_hashable` already advertises the mixed-type defence as a property of the function, so the implementation now matches its own contract.

### Tests added or updated

- `tests/filters/test_factories.py::test_make_hashable_dict_branch_supports_mixed_key_types` — regression test pinning Low #2's fix. Calls `_make_hashable({"a": 1, 0: 2})` and asserts the call returns a tuple containing both `(k, val)` pairs by set-equality (canonical order is `repr`-sorted, so positional assertions would be brittle). Without the `key=repr` fix this test would raise `TypeError` on the default tuple comparison.
- `tests/filters/test_factories.py` import block — added `_make_hashable` to the existing `factories` import grouping so the new test can call the helper directly. No other test was modified.

Low #1 has no new test: the comprehension was a pure pass-through and the existing factory-arguments tests (`test_filter_arguments_factory_visits_every_reachable_filterset`, `test_filter_arguments_factory_idempotent_repeated_arguments`, etc.) already exercise the call path end-to-end and pin the resulting input-class shape. Adding a test for the splat-form would only re-pin behaviour those tests already cover.

### Validation run

- `uv run ruff format .` — pass / 183 files left unchanged.
- `uv run ruff check --fix .` — pass / All checks passed.
- pytest NOT run per Worker 2 hard rule.

### Notes for Worker 3

- No shadow file was used during this pass.
- Lows #3, #5 are comment-pass items and will be addressed in the comment sub-spawn after logic approval.
- Lows #4, #6 are deferred / forwarded per the artifact and the dispatch prompt; no in-cycle source edit.
- `uv.lock` is unchanged (verified via `git status --short`).
- Pre-existing dirty paths under the working tree (other filter / list_field / sets_mixins / scalars / exceptions edits and the rev-*.md scratchpads) were not touched by this pass.
- The `_make_hashable` docstring already advertises the mixed-type defence as a property of the function (current text at `factories.py:198-200`), so Low #2's fix brings the implementation in line with the *existing* docstring rather than introducing a new contract. The comment-pass is therefore not obligated to widen the docstring; if anything it could tighten the wording to call out that both unordered branches share the `repr`-sort defence, but that is a comment-pass call.

---

## Verification (Worker 3)

### Logic verification outcome

- **Low #1 (pass-through comprehension collapsed).** `factories.py:170-181` now reads `input_cls = build_input_class(type_name, [*input_field_triples, *logic_field_triples])`; the `field_specs: list[tuple[str, Any, dict[str, Any] | None]] = [...]` binding and its triple-rebuilding comprehension are removed. Behaviour preserved — same triple objects in same order, just no rebind. Type compatibility holds because `build_input_class`'s parameter annotation accepts `dict[str, Any] | None` per `inputs.py::build_input_class`. The existing factory-arguments tests (`test_filter_arguments_factory_visits_every_reachable_filterset`, `test_filter_arguments_factory_idempotent_repeated_arguments`, etc.) already exercise the call path end-to-end, so the artifact's "no new test" rationale holds.
- **Low #2 (`_make_hashable` dict branch repr defence).** `factories.py:201-204` now sorts the dict branch with `key=repr`, symmetric with the `set/frozenset` branch at `factories.py:205-206`. The new regression test `tests/filters/test_factories.py::test_make_hashable_dict_branch_supports_mixed_key_types` at `test_factories.py:323-339` pins `_make_hashable({"a": 1, 0: 2})` returning a tuple with both `(k, val)` pairs by set-equality (canonical order is `repr`-sorted). Without `key=repr` the default tuple comparison raises `TypeError: '<' not supported between instances of 'int' and 'str'`. The `_make_hashable` import addition at `test_factories.py:29` is scoped — only the new symbol is added to the existing `factories` grouping.
- **Lows #3, #5 (comment-pass items).** Untouched in this pass per the artifact split; will be addressed in the comment sub-spawn after logic acceptance.
- **Lows #4, #6 (forwarded / deferred).** Untouched per the artifact's forward-to-project-pass framing and the dispatch prompt's "no in-cycle source edit" rule.
- **`spec-021` citation drift in this file (factories.py:3, 12, 98).** Untouched per dispatch — consolidated under `rev-filters__base.md` Low #2's subpackage-wide forward to the folder pass.

### DRY findings disposition

All three DRY items map to the cycle's Lows or were authored as explicit deferrals:
- DRY #1 (pure-passthrough comprehension) — landed as Low #1, addressed here.
- DRY #2 (`{"model", "fields"}` carve-out hoist) — deferred to a second-carve-out-site trigger; no edit.
- DRY #3 (`_make_hashable` isinstance ladder → mapping table) — deferred to a fourth-container-type trigger; no edit.

### Temp test verification

- No temp test files created — the new permanent regression test in `tests/filters/test_factories.py` directly pins Low #2's fix and is the right placement under the existing `tests/filters/` tree.
- Disposition: N/A.

### Diff scope

`git diff -- django_strawberry_framework/filters/factories.py tests/filters/test_factories.py` shows only the two source hunks (Lows #1 + #2) and the matching test addition + single-symbol import. No comment-pass edits leaked in. No drive-by changes to Lows #3 / #4 / #5 / #6. Other dirty paths under the working tree belong to sibling rev-* cycles and dispatch acknowledges them as out-of-scope.

### Focused test run

```
uv run pytest tests/filters/test_factories.py -x -k "make_hashable" 2>&1 | tail -20
...
======================= 1 passed, 21 deselected in 0.24s =======================
```

The `1 passed` is `test_make_hashable_dict_branch_supports_mixed_key_types`. The accompanying coverage-fail line is the expected `fail_under = 100` artifact under `-k` filtering (only one test selected out of the suite) and is not a regression signal.

### Ruff outcomes

- `uv run ruff format --check django_strawberry_framework/filters/factories.py tests/filters/test_factories.py` → `2 files already formatted`.
- `uv run ruff check django_strawberry_framework/filters/factories.py tests/filters/test_factories.py` → `All checks passed!`.

### Verification outcome

`logic accepted; awaiting comment pass` — top-level `Status: logic-accepted`.

### Comment-pass verification (pass 2)

- **Low #3 verbatim docstring addition.** `factories.py:296-299` appends the exact four-sentence artifact recommendation (artifact lines 92-96) verbatim into `get_filterset_class`'s `Returns:` paragraph. RST-style inline-code backticks (`` ``__name__`` ``, `` ``_type_filterset_registry`` ``, `` ``filterset_class=`` ``) match the file's existing docstring convention; the `**distinct**` emphasis is preserved.
- **Low #5 tense rotation.** `factories.py:12-14` replaces `"Slice 3's finalizer materializes the built classes as module globals; Slice 2 only builds them."` with `"The finalizer materializes the built classes as module globals at finalize time; this module owns build-only."` — the artifact's second-recommended option ("drop the slice-numbering and frame as ..."), applied verbatim. Slice 3 is shipped at 0.0.7 (the finalizer wiring lives at `types/finalizer.py::SchemaFinalizer`), so the future-work framing is correctly retired.
- **`_make_hashable` docstring symmetric description.** `factories.py:190-202` widens the prior set/frozenset-only mixed-type-defence sentence to cover both unordered branches: `"Both unordered branches sort by ``repr`` rather than by the values themselves so they stay total-ordered even for mixed, mutually-unorderable member or key types (e.g. ``{1, "a"}`` or ``{"a": 1, 0: 2}``)..."`. Both example forms (set + dict) appear, matching the logic-pass parity fix (`key=repr` now on the dict branch at `factories.py:204-206`). This resolves the Worker 2 logic-pass Notes-for-Worker-3 callout that flagged tightening this wording as comment-pass-eligible.
- **Scope creep check.** `git diff HEAD -- django_strawberry_framework/filters/factories.py` shows exactly three docstring hunks plus the Low #1 + Low #2 logic-pass hunks from pass 1; no drive-by edits to Lows #4 / #6, no source-logic mutation in this comment pass, and `spec-021` citation drift remains untouched per dispatch (consolidated under `rev-filters__base.md` Low #2's folder-pass forward).
- **Ruff outcomes (comment pass).** `uv run ruff format --check django_strawberry_framework/filters/factories.py` → `1 file already formatted`. `uv run ruff check django_strawberry_framework/filters/factories.py` → `All checks passed!`. Matches Worker 2's recorded validation.

`comments accepted; awaiting changelog disposition` — top-level `Status: comments-accepted`.

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/filters/factories.py:12-14` — Low #5: rewrote the module-docstring tense rot. `"Slice 3's finalizer materializes the built classes as module globals; Slice 2 only builds them."` becomes `"The finalizer materializes the built classes as module globals at finalize time; this module owns build-only."` per the artifact's recommended option (drop the slice-numbering, frame as shipped behaviour). Slice 3 is shipped at 0.0.7 (the finalizer wiring lives at `types/finalizer.py::SchemaFinalizer` per the artifact's citation) so the future-work framing was inaccurate.
- `django_strawberry_framework/filters/factories.py:289-298` — Low #3: appended the verbatim artifact-recommended sentence to `get_filterset_class`'s `Returns:` paragraph, lifted exactly as Worker 1 phrased it. The previous text named only the equivalent-meta cache-hit case ("two callers with equivalent declarations get the same `__name__`"); the new sentence spells out the inverse — distinct-meta-same-model collision — and points the consumer at the explicit `filterset_class=` resolution path. No tests pin this docstring; the BFS collision raise at `factories.py:152-158` and its pinning test `test_filter_arguments_factory_collision_raises_on_distinct_class_with_same_name` govern the behaviour the docstring now describes.
- `django_strawberry_framework/filters/factories.py:189-200` — `_make_hashable` docstring tightened to cover the post-logic-pass dict-branch parity. Pre-pass wording attributed the mixed-type defence to the set/frozenset branch only ("The ``set`` / ``frozenset`` branch sorts by ``repr`` rather than by the values themselves..."); post-pass the dict branch also sorts by `key=repr`, so the docstring now reads "Both unordered branches sort by ``repr`` rather than by the values themselves so they stay total-ordered even for mixed, mutually-unorderable member or key types (e.g. ``{1, "a"}`` or ``{"a": 1, 0: 2}``)". This brings the docstring in line with the Low #2 logic-pass fix and resolves the Worker 2 logic-pass Notes-for-Worker-3 callout that flagged "if anything it could tighten the wording to call out that both unordered branches share the `repr`-sort defence".

### Per-finding dispositions

- Low #1: addressed in the logic pass — no comment-pass follow-up.
- Low #2: addressed in the logic pass — comment-pass docstring tightening applied above (the `_make_hashable` docstring now covers the dict-branch parity).
- Low #3: addressed — verbatim sentence appended to `get_filterset_class`'s `Returns:` paragraph per the artifact's exact phrasing.
- Low #4: deferred per the artifact's trigger condition (a second reserved kwarg lands, or `filterset_base_class` extension point is wired); no in-cycle edit.
- Low #5: addressed — module-docstring tense rotated to past/present per the artifact's option (drop the slice-numbering).
- Low #6: forwarded to `rev-django_strawberry_framework.md` project pass per the artifact's explicit routing; no in-cycle GLOSSARY edit.

`spec-021` citation drift (factories.py:3, 12, 98): untouched per dispatch — consolidated under `rev-filters__base.md` Low #2's subpackage-wide forward to the folder pass. The folder-pass author owns the cross-file sweep.

### Validation run

- `uv run ruff format .` — pass / 183 files left unchanged.
- `uv run ruff check --fix .` — pass / All checks passed!
- pytest NOT run per Worker 2 hard rule.

### Notes for Worker 3

- No shadow file was used during this pass.
- `uv.lock` is unchanged (verified via `git status --short uv.lock`).
- All three edits are docstring-only — no logic mutation, no test churn. Existing tests (`test_make_hashable_dict_branch_supports_mixed_key_types`, the factory-arguments tests, and the collision-detection test) continue to pin the behaviours these docstrings now describe more accurately.
- The verbatim Low #3 sentence is appended in place; the artifact phrasing uses RST-style `` ``backticks`` `` for inline code (`` ``filterset_class=`` ``, `` ``__name__`` ``, `` ``_type_filterset_registry`` ``), matching the rest of the file's docstring convention.
- Pre-existing dirty paths under the working tree (sibling rev-* edits and scratchpads) were not touched by this pass.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Per `AGENTS.md` rule "Do not update CHANGELOG.md unless explicitly instructed", and the active 0.0.7 review plan is silent on changelog authorization for this cycle item (the dispatch prompt for this pass does not name any explicit `CHANGELOG.md` authorization). Both citations are required for `Not warranted`; both apply here.

The cycle's edits are all internal:

- **Low #1 (pass-through comprehension collapse, `factories.py:170-181`)** — a pure internal refactor against the existing `build_input_class` helper; same triple objects in same order, zero behavioural change.
- **Low #2 (`_make_hashable` dict-branch `key=repr`, `factories.py:201-206`)** — a parity fix inside a **private** helper. `_make_hashable` has a leading underscore, is not in any `__all__`, and is not re-exported through `filters/__init__.py` (which exports `filter_input_type` and a small public set only). The fix brings the implementation in line with the helper's own pre-existing docstring promise ("stays total-ordered even for mixed, mutually-unorderable member types") rather than introducing a new contract. The only consumer-observable effect is that a dict-with-mixed-key-types `**meta` extra passed through `get_filterset_class` no longer raises `TypeError` on cache lookup — but that input shape was never supported, never tested, and the loud-fail was a latent bug, not a documented contract.
- **Low #3 (`get_filterset_class` `Returns:` paragraph addition, `factories.py:289-298`)** — docstring polish on a consumer-facing helper; describes the existing BFS collision behaviour that was already pinned by `test_filter_arguments_factory_collision_raises_on_distinct_class_with_same_name`. No behaviour change.
- **Low #5 (module-docstring tense rotation, `factories.py:12-14`)** — citation/tense hygiene; the policy text was already correct against the shipped behaviour, only the future-work framing rotted.
- **`_make_hashable` docstring widening (`factories.py:189-200`)** — internal helper docstring tightening to match the post-Low-#2 dict-branch parity.

The dispatch prompt itself acknowledges `Not warranted` as defensible here, citing the internal-helper privacy of `_make_hashable` and the strict-bug-fix framing of the dict-branch parity gap. No consumer-visible public-API surface changed; the pre-existing tests continue to govern every consumer-facing contract these edits touch.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass / 183 files left unchanged.
- `uv run ruff check --fix .` — pass / All checks passed!

---

## Iteration log

To be appended by Workers 2 and 3 on re-passes.

### Verification (Worker 3, pass 3 — terminal)

- `git diff -- CHANGELOG.md` is empty — confirmed, matches the `Not warranted` disposition.
- Changelog disposition cites BOTH `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") AND the active 0.0.7 review plan's silence on changelog authorization. Both citations are present at the disposition's `Reason` section.
- Internal-only framing is honest:
  - `_make_hashable` is a private helper — leading underscore at `factories.py:190`, not in `django_strawberry_framework/filters/__init__.py::__all__` (export list at lines 90-107 contains only public names: `ArrayFilter`, `Filter`, `FilterSet`, `RelatedFilter`, `TypedFilter`, `filter_input_type`, etc.).
  - The Low #2 parity fix (`factories.py:203-206`, `sorted(..., key=repr)` on the dict branch) brings the implementation in line with the pre-existing docstring at `factories.py:197-201` ("Both unordered branches sort by `repr` ... stays total-ordered even for mixed, mutually-unorderable member or key types"). The docstring's promise predates the fix; the implementation now honours it.
  - Low #1 (`factories.py:177-180`): pure-pass-through comprehension collapse — same triples in same order, zero behaviour change.
  - Low #3 (`factories.py:296-299`): docstring polish on `get_filterset_class`'s `Returns:` describing already-pinned BFS collision behaviour.
  - Low #5 (`factories.py:12-14`): module-docstring tense rotation, no policy change.
  - No public-surface symbol changed.
- Logic pass + comment pass already accepted in this artifact's iteration log (Status was raised to `logic-accepted` then `comments-accepted` on prior verifier passes); terminal-verify checked the remaining changelog disposition only.
- Ruff outcomes (terminal pass):
  - `uv run ruff format --check django_strawberry_framework/filters/factories.py tests/filters/test_factories.py` -> `2 files already formatted`.
  - `uv run ruff check django_strawberry_framework/filters/factories.py tests/filters/test_factories.py` -> `All checks passed!`.
- Focused test confirmation: `uv run pytest tests/filters/test_factories.py -x -k "make_hashable_dict_branch" --no-cov` -> `1 passed, 21 deselected`.

`cycle accepted; verified` — top-level `Status: verified`; marking the checklist box in `docs/review/review-0_0_7.md`.
