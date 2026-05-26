# Review: `django_strawberry_framework/utils/relations.py`

Status: verified

## DRY analysis

- None — the module is the canonical home for the `RelationKind` literal, the `MANY_SIDE_RELATION_KINDS` frozenset, and the `relation_kind` / `is_many_side_relation_kind` pair. The four `Literal` members (`"many"`, `"reverse_many_to_one"`, `"reverse_one_to_one"`, `"forward_single"`) are defined once in the `TypeAlias` and reused by callers via the alias and the frozenset (`utils/relations.py:7-19`); the two consumer literal compare sites (`optimizer/walker.py:624` `kind == "reverse_one_to_one"`; `optimizer/field_meta.py:156` and `types/resolvers.py:196` same comparison) read the alias members directly and are intentional shape-narrowing, not duplication of this module's contract. Folder pass `rev-utils.md` is the right place to record any cross-sibling DRY signals if `utils/strings.py` or `utils/typing.py` grow similar enum/literal helpers.

## High:

None.

## Medium:

None.

## Low:

### `relation_kind` `one_to_many` without `auto_created` silently returns `"many"`

The `one_to_many` branch at `utils/relations.py:65-68` returns `"reverse_many_to_one"` when `auto_created=True` and otherwise falls through to `"many"`. Django itself only sets `one_to_many=True` on `ManyToOneRel` descriptors, which always carry `auto_created=True`; the `auto_created=False` branch is a defensive fallback for shapes Django does not emit and is pinned by `tests/utils/test_relations.py:21-24` (`test_relation_kind_classifies_one_to_many_as_many`). The fallback is internally consistent (a list-valued cardinality maps to a list-valued kind), but the docstring (`utils/relations.py:43-55`) enumerates only `many_to_many=True` for `"many"` and does not mention the `one_to_many=True, auto_created=False` branch. Defer until a real Django shape with `one_to_many=True, auto_created=False` is discovered OR until a consumer needs to disambiguate "synthetic many" from "forward M2M"; at that point either tighten the branch to `assert auto_created` (raise on the unknown shape) or split the literal into a distinct member. Comment-pass-eligible only: the docstring could name the fallback explicitly without changing behavior.

### `is_many_side_relation_kind(None)` is a typed valid call

The signature `kind: RelationKind | None` (`utils/relations.py:74`) explicitly admits `None`, and the in-frozenset check at `:76` returns `False` for `None` by construction. `types/resolvers.py:144` calls this with `kind: str | None` from `_check_n1`'s keyword-only parameter (`types/resolvers.py:119-126`), where the `None` legacy-fallback path is part of the documented contract. The `kind: str | None` annotation in `_check_n1` is technically wider than `RelationKind | None` — production callers always pass a real `RelationKind`, so this is forward-compatible widening. Defer until `_check_n1` callers are audited for a non-`RelationKind` `str` ever being passed; tightening `_check_n1`'s `kind` parameter to `RelationKind | None` would document the production contract more precisely. Forward to `rev-utils.md` folder pass only if the same wide-`str` admission pattern appears on a second consumer.

### Examples block in `relation_kind` docstring reads as redundant restatement

The `Examples:` block at `utils/relations.py:57-61` repeats the four bullet mappings from `utils/relations.py:43-55` in a one-line `X-like -> "Y"` shape. The block is mildly useful for fast scanning but does not add information beyond the bullets. Defer; cosmetic — comment-pass candidate only if the bullets above grow more prose and the examples become genuinely useful as a quick-reference index.

## What looks solid

### DRY recap

- **Existing patterns reused.** `relation_kind` is the single classifier consumed by `optimizer/walker.py:14,74,451,623`, `optimizer/field_meta.py:29,106,156`, and `types/resolvers.py:46,144,196`; `is_many_side_relation_kind` is the single many-side predicate consumed by `optimizer/walker.py:74,452`, `optimizer/field_meta.py:28,111`, and `types/resolvers.py:46,144`; `RelationKind` is the single literal alias consumed by `optimizer/field_meta.py:27,104` and `types/relations.py:24,53`. Three helpers, one home, every package consumer routes through the `from ..utils.relations import …` form (`optimizer/walker.py:14`, `optimizer/field_meta.py:27-29`, `types/relations.py:24`, `types/resolvers.py:46`).
- **New helpers considered.** A literal-kind-only `is_single_side_relation_kind` mirror was considered and rejected — every package consumer uses the many-side predicate or compares `kind == "reverse_one_to_one"` directly (`optimizer/walker.py:624`, `optimizer/field_meta.py:156`, `types/resolvers.py:196`); a single-side helper would have only one of those sites as a real consumer and would muddle the contract. The `MANY_SIDE_RELATION_KINDS` frozenset is exposed only by `is_many_side_relation_kind` (no direct package imports) — keeping it module-private would be a fine future refinement (drop the type annotation as a module-level export); defer until a consumer needs to enumerate the many-side membership directly.
- **Duplication risk in the current file.** The four `Literal` members appear in the `TypeAlias` (`utils/relations.py:7-12`) and the two-element frozenset (`utils/relations.py:14-19`); both are intentional canonical home declarations, not duplication — `mypy` would catch a typo on either side because the frozenset is annotated `frozenset[RelationKind]`.

### Other positives

- Four-flag `_RelationFieldLike` `Protocol` (`utils/relations.py:22-35`) documents the read contract while the body's `getattr(..., False)` defends against shapes that omit a flag — narrower-annotation-than-runtime is the right shape for a classifier that has to handle reverse-rel descriptors that may not implement the full protocol.
- Cascade ordering in `relation_kind` is correct: `many_to_many` first short-circuits a forward M2M before any reverse-rel flag is consulted, then `one_to_many` + `auto_created` distinguishes the reverse-FK descriptor from the (Django-impossible-but-defensive) `one_to_many=True, auto_created=False` shape, then `one_to_one` + `auto_created` distinguishes reverse OneToOne from forward OneToOne. The cascade matches the GraphQL list/single semantics every consumer needs.
- Coverage from `tests/utils/test_relations.py` pins seven branches: `many_to_many=True` → `"many"`, `one_to_many=True, auto_created=False` → `"many"` (the defensive fallback), `one_to_many=True, auto_created=True` → `"reverse_many_to_one"`, `one_to_one=True, auto_created=True` → `"reverse_one_to_one"`, `one_to_one=True, auto_created=False` → `"forward_single"`, every `is_many_side_relation_kind` literal + `None`, and the `RelationKind` `typing.get_args` literal-membership pin that ties this module's contract to the `tests/test_registry.py` `PendingRelation(relation_kind=…)` call site.
- `utils/__init__.py:20,25-28` re-exports `RelationKind`, `is_many_side_relation_kind`, and `relation_kind` with the `__all__` audit pinned by `tests/utils/test_relations.py:46-50` (`test_utils_init_reexports_match_submodule`); the dotted-path import is the convenience surface, the submodule path is the canonical one.

### Summary

Three-symbol public surface (`RelationKind`, `relation_kind`, `is_many_side_relation_kind`) plus the `MANY_SIDE_RELATION_KINDS` frozenset and the `_RelationFieldLike` Protocol. The module is the canonical home for the relation-cardinality classifier consumed by `optimizer/walker.py`, `optimizer/field_meta.py`, `types/relations.py`, and `types/resolvers.py`; the cascade ordering is correct, the defensive `getattr(..., False)` fallback paired with the narrower Protocol annotation is the right read contract, and `tests/utils/test_relations.py` pins every branch including the `None` admission on the many-side predicate and the `typing.get_args` literal-membership audit. Three forward-looking Lows captured (defensive `one_to_many=True, auto_created=False` fallback docstring gap; `_check_n1` `kind: str | None` widening at consumer call site; restating-Examples block in `relation_kind` docstring). No DRY findings — this IS the consolidation home for the cross-cutting relation classifier.

---

## Fix report (Worker 2)

Consolidated single-spawn cycle: 0H/0M/3L with all three Lows forward-looking per Worker 1's own prose ("Defer until a real Django shape with `one_to_many=True, auto_created=False` is discovered OR until a consumer needs to disambiguate ...", "Defer until `_check_n1` callers are audited for a non-`RelationKind` `str` ever being passed", "Defer; cosmetic — comment-pass candidate only if the bullets above grow more prose"). DRY analysis is "None — the module is the canonical home". Qualifies under the consolidated-single-spawn rule (all Lows forward-looking; no in-cycle edit required).

### Files touched
- None — no source/test/docstring edits.

### Tests added or updated
- None.

### Validation run
- `uv run ruff format .` — pass / no-changes (118 files left unchanged)
- `uv run ruff check --fix .` — pass / no-changes (All checks passed)

### Notes for Worker 3
- No shadow file used during fix implementation (no source edit).
- Zero-line footprint: `git diff -- django_strawberry_framework/utils/relations.py tests/utils/test_relations.py` is empty.
- All three Lows are explicit forward-looking deferrals with grep-discoverable verbatim trigger phrases (see per-finding dispositions below).
- DRY analysis self-asserts canonical-home status; no DRY findings to route forward.

---

## Comment/docstring pass

Structurally fused with the logic pass under the consolidated single-spawn shape — no source edit, no docstring drift to address.

### Files touched
- None.

### Per-finding dispositions
- Low 1 (`relation_kind` `one_to_many` without `auto_created` silently returns `"many"`): No edit. Worker 1's verbatim trigger phrase: "Defer until a real Django shape with `one_to_many=True, auto_created=False` is discovered OR until a consumer needs to disambiguate 'synthetic many' from 'forward M2M'; at that point either tighten the branch to `assert auto_created` (raise on the unknown shape) or split the literal into a distinct member." Both disjunctive trigger arms preserved verbatim. The "Comment-pass-eligible only: the docstring could name the fallback explicitly without changing behavior" line is itself trigger-gated on the prior shape-discovery — Worker 1's prose frames the docstring touch as conditional on the same trigger, not as an in-cycle act-now.
- Low 2 (`is_many_side_relation_kind(None)` is a typed valid call): No edit. Worker 1's verbatim trigger phrase: "Defer until `_check_n1` callers are audited for a non-`RelationKind` `str` ever being passed; tightening `_check_n1`'s `kind` parameter to `RelationKind | None` would document the production contract more precisely. Forward to `rev-utils.md` folder pass only if the same wide-`str` admission pattern appears on a second consumer." Both arms (audit-trigger AND second-consumer-arm folder forward) preserved verbatim.
- Low 3 (Examples block in `relation_kind` docstring reads as redundant restatement): No edit. Worker 1's verbatim trigger phrase: "Defer; cosmetic — comment-pass candidate only if the bullets above grow more prose and the examples become genuinely useful as a quick-reference index." Trigger preserved verbatim.

### Validation run
- `uv run ruff format .` — pass / no-changes
- `uv run ruff check --fix .` — pass / no-changes

### Notes for Worker 3
- Pattern (11) variant: Worker 1's own per-Low prose self-adjudicates each Low against in-cycle action — quoted verbatim above.
- Pattern (18): folder-pass with 0H/0M/N-Lows-all-with-Worker-1's-verbatim-Defer-prose was the same shape used in cycles 24/25/27; the per-finding dispositions quote those triggers verbatim as evidence-of-no-edit.

---

## Changelog disposition

### State
`Not warranted`

### Reason
Cite BOTH:
- `AGENTS.md` line 21: "Do not update CHANGELOG.md unless explicitly instructed."
- Active plan `docs/review/review-0_0_7.md` is silent on changelog authorisation for this cycle.

Additionally, this is the twenty-eighth consecutive `Not warranted` disposition in the 0.0.7 review chain — chain-length itself is the dominant precedent argument for zero-edit consolidated spawns (pattern (1) from memory). The cycle's footprint is zero-line: no source edit, no test edit, no docstring edit, so there is no consumer-visible change to note.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / no-changes
- `uv run ruff check --fix .` — pass / no-changes

---

## Verification (Worker 3)

### Logic verification outcome
0H/0M/3L all forward-looking; no source/test edit required. Each Low's Worker 2 disposition quotes Worker 1's verbatim "Defer until ..." trigger phrasing with all disjunctive arms preserved: L1 ("`one_to_many=True, auto_created=False` shape discovered" OR "consumer needs to disambiguate 'synthetic many' from 'forward M2M'" + remediation arms "`assert auto_created`" OR "split the literal into a distinct member" + the comment-pass-eligibility sub-clause); L2 (audit-trigger AND second-consumer folder-forward to `rev-utils.md`); L3 (cosmetic comment-pass condition "bullets above grow more prose"). DRY analysis self-asserts canonical-home status — `relation_kind` / `is_many_side_relation_kind` / `RelationKind` / `MANY_SIDE_RELATION_KINDS` are the single home for the cross-cutting classifier consumed by `optimizer/walker.py`, `optimizer/field_meta.py`, `types/relations.py`, `types/resolvers.py`.

### DRY findings disposition
None — module is canonical home; folder pass (`rev-utils.md`) is the right place for any cross-sibling DRY signals once `utils/strings.py` / `utils/typing.py` are reviewed.

### Temp test verification
- None.

### Verification outcome
`cycle accepted; verified` — `git diff -- django_strawberry_framework/utils/relations.py tests/utils/test_relations.py` empty; `git diff -- CHANGELOG.md` empty matching `Not warranted` framing (AGENTS.md:21 + plan silence + twenty-eight-cycle precedent chain); `uv run ruff format .` and `uv run ruff check .` both pass.

---

## Iteration log

(No re-passes; single consolidated spawn closed the cycle.)
