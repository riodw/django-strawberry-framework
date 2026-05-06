# Review: `django_strawberry_framework/optimizer/plans.py`

## High:

None.

## Medium:

### `OptimizationPlan` is mutable (non-frozen) and shared via the extension's plan cache

The class is `@dataclass` (not `@dataclass(frozen=True)`), so cached plans can be mutated by any caller that holds a reference. Today, `diff_plan_for_queryset` uses `replace(plan, ...)` to produce a fresh copy when reconciliation changes the shape, which is the right pattern. But nothing in the type itself prevents a future caller from doing `plan.select_related.append(...)` on a cached plan and silently corrupting subsequent cache hits. The cache lives in `DjangoOptimizerExtension._plan_cache` and is process-scoped per extension instance — a single accidental mutation contaminates every later request that hits the same cache key.

Two viable mitigations:

- **Soft**: keep the dataclass mutable, but add a comment in this file's class docstring noting the cache invariant ("cached plans must be treated as immutable; use `dataclasses.replace` to derive a modified plan") and document that the walker is the only writer.
- **Hard**: convert to `@dataclass(frozen=True)` and switch the walker from `plan.select_related.append(...)` to a builder pattern that constructs the final plan once. This is a bigger change but eliminates the class of bug.

Recommend the soft mitigation in this cycle (one comment update, no behaviour change), and track the hard mitigation as a follow-up if the walker accumulates more in-place mutations.

```django_strawberry_framework/optimizer/plans.py:35:69
@dataclass
class OptimizationPlan:
    """Immutable-ish bag of optimizer directives for one root queryset.
    ...
    """
    select_related: list[str] = field(default_factory=list)
    ...
```

## Low:

### `prefetch_related: list[Any]` could be `list[str | Prefetch]`

The docstring already says the field carries strings or `django.db.models.Prefetch` objects. Tightening the type under `TYPE_CHECKING` (using `if TYPE_CHECKING: from django.db.models import Prefetch`) gives consumers and tooling the right shape. Comment polish — defer to comment pass.

```django_strawberry_framework/optimizer/plans.py:46:53
prefetch_related: list[Any] = field(default_factory=list)
```

### `getattr(queryset.query, "select_related", False)` — `.query` is assumed to exist

`diff_plan_for_queryset` reads `queryset.query.select_related`. Django's `QuerySet.query` is always present, so this is safe in practice, but the rest of the function uses `getattr(..., default)` defensively (`_prefetch_related_lookups`, `prefetch_to`, etc.). For consistency, either change to `getattr(getattr(queryset, "query", None), "select_related", False)` and short-circuit on `None`, or accept the asymmetry as "we trust Django's QuerySet contract."

```django_strawberry_framework/optimizer/plans.py:239:239
already_select = _flatten_select_related(getattr(queryset.query, "select_related", False))
```

### `queryset.prefetch_related(None)` clearing pattern is non-obvious

`new_queryset = queryset.prefetch_related(None)` clears existing prefetches, then `prefetch_related(*keep)` adds the kept ones back. This is a real Django idiom — passing `None` to `prefetch_related` resets the prefetch list — but the line carries no comment, and a reader unfamiliar with the idiom may "fix" it to a chained call. Add a one-line comment. Comment polish — defer.

```django_strawberry_framework/optimizer/plans.py:265:272
new_queryset = queryset
if paths_to_strip:
    keep = tuple(
        entry for entry in consumer_pf if getattr(entry, "prefetch_to", entry) not in paths_to_strip
    )
    new_queryset = queryset.prefetch_related(None)
    if keep:
        new_queryset = new_queryset.prefetch_related(*keep)
```

### `is_empty` checks five fields — would benefit from a tuple-driven check

`is_empty` enumerates every list field individually. Adding a sixth field requires remembering to update this property, which is the kind of "easy to forget" change the type system cannot catch. Replacing with `not (self.select_related or self.prefetch_related or self.only_fields or self.fk_id_elisions or self.planned_resolver_keys)` does not help; a more durable shape would iterate over the dataclass fields. But the boilerplate cost outweighs the benefit at five fields. Note for future review only.

```django_strawberry_framework/optimizer/plans.py:71:80
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

- Module docstring lists every field on `OptimizationPlan` with the directive each one drives, and explains the role of `cacheable` (per-request `Prefetch.queryset` may close over `info.context`, so plans built with `DjangoType.get_queryset` overrides are correctly excluded from the cache).
- `apply()` documents and enforces the correct order: `only()` → `select_related()` → `prefetch_related()`. The order matters and the docstring says why.
- `_flatten_select_related` handles all three Django shapes (`False`, `True`, dict) and explicitly justifies why `True` (wildcard) is treated as no overlap — that is the right call to preserve nullable-FK explicit entries.
- `diff_plan_for_queryset` is the most complex function and its docstring is the longest in the file; it reads as a spec document for the reconciliation logic, including the lossless-absorption case that prevents the "lookup already seen with a different queryset" Django ValueError.
- `_optimizer_can_absorb` enumerates the three preconditions for absorption with a numbered list in the docstring; the implementation matches one-for-one.
- `_prefetch_lookup_paths` correctly recurses through nested `Prefetch.queryset._prefetch_related_lookups`, which is what makes nested optimizer plans (`Prefetch("items", queryset=...prefetch_related("entries"))`) reconcilable against consumer plain-string descendants.
- `resolver_key` and `runtime_path_from_*` are simple, deterministic, and used by both walker and resolvers — single source of truth for branch-sensitive keys.
- `replace(plan, ...)` is the only path that produces a modified plan, so the cache invariant is honored as long as no future caller mutates a plan in place (see Medium item).
- 100% line coverage in the package suite.

---

### Summary:

`plans.py` carries the optimizer's data model and the most subtle reconciliation logic in the subsystem. The Medium item is a documentation-or-API hardening choice: today's `OptimizationPlan` is mutable and shared through the cache, which is fine because every writer honors the `replace`-not-mutate invariant, but nothing in the type enforces that. Soft fix: pin the invariant in the class docstring. Hard fix: freeze the dataclass and convert the walker to a builder pattern; track separately. Low items are typing/comment polish on `prefetch_related`'s element type, the `queryset.query` access, the `prefetch_related(None)` clearing idiom, and a note on `is_empty`'s field-by-field enumeration.

---

### Worker 3 verification

- Medium fix: applied the soft mitigation. `OptimizationPlan` class docstring now spells out the cache invariant: cached / handed-off plans must be treated as immutable, callers use `dataclasses.replace`, the dataclass is intentionally not `frozen=True` because the walker accumulates entries during construction. The hard mitigation (freeze + builder) is recorded as a follow-up; not implemented in this cycle to keep the change scope-bounded.
- Low fix 1: `prefetch_related` annotation tightened to `list[str | Prefetch]` with a `TYPE_CHECKING` import of `Prefetch` (gated by `# pragma: no cover`).
- Low fix 3: comment added above the `prefetch_related(None)` clear-and-rebuild block explaining it is the documented Django reset idiom.
- Low items not addressed: `getattr(queryset.query, ...)` consistency nit and the `is_empty` enumeration concern. Both deferred — the first is a defensive-style choice the file already makes asymmetrically, and the second is a five-field property that adding a field to is rare enough not to be a real maintenance burden today.
- No new tests required: all changes are typing/comment polish or invariant documentation; no behaviour change.
- Validation: `uv run ruff format` and `uv run ruff check` clean; `uv run pytest -q` -> 351 passed, 4 skipped, 100% coverage.
- CHANGELOG: not updated. No user-visible behaviour change.
- Scope: changes confined to `django_strawberry_framework/optimizer/plans.py`.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.

---

### Helper-surfaced follow-ups (post-cycle audit)

This section was added after the cycle was reviewed. Running `scripts/review_inspect.py` on `plans.py` post-cycle surfaced one in-cycle defect (now fixed) and three forward-looking follow-ups for the next release.

- **Fixed in this audit pass — duplicate docstring summary on `runtime_path_from_info` and `runtime_path_from_path`.** Both functions carried the same one-line summary ("Return a GraphQL response path tuple with list indexes stripped."). Reviewers and tooling could not distinguish them from the symbol-overview docstring summary alone. Replaced with two distinct docstrings: `runtime_path_from_info` describes itself as the thin wrapper that delegates to `runtime_path_from_path`; `runtime_path_from_path` describes the linked-list walk and the integer-key-skipping invariant. The full test suite passes (353 passed, 100% coverage); no behaviour change.
- **`prefetch_to` repeated literal (4x) and `_prefetched_related_lookups` repeated literal (2x).** These are `getattr(entry, "prefetch_to", entry)` / `getattr(qs, "_prefetched_related_lookups", None)` patterns spread across `diff_plan_for_queryset`, `_optimizer_can_absorb`, and `_prefetch_lookup_paths`. They are documented Django-private contracts (`Prefetch.prefetch_to` and `QuerySet._prefetched_related_lookups`) but the duplicated string keys are the kind of thing a future Django rename will silently break. Defining `_PREFETCH_TO = "prefetch_to"` / `_PREFETCH_LOOKUPS = "_prefetched_related_lookups"` module constants — or a `_lookup_path(entry)` / `_prefetch_lookups_of(qs)` helper pair — would centralize the fragility. Pure refactor; no behaviour change.
- **`diff_plan_for_queryset` hotspot at 95 lines / 10 branches.** The original Medium item flagged the cache invariant; the helper makes the function-length concern explicit. The function has two clearly separable halves: the `select_related` reconciliation (lines ~239-241) and the `prefetch_related` reconciliation (lines ~242-272). Splitting into `_diff_select_related(plan, queryset)` and `_diff_prefetch_related(plan, queryset)` would let `diff_plan_for_queryset` stay as the orchestrator and make the per-side reconciliation logic testable in isolation.

**Status (post-audit implementation pass):** both remaining follow-ups addressed (the duplicate docstring was already fixed in the audit pass itself).

- Helper pair added: `_lookup_path(entry)` (centralizes `getattr(entry, "prefetch_to", entry)`) and `_consumer_prefetch_lookups(queryset)` (centralizes `list(getattr(qs, "_prefetch_related_lookups", ()) or ())`). Used in `_diff_prefetch_related` and `_prefetch_lookup_paths`. The `prefetch_to` literal still appears in `_prefetch_lookup_paths` because that function uses a *different* default semantics (`None` vs the entry itself) for non-Prefetch cases — same name, different contract; not a safe consolidation target.
- `diff_plan_for_queryset` split: now ~12 lines of orchestration calling `_diff_select_related(plan.select_related, queryset)` and `_diff_prefetch_related(plan.prefetch_related, queryset)`. Each helper is independently testable and named after the reconciliation it performs. The full reconciliation rules docstring stays on `diff_plan_for_queryset` (the orchestrator) so consumers reading the public-ish API see the contract in one place.
- Validation: `uv run pytest -q` -> 354 passed, 100% coverage.
