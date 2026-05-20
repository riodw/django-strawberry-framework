# Review: `django_strawberry_framework/types/relations.py`

Status: verified

<!-- Top status reflects the comment + changelog pass; see Comment/docstring pass and Changelog disposition sections below. -->


## DRY analysis

- Defer until a second `PendingRelation` producer lands (e.g. the deferred lazy/forward-reference path mentioned in `types/finalizer.py:179-184`): extract a `PendingRelation.from_field(cls, source_model, field, field_meta)` classmethod to absorb the inline seven-kwarg construction in `_build_annotations` at `types/base.py:810-820`. Single producer today.

## High:

None.

## Medium:

### `@dataclass(frozen=True)` advertises a `__hash__` that fails at runtime when `django_field` is non-hashable, contradicting the registry's identity contract

`PendingRelation` (`types/relations.py:12`) is declared `@dataclass(frozen=True)`, which makes the dataclass machinery emit a `__hash__` built from the seven field values via `hash((source_type, source_model, field_name, django_field, related_model, relation_kind, nullable))`. The class docstring at lines 14-19 explicitly states that `TypeRegistry.discard_pending()` "removes resolved records by identity rather than equality or hash semantics", and `tests/test_registry.py:582-601` pins that `discard_pending` tolerates a `django_field` whose `__hash__` is `None`. But the synthesized `__hash__` ON `PendingRelation` is still defined and callable — anyone who writes `hash(pending)`, `{pending: ...}`, or `set(pendings)` would crash with `TypeError: unhashable type` whenever `django_field` is a non-hashable Django rel descriptor. Today no production code path hashes a `PendingRelation` (grepped: no `hash(pending)`, no set/dict containment), so this is latent — but the dataclass's `frozen=True` flag is the standard "I am hashable" signal that future maintainers will read at face value and reach for. Two ways out: (a) `@dataclass(frozen=True, eq=False)` — drops the synthesized `__eq__`/`__hash__` and falls back to `object` identity-based defaults, exactly matching the docstring contract; (b) `@dataclass(frozen=True)` + explicit `__hash__ = object.__hash__` override — keeps value-based `__eq__` (which `tests/test_registry.py:547-579` relies on at line 573, `assert record_a == record_b`) but restores identity-based hashing. Option (b) preserves the existing test surface. Recommended change: option (b). Test pin: add `tests/utils/test_relations.py` (or `tests/types/test_relations.py`) asserting `hash(PendingRelation(...))` returns the `id()`-derived value and does NOT raise when `django_field` is non-hashable; today the only non-hashable-field test exercises `discard_pending`, not `hash(pending)` directly.

```django_strawberry_framework/types/relations.py:12-27
@dataclass(frozen=True)
class PendingRelation:
    """Relation field whose target ``DjangoType`` was not registered during collection.

    Finalization passes the original record instances back to
    ``TypeRegistry.discard_pending()``, which removes resolved records by
    identity rather than equality or hash semantics.
    """

    source_type: type
    source_model: type[models.Model]
    field_name: str
    django_field: models.Field | models.ForeignObjectRel
    related_model: type[models.Model]
    relation_kind: RelationKind
    nullable: bool
```

## Low:

### `PendingRelation` stores `field_name` as the raw Django `field.name` while the field-map lookup at the consumer snake-cases the same string

`PendingRelation.field_name` (`types/relations.py:23`) stores whatever the producer hands in. The producer at `types/base.py:814` writes `field_name=field.name`, which is the raw Django field name (not snake-cased). The downstream consumer at `types/finalizer.py:192` then writes `definition.field_map[snake_case(pending.field_name)]` — the same string is canonicalised twice (once at `types/base.py:168` when `field_map` is built with snake-cased keys, once at `types/finalizer.py:192` when the lookup snake-cases on the way in). Storing the raw name is the right contract today — the finalizer's `__annotations__` rewrite at `types/finalizer.py:200` uses the raw name (Strawberry sees the Django `field.name`, not the snake-cased variant), and the error formatter at `types/finalizer.py:70` also wants the raw name in the user-visible string. So both forms are needed, but the record only carries one. Recommended change: document the field-name convention on the dataclass — one sentence on `field_name` saying "raw Django `field.name` as stored on the model; the snake-cased form used as a `field_map` key is rebuilt at the consumer via `snake_case(pending.field_name)`." Prevents a future change from "helpfully" snake-casing at the producer and silently breaking the `__annotations__` rewrite. Doc-only; no logic change.

```django_strawberry_framework/types/relations.py:21-27
    source_type: type
    source_model: type[models.Model]
    field_name: str
    django_field: models.Field | models.ForeignObjectRel
    related_model: type[models.Model]
    relation_kind: RelationKind
    nullable: bool
```

### `nullable` is stored on the record but the finalizer never reads it; consumers reach for it via `field_meta.nullable` instead

`PendingRelation.nullable` (`types/relations.py:27`) is populated from `field_meta.nullable` at `types/base.py:818`. The finalizer at `types/finalizer.py:170-206` reads `pending.source_type`, `pending.source_model`, `pending.field_name`, `pending.django_field`, and `pending.related_model` — but never `pending.nullable` or `pending.relation_kind`. The actual `nullable` lookup the resolver/optimizer pipeline needs is reached via `field_meta = definition.field_map[snake_case(pending.field_name)]` (`types/finalizer.py:192`) and then `field_meta.nullable`. Same story for `relation_kind`: stored on the record (line 26), recomputed at consumer sites from `field_meta.relation_kind`. So both fields exist on the dataclass as snapshots taken at producer-time but the consumer prefers the live `field_meta` lookup. Two readings: (a) the record's `nullable` / `relation_kind` are defensive snapshots so the record is self-contained even if `definition.field_map` is somehow torn down; (b) they are vestigial. Today's call graph is (b). Recommended change: either remove `nullable` and `relation_kind` from the dataclass (saves nothing measurable, but tightens the contract surface to "the five fields the finalizer actually reads"), or add a class-docstring sentence stating "snapshot fields kept for self-contained record introspection even when no `DjangoTypeDefinition` is available; the production consumer reads the live `FieldMeta` instead." Low-risk; the audit's `_format_unresolved_targets_error` (`types/finalizer.py:58-79`) only reads `source_model.__name__`, `field_name`, and `related_model.__name__`, so neither field is needed for the consumer-visible error string.

```django_strawberry_framework/types/relations.py:21-27
    source_type: type
    source_model: type[models.Model]
    field_name: str
    django_field: models.Field | models.ForeignObjectRel
    related_model: type[models.Model]
    relation_kind: RelationKind
    nullable: bool
```

### `_PendingRelationAnnotationMeta` is a single-use private metaclass; the class docstring on `PendingRelationAnnotation` at line 47 does not mention the metaclass relationship

`_PendingRelationAnnotationMeta` (`types/relations.py:30-43`) exists only to give `PendingRelationAnnotation` (line 46) a useful `__repr__`. The class docstring on `PendingRelationAnnotation` ("Sentinel annotation rewritten before `strawberry.type` sees the class.") is correct but does not explain why a metaclass is needed at all — a future maintainer scanning the file will see "two classes" and likely guess "metaclass is over-engineering" before reading the comment at lines 33-37 that pins the role. Recommended change: extend `PendingRelationAnnotation`'s docstring one sentence — "Carries `_PendingRelationAnnotationMeta` so the schema-construction `TypeError` (raised when `finalize_django_types()` was skipped and Strawberry sees the un-rewritten sentinel) reports a useful class repr instead of `<class '...PendingRelationAnnotation'>`." Closes the why-a-metaclass gap. Doc-only.

```django_strawberry_framework/types/relations.py:46-47
class PendingRelationAnnotation(metaclass=_PendingRelationAnnotationMeta):
    """Sentinel annotation rewritten before ``strawberry.type`` sees the class."""
```

### Module docstring at line 1 is single-line; the file owns the deferred-relation-resolution scaffolding for the package and deserves a short paragraph

`types/relations.py:1` is a single line: `"""Pending relation records for definition-order-independent ``DjangoType`` finalization."""`. The module's role is load-bearing: it carries the two scaffolding objects (`PendingRelation` record + `PendingRelationAnnotation` sentinel) that close the import-order trap fixed by spec-014 H1, and both are referenced from three sibling modules (`registry.py`, `types/base.py`, `types/finalizer.py`). The module-docstring discipline `types/relay.py:1-21` and `types/finalizer.py:1` (now expanded per its review's L5) sets the bar. Recommended change: expand the module docstring to a short paragraph naming both exports, the producer site (`types/base.py:_build_annotations`), the consumer site (`types/finalizer.py:finalize_django_types`), and the identity-match contract that `TypeRegistry.discard_pending` relies on. Comment-pass work; defer until logic findings are accepted.

```django_strawberry_framework/types/relations.py:1
"""Pending relation records for definition-order-independent ``DjangoType`` finalization."""
```

### Class-level docstring on `PendingRelation` omits the producer/consumer site cross-reference that finalizer.py's sibling formatters carry

`PendingRelation`'s docstring at `types/relations.py:14-19` documents the identity-match contract but does not name the producer (`types/base.py:810-820`) or the consumer (`types/finalizer.py:170-206`). The cross-cycle pattern in `worker-memory/worker-1.md` for sibling cross-references (the three error formatters at `_format_unknown_fields_error` / `_format_unresolved_targets_error` / `_format_ambiguity_error`) makes producer/consumer cross-references a documented family. Recommended change: add one sentence to `PendingRelation`'s docstring — "Constructed by `_build_annotations` (`types/base.py:810-820`) when a relation target type is not yet registered; resolved by `finalize_django_types` (`types/finalizer.py:170-206`) after every `DjangoType` has registered." Doc-only.

```django_strawberry_framework/types/relations.py:13-19
@dataclass(frozen=True)
class PendingRelation:
    """Relation field whose target ``DjangoType`` was not registered during collection.

    Finalization passes the original record instances back to
    ``TypeRegistry.discard_pending()``, which removes resolved records by
    identity rather than equality or hash semantics.
    """
```

## What looks solid

### DRY recap

- **Existing patterns reused.** `RelationKind` is the cardinality TypeAlias from `utils/relations.py:7-12`; `PendingRelation` (`types/relations.py:13-27`) stores the value computed by `relation_kind(field)` at the producer site (`types/base.py:817` via `field_meta.relation_kind`). The single producer is `_build_annotations` (`types/base.py:810-820`) and the single consumer of the record's `field_name` / `related_model` / `django_field` triple is `finalize_django_types` (`types/finalizer.py:170-206`). `PendingRelationAnnotation` is the sentinel installed at `types/base.py:821` and rewritten at `types/finalizer.py:200-204` by `resolved_relation_annotation` (`types/converters.py:312-324`); the `__repr__` shaped by `_PendingRelationAnnotationMeta` (`types/relations.py:30-43`) is asserted at `tests/types/test_base.py:684-685`. Identity-match semantics are pinned by `tests/test_registry.py:547-579` (`test_discard_pending_uses_identity_match_with_real_pending_relation`) and `tests/test_registry.py:582-601` (`test_discard_pending_tolerates_non_hashable_django_field`); `discard_pending` (`registry.py:331-342`) intentionally uses `id()` so it can drop records whose `django_field` is non-hashable.
- **Duplication risk in the current file.** None. No repeated string literals (the static helper's "Repeated string literals" section is empty), no near-copies, no branches that drift from siblings. The `DjangoType` token appears three times — once in the module docstring, once in `PendingRelation`'s class docstring, and once inside `_PendingRelationAnnotationMeta.__repr__` — but each use is purposeful (module purpose, contract surface, runtime error message). The sentinel-class / metaclass / repr triple is one logical unit and is not redundant with any other sentinel in the package (`hints.py` `SKIP`, `_context.py` `_MISSING`, `plans.py` finalize tuple-swap are the worker-memory-flagged sentinel siblings; none of them use a metaclass `__repr__` because none of them are leaked into `__annotations__` where Strawberry would print them).

### Other positives

- Static helper ran cleanly: 48 lines, three symbols (`PendingRelation`, `_PendingRelationAnnotationMeta`, `PendingRelationAnnotation`), no control-flow hotspots, no repeated string literals, no TODO comments, no calls of interest (no reflective access). The file is a pure declaration module — no logic to audit beyond the dataclass shape and the metaclass repr.
- The metaclass-driven `__repr__` (`types/relations.py:39-43`) is the correct pattern for a sentinel that leaks into `__annotations__` and into Strawberry's schema-construction error messages. The comment block at lines 33-37 explicitly pins why the metaclass exists (the sentinel is rewritten by `finalize_django_types`, and `__repr__` exists to shape the `TypeError` when that rewrite was skipped). Sentinel discipline matches the worker-memory pattern (hints.py `SKIP`, _context.py `_MISSING`, plans.py finalize tuple-swap): structural invariant + test pin (`tests/types/test_base.py:684-685` asserts `"finalize_django_types()" in repr(PendingRelationAnnotation)`).
- The dataclass is correctly minimal — `@dataclass(frozen=True)` documents immutability of an instance once constructed, the seven fields are exactly what the audit-error formatter (`types/finalizer.py:58-79`) and the consumer pipeline (`types/finalizer.py:170-206`) need, and identity-based deduplication is the explicit `discard_pending` contract (`registry.py:331-342` + the two identity-pinning tests). The only Medium above (`__hash__` advertising) is about the `frozen=True` flag's side-effect, not the field set.
- One-way dependency direction: `relations.py` imports `..utils.relations.RelationKind` only — no imports from `registry.py`, `types/base.py`, or `types/finalizer.py`. The three siblings all import FROM `relations.py`, never the other way. No circular-import risk; the module is a pure leaf in the dependency graph.
- Forward-reference / lazy-resolution scaffolding hits exactly the two seams that need to know about it: the producer at `types/base.py` (which records pending + installs the sentinel) and the consumer at `types/finalizer.py` (which rewrites the sentinel via `resolved_relation_annotation`). No third call site quietly reads `PendingRelationAnnotation` (grepped: only `tests/types/test_base.py:684-685`, `tests/test_registry.py:452-470`, and `tests/types/test_definition_order.py:65-90` reference the sentinel; production code only writes it at `types/base.py:821` and reads-then-overwrites it at `types/finalizer.py:200`).
- Test surface is strong: `tests/test_registry.py:547-601` pins both the identity-match contract and the non-hashable-`django_field` tolerance; `tests/types/test_base.py:684-685` pins the sentinel-installed + repr behaviour; `tests/types/test_definition_order.py:60-90` pins that the sentinel survives different declaration orders. The dataclass shape is exercised whenever any test calls `services.seed_data` + `finalize_django_types` (per AGENTS.md test-through-real-usage rule).

### Summary

`types/relations.py` is a 48-line leaf module carrying the two scaffolding objects (`PendingRelation` dataclass + `PendingRelationAnnotation` sentinel) that close the import-order trap fixed by spec-014 H1. 0 High / 1 Medium / 5 Low. The Medium is the `@dataclass(frozen=True)` flag advertising a synthesized `__hash__` that fails at runtime whenever `django_field` is non-hashable — contradicting the identity-based `discard_pending` contract the class docstring explicitly names. The five Lows are documentation polish (raw-vs-snake_case field-name convention, snapshot-vs-live `nullable`/`relation_kind` redundancy, why-a-metaclass docstring, module docstring expansion, producer/consumer cross-reference). No logic bugs, no DRY duplication, sentinel discipline matches the worker-memory pattern, and the test surface pins both the identity contract and the non-hashable-`django_field` tolerance.

## Fix report (Worker 2)

### Logic pass — 2026-05-20

**M1 — `__hash__` override on `PendingRelation`**

Applied Worker 1's recommended option (b): added `__hash__ = object.__hash__` inside the `@dataclass(frozen=True)` body at `django_strawberry_framework/types/relations.py:28` (immediately after the seven dataclass fields). This restores identity-based hashing — the same semantics as `discard_pending`'s `id()`-based lookup at `registry.py:331-342` — while preserving the synthesized value-based `__eq__` that `tests/test_registry.py:573` exercises via `assert record_a == record_b`. The inline comment names the rationale (`django_field` may be unhashable).

**Test pin — `tests/types/test_relations.py`**

Created the new test module at `tests/types/test_relations.py` (no pre-existing file). Three tests, all constructed in-test from a `_NonHashableField` stand-in whose `__hash__` is `None`:

- `test_pending_relation_hash_is_identity_based_with_non_hashable_django_field` — asserts `hash(pending) == object.__hash__(pending)` without raising.
- `test_pending_relation_equality_still_works_with_non_hashable_django_field` — asserts reflexive `pending == pending` to pin that the synthesized `__eq__` survives the override.
- `test_pending_relation_is_set_member_with_non_hashable_django_field` — asserts `{pending}` membership and `len() == 1`, exercising the third documented failure path Worker 1 named ("`set(pendings)` would crash").

No DB state needed — the test is purely the dataclass shape, so no `services.seed_data` call. Imports `Category` / `Item` from `apps.products.models` to populate the `source_model` / `related_model` slots with real Django models (matching the shape `tests/test_registry.py:582-601` uses for the same scenario).

**Validation**

- `uv run ruff format .` — pass (101 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed).
- `uv run pytest tests/types/ tests/test_registry.py -x` — 301 passed, 2 skipped, 2 warnings. Coverage line is informational only (focused subset, not full suite).
- `uv run pytest tests/types/test_relations.py -v` — 3 passed (the three new tests).

**Notes for Worker 3**

- No existing tests broke. `tests/test_registry.py:547-579` (the `record_a == record_b` equality assertion at line 573) continues to pass — `object.__hash__` only replaces hashing; the dataclass-synthesized `__eq__` is untouched.
- The five Lows (L1 raw-vs-snake_case field-name doc, L2 nullable/relation_kind snapshot doc, L3 metaclass-why docstring, L4 module-docstring expansion, L5 producer/consumer cross-reference) are all comment-pass work and intentionally deferred per the dispatch instructions.

## Verification (Worker 3)

### Logic pass — 2026-05-20

- M1 accepted. `git diff -- django_strawberry_framework/types/relations.py` shows exactly the recommended option (b): `__hash__ = object.__hash__` added inside the `@dataclass(frozen=True)` body at `types/relations.py:29` with an inline comment naming the rationale (`django_field` may be unhashable). The synthesized value-based `__eq__` is preserved, matching `tests/test_registry.py:573`'s `assert record_a == record_b`.
- Test pin verified. New module `tests/types/test_relations.py` adds three tests built from a `_NonHashableField` stand-in (`__hash__ = None`) with `Category`/`Item` filling the model slots: `test_pending_relation_hash_is_identity_based_with_non_hashable_django_field` (asserts `hash(pending) == object.__hash__(pending)` without raising), `test_pending_relation_equality_still_works_with_non_hashable_django_field` (reflexive `pending == pending`), and `test_pending_relation_is_set_member_with_non_hashable_django_field` (`{pending}` membership + `len() == 1`). All three documented failure paths Worker 1 named (`hash(pending)`, dict key, set member) are pinned.
- `uv run pytest tests/types/ tests/test_registry.py -x` — 301 passed, 2 skipped, 2 warnings. New tests pass; existing `tests/test_registry.py:547-579` (`record_a == record_b`) and `tests/test_registry.py:582-601` (non-hashable `django_field` `discard_pending`) tests continue to pass — the override only replaces hashing, not equality.
- L1-L5 deferred to the comment pass per the dispatch instructions.
- Verification outcome: `logic accepted; awaiting comment pass`.

---

## Comment/docstring pass

### Comment pass — 2026-05-20

Applied all five Lows as docstring-only edits in `django_strawberry_framework/types/relations.py`. No logic touched, no fields removed, no public API change.

- **L1 — `field_name` convention.** Added a sentence to `PendingRelation`'s class docstring stating: "`field_name` is the raw Django `field.name` as stored on the model; the snake-cased form used as a `field_map` key is rebuilt at the consumer via `snake_case(pending.field_name)`." Closes the raw-vs-snake_case convention gap Worker 1 flagged.
- **L2 — `nullable` / `relation_kind` snapshot fields.** Extended the same class docstring with: "`nullable` and `relation_kind` are snapshot fields kept for self-contained record introspection; the production consumer reads the live `FieldMeta` from `DjangoTypeDefinition.field_map` instead." Documentation-only; the fields are not removed (would be a public API change in a pre-alpha but unnecessary for this cycle per dispatch instructions).
- **L3 — `PendingRelationAnnotation` metaclass rationale.** Extended `PendingRelationAnnotation`'s class docstring with: "Carries `_PendingRelationAnnotationMeta` so the schema-construction `TypeError` (raised when `finalize_django_types()` was skipped and Strawberry sees the un-rewritten sentinel) reports a useful class repr instead of `<class '...PendingRelationAnnotation'>`." Closes the why-a-metaclass gap.
- **L4 — module docstring expansion.** Replaced the single-line module docstring with a short paragraph naming both exports (`PendingRelation`, `PendingRelationAnnotation`), the producer site (`types/base.py:_build_annotations`), the consumer site (`types/finalizer.py:finalize_django_types`), the spec anchor (spec-014 H1 import-order trap), and the identity-match contract that `TypeRegistry.discard_pending` relies on. Modeled after `types/finalizer.py`'s expanded module docstring.
- **L5 — `PendingRelation` producer/consumer cross-reference.** Added a sentence to `PendingRelation`'s class docstring naming the producer (`types/base.py:_build_annotations`) and consumer (`types/finalizer.py:finalize_django_types`). Matches the cross-cycle sibling cross-reference pattern.

### Files touched

- `django_strawberry_framework/types/relations.py` — module docstring expansion (L4), `PendingRelation` class docstring expansion (L1, L2, L5), `PendingRelationAnnotation` class docstring expansion (L3). No logic changes.

### Validation

- `uv run ruff format .` — pass (101 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed).

### Notes for Worker 3

- All five edits are docstring-only. The dataclass field list, the `__hash__ = object.__hash__` override from the logic pass, and the metaclass body are untouched.
- L2 explicitly preserves the `nullable` and `relation_kind` fields per dispatch instructions ("do NOT remove the fields — that would be a public API change in a pre-alpha but unnecessary for this cycle").
- L4 module docstring extends to ~16 lines but stays inside the existing triple-quoted block; no module-level executable code was added or removed.

---

## Changelog disposition

### Disposition — 2026-05-20

**Not warranted.**

**Reason.** This cycle's changes are:

- M1 (logic pass, prior): `__hash__ = object.__hash__` restored on `PendingRelation`. Internal — fixes a latent crash if a non-hashable `django_field` is hashed via `hash(pending)`, `{pending: ...}`, or `set(pendings)`, but the production call graph never hashes a `PendingRelation` today (the only consumer is `discard_pending`, which uses `id()` directly). No public API change, no observable behavior change in the production pipeline.
- L1-L5 (this pass): docstring polish only. No public surface or behavior change; no consumer-visible string is altered (the `__repr__` on `_PendingRelationAnnotationMeta` is untouched).

Per `AGENTS.md`: "Do not update CHANGELOG.md unless explicitly instructed." The active review plan and the dispatch instructions for this cycle do not authorize a CHANGELOG edit, and the changes have no consumer-visible impact that would warrant one. Matches the "Not warranted" pattern in `worker-memory/worker-2.md` for internal-only changes + docstring polish.

**What was done.** No edit to `CHANGELOG.md`. Disposition recorded here for the audit trail.

---

## Iteration log

## Verification (Worker 3, pass 2)

### Comment + changelog pass — 2026-05-20

- All five Lows accepted as docstring-only edits in `django_strawberry_framework/types/relations.py`. `git diff -- django_strawberry_framework/types/relations.py` shows: module docstring expanded to a multi-line paragraph naming both exports (`PendingRelation`, `PendingRelationAnnotation`), the producer site (`types/base.py:_build_annotations`), the consumer site (`types/finalizer.py:finalize_django_types`), the spec anchor (spec-014 H1), and the identity-match contract (L4); `PendingRelation` class docstring extended with producer/consumer cross-reference (L5), `field_name` raw-vs-snake_case convention sentence (L1), and `nullable`/`relation_kind` snapshot-vs-live `FieldMeta` sentence (L2); `PendingRelationAnnotation` class docstring extended with the metaclass rationale naming the schema-construction `TypeError` and the un-rewritten-sentinel failure mode (L3). The `__hash__ = object.__hash__` override from the logic pass is preserved verbatim at line 56; the dataclass field list is untouched; no logic changed.
- Changelog disposition "not warranted" accepted. `git diff -- CHANGELOG.md` is empty; the disposition cites both the `AGENTS.md` "do not update CHANGELOG.md unless explicitly instructed" rule AND the active plan's lack of authorization, and names the no-public-API/no-observable-behavior facts (M1 fixes a latent crash never reached by production call sites; L1-L5 are docstring polish).
- Verification outcome: `cycle accepted; verified`.
