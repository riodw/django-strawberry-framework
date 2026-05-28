# Branch review — round 2: `build-021-filters-0_0_8` vs `main`

Scope: `.py` files under `django_strawberry_framework/` only. Anchored at `origin/main` (`039c4425`) through `HEAD` (`860d0129`). Per-file stripped diffs regenerated via `uv run python scripts/review_changed_python_diffs_against_head.py 039c4425…`; outputs live under `docs/shadow/bug_hunt/diff/`.

This pass compares against the first round of feedback (now overwritten). Below: (1) what landed, (2) one new bug introduced by the UNSET work, (3) outstanding items carried forward.

Severity legend:
- **[Bug]** — incorrect behavior or crash risk on a realistic input.
- **[Risk]** — fragile design, hidden coupling, or subtle edge case.
- **[Cleanup]** — dead code, naming, or doc nit.

---

## What was addressed since round 1

| Round-1 finding | Status | Where |
| --- | --- | --- |
| `_q_for_branch` skipped `_validate_form_or_raise` → malformed nested branches silently produced empty `pk__in` | **Fixed** | [filters/sets.py:807](django_strawberry_framework/filters/sets.py:807) |
| `_normalize_input(owner_definition=…)` dead parameter | **Fixed** | [filters/sets.py:380](django_strawberry_framework/filters/sets.py:380) — parameter removed, docstring explains GlobalID validation lives on the filter side |
| `_iter_active_related_branches` / `_extract_branch_value` treated `strawberry.UNSET` as active | **Fixed (partial — see new bug below)** | [filters/sets.py:577](django_strawberry_framework/filters/sets.py:577), [filters/sets.py:432](django_strawberry_framework/filters/sets.py:432) |
| `_bind_filtersets` only remapped `ImportError`; other exceptions leaked through as their raw class | **Fixed** | [types/finalizer.py:463-475](django_strawberry_framework/types/finalizer.py:463) — `except ConfigurationError: raise` + `except Exception` rewrap |
| `_SYNC_MISUSE_SENTINEL` defined separately at the raise site and the catch site | **Partially fixed** | [types/relay.py:41](django_strawberry_framework/types/relay.py:41) — single constant now lives in `types/relay.py` and the raise site interpolates it. The dispatch is still a substring match (see outstanding `[Risk]` below). |

Nice work on threading the form-validation guard through `_q_for_branch` and on the uniform-`ConfigurationError` shape at finalize. Both were the kind of correctness gaps that would have leaked into production as opaque failures.

---

## New finding (introduced by the UNSET patch)

### [Bug] Operator-bag inner loop in `_normalize_input` skips `None` but **not** `UNSET`
[filters/sets.py:447-449](django_strawberry_framework/filters/sets.py:447)

```python
for lookup_attr, lookup_value in bag_items:
    if lookup_value is None:
        continue
```

The outer loop (line 428) was updated to `if raw_value is None or raw_value is UNSET: continue`, but the inner operator-bag loop two scopes down still only checks `None`. Combined with the fact that `normalize_input_value` ([filters/inputs.py:372](django_strawberry_framework/filters/inputs.py:372)) also only short-circuits on `None`, every UNSET inside an operator bag now leaks into `normalize_input_value`:

- For `ListFilter` / `ArrayFilter` / `GlobalIDMultipleChoiceFilter` → `[_decode_global_id(item) for item in UNSET]` raises `TypeError: argument of type 'UNSET' is not iterable`.
- For scalar filters (`ChoiceFilter`, default branch) → `_unwrap_enum_member(UNSET)` returns the UNSET sentinel; that sentinel then lands in `data[form_key]` and the underlying Django form validates an UNSET-shaped value.
- For `RangeFilter` → `getattr(UNSET, "start", None)` produces `{base_0: None, base_1: None}` which silently widens the range to "no constraint" without surfacing the misuse.

Concrete repro shape:

```graphql
filter: {
  title: { exact: null, icontains: "foo" }  # `exact` omitted (UNSET) is the common case
}
```

A Strawberry input dataclass renders unsupplied fields as `UNSET`, so any consumer who supplies *some* but not *all* lookups in an operator bag will trigger this. It is the common case, not an edge case.

**Fix shape (pick one — both is fine):**
1. Mirror the outer-loop guard inside the bag loop: `if lookup_value is None or lookup_value is UNSET: continue`.
2. Centralize the check at the entry to `normalize_input_value` — `if raw_value is None or raw_value is UNSET: return None`. This is the more defensible spot since every future caller benefits and `_q_for_branch`/`_evaluate_logic_tree` recursion through `_normalize_input` then can't reintroduce the gap.

Recommend doing both — outer skip avoids constructing an empty form key, inner short-circuit defends every other call site.

---

## Outstanding from round 1 (still open)

### `django_strawberry_framework/filters/base.py`

#### [Bug] `GlobalIDMultipleChoiceFilter.filter` crashes when `value is None`
[filters/base.py:247-250](django_strawberry_framework/filters/base.py:247)

```python
def filter(self, qs: Any, value: Any) -> Any:
    node_ids = [_decode_and_validate_global_id(item, self, index=idx) for idx, item in enumerate(value)]
    return super().filter(qs, node_ids)
```

`GlobalIDFilter.filter` directly above guards `if value is None: return super().filter(qs, None)`. The multi-value sibling does not. If the optional input ever resolves to `None` (e.g. a related-filter expansion produces an `__in` filter that wasn't supplied), this raises `TypeError: 'NoneType' object is not iterable`. Mirror the `None` guard from the scalar version. Empty list is fine.

#### [Risk] `ArrayFilter.filter` accepts `[]` as a real value; downstream semantics depend on the lookup
[filters/base.py:79-86](django_strawberry_framework/filters/base.py:79)

The `value in EMPTY_VALUES and value != []` carve-out is deliberate, but `field__contains=[]` matches every row on Postgres `ArrayField` while `field__overlap=[]` matches none. Either reject `[]` for non-overlap lookups, or pin the contract in the class docstring so consumers don't get surprised.

#### [Risk] `RelatedFilter.bind_filterset` silently swallows re-binds
[filters/base.py:319-323](django_strawberry_framework/filters/base.py:319)

```python
def bind_filterset(self, filterset):
    if not hasattr(self, "bound_filterset"):
        self.bound_filterset = filterset
```

If a `RelatedFilter` instance is shared across two `FilterSet` subclasses (rare but possible — module-level filter instances are class-shared), the second binding silently no-ops. `_bind_filterset_owner` catches the broader "owner mismatch" case at finalize, so this is mostly defense-in-depth; the silent-no-op contract is just invisible at the call site. Either raise on mismatch or document.

#### [Risk] `convert_filter_to_input_annotation` mutates the filter instance
[filters/inputs.py:323-324](django_strawberry_framework/filters/inputs.py:323)

```python
if model_field is not None:
    filter_instance._model_field = model_field
```

Side effect on a filter during input-class construction. Thread `model_field` through the call chain as a parameter, or pin `_model_field` on `TypedFilter` as the documented contract.

#### [Cleanup] `_scalar_from_form_field` has a dead `CharField` branch
[filters/inputs.py:228-234](django_strawberry_framework/filters/inputs.py:228)

The explicit `if isinstance(form_field, forms.CharField): return str` collapses to the same value as the catch-all `return str`. Either keep with a comment ("explicit for readability") or drop.

#### [Cleanup] `_pascal_case` returns `""` for `__name__ == "_"`
[filters/inputs.py:181-183](django_strawberry_framework/filters/inputs.py:181)

Edge case — would later collide on `_input_type_name_for`. Add a unit test or guard.

---

### `django_strawberry_framework/filters/sets.py`

#### [Risk] `apply()` dispatcher still substring-matches `_SYNC_MISUSE_SENTINEL`
[filters/sets.py:879-886](django_strawberry_framework/filters/sets.py:879)

```python
if _SYNC_MISUSE_SENTINEL in str(exc):
    raise RuntimeError(...) from exc
```

The constant now lives in one place ([types/relay.py:41](django_strawberry_framework/types/relay.py:41)) — that's an improvement. But the dispatch is still "substring-of-the-exception-message," which breaks if anything ever wraps or localizes the message. Subclass `RuntimeError` once (`SyncMisuseError`), raise that subclass at `_apply_get_queryset_sync`, catch the subclass at `apply()`, and the sentinel constant goes away. Same finding applies to `types/relay.py`.

#### [Risk] Permission checks recurse via the parent's bare instance for the per-branch gate
[filters/sets.py:660-668](django_strawberry_framework/filters/sets.py:660)

```python
for field_name, related_filter, child_input in cls._iter_active_related_branches(input_value):
    child_filterset = related_filter.filterset
    if child_filterset is not None and hasattr(child_filterset, "_run_permission_checks"):
        child_filterset._run_permission_checks(child_input, request)
    cls._invoke_permission_method(bare, field_name, request)
```

The double dispatch (child's `_run_permission_checks` + parent's per-branch `check_<field>_permission`) is by design. Worth a docstring example pinning the contract so consumers don't double-charge an audit log. (The UNSET fix on `_extract_branch_value` is the right defense against firing gates on unsent branches.)

#### [Risk] `_apply_related_constraints` does `explicit & child_qs` with no model-match check
[filters/sets.py:794-819](django_strawberry_framework/filters/sets.py:794)

```python
intersected = explicit & child_qs
```

Django raises `AssertionError: Cannot combine queries on two different base models` if the consumer-supplied `queryset=` on the `RelatedFilter` is keyed on a different model than the target filterset's `_meta.model`. The assertion text is opaque from a GraphQL consumer's perspective. Pre-check `explicit.model is child_qs.model` and raise a `ConfigurationError` with both model names, or pin the contract on `RelatedFilter.__init__`.

#### [Risk] `FilterSet.get_filters` uses a class-level `_is_expanding_filters` flag for reentrancy
[filters/sets.py:135-188](django_strawberry_framework/filters/sets.py:135)

Concurrent calls on the same class from different threads will see the same flag and the second thread short-circuits to `super().get_filters()`. Unlikely to bite at runtime (expansion happens during finalize) but could surface in parallel test runs. Either use a `threading.local` / stack-passed set, or pin the single-threaded contract in a docstring.

#### [Cleanup] `expand_related_filter` is a metaclass classmethod but has no metaclass state
[filters/sets.py:165](django_strawberry_framework/filters/sets.py:165)

Called as `cls.__class__.expand_related_filter(cls, filter_name, f)`. Move it onto `FilterSet` as a regular `@classmethod` / `@staticmethod` so the call site becomes `cls.expand_related_filter(filter_name, f)`. The current shape obscures that this is just expansion, not class construction.

---

### `django_strawberry_framework/filters/factories.py`

#### [Risk] `FilterArgumentsFactory.input_object_types` and `_type_filterset_registry` are class-level shared dicts
[filters/factories.py:55-62](django_strawberry_framework/filters/factories.py:55)

The collision-detection in `_ensure_built` catches the "two filtersets fighting for the same input-type name" case, and `clear_filter_input_namespace()` clears them — both good. Two follow-ups: (1) document that subclassing `FilterArgumentsFactory` is not supported (subclasses would inherit the same dict instance); (2) a unit test that asserts two structurally-equivalent meta dicts hash to the same `_dynamic_filterset_cache` slot.

---

### `django_strawberry_framework/filters/inputs.py`

#### [Risk] `clear_filter_input_namespace` walks `__subclasses__()`
[filters/inputs.py:805-820](django_strawberry_framework/filters/inputs.py:805)

Correct behavior for live classes, but a long-running test runner that keeps fixture refs accumulates filtersets across tests. Each carries `_expanded_filters` and `base_filters` on `__dict__`. Probably acceptable; worth a profiler pass if integration tests run thousands of fixture-based filtersets.

---

### `django_strawberry_framework/types/finalizer.py`

#### [Risk] Orphan detection runs after wiring + materialization
[types/finalizer.py final block of `_bind_filtersets`](django_strawberry_framework/types/finalizer.py:262)

If a consumer references a filterset via `filter_input_type(...)` without binding it through `Meta.filterset_class`, the orphan check raises *after* the input class has already been registered in `materialize_input_class`. Failure is loud (`ConfigurationError`), but partial state in `_materialized_names` + `FilterArgumentsFactory.input_object_types` persists across the failure. Either move orphan detection to *before* materialization, or document the contract that callers must invoke `registry.reset()` on any finalize failure.

#### [Cleanup] `_graphql_type_name` duplicates the same logic that lives in `filters/base.py` and `filters/inputs.py`
[types/finalizer.py:60-68](django_strawberry_framework/types/finalizer.py:60)

```python
return definition.name if definition.name is not None else definition.origin.__name__
```

Same shape appears in `_expected_global_id_type_name` ([filters/base.py:166-172](django_strawberry_framework/filters/base.py:166)) and `_owner_type_name` ([filters/inputs.py](django_strawberry_framework/filters/inputs.py)). Pull onto `DjangoTypeDefinition` as a `graphql_type_name` property so future renames stay coherent.

---

### `django_strawberry_framework/types/definition.py`

#### [Risk] `related_target_for` re-reads `model._meta.get_field(field_name)` every call
[types/definition.py](django_strawberry_framework/types/definition.py:88)

Called from `_bind_filterset_owner` (per related filter) and `_expected_global_id_type_name` (per filter evaluation). `_meta.get_field()` is cheap but not free; result is stable for the lifetime of the type definition. Cache on `DjangoTypeDefinition` (a dict keyed by field name) if profiling shows it on the hot path. Not urgent.

---

### `django_strawberry_framework/types/base.py`

#### [Cleanup] `_validate_filterset_class` imports `FilterSet` inside the function — the *why* should be a comment
[types/base.py:72-89](django_strawberry_framework/types/base.py:72)

The in-function import dodges the `types → filters → types` cycle. Add a one-liner so a future reader doesn't "fix" it. Same suggestion applies to the in-function import inside `DjangoTypeDefinition.related_target_for`.

---

### `django_strawberry_framework/types/relay.py`

#### [Risk] `_SYNC_MISUSE_SENTINEL` is the substring matcher described under `filters/sets.py::apply` above
[types/relay.py:41](django_strawberry_framework/types/relay.py:41)

Same finding — single constant is a win over round 1, but the dispatch is still stringly typed. The structural fix is a `SyncMisuseError(RuntimeError)` subclass exported from this module.

---

### `django_strawberry_framework/registry.py`

#### [Cleanup] Two near-identical try/except ImportError blocks have asymmetric failure modes
[registry.py:419-435](django_strawberry_framework/registry.py:419)

The first block silently `pass`-es on ImportError and continues; the second `return`-s and skips the rest of the cleanup. Pick one shape uniformly so the "best-effort cleanup" contract is legible.

---

## Cross-cutting recap

Two structural threads remain after the round-1 fixes:

1. **Stringly-typed dispatch around sync/async misuse.** The single-constant refactor consolidated the source of truth, but the catch site still does `if _SYNC_MISUSE_SENTINEL in str(exc)`. Subclass `RuntimeError` once and the substring matching goes away. (Affects `filters/sets.py::apply` and `types/relay.py`.)

2. **`graphql_type_name` resolution duplicated in three files** invites drift across future renames. Promote to a method on `DjangoTypeDefinition`. (Affects `types/finalizer.py`, `filters/base.py`, `filters/inputs.py`.)

And the immediate fix to ship before merging:

3. **UNSET in operator bags.** [filters/sets.py:447-449](django_strawberry_framework/filters/sets.py:447) + [filters/inputs.py:372](django_strawberry_framework/filters/inputs.py:372). Two-line patch (mirror the outer guard inside the bag loop; short-circuit `normalize_input_value` on UNSET). This is a real runtime crash on the common case of a partially-filled operator bag.

---

Generated via `uv run python scripts/review_changed_python_diffs_against_head.py 039c44252cef807916f55b279f6c4a463a9260bf`. Per-file stripped diffs at `docs/shadow/bug_hunt/diff/django_strawberry_framework__*.diff`.
