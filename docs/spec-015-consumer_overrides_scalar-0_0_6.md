# Spec: Consumer override semantics for scalar fields

Target release: `0.0.6`.
Status: draft (revision 1, initial).
Owner: package maintainer.
Predecessors: [`docs/FEATURES.md`](FEATURES.md) (entries [`DjangoType`](FEATURES.md#djangotype), [`Scalar field conversion`](FEATURES.md#scalar-field-conversion), [`Scalar field override semantics`](FEATURES.md#scalar-field-override-semantics), [`Definition-order independence`](FEATURES.md#definition-order-independence), [`Relation handling`](FEATURES.md#relation-handling)), [`KANBAN.md`](../KANBAN.md) card `WIP-ALPHA-015-0.0.6`.
Card line: ["Consumer override semantics (scalar fields) — extends the `DONE-006-0.0.4` relation-field override contract to scalar fields and closes out the remaining `0.0.6` patch."](../KANBAN.md)

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Surfaces the existing scalar/relation asymmetry in `_build_annotations`, pins the symmetric annotation-only contract for scalars (mirroring the shipped `consumer_annotated_relation_fields` path), confirms the assigned-`strawberry.field` scalar contract already shipped in `0.0.5` and stays unchanged, and lands the previously-skipped `test_consumer_annotation_overrides_synthesized` test as the proof of the new contract.

## Key glossary references

Skim these [`docs/FEATURES.md`](FEATURES.md) entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoType`](FEATURES.md#djangotype) — the base class whose scalar-override gap this card closes.
- [`Scalar field conversion`](FEATURES.md#scalar-field-conversion) — the auto-synthesized scalar annotation path this card lets consumers override.
- [`Scalar field override semantics`](FEATURES.md#scalar-field-override-semantics) — currently `planned for 0.0.6`; flipped to `shipped (0.0.6)` in [Slice 6](#slice-6--docs-kanban-changelog-archive).
- [`Relation handling`](FEATURES.md#relation-handling) — the relation-override path whose annotation-only contract this card mirrors for scalars.
- [`Definition-order independence`](FEATURES.md#definition-order-independence) — the foundation slice (`DONE-006-0.0.4`) that pinned the relation-field override contract; this card extends the same shape to scalars.
- [`ConfigurationError`](FEATURES.md#configurationerror) — raised at type-creation time for unsupported shadow shapes; this card adds no new error sites.

Project conventions to follow:

- [`AGENTS.md`](../AGENTS.md) — schema testing via `schema.execute_sync`. **Note:** `AGENTS.md` prohibits `CHANGELOG.md` edits without explicit permission; [Slice 6](#slice-6--docs-kanban-changelog-archive) grants that permission.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — 100% coverage target; release-bump checklist.
- [`KANBAN.md`](../KANBAN.md) — card-ID format; column movement at Slice 6.
- [`docs/TREE.md`](TREE.md) — package layout; tests mirror source one-to-one.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan).

- [ ] Slice 1: Track annotation-only scalar overrides on `DjangoTypeDefinition`
  - [ ] In `django_strawberry_framework/types/base.py:95-108`, collect a new `consumer_annotated_scalar_fields` frozenset in `DjangoType.__init_subclass__` parallel to `consumer_annotated_relation_fields`. Walks the same `consumer_annotations = dict(getattr(cls, "__annotations__", {}))` mapping but filters on `not field.is_relation` instead of `field.is_relation`. (See [Decision 1](#decision-1--annotation-only-scalar-override-collection).)
  - [ ] Add `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field to `django_strawberry_framework/types/definition.py:DjangoTypeDefinition` after the existing `consumer_assigned_scalar_fields` field. Populated from the new collection above.
  - [ ] Union the new set into the existing `consumer_authored_fields` frozenset at `types/base.py:102-108`. The scalar branch of `_build_annotations` already short-circuits on `consumer_authored_fields` membership (`types/base.py:644`) — once annotation-only scalars are members, synthesis is skipped for them, and the existing post-merge line `cls.__annotations__ = {**synthesized, **consumer_annotations}` at `types/base.py:138` leaves the consumer's annotation untouched. **No change to `_build_annotations` body.**
  - [ ] Plumb the new set through to `DjangoTypeDefinition` at the registration call site (`types/base.py:117-134`).
  - [ ] Tests in `tests/types/test_definition_order.py` (the existing override-contract host, where the three relation-override tests at `:179`, `:206`, `:235` live, plus the `:278` `test_assigned_scalar_field_override_keeps_consumer_resolver` test). The annotation-only scalar contract is the natural fourth sibling; placement matches the existing relation/scalar/annotation/assigned 2×2 matrix:
    - [ ] `test_annotation_only_scalar_field_override_wins_over_synthesized` (H1 — the headline test for this card): declare a `DjangoType` with a Django `CharField` selected and a consumer annotation `description: int` shadowing it. Pre-finalize, assert `cls.__annotations__["description"] is int`. Post-finalize, assert the same — and assert the Strawberry definition's field type matches the consumer's annotation, not the auto-synthesized `str`. This is the test currently skipped at `tests/types/test_base.py:444-465` (rename / move and unskip — see Slice 2).
    - [ ] `test_annotation_only_scalar_override_populates_definition_metadata`: assert `definition.consumer_annotated_scalar_fields == frozenset({"description"})`, `definition.consumer_authored_fields >= frozenset({"description"})`, and `definition.consumer_assigned_scalar_fields == frozenset()` (annotation-only, no assignment).
    - [ ] `test_annotation_only_scalar_override_does_not_emit_synthesized_annotation`: assert the synthesized annotations dict returned by `_build_annotations` does NOT contain `"description"` for the override case. (Pins that the short-circuit fires; without this we could still merge consumer-over-synthesized but the side-effect of double-walking the field path could regress later.)
    - [ ] `test_annotation_only_scalar_override_survives_strawberry_finalization` (H1 regression): the historical skip-reason at `tests/types/test_base.py:444-453` claimed Strawberry's `@strawberry.type` decorator regenerates `cls.__annotations__` after our merge. The current `__init_subclass__` already merges `{**synthesized, **consumer_annotations}` at `types/base.py:138` (consumer last so consumer wins), but the pre-Slice-1 single-source `synthesized` dict still contained the auto-mapped scalar annotation for the field name. Under this card, the synthesized dict no longer contains the consumer-overridden field, so the merge degenerates to "consumer annotation only" — no Strawberry-side regeneration can override it because there's nothing for it to fall back to. This test calls `finalize_django_types()`, builds a `strawberry.Schema(query=Query)` with a query field returning the type, runs `schema.execute_sync(...)` against a `__schema { types { name fields { name type { name } } } }` introspection query, and asserts the override-field's GraphQL type matches the consumer's annotation (e.g., `Int` for the `description: int` example). Pins the end-to-end contract.
- [ ] Slice 2: Unskip / replace `test_consumer_annotation_overrides_synthesized`
  - [ ] Remove the `@pytest.mark.skip` decorator and its reason text at `tests/types/test_base.py:444-453`.
  - [ ] Either (a) delete the test body at `tests/types/test_base.py:454-465` because Slice 1's new tests cover the contract more thoroughly, or (b) keep the existing assertion as a smaller smoke test alongside the Slice 1 tests. Worker 1 picks during planning — the Slice 1 placements name `tests/types/test_definition_order.py` as the canonical host, so the smaller-touch option is (a) to avoid duplicate coverage on a contract pinned more strictly elsewhere.
  - [ ] If (a) was chosen above, also remove the `CATEGORY_SCALAR_FIELDS` reference if it becomes unused (check via `grep` before deleting).
- [ ] Slice 3: Document the four-corner override contract in `_consumer_assigned_fields`'s docstring
  - [ ] After Slice 1 lands, the four-corner override matrix (`relation × annotation`, `relation × assigned`, `scalar × annotation`, `scalar × assigned`) is symmetric and complete. Update the `_consumer_assigned_fields` docstring at `types/base.py:211-220` so it names the parallel `consumer_annotated_relation_fields` / `consumer_annotated_scalar_fields` collection sites in `__init_subclass__`, the four `consumer_*_fields` sets on `DjangoTypeDefinition`, and the single `consumer_authored_fields` short-circuit in `_build_annotations`. This is documentation only — no behavior change. Worker 1 verifies no other docstrings need parallel updates (likely `_build_annotations` already documents the relation+scalar consumer-authored branches; if it does, no change there either).
- [ ] Slice 4: Atomic version-bump quintet (single commit). Same shape as `spec-013-deferred_scalars-0_0_6.md` Slice 5 and `spec-014-meta_primary-0_0_6.md` Slice 5: covers programmatically-checked sites only (`pyproject.toml`, `__init__.py`, `tests/base/test_init.py`'s pinned `__version__`, `docs/FEATURES.md`'s "Current package version" line, `uv.lock`). The two consumer-facing version strings (`README.md`, `docs/README.md`) move in Slice 5. **At spec-authoring time the tree is already at `0.0.6` from `spec-013-deferred_scalars-0_0_6.md` and `spec-014-meta_primary-0_0_6.md`'s Slice 5**, so every checkbox below is expected to be a no-op. The slice still exists in the plan so the build cycle's Worker 1 final-verification pass explicitly `grep`s for stale `0.0.5` strings before marking complete.
  - [ ] `pyproject.toml` — `version = "0.0.6"` (no-op if already at `0.0.6` from any prior `0.0.6` card).
  - [ ] `django_strawberry_framework/__init__.py` — `__version__ = "0.0.6"` (no-op if already bumped).
  - [ ] `tests/base/test_init.py` — pinned `__version__` assertion to `"0.0.6"` (no-op if already bumped).
  - [ ] `docs/FEATURES.md` — "Current package version: `0.0.6`" line (no-op if already bumped).
  - [ ] `uv.lock` — re-lock with `uv lock` (no-op if already at `0.0.6`).
  - [ ] **Prior-`0.0.6`-card note.** `0.0.6` carries three cards (`spec-013-deferred_scalars`, `spec-014-meta_primary`, this card). The first card to land does the real bump; every subsequent card's Slice 4 is a no-op. The Worker 1 final-verification pass MUST `grep` for stale `0.0.5` strings rather than blindly editing — if the bump has already happened, mark every checkbox above complete without re-editing.
- [ ] Slice 5: Docs, KANBAN, CHANGELOG, archive (separate commit; may follow Slice 4 by any interval).
  - [ ] Root `README.md` — confirm the package-version line reads `0.0.6` (no-op if any prior `0.0.6` card already bumped it).
  - [ ] `docs/README.md` — confirm the "shipped today is `0.0.6`" line (no-op if any prior `0.0.6` card already bumped it). Add a one-line mention of scalar override symmetry to the shipped-capability summary.
  - [ ] `docs/FEATURES.md` entries updated:
    - [`Scalar field override semantics`](FEATURES.md#scalar-field-override-semantics) → `shipped (0.0.6)`. Rewrite the body to describe the actual delivered contract: annotation-only and assigned-`strawberry.field` scalar overrides both supported, with the same `consumer_authored_fields` short-circuit; opt-out via `Meta.exclude`; field metadata via the assigned-`strawberry.field(...)` path. Drop the "planned for `0.0.6`" framing.
    - [`Definition-order independence`](FEATURES.md#definition-order-independence) → remove the "Manual scalar-field override semantics remain an implementation detail until [Scalar field override semantics](#scalar-field-override-semantics) ships." closing sentence; the contract is now part of the foundation.
    - [`DjangoType`](FEATURES.md#djangotype) — review the "Current alpha constraints" bullet list (`docs/FEATURES.md:386-388`) and remove any scalar-override-related entry. Today the list only has the relation-cardinality-validation deferral; the spec author should verify nothing scalar-shaped is in there to drop.
    - [Index](FEATURES.md#index) → flip the status badge on `Scalar field override semantics` to `shipped (0.0.6)`.
  - [ ] `docs/TREE.md` — no source-tree changes (no new files); confirm the `types/base.py` and `types/definition.py` per-file annotations in the current-on-disk-layout block don't need updating. The `DjangoTypeDefinition` line in `definition.py` currently reads "canonical per-type metadata with Meta.primary flag and forward-reserved Layer-3 slots" (post-DONE-014); no update needed for this card — the new `consumer_annotated_scalar_fields` field is part of the same internal-metadata shape, not a new public capability.
  - [ ] `TODAY.md` — add scalar override semantics to the "shipped today" section. The fakeshop example does not currently exercise scalar annotation overrides; mention under "available but not currently demonstrated in fakeshop" if that subsection exists.
  - [ ] `KANBAN.md` — move `WIP-ALPHA-015-0.0.6` → `DONE-015-0.0.6`. **Drop in the verbatim body below:**

    ```markdown
    ### DONE-015-0.0.6 — Consumer override semantics (scalar fields)

    Slice-by-slice scope (per `docs/spec-015-consumer_overrides_scalar-0_0_6.md`):

    - `DjangoType.__init_subclass__` collects `consumer_annotated_scalar_fields`
      parallel to `consumer_annotated_relation_fields`. Annotation-only scalar
      overrides (e.g., `description: int` shadowing an auto-synthesized `str`)
      are added to the unified `consumer_authored_fields` frozenset and skip
      auto-synthesis in `_build_annotations`'s scalar branch via the existing
      `if field.name in consumer_authored_fields: continue` short-circuit.
    - `DjangoTypeDefinition` gains `consumer_annotated_scalar_fields: frozenset[str]`.
    - The previously-skipped `test_consumer_annotation_overrides_synthesized`
      lands as `test_annotation_only_scalar_field_override_wins_over_synthesized`
      in `tests/types/test_definition_order.py` alongside the three relation
      overrides and the assigned-scalar override. The four-corner matrix
      (relation × annotation, relation × assigned, scalar × annotation,
      scalar × assigned) is symmetric and complete.
    - End-to-end test pins the override survives `strawberry.type(...)`
      decoration and shows up in the GraphQL schema with the consumer's type.
    - No new public API. No `Meta.field_overrides = {...}`-style key. Opt-out
      / removal continues to go through `Meta.exclude`. Field description /
      deprecation / default continues to go through the assigned
      `strawberry.field(...)` path that shipped in `0.0.5`.
    - 100% coverage across `tests/types/test_definition_order.py` (the
      override-contract host).

    Design notes carried into `0.0.6`:

    - The four `consumer_*_fields` sets on `DjangoTypeDefinition`
      (`consumer_annotated_relation_fields`, `consumer_assigned_relation_fields`,
      `consumer_annotated_scalar_fields`, `consumer_assigned_scalar_fields`) are
      the introspection surface. The unified `consumer_authored_fields` is the
      single short-circuit input for `_build_annotations`.
    - Resolver / metadata overrides for scalars stay on the assigned
      `strawberry.field(...)` path — the consumer writes
      `description = strawberry.field(resolver=..., description="...", deprecation_reason=...)`
      and `_consumer_assigned_fields` already routes it through the
      `consumer_assigned_scalar_fields` short-circuit.
    - Type-annotation overrides are the consumer's responsibility for runtime
      correctness. `description: int` against a `CharField` will surface a
      Strawberry-side serialization error at query time if the database returns
      a non-integer value; the package does not pre-check annotation/field-type
      compatibility (out of scope for this card).
    ```
  - [ ] `CHANGELOG.md` — `[Unreleased]` entries (**permission granted by this spec**, overriding [`AGENTS.md`](../AGENTS.md)'s default prohibition):
    - `Added`: Annotation-only scalar field overrides on `DjangoType`. Writing `description: int` (or any other class-level scalar annotation that shadows a Django scalar column selected via `Meta.fields`) is now a stable public contract — the consumer's annotation wins over the auto-synthesized one and survives `finalize_django_types()` / `strawberry.type(...)` decoration. Mirrors the annotation-only relation-override path that has shipped since `0.0.4` (`DONE-006-0.0.4`).
    - `Added`: `DjangoTypeDefinition.consumer_annotated_scalar_fields: frozenset[str]` — introspection surface for the new override path; symmetric with the existing `consumer_annotated_relation_fields`, `consumer_assigned_relation_fields`, and `consumer_assigned_scalar_fields` sets.
  - [ ] **Before archiving**, the spec stays at its working location per [`docs/builder/BUILD.md`](builder/BUILD.md) "Specs stay at their working location after closeout". Opt-in archival to `docs/SPECS/` is the maintainer's call; the [Definition of done](#definition-of-done) does not gate on it.

## Problem statement

[`docs/FEATURES.md`](FEATURES.md)'s [`Definition-order independence`](FEATURES.md#definition-order-independence) entry currently closes with the sentence: *"Manual scalar-field override semantics remain an implementation detail until [Scalar field override semantics](#scalar-field-override-semantics) ships."* The `DONE-006-0.0.4` foundation slice pinned the override contract for **relation fields only** — both the annotation-only path (`items: list["AdminItemType"]`) and the assigned-`strawberry.field` path are part of the stable surface and are exercised by the three tests at `tests/types/test_definition_order.py:179`, `:206`, and `:235`.

For scalar fields, the picture is asymmetric. The assigned-`strawberry.field` path landed during the `0.0.5` foundation extension (`tests/types/test_definition_order.py:278`'s `test_assigned_scalar_field_override_keeps_consumer_resolver` — its docstring credits the "Medium fix from `rev-types__base.md`" that widened `_consumer_assigned_fields` to walk every selected Django field rather than only relations). The **annotation-only path** for scalars never got the same treatment: today, writing `description: int` on a `DjangoType` whose `CharField` `description` column is selected via `Meta.fields` lands the consumer's annotation in `cls.__annotations__` at `__init_subclass__` time (the merge at `types/base.py:138` puts `consumer_annotations` last so consumer wins), but the `consumer_authored_fields` set does NOT contain the name, so the synthesized scalar annotation is also computed and written into the same dict (the consumer's `int` lands over the synthesized `str` only because dict-merge order favors the consumer — the path is brittle and not a stable contract).

The previously-skipped `tests/types/test_base.py:444-465`'s `test_consumer_annotation_overrides_synthesized` was the original placeholder for this contract. Its skip reason states *"Strawberry's @strawberry.type decorator regenerates cls.__annotations__ from its own field metadata after our merge in DjangoType.__init_subclass__, so the consumer's class-level scalar annotation loses to the synthesized one."* Under the current code, the merge order at `types/base.py:138` already puts the consumer's annotation last — the skip reason describes a pre-foundation-slice state. The test would likely pass today for the simple pre-finalize case, but the contract is not part of the documented public surface, and the symmetric four-corner override matrix is incomplete.

This card closes the asymmetry by extending the existing `consumer_annotated_relation_fields` collection to a parallel `consumer_annotated_scalar_fields` set, unioning it into `consumer_authored_fields`, and landing the test as the stable proof.

## Current state

`DjangoType.__init_subclass__` (`django_strawberry_framework/types/base.py:75-140`) builds the override-routing state as follows:

```python
# types/base.py:94-108 (current)
consumer_annotations = dict(getattr(cls, "__annotations__", {}))
consumer_annotated_relation_fields = frozenset(
    field.name for field in fields if field.is_relation and field.name in consumer_annotations
)
consumer_assigned_relation_fields, consumer_assigned_scalar_fields = _consumer_assigned_fields(
    cls.__dict__,
    fields,
)
consumer_authored_fields = frozenset(
    {
        *consumer_annotated_relation_fields,
        *consumer_assigned_relation_fields,
        *consumer_assigned_scalar_fields,
    },
)
```

Note the asymmetry: `consumer_annotated_relation_fields` filters on `field.is_relation`, but there is no parallel `consumer_annotated_scalar_fields`. The unified `consumer_authored_fields` therefore covers three of the four override corners but not the fourth (scalar annotation only).

`_build_annotations` (`types/base.py:535-659`) already has the right short-circuit shape — both branches check `if field.name in consumer_authored_fields: continue` (`:621` for relations, `:644` for scalars). Once the fourth corner lands in `consumer_authored_fields`, the scalar branch will skip synthesis for annotation-only-overridden scalars without further code change.

`DjangoTypeDefinition` (`django_strawberry_framework/types/definition.py:14-34`) carries the three existing introspection sets:

```python
# types/definition.py:28-31 (current)
consumer_authored_fields: frozenset[str] = frozenset()
consumer_annotated_relation_fields: frozenset[str] = frozenset()
consumer_assigned_relation_fields: frozenset[str] = frozenset()
consumer_assigned_scalar_fields: frozenset[str] = frozenset()
```

The `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field is the symmetric fourth corner.

`tests/types/test_definition_order.py:179-303` carries the four-corner test cluster as of `0.0.5`:

| Field shape | Override style | Test |
|---|---|---|
| Relation | Annotation-only | `test_annotation_only_relation_override_keeps_generated_resolver` (`:179`) |
| Relation | Assigned `strawberry.field` | `test_assigned_relation_field_override_keeps_consumer_resolver` (`:206`) + decorator variant at `:235` |
| Scalar | Assigned `strawberry.field` | `test_assigned_scalar_field_override_keeps_consumer_resolver` (`:278`) |
| Scalar | Annotation-only | **missing** — currently the skipped test at `tests/types/test_base.py:454-465` |

This card lands the bottom-right cell.

## Goals

- Add `consumer_annotated_scalar_fields` collection in `DjangoType.__init_subclass__`, parallel to the existing `consumer_annotated_relation_fields` collection.
- Add `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field to `DjangoTypeDefinition`.
- Union the new set into `consumer_authored_fields` so the existing scalar-branch short-circuit in `_build_annotations` fires for the new override path.
- Unskip and relocate the existing `test_consumer_annotation_overrides_synthesized` (or replace it with a stricter Slice 1 test cluster on `tests/types/test_definition_order.py`).
- Document the four-corner override contract in `docs/FEATURES.md`'s `Scalar field override semantics` entry, flipping its status to `shipped (0.0.6)`.
- 100% coverage on the new collection path, the new definition field, and the new test cluster.

## Non-goals

- **No new `Meta.field_overrides = {...}` API.** The card's KANBAN entry explicitly lists `Meta.field_overrides` as a *design choice* but the symmetric annotation-only + assigned-`strawberry.field` path is sufficient to close the contract gap. A future card may add a declarative override key if the assigned / annotation routes prove insufficient for some real consumer use case; that lives outside `0.0.6`.
- **No annotation/field-type compatibility pre-check.** Writing `description: int` against a `CharField` is the consumer's responsibility; the package does not assert that the consumer's annotation is type-compatible with the Django column. Runtime serialization errors at query time are the consumer-visible failure mode and are intentional — the package treats consumer overrides as authoritative.
- **No new opt-out / removal API.** The `Meta.exclude` path that shipped in `0.0.1` already covers "drop the field entirely". This card does not add a sentinel-value or `Skip`-typed annotation shape (e.g., `description: None` or `description: strawberry.SKIP`) — the design space is not justified by any pending consumer use case.
- **No new field metadata API.** Description / deprecation / default routing already work via the assigned `strawberry.field(...)` path (`description = strawberry.field(description="...", deprecation_reason="...")` is preserved by `_consumer_assigned_fields`'s scalar branch). This card adds no parallel route through annotation-only syntax.
- **No change to relation overrides.** All four cells of the relation × {annotation, assigned} matrix shipped in `0.0.4` / `0.0.5` and stay unchanged.
- **No change to the post-merge annotation order at `types/base.py:138`.** The line `cls.__annotations__ = {**synthesized, **consumer_annotations}` continues to put consumer last; the only difference is that under this card the synthesized dict no longer contains entries for annotation-only-overridden scalars, so the merge degenerates to "consumer annotation only" for those keys.

## Architectural decisions

### Decision 1 — Annotation-only scalar override collection

Symmetric to the existing relation collection. Replace the single-list comprehension at `types/base.py:95-97` with two comprehensions:

```python
# types/base.py (post-Slice-1)
consumer_annotations = dict(getattr(cls, "__annotations__", {}))
consumer_annotated_relation_fields = frozenset(
    field.name for field in fields if field.is_relation and field.name in consumer_annotations
)
consumer_annotated_scalar_fields = frozenset(
    field.name for field in fields if not field.is_relation and field.name in consumer_annotations
)
```

Both filters walk the same `fields` tuple and read the same `consumer_annotations` dict; the only difference is the `field.is_relation` polarity. The two sets are disjoint by construction.

**Why two filters rather than one walk-and-bucket loop.** The two-comprehension form keeps the code shape symmetric with the existing relation collection one line above. A bucket-loop variant would compress the two lines into a single multi-line for-loop with an if/else inside, which loses the visual symmetry and makes the two override paths look like they are doing different things. They are not — they are the same logic with a polarity flip.

**Why filter on `not field.is_relation` rather than `field.is_relation is False`.** Django's `Field.is_relation` attribute is documented as a bool but is sometimes accessed at type-check time before model loading completes; the `not` form is bool-coercion-safe in a way that the explicit-comparison form is not. The existing `_build_annotations` code at `types/base.py:620` uses `if field.is_relation:` (bool-coercion), so the new filter matches the established convention.

### Decision 2 — `consumer_authored_fields` union shape

The single `consumer_authored_fields` frozenset stays as the only short-circuit input to `_build_annotations`. Extend its construction at `types/base.py:102-108` to include the new set:

```python
# types/base.py (post-Slice-1)
consumer_authored_fields = frozenset(
    {
        *consumer_annotated_relation_fields,
        *consumer_annotated_scalar_fields,   # new
        *consumer_assigned_relation_fields,
        *consumer_assigned_scalar_fields,
    },
)
```

Order inside the set literal does not matter (frozenset is unordered). The line ordering is chosen to keep relations and scalars adjacent — relations first, then scalars, within each (annotated, assigned) pair.

**Why not pass the four sets individually to `_build_annotations`.** The function already only needs the union — it does not distinguish between the four corners. Passing four sets would force `_build_annotations` to recompute the union or to switch on which set the name came from, neither of which it needs to do. The single `consumer_authored_fields` argument stays.

### Decision 3 — `DjangoTypeDefinition.consumer_annotated_scalar_fields` field

Symmetric to the three existing sibling fields. Add to `types/definition.py:28-31`:

```python
# types/definition.py (post-Slice-1)
consumer_authored_fields: frozenset[str] = frozenset()
consumer_annotated_relation_fields: frozenset[str] = frozenset()
consumer_annotated_scalar_fields: frozenset[str] = frozenset()      # new
consumer_assigned_relation_fields: frozenset[str] = frozenset()
consumer_assigned_scalar_fields: frozenset[str] = frozenset()
```

Order chosen to group annotated fields first, then assigned fields, with relation and scalar pairs adjacent within each. (The existing order has the same grouping inconsistency that the spec author resists fixing as part of this card to keep the diff minimal — Worker 1 may choose to also re-order the existing two `consumer_assigned_*` lines for symmetry, or leave them; the spec is neutral on the cosmetic re-order.)

The field is read by tests for introspection (per the Slice 1 test cluster). No production code path consumes it directly — production routes through the unified `consumer_authored_fields`. The four-corner sets exist as the introspection surface and as a tested contract that the package will not silently change the bucketing.

### Decision 4 — `_build_annotations` body stays unchanged

The scalar branch at `types/base.py:643-650` already does the right thing:

```python
# types/base.py:643-650 (unchanged)
else:
    if field.name in consumer_authored_fields:
        # A consumer-assigned ``StrawberryField`` (or annotation) on a
        # scalar column wins over the auto-synthesized annotation so
        # ``strawberry.field(resolver=...)`` overrides survive
        # collection. Relation override symmetry: see the
        # ``field.is_relation`` branch above.
        continue
    if suppress_pk_annotation and field.name == pk_name:
        continue
    annotations[field.name] = convert_scalar(field, cls.__name__)
```

The existing inline comment already mentions "annotation" in parallel with "assigned `StrawberryField`" — the docstring's *intent* covers the annotation-only path. What's been missing is the upstream collection that adds annotation-only scalars to `consumer_authored_fields`. Slice 1 closes that gap with no body edit in `_build_annotations`. Worker 1 may choose to slightly retighten the inline comment for clarity after Slice 1 lands; the spec is neutral on the wording polish.

### Decision 5 — Test placement and the skipped test's fate

The four-corner override matrix lives in `tests/types/test_definition_order.py` (the foundation-slice override-contract host) — three of the four cells are already there at `:179`, `:206`, `:235`, and `:278`. The fourth cell (annotation-only scalar) is the natural sibling and lands as a new test in the same file. The placement keeps the override matrix discoverable in one spot.

The previously-skipped `tests/types/test_base.py:454-465` is then redundant. Two reasonable resolutions:

1. **Delete** the skipped test entirely. The new tests in `test_definition_order.py` cover the contract more thoroughly (pre-finalize + post-finalize + introspection + end-to-end Strawberry schema query). Smaller-touch.
2. **Unskip and keep** as a tiny smoke-test sibling of the larger test cluster. Doesn't add coverage value, but preserves test history.

The spec recommends option (1) — `test_definition_order.py` is the canonical host for the override-contract matrix, and a one-line smoke test sitting alone in `test_base.py` would invite future drift between the two locations. Worker 1 may override during planning if there's a strong reason to keep the test_base.py site.

### Decision 6 — Why `_consumer_assigned_fields` stays the way it is

`_consumer_assigned_fields` at `types/base.py:207-240` walks `cls.__dict__` and buckets assigned `StrawberryField` instances into (relation, scalar) tuples. The function does NOT walk `consumer_annotations` — that's the parallel job of the annotation-collection lines at `:95-97`. Symmetric responsibility split:

- `_consumer_assigned_fields` reads `cls.__dict__` → produces `(consumer_assigned_relation_fields, consumer_assigned_scalar_fields)`.
- The annotation-collection lines read `cls.__annotations__` → produce `(consumer_annotated_relation_fields, consumer_annotated_scalar_fields)`.

The two sources are independent (a consumer can write `description: int` annotation-only, OR `description = strawberry.field(...)` assigned, OR both — the four-corner matrix treats them as separate input channels). `_consumer_assigned_fields` stays unchanged by this card; the new collection is the annotation-side parallel.

## Implementation plan

The slice ordering is **strict** — each slice depends on the previous. The plan deliberately keeps Slice 1 a one-commit change (collection + definition field + tests in `test_definition_order.py`) so the historical staleness in `test_base.py` is cleared in a discrete Slice 2 commit and the doc / KANBAN / CHANGELOG churn lives entirely in Slice 5.

| Slice | Files | Approx. line delta | Tests landed | Notes |
|---|---|---|---|---|
| 1 | `types/base.py`, `types/definition.py`, `tests/types/test_definition_order.py` | +30/-1 | 4 new tests in `test_definition_order.py` | Headline change. |
| 2 | `tests/types/test_base.py` | -22/+0 (delete the skipped test block) or -1/+0 (just the `@pytest.mark.skip` decorator) | None new; existing skipped test resolved | Smaller-touch option is the full delete. |
| 3 | `types/base.py` | +5/-3 (docstring polish in `_consumer_assigned_fields`) | None | Documentation only. |
| 4 | Version-bump quintet | 0 lines if any prior `0.0.6` card already bumped | None | No-op gate. |
| 5 | Docs / KANBAN / CHANGELOG | +50/-10 | None | Largest cosmetic churn; closeout. |

Total expected delta: ~80 lines added across the package and tests; one delete in `tests/types/test_base.py`; one substantial KANBAN body insert in `KANBAN.md`. No new source files. No new test files.

## Edge cases and constraints

- **`Meta.fields = "__all__"` interaction.** When `Meta.fields` is unspecified or `"__all__"`, every concrete Django field is selected. A consumer annotation that shadows any one of them — relation or scalar — lands in `consumer_authored_fields` under this card. The interaction with `Meta.exclude` is unchanged: a name listed in `Meta.exclude` is filtered out of `fields` upstream of the collection, so the `field.name in consumer_annotations` check never sees it. (Worker 1 should verify by reading `_select_fields` at `types/base.py:472`.)
- **`relay.Node` `id` suppression.** `_build_annotations` at `types/base.py:651-657` already short-circuits the synthesized `id: int` annotation when the type implements `relay.Node`. A consumer who writes `id: int` on a Relay-Node-shaped type will now land in `consumer_annotated_scalar_fields` — but the existing pk-suppression branch at `:651-657` continues to suppress synthesis. The merge at `:138` will still place the consumer's `id: int` annotation, which would re-introduce the `NodeIDAnnotationError` that the `relay.Node` suppression exists to prevent. Worker 1 should add a regression test pinning this interaction: a `DjangoType` with `Meta.interfaces = (relay.Node,)` and a consumer `id: int` annotation should still raise `NodeIDAnnotationError` at finalization (consumer takes responsibility for the override; the package does not silently swallow it).
- **Choice-enum fields.** A scalar field with `choices=...` is auto-mapped to a generated Strawberry enum by `convert_scalar` → `convert_choices_to_enum`. A consumer annotation `status: MyEnum` on such a field is, today, technically supported by the merge but never tested. Under this card the annotation lands in `consumer_annotated_scalar_fields` and the enum-generation path is skipped for that name (because `_build_annotations`'s scalar branch short-circuits before calling `convert_scalar`). The cached enum at `registry.get_enum(model, field_name)` is therefore not populated for that field — Worker 1 should add a smoke test pinning that overriding a choice-field annotation does NOT also implicitly register an enum for the field (the consumer's annotation is treated as authoritative).
- **Inheritance.** Inherited consumer annotations on a base `DjangoType` subclass are NOT in the subclass's own `cls.__annotations__` (Python returns only the class's own annotations dict). A subclass that inherits from a base with `description: int` and adds `class Meta: model = Category` will see `cls.__annotations__ = {}` at `__init_subclass__` time and the collection will miss the inherited override. This matches the existing relation-annotation behavior at `:95-97` (also walks `cls.__annotations__`, also misses inherited annotations) — no asymmetry to fix here. Worker 1 should document this in the docstring or `FEATURES.md`'s `Scalar field override semantics` entry for clarity; it is not a bug, it is the same "per-subclass declaration" contract as relations.
- **Mutable-default-argument hazard.** `consumer_authored_fields: frozenset[str] = frozenset()` is the default argument shape in `_build_annotations`'s signature at `types/base.py:541`. `frozenset()` is immutable, so the default is safe. The new `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field on `DjangoTypeDefinition` uses the same pattern (and `DjangoTypeDefinition` is a `@dataclass`, where mutable defaults of mutable types must use `field(default_factory=...)` — but `frozenset()` is immutable, so the bare default is allowed). The spec uses `frozenset()` literals throughout to match the existing siblings.
- **`finalize_django_types()` interaction.** Annotation-only overrides land in `cls.__annotations__` at `__init_subclass__` time (before finalize). `finalize_django_types()` does not re-read `cls.__annotations__` for the override-routing decision — it only resolves pending relations and decorates with `strawberry.type(...)`. The Strawberry decorator reads `cls.__annotations__` to build `__strawberry_definition__.fields`; under this card the consumer's annotation is what's in the dict, so the resulting Strawberry field type matches the consumer's override. This is the end-to-end contract that the Slice 1 `test_annotation_only_scalar_override_survives_strawberry_finalization` test pins.

## Test strategy

All new tests land in `tests/types/test_definition_order.py` — the existing host for the override-contract matrix (per [Decision 5](#decision-5--test-placement-and-the-skipped-tests-fate)).

The four new tests in Slice 1 — `test_annotation_only_scalar_field_override_wins_over_synthesized`, `test_annotation_only_scalar_override_populates_definition_metadata`, `test_annotation_only_scalar_override_does_not_emit_synthesized_annotation`, `test_annotation_only_scalar_override_survives_strawberry_finalization` — cover:

- **Pre-finalize annotation contents.** Assert `cls.__annotations__[field_name]` is the consumer's type immediately after `__init_subclass__`.
- **`consumer_*_fields` introspection.** Assert the new `consumer_annotated_scalar_fields` set on `DjangoTypeDefinition` contains exactly the overridden name, that `consumer_authored_fields` contains it (transitively, via the union), and that `consumer_assigned_scalar_fields` does NOT (because the override is annotation-only).
- **`_build_annotations` skip.** Assert the synthesized annotations dict — the first element of `_build_annotations`'s return tuple — does NOT contain the override-field key. Whitebox-but-stable: the synthesized dict is what feeds the post-merge line at `types/base.py:138`, so its shape is the contract under test.
- **End-to-end Strawberry schema.** Build a `strawberry.Schema(query=Query)` with a query field returning the type, execute an introspection query, and assert the Strawberry field type for the overridden field matches the consumer's annotation.

The Slice 1 cluster does NOT include the four edge-case interactions listed in [Edge cases and constraints](#edge-cases-and-constraints) — those are Worker 1's planning surface to either fold into the Slice 1 cluster or land in a Slice 1a addendum. The mandatory baseline is the four tests above.

Slice 2 has no new tests — it deletes (or unskips) one existing test. The full-suite pass on Slice 2 is the only test-side contract.

Slices 3 / 4 / 5 are documentation-only and have no test deltas. Coverage stays at 100% because the new definition field is exercised by Slice 1 tests, and the new collection branch in `__init_subclass__` is exercised by every override test in `tests/types/test_definition_order.py` (the scalar-annotation-only branch is new but the bucket-walking pattern is the same).

## Definition of done

- [ ] Every Slice 1 / Slice 2 / Slice 3 checkbox in [Slice checklist](#slice-checklist) is checked.
- [ ] `tests/types/test_base.py:454-465` (`test_consumer_annotation_overrides_synthesized`) is either deleted or unskipped per [Decision 5](#decision-5--test-placement-and-the-skipped-tests-fate); no `@pytest.mark.skip` block referencing "Deferred scalar-field override behavior" remains.
- [ ] `uv run pytest` passes locally with 100% package coverage.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format --check .` passes.
- [ ] `git diff --check` passes.
- [ ] `docs/FEATURES.md`'s `Scalar field override semantics` entry reads `shipped (0.0.6)` (Slice 5).
- [ ] `KANBAN.md` shows `DONE-015-0.0.6` with the verbatim body from Slice 5 above; `WIP-ALPHA-015-0.0.6` is no longer present.
- [ ] `CHANGELOG.md` `[Unreleased]` carries the two `Added` entries from Slice 5.
- [ ] Slice 4 version-bump quintet is verified by `grep` rather than blind edits — every checkbox is a no-op if `spec-013-deferred_scalars-0_0_6.md` or `spec-014-meta_primary-0_0_6.md` already landed the bump.
- [ ] No new public top-level symbol; no new `Meta.*` key; `django_strawberry_framework/__init__.py.__all__` is unchanged.
