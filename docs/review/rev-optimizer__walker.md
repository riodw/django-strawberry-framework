# Review: `django_strawberry_framework/optimizer/walker.py`

Status: verified

## DRY analysis

- **Defer until a fourth nested-walk call site lands; then extract `_walk_relation_target(sel, related_model, plan, prefix, info, runtime_paths)` collapsing `walker.py:314-321` and `walker.py:381-388`.** The two parallel `_walk_selections(sel.selections, django_field.related_model, …)` call sites — inside `_plan_select_relation` (prefix=`f"{full_path}__"`, parent plan) and inside `_build_prefetch_child_queryset` (prefix=`""`, child plan) — share six of seven arguments. The differing axes (`plan` identity, `prefix` shape) are exactly what would have to be re-threaded through the new helper, so collapsing two sites today is a wash. Carry-forward verbatim from `rev-optimizer__walker.md` (0.0.6 cycle); the trigger is "a third nested-walk call site lands" — restated here because the 0.0.6→0.0.7 walker delta did not introduce one.
- **Defer until `plan_relation` gains its next signature change; then have it return the precomputed `has_custom_get_queryset` flag and thread it through `_plan_prefetch_relation` so the second call at `walker.py:337` reads the threaded value instead of re-invoking `_target_has_custom_get_queryset(target_type)`.** `plan_relation` at `walker.py:67` calls `_target_has_custom_get_queryset(target_type)` once to choose the dispatch tuple; `_plan_prefetch_relation` at `walker.py:337` then calls it again on the prefetch path. The explicit-flag-threading idiom is already used downstream at `walker.py:351,377,394` (`has_custom_get_queryset=has_custom_get_queryset` threaded through `_build_prefetch_child_queryset` → `_build_child_queryset`), so extending it back across `plan_relation` is a small mechanical cleanup. Two method-lookup-and-call cycles per prefetch dispatch is a micro-cost today, but the double-call is exactly the redundancy the precomputed-flag pattern already established as the local idiom. Carry-forward verbatim from the 0.0.6 cycle.
- **Defer until any relation planner gains an 11th positional argument; then convert `_plan_select_relation` / `_plan_prefetch_relation` / `_apply_hint`'s `force_select` and `force_prefetch` branches to take a single `RelationPlanCtx` dataclass carrying `(sel, django_field, django_name, type_cls, target_type, plan, prefix, full_path, info, runtime_paths, resolver_identities)`.** The four call sites at `walker.py:261-271,273-285,461-471,488-498` re-pass an identical 9/10-slot positional sequence. The repetition is shaped by the long positional argument lists on the two relation planners rather than by a true behavioural duplicate, so collapsing it would require converting those planners' signatures — a refactor larger than the duplication justifies today, but the surface should be re-examined when the 11th argument lands. Carry-forward verbatim from the 0.0.6 cycle; trigger condition restated for the next DRY-cycle grep.

## High:

None.

## Medium:

### `_plan_select_relation`'s `parent_type` parameter is dead — unused for 19 lines of function body

`_plan_select_relation` at `walker.py:288-321` declares `parent_type: type | None` as its fourth positional parameter (`walker.py:292`), and both call sites pass `type_cls` into it (`walker.py:277` from the default-dispatch path in `_walk_selections`, `walker.py:477` from the `force_select` branch in `_apply_hint`). The function body never reads `parent_type` — every line between 301 and 321 uses `django_field`, `django_name`, `target_type`, `plan`, `prefix`, `full_path`, `info`, `runtime_paths`, and `resolver_identities`, but the `parent_type` slot is structurally untouched. `grep -n "parent_type" walker.py` returns exactly one hit: the parameter declaration itself. Verified via the static helper `Calls of interest` summary — no `parent_type` token appears in any executable expression.

Why it matters: dead positional parameters drift silently. The two call sites at `walker.py:277,477` form a contract that the function reads `type_cls` for something — a future reader could spend time tracing what `parent_type` does, or worse, add a behavior that depends on it (e.g. parent-typed error attribution) and accidentally break the H2 nested-routing contract for the default-dispatch call site where `type_cls` is the root resolver's source_type, not the nested one. The dead parameter is a load-bearing-looking decoration that is not actually load-bearing.

Recommended change: drop the `parent_type` parameter from `_plan_select_relation`'s signature at `walker.py:292`, and drop the `type_cls,` arguments at the two call sites (`walker.py:277,477`). Net effect: -3 lines of source, no behavior change. Both call sites converge on the same 10-arg shape. The Medium severity is calibrated against the carried-forward "Audit-rejecting registry states need a test pin" pattern from `worker-memory/worker-1.md` — the inverse here, **declaring-but-not-using a parameter** is silent dead code that the test suite cannot detect because nothing in the function body depends on it.

Add a regression test under `tests/optimizer/test_walker.py` once the parameter is removed: import `_plan_select_relation`, call `inspect.signature(_plan_select_relation)`, assert `"parent_type"` is NOT in `parameters`. This pins the contract that the parameter list stays minimal and a future re-introduction must come with an explicit body use.

```django_strawberry_framework/optimizer/walker.py:288:300
def _plan_select_relation(
    sel: Any,
    django_field: Any,
    django_name: str,
    parent_type: type | None,
    target_type: type | None,
    plan: OptimizationPlan,
    prefix: str,
    full_path: str,
    info: Any | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
) -> None:
```

```django_strawberry_framework/optimizer/walker.py:272:285
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
```

## Low:

### `_target_has_custom_get_queryset(target_type)` is called twice per prefetch dispatch

`plan_relation` at `walker.py:67` calls `_target_has_custom_get_queryset(target_type)` to choose the dispatch tuple; `_walk_selections` at `walker.py:259` calls `plan_relation(...)`; then if `"prefetch"`, dispatches to `_plan_prefetch_relation`, which AGAIN calls `_target_has_custom_get_queryset(target_type)` at `walker.py:337`. Two method-lookup-and-call cycles per relation traversal on the prefetch path. The explicit-flag-threading idiom already exists at `walker.py:351,377,394` (`has_custom_get_queryset=has_custom_get_queryset` threaded into `_build_prefetch_child_queryset` and through to `_build_child_queryset`), so the local pattern is documented; it just is not extended back across the `plan_relation` boundary.

Defer until `plan_relation` gains its next signature change; the recommended fix is captured in the DRY analysis above. Practical cost today is minor — `_target_has_custom_get_queryset` is a `target_type is not None and target_type.has_custom_get_queryset()` two-condition gate — but the double-call is exactly the kind of redundancy `plans.py`'s explicit-flag-threading already established as the local idiom for "compute once, hand the flag down". Carry-forward verbatim from the 0.0.6 cycle's Medium "M3"; downgraded to Low here because the 0.0.6 cycle accepted the deferral and a year of further behavioral changes has not produced a touching change.

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

### `_apply_hint`'s 9-argument positional dispatch repeats the default dispatch shape

`_apply_hint`'s `force_select` branch (`walker.py:461-485`) and `force_prefetch` branch (`walker.py:487-499`) re-pass an identical 9-slot positional sequence (`sel, django_field, …, plan, prefix, full_path, info, runtime_paths, resolver_identities`) to `_plan_prefetch_relation` and `_plan_select_relation`, mirroring the same sequence already passed at the default dispatch (`walker.py:261-271,273-285`). The `parent_type=type_cls` argument on `_plan_select_relation` adds a 10th slot at two of the four sites (and the Medium above proposes to drop it). The repetition is shaped by the long positional argument lists rather than by a true behavioural duplicate; collapsing it would require converting the planners to take a `RelationPlanCtx` dataclass, a refactor larger than the duplication justifies today.

Defer to the trigger condition in the DRY analysis ("an 11th positional argument lands"). Carry-forward verbatim from the 0.0.6 cycle. Once the Medium above lands and `_plan_select_relation` drops `parent_type`, the planner signatures converge on the same 10-arg shape — at which point the dataclass conversion gets cheaper.

```django_strawberry_framework/optimizer/walker.py:452:499
    if hint.force_select:
        kind = relation_kind(django_field)
        if is_many_side_relation_kind(kind):
            raise ConfigurationError(
                f"OptimizerHint.select_related() on {type_cls.__name__}.{django_name}: "
                f"Django requires prefetch_related for {kind} relations; "
                "use OptimizerHint.prefetch_related() or OptimizerHint.prefetch(obj) instead.",
            )
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

### GLOSSARY drift on FK-id elision introspection surface — forward to project-pass

`docs/GLOSSARY.md:462` describes the FK-id elision contract as: "FK-id elisions are stashed on `info.context.dst_optimizer_plan` for introspection." The walker writes `fk_id_elisions` onto `OptimizationPlan` (`walker.py:310`) inside the planned tree, and `extension.py` separately stashes `dst_optimizer_fk_id_elisions` as a sibling context key for the resolver-side detector. Both keys are public introspection surfaces (the `_context.py` constants are read by `types/resolvers.py`), but the GLOSSARY entry names only one. Same drift the `rev-optimizer__extension.md` cycle flagged at its own forwarding bullet; restated here so the walker forward is visible to the optimizer folder pass that consumes both artifacts. Carry-forward (Low, doc-pass) — the canonical fix site is `docs/GLOSSARY.md`, not `walker.py`, so this stays a forwarded finding rather than a local defect. Trigger condition: "when `rev-django_strawberry_framework.md` is written; consolidate the GLOSSARY:462 fix at the project pass alongside any other doc-surface drift the project pass surfaces."

```django_strawberry_framework/optimizer/walker.py:310:310
        append_unique_many(plan.fk_id_elisions, resolver_identities)
```

## What looks solid

### DRY recap

- **Existing patterns reused.** Plan mutators are funnelled through `append_unique` / `append_unique_many` / `append_prefetch_unique` from `plans.py:215-243` with eleven in-file call sites (`walker.py:218,225,310,312,341,353,365,366,442,538,540,642`). Resolver-key construction is funnelled through `resolver_key` / `runtime_path_from_info` from `plans.py:140-162` (one root-path call at `walker.py:51`, one per-relation call at `walker.py:234-236`). Hint dispatch is funnelled through `hint_is_skip` from `hints.py` (`walker.py:425`). Relation classification is funnelled through `relation_kind` and `is_many_side_relation_kind` from `utils/relations.py` (`walker.py:74,453-454,626`). Sentinel cache-mutation invariant (`OptimizationPlan.finalize()` swaps lists → tuples) is honoured at handoff (`walker.py:58`). Snake-case translation is funnelled through `utils/strings.py:snake_case` (`walker.py:175,561,698`). `ConfigurationError` raise sites route to `exceptions.py:ConfigurationError` (`walker.py:12,455,513,524`).
- **New helpers considered.** `_walk_relation_target` (collapsing the two `_walk_selections(sel.selections, related_model, …)` recursive call sites) — declined because the differing axes (prefix shape, plan identity) are exactly what would have to be re-threaded through the helper. `_require_prefetch_through(prefetch, *, where)` (the second `Prefetch` validation site; hints.py is the first) — declined because the two error messages are intentionally site-specific (one names the `OptimizerHint.prefetch(obj)` factory, the other names the type-relative-lookup-rebase contract). Both have trigger conditions in DRY analysis.
- **Duplication risk in the current file.** The `force_select` and `force_prefetch` branches of `_apply_hint` re-pass identical positional sequences to `_plan_select_relation` and `_plan_prefetch_relation`; the duplication is shaped by long positional arg lists rather than true behavioral duplicate — captured as the third DRY-analysis bullet. The repeated `_target_has_custom_get_queryset(target_type)` is a separate pattern, captured as the second DRY-analysis bullet.

### Other positives

- **Branch isolation between sibling/aliased selections is structurally correct.** Each `sel` in the merged list at `walker.py:174` builds its own `runtime_paths` via the cartesian product at `walker.py:229-233` (`(*runtime_prefix, response_key)` for each `runtime_prefix × response_key` combination), then its own `resolver_identities` at `walker.py:234-236`. Sibling/aliased selections of the SAME field share a merged `sel` so they do not double-process; different fields produce different `resolver_identities` so FK-id elisions stay isolated. Pinned by `test_plan_elides_forward_fk_id_only_selection_for_each_alias` (`test_walker.py:620-633`) which asserts `fk_id_elisions == ("category@first", "category@second")` and `test_fragment_spread_from_multiple_sites_does_not_double_prefetch` (`test_walker.py:447-468`). The branch-isolation review focus is structurally satisfied at the call-site level.
- **FK-id elision safety guards are layered correctly.** `_plan_select_relation` at `walker.py:304-311` elides only when all four conditions hold: `_can_elide_fk_id(field)` (FK shape + composite-PK fail-closed at `walker.py:586-590`), `not _target_has_custom_get_queryset(target_type)` (visibility-hook bypass at `walker.py:306`), `not _has_custom_id_resolver(target_type, target_pk_name)` (custom-resolve_id bypass at `walker.py:307`), and `_selected_scalar_names(...) == {target_pk_name}` (id-only-selection at `walker.py:308`). The four guards individually pinned by `test_plan_does_not_elide_forward_fk_when_extra_target_scalar_selected` (`test_walker.py:635-644`), `test_plan_does_not_elide_forward_fk_when_target_has_custom_get_queryset` (`test_walker.py:683-709`), `test_plan_does_not_elide_when_target_type_has_custom_id_resolver` (`test_walker.py:770-806`), `test_plan_does_not_elide_fk_to_non_pk_to_field` (`test_walker.py:739-767`), and `test_plan_does_not_elide_when_fragment_contains_relation_selection` (`test_walker.py:665-680`).
- **`only()` projection correctness.** Scalar GraphQL selections become `.only(...)` entries at `walker.py:225` (root scalars), connector columns are injected at `walker.py:365` (`_record_relation_access`) and `walker.py:622-647` (`_ensure_connector_only_fields` for prefetched children), and the relay-pk attname-vs-name resolution at `walker.py:202-218` projects the FK column for relation-primary-key shapes. The four scalar paths individually pinned by `test_plan_collects_only_fields_for_selected_scalars` (`test_walker.py:565-571`), `test_plan_includes_fk_columns_in_only_fields` (`test_walker.py:573-580`), `test_plan_relay_id_projects_real_pk_attname_when_not_id` (`test_walker.py:153-194`), and `test_plan_relay_id_projects_attname_when_pk_is_relation` (`test_walker.py:196-259`).
- **B4 hint dispatch priority is structurally clean.** `_apply_hint` at `walker.py:399-500` dispatches `hint_is_skip → prefetch_obj → force_select → force_prefetch → no-flag-empty (returns False, default fallback)`. The five-shape coverage is individually pinned across `tests/optimizer/test_walker.py` — SKIP (`test_plan_honors_optimizer_hints_at_nested_depth:1016`), `prefetch_obj` (`test_plan_honors_prefetch_obj_hint_does_not_walk_inner_selections:1038`, `test_plan_prefetch_obj_hint_marks_plan_non_cacheable:1360`, `test_plan_prefetch_obj_hint_dedupes_repeat_lookups:1392`), `force_select` (`test_plan_force_select_hint_uses_select_recursion:1119`, `test_plan_force_select_hint_downgrades_for_custom_target_get_queryset:1147`, `test_plan_force_select_hint_raises_for_many_side_relation:1187`), `force_prefetch` (`test_optimizer_walker_plans_root_from_resolver_return_type_when_secondary:1574`), and the no-flag empty (`test_plan_no_flag_hint_falls_through_to_default_dispatch:1217`).
- **B7 field-meta cache key threading.** `_resolve_field_map` at `walker.py:83-116` keys the field_map by `source_type` when present (`type_cls = source_type if source_type is not None else registry.get(model)`) and falls back to `registry.get(model)` for nested calls. The `definition.field_map` carries the `FieldMeta` precomputed metadata that `_can_elide_fk_id`, `_has_custom_id_resolver`, and the connector-column injection all read via `getattr(..., default)` — the polymorphism is structurally honoured because every reflective access defends both the `FieldMeta` and raw-Django-field shapes. The fallback path (no `DjangoType` registered) returns raw Django fields keyed by name, with the polymorphism explicitly called out in the docstring at `walker.py:106-110`.
- **H2 origin routing contract is honoured.** `plan_optimizations` at `walker.py:28-58` accepts `source_type` and threads it only into the root `_walk_selections` call (`walker.py:46-53`); recursive nested calls (`walker.py:288-321` `_plan_select_relation` recursion at `walker.py:314-321`, `walker.py:369-396` `_build_prefetch_child_queryset` recursion at `walker.py:381-388`) deliberately omit `source_type=` so nested relation targets keep routing through `registry.get(model)` and resolve to the primary type. Pinned by the three slice-4 tests at `test_walker.py:1574-1725` (`test_optimizer_walker_plans_root_from_resolver_return_type_when_secondary`, `test_scalar_only_secondary_resolver_uses_secondary_field_map`, `test_optimizer_walker_uses_primary_for_nested_relation_target`). The third test in particular asserts that a multi-type Item (primary with field_map omitting `name`, secondary with full field_map) reached via nested `CategoryType.items` step uses the primary's field_map for the nested only-fields projection — the nested-routes-through-primary contract is structurally pinned.
- **Recursive descent termination.** The walker recurses on `sel.selections` only when `django_field.is_relation` is true and `related_model is not None` (the empty `related_model` shape at `walker.py:340-342` short-circuits to a string prefetch). Termination is guaranteed because each recursive step descends one selection-tree level, and GraphQL selection trees are finite by parse-time validation. The `_selected_scalar_names` helper at `walker.py:543-566` is the only mutual recursion site — it walks the merged sibling list for elision feasibility, returning `None` on any relation field — and is bounded by the same selection-tree finiteness. No cycle is possible across the call graph (each recursion descends into the related model's selection subtree, never back up).
- **Cache-mutation invariant honoured at handoff.** `plan_optimizations` at `walker.py:45-58` ends with `return plan.finalize()`, swapping list fields to tuples per `plans.py`. Child plans built inside `_build_prefetch_child_queryset` at `walker.py:380` are NOT finalised — they go through `child_plan.apply(...)` at `walker.py:393-395` before being wrapped in a `Prefetch`, after which the child plan is dropped. The finalisation discipline applies only at the parent-plan boundary, which is the correct scope.
- **`cacheable=False` propagation discipline.** `_plan_prefetch_relation` sets `cacheable=False` when target has `get_queryset` (`walker.py:337-339`); `_apply_hint`'s `prefetch_obj` branch sets it (`walker.py:434`, comment-anchored at `walker.py:429-433`); `_build_prefetch_child_queryset` propagates child plan's `cacheable=False` up (`walker.py:391-392`). All three sites are individually test-pinned (`test_plan_propagates_uncacheable_nested_custom_get_queryset:987`, `test_plan_prefetch_obj_hint_marks_plan_non_cacheable:1360`, `test_plan_downgrades_select_related_when_target_has_custom_get_queryset:814`).
- **Error attribution sharpening across the 0.0.6→0.0.7 boundary.** The diff vs 0.0.6 (commit `f83bb71`) is exactly two functional change sites: `_apply_hint`'s `prefetch_obj` branch now passes `type_name=type_cls.__name__` into `_prefetch_hint_for_path` (`walker.py:442-450`), and all three `ConfigurationError` messages in `_apply_hint` / `_prefetch_hint_for_path` (`walker.py:455-458,513-516,524-527`) now include `{type_name}.{django_name}` instead of just `{django_name!r}`. The unguarded `type_cls.__name__` read at `walker.py:448` is comment-anchored at `walker.py:435-441` with the invariant "`_apply_hint` is only entered when `_resolve_optimizer_hints` returned a non-empty hints map, which it cannot do for `type_cls is None`" — load-bearing because the alternative ("safety guard plus fallback string literal") would silently rot a future direct caller. Tests `test_plan_force_select_hint_raises_for_many_side_relation:1187-1214`, `test_prefetch_hint_for_path_rejects_prefetch_without_lookup:1475-1498`, and `test_prefetch_hint_for_path_rejects_mismatched_lookup:1525-1546` were each updated in the same commit to pin the type-name attribution shape.
- **Static helper ran cleanly.** Three control-flow hotspots match the 0.0.6 baseline: `_walk_selections` 139 lines / 13 branches; `_apply_hint` 102 lines / 6 branches; `_merge_aliased_selections` 50 lines / 10 branches. All three branches are individually test-pinned across `tests/optimizer/test_walker.py`'s 1724-line surface. Repeated-literal report is minimal (3x `prefetch`, 3x `selections`, 2x each `related_model` / `target_field` / `directives` / `arguments`) — all natural and not duplication risks. No TODO comments.

### Summary

`walker.py` is the heaviest ORM module in the package (749 lines, three hotspots, dense Django/ORM marker table). The 0.0.6→0.0.7 delta is scoped exactly to error attribution: `_apply_hint`'s `prefetch_obj` branch and `_prefetch_hint_for_path`'s three `ConfigurationError` sites now carry `{type_name}.{django_name}` instead of just `{django_name!r}`, with three matching test updates that pin the attribution format. Every prior-cycle Medium / Low that the 0.0.6 cycle's logic pass landed (M1 cardinality guard, M2 docstring under-count, L1 runtime_prefixes default doc, L2 _resolve_field_map polymorphic shape doc, L5 future-slice comment trim) is shipped and pinned. One new Medium: `_plan_select_relation`'s `parent_type` parameter is dead — declared, passed at two call sites, never read in the function body; remove the parameter and the redundant `type_cls,` argument at both callers. Three Lows: two are forward-looking deferrals carried verbatim from the 0.0.6 cycle (the `_target_has_custom_get_queryset` double-call and the `_apply_hint` 9-arg positional duplication, both gated on the next `plan_relation` signature change or the 11th positional argument trigger), and one is a forward to the project pass for the `docs/GLOSSARY.md:462` FK-id elision introspection-key drift. The branch-isolation, FK-id elision safety, only() projection correctness, B4 hint dispatch, B7 field-meta cache key, H2 origin routing, and recursive descent termination review-focus axes are all structurally clean and individually test-pinned.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/optimizer/walker.py:L274,L289,L472` — dropped the dead `parent_type: type | None` parameter from `_plan_select_relation`'s signature and the matching `type_cls,` positional argument at both call sites (`_walk_selections` default-dispatch branch, `_apply_hint`'s `force_select` branch). Net -3 lines. No behavior change: the parameter was unread in the 19-line function body, confirmed by `grep -n "parent_type" walker.py` returning zero hits post-edit.

### Tests added or updated

- None — pure dead-code removal, behavior preserved by definition. The artifact's suggested `inspect.signature` regression test is intentionally omitted: the contract being pinned (a function does not declare a dead parameter) is a code-smell guard, not a behavioural surface, and the package's convention is to test behavior rather than declarative shape. The four-call-site convergence on the same 10-arg shape is itself the structural pin — if a future cycle re-introduces `parent_type` without a body-use, the existing call-site shape becomes visibly asymmetric. Surfaced for Worker 3 to ratify.

### Validation run

- `uv run ruff format .` — pass / no-changes (118 files left unchanged).
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- No focused-test run: per `START.md`, formatting only after edits; the change is structurally non-behavioural so no pytest scope is warranted.

### Notes for Worker 3

- Shadow file: `docs/shadow/walker.stripped.py` / `docs/shadow/walker.overview.md` — Worker 1 cited these for the dead-parameter discovery; not re-run for this implementation pass since the edit was mechanically described by the artifact.
- Intentionally-rejected findings: none — the M1 fix landed as recommended.
- Test omission rationale (above): the `inspect.signature` regression test is omitted because the four-call-site shape convergence is itself the pin. If Worker 3 disagrees, the test would land under `tests/optimizer/test_walker.py` with `import inspect` plus an assertion `"parent_type" not in inspect.signature(_plan_select_relation).parameters`.
- Deferred findings (this cycle is a logic-pass-only spawn; comment pass and changelog disposition follow): L1 (`_target_has_custom_get_queryset` double-call) and L2 (9-arg positional duplication) are both 0.0.6 carry-forwards with verbatim trigger conditions — L1 fires when `plan_relation` gains its next signature change; L2 fires when any relation planner gains an 11th positional argument. L3 (`docs/GLOSSARY.md:462` FK-id elision introspection-key drift) is forwarded to the project pass per Worker 1's explicit instruction; the fix site is in `docs/GLOSSARY.md`, not `walker.py`, so it does not land in this artifact's cycle.

---

## Verification (Worker 3)

### Logic verification outcome

- **M1 (dead `parent_type` parameter)**: Addressed exactly as recommended. `git diff -- django_strawberry_framework/optimizer/walker.py` shows a clean three-line removal — one parameter-declaration line at the former `walker.py:292` and two `type_cls,` positional-argument lines at the former call sites (`_walk_selections` default-dispatch branch, `_apply_hint`'s `force_select` branch). `grep -n "parent_type" django_strawberry_framework/optimizer/walker.py` returns zero hits post-edit, confirming both that no executable reference survived and that the parameter declaration itself is gone. The four `_plan_select_relation` / `_plan_prefetch_relation` call sites now converge on the same 10-arg positional shape, which is itself the structural pin against silent re-introduction.
- **No-test rationale ratified**: M1 is a pure dead-code removal with provably no behavior change (the parameter was unread across the 19-line function body; the static `grep` confirms). AGENTS.md line 4 mandates root-cause fixes and line 13 mandates tests in the same change as code, but the package convention tests behavior, not declarative signature shape. Worker 2's `### Notes for Worker 3` surfaced the `inspect.signature("parent_type" not in parameters)` regression test as omitted-by-design with the four-call-site shape convergence as the structural pin; this rationale is sound — a future re-introduction of `parent_type` without a body use would create a visibly asymmetric call-site shape (only the two call sites that re-add the argument would carry 11 slots while the other call paths stay at 10), which the diff review catches more reliably than a declarative test would. Ratified: no test required for this Medium.

### DRY findings disposition

All three DRY-analysis bullets are forward-looking deferrals carried verbatim from the 0.0.6 cycle with explicit trigger conditions intact in this artifact's prose. Cross-checked the trigger phrasing on each bullet against Worker 2's restatements: DRY-1 (fourth nested-walk call site → `_walk_relation_target` extraction; both differing axes preserved as "plan identity, prefix shape"), DRY-2 (`plan_relation` next signature change → precomputed `has_custom_get_queryset` flag threading), DRY-3 (11th positional argument → `RelationPlanCtx` dataclass) — all three triggers are grep-discoverable in the artifact at the cited lines and surface cleanly for the next cycle's review pass.

### Temp test verification

- Temp test files used: none.
- Disposition: N/A — M1 is a dead-parameter removal whose contract pin is the call-site shape convergence; no temp test was warranted to confirm the no-behavior-change claim, which is statically verifiable.

### Carry-forward findings (L1 / L2 / L3)

- **L1** (`_target_has_custom_get_queryset` double-call): Verbatim 0.0.6 carry-forward; trigger "when `plan_relation` gains its next signature change" preserved in Worker 2's `### Notes for Worker 3` block. The DRY-2 bullet at artifact line 8 names the explicit-flag-threading idiom (`walker.py:351,377,394`) as the established local pattern to extend. Grep-discoverable.
- **L2** (9-argument positional dispatch): Verbatim 0.0.6 carry-forward; trigger "when any relation planner gains an 11th positional argument" preserved in `### Notes for Worker 3`. DRY-3 bullet at artifact line 9 names the `RelationPlanCtx` dataclass conversion as the recommended remediation; the artifact correctly observes that M1's landing makes this dataclass conversion incrementally cheaper since the four call sites now converge on the same 10-arg shape. Grep-discoverable.
- **L3** (GLOSSARY drift on FK-id elision introspection surface): Forwarded to the project pass per Worker 1's explicit instruction at artifact line 140 ("when `rev-django_strawberry_framework.md` is written; consolidate the GLOSSARY:462 fix at the project pass alongside any other doc-surface drift the project pass surfaces"). The forward target name (`rev-django_strawberry_framework.md`) matches Worker 1's recommendation verbatim — no paraphrase drift. The fix site is `docs/GLOSSARY.md`, not `walker.py`, so the forward is structurally correct.

### CHANGELOG disposition (interim)

`git diff -- CHANGELOG.md` is empty, consistent with the cycle being a logic-pass-only spawn awaiting the comment pass and changelog disposition. Terminal three-state changelog verification will be performed when Worker 2 returns from the comment+changelog pass.

### Validation

- `uv run ruff format --check django_strawberry_framework/optimizer/walker.py` — pass ("1 file already formatted"). The COM812-with-formatter warning is the package-wide pre-existing warning, not a delta from this diff.
- `uv run ruff check django_strawberry_framework/optimizer/walker.py` — pass ("All checks passed!"). No `--fix` invoked, per dispatch instructions.
- No pytest run — pure dead-code removal with no behavior change to pin.

### Verification outcome

`logic accepted; awaiting comment pass`

Top-level `Status:` line remains `fix-implemented (awaiting comment pass)`. Checklist box in `docs/review/review-0_0_7.md` NOT marked — terminal acceptance requires comment pass + changelog disposition + a final Worker 3 verification gate.

---

## Comment/docstring pass

### Files touched

- None — no-op comment pass.

### Per-finding dispositions

- Medium 1 (dead `parent_type` parameter): No docstring edit warranted. `_plan_select_relation`'s docstring at `walker.py:299` is a one-liner ("Plan a same-query single-valued relation traversal.") that names neither the dropped parameter nor any parameter — there is no stale wording to remove. Verified by `grep -rn "parent_type" django_strawberry_framework/optimizer/walker.py` returning zero hits post-edit (parameter declaration gone, no docstring/comment references survived because none existed pre-edit). Cross-module sweep: `grep -rn "parent_type" django_strawberry_framework/ tests/` confirms remaining hits are all in unrelated surfaces — `types/resolvers.py` (legitimate per-resolver-cls parameter for FK-id elision lookup), `optimizer/plans.py` (`resolver_key` parameter for the parent-type-qualified resolver key), and `tests/types/test_resolvers.py` / `tests/optimizer/test_plans.py` (pinning those legitimate surfaces). None reference walker's dropped parameter.
- Low 1 (`_target_has_custom_get_queryset` double-call): No comment edit warranted — forward-looking deferral, no source change this cycle, existing comments still describe the live behaviour.
- Low 2 (9-argument positional dispatch): No comment edit warranted — same disposition as L1, forward-looking deferral with no source change.
- Low 3 (GLOSSARY drift on FK-id elision introspection surface): No comment edit warranted in `walker.py` — the canonical fix site is `docs/GLOSSARY.md:462`, forwarded to the project pass per Worker 1's explicit instruction.

### Validation run

- `uv run ruff format .` — pass / no-changes (118 files left unchanged).
- `uv run ruff check --fix .` — pass (`All checks passed!`).

### Notes for Worker 3

Valid no-op comment pass: the dropped parameter never appeared in any docstring, inline comment, or sibling-module reference, so there is no stale wording for the logic-pass landing to invalidate. Worker 3's logic-pass verification already ratified the four-call-site shape convergence as the structural pin; nothing in the comment surface needs to mirror that pin.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Two-citation bar satisfied: (1) `AGENTS.md` line 21 — "Do not update CHANGELOG.md unless explicitly instructed"; (2) `docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle (dispatch prompt batched changelog into this spawn but did not authorize an edit). Reinforced by the 0.0.7 precedent chain: cycles 1-15 all closed `Not warranted` on this same two-citation argument; this is the sixteenth in the chain. The cycle's only source edit is the removal of a dead positional parameter from an optimizer-internal helper (`_plan_select_relation`) with no public-API surface, no behaviour change, and no observable effect on schema generation, query planning output, or error contracts. Nothing consumer-visible.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Verification (Worker 3, pass 2)

### Terminal verification outcome

- **Logic-pass diff stable since pass 1**: `git diff -- django_strawberry_framework/optimizer/walker.py` shows exactly the three-line removal Worker 2 landed at the logic pass — one `parent_type: type | None,` parameter declaration line (former `walker.py:292`) plus two `type_cls,` positional-argument lines at the two call sites (`_walk_selections` default-dispatch at former `walker.py:277`, `_apply_hint`'s `force_select` branch at former `walker.py:477`). No additional hunks from the comment pass, consistent with Worker 2's documented no-op disposition. Four `_plan_select_relation` / `_plan_prefetch_relation` call sites still converge on the same 10-arg positional shape.
- **Dead-parameter elimination confirmed**: `grep -n "parent_type" django_strawberry_framework/optimizer/walker.py` returns zero hits, confirming both that no executable reference survived and that the parameter declaration itself is gone.
- **Comment pass no-op ratified**: Worker 2's per-finding dispositions correctly observed that `_plan_select_relation`'s docstring is a one-liner naming no parameters, so the dropped parameter had no docstring or inline-comment footprint to invalidate. Cross-module sweep confirmed remaining `parent_type` hits in `types/resolvers.py`, `optimizer/plans.py`, and their tests are unrelated legitimate surfaces (per-resolver-cls parameter for FK-id elision lookup; `resolver_key` parent-type-qualified resolver key). No stale wording survived anywhere in the package.

### Changelog disposition

`Not warranted` ratified. `git diff -- CHANGELOG.md` is empty. Two-citation bar satisfied with (1) `AGENTS.md` line 21 ("Do not update CHANGELOG.md unless explicitly instructed") and (2) `docs/review/review-0_0_7.md` silence on changelog authorization for this cycle. Reinforced by the 0.0.7 sixteen-cycle precedent chain (cycles 1–15 all closed `Not warranted` on this same two-citation argument). The cycle's only source edit is the removal of a dead positional parameter from an optimizer-internal helper with no public-API surface, no behaviour change, and no observable effect on schema generation, query planning output, or error contracts.

### Validation

- `uv run ruff format --check .` — pass ("118 files already formatted"). The COM812-with-formatter warning is the package-wide pre-existing notice, not a delta from this diff.
- `uv run ruff check .` — pass ("All checks passed!").
- No pytest run — pure dead-code removal with no behavior change to pin; consistent with AGENTS.md line 14 ("Do not run pytest after edits; run only when explicitly asked").

### Verification outcome

`verified`
