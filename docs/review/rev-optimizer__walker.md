# Review: `django_strawberry_framework/optimizer/walker.py`

Status: verified

## DRY analysis

- Defer until a third walker-level call to `_apply_hint`'s `force_select` / `force_prefetch` dispatch lands; collapse `walker.py::_apply_hint`'s `if hint.force_select:` branch (`walker.py:460-492`) and `if hint.force_prefetch:` branch (`walker.py:494-506`) plus the default-cardinality dispatch at `walker.py:264-289` into a shared `_dispatch_select_or_prefetch(sel, django_field, django_name, target_type, plan, prefix, full_path, info, runtime_paths, resolver_identities, *, force_kind=None)` helper. Today there are three near-identical 9-argument call-tuples at `walker.py:266-276` (default prefetch), `walker.py:278-289` (default select), `walker.py:469-479` (force_select downgrade to prefetch), `walker.py:481-492` (force_select), and `walker.py:495-505` (force_prefetch) — five sites, but four of them are inside `_apply_hint` and share the `force_kind` decision branch with one call site outside `_apply_hint`. Trigger: a third hint shape (e.g. an aggregates `force_aggregate` mode) lands and adds a sixth call tuple. Until then the explicit five-line `_plan_*_relation(... 9 positional args ...)` stanzas read clearly and the visual symmetry between force_select/force_prefetch/default is load-bearing for the priority-order comment at `walker.py:429-431`.

- Defer until a second non-`_walk_selections` callsite of `_merge_aliased_selections(_included_field_selections(selections))` lands; promote the two-step combinator at `walker.py:176` (`_walk_selections`) and `walker.py:567` (`_selected_scalar_names`) into a single `_normalized_field_selections(selections) -> list[Any]` helper. Both call sites use the exact same `_merge_aliased_selections(_included_field_selections(selections))` chain to convert raw selections into "directive-filtered + fragment-inlined + alias-merged field list"; calling the two-step shape `_normalized_field_selections` would make the contract a single name and prevent a future drift where one site inlines fragments without merging aliases (or vice versa). Trigger: a third caller materializes the same chain (likely when aggregates / orders sites need the same normalization), OR a regression test pins the helper composition. Until then two call sites is below the rule-of-three.

- Defer until `_can_elide_fk_id`'s field-shape probing grows a fourth `getattr` or the composite-PK guard graduates from `pragma: no cover` to a real test; extract `_target_pk_fields(field) -> tuple[str, ...] | None` to encapsulate the `getattr(related_model._meta, "pk_fields", None)` probe at `walker.py:592-594`. Today the composite-PK guard at `walker.py:595-599` is the sole consumer and is correctly `pragma: no cover` per AGENTS.md rule 12 (Django 5.2+ composite PK fixtures do not exist in the test suite). Trigger: a Django 5.2+ composite-PK fixture lands, OR a second pk-shape probe (e.g. nullable-pk detection) needs the same `_meta.pk_fields` access. Until then the inline form is auditable in one place.

## High:

None.

## Medium:

### `walker.py::_apply_hint` `prefetch_obj` branch records resolver identities BEFORE the lookup-rebase that can raise `ConfigurationError`

In `_apply_hint`, the `if hint.prefetch_obj is not None:` branch (`walker.py:435-459`) executes `_record_relation_access(plan, django_field, prefix, resolver_identities)` and sets `plan.cacheable = False` at lines 436 and 442 **before** calling `_prefetch_hint_for_path(...)` at line 452 which may raise `ConfigurationError` for two distinct misconfiguration shapes — `prefetch_through is None` (`walker.py:519-523`) or a lookup that doesn't target the hinted relation (`walker.py:531-534`).

Consequence: when a consumer's misconfigured `OptimizerHint.prefetch(obj)` raises at plan time, the partially-mutated `plan` (with the resolver identity recorded in `planned_resolver_keys`, the `attname` appended to `only_fields`, and `cacheable=False`) is the same `plan` object that the root `plan_optimizations` returns via `plan.finalize()` if the caller swallows the exception. The exception today bubbles out of `plan_optimizations` and the partially-mutated plan is unreachable, but the call-order is a brittle-edge-case shape: any future caller that catches `ConfigurationError` at this layer (e.g. a permissive-mode toggle, a `try/except` around `_apply_hint` per-field) would consume a plan with phantom `planned_resolver_keys` and a phantom connector column for a relation that was never actually planned. The `_prefetch_hint_for_path` validators are the load-bearing guard against silent misrouting (per `walker.py:531-534`); they should run before any plan mutation.

Recommended fix: hoist the `_prefetch_hint_for_path(...)` call above the `_record_relation_access` / `cacheable = False` mutations so the rebased `Prefetch` is computed first; only after the validators pass should `plan` be mutated. The append_prefetch_unique guard remains last. Test pin: a new `test_plan_prefetch_obj_hint_misconfigured_lookup_leaves_plan_clean` that asserts after a raised `ConfigurationError`, `plan.planned_resolver_keys`, `plan.only_fields`, and `plan.cacheable` are unchanged from a baseline empty plan.

```django_strawberry_framework/optimizer/walker.py:435-459
    if hint.prefetch_obj is not None:
        _record_relation_access(plan, django_field, prefix, resolver_identities)
        # Consumer-supplied Prefetch objects commonly close over a queryset
        # built with request- or user-scoped filters; matching the
        # has_custom_get_queryset discipline in _plan_prefetch_relation, mark
        # the plan non-cacheable so the plan cache cannot serve one
        # request's queryset to the next.
        plan.cacheable = False
        ...
        append_prefetch_unique(
            plan.prefetch_related,
            _prefetch_hint_for_path(    # may raise ConfigurationError
                hint.prefetch_obj,
                django_name=django_name,
                full_path=full_path,
                type_name=type_cls.__name__,
            ),
        )
        return True
```

## Low:

### Stale `spec-014` citations in walker docstrings; the cited contract lives in `spec-018-meta_primary-0_0_6.md`

Two docstrings cite `spec-014` for the H2/nested-source_type contract, but the actual contract lives in `spec-018-meta_primary-0_0_6.md` (rev6 M1 audit invariant, "Cache scope (rev6 L1)", and the Slice 4 `_resolve_field_map` call-site decision at `docs/SPECS/spec-018-meta_primary-0_0_6.md:141`). `spec-014-testing_shift-0_0_4.md` carries zero matches for `source_type` — it is the testing-shift spec, not the multi-type/primary spec.

- `walker.py::_resolve_field_map` `#"the spec-014 nested contract"` (line 98) — should read `the spec-018 nested contract`.
- `walker.py::_selected_scalar_names` `#"(spec-014 rev6 M1 audit invariant.)"` (line 564) — should read `(spec-018 rev6 M1 audit invariant.)`.

Same severity calibration as the `spec-016 → spec-020` drift in `list_field.py`, the `spec-020 → spec-025` drift in `scalars.py`, and the `spec-014 → spec-018` drift in `optimizer/extension.py` already filed at `rev-optimizer__extension.md` (Low). Citation hygiene, not logic; the reasoning the comments capture is correct against the actual cited spec.

### `_walk_selections`'s 140-line / 13-branch body is the package's top control-flow hotspot

`walker.py::_walk_selections` (lines 150-289) spans 140 source lines and 13 branch nodes per the shadow overview — comfortably above the Medium-tier 40-line / 8-branch threshold from `REVIEW.md` "Reading the overview". The body interleaves four distinct concerns:

1. Root field-map / hints resolution (lines 175-176, 246-247).
2. Decision-7 custom-pk Relay projection (lines 180-222).
3. Scalar projection (lines 223-229).
4. Relation dispatch (lines 230-289), which itself splits into the hint-apply branch (lines 246-262) and the default cardinality dispatch (lines 264-289).

Today every concern is reachable through a tight focused test in `tests/optimizer/test_walker.py` (Decision-7 custom-pk via `test_plan_relay_id_projects_real_pk_attname_when_not_id` at `tests/optimizer/test_walker.py:173-213`, scalar projection via `test_plan_collects_only_fields_for_selected_scalars`, hint-apply via the `_apply_hint` tests). Branch coverage is solid. The concern is maintainability: a future slice that touches any of the four concerns has to re-read all four to keep the loop body coherent.

Defer the refactor (extract `_plan_custom_pk_relay_projection(sel, type_cls, model, field_map, plan, prefix)` and `_plan_relation_dispatch(sel, django_field, django_name, type_cls, target_type, hints_map, plan, prefix, info, runtime_prefixes)`) until a fifth concern lands in the loop body — currently the four-concern shape is the natural decomposition of "walk one selection layer". Trigger condition: an aggregates / orders / connection-field slice adds a fifth in-body concern, OR a regression test pins one concern in isolation against a shared scaffold that the inline form does not provide.

### `_resolve_field_map` dual-contract fallback returns raw Django fields keyed by `f.name` without `snake_case` normalization

`walker.py::_resolve_field_map` builds the fallback field_map as `{f.name: f for f in model._meta.get_fields()}` at line 117. The registered path keys on `snake_case(field.name)` (per `tests/optimizer/test_walker.py:117`'s `_register_type_definition` helper and the registry side at `field_meta.py`). For Django field names that are already snake_case (the overwhelming majority) the two key shapes coincide. But a field whose name contains an underscore-camelCase mix (e.g. Django auto-generated `_ptr` MTI fields, or a future consumer with `myField` ORM-level naming) would key the registered path on `my_field` and the fallback path on `myField`, producing silent lookup misses on the fallback path.

The fallback path is exercised in `tests/optimizer/test_walker.py:282-302` (`test_plan_prefetches_relation_with_missing_related_model_defensively`) and `:305-326` (`test_plan_select_relation_with_missing_related_model_is_not_elided`), both of which key on the test's own fake_field with snake_case names already, so the drift is not currently surfaced.

Defer until a second `snake_case(...)` key mismatch lands as a real regression OR the registry-coverage gate referenced in the dual-contract docstring at `walker.py:101-110` ships and removes the fallback path. Trigger: any test that builds a `model._meta.get_fields()` shape with non-snake_case field names. Same severity calibration as the `_can_elide_fk_id` composite-PK pragma-no-cover Low — defensive shape that the test suite cannot reach today but a future fixture can.

### `_merge_aliased_selections` O(N²) copy of `merged.selections` on each merge

In `walker.py::_merge_aliased_selections` lines 715-717:

```python
merged.selections = list(merged.selections) + list(
    getattr(sel, "selections", None) or [],
)
```

Each subsequent alias of the same field rebuilds `merged.selections` by copying the accumulated list. For N aliases of the same field the total work is O(N²) and the allocator pressure grows with the cumulative child-selection count. The behavior is correct; the cost is invisible because real-world N is 2-5.

Defer until a real-world workload pins a regression — `merged.selections.extend(...)` would be the obvious in-place fix but the current assignment is documented as defensive against tests / future integration shims that omit the selections list (`walker.py:712-714` comment). The current shape is intentional defensive widening; the rewrite to in-place extend would silently swallow the same shim shapes. Trigger: a benchmark / profiler trace pins this as hot, OR the defensive widening is removed because the shim shapes are deprecated.

### `_walk_selections` Decision-7 custom-pk Relay branch has no explicit pin for the `id_attr == "pk"` resolution branch

Inside `walker.py::_walk_selections` lines 201-212, the Decision-7 branch resolves `id_attr = type_cls.resolve_id_attr()` and, when that returns the literal `"pk"`, falls back to `model._meta.pk.attname` at line 204. Both regression tests in this branch (`test_plan_relay_id_projects_real_pk_attname_when_not_id` at `tests/optimizer/test_walker.py:173-213` and `test_plan_relay_id_projects_attname_when_pk_is_relation` at `tests/optimizer/test_walker.py:216-279`) exercise the `id_attr != "pk"` shape — the first monkey-patches `Category._meta.pk.attname` to `"name"` after registering with default Relay setup; the second uses `OneToOneField(primary_key=True)` whose `resolve_id_attr` returns the explicit field name. The `id_attr == "pk"` fallback at `walker.py:203-204` is reachable when a consumer subclasses `relay.Node` without overriding `resolve_id_attr` and the model's pk attname is NOT `"id"` (e.g. a `UUIDField(primary_key=True)` named `uuid` with default `relay.Node` config). Today's tests register Relay types where the `id_attr` is already explicitly resolved, skipping the `"pk"` fallback.

Defer until the next Decision-7 regression lands OR the next `_walk_selections` refactor splits the Decision-7 branch into a named helper (`_plan_custom_pk_relay_projection` per the per-`_walk_selections` hotspot Low). At that point a focused unit test against the named helper would pin both branches cleanly. Trigger: a consumer-reported lazy-load on `resolve_id` with default Relay config and a non-`"id"` pk attname, OR the hotspot decomposition. Same severity as the existing `pragma: no cover` Low for composite PK in `_can_elide_fk_id` — defensive branch, no current test, no current regression.

### `_walk_selections`'s `db_field = next(...)` over `field_map.values()` is O(N) per missing `id` selection

In `walker.py::_walk_selections` line 205-212, the Decision-7 Relay projection branch resolves `id_attr` and then scans every value in `field_map` to find a `FieldMeta` whose `name` or `attname` matches. For models with N fields and an `id`-only top-level selection from a custom-pk Relay type, this is O(N) per call. Today's models are small (<20 fields) and the call only fires when `django_name == "id"` and the field_map lacks `"id"` (the custom-pk path), so the cost is negligible.

The alternative — maintaining a precomputed `id_attr_lookup: dict[str, FieldMeta]` on the registered `DjangoTypeDefinition` — would be a real `FieldMeta`-side optimization, not a walker-level one. The walker correctly performs the lookup at the layer that has the information (the `id_attr` value depends on `type_cls.resolve_id_attr()` which is a per-call Strawberry Relay shape).

Defer until the registry's field_map carries `attname`-indexed lookup as a first-class shape OR a benchmark pins this branch as hot. Trigger: the registry-coverage gate from `walker.py:101-110` lands and removes the fallback dict shape entirely, at which point the lookup can move into `FieldMeta`'s build-time precomputation.

### `_ensure_connector_only_fields` reverse-O2O / reverse-FK connector fallback uses `getattr(parent_field, "reverse_connector_attname", None)`

`walker.py::_ensure_connector_only_fields` lines 636-641 handle the reverse-O2O / reverse-FK case by reading `getattr(getattr(parent_field, "field", None), "attname", None) or getattr(parent_field, "reverse_connector_attname", None)`. The second clause references an attribute name `reverse_connector_attname` that does NOT exist on Django's `OneToOneRel` / `ManyToOneRel` shapes — `getattr(...)` returns `None` on every real Django field. The fallback is dead code under all Django shapes the test suite exercises.

The first clause covers the real shape: Django reverse-relation descriptors expose `.field` (the forward FK on the related model), whose `.attname` is the connector column. The test `test_ensure_connector_only_fields_adds_reverse_o2o_connector` at `tests/optimizer/test_walker.py:1578-1595` pins this via `Patron._meta.get_field("card")` — a real reverse-O2O whose `.field.attname` resolves the connector.

The `reverse_connector_attname` clause was likely a port-time defensive shape that no Django version surfaces. Same severity as the `_can_elide_fk_id` composite-PK pragma-no-cover: defensive code with no current reachability. Defer dropping it until a Django version change is reviewed OR the helper grows a named `_reverse_connector(parent_field)` extraction that consolidates the three connector-resolution shapes.

### `_record_relation_access` always appends the FK `attname` to `plan.only_fields` even when the relation is later FK-id elided

`walker.py::_plan_select_relation` calls `_record_relation_access(plan, django_field, prefix, resolver_identities)` at line 305 BEFORE the FK-id elision check at lines 307-314. `_record_relation_access` appends `f"{prefix}{attname}"` to `plan.only_fields` at line 368. When the elision branch fires at line 313 (`append_unique_many(plan.fk_id_elisions, resolver_identities)`), the connector column has already been recorded in `only_fields` — which is exactly what's needed because Django still needs the FK column even when the JOIN is elided.

This is correct behavior (verified by `test_plan_elides_forward_fk_when_child_selection_is_id_only` at `tests/optimizer/test_walker.py:627-637` where `only_fields == ("name", "category_id")` and `fk_id_elisions == ("category@category",)`). The Low is documentation: the docstring on `_record_relation_access` at `walker.py:365` reads "Record the shared connector and resolver metadata for a relation" — it doesn't surface that the connector is *required* downstream when elision fires. A future reader refactoring the call-order in `_plan_select_relation` could move `_record_relation_access` after the elision check and silently drop the FK column on the elided path, reintroducing a lazy load through `getattr(obj, "category_id")` falling back to `obj.category.pk`.

Defer until the docstring grows or a property-test pins "FK-id elision always coexists with the connector column in only_fields". Trigger: the same future refactor that decomposes `_walk_selections` into named helpers (the per-`_walk_selections` hotspot Low). At that point the contract should be encoded explicitly: `_record_relation_access` MUST run before the elision check.

### Forward to `rev-optimizer.md` folder pass: `_resolve_field_map` and `_field_meta_for_resolver` dual-contract mirror

`walker.py::_resolve_field_map` and `types/resolvers.py::_field_meta_for_resolver` both materialize the same dual-contract field-map (registered DjangoType → `FieldMeta`, fallback → raw Django field). The walker's docstring at `walker.py:108-110` explicitly names the divergence and asks "keep the two in sync." `rev-optimizer__field_meta.md` already flagged the act-now opportunity to extract `FieldMeta._from_field_shape(field, *, is_relation)` to collapse the resolver-side mirror. The walker-side `_resolve_field_map`'s `else {f.name: f for f in model._meta.get_fields()}` branch is the OTHER half of the same DRY opportunity — both call sites would benefit from a shared `_field_map_or_fallback(model, source_type)` helper that returns `(type_cls, field_map_or_fallback)` with a uniform key shape. Carrying forward to the folder pass since the two call sites are in different folders (`optimizer/walker.py` and `types/resolvers.py`); the act-now folding happens at `rev-types__resolvers.md` review or at the folder pass.

### Forward to `rev-django_strawberry_framework.md` project pass: walker-internal symbols (`plan_optimizations`, `plan_relation`) GLOSSARY coverage

`plan_optimizations` (the optimizer's pure-function entry point used by the extension) and `plan_relation` (the relation-kind probe used by `types/resolvers.py`) are both consumer-internal but cross-module-imported within `django_strawberry_framework`. Per the `optimizer/__init__.py:14-17` "internal implementation details" framing (cited in `rev-optimizer__plans.md`), these are correctly absent from GLOSSARY. No in-cycle action.

Same calibration as the per-helper symbols in `rev-optimizer__plans.md` (`OptimizationPlan`, `diff_plan_for_queryset`, etc.) — internal mechanics correctly absent from GLOSSARY; the consumer-facing surface for the optimizer is `DjangoOptimizerExtension`, `OptimizerHint`, `Meta.optimizer_hints`, `Plan cache`, `FK-id elision`, `only() projection` — all of which have current entries (drift items already filed under `rev-optimizer__extension.md` and `rev-optimizer__plans.md`).

## What looks solid

### DRY recap

- **Existing patterns reused.** Walker reuses `plans.py`'s `append_unique` (`walker.py:221, 228, 315, 344, 368, 545, 547, 651`), `append_unique_many` (`walker.py:313, 369`), `append_prefetch_unique` (`walker.py:356, 450`), `resolver_key` (`walker.py:238`), and `runtime_path_from_info` (`walker.py:51`) — every plan mutation routes through a `plans.py` helper, no open-coded dedupe. The `OptimizationPlan.finalize()` single-handoff at `walker.py:58` is the only finalisation site in the optimizer subpackage (audit per `rev-optimizer__plans.md` carry-forward — confirmed clean). `_target_has_custom_get_queryset` (`walker.py:75-76`) consolidates the `target_type is not None and target_type.has_custom_get_queryset()` predicate at four call sites (lines 63, 309, 340, 468). `hint_is_skip` (imported from `.hints`) routes the skip-shape check through a single dispatch helper, no open-coded `hint is OptimizerHint.SKIP or hint.skip` regressions (audit per `rev-optimizer__hints.md` carry-forward — confirmed clean). `DST_OPTIMIZER_*` key constants are not raw-string-imported (audit per `rev-optimizer___context.md` carry-forward — confirmed clean; walker does not stash on context directly, the extension does).
- **New helpers considered.** A `_dispatch_select_or_prefetch(force_kind=...)` consolidator collapsing the three near-identical `_plan_*_relation(... 9 positional args ...)` call tuples in `_apply_hint`'s force_select/force_prefetch branches plus the default-cardinality dispatch in `_walk_selections` was evaluated and deferred (per DRY analysis bullet 1) — the visual symmetry between the three sites is load-bearing for the priority-order comment at `walker.py:429-431`. A `_normalized_field_selections(selections)` two-step combinator at `walker.py:176` / `walker.py:567` was evaluated and deferred (DRY bullet 2) — two call sites is below the rule-of-three.
- **Duplication risk in the current file.** `_walk_selections` and `_build_prefetch_child_queryset` both call `_walk_selections` recursively; the deliberate divergence (root call passes `source_type=origin`, nested calls leave it `None`) is the spec-018 nested contract and must NOT be folded through a shared "recursive walk" helper. Two `_target_has_custom_get_queryset(target_type)` calls inside `_plan_prefetch_relation` (`walker.py:340`) and `_build_prefetch_child_queryset` (`walker.py:401` via `has_custom_get_queryset=has_custom_get_queryset` parameter) is intentional: the parent computes once and threads the value down, avoiding the second method call on the prefetch path (per the `_build_child_queryset` docstring at `walker.py:138-143`). The `_record_relation_access` call in `_plan_select_relation:305`, `_plan_prefetch_relation:339`, and `_apply_hint`'s `prefetch_obj` branch at `walker.py:436` is the same connector-recording helper invoked at three sites — single source of truth for the connector-column + resolver-identity invariant.

### Other positives

- The Decision-7 custom-pk Relay projection branch (`walker.py:181-222`) has the most thorough inline rationale in the package: 19 lines of comment explaining `id_attr in field_map` is the wrong check, why `attname` differs from `name` on `OneToOneField(primary_key=True)`, and which test pins which sub-case. Audit-trail quality is high.
- The `_can_elide_fk_id` composite-PK guard at `walker.py:595-599` carries an explicit `pragma: no cover` with the reason "Test fixtures do not define one; the guard exists so the elision branch fails closed if a consumer adopts composite PKs" — exactly the AGENTS.md rule 12 shape for genuinely unreachable defensive guards.
- The `_apply_hint` `prefetch_obj` branch's `type_cls.__name__` unguarded access at `walker.py:456` is paired with an explanatory comment at `walker.py:443-449` that justifies the lack of `is not None` guard via the upstream `_resolve_optimizer_hints` short-circuit invariant. Future direct callers will `AttributeError` loudly rather than rot behind a silent `"UnknownType"` literal — the right defensive-vs-loud calibration.
- Test surface in `tests/optimizer/test_walker.py` (1,754 lines, 60+ test functions) covers every documented walker behavior with focused synthetic-selection fixtures. The fragment/alias/directive/Relay-pk/FK-id-elision/hint dispatch / nested-prefetch / cache-safety / connector-column matrix is the canonical example of "Test through real usage and prefer the example project" applied to a pure walker — the walker is testable in isolation because it dispatches on duck-typed attributes, so the test fixtures are `SimpleNamespace` shells that exercise the same code paths as real Strawberry nodes.
- The `_merge_aliased_selections` debug-log for divergent arguments (`walker.py:725-731`) is pinned by `test_merge_aliased_selections_logs_when_arguments_diverge` at `tests/optimizer/test_walker.py:533-563` — the trace exists exactly to surface the future per-argument planning slice, with the test as a tripwire.
- The deliberate divergence between `_walk_selections`'s root invocation receiving `source_type=origin` and the recursive nested calls receiving `source_type=None` (per `walker.py:163-168` and `walker.py:317-324`) is correct against the spec-018 multi-type primary contract: the resolver's actual Strawberry return type drives the root field_map, but nested relation targets always resolve to the primary. The test triad — `test_optimizer_walker_plans_root_from_resolver_return_type_when_secondary`, `test_scalar_only_secondary_resolver_uses_secondary_field_map`, `test_optimizer_walker_uses_primary_for_nested_relation_target` at `tests/optimizer/test_walker.py:1603-1753` — pins all three contract arms cleanly.

### Summary

`walker.py` is the optimizer's selection-tree workhorse: 764 lines, 25 module-level symbols, 14 helpers + 2 public entries (`plan_optimizations`, `plan_relation`) + supporting predicates. One Medium calls out a brittle-edge-case: `_apply_hint`'s `prefetch_obj` branch mutates `plan` before the `_prefetch_hint_for_path` validators run, so a future caller that catches `ConfigurationError` at this layer would consume a partially-mutated plan with phantom connector columns and resolver keys. Eight Lows split between citation hygiene (spec-014 → spec-018 in two docstrings), control-flow hotspot decomposition deferred to a fifth-concern trigger (`_walk_selections` at 140/13 hot), and forward-looking gaps with explicit triggers (composite-PK pragma, snake_case fallback drift, Decision-7 `id_attr=="pk"` branch coverage, O(N²) merge cost, dead reverse_connector_attname fallback, connector-column docstring tightening). One DRY bullet forwarded to the folder pass (`_resolve_field_map` / `_field_meta_for_resolver` dual-contract mirror) and one GLOSSARY confirmation forwarded to the project pass (walker-internal symbols correctly absent per `optimizer/__init__.py:14-17`). All major contracts — H2 root origin threading, spec-018 nested primary contract, Decision-7 custom-pk Relay projection, FK-id elision branch isolation, optimizer hint dispatch, `_ensure_connector_only_fields` four-shape connector resolution, plan cacheable flip on consumer-supplied Prefetch — are pinned by focused tests.

---

## Fix report (Worker 2)

### Files touched
- `django_strawberry_framework/optimizer/walker.py::_apply_hint` `#"if hint.prefetch_obj is not None:"` — hoisted the `_prefetch_hint_for_path(...)` validator call ABOVE the `_record_relation_access(plan, ...)` + `plan.cacheable = False` mutations. The rebased `Prefetch` is now computed into a `rebased_prefetch` local first; only after the validators pass do the plan mutations + `append_prefetch_unique` run. Added an inline comment naming the no-mutation-on-raise invariant and citing the two raising shapes inside `_prefetch_hint_for_path` (`prefetch_through is None`, mismatched lookup). The `type_cls.__name__` short-circuit comment is preserved verbatim above the new validator call.

### Tests added or updated
- `tests/optimizer/test_walker.py::test_apply_hint_prefetch_obj_misconfigured_lookup_leaves_plan_clean` — pins the no-mutation-on-raise contract. Builds a baseline empty `OptimizationPlan()`, calls `_apply_hint` directly with `OptimizerHint.prefetch(Prefetch("unrelated_relation", ...))` on `Item._meta.get_field("category")`, expects `ConfigurationError` matching the mismatched-lookup attribution (`ItemType.category`, `'category'`), and asserts `plan.only_fields`, `plan.planned_resolver_keys`, and `plan.cacheable` are bit-equal to the baseline tuple captured before the raise. Pre-fix this test would fail because `_record_relation_access` already appended `"category_id"` to `only_fields` and the resolver identity to `planned_resolver_keys`, and `cacheable` was flipped to `False`, before the validator raised.
- Added `_apply_hint` and `OptimizationPlan` to the existing `from django_strawberry_framework.optimizer.walker import (...)` block and `from django_strawberry_framework.optimizer.plans import OptimizationPlan` import (module-level; mirrors the two existing local imports at `tests/optimizer/test_walker.py:1359` and `:1591` consolidating to the top of the file for the new test's reuse). The local imports inside the two existing tests stay untouched per logic-pass scope discipline.

### Validation run
- `uv run ruff format .` — pass (213 files left unchanged)
- `uv run ruff check --fix .` — pass (All checks passed!)
- No pytest run per worker-2 hard rule; read the new test inline and verified the assertion shape matches the post-fix invariant (pre-fix path mutates `only_fields` via `_record_relation_access`'s `append_unique(plan.only_fields, f"{prefix}{attname}")` at `walker.py::_record_relation_access`, post-fix `_prefetch_hint_for_path` raises first and the plan stays at its baseline tuple).

### Notes for Worker 3
- Shadow file: not used during this fix; existing `docs/shadow/walker.*` files from plan time remain authoritative but were not re-consulted.
- Low #1 (spec-014 → spec-018 citation drift at `walker.py::_resolve_field_map` `#"the spec-014 nested contract"` and `walker.py::_selected_scalar_names` `#"(spec-014 rev6 M1 audit invariant.)"`) is comment-pass scope per the dispatch prompt — NOT touched in this logic pass.
- All other Lows are explicitly defer-with-trigger per Worker 1's prose; no in-cycle edit.
- DRY analysis: all three bullets are defer-with-trigger; no in-cycle edit.
- The pre-fix call order at `walker.py::_apply_hint #"_record_relation_access(plan, django_field, prefix, resolver_identities)"` (the original line 436 in the artifact) is replaced; the post-fix order is `_prefetch_hint_for_path(...) → _record_relation_access(...) → plan.cacheable = False → append_prefetch_unique(plan.prefetch_related, rebased_prefetch)`. No behavioral change on the happy path: the same Prefetch is appended, the same connector column is recorded, the same `cacheable` flip happens — only the failure path is now strictly fail-fast-clean.
- Many out-of-scope paths are dirty (presumptively concurrent maintainer work per AGENTS.md #33): `TODAY.md`, `optimizer/{plans,extension,hints,_context,field_meta}.py`, `orders/**`, `examples/fakeshop/**`, `docs/{GLOSSARY,TREE}.md`, multiple `docs/review/rev-*.md`, `scripts/{build,import}_glossary_md.py`, `tests/orders/*`, etc. None touched by this cycle.
- `uv.lock` unchanged (no `uv run ...` dependency-change call surface).

---

## Verification (Worker 3)

### Logic verification outcome
- **Medium accepted.** `_prefetch_hint_for_path(...)` is hoisted above the plan mutations in `_apply_hint`'s `prefetch_obj` branch (`walker.py:453-466`): the validator runs first into a `rebased_prefetch` local, then `_record_relation_access` (line 459), `plan.cacheable = False` (line 465), and `append_prefetch_unique(plan.prefetch_related, rebased_prefetch)` (line 466) only on the success path. The pre-fix call-order from the artifact's quoted block is no longer present (grep confirms `_record_relation_access` no longer precedes the validator in this branch). The inline comment block at `walker.py:443-452` names the no-mutation-on-raise invariant and cites both raising shapes (missing lookup, mismatched relation), so a future reader cannot silently move the mutations back ahead of the validator without contradicting the in-source rationale.
- **Lows.** All eight Lows are explicitly defer-with-trigger per Worker 1's prose; Low #1 (spec-014 → spec-018 citation drift) is comment-pass scope and correctly untouched at this logic pass per the Notes-for-Worker-3 block. No in-cycle edits required.

### DRY findings disposition
- All three DRY bullets are defer-with-trigger; no in-cycle edits required (`_dispatch_select_or_prefetch` consolidator deferred until a sixth call tuple lands; `_normalized_field_selections` two-step combinator deferred until a third caller; `_target_pk_fields` extraction deferred until a fourth `_meta` probe or a composite-PK fixture). Worker 2's report confirms no DRY edits attempted, which is the right scoping for a Medium-only logic pass.

### Temp test verification
- No temp tests needed. The new regression test `test_apply_hint_prefetch_obj_misconfigured_lookup_leaves_plan_clean` at `tests/optimizer/test_walker.py:1580` directly pins the invariant the Medium fix protects: baseline empty `OptimizationPlan()`, `_apply_hint` invocation with a `Prefetch("unrelated_relation", ...)` against `Item._meta.get_field("category")`, expected `ConfigurationError` matching the mismatched-lookup attribution (`ItemType.category` + `'category'`), and a triple-assertion that `only_fields` / `planned_resolver_keys` / `cacheable` are bit-equal to the baseline tuple captured before the raise. Focused run: `uv run pytest tests/optimizer/test_walker.py -x -k "apply_hint_prefetch_obj"` → `1 passed, 77 deselected in 0.31s` (the `fail_under = 100` coverage gate trips because focused-by-`-k` runs only one test, which is expected and not in-scope for logic verification).

### Verification outcome
- logic accepted; awaiting comment pass
- comments accepted; awaiting changelog disposition
- cycle accepted; verified

### Terminal-verify (Worker 3)
- `git diff -- CHANGELOG.md` empty — matches `Not warranted` state.
- Changelog disposition cites both AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and active-plan silence (`review-0_0_7.md:78` checkbox for this artifact, no changelog authorisation in dispatch prompt).
- "Not warranted" framing honest: Medium is a private-method (`_apply_hint`) no-mutation-on-raise hardening; `ConfigurationError` from `_prefetch_hint_for_path` already bubbled out of `plan_optimizations` pre-fix with identical exception type/message; partial plan state on the failure path was unreachable to consumers (the fix protects against a hypothetical future mid-walk catcher, not against any currently-shipped caller). Lows #1 and #8 are docstring/citation hygiene on internal helpers. Same calibration precedent as `optimizer/field_meta.py` and `optimizer/_context.py` cycles.
- Logic pass re-verified: `_prefetch_hint_for_path(...)` validator runs into `rebased_prefetch` at `walker.py:464-469` before `_record_relation_access(...)` at `:470`, `plan.cacheable = False` at `:476`, and `append_prefetch_unique(plan.prefetch_related, rebased_prefetch)` at `:477`. The inline rationale block at `walker.py:451-462` encodes the no-mutation-on-raise invariant in-source.
- Comment pass re-verified: `grep -n "spec-014" django_strawberry_framework/optimizer/walker.py` → zero hits; `spec-018` lands at lines 98 (`_resolve_field_map`) and 581 (`_selected_scalar_names`). `_record_relation_access` docstring (`walker.py:365-374`) encodes the must-run-before-elision contract explicitly.
- Ruff: `uv run ruff format --check django_strawberry_framework/optimizer/walker.py` → 1 file already formatted; `uv run ruff check django_strawberry_framework/optimizer/walker.py` → All checks passed.

### Comment-pass verification (Worker 3)
- Low #1 spec-014 → spec-018 token swap landed at both cited sites: `walker.py::_resolve_field_map #"the spec-018 nested contract"` (line 98) and `walker.py::_selected_scalar_names #"(spec-018 rev6 M1 audit invariant.)"` (line 581). `grep -n "spec-014" walker.py` returns zero hits post-fix. Premise verified independently: `grep -c "source_type" docs/SPECS/spec-014-testing_shift-0_0_4.md` is `0`, and `docs/SPECS/spec-018-meta_primary-0_0_6.md` carries the canonical `_resolve_field_map` Slice 4 call-site decision (lines 140-141) and the rev6 M1 audit anchor.
- Low #8 `_record_relation_access` docstring (`walker.py:365-374`) now encodes the must-run-before-elision order contract: explicitly names `_can_elide_fk_id` in `_plan_select_relation`, surfaces why the FK `attname` appended to `plan.only_fields` is the column Django still needs to materialise the relation on the elided path (`_resolve_id_default` reading `obj.<fk>_id` directly instead of triggering a lazy load through `obj.<fk>.pk`), and warns that moving the call after the elision check would silently drop the FK column and reintroduce the N+1. Encodes Worker 1's "future reader refactoring the call-order in `_plan_select_relation`" tripwire directly in-source.
- Lows #3 and #5 confirmed pure defer-with-trigger; no edits expected and none made.
- Lows #2, #4, #6, #7 preserved as defer-with-trigger in the Comment/docstring-pass Notes for Worker 3 block with verbatim trigger phrasing carried over from Worker 1's prose; future-cycle re-evaluation surface is intact.
- Lows #9 and #10 correctly forwarded (folder pass and project pass respectively); no in-cycle action.
- Ruff: `uv run ruff format --check .` → 213 files already formatted; `uv run ruff check .` → All checks passed.
- DRY analysis: all three bullets remain defer-with-trigger; no in-cycle edits attempted (correct scoping for a comment-only pass).

---

## Comment/docstring pass

### Files touched
- `django_strawberry_framework/optimizer/walker.py::_resolve_field_map` `#"the spec-018 nested contract"` (formerly `spec-014`) — Low #1 first citation rotated; the H2/nested-`source_type` contract actually lives in `docs/SPECS/spec-018-meta_primary-0_0_6.md` (rev6 M1 audit invariant + Slice 4 `_resolve_field_map` call-site decision). `spec-014-testing_shift-0_0_4.md` carries zero `source_type` matches.
- `django_strawberry_framework/optimizer/walker.py::_selected_scalar_names` `#"(spec-018 rev6 M1 audit invariant.)"` (formerly `spec-014`) — Low #1 second citation rotated; same rationale as above, this is the exact phrase Worker 1's artifact flagged. Note: the artifact named `walker.py:564` for this line but the actual source line is `walker.py:572` post-`_record_relation_access` docstring expansion below; the cited substring (``(spec-014 rev6 M1 audit invariant.)``) is grep-unique and was rotated in place.
- `django_strawberry_framework/optimizer/walker.py::_record_relation_access` (Low #8) — expanded the one-line docstring (``Record the shared connector and resolver metadata for a relation.``) into a four-sentence block that surfaces the must-run-before-elision contract: the FK ``attname`` appended to ``plan.only_fields`` here is the column Django still needs to materialise the relation when the JOIN is elided (``_resolve_id_default`` reads ``obj.<fk>_id`` directly instead of triggering a lazy load through ``obj.<fk>.pk``). Moving this call after the elision check would silently drop the FK column on the elided path and reintroduce the N+1. Encodes the contract Worker 1 named ("a future reader refactoring the call-order in ``_plan_select_relation`` could move ``_record_relation_access`` after the elision check and silently drop the FK column on the elided path") so the trigger condition Worker 1 cited ("the docstring grows") is now satisfied in-source.

### Per-finding dispositions
- Medium 1: already addressed at logic pass (`_apply_hint`'s `prefetch_obj` branch hoisted `_prefetch_hint_for_path` above plan mutations); no further comment work needed — the inline block at `walker.py:443-452` already names the no-mutation-on-raise invariant.
- Low 1 (spec-014 → spec-018 citation drift at `_resolve_field_map` and `_selected_scalar_names`): both citations rotated in-place per dispatch prompt directive.
- Low 2 (`_walk_selections` 140-line / 13-branch hotspot decomposition): defer-with-trigger per Worker 1's prose ("Defer the refactor … until a fifth concern lands in the loop body — currently the four-concern shape is the natural decomposition of 'walk one selection layer'"). Trigger preserved in Notes for Worker 3 below.
- Low 3 (`_resolve_field_map` fallback drift on non-snake_case Django field names): defer-with-trigger per Worker 1's prose ("Defer until a second `snake_case(...)` key mismatch lands as a real regression OR the registry-coverage gate referenced in the dual-contract docstring at `walker.py:101-110` ships and removes the fallback path"). No in-cycle comment tightening recommended in artifact. Preserved in Notes for Worker 3 below.
- Low 4 (`_merge_aliased_selections` O(N²) list copy): defer-with-trigger per Worker 1's prose ("Defer until a real-world workload pins a regression … the current shape is intentional defensive widening; the rewrite to in-place extend would silently swallow the same shim shapes"). Existing comment at `walker.py:720-722` already names the defensive-widening rationale. Preserved in Notes for Worker 3 below.
- Low 5 (Decision-7 `id_attr=="pk"` branch coverage): defer-with-trigger per Worker 1's prose ("Defer until the next Decision-7 regression lands OR the next `_walk_selections` refactor splits the Decision-7 branch into a named helper"). No in-cycle comment tightening recommended in artifact. Preserved in Notes for Worker 3 below.
- Low 6 (`_walk_selections` Decision-7 O(N) scan over `field_map.values()`): defer-with-trigger per Worker 1's prose ("Defer until the registry's field_map carries `attname`-indexed lookup as a first-class shape OR a benchmark pins this branch as hot"). The alternative is `FieldMeta`-side, not walker-side. Preserved in Notes for Worker 3 below.
- Low 7 (`_ensure_connector_only_fields` dead `reverse_connector_attname` fallback): defer-with-trigger per Worker 1's prose ("Defer dropping it until a Django version change is reviewed OR the helper grows a named `_reverse_connector(parent_field)` extraction that consolidates the three connector-resolution shapes"). Preserved in Notes for Worker 3 below.
- Low 8 (`_record_relation_access` order contract): docstring tightened in-place per artifact prose ("The Low is documentation: the docstring on `_record_relation_access` at `walker.py:365` reads 'Record the shared connector and resolver metadata for a relation' — it doesn't surface that the connector is *required* downstream when elision fires"). The expanded docstring now encodes the must-run-before-elision contract directly so a future refactor cannot silently move the call after the elision check without contradicting the in-source rationale.
- Low 9 (forwarded to `rev-optimizer.md` folder pass): `_resolve_field_map` / `_field_meta_for_resolver` dual-contract mirror — no in-cycle action; carried forward per Worker 1's forwarding directive.
- Low 10 (forwarded to `rev-django_strawberry_framework.md` project pass): `plan_optimizations` / `plan_relation` GLOSSARY coverage — correctly absent per `optimizer/__init__.py:14-17`; no in-cycle action.

### Validation run
- `uv run ruff format .` — pass (213 files left unchanged)
- `uv run ruff check --fix .` — pass (All checks passed!)

### Notes for Worker 3
- All in-cycle edits are comment/docstring-only; no behavior change. Low #1 is a two-site `spec-014` → `spec-018` token swap (citation hygiene matching `extension.py`'s prior cycle). Low #8 expands `_record_relation_access`'s one-line docstring to encode the must-run-before-elision contract in-source.
- Lows #2, #3, #4, #5, #6, #7 are all explicitly defer-with-trigger per Worker 1's prose; preserved here so the next walker review cycle can re-evaluate against fresh source:
  - Low #2 trigger: a fifth in-body concern lands in `_walk_selections` (aggregates / orders / connection-field slice), OR a regression test pins one concern in isolation against a shared scaffold.
  - Low #3 trigger: a second `snake_case(...)` key mismatch lands as a real regression OR the registry-coverage gate referenced in the dual-contract docstring at `walker.py::_resolve_field_map #"DUAL CONTRACT"` ships and removes the fallback path entirely.
  - Low #4 trigger: a benchmark / profiler trace pins `_merge_aliased_selections` as hot, OR the defensive widening at `walker.py::_merge_aliased_selections #"Keep duplicate selections as defensive"` is removed because the shim shapes are deprecated.
  - Low #5 trigger: a consumer-reported lazy-load on `resolve_id` with default Relay config and a non-`"id"` pk attname, OR the hotspot decomposition from Low #2.
  - Low #6 trigger: the registry-coverage gate from `walker.py::_resolve_field_map #"DUAL CONTRACT"` lands and removes the fallback dict shape entirely, at which point the lookup can move into `FieldMeta`'s build-time precomputation.
  - Low #7 trigger: a Django version change is reviewed OR the helper grows a named `_reverse_connector(parent_field)` extraction that consolidates the three connector-resolution shapes.
- DRY analysis: all three bullets remain defer-with-trigger; no in-cycle edits attempted (the dispatch prompt's scope is comment-pass-only).
- Artifact citation drift detected and not silently corrected: the artifact cited `walker.py:564` for the `_selected_scalar_names` `spec-014` citation; the actual current line is `walker.py:572` (post the `_record_relation_access` docstring expansion done in this same pass, prior line was around `walker.py:564` matching artifact). Edit was made via the grep-unique substring `(spec-014 rev6 M1 audit invariant.)` per AGENTS.md #27, not by line number; the rotation lands on the correct line regardless of the docstring-expansion offset.
- `uv.lock` unchanged (no `uv run ...` dependency-change call surface).
- Dirty paths flagged in prior pass remain dirty (TODAY.md, neighbouring optimizer modules, orders/**, etc.); none touched by this cycle per AGENTS.md #33.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
- AGENTS.md #21: "Do not update CHANGELOG.md unless explicitly instructed."
- The active review plan does not authorize a `CHANGELOG.md` edit for this cycle (the dispatch prompt explicitly framed the Medium as "Internal behavior — `_apply_hint` is private" and flagged the consumer-observable surface as a hypothetical "could surface" rather than a currently-shipped contract change). Neither the artifact nor the dispatch names an explicit changelog authorisation.
- Cycle scope is exclusively internal: (a) Medium is a no-mutation-on-raise hardening on the private helper `_apply_hint`'s `prefetch_obj` branch — the `ConfigurationError` raised by `_prefetch_hint_for_path` already bubbled out of `plan_optimizations` pre-fix and reached the same consumer call sites with the same exception type and message; the partially-mutated plan was unreachable on the failure path then and remains unreachable now (the fix protects against a hypothetical future caller catching mid-walk, not against any currently-shipped caller); (b) Low #1 is a two-site `spec-014` → `spec-018` citation rotation in internal docstrings; (c) Low #8 is a docstring expansion on the private helper `_record_relation_access` encoding the must-run-before-elision contract. None of (a), (b), (c) changes a consumer-visible surface: no public symbol added/removed, no typed-error contract changed, no behavioural change observable to a consumer running `plan_optimizations` through `DjangoOptimizerExtension`.
- Same calibration as `optimizer/field_meta.py`'s three-pass cycle (CL `Not warranted`, internal-only `RelationKind` TYPE_CHECKING relocation + docstring polish) and `optimizer/_context.py`'s consolidated cycle (CL `Not warranted`, docstring/inline-comment Lows only). The Medium here, although a bug-fix in form, is brittle-edge-case-only-reachable-by-a-hypothetical-future-caller in substance — the existing public contract (`ConfigurationError` raised, plan inaccessible) is preserved bit-for-bit.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass (213 files left unchanged)
- `uv run ruff check --fix .` — pass (All checks passed!)

---

## Iteration log
