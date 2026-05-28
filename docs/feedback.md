# Branch review — round 4: `build-021-filters-0_0_8` vs `main`

Scope: `.py` files under `django_strawberry_framework/` only. Anchored at `origin/main` (`039c4425`) through `HEAD` (`bab59cd1`). Per-file stripped diffs regenerated via `uv run python scripts/review_changed_python_diffs_against_head.py 039c4425…`; outputs live under `docs/shadow/bug_hunt/diff/`.

This pass compares against round 3 (now overwritten). **The round-3 list is essentially cleared.** The critical UNSET-in-operator-bag bug landed in the cleanest possible shape (outer guard + inner guard + defensive entry point in `normalize_input_value`), the `SyncMisuseError` loop is closed end-to-end, the `graphql_type_name` dedup is complete across all three call sites, and a half-dozen other risk and cleanup items got real treatment. Round 4 raises a small set of follow-up observations on the round-3 changes themselves — none rise to "blocker" — and notes one unit-test nit that has now been carried across three reviews.

Severity legend:
- **[Bug]** — incorrect behavior or crash risk on a realistic input.
- **[Risk]** — fragile design, hidden coupling, or subtle edge case.
- **[Cleanup]** — dead code, naming, or doc nit.

---

## What was addressed since round 3

| Round-3 finding | Status | Where |
| --- | --- | --- |
| **UNSET in operator-bag inner loop** (round 3's critical item, carried from round 2) | **Fixed** | [filters/sets.py:464-473](django_strawberry_framework/filters/sets.py:464) — inner-loop guard mirrors the outer one; outer guard also handles top-level UNSET at [filters/sets.py:418](django_strawberry_framework/filters/sets.py:418) |
| **`normalize_input_value` UNSET handling** (defensive entry point) | **Fixed** | [filters/inputs.py:393-401](django_strawberry_framework/filters/inputs.py:393) — every future caller, including the `_q_for_branch` recursion, inherits the protection |
| **`SyncMisuseError` catch site still substring-matched** | **Fixed** | [filters/sets.py:975-980](django_strawberry_framework/filters/sets.py:975) — typed `except SyncMisuseError` dispatch; `_SYNC_MISUSE_SENTINEL` deleted entirely |
| **`SyncMisuseError` needed a public export** | **Fixed** | [django_strawberry_framework/__init__.py:24](django_strawberry_framework/__init__.py:24) + [types/__init__.py:27](django_strawberry_framework/types/__init__.py:27) — consumers can catch the typed class without reaching into private `types.relay` |
| **`_owner_type_name` still duplicated `graphql_type_name`** | **Fixed** | [filters/inputs.py:483-491](django_strawberry_framework/filters/inputs.py:483) — delegates to `DjangoTypeDefinition.graphql_type_name`; all three call sites share the rule |
| `convert_filter_to_input_annotation` mutated filter via `_model_field` | **Fixed** | [filters/inputs.py:280-302](django_strawberry_framework/filters/inputs.py:280) — `model_field` threaded as a parameter through `_choice_enum_from_filter`; the side-effect write at the converter is gone |
| `_apply_related_constraints` had no model-match check | **Fixed** | [filters/sets.py:892-910](django_strawberry_framework/filters/sets.py:892) — typed `ConfigurationError` names the filter and both model classes |
| `expand_related_filter` lived on the metaclass without metaclass state | **Fixed** | [filters/sets.py:81-103](django_strawberry_framework/filters/sets.py:81) — moved to module-scope `_expand_related_filter`; call site reads cleanly |
| `related_target_for` re-read `_meta.get_field` on every call | **Fixed** | [types/definition.py:88-97](django_strawberry_framework/types/definition.py:88) + [types/definition.py:143-178](django_strawberry_framework/types/definition.py:143) — per-instance cache via `field(default_factory=dict)`, gated on `registry.is_finalized()` |
| `FilterSet.get_filters` single-threaded contract was undocumented | **Documented** | [filters/sets.py:154-168](django_strawberry_framework/filters/sets.py:154) — explicit "do not introduce `threading.local` without a real consumer path" warning |
| Permission-check double-dispatch (parent-branch + child-class gates) was undocumented | **Documented** | [filters/sets.py:691-703](django_strawberry_framework/filters/sets.py:691) — explicit "audit-log warning" call-out |
| `_pascal_case` silently returned `""` for `"_"` / `""` / `"__"` | **Fixed** | [filters/inputs.py:158-176](django_strawberry_framework/filters/inputs.py:158) — raises `ConfigurationError` at the source instead of leaking through to a downstream naming collision |
| `_scalar_from_form_field` dead `CharField` branch | **Documented** | [filters/inputs.py:221-225](django_strawberry_framework/filters/inputs.py:221) — kept with an explanatory comment so a future reader doesn't strip it as dead code |
| `_iter_filterset_subclasses` `__subclasses__()` traversal trade-off | **Documented** | [filters/inputs.py:826-840](django_strawberry_framework/filters/inputs.py:826) — long-running-test profiling note |

Beyond the round-3 list, the same commit also added two real semantic improvements worth pinning explicitly:

- **`_run_permission_checks` now recurses into `and` / `or` / `not` branches** ([filters/sets.py:725-738](django_strawberry_framework/filters/sets.py:725)). Previously a `check_<field>_permission` gate fired only if the field appeared at the top level of the input. Now it also fires for fields nested under logical operators. The right semantic — permission gates should govern any active filter regardless of how it's logically composed.
- **`_q_for_branch` propagates `request` to nested filterset instances** ([filters/sets.py:855-861](django_strawberry_framework/filters/sets.py:855)). Previously hardcoded `request=None`, which meant any `method=` filter that reads the request silently lost it inside logical branches. Now the request threads through `_evaluate_logic_tree` → `_q_for_branch` → child constructor.

---

## New observations on the round-4 changes

These are follow-ups to the new code, not blockers.

### [Risk] `_run_permission_checks` may fire the same gate multiple times inside an `or` branch
[filters/sets.py:725-738](django_strawberry_framework/filters/sets.py:725)

The recursion into logical branches is correct, but the same field appearing in multiple branches now fires its `check_<field>_permission` once per occurrence. Concretely:

```graphql
filter: {
  or: [
    { title: { icontains: "foo" } },
    { title: { icontains: "bar" } }
  ]
}
```

`check_title_permission(request)` fires twice — once for each `or` arm. The check itself is idempotent (it either raises or doesn't), so this is functionally harmless — but consumers who log from inside the gate get two audit entries for one logically-coherent filter. The existing double-dispatch docstring at [filters/sets.py:691-703](django_strawberry_framework/filters/sets.py:691) covers the parent-branch + child-class double-fire but not this logical-branch case. Either extend that docstring to cover all three double-fire shapes, or dedupe by collecting fired `(method_name)` keys in a `set` for the duration of the top-level call.

### [Risk] `_apply_related_constraints` model-match check uses `is`, which trips on proxies and multi-table inheritance
[filters/sets.py:892-910](django_strawberry_framework/filters/sets.py:892)

```python
if explicit.model is not child_qs.model:
    raise ConfigurationError(...)
```

If the consumer supplies a `RelatedFilter(queryset=ProxyModel.objects.all())` and the target filterset is keyed on the concrete model (or vice versa), they share a database table and `&` would actually work — but `is` rejects them. Same hazard for multi-table inheritance where a parent and child model can be `.filter(...)`-combined under specific conditions. Either:

- Replace `is` with a check via `_meta.concrete_model` so proxies of the same table compare equal: `explicit.model._meta.concrete_model is not child_qs.model._meta.concrete_model`.
- Or keep `is` and document the proxy/MTI carve-out in the `RelatedFilter` docstring with the suggested workaround ("pass an explicit queryset of the target's concrete model class").

### [Risk] `_q_for_branch` request propagation is a behavioral change worth pinning
[filters/sets.py:855-861](django_strawberry_framework/filters/sets.py:855)

Previously hardcoded `request=None`; now propagates the real request. The new shape is correct, but any consumer who happened to depend on the old "request is `None` inside logical branches" behavior (e.g., a `method=` filter that branches on `request is None` to mean "I'm in a sub-branch") would see a different code path. Probably no real consumer does that, but worth a CHANGELOG line so the behavioral change is discoverable.

### [Risk] `_pascal_case` now raises where it used to silently return `""`
[filters/inputs.py:158-176](django_strawberry_framework/filters/inputs.py:158)

A pre-existing FilterSet class whose `__name__` is `"_"` (synthetic test fixtures, single-underscore module-private classes, very-unusual generated names) used to produce a downstream naming collision; it now raises `ConfigurationError` at the source. That's the right call. Worth a one-line CHANGELOG note since the surface error class did change for the same input.

### [Cleanup] `_run_permission_checks` has no recursion-depth guard
[filters/sets.py:725-738](django_strawberry_framework/filters/sets.py:725)

A maliciously-deep input like `and: [{and: [{and: [...]}]}]` could blow the stack. Probably not a real concern (consumer-driven graphs are typically shallow), but every level allocates a fresh `bare = object.__new__(cls)`. If you want defense in depth against pathological inputs, cap the recursion at e.g. `sys.getrecursionlimit() // 4` or a hard `MAX_LOGIC_DEPTH = 8` with a clear `ConfigurationError`. Same caveat applies to `_evaluate_logic_tree` and `_q_for_branch`. Not urgent.

### [Cleanup] `_choice_enum_from_filter` signature is now a positional `model_field` — internal-only, but a breaking signature change
[filters/inputs.py:279-283](django_strawberry_framework/filters/inputs.py:279)

The function is module-private (underscore prefix). If any future external caller imports it (unlikely; the underscore signals intent), the positional signature change would break them. No action required, just flagging that the internal API moved.

---

## Still outstanding

Just one. Carried forward verbatim from round 2.

### [Cleanup] Unit-test the `_dynamic_filterset_cache` key for equivalent metas
[filters/factories.py:158-170](django_strawberry_framework/filters/factories.py:158)

The class-level shared-dict subclassing trap is documented (round 3). The remaining nit is a unit test that asserts two structurally-equivalent meta dicts hash to the same cache slot — the keying logic (model class + sorted fields tuple + sorted extras tuple) is non-obvious enough to deserve a regression pin. This is the only round-1 / round-2 / round-3 item that hasn't been touched.

---

## Cross-cutting recap

After four rounds:

1. **The branch is in shippable shape on the framework code.** Every `[Bug]`-tier finding across all four rounds has been resolved. The one critical correctness gap from rounds 2–3 (UNSET in operator bags) landed with the defensive entry-point shape that's hardest to regress against.

2. **The `SyncMisuseError` story is fully closed.** Class hierarchy, raise site, typed catch site, public export, sentinel-constant removal — all in one place. The round-3 "future pass" comment that the class docstring referenced is now obsolete; consider trimming the docstring to remove the reference to the substring-matching mention.

3. **`graphql_type_name` is the canonical derivation rule across all three former duplicate sites.** A future rename that breaks the property would break a single test instead of silently drifting across three files.

4. **One unit-test pin remains** (`_dynamic_filterset_cache` keying). Low priority, but it has now survived three reviews — worth knocking out before merge so the open-items list is empty.

Round-4 follow-ups are all `[Risk]` or `[Cleanup]` and can land as a separate pass: the permission-recursion dedup, the proxy/MTI carve-out on `_apply_related_constraints`, the CHANGELOG notes for behavioral changes, and the optional recursion-depth cap on logical branches.

---

Generated via `uv run python scripts/review_changed_python_diffs_against_head.py 039c44252cef807916f55b279f6c4a463a9260bf`. Per-file stripped diffs at `docs/shadow/bug_hunt/diff/django_strawberry_framework__*.diff`.
