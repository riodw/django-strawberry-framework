# Review: `django_strawberry_framework/optimizer/field_meta.py`

Status: verified

## DRY analysis

- **Extract `FieldMeta._from_field_shape(field, *, is_relation)` to fold the per-attribute extraction shared with `_field_meta_for_resolver`'s test-double fallback.** `optimizer/field_meta.py:130-172` (`FieldMeta.from_django_field`) and `types/resolvers.py:182-212` (`_field_meta_for_resolver`'s `not hasattr(field, "is_relation")` branch) carry an eleven-line, line-for-line identical body: same `is_m2m` / `is_o2m` reads, same `target_field` cache, same many-side `nullable` short-circuit, same `relation_kind(field) == "reverse_one_to_one"` clause, same nine-attribute `FieldMeta(...)` call. The duplicate's own docstring (`types/resolvers.py:182-189`) names the mirror as load-bearing — "the test-double fallback advertises the same shape the canonical builder would" — which is exactly the DRY brittleness condition: two sites that must stay in lock-step but are physically separate. Act-now opportunity. Signature: `FieldMeta._from_field_shape(field: Any, *, is_relation: bool) -> FieldMeta`; `from_django_field` becomes `if not hasattr(...): raise OptimizerError(...); return cls._from_field_shape(field, is_relation=bool(field.is_relation))`; `_field_meta_for_resolver`'s fallback collapses to `return FieldMeta._from_field_shape(field, is_relation=True)`. Removes the maintenance burden the resolver docstring already documents.
- **Defer until a third `FieldMeta` builder lands — collapse the nine sequential `getattr(field, attr, default)` calls in `from_django_field` (`optimizer/field_meta.py:137-171`) through a small attribute-spec tuple iterated into the `cls(**kwargs)` invocation.** Today only two builders exist (`from_django_field` and `_field_meta_for_resolver`'s fallback), and the act-now duplication is best resolved by the bullet above rather than by collapsing the per-attribute loop. Trigger: a third call site that constructs a `FieldMeta` from a Django-field-like object directly (e.g. a future schema-introspection or migration-shadow builder) — at that point a table-driven extraction becomes worth the readability cost.

## High:

None.

## Medium:

None.

## Low:

### `target_field_*` docstring claims "None for non-FK fields" but is populated for forward M2M

The `target_field_name` / `target_field_attname` docstring at `optimizer/field_meta.py:80-83` reads "or `None` for non-FK fields"; `from_django_field` actually populates both from `getattr(field, "target_field", None)` (`field_meta.py:137`), and Django's forward `ManyToManyField` descriptor exposes `target_field` pointing at the target model's PK. So a forward M2M `genres = ManyToManyField(Genre)` resolves to `target_field_name="id"` / `target_field_attname="id"`, not `None`. The behaviour is correct (the column metadata is genuinely available and consumers in `walker.py:586-590` and `walker.py:643-645` do read it through both forward FK and forward-M2M paths); only the docstring under-promises. Recommended change: drop "non-FK" and say "or `None` for descriptors whose `target_field` attribute is absent (most reverse-relation descriptors)". Citation hygiene — same severity calibration as `list_field.py`'s `spec-016 → spec-020` drift and `scalars.py`'s `TODO-ALPHA-028 → TODO-ALPHA-035` drift recorded in worker memory.

```django_strawberry_framework/optimizer/field_meta.py:80-83
        target_field_name: The target model field name a FK points at,
            or ``None`` for non-FK fields.
        target_field_attname: The target model column attname a FK
            points at, preserving non-PK ``to_field`` connector rules.
```

### `GLOSSARY.md` has no `FieldMeta` entry despite cross-module public-import surface

`docs/GLOSSARY.md:825` ("`DjangoType` precomputes optimizer field metadata at class creation.") is the only GLOSSARY trace of the noun. `FieldMeta` itself is absent, even though it is imported across four `types/*.py` modules (`types/base.py:39`, `types/definition.py:10`, `types/converters.py:49`, `types/resolvers.py:43`, `types/finalizer.py:54`) as the canonical relation-shape carrier per the module docstring at `field_meta.py:3-11` ("the canonical single source of truth for relation shape across the package"). Forward to project pass (`rev-django_strawberry_framework.md`) paired with the prior `rev-optimizer___context.md` carry-forward — internal but cross-module-visible symbols are best authored at the project layer together with the `DST_OPTIMIZER_*` constant LITERALS, not as a per-file in-cycle GLOSSARY edit. Same joint-cut deferral pattern as `rev-filters__base.md::Low #5` and `rev-sets_mixins.md`'s GLOSSARY forward.

### Comment block at lines 140-152 is a verbatim narrative duplicate of the `nullable` field docstring at lines 62-76

The 12-line inline comment block at `optimizer/field_meta.py:140-152` ("Many-side cardinalities ... resolves to a manager / queryset ... Reverse OneToOne short-circuits to True ...") is a near-verbatim paraphrase of the same property captured in the `nullable` attribute docstring at `field_meta.py:62-76`. Both blocks live ~80 lines apart in the same module, so the reader has to read both to be sure they agree. Recommended change: replace the inline block with a single one-line comment ("`# Cardinality-gated nullable rule — see ``nullable`` field docstring above for the full rationale.`"). Keeps the single source of truth at the dataclass attribute (where consumers reading the dataclass first encounter the rule) and removes the prose duplication. Comment-pass territory.

```django_strawberry_framework/optimizer/field_meta.py:140-152
        # Many-side cardinalities (reverse FK / M2M, forward or reverse)
        # resolve to a manager / queryset that may be empty but is never
        # ``None``, so the rendered GraphQL annotation is
        # ``list[target_type]`` regardless of any Django ``null`` flag.
        # Force ``nullable=False`` for those shapes BEFORE consulting
        # ``field.null`` — Django's ``ForeignObjectRel`` (parent of
        # ``ManyToOneRel`` / ``ManyToManyRel``) proxies the forward FK's
        # ``null`` flag, so a reverse-FK descriptor for a nullable
        # forward FK would otherwise read ``True`` here. Reverse
        # OneToOne short-circuits to ``True`` because the related row
        # may legitimately be absent; every other single-relation shape
        # follows ``field.null`` with the ``getattr`` default of
        # ``False`` for descriptors that omit it.
```

### `RelationKind` import is used only as a forward-reference annotation

`field_meta.py:27` imports `RelationKind` from `..utils.relations`, but the only runtime use is the `-> RelationKind` return annotation on the `relation_kind` property (`field_meta.py:104`). With `from __future__ import annotations` already active (`field_meta.py:20`), the annotation is a deferred string, so the import is required only for static checkers — same condition that would normally route through `if TYPE_CHECKING:`. Recommended change: move `RelationKind` under the existing `TYPE_CHECKING` block at `field_meta.py:32-33` (keeping `is_many_side_relation_kind` and the helper `relation_kind` function at runtime scope where they are called). Localised maintainability tightening, not a runtime bug.

```django_strawberry_framework/optimizer/field_meta.py:26-30
from ..utils.relations import (
    RelationKind,
    is_many_side_relation_kind,
    relation_kind,
)
```

## What looks solid

### DRY recap

- **Existing patterns reused.** `relation_kind` and `is_many_side_relation_kind` from `utils/relations.py:35` / `:71` are the single classifier home — the property at `field_meta.py:104-111` is a thin delegation, not a re-implementation. Same dispatch home is reused inside `from_django_field` at `field_meta.py:156`. The dataclass-with-`slots=True` shape (`field_meta.py:52`) matches the rest of the package's frozen-snapshot pattern.
- **New helpers considered.** A separate `_extract_target_field_attrs(field)` helper to fold the three `target_field`-derived reads (`field_meta.py:137`, `:168`, `:169`) — rejected because the existing `target_field = getattr(field, "target_field", None)` single-read at line 137 is already the dedup point, and the two downstream `getattr(target_field, ...)` reads are different attributes (`name` vs `attname`). The right helper signature would be `(target_field) -> (name, attname)` which is barely a function. The shadow's "Calls of interest" table (14 entries, all `getattr` / `hasattr`) reads like a smell signal but the per-field defensive shape is load-bearing per the `_DjangoFieldLike` Protocol docstring at `field_meta.py:37-46`.
- **Duplication risk in the current file.** None inside this file — the duplication risk is cross-module, captured by the DRY analysis's first bullet (the `_field_meta_for_resolver` mirror).

### Other positives

- The structural `_DjangoFieldLike` Protocol at `field_meta.py:36-49` documents the read contract narrowly (only `name` + `is_relation` as required; everything else `getattr`-defended) and is consistent with the parallel `_RelationFieldLike` Protocol at `utils/relations.py:19-32` — both document the read contract while keeping `getattr` defences in the bodies. The dual-layered design (narrow Protocol annotation + permissive `getattr` body) is the right shape for accepting Django's forward fields, reverse rels, and M2M rels through one classmethod without per-shape branching.
- `from_django_field`'s `OptimizerError` guard at `field_meta.py:130-134` correctly converts a late `AttributeError` into a typed call-site failure naming the bad input; `exceptions.py:36-40` already names this as one of the two raise sites for `OptimizerError`, so the exception module and the source are in lock-step. Two test pins confirm both the all-missing and partial-shape rejection paths (`tests/optimizer/test_field_meta.py:157-179`).
- The cardinality gate at `field_meta.py:153-158` ordered `is_m2m or is_o2m` FIRST before consulting `field.null` is load-bearing — `tests/optimizer/test_field_meta.py:65-86` (`test_from_django_field_reverse_fk`) and `:89-109` (`test_from_django_field_reverse_many_to_many`) both pin `nullable is False` against Django's `ForeignObjectRel` class-level `null=True` default, exactly the corruption pathway the inline comment block calls out. The reverse-O2O `nullable is True` short-circuit is pinned by `tests/optimizer/test_field_meta.py:146-154`.
- The frozen `@dataclass(frozen=True, slots=True)` shape (`field_meta.py:52`) is the right immutability+memory shape for a per-class-creation cached carrier — `tests/optimizer/test_field_meta.py:182-186` (`test_field_meta_is_frozen`) pins the frozen property explicitly.
- `tests/optimizer/test_field_meta.py:189-221` (`test_is_many_side_pins_every_relation_kind`) covers every `RelationKind` value directly rather than indirectly through the `nullable` short-circuits, which is the right test-discipline call — guards against a future refactor that fixes the property but breaks the nullable rule (or vice versa) silently.

### Summary

`field_meta.py` is a well-factored frozen-snapshot dataclass with one classmethod builder, one classifier-property delegation, and an `_DjangoFieldLike` Protocol that documents the read contract narrowly. Zero High; zero Medium; four Lows are all comment/docstring/import-scope hygiene. The substantive DRY observation is cross-module — `_field_meta_for_resolver`'s fallback at `types/resolvers.py:182-212` line-for-line duplicates `from_django_field`'s body, and the duplicate's docstring already names the mirroring as load-bearing; act-now opportunity for an extracted `FieldMeta._from_field_shape(field, *, is_relation)` builder. GLOSSARY drift is a project-pass forward (no `FieldMeta` entry today despite cross-module public-import surface). Standard three-spawn cycle.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/optimizer/field_meta.py:25-33` — applied Low #4: moved `RelationKind` import out of the runtime block at `..utils.relations` and into the existing `if TYPE_CHECKING:` block. `is_many_side_relation_kind` and `relation_kind` stay at runtime scope (both are called inside `from_django_field` and in the `relation_kind` property body). Verified `from __future__ import annotations` already active at `field_meta.py:20`, so the `-> RelationKind` return annotation at `field_meta.py:104` continues to resolve as a deferred string. Grep-confirmed `RelationKind` appears only at the (now-relocated) import and the single return annotation — no other runtime use anywhere in the module.

### Tests added or updated

- None. Low #4 is an import-scope tightening with no behaviour change; the existing `test_is_many_side_pins_every_relation_kind` (`tests/optimizer/test_field_meta.py:189-221`) and the four `nullable`-pinning tests continue to cover the `relation_kind` property delegation.

### Validation run

- `uv run ruff format .` — pass (211 files unchanged; COM812 formatter-conflict warning is repo-wide and pre-existing).
- `uv run ruff check --fix .` — pass (all checks passed).
- No pytest run (per Worker 2 hard rule).
- `uv.lock` unchanged after both ruff runs.

### Notes for Worker 3

- Low #1 (`target_field_*` docstring "non-FK fields" → forward-M2M-aware wording) is a comment-pass item, intentionally not applied in this logic pass per Worker 2 dicta ("Do not update comments before logic is approved").
- Low #2 (GLOSSARY `FieldMeta` entry) explicitly forwarded by the artifact to the project pass (`rev-django_strawberry_framework.md`); no GLOSSARY edit this cycle.
- Low #3 (inline-comment block at `field_meta.py:140-152` near-duplicating the `nullable` field docstring at `:62-76`) is also a comment-pass item — not applied here.
- DRY analysis act-now opportunity (extract `FieldMeta._from_field_shape(field, *, is_relation)` to dedupe the eleven-line mirror at `types/resolvers.py:182-212`) deferred to the separate DRY cycle per `worker-1.md`; no DRY-driven edit this cycle.
- No shadow file consulted for this trivial import-scope move.
- Pre-existing dirty files in `git status` (TODAY.md, orders/*, GLOSSARY.md, etc.) are out-of-scope concurrent maintainer work; not touched (AGENTS.md rule #33).

---

## Verification (Worker 3)

### Logic verification outcome

Low #4 applied cleanly. `RelationKind` is now imported only under `if TYPE_CHECKING:` at `field_meta.py:31`, alongside the existing `models` typing import. The runtime import at `field_meta.py:26` retains `is_many_side_relation_kind` and the `relation_kind` function — both are runtime-called (the function at `:104` inside the `relation_kind` property and at `:154` inside `from_django_field`'s nullable gate; `is_many_side_relation_kind` at `:109` inside the `is_many_side` property). `from __future__ import annotations` remains active at `field_meta.py:20`, so the `-> RelationKind` return annotation at `:102` resolves as a deferred string and the TYPE_CHECKING relocation does not change runtime behavior. Grep-confirmed `RelationKind` appears exactly twice in the module (the new TYPE_CHECKING import + the property's return annotation) and zero other runtime references.

Low #1 (`target_field_*` docstring "non-FK fields" wording) confirmed untouched at `field_meta.py:77` and `:79` — deferred to comment pass per Worker 2 dicta. Low #3 (inline narrative block duplicating the `nullable` field docstring) confirmed untouched at `field_meta.py:138-150` — also deferred to comment pass. Low #2 (`FieldMeta` GLOSSARY entry) explicitly forwarded by the artifact to the project pass; no GLOSSARY edit attempted this cycle, which matches the forwarding contract.

### DRY findings disposition

Both DRY bullets carried forward unchanged per Worker 1's framing: act-now `_from_field_shape` extraction is deferred to the separate DRY cycle (Worker 2 noted this in `## Notes for Worker 3`), and the second bullet (table-driven `getattr` extraction) is trigger-gated on a third `FieldMeta` builder landing — still only two builders exist (`from_django_field` and `_field_meta_for_resolver`'s fallback), so the trigger remains unfired.

### Temp test verification

None — Low #4 is a no-behavior-change import-scope tightening; ruff format-check + lint pass is sufficient validation per Worker 2's report, and no temp test was needed to disambiguate behavior. Spot-confirmed `uv run ruff format --check` (1 file already formatted) and `uv run ruff check` (all checks passed) on `field_meta.py` directly.

### Verification outcome

logic accepted; awaiting comment pass

---

## Verification (Worker 3, pass 2 — comment pass)

### Comment verification outcome

Low #1 applied per artifact recommendation, widened to name the original premise from the finding header — the `target_field_name` docstring at `field_meta.py:78-83` now names the forward `ManyToManyField` case explicitly (Django's M2M descriptor exposes `target_field` pointing at the target model's PK, so forward M2M resolves to `"id"`, not `None`) AND names the actual `None` condition verbatim from the artifact ("descriptors whose ``target_field`` attribute is absent — most reverse-relation descriptors"). `target_field_attname` at `:84-87` carries the parallel widening for the column-attname half plus the same actual-None condition. The widening to name the forward-M2M case in prose (beyond the artifact's strict "drop ``non-FK``" recommendation) is honest because the finding's own header named the forward-M2M-resolves-to-PK case as the original premise, and the new wording is what makes the docstring correct rather than just less wrong. Both docstrings now describe the populated case (FK and forward M2M both resolve through `target_field`) and the None case (descriptors without the attribute) with no over-promise or under-promise.

Low #3 applied per artifact recommendation — the 12-line inline narrative block at the prior `field_meta.py:140-152` is replaced with a single one-line cross-reference at `:144` (`# Cardinality-gated nullable rule — see ``nullable`` field docstring above for the full rationale.`). 108 chars, within the 110-char E501 grace per AGENTS.md. The single source of truth now lives on the `nullable` attribute docstring at `:60-74` where consumers reading the dataclass first encounter the rule. Verified by `Read`: the `nullable` field docstring already carries the full rationale (many-side short-circuit, reverse-OneToOne short-circuit, every-other-shape follows `field.null`, `ForeignObjectRel` corruption defense). The cross-reference resolves cleanly to that block; no information is lost.

Scope check: diff is exactly the two docstring/comment hunks for Low #1 / Low #3 plus the prior Low #4 import-scope tightening from pass 1. No source-logic edits, no GLOSSARY edits (Low #2 forwarded to project pass per artifact), no drive-by edits. DRY analysis bullets remain deferred per their original framings (act-now extraction to separate DRY cycle; second bullet trigger-gated on a third builder).

### Validation

- `uv run ruff format --check django_strawberry_framework/optimizer/field_meta.py` — pass (1 file already formatted; the repo-wide COM812 formatter-conflict warning is pre-existing).
- `uv run ruff check django_strawberry_framework/optimizer/field_meta.py` — pass (all checks passed).

### Verification outcome

comments accepted; awaiting changelog disposition

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/optimizer/field_meta.py` (`target_field_name` / `target_field_attname` attribute docstrings inside the `FieldMeta` dataclass docstring) — applied Low #1: dropped the inaccurate "or ``None`` for non-FK fields" promise and rewrote the two attribute docstrings to name the forward `ManyToManyField` case explicitly (Django's M2M descriptor exposes `target_field` pointing at the target model's PK, so forward M2M resolves to `"id"` here, not `None`) plus the actual `None` condition ("descriptors whose ``target_field`` attribute is absent — most reverse-relation descriptors"). Mirrors the artifact's recommended wording.
- `django_strawberry_framework/optimizer/field_meta.py` (inline comment immediately above the `if is_m2m or is_o2m:` nullable gate inside `from_django_field`) — applied Low #3: replaced the 12-line inline narrative block with the artifact's recommended one-line cross-reference (`# Cardinality-gated nullable rule — see ``nullable`` field docstring above for the full rationale.`). The single source of truth now lives on the dataclass `nullable` attribute docstring (where consumers reading the dataclass first encounter the rule) and the inline comment is a one-line pointer rather than a near-verbatim duplicate.

### Per-finding dispositions

- Low #1 (`target_field_*` docstring "non-FK fields" wording): applied per artifact recommendation; rewritten to acknowledge the forward-M2M case and correctly name the actual `None` condition.
- Low #2 (`FieldMeta` GLOSSARY entry): forwarded to the project pass (`rev-django_strawberry_framework.md`) per the artifact's explicit routing; no GLOSSARY edit this cycle.
- Low #3 (inline comment block duplicating the `nullable` field docstring): applied per artifact recommendation; 12-line block collapsed to a one-line cross-reference.
- Low #4 (RelationKind import scope): already applied in the logic pass; no change in this comment pass.
- DRY analysis bullets: act-now `_from_field_shape` extraction remains deferred to the separate DRY cycle; trigger-gated table-driven extraction bullet remains unfired.

### Validation run

- `uv run ruff format .` — pass (211 files left unchanged; COM812 formatter-conflict warning is repo-wide and pre-existing).
- `uv run ruff check --fix .` — pass (all checks passed).
- `uv.lock` unchanged after both ruff runs.

### Notes for Worker 3

- Low #1's new wording follows the artifact's exact recommended phrasing ("drop ``non-FK`` and say ``or `None` for descriptors whose `target_field` attribute is absent (most reverse-relation descriptors)``") but widened to also name the forward-M2M-resolves-to-PK case explicitly in the prose, since that case is the original premise behind the artifact's "claims `None` for non-FK but is populated for forward M2M" finding header.
- Low #3's one-line replacement comment runs 107 chars (under the 110 grace limit); ruff format made no change and no E501 was raised.
- No shadow file consulted for these documentation-only edits.
- No tests pin the rewritten docstring text or the rewritten inline comment (grep on `target_field_name` / `Cardinality-gated nullable rule` returns only source-tree matches; no test asserts on either string).

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Cycle edits are internal-only: (a) Low #4 import-scope tightening moved `RelationKind` under `if TYPE_CHECKING:` (no runtime behaviour change; the `-> RelationKind` annotation already resolves as a deferred string under `from __future__ import annotations`); (b) Low #1 rewrote two `FieldMeta` attribute docstrings (`target_field_name` / `target_field_attname`) to drop the inaccurate "non-FK fields" promise — the documented contract now matches the long-standing populated-for-forward-M2M behaviour rather than introducing it; (c) Low #3 collapsed a 12-line inline narrative duplicate into a one-line cross-reference to the canonical `nullable` field docstring (prose de-duplication; the rationale lives at one site rather than two). No consumer-visible behaviour change, no public-API typed-error contract change, no symbol removal. Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorisation for this cycle item — both halves required per `worker-2.md` "Changelog dicta — three-state disposition / Not warranted" — no `CHANGELOG.md` edit is made.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass (211 files left unchanged; repo-wide COM812 formatter-conflict warning pre-existing).
- `uv run ruff check --fix .` — pass (all checks passed).
- `uv.lock` unchanged.

---

## Iteration log

## Verification (Worker 3, pass 3 — terminal verify)

### Terminal verification outcome

All five terminal checks pass:

1. `git diff -- CHANGELOG.md` empty — confirmed.
2. Changelog disposition cites BOTH AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorisation for this cycle item (`review-0_0_7.md` carries no changelog directive for this artifact) — both halves required per `worker-3.md` "Changelog verification job / Not warranted", both present in the disposition prose at this artifact's `Reason` paragraph.
3. Internal-only framing honest — cycle edits are (a) Low #4 `RelationKind` TYPE_CHECKING relocation (no runtime change; `from __future__ import annotations` active at `field_meta.py:20`), (b) Low #1 `target_field_name`/`target_field_attname` attribute docstring rewrite (corrects under-promise; populated-for-forward-M2M behaviour is long-standing, not introduced), (c) Low #3 12-line inline narrative collapse to a one-line cross-reference (prose de-duplication). No symbol added/renamed/removed; no behaviour change; no typed-error contract change. Although `FieldMeta` is cross-module public-imported per Low #2's framing, the public-surface contract is unchanged at the behavioral level — same `Not warranted` precedent as `rev-filters.md` (comment-only on already-public surfaces). The Low #2 GLOSSARY entry was correctly forwarded to the project pass rather than authored here.
4. Logic + comment passes already accepted in pass 1 and pass 2 of this artifact's `## Verification (Worker 3)` blocks — re-spot-verified the prior acceptances on disk: Low #4 import is at `field_meta.py:31` under `if TYPE_CHECKING:`; Low #1 docstring rewrite at `:78-87` names both the forward-M2M-resolves-to-PK case and the actual `None` condition; Low #3 single-line cross-reference at `:144` runs 108 chars; the canonical `nullable` field docstring with full rationale lives at `:60-74`. All matches the artifact's claimed shape.
5. Ruff outcomes recorded — re-ran `uv run ruff format --check django_strawberry_framework/optimizer/field_meta.py` (1 file already formatted) and `uv run ruff check django_strawberry_framework/optimizer/field_meta.py` (all checks passed). Repo-wide COM812 formatter-conflict warning is pre-existing and not introduced by this cycle.

Scope spot-check: `git diff -- django_strawberry_framework/optimizer/field_meta.py` matches the artifact's three edits exactly (TYPE_CHECKING relocation, two attribute-docstring rewrites, one-line comment collapse) — no drive-by edits, no source-logic changes. The broader `git diff --stat HEAD` shows other dirty paths (TODAY.md, orders/*, GLOSSARY.md, etc.) all attributable to concurrent maintainer work or sibling cycles per AGENTS.md #33 — out-of-scope for this artifact.

### Verification outcome

cycle accepted; verified
