# Review: `django_strawberry_framework/types/relations.py`

Status: verified

## DRY analysis

- None — the module owns two intentionally-distinct scaffolding objects (a frozen dataclass record at `relations.py:27-56` and a metaclass-bearing sentinel class at `relations.py:59-82`); neither has a sibling implementation worth collapsing through a shared helper. The `__hash__ = object.__hash__` idiom at `relations.py:56` is local-by-design (frozen dataclass + per-instance identity) rather than a cross-file pattern, and the metaclass `__repr__` at `relations.py:68-72` is the only `type.__repr__` override in the package. No deferred-with-trigger candidate.

## High:

None.

## Medium:

None.

## Low:

### Module docstring drifts on `source_type` vs. dataclass field semantics

The module docstring at `relations.py:1-16` (and the `PendingRelation` class docstring at `relations.py:29-46`) frames the record as "a relation field whose target ``DjangoType`` was not yet registered at collection time" but the dataclass field at `relations.py:48` (`source_type: type`) holds the OWNING `DjangoType` class, not the target — the target's `models.Model` lives in `related_model` (`relations.py:52`). A first-time reader who has not yet traced `_build_annotations` (`base.py:838-849`) may misread `source_type` as "the source/target of the relation." The drift is internal-doc-only (no test pin against the substring), so this stays Low. Consider a one-line clarification in the class docstring, e.g. "``source_type`` is the owning ``DjangoType`` subclass; ``related_model`` is the (not-yet-registered) target's Django model." Defer until the next refactor touches `relations.py`; the contract is read-pinned by `tests/types/test_definition_order.py:65-66,89-90` and `tests/test_registry.py:259,567-568,1172-1181` even with the imprecise prose.

### Sentinel `__repr__` is class-level, not instance-level

The metaclass `__repr__` at `relations.py:68-72` only fires when Strawberry calls `repr(cls)` (which it does for unbound annotations). If a future code path ever stores an INSTANCE of `PendingRelationAnnotation` somewhere (none exists today; the class is referenced by identity at `base.py:849` and `finalizer.py:202` rewrites the slot), the instance `__repr__` falls back to `object.__repr__` and the helpful "call finalize_django_types() before constructing strawberry.Schema" hint is lost. The trigger-gated fix is "if a code path ever instantiates `PendingRelationAnnotation()`, add a sibling `__repr__` on the class body so instance reprs surface the same message." Today the sentinel is class-as-value, so this is a pure forward-looking note.

### `PendingRelation.field_name` semantics worth pinning in the docstring

The `PendingRelation` docstring at `relations.py:40-43` already notes that `field_name` is the raw Django `field.name` and snake-casing is rebuilt at the consumer, but the snake-case rebuild site at `finalizer.py:194` (`field_meta = definition.field_map[snake_case(pending.field_name)]`) is the only canonical consumer. If a future Phase-2/3 helper grows a parallel `field_map` read site (the carry-forward "consumer_authored_fields four-corner contract" from `rev-types__base.md` Medium M2 audit), each new site must repeat the `snake_case(...)` wrap. Defer until a second `field_map` read of `pending.field_name` lands; then promote `pending.field_map_key` (cached property on the dataclass) as the canonical accessor.

## What looks solid

### DRY recap

- **Existing patterns reused.** Frozen-dataclass-with-identity-hash idiom at `relations.py:27-56` mirrors the producer/consumer hand-back contract pinned by `registry.discard_pending()` (`registry.py:337-348`). Module docstring's producer/consumer citation chain at `relations.py:7-15` matches the `base.py:838-849` → `finalizer.py:172-208` → `registry.py:347` loop end-to-end.
- **New helpers considered.** Considered hoisting `__hash__ = object.__hash__` into a shared `IdentityFrozenDataclass` mixin in `utils/`. Rejected: only one such record exists in the package, the one-line override is more readable than the import, and the load-bearing comment at `relations.py:56` explains the rationale inline. Re-triage if a second identity-hashed frozen dataclass lands.
- **Duplication risk in the current file.** None — the file is 82 lines with two distinct symbols and one helper metaclass; no near-copies. The metaclass + sentinel split is the canonical Python pattern for "useful `repr()` on an unbound class-as-value."

### Other positives

- Identity-based `discard_pending` contract is correctly motivated at `relations.py:13-15` and at `registry.py:340-345`; both citation chains agree, and the docstring explicitly calls out non-hashable `django_field` as the reason — this is the kind of "why not equality?" rationale that survives reader trust.
- Snapshot fields (`nullable`, `relation_kind`) at `relations.py:53-54` are correctly framed at `relations.py:42-45` as "kept for self-contained record introspection; the production consumer reads the live ``FieldMeta`` from ``DjangoTypeDefinition.field_map`` instead" — this matches the per-`FieldMeta` lookup at `finalizer.py:194` and avoids the parallel-data-flow concern the `rev-types__definition.md` Medium flagged for `definition.primary`.
- Sentinel `__repr__` contract at `relations.py:68-72` is test-pinned end-to-end by `tests/types/test_definition_order_schema.py:77-98` (the "Unexpected type" + "finalize_django_types()" substring assertion) and by `tests/types/test_base.py:774-775` (the identity check + repr substring). The metaclass-bearing-sentinel design is load-bearing for the consumer-facing error message and the tests prove it.
- Cooperation with finalizer Phase 1 is clean: `base.py:838-849` records the `PendingRelation` instance and writes the sentinel into `cls.__annotations__`; `finalizer.py:172-208` (Phase 1 loop) walks `registry.iter_pending_relations()`, rewrites the slot via `resolved_relation_annotation` at `finalizer.py:202`, and hands every consumed instance back via `registry.discard_pending()`. The consumer-authored short-circuit at `finalizer.py:187-189` re-uses the same identity-hand-back path, and the defense-in-depth comment at `finalizer.py:181-186` correctly explains why that branch is a no-op under the documented call graph.
- `from __future__ import annotations` at `relations.py:18` keeps `source_type: type`, `django_field: models.Field | models.ForeignObjectRel`, and `related_model: type[models.Model]` purely string-typed at runtime so the dataclass does not pay PEP-604-evaluation cost during collection.

### Summary

Small, focused scaffolding module (82 lines, two symbols + one helper metaclass) that owns the spec-014 H1 deferred-resolution contract. No High or Medium findings. The frozen-dataclass-with-identity-hash + metaclass-bearing-sentinel design is the right shape for the producer/consumer hand-back loop with `registry.discard_pending()`, and the sentinel `__repr__` is test-pinned by `tests/types/test_definition_order_schema.py:77-98`. Three trigger-gated Lows: a Low docstring-clarity note on `source_type` framing (the field holds the OWNING `DjangoType`, not the target — easy first-time-reader misread), a forward-looking note on class-vs-instance `__repr__` if a code path ever instantiates the sentinel, and a deferred `pending.field_map_key` cached-property promotion gated on a second `field_map` read site landing. Cooperation with finalizer Phase 1 (`finalizer.py:172-208`) is clean and the citation chain end-to-end (producer `base.py:838-849` → record consumer `finalizer.py:172-208` → registry hand-back `registry.py:337-348`) reads coherent in both directions.

---

## Fix report (Worker 2)

### Files touched
- None — consolidated single-spawn no-source-edit pass. All three Lows are explicitly forward-looking per Worker 1's verbatim deferral prose; 0H/0M.

### Tests added or updated
- None — no source edit; existing pin set (`tests/types/test_definition_order_schema.py:77-98`, `tests/types/test_base.py:774-775`, `tests/types/test_definition_order.py:65-66,89-90`, `tests/test_registry.py:259,567-568,1172-1181`) remains load-bearing as cited in Worker 1's "What looks solid".

### Validation run
- `uv run ruff format .` — pass / no-changes (118 files left unchanged)
- `uv run ruff check --fix .` — pass / no-changes (all checks passed)
- No pytest per `START.md` standing rule and `AGENTS.md` (no test or source change in this cycle).

### Notes for Worker 3
- Shadow file used: none in this consolidated spawn; Worker 1's `docs/shadow/relations.overview.md` consulted during review remains a planning aid only.
- Forward-looking Lows with verbatim trigger phrases (each grep-discoverable from Worker 1's prose under the corresponding Low):
  - Low #1 (`source_type` docstring drift) — verbatim trigger: "Defer until the next refactor touches `relations.py`; the contract is read-pinned by `tests/types/test_definition_order.py:65-66,89-90` and `tests/test_registry.py:259,567-568,1172-1181` even with the imprecise prose."
  - Low #2 (sentinel class-vs-instance `__repr__`) — verbatim trigger: "if a code path ever instantiates `PendingRelationAnnotation()`, add a sibling `__repr__` on the class body so instance reprs surface the same message."
  - Low #3 (`pending.field_map_key` cached-property promotion) — verbatim trigger: "Defer until a second `field_map` read of `pending.field_name` lands; then promote `pending.field_map_key` (cached property on the dataclass) as the canonical accessor."
- No false-premise rejections.
- Consolidated single-spawn rationale: artifact qualifies under bullet 1 of `worker-2.md` ("All Lows are explicitly forward-looking per Worker 1's own prose ... no in-cycle edit required.") and is reinforced by 0H/0M and Worker 1's "None — at the right granularity" DRY framing.

---

## Comment/docstring pass

(Fused into the consolidated spawn; structurally a no-op because there is no logic change to redescribe and no in-cycle docstring touch.)

### Files touched
- None.

### Per-finding dispositions
- Low #1 (`source_type` docstring drift): no edit. Worker 1's own prose: "Defer until the next refactor touches `relations.py`; the contract is read-pinned by `tests/types/test_definition_order.py:65-66,89-90` and `tests/test_registry.py:259,567-568,1172-1181` even with the imprecise prose." Trigger condition not yet satisfied — no refactor in this cycle touches `relations.py`.
- Low #2 (sentinel `__repr__` class-vs-instance): no edit. Worker 1's own prose: "Today the sentinel is class-as-value, so this is a pure forward-looking note." `grep -rn "PendingRelationAnnotation()" --include="*.py" .` returns zero instantiations; the only references are identity-class references at `base.py:849` and `finalizer.py:202`, matching the artifact's evidence at `relations.py:25`.
- Low #3 (`pending.field_map_key` promotion): no edit. Worker 1's own prose: "Defer until a second `field_map` read of `pending.field_name` lands". `finalizer.py:194` remains the sole canonical consumer of `field_map[snake_case(pending.field_name)]`; second-site trigger not satisfied.

### Validation run
- `uv run ruff format .` — pass / no-changes
- `uv run ruff check --fix .` — pass / no-changes

### Notes for Worker 3
The three Lows fall under pattern (11) from `worker-memory/worker-2.md`: Worker 1's own prose self-asserts forward-looking framing for each, and the trigger phrases are quoted verbatim above for grep discoverability. The comment pass is structurally a no-op extending pattern (15) to no-source-edit cycles — there is no post-edit contract to redescribe.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Per `AGENTS.md` line 21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan `docs/review/review-0_0_7.md`'s silence on changelog authorisation for this cycle (the dispatch prompt names neither a release-note carve-out nor an explicit authorisation). The cycle's edits are zero — no source change, no test change, no docstring change — which is the strongest possible "internal-only" footprint and additionally invokes the twenty-four-deep 0.0.7 precedent chain (`rev-_django_patches.md` through `rev-types__finalizer.md`, all `Not warranted`).

### What was done
No `CHANGELOG.md` edit. The cycle's footprint is zero source/test/docstring lines touched; the only artifact changes are the standard Worker 2 sections in `rev-types__relations.md` plus the `Status:` line transition from `under-review` to `fix-implemented`. There is no consumer-visible behaviour change to record.

### Validation run
- `uv run ruff format .` — pass / no-changes
- `uv run ruff check --fix .` — pass / no-changes

---

## Iteration log

(No re-passes yet; consolidated single-spawn closed the cycle in one shot.)

---

## Verification (Worker 3)

### Logic verification outcome
0H/0M; three Lows all forward-looking with verbatim trigger phrasing preserved in Worker 2's `### Notes for Worker 3`:
- Low #1 (`source_type` docstring drift): verbatim trigger "Defer until the next refactor touches `relations.py`; the contract is read-pinned by `tests/types/test_definition_order.py:65-66,89-90` and `tests/test_registry.py:259,567-568,1172-1181` even with the imprecise prose." matches Low body at `rev-types__relations.md:21`.
- Low #2 (sentinel class-vs-instance `__repr__`): verbatim trigger "if a code path ever instantiates `PendingRelationAnnotation()`, add a sibling `__repr__` on the class body so instance reprs surface the same message." matches Low body at `rev-types__relations.md:25`.
- Low #3 (`pending.field_map_key` cached-property promotion): verbatim trigger "Defer until a second `field_map` read of `pending.field_name` lands; then promote `pending.field_map_key` (cached property on the dataclass) as the canonical accessor." matches Low body at `rev-types__relations.md:29`.

### DRY findings disposition
None — Worker 1 recorded "None" under DRY analysis; no carry-forward.

### Temp test verification
- Temp test files used: none.
- Disposition: n/a.

### Changelog disposition verification
`git diff -- CHANGELOG.md` is empty. The disposition cites BOTH `AGENTS.md` line 21 AND the active plan `docs/review/review-0_0_7.md`'s silence on changelog authorisation for this cycle, plus the twenty-four-deep 0.0.7 precedent chain. Cycle's source/test/docstring footprint is zero, so the "internal-only" framing is honest (`Not warranted` is the correct state, not "Warranted but deferred").

### Validation
- `git diff -- django_strawberry_framework/types/relations.py` empty.
- `git diff -- CHANGELOG.md` empty.
- `uv run ruff format --check .` clean (118 files already formatted).
- `uv run ruff check .` clean (all checks passed).

### Verification outcome
`cycle accepted; verified` — top-level `Status: verified`; ticking `docs/review/review-0_0_7.md:121` for `django_strawberry_framework/types/relations.py`.
