# Review: `django_strawberry_framework/orders/factories.py`

Status: verified

## DRY analysis

- **Order/filter family-wrapper consolidation is already maximally factored at this layer; the only residual cross-folder twin is the deferred Layer 6.** `orders/factories.py::OrderArgumentsFactory` and `filters/factories.py::FilterArgumentsFactory` are both thin parameterizations of `utils/inputs.py::GeneratedInputArgumentsFactory` (the BFS walk, collision check, idempotent cache, and `__init_subclass__` rejection guard are single-sited there, 0.0.9 DRY pass). The order subclass is 7 class-attr assignments + one `_build_input_triples` hook (`factories.py:64-82`); the filter subclass is the same 7 + a hook that additionally splices `_build_logic_fields` (`filters/factories.py:95-112`). This is the intended shared-base/family-hook shape, NOT duplication — no further consolidation at the subclass layer is possible without erasing the per-family caches that MUST stay distinct namespaces. **Defer the only remaining twin (the Layer 6 dynamic-cache: `_make_hashable` / `_make_cache_key` / `_create_dynamic_*_class` / `get_*set_class`, live only on the filter side at `filters/factories.py:120-246`) until the order side ships its Layer 6** per the TODO anchor at `orders/factories.py:85-96`. The trigger is verbatim in-source: *"this remains a standing deferred non-goal until a card revives it."* When that card lands, the cache machinery should be hoisted into `utils/inputs.py` parameterized by family (base class + reserved-keys frozenset + name-suffix), built ONCE rather than hand-mirrored — the prior `filters/factories.py` cycle's `_make_cache_key` keys-always-strings precondition and its Layer-6 DRY both fold into that same future hoist. Cross-folder; forwarded to the project pass per the dispatch, not merged here.

## High:

None.

## Medium:

None.

## Low:

### Stale "dynamic OrderSet caching" claim in the order test file + TREE (out-of-target; folder/project-pass follow-up)

`tests/orders/test_factories.py:1` (module docstring) and `docs/TREE.md:376` + `docs/TREE.md:515` all describe the order test file as covering *"BFS input generation **and dynamic OrderSet caching**."* But `orders/factories.py` deliberately ships NO dynamic cache — Layer 6 (`_dynamic_orderset_cache` / `get_orderset_class`) is a standing deferred non-goal (the module docstring `factories.py:10-19` and the TODO anchor `factories.py:85-96` both state this), and the test file contains zero dynamic-cache tests (every `def test_*` is a BFS / collision / idempotency / subclass-rejection case). The "dynamic OrderSet caching" phrase appears to be a copy-from-filter-side artifact: the filter twin genuinely ships and tests Layer 6, the order twin does not. The claim promises behavior that does not exist.

This is not a defect in the target file (`orders/factories.py` is accurate about its own non-shipping of Layer 6). The fix touches `tests/orders/test_factories.py` and `docs/TREE.md`, both outside this cycle item's target. Recommend Worker 2 trim the phrase to "BFS input generation" in all three locations, OR defer to the `orders/` folder pass (which owns sibling-test consistency) / project pass (which owns TREE consistency). Recorded here so the disposition is greppable; do not edit the target file for it.

### `del type_name` in the hook reads as discard-only; a one-word note on the asymmetry would aid the reader (forward-looking)

`_build_input_triples` (`factories.py:74-82`) takes the base-contract three-arg signature `(set_cls, type_name, owner_definition)` and immediately `del type_name`, because the order side has no `and_`/`or_`/`not_` operator bag (the filter twin passes `type_name` to `_build_logic_fields`). The inline comment `# the order side has no ``and_`` / ``or_`` / ``not_`` bag.` already explains WHY, and the docstring cites Spec Decision 8 — this is well-documented. No change now. Defer until a future order-side feature consumes `type_name` (e.g. an order-family logic surface); at that point the `del` becomes a real use and this note is moot. Forward-looking, no source edit.

## What looks solid

### DRY recap

- **Existing patterns reused.** The file reuses `utils/inputs.py::GeneratedInputArgumentsFactory` for the entire BFS/collision/cache/subclass-rejection machinery (`factories.py:33` extends it; the base is `utils/inputs.py:277-417`) and `orders/inputs.py::_build_input_fields` for the per-field triple build (`factories.py:27,82`). The 7 hook class-attrs (`_collision_registry_attr` / `_factory_label` / `_family_label` / `_rename_noun` / `_related_attr` / `_related_target_attr` + the two ClassVar caches, `factories.py:64-72`) are exactly the contract the base documents at `utils/inputs.py:287-304`. This is the canonical family-parameterization shape.
- **New helpers considered.** None warranted — there is no executable logic in this file to factor (2 symbols, 0 control-flow hotspots, 0 ORM markers per the shadow overview). The only candidate is the deferred Layer-6 cache hoist, captured in `## DRY analysis` with its trigger.
- **Duplication risk in the current file.** The shadow's `2x ``orderset``` repeated literal is the two related-target hook attrs (`_rename_noun = "orderset"` for collision-error wording, `_related_target_attr = "orderset"` for the base's `getattr(related, ...)` resolution at `utils/inputs.py:391`). These are two semantically-distinct slots that happen to share a value; collapsing them would couple the error-message noun to the attribute name. Intentional, not duplication.

### Other positives

- **Subclass-rejection guard is inherited, not re-spelled.** The order factory gets `__init_subclass__`'s grand-subclass rejection (`utils/inputs.py:324-338`) for free; the docstring restates the contract ("Subclassing is rejected at class-creation time; extend by composition", `factories.py:60-61`) without re-implementing it. Pinned by `tests/orders/test_factories.py::test_factory_subclass_rejected_at_class_creation_time`.
- **Lazy related-class resolution is correct and shared.** The order side never imports `OrderSet` or any concrete set class at module load; related-target resolution happens at BFS time via the base's `getattr(set_cls, self._related_attr, {}).values()` + `getattr(related, self._related_target_attr)` (`utils/inputs.py:390-394`), with `None`-target placeholders skipped (pinned by `test_factory_skips_related_order_with_none_target`). No import-time side effects, no circular-import surface — `factories.py` imports only `..utils.inputs` (outward to the shared core) and `.inputs` (sibling), matching the order twin's one-way dependency direction.
- **Stable input names.** Names flow from `set_cls.type_name_for()` (base `utils/inputs.py:343,376,398`), single-sourced so the runtime order shape and the GraphQL input shape stay downstream of one decision site — exactly the Decision-4-H1 invariant the module docstring claims (`factories.py:6-9`). Idempotent rebuild pinned by `test_factory_arguments_is_idempotent` + `test_factory_input_object_types_shared_across_factory_instances`.
- **Hook signature matches the base contract and the delegate.** `_build_input_triples(set_cls, type_name, owner_definition) -> list[tuple[str, Any, dict[str, Any]]]` matches the base's `NotImplementedError` hook (`utils/inputs.py:405-417`); the delegated `_build_input_fields(set_cls, owner_definition)` matches `orders/inputs.py:195-198`'s `(orderset_cls, owner_definition=None)`. Type-correct end to end.
- **Cache-key correctness is N/A by design, and the file is honest about it.** The REVIEW order focus item "cache-key correctness" lands entirely in the deferred Layer 6 (`_make_cache_key` exists only on the filter side). The order file ships no cache key and the TODO anchor (`factories.py:85-96`) precisely names the forward-reserved symbols (`_dynamic_orderset_cache`, `get_orderset_class`) and the active design doc + decision (spec-028 Decision 12), satisfying AGENTS.md #26's "TODO must name the active doc + slice" rule. The `TYPE_CHECKING` `from django.db import models` is unused on the order side (no `_create_dynamic_*` function) but documented as `# noqa: F401 - kept for filter-side parity.` — a deliberate twin-symmetry choice, not dead-import drift.

### Summary

Clean file, empty `git log 14910230..HEAD` and empty `git diff HEAD` (confirmed; not in the spec-035 set, exactly as the change context predicted). `orders/factories.py` is a thin, correct parameterization of the shared `GeneratedInputArgumentsFactory` substrate — 7 hook attrs plus one `_build_input_triples` override that drops the filter side's operator bag (Spec Decision 8). All real BFS/collision/cache/lazy-resolution logic lives in `utils/inputs.py` and is well-tested via `tests/orders/test_factories.py`. No High, no Medium. Two Lows, both non-local: a stale "dynamic OrderSet caching" phrase in the order test docstring + TREE.md (out of this file; forward to the folder/project pass), and a forward-looking note on the `del type_name` hook asymmetry (no edit). DRY is maximal at this layer; the only residual twin is the deferred Layer-6 dynamic cache, gated behind the in-source TODO trigger and forwarded to the project pass. No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 270 files unchanged.
- `uv run ruff check --fix .` — all checks passed (only the pre-existing COM812-vs-formatter config notice).

### Notes for Worker 3
- **Low #1 (stale "dynamic OrderSet caching" claim):** target file is accurate; the stale phrase lives in `tests/orders/test_factories.py:1`, `docs/TREE.md:376`, `docs/TREE.md:515` — all OUTSIDE this cycle item's target. Not editable in this cycle without touching out-of-scope files; explicitly forwarded to the `orders/` folder pass (sibling-test consistency) and the project pass (TREE consistency). No edit made.
- **Low #2 (`del type_name` hook asymmetry):** forward-looking, no edit; trigger is a future order-side logic surface that consumes `type_name`. The behavior is already correct and documented (inline comment + Spec Decision 8 docstring cite).
- No GLOSSARY-only fix in scope: GLOSSARY.md has no `OrderArgumentsFactory` / `orders/factories` entry (grep = 0), so there is nothing to correct there. The `Meta.orderset_class` GLOSSARY entry (824-832) describes the consumer wiring and is accurate; it does not claim a dynamic OrderSet cache.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No source-comment or docstring edits in scope. The target file's module docstring, class docstring, hook docstring, and TODO anchor are all accurate and AGENTS.md #26-compliant (the TODO names the active spec + decision and the forward-reserved symbols). The stale "dynamic OrderSet caching" phrase is in a test docstring + TREE.md, both outside the target file — see `### Notes for Worker 3`.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No behavior change, no source edit (AGENTS.md #21 "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_10.md` is silent on changelog work for this item).

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit cycle (shape #5). `git diff HEAD -- orders/factories.py` and `git log 14910230..HEAD -- orders/factories.py` both empty; HEAD 58ca2def. `orders/factories.py` is absent from the `git diff --stat 14910230 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` set, so the zero-edit claim holds; the 27 dirty paths in that stat are other cycle items' files, none owned by this item.

- **Thin-parameterization + base hook contract (verified against source).** `OrderArgumentsFactory` (`factories.py:33-82`) supplies exactly the 7 family attrs the base documents at `utils/inputs.py:287-322` — `input_object_types` + `_type_orderset_registry` (the two fresh per-family ClassVar caches, `factories.py:64-65`), `_collision_registry_attr`/`_factory_label`/`_family_label`/`_rename_noun`/`_related_attr`/`_related_target_attr` (`factories.py:67-72`). Values match the slots the base reads: `_related_attr="related_orders"` feeds `getattr(set_cls, self._related_attr, {}).values()` (`utils/inputs.py:390`); `_related_target_attr="orderset"` feeds `getattr(related, self._related_target_attr)` (`utils/inputs.py:391`); `_collision_registry_attr="_type_orderset_registry"` is read via the base `_collision_registry` property (`utils/inputs.py:348`). The base single-sites BFS/collision/idempotent-cache/`__init_subclass__` rejection (`utils/inputs.py:324-403`); the subclass adds no logic. Canonical family-parameterization shape, not duplication.
- **Decision-8 operator-bag drop (verified against the filter twin).** Base hook is `_build_input_triples(set_cls, type_name, owner_definition)` returning field triples, with a `NotImplementedError` family-hook body (`utils/inputs.py:405-417`). Order override (`factories.py:74-82`) returns `_build_input_fields(set_cls, owner_definition)` verbatim and `del type_name` because the order side has no `and_`/`or_`/`not_` bag. Filter twin (`filters/factories.py:105-112`) is identical except it splices `*_build_logic_fields(type_name)` — so `type_name` is live on the filter side and genuinely unused on the order side. The drop is correct: the order family ships no logic surface, so consuming `type_name` would be dead. Signature matches the base contract and the delegate (`orders/inputs.py::_build_input_fields`).
- **Layer-6 absence is TODO-anchored, not a silent gap (AGENTS.md #26).** The forward-reserved symbols `_dynamic_orderset_cache` / `get_orderset_class` exist only in the module docstring (`factories.py:18`) and the TODO anchor (`factories.py:85-96`) — grep of the target file finds no definition, only doc/anchor references. The TODO names the active design doc + decision (`spec-028-orders-0_0_8 Decision 12`), the forward-reserved symbols, and the reason (connection field consumes the explicit `Meta.orderset_class` sidecar). No NotImplementedError pairing is required: the default order path is complete and no call path must fail loudly, so #26's NotImplementedError requirement is correctly NOT triggered. The filter twin DOES ship Layer 6 (`filters/factories.py:120-218`: `_make_hashable`/`_make_cache_key`/`_create_dynamic_filterset_class`/`get_filterset_class`), confirming the order-side absence is a deliberate non-goal, not an omission.

### DRY findings disposition
DRY at this layer is maximal: the subclass is 7 attrs + one hook override; all BFS/collision/cache/lazy-resolution logic is single-sited in `utils/inputs.py::GeneratedInputArgumentsFactory`. The only residual cross-folder twin — the deferred Layer-6 dynamic cache (`_make_cache_key` and siblings, live only on the filter side) — is gated behind the in-source TODO trigger (`factories.py:85-96`, verbatim "this remains a standing deferred non-goal until a card revives it") and forwarded to the project pass. The filter-side `_make_cache_key` keys-always-strings precondition does not recur here because the order side ships no cache key. Forward correctly disposed by citation; not force-merged.

### Temp test verification
- No temp tests needed. Source-read verification of the base contract, the filter-twin diff, and the test-file inventory was sufficient.
- Disposition: none.

### Low dispositions
- **Low #1 (stale "dynamic OrderSet caching" claim) — genuinely out-of-file, correctly forwarded.** Confirmed the phrase lives at `tests/orders/test_factories.py:1` (module docstring) and `docs/TREE.md:376` + `:515` — all OUTSIDE the target file. The target file is accurate about its own non-shipping of Layer 6. Confirmed `tests/orders/test_factories.py` ships ZERO dynamic-cache tests: all 10 `def test_*` functions are BFS/cycle/leaf/collision/idempotency/subclass-rejection/none-target/dedupe cases (grep for a cache/dynamic/get_orderset test fn returns nothing). This is a real stale copy-from-filter artifact, but fixing it requires editing out-of-scope files; correctly forwarded to the `orders/` folder pass (sibling-test consistency) and project pass (TREE consistency). NOT a local defect this cycle must fix.
- **Low #2 (`del type_name` hook asymmetry) — genuinely forward-looking.** The behavior is correct and documented (inline comment `factories.py:81` + Spec Decision 8 docstring cite). Trigger is a future order-side logic surface that consumes `type_name`; no edit warranted now. Verbatim in-source trigger present.

### Changelog verification
`git diff -- CHANGELOG.md` empty (the +9 CHANGELOG hunk in the cycle-wide stat belongs to other cycle items, not this one — this item's disposition is Not warranted with an empty target-file diff). Disposition cites both AGENTS.md #21 and the active plan's silence on changelog work for this item. Internal-only framing correct: no source edit, no public-API change. Accepted.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` and marks the `orders/factories.py` box in `docs/review/review-0_0_10.md`. Shape #5 preamble present in all three Worker 2 sections ("Filled by Worker 1 per no-source-edit cycle pattern."); ruff format-check + check pass on the target file; both Lows have verbatim triggers or are forwarded; no GLOSSARY-only fix in scope.

---

## Iteration log

(none)
