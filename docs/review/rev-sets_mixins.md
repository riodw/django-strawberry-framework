# Review: `django_strawberry_framework/sets_mixins.py`

Status: verified

## DRY analysis

- None — this module IS the set-family DRY chokepoint (the 0.0.9 DRY pass, `docs/feedback.md` Major 3). Every symbol here exists to single-site machinery that `FilterSet`/`OrderSet` would otherwise carry as byte-parallel copies: `ClassBasedTypeNameMixin.type_name_for` (consumed by `filters/inputs.py::_input_type_name_for` + `filters/sets.py:712`, `orders/inputs.py::_input_type_name_for`, `utils/inputs.py:343/376/398`), `RelatedSetTargetMixin._bind_owner/_resolved_target/_set_target` (wrapped by `filters/base.py::RelatedFilter` + `orders/base.py::RelatedOrder`), `collect_related_declarations` (called once each from `filters/sets.py:177` + `orders/sets.py:111`), `expanded_once` (called once each from `filters/sets.py:368` + `orders/sets.py:220`), and `SetLifecycleAttrs.binding_attrs` (consumed by `utils/inputs.py:265`). The two call sites per helper are the deliberate two-family fan-out the module was built to serve; there is no third near-copy to hoist and no repeated literal to name (the 2x `"InputType"` is two distinct class-attribute defaults — `_root_type_suffix` and `_field_type_suffix` — not a shared constant). Defer any further consolidation until the `AggregateSet`/`fieldsets` family lands (`WIP-ALPHA-028-0.0.8` and later); at that point re-confirm all three families still share the exact `_target_attr`/`_owner_attr` + `cache_attr`/`guard_attr` parameterization rather than diverging.

## High:

None.

## Medium:

None.

## Low:

### `expanded_once` `cached is not None` vs truthiness (no-action, pre-empt re-flag)

`expanded_once` reads `cached = cls.__dict__.get(cache_attr); if cached is not None: return cached` (`sets_mixins.py::expanded_once`). The `is not None` guard — rather than a plain truthiness check — is load-bearing and correct: `build()` writes an `OrderedDict` (`filters/sets.py:358` writes `cls._expanded_filters = all_filters`; `orders/sets.py:212` writes `cls._expanded_fields = fields`), and a set with zero filters/fields legitimately produces an *empty* `OrderedDict`, which is falsy but not `None`. A truthiness check would re-run `build()` on every access for an empty-but-fully-expanded set. The `None` sentinel also correctly distinguishes "never built" / "built but deliberately not cached (unresolved string forward-refs remain)" from "built and cached as empty". Recorded only to pre-empt a future reviewer mistaking the `is not None` for an over-careful truthiness check; it is the right comparison and needs no change.

### `expanded_once` single-threaded reentry-guard contract (no-action, forward-looking)

The reentry guard `guard_attr` is a class-level boolean flag (`setattr(cls, guard_attr, True)` … `finally: setattr(cls, guard_attr, False)`), not a `threading.local`, and the docstring explicitly documents the single-threaded contract: expansion runs during `finalize_django_types()` (single-threaded) once per class. The docstring already carries the verbatim deferral trigger ("Do not introduce a `threading.local` here without a real consumer call path requiring it"). Defer until a consumer call path exercises the same set class from multiple threads concurrently outside finalize; only then revisit the flag's storage. No action now — the inline trigger already governs this.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module reuses `utils/strings.py::pascal_case` in place of the cookbook's `stringcase.pascalcase` (`type_name_for`, `sets_mixins.py:91`) and `django.utils.module_loading.import_string` for the two-attempt lazy resolution (`resolve_lazy_class`, `sets_mixins.py:131/135`). `RelatedSetTargetMixin` extends `LazyRelatedClassMixin` so the related-target machinery reuses the one resolution body rather than re-implementing it.
- **New helpers considered.** A shared constant for the 2x `"InputType"` literal was considered and rejected: the two occurrences are independent class-attribute defaults (`_root_type_suffix`, `_field_type_suffix`) on `ClassBasedTypeNameMixin` that `FilterSet` overrides asymmetrically (`_field_type_suffix = "FilterInputType"` at `filters/sets.py:292`, root kept as `"InputType"`); naming a constant would couple two defaults that subclasses tune separately. No further helper at this granularity — the module is already the helper layer.
- **Duplication risk in the current file.** The thin-wrapper pattern (`RelatedFilter.bind_filterset`/`.filterset` over `_bind_owner`/`_resolved_target`, `RelatedOrder.bind_orderset`/`.orderset` over the same) lives in the consumer modules, not here; this module exposes the single shared implementation. The two-call-site fan-out of every helper is intentional two-family design, not accidental duplication.

### Other positives

- **Cache isolation via `cls.__dict__.get`.** `expanded_once` reads from the class's OWN `__dict__` (not `getattr`), correctly preventing a subclass from inheriting a parent's completed expansion via MRO and preventing an in-flight class (metaclass runs `super().__new__` → `get_filters` before stamping `related_filters`) from serving a half-built result. The rationale is documented inline.
- **Idempotent bind.** `_bind_owner` uses `if not hasattr(self, self._owner_attr)` so a second (possibly divergent) bind is a no-op; strict cross-owner mismatch is deferred to finalize, which is the correct layer to name the offending set.
- **`ImportError` propagation contract.** `resolve_lazy_class` lets the original `ImportError` propagate unchanged when `bound_class` is falsy, and on the module-prefixed second attempt surfaces only that single attempted path — matching the documented `RelatedOrder` GLOSSARY contract verbatim (no rewrap into `ConfigurationError` here; that happens a layer up at finalize).
- **`type_name_for` empty-token guard.** Raising `ConfigurationError` when a PascalCased field path collapses to `""` (`field_path` of `""`/`"_"`/`"__"`) surfaces the real cause at the call site and prevents a silent type-name collision with the root type or a sibling field's bag class.
- **`SetLifecycleAttrs` frozen dataclass.** Single source for the `(owner, cache, guard)` attr-name strings, consumed via `binding_attrs` by `utils/inputs.py:265` for the `registry.clear()` reset — removes the re-spelled-tuple drift risk across each family's class body, expansion, and clear path.
- **GLOSSARY accuracy.** The `RelatedOrder` entry (`docs/GLOSSARY.md:1024`) names `sets_mixins.LazyRelatedClassMixin` as the shared resolution home and describes the two-attempt resolution + unchanged-`ImportError` propagation verbatim against `resolve_lazy_class`. No drift. No dedicated GLOSSARY entry exists for the helper symbols themselves (they are internal set-family machinery, not a consumer contract surface) — correct.

### Summary

`sets_mixins.py` is the package-root set-family DRY chokepoint that the 0.0.9 DRY pass single-sited (naming rule, lazy-class resolution, related-declaration collect-and-bind, expansion cache + reentry guard, and lifecycle-attr descriptor). The cycle diff against the baseline is empty — the file is unchanged this cycle and was reviewed as standing code. Every helper has exactly the two-family fan-out (`FilterSet`/`OrderSet`) it was built for, all call shapes verified consistent at their consumer sites, and the load-bearing subtleties (`cls.__dict__.get` own-class read, `cached is not None` vs truthiness, idempotent `hasattr`-gated bind, single-threaded guard, asymmetric `_root`/`_field` suffix defaults) are correct and documented inline. No High, no Medium; two no-action Lows recorded only to pre-empt re-flagging, both already governed by their own inline contracts/triggers. GLOSSARY accurate, no drift. No-findings + no-source-edit cycle (shapes #1 → #5); bare `Status: fix-implemented`; both ruff runs clean (267 files unchanged).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 267 files left unchanged.
- `uv run ruff check --fix .` — pass; all checks passed.

### Notes for Worker 3
- Cycle diff `git diff a5307410a6e5801612e3ad7b661f707e10dfcd34 -- django_strawberry_framework/sets_mixins.py` is empty; file unchanged this cycle, reviewed as standing code.
- No High, no Medium. Two Lows are no-action / forward-looking only:
  - `expanded_once` `cached is not None` — the `is not None` (not truthiness) comparison is correct because empty-but-expanded sets cache an empty falsy `OrderedDict`; no change.
  - `expanded_once` single-threaded guard — inline docstring already carries the verbatim deferral trigger; no change.
- No GLOSSARY-only fix in scope. GLOSSARY `RelatedOrder` entry (`docs/GLOSSARY.md:1024`) verified accurate against `resolve_lazy_class`; no drift, no edit warranted.
- Static helper overview at `docs/shadow/django_strawberry_framework__sets_mixins.overview.md` used as-is (plan-time `--all` sweep); not regenerated.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring changes — docstrings on all six exported symbols are accurate and surface the load-bearing rationale (own-`__dict__` cache read, single-threaded guard contract, idempotent bind, `ImportError` propagation, empty-token guard). No stale comments, no TODO-anchor issues in this module (the one TODO anchor lives in `filters/sets.py`, out of scope).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source edit this cycle (internal set-family machinery, no consumer-visible behavior change). Per `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" and the active plan `docs/review/review-0_0_10.md` is silent on changelog edits for this item.

---

## Verification (Worker 3)

Terminal-verify of a no-source-edit (shape #5) + no-findings-of-consequence cycle (H0 / M0 / L2, both Lows no-action). Shadow overview (`docs/shadow/django_strawberry_framework__sets_mixins.overview.md`) re-read; source byte-matches it (12 symbols, 9 imports, 0 TODO, 1 control-flow hotspot at `expanded_once`, 2x `"InputType"` literal). Shadow line numbers treated as non-canonical per the dicta.

### Logic verification outcome

Both Lows confirmed genuinely no-action and masking no present defect, re-derived against source (not artifact prose):

- **`expanded_once` `cached is not None` vs truthiness** — load-bearing and correct. The two cache writes are `cls._expanded_filters = all_filters` (`filters/sets.py` #"cls._expanded_filters = all_filters") and `cls._expanded_fields = fields` (`orders/sets.py` #"cls._expanded_fields = fields"), both `OrderedDict`. A set with zero filters/fields produces an empty `OrderedDict` (falsy, not `None`); a truthiness guard at `sets_mixins.py::expanded_once #"if cached is not None"` would re-run `build()` on every access for an empty-but-fully-expanded set. The `None` sentinel correctly distinguishes never-built / built-but-not-cached (unresolved string forward-refs remain) from built-and-empty. Both cache writes are gated on `not isinstance(f._filterset/_orderset, str)` — confirming the "built but deliberately not cached" branch the docstring names. No change.
- **`expanded_once` single-threaded reentry-guard contract** — `guard_attr` is a class-level boolean (`setattr(cls, guard_attr, True)` … `finally: setattr(cls, guard_attr, False)`), not a `threading.local`; the docstring (`sets_mixins.py::expanded_once`) carries the verbatim deferral trigger ("Do not introduce a `threading.local` here without a real consumer call path requiring it"). Forward-looking, governed by its own inline trigger. No change.

Independently sanity-checked the shared-base coupling Worker 1 cleared:
- **Two-family fan-out (chokepoint claim).** `expanded_once` called once each from `filters/sets.py` #"return expanded_once" and `orders/sets.py` #"return expanded_once"; `collect_related_declarations` once each from `filters/sets.py:177` + `orders/sets.py:111`; `RelatedSetTargetMixin` extended only by `RelatedFilter` (`filters/base.py::RelatedFilter`) and `RelatedOrder` (`orders/base.py::RelatedOrder`), both as thin `bind_*`/`.<target>` wrappers over `_bind_owner`/`_resolved_target`/`_set_target`; `SetLifecycleAttrs.binding_attrs` consumed at `utils/inputs.py #"binding_attrs = set_root._lifecycle.binding_attrs"`. Exactly the deliberate two-call-site fan-out; no third near-copy, no accidental duplication.
- **`on_reentry` asymmetry.** Filter side passes `on_reentry=get_base` (self-referential `RelatedFilter` cycle fallback); order side passes none — matches the docstring contract.
- **`cls.__dict__.get` own-class read** prevents a subclass inheriting a parent's completed expansion via MRO and prevents an in-flight class serving a half-built result — confirmed against both build sites' `"related_filters"/"related_orders" in cls.__dict__` guards.
- **Idempotent `hasattr`-gated `_bind_owner`** records the owner once; cross-owner mismatch deferred to finalize.
- **`resolve_lazy_class` `ImportError` propagation** (two-attempt, unchanged-`ImportError` on falsy `bound_class`, module-prefixed second attempt surfaces only that one path) matches the `RelatedOrder` GLOSSARY entry (`docs/GLOSSARY.md` #"sibling import from `sets_mixins.LazyRelatedClassMixin`") verbatim. No drift.
- **Asymmetric suffix defaults.** `ClassBasedTypeNameMixin._root_type_suffix = _field_type_suffix = "InputType"`; `FilterSet` overrides only `_field_type_suffix = "FilterInputType"` (`filters/sets.py:292`), keeps root `"InputType"`; `OrderSet` overrides neither (`orders/sets.py:140` comment confirms). A shared constant for the 2x `"InputType"` would couple two independently-tuned defaults — the DRY=None reject is sound.

Note: the dispatch named `check_<field>_permission` plumbing; that symbol does not live in `sets_mixins.py` (it is filter/order set machinery in `filters/sets.py` / `orders/sets.py`, out of scope). The actual coupling surfaces this module exposes — owner-bind idempotency, lazy-target resolution, the GLOSSARY contract — were verified instead.

### DRY findings disposition

DRY=None accepted. This module IS the set-family chokepoint; every helper has exactly the two-family fan-out it was built for. No third copy to hoist; the 2x `"InputType"` is two distinct class-attribute defaults, not a shared constant. Further consolidation correctly deferred to the `AggregateSet`/`fieldsets` family landing.

### Temp test verification

None — no source edit, no new behavior to pin; the two Lows are verifiable by inspection against existing call sites. No temp tests created.

### Shape #5 checklist

1. `git diff --stat a5307410a6e5801612e3ad7b661f707e10dfcd34 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty; per-file baseline diff of `sets_mixins.py` empty. No dirty owned paths.
2. Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` ✓
3. Both Lows carry their no-action rationale (no verbatim-trigger requirement applies — neither is forwarded; no GLOSSARY-only fix present). ✓
4. Changelog `Not warranted` cites both `AGENTS.md` AND the active plan's silence; `git diff -- CHANGELOG.md` empty; internal-only framing matches the empty diff scope. ✓
5. `uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (all checks passed) on `sets_mixins.py`. ✓

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `sets_mixins.py` checklist box in `docs/review/review-0_0_10.md`.
