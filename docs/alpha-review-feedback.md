# Alpha Review Feedback: O4 Nested Prefetch Chains

## Scope reviewed

- `docs/spec-optimizer_nested_prefetch_chains.md`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/hints.py`
- `django_strawberry_framework/types/resolvers.py`
- `tests/optimizer/test_walker.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_plans.py`
- `tests/types/test_resolvers.py`

## Findings

### 1. Bare `field_name` fallback in resolvers defeats branch-sensitive keys

Priority: P1

Both `_is_fk_id_elided` and `_check_n1` in `resolvers.py` contain an `or field_name in elisions` / `or field_name in planned` fallback after the branch-sensitive resolver-key check:

```python
# _is_fk_id_elided
key = resolver_key(parent_type, field_name, _runtime_path_from_info(info))
return key in elisions or field_name in elisions

# _check_n1
key = resolver_key(parent_type, field_name, _runtime_path_from_info(info))
if key in planned or field_name in planned:
    return
```

The walker now exclusively produces resolver keys (e.g. `"ItemType.category@allItems.category"`), not bare field names. The `planned` and `elisions` sets only contain these resolver keys. So `field_name in planned` / `field_name in elisions` is dead code that will never match.

The fallback is harmless today but dangerous going forward: if a future change accidentally populates a bare field name into either set, the fallback would silently match for *every* branch that uses that field name — exactly the cross-branch leak the resolver-key design exists to prevent.

Recommended fix: Remove both fallbacks. If they exist as a safety net for some transition period, gate them behind a comment with a concrete removal deadline (e.g. "Remove after O4 tests are green for one release cycle").

Relevant code:

- `django_strawberry_framework/types/resolvers.py:80-81`
- `django_strawberry_framework/types/resolvers.py:128-129`

### 2. Alias merging discards runtime-path info, breaking B2/B3 for aliased branches

Priority: P2

The spec explicitly warns: "_Because `_merge_aliased_selections` currently merges by underlying field name, O4 must either preserve the response aliases on merged nodes or record resolver keys from the original selections before merging. Do not collapse two branches into one elision key unless their selection sets are equivalent for that optimization._"

The current implementation does neither. `_merge_aliased_selections` merges two aliased selections into one node (keeping the first occurrence's alias), and the walker produces one resolver key using that first alias. At resolve time, the second alias fires its own resolver, whose `_runtime_path_from_info(info)` produces a different path (containing the second alias), so its resolver key won't match the single walker-produced key.

Example: `{ first: category { id } second: category { id } }` on an Item root. The walker merges both into one selection, elides (id-only), and stores one key like `"ItemType.category@allItems.first"`. When the `second` resolver fires, it computes `"ItemType.category@allItems.second"`, which is not in `fk_id_elisions`. The bare-name fallback (finding #1) doesn't help either since `"category"` is not in the set. The resolver falls through to `getattr(root, field_name)`, triggering a lazy load for the second alias.

This is unlikely to cause data correctness issues (Django's cache would often prevent the lazy load), and the B3 strictness false positive would be masked by `_will_lazy_load` returning `False` in most cases. But it's a contract violation the spec specifically identified.

Recommended fix: Either emit resolver keys for all original aliases before merging, or record a set of alias-equivalent keys during merge so both `first` and `second` map to the same plan entry.

Relevant code:

- `django_strawberry_framework/optimizer/walker.py:94-98` (runtime_path computation)
- `django_strawberry_framework/optimizer/walker.py:394-408` (`_merge_aliased_selections`)

### 3. Duplicate runtime-path helpers with subtle behavioral divergence

Priority: P2

Two separate implementations of the "walk `info.path`, strip int indexes, reverse" logic exist:

- `walker.py:_runtime_prefix_from_info` → `_runtime_path_from_path` (no fallback for empty paths)
- `resolvers.py:_runtime_path_from_info` (has a `field_name` fallback when path has no string keys)

The resolver version's fallback:

```python
if keys:
    return tuple(reversed(keys))
field_name = getattr(info, "field_name", None)
return (str(field_name),) if field_name else ()
```

If this fallback ever fires, the resolver-side key would be `"ParentType.field@field_name"` while the walker side would be `"ParentType.field@"` (empty path joined). They would not match.

The spec anticipated this: "_Add `_runtime_path_from_info(info)` and shared resolver-key helpers in this module or import them from a small optimizer utility if needed._"

Recommended fix: Extract one canonical implementation into a shared location (e.g. `optimizer/plans.py` alongside `resolver_key`, or a small `optimizer/paths.py`). Remove the resolver-side fallback — if `info.path` produces no string keys, something is wrong and the mismatch should surface as a test failure, not be papered over.

Relevant code:

- `django_strawberry_framework/optimizer/walker.py:354-369`
- `django_strawberry_framework/types/resolvers.py:58-70`

### 4. No depth-3 test

Priority: P2

The recursion naturally handles arbitrary depth, and the removed TODO placeholder mentioned `test_plan_emits_nested_prefetch_chain_depth_3`. The new test suite doesn't include it. A depth-3 test (e.g. `Category > items > entries > property`) would exercise that inner `Prefetch` objects correctly nest their own child `Prefetch` objects and that connector columns are injected at each boundary.

Without it, a regression that breaks only at depth 3+ (e.g. a connector-column bug when the parent field is itself inside a child queryset) could land undetected.

Recommended fix: Add `test_plan_emits_nested_prefetch_chain_depth_3` exercising `Category > items > entries > property` (all four fakeshop models). Assert the queryset nesting is three `Prefetch` objects deep and that each child queryset's `only()` includes its connector column.

### 5. `_ensure_connector_only_fields` silently swallows `None` attname

Priority: P3

The function has three branches: `one_to_many`, `not many_to_many` (forward FK / O2O downgrade), and `many_to_many`. The `one_to_many` and forward branches use double-getattr chains that can both produce `None`:

```python
if parent_field.one_to_many:
    attname = getattr(getattr(parent_field, "field", None), "attname", None) or getattr(
        parent_field, "reverse_connector_attname", None,
    )
```

When both paths return `None`, the final `if attname is not None` guard prevents a crash, but the missing connector column would cause Django to issue an extra query to fetch the FK column — silently degrading from the expected query count. This would only happen for a Django field object that is `one_to_many` but has neither `.field.attname` nor `.reverse_connector_attname` (an unusual edge case, possibly a `GenericRelation`).

Recommended fix: Add a `logger.debug` when `attname` resolves to `None` despite `plan.only_fields` being non-empty, so the missing connector surfaces in debug logs.

Relevant code:

- `django_strawberry_framework/optimizer/walker.py:332-351`

### 6. Spec-required doc updates are missing

Priority: P3

The spec's "Documentation updates when O4 ships" section requires:

- Update `docs/spec-optimizer.md` to mark O4 shipped.
- Update `docs/spec-optimizer_beyond.md` to remove the "O4 is unimplemented" riders.
- Remove remaining `TODO(spec-optimizer_nested_prefetch_chains.md O4)` anchors from source and test files.

The diff cleans up all source-level TODO anchors but does not touch `spec-optimizer.md` or `spec-optimizer_beyond.md`. These should land in the same change to keep the docs consistent with the shipped state.

### 7. `_append_unique` is O(n) per call

Priority: P3

`_append_unique` uses `if value not in values: values.append(value)`, which is O(n) per call where n is the current list length. For each relation at each depth, the walker calls `_append_unique` on `only_fields`, `planned_resolver_keys`, `fk_id_elisions`, `select_related`, and `prefetch_related`. For a schema with hundreds of fields and deep nesting, this accumulates to O(n²) per plan construction.

This is unlikely to matter for realistic schemas today but could become noticeable as the optimizer handles wider queries on larger schemas.

Recommended fix: Not urgent. If profiling ever shows this as a bottleneck, switch to a `(list, set)` pair per bag — the set for O(1) membership checks, the list for ordered output.

### 8. `plan_relation` return type annotation changed but `DjangoOptimizerExtension.plan_relation` annotation not updated

Priority: P3

The module-level `plan_relation` now returns `tuple[str, str]` (kind + reason string), but `DjangoOptimizerExtension.plan_relation` in `extension.py:454-465` still has the return annotation `tuple[str, Any]`. The docstring was updated ("Returns `("select", reason)` or `("prefetch", reason)`"), but the type annotation should match for `mypy`/`pyright` consistency.

Relevant code:

- `django_strawberry_framework/optimizer/extension.py:459`

### 9. `_plan_select_relation` parameter list is wide (11 params)

Priority: P3

`_plan_select_relation` accepts 11 positional parameters. `_plan_prefetch_relation` accepts 9. These are internal helpers, but the wide parameter lists make call sites verbose and error-prone (easy to swap `runtime_path` and `resolver_identity`, both tuples/strings). A lightweight `_WalkerContext` dataclass grouping the common parameters (`plan`, `prefix`, `full_path`, `info`, `runtime_path`, `resolver_identity`) would reduce every call site and make additions easier.

### 10. `_plan_prefetch_relation` emits string fallback that diverges from spec preference

Priority: P3

The spec says: "_Prefer `Prefetch` for uniformity with B8 diffing (which inspects `prefetch_to`)._" The implementation emits a plain string when `child_plan.is_empty and not has_custom_get_queryset`. This is functionally correct (a string and a `Prefetch` with no queryset are equivalent to Django), but it means `lookup_paths` must handle both string and `Prefetch` entries — which it already does, so no bug. However, the B8 diffing code will need to handle the mixed-type list too. Switching to always-`Prefetch` would simplify downstream consumers at the cost of one extra object allocation per trivial prefetch.

## Overall assessment

The O4 implementation is structurally sound. The core recursion — same-query `_plan_select_relation` for single-valued chains and queryset-boundary `_plan_prefetch_relation` for many-side branches — matches the spec design. The `plan_relation` refactoring to a pure classification function is clean, connector column injection via `_ensure_connector_only_fields` handles both raw Django fields and `FieldMeta` objects correctly, and cacheability propagation from nested custom `get_queryset` branches is properly wired.

Test coverage is solid: all spec-enumerated tests are present, the integration tests verify real query counts against the fakeshop seeder, and the resolver-key leak regression test is a good addition.

The P1 risk is the bare-field-name fallback in resolvers, which is dead code that obscures whether keys actually match. The P2 risks are the alias-merging gap (spec explicitly flagged this) and the duplicate runtime-path helpers (which could diverge). Neither will cause data corruption today, but both weaken the branch-sensitivity guarantees the resolver-key design was built to provide.