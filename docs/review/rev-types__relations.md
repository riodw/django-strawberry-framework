# Review: `django_strawberry_framework/types/relations.py`

Status: verified

## DRY analysis

- None — the module is two cooperating scaffolding objects (`PendingRelation` frozen dataclass + `PendingRelationAnnotation` sentinel and its metaclass) with no logic to share and no repeated literal (shadow "Repeated string literals": none). There is no second relation-record shape to fold against; the only candidate near-twin would be a future lazy/forward-reference pending record, and none exists. Folding the metaclass `__repr__` string anywhere else would re-couple a sentinel-specific schema-construction message to an unrelated site.

## High:

None.

## Medium:

None.

## Low:

### `nullable` / `relation_kind` snapshot fields are write-only at the production consumer

`PendingRelation` carries `relation_kind: RelationKind` and `nullable: bool`
(`types/relations.py::PendingRelation`), but the production consumer never reads
them: `finalize_django_types` re-derives the live `FieldMeta` via
`definition.field_map[snake_case(pending.field_name)]`
(`types/finalizer.py` #"field_meta = definition.field_map[snake_case(pending.field_name)]")
and the unresolved-target error formatter only reads `source_model`,
`field_name`, `related_model`
(`types/finalizer.py::_format_unresolved_targets_error`). The docstring is
honest about this — they are deliberately retained as "snapshot fields kept for
self-contained record introspection" while "the production consumer reads the
live ``FieldMeta``" (`types/relations.py` #"snapshot fields kept for
self-contained record introspection"). Carrying them keeps the record
self-describing without a registry round-trip, which is a reasonable design
choice for a frozen record. This is not a defect today.

Defer until a consumer (a debug/inspection path, or a lazy-resolution branch
that must decide nullability without a finalized `field_map`) actually reads
`pending.nullable` / `pending.relation_kind`; at that point the snapshot becomes
load-bearing and warrants a pinning test. If no such consumer ever lands and the
producer (`types/base.py::_build_annotations` #"PendingRelation(") is the only
writer, drop the two unused fields rather than keep dead snapshot state.

## What looks solid

### DRY recap

- **Existing patterns reused.** Imports the single-source `RelationKind` alias from `utils/relations.py::RelationKind` (`types/relations.py` #"from ..utils.relations import RelationKind") rather than re-declaring the literal-union; consistent with the registry's typed sentinel noted in `utils/relations.py` #"the registry's typed ``PendingRelation`` sentinel".
- **New helpers considered.** None warranted — a pure-data record plus a sentinel-with-repr has no extractable behavior. The metaclass `__repr__` is the single source of the "call finalize_django_types() first" schema-construction message.
- **Duplication risk in the current file.** None — no repeated literals (shadow confirms 0); the only string is the unique metaclass `__repr__` message.

### Other positives

- **Identity-hash choice is contract-correct.** `__hash__ = object.__hash__` (`types/relations.py` #"identity-based hash; django_field may be unhashable") is justified by `django_field: models.Field | models.ForeignObjectRel` being potentially non-hashable, and it matches the consumer contract exactly: `registry.discard_pending` removes resolved records by `{id(record) ...}` set membership (`registry.py::TypeRegistry.discard_pending`), with that method's docstring explicitly stating identity is "a stronger contract than ``__eq__`` and avoids coupling this module to ``PendingRelation``'s hashability." Producer/consumer agree.
- **Producer/consumer wiring is accurate and verified.** The module docstring names `types/base.py::_build_annotations` as producer (confirmed: constructs the record at `types/base.py` #"PendingRelation(" and installs the sentinel at `types/base.py` #"annotations[field.name] = PendingRelationAnnotation") and `types/finalizer.py::finalize_django_types` as consumer (confirmed import + partition at `types/finalizer.py` #"from .relations import PendingRelation"). `field_name` is documented as the raw `field.name` rebuilt via `snake_case(pending.field_name)` at the consumer, matching `types/finalizer.py` #"definition.field_map[snake_case(pending.field_name)]".
- **Sentinel metaclass `__repr__` is well-targeted.** It shapes the Strawberry-side `TypeError` repr only on the skipped-finalize path; the comment block (`types/relations.py` #"The sentinel exists only to be rewritten") explains the non-obvious metaclass-for-repr trick, which is exactly the kind of non-obvious behavior comments should cover.
- **No import-time side effects, no ORM markers, no reflective access.** Shadow overview: 0 ORM markers, 0 calls of interest, 0 control-flow hotspots. Module top level is imports + two class definitions + one frozen dataclass; nothing executes at import beyond class-body construction. No circular-import risk — `relations.py` imports only `utils.relations` (leaf), while `base.py`/`finalizer.py`/`registry.py` import `relations.py` one-way (registry uses a `TYPE_CHECKING`-guarded import, `registry.py` #"from .types.relations import PendingRelation").
- **Typing quality.** Fully annotated frozen dataclass; `from __future__ import annotations` defers evaluation so the `models.Field | models.ForeignObjectRel` union and `type[models.Model]` annotations cost nothing at runtime.
- **No GLOSSARY drift.** `PendingRelation` / `PendingRelationAnnotation` are internal scaffolding, not documented in `docs/GLOSSARY.md` (grep: zero hits) — no public-contract prose to go stale.

### Summary

`types/relations.py` is a small, well-documented data-scaffolding module: a frozen `PendingRelation` record and a `PendingRelationAnnotation` sentinel whose metaclass exists purely to render a helpful schema-construction error. It is unchanged since baseline 14910230 (empty `git log` and `git diff HEAD`) and is not in the spec-035 changed set. Zero ORM markers, zero reflective access, zero repeated literals, no import-time side effects, no circular-import risk. Producer/consumer/`discard_pending` identity-contract claims in the docstrings all verified against source. The single Low is forward-looking (two snapshot fields the production consumer does not read, retained intentionally and documented as such). No High/Medium and no source edit — clean no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (270 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3
- Shape #5 (no-source-edit). Unchanged since baseline 14910230: `git log --oneline 14910230..HEAD -- django_strawberry_framework/types/relations.py` empty; `git diff HEAD -- django_strawberry_framework/types/relations.py` empty.
- Single Low (`nullable` / `relation_kind` write-only snapshot fields) is forward-looking with an explicit trigger ("until a consumer actually reads `pending.nullable` / `pending.relation_kind`"); no current defect, no edit required. Verified the production consumer reads live `FieldMeta` at `types/finalizer.py` #"definition.field_map[snake_case(pending.field_name)]" and the error formatter (`types/finalizer.py::_format_unresolved_targets_error`) reads only `source_model`/`field_name`/`related_model`.
- No GLOSSARY-only fix in scope (zero `PendingRelation`/`PendingRelationAnnotation` hits in `docs/GLOSSARY.md`).
- Identity-hash contract cross-checked against `registry.py::TypeRegistry.discard_pending` (id()-based removal) — producer/consumer agree.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring changes — the module/class docstrings and the two inline comment blocks are accurate against source (producer, consumer, `discard_pending` identity semantics, snapshot-fields note all verified). No stale comments, no restating-the-obvious, no obsolete TODOs (shadow: 0 TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source/behavior change (AGENTS.md #21 "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_10.md` records no changelog directive for this item).

---

## Verification (Worker 3)

> Shadow caveat applied: the shadow strips `#` comments and replaces string literals with `...`; its line numbers are not canonical. Source line numbers and the artifact's `path #"substring"` references are treated as authoritative; the shadow was used only to confirm control flow (0 hotspots / 0 ORM markers / 0 calls of interest / 0 repeated literals — all confirmed).

### Logic verification outcome
Shape #5 (no-source-edit) terminal-verify. All findings dispositioned:
- **High / Medium: None** — confirmed. Module is pure data scaffolding: a frozen `PendingRelation` dataclass + a `PendingRelationAnnotation` sentinel whose metaclass renders the skipped-finalize schema-construction error repr. No logic to defect on.
- **Low (`nullable` / `relation_kind` write-only at the production consumer): genuinely no-action.** Verified the two snapshot fields are written by the producer and never read by the consumer:
  - Producer writes both: `types/base.py` #"PendingRelation(" (base.py:1591) sets `relation_kind=field_meta.relation_kind` and `nullable=field_meta.nullable`.
  - Consumer re-derives live `FieldMeta`: `definition.field_map[snake_case(pending.field_name)]` confirmed at `types/finalizer.py` #"field_map[snake_case(pending.field_name)]" (finalizer.py:597).
  - Error formatter reads only `source_model`/`field_name`/`related_model`: confirmed in the body of `_format_unresolved_targets_error` (finalizer.py:92-96) — no `pending.nullable` / `pending.relation_kind` read.
  - Whole-file grep `pending.nullable` / `pending.relation_kind` across finalizer.py = zero hits → write-only confirmed, not merely asserted.
  The docstring is honest ("snapshot fields kept for self-contained record introspection ... the production consumer reads the live ``FieldMeta``", relations.py:43-45) and the Low carries a verbatim in-source-grounded trigger ("until a consumer actually reads `pending.nullable` / `pending.relation_kind`"). Forward-looking, no edit required. Not a GLOSSARY-only fix (`grep -c PendingRelation docs/GLOSSARY.md` = 0).
- **Identity-hash contract correct.** `__hash__ = object.__hash__` (relations.py:56) matches consumer: `discard_pending` removes by `{id(record) for record in resolved}` confirmed at `registry.py::TypeRegistry.discard_pending` (registry.py:424). Producer/consumer agree; `django_field: models.Field | models.ForeignObjectRel` may be unhashable, so identity is the correct contract.
- **Producer/consumer wiring accurate.** Sentinel install confirmed `annotations[field.name] = PendingRelationAnnotation` (base.py:1601); finalizer imports `PendingRelation` and the consumer rewrites the sentinel. No missed logic.
- **No import-time side effects / no circular-import risk.** `relations.py` imports only `utils.relations` (leaf); `RelationKind` is the single-source `TypeAlias` (`utils/relations.py:7`), not a re-declared literal-union. `from __future__ import annotations` defers the union/`type[...]` annotations.

### DRY findings disposition
DRY None — confirmed sound. Two cooperating scaffolding objects with no shared logic and no repeated literal (shadow: 0 repeated string literals). `RelationKind` reused from `utils/relations.py` rather than re-declared. The metaclass `__repr__` is the single source of the "call finalize_django_types() first" message; folding it elsewhere would re-couple a sentinel-specific message to an unrelated site. No act-now opportunity, no forward DRY item.

### Temp test verification
- None used. The Low is write-only-field provenance, decidable by grep (producer writes / consumer never reads); no behavioral suspicion required a temp test.
- Disposition: n/a.

### Shape #5 checklist
1. **Zero this-cycle edit:** `git diff HEAD -- django_strawberry_framework/types/relations.py` empty; target ABSENT from the cycle-owned `git diff --stat HEAD` (the 8 dirty paths are sibling/maintainer work, see attribution below). Last-touch `92ca9aa4` predates HEAD `58ca2def`. Baseline `14910230` in the dispatch prompt is stale relative to HEAD — content verified by grepping quoted substrings, not by trusting the SHA (content-not-identifier).
2. **Worker 2 sections:** all open `Filled by Worker 1 per no-source-edit cycle pattern.` — confirmed (Fix report, Comment/docstring pass, Changelog disposition).
3. **Every Low** has verbatim in-source trigger phrasing; no GLOSSARY-only fix. Confirmed.
4. **Changelog `Not warranted`** cites BOTH AGENTS.md #21 AND the active plan's silence; `git diff HEAD -- CHANGELOG.md` empty. Confirmed. Internal-only framing matches scope (zero source/behavior change, internal scaffolding not in GLOSSARY) — `Not warranted` is the correct state.
5. **Ruff:** `uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (All checks passed!) on the target. Pass.

### Sibling-cycle diff-stat attribution
The cycle-owned diff stat is non-empty but no hunk touches `types/relations.py`. Each dirty path attributes to a CLOSED sibling cycle or to concurrent-maintainer work (AGENTS.md #33):
- `management/commands/_imports.py`, `export_schema.py`, `inspect_django_type.py`, `tests/management/test_imports.py` → `rev-management__commands.md` (verified, [x] review-0_0_10.md:90).
- `optimizer/selections.py` → `rev-optimizer__selections.md` (verified, [x]:98).
- `orders/sets.py` → `rev-orders__sets.md` (verified, [x]:105).
- `tests/orders/test_factories.py` → `rev-orders.md` folder doc-trim (verified).
- `utils/permissions.py` → maintainer `active_permission_targets` classifier landed for the RE-OPENED `rev-filters__sets.md` (verified, [x]:84); its own per-file item `rev-utils__permissions.md` (review-0_0_10.md:124) is still `[ ]` and will be its own future cycle. Not owned by this cycle.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `types/relations.py` checklist box at review-0_0_10.md:116.

---

## Iteration log
