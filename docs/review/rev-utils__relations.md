# Review: `django_strawberry_framework/utils/relations.py`

Status: verified

## DRY analysis

- None — the module is the single canonical home for the four-branch Django cardinality classifier; every consumer (`optimizer/walker.py:14`, `optimizer/walker.py:70`, `optimizer/walker.py:478-479`, `optimizer/walker.py:652`, `optimizer/field_meta.py:26`, `optimizer/field_meta.py:108-110`, `optimizer/field_meta.py:115`, `optimizer/field_meta.py:173`, `types/relations.py:24`, `types/resolvers.py:50`, `types/resolvers.py:148`, plus the `utils/__init__.py:20` re-export surface for `tests/test_registry.py`) imports from here rather than duplicating the four-way `many_to_many` / `one_to_many` / `one_to_one` / `auto_created` ladder. The membership shortcut is published as a single `MANY_SIDE_RELATION_KINDS` frozenset that the helper closes over, and `is_many_side_relation_kind` consumes the same set so the "many-side" definition has exactly one source of truth (`django_strawberry_framework/utils/relations.py:14-16, 71-73`). No further factoring available without inventing artificial seams.

## High:

None.

## Medium:

None.

## Low:

### L1 — Reachability gap between docstring and the `one_to_many=True, auto_created=False` branch

`relation_kind`'s body at `django_strawberry_framework/utils/relations.py:62-65` distinguishes two cases under `one_to_many=True`: when `auto_created=True` it returns `"reverse_many_to_one"`, otherwise it returns `"many"`. The docstring (`django_strawberry_framework/utils/relations.py:36-58`) names every shape this classifier intends to recognise — `ManyToManyField` → `"many"`, `ManyToOneRel` → `"reverse_many_to_one"`, `OneToOneRel` → `"reverse_one_to_one"`, `ForeignKey` → `"forward_single"` — but never explains what real Django shape lands on the bare `one_to_many=True, auto_created=False` fallback that maps to `"many"`. In stock Django this combination is not produced by any built-in relation field: `ManyToManyField` sets `many_to_many=True`, reverse FK/M2M descriptors always set `auto_created=True`, and forward FK / forward `OneToOneField` set `one_to_many=False`. The branch is nevertheless test-pinned by `tests/utils/test_relations.py::test_relation_kind_classifies_one_to_many_as_many` (lines 30-38) with a hand-rolled `SimpleNamespace` whose semantics aren't grounded in any Django shape. Either the docstring should add a one-line note that `one_to_many=True` without `auto_created` is a defensive fallback (e.g., custom relation descriptors a third-party app might supply, or future Django private relation flags), or the test should be re-pinned to a documented Django shape so the contract and the body agree. Recommended fix: docstring-only sentence under the bullet list — "Any `one_to_many` shape without `auto_created` falls back to `"many"` as a defensive mapping; stock Django relation descriptors never produce that combination." Drop the corresponding plain bullet ahead of this in the docstring example list if useful. Citation hygiene only — behaviour preserved.

### L2 — `_RelationFieldLike` Protocol's runtime contract is documented twice in slightly different terms

`django_strawberry_framework/utils/relations.py:19-32` declares the Protocol with four `bool` attributes and a docstring that explains why the body uses `getattr(..., False)` (defends against shapes that omit a flag). The runtime helper then re-implements the defensive read on every branch (`getattr(field, "many_to_many", False)`, etc., lines 60-66). The Protocol contract says the attributes are "always present" for the real callers, while the body's `getattr` default contradicts that for the test-double / custom-descriptor case. The two parts agree in spirit but the Protocol's narrower wording ("always present") is the load-bearing claim for type-checkers; the runtime `getattr` defaults exist for non-Django shapes that legitimately omit attributes. Defer-with-trigger: when a fifth caller lands or the test surface grows beyond `SimpleNamespace` fixtures, fold the Protocol's "always present" claim into an `attribute or False` accessor and drop the `getattr(..., False)` repetition. The trigger condition is "next consumer that shapes a `_RelationFieldLike` from a non-Django source." Citation hygiene only — behaviour preserved.

### L3 — Public re-export at `utils/__init__.py` documents `RelationKind` / `relation_kind` / `is_many_side_relation_kind` but the module itself has no `__all__`

`django_strawberry_framework/utils/relations.py` exposes `RelationKind`, `MANY_SIDE_RELATION_KINDS`, `_RelationFieldLike`, `relation_kind`, and `is_many_side_relation_kind` to the wildcard surface (none have an `__all__` gate). The `utils/__init__.py` re-export curates the three public symbols (`utils/__init__.py:20, 25-28`) and the module-level docstring at `utils/__init__.py:7-8` names them as the public surface. Submodule-level `__all__` is not a hard requirement — the sibling `utils/strings.py` / `utils/typing.py` shapes apply too — but adding `__all__ = ("RelationKind", "is_many_side_relation_kind", "relation_kind")` would (a) gate `_RelationFieldLike` and `MANY_SIDE_RELATION_KINDS` away from `from .relations import *` consumers (today there are none, so this is forward-looking), and (b) make the public/private split explicit at the submodule for the next reviewer. Defer-with-trigger: revisit when the sibling utils submodules grow an `__all__` or when a fourth public symbol lands here.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is the canonical home for the four-branch cardinality classifier; every consumer imports from here rather than re-implementing the `many_to_many` / `one_to_many + auto_created` / `one_to_one + auto_created` / fallback ladder (`optimizer/walker.py:14, 70, 478-479, 652`, `optimizer/field_meta.py:26, 108-110, 115, 173`, `types/resolvers.py:50, 148`, `types/relations.py:24`, `utils/__init__.py:20`). `MANY_SIDE_RELATION_KINDS` is the single source of truth for the "many-side" membership set; `is_many_side_relation_kind` closes over it so the predicate cannot drift from the literal.
- **New helpers considered.** Considered: pull the four-branch dispatch into a `tuple[predicate, kind]` table (e.g. `((attrgetter("many_to_many"), "many"), ...)`); rejected — the second branch (`one_to_many`) is a two-step composite test that doesn't fit the flat table, and the current straight-line if-chain reads more clearly than a table-plus-fallback. Considered: collapse `_RelationFieldLike` into a `TypedDict`; rejected — Django relation fields are class instances, not mappings, so the Protocol is the correct typing shape.
- **Duplication risk in the current file.** The `getattr(field, "<flag>", False)` shape repeats four times (`relations.py:60, 62, 63, 66`) but each call reads a distinct attribute; folding through a helper (`_flag(field, "many_to_many")`) would obscure the branch structure rather than DRY meaningful code. Intentional sibling-line repetition, not duplication.

### Other positives

- The docstring distinguishes the runtime cardinality (`"reverse_many_to_one"` "collapses into the many-side for plan building today") from the descriptor identity (the typed `PendingRelation` sentinel needs to disambiguate forward M2M from reverse FK), which is a load-bearing contract — `types/relations.py:53` and the registry tests at `tests/test_registry.py:268, 577, 607, 640, 1193, 1202` consume the descriptor-identity facet.
- Branch coverage is complete in `tests/utils/test_relations.py`: forward M2M (`test_relation_kind_classifies_many_to_many_as_many`), `one_to_many=True` without `auto_created` (`test_relation_kind_classifies_one_to_many_as_many`), reverse FK descriptor (`test_relation_kind_classifies_auto_created_one_to_many_as_reverse_many_to_one`), reverse O2O (`test_relation_kind_classifies_auto_created_one_to_one_as_reverse`), forward single (`test_relation_kind_classifies_forward_single_relations`), the `RelationKind` literal enumeration audit (`test_relation_kind_reverse_many_to_one_is_in_literal`), the `is_many_side_relation_kind` per-kind sweep (`test_is_many_side_relation_kind_matches_list_valued_shapes`), and the re-export identity assertion (`test_utils_init_reexports_match_submodule`). Every public surface symbol is pinned.
- GLOSSARY drift quick-check: `relation_kind`, `RelationKind`, `is_many_side_relation_kind`, `MANY_SIDE_RELATION_KINDS`, and `_RelationFieldLike` are all internal mechanics (consumer-visible relation behaviour is documented under [`Relation handling`](../GLOSSARY.md#relation-handling) at `docs/GLOSSARY.md:888-926`, which describes the GraphQL type shape per Django relation cardinality without naming the helper symbols). Per the memory calibration "Internal-mechanics GLOSSARY absence is correct convention" this is the expected coverage — the helper names are not part of the published consumer contract. Not a finding.
- The `tests/utils/test_relations.py` re-export identity test (`test_utils_init_reexports_match_submodule`) pins `utils.relation_kind is utils.relations.relation_kind` for all three public symbols. This is the right shape — it asserts identity, not just equality, so an accidental re-import via wildcard or a future shim that wraps the helpers would surface as a test failure.
- `from __future__ import annotations` (line 3) demotes the `_RelationFieldLike` parameter annotation on `relation_kind` (line 35) and the `RelationKind | None` annotation on `is_many_side_relation_kind` (line 71) to forward references, so the runtime import of `Protocol` at line 5 is purely for the class-definition base class — no runtime cost on the call path. Correct discipline per the memory calibration "`get_type_hints` / `from __future__ import annotations` discipline."
- `RelationKind` is a `TypeAlias` over a closed `Literal`, which means strict type-checkers will flag any new caller passing an unenumerated string at the call site (e.g. the rev2/rev3 drift documented in `docs/SPECS/spec-023-multi_db-0_0_7.md:38` where `"many_to_one"` was discovered as a non-`RelationKind` string at review-time). This is exactly the contract the alias is designed to enforce.
- Static helper not run for this 73-line module per `REVIEW.md` "Static review helper" optional-under-150-lines threshold; the module is not under `optimizer/` or `types/`. The straight-line classifier has no control-flow hotspots and no reflective access beyond the four `getattr` defaults already audited inline. Skipping the helper does not change the review surface.

### Summary

`utils/relations.py` is a focused 73-line module hosting the four-branch Django relation cardinality classifier (`relation_kind`), its closed-literal type alias (`RelationKind`), the many-side membership predicate (`is_many_side_relation_kind`), and the single source of truth for what counts as "many-side" (`MANY_SIDE_RELATION_KINDS`). The module is the canonical home for this logic — every optimizer, types, and registry consumer imports from here. Three forward-looking Lows around docstring-vs-body reachability commentary, Protocol-vs-runtime-defaults consistency, and a future `__all__` gate; no High or Medium findings. GLOSSARY absence is correct convention per the internal-mechanics calibration.

---

## Fix report (Worker 2)

### Files touched
- `django_strawberry_framework/utils/relations.py::relation_kind` — appended a paragraph to the docstring after the four-bullet shape list explaining that `one_to_many=True, auto_created=False → "many"` is a defensive fallback unreachable from stock Django relation descriptors (with the three concrete reasons: `ManyToManyField` sets `many_to_many=True`; reverse FK/M2M descriptors always set `auto_created=True`; forward FK / forward `OneToOneField` set `one_to_many=False`), and cited the pinning test `tests/utils/test_relations.py::test_relation_kind_classifies_one_to_many_as_many` so the fallback semantics cannot drift. L1 only.

### Tests added or updated
- None. L1 is a docstring-only fix; the contract is already pinned by the existing `test_relation_kind_classifies_one_to_many_as_many` test which the new docstring text now names by qualified path.

### Validation run
- `uv run ruff format .` — pass (213 files unchanged)
- `uv run ruff check --fix .` — pass (All checks passed)

### Notes for Worker 3
- L2 (`_RelationFieldLike` Protocol's "always present" wording vs. `getattr(..., False)` runtime defaults) deferred-with-trigger per dispatch prompt: next consumer that shapes a `_RelationFieldLike` from a non-Django source.
- L3 (submodule `__all__` gate) deferred-with-trigger per dispatch prompt: when sibling utils submodules grow an `__all__` or when a fourth public symbol lands here.
- Shadow file not used; module is 73 lines and outside `optimizer/` / `types/`.
- Concurrent maintainer activity flagged in `git status` (KANBAN/types/optimizer/builder docs/kanban-app/review plan/rev-* sibling artifacts) left untouched per AGENTS.md #33; only `django_strawberry_framework/utils/relations.py` and this artifact were touched by Worker 2 this cycle.
- `uv.lock` unchanged.

---

## Comment/docstring pass

Consolidated single-spawn: the in-cycle edit IS a docstring change, so the logic and comment passes collapse into the same edit. L1 was applied above as part of the single edit; no additional comment-pass work.

### Files touched
- (None beyond the single docstring edit recorded under Fix report.)

### Per-finding dispositions
- Low 1: docstring sentence appended to `relation_kind` per artifact's recommended fix; cites the pinning test by qualified path.
- Low 2: deferred-with-trigger per artifact prose (next non-Django-shape consumer).
- Low 3: deferred-with-trigger per artifact prose (sibling `__all__` adoption or fourth public symbol).

### Validation run
- `uv run ruff format .` — pass (213 files unchanged)
- `uv run ruff check --fix .` — pass

### Notes for Worker 3
Same as Fix report's Notes for Worker 3.

---

## Changelog disposition

### State
Not warranted.

### Reason
Cites BOTH halves required by the worker-2 rule for `Not warranted`: AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan `docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle. The edit is docstring-polish only — no public-API surface, no exception message substring, no consumer-visible behaviour change. Behaviour was preserved bit-for-bit; the docstring now describes what the body already did.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass (213 files unchanged)
- `uv run ruff check --fix .` — pass

---

---

## Verification (Worker 3)

### Logic verification outcome
- **L1** (docstring reachability gap): addressed. The 9-line paragraph at `relations.py:54-61` lands between the four-bullet shape list and the `Examples:` block, enumerates all three reasons no stock Django descriptor produces the `one_to_many=True, auto_created=False` combination (`ManyToManyField` → `many_to_many=True`; reverse FK/M2M → `auto_created=True`; forward FK / `OneToOneField` → `one_to_many=False`), and cites the pinning test by fully-qualified path. Behaviour bit-preserved; the docstring now describes what the body already did.
- **L2** (Protocol "always present" vs `getattr(..., False)` runtime defaults): deferred-with-trigger per the artifact's own verbatim prose — next consumer that shapes a `_RelationFieldLike` from a non-Django source. Source un-changed (`getattr(field, "<flag>", False)` repetition intact at `relations.py:69-75`).
- **L3** (submodule `__all__` gate): deferred-with-trigger per the artifact's own verbatim prose — sibling utils submodules adopt `__all__` OR fourth public symbol lands here. Source un-changed.

### DRY findings disposition
DRY analysis explicitly recorded "None — no further factoring available without inventing artificial seams"; Worker 2 introduced no DRY edits this cycle and Worker 1's recap stands.

### Temp test verification
- None used. The artifact's L1 fix is docstring-only and is already pinned by `tests/utils/test_relations.py::test_relation_kind_classifies_one_to_many_as_many` (line 30) plus the seven sibling tests in the same file. No focused pytest run required.

### Changelog verification
- `git diff -- CHANGELOG.md` empty — matches `Not warranted` claim.
- Both required citations present in the disposition: AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND active plan `docs/review/review-0_0_7.md` silence on changelog authorization for this cycle.
- "Internal-only" framing honest: `_RelationFieldLike` is leading-underscore private, and `relation_kind` / `RelationKind` / `is_many_side_relation_kind` / `MANY_SIDE_RELATION_KINDS` are internal mechanics per the artifact's GLOSSARY-absence calibration (consumer-visible relation behaviour is documented under `Relation handling` at `docs/GLOSSARY.md:888-926` without naming the helper symbols). The cycle's edit is docstring-polish only; no public-API surface, no exception message substring, no consumer-visible behaviour change.

### Ruff
- `uv run ruff format --check django_strawberry_framework/utils/relations.py` → "1 file already formatted".
- `uv run ruff check django_strawberry_framework/utils/relations.py` → "All checks passed!"

### Verification outcome
cycle accepted; verified.

---

## Iteration log

(No re-passes yet.)
