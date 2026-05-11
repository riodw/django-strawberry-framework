# Review: `django_strawberry_framework/optimizer/walker.py`

## High:

None.

## Medium:

### `hint.prefetch_obj` path skips `_append_prefetch_unique` dedupe

`_apply_hint` appends a consumer-supplied `Prefetch` directly to `plan.prefetch_related` with `list.append`, bypassing the `_append_prefetch_unique` helper used by `_plan_prefetch_relation`. When a hint targets the same lookup path the walker would otherwise infer (e.g., a Meta-class `force_prefetch` plus a sibling default-prefetch traversal from a different code path, or a re-run after plan-cache eviction with overlapping fragments), the plan can end up with two `Prefetch` entries for the same lookup. Django then attaches the relation twice and the second call replaces the first — the consumer-supplied queryset can be silently dropped depending on order. Use `_append_prefetch_unique` here so the lookup-path dedupe applies to hint-sourced prefetches as well.

```django_strawberry_framework/optimizer/walker.py:296:302
    if hint.prefetch_obj is not None:
        attname = getattr(django_field, "attname", None)
        if attname is not None:
            _append_unique(plan.only_fields, f"{prefix}{attname}")
        _append_unique_many(plan.planned_resolver_keys, resolver_identities)
        plan.prefetch_related.append(hint.prefetch_obj)
        return True
```

### `hint.prefetch_obj` path does not flip `plan.cacheable = False`

`_plan_prefetch_relation` correctly flips `plan.cacheable = False` whenever the target type overrides `get_queryset`, because the resulting queryset depends on `info` (per-request state) and re-using the plan across requests would leak the first request's user/permissions. The `hint.prefetch_obj` branch in `_apply_hint` is structurally identical from a cache-safety perspective: a consumer-supplied `Prefetch` object commonly closes over a queryset built with request- or user-scoped filters, but the plan is then cached and re-used for matching ASTs. The plan cache will serve the cached `Prefetch` object — and its embedded queryset — to subsequent requests. At minimum, set `plan.cacheable = False` on this branch, matching the conservative posture taken for `has_custom_get_queryset`. The alternative is to document on `OptimizerHint.prefetch_obj` that the prefetch's queryset must be request-independent, but a runtime guard is safer.

```django_strawberry_framework/optimizer/walker.py:296:302
    if hint.prefetch_obj is not None:
        attname = getattr(django_field, "attname", None)
        if attname is not None:
            _append_unique(plan.only_fields, f"{prefix}{attname}")
        _append_unique_many(plan.planned_resolver_keys, resolver_identities)
        plan.prefetch_related.append(hint.prefetch_obj)
        return True
```

### `_walk_selections` is a 94-line / 9-branch hotspot with untested branch matrix

The static helper flags `_walk_selections` as the longest function in the file (lines 91-184, 9 branch nodes). The body interleaves the field-map resolution, fragment recursion, scalar-vs-relation dispatch, hint dispatch, and same-query-vs-prefetch dispatch. Each path inside has its own helper, but the dispatch itself is the kind of branchy core where a missing per-branch named test is a Medium "missing tests for important branches" finding per the review template. Specifically: (a) the `django_field is None` skip branch (line 115), (b) the `not is_relation` scalar-projection branch (line 117), (c) the fragment-recursion branch (line 103), (d) the hint-handled-return branch (line 142), and (e) the `target_type is None` branch interacting with `plan_relation` (line 134). Confirm each branch has a named behavioural test in `tests/test_optimizer*.py`; if any reach the branch only as a side-effect of a higher-level integration test, add a focused unit test in the same change as any fix that touches the dispatch shape.

```django_strawberry_framework/optimizer/walker.py:091:184
def _walk_selections(
    selections: list[Any],
    model: type[models.Model],
    plan: OptimizationPlan,
    prefix: str = "",
    info: Any | None = None,
    runtime_prefixes: tuple[tuple[str, ...], ...] = ((),),
) -> None:
```

### Hint read tolerates `_optimizer_hints = None` only by accident

Line 141 reads `getattr(type_cls, "_optimizer_hints", {}).get(django_name)`. If a future code path sets `type_cls._optimizer_hints = None` (the same `or {}`/`getattr(..., default) or default` shape pattern flagged in `conf.py` and `_context.py`), this raises `AttributeError: 'NoneType' object has no attribute 'get'`. The legacy mirror writer is presumably disciplined, but the documented contract is "dict or absent". Use `getattr(type_cls, "_optimizer_hints", None) or {}` to match the shape-guard pattern used elsewhere in the optimizer, or — preferred — read through `registry.get_definition(type_cls)` as the existing TODO anchor at line 138 already requires. This is a recurring "validates A but not the intersection of A and B" pattern called out in the prior cycle's memory.

```django_strawberry_framework/optimizer/walker.py:141:142
        hint = getattr(type_cls, "_optimizer_hints", {}).get(django_name) if type_cls is not None else None
        if hint is not None and _apply_hint(
```

## Low:

### Inconsistent `attname` shape-guard between hot paths

`_plan_select_relation` (line 201) and `_plan_prefetch_relation` (line 239) read `attname = getattr(django_field, "attname", None)` defensively, but `_can_elide_fk_id` reads `field.attname is not None` directly (line 389). Both touch the same `django_field` shape inside the same call frame. Either both should defensive-getattr or neither should. If the documented contract is "any Django relation field has `attname`", drop the `getattr` defaults in the two planners; if the contract is "any field shape including reverse descriptors", keep `getattr` in `_can_elide_fk_id` too.

```django_strawberry_framework/optimizer/walker.py:386:396
    if pk_fields is not None and len(pk_fields) > 1:  # pragma: no cover
        return False
    return (
        field.attname is not None
        and related_model is not None
```

### `_ensure_connector_only_fields` may KeyError on composite PK M2M

Line 436 reads `parent_field.related_model._meta.pk.attname` on the many-to-many branch. The matching `_can_elide_fk_id` is careful to handle the Django 5.2+ composite-PK case (line 382-387, guarded with `# pragma: no cover`), but `_ensure_connector_only_fields` reaches for `_meta.pk` without the same guard. On a composite PK target this is the model's `CompositePrimaryKey` pseudo-field, whose `attname` semantics differ. Today the test surface does not exercise composite PKs so the consequence is theoretical, but the symmetry with `_can_elide_fk_id` would document the assumption explicitly.

```django_strawberry_framework/optimizer/walker.py:435:438
    else:
        attname = parent_field.related_model._meta.pk.attname
    if attname is not None:
        _append_unique(plan.only_fields, attname)
```

### Two TODO(post-foundation) anchors duplicate the same retirement signal

Lines 64-67 and 138-140 carry near-identical TODOs naming the same "compatibility mirror removal" retirement slice on two adjacent reads (`_optimizer_field_map` and `_optimizer_hints`). Consolidate behind a single helper, or — at minimum — make both anchors cite the same retirement slice label so a future grep returns one decision point, not two near-duplicates. Same theme as the `field_meta.py` carry-forward: the mirror has writer sites; only the readers carry the anchor.

```django_strawberry_framework/optimizer/walker.py:064:069
    # TODO(post-foundation): once the one-minor compatibility mirror from
    # ``DjangoTypeDefinition.field_map`` to ``type_cls._optimizer_field_map``
    # is removed, read through ``registry.get_definition(type_cls)`` here
    # instead of the legacy class attribute.
    cached_map = getattr(type_cls, "_optimizer_field_map", None) if type_cls is not None else None
    field_map = cached_map if cached_map is not None else {f.name: f for f in model._meta.get_fields()}
```

### `_merge_aliased_selections` constructs `SimpleNamespace` shaped like a Strawberry selection

The merge synthesizes a `SimpleNamespace` carrying `name`, `alias`, `directives`, `arguments`, `selections`, and a private `_optimizer_response_keys` (line 515-526). The synthesized shape is then consumed by recursive `_walk_selections`/`_apply_hint` callers as if it were a real selection. This works today but tightly couples the merge to the consumer-side attribute set; if a future slice teaches `_walk_selections` to read `sel.type_condition` (currently only `_is_fragment`'s `hasattr` check) or any other selection attribute, the synthesized merged selection will silently lie about it. Either keep this in mind as a known coupling, or extract a tiny `_MergedSelection` dataclass naming the contract.

```django_strawberry_framework/optimizer/walker.py:515:527
            merged = SimpleNamespace(
                name=sel.name,
                alias=getattr(sel, "alias", None),
                directives=getattr(sel, "directives", None) or {},
                arguments=getattr(sel, "arguments", None) or {},
                selections=list(getattr(sel, "selections", None) or []),
                _optimizer_response_keys=[_response_key(sel)],
            )
            seen[key] = merged
            result.append(merged)
```

### `_is_fragment` uses `hasattr` for both fragment spread and inline fragment

`_is_fragment` returns `hasattr(selection, "type_condition")`. The shape contract is "any object exposing `type_condition` is a fragment". Strawberry's `SelectedField` does not currently carry `type_condition` so the discriminant is correct, but the `SimpleNamespace` produced by `_merge_aliased_selections` does not pre-declare the attribute either, so the discriminant is purely structural. A short docstring note on `_is_fragment` clarifying "we rely on Strawberry SelectedField never exposing `type_condition`" would lock the invariant; equivalent to the `_context.py` calibration about isinstance-vs-getattr dispatch order being undocumented.

```django_strawberry_framework/optimizer/walker.py:542:544
def _is_fragment(selection: Any) -> bool:
    """Return ``True`` if the selection is a fragment spread or inline fragment."""
    return hasattr(selection, "type_condition")
```

## What looks solid

- The two-phase walk (resolve field map → merge aliases → dispatch) and the dedicated `_plan_select_relation` / `_plan_prefetch_relation` decomposition is clean; the dispatch core stays readable despite the helper's complexity flag.
- `_apply_hint` documents the priority order explicitly and defers conflict arbitration to `OptimizerHint.__post_init__`, matching the calibration from the `hints.py` review (one owner for the hint shape contract).
- `_can_elide_fk_id` is conservative: composite PK guarded, attname/PK-name agreement checked, many-to-many and one-to-many excluded, auto-created excluded.
- `_ensure_connector_only_fields` correctly handles three distinct connector-column cases (one-to-many, many-to-many, default forward FK target) and falls through to a debug log rather than silently producing a wrong `only()`.
- `_build_child_queryset` accepts a precomputed `has_custom_qs` flag, avoiding the duplicate `target_type.has_custom_get_queryset()` call the static helper would otherwise have flagged across `plan_relation` and the prefetch planner.
- Static helper was run per the optimizer-folder mandate; the Django/ORM marker table was walked and every entry is either justified by the surrounding logic (e.g., `_meta.get_fields()` fallback documented at line 60) or surfaced as a finding above.

---

### Summary:

Two cache-safety findings dominate: the `hint.prefetch_obj` branch in `_apply_hint` bypasses both `_append_prefetch_unique` dedupe and the `plan.cacheable = False` flip that the inferred-prefetch path uses for request-scoped querysets. Both are plan-cache poisoning risks that mirror the `has_custom_get_queryset` discipline already in place a few lines away. Beyond those, the `_optimizer_hints` read inherits the same "documented dict, no shape guard" pattern flagged in earlier cycles and should move to `registry.get_definition` along with its sibling `_optimizer_field_map` reader. The walker's hotspot complexity is structurally fine — helpers carry the weight — but a per-branch named test audit for `_walk_selections` is recommended in any change that touches the dispatch core. Carry forward at the optimizer folder pass: confirm `hint.prefetch_obj` dedup/cacheable discipline, audit the legacy `_optimizer_*` mirror reader sites against the `registry.get_definition` retirement slice, and check whether `_append_prefetch_unique` / `_append_unique` should live in `plans.py` next to `_lookup_path` rather than in `walker.py`.

## Verification

PASS (Worker 3, 2026-05-10).

- Medium 1 (dedupe): `_apply_hint` now routes `hint.prefetch_obj` through `_append_prefetch_unique`. New test `test_plan_prefetch_obj_hint_dedupes_repeat_lookups` pins single-entry behaviour on repeat selections.
- Medium 2 (cacheable): `plan.cacheable = False` set on the `hint.prefetch_obj` branch with explanatory comment matching the `_plan_prefetch_relation` discipline. New test `test_plan_prefetch_obj_hint_marks_plan_non_cacheable`.
- Medium 3 (hotspot tests): three new behavioural tests added against `_walk_selections` dispatch shape via the hint paths.
- Medium 4 (`_optimizer_hints = None` shape guard): read rewritten to `getattr(..., None) or {}` pattern. New test `test_plan_tolerates_optimizer_hints_set_to_none`.
- Lows: intentionally not modified this cycle — they are calibration / future-pass items (attname symmetry, composite-PK M2M, TODO consolidation, `SimpleNamespace` coupling, `_is_fragment` docstring) and the artifact body frames them for the optimizer folder pass.
- Validation: `uv run pytest tests/optimizer -q` → 232 passed. Walker.py module coverage 100%. Focused-run global fail_under gate trips harmlessly (expected per worker-3 calibration).
