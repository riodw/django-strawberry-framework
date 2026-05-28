# Branch review: `build-021-filters-0_0_8` vs `main`

Scope: `.py` files under `django_strawberry_framework/` only. Comparison anchored at `origin/main` (`039c4425`) through `HEAD` (`c3ded04`). Per-file stripped diffs live in `docs/shadow/bug_hunt/diff/` (regenerated via `scripts/review_changed_python_diffs_against_head.py`).

Net shape of the change: this is the Slice-3 landing of the filters subsystem — `filters/base.py`, `filters/factories.py`, `filters/inputs.py`, `filters/sets.py` go from skeleton stubs to full implementations; `types/finalizer.py` gains the `_bind_filtersets()` phase; `types/base.py`, `types/definition.py`, `types/relay.py`, and `registry.py` get the small attachment points (`filterset_class` validated meta key, `related_target_for(...)` helper, `_SYNC_MISUSE_SENTINEL`, registry cleanup hook). Overall the wiring looks coherent and the helper/orphan handshake is well thought through. Findings below are the spots that warrant a second look before this is merged.

Severity legend:
- **[Bug]** — incorrect behavior or crash risk on a realistic input.
- **[Risk]** — fragile design, hidden coupling, or subtle edge case.
- **[Cleanup]** — dead code, naming, or doc nit.

---

## `django_strawberry_framework/filters/base.py`

### [Bug] `GlobalIDMultipleChoiceFilter.filter` crashes when `value is None`
[filters/base.py:247](django_strawberry_framework/filters/base.py:247)

```python
def filter(self, qs: Any, value: Any) -> Any:
    node_ids = [_decode_and_validate_global_id(item, self, index=idx) for idx, item in enumerate(value)]
    return super().filter(qs, node_ids)
```

`GlobalIDFilter.filter` directly above explicitly guards `if value is None: return super().filter(qs, None)`. The multi-value sibling does not. If the optional input ever resolves to `None` (e.g. when a related-filter expansion produces an `__in` filter that wasn't supplied), this raises `TypeError: 'NoneType' object is not iterable`. Mirror the `None` guard from the scalar version. Empty-list is fine — `enumerate([])` just produces `[]`, and `MultipleChoiceFilter.filter` handles `[]` correctly.

### [Risk] `ArrayFilter.filter` accepts `[]` as a real value; downstream semantics depend on lookup
[filters/base.py:79-86](django_strawberry_framework/filters/base.py:79)

```python
if value in EMPTY_VALUES and value != []:
    return qs
...
return self.get_method(qs)(**{lookup: value})
```

The carve-out is deliberate (the docstring says so), but the resulting `field__contains=[]` matches every row on Postgres `ArrayField` while `field__overlap=[]` matches none. Whatever lookup `lookup_expr` is bound to determines whether an empty list is "no constraint" or "exclude everything". Two suggestions: (1) document the contract on the class, and (2) consider rejecting `[]` for non-overlap lookups rather than silently treating it as a no-op.

### [Cleanup] `validate_range` is invoked through Django's form-validator path, but `RangeField.empty_values = [None]` makes that contract subtle
[filters/base.py:103-107](django_strawberry_framework/filters/base.py:103)

By restricting `empty_values` to `[None]`, an empty list reaches the validator and gets rejected as "needs 2 values". That's correct, but worth a one-line comment on `RangeField` so a future reader doesn't widen `empty_values` and silently turn `[]` into a pass-through.

### [Risk] `RelatedFilter.bind_filterset` swallows re-binds
[filters/base.py:319](django_strawberry_framework/filters/base.py:319)

```python
def bind_filterset(self, filterset):
    if not hasattr(self, "bound_filterset"):
        self.bound_filterset = filterset
```

If a `RelatedFilter` instance is shared across two `FilterSet` subclasses (uncommon but possible — class-level filter declarations are shared if the user reuses a module-level instance), the second binding silently no-ops. Slice 3 catches the broader "owner mismatch" case in `_bind_filterset_owner`, so this is probably a non-issue in practice; flagging only because the silent-no-op vs. raise contract is invisible at the call site.

---

## `django_strawberry_framework/filters/sets.py`

### [Bug] `_q_for_branch` re-instantiates the filterset without form validation, so a malformed nested `and`/`or`/`not` branch silently produces an empty `pk__in`
[filters/sets.py:778-791](django_strawberry_framework/filters/sets.py:778)

```python
child_data = cls._normalize_input(child_input)
child_set = cls(data=child_data, queryset=queryset, request=None)
return models.Q(pk__in=child_set.qs.values("pk"))
```

`_validate_form_or_raise` is only called once, against the top-level `filterset_instance`. Reading `child_set.qs` re-enters `filter_queryset` → `_evaluate_logic_tree` for any deeper branches, but never validates the child form. `BaseFilterSet.qs` is documented in `_validate_form_or_raise` (line 700) as silently falling through to `filter_queryset` on invalid form — meaning a bad sub-branch (e.g. wrong-typed scalar in `not.someField`) returns an empty `pk__in` set instead of surfacing the `GraphQLError`. Run `_validate_form_or_raise(child_set)` inside `_q_for_branch` so malformed nested inputs raise structurally.

### [Bug] `_normalize_input`'s `owner_definition` parameter is dead
[filters/sets.py:378-407](django_strawberry_framework/filters/sets.py:378), [filters/sets.py:836, 853](django_strawberry_framework/filters/sets.py:836)

The signature accepts `owner_definition: DjangoTypeDefinition | None = None`, and `apply_sync`/`apply_async` dutifully pass `cls._owner_definition` — but the body never references the parameter. Either wire it into the recursion (so nested branches can decode GlobalIDs against the correct expected type per `_decode_and_validate_global_id`'s expected-type-name check) or drop the parameter. The current shape suggests an unfinished plumb.

### [Bug] Permission checks recurse against the parent's input but the bare instance is wrong type for children
[filters/sets.py:660-668](django_strawberry_framework/filters/sets.py:660)

```python
for field_name, related_filter, child_input in cls._iter_active_related_branches(input_value):
    child_filterset = related_filter.filterset
    if child_filterset is not None and hasattr(child_filterset, "_run_permission_checks"):
        child_filterset._run_permission_checks(child_input, request)
    cls._invoke_permission_method(bare, field_name, request)
```

The recursive call into `child_filterset._run_permission_checks` correctly switches to the child class. The follow-up `cls._invoke_permission_method(bare, field_name, request)` then fires `check_<field_name>_permission` on the *parent's* bare instance — that's the "parent's per-branch gate" by design. Two concerns:

1. If the parent declares both `check_shelves_permission` (per-branch gate) and the child filterset also declares one, both fire. That looks intentional but is worth pinning in a docstring example so consumers don't double-charge an audit log.
2. `_iter_active_related_branches` walks `getattr(input_value, field_name, None)` for non-dict inputs. For a Strawberry input dataclass whose unset value is `strawberry.UNSET` rather than `None`, this picks up `UNSET` and treats the branch as active. Verify `_extract_branch_value` against UNSET — if a Strawberry input ever surfaces UNSET, the permission gate fires for fields the user never sent.

### [Risk] `apply()` dispatcher matches the async-misuse sentinel via substring
[filters/sets.py:879-886](django_strawberry_framework/filters/sets.py:879)

```python
if _SYNC_MISUSE_SENTINEL in str(exc):
    raise RuntimeError(...) from exc
```

The sentinel is the human-readable phrase `"get_queryset returned a coroutine in a sync resolver context"` ([types/relay.py:41](django_strawberry_framework/types/relay.py:41)). If anything ever localizes or rewrites the message text (logging integrations sometimes do), the substring check silently fails and a real async-misuse turns into the raw `RuntimeError` instead of the actionable rethrow. Tag the exception with a class marker (`exc.is_sync_misuse = True` set at the raise site, or a dedicated subclass) and dispatch on that instead.

### [Risk] `FilterSet.get_filters` uses a class-level `_is_expanding_filters` flag for reentrancy
[filters/sets.py:135-188](django_strawberry_framework/filters/sets.py:135)

`cls._is_expanding_filters = True` is set on the class before recursion and cleared in `finally`. Concurrent calls on the same class from different threads will see the same flag and the second thread's call short-circuits to `super().get_filters()` — yielding the unexpanded set. This is unlikely at runtime (expansion happens once during finalize), but could surface in test parallelism or any future async-finalize variant. A per-call local guard (e.g. a `threading.local` or a stack-passed set) would be safer; minimum, comment that expansion is single-threaded.

### [Risk] `_apply_related_constraints` requires `explicit & child_qs` on matching models
[filters/sets.py:794-819](django_strawberry_framework/filters/sets.py:794)

```python
intersected = explicit & child_qs
```

Django raises `AssertionError: Cannot combine queries on two different base models` if the user-supplied `queryset=` on the `RelatedFilter` is keyed on a different model than the target filterset's `_meta.model`. The assertion text is opaque from a GraphQL consumer's perspective. Either pre-check `explicit.model is child_qs.model` and raise a `ConfigurationError` with the filter and the two model names, or document the contract on `RelatedFilter.__init__`.

### [Cleanup] `expand_related_filter` is a metaclass classmethod but called via `cls.__class__.expand_related_filter(cls, ...)`
[filters/sets.py:165](django_strawberry_framework/filters/sets.py:165)

It does not need to be on the metaclass at all — there is no metaclass-specific state. Move it to `FilterSet` as a regular `@classmethod` (or `@staticmethod`), and the call becomes `cls.expand_related_filter(filter_name, f)`. The current shape obscures that this is just expansion, not class construction.

---

## `django_strawberry_framework/filters/inputs.py`

### [Risk] `convert_filter_to_input_annotation` mutates the filter instance
[filters/inputs.py:323-324](django_strawberry_framework/filters/inputs.py:323)

```python
if model_field is not None:
    filter_instance._model_field = model_field
```

Side effect on a filter instance during input-class construction. If `_build_input_fields` ever runs twice for the same filterset against a *different* model field (e.g. between a test setup and tear-down with the namespace cleared but the filter instance preserved on the class), the cache lies. The safer move is to thread `model_field` through the bag-building loop as a parameter so the filter stays stateless. If you keep the side effect, document it on `TypedFilter` so future maintainers know `_model_field` is the contract.

### [Risk] `clear_filter_input_namespace` walks `__subclasses__()` — does not catch garbage-collected refs
[filters/inputs.py:805-820](django_strawberry_framework/filters/inputs.py:805)

`__subclasses__()` returns only live subclasses; if a test created an ephemeral `FilterSet` subclass that was already garbage-collected, the cleanup skips it (correct behavior). But a long-running test runner that keeps refs through fixtures will accumulate filtersets across tests. Since each class carries `_expanded_filters` and `base_filters` on `__dict__`, this can blow up test memory. Probably acceptable for the framework, but worth a profiler pass if the integration tests run thousands of fixture-based filtersets.

### [Cleanup] `_pascal_case` strips non-word chars but doesn't dedupe trailing underscores
[filters/inputs.py:181-183](django_strawberry_framework/filters/inputs.py:181)

A `filterset_class.__name__` ending in `_` produces an empty segment that gets filtered, which is fine. Just worth a unit test against `__name__ == "_"` (edge case) — the helper currently returns `""`, which would then collide on `_input_type_name_for` later.

### [Cleanup] `_scalar_from_form_field` returns `str` for both `CharField` and the catch-all fallback
[filters/inputs.py:228-234](django_strawberry_framework/filters/inputs.py:228)

Two branches collapse to the same return value; the explicit `if isinstance(form_field, forms.CharField): return str` is dead. Either keep it for documentation (and add a comment) or drop it.

---

## `django_strawberry_framework/filters/factories.py`

### [Risk] `FilterArgumentsFactory.input_object_types` and `_type_filterset_registry` are class-level shared dicts
[filters/factories.py:55-62](django_strawberry_framework/filters/factories.py:55)

```python
input_object_types: dict[str, type] = {}
_type_filterset_registry: dict[str, type] = {}
```

Every `FilterArgumentsFactory` instance shares the same dicts — that's the design (deduping by input type name across the whole schema). The collision-detection in `_ensure_built` (existing_owner check) is good. Two things to verify:

1. The matching `clear_filter_input_namespace()` (in `inputs.py`) imports and clears these — confirms test-isolation works. Good.
2. The class-level annotation `dict[str, type] = {}` is a mutable class default; subclassing `FilterArgumentsFactory` (unlikely but possible) would inherit the same dict instance. Not a current concern, but pin in a docstring that subclassing is not supported.

### [Cleanup] `_dynamic_filterset_cache` key includes `model` class, fields, and `extra` tuple — but skips fields if `safe_meta` lacks the key
[filters/factories.py:158-170](django_strawberry_framework/filters/factories.py:158)

`safe_meta.get("fields")` returning `None` produces `fields_key = ("fields", None)` via the `else` branch — fine. The cache key shape is stable and deterministic. No issue, but worth a unit test that asserts two structurally-equivalent meta dicts hash to the same cache slot.

---

## `django_strawberry_framework/types/finalizer.py`

### [Bug] `_bind_filtersets`'s "wire then materialize" loop runs `get_filters()` once per wired class; ImportError gets remapped, but other exceptions do not
[types/finalizer.py around the ImportError catch](django_strawberry_framework/types/finalizer.py:209)

```python
try:
    filterset_cls.get_filters()
except ImportError as exc:
    raise ConfigurationError(...) from exc
```

Other errors raised inside `get_filters()` (e.g. a `RelatedFilter` whose `filterset` resolves via `import_string` and the imported class fails its own validation) bubble up unwrapped. That's defensible — they aren't import errors — but the error message a consumer sees during `finalize_django_types()` will be confusing if it isn't a `ConfigurationError`. Consider catching `Exception` and re-raising the original message inside a `ConfigurationError` so all finalizer failures look uniform.

### [Risk] Orphan detection runs after wiring + materialization
[types/finalizer.py final block of `_bind_filtersets`](django_strawberry_framework/types/finalizer.py:262)

If a consumer references a filterset via `filter_input_type(...)` without binding it through `Meta.filterset_class`, the orphan check raises *after* the input class has already been registered in `materialize_input_class`. Failure is loud (`ConfigurationError`), but the partial state in `_materialized_names` + `FilterArgumentsFactory.input_object_types` persists across the failure and lingers if a test re-runs `finalize_django_types()` without an intervening `registry.reset()`. Either move orphan detection to *before* materialization, or document the contract that callers must invoke `registry.reset()` on any finalize failure.

### [Cleanup] `_graphql_type_name` uses `definition.name if definition.name is not None else definition.origin.__name__`
[types/finalizer.py:60-68](django_strawberry_framework/types/finalizer.py:60)

That logic appears in three places (here, `_expected_global_id_type_name` in `filters/base.py`, and `_owner_type_name` in `filters/inputs.py`). Pull it onto `DjangoTypeDefinition` as a `graphql_type_name` property so future renames stay coherent.

---

## `django_strawberry_framework/types/definition.py`

### [Risk] `related_target_for` re-reads `model._meta.get_field(field_name)` every call
[types/definition.py around new method](django_strawberry_framework/types/definition.py:88)

Called from `_bind_filterset_owner` (per-related-filter) and `_expected_global_id_type_name` (per-filter-evaluation). The `_meta.get_field()` call is cheap but not free, and the result is stable for the lifetime of the type definition. Worth caching on `DjangoTypeDefinition` (a `functools.lru_cache`-style dict keyed by `field_name`) if profiling shows it on the hot path. Not urgent.

---

## `django_strawberry_framework/types/base.py`

### [Cleanup] `_validate_filterset_class` imports `FilterSet` inside the function — correct, but the comment is missing
[types/base.py:72-89](django_strawberry_framework/types/base.py:72)

The in-function import is to dodge the `types -> filters -> types` cycle; that's the right call, but a one-liner on why the import is local (vs. module-top) would save a future reader from "fixing" it. Same suggestion applies to the in-function import inside `DjangoTypeDefinition.related_target_for`.

---

## `django_strawberry_framework/types/relay.py`

### [Risk] `_SYNC_MISUSE_SENTINEL` is the substring matcher described in `sets.py` `apply()` above
[types/relay.py:41](django_strawberry_framework/types/relay.py:41)

Same finding as the `apply()` dispatcher above: stringly-typed dispatch. Consider a dedicated exception subclass exported from `types/relay.py` (`SyncMisuseError(RuntimeError)`) so callers can `except SyncMisuseError` instead of doing substring matching on the message.

---

## `django_strawberry_framework/registry.py`

### [Cleanup] Two near-identical try/except ImportError blocks
[registry.py:419-435](django_strawberry_framework/registry.py:419)

```python
try:
    from .filters.inputs import clear_filter_input_namespace
except ImportError:
    pass
else:
    clear_filter_input_namespace()

try:
    from .filters import _helper_referenced_filtersets
except ImportError:
    return
_helper_referenced_filtersets.clear()
```

The two blocks differ in failure mode — the first silently skips, the second returns and skips the rest of the cleanup. Pick one shape (`return`) and apply uniformly so the cleanup contract is "best-effort, abort on first ImportError" or "best-effort, skip and continue", not both. The current asymmetry is invisible at read time and would surprise the next person.

---

## Cross-cutting

- **Stringly-typed dispatch around sync/async misuse** is the highest-priority cleanup. Subclass `RuntimeError` once, raise the subclass in `_apply_get_queryset_sync`, catch the subclass in `FilterSet.apply`, and `_SYNC_MISUSE_SENTINEL` can go away. This is the same finding under `sets.py::apply` and `types/relay.py`.
- **Form validation for nested branches** (`_q_for_branch`) is the highest-priority correctness gap. Top-level `_validate_form_or_raise` doesn't cover deeper `and`/`or`/`not` levels, so malformed sub-branch inputs silently degrade rather than raising `GraphQLError`.
- **Dead `owner_definition` parameter** in `_normalize_input` either needs to be wired (so GlobalID decoding knows the expected type per branch) or removed. As-is, it's misleading.
- **`graphql_type_name` duplication** across three files invites drift; promote to a method on `DjangoTypeDefinition`.

---

Generated via `uv run python scripts/review_changed_python_diffs_against_head.py 039c44252cef807916f55b279f6c4a463a9260bf`. Stripped diffs are under `docs/shadow/bug_hunt/diff/django_strawberry_framework__*.diff`.
