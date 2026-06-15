# Review: `django_strawberry_framework/filters/factories.py`

Status: verified

## DRY analysis

- Defer until `orders/factories.py` revives Layer 6 (the TODO anchor at `orders/factories.py` #"TODO(spec-028-orders-0_0_8 Decision 12"): the filter-side Layer-6 trio — `_make_hashable` / `_make_cache_key` / `_create_dynamic_filterset_class` / `get_filterset_class` plus the `_dynamic_filterset_cache` + `_RESERVED_FACTORY_KEYS` module state — is a single-family copy today. When the deferred order-side `get_orderset_class` / `_dynamic_orderset_cache` ships, `_make_hashable` and `_make_cache_key` (pure, family-agnostic dict-to-hashable-key helpers) and the `get_*_class(... ) -> cached | type(name,(Base,),{"Meta":...})` skeleton become a two-family near-copy. Trigger to consolidate: the order TODO anchor is resolved. Shape: hoist `_make_hashable` + `_make_cache_key` into `utils/inputs.py` (they have zero filter-domain coupling) and parameterize a shared `get_dynamic_set_class(cache, base, reserved_keys, **meta)` over the per-family cache dict and base class. Do NOT act before that consumer lands — Layer 6 is itself an unconsumed deferred non-goal on the filter side, so pre-consolidating would build shared machinery for two non-shipped surfaces.

## High:

None.

## Medium:

None.

## Low:

### `_make_cache_key`'s own two `sorted()` calls omit the `key=repr` total-order guard that `_make_hashable` documents as load-bearing

`_make_hashable` (`filters/factories.py::_make_hashable`) sorts its `dict` and `set`/`frozenset` branches with `key=repr` and its docstring states the rationale verbatim: stay total-ordered "even for mixed, mutually-unorderable member or key types (e.g. `{1, "a"}` or `{"a": 1, 0: 2}`)". But `_make_cache_key`'s two own `sorted()` calls do not carry that guard:

```django_strawberry_framework/filters/factories.py:164:181
    if isinstance(fields, dict):
        fields_key: tuple = (
            "dict",
            tuple(sorted((k, _make_hashable(v)) for k, v in fields.items())),
        )
    ...
    extra = tuple(
        sorted(
            (k, _make_hashable(v)) for k, v in safe_meta.items() if k not in {"model", "fields"}
        ),
    )
```

In practice this never raises: both sort `(k, hashable_v)` tuples whose first element `k` is always a `str` (dict-`fields` keys are field names; `extra` keys are `Meta` attribute names), and tuple comparison short-circuits on the unequal first element before ever comparing the heterogeneous second element. The dict-key uniqueness invariant guarantees no two first elements tie. So this is correct today, not a bug.

The Low is internal-consistency only: the module documents mixed-key defence as a property of `_make_hashable` (and `test_make_hashable_dict_branch_supports_mixed_key_types` at `tests/filters/test_factories.py:328-344` pins it), yet `_make_cache_key`'s sibling sorts rely on an unstated "keys are always strings" precondition rather than the same `key=repr` shield. A future change that fed a non-string-keyed dict into `_make_cache_key`'s top-level `fields`/`extra` (not currently reachable) would `TypeError` here while `_make_hashable` would tolerate it. Recommendation: add `key=repr` to both `sorted()` calls for uniformity with the documented helper contract, OR add a one-line comment stating the "keys are field-name / Meta-attr strings, so plain tuple sort is total" precondition so the asymmetry reads as deliberate. No behaviour change either way. Recorded to pre-empt re-flagging, not as a defect requiring a fix.

## What looks solid

### DRY recap

- **Existing patterns reused.** `FilterArgumentsFactory` subclasses the single-sited `utils/inputs.py::GeneratedInputArgumentsFactory` (the 0.0.9 DRY pass, `docs/feedback.md` Major 1) and supplies only the family caches (`input_object_types`, `_type_filterset_registry`) plus the six hook attrs (`_collision_registry_attr` / `_factory_label` / `_family_label` / `_rename_noun` / `_related_attr` / `_related_target_attr`) and the one `_build_input_triples` override — verified symmetric with `orders/factories.py::OrderArgumentsFactory`. The BFS walk, collision check, idempotent cache, and subclass-rejection guard are NOT re-implemented here. `_build_input_triples` delegates to `filters/inputs.py::_build_input_fields` + `_build_logic_fields` (signatures confirmed at `filters/inputs.py:596`/`616`).
- **New helpers considered.** A cross-family hoist of `_make_hashable`/`_make_cache_key`/`get_filterset_class` was evaluated and deferred-with-trigger (see DRY analysis) — pre-consolidating two unconsumed deferred surfaces would add shared machinery before either consumer exists.
- **Duplication risk in the current file.** The 2x `filterset` literal flagged by the static helper is `_related_target_attr = "filterset"` (BFS related-entry target attr) vs. the docstring/error noun — two distinct roles, not a hoist; the family-naming asymmetry vs. the order twin (`orderset`) is exactly what the shared base parameterizes. `_create_dynamic_filterset_class` builds via plain `type(name, (FilterSet,), {"Meta": ...})` rather than graphene-django's `custom_filterset_factory` (spec line 247 drops the `replace_csv_filters` rewrap) — pinned by `test_dynamic_filterset_cache_does_not_replace_csv_filters` (`tests/filters/test_factories.py:425`).

### Other positives

- **`_make_hashable` ordered-vs-unordered contract is correct and tested.** `dict`/`set`/`frozenset` (unordered) sort to a canonical form so structurally-equal declarations collapse to one cache key; `list`/`tuple` (ordered, because a list-shaped `Meta.fields` defines filter order) preserve order. The `repr`-keyed sort keeps mixed unorderable members total-ordered. Equivalence classes pinned across all five branches in `tests/filters/test_factories.py:310-408`.
- **Top-level set-shaped `fields` caveat is documented honestly.** `_make_cache_key`'s docstring states that a top-level `set`-shaped `fields` keys off iteration order (the `"seq"` branch iterates directly), which is `PYTHONHASHSEED`-randomized across processes and also governs generated filter order — and steers callers to `list`/`tuple` when order matters. This is the correct disclosure, not a silent footgun.
- **`get_filterset_class` is honest about being unconsumed.** Docstring + module docstring both state Layer 6 has no source consumer (`DjangoConnectionField` reads the resolved `Meta.filterset_class` sidecar directly; auto-generation is a standing deferred spec-027 Non-goal), and that distinct-meta/same-model collisions surface through the BFS `_type_filterset_registry` check with a documented escape (declare an explicit `filterset_class=`). The cache-no-clear-hook lifecycle is documented inline with the model-identity-keyed rebuild-safety rationale (M-filters-3 review).
- **`_RESERVED_FACTORY_KEYS` stripping** prevents `filterset_base_class` from leaking into the generated `Meta` namespace; pinned by `test_get_filterset_class_strips_reserved_kwargs` (`tests/filters/test_factories.py:445`). The `model is None` guard raises a named `ConfigurationError`, pinned by `test_get_filterset_class_requires_model_when_dynamic`.
- **Unhashable Meta values are supported** end-to-end (`test_get_filterset_class_supports_unhashable_meta_values`, `tests/filters/test_factories.py:464`) — the whole reason `_make_hashable` exists. Subclass rejection of `FilterArgumentsFactory` is pinned at `tests/filters/test_factories.py:501`.
- **GLOSSARY: no drift.** `get_filterset_class` / `_dynamic_filterset_cache` / `FilterArgumentsFactory` / `_make_cache_key` have no dedicated GLOSSARY entries (internal Layer-5/6 machinery, correct — not consumer-contract surfaces); `Meta.filterset_class` (GLOSSARY.md:688) describes the finalizer's `get_filters()` -> BFS factory -> materialize chain accurately and does not over-promise the unconsumed Layer-6 auto-generation path.

### Summary

A clean, well-factored file. The BFS factory is a thin family-specialization of the shared `GeneratedInputArgumentsFactory` base — no duplicated walk/collision/cache logic — and the Layer-6 dynamic-FilterSet plumbing is correct, thoroughly tested (`tests/filters/test_factories.py`), and scrupulously documented as an unconsumed deferred surface. Cycle diff against the baseline is empty (file unchanged this cycle); this is a standing-code re-review. No High or Medium findings. One internal-consistency Low (the two `sorted()` calls in `_make_cache_key` omit the `key=repr` shield that `_make_hashable` documents as load-bearing — correct today via the keys-are-always-strings precondition, recorded to pre-empt re-flagging). The one DRY opportunity is a defer-with-trigger keyed to the order-side Layer-6 revival. No High/Medium and the single Low is no-action; this qualifies as a no-source-edit cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 267 files unchanged.
- `uv run ruff check --fix .` — pass; All checks passed.

### Notes for Worker 3
- The single Low (`_make_cache_key` `sorted()` calls omit `key=repr`) is a no-action internal-consistency observation: correct today because both sort sites compare `(k, hashable_v)` tuples whose first element `k` is always a `str` (field names / `Meta` attr names) and tuple comparison short-circuits before the heterogeneous second element; dict-key uniqueness guarantees no first-element tie. Recorded to pre-empt re-flagging, not a defect requiring a fix.
- The DRY analysis bullet is defer-with-trigger only (trigger: the `orders/factories.py` Layer-6 TODO anchor is resolved). No act-now consolidation.
- No GLOSSARY-only fix in scope (no GLOSSARY drift found).
- No shadow file regenerated; plan-time `--all` overview at `docs/shadow/django_strawberry_framework__filters__factories.overview.md` was used as-is.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/test edits this cycle (no-source-edit cycle; cycle diff against baseline empty). Per AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" and the active plan `docs/review/review-0_0_10.md` carrying no changelog directive for this item.

---

## Verification (Worker 3)

No-source-edit cycle (shape #5). Re-read source + the plan-time shadow overview (`docs/shadow/django_strawberry_framework__filters__factories.overview.md`). Per shadow-file dicta: shadow line numbers are non-canonical; original source line numbers treated as authoritative.

### Logic verification outcome

- **High / Medium: None.** Confirmed.
- **Low (`_make_cache_key`'s two `sorted()` calls omit `key=repr`) is genuinely no-action.** Re-derived the cache-key construction at `_make_cache_key` (lines 162-181). Both sort sites sort `(k, _make_hashable(v))` tuples:
  - Site 1 (line 167): only reached for dict-shaped `fields`; `k` is a dict-`fields` key = django-filter field name → always `str`.
  - Site 2 (lines 176-180): `k` ranges over `safe_meta` keys excluding `model`/`fields` = `Meta` attribute names → always `str`.
  Tuple comparison short-circuits on the unequal first element (`k`); dict-key uniqueness guarantees no first-element tie, so the heterogeneous `_make_hashable(v)` second element is never compared. No `TypeError` is reachable today — the keys-always-strings precondition holds. The asymmetry (the omitted `key=repr` shield that `_make_hashable` lines 135/138 *do* carry, documented as load-bearing in its docstring lines 127-131) is internal-consistency only. This is NOT a latent cache-collision Medium: collisions would require equal keys hashing apart or distinct keys colliding; the precondition concerns *sort-ordering total-ness*, not key equality, and the absence of `key=repr` cannot produce a wrong-key hit — at worst a `TypeError` on a non-string-keyed top-level input, which is unreachable (see below).
- **Precondition unbreachable via a live path — Layer 6 is unconsumed.** Grepped the whole package: `get_filterset_class` / `_make_cache_key` / `_create_dynamic_filterset_class` have **zero** source consumers (only `FilterArgumentsFactory`, the Layer-5 BFS surface, is consumed — at `types/finalizer.py:1344-1354` and `filters/inputs.py:879`, none of which routes through the Layer-6 cache). So a non-string-keyed top-level `fields`/`extra` is reachable only by hand-constructed test input, never by a real declaration. The "correct today" framing is sound.
- **The mixed-key test pins `_make_hashable`, not the sibling sorts — consistent with the artifact.** `test_make_hashable_dict_branch_supports_mixed_key_types` (`tests/filters/test_factories.py:328-343`) calls `_make_hashable({"a": 1, 0: 2})` directly and asserts no raise + set-equality; it exercises `_make_hashable`'s `key=repr` branch, exactly the documented-helper contract the Low says `_make_cache_key`'s sorts do not mirror. The asymmetry the Low records is real and the test boundary matches the artifact's description.

### DRY findings disposition

- **The single defer-with-trigger DRY item is correctly deferred with a valid, grep-discoverable trigger.** The artifact keys consolidation to "the `orders/factories.py` Layer-6 TODO anchor is resolved." Confirmed the anchor exists verbatim at `orders/factories.py:85` (`# TODO(spec-028-orders-0_0_8 Decision 12; standing deferred non-goal):`) reserving `_dynamic_orderset_cache` / `get_orderset_class` (lines 90-93) as a not-yet-shipped mirror of the filter side. Both families' Layer-6 surfaces are presently unconsumed, so hoisting `_make_hashable`/`_make_cache_key` into `utils/inputs.py` + parameterizing a shared `get_dynamic_set_class` now would build shared machinery for two non-shipped surfaces — the deferral is the right call under AGENTS.md "do not preemptively populate." Trigger is concrete and falsifiable.
- **DRY-section soundness (Layer-5 reuse claims).** Spot-confirmed `FilterArgumentsFactory` (lines 67-112) supplies only family caches + the six hook attrs + the one `_build_input_triples` override, subclassing the single-sited `GeneratedInputArgumentsFactory` — the BFS walk/collision/cache/subclass-guard are NOT re-implemented here (delegated, per the grep above). Worker 1's "two distinct roles" reading of the 2x `filterset` literal (`_related_target_attr = "filterset"` vs. the docstring noun) is correct.

### Items Worker 1 cleared — spot-confirmed sound

- **Input-type-name stability / generated-type caching.** `_create_dynamic_filterset_class` (lines 184-202) derives `name = f"{model.__name__}AutoFilter"` and builds via plain `type(name, (FilterSet,), {"Meta": ...})` (drops `replace_csv_filters`, spec line 247); `get_filterset_class` collapses equivalent meta onto a shared cached class via `_make_cache_key`, so equivalent declarations converge on one `__name__`. The `model is None` guard raises a named `ConfigurationError` (lines 194-198). Cited tests exist: `test_get_filterset_class_strips_reserved_kwargs` (:445), `test_get_filterset_class_requires_model_when_dynamic` (:457), `test_get_filterset_class_supports_unhashable_meta_values` (:464), `test_dynamic_filterset_cache_does_not_replace_csv_filters` (:425).
- **Lazy related-class resolution / cache-no-clear lifecycle.** The `_dynamic_filterset_cache` has no clear hook by design (lines 52-58): keys embed model identity, so a post-`registry.clear()` rebuild gets a fresh key rather than a wrong hit — documented honestly, no real-world cost in a non-reloading process. Sound.

### Temp test verification

- None. The Low is verifiable by inspection (string-key precondition + short-circuit semantics) and the unconsumed-path grep; no temp test needed.

### Shape #5 checks

1. `git diff e544a01… -- django_strawberry_framework/filters/factories.py` empty; `git diff --stat e544a01… -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty over all owned paths. No dirty-tree noise this cycle.
2. Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` ✓
3. The single Low carries no-action rationale (not a GLOSSARY-only fix); no GLOSSARY-only fix present. ✓
4. Changelog `Not warranted` cites BOTH AGENTS.md and the active plan's silence; `git diff -- CHANGELOG.md` empty. ✓
5. `uv run ruff format --check` → "1 file already formatted"; `uv run ruff check` → "All checks passed!" ✓

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` and marks the `filters/factories.py` checklist box in `docs/review/review-0_0_10.md`.

