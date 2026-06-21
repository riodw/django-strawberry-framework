# Review: `django_strawberry_framework/orders/factories.py`

Status: verified

## DRY analysis

- **Order/filter family-wrapper consolidation is maximal at this layer; the only residual cross-folder twin is the deferred Layer 6 — defer with the in-source trigger.** `orders/factories.py::OrderArgumentsFactory` and `filters/factories.py::FilterArgumentsFactory` are both thin parameterizations of `utils/inputs.py::GeneratedInputArgumentsFactory` (the BFS walk, collision check, idempotent cache, and `__init_subclass__` rejection guard are single-sited there, 0.0.9 DRY pass). The order subclass is 6 hook attrs + 2 ClassVar caches + one `_build_input_triples` hook (`orders/factories.py:64-82`); the filter subclass is the same shape plus a hook that additionally splices `_build_logic_fields` (`filters/factories.py:95-112`). This is the intended shared-base/family-hook shape, NOT duplication — no further subclass-layer consolidation is possible without erasing the per-family caches that MUST stay distinct namespaces. **Defer the only remaining twin (the Layer-6 dynamic-cache primitives `_make_hashable` / `_make_cache_key` / `_create_dynamic_*_class` / `get_*set_class`, live only on the filter side at `filters/factories.py:120-246`) until the order side ships its Layer 6** per the TODO anchor at `orders/factories.py:85-96` — verbatim trigger in-source: *"this remains a standing deferred non-goal until a card revives it."* When that card lands, the cache machinery should be hoisted into `utils/inputs.py` parameterized by family (base class + reserved-keys frozenset + name-suffix), built ONCE; the filter-side `_make_cache_key` keys-precondition folds into that same future hoist. Cross-folder; forwarded to the project pass, not merged here.

## High:

None.

## Medium:

None.

## Low:

### `del type_name` in the hook reads as discard-only; the asymmetry is documented (forward-looking, no edit)

`OrderArgumentsFactory._build_input_triples` (`orders/factories.py:74-82`) takes the base-contract three-arg signature `(set_cls, type_name, owner_definition)` and immediately `del type_name`, because the order side has no `and_`/`or_`/`not_` operator bag (the filter twin passes `type_name` to `_build_logic_fields`). The inline comment `# the order side has no ``and_`` / ``or_`` / ``not_`` bag.` already explains WHY, and the docstring cites Spec Decision 8 — well-documented. No change now. Defer until a future order-side feature consumes `type_name` (e.g. an order-family logic surface); at that point the `del` becomes a real use and this note is moot. Forward-looking, no source edit.

## What looks solid

### DRY recap

- **Existing patterns reused.** The file reuses `utils/inputs.py::GeneratedInputArgumentsFactory` for the entire BFS/collision/cache/subclass-rejection machinery (`orders/factories.py:33` extends it; base at `utils/inputs.py:277-417`) and `orders/inputs.py::_build_input_fields` for the per-field triple build (`orders/factories.py:27,82`). The hook attrs (`_collision_registry_attr` / `_factory_label` / `_family_label` / `_rename_noun` / `_related_attr` / `_related_target_attr` + the two ClassVar caches, `orders/factories.py:64-72`) are exactly the contract the base documents at `utils/inputs.py:287-322`. Canonical family-parameterization shape.
- **New helpers considered.** None warranted — there is no executable logic in this file to factor (2 symbols, 0 control-flow hotspots, 0 ORM markers per the shadow overview). The only candidate is the deferred Layer-6 cache hoist, captured in `## DRY analysis` with its in-source trigger.
- **Duplication risk in the current file.** The shadow's `2x ``orderset``` repeated literal is the two distinct hook slots `_rename_noun = "orderset"` (collision-error wording) and `_related_target_attr = "orderset"` (the base's `getattr(related, ...)` resolution at `utils/inputs.py:391`). Two semantically-distinct roles that happen to share a value; collapsing them would couple the error-message noun to the attribute name. Intentional, not duplication.

### Other positives

- **Subclass-rejection guard is inherited, not re-spelled.** The order factory gets `__init_subclass__`'s grand-subclass rejection (`utils/inputs.py:324-338`) for free; the docstring restates the contract ("Subclassing is rejected at class-creation time; extend by composition", `orders/factories.py:60-61`) without re-implementing it. Pinned by `tests/orders/test_factories.py::test_factory_subclass_rejected_at_class_creation_time`.
- **Lazy related-class resolution is correct and shared.** The order side never imports `OrderSet` or any concrete set class at module load; related-target resolution happens at BFS time via the base's `getattr(set_cls, self._related_attr, {}).values()` + `getattr(related, self._related_target_attr)` (`utils/inputs.py:390-394`), with `None`-target placeholders skipped (pinned by `test_factory_skips_related_order_with_none_target`). No import-time side effects, no circular-import surface — `orders/factories.py` imports only `..utils.inputs` (outward to the shared core) and `.inputs` (sibling), matching the filter twin's one-way dependency direction.
- **Stable input names, single decision site.** Names flow from `set_cls.type_name_for()` (base `utils/inputs.py:343,376,398`), single-sourced so the runtime order shape and the GraphQL input shape stay downstream of one decision site — exactly the Decision-4-H1 invariant the module docstring claims (`orders/factories.py:6-9`). Idempotent rebuild pinned by `test_factory_arguments_is_idempotent` + `test_factory_input_object_types_shared_across_factory_instances`.
- **Layer-6 absence is TODO-anchored, not a silent gap (AGENTS.md #26).** The forward-reserved symbols `_dynamic_orderset_cache` / `get_orderset_class` exist only in the module docstring (`orders/factories.py:18`) and the TODO anchor (`orders/factories.py:85-96`) — no definition in the shipped module. The TODO names the active design doc + decision (`spec-028-orders-0_0_8 Decision 12`), the forward-reserved symbols, and the reason (connection field consumes the explicit `Meta.orderset_class` sidecar). No `NotImplementedError` pairing is required: the default order path is complete and no call path must fail loudly, so #26's NotImplementedError clause is correctly NOT triggered. The `TYPE_CHECKING` `from django.db import models` is unused on the order side but documented `# noqa: F401 - kept for filter-side parity.` — deliberate twin-symmetry, not dead-import drift.
- **Prior-cycle stale-coverage Low is RESOLVED.** The 0.0.10-cycle Low (the order test docstring + `docs/TREE.md` claiming "dynamic OrderSet caching" coverage that does not exist) was fixed by the `orders/` folder pass (`docs/review/rev-orders.md`): `tests/orders/test_factories.py:1` now reads "BFS input generation." and `docs/TREE.md:376`/`:515` no longer carry the stale clause (grep-confirmed: zero "dynamic OrderSet caching" hits in standing docs/tests). Not re-flagged.

### Summary

`orders/factories.py` is a thin, correct parameterization of the shared `GeneratedInputArgumentsFactory` substrate — 6 hook attrs + 2 per-family ClassVar caches plus one `_build_input_triples` override that drops the filter side's operator bag (Spec Decision 8). All real BFS/collision/cache/lazy-resolution logic lives in `utils/inputs.py` and is well-tested via `tests/orders/test_factories.py`. No High, no Medium. One Low, genuinely forward-looking (the `del type_name` hook asymmetry, already documented; no edit). The prior cycle's stale-coverage Low is resolved upstream in the folder pass. DRY is maximal at this layer; the only residual twin is the deferred Layer-6 dynamic cache, gated behind the in-source TODO trigger and forwarded to the project pass. No-source-edit cycle (shape #5): `git diff c0de6394 -- orders/factories.py` and `git diff HEAD -- orders/factories.py` both empty.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; "289 files left unchanged".
- `uv run ruff check --fix .` — pass; "All checks passed!".

### Notes for Worker 3
- Shape #5 (no-source-edit cycle): `git diff c0de6394bb259b44ca17e388f02d036f09f38130 -- django_strawberry_framework/orders/factories.py` AND `git diff HEAD -- django_strawberry_framework/orders/factories.py` BOTH empty.
- All High/Medium `None.`; one Low (`del type_name` hook asymmetry) is genuinely forward-looking with a verbatim in-source trigger — no edit warranted.
- Prior 0.0.10-cycle Low (stale "dynamic OrderSet caching" coverage claim) is RESOLVED upstream by `docs/review/rev-orders.md` (folder pass trimmed the phrase in `tests/orders/test_factories.py:1` + `docs/TREE.md:376`/`:515`; grep confirms zero hits in standing docs/tests). Not re-flagged.
- No GLOSSARY-only fix in scope: `OrderArgumentsFactory` / `get_orderset_class` / `_dynamic_orderset_cache` have zero `docs/GLOSSARY.md` entries (grep = 0); private/no-`__all__`/not re-exported from `orders/__init__.py` — absence correct. The `Meta.orderset_class` GLOSSARY entry is accurate and claims no dynamic cache.
- One DRY item forwarded to project pass (`rev-django_strawberry_framework.md`): the filters-vs-orders Layer-6 hashing-primitive pairing — orders side is the deferred TODO non-goal, so no act-now consolidation.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No source-comment or docstring edits in scope. The target file's module docstring, class docstring, hook docstring, and TODO anchor are all accurate and AGENTS.md #26-compliant (the TODO names the active spec + decision and the forward-reserved symbols). The prior stale "dynamic OrderSet caching" phrase was in a test docstring + TREE.md (both outside this file) and is already fixed upstream — see `### Notes for Worker 3`.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source/test/doc edit in this cycle; AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` is silent on changelog work for this item.

---

## Verification (Worker 3)

### Logic verification outcome
All High/Medium `None.` independently confirmed genuine; the one Low (`del type_name` hook asymmetry) is genuinely forward-looking, no edit warranted.

- **High/Medium None — order BFS factory correctness confirmed.** The 6 hook attrs + 2 ClassVar caches on `OrderArgumentsFactory` (`orders/factories.py:64-72`) exactly match the base's declared contract (`utils/inputs.py:316-322`); `_related_target_attr = "orderset"` is the attr the base resolves at `utils/inputs.py:391` (`getattr(related, self._related_target_attr)`), `_related_attr = "related_orders"` the collection at `:390`. The factory is a pure parameterization — all BFS/collision/cache/subclass-rejection logic single-sited in the base. Pinned by `tests/orders/test_factories.py` (10 functions: BFS-reachability, cycle-via-seen-set, leaf/related-annotation, classname-collision, idempotency, shared-input, subclass-rejection, none-target-skip, double-enqueue-dedupe).
- **Layer-6 dynamic OrderSet generation is a genuine deferred non-goal (not a silent gap).** Grep for shipped defs (`get_orderset_class` / `_make_hashable` / `_make_cache_key` / `_create_dynamic_*` / the `_dynamic_orderset_cache` dict) in `orders/factories.py` returns ONLY the TODO-anchor comment at `:90` — zero shipped symbols. The TODO (`:85-96`) names the active design doc (`spec-028-orders-0_0_8 Decision 12`), the forward-reserved symbols, and the reason (connection field consumes the explicit `Meta.orderset_class` sidecar, no auto-gen). AGENTS.md #26-compliant; no `NotImplementedError` pairing required because the default order path is complete and no call path must fail loudly.
- **Low (`del type_name` asymmetry) genuinely forward-looking with an in-source trigger.** The base calls the three-arg `self._build_input_triples(set_cls, type_name, owner_definition)` at `utils/inputs.py:400` — a fixed contract. The filter twin genuinely consumes `type_name`: `filters/factories.py:112` splices `*_build_logic_fields(type_name)` for its `and_`/`or_`/`not_` bag. The order side has no operator bag, so the override accepts and `del`s the arg (`orders/factories.py:74-82`), documented by the inline comment + Spec Decision 8 in the docstring. The `del` becomes a real use only when a future order-family logic surface consumes `type_name` — verbatim in-source trigger present. No edit.

### DRY findings disposition
The only residual cross-folder twin (Layer-6 dynamic-cache primitives live on the filter side only) is correctly **forwarded** to the project pass (`rev-django_strawberry_framework.md`), not merged — the order side is the deferred TODO non-goal, gated behind the in-source trigger. Subclass-layer consolidation is maximal (per-family caches MUST stay distinct namespaces). Confirmed against my filters/factories.py cycle note: grep proved zero source callers of the Layer-6 cache; the lone cross-folder hit is the deferral-TODO in `orders/factories.py` — not a live caller.

### Temp test verification
None used — empty-diff #5; correctness confirmed by grep + reading the named pinning tests.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

- Zero-edit proof: `git diff c0de6394bb259b44ca17e388f02d036f09f38130 -- django_strawberry_framework/orders/factories.py` AND `git diff HEAD -- …` BOTH empty; owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) empty (no sibling attribution needed).
- Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern."; the one Low has verbatim trigger phrasing; no GLOSSARY-only fix.
- No GLOSSARY drift: `OrderArgumentsFactory` / `get_orderset_class` / `_dynamic_orderset_cache` have zero `docs/GLOSSARY.md` entries (private, no `__all__`, not re-exported from `orders/__init__.py` — confirmed absent from its `__all__`); absence correct.
- Prior 0.0.10-cycle Low ("dynamic OrderSet caching" stale claim) resolved upstream by the `orders/` folder pass — grep confirms zero hits in standing docs/tests (only `docs/review/` artifact mentions remain).
- Changelog `Not warranted` with both citations (AGENTS.md #21 + active-plan silence); `git diff -- CHANGELOG.md` empty.
