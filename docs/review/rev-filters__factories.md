# Review: `django_strawberry_framework/filters/factories.py`

Status: verified

## DRY analysis

- Defer-with-trigger: the Layer-6 dynamic-cache helper trio (`filters/factories.py::_make_hashable`, `::_make_cache_key`, `::get_filterset_class`, `::_create_dynamic_filterset_class`, `::_dynamic_filterset_cache`) is the only concrete implementation of the `(model, fields, extra_meta)` cache shape. The orders side currently has **no** twin — `orders/factories.py` lines 85-96 explicitly defer Layer 6 as a TODO-anchored standing non-goal and reserves the symbol names `_dynamic_orderset_cache` / `get_orderset_class`. **Trigger:** when a card revives the orders Layer-6 surface (i.e. `orders/factories.py` gains a real `get_orderset_class` + `_dynamic_orderset_cache` implementation), extract the model-keyed hashing primitives — `_make_hashable(v)` and the `(model, fields_key, extra)` key-building body of `_make_cache_key(safe_meta)` — into a shared helper (e.g. `utils/inputs.py::make_set_meta_cache_key`) and have both factories consume it. Until that twin exists there is nothing to consolidate; a single concrete site is not duplication.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The BFS walk, per-class collision check, idempotent `input_object_types` cache, and subclass-rejection guard all live in the single-sited base `utils/inputs.py::GeneratedInputArgumentsFactory` (`utils/inputs.py:277` with `__init_subclass__` reject at `:324-339`); `FilterArgumentsFactory` (`filters/factories.py:67-112`) supplies only the filter-family caches, the six `_*_label` / `_*_attr` hooks, and the `_build_input_triples` override that splices `_build_input_fields` + `_build_logic_fields` from `filters/inputs.py`. The order side (`orders/factories.py`) is the parallel thin subclass, so the BFS algorithm is genuinely single-sourced across both families (Decision-9 named caches preserved so `registry.clear()` / tests address them directly).
- **New helpers considered.** Considered extracting `_make_hashable` / the `_make_cache_key` body into a shared `utils/inputs.py` primitive now — rejected: the orders Layer-6 twin is a deferred non-goal that does not yet exist (`orders/factories.py:85-96`), so extracting today would create a single-caller helper. Recorded as the lone defer-with-trigger DRY bullet instead.
- **Duplication risk in the current file.** The two `tuple(sorted(... key=repr))` branches in `_make_hashable` (`filters/factories.py:133-138`, dict vs set/frozenset) are intentional sibling design — both unordered containers need canonical ordering, but the dict branch zips `(k, _make_hashable(val))` pairs while the set branch maps bare members; collapsing them would obscure the key/value asymmetry. The repeated `{"model", "fields"}` / `safe_meta.get("model"|"fields")` accesses (`:162-163`, `:178`) are the discriminator-vs-extra split, not a literal to hoist. The single `2x "filterset"` repeated literal flagged by the static helper is the `_rename_noun` / `_related_target_attr` hook pair (`:101`, `:103`) — distinct semantic slots that legitimately share the word.

### Other positives

- **Unconsumed Layer 6 is honestly documented, not silently dead.** The module docstring (`:1-28`), the `_dynamic_filterset_cache` comment block (`:43-58`), and `get_filterset_class`'s docstring (`:206-236`) all state plainly that no source path consumes the cache (DjangoConnectionField reads the resolved `Meta.filterset_class` sidecar directly), cite the standing spec-027 Non-goal, and record the M-filters-3 lifecycle decision (no clear hook needed — keys embed model identity, so a rebuilt model gets a fresh key, never a stale hit). This is the correct way to land plumbing ahead of its consumer.
- **`_make_hashable` is provably total-ordered.** Both unordered branches sort by `repr` rather than by the members themselves, so mixed mutually-unorderable member/key types (`{1, "a"}`, `{"a": 1, 0: 2}`) never raise `TypeError`; equal members produce equal reprs so the canonical order is stable. The docstring (`:121-132`) explains exactly this, and `tests/filters/test_factories.py::test_make_hashable_dict_branch_supports_mixed_key_types` pins it.
- **The model is the primary cache discriminator and the PYTHONHASHSEED caveat is documented.** `_make_cache_key` keys off `model` first (`:162`, `:181`); the docstring (`:145-161`) is candid that a *top-level* `set`-shaped `fields` keys off iteration order (which also governs generated filter order) and recommends `list`/`tuple` when order matters — a correct, scoped caveat rather than a hidden footgun. Nested set-valued lookups under a dict-shaped `fields` are still canonicalized via `_make_hashable`.
- **`ConfigurationError` raised on the real misuse.** `_create_dynamic_filterset_class` raises a clear `ConfigurationError` when `model` is absent (`:194-198`), naming the missing key and the cause; `get_filterset_class` documents the distinct-meta-same-`__name__` collision path and the explicit-`filterset_class=` escape hatch.
- **Test discipline.** `tests/filters/test_factories.py` covers the BFS factory (cycle handling, dedupe, collision, idempotency, relay + non-relay shape parity) and every Layer-6 plumbing branch (explicit pass-through, dict/list/scalar key normalization, structural-equivalence sharing, extra-meta distinction, model discrimination, dynamic-cache collapse) despite the path having no production consumer — the deferred surface is fully pinned.

### Summary

`filters/factories.py` is unchanged versus both the cycle baseline (`edb2e2e6`) and HEAD; `git diff` is empty for both. The BFS factory delegates all algorithm logic to the single-sited `GeneratedInputArgumentsFactory` base and supplies only family hooks, and the Layer-6 dynamic-FilterSet cache is honestly documented as built-and-tested ahead of an unbuilt, deferred-non-goal consumer with a reviewed lifecycle (no clear hook needed because keys embed model identity). No correctness, ORM, mutability, or cache-key bug surfaced; `_make_hashable` is total-ordered and the one order-sensitivity caveat is documented and tested. GLOSSARY carries no entry for these symbols (the BFS argument factory is referenced accurately via `Meta.filterset_class` prose at GLOSSARY:723), so no doc drift. The sole DRY item is a defer-with-trigger gated on the orders Layer-6 twin actually landing. Genuine no-source-edit cycle (shape #5): zero findings, zero tracked edits.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, 289 files left unchanged.
- `uv run ruff check --fix .` — pass, All checks passed!

### Notes for Worker 3
- Cycle qualifies as shape #5: `git diff edb2e2e6ef4cca6fac63641f9db3729bb28b70fb -- django_strawberry_framework/filters/factories.py` and `git diff HEAD -- …` are both empty.
- All severities `None.`; no High and no behaviour-changing Medium.
- The single DRY bullet is defer-with-trigger (orders Layer-6 twin must land first); not actionable this cycle.
- No GLOSSARY-only fix in scope — GLOSSARY has no entry for `get_filterset_class` / `_make_cache_key` / `_make_hashable` / `_dynamic_filterset_cache`; `FilterArgumentsFactory` is referenced accurately via `Meta.filterset_class` prose (GLOSSARY:723), no drift.
- Load-bearing claims re-verified this cycle: (a) `get_filterset_class` and the Layer-6 helpers have zero source callers (only docstrings + `tests/filters/test_factories.py`); `FilterArgumentsFactory` is consumed by `types/finalizer.py:1374-1384`. (b) `orders/factories.py:85-96` still defers Layer 6 as a TODO-anchored non-goal — no parallel implementation exists, so no act-now DRY. (c) Subclass rejection lives in `utils/inputs.py::GeneratedInputArgumentsFactory.__init_subclass__` (`:324-339`).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits warranted — the module docstring, the `_dynamic_filterset_cache` lifecycle comment, and the per-function docstrings are accurate and current (verified against impl and against the orders-side deferral). Nothing to change.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source edit this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; active plan `docs/review/review-0_0_11.md` records no changelog obligation for this item).

---

## Verification (Worker 3)

### Logic verification outcome
All severities are `None.` and verified genuine (not lazy):
- **Unconsumed Layer-6 cache honestly documented, not a hidden defect.** `grep -rn` over `django_strawberry_framework/` confirms zero source callers of `get_filterset_class`, `_make_cache_key`, `_make_hashable`, `_create_dynamic_filterset_class`, `_dynamic_filterset_cache`. The lone non-self hit (`orders/factories.py:93`) is a *comment* naming the symbol in the deferral TODO, not a call. `FilterArgumentsFactory` is consumed by `types/finalizer.py:1374-1384`. The cache is genuinely build-and-test-only ahead of the deferred consumer, exactly as the module docstring (`:1-28`), the `_dynamic_filterset_cache` comment (`:43-58`), and `get_filterset_class`'s docstring (`:206-236`) state.
- **BFS input-class factory correct.** `FilterArgumentsFactory` delegates the BFS walk + collision + idempotent cache + subclass-reject to single-sited `GeneratedInputArgumentsFactory`, supplying only family hooks (`_rename_noun`/`_related_*`) and the `_build_input_triples` override splicing `_build_input_fields` + `_build_logic_fields`. Pinned by `tests/filters/test_factories.py`: cycle (`test_..._bfs_handles_cycle`), diamond pop-time dedup (`test_..._dedupes_target_enqueued_twice`), collision→ConfigurationError with family wording (`test_..._collision_raises...`), idempotency, relay/non-relay shape parity, subclass-rejection (`test_..._rejects_subclassing`).
- **`_make_hashable` total-ordered.** Both unordered branches (dict `:135`, set/frozenset `:138`) sort by `key=repr`, so mixed mutually-unorderable members/keys never raise `TypeError`. Pinned by `test_make_hashable_dict_branch_supports_mixed_key_types` (`{"a":1, 0:2}` normalizes without raising; asserts by set-equality since canonical order is repr-driven).
- **`_make_cache_key` correct.** `model` primary discriminator (`:162`, `:181`); dict/seq/raw branches + sorted extras all pinned — `test_make_cache_key_normalizes_{dict,list,scalar}_fields_shape`, `..._distinguishes_extra_meta_keys`, `..._structurally_equivalent_metas_share_a_slot` (5 equivalence classes incl. model discrimination), `test_dynamic_filterset_cache_collapses_equivalent_metas_to_one_class`, `test_get_filterset_class_supports_unhashable_meta_values`. The top-level-`set` `PYTHONHASHSEED` order caveat (`:154-160`) is a documented, scoped caveat, not a hidden footgun.
- **`ConfigurationError` on the real misuse.** Missing `model` (`:194-198`) pinned by `test_get_filterset_class_requires_model_when_dynamic`. Reserved-kwarg strip, explicit pass-through, distinct-meta paths pinned.

### DRY findings disposition
The single DRY bullet (extract `_make_hashable` + the `(model, fields_key, extra)` key body into a shared `utils/inputs.py` primitive) is correctly **defer-with-trigger**. Independently confirmed: `orders/factories.py:85-103` reserves `_dynamic_orderset_cache` / `get_orderset_class` as a TODO-anchored standing deferred non-goal with **no** implementation — so no twin exists yet and a single concrete site is not duplication. The verbatim trigger (orders Layer-6 surface gaining a real `get_orderset_class` + `_dynamic_orderset_cache`) is present and actionable when that card lands.

### Temp test verification
None — no temp tests needed; all `None.` severities verified by reading source against named permanent tests in `tests/filters/test_factories.py`.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

Zero-edit proof (shape #5): `git diff edb2e2e6ef4cca6fac63641f9db3729bb28b70fb -- django_strawberry_framework/filters/factories.py` and `git diff HEAD -- …` both empty; target absent from `git diff --stat edb2e2e6 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` (owned-paths stat fully clean this run — no concurrent #33 dirt). Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.`. No GLOSSARY-only fix in scope: zero GLOSSARY hits for any Layer-6 symbol; `Meta.filterset_class` prose at GLOSSARY:723 accurately describes the BFS argument factory without naming the unconsumed helpers — genuine #5, no drift. Changelog `Not warranted` with both required citations (AGENTS.md + plan silence); `git diff -- CHANGELOG.md` empty. Ruff format-check + check pass on target and test.
