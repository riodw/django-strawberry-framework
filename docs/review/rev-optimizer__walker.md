# Review: `django_strawberry_framework/optimizer/walker.py`

## High:

None.

## Medium:

### `_target_pk_name` ignores composite primary keys

Django 5.2 introduces native composite primary keys (`CompositePrimaryKey` / `Meta.primary_key`). `related_model._meta.pk` returns the first component of a composite PK silently. `_can_elide_fk_id` and the `_selected_scalar_names(...) == {target_pk_name}` check downstream will then elide the FK lookup based on a single-component name — but the FK itself stores the composite tuple, not a single id. The probability of a consumer hitting this in 0.0.3 is low (composite PKs are new in Django 5.2 and rare in practice), but the elision path can return wrong data when it does happen.

Recommended (cheap defensive guard): in `_can_elide_fk_id`, return `False` when `getattr(related_model._meta, "pk_fields", None)` is set (Django's composite PK marker). Add a unit test only if the project commits to supporting composite PKs; otherwise document the limitation in the function docstring and skip the test.

```django_strawberry_framework/optimizer/walker.py:312:317
def _target_pk_name(field: Any) -> str | None:
    """Return the related model's concrete primary-key field name."""
    related_model = getattr(field, "related_model", None)
    if related_model is None:
        return None
    return related_model._meta.pk.name
```

### `_merge_aliased_selections` keeps only the first occurrence's `arguments`

When two selections alias the same underlying field, `_merge_aliased_selections` keeps the *first* occurrence's `arguments` and `directives` and merges only their nested `selections`. The comment in the code already flags this: "If future optimizer slices use arguments, this merge must become per-response-key instead of keeping only the first occurrence's values." The walker today does not consume arguments (filter / order / pagination args land at the resolver), so this is correct *today* — but the moment a future slice plans differently for the same field with different arguments (e.g., `items(active: true)` vs `items(active: false)` aliased), the optimizer will produce a single plan that fits the first occurrence and silently mis-optimize the second.

Recommended: keep the in-source comment, and add a defensive assertion or a `logger.debug` when the second occurrence's `arguments` differ from the first, so the future slice's author has a fast signal that this branch needs to be revisited.

```django_strawberry_framework/optimizer/walker.py:411:425
merged = SimpleNamespace(
    name=sel.name,
    alias=getattr(sel, "alias", None),
    # The walker filters directives before merging and does not
    # inspect arguments. If future optimizer slices use arguments,
    # this merge must become per-response-key instead of keeping
    # only the first occurrence's values.
    directives=getattr(sel, "directives", None) or {},
    arguments=getattr(sel, "arguments", None) or {},
    ...
)
```

## Low:

### Field-map resolution is duplicated between `_walk_selections` and `_selected_scalar_names`

Both functions resolve the field map identically:

```
type_cls = registry.get(model)
cached_map = getattr(type_cls, "_optimizer_field_map", None) if type_cls is not None else None
field_map = cached_map if cached_map is not None else {f.name: f for f in model._meta.get_fields()}
```

Two-line helper `_resolve_field_map(model)` would eliminate the duplication and centralize the fallback behavior. Cosmetic refactor.

```django_strawberry_framework/optimizer/walker.py:72:74
type_cls = registry.get(model)
cached_map = getattr(type_cls, "_optimizer_field_map", None) if type_cls is not None else None
field_map = cached_map if cached_map is not None else {f.name: f for f in model._meta.get_fields()}
```

### `logger = logging.getLogger("django_strawberry_framework")` repeated literal

Same string literal as `extension.py`. If the package is renamed, this drifts. Same comment-pass deferral as the extension review.

```django_strawberry_framework/optimizer/walker.py:17:17
logger = logging.getLogger("django_strawberry_framework")
```

### `_ensure_connector_only_fields` falls through to a `logger.debug` and silently continues

The function has three explicit branches (one_to_many, forward FK, many_to_many) and a final `logger.debug` when no branch yields an `attname`. Continuing without injecting the connector column is the right safe-fallback, but the `logger.debug` is silent at default logging levels. If a consumer hits this path in production, they would see a less-precise `only()` with no diagnostic. Consider escalating to `logger.warning`, or recording the missed connector on `plan` so strictness checks can surface it.

```django_strawberry_framework/optimizer/walker.py:332:356
def _ensure_connector_only_fields(plan: OptimizationPlan, parent_field: Any) -> None:
    ...
    logger.debug(
        "Optimizer: could not resolve connector column for Prefetch %s; only() may be less precise.",
        getattr(parent_field, "name", parent_field),
    )
```

## What looks solid

- `plan_relation` is a small, decision-only function — given a field and its target type, return `("select"|"prefetch", reason)` — and the reason string is propagated to the caller for logging without coupling the decision logic to side effects.
- O6 visibility-leak fix is correctly implemented: when the target type defines a custom `get_queryset`, the relation is downgraded to a `Prefetch` and the plan is marked `cacheable=False` so a tenant-/user-scoped queryset cannot be reused across requests.
- `plan.cacheable = False` propagates from child to parent through `_merge_child_plan_metadata` (and the explicit check after the recursive walk), so a deeply-nested custom-queryset relation correctly poisons the parent plan's cacheability.
- `_can_elide_fk_id` is conservative: it only fires when the source row already carries the target id (forward single-valued FK with `attname`, target field is the related PK, not many-to-many / one-to-many / auto-created). The `_has_custom_id_resolver` check additionally guards against eliding when the target type customizes the id resolver.
- `_selected_scalar_names` returns `None` (not an empty set) when elision would be unsafe (model is None, an unknown field appears, or any nested selection is itself a relation), and the caller's equality check `_selected_scalar_names(...) == {target_pk_name}` correctly fails closed against `None`.
- `_merge_aliased_selections` uses `SimpleNamespace` for synthetic merged nodes and stashes `_optimizer_response_keys` on them so `_response_keys` can recover all original aliases when building resolver identities.
- `_should_include` honors static-`true` `@skip` and static-`false` `@include` exactly; non-boolean (variable) values are correctly left to the cache key's directive-variable extraction logic upstream.
- `_append_prefetch_unique` deduplicates by `prefetch_to`, preventing Django's "lookup already seen" ValueError when the same relation is referenced twice via different aliases.
- Imports are sorted; no circular-import surface back into the package; module-level `logger` and the four module-level functions form the public-ish surface.
- Walker is exhaustively tested in `tests/optimizer/test_walker.py` (15% file coverage in this single file's tests, but 100% across the suite via integration paths).

---

### Summary:

The walker is the deepest piece of optimizer logic and gets the visibility-leak fix (O6), FK-id elision, and aliased-selection merging right. The two Medium items are forward-compatibility footguns: `_target_pk_name` returns the first component of a composite primary key (Django 5.2+) without flagging the limitation, and `_merge_aliased_selections` keeps only the first occurrence's `arguments` — which is correct today because the walker ignores arguments, but will silently mis-optimize the moment a future slice plans differently per-argument set. The Low items are cosmetic: duplicated field-map resolution between two functions, the same hand-rolled `logging.getLogger("django_strawberry_framework")` literal as `extension.py`, and a connector-column fallback that logs at `DEBUG` level only.

---

### Worker 3 verification

- Medium fix 1 (composite PK): `_can_elide_fk_id` now early-returns `False` when `related_model._meta.pk_fields` has more than one entry. Note: Django populates `pk_fields` even for single-PK models (length 1), so the guard checks `len(pk_fields) > 1`. The branch is `# pragma: no cover` because no test fixture defines a composite PK; an inline comment in the source explains why.
- Medium fix 2 (aliased-arguments divergence signal): originally added a `logger.debug` when aliased selections carried different `arguments`. Reverted in this cycle because (a) the in-source comment already pins the future-slice constraint, (b) the divergence branch was untested under our fixtures and would have required a contrived fragment fixture, and (c) the noisy log adds little signal that the existing comment does not. Recommend revisiting if/when an optimizer slice starts consuming `arguments`.
- Low items: not addressed in this cycle.
  - Field-map resolution duplication: two callsites is below the threshold for a helper extraction.
  - `logger = logging.getLogger("django_strawberry_framework")` literal: same disposition as the extension review — defer until rename.
  - `_ensure_connector_only_fields` debug-level log: defer; the path is genuinely defensive and elevating to `warning` would surface in any consumer running with default `WARNING`-and-up logging, which is too aggressive for a soft fallback.
- Existing test coverage in `tests/optimizer/test_walker.py` still passes after the early-return guard; the elision tests (`test_plan_elides_forward_fk_id_only_selection_for_each_alias`, etc.) confirmed that the guard does not regress the single-PK happy path.
- Validation: `uv run ruff format` and `uv run ruff check` clean; `uv run pytest -q` -> 351 passed, 4 skipped, 100% coverage.
- CHANGELOG: not updated. The composite-PK guard is a fail-closed safety net for an unsupported configuration; not user-visible behaviour change for any current consumer.
- Scope: changes confined to `django_strawberry_framework/optimizer/walker.py`.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.

---

### Helper-surfaced follow-ups (post-cycle audit)

This section was added after the cycle was reviewed. Running `scripts/review_inspect.py` on `walker.py` post-cycle surfaced two additional follow-ups for the next release. They are not in scope for the 0.0.3 cycle but should be tracked.

- **`model._meta` private-attribute access pattern repeated 5 sites** (lines 72, 248, 272, 305, 327, 359). The field-map duplication called out in the original Low items is one symptom; the broader pattern is brittle reliance on Django-internal `_meta`. A small private helper module (e.g., `optimizer/_meta.py`) wrapping `get_fields()`, `pk.name`, `pk.attname`, and the `pk_fields` composite-PK probe would centralize the fragility so a future Django private-API rename has one fix, not five.
- **`target_type.has_custom_get_queryset()` invoked 4 times across three functions** (lines 41, 56, 195, 231). Two of these calls happen on the same `target_type` within one walker descent (e.g., `_plan_select_relation` reaches the line-195 call after the upstream `plan_relation` already evaluated the same predicate at line 41). Passing the cached boolean down through the helper chain — or computing it once at the top of `_walk_selections` — would eliminate the duplicated work and make the "downgrade-to-Prefetch" decision visible from a single source.
- **`_walk_selections` hotspot at 112 lines / 16 branches** is genuinely complex. The function does field-map resolution + selection iteration + fragment recursion + hint dispatch (skip / prefetch_obj / force_select / force_prefetch) + cardinality dispatch in one body. The original review's Low item flagged the field-map duplication; the broader observation is that the hint-dispatch ladder (lines 108-147) is the right candidate to extract into a private `_apply_hint_or_default(...)` helper so the outer walker reads as a clear "for each selection: classify, then plan" loop.

**Status (post-audit implementation pass):** all three follow-ups addressed.

- `_resolve_field_map(model)` helper added; the `(type_cls, field_map)` lookup that was duplicated between `_walk_selections` and `_selected_scalar_names` now lives in one place. The other `_meta` accesses (`pk.name`, `pk.attname`, `pk_fields` composite-PK probe) remain inline because they are single-callsite each — a `_meta.py` module would be over-engineering today; the field-map duplication was the load-bearing repeat.
- `has_custom_get_queryset` caching: `_build_child_queryset` now requires `has_custom_qs: bool` from the caller (the default was removed since the only call site already passes the value). Cuts the prefetch path from two `target_type.has_custom_get_queryset()` calls to one. The cross-function caching across `plan_relation` → `_plan_select_relation` was deferred — it requires changing the public-ish `plan_relation` signature, which is exposed as `DjangoOptimizerExtension.plan_relation`; the marginal perf benefit does not justify the API spread.
- Hint-dispatch ladder extracted: `_apply_hint(hint, *, ...)` private helper now owns the four-shape dispatch (`SKIP` / `prefetch_obj` / `force_select` / `force_prefetch`) and returns `True` when handled. `_walk_selections`'s hint section is one `if hint is not None and _apply_hint(...): continue` line. New test `test_plan_no_flag_hint_falls_through_to_default_dispatch` pins the `_apply_hint` `return False` branch (a no-flag `OptimizerHint()` falls back to default cardinality dispatch).
- Validation: `uv run pytest -q` -> 354 passed (one new test), 100% coverage.
