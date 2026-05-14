# Review: `django_strawberry_framework/optimizer/walker.py`

Status: fix-implemented

## DRY analysis

- Existing patterns reused: `plan_optimizations` returns the shared `OptimizationPlan` from `django_strawberry_framework/optimizer/plans.py:38-116`; relation dispatch reuses `relation_kind` from `django_strawberry_framework/utils/relations.py:32-58`; field metadata is read through the cached `_optimizer_field_map` written by `django_strawberry_framework/types/base.py:90-142`; selection normalization now reuses `_included_field_selections` and `_merge_aliased_selections` in `django_strawberry_framework/optimizer/walker.py:112-115` and `django_strawberry_framework/optimizer/walker.py:367-382`.
- New helpers a fix might justify: a single hint-planning helper that first applies the shared relation-safety rules (`custom_get_queryset`, relation cardinality, and current `prefix` / `full_path`) and then dispatches to select, generated prefetch, or explicit `Prefetch` handling. It would serve `_apply_hint` in `django_strawberry_framework/optimizer/walker.py:288-356` and remove the need for hint branches to duplicate relation bookkeeping from `_plan_select_relation` / `_plan_prefetch_relation`.
- Duplication risk in the current file: relation setup is repeated across `_plan_select_relation`, `_plan_prefetch_relation`, and the explicit-prefetch hint branch (`django_strawberry_framework/optimizer/walker.py:220-234`, `django_strawberry_framework/optimizer/walker.py:258-285`, `django_strawberry_framework/optimizer/walker.py:315-326`). The drift is already visible: default dispatch consults `plan_relation` before selecting, generated prefetches use `full_path`, but hint dispatch can skip both safeguards.

## High:

### `force_select` hints can bypass target `get_queryset` visibility

The default relation path correctly downgrades a single-valued relation to `Prefetch` when the target `DjangoType` has a custom `get_queryset`, preserving row-level visibility filters. `_apply_hint` runs before that default dispatch and honors `OptimizerHint.select_related()` by calling `_plan_select_relation` directly, so a consumer can configure a force-select hint on a relation whose target type filters in `get_queryset` and the walker will emit a join instead of the filtered prefetch. That bypasses the target visibility hook for nested relation traversal and can expose related rows that the target type would otherwise hide. Recommended change: treat custom target `get_queryset` as non-overridable by `force_select` (downgrade to `_plan_prefetch_relation` or raise `ConfigurationError` during type validation), and add an end-to-end optimizer test proving a force-select hint cannot bypass a target type's `get_queryset` filter.

```django_strawberry_framework/optimizer/walker.py:54:63
if target_type is not None and target_type.has_custom_get_queryset():
    logger.debug(
        "Optimizer: will downgrade %s to Prefetch because %s overrides get_queryset.",
        field.name,
        target_type.__name__,
    )
    return ("prefetch", "custom_get_queryset")
if relation_kind(field) in ("many", "reverse_many_to_one"):
    return ("prefetch", "default")
return ("select", "default")
```

```django_strawberry_framework/optimizer/walker.py:161:178
if hint is not None and _apply_hint(
    hint,
    sel=sel,
    django_field=django_field,
    django_name=django_name,
    type_cls=type_cls,
    target_type=target_type,
    plan=plan,
    prefix=prefix,
    full_path=full_path,
    info=info,
    runtime_paths=runtime_paths,
    resolver_identities=resolver_identities,
):
    continue

relation_plan_kind, _ = plan_relation(django_field, target_type, info)
```

```django_strawberry_framework/optimizer/walker.py:328:341
if hint.force_select:
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

## Medium:

### Explicit `Prefetch` hints are not reconciled with nested `full_path`

Generated prefetches are built with the walker's current `full_path`, so a relation reached through a selected parent such as `category { items { ... } }` becomes `Prefetch("category__items", ...)` on the root queryset. The explicit `OptimizerHint.prefetch(Prefetch(...))` branch appends the consumer object unchanged, even when the walker is inside a non-empty prefix. A hint declared on `CategoryType.Meta.optimizer_hints["items"]` will naturally be relative to `Category` (`Prefetch("items", ...)`), but when reached from an `Item` root through `category`, that relative object is attached to the root `Item` queryset as `Prefetch("items", ...)` instead of `Prefetch("category__items", ...)`. If the root model has no same-named relation this can crash; if it does, it can prefetch the wrong path while still marking the nested resolver as planned. Recommended change: validate or adapt explicit `Prefetch` hints against `full_path` before appending, with coverage for a prefetch hint on a relation reached beneath a selected single-valued parent.

```django_strawberry_framework/optimizer/walker.py:315:326
if hint.prefetch_obj is not None:
    attname = getattr(django_field, "attname", None)
    if attname is not None:
        append_unique(plan.only_fields, f"{prefix}{attname}")
    append_unique_many(plan.planned_resolver_keys, resolver_identities)
    # Consumer-supplied Prefetch objects commonly close over a queryset
    # built with request- or user-scoped filters; matching the
    # has_custom_get_queryset discipline in _plan_prefetch_relation, mark
    # the plan non-cacheable so the plan cache cannot serve one
    # request's queryset to the next.
    plan.cacheable = False
    append_prefetch_unique(plan.prefetch_related, hint.prefetch_obj)
```

```django_strawberry_framework/optimizer/walker.py:269:285
child_plan = OptimizationPlan()
_walk_selections(
    sel.selections,
    django_field.related_model,
    child_plan,
    prefix="",
    info=info,
    runtime_prefixes=runtime_paths,
)
_ensure_connector_only_fields(child_plan, django_field)
_merge_child_plan_metadata(plan, child_plan)
if not child_plan.cacheable:
    plan.cacheable = False
child_queryset = child_plan.apply(
    _build_child_queryset(django_field, target_type, info, has_custom_qs=has_custom_get_queryset),
)
append_prefetch_unique(plan.prefetch_related, Prefetch(full_path, queryset=child_queryset))
```

## Low:

### Relation planning preamble is duplicated across default and hint paths

The same connector-column and planned-resolver-key setup appears in select planning, generated prefetch planning, and the explicit-prefetch hint branch. The duplication makes it easy for hint handling to drift from default relation handling: the current High and Medium findings both come from hint branches bypassing safeguards that are already present in the default path. After fixing the behavior, consider a small helper for "record relation connector and resolver keys" or a higher-level hint planner that delegates back through the default relation helpers instead of open-coding partial setup.

```django_strawberry_framework/optimizer/walker.py:220:234
attname = getattr(django_field, "attname", None)
if attname is not None:
    append_unique(plan.only_fields, f"{prefix}{attname}")
target_pk_name = _target_pk_name(django_field)
if (
    _can_elide_fk_id(django_field)
    and not (target_type is not None and target_type.has_custom_get_queryset())
    and not _has_custom_id_resolver(target_type, target_pk_name)
    and _selected_scalar_names(sel.selections, django_field.related_model) == {target_pk_name}
):
    append_unique_many(plan.fk_id_elisions, resolver_identities)
    append_unique_many(plan.planned_resolver_keys, resolver_identities)
    return
append_unique_many(plan.planned_resolver_keys, resolver_identities)
append_unique(plan.select_related, full_path)
```

```django_strawberry_framework/optimizer/walker.py:258:266
attname = getattr(django_field, "attname", None)
if attname is not None:
    append_unique(plan.only_fields, f"{prefix}{attname}")
append_unique_many(plan.planned_resolver_keys, resolver_identities)
has_custom_get_queryset = target_type is not None and target_type.has_custom_get_queryset()
if has_custom_get_queryset:
    plan.cacheable = False
if django_field.related_model is None:
    append_unique(plan.prefetch_related, full_path)
```

## What looks solid

- The static helper was run for this optimizer file: `python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/review/shadow --stdout`.
- The accepted `rev-optimizer__plans` change is reflected in `django_strawberry_framework/optimizer/walker.py:481-506`: included fragments are flattened before alias/relation merging, so duplicate generated relation branches are combined before child `Prefetch` querysets are built.
- FK-id elision has clear guardrails for custom target querysets, custom target id resolvers, non-PK `to_field`, and composite primary keys in `django_strawberry_framework/optimizer/walker.py:223-231` and `django_strawberry_framework/optimizer/walker.py:385-415`.
- The walker finalizes plans at the public handoff in `django_strawberry_framework/optimizer/walker.py:41-45`, preserving the immutable-after-cache invariant established in `OptimizationPlan`.

### Summary

`walker.py` is structurally coherent after the fragment-normalization fix, and the main default relation paths line up with the documented optimizer behavior. The remaining risk is concentrated in hint handling: `force_select` can step around the `get_queryset` visibility downgrade, and explicit `Prefetch` hints do not account for nested traversal prefixes. Both issues point to the same DRY concern: hint dispatch should reuse the default relation safety rules instead of duplicating only part of relation planning.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/optimizer/walker.py` — centralized shared relation connector/resolver-key recording, made `force_select` downgrade to generated `Prefetch` when the target type has custom `get_queryset`, and adapted explicit `OptimizerHint.prefetch(Prefetch(...))` lookups from type-relative paths to the current nested `full_path`.
- `django_strawberry_framework/optimizer/_context.py` — broadened the mapping-write read-only context catch from `TypeError` to `TypeError` plus `AttributeError` so immutable `dict` subclasses such as Django `QueryDict` do not abort optimizer-plan stashing.
- `tests/optimizer/test_walker.py` — added walker-level regressions for nested explicit `Prefetch` hint path adaptation and `force_select` downgrade when the target type filters through `get_queryset`.
- `tests/optimizer/test_extension.py` — added end-to-end schema execution coverage proving a `force_select` hint still routes through the target type's filtered `get_queryset` path, plus immutable dict-subclass context coverage for the `_context.py` change.

### Tests added or updated

- `tests/optimizer/test_walker.py::test_plan_prefetch_obj_hint_adapts_nested_selected_parent_prefix` — pins that `Prefetch("items", ...)` declared on `CategoryType.items` becomes `Prefetch("category__items", ...)` when reached under `Item.category`.
- `tests/optimizer/test_walker.py::test_plan_force_select_hint_downgrades_for_custom_target_get_queryset` — pins that `OptimizerHint.select_related()` cannot override a target type with custom `get_queryset`.
- `tests/optimizer/test_extension.py::test_optimizer_hint_force_select_does_not_bypass_custom_get_queryset` — executes a real Strawberry schema with `DjangoOptimizerExtension` and verifies the forced-select hint produces a filtered `Prefetch`, not `select_related`.
- `tests/optimizer/test_extension.py::test_stash_on_immutable_dict_subclass_is_silent` — pins that `AttributeError` from an immutable `dict` subclass mapping write is treated as a read-only stash failure, matching the `_context.py` contract.

### Validation run

- `python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --strip-docstrings --output-dir docs/review/shadow` — passed; wrote `docs/review/shadow/django_strawberry_framework__optimizer__walker.stripped.py` and `.overview.md`.
- `uv run pytest tests/optimizer/test_walker.py::test_plan_prefetch_obj_hint_adapts_nested_selected_parent_prefix tests/optimizer/test_walker.py::test_plan_force_select_hint_downgrades_for_custom_target_get_queryset tests/optimizer/test_extension.py::test_optimizer_hint_force_select_does_not_bypass_custom_get_queryset --no-cov` — passed, 3 tests.
- `uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_extension.py --no-cov` — passed, 165 tests.
- `uv run ruff format .` — failed only on unrelated generated scratch files under `docs/review/new/*.stripped.py` with invalid placeholder syntax; 100 files left unchanged.
- `uv run ruff check --fix .` — failed only on unrelated generated scratch files under `docs/review/new/`.
- `uv run ruff format django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py` — passed, 3 files unchanged.
- `uv run ruff check django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py` — passed.
- `uv run ruff check --fix django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py` — passed.

### Notes for Worker 3

- Shadow helper output was used during implementation; cite original source line numbers, not shadow line numbers.
- High addressed by making custom target `get_queryset` non-overridable by `force_select`; the hint now takes the same generated-prefetch path as default planning in that case.
- Medium addressed by adapting explicit `Prefetch` hint lookups when the hint's lookup is relative to the hinted relation, while preserving root-level hints unchanged.
- Low/DRY addressed with `_record_relation_access` for the shared connector-column and planned-resolver-key setup used by select, generated prefetch, and explicit-prefetch hint handling.
- `CHANGELOG.md` was not edited; changelog disposition is intentionally left for the post-comment verification pass.

---

## Verification (Worker 3)

### Logic verification outcome

- High accepted: `force_select` hints now call `_plan_prefetch_relation` when `_target_has_custom_get_queryset(target_type)` is true, so the target type's `get_queryset` filter is applied through `_build_child_queryset`, the plan becomes non-cacheable, and no `select_related` join bypasses the visibility hook.
- Medium accepted: explicit `OptimizerHint.prefetch(Prefetch(...))` hints now pass through `_prefetch_hint_for_path`, which keeps already-rooted lookups unchanged, adapts type-relative lookups to the current `full_path`, preserves the supplied queryset and `to_attr` when rebuilding, and raises `ConfigurationError` for a lookup that does not target the hinted relation.
- Low accepted for logic: `_record_relation_access` centralizes the shared connector-column and resolver-key bookkeeping for select, generated prefetch, and explicit-prefetch hint paths.
- Additional actual diff accepted for logic: `django_strawberry_framework/optimizer/_context.py` now catches `AttributeError` from mapping writes as well as `TypeError`, which is justified for immutable Django `QueryDict`-style `dict` subclasses and is pinned by `tests/optimizer/test_extension.py::test_stash_on_immutable_dict_subclass_is_silent`.
- Artifact/report blocker for the next Worker 2 pass: Worker 2's changed-path report omits the actual `_context.py` source change and the related `test_stash_on_immutable_dict_subclass_is_silent` test. Record those in the artifact before final verification.

### DRY findings disposition

- Accepted: the duplicated relation connector/resolver-key setup is now behind `_record_relation_access`.
- Accepted: custom-`get_queryset` checks now flow through `_target_has_custom_get_queryset`, reducing repeated `target_type is not None and ...` branches.
- Carried forward as acceptable for this slice: hint dispatch still branches by hint shape, but the corrected branches now reuse the same relation planning helpers for generated select/prefetch behavior.

### Temp test verification

- No temp tests used.
- Permanent coverage verified:
  - `tests/optimizer/test_walker.py::test_plan_prefetch_obj_hint_adapts_nested_selected_parent_prefix`
  - `tests/optimizer/test_walker.py::test_plan_force_select_hint_downgrades_for_custom_target_get_queryset`
  - `tests/optimizer/test_extension.py::test_optimizer_hint_force_select_does_not_bypass_custom_get_queryset`
  - `tests/optimizer/test_extension.py::test_stash_on_immutable_dict_subclass_is_silent`

### Validation run

- `uv run pytest tests/optimizer/test_walker.py::test_plan_prefetch_obj_hint_adapts_nested_selected_parent_prefix tests/optimizer/test_walker.py::test_plan_force_select_hint_downgrades_for_custom_target_get_queryset tests/optimizer/test_extension.py::test_optimizer_hint_force_select_does_not_bypass_custom_get_queryset tests/optimizer/test_extension.py::test_stash_on_immutable_dict_subclass_is_silent --no-cov` — passed, 4 tests.
- `uv run ruff format --check django_strawberry_framework/optimizer/walker.py django_strawberry_framework/optimizer/_context.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py` — passed.
- `uv run ruff check django_strawberry_framework/optimizer/walker.py django_strawberry_framework/optimizer/_context.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py` — passed.

### Comment/docstring notes for Worker 2

- `tests/optimizer/test_extension.py::test_stash_does_not_swallow_unexpected_exceptions_from_setitem` still says the dict fallback is narrowed to `TypeError`; that is stale after the accepted `_context.py` change because `AttributeError` is now intentionally swallowed for immutable `dict` subclasses.
- Complete the comment/docstring pass for all actually touched files, including `django_strawberry_framework/optimizer/_context.py`, `django_strawberry_framework/optimizer/walker.py`, `tests/optimizer/test_walker.py`, and `tests/optimizer/test_extension.py`.

### Verification outcome

logic accepted; awaiting comment pass

---

## Comment/docstring pass

### Files touched

- `tests/optimizer/test_extension.py` — updated stale stash-test docstrings so they describe the accepted dict-first dispatch and mapping-write exception policy (`TypeError` and `AttributeError` are read-only context failures; unrelated custom exceptions still surface).

### Review result

- `django_strawberry_framework/optimizer/walker.py` comments/docstrings already describe the accepted helper behavior for `_record_relation_access`, generated prefetch child querysets, type-relative `Prefetch` adaptation, and fragment inlining; no source comment changes needed.
- `django_strawberry_framework/optimizer/_context.py` comments/docstrings already describe the accepted `AttributeError` handling for immutable `dict` subclasses; no source comment changes needed.
- `tests/optimizer/test_walker.py` test docstrings already describe the final walker behavior; no changes needed.
- Top-level `Status:` remains `fix-implemented`.

### Validation run

- `uv run ruff format django_strawberry_framework/optimizer/walker.py django_strawberry_framework/optimizer/_context.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py` — passed, 4 files unchanged.
- `uv run ruff check django_strawberry_framework/optimizer/walker.py django_strawberry_framework/optimizer/_context.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py` — passed.

---

## Changelog disposition

Worker 2 records changelog handling here after comment verification.

---

## Iteration log

Each Worker 2 re-pass appends a `## Fix report (Worker 2, pass <N>)` section here. Each Worker 3 re-verification appends a `## Verification (Worker 3, pass <N>)` section here. Do not edit prior entries; append.
