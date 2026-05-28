# Post-hunt verification review — `build-021-filters-0_0_8`

Scope: a verification pass over the finished `docs/bug_hunt/bug_hunt.fe3151f.md`
hunt, comparing every per-file `Result:` summary against the actual `.py`
source at `HEAD` (`f2c824e`). All 28 file sections were reconciled with the
current code; the 5 "Fixed" claims were re-verified against source + tests, and
the 23 "No issues" verdicts were independently re-audited (including the 5 files
that review rounds 3–5 modified *after* the hunt wrote its verdict).

Headline: **no confirmed outstanding defects in the framework code.** Every
`[Bug]`-tier finding from the hunt and from review rounds 1–5 is resolved in
source and backed by a passing pinning test. The items below are
state/hygiene/docs actions plus one low-severity robustness note — none block a
`0.0.8` cut.

Severity legend:
- **[Bug]** — incorrect behavior or crash risk on a realistic input.
- **[Risk]** — fragile design, hidden coupling, or subtle edge case.
- **[Cleanup]** — dead code, naming, doc, or hygiene nit.

---

## What was verified against source

| Hunt "Fixed" claim | Source location | Pinning test | Status |
| --- | --- | --- | --- |
| `conf.py` — `Settings.__getattr__` recursion guard | [conf.py:145](django_strawberry_framework/conf.py:145) | `test_settings_uninitialized_user_settings_does_not_recurse`, `test_settings_normalization_attribute_error_does_not_recurse` | **Confirmed** |
| `filters/base.py` — GlobalID `None` guard | [base.py:251](django_strawberry_framework/filters/base.py:251), [base.py:267](django_strawberry_framework/filters/base.py:267) | `test_global_id_filter_passes_through_none`, `test_global_id_multiple_choice_filter_passes_through_none` | **Confirmed** |
| `filters/factories.py` — unhashable-`Meta` cache crash | [factories.py:158](django_strawberry_framework/filters/factories.py:158) (`_make_hashable`) | `test_get_filterset_class_supports_unhashable_meta_values`, `test_make_cache_key_structurally_equivalent_metas_share_a_slot` | **Confirmed** |
| `filters/inputs.py` — `lookup_token` grouping when field name ∈ `LOOKUP_NAME_MAP` | [inputs.py:600](django_strawberry_framework/filters/inputs.py:600) | `tests/filters/test_inputs.py:244` (traversed-relation grouping) | **Confirmed** |
| `filters/sets.py` — logical-branch permission bypass + request-context loss | [sets.py:793](django_strawberry_framework/filters/sets.py:793) (branch recursion), [sets.py:933](django_strawberry_framework/filters/sets.py:933) (request propagation), [sets.py:851](django_strawberry_framework/filters/sets.py:851) (`_validate_form_or_raise`) | `test_run_permission_checks_recurses_into_logical_branches` (+ 6 more) | **Confirmed** |

The 23 "No issues" sections were re-read against current source — all hold,
including `registry.py`, `types/base.py`, `types/definition.py`,
`types/finalizer.py`, `types/relay.py`, which were edited in rounds 3–5 after the
hunt's verdict was written. The highest-risk later changes
(`definition.py`'s `registry.is_finalized()`-gated `_related_target_cache`, and
`finalizer.py`'s orphan-before-materialize reorder) are sound.

All 149 tests across the five affected modules pass against the current working
tree (`uv run pytest … --no-cov`).

---

## Things that need to change (as of now)

### [Risk] Five valid fixes are sitting uncommitted in the working tree
The hunt's "Fixed" claims for `conf.py` and `filters/factories.py` describe edits
that exist **only in the working tree** — they are in no commit:

```
 M django_strawberry_framework/conf.py
 M django_strawberry_framework/filters/factories.py
 M tests/base/test_conf.py
 M tests/filters/test_base.py
 M tests/filters/test_factories.py
```

The code is correct and the tests pass, but until these are committed the
`conf.py` recursion guard and the `factories.py` `_make_hashable` cache fix are
not actually landed. **Action:** commit these five files (the recursion guard +
the unhashable-`Meta` cache fix and their tests) so the hunt's "Fixed" status is
real. This is the single most actionable item.

### [Cleanup] `_make_hashable` normalizes `dict` keys but not `set` ordering
[filters/factories.py:158-164](django_strawberry_framework/filters/factories.py:158)

```python
def _make_hashable(v: Any) -> Any:
    if isinstance(v, dict):
        return tuple(sorted((k, _make_hashable(val)) for k, val in v.items()))   # sorted
    if isinstance(v, (list, tuple, set, frozenset)):
        return tuple(_make_hashable(item) for item in v)                          # NOT sorted
    return v
```

The `dict` branch sorts (so key order is irrelevant), but the
`set`/`frozenset` branch preserves iteration order. `_make_cache_key` accepts a
`set`-shaped `Meta.fields` (`isinstance(fields, (list, tuple, set))`), so two
structurally-equal `set` inputs are *not guaranteed* to collapse onto the same
cache slot. This is **not a correctness bug** — a cache miss merely regenerates
an identical `FilterSet` class — and `Meta.fields` as a `set` is unconventional,
so severity is Low. If touched: sort the `set`/`frozenset` branch when elements
are orderable (fall back to insertion order on `TypeError` for mixed-type
members), mirroring the `dict` branch, and extend
`test_make_cache_key_structurally_equivalent_metas_share_a_slot` with a
set-ordering case. Defer until a consumer actually keys a dynamic filterset off
a `set` of fields.

### [Cleanup] Hunt document summaries are stale relative to current source
`docs/bug_hunt/bug_hunt.fe3151f.md` is accurate-but-incomplete for files that
received further work in review rounds 3–5 (which landed *after* each `Result:`
line was written):

- **`filters/sets.py`** — the summary records only the round-1/2 fix
  ("logical-branch permission bypass and Medium request context loss"). The
  current file also carries: UNSET-in-operator-bag guards, cross-branch
  permission dedup (`_fired: dict[type, set[str]]`), the `_MAX_LOGIC_DEPTH`
  recursion cap, and the proxy/MTI carve-out. None are reflected in the
  one-liner.
- **`filters/inputs.py`** — the `Result:` footnote says the fix was
  "committed/pushed on branch `bugfix/inputs-lookup-token-grouping`." That
  branch was deleted; the commit (`a70f98b`) now lives on
  `build-021-filters-0_0_8`. The fix is preserved — only the branch reference is
  stale.

**Action (optional):** refresh those summaries, or note that per-file `Result:`
lines reflect the *first* fix that landed during the hunt, not subsequent review
hardening.

---

## Already resolved (no action — verified in source)

Every round-5 follow-up observation is resolved at `HEAD`:

1. **Cross-branch permission dedup** — `_fired` is now a `dict[type, set[str]]`
   threaded into child-filterset recursion ([sets.py:779](django_strawberry_framework/filters/sets.py:779)),
   so a same-class child re-entered from sibling branches dedups against its
   prior fired set.
2. **Proxy-model test fixture at module scope** — `ShelfProxy` is declared at
   module scope ([tests/filters/test_sets.py:35](tests/filters/test_sets.py:35)),
   not inside the test body.
3. **`_logic_depth` declared at class scope** — [sets.py:151](django_strawberry_framework/filters/sets.py:151)
   (`_logic_depth: int = 0`), so the depth-counter hand-off is visible to static
   analysis.
4. **`bare` threaded through recursion** — `_run_permission_checks` accepts a
   `_bare` parameter instead of allocating `object.__new__(cls)` per level.
5. **`_MAX_LOGIC_DEPTH` overridable** — promoted to
   `ClassVar[int] = 8` on `FilterSet` ([sets.py:143](django_strawberry_framework/filters/sets.py:143)),
   so subclasses can override the cap.

One non-actionable note carried from the optimizer re-audit:
`optimizer/extension.py`'s plan-cache hit/miss counters are unlocked under
concurrent async, but this is a *documented* best-effort trade-off — cache
*correctness* is unaffected (a missed insert or double-evict only lowers hit
rate). No change warranted.

---

## Recap

The framework code is in shippable shape for `0.0.8`. The only thing standing
between "verified-correct in the working tree" and "landed" is the **commit of
the five uncommitted files**. The remaining items are a Low-severity cache-key
robustness nit (defer) and documentation freshness on the hunt log itself.
