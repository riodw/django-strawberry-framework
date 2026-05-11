# Review: `django_strawberry_framework/types/resolvers.py`

## High:

None.

## Medium:

### `_will_lazy_load` false-negative via `__dict__` short-circuit hides real lazy-load on many-side

`_will_lazy_load` returns `False` as soon as `field_name in root.__dict__` is true. For real Django model instances, the *many-side* related descriptor name (e.g., a reverse FK or M2M `entries`) is almost never in `__dict__` — but if a consumer (or a test double, or a future code path) ever sets `root.entries = <something>` directly, the function will declare "already loaded" and `_check_n1` will silently skip the strictness branch. The docstring documents this as "compatibility for test doubles" but the same short-circuit runs in production. The proper check on the many side is `field_name in root._prefetched_objects_cache`, full stop; the `__dict__` fallback should be limited to single-valued relations (where Django's descriptor genuinely populates `__dict__` only after access).

```django_strawberry_framework/types/resolvers.py:70:93
def _will_lazy_load(root: Any, field_name: str) -> bool:
    ...
    if field_name in getattr(root, "__dict__", {}):
        return False
    state = getattr(root, "_state", None)
    fields_cache = getattr(state, "fields_cache", {})
    if field_name in fields_cache:
        return False
    prefetch_cache = getattr(root, "_prefetched_objects_cache", {})
    return field_name not in prefetch_cache
```

Recommended: pass `kind` (or split into `_will_lazy_load_single` / `_will_lazy_load_many`) and check `__dict__`/`fields_cache` only for single-valued and `_prefetched_objects_cache` only for many. A named per-cardinality unit test for the "consumer set attribute then strictness=raise" branch should be added — the package-wide "documented contract, not enforced" calibration applies: the docstring promises strictness, the code silently exempts a path.

### Strictness branch coverage is implicit through `_check_n1` callers

`_check_n1` has four behavioural branches (planned-absent, planned-hit, lazy-load-skip, strictness=raise, strictness=warn, strictness=off-default) and is invoked from three resolver closures plus the forward-FK-id-elided fast path. None of those branches has a named per-shape test reachable through this module's public surface; coverage today comes via end-to-end query tests in `examples/fakeshop/test_query/`. Per `worker-1` calibration ("a branchy function whose branches are only incidentally covered = Medium missing-tests"), this is Medium not Low — the strictness contract is consumer-visible and silently flipping `"off"` ↔ `"warn"` ↔ `"raise"` is exactly the kind of defect that won't surface unless a branch is pinned.

```django_strawberry_framework/types/resolvers.py:96:119
def _check_n1(...):
    planned = _get_context_value(context, DST_OPTIMIZER_PLANNED)
    if planned is None: return
    ...
    if key in planned: return
    if not _will_lazy_load(root, field_name): return
    strictness = _get_context_value(context, DST_OPTIMIZER_STRICTNESS, "off")
    if strictness == "raise": raise OptimizerError(...)
    if strictness == "warn": _resolver_logger.warning(...)
```

Recommended: add named branch tests under `tests/` (planned-absent → silent, planned-hit → silent, planned-miss + cached → silent, planned-miss + lazy + off → silent, +warn → log, +raise → OptimizerError) using `schema.execute_sync` per AGENTS "test through real usage".

### `_check_n1` deferred import of `OptimizerError` is structural, not circular

`from ..exceptions import OptimizerError` is moved into the function body. There is no circular-import risk here — `..exceptions` is a stdlib-only leaf module (per `rev-exceptions.md` skip artifact) and `..optimizer` already imports freely at module top. The deferred import is dead defensive work that runs on every strict-raise dispatch and obscures the dependency graph that the file's docstring emphasises ("imports nothing from base.py"). Same calibration as the optimizer-folder "dead `_optimizer_active` ContextVar" Medium — code that pretends to defend an invariant that isn't real.

```django_strawberry_framework/types/resolvers.py:102:103
    """B3: warn or raise if the relation is not planned and would lazy-load."""
    from ..exceptions import OptimizerError
```

Recommended: lift the import to module top alongside `..optimizer` and `..utils.relations`.

## Low:

### `_is_fk_id_elided` defaults `elisions` to a fresh `set()` per call

`_get_context_value(..., set())` allocates a new empty set on every forward-resolver dispatch when the context key is absent. Same package-wide `or {}` / `or ()` defensive-coerce posture flagged in `conf.py`, `optimizer/extension.py`, `_context.py`, `walker.py`, `base.py`. Use a module-level `_EMPTY_FROZENSET = frozenset()` sentinel or check `is None` first.

```django_strawberry_framework/types/resolvers.py:47:53
    elisions = _get_context_value(
        getattr(info, "context", None),
        DST_OPTIMIZER_FK_ID_ELISIONS,
        set(),
    )
    key = resolver_key(parent_type, field_name, runtime_path_from_info(info))
    return key in elisions
```

### `attname` resolution is `getattr(field, "attname", None)` not from `FieldMeta`

`field.attname` is fetched via `getattr` with a `None` default at closure-build time, then guarded inside `forward_resolver` with `if attname is not None`. Per the `optimizer/field_meta.py` carry-forward calibration, `FieldMeta` is the documented single source of truth for relation shape (forward/reverse, attname presence). The walker side already consumes `FieldMeta`; here the resolver re-derives the same shape via `getattr` + `relation_kind`. Folder-pass DRY candidate: should resolvers consume `FieldMeta` instead of re-deriving?

```django_strawberry_framework/types/resolvers.py:167:173
    attname = getattr(field, "attname", None)

    def forward_resolver(root: Any, info: Info) -> Any:
        if attname is not None and _is_fk_id_elided(info, field_name, parent_type):
            return _build_fk_id_stub(root, field)
```

### Three near-duplicate `__name__ = f"resolve_{field_name}"` assignments

The closure-rename idiom is repeated in all three branches of `_make_relation_resolver`. Helper's repeated-literals section flagged `resolve_` 3x. Pull into a single `_name(closure, field_name)` helper or use `functools.wraps`-style decorator; trivial maintainability fix.

```django_strawberry_framework/types/resolvers.py:151:175
        many_resolver.__name__ = f"resolve_{field_name}"
        ...
        reverse_one_to_one_resolver.__name__ = f"resolve_{field_name}"
        ...
        forward_resolver.__name__ = f"resolve_{field_name}"
```

### TODO at line 44 cites `0.0.5 relay interfaces` but does not pair with `NotImplementedError`

Per `AGENTS.md`: "pair it with `NotImplementedError` if the call path must fail loudly". Here the call path *does not* fail loudly — Relay GlobalID handling simply isn't isolated yet. The TODO is an annotation for future work, not an active anchor. Either fine to leave as-is (the comment names the slice that will land the change) or — for consistency with the relay-interfaces slice anchors already on `types/base.py` and `types/relay.py` — restate it as part of that slice's TODO inventory.

```django_strawberry_framework/types/resolvers.py:44:46
    # TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
    # keep Relay GlobalID handling isolated from forward-relation FK-id
    # elision; Relay id resolution belongs in ``types.relay``.
```

### Import grouping: two `from ..optimizer._context import` blocks back-to-back

Lines 30-34 import three sentinels; lines 35-37 import `get_context_value as _get_context_value` from the same module. Collapse into one `from ..optimizer._context import (...)` block. Pure layout.

```django_strawberry_framework/types/resolvers.py:30:37
from ..optimizer._context import (
    DST_OPTIMIZER_FK_ID_ELISIONS,
    DST_OPTIMIZER_PLANNED,
    DST_OPTIMIZER_STRICTNESS,
)
from ..optimizer._context import (
    get_context_value as _get_context_value,
)
```

## What looks solid

- Helper ran (mandatory under `types/`); overview confirms file is 199 lines, 5 module-level symbols, one 55-line hotspot (`_make_relation_resolver`) split cleanly across three cardinality branches.
- Module docstring's "imports nothing from base.py" promise is honoured — dependency direction is one-way into `..optimizer` and `..utils.relations`.
- `_build_fk_id_stub`'s `router.db_for_read(..., instance=root if hasattr(root, "_state") else None)` correctly handles synthetic test-double roots; the `instance=` parameter is the right Django routing hook.
- Reverse-OneToOne branch correctly localises `field.related_model.DoesNotExist` capture outside the closure (one attribute lookup per finalize, not per resolve).
- `skip_field_names: frozenset[str] = frozenset()` correctly uses an immutable default — no mutable-default trap.
- The closure-renaming pattern keeps GraphiQL traces readable.
- `_check_n1` returns early on `planned is None`, preserving the "optimizer not engaged" no-op path (correct).

---

### Summary:

Resolvers module is well-scoped and the cardinality split is clean. Two Medium logic concerns: (1) `_will_lazy_load`'s `__dict__` short-circuit silently exempts the many-side strictness path, and (2) `_check_n1`'s six behavioural branches lack named per-branch tests — both consumer-visible strictness contract risks. One Medium structural cleanup: defer-imported `OptimizerError` is dead defensive work. Lows are all package-wide pattern matches (`or {}` posture, `FieldMeta`-as-SSoT question, `resolve_` rename triplet, TODO/slice anchor shape, import-block collapse) and should be carried into the `types/` folder pass for consolidation with sibling files. Cross-folder follow-up: optimiser/resolvers shared sentinel-default and `runtime_path_*` ownership question already flagged in `optimizer/_context.py` and `optimizer/plans.py` artifacts now has a third caller site here.

## Verification

PASS (2026-05-11). Worker 2 diff addresses every Medium and the two non-deferred Lows:

- Medium 1 (`_will_lazy_load` __dict__ short-circuit on many): split into `_will_lazy_load_single` and `_will_lazy_load_many`; the many-side path no longer consults `__dict__`. `_check_n1` now takes a keyword-only `kind` and dispatches per cardinality. New tests `test_check_n1_many_kind_treats_consumer_set_attribute_as_lazy` and `test_check_n1_many_kind_respects_prefetched_objects_cache` pin the corrected contract.
- Medium 2 (named per-branch tests for `_check_n1`): four new tests (`planned_absent`, `planned_hit`, `default_strictness_off`, `raise_strictness_raises`) plus the two many-side tests above; the existing `_check_n1_warns_for_unplanned_lazy_load` covers the `warn` branch. All six behavioural branches now have named coverage.
- Medium 3 (deferred `OptimizerError` import): lifted to module-top imports.
- Low 1 (fresh `set()` per call): replaced with `_EMPTY_FROZENSET` module-level sentinel.
- Low 3 (three `__name__` rename calls): centralised into `_name_resolver` helper, all three branches route through it.
- Low 2 (FieldMeta-as-SSoT for `attname`), Low 4 (TODO slice-anchor consistency), Low 5 (import-block collapse): retained as folder-pass polish per artifact framing; acceptable deferrals.

`uv run pytest tests/types -q --no-cov` → 90 passed, 1 skipped.
