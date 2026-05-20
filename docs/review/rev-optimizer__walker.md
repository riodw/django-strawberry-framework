# Review: `django_strawberry_framework/optimizer/walker.py`

Status: verified
<!-- Cycle accepted (logic + comment + changelog passes); checklist box marked in review-0_0_6.md. -->


## DRY analysis

- Defer until a third nested-walk call site lands: extract `_walk_relation_target(sel, related_model, plan, prefix, info, runtime_paths)` to wrap the two parallel `_walk_selections(sel.selections, django_field.related_model, …)` sites at `walker.py:302-309` (inside `_plan_select_relation`, prefix=`f"{full_path}__"`, parent plan) and `walker.py:369-376` (inside `_build_prefetch_child_queryset`, prefix=`""`, child plan). Both sites share six of seven arguments; the parameter axes that differ (prefix shape, plan identity) are exactly what would have to be re-threaded through the new helper.
- Defer until any planner gains an 11th argument: convert `_plan_prefetch_relation` and `_plan_select_relation` to take a `RelationPlanCtx` dataclass, collapsing `_apply_hint`'s `force_select` branch (`walker.py:427-453`) and `force_prefetch` branch (`walker.py:455-467`) and the default dispatch (`walker.py:248-273`) which each re-pass the same 9-/10-arg sequence.
- Defer until the next pass that touches `plan_relation`'s signature: thread the `_target_has_custom_get_queryset(target_type)` result through the boundary so the helper isn't called twice (currently at `walker.py:247` inside `plan_relation` and again at `walker.py:325` inside `_plan_prefetch_relation`). The precomputed-result pattern at `walker.py:339,365,382` shows the explicit-flag-threading idiom but is not extended back across the public `plan_relation` boundary.

## High:

None.

## Medium:

### `force_select` hint silently dispatches to `select_related` on many-side cardinalities

`_apply_hint` at `walker.py:427-454` treats `hint.force_select` as a binary "use `_plan_select_relation` unless the target has `get_queryset`" decision. There is no cardinality guard: a consumer setting `OptimizerHint.select_related()` on a reverse-FK or M2M field will be routed through `_plan_select_relation` (`walker.py:441-453`), which calls `append_unique(plan.select_related, full_path)` (`walker.py:300`) on a many-side path. Django raises `FieldError("...one-to-many or many-to-many relation...")` at queryset execution time on `select_related` of a many-side relation, which surfaces deep in the resolver stack with a stack trace that does not name `OptimizerHint.select_related()` as the cause.

`OptimizerHint.__post_init__` at `hints.py:73-102` validates flag conflicts but does not know the relation cardinality (the hint is constructed before the field's Django descriptor is in scope). The walker is the first place where both the hint and the field are available; it is the right site to raise a typed `ConfigurationError` with both the hinted field name and the actual cardinality, instead of letting Django's `FieldError` surface at query time.

Recommended change: in `_apply_hint`'s `force_select` branch, after the `_target_has_custom_get_queryset` downgrade check (`walker.py:428`), call `is_many_side_relation_kind(relation_kind(django_field))` (both already imported at `walker.py:14`); when the relation is many-side, raise `ConfigurationError(f"OptimizerHint.select_related() on {django_name!r}: Django requires prefetch_related for {kind} relations; use OptimizerHint.prefetch_related() or OptimizerHint.prefetch(obj) instead.")`. Add a test under `tests/optimizer/test_walker.py` next to `test_plan_force_select_hint_downgrades_for_custom_target_get_queryset` (`test_walker.py:1147`) pinning the typed error on a reverse-FK + `force_select` shape.

```django_strawberry_framework/optimizer/walker.py:427:454
    if hint.force_select:
        if _target_has_custom_get_queryset(target_type):
            _plan_prefetch_relation(
                sel,
                django_field,
                target_type,
                plan,
                prefix,
                full_path,
                info,
                runtime_paths,
                resolver_identities,
            )
        else:
            _plan_select_relation(
                sel,
                django_field,
                django_name,
                type_cls,
                target_type,
                plan,
                prefix,
                full_path,
                info,
                runtime_paths,
                resolver_identities,
            )
        return True
```

### `_apply_hint` docstring under-counts the documented hint shapes

`_apply_hint`'s docstring at `walker.py:402-411` claims "the four documented hint shapes (`SKIP`, `prefetch_obj`, `force_select`, `force_prefetch`)" and says the function "returns ``False`` for hints that set no flag". Test `test_plan_no_flag_hint_falls_through_to_default_dispatch` at `tests/optimizer/test_walker.py:1187-1204` pins exactly this no-op-empty-hint fall-through as a fifth documented shape. The docstring's "returns False" sentence is correct but the "four documented hint shapes" claim is incomplete — the no-op `OptimizerHint()` shape is the fifth and is what allows a consumer to configure a hint with no flags (e.g., as a placeholder that the optimizer reads but ignores). The same docstring drift exists in `hints.py:76-82` ("strict priority order (skip → prefetch_obj → force_select → force_prefetch)") — both sites under-document the no-flag shape.

Recommended change: in `walker.py:402-411`, change "four documented hint shapes" to "four configurable hint shapes plus the no-op empty form, where an `OptimizerHint()` with no flags falls through to the default cardinality dispatch". The hint-tests carry-forward in `worker-memory/worker-1.md` flagged this drift at the hints.py review; the walker comment pass is the right place to land the second half of the fix.

```django_strawberry_framework/optimizer/walker.py:402:411
    """Apply a Meta-level ``OptimizerHint`` to ``plan``; return ``True`` when handled.

    Dispatches the four documented hint shapes (``SKIP``, ``prefetch_obj``,
    ``force_select``, ``force_prefetch``) and returns ``True`` after the
    matching action has been taken.  Returns ``False`` for hints that
    set no flag — the caller falls back to the default cardinality
    dispatch in that case.  ``OptimizerHint.__post_init__`` already
    rejects conflicting flag combinations, so the priority order here
    is documentation, not collision arbitration.
    """
```

### `_target_has_custom_get_queryset(target_type)` is called twice per prefetch dispatch

`plan_relation` at `walker.py:67` reads `_target_has_custom_get_queryset(target_type)` to choose `("prefetch", "custom_get_queryset")` vs the cardinality-default dispatch. `_walk_selections` at `walker.py:247` calls `plan_relation(...)`, then if `"prefetch"`, dispatches to `_plan_prefetch_relation`, which AGAIN calls `_target_has_custom_get_queryset(target_type)` at `walker.py:325`. Two method-lookup-and-call cycles per relation traversal on the prefetch path. The same explicit-flag-threading idiom already exists at `walker.py:339,365,382` (`has_custom_get_queryset=has_custom_get_queryset` threaded into `_build_prefetch_child_queryset` and through to `_build_child_queryset`), so the pattern is documented; it just is not extended back across the `plan_relation` boundary.

Recommended change: `plan_relation` returns the kind tuple but could also return the precomputed `has_custom_get_queryset` flag (or change the return to a small namedtuple/dataclass for forward-compat). Then `_walk_selections` threads the flag into `_plan_prefetch_relation`, which threads it into `_build_prefetch_child_queryset` (already threaded today). Below the bar to require a fix in this cycle, but worth a Medium note for the next pass that touches `plan_relation`'s signature. Practical cost today is minor — `_target_has_custom_get_queryset` is a `target_type is not None and target_type.has_custom_get_queryset()` two-condition gate — but the double-call is exactly the kind of redundancy `plans.py`'s explicit-flag-threading already established as the local idiom for "compute once, hand the flag down".

```django_strawberry_framework/optimizer/walker.py:67:76
    if _target_has_custom_get_queryset(target_type):
        logger.debug(
            "Optimizer: will downgrade %s to Prefetch because %s overrides get_queryset.",
            field.name,
            target_type.__name__,
        )
        return ("prefetch", "custom_get_queryset")
    if is_many_side_relation_kind(relation_kind(field)):
        return ("prefetch", "default")
    return ("select", "default")
```

```django_strawberry_framework/optimizer/walker.py:325:339
    has_custom_get_queryset = _target_has_custom_get_queryset(target_type)
    if has_custom_get_queryset:
        plan.cacheable = False
    if django_field.related_model is None:
        append_unique(plan.prefetch_related, full_path)
        return

    child_queryset = _build_prefetch_child_queryset(
        sel,
        django_field,
        target_type,
        plan,
        info,
        runtime_paths,
        runtime_paths,
        has_custom_get_queryset=has_custom_get_queryset,
    )
```

## Low:

### `_walk_selections` default `runtime_prefixes=((),)` is a non-obvious encoding

`_walk_selections` at `walker.py:140-149` takes `runtime_prefixes: tuple[tuple[str, ...], ...] = ((),)` — a tuple of tuples whose default is "one empty path". The natural reading of the default (`((),)`) is hard for a maintainer who has not internalized that `runtime_paths` is a per-response-key tuple-of-tuples for alias-merged selections. The `_response_keys` helper at `walker.py:704-706` is where the per-key fan-out happens (default to a single-key tuple when no `_optimizer_response_keys` is set); the same single-key shape is what `((),)` encodes at the root level. The default works correctly with `plan_optimizations`'s explicit call at `walker.py:46-53` (`runtime_prefixes=(runtime_path_from_info(info),)`), but a direct test-fixture caller passing the default and then expecting `(\"<top>\",)` would see `()` and silently get a single empty-path resolver key.

Recommended change: at the comment pass, add a one-line comment on `walker.py:146-147` noting "default ((),) means 'one empty-path prefix' — root callers from `plan_optimizations` always pass an explicit single-tuple, the default is for direct/test-only callers that have no `info`". The shape is correct; just under-documented.

```django_strawberry_framework/optimizer/walker.py:140:149
def _walk_selections(
    selections: list[Any],
    model: type[models.Model],
    plan: OptimizationPlan,
    prefix: str = "",
    info: Any | None = None,
    runtime_prefixes: tuple[tuple[str, ...], ...] = ((),),
    *,
    source_type: type | None = None,
) -> None:
```

### `_resolve_field_map` fallback produces raw Django fields, not `FieldMeta`

`_resolve_field_map` at `walker.py:106-108` returns `{f.name: f for f in model._meta.get_fields()}` when no `DjangoType` is registered for the model. Every other path in the registry (`registry.get(model)` → `DjangoTypeDefinition.field_map`) returns `dict[str, FieldMeta]`. The walker reads attributes off the values with `getattr(field, attr, default)` (`walker.py:194,205,351,536-557,587-593,605`) so both shapes satisfy the consumer contract — but the polymorphic shape is undocumented. The `field_meta.py` review (`rev-optimizer__field_meta.md`) already flagged this carry-forward; the walker is the consumer site where the polymorphism is load-bearing.

Recommended change: at the comment pass, add a sentence to `_resolve_field_map`'s docstring (`walker.py:88-103`) saying "The fallback path returns the raw Django field objects keyed by `name`; downstream walker code reads attributes through `getattr(..., default)` so both shapes work, but consumers of `_resolve_field_map`'s second return value should treat the values as `FieldMeta | Any` until the registry-coverage gate (TODO) lands." No logic change.

```django_strawberry_framework/optimizer/walker.py:106:108
    field_map = (
        definition.field_map if definition is not None else {f.name: f for f in model._meta.get_fields()}
    )
```

### `_apply_hint` `force_select` / `force_prefetch` branches re-pass identical 9-arg sequences

`_apply_hint` at `walker.py:427-467` calls `_plan_prefetch_relation` and `_plan_select_relation` with positional argument lists that exactly mirror the default-dispatch call sites at `walker.py:248-273`. The 9- and 10-slot positional sequences are the source of most of the function's line count. The duplication is mechanical (the planners take positional arguments by design), and any consolidation would require converting the planners' signatures to take a small `RelationPlanCtx` dataclass — a refactor that would touch the default-dispatch call sites too. Below the bar for this cycle; flag for the folder pass.

Recommended change: defer to folder pass. If a `RelationPlanCtx` dataclass would carry `sel`, `django_field`, `django_name`, `type_cls`, `target_type`, `plan`, `prefix`, `full_path`, `info`, `runtime_paths`, `resolver_identities` together, the four call sites collapse to one-line dispatches. Worth evaluating but not in this file's scope.

```django_strawberry_framework/optimizer/walker.py:427:467
    if hint.force_select:
        if _target_has_custom_get_queryset(target_type):
            _plan_prefetch_relation(
                sel,
                django_field,
                target_type,
                plan,
                prefix,
                full_path,
                info,
                runtime_paths,
                resolver_identities,
            )
        else:
            _plan_select_relation(
                sel,
                django_field,
                django_name,
                type_cls,
                target_type,
                plan,
                prefix,
                full_path,
                info,
                runtime_paths,
                resolver_identities,
            )
        return True
    if hint.force_prefetch:
        _plan_prefetch_relation(
            sel,
            django_field,
            target_type,
            plan,
            prefix,
            full_path,
            info,
            runtime_paths,
            resolver_identities,
        )
        return True
```

### `_ensure_connector_only_fields`'s debug log only fires on shapes the test suite cannot reach

`_ensure_connector_only_fields` at `walker.py:581-606` has a final `logger.debug(...)` fall-through at `walker.py:603-606` when no `attname` can be resolved. Every code path that reaches the `logger.debug` would require a Django relation descriptor that simultaneously has `one_to_many` / `reverse_one_to_one` / forward / M2M shapes AND lacks the standard `field.attname` / `target_field.attname` / `reverse_connector_attname` / `target_field_attname` chain. No fixture in `tests/optimizer/` constructs such a shape, and the branch is not pragma-no-cover. Either the branch is reachable via a custom descriptor the test surface should pin, or it is genuinely unreachable and should be marked `# pragma: no cover` with a one-line comment ("guard for non-standard Django descriptor shapes; no current fixture exercises it").

Recommended change: at the comment pass, decide between (1) adding a fixture under `tests/optimizer/test_walker.py` that pins the debug-log path via a stub descriptor, or (2) marking the `logger.debug(...)` block `# pragma: no cover` with the rationale. Option 2 is the lower-cost path given the coverage gate (`fail_under = 100`); option 1 is more honest but requires building a custom descriptor stub.

```django_strawberry_framework/optimizer/walker.py:600:606
    if attname is not None:
        append_unique(plan.only_fields, attname)
        return
    logger.debug(
        "Optimizer: could not resolve connector column for Prefetch %s; only() may be less precise.",
        getattr(parent_field, "name", parent_field),
    )
```

### `_merge_aliased_selections` divergent-arguments debug log is correct but the future-slice comment over-claims

`_merge_aliased_selections` at `walker.py:644-696` emits a debug log when aliased selections of the same field carry different `arguments` (`walker.py:676-680`), explaining that "today's walker ignores `arguments`, so divergent arguments between aliased selections are harmless." The comment block at `walker.py:667-673` and the inline comment at `walker.py:686-688` both call out that "future optimizer slices use arguments [this merge] must become per-response-key instead of keeping only the first occurrence's values." The phrasing is accurate but the "future slice" anchor is not paired with a TODO comment naming the active design doc — per `AGENTS.md` ("anchor the exact source site with a TODO comment naming the active design doc and slice"), this is the kind of forward-looking comment that should carry a TODO anchor.

Recommended change: at the comment pass, either (1) add a `# TODO(spec-XXX): per-response-key planning when optimizer slices read arguments` anchor pointing to the active design doc, or (2) trim the forward-looking phrasing to "today's walker ignores arguments; if a future slice plans per-argument, this merge must become per-response-key" without the implication that the slice is actively planned. Option 1 if a slice is on the KANBAN, option 2 if not.

```django_strawberry_framework/optimizer/walker.py:667:680
            # Forward-compat signal: today's walker ignores ``arguments``,
            # so divergent arguments between aliased selections are
            # harmless.  When a future slice plans differently per
            # argument set this branch will need to plan per-response-key
            # instead of merging — emitting at DEBUG level here gives
            # that author a fast trace without changing current
            # behaviour.
            sel_arguments = getattr(sel, "arguments", None) or {}
            if sel_arguments != merged.arguments:
                logger.debug(
                    "Optimizer: aliased selections of %s carry different arguments; "
                    "merge keeps the first occurrence's values.",
                    sel.name,
                )
```

## What looks solid

### DRY recap

- **Existing patterns reused.** Plan mutators are funnelled through `append_unique` / `append_unique_many` / `append_prefetch_unique` from `plans.py:215-243` (canonical dedupe discipline lives next to `OptimizationPlan`), with six in-file call sites (`walker.py:206,213,298,300,329,341,353-354,422-425,497-499,601`). Resolver-key construction is funnelled through `resolver_key` / `runtime_path_from_info` from `plans.py:140-162` (one root-path call at `walker.py:51`, one per-relation call at `walker.py:222-223`). Hint dispatch is funnelled through `hint_is_skip` from `hints.py:129-146` (`walker.py:412`). Relation classification is funnelled through `relation_kind` and `is_many_side_relation_kind` from `utils/relations.py:39-70` (`walker.py:74,585`). Sentinel cache-mutation invariant (`OptimizationPlan.finalize()` swaps lists → tuples) is honoured at handoff (`walker.py:58`). Snake-case translation is funnelled through `utils/strings.py:snake_case` (`walker.py:163,520,657`). ConfigurationError raise sites route to `exceptions.py:ConfigurationError` (`walker.py:12,475,483`).

### Other positives

- Polymorphic shape across `field_map.values()` is structurally honoured: every reflective access in `_walk_selections` (`walker.py:194,205`), `_can_elide_fk_id` (`walker.py:536-557`), `_target_pk_name` (`walker.py:563`), `_has_custom_id_resolver` (`walker.py:575-576`), `_ensure_connector_only_fields` (`walker.py:587-605`), `_record_relation_access` (`walker.py:351`), `_prefetch_hint_for_path` (`walker.py:473,490`), `_should_include` (`walker.py:611`), `_merge_aliased_selections` (`walker.py:663,674,684,689-691`), and `_response_key` / `_response_keys` / `_is_fragment` (`walker.py:701,706,711`) uses defensive `getattr(field, attr, default)` so the dual shape (`FieldMeta` for registered types, raw Django field for unregistered fallback) is uniformly handled. The pattern matches `field_meta.py:142-174`'s same idiom — `getattr(..., default)` reads work whether the value is a `FieldMeta` instance or a Django descriptor.
- The cache-mutation invariant is honoured at handoff: `plan_optimizations` at `walker.py:45-58` ends with `return plan.finalize()`, which swaps list fields to tuples per `plans.py:117-122`; the structural enforcement (`finalize()` blocks post-handoff `append`) is pinned by `test_finalize_blocks_post_handoff_append_on_cache_isolation` (`tests/optimizer/test_plans.py:152-160`). Child plans built inside `_build_prefetch_child_queryset` (`walker.py:368`) are NOT finalised — they go through `child_plan.apply(...)` at `walker.py:381` before being wrapped in a `Prefetch`, after which the child plan is dropped (not cached). The finalisation discipline only applies at the parent-plan boundary, which is the correct scope.
- Resolver-key derivation correctly handles aliased selections: `_walk_selections` at `walker.py:217-224` builds `runtime_paths` as the cartesian product of incoming `runtime_prefixes` × per-selection `_response_keys`, then constructs one `resolver_key` per runtime path. The fan-out matches the resolver-side dispatch in `types/resolvers.py` (per the field_meta carry-forward note), and `_merge_aliased_selections` at `walker.py:665-666` populates `_optimizer_response_keys` so the per-key fan-out is visible to `_response_keys` at `walker.py:706`. The two-test surface (`test_plan_elides_forward_fk_id_only_selection_for_each_alias`, `test_fragment_spread_from_multiple_sites_does_not_double_prefetch`) pins both the fan-out and the dedupe at `walker.py:354`.
- The `select_related` vs `prefetch_related` cardinality choice rules are correctly centralised in `plan_relation` (`walker.py:61-76`): custom-`get_queryset` downgrade first (matching the "downgrade to Prefetch when target type has a custom get_queryset" rule in `START.md:60`), then many-side detection via `is_many_side_relation_kind(relation_kind(field))`, then the `forward_single` default to `select`. The three branches are exhaustively pinned by `test_plan_dispatches_forward_fk_to_select_related`, `test_plan_dispatches_reverse_fk_to_prefetch_related`, `test_plan_downgrades_select_related_when_target_has_custom_get_queryset`, and `test_plan_prefetches_many_side_with_custom_target_get_queryset` at `tests/optimizer/test_walker.py:119,127,814,877`.
- Hint integration is structurally clean: `hint_is_skip(hint)` from `hints.py:129-146` is the first dispatch (`walker.py:412`), followed by `prefetch_obj` (`walker.py:414`), `force_select` (`walker.py:427`), `force_prefetch` (`walker.py:455`). The priority order matches `OptimizerHint.__post_init__`'s documented order (`hints.py:76-77`), and `__post_init__` rejects conflicting flag combinations at construction time so the walker priority order is "documentation, not collision arbitration" (`walker.py:408-410`). The fifth no-op shape (`OptimizerHint()` with no flags) correctly falls through to the default cardinality dispatch, pinned by `test_plan_no_flag_hint_falls_through_to_default_dispatch` at `tests/optimizer/test_walker.py:1187`.
- The Relay custom-PK projection branch at `walker.py:166-206` is the single most-comment-anchored block in the file (40 lines of commentary explaining the `name` / `attname` mismatch on relation primary keys, the `id_attr == "pk"` resolution, and the `.only(attname)` discipline that prevents lazy loads on `resolve_id`). The block is pinned by `test_plan_relay_id_projects_real_pk_attname_when_not_id` (`tests/optimizer/test_walker.py:153`) and `test_plan_relay_id_projects_attname_when_pk_is_relation` (`test_walker.py:196`). The verification scan at `walker.py:190-195` correctly checks both `f.name == id_attr` AND `getattr(f, "attname", None) == id_attr` — the "naive `in field_map` check would skip projection on `OneToOneField(primary_key=True)` shapes" hazard is explicitly comment-documented at `walker.py:175-185`.
- `_can_elide_fk_id` at `walker.py:528-558` correctly guards against composite primary keys (Django 5.2+) at `walker.py:544-549` with a `# pragma: no cover` annotation explaining "Composite primary key (Django 5.2+). Test fixtures do not define one; the guard exists so the elision branch fails closed if a consumer adopts composite PKs." The "fail closed" discipline matches the `plans.py:_optimizer_can_absorb` "drop self rather than corrupt consumer" bias from the carry-forward in `rev-optimizer__plans.md`.
- The `cacheable=False` propagation discipline is structurally correct: `_plan_prefetch_relation` sets `cacheable=False` when target has `get_queryset` (`walker.py:326-327`); `_apply_hint`'s `prefetch_obj` branch sets it (`walker.py:421`, comment-anchored at `walker.py:416-420`); `_build_prefetch_child_queryset` propagates child plan's `cacheable=False` up (`walker.py:379-380`). All three sites are individually test-pinned (`test_plan_propagates_uncacheable_nested_custom_get_queryset`, `test_plan_prefetch_obj_hint_marks_plan_non_cacheable`, `test_plan_downgrades_select_related_when_target_has_custom_get_queryset`). The discipline matches the "consumer queryset closes over request- or user-scoped filters; the plan cache cannot serve one request's queryset to the next" invariant.
- Cache key relevance: `_build_cache_key` in `extension.py:697-755` derives the plan-cache key from the GraphQL operation AST + `@skip`/`@include` variables + target model + root response path + origin Strawberry type. Nothing the walker constructs (relation paths, runtime paths, resolver identities, `cacheable` flag) feeds into the cache key — those are stored on the resulting plan, not the key. The walker correctly stays out of cache-key construction. The `cacheable=False` flag is consulted by `extension.py` to decide whether to cache the plan, not whether to look it up.
- Static helper ran cleanly: three control-flow hotspots (`_walk_selections` 134 lines / 13 branches; `_apply_hint` 82 lines / 5 branches; `_merge_aliased_selections` 53 lines / 10 branches). All three are individually test-pinned across `tests/optimizer/test_walker.py`'s 1687-line surface (every branch of `_walk_selections` is exercised by at least one fixture, including the relay-pk custom-attname path at `walker.py:186-206`, the `force_select` / `force_prefetch` / `prefetch_obj` / `SKIP` hint paths, and the alias-merge + fragment-spread combinations). Repeated-literal report is minimal (3x `prefetch`, 3x `selections`, 2x each `related_model` / `target_field` / `directives` / `arguments`) — all natural and not duplication risks. No TODO comments.

### Summary

`walker.py` is the heaviest ORM module in the package (711 lines, three hotspots, dense Django/ORM marker table). The recursion correctness, the `select_related` vs `prefetch_related` choice rule (including the `get_queryset` downgrade), hint integration, resolver-key derivation, and cache-mutation invariants are all structurally clean and individually test-pinned across the 1687-line `tests/optimizer/test_walker.py` surface. Three Mediums: (1) `force_select` hint silently dispatches to `select_related` on many-side cardinalities and lets Django's `FieldError` surface deep in the resolver stack rather than raising a typed `ConfigurationError` with the field name at plan time; (2) `_apply_hint`'s docstring under-counts the documented hint shapes (the no-op-empty fifth shape is pinned by `test_plan_no_flag_hint_falls_through_to_default_dispatch` but not documented); (3) `_target_has_custom_get_queryset(target_type)` is called twice per prefetch dispatch — a minor DRY against the explicit-flag-threading idiom that `plans.py` and `_build_prefetch_child_queryset` already establish locally. Five Lows: the `runtime_prefixes=((),)` default is under-documented; the `_resolve_field_map` fallback's polymorphic-shape contract is under-documented (carry-forward from `rev-optimizer__field_meta.md`); the `_apply_hint` `force_select` / `force_prefetch` branches re-pass identical multi-arg sequences (folder-pass `RelationPlanCtx` evaluation); the `_ensure_connector_only_fields` debug-log fall-through is not test-covered and needs either a fixture or a `# pragma: no cover`; and `_merge_aliased_selections`'s "future slice" comment block should carry a TODO anchor if a slice is on the KANBAN, otherwise trim the forward-looking phrasing.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/optimizer/walker.py` — added M1 cardinality guard in `_apply_hint`'s `force_select` branch (lines 427-435 of the post-edit file): before the `_target_has_custom_get_queryset` downgrade check, classify `relation_kind(django_field)` and raise `ConfigurationError` with the field name and detected `kind` when `is_many_side_relation_kind(kind)` is true. Both helpers were already imported at `walker.py:14`. No other source edits.
- L4 (`_ensure_connector_only_fields` `logger.debug` pragma) was NOT applied. The artifact's L4 premise that "no fixture exercises the debug path" is contradicted by `tests/optimizer/test_walker.py:1312` (`test_ensure_connector_only_fields_logs_when_connector_unknown`) which constructs a stub `SimpleNamespace(one_to_many=True, many_to_many=False)` lacking `field.attname` and asserts the debug message. Marking it `# pragma: no cover` would (a) suppress a line the existing fixture already covers and (b) misdocument the branch as unreachable. Surfaced here for Worker 3; no in-cycle edit.

### Tests added or updated

- `tests/optimizer/test_walker.py::test_plan_force_select_hint_raises_for_many_side_relation` — pins M1. Registers `CategoryType` (no custom `get_queryset`) on `Category` with `optimizer_hints={"items": OptimizerHint.select_related()}` (reverse-FK many-side relation), runs `plan_optimizations([_sel("items", selections=[_sel("name")])], Category)`, and asserts the raised `ConfigurationError` matches `r"OptimizerHint\.select_related.*'items'"`. Placed immediately above `test_plan_no_flag_hint_falls_through_to_default_dispatch` per the artifact instruction. No DB seeding required — the cardinality guard fires at plan-time before any queryset is built; matches the pattern of the surrounding registry/type-construction hint tests.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged; only the COM812 / formatter compatibility warning).
- `uv run ruff check --fix .` — pass (All checks passed).
- `uv run pytest tests/optimizer/test_walker.py -k "force_select" -x` — 3 passed (`test_plan_force_select_hint_uses_select_recursion`, `test_plan_force_select_hint_downgrades_for_custom_target_get_queryset`, and the new `test_plan_force_select_hint_raises_for_many_side_relation`). The coverage gate fails at 40% as expected for a focused `-k` selection; the gate runs against the full suite in CI, not the focused subset.

### Notes for Worker 3

- M2 (docstring under-counts hint shapes), L1 (`runtime_prefixes=((),)` under-documented), L2 (`_resolve_field_map` polymorphic-shape docs), L5 (`_merge_aliased_selections` TODO anchor) — deferred to the comment pass per the dispatch instructions.
- M3 (`_target_has_custom_get_queryset` double-call) and L3 (`_apply_hint` 9-arg duplication) — deferred without in-cycle edit per the dispatch instructions; M3's own artifact text says "Below the bar to require a fix in this cycle", L3 routes to the folder pass.
- L4 (debug-log pragma) — NOT applied; the artifact's premise is wrong because `test_ensure_connector_only_fields_logs_when_connector_unknown` at `tests/optimizer/test_walker.py:1312` is the fixture that exercises that branch via a `SimpleNamespace(one_to_many=True, many_to_many=False)` stub. Adding `# pragma: no cover` would suppress a line that the existing fixture covers. Recommend the artifact be updated at comment pass to note that the debug-log branch IS test-pinned, not unreachable.
- No shadow file was used. The artifact's existing source-line citations were accurate enough to plan from directly.

---

## Verification (Worker 3)

### Logic verification outcome

- High: None — accepted.
- M1 (`force_select` many-side cardinality guard): cardinality guard applied at `walker.py:427-434` using `relation_kind(django_field)` + `is_many_side_relation_kind(kind)`. The raised `ConfigurationError` message includes the field name (`{django_name!r}`) and explicitly names `OptimizerHint.select_related()`. The guard is placed before the `_target_has_custom_get_queryset` downgrade check, so many-side relations short-circuit before the downgrade path; the existing downgrade test `test_plan_force_select_hint_downgrades_for_custom_target_get_queryset` (Item.category is a forward FK, single-side) is unaffected and still passes. New test `test_plan_force_select_hint_raises_for_many_side_relation` at `test_walker.py:1187` targets `Category.items` (reverse FK, many-side), asserts `ConfigurationError` with `match=r"OptimizerHint\.select_related.*'items'"`, follows the surrounding registry/hint test seeding pattern (no DB seeding required since the guard fires at plan time), and uses `registry.clear()` in a `try/finally`. `uv run pytest tests/optimizer/test_walker.py -k "force_select" -x` — 3 passed. **Accepted.**
- M2 (`_apply_hint` docstring under-counts hint shapes): deferred to comment pass — accepted.
- M3 (`_target_has_custom_get_queryset` double-call): deferred (no in-cycle edit per artifact "Below the bar to require a fix in this cycle") — accepted.
- L1 (`runtime_prefixes=((),)` under-documented): deferred to comment pass — accepted.
- L2 (`_resolve_field_map` polymorphic-shape docs): deferred to comment pass — accepted.
- L3 (`_apply_hint` 9-arg duplication / `RelationPlanCtx`): deferred to folder pass per artifact — accepted.
- L4 (`_ensure_connector_only_fields` debug-log pragma): **rejected as a finding.** Worker 2's claim verified: `test_ensure_connector_only_fields_logs_when_connector_unknown` at `test_walker.py:1339-1354` exercises the debug-log fall-through directly by constructing `SimpleNamespace(name="generic", one_to_many=True, many_to_many=False)` (no `field.attname` / `target_field` / `reverse_connector_attname` chain), setting caplog to DEBUG, calling `_ensure_connector_only_fields`, and asserting `"could not resolve connector column"` appears in the captured records. The artifact's premise that "no fixture in tests/optimizer/ constructs such a shape" is false. Adding `# pragma: no cover` would have suppressed a covered line. The original Low item is invalid; the artifact's L4 disposition is updated accordingly. **Accepted.**
- L5 (`_merge_aliased_selections` TODO anchor): deferred to comment pass — accepted.

### DRY findings disposition

Walker reuses canonical helpers (`relation_kind`, `is_many_side_relation_kind`, `hint_is_skip`, `append_unique`, `append_prefetch_unique`, `append_unique_many`, `runtime_path_from_info`, `resolver_key`, `snake_case`, `ConfigurationError`); the M1 logic-pass change uses the existing `relation_kind` + `is_many_side_relation_kind` + `ConfigurationError` helpers rather than re-implementing cardinality classification or defining a new exception type. Accepted.

### Temp test verification

None used; permanent test added directly under `tests/optimizer/test_walker.py::test_plan_force_select_hint_raises_for_many_side_relation`.

### Verification outcome

logic accepted; awaiting comment pass

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/optimizer/walker.py` — four docstring/comment edits:
  - **M2 docstring fix (lines 402-412 post-edit)**: `_apply_hint` docstring now reads "Dispatches the four configurable hint shapes (`SKIP`, `prefetch_obj`, `force_select`, `force_prefetch`) plus the no-op empty form. Returns `True` when one of the configurable shapes is matched. Returns `False` for an `OptimizerHint()` with no flag set — the caller falls back to the default cardinality dispatch in that case." Preserves the existing `__post_init__` priority-order-is-documentation sentence.
  - **L1 prefix-default comment (lines 160-164 post-edit)**: appended a paragraph to `_walk_selections`'s docstring noting that the default `runtime_prefixes=((),)` encodes "one empty-path prefix" for direct/test-only callers without `info`; `plan_optimizations` always passes an explicit single-tuple via `runtime_path_from_info(info)`.
  - **L2 polymorphic-shape doc (lines 105-110 post-edit)**: appended a paragraph to `_resolve_field_map`'s docstring describing the fallback path (no `DjangoType` registered) returning raw Django field objects keyed by name, and the consumer contract (`getattr(..., default)` reads make both `FieldMeta` and raw Django field shapes satisfy the contract; treat values as `FieldMeta | Any` until the registry-coverage gate lands).
  - **L5 trim forward-looking phrasing (lines 678-682 post-edit, option 2)**: replaced the six-line comment block with a four-line block: "Today's walker ignores `arguments`, so divergent arguments between aliased selections are harmless. If a future slice plans per-argument, this merge must become per-response-key instead of merging." Dropped the "fast trace without changing current behaviour" sentence (the debug log itself is self-explanatory).

### L5 choice rationale

Chose **option 2 (trim)**. KANBAN check: `grep -ni -E "per-argument|per-arg|argument set|per_argument|response-key planning|per-response-key" KANBAN.md` returned no matches. The closest references (`grep -ni "argument" KANBAN.md`) are GraphQL argument factories for the filter / order / aggregate subsystems (TODO-ALPHA-020/021, KANBAN.md:285,377,882), which do not describe per-argument optimizer planning. No active per-argument planning slice exists, so option 1's TODO anchor would point at nothing actionable. Per the artifact's "Option 1 if a slice is on the KANBAN, option 2 if not" rule, option 2 is correct.

### Deferred findings re-affirmed

- **M3** (`_target_has_custom_get_queryset` double call): deferred without in-cycle edit per the artifact text ("Below the bar to require a fix in this cycle"). Worth a note for the next pass that touches `plan_relation`'s signature.
- **L3** (`_apply_hint` 9-arg duplication / `RelationPlanCtx`): deferred to folder pass per artifact.
- **L4** (`_ensure_connector_only_fields` debug-log pragma): false premise; rejected at logic-pass verification. No comment-pass edit needed; the existing test `test_ensure_connector_only_fields_logs_when_connector_unknown` at `tests/optimizer/test_walker.py:1339-1354` exercises the branch.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged; only the standard COM812 / formatter compatibility warning).
- `uv run ruff check --fix .` — pass (All checks passed).

### Notes for Worker 3

- All four edits are docstring/comment-only; no logic changes in this pass.
- L5's option-2 choice is anchored by the KANBAN grep above; if a per-argument planning slice lands later, a future cycle should re-anchor the comment with a TODO referencing the new spec.

---

## Changelog disposition

### Disposition: warranted but deferred to maintainer

**Reason**: M1 (logic-pass change) converts the runtime failure mode of `OptimizerHint.select_related()` on many-side relations (reverse FK, M2M) from Django's opaque `FieldError` surfacing deep in the resolver stack at query time into a typed `ConfigurationError` with the field name at plan time. This is a typed-error contract change on a consumer-facing API surface (`OptimizerHint.select_related()`) — misconfigured hints used to fail loud and opaque; they now fail loud and typed. Worth a `### Changed` entry on a stable release.

The contract change is in the error type only; consumer code that previously caught the opaque `FieldError` and either expected a specific message or fell through to a generic handler would need to catch `ConfigurationError` instead. In practice misconfigured hints are programmer errors that should fail loud — no production consumer is realistically catching `FieldError` from `select_related` on a reverse FK — so the practical migration cost is zero, but the disposition is still recorded as "warranted" because the typed error is a contract.

M2 / L1 / L2 / L5 are docstring or comment polish only and do not alter consumer-visible behavior; they do not justify a changelog entry on their own.

### Suggested entry text

> `DjangoOptimizerExtension`: `OptimizerHint.select_related()` on many-side relations (reverse FK, M2M) now raises `ConfigurationError` at plan time with the field name in the message, replacing the previous opaque Django `FieldError` at query time.

Place under `### Changed` (or `### Fixed` at maintainer discretion) in the `[0.0.6]` block of `CHANGELOG.md`.

### What was done

No edit to `CHANGELOG.md`. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed.") and the active plan's silence on changelog authorization for this cycle item, the disposition is recorded here for the maintainer to lift verbatim at release time. The audit trail (warranted + suggested wording) is preserved in this artifact.

### Validation run

- `uv run ruff format .` — pass (no changes).
- `uv run ruff check --fix .` — pass (All checks passed).

---

## Iteration log

- 2026-05-19 — comment + changelog pass complete. Four docstring/comment edits landed (M2, L1, L2, L5). L5 chose option 2 (trim phrasing) after KANBAN check found no active per-argument planning slice. M3, L3 re-affirmed as deferred per artifact disposition. L4 false-premise rejection re-affirmed. Changelog disposition: warranted (M1's typed-error contract change) but deferred to maintainer; suggested entry text recorded. Both ruff commands pass.

## Verification (Worker 3, pass 2)

- **Comment verification outcome:** Four docstring/comment edits accepted. M2 — `_apply_hint` docstring at `walker.py:414-423` now names the four configurable shapes plus the no-op empty form, matching the test surface (`test_plan_no_flag_hint_falls_through_to_default_dispatch`). L1 — `_walk_selections`'s docstring at `walker.py:167-170` explains the `((),)` default as "one empty-path prefix" and notes the explicit single-tuple shape `plan_optimizations` always passes. L2 — `_resolve_field_map`'s docstring at `walker.py:104-109` describes the polymorphic FieldMeta-vs-raw-Django-field shape under the fallback path and the `getattr(..., default)` consumer contract. L5 — comment block at `walker.py:687-690` trimmed to drop the "future slice" / "fast trace" phrasing; option 2 (trim) is the correct variant because the KANBAN check (`grep -ni -E "per-argument|per-arg|argument set|per_argument|response-key planning|per-response-key" KANBAN.md`) returned zero matches, so an option-1 TODO anchor would have pointed at nothing actionable. All four edits describe final approved behavior, do not restate obvious code, and stay within the reviewed scope.
- **Changelog verification outcome:** Warranted-but-deferred is the right disposition. M1's logic-pass change converts an opaque Django `FieldError` at query time into a typed `ConfigurationError` at plan time naming the offending field — a consumer-visible typed-error contract change on a public hint API (`OptimizerHint.select_related()`). Disposition cites both the `AGENTS.md` ban ("Do not update CHANGELOG.md unless explicitly instructed.") and the active plan's silence on changelog authorization. Suggested entry text is recorded verbatim for the maintainer to lift at release time. `git diff -- CHANGELOG.md` confirmed empty. Accepted.
- **Verification outcome:** cycle accepted; verified.
