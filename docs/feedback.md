# Branch review — round 5: `bugfix/inputs-lookup-token-grouping` vs `main`

Scope: `.py` files under `django_strawberry_framework/` only. Anchored at `origin/main` (`039c4425`) through `HEAD` (`df1e090f`). Per-file stripped diffs regenerated via `uv run python scripts/review_changed_python_diffs_against_head.py 039c4425…`; outputs live under `docs/shadow/bug_hunt/diff/`.

Round-5 compares against round-4 (now overwritten). **The round-4 follow-up list is fully resolved.** Permission-check dedup, the `_MAX_LOGIC_DEPTH` recursion guard, the proxy/MTI carve-out, both CHANGELOG entries for the `_q_for_branch` and `_pascal_case` behavioral changes, the `SyncMisuseError` docstring trim, AND the long-standing `_dynamic_filterset_cache` unit-test pin (carried verbatim across rounds 1–4) all landed in commit `df1e090`. The open-items list is now empty.

Round 5 raises a few small new observations on the round-4 changes themselves — none are blockers; the framework code is in shippable shape.

Severity legend:
- **[Bug]** — incorrect behavior or crash risk on a realistic input.
- **[Risk]** — fragile design, hidden coupling, or subtle edge case.
- **[Cleanup]** — dead code, naming, or doc nit.

---

## What was addressed since round 4

| Round-4 finding | Status | Where |
| --- | --- | --- |
| **`_run_permission_checks` may fire the same gate multiple times inside an `or` branch** | **Fixed** | [filters/sets.py:687-783](django_strawberry_framework/filters/sets.py:687) — keyword-only `_fired` set threaded through recursion; `_invoke_permission_method` records and short-circuits via method-name. New test `test_run_permission_checks_recurses_into_logical_branches` was updated to assert single-fire dedup. |
| **`_apply_related_constraints` model-match uses `is`, trips on proxies / MTI** | **Documented (carve-out)** | [filters/sets.py:994-1014](django_strawberry_framework/filters/sets.py:994) — docstring + error message explicitly carve proxy and multi-table-inheritance children out, mirroring Django's `Query.combine` identity behavior. New test `test_apply_related_constraints_proxy_model_is_rejected` pins the rejection path. |
| **`_q_for_branch` request propagation needs a CHANGELOG line** | **Fixed** | [CHANGELOG.md:25](CHANGELOG.md:25) — explicit "Changed" entry documenting that nested filterset instances now receive the live request (was hardcoded `None`). |
| **`_pascal_case` raise replaces silent `""` return — needs a CHANGELOG line** | **Fixed** | [CHANGELOG.md:26](CHANGELOG.md:26) — explicit "Changed" entry documenting the new `ConfigurationError` shape for no-word-character inputs. |
| **No recursion-depth guard on logical branches** | **Fixed** | [filters/sets.py:43-49](django_strawberry_framework/filters/sets.py:43) — `_MAX_LOGIC_DEPTH = 8` module constant; `_run_permission_checks`, `_evaluate_logic_tree`, `_q_for_branch` all cap and raise `ConfigurationError` past the threshold. `_q_for_branch` stashes `_logic_depth` on the sibling instance so `filter_queryset` can carry the counter across django-filter's `.qs` boundary. New test `test_run_permission_checks_caps_logical_branch_nesting` pins the cap. |
| **`_choice_enum_from_filter` internal-API signature change** | **Acknowledged** | No action — underscore-prefixed; the round-4 review explicitly marked this as "no action required, just flagging". |

| Round-1/2/3 carry-over | Status | Where |
| --- | --- | --- |
| **`_dynamic_filterset_cache` keying unit-test pin** (carried across rounds 1, 2, 3, 4) | **Fixed** | [tests/filters/test_factories.py:275-334](tests/filters/test_factories.py:275) — `test_make_cache_key_structurally_equivalent_metas_share_a_slot` covers list-vs-tuple lookups, dict key order, extras order, and model-class discrimination; `test_dynamic_filterset_cache_collapses_equivalent_metas_to_one_class` is the end-to-end pin via `get_filterset_class`. The non-obvious cache-key shape is now regression-pinned. |

Two specific implementation notes worth pinning explicitly for future readers:

- **Dedup scope is one-class-deep.** `_run_permission_checks` threads `_fired` through `cls`-recursion (logical branches) but **deliberately** omits `_fired` when descending into a `RelatedFilter` child filterset. The docstring is explicit: "gates on a different class have a different identity". This means a child filterset starts a fresh dedup set every time the parent enters it. See round-5 observation below for the corollary.
- **Depth-counter hand-off via `_logic_depth` instance attribute.** `_q_for_branch` sets `child_set._logic_depth = _depth`; `filter_queryset` reads it back via `getattr(self, "_logic_depth", 0)`. This is the only way to carry the counter across django-filter's `.qs` boundary without owning `BaseFilterSet`. The contract is documented in both call-sites' docstrings.

---

## New observations on the round-5 changes

These are follow-ups to the round-4 commit, not blockers.

### [Risk] Dedup boundary is one-class-deep — same child filterset entered from multiple sibling branches still fires its gates per-branch
[filters/sets.py:757-769](django_strawberry_framework/filters/sets.py:757)

The parent's `_fired` set correctly dedups its own per-branch gate across sibling logic arms. The recursion into the child filterset, however, is invoked with no `_fired` argument, so each invocation starts a fresh dedup set. Concrete shape:

```graphql
filter: {
  or_: [
    { shelves: { published: true } },
    { shelves: { published: false } }
  ]
}
```

- Parent's `check_shelves_permission` fires **once** (deduped — correct).
- Child `ShelfFilter.check_published_permission` fires **twice** — once per `or` arm, because each arm spawns a fresh `child_filterset._run_permission_checks(child_input, request)` call with a fresh internal `_fired`.

The docstring justifies this as "different class identity means different gate identity" — which is true between *different classes* but does not address the case where the same child class is entered multiple times from sibling branches of the *same* parent call. The child's gate is idempotent (it either raises or doesn't), so this is functionally harmless — but a consumer who logs from the child's gate sees the same shape that the round-4 fix specifically wanted to eliminate at the parent level: duplicate audit-log entries for one logically-coherent filter.

Two options:
- Maintain a parent-side `dict[type[FilterSet], set[str]]` so a same-class child re-entry deduplicates against its prior fired set.
- Or extend the "Dedup contract" docstring to call out this carve-out explicitly: "same child filterset re-entered from sibling logical branches fires its own gates per branch; the dedup boundary is the immediate `cls` recursion."

### [Risk] Proxy-model test fixture is declared inside the test function body
[tests/filters/test_sets.py:947-953](tests/filters/test_sets.py:947)

```python
class ShelfProxy(library_models.Shelf):
    class Meta:
        proxy = True
        app_label = "library"
```

The proxy class is declared inside the test function. Django's app-loading machinery typically expects model classes at module scope so the app registry sees them during startup; `app_label` makes this work in practice but the pattern is fragile across Django versions (the registry's tolerance for late-bound model registration has shifted across releases). If the test currently passes that's the deciding signal, but moving `ShelfProxy` to `tests/filters/conftest.py` (or a module-scope fixture file) would make the suite resilient to future Django release-note changes around model registration timing.

### [Risk] `_logic_depth` is an undeclared instance attribute set conditionally on the sibling
[filters/sets.py:957-958](django_strawberry_framework/filters/sets.py:957) + [filters/sets.py:877-883](django_strawberry_framework/filters/sets.py:877)

The depth counter hand-off works correctly: `_q_for_branch` sets `child_set._logic_depth = _depth`; `filter_queryset` reads it back with `getattr(self, "_logic_depth", 0)`. The implementation is the only way to thread state across django-filter's `.qs` boundary without owning `BaseFilterSet`.

Concern: the attribute is invisible to anything that walks declared class attributes (`__slots__`, dataclass introspection, strict mypy, IDE autocomplete). A future refactor toward `__slots__` or a stricter typing pass on `FilterSet` would silently lose the channel. Two stabilising options:

- Declare `_logic_depth: int = 0` at class scope so the attribute exists on every instance and the default is explicit.
- Or hoist the contract into a class-level `_LogicDepthMixin` (or a `__init_subclass__` hook) that types it.

Either is a one-line change; both make the hand-off discoverable to static analysis.

### [Cleanup] `_run_permission_checks` allocates a fresh `bare` instance per recursion level
[filters/sets.py:750](django_strawberry_framework/filters/sets.py:750)

```python
bare = object.__new__(cls)
```

Allocated at the top of every recursive call. The `bare` is only used as a getattr target for `check_<field>_permission` method lookup, so a single instance threaded through the recursion would suffice. Not a perf concern (object allocation is cheap), but a future static-analysis pass that flags "create-once / reuse" opportunities would point at it. Worth threading the `bare` through alongside `_fired` and `_depth` if you ever revisit the signature.

### [Cleanup] `_MAX_LOGIC_DEPTH = 8` constant is module-private with no override hook
[filters/sets.py:43-49](django_strawberry_framework/filters/sets.py:43)

The cap is reasonable (eight levels covers every realistic consumer-driven graph), but a consumer with a legitimate deeper-nesting case (machine-generated queries, complex faceted search) has no escape hatch short of monkey-patching the module constant. Two options if a real consumer surfaces:

- Expose `_MAX_LOGIC_DEPTH` as a class attribute (`FilterSet._MAX_LOGIC_DEPTH: ClassVar[int] = 8`) so subclasses can override.
- Or leave as module constant and document the monkey-patch as the supported escape hatch.

Not urgent — the cap is high enough that no realistic consumer will hit it.

---

## Still outstanding

None on the framework code. The open-items list is empty.

---

## Cross-cutting recap

After five rounds:

1. **The branch is in shippable shape on the framework code.** Every `[Bug]`-tier finding across all five rounds has been resolved. The two critical correctness gaps (UNSET in operator bags from rounds 2–3, the `SyncMisuseError` substring catch from round 3) have both landed with defensive entry-point shapes that are hard to regress against.

2. **The `SyncMisuseError` story is fully closed.** Class hierarchy, raise site, typed catch site, public export, sentinel-constant removal, AND the docstring is now trimmed to remove the obsolete "future pass" reference.

3. **`graphql_type_name` is the canonical derivation rule across all three former duplicate sites.** A rename that breaks the property breaks a single test instead of silently drifting across three files.

4. **The `_dynamic_filterset_cache` keying contract is now regression-pinned** with both unit-level (`_make_cache_key`) and end-to-end (`get_filterset_class`) tests covering list-vs-tuple, key-order, and extras-order equivalence classes. This closes the one carry-over item that survived four reviews.

5. **Permission-check dedup is correct one class deep** and **recursion-depth is guarded** via `_MAX_LOGIC_DEPTH = 8` across the three recursion paths (`_run_permission_checks` / `_evaluate_logic_tree` / `_q_for_branch`).

6. **Behavioral changes are documented in CHANGELOG.** Both the `_q_for_branch` request propagation and the `_pascal_case` raise are now discoverable to a consumer reading the release notes.

Round-5 follow-ups are all `[Risk]` or `[Cleanup]` and can land as a separate pass (or be deferred): the child-filterset cross-branch dedup carve-out, the proxy-model test fixture stability, the `_logic_depth` static-analysis visibility, and the optional `_MAX_LOGIC_DEPTH` override hook. None of these block a `0.0.8` cut.

---

Generated via `uv run python scripts/review_changed_python_diffs_against_head.py 039c44252cef807916f55b279f6c4a463a9260bf`. Per-file stripped diffs at `docs/shadow/bug_hunt/diff/django_strawberry_framework__*.diff`.
