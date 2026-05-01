# Spec: Optimizer O4 — Nested Prefetch Chains

## Problem statement
`docs/spec-optimizer.md` rebuilds the optimizer around a root-gated selection-tree walk. O1, O2, O3, O5, and O6 have shipped, so the optimizer is effective for depth-1 relation selections. The remaining O-slice is O4: planning nested relation paths so a query like `{ allCategories { items { entries { value } } } }` is optimized at the root instead of falling back to per-row lazy loads at the second relation level.

The current walker already carries a `prefix` argument and can collect scalar fields through `select_related` paths via `_collect_scalar_only_fields`, but it stops after planning the current relation. The TODO in `django_strawberry_framework/optimizer/walker.py` (right at the end of `_walk_selections`) is the implementation anchor: recurse into relation child selections and emit depth > 1 relation chains.

## End-goal context
`docs/spec-optimizer_beyond.md` assumes O4 is the last missing foundation slice. B1 plan caching, B7 field metadata, B3 strictness, B4 optimizer hints, B5 context stashing, B2 FK-id elision, and B6 schema audit have shipped or are designed around the current `OptimizationPlan` shape. O4 must therefore extend the planner without breaking these contracts:

- Cached plans must remain reusable; request-dependent nested `Prefetch` querysets must set `plan.cacheable = False`.
- `_optimizer_field_map` (B7) is already used at every recursion level because `_walk_selections` re-reads it on each entry — that property must be preserved when recursion is introduced for nested branches.
- `Meta.optimizer_hints` (B4) must apply at nested levels, not only root fields.
- `get_queryset` downgrades (O6) must compose with nested child plans.
- B2 FK-id elisions and B3 strictness sentinels must use walker-produced branch-sensitive resolver keys once nested paths exist; Django lookup paths are only for debugging/B8 (see "Lookup paths vs resolver keys" below).
- Future B8 queryset diffing will normalize `select_related` paths and `Prefetch.prefetch_to` paths, so O4 should preserve stable lookup identities.

## Current state
`OptimizationPlan` currently holds:

- `select_related`: single-valued relation paths for `QuerySet.select_related`.
- `prefetch_related`: strings or `Prefetch` objects for `QuerySet.prefetch_related`.
- `only_fields`: root-query scalar paths for `QuerySet.only`.
- `fk_id_elisions`: currently relation paths whose selected target primary key can be served from the source row. O4 must migrate this bag, or a replacement bag, to branch-sensitive resolver keys.
- `cacheable`: whether the plan can be stored in the extension plan cache.

`plan_optimizations(selected_fields, model, info=None)` calls `_walk_selections(...)` with an empty prefix. `_walk_selections` can already produce prefixed paths such as `item__category_id` for single-valued joins via `_collect_scalar_only_fields`, but the final relation-dispatch block still has O4 TODO anchors instead of recursing into `sel.selections`. Concretely, the same-query branch's depth-1 behavior is:

```python
# walker.py — current depth-1 behaviour for forward FK / OneToOne
if django_field.related_model is not None:
    _collect_scalar_only_fields(
        sel.selections,
        django_field.related_model,
        plan,
        prefix=f"{full_path}__",
    )
plan.select_related.append(full_path)
# TODO(spec-optimizer_nested_prefetch_chains.md O4): recurse into
# sel.selections to build nested Prefetch chains for depth > 1.
```

`_collect_scalar_only_fields` walks scalar children only and silently drops any nested relation. O4 replaces that call with a recursive `_walk_selections` call so nested relations on the same single-valued chain land in `select_related` instead of being dropped.

`OptimizationPlan.prefetch_related` already accepts `Prefetch` objects. `docs/spec-optimizer.md` describes O4 as emitting `prefetch_related("items__entries")` style chains; this spec narrows the intended implementation to nested `Prefetch` objects whenever a child queryset needs its own optimization (custom `get_queryset`, child `only_fields`, child FK-id elisions, or further nested branches). Plain string lookups remain valid only when the child branch carries no per-queryset state.

## Desired behavior
Depth-2 many-side chain:

- GraphQL: `{ allCategories { items { entries { value } } } }`
- Root queryset: `Category.objects...`
- SQL target: 3 queries total with optimizer enabled — categories, prefetched items, prefetched entries.
- Plan shape: root prefetch covers the full `items__entries` path, expressed as `Prefetch("items", queryset=Item.objects.prefetch_related(Prefetch("entries", queryset=Entry.objects.only("value", "item_id"))))` for the query shown. If scalar fields on `items` are also selected, those fields and the outer connector (`category_id`) belong to the `Item` child queryset, not the root `Category` queryset.

Depth-3 single-valued chain:

- GraphQL: `{ allEntries { item { category { name } } } }`
- Root queryset: `Entry.objects...`
- SQL target: 1 query total with optimizer enabled via `select_related("item__category")`.
- Plan shape: root `select_related` includes the nested path and `only_fields` includes the FK columns and selected scalar columns needed to hydrate the joined rows: `["item_id", "item__category_id", "item__category__name"]`.

Mixed chain:

- GraphQL: `{ allCategories { items { category { id } entries { property { name } } } } }`
- The prefetch branch must optimize the `Item` queryset internally:
  - `items.category` is a forward FK on `Item` and the only target selection is `id`, so the **child** plan should record an FK-id elision on `category` (resolved against `Item.category_id` without a JOIN).
  - `items.entries` is a reverse FK; the child plan emits a nested `Prefetch("entries", queryset=...)` whose inner plan select-relates `property`.
- Net result: 1 query for `Category`, 1 prefetch for `items` (no `category` JOIN), 1 prefetch for `entries` with `property` joined in. Three queries.

This example exercises the contract that nested branches inherit the same dispatch logic the root walker uses, including B2.

## Implementation design
O4 splits recursion into two cases. The two cases share the existing `_walk_selections` entry point — the dispatch decision lives in the relation branch.

### Same-query recursion for single-valued paths
Forward FK and forward OneToOne relations that remain `select_related` stay in the root query. Recursing through these paths can keep using the current `prefix` strategy:

- Add the source FK column to `only_fields` using the current prefix (already done).
- Apply the FK-id elision check at this level (already done; B2 short-circuits before recursion).
- Add the selected relation path to `select_related`.
- Recurse into the related model with `prefix=f"{full_path}__"` using `_walk_selections`, replacing the current `_collect_scalar_only_fields` call. The recursive call handles scalars and nested relations together.

This is the path that makes `entry > item > category` collapse into one SQL query.

```python
# walker.py — proposed same-query recursion (replaces _collect_scalar_only_fields)
else:  # relation_kind == "select"
    runtime_path = (*runtime_prefix, sel.alias or sel.name)
    if django_field.attname is not None:
        _append_unique(plan.only_fields, f"{prefix}{django_field.attname}")
    target_pk_name = _target_pk_name(django_field)
    if (
        _can_elide_fk_id(django_field)
        and not (target_type is not None and target_type.has_custom_get_queryset())
        and not _has_custom_id_resolver(target_type, target_pk_name)
        and _selected_scalar_names(sel.selections, django_field.related_model)
            == {target_pk_name}
    ):
        _append_unique(
            plan.fk_id_elisions,
            _resolver_key(parent_type, django_name, runtime_path),
        )
        continue
    plan.select_related.append(full_path)
    if django_field.related_model is not None:
        _walk_selections(
            sel.selections,
            django_field.related_model,
            plan,
            prefix=f"{full_path}__",
            runtime_prefix=runtime_path,
            info=info,
        )
```

`_collect_scalar_only_fields` becomes obsolete in the same-query branch and can be deleted once the recursion lands and tests pass. (It is not called from the prefetch branch today.)

### Prefetch-boundary recursion for many-side and downgraded paths
Reverse FK, M2M, and O6-downgraded forward relations cross a queryset boundary. Child scalar `only()` paths must not be pushed into the root queryset. Instead:

- Build a child queryset for the related model (use the target type's `get_queryset(queryset, info)` if O6 requires it).
- Refactor `plan_relation` before wiring this branch. Today it calls `target_type.get_queryset(...)` and returns a `Prefetch` object for O6. O4 should move queryset construction into `_build_child_queryset(...)` so custom `get_queryset` is called exactly once and the prefetch branch owns the child plan application.
- Build a child `OptimizationPlan` from the relation's child selections using the related model as the child root and an empty prefix.
- Treat `full_path` as relative to the plan/queryset currently being built. A root plan may legitimately hold a lookup such as `category__properties` after same-query recursion crosses into a later prefetch boundary, but once a child `Prefetch` queryset is created, that child plan resets `prefix=""` and inner `Prefetch` objects use queryset-local paths such as `entries`, not root-global paths such as `items__entries`.
- Add connector columns to the child plan **after** walking (the walker only knows about selected columns; the connector columns must be present even if the schema does not expose them):
  - reverse FK (`one_to_many`): the forward FK back to the parent — `parent_field.field.attname` (e.g. `Item.category_id` when prefetching `Category.items`). The walker starts from the reverse `ManyToOneRel`, so `.field` is the access path to the actual `ForeignKey`.
  - forward FK / OneToOne demoted to Prefetch by O6: the target field Django will match against — `parent_field.target_field.attname`. This is usually the target PK but must preserve `to_field` correctness.
  - M2M (`many_to_many`): the target PK — `parent_field.related_model._meta.pk.attname`. Django handles the through-table query.
- Apply the child plan to the child queryset.
- Wrap the result in `Prefetch(full_path, queryset=child_queryset)`.
- Append the `Prefetch` to the parent plan.
- If the child queryset came from a custom `get_queryset` *or* the child plan has any nested `Prefetch` whose inner queryset is request-dependent, propagate `cacheable=False` to the parent plan.

```python
# walker.py — proposed prefetch-boundary recursion
if relation_kind == "prefetch":
    runtime_path = (*runtime_prefix, sel.alias or sel.name)
    if django_field.attname is not None:
        _append_unique(plan.only_fields, f"{prefix}{django_field.attname}")
    if target_type is not None and target_type.has_custom_get_queryset():
        plan.cacheable = False
    child_qs = _build_child_queryset(django_field, target_type, info)
    child_plan = OptimizationPlan()
    _walk_selections(
        sel.selections,
        django_field.related_model,
        child_plan,
        prefix="",
        runtime_prefix=runtime_path,
        info=info,
    )
    _ensure_connector_only_fields(child_plan, django_field)
    child_qs = child_plan.apply(child_qs)
    if not child_plan.cacheable:
        plan.cacheable = False
    plan.prefetch_related.append(Prefetch(full_path, queryset=child_qs))
    continue
```

```python
# walker.py — proposed helpers
def _build_child_queryset(field: Any, target_type: type | None, info: Any) -> Any:
    """Pick the child queryset, honoring O6 visibility filters."""
    qs = field.related_model._default_manager.all()
    if target_type is not None and target_type.has_custom_get_queryset():
        qs = target_type.get_queryset(qs, info)
    return qs


def _ensure_connector_only_fields(plan: OptimizationPlan, parent_field: Any) -> None:
    """Inject the column Django needs to wire prefetched rows back to parents."""
    if not plan.only_fields:
        # No child only() applied; Django will fetch full rows and connectors come for free.
        return
    if parent_field.one_to_many:
        _append_unique(plan.only_fields, parent_field.field.attname)
    elif not parent_field.many_to_many:
        # Forward FK / OneToOne demoted by O6. Preserve non-PK to_field targets.
        _append_unique(plan.only_fields, parent_field.target_field.attname)
    else:
        # M2M target rows are associated through Django's through-table query.
        _append_unique(plan.only_fields, parent_field.related_model._meta.pk.attname)
```

For a default branch with no child plan and no child `only()` projection, a plain string lookup is still acceptable — but the simplest implementation always emits a `Prefetch`, which is semantically equivalent. Prefer `Prefetch` for uniformity with B8 diffing (which inspects `prefetch_to`).

### Hints are leaf operations
`OptimizerHint.prefetch(obj)` already lets the consumer hand in their own `Prefetch` instance. O4 must not recurse into `sel.selections` for hint-supplied prefetches — the consumer's queryset is the source of truth, including any `only()` and nested prefetches it carries. The current walker already treats `hint.prefetch_obj` as a leaf; preserve that.

`OptimizerHint.prefetch_related()` (no `obj`) and `OptimizerHint.select_related()` should both go through the recursive paths above so nested selections under a hinted relation still get optimized. The current implementation calls `_collect_scalar_only_fields` for `force_select`; that line should also switch to `_walk_selections` for symmetry with the unhinted same-query branch.

## Lookup paths vs resolver sentinel keys
O4 makes bare field-name sentinels insufficient.

Keep two identities separate:

- **Django lookup paths**: strings such as `items__entries` or `item__category`. These are useful for debug output and B8 queryset diffing.
- **Resolver sentinel keys**: branch-sensitive identities used by B2 FK-id elision and B3 strictness when a resolver runs. These must distinguish aliases, sibling branches, parent types, and root fields.

Do not try to derive resolver sentinel keys from `Prefetch` objects after planning. A `Prefetch` only carries Django lookup strings and a queryset; it does not retain the parent `DjangoType`, GraphQL response aliases, or selection-branch identity. The walker has that information while it traverses the selection tree, so it should record resolver keys as part of planning.

### Lookup-path flattening
B8 still needs a helper that flattens relation lookup paths. This helper should recurse through nested `Prefetch.queryset._prefetch_related_lookups` to arbitrary depth, not just one child level. Locate it on `plans.py` next to `OptimizationPlan`.

```python
# plans.py — proposed lookup-path flattening helper
def lookup_paths(plan: OptimizationPlan) -> set[str]:
    """All Django relation lookup paths covered by ``plan`` (for B8/debugging)."""
    paths = set(plan.select_related)
    paths.update(_prefetch_lookup_paths(plan.prefetch_related))
    return paths


def _prefetch_lookup_paths(entries: Iterable[Any], prefix: str = "") -> set[str]:
    paths: set[str] = set()
    for entry in entries:
        if isinstance(entry, str):
            path = f"{prefix}__{entry}" if prefix else entry
            paths.add(path)
            continue
        path = f"{prefix}__{entry.prefetch_to}" if prefix else entry.prefetch_to
        paths.add(path)
        inner = getattr(entry, "queryset", None)
        if inner is not None:
            paths |= _prefetch_lookup_paths(inner._prefetch_related_lookups, path)
    return paths
```

### Resolver sentinel keys
B2 FK-id elision currently works only at depth 1 and is keyed by the bare field name (e.g. `"category"`) on `info.context.dst_optimizer_fk_id_elisions`. There is already a latent leak today: if two unrelated root types both expose a `category` field and only one elides, both forward resolvers will see `"category"` in the elisions set. O4 amplifies this because nested `category` selections at multiple depths, aliases, sibling branches, and parent types collide.

Parent-type + field-name is necessary but not sufficient: it fixes unrelated parent-type collisions, but it still leaks when two sibling/root branches resolve the same `DjangoType.field` with different selection sets. The resolver key therefore needs both:

- the parent type and Django field name, which the resolver closure can know because `_attach_relation_resolvers(cls, fields)` is per type;
- the GraphQL response path branch, with list indexes stripped, so aliases and sibling root fields stay distinct.

Thread a `runtime_path` tuple through `_walk_selections` alongside the Django `prefix`. Use `sel.alias or sel.name` for each GraphQL response segment. Because `_merge_aliased_selections` currently merges by underlying field name, O4 must either preserve the response aliases on merged nodes or record resolver keys from the original selections before merging. Do not collapse two branches into one elision key unless their selection sets are equivalent for that optimization.

```python
# walker.py — keying elisions by parent type + field + runtime branch
runtime_path = (*runtime_prefix, sel.alias or sel.name)
_append_unique(
    plan.fk_id_elisions,
    _resolver_key(type_cls, django_name, runtime_path),
)


def _resolver_key(parent_type: type | None, field_name: str, runtime_path: tuple[str, ...]) -> str:
    """Stable B2/B3 key that survives nesting, aliases, and parent-type collisions."""
    path = ".".join(runtime_path)
    if parent_type is None:
        return f"{field_name}@{path}"
    return f"{parent_type.__name__}.{field_name}@{path}"
```

```python
# resolvers.py — corresponding resolver-side check
def _is_fk_id_elided(info: Any, field_name: str, parent_type: type) -> bool:
    elisions = _get_context_value(
        getattr(info, "context", None),
        "dst_optimizer_fk_id_elisions",
        set(),
    )
    return _resolver_key(parent_type, field_name, _runtime_path_from_info(info)) in elisions
```

`_runtime_path_from_info(info)` should walk `info.path.prev`, drop numeric list indexes, and keep response keys (aliases included). The walker-side `runtime_path` must use the same response-key convention.

`_attach_relation_resolvers` already iterates per type, so passing `cls` into `_make_relation_resolver` and binding it into each resolver closure is straightforward. This change is small enough to land alongside O4 and fixes the depth-1 leak as a side effect.

For B3 strictness, add a resolver-key collection alongside the lookup-path collection. This can be a new `OptimizationPlan.planned_resolver_keys` bag populated by the walker, or an equivalent helper that consumes walker-retained metadata. Do not use `lookup_paths(plan)` for resolver strictness checks; lookup paths and resolver keys answer different questions.

The pseudocode anchors now live in both `optimizer/walker.py` and `types/resolvers.py`, which is intentional: the walker is the only code that can see merged GraphQL selections before planning, while the resolver is the only code that can reconstruct the runtime response branch from `info.path`. Keep both sides on the same key format before changing the extension context stash.

## Interactions with shipped beyond slices
### B1 plan cache
Nested `Prefetch` objects that embed request-dependent `get_queryset(queryset, info)` results are not cacheable. Any recursive branch that calls a custom `get_queryset` must set the root plan's `cacheable` to `False`. The propagation in `_walk_selections`'s prefetch branch handles this when it copies `child_plan.cacheable` upward.

### B3 strictness
Strictness must treat nested optimized relations as planned. Querying `items { entries { value } }` should not warn or raise for `entries` after O4, because the resolver key for that `entries` branch is covered by the root plan. The extension should stash the walker-produced resolver-key set for B3, and may separately stash `lookup_paths(plan)` for introspection/debugging.

### B4 optimizer hints
Hints must be honored at every recursion level:

- `OptimizerHint.SKIP` suppresses planning for the nested relation branch (no recursion).
- `force_select` should participate in same-query recursion when the relation is single-valued — switch its `_collect_scalar_only_fields` call to `_walk_selections` for parity.
- `force_prefetch` creates a prefetch boundary even when the cardinality dispatch would select; it should follow the same prefetch-boundary recursion path as a natural many-side prefetch.
- `prefetch(obj)` is a leaf — do not walk `sel.selections`. Document this explicitly in `hints.py`.

### B2 FK-id elision
FK-id elision can fire inside nested child querysets, but only with the branch-sensitive resolver-key identity above and the same safety guards already in place: target primary key selection only, FK points at the target primary key, no custom `get_queryset`, and no custom id/PK resolver.

The prefetch-boundary case is interesting: a forward FK *inside* a prefetched child queryset can still elide because the child queryset already loaded the source row's `<field>_id`. The recursive `_walk_selections` call on the child plan handles this naturally — it dispatches through the same B2 branch.

### B8 queryset diffing
B8 will diff plan output against existing queryset optimization. O4 should make nested lookup normalization straightforward by reusing `lookup_paths` (above) to flatten:

- `select_related` strings such as `item__category`;
- plain prefetch strings such as `items__entries`;
- nested `Prefetch` objects by combining the outer `prefetch_to` with inner queryset `_prefetch_related_lookups`.

## Test plan
Add walker unit tests in `tests/optimizer/test_walker.py`:

- `test_plan_emits_nested_prefetch_chain_depth_2` for `Category > items > entries` — assert the outer entry is a `Prefetch("items", queryset=...)` whose inner queryset's `_prefetch_related_lookups` contains an `entries` `Prefetch`.
- `test_plan_emits_nested_select_related_chain_depth_2` for `Entry > item > category` — assert `select_related == ["item", "item__category"]` and `only_fields` contains `item_id`, `item__category_id`, `item__category__name`.
- `test_plan_combines_prefetch_boundary_with_inner_select_related` for `Category > items > category` — outer `Prefetch("items", ...)`, inner queryset's plan has `select_related == ["category"]` (or, when `{ id }` only, an FK-id elision instead).
- `test_plan_propagates_uncacheable_nested_custom_get_queryset` — nested target type overriding `get_queryset` flips root plan's `cacheable` to `False`.
- `test_plan_honors_optimizer_hints_at_nested_depth` — `OptimizerHint.SKIP` on a depth-2 relation suppresses its branch entirely.
- `test_plan_honors_prefetch_obj_hint_does_not_walk_inner_selections` — explicit `prefetch_obj` is appended verbatim regardless of selections under it.
- `test_plan_records_nested_fk_id_elision_with_resolver_key` — id-only nested forward FK lands in `fk_id_elisions` keyed by parent type, field name, and runtime branch.
- Fragment, alias, and directive variants for a nested relation branch, reusing the existing synthetic selection helpers (`_sel`, `_inline_fragment`, `_fragment_spread`).

Add extension integration tests in `tests/optimizer/test_extension.py`:

- `test_optimizer_prefetches_nested_reverse_fk_depth_2`: `{ allCategories { items { entries { value } } } }` should execute in 3 queries.
- `test_optimizer_selects_nested_forward_fk_depth_2`: `{ allEntries { item { category { name } } } }` should execute in 1 query.
- `test_optimizer_strictness_accepts_nested_planned_relation`: strictness `"raise"` should not raise for a nested relation covered by O4.
- `test_optimizer_nested_fk_id_elision_does_not_leak_to_sibling_branch`: a nested id-only branch should not elide an unrelated same-name relation branch on a different parent type.
- `test_optimizer_nested_prefetch_with_custom_get_queryset_marks_uncacheable`: combined O6 + O4 path flips the cache flag.

Use the real fakeshop service seeders (`services.seed_data(n)`) for database tests. The four-model graph `Category → Item → Entry → Property` covers every cardinality the spec exercises.

Add resolver-focused tests in `tests/types/test_resolvers.py`:

- Update the existing B2 stub/null tests to use branch-sensitive resolver keys instead of bare field names.
- `test_b2_forward_fk_id_elision_does_not_leak_across_parent_types` for the existing depth-1 leak.
- A runtime-path helper test that proves numeric list indexes are stripped and aliases/response keys are preserved.

## Documentation updates when O4 ships
When implementation lands:

- Update `docs/spec-optimizer.md` current state, visibility status, and checklist to mark O4 shipped.
- Update `docs/spec-optimizer_beyond.md` current state to remove the note that O4 is unimplemented and the `not yet implemented` rider on the B-slices that depend on nested resolver-key sentinels.
- Remove or update `TODO(spec-optimizer_nested_prefetch_chains.md O4)` anchors in source and tests (`walker.py`, `plans.py`, `extension.py`, `resolvers.py`, `hints.py`, and the parallel test files). Also update the older parent-spec O4 references in `docs/spec-optimizer.md`.
- Update the depth-1-only comment in `resolvers.py:_get_relation_field_name` and `_is_fk_id_elided` (currently "Nested-path reconstruction (depth > 1) will need revisiting when O4 ships").

## Definition of done
O4 is complete when:

- Depth > 1 many-side traversal is optimized from the root queryset.
- Nested single-valued traversal emits `select_related` chains and the obsolete `_collect_scalar_only_fields` call site is replaced with recursive `_walk_selections`.
- Prefetch boundaries carry child queryset optimization without pushing invalid child `only()` paths onto the root queryset, and connector FK columns are injected automatically.
- O6 custom `get_queryset` branches compose with nested child plans and correctly mark plans uncacheable.
- B2 and B3 context sentinels use branch-sensitive resolver identities (parent type + field + runtime response path, or an equivalent scheme) and do not leak across siblings, parent types, aliases, or root fields.
- The `lookup_paths` flattening helper exists on `plans.py` for B8/debugging, recurses through nested `Prefetch` objects to arbitrary depth, and is kept separate from resolver strictness keys.
- The new walker and extension tests pass.
- `uv run ruff format .` and `uv run ruff check .` have been run after edits, with TODO-anchored pseudo-code findings left untouched.

## Implementation insertion points (O4)
Line numbers below refer to the current O4 starting point and are approximate; trust the symbols and nearby comments over exact offsets after edits begin.

**`django_strawberry_framework/optimizer/walker.py`**

- `_walk_selections` prefetch branch — replace the current depth-1 prefetch handling with prefetch-boundary recursion.
- `_walk_selections` same-query `select` branch — replace the `_collect_scalar_only_fields(...)` call with recursive `_walk_selections(...)`.
- FK-id elision append site — switch from a bare Django path/string to the branch-sensitive resolver key shape described above.
- O4 TODO at the end of `_walk_selections` — delete once recursion lands.
- `_collect_scalar_only_fields` — delete after same-query recursion replaces all call sites.
- Right after `plan_relation` — add `_build_child_queryset(field, target_type, info)`.
- Near the existing small helper block — add `_ensure_connector_only_fields(plan, parent_field)` and resolver-key helpers.
- Thread a `runtime_prefix` / response-path accumulator through `_walk_selections` before relying on resolver-key sentinels. The anchors are currently comments only; implementation must make alias-preserving behavior explicit before `_merge_aliased_selections` discards branch details.
- Hint branches — update `force_select` and `force_prefetch` to flow through the new recursion paths. `force_select` currently calls `_collect_scalar_only_fields`; `force_prefetch` currently appends a bare string. `prefetch_obj` remains a leaf and must not be re-walked.
- `plan_relation` — refactor so it reports relation kind/downgrade intent without constructing an O6 `Prefetch` itself; `_build_child_queryset` should be the only place that calls target `get_queryset`.

**`django_strawberry_framework/optimizer/plans.py`**

- Module docstring `fk_id_elisions` bullet — update it to describe resolver-key identities rather than bare relation paths.
- `prefetch_related` O4 TODO — replace with shipped nested-`Prefetch` semantics when O4 lands.
- `OptimizationPlan` fields — add a resolver-key collection for B3 strictness if the implementation chooses to store keys directly on the plan.
- End of file — add `lookup_paths(plan)` and recursive helper(s) for B8/debugging path flattening. Do not use this helper for B3 resolver strictness.

**`django_strawberry_framework/optimizer/extension.py`**

- Imports — import `lookup_paths` from `optimizer.plans` if the extension stashes/debugs lookup-path coverage.
- FK-id-elision context stash — continue stashing the set the walker emits, but update comments/tests for branch-sensitive resolver-key shape.
- Strictness context stash — replace ad-hoc planned-set construction with the walker-produced resolver-key set. `lookup_paths(plan)` may be stashed separately for introspection/debugging, but should not drive resolver checks.
- B8 TODO block — leave the pseudo-code anchor intact. `lookup_paths(plan)` is the helper B8 will reuse or extend for queryset diffing.

**`django_strawberry_framework/types/resolvers.py`**

- `_get_relation_field_name` docstring — drop the depth-1 caveat or replace it with the new runtime-path helper description.
- `_is_fk_id_elided` — add `parent_type`, compute the same branch-sensitive resolver key as the walker, and check that key in `dst_optimizer_fk_id_elisions`.
- `_check_n1` — switch from `field_name in planned` to resolver-key lookup for parity with B2.
- `_make_relation_resolver` — add a `parent_type` parameter and thread it into resolver closures.
- Forward resolver body — pass `parent_type` to `_is_fk_id_elided` and `_check_n1`.
- `_attach_relation_resolvers` — pass `cls` into `_make_relation_resolver(field, parent_type=cls)`.
- Add `_runtime_path_from_info(info)` and shared resolver-key helper(s) in this module or import them from a small optimizer utility if needed.

**`django_strawberry_framework/optimizer/hints.py`**

- `OptimizerHint.prefetch(obj)` docs — add a note that the consumer's `Prefetch` queryset is a leaf and inner selections are not walked.

**`tests/optimizer/test_walker.py`**

- Add the O4 walker tests enumerated in the test plan by replacing the current "Future slice placeholders" TODO block, or move that block into a dedicated O4 section. The placeholder currently sits after the O6 tests.

**`tests/optimizer/test_extension.py`**

- Add the O4 integration tests near the existing optimizer query-count and strictness coverage. Keep strictness-specific O4 tests near the strictness suite.

**`tests/optimizer/test_plans.py`**

- Add a `TestLookupPaths` class after the existing `TestOptimizationPlanIsEmpty` class to cover recursive lookup-path flattening.
- If `OptimizationPlan` gains a resolver-key collection, add focused tests for `is_empty` behavior and construction defaults.

**`tests/types/test_resolvers.py`**

- Update the two B2 tests (`test_b2_forward_fk_id_elision_returns_stub_without_accessing_relation`, `test_b2_forward_fk_id_elision_returns_none_for_null_fk`) to use branch-sensitive resolver keys.
- Add `test_b2_forward_fk_id_elision_does_not_leak_across_parent_types`.
- Add or extend a resolver test for alias/runtime-path isolation if the path helper is implemented in `types/resolvers.py`.

## Anchor and lint notes
The O4 pseudocode anchors have already been staged in the relevant source and test files using `TODO(spec-optimizer_nested_prefetch_chains.md O4)`. They intentionally include pseudo-code, so `uv run ruff check .` may report `ERA001` until O4 is implemented. Leave those findings in place while the TODO anchors are serving as implementation guidance; remove them only when replacing the pseudo-code with real code.

## Missing `.py` files
None. Every O4 change lands in an existing module: `walker.py`, `plans.py`, `extension.py`, `resolvers.py`, `hints.py`, and the four parallel test files. No new subpackage or Python module needs to be created for O4.
