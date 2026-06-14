# Review: `django_strawberry_framework/types/relations.py`

Status: verified

## DRY analysis

- None — the module is 83 lines hosting exactly two public scaffolding objects (`PendingRelation` frozen dataclass, `PendingRelationAnnotation` sentinel) plus the private `_PendingRelationAnnotationMeta` metaclass at the single canonical home for relation-pending records. The shadow overview confirms 0 control-flow hotspots, 0 calls-of-interest, 0 Django/ORM markers, 0 repeated string literals. The producer (`types/base.py::_build_annotations`, `base.py:1583-1594`) and consumer (`types/finalizer.py::finalize_django_types`, `finalizer.py:575-613`) each import from this module, so the cross-folder consolidation point already exists; any alternative shape would re-introduce the split-truth pattern this module was authored to eliminate (module docstring `relations.py:1-16`).

## High:

None.

## Medium:

None.

## Low:

None — the three Lows on the prior-release (0.0.7, `Status: verified`) artifact are all stale and superseded:

- **Citation-style drift (single-colon `path:symbol`)** — ALREADY FIXED in live source. The module docstring (`relations.py:7,10`) and class docstring (`relations.py:33,34`) now use the canonical AGENTS.md rule-27 `path::QualifiedName` double-colon form (`` ``types/base.py::_build_annotations`` ``, `` ``types/finalizer.py::finalize_django_types`` ``). Re-raising would be a resolved-Low re-raise.
- **spec-014 H1 anchor (defer-with-trigger, no action)** — still correct against the spec on disk; the docstring at `relations.py:3-5` cites the H1 import-order-trap closure. No regression in the spec mapping has fired. No edit warranted.
- **`field_name` raw-vs-snake_case producer pin (defer-with-trigger, no action)** — the contract is single-sourced (one producer: `base.py:1583-1594` stamps `field_name=field.name` raw; one consumer: `finalizer.py:597` rebuilds via `snake_case(pending.field_name)`), and the documented behavior is correct. `tests/types/test_relations.py` pins the identity/equality/set-membership surfaces; the producer-stores-raw / consumer-rebuilds path is indirectly covered through `tests/types/test_definition_order.py`. No third producer has landed; trigger unmet.

## What looks solid

### DRY recap

- **Existing patterns reused.** `PendingRelation` is the sole typed carrier between producer and consumer; both `registry.py` (`add_pending_relation`/`iter_pending_relations`/`discard_pending`, `registry.py:396-425`) and `finalizer.py` type-annotate against this one import. `RelationKind` is reused from `utils/relations.py` (`relations.py:24`), not re-declared — `PendingRelation.relation_kind` shares the same alias the optimizer's `FieldMeta.relation_kind` uses.
- **New helpers considered.** None — the file is two data carriers and a repr-shaping metaclass; there is no logic to extract.
- **Duplication risk in the current file.** None — zero repeated literals per the shadow overview; the `field_name`/`snake_case` split across producer/consumer is deliberate single-sourcing, not duplication.

### Other positives

- **Identity-hash contract is correct and triple-pinned.** `__hash__ = object.__hash__` (`relations.py:56`) overrides the `@dataclass(frozen=True)`-synthesized value hash so a non-hashable `django_field` (Django rel descriptor with `__hash__ = None`) cannot raise `TypeError`. This matches `registry.discard_pending`'s `id()`-based matching exactly (`registry.py:424-425`), and is pinned by `tests/types/test_relations.py` (hash/eq/set-membership with a `_NonHashableField()` stand-in) plus `tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation`. The synthesized value-based `__eq__` is preserved (only `__hash__` is overridden) so the registry value-equality test still holds.
- **Sentinel metaclass is a genuine UX improvement, not cleverness.** `_PendingRelationAnnotationMeta.__repr__` (`relations.py:68-72`) shapes the Strawberry-side `TypeError` message when `finalize_django_types()` is skipped, so the failure names the missing finalize call rather than emitting `<class '...PendingRelationAnnotation'>`. The comment at `relations.py:62-66` documents the precise fire condition (un-rewritten sentinel reaching `strawberry.type`).
- **Producer/consumer contract verified end-to-end.** `_build_annotations` always defers auto-synthesized relations to a `PendingRelation` + installs `PendingRelationAnnotation` (`base.py:1583-1594`); the finalizer rewrites `source_type.__annotations__[field_name]` via `resolved_relation_annotation` and hands the original instances back by identity (`finalizer.py:607-613`). The `consumer_authored` branch (`finalizer.py:590-592`) is documented defense-in-depth — `_build_annotations` already skips the pending append for consumer-annotated fields. Definition-order-independence is real: the finalizer resolves targets through `registry.get(pending.related_model)` post-registration, closing the import-order trap.
- **`nullable`/`relation_kind` snapshot fields honestly scoped.** The docstring (`relations.py:43-46`) states these are self-contained-introspection snapshots and that the production consumer reads the live `FieldMeta` from `field_map` instead — and indeed the finalizer reads `definition.field_map[snake_case(...)]` (`finalizer.py:597`), never `pending.nullable`/`pending.relation_kind`. No stale-snapshot risk.

### Summary

Clean two-carrier module at the single canonical home for definition-order-independent finalization scaffolding. The identity-hash override, the sentinel repr metaclass, and the raw-`field_name`/consumer-`snake_case` split are all correct and verified against the live producer (`base.py`), consumer (`finalizer.py`), and registry (`registry.py`) sites, plus the dedicated test module. The prior-release artifact's three Lows are stale: the citation-style Low is already fixed in live source (now `::` throughout), and the other two were no-action defer-with-trigger items whose triggers remain unmet. No GLOSSARY entry exists for `PendingRelation`/`PendingRelationAnnotation` (correct — internal scaffolding, not public contract). No High, no Medium, no actionable Low, zero edits to any tracked file: a no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format django_strawberry_framework/types/relations.py` — `1 file left unchanged`.
- `uv run ruff check django_strawberry_framework/types/relations.py` — `All checks passed!`.

### Notes for Worker 3
- No High / no Medium. Three Lows, all no-action:
  - Citation-style Low: ALREADY FIXED in live source (`relations.py:7,10,33,34` use `::`). Verified by reading the live file; not re-raised.
  - spec-014 H1 anchor Low: correct against spec on disk; defer-with-trigger, trigger unmet; no edit.
  - `field_name` raw-vs-snake_case producer-pin Low: contract single-sourced (`base.py:1587` producer, `finalizer.py:597` consumer), correct, indirectly tested via `tests/types/test_definition_order.py`; defer-with-trigger (third producer), trigger unmet; no edit.
- No GLOSSARY-only fix in scope: grep of `docs/GLOSSARY.md` for `PendingRelation`/`PendingRelationAnnotation` returned zero hits — these are internal scaffolding symbols, not documented public contract, so no roster/prose drift exists.

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. Logic was accepted with no edits; the docstrings and comments are accurate against live source (producer/consumer/registry sites and the test module all verified). No comment or docstring changes warranted.

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — zero edits to any tracked file (AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed"; active plan `review-0_0_9.md` records no changelog directive for this item).

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit (shape #5) cycle; no High/Medium/actionable Low to address. Independently verified the load-bearing contracts:

- **Cycle diff empty.** `git diff --stat 0872a20 -- django_strawberry_framework/types/relations.py` produces no output; `relations.py` absent from `git status` (byte-unchanged at baseline). "Files touched: None" holds. `git diff -- CHANGELOG.md` empty.
- **Identity-hash override correct (the headline).** Drove live (`config.settings`, fakeshop): `PendingRelation.__hash__ is object.__hash__` (NOT the `@dataclass(frozen=True)` value-hash). A `PendingRelation` carrying a `__hash__ = None` (non-hashable) `django_field` stand-in: `hash(pr)` succeeds, equals `object.__hash__(pr)`, and set-membership works — the value-hash would have raised `TypeError`. The dataclass VALUE `__eq__` is preserved (two distinct-identity, equal-field records compare `==`) while their identity hashes differ.
- **Registry identity-match matches the override.** `discard_pending([pr])` over `{pr, pr2}` (value-equal but distinct identity) removed only `pr` and left `pr2 is` the surviving record — proving `registry.py:424-425` `id()`-keyed matching, exactly what the `object.__hash__` override is for.
- **Single producer / single consumer / snake_case split.** `grep "PendingRelation("` over source = one producer (`base.py:1584`, stamps `field_name=field.name` RAW at :1587). Consumer rebuilds via `definition.field_map[snake_case(pending.field_name)]` (`finalizer.py:597`). No third producer landed → the field_name raw-vs-snake_case defer-with-trigger Low is correctly unmet.
- **Definition-order-independence real.** Producer always defers auto-synthesized relations to a `PendingRelation` + `PendingRelationAnnotation` sentinel (`base.py:1583-1594`); consumer resolves the target through `registry.get(pending.related_model)` post-registration (`finalizer.py:593`), so import order cannot mis-bind (the spec-014 H1 import-order trap). Frozen-dataclass immutability confirmed (`FrozenInstanceError` on attribute set).
- **Sentinel metaclass repr.** `repr(PendingRelationAnnotation)` returns the `finalize_django_types()`-naming message, not `<class '...PendingRelationAnnotation'>`.
- **Test pins grep-match.** `tests/types/test_relations.py` (`_NonHashableField` + `test_pending_relation_hash_is_identity_based...` / `_equality_still_works...` / `_is_set_member...`), `tests/test_registry.py:651` (`test_discard_pending_uses_identity_match_with_real_pending_relation`).

### DRY findings disposition
None — module is two data carriers + a repr metaclass; `RelationKind` reused from `utils/relations.py`, not re-declared. No extraction warranted (confirmed: 0 DRY items in artifact, consistent with shadow overview's 0 hotspots / 0 repeated literals).

### Temp test verification
- No temp test files; all verification via one read-only `uv run python` probe (not persisted).
- Disposition: n/a — no new behavior introduced; existing permanent pins cover the contract.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

The three prior-release Lows are correctly stale/superseded: citation-style already `::` in live source (`relations.py:7,10,33,34` confirmed); spec-014 H1 anchor + field_name raw-vs-snake_case are no-action defer-with-trigger items, triggers unmet (single producer/consumer confirmed by grep). No GLOSSARY entry (`grep PendingRelation docs/GLOSSARY.md` = 0), so no GLOSSARY-only fix in scope. Ruff format-check + check pass (COM812 standing warning).
