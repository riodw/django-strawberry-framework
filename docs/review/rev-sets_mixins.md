# Review: `django_strawberry_framework/sets_mixins.py`

Status: verified

## DRY analysis

- None — this module IS the set-family DRY chokepoint (the 0.0.9 DRY pass, `docs/feedback.md` Major 3). Every symbol here exists to single-site machinery that `FilterSet`/`OrderSet` would otherwise carry as byte-parallel copies: `ClassBasedTypeNameMixin.type_name_for` (consumed by `filters/inputs.py::_input_type_name_for` at `filters/inputs.py:205` + `filters/inputs.py:713`, `orders/inputs.py::_input_type_name_for` at `orders/inputs.py:144`, `utils/inputs.py:343/376/398`), `RelatedSetTargetMixin._bind_owner/_resolved_target/_set_target` (wrapped by `filters/base.py::RelatedFilter` at `filters/base.py:455/466/470` + `orders/base.py::RelatedOrder` at `orders/base.py:70/82/86`), `collect_related_declarations` (called once each from `filters/sets.py:194` + `orders/sets.py:118`), `expanded_once` (called once each from `filters/sets.py:385` + `orders/sets.py:227`), and `SetLifecycleAttrs.binding_attrs` (consumed by `utils/inputs.py:265`). The two call sites per helper are the deliberate two-family fan-out the module was built to serve; there is no third near-copy to hoist and no repeated literal to name (the 2x `"InputType"` is two distinct class-attribute defaults — `_root_type_suffix` and `_field_type_suffix` — not a shared constant). Defer any further consolidation until the `AggregateSet`/`fieldsets` family lands (`WIP-ALPHA-028-0.0.8` and later); at that point re-confirm all three families still share the exact `_target_attr`/`_owner_attr` + `cache_attr`/`guard_attr` parameterization rather than diverging.

## High:

None.

## Medium:

None.

## Low:

### `expanded_once` `cached is not None` vs truthiness (no-action, pre-empt re-flag)

`expanded_once` reads `cached = cls.__dict__.get(cache_attr); if cached is not None: return cached` (`sets_mixins.py::expanded_once`). The `is not None` guard — rather than a plain truthiness check — is load-bearing and correct: `build()` writes an `OrderedDict` (`filters/sets.py:375` writes `cls._expanded_filters = all_filters`; `orders/sets.py:219` writes `cls._expanded_fields = fields`), and a set with zero filters/fields legitimately produces an *empty* `OrderedDict`, which is falsy but not `None`. A truthiness check would re-run `build()` on every access for an empty-but-fully-expanded set. The `None` sentinel also correctly distinguishes "never built" / "built but deliberately not cached (unresolved string forward-refs remain)" from "built and cached as empty". Recorded only to pre-empt a future reviewer mistaking the `is not None` for an over-careful truthiness check; it is the right comparison and needs no change.

### `expanded_once` single-threaded reentry-guard contract (no-action, forward-looking)

The reentry guard `guard_attr` is a class-level boolean flag (`setattr(cls, guard_attr, True)` … `finally: setattr(cls, guard_attr, False)`), not a `threading.local`, and the docstring explicitly documents the single-threaded contract: expansion runs during `finalize_django_types()` (single-threaded) once per class. The docstring already carries the verbatim deferral trigger ("Do not introduce a `threading.local` here without a real consumer call path requiring it"). Defer until a consumer call path exercises the same set class from multiple threads concurrently outside finalize; only then revisit the flag's storage. No action now — the inline trigger already governs this.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module reuses `utils/strings.py::pascal_case` in place of the cookbook's `stringcase.pascalcase` (`type_name_for`, `sets_mixins.py:91`) and `django.utils.module_loading.import_string` for the two-attempt lazy resolution (`resolve_lazy_class`, `sets_mixins.py:131/135`). `RelatedSetTargetMixin` extends `LazyRelatedClassMixin` so the related-target machinery reuses the one resolution body rather than re-implementing it. Every `__all__` export has live first-party callers (cited in `## DRY analysis`); no orphaned/never-called public symbol — shape #5's act-now-vs-defer orphan axis does not apply.
- **New helpers considered.** A shared constant for the 2x `"InputType"` literal was considered and rejected: the two occurrences are independent class-attribute defaults (`_root_type_suffix`, `_field_type_suffix`) on `ClassBasedTypeNameMixin` that `FilterSet` overrides asymmetrically (`_field_type_suffix = "FilterInputType"` at `filters/sets.py:309`, root kept as `"InputType"`); naming a constant would couple two defaults that subclasses tune separately. No further helper at this granularity — the module is already the helper layer.
- **Duplication risk in the current file.** The thin-wrapper pattern (`RelatedFilter.bind_filterset`/`.filterset` over `_bind_owner`/`_resolved_target`, `RelatedOrder.bind_orderset`/`.orderset` over the same) lives in the consumer modules, not here; this module exposes the single shared implementation. The two-call-site fan-out of every helper is intentional two-family design, not accidental duplication.

### Other positives

- **Cache isolation via `cls.__dict__.get`.** `expanded_once` reads from the class's OWN `__dict__` (not `getattr`), correctly preventing a subclass from inheriting a parent's completed expansion via MRO and preventing an in-flight class (metaclass runs `super().__new__` → `get_filters` before stamping `related_filters`) from serving a half-built result. The rationale is documented inline.
- **Idempotent bind.** `_bind_owner` uses `if not hasattr(self, self._owner_attr)` so a second (possibly divergent) bind is a no-op; strict cross-owner mismatch is deferred to finalize, which is the correct layer to name the offending set.
- **`ImportError` propagation contract.** `resolve_lazy_class` lets the original `ImportError` propagate unchanged when `bound_class` is falsy, and on the module-prefixed second attempt surfaces only that single attempted path — matching the documented `RelatedOrder` GLOSSARY contract verbatim (no rewrap into `ConfigurationError` here; that happens a layer up at finalize).
- **`type_name_for` empty-token guard.** Raising `ConfigurationError` when a PascalCased field path collapses to `""` (`field_path` of `""`/`"_"`/`"__"`) surfaces the real cause at the call site and prevents a silent type-name collision with the root type or a sibling field's bag class.
- **`SetLifecycleAttrs` frozen dataclass.** Single source for the `(owner, cache, guard)` attr-name strings, consumed via `binding_attrs` by `utils/inputs.py:265` for the `registry.clear()` reset — removes the re-spelled-tuple drift risk across each family's class body, expansion, and clear path.
- **GLOSSARY accuracy.** The `RelatedOrder` entry (`docs/GLOSSARY.md:1057`) names `sets_mixins.LazyRelatedClassMixin` as the shared resolution home and describes the two-attempt resolution + unchanged-`ImportError` propagation verbatim against `resolve_lazy_class`. No drift. No dedicated GLOSSARY entry exists for the helper symbols themselves (they are internal set-family machinery, not a consumer contract surface) — correct.

### Summary

`sets_mixins.py` is the package-root set-family DRY chokepoint that the 0.0.9 DRY pass single-sited (naming rule, lazy-class resolution, related-declaration collect-and-bind, expansion cache + reentry guard, and lifecycle-attr descriptor). The cycle diff against the baseline (`6c7f1645`) and HEAD are both empty — the file is unchanged this cycle and was reviewed as standing code. Every helper has exactly the two-family fan-out (`FilterSet`/`OrderSet`) it was built for, all call shapes verified consistent at their consumer sites, and the load-bearing subtleties (`cls.__dict__.get` own-class read, `cached is not None` vs truthiness, idempotent `hasattr`-gated bind, single-threaded guard, asymmetric `_root`/`_field` suffix defaults) are correct and documented inline. No High, no Medium; two no-action Lows recorded only to pre-empt re-flagging, both already governed by their own inline contracts/triggers. GLOSSARY accurate, no drift. No-findings-of-consequence + no-source-edit cycle (shapes #1 → #5); bare `Status: fix-implemented`; both ruff runs clean (289 files unchanged).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 289 files left unchanged.
- `uv run ruff check --fix .` — pass; all checks passed.

### Notes for Worker 3
- Cycle diff `git diff 6c7f1645f86466557e97f013f73ac26cedfffccb -- django_strawberry_framework/sets_mixins.py` is empty; `git diff HEAD -- …` also empty. File unchanged this cycle, reviewed as standing code.
- No High, no Medium. Two Lows are no-action / forward-looking only:
  - `expanded_once` `cached is not None` — the `is not None` (not truthiness) comparison is correct because empty-but-expanded sets cache an empty falsy `OrderedDict`; no change.
  - `expanded_once` single-threaded guard — inline docstring already carries the verbatim deferral trigger; no change.
- No GLOSSARY-only fix in scope. GLOSSARY `RelatedOrder` entry (`docs/GLOSSARY.md:1057`) verified accurate against `resolve_lazy_class`; no drift, no edit warranted.
- Static helper overview at `docs/shadow/django_strawberry_framework__sets_mixins.overview.md` used as-is (plan-time `--all` sweep); not regenerated.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring changes — docstrings on all six exported symbols are accurate and surface the load-bearing rationale (own-`__dict__` cache read, single-threaded guard contract, idempotent bind, `ImportError` propagation, empty-token guard). No stale comments, no TODO-anchor issues in this module (static helper reports 0 TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source edit this cycle (internal set-family machinery, no consumer-visible behavior change). Per `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" and the active plan `docs/review/review-0_0_11.md` is silent on changelog edits for this item.

---

## Verification (Worker 3)

### Logic verification outcome

Shape #5 no-source-edit cycle confirmed. Zero-edit proof established two ways: `git diff 6c7f1645f86466557e97f013f73ac26cedfffccb -- django_strawberry_framework/sets_mixins.py` empty AND `git diff HEAD -- …` empty; `git diff --stat 6c7f1645 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` entirely empty (clean run, no #33 concurrent dirt to attribute this cycle). All three Worker 2 sections open with "Filled by Worker 1 per no-source-edit cycle pattern." No High, no Medium — both `None.` genuine. Independent logic read confirms no defect was skipped that would force a source edit:

- **Low 1 — `cached is not None` vs truthiness (no-action, correct):** Verified in source — `expanded_once` reads `cached = cls.__dict__.get(cache_attr)` and gates on `if cached is not None` (`sets_mixins.py::expanded_once`, the `cached is not None` line). Both cache-write sites write a possibly-empty `OrderedDict`: `cls._expanded_filters = all_filters` (`filters/sets.py` #"cls._expanded_filters = all_filters", `all_filters` built from `get_base()`/`OrderedDict`) and `cls._expanded_fields = fields` (`orders/sets.py` #"cls._expanded_fields = fields", `fields` an `OrderedDict`). An empty-but-fully-expanded set caches a falsy-but-non-`None` `OrderedDict`; a truthiness check would re-run `build()` on every access. The `is not None` is load-bearing and correct — not a missed Low. The `isinstance(..., str)` cache-write gating ("no unresolved string forward-refs remain") is present at both sites and matches the docstring's "built but deliberately not cached" sentinel rationale.
- **Low 2 — single-threaded reentry guard (no-action, forward-looking):** The docstring carries the verbatim deferral trigger "Do not introduce a `threading.local` here without a real consumer call path requiring it" (`sets_mixins.py::expanded_once`). The `on_reentry` asymmetry the Low's context depends on is confirmed: filter side passes `on_reentry=get_base` (`filters/sets.py` #"on_reentry=get_base"); order side omits it / passes `None` (`orders/sets.py` `expanded_once(` call has no `on_reentry` arg). Guard is the class-level boolean flag with `try/finally` clear, as documented. Genuine defer-with-trigger, no edit owed now.
- **Suffix-default asymmetry:** Defaults `_root_type_suffix = "InputType"` and `_field_type_suffix = "InputType"` (`sets_mixins.py::ClassBasedTypeNameMixin`). `FilterSet` overrides only `_field_type_suffix = "FilterInputType"` (`filters/sets.py` #"_field_type_suffix"); order side deliberately does NOT override (`orders/sets.py` #"The order side does NOT override"). Two distinct class-attribute defaults tuned asymmetrically by subclasses — the "no shared constant" rejection in `What looks solid` is correct.

### DRY findings disposition

Single DRY bullet is the justified `None` — this module IS the set-family DRY chokepoint; every helper has exactly the deliberate two-family (`FilterSet`/`OrderSet`) fan-out it was built to serve, with no third near-copy to hoist. Correctly defers further consolidation to the `AggregateSet`/`fieldsets` family with an explicit re-confirm trigger. No carry-forward DRY obligation.

### Temp test verification

None — no temp tests created; zero-edit cycle, no behavior to pin beyond existing suite. pytest not run (no test introduced; AGENTS.md #14).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `sets_mixins.py` checkbox in `docs/review/review-0_0_11.md`.

Additional gates: GLOSSARY `RelatedOrder` entry (`docs/GLOSSARY.md` #"The shared Layer-2 module-fallback resolution is a sibling import from `sets_mixins.LazyRelatedClassMixin`") reads accurate vs live `resolve_lazy_class` — names the neutral shared module, the two-attempt resolution (absolute path → module-prefixed fallback), and the unchanged-`ImportError` propagation with no `ConfigurationError` rewrap here (finalize a layer up). No drift; no GLOSSARY-only fix in scope (genuine #5, not a missed #4). Changelog "Not warranted" cites BOTH AGENTS.md and plan silence. `uv run ruff check` → all checks passed; `uv run ruff format --check` → already formatted.
