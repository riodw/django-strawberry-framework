# Review of `django_strawberry_framework` Python diff vs `main`

Reviewed the `build-021-filters-0_0_8` branch against `main` at merge-base
`039c44252cef807916f55b279f6c4a463a9260bf` (branch tip `f2c824e`), inspecting
only the changed `.py` files under `django_strawberry_framework/`. The review
covers the **current working tree**, which carries four uncommitted production
edits on top of `f2c824e` (`conf.py`, `filters/factories.py`, `filters/inputs.py`,
`filters/sets.py`) — see finding 3.

Severity legend:
- **[High]** — incorrect behavior or crash on a realistic input.
- **[Risk]** — fragile design, hidden coupling, or repo-state hazard.
- **[Cleanup]** — dead code, naming, doc, or hygiene nit.

Both High findings below were raised in the previous round and remain
**unaddressed in source**; I re-confirmed each by reproducing it in an isolated
process against the fakeshop models.

## Findings

### 1. [High] Aliased `RelatedFilter` parent constraint uses the declared name, not the ORM path
- Relevant code: `django_strawberry_framework/filters/sets.py:1041` (with the loop at `sets.py:1001` and the branch enumerator at `sets.py:608`).
- `related_filters` is keyed by the **declared attribute name** (`FilterSetMetaclass.__new__`, `sets.py:67-73`), and `_iter_active_related_branches` yields that key as its `field_name`. `_expand_related_filter` is careful to distinguish the two — it builds the input key from the declared name but rewrites the child ORM path from `f.field_name` (`sets.py:101-103`). `_apply_related_constraints` is not: it emits the parent restriction as `parent_qs.filter(**{f"{field_name}__in": intersected})` using the *declared* key.
- Whenever a consumer declares a `RelatedFilter` whose attribute name differs from its `field_name` (a documented django-filter pattern — e.g. exposing a friendlier GraphQL name than the ORM accessor), the constraint is built against a non-existent relation path and Django raises `FieldError`.
- **Why CI is green:** every `RelatedFilter` in `examples/fakeshop/apps/library/filters.py` sets `field_name` equal to its attribute name (`shelves→shelves`, `branch→branch`, `books→books`, …), so the divergence never fires in the example suite. This is latent, not exercised.
- Reproduced in an isolated process:
  ```python
  class BranchVisFilter(FilterSet):
      visible_shelves = RelatedFilter(ShelfFilter, field_name="shelves",
                                      queryset=models.Shelf.objects.all())
      class Meta:
          model = models.Branch
          fields = {"id": ["exact"]}

  BranchVisFilter.apply_sync({"visible_shelves": {}}, Branch.objects.all(), info)
  # FieldError: Cannot resolve keyword 'visible_shelves' into field.
  #             Choices are: city, id, name, shelves, tags
  ```
- **Suggested fix:** in `_apply_related_constraints`, build the ORM clause from `related_filter.field_name`, not the loop's declared key:
  ```python
  constrained = constrained.filter(**{f"{related_filter.field_name}__in": intersected})
  ```
  Keep the `child_qs_by_branch.get(field_name)` lookup on the declared key — `_derive_related_visibility_querysets_*` key that dict by the declared name, so only the final `.filter(...)` path is wrong.

### 2. [High] Related-branch visibility runs the wrong type's `get_queryset()` when the child filterset is bound to a non-primary type
- Relevant code: `django_strawberry_framework/filters/sets.py:691-697` (`_target_type_for_related_filter`), consumed by `_derive_related_visibility_querysets_sync` (`sets.py:659`) / `_async` (`sets.py:680`).
- `_target_type_for_related_filter` resolves the visibility-scoping type purely from the model: `registry.primary_for(child_model) or registry.get(child_model)`. It ignores the bound owner of the *explicitly-wired* child filterset (`related_filter.filterset._owner_definition`).
- When more than one `DjangoType` is registered for the child model and the child `FilterSet` is wired to a **non-primary** one via `Meta.filterset_class`, the derivation runs the **primary** type's `get_queryset()` while applying the filterset that belongs to the non-primary type. If the two `get_queryset()` implementations differ (e.g. the non-primary type scopes to a tenant / visibility predicate the primary does not), the related branch is scoped by the wrong visibility hook — a silent correctness/row-leak hazard.
- Reproduced in an isolated process (two types registered for `Shelf`, `ShelfFilter` bound to the non-primary):
  ```
  child filterset bound owner            = SecondaryShelfType
  _target_type_for_related_filter resolved = PrimaryShelfType   # wrong type's get_queryset() runs
  ```
- This is a genuine seam, not a style nit: `_resolve_relation_target_type` (the sibling used by `filter_for_field`, `sets.py:374-411`) *does* consult `_owner_definition` first. The asymmetry is the bug — `_target_type_for_related_filter` should be owner-aware too.
- **Suggested fix:** prefer the child filterset's bound owner, fall back to the registry only when unbound:
  ```python
  child_owner = getattr(child_filterset, "_owner_definition", None)
  if child_owner is not None:
      return getattr(child_owner, "origin", None) or getattr(child_owner, "type", None)
  return registry.primary_for(child_model) or registry.get(child_model)
  ```
  Note this is intentionally *more* owner-aware than `related_target_for` (which resolves to the primary for GlobalID type-naming). The two concerns differ: relation *naming* wants the canonical public type; the visibility *hook* must follow the filterset the consumer actually wired.

### 3. [Risk] Real production fixes are sitting uncommitted in the working tree
- `git status` shows four package files modified but in **no commit** on top of `f2c824e`:
  - `conf.py:145` — `Settings.__getattr__` recursion guard (adds `user_settings` / `_user_settings` / `reload` to the early-`AttributeError` set so attribute access during init cannot recurse). Correct fix; reproducing the `RecursionError` it prevents requires only an uninitialized-settings attribute probe.
  - `filters/factories.py:158` — the `_make_hashable` cache-key helper (prevents an unhashable-`Meta` crash in `_make_cache_key`). Correct fix.
  - `filters/inputs.py:204-220` — `_scalar_from_form_field` reordered so `DecimalField` / `FloatField` are matched **before** `IntegerField` (both subclass `forms.IntegerField` in the form-field hierarchy, so the old order mapped decimal/float-backed filters to `int` and left the float/decimal branches dead). Behavior-changing correctness fix.
  - `filters/sets.py:242` — `# pragma: no cover` on the genuinely-unreachable `model is None` guard in `get_fields` (`super().get_fields()` raises first for the `model=None` + `"__all__"` shape).
- Until these are committed, the branch tip (`f2c824e`) does **not** contain the recursion guard, the cache-crash fix, or the decimal/float mapping fix, and a clean checkout would regress. **Action:** commit these four (plus their tests) so the landed state matches what the suite is green against. Per the repo convention I did **not** touch `CHANGELOG.md`; the `inputs.py` decimal/float fix is a behavior change a maintainer may want to log there.

### 4. [Cleanup] `_make_hashable` sorts `dict` keys but not `set` / `frozenset` members
- Relevant code: `django_strawberry_framework/filters/factories.py:158-164`.
- The `dict` branch normalizes via `tuple(sorted(...))` (key order irrelevant); the `set` / `frozenset` branch is `tuple(_make_hashable(item) for item in v)` — iteration order preserved, not sorted. `_make_cache_key` accepts a `set`-shaped `Meta.fields` (`sets`/`("seq", …)` branch), so the helper's contract is "structurally-equal inputs collapse to one key."
- Impact is low: within a single process two equal `set`s iterate identically, so this is not a live cache-divergence today; it's a latent inconsistency if the helper is reused where members come from differently-ordered sources. **Suggested:** sort the `set` / `frozenset` branch on the `_make_hashable`-of-each-item (guard for unorderable mixed types) so the helper's normalization is uniform across container kinds. Separately, a `set`-typed `Meta.fields` yields hash-randomized *filter order* across processes regardless of caching — worth a docstring caveat steering consumers to `list` / `tuple`.

## Notes
- The `apply_sync` / `apply_async` pipeline ordering (derive visibility → resolve request → apply related constraints → construct → permission-check → validate → return `.qs`) is internally consistent; logical-branch permission recursion (`_run_permission_checks`) and the `_evaluate_logic_tree` / `_q_for_branch` `_logic_depth` hand-off both cap at `_MAX_LOGIC_DEPTH` and re-enter cleanly across django-filter's `.qs` boundary. No new defect found there.
- GlobalID decode/validate (`base.py:205-270`), the `ArrayFilter` / `ListFilter` empty-list contracts (`base.py:97-164`), and `_expected_global_id_type_name`'s own-PK vs relation routing (`base.py:167-202`) read correctly.
- Findings 1 and 2 are the only two correctness bugs I found; both are pre-existing carry-forwards from the prior round and both are latent against the current fakeshop filter graph (every live `RelatedFilter` uses matching names and a single-type-per-model registry).
