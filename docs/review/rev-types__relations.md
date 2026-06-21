# Review: `django_strawberry_framework/types/relations.py`

Status: verified

## DRY analysis

- None — the module is two cooperating scaffolding objects (`PendingRelation`
  frozen dataclass + `PendingRelationAnnotation` sentinel and its metaclass) with
  no logic to share and no repeated literal (static overview: 0 repeated string
  literals, 0 control-flow hotspots, 0 ORM markers, 0 calls of interest). The
  relation-kind vocabulary is single-sourced in `utils/relations.py::RelationKind`
  and imported here, not re-declared; the identity-discard contract the docstring
  describes is single-sourced in `registry.py::TypeRegistry.discard_pending`. There
  is no second pending-record shape to fold against, and folding the metaclass
  `__repr__` message anywhere else would re-couple a sentinel-specific
  schema-construction string to an unrelated site.

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
(`types/finalizer.py` #"definition.field_map[snake_case(pending.field_name)]")
and the unresolved-target error formatter reads only `source_model`,
`field_name`, `related_model` (`types/finalizer.py::_format_unresolved_targets_error`).
The docstring is honest about this — they are deliberately retained as "snapshot
fields kept for self-contained record introspection" while "the production
consumer reads the live ``FieldMeta``" (`types/relations.py` #"snapshot fields
kept for self-contained record introspection"). Carrying them keeps the frozen
record self-describing without a registry round-trip, a reasonable design choice.
This is not a defect today.

Defer until a consumer (a debug/inspection path, or a lazy-resolution branch that
must decide nullability without a finalized `field_map`) actually reads
`pending.nullable` / `pending.relation_kind`; at that point the snapshot becomes
load-bearing and warrants a pinning test. If no such consumer ever lands and the
producer (`types/base.py::_build_annotations` #"PendingRelation(") stays the only
writer, drop the two unused fields rather than keep dead snapshot state.

## What looks solid

### DRY recap

- **Existing patterns reused.** Imports the single-source `RelationKind` alias from
  `..utils.relations` (`types/relations.py` #"from ..utils.relations import RelationKind";
  alias defined at `utils/relations.py:10`) rather than re-declaring the literal-union.
  The identity-based discard contract is owned by
  `registry.py::TypeRegistry.discard_pending` (`registry.py:414-426`); the module
  docstring defers to it rather than reimplementing or asserting hashability locally.
- **New helpers considered.** None warranted — a pure-data record plus a
  sentinel-with-repr has no extractable behavior. The metaclass `__repr__` is the
  single source of the "call finalize_django_types() first" message.
- **Duplication risk in the current file.** `relation_kind` / `nullable`
  (`types/relations.py:53-54`) are deliberate *snapshot* fields, not a duplicate of
  the live `FieldMeta` carried in `DjangoTypeDefinition.field_map`; the docstring is
  explicit that the production consumer uses the live `FieldMeta` instead. Intentional,
  not stale duplication (see the Low for the forward-looking disposition).

### Other positives

- **Identity-hash choice is contract-correct.** `__hash__ = object.__hash__`
  (`types/relations.py` #"identity-based hash; django_field may be unhashable") is
  justified by `django_field: models.Field | models.ForeignObjectRel` being
  potentially non-hashable; a `@dataclass(frozen=True)`-synthesized field-based hash
  would raise on it. It matches the consumer contract exactly:
  `registry.discard_pending` removes resolved records by `{id(record) for record in resolved}`
  (`registry.py:425`), with that method's docstring stating identity is "a stronger
  contract than ``__eq__`` and avoids coupling this module to ``PendingRelation``'s
  hashability." Producer/consumer agree.
- **Producer/consumer wiring is accurate and verified at source.** Producer
  `types/base.py::_build_annotations` constructs the record (`types/base.py` #"PendingRelation(",
  base.py:1600) and installs the sentinel (`types/base.py` #"annotations[field.name] = PendingRelationAnnotation",
  base.py:1610); consumer `types/finalizer.py::finalize_django_types` rewrites the
  sentinel via `resolved_relation_annotation` (`types/finalizer.py` #"= resolved_relation_annotation(",
  finalizer.py:607) and hands the original instance back to `discard_pending`
  (finalizer.py:613). `field_name` is the raw `field.name`, rebuilt at the consumer via
  `snake_case(pending.field_name)` (finalizer.py:597) — matches the docstring.
- **Sentinel metaclass `__repr__` is well-targeted.** It shapes the Strawberry-side
  `TypeError` repr only on the skipped-finalize path; the comment block
  (`types/relations.py` #"The sentinel exists only to be rewritten") explains the
  non-obvious metaclass-for-repr trick — exactly the kind of behavior comments should cover.
- **No import-time side effects, no ORM markers, no reflective access.** Static overview:
  0 ORM markers, 0 calls of interest, 0 control-flow hotspots. Module top level is
  imports + two class definitions + one frozen dataclass; nothing executes at import
  beyond class-body construction. No circular-import risk — `relations.py` imports only
  `utils.relations` (a leaf relative to `types/`), while `base.py`/`finalizer.py` import
  it one-way and `registry.py` uses a `TYPE_CHECKING`-guarded import
  (`registry.py:31`). Symbols are private to `types/` (absent from
  `types/__init__.py::__all__`, `types/__init__.py:35`).
- **Typing quality.** Fully annotated frozen dataclass; `from __future__ import annotations`
  defers evaluation so the `models.Field | models.ForeignObjectRel` union and
  `type[models.Model]` annotations cost nothing at runtime.
- **No GLOSSARY drift.** `PendingRelation` / `PendingRelationAnnotation` are internal
  scaffolding with no dedicated `docs/GLOSSARY.md` entry; GLOSSARY references "pending
  relations" only at the contract level under `finalize_django_types` /
  `__init_subclass__` (GLOSSARY:45/280/556), which stays accurate. Absence of a
  symbol-level entry is correct.

### Summary

`types/relations.py` is a small, well-documented data-scaffolding module: a frozen
`PendingRelation` record and a `PendingRelationAnnotation` sentinel whose metaclass
exists purely to render a helpful schema-construction error when
`finalize_django_types()` is skipped. The cycle diff against baseline
`eae2c94aa186e1d257c3bf4d85cb2708c60853b3` and `git diff HEAD` are both empty, and
`git log baseline..HEAD -- types/relations.py` returns nothing, so there is no source
change to review this cycle. Zero ORM markers, zero reflective access, zero repeated
literals, no import-time side effects, no circular-import risk. Producer/consumer and
`discard_pending` identity-contract claims in the docstrings all re-verified against
source with no drift. The single Low is forward-looking (two snapshot fields the
production consumer does not read, retained intentionally and documented as such). No
High/Medium and no source edit — clean no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (`289 files left unchanged`).
- `uv run ruff check --fix .` — pass (`All checks passed!`).

### Notes for Worker 3
- Shape #5 (no-source-edit). Both `git diff eae2c94aa186e1d257c3bf4d85cb2708c60853b3 -- django_strawberry_framework/types/relations.py`
  and `git diff HEAD -- django_strawberry_framework/types/relations.py` empty;
  `git log eae2c94a..HEAD -- django_strawberry_framework/types/relations.py` returns nothing.
- Single Low (`nullable` / `relation_kind` write-only snapshot fields) is forward-looking
  with an explicit in-source-grounded trigger; no current defect, no edit required.
  Verified the production consumer reads live `FieldMeta` at `types/finalizer.py`
  #"definition.field_map[snake_case(pending.field_name)]" (finalizer.py:597), the producer
  writes both fields at `types/base.py` #"PendingRelation(" (base.py:1600), and the error
  formatter `types/finalizer.py::_format_unresolved_targets_error` reads only
  `source_model`/`field_name`/`related_model`.
- No GLOSSARY-only fix in scope — `PendingRelation`/`PendingRelationAnnotation` carry no
  symbol-level `docs/GLOSSARY.md` entry; the contract-level "pending relations" prose under
  `finalize_django_types`/`__init_subclass__` (GLOSSARY:45/280/556) is accurate.
- Identity-hash contract cross-checked against `registry.py::TypeRegistry.discard_pending`
  (id()-based removal, registry.py:414-426) — producer/consumer agree.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring changes — the
module/class docstrings and the two inline comment blocks are accurate against source
(producer at base.py:1600/1610, consumer rewrite at finalizer.py:607 + discard at
finalizer.py:613, `discard_pending` identity semantics at registry.py:414-426, and the
snapshot-fields note all verified). No stale comments, no restating-the-obvious, no
obsolete TODOs (static overview: 0 TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source/behavior
change and no tracked-file edit this cycle (AGENTS.md #21 "Do not update CHANGELOG.md
unless explicitly instructed"; the active plan `docs/review/review-0_0_11.md` records no
changelog directive for this item).

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit (shape #5) cycle, terminal-verify. Zero-edit proof clean on all four
axes against baseline `eae2c94aa186e1d257c3bf4d85cb2708c60853b3`: `git diff baseline`
empty, `git diff HEAD` empty, `git log baseline..HEAD -- types/relations.py` empty,
owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md
CHANGELOG.md`) empty. Dirty tree is `docs/dry/dry-0_0_11.md` only (out of scope).

High / Medium: both `None.` — independently confirmed genuine.

- **Identity hash/equality (no defect).** `PendingRelation.__hash__ = object.__hash__`
  (`types/relations.py` #"identity-based hash; django_field may be unhashable") is the
  identity contract `TypeRegistry.discard_pending` relies on: it removes resolved
  records via `{id(record) for record in resolved}` (`registry.py:424`), not equality
  or hash. A `@dataclass(frozen=True)`-synthesized field hash would hash
  `django_field` (a `models.Field | models.ForeignObjectRel`, potentially
  non-hashable) and raise. Producer/consumer agree. Pinned by
  `tests/types/test_relations.py::test_pending_relation_hash_is_identity_based_with_non_hashable_django_field`
  (asserts `hash(pending) == object.__hash__(pending)` with a `__hash__ = None`
  stand-in) plus the equality and set-membership siblings.
- **Record-shape field contracts.** Producer `_build_annotations` constructs all seven
  fields at `types/base.py:1600-1608` and installs the sentinel at `:1610`.

The single **Low** (`nullable` / `relation_kind` write-only snapshot fields) is
genuinely forward-looking and confirmed against live source: the production consumer
never reads them — `grep "nullable\|relation_kind"` over `types/finalizer.py` returns
nothing; the consumer re-derives live `FieldMeta` via
`definition.field_map[snake_case(pending.field_name)]` (`types/finalizer.py:597`), and
the unresolved-target formatter reads only `source_model`/`field_name`/`related_model`
(`types/finalizer.py:94-95`). The sole writer is the producer at `base.py:1606-1607`.
The docstring is honest about the snapshot-field intent. No current defect; deferred
with an in-source-grounded trigger. Verbatim trigger phrasing present, not a
GLOSSARY-only fix.

### DRY findings disposition
DRY-None genuine. `RelationKind` is single-sourced at `utils/relations.py:10` and
imported, not re-declared. The identity-discard contract is owned by
`registry.py::TypeRegistry.discard_pending` and deferred to, not reimplemented. No
second pending-record shape to fold against. Nothing forwarded.

### Temp test verification
None — no temp tests needed; existing `tests/types/test_relations.py` pins the
load-bearing identity-hash contract.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
`types/relations.py` checklist box in `docs/review/review-0_0_11.md`.

Shape #5 gates all pass: all three Worker 2 sections open with "Filled by Worker 1 per
no-source-edit cycle pattern."; changelog `Not warranted` cites BOTH AGENTS.md #21 and
the active plan's silence (and `git diff -- CHANGELOG.md` is empty); no GLOSSARY-only
fix (`PendingRelation`/`PendingRelationAnnotation` absent from `types/__init__.__all__`
→ private symbols correctly carry no symbol-level GLOSSARY entry). `uv run ruff format
--check` (2 files already formatted) and `uv run ruff check` (All checks passed!) pass.
