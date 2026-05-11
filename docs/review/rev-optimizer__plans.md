# Review: `django_strawberry_framework/optimizer/plans.py`

## High:

None.

## Medium:

### Documented "do not mutate" contract on `OptimizationPlan` is not enforced

The class docstring states that once a plan is handed off (returned from the walker, stashed on `info.context`, or stored in the extension's plan cache) it must not be mutated in place, and that callers must use `dataclasses.replace` to derive modifications. The class is intentionally `@dataclass` (not `frozen=True`) so the walker can accumulate. But nothing freezes the lists or marks the plan as "handed off"; a future caller appending to `plan.select_related` directly will silently poison the extension's plan cache (the cache hands the same instance to every matching request — see the cache docstring at line 73-80). This is the same calibration noted for `registry._finalized` in worker-1.md: a documented contract that the code does not enforce, where the symptom is silent state corruption rather than a loud failure. Consider either (a) flipping to `frozen=True` and having the walker assemble via a builder / `replace`, or (b) exposing a `finalize()` that swaps list attributes for tuples and is called by the walker exit and by `diff_plan_for_queryset`'s `replace` branch. Tests would need to pin "post-handoff mutation does not affect cached plan" — a B1 cache-isolation test.

```django_strawberry_framework/optimizer/plans.py:38:80
@dataclass
class OptimizationPlan:
    """Immutable-ish bag of optimizer directives for one root queryset.
    ...
    Cache invariant: once a plan has been handed off (returned from the
    walker, stashed on ``info.context``, or stored in the extension's
    plan cache), it must not be mutated in place.  Use
    ``dataclasses.replace`` to derive a modified plan.  The class is
    intentionally not ``frozen=True`` so the walker can accumulate
    entries during construction; every other caller treats the plan as
    immutable.
    """

    select_related: list[str] = field(default_factory=list)
    ...
    prefetch_related: list[str | Prefetch] = field(default_factory=list)
    ...
    cacheable: bool = True
    """Whether this plan can be reused from the extension's plan cache.

    O6 ``Prefetch`` downgrades may embed querysets produced by
    ``DjangoType.get_queryset(queryset, info)``. ...
    """
```

### `diff_plan_for_queryset` change-detection by length only is structurally safe but brittle

The early-return guard compares `len(new_select) == len(plan.select_related)` and `len(new_prefetch) == len(plan.prefetch_related)` to decide whether to call `replace`. Today this is safe because `_diff_select_related` and `_diff_prefetch_related` only filter / drop entries — they never substitute, so equal length implies equal contents. But the surrounding code already comments that the function may rewrite the queryset, and a future refactor that introduces "rewrite optimizer entry with a narrowed `Prefetch`" would silently miss the `replace` branch and return the unmodified plan while `new_queryset` is also unchanged-but-shared. Either (a) use `new_select == plan.select_related and new_prefetch == plan.prefetch_related` for value-level equality, or (b) have `_diff_*` return sentinels (`None` for "no change") so the guard is intent-driven rather than length-driven. Test: a regression test naming "filter-only contract" so the assumption is documented.

```django_strawberry_framework/optimizer/plans.py:283:295
new_select = _diff_select_related(plan.select_related, queryset)
new_prefetch, new_queryset = _diff_prefetch_related(plan.prefetch_related, queryset)

if (
    len(new_select) == len(plan.select_related)
    and len(new_prefetch) == len(plan.prefetch_related)
    and new_queryset is queryset
):
    return plan, queryset
return (
    replace(plan, select_related=new_select, prefetch_related=new_prefetch),
    new_queryset,
)
```

### `_diff_prefetch_related` is a branchy hotspot; per-shape behavioural coverage should be named

`_diff_prefetch_related` is flagged by the helper as 41 lines / 6 branch nodes and is the load-bearing reconciliation routine for the O6 downgrade story: pass-through, lossless-absorb, and consumer-wins shapes (with descendant matching and the `prefetch_related(None)` reset idiom) all live here. Each docstring-named shape (no consumer entries on subtree; optimizer-can-absorb; consumer wins on plain-string match; consumer wins on consumer-Prefetch-on-subtree; consumer descendant the optimizer subtree does not cover) needs a named behavioural test in the package tests so that any future refactor breaks loudly. Folder pass should confirm the optimizer test surface covers each branch by name rather than by happy-path integration.

```django_strawberry_framework/optimizer/plans.py:314:354
def _diff_prefetch_related(
    plan_prefetch_related: list[Any],
    queryset: Any,
) -> tuple[list[Any], Any]:
    ...
    for opt_entry in plan_prefetch_related:
        opt_path = _lookup_path(opt_entry)
        descendant_prefix = f"{opt_path}__"
        matching_paths = [
            path for path in consumer_by_path if path == opt_path or path.startswith(descendant_prefix)
        ]
        if not matching_paths:
            new_prefetch.append(opt_entry)
            continue
        if _optimizer_can_absorb(opt_entry, matching_paths, consumer_by_path):
            paths_to_strip.update(matching_paths)
            new_prefetch.append(opt_entry)
        # else: consumer wins on this subtree; optimizer dropped.
    ...
```

## Low:

### `_lookup_path` silently returns non-string / non-Prefetch entries unchanged

`getattr(entry, "prefetch_to", entry)` returns `entry` for anything without `prefetch_to`. The function's contract is "string or `Prefetch`", but a future entry shape (or a bug producing e.g. a `Prefetch`-like object stripped of its attribute) would flow through downstream `in` / `startswith` calls and either crash with `AttributeError` deep in `_diff_prefetch_related` or, worse, silently key by `id(obj)` in `consumer_by_path`. A narrow `isinstance(entry, str)` short-circuit with an explicit `Prefetch`-or-string assertion would make the contract concrete. Same calibration as the `field: object` shape-guard Low recorded for `optimizer/field_meta.py`.

```django_strawberry_framework/optimizer/plans.py:186:193
def _lookup_path(entry: Any) -> str:
    """Return the prefetch lookup path for an entry (string or ``Prefetch``).
    ...
    """
    return getattr(entry, "prefetch_to", entry)
```

### `_consumer_prefetch_lookups` uses the `or ()` defensive pattern flagged across the optimizer

`list(getattr(queryset, "_prefetch_related_lookups", ()) or ())` swallows a `None` value at the attribute the same way `conf.py`'s `or {}` swallows a misconfigured setting (worker-1.md memory). Here it is more defensible because `_prefetch_related_lookups` is a documented Django private attribute that can legitimately be `None`-ish on freshly cleared querysets, but the pattern is worth surfacing at the folder pass for a consistent stance on "defensive empty coerce vs explicit `None` guard".

```django_strawberry_framework/optimizer/plans.py:196:204
def _consumer_prefetch_lookups(queryset: Any) -> list[Any]:
    """Return the ``_prefetch_related_lookups`` already attached to a queryset.
    ...
    """
    return list(getattr(queryset, "_prefetch_related_lookups", ()) or ())
```

### `runtime_path_from_path` / `runtime_path_from_info` live in `plans.py` but operate on `info.path`

These two helpers do not touch `OptimizationPlan` and are pure GraphQL `path`-linked-list utilities. They are referenced by `resolver_key` which is a plan-adjacent concern, but the path helpers themselves are reusable elsewhere (resolvers, extension diagnostics). Module-responsibility question for the folder pass: do these belong in `_context.py` or a new `_paths.py`, leaving `plans.py` to be only the `OptimizationPlan` shape and its diff helpers? Not a per-file defect.

```django_strawberry_framework/optimizer/plans.py:123:150
def runtime_path_from_info(info: Any | None) -> tuple[str, ...]:
    ...
def runtime_path_from_path(path: Any) -> tuple[str, ...]:
    ...
```

### Module docstring claims `prefetch_related` is "many-side relations (reverse FK, M2M) and visibility-downgraded forward rels" but `cacheable=True` default does not match the O6 docstring

The class field docstring at lines 73-80 explains that O6 `Prefetch` downgrades produce request-dependent querysets and therefore plans containing such querysets "must be applied for the current request only". The default `cacheable = True` puts the burden on the walker to flip it to `False` whenever it emits an O6 `Prefetch` downgrade. The contract is documented in prose but not enforced at construction. A factory `OptimizationPlan.with_downgrade(...)` or a post-construction validator that scans `prefetch_related` for `Prefetch` entries with non-default querysets would make the contract concrete. Folder-pass follow-up — the walker is the natural single owner of the flip and may already do this correctly.

```django_strawberry_framework/optimizer/plans.py:72:80
    cacheable: bool = True
    """Whether this plan can be reused from the extension's plan cache.

    O6 ``Prefetch`` downgrades may embed querysets produced by
    ``DjangoType.get_queryset(queryset, info)``. Those querysets can be
    request-dependent because ``info.context`` may carry the current
    user, tenant, or permissions. Plans containing such dynamic
    querysets must be applied for the current request only.
    """
```

## What looks solid

- Static helper run (`scripts/review_inspect.py django_strawberry_framework/optimizer/plans.py`); shadow overview consulted for hotspot and marker triage.
- `_flatten_select_related` correctly handles all three Django `query.select_related` shapes (`False`, `True`, `dict`) and the wildcard-no-overlap decision is explicit and well-documented.
- `apply()` order (`only` → `select_related` → `prefetch_related`) is the right Django order and the docstring explains why.
- `_optimizer_can_absorb` enumerates its three preconditions in prose and in code, and the third condition (consumer paths covered by the optimizer's own lookup tree) is the load-bearing check that prevents silently dropping consumer prefetches.
- `prefetch_related(None)` reset-then-rebuild for stripping absorbed consumer entries is the documented Django idiom and is called out in an inline comment so future maintainers do not "simplify" it away.
- `_prefetch_lookup_paths` recursion handles both bare strings and nested `Prefetch` objects with inner-queryset prefetches, producing the dotted lookup tree the absorb check relies on.
- `Prefetch` is imported under `TYPE_CHECKING` only, keeping `plans.py` import-light and matching the optimizer subpackage's no-import-time-Django-side-effects discipline.

---

### Summary:

`plans.py` is the optimizer's data-shape and reconciliation core and reads as carefully constructed. The substantive concerns are all enforcement-of-documented-contract: the `OptimizationPlan` mutation invariant, the `cacheable=True` default that depends on the walker remembering to flip it for O6 downgrades, and the length-based change-detection in `diff_plan_for_queryset` that is correct today only because the `_diff_*` helpers happen to filter rather than substitute. None are bugs in current behaviour; all are calibration-of-future-breakage findings. The branchy `_diff_prefetch_related` deserves named per-shape behavioural tests at the folder pass. Module-responsibility question on the `runtime_path_*` helpers is a folder-pass concern, not a local defect.

## Verification

PASS — no-source-change cycle; deferred to folder pass. Artifact has no High findings; all Mediums and Lows are explicitly framed as future-breakage calibration or folder-pass follow-ups (mutation-contract enforcement, length-vs-value diff guard, per-shape `_diff_prefetch_related` tests, `_lookup_path` shape guard, `or ()` pattern stance, `runtime_path_*` responsibility, `cacheable=True` default coupling to walker). Worker 2 made no source changes, which matches the artifact's contract that the substantive concerns belong at the optimizer folder pass where the walker / cache / sibling-file ownership boundaries are visible. `uv run pytest tests/optimizer -q` → 229 passed (the focused-run coverage gate trips harmlessly as expected per standing memory).
