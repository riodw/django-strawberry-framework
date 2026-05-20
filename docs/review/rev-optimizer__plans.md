# Review: `django_strawberry_framework/optimizer/plans.py`

Status: verified

## DRY analysis

- None — `plans.py` is at the right granularity; every brittle Django-private access (`prefetch_to`, `_prefetch_related_lookups`, `query.select_related`) is funnelled through a single helper, and the one noted `_lookup_path` vs inline-`getattr` asymmetry at `plans.py:430` is tracked as a Low finding because the bare-string branch's `prefix` composition prevents direct substitution.

## High:

None.

## Medium:

### `apply()` chained `.only()` silently overrides consumer-applied projection

`OptimizationPlan.apply` (`plans.py:118-133`) applies `queryset.only(*self.only_fields)` unconditionally before `select_related` and `prefetch_related`. Django's `QuerySet.only()` chained on top of an existing `only()` **replaces** the previous deferred-field set rather than merging it; verified empirically that `User.objects.only("username", "email").only("first_name")` collapses to `SELECT id, first_name`. A consumer whose `DjangoType.get_queryset` returns `Model.objects.only("name", "owner_id")` to enforce a column-level permission boundary will have those projections silently overwritten by the optimizer's own `only_fields`, and the rendered row will be missing the columns the consumer required.

`diff_plan_for_queryset` (`plans.py:295-353`) reconciles `select_related` and `prefetch_related` against the queryset but does not look at `only_fields` at all — there is no mention of `only` in either the docstring or the implementation. The cache-safety invariant is preserved (the plan is never mutated), but the consumer's projection is not.

Recommended change: either (1) extend `diff_plan_for_queryset` with an `only` reconciliation rule (merge consumer's `query.deferred_loading` set into `plan.only_fields` and apply the merged set, or drop `plan.only_fields` when the consumer already restricted columns), or (2) document the constraint explicitly in `OptimizationPlan.apply` and on the `DjangoType.get_queryset` consumer surface ("returning a queryset with `.only()` already applied is unsupported; the optimizer's `only_fields` will replace your set"). Option 1 is the consumer-safer default and matches the existing `select_related`/`prefetch_related` reconciliation discipline. A test pin under `tests/optimizer/test_plans.py::TestDiffPlanForQueryset` (consumer `qs.only("name")` + plan `only_fields=["id"]` → resulting deferred-loading set covers both) would lock the chosen behaviour.

```django_strawberry_framework/optimizer/plans.py:118:133
def apply(self, queryset: Any) -> Any:
    """Apply the plan to a ``QuerySet`` and return the optimized copy.

    Applies in order: ``only()`` → ``select_related()`` →
    ``prefetch_related()``. The order matters because
    ``select_related`` may narrow ``only()`` column lists and
    ``prefetch_related`` may carry nested ``Prefetch`` objects whose
    inner querysets already have their own ``only()`` applied.
    """
    if self.only_fields:
        queryset = queryset.only(*self.only_fields)
    if self.select_related:
        queryset = queryset.select_related(*self.select_related)
    if self.prefetch_related:
        queryset = queryset.prefetch_related(*self.prefetch_related)
    return queryset
```

```django_strawberry_framework/optimizer/plans.py:295:353
def diff_plan_for_queryset(
    plan: OptimizationPlan,
    queryset: Any,
) -> tuple[OptimizationPlan, Any]:
    # ... reconciles select_related and prefetch_related;
    # only_fields is silently passed through, not reconciled.
```

## Low:

### `_prefetch_lookup_paths` bypasses `_lookup_path` for its own `prefetch_to` read

`_lookup_path` (`plans.py:244-251`) is documented as the single fix-site for a future Django rename of `Prefetch.prefetch_to`. `_prefetch_lookup_paths` (`plans.py:430`) reads `prefetch_to` directly with `getattr(entry, "prefetch_to", None)` instead of routing through `_lookup_path`. The branching shape differs (bare-string entries are already handled in the loop above, and the path needs to be composed with `prefix`), so a literal substitution does not work — but the contract claim in `_lookup_path` would be stronger if a small `_prefetch_to_or_none(entry)` helper (or a `default=None` parameter on `_lookup_path`) covered this site too. Cosmetic; the practical risk is low because both call sites would be obvious to fix together if Django ever renamed the attribute.

```django_strawberry_framework/optimizer/plans.py:430:430
prefetch_to = getattr(entry, "prefetch_to", None)
```

### `runtime_path_from_path` `str(key)` is redundant after the int-skip filter

`runtime_path_from_path` (`plans.py:161-175`) skips integer keys (list indexes) and `None` keys, then calls `str(key)` on what survives. graphql-core's path keys that are not integers are already strings; `str(key)` is defensive against a hypothetical non-int non-str non-None key. The defensiveness is harmless but the function is on the resolver-key hot path (called once per relation resolver per request). Replacing with a direct `keys.append(key)` would remove the per-call function call cost. Trivial; flag for the next pass that touches this function.

```django_strawberry_framework/optimizer/plans.py:169:175
keys: list[str] = []
while path is not None:
    key = getattr(path, "key", None)
    if not isinstance(key, int) and key is not None:
        keys.append(str(key))
    path = getattr(path, "prev", None)
return tuple(reversed(keys))
```

### `is_empty` docstring does not mention `cacheable`

`OptimizationPlan.is_empty` (`plans.py:82-91`) deliberately excludes `cacheable` from the emptiness check — pinned by `test_cacheable_flag_does_not_affect_empty_state` (`tests/optimizer/test_plans.py:48-50`). The one-line docstring ("Return ``True`` when no optimization directives were collected.") is accurate but does not warn the reader that an empty-but-uncacheable plan still returns `True`. A future maintainer reading the docstring alone would have to read `extension.py:572` to see that `is_empty` is the early-exit gate for `_optimize` and confirm that `cacheable=False` does not block that early exit. Add one sentence ("``cacheable`` is metadata about cache reuse and is excluded from the emptiness check.") at the comment pass.

```django_strawberry_framework/optimizer/plans.py:82:91
@property
def is_empty(self) -> bool:
    """Return ``True`` when no optimization directives were collected."""
    return (
        not self.select_related
        and not self.prefetch_related
        and not self.only_fields
        and not self.fk_id_elisions
        and not self.planned_resolver_keys
    )
```

## What looks solid

### DRY recap

- **Existing patterns reused.** `_lookup_path` (`plans.py:244-251`) centralises the `getattr(entry, "prefetch_to", entry)` contract for prefetch-entry path extraction and is reused at `plans.py:239` (`append_prefetch_unique`), `plans.py:382` (`_diff_prefetch_related` building `consumer_by_path`), and `plans.py:388` (`_diff_prefetch_related` per-entry path). `_consumer_prefetch_lookups` (`plans.py:254-262`) centralises the brittle `QuerySet._prefetch_related_lookups` access and is reused at `plans.py:381` (`_diff_prefetch_related`) and `plans.py:436` (`_prefetch_lookup_paths` for nested-Prefetch inner querysets). `_flatten_select_related` (`plans.py:178-208`) centralises Django's three-shape `query.select_related` contract and is reused at `plans.py:368` (`_diff_select_related`). `append_unique`, `append_unique_many`, and `append_prefetch_unique` are reused at six walker call sites (`walker.py:206,213,298,300,329,341,353,354,422,497-499,601`). `resolver_key` + `runtime_path_from_info` are reused at the two resolver-key construction call sites (`walker.py:51,223,298` and `types/resolvers.py:62,136`).
- **New helpers a fix might justify.** None. The file is already at the right granularity — every reflective Django-private access (`prefetch_to`, `_prefetch_related_lookups`, `query.select_related`) is funnelled through a single helper, and the mutator family lives next to the dataclass it serves.
- **Duplication risk in the current file.** `_prefetch_lookup_paths` (`plans.py:430`) reads `prefetch_to` directly with `getattr(entry, "prefetch_to", None)` rather than calling `_lookup_path`. The shape contract is the same brittle Django-private attribute, but `_lookup_path` returns the *entry itself* on the string branch (so it cannot be substituted unmodified inside the branched walker — the bare-string branch above does its own `prefix` composition). Acceptable as-is, but the docstring claim in `_lookup_path` ("Centralizes the brittle Django-private contract for ``Prefetch.prefetch_to`` so a future Django rename has one fix") is mildly weakened by the inline access at line 430. Flagged Low. No other repeated literals beyond `prefetch_to` (2x) and `queryset` (2x), both in their natural docstring/code positions.

### Other positives

- Helper ran cleanly (two hotspots — `diff_plan_for_queryset` 59 lines / 2 branches, and `_diff_prefetch_related` 41 lines / 6 branches — both well within Medium-tier complexity and individually test-pinned by `TestDiffPlanForQueryset` across 12 cases at `tests/optimizer/test_plans.py:226-411`). No TODO comments; the five comment-inventory lines are all load-bearing (the four-line block at lines 404-407 explaining the documented `prefetch_related(None)` reset idiom is exactly the kind of "non-obvious Django behaviour" comment the workflow asks for).
- The cache-safety invariant ("once a plan has been handed off, do not mutate in place") is enforced structurally by `finalize()` swapping list fields to tuples, *and* tested by `test_finalize_blocks_post_handoff_append_on_cache_isolation` (`tests/optimizer/test_plans.py:152-160`). `diff_plan_for_queryset` honours the invariant by routing every change through `replace(plan, ...).finalize()` (`plans.py:351`) rather than mutating, and the early-exit fast path (`plans.py:344-349`) returns the original plan identity when nothing changes, also test-pinned by `test_returns_same_instances_when_nothing_to_drop` (`tests/optimizer/test_plans.py:229-234`). The cache mutation discipline carried forward from `_context.py`'s narrow-exception pin and `hints.py`'s sentinel-identity pin is the same shape here.
- Every brittle Django-private access (`prefetch_to`, `_prefetch_related_lookups`, `query.select_related`) is funnelled through a single helper with a docstring saying so. The `_optimizer_can_absorb` three-condition gate (`plans.py:265-292`) is the strongest part of the file: each condition is documented, the `else: consumer wins on this subtree` branch is comment-anchored at line 399, and every branch is individually test-pinned (cases 1, 2, follow-up + variant at `test_plans.py:297-411`). When the optimizer cannot losslessly absorb a consumer subtree it drops itself rather than corrupting the consumer's tree — the safer-side bias that the Two-Scoops "explicit queryset boundaries" rule rewards.
- `_flatten_select_related`'s wildcard-True handling (`plans.py:196-197`) and the "treat wildcard as no overlap" semantics are documented in both the helper docstring and `_diff_select_related`'s docstring, and pinned by `test_wildcard_select_related_does_not_drop_explicit_entries` (`tests/optimizer/test_plans.py:252-260`). The semantics are correct: Django's wildcard `select_related()` only follows non-null FKs, so optimizer entries for nullable FKs would be silently dropped if the wildcard were treated as covering everything. The conservative no-overlap rule preserves correctness at the cost of one extra `select_related(*names)` call.
- `_prefetch_lookup_paths` (`plans.py:422-439`) correctly recurses through nested `Prefetch` queryset chains via `_consumer_prefetch_lookups` — this is what makes `_optimizer_can_absorb` able to ask "does my own subtree cover this consumer descendant" for deep optimizer trees. Pinned by `test_flatten_nested_prefetch_objects_recursively` and the four absorption-variant tests under `TestDiffPlanForQueryset`.
- The "lives next to the plan shape" relocation of `append_unique` / `append_unique_many` / `append_prefetch_unique` matches the documented intent in each helper's docstring ("plan-shape mutator: lives next to ``OptimizationPlan`` so the dedupe discipline is a property of the plan list shape rather than a walker-local convention") and is consistent with the carry-forward calibration from `_context.py` — helpers that own a shape contract belong with the shape.

### Summary

`plans.py` is a tight, well-tested 440-line module that owns the optimizer's plan dataclass, the brittle Django-private access surface (`prefetch_to`, `_prefetch_related_lookups`, `query.select_related`), and the consumer-vs-optimizer reconciliation logic. The cache-mutation invariant is structurally enforced and pinned by tests. The one substantive finding is Medium: `apply()` calls `queryset.only(*self.only_fields)` without reconciling against any `.only()` the consumer's `DjangoType.get_queryset` may have already applied, and Django's `.only().only()` chaining replaces rather than merges — silently dropping consumer-applied column projections. The two Lows are cosmetic (a small `_lookup_path` reuse opportunity in `_prefetch_lookup_paths` and a redundant `str(key)` call in `runtime_path_from_path`) plus a one-sentence docstring nit for `is_empty`. Comment polish (the `is_empty` clarification and the optional `only` reconciliation behaviour notes) should wait for the comment pass after the Medium is resolved.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/optimizer/plans.py`:
  - Added `_consumer_only_fields(queryset)` helper (lines ~265-293) — funnels the brittle `query.deferred_loading` Django-private access through one site, mirroring the existing `_consumer_prefetch_lookups` pattern. Returns the non-empty consumer `.only()` field set or `None` (None for default, `.defer()` mode, or non-QuerySet inputs).
  - Extended `diff_plan_for_queryset` docstring (lines ~339-354) with the new `only_fields` reconciliation rule, explaining the chained-`.only()` replace-not-merge semantics and the conservative consumer-wins choice (drop the optimizer's `only_fields` rather than merging or overwriting).
  - Extended `diff_plan_for_queryset` body (lines ~375-396) with the `drop_only_fields` reconciliation step: computed alongside the existing select/prefetch diffs, factored into the fast-path "nothing changes" early-exit, and passed through `replace(plan, only_fields=...)` so the cache-safety invariant (`finalize()` on every derived plan) is preserved.
- `tests/optimizer/test_plans.py`: added four cases inside `TestDiffPlanForQueryset` covering the four detection branches Worker 1 asked for.

### Tests added or updated

- `tests/optimizer/test_plans.py::TestDiffPlanForQueryset::test_drops_only_fields_when_consumer_applied_only` — consumer `qs.only("name")` + plan `only_fields=["id"]` → resulting plan has `only_fields=()` and consumer projection survives. Asserts the cache-safety invariant (original plan untouched).
- `tests/optimizer/test_plans.py::TestDiffPlanForQueryset::test_keeps_only_fields_when_consumer_did_not_apply_only` — consumer no `.only()` + plan `only_fields=["id"]` → plan is the same instance (fast-path early exit), `apply()` still applies the optimizer's `only_fields`.
- `tests/optimizer/test_plans.py::TestDiffPlanForQueryset::test_keeps_only_fields_when_consumer_used_defer` — consumer `qs.defer("name")` + plan `only_fields=["id"]` → plan kept; `.defer()` is not treated as a `.only()` projection.
- `tests/optimizer/test_plans.py::TestDiffPlanForQueryset::test_drops_only_fields_when_consumer_chained_only` — consumer `qs.only("name").only("category_id")` → Django collapses to the last `.only()` argument set, `deferred_loading=({category_id}, False)`, consumer-applied `.only()` still triggers the drop.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged; the COM812-vs-formatter warning is the standing project-config warning, not a fix-induced issue).
- `uv run ruff check --fix .` — pass (All checks passed).
- `uv run pytest tests/optimizer/test_plans.py -k "diff_plan or only" -x` — 7 passed, 42 deselected. All four new test cases pass; pre-existing diff/only tests still pass. (The pytest run prints a coverage-gate failure because the focused `-k` subset only exercises one source file; coverage is a full-suite/CI gate, not a focused-run gate.)

### Notes for Worker 3

- No shadow file used.
- Drop-not-merge variant chosen per the artifact's Medium 1 dispatch instructions (conservative consumer-wins; matches the existing `select_related`/`prefetch_related` reconciliation discipline that drops the optimizer rather than corrupting the consumer's tree).
- New helper `_consumer_only_fields` placed next to `_consumer_prefetch_lookups` because both funnel a brittle Django-private access into one site (the `_consumer_*` naming + colocation is intentional).
- Fast-path "nothing changes" early-exit now also gates on `drop_only_fields` so a consumer-`.only()` detection still produces a derived plan rather than returning `plan` unchanged.
- Low 1 (`_prefetch_lookup_paths` bypasses `_lookup_path`): deferred — no in-cycle edit per artifact instructions ("cosmetic, literal substitution doesn't work").
- Low 2 (`runtime_path_from_path` redundant `str(key)`): deferred — no in-cycle edit per artifact instructions ("Trivial; flag for the next pass that touches this function").
- Low 3 (`is_empty` docstring missing `cacheable` mention): deferred to comment pass per artifact instructions.
- No CHANGELOG.md edit (logic pass only; AGENTS.md says don't touch CHANGELOG.md unless explicitly instructed, and the active plan did not authorize a changelog pass for this cycle item).

---

## Verification (Worker 3)

### Logic verification outcome

- **High:** None — accepted.
- **M1 (`apply()` chained `.only()` silently overrides consumer projection):** addressed via new `_consumer_only_fields` helper (`plans.py:265-293`) + reconciliation step in `diff_plan_for_queryset` (`plans.py:388-389, 395, 399-404`) + 4 new tests in `TestDiffPlanForQueryset`; all pass. Helper correctly reads `query.deferred_loading` defensively (`getattr` on both `query` and `deferred_loading`), unpacks `(field_set, defer_flag)` inside a `try` for non-tuple shapes, treats `defer_flag is not False` (covers True and any non-False) as "not a consumer `.only()`", and treats an empty `field_set` as "no projection". Drop-not-merge variant matches the artifact's recommendation. Fast-path early-exit gate updated with `and not drop_only_fields` so a pure-only-drop case still routes through `replace(...).finalize()` and preserves the B1 cache-mutation invariant. Accepted.
- **L1 (`_prefetch_lookup_paths` bypasses `_lookup_path`):** deferred per artifact prose ("cosmetic, literal substitution doesn't work"). Accepted.
- **L2 (`runtime_path_from_path` redundant `str(key)`):** deferred per artifact prose ("Trivial; flag for the next pass that touches this function"). Accepted.
- **L3 (`is_empty` docstring missing `cacheable` mention):** deferred to comment pass per artifact instructions. Accepted.

### DRY findings disposition

New helper `_consumer_only_fields` matches the existing `_consumer_prefetch_lookups` pattern (Django-private access funnelled through one helper, colocated, identically named with the `_consumer_*` prefix). The third Django-private surface (`prefetch_to`) already has `_lookup_path`; the file now has one helper per brittle-private attribute, which is the right granularity. Accepted.

### Temp test verification

None used; permanent tests written directly into `TestDiffPlanForQueryset`.

### Verification outcome

- `logic accepted; awaiting comment pass`

Test run: `uv run pytest tests/optimizer/test_plans.py::TestDiffPlanForQueryset -x` → 20 passed (4 new + 16 existing). Coverage failure on the focused run is expected (full-suite gate, not focused-run gate) and matches Worker 2's noted behavior.

Spot-checks performed:
- Test 1 (consumer `.only("name")` + plan `only_fields=["id"]`): asserts `delta_plan.only_fields == ()` AND `delta_qs.query.deferred_loading == ({"name"}, False)` AND original `plan.only_fields == ["id"]` (cache invariant). Pass.
- Test 2 (consumer no `.only()`): asserts `delta_plan is plan` (fast-path identity) and `apply()` still applies optimizer's `only_fields`. Pass.
- Test 3 (consumer `.defer("name")`): asserts `delta_plan is plan` — `.defer()` correctly distinguished from `.only()` because `deferred_loading[1]` is True under defer mode, so helper returns None. Pass.
- Test 4 (chained `.only().only()`): Django collapses to the last call's argument set with `defer_flag=False`, helper detects it, drop applies. Pass.

Do not change top-level `Status:` line.

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/optimizer/plans.py:82-95` — `OptimizationPlan.is_empty` docstring: appended the sentence "``cacheable`` is metadata about cache reuse and is excluded from the emptiness check." so a future maintainer reading the docstring alone understands why an empty-but-uncacheable plan still returns `True` (and that `extension.py:572`'s early-exit gate is still hit). Google docstring convention, ≤110 line length, no logic change.

### Findings disposition

- **L1 (`_prefetch_lookup_paths` bypasses `_lookup_path`):** deferred per artifact prose ("Cosmetic; the practical risk is low because both call sites would be obvious to fix together if Django ever renamed the attribute"). No edit.
- **L2 (`runtime_path_from_path` redundant `str(key)`):** deferred per artifact prose ("Trivial; flag for the next pass that touches this function"). No edit.
- **L3 (`is_empty` docstring missing `cacheable` mention):** addressed — one-sentence addition (see above).

### `apply()` / `diff_plan_for_queryset` docstring verification

- `diff_plan_for_queryset` (`plans.py:326-385`) docstring already covers the new `only_fields` reconciliation rule (lines 346-358 in the source), describing the chained-`.only()` replace-not-merge semantics and the conservative consumer-wins drop. The logic pass landed the documentation alongside the body change; no further edit needed.
- `apply()` (`plans.py:121-129`) docstring is unchanged. The order-of-application ("Applies in order: only() → select_related() → prefetch_related()") and the rationale paragraph still accurately describe `apply()`'s own behaviour — the consumer-`.only()` drop happens upstream in `diff_plan_for_queryset`, not inside `apply()`. Left as-is per the artifact's comment-pass instructions.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged; the standing COM812-vs-formatter warning is project-config, not fix-induced).
- `uv run ruff check --fix .` — pass (All checks passed!).
- pytest not run (comment-only pass; logic-pass tests already verified by Worker 3).

### Notes for Worker 3

- Single-sentence docstring addition only. No logic touched. No new tests. No `apply()` docstring change (logic pass already updated `diff_plan_for_queryset`'s docstring; `apply()`'s docstring remains accurate as-is).

---

## Changelog disposition

### Warranted?

**Warranted — deferred to maintainer.** No `CHANGELOG.md` edit made.

### Reason

This cycle fixes a real consumer-visible bug: `OptimizationPlan.diff_plan_for_queryset` now honours consumer-applied `QuerySet.only(...)` by dropping the optimizer's own `only_fields`, rather than letting `apply()` silently overwrite the consumer's column projection. Django's `QuerySet.only(...).only(...)` chaining **replaces** rather than merges the deferred-loading field set, so the pre-fix behaviour could silently strip columns a consumer's `DjangoType.get_queryset` had restricted — including columns restricted to enforce a permission boundary or to constrain per-row materialisation cost. The fix is behaviour-changing for any consumer relying on `.only()` on their returned queryset, which is exactly the kind of consumer-visible bug fix a `[Fixed]` changelog entry exists to record.

A reasonable `[Fixed]`-class entry under `0.0.6`:

> `DjangoOptimizerExtension`: `OptimizationPlan.diff_plan_for_queryset` now honours consumer-applied `QuerySet.only(...)` by dropping the optimizer's own `only_fields`, preventing silent override of consumer column projections (Django chained `.only()` replaces rather than merges).

### What was done

No `CHANGELOG.md` edit. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed.") and the active plan (`docs/review/review-0_0_6.md` does not authorize a changelog pass for this cycle item), the entry is **deferred to the maintainer** for placement at release time. The Fix report and the docstring updates inside `plans.py` already document the behaviour change for future readers; the maintainer can lift the suggested entry above verbatim, or restate it in the project's preferred phrasing.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

---

## Iteration log

- _pending_

## Verification (Worker 3, pass 2)

- **Comment verification outcome:** `is_empty` docstring sentence accurate; deferrals captured. Accepted.
- **Changelog verification outcome:** Warranted-but-deferred is the right disposition — real consumer-visible bug fix, but the active plan does not authorize edits. Worker 2's suggested entry text is preserved in the artifact so the maintainer can lift it verbatim at release time. Accepted.
- **Verification outcome:** cycle accepted; verified
