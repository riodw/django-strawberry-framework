# Spec: Upload scalar and file / image field mapping — `FileField` / `ImageField` output objects, mutation `Upload` inputs, and the final `0.0.11` cut

Planned for `0.0.11` (card [`TODO-ALPHA-037-0.0.11`][kanban]). This card
completes the package's file/image story across both directions of the wire
contract: on the **read** side it replaces the placeholder `FileField` /
`ImageField` → `str` mapping (the earliest [`spec-001`][spec-001] "URL/path
string" simplification) with structured
[`DjangoFileType`][glossary-djangofiletype] /
[`DjangoImageType`][glossary-djangoimagetype] output objects (`name` / `path` /
`size` / `url`, plus `width` / `height` for images); on the **write** side it
plugs Strawberry's [`Upload` scalar][glossary-upload-scalar] into the
[auto-generated mutation `Input` types][glossary-input-type-generation] that
[`DONE-036-0.0.11`][kanban] ([`spec-036`][spec-036]) built — turning the
staged-seam `NotImplementedError` that card left at
[`mutations/inputs.py`][mutations-inputs] #"Upload staged seam
(TODO-ALPHA-037-0.0.11)" into a real `Upload`-typed input field. It is a
Required [`strawberry-graphql-django`][upstream-field-types] parity item (the
card's own 🍓 Required tag): upstream's `field_type_map` maps `files.FileField` →
`DjangoFileType`, `files.ImageField` → `DjangoImageType`, and both → `Upload` in
`input_field_type_map`, and without this every consumer touching user uploads
hand-rolls the mapping. The scalar registration reuses the shipped
[`BigInt`][glossary-bigint-scalar] /
[`strawberry_config`][glossary-strawberry-config] path verbatim — `Upload` is a
`NewType("Upload", bytes)` + a `ScalarDefinition`, structurally identical to
`BigInt`. **Version boundary** (see
[Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)): unlike
[`spec-036`][spec-036] (which shared its patch line with an unstarted sibling
and so deferred), this card is the **last** `0.0.11` card — `036` is already
`DONE` and 037 is the lone `## In progress` entry on `0.0.11` — so the
`pyproject.toml` / `__version__` /
[`tests/base/test_init.py::test_version`][test-base-init] bump that `036`
deferred to the joint cut **lands here**.

Status: **DRAFT** — authored for `TODO-ALPHA-037-0.0.11` via the
[`docs/SPECS/NEXT.md`][next] flow; implementation not yet started. Slices: Slice
1 (**read-side output objects** — `DjangoFileType` / `DjangoImageType`, the two
`SCALAR_MAP` rows, and the empty-file resolver guard;
[Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)
/
[Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)),
Slice 2 (**write-side `Upload` input** — the `Upload` scalar registration in
[`scalars.py`][scalars] and the [`mutations/inputs.py`][mutations-inputs]
seam-to-`Upload` swap plus the write-resolver file assignment;
[Decision 5](#decision-5--upload-scalar-registration-mirrors-the-bigint-precedent)
/
[Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)),
Slice 3 (**public exports + coverage hardening** — `Upload` / `DjangoFileType` /
`DjangoImageType` re-exported and pinned, plus the synthetic-model
read/write/storage-failure tests;
[Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols) /
[Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)),
and Slice 4 (**docs + the `0.0.11` version cut + card wrap**; the per-card
[`CHANGELOG.md`][changelog] edit must be named explicitly in the Slice 4
maintainer prompt — this spec describes the edit but cannot grant the permission
[`AGENTS.md`][agents] reserves for an explicit instruction). The card's hard
dependency is satisfied: [`DONE-036-0.0.11`][kanban] (the mutation foundation
whose input generator this card extends, leaving the `Upload` seam this card
consumes) has shipped.

Owner: package maintainer.

Predecessors: [`spec-036-mutations-0_0_11.md`][spec-036] (the sibling `0.0.11`
mutations card this card plugs into — its [Decision 6][spec-036] left "a thin
input-converter seam … so 037 plugs `Upload` in without re-opening the
generator", realized as the [`mutations/inputs.py`][mutations-inputs]
`NotImplementedError` this card replaces; the most-recently-authored spec and
the canonical voice / depth / section-layout reference);
[`spec-025-scalar_map_helper-0_0_7.md`][spec-025] (the
[`strawberry_config`][glossary-strawberry-config] / `_PACKAGE_SCALAR_MAP`
registration path `Upload` rides — its Decision 3 redefined `BigInt` as a bare
`NewType` + `ScalarDefinition`, the exact shape `Upload` already has upstream);
[`spec-017-deferred_scalars-0_0_6.md`][spec-017] (the converter-table-addition
precedent — it added `BigInt` / `JSON` / `ArrayField` / `HStoreField` to
[`SCALAR_MAP`][types-converters], the same table this card extends, and
pioneered the synthetic-model test strategy);
[`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026] (the
scalar-conversion coverage posture); and
[`spec-001-django_types-0_0_1.md`][spec-001] (the original `FileField` /
`ImageField` read-side `str` mapping this card replaces).
[`docs/GLOSSARY.md`][glossary] carries
[`Upload` scalar][glossary-upload-scalar],
[`DjangoFileType`][glossary-djangofiletype], and
[`DjangoImageType`][glossary-djangoimagetype] as `planned for 0.0.11`; Slice 4
promotes all three to `shipped (0.0.11)`, rewrites the
[Scalar field conversion][glossary-scalar-field-conversion] /
[Specialized scalar conversions][glossary-specialized-scalar-conversions]
file/image rows, and moves the package-version line to `0.0.11`.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the
  [`TODO-ALPHA-037-0.0.11`][kanban] card body via the
  [`docs/SPECS/NEXT.md`][next] flow (2026-06-19). Pinned: the canonical
  structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the
  card-scope boundary as a file/image conversion card, not a multipart-transport
  or storage-abstraction card
  ([Decision 2](#decision-2--card-scope-boundary-fileimage-conversion-only-not-transport-or-storage-abstraction));
  the `DjangoFileType` / `DjangoImageType` output shapes mirroring
  [`strawberry-graphql-django`][upstream-field-types] with an empty-file
  resolver guard
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream));
  **storage-safe nullable subfields** (`path` / `size` / `url` / `width` /
  `height` nullable; `name` non-null) so a non-filesystem backend or a vanished
  file degrades to `null` rather than a GraphQL 500, and the `blank`-or-`null`
  object nullability
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability));
  the `Upload` scalar registration as a one-entry `_PACKAGE_SCALAR_MAP`
  extension mirroring [`BigInt`][glossary-bigint-scalar]
  ([Decision 5](#decision-5--upload-scalar-registration-mirrors-the-bigint-precedent));
  the write-side seam-to-`Upload` swap and the write-resolver file assignment,
  lifting the `036` file-column merge-override exception
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload));
  the three net-new root-exported public symbols
  ([Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols));
  no new `DjangoType` `Meta` key or settings key
  ([Decision 8](#decision-8--no-new-meta-key-no-new-setting-no-dynamic-storage-policy));
  the synthetic-model test strategy with live coverage only where a real
  fakeshop path exists
  ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models));
  and **this card owning the final `0.0.11` version bump**
  ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).
  Three card-body conflicts are carried into
  [Risks and open questions](#risks-and-open-questions) rather than silently
  reconciled (the stale `"Pairs with 028"` note, the stale
  `mutations/ (planned)` predicted-file annotation, and the stale
  `TODO-ALPHA-035-0.0.11` reference in the [`scalars.py`][scalars] docstring),
  each with a preferred reading.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [`Upload` scalar][glossary-upload-scalar] — the write-side subject. The
  glossary pins its planned contract: a Strawberry `Upload` scalar mapping for
  `FileField` / `ImageField` on mutation inputs, paired with
  [`DjangoFileType`][glossary-djangofiletype] /
  [`DjangoImageType`][glossary-djangoimagetype] on the output side. This card
  ships exactly that; the entry is promoted from `planned for 0.0.11` to
  `shipped (0.0.11)` in Slice 4.
- [`DjangoFileType`][glossary-djangofiletype] /
  [`DjangoImageType`][glossary-djangoimagetype] — the read-side subjects.
  `DjangoFileType` carries `name` / `path` / `size` / `url`; `DjangoImageType`
  adds image dimensions where Pillow is available.
  [Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)
  /
  [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)
  realize both.
- [Scalar field conversion][glossary-scalar-field-conversion] /
  [Specialized scalar conversions][glossary-specialized-scalar-conversions] —
  the converter table this card extends. Today both list `FileField` /
  `ImageField` → `str` (string path / URL); this card rewrites those two rows to
  the structured output objects and documents the
  [breaking wire-format change][glossary-specialized-scalar-conversions]
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)).
- [`BigInt` scalar][glossary-bigint-scalar] /
  [`strawberry_config`][glossary-strawberry-config] — the scalar-registration
  precedent and path. `Upload` registers exactly as `BigInt` does: a package
  scalar added to `_PACKAGE_SCALAR_MAP` and bound through the
  [`strawberry_config`][glossary-strawberry-config] factory
  ([Decision 5](#decision-5--upload-scalar-registration-mirrors-the-bigint-precedent)).
  The glossary's `strawberry_config` entry already anticipates `Upload` landing
  here.
- [`DjangoMutation`][glossary-djangomutation] /
  [Input type generation][glossary-input-type-generation] /
  [`DjangoMutationField`][glossary-djangomutationfield] /
  [`FieldError` envelope][glossary-fielderror-envelope] — the shipped
  [`spec-036`][spec-036] write side this card extends; the input generator
  already produces `<Model>Input` / `<Model>PartialInput`, and this card teaches
  it to map a file/image column to `Upload` instead of failing loud
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).
- [Scalar field override semantics][glossary-scalar-field-override-semantics] /
  [`auto`-typed annotations][glossary-auto-typed-annotations] — the consumer
  opt-out. A consumer who wants the legacy `str` (URL) read shape keeps it with
  a concrete annotation override (`avatar: str`), which bypasses
  `convert_scalar`; the override contract is unchanged
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)).
- [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]
  / [`DjangoType`][glossary-djangotype] / [`Meta.model`][glossary-metamodel] —
  the type-system surface the conversions ride; a file column is selected /
  excluded by the same `Meta.fields` / `Meta.exclude` rules as any column, and
  the input generator narrows by the mutation's own `Meta.fields` /
  `Meta.exclude` ([`spec-036`][spec-036] Decision 6).
- [`Meta.nullable_overrides`][glossary-metanullable-overrides] /
  [`Meta.required_overrides`][glossary-metarequired-overrides] — the existing
  `force_nullable` tri-state in [`convert_scalar`][types-converters] that this
  card's `blank`-aware file nullability composes with
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
- [`ConfigurationError`][glossary-configurationerror] — the validation exception
  the read path keeps raising for an unsupported field; the file/image branch
  makes `FileField` / `ImageField` supported on both read and write, so a
  previously-`NotImplementedError`-raising write input over a file column now
  generates a valid `Upload` field.
- [`DjangoFormMutation`][glossary-djangoformmutation] /
  [`SerializerMutation`][glossary-serializermutation] — the downstream `0.0.12`
  / `0.0.13` flavor cards that inherit the `Upload` input mapping for free,
  because they reuse the same
  [Input type generation][glossary-input-type-generation] and
  [`FieldError` envelope][glossary-fielderror-envelope] this card extends.
- [`TestClient`][glossary-testclient] — the `0.0.14` multipart test-client card
  that *depends on* this card: it must send multipart requests once `Upload`
  exists. The dependency is one-directional — this card ships the scalar, that
  card ships the transport helper ([Non-goals](#non-goals)).
- [relation handling][glossary-relation-handling] /
  [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — context for
  why a file column is a **scalar** column, not a relation: it carries no FK and
  needs no optimizer planning; the read resolver is a thin scalar-column
  wrapper, not a relation resolver.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package-internal converter /
  scalar / input mechanics under [`tests/types/`][test-types] /
  [`tests/`][test-scalars] / [`tests/mutations/`][test-mutations] mirroring
  source; live consumer behavior over `/graphql/` only when a realistic request
  reaches it —
  [Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models));
  the settings-keys-only-when-needed rule (this card adds no settings key); the
  no-pytest-after-edits rule; the CHANGELOG-edit-permission rule at
  [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly
  instructed" — Slice 4's release-note edit must be named in its maintainer
  prompt.
- [`START.md`][start] — the "behaviorally we copy `strawberry-graphql-django`'s
  good ideas, surface-wise we copy `django-graphene-filters`" rule (this card
  borrows upstream's file/image output shapes and `Upload` mapping at the
  *outcome* level); the "do both libraries provide it? → foundational" test; and
  the reference-style markdown link convention (defs at the bottom under the 10
  canonical group headers).
- [`CONTRIBUTING.md`][contributing] — the 100% coverage target
  (`fail_under = 100`); every converter branch, the read resolver's empty-file /
  storage-failure guard, the `Upload` registration, and the write-input mapping
  earn coverage in the package test trees.
- [`docs/TREE.md`][tree] — the conversion-table rows the package documents; this
  card touches [`types/converters.py`][types-converters] (read),
  [`scalars.py`][scalars] (the `Upload` scalar), and
  [`mutations/inputs.py`][mutations-inputs] (write) and adds no module outside
  the existing trees.
- [`GOAL.md`][goal] — success-criterion 6 ("Write mutations declaratively … plus
  `Upload` scalar for `FileField` / `ImageField`") names the `Upload` scalar
  explicitly; this card satisfies the upload half of that criterion.

## Slice checklist

Each top-level item maps to one commit / PR. **Four slices: read output objects
(Slice 1), write `Upload` input (Slice 2), exports + coverage (Slice 3), docs +
the `0.0.11` cut (Slice 4).** Slices 1–2 are independent (read vs write modules)
and can land in either order; Slice 3 depends on both; Slice 4 is doc +
version-cut only.

- [ ] Slice 1: read-side output objects + the `SCALAR_MAP` change + the
  empty-file resolver (per
  [Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)
  /
  [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability))
  - [ ] [`types/converters.py`][types-converters]: define `DjangoFileType`
    (`@strawberry.type` with `name: str`, `path: str | None`,
    `size: int | None`, `url: str | None`) and `DjangoImageType(DjangoFileType)`
    (adds `width: int | None`, `height: int | None`); rewrite the two
    [`SCALAR_MAP`][types-converters] rows `FileField: str` → `DjangoFileType`
    and `ImageField: str` → `DjangoImageType`. The MRO walk keeps an
    `ImageField` (a `FileField` subclass) resolving to `DjangoImageType` because
    its own row precedes the `FileField` row.
  - [ ] [`types/base.py`][types-base] / [`types/resolvers.py`][types-resolvers]:
    a generated **file-column read resolver** for any column resolving to
    `DjangoFileType` / `DjangoImageType` — returns `None` for an empty / falsy
    `FieldFile` (`not value`) and otherwise the bound `FieldFile`, whose `name`
    / `path` / `size` / `url` (and `width` / `height` for images) Strawberry
    reads, with a **narrow per-subfield exception guard** (`ValueError` /
    `OSError` / storage `NotImplementedError` → `None`) so a non-filesystem
    `path` or a vanished file degrades to a `null` subfield, not a 500; the
    standing consumer-override short-circuit
    ([Scalar field override semantics][glossary-scalar-field-override-semantics])
    is preserved.
  - [ ] Output object nullability: a file column widens to
    `DjangoFileType | None` when the column is `null=True` **or** `blank=True`
    (an absent file is representable for a blank column), composing with the
    [`Meta.nullable_overrides`][glossary-metanullable-overrides] /
    [`Meta.required_overrides`][glossary-metarequired-overrides]
    `force_nullable` tri-state.
  - [ ] Package coverage: [`tests/types/test_converters.py`][test-types] (the
    card's named test file) — `FileField` → `DjangoFileType`, `ImageField` →
    `DjangoImageType`, MRO precedence, `blank` / `null` → `| None`,
    `force_nullable` compose; [`tests/types/test_resolvers.py`][test-types] —
    the empty-file → `None` guard, the populated-`FieldFile` pass-through
    (subfields resolve), and a storage-property failure degrading to a `null`
    subfield; [`tests/types/test_base.py`][test-types] — the consumer-annotation
    override (`avatar: str`) still wins.
- [ ] Slice 2: write-side `Upload` input + the scalar registration (per
  [Decision 5](#decision-5--upload-scalar-registration-mirrors-the-bigint-precedent)
  /
  [Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload))
  - [ ] [`scalars.py`][scalars]: re-export `Upload` and its `UploadDefinition`
    from `strawberry.file_uploads.scalars`, and add `Upload: UploadDefinition`
    to `_PACKAGE_SCALAR_MAP` so the
    [`strawberry_config`][glossary-strawberry-config] factory binds it — the
    one-entry extension of the [`BigInt`][glossary-bigint-scalar] precedent; fix
    the stale `TODO-ALPHA-035-0.0.11` reference in the module docstring to
    `TODO-ALPHA-037-0.0.11`.
  - [ ] [`mutations/inputs.py`][mutations-inputs]: remove the staged seam at
    #"Upload staged seam (TODO-ALPHA-037-0.0.11)" — a `FileField` / `ImageField`
    input field now maps to `Upload`, required per the shipped per-field rule (a
    `blank=False` / `null=False` / no-default file column is required in the
    create `<Model>Input`, optional otherwise and in `<Model>PartialInput`),
    widened to `Upload | None` on `blank` / `null`. The Python attribute is the
    model field name (`attachment`, not `attachment_id` — file columns are
    scalar, not relation, inputs). The `036` file-column merge-override
    exception (the `NotImplementedError` preceding the override skip) is lifted:
    file columns now participate in the
    [`Meta.input_class`][glossary-input-type-generation] merge override like any
    scalar.
  - [ ] [`mutations/resolvers.py`][mutations-resolvers]: the write pipeline
    assigns a provided `Upload` value to the model's file field before
    `full_clean()` / `save()` — a provided `UNSET` leaves the file unchanged on
    partial update; clearing via explicit `null` is governed by the shipped
    pipeline's nullable-scalar handling and is a
    [Risks](#risks-and-open-questions) item, not promised here.
  - [ ] Package coverage: [`tests/test_scalars.py`][test-scalars] — `Upload` is
    registered in `strawberry_config()`'s scalar map and resolves, and an
    `extra_scalar_map={Upload: ...}` collision raises the existing `ValueError`;
    [`tests/mutations/test_inputs.py`][test-mutations] — replace the
    staged-`NotImplementedError` tests with positive `FileField` / `ImageField`
    → `Upload` required/optional shapes, `| None` widening, and the lifted CR-6
    override; [`tests/mutations/test_resolvers.py`][test-mutations] — file
    assignment on create / partial update.
- [ ] Slice 3: public exports + coverage hardening (per
  [Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols)
  /
  [Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models))
  - [ ] [`__init__.py`][init]: re-export `Upload` (from [`scalars.py`][scalars])
    and `DjangoFileType` / `DjangoImageType` (from
    [`types/converters.py`][types-converters]); add all three to `__all__`.
  - [ ] Package coverage: [`tests/base/test_init.py`][test-base-init] — the
    public-export and `__all__` assertions add the three symbols (`test_version`
    moves to `0.0.11` in Slice 4,
    [Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).
    Storage-failure / null-blank / image-dimension edge tests harden the
    synthetic-model coverage.
- [ ] Slice 4: docs + the `0.0.11` version cut + card wrap (per
  [Doc updates](#doc-updates) /
  [Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump))
  - [ ] **Version files to `0.0.11`**
    ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)):
    [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init],
    [`tests/base/test_init.py::test_version`][test-base-init], the
    [`docs/GLOSSARY.md`][glossary] package-version line, and `uv.lock` if it
    carries the package version.
  - [ ] [`docs/GLOSSARY.md`][glossary] (promote
    [`Upload` scalar][glossary-upload-scalar] /
    [`DjangoFileType`][glossary-djangofiletype] /
    [`DjangoImageType`][glossary-djangoimagetype] to `shipped (0.0.11)`; rewrite
    the [Scalar field conversion][glossary-scalar-field-conversion] /
    [Specialized scalar conversions][glossary-specialized-scalar-conversions]
    file/image rows; add the three to **Public exports** + the **Index** + the
    **File / image uploads** browse-by-category row; record the read-side
    breaking-wire-format change; flip the
    [`strawberry_config`][glossary-strawberry-config] entry's "next: `Upload`"
    to "`BigInt` + `Upload`"), [`docs/README.md`][docs-readme] /
    [`README.md`][readme] (move the `Upload` scalar + file/image mapping from
    "Coming next (`0.0.11`)" to "Shipped today", and the README **Status** line
    from `0.0.10` to `0.0.11`), [`GOAL.md`][goal] (success-criterion 6's
    `Upload` reference now ships), [`TODAY.md`][today] (rewrite the
    scalar-conversion table's `FileField` / `ImageField` → `str` row to the
    structured output objects and note upload mutation inputs as a package
    capability not exercised by products), [`CHANGELOG.md`][changelog] (only if
    the Slice 4 maintainer prompt explicitly requests it), [`KANBAN.md`][kanban]
    (card → Done via the kanban DB + re-render).

## Problem statement

`django-strawberry-framework` treats file/image columns asymmetrically and
incompletely:

- On the **read side**, [`types/converters.py`][types-converters] maps
  `models.FileField` and `models.ImageField` to `str`, preserving the earliest
  [`spec-001`][spec-001] "URL/path string" simplification. A `str`-typed file
  field serializes to the file's name (`str(FieldFile)`), discarding the `url` a
  client needs to fetch the file, the `size`, the storage `path`, and — for
  images — the dimensions. [`strawberry-graphql-django`][upstream-field-types]
  returns a `DjangoFileType` / `DjangoImageType` so the client gets the whole
  picture in one selection; a consumer migrating from upstream and selecting
  `{ avatar { url width } }` hits a schema error against this package today.
- On the **write side**, [`mutations/inputs.py`][mutations-inputs] deliberately
  rejects `FileField` / `ImageField` before scalar conversion (a
  `NotImplementedError` naming this card). That was the correct
  [`spec-036`][spec-036] staged seam — silently inheriting the read-side `str`
  mapping would have created a wrong mutation contract — but after
  [`DjangoMutation`][glossary-djangomutation] shipped, the seam is now the
  blocker: any model with an editable file/image column cannot use generated
  mutation inputs unless the consumer excludes the column.
- The schema-config helper already has the right shape.
  [`strawberry_config`][glossary-strawberry-config] registers
  [`BigInt`][glossary-bigint-scalar]; Strawberry's `Upload` is a scalar
  definition of the same `NewType` + `ScalarDefinition` shape and should join
  the same `_PACKAGE_SCALAR_MAP` path, not a new settings or decorator path.

The card matters because upload fields are ordinary Django model fields. A
package that claims DRF-shaped model-to-GraphQL generation cannot require every
user-upload model to hand-roll both output object fields and mutation input
scalars. This is a Required `strawberry-graphql-django` parity item,
foundational by the [`START.md`][start] "do both libraries provide it?" test
(both upstreams map file/image fields).

## Current state

A true description of the repo as this spec is authored:

- **`FileField` / `ImageField` → `str` on read.**
  [`types/converters.py`][types-converters] #"models.FileField: str" maps both
  to `str` in [`SCALAR_MAP`][types-converters];
  [`convert_scalar`][types-converters] resolves them through the shared
  `scalar_for_field` MRO walk and widens to `str | None` on `field.null` (or a
  `Meta.nullable_overrides` / `Meta.required_overrides` `force_nullable`
  tri-state). There is **no** `DjangoFileType` / `DjangoImageType` symbol and no
  file-column read resolver — a file column rides Strawberry's default attribute
  resolver and serializes via `str(FieldFile)`.
- **The write generator refuses file columns.**
  [`mutations/inputs.py`][mutations-inputs] #"Upload staged seam
  (TODO-ALPHA-037-0.0.11)" raises `NotImplementedError` for a `FileField` /
  `ImageField`, with a `TODO(spec-036 Slice 1)` comment naming this card;
  [`tests/mutations/test_inputs.py`][test-mutations] pins that fail-loud
  behavior. The `036` review (CR-6) pinned that file columns are "the one
  exception to the merge override" precisely because this `NotImplementedError`
  precedes the `Meta.input_class` override skip — an exception this card lifts.
- **`Upload` is not registered.** [`scalars.py`][scalars] holds `BigInt` (a
  `NewType("BigInt", int)` + a `ScalarDefinition`) and
  `_PACKAGE_SCALAR_MAP = {BigInt: _BIGINT_SCALAR_DEFINITION}`; `Upload` is
  absent. Strawberry ships `Upload = NewType("Upload", bytes)` +
  `UploadDefinition` at `strawberry.file_uploads.scalars` — structurally
  identical to `BigInt`, so it is a one-line `_PACKAGE_SCALAR_MAP` addition. The
  module docstring's "Future scalars (e.g. `Upload` per TODO-ALPHA-035-0.0.11)"
  carries a **stale card number** (`035` is the optimizer-hardening card; the
  real owner is this card, `037`).
- **The version line still reads `0.0.10`.** [`__init__.py`][init] exports the
  `0.0.11` mutation symbols but reports `__version__ = "0.0.10"`;
  [`pyproject.toml`][pyproject] and
  [`tests/base/test_init.py::test_version`][test-base-init] are also `0.0.10`,
  and [`docs/GLOSSARY.md`][glossary]'s package-version line is `0.0.10` while
  `DjangoMutation` is already `shipped (0.0.11)` — the joint cut
  [`spec-036`][spec-036] deferred has not landed
  ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).
- **The mutation subpackage exists.** The card's "Predicted files" annotates
  `django_strawberry_framework/mutations/ (planned)`, but `mutations/` shipped
  with [`DONE-036-0.0.11`][kanban]; [`mutations/inputs.py`][mutations-inputs] /
  [`mutations/resolvers.py`][mutations-resolvers] are on disk. The annotation is
  stale ([Risks](#risks-and-open-questions)).
- **No example app uses a file/image column.**
  `grep -rln "FileField\|ImageField" examples/` returns nothing — `products` /
  `library` / `scalars` carry no file column, so the read-side break invalidates
  no in-repo schema and the card's "synthetic-model tests" scoping is sufficient
  for coverage
  ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).

## Goals

1. **Expose file/image output as structured objects.**
   [`SCALAR_MAP`][types-converters] returns
   [`DjangoFileType`][glossary-djangofiletype] /
   [`DjangoImageType`][glossary-djangoimagetype] (mirroring
   [`strawberry-graphql-django`][upstream-field-types]) so a client gets `name`
   / `path` / `size` / `url` (+ `width` / `height`) in one selection
   ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)).
2. **Handle empty / unreadable files deliberately.** An absent file resolves to
   `null` (the whole object); a storage property that cannot be produced
   degrades to a `null` subfield — never a `FieldFile.url` / `.path` exception
   surfacing as a GraphQL 500
   ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
3. **Register `Upload` through the package config factory.** `Upload` lands in
   `_PACKAGE_SCALAR_MAP` and binds via
   [`strawberry_config`][glossary-strawberry-config], the same path
   [`BigInt`][glossary-bigint-scalar] uses
   ([Decision 5](#decision-5--upload-scalar-registration-mirrors-the-bigint-precedent)).
4. **Map `FileField` / `ImageField` to `Upload` on the mutation input side.**
   The [`spec-036`][spec-036] staged seam becomes a real `Upload`-typed input
   field, required per the shipped per-field rule, and the write resolver
   assigns the uploaded file
   ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).
5. **Keep read and write contracts distinct.** Output is an object type; input
   is `Upload`; neither side leaks the other's representation.
6. **Export `Upload` / `DjangoFileType` / `DjangoImageType` from the package
   root**
   ([Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols)).
7. **Complete the `0.0.11` cut.** Since `037` is the only active WIP card on
   `0.0.11` and `036` deferred the bump, Slice 4 owns the version-file alignment
   ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).

## Non-goals

- **Multipart test-client helper.** The future
  [`TestClient`][glossary-testclient] card (`0.0.14`) references
  `TODO-ALPHA-037` because it must send multipart requests once `Upload` exists;
  the helper itself is `0.0.14`, not this card
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **A new fakeshop upload domain.** This card does not add a fake image/product
  app or unrelated model just to force live HTTP coverage; if a real file/image
  field is later added to fakeshop, it earns live coverage then
  ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).
- **Nested writes / file-replacement policy beyond the direct field.** This card
  maps the scalar and lets the shipped mutation pipeline assign Django's
  uploaded file object to the model field; complex replace/delete semantics
  beyond "provided value sets the field, omitted value leaves it alone on
  partial update" stay out
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Storage abstraction / signed URLs / image processing.** The package does not
  wrap every Django storage backend; it exposes safe nullable subfields where
  storage properties may be unavailable and lets Django's storage object answer
  `url` / `path` / `size` ([Edge cases](#edge-cases-and-constraints)).
- **`DurationField` / `BinaryField` and other unmapped scalars.** They remain
  intentionally absent from [`SCALAR_MAP`][types-converters] with their
  documented custom-scalar plugs.
- **A new `DjangoType` `Meta` key or settings key**
  ([Decision 8](#decision-8--no-new-meta-key-no-new-setting-no-dynamic-storage-policy)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it? → foundational" test,
file/image mapping is **Required `strawberry-graphql-django` parity** (the
card's own 🍓 Required tag) and `graphene-django` provides a weaker form. The
borrowing splits along the package's standing line — *behaviorally* copy
`strawberry-graphql-django`'s output shapes and `Upload` mapping; *surface-wise*
keep the package's automatic `class Meta`-driven conversion (the consumer
declares no decorator and no upload helper — a file column is converted by the
same `Meta.fields` / `Meta.exclude` selection as any column). `graphene-django`
maps `FileField` to a `String` output (matching this package's original
`spec-001` simplification, but not the card's target); we follow the richer
Strawberry output object because the engine is Strawberry.

### Reference-package parity checkpoint

| Upstream | `django-strawberry-framework` | Status |
| --- | --- | --- |
| [`strawberry_django.fields.types.DjangoFileType`][upstream-field-types] (`name` / `path` / `size` / `url`) | [`DjangoFileType`][glossary-djangofiletype] public output type; `models.FileField` converter row ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)) | this card — required parity |
| [`strawberry_django.fields.types.DjangoImageType`][upstream-field-types] (file fields + dimensions) | [`DjangoImageType`][glossary-djangoimagetype] public output type; `models.ImageField` converter row ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)) | this card — required parity (subfields widened nullable, [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)) |
| [`strawberry_django` `input_field_type_map` maps file/image → `Upload`][upstream-field-types] | the [`mutations/inputs.py`][mutations-inputs] generator maps both to [`Upload`][glossary-upload-scalar] ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)) | this card — required parity |
| `strawberry.file_uploads.scalars.Upload` | re-exported and registered in `_PACKAGE_SCALAR_MAP` via [`strawberry_config`][glossary-strawberry-config] ([Decision 5](#decision-5--upload-scalar-registration-mirrors-the-bigint-precedent)) | this card — adopt upstream scalar, register through the package path |
| `graphene_django.converter.convert_field_to_string` for `FileField` | rejected as too weak for this package's Strawberry output shape | deliberately not borrowed |

### From `strawberry-graphql-django` — borrow the output shapes and the input mapping

- **Output types.** `DjangoFileType` (`name` / `path` / `size` / `url`) and
  `DjangoImageType(DjangoFileType)` (+ `width` / `height`) — adopted
  field-for-field, so a migrating consumer's `{ avatar { url width } }`
  selection ports unchanged. The one deliberate divergence is subfield
  nullability
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
- **Input mapping.** `FileField` / `ImageField` → `Upload` on the mutation input
  — adopted; the empty-file / partial-update write semantics are the package's
  own
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).

### From `graphene-django` / DRF — borrow the user-facing shape

- **Automatic, `Meta`-driven conversion.** No `Upload` helper, no decorator, no
  per-field declaration — a file column is converted because it is in the type's
  `Meta.fields` selection, exactly as every other column.
- **Editable / `blank` / `null` / `default` metadata** drives whether an upload
  input is required (the DRF `required=False`-from-metadata rule the shipped
  generator already uses).

### Explicitly do not borrow

- **A single flagged file type with an `is_image` runtime check.** Rejected: two
  distinct types (`DjangoFileType` / `DjangoImageType`) is the upstream shape,
  keeps dimension fields off non-image files, and the MRO walk selects the right
  one automatically.
- **A bespoke package-defined `Upload` scalar.** Rejected: Strawberry ships
  `Upload` (`strawberry.file_uploads.scalars`); re-using it keeps multipart
  parsing on the engine and avoids a parallel scalar incompatible with the
  built-in multipart conventions
  ([Decision 5](#decision-5--upload-scalar-registration-mirrors-the-bigint-precedent)).
- **`graphene-django`'s `FileField` → `String` output.** Rejected: too weak; it
  matches the old `spec-001` simplification this card replaces.
- **Storage-backend abstraction / signed-URL generation.** Out of scope
  ([Non-goals](#non-goals)).

## User-facing API

No new `DjangoType` `Meta` key, no new constructor argument — a file/image
column is converted automatically by being in the type's `Meta.fields`
selection. Three net-new public symbols are added to the package root
([Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols)).

Read side — a `DjangoType` over a model with file/image columns:

```python
from django.db import models

from django_strawberry_framework import DjangoFileType, DjangoImageType, DjangoType, finalize_django_types


class Asset(models.Model):
    attachment = models.FileField(upload_to="files/")          # required: no default / blank / null
    preview = models.ImageField(upload_to="previews/", blank=True)  # optional: blank=True


class AssetType(DjangoType):
    class Meta:
        model = Asset
        fields = ("id", "attachment", "preview")


finalize_django_types()
```

generates:

```graphql
type AssetType {
  id: Int!
  attachment: DjangoFileType!
  preview: DjangoImageType
}

type DjangoFileType {
  name: String!
  path: String
  size: Int
  url: String
}

type DjangoImageType {
  name: String!
  path: String
  size: Int
  url: String
  width: Int
  height: Int
}
```

The object field is nullable when the Django file column can realistically be
absent (`null=True` or `blank=True`, unless
[`Meta.required_overrides`][glossary-metarequired-overrides] forces the stricter
contract). `name` is non-null for a present file; `path` / `size` / `url` /
`width` / `height` are **nullable** because storage backends and
corrupt/vanished rows can make individual properties unavailable even when a
file name exists
([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
A missing/empty file resolves the whole object as `null`, never a
`FieldFile.url` `ValueError`. A consumer who wants the legacy `str` (URL/name)
shape keeps it with a concrete annotation override (`attachment: str`), which
bypasses `convert_scalar` per
[Scalar field override semantics][glossary-scalar-field-override-semantics].

Write side — a [`DjangoMutation`][glossary-djangomutation] over the same model
generates an `Upload`-typed input field:

```python
import strawberry

from django_strawberry_framework import DjangoMutation, DjangoMutationField


class CreateAsset(DjangoMutation):
    class Meta:
        model = Asset
        operation = "create"


class UpdateAsset(DjangoMutation):
    class Meta:
        model = Asset
        operation = "update"


@strawberry.type
class Mutation:
    create_asset = DjangoMutationField(CreateAsset)
    update_asset = DjangoMutationField(UpdateAsset)
```

generates:

```graphql
scalar Upload

input AssetInput {
  attachment: Upload!
  preview: Upload
}

input AssetPartialInput {
  attachment: Upload
  preview: Upload
}
```

The same per-field requiredness rule applies (a create-input field is required
only when the model field has no usable `default`, is not `null=True`, and is
not `blank=True`); partial inputs are all-optional `UNSET`. A provided upload is
assigned through Django's normal model-field path before `full_clean()` /
`save()`; an omitted upload on update leaves the current file untouched. Binding
`Upload` requires the package config factory (the same call `BigInt` already
needs):

```python
schema = strawberry.Schema(query=Query, mutation=Mutation, config=strawberry_config())
```

### Error shapes

- A file column over an **unsupported subclass** with no registered ancestor
  still raises [`ConfigurationError`][glossary-configurationerror] at type
  creation (unchanged — `FileField` / `ImageField` are now supported, but a
  hypothetical unrelated field class is not).
- On write, a missing required `Upload` fails at the GraphQL layer as a missing
  required argument; a `full_clean()` failure (e.g. an `ImageField` validator
  rejecting a non-image upload) populates the
  [`FieldError` envelope][glossary-fielderror-envelope] keyed to the file field,
  returning a null object — not a top-level `GraphQLError`
  ([`spec-036`][spec-036] Decision 7).
- Reading a populated file whose storage cannot produce a property (a
  non-filesystem `path`, a vanished file) degrades that **subfield** to `null`
  via the narrow per-subfield guard
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability))
  — not a top-level error and not a swallowed resolver bug (the catch list is
  `ValueError` / `OSError` / storage `NotImplementedError`).
- An `extra_scalar_map={Upload: ...}` collision passed to `strawberry_config()`
  raises the existing `ValueError`, now naming `Upload` — consistent with the
  `BigInt` collision contract.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-037-upload_file_image_mapping-0_0_11.md`**.

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in
  [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN (`037`) and target
  patch (`0_0_11`) into the filename.
- The topic slug is `upload_file_image_mapping` — short, snake-case, and broad
  enough to name **both** halves of the card (the write-side `Upload` scalar
  *and* the read-side file/image output objects), which a slug like `uploads` or
  `upload_scalar` undersells.

Alternatives considered (and rejected):

- **`spec-037-upload_scalar-0_0_11.md` / `spec-037-uploads-0_0_11.md`.**
  Rejected: narrows the filename to the write half, while the read-side
  `DjangoFileType` / `DjangoImageType` change is equally in the card DoD.
- **`spec-037-files-0_0_11.md`.** Rejected: too vague; it does not name the
  write-side `Upload` scalar.

### Decision 2 — Card-scope boundary: file/image conversion only, not transport or storage abstraction

This card ships three tightly related artifacts: (1) `FileField` / `ImageField`
output object types; (2) `Upload` scalar registration and mutation input
mapping; (3) the version/doc wrap for the now-complete `0.0.11` patch. It does
**not** ship multipart test helpers, an example upload app, remote-storage
policies, image processing, or nested upload writes — each named in
[Non-goals](#non-goals) /
[Out of scope](#out-of-scope-explicitly-tracked-elsewhere).

Justification: the card is sized **S** and its DoD is a converter-table change,
a mutation-input mapping, synthetic-model tests, and glossary docs. The `0.0.14`
[`TestClient`][glossary-testclient] card already owns multipart helper
ergonomics and explicitly depends on this card for the scalar, not vice versa.
Keeping scope here small prevents a file-upload transport design from delaying
the foundational mapping ([`START.md`][start] scope-creep rule).

Alternatives considered (and rejected):

- **Ship only the read side now, write later.** Rejected: the card pairs read
  and write (its DoD names both), and the write seam already exists as a `036`
  `NotImplementedError` waiting to be filled — splitting would leave a
  half-mapped field type and a dangling seam.
- **Add a live fakeshop file model in this card.** Rejected: a `FileField` on a
  fakeshop model needs a media-root fixture and multipart HTTP plumbing —
  heavier than an S card; synthetic-model tests give full coverage
  ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).

### Decision 3 — Read-side output types: `DjangoFileType` / `DjangoImageType` mirroring upstream

[`types/converters.py`][types-converters] defines two `@strawberry.type` output
types and rewrites the two [`SCALAR_MAP`][types-converters] rows:

- `DjangoFileType` — `name`, `path`, `size`, `url` (the four fields
  [`strawberry-graphql-django`][upstream-field-types] ships).
- `DjangoImageType(DjangoFileType)` — adds `width`, `height`.
- `SCALAR_MAP[models.FileField] = DjangoFileType`;
  `SCALAR_MAP[models.ImageField] = DjangoImageType`.

`ImageField` is a `FileField` subclass, so lookup order matters:
`scalar_for_field`'s MRO walk tests `type(field).__mro__` against `SCALAR_MAP`
in MRO order, and `ImageField` appears in its own MRO *before* `FileField`, so
an `ImageField` (and a consumer `ImageField` subclass) resolves to
`DjangoImageType`, never falling through to `DjangoFileType`. Both rows are
explicit, as today's two `str` rows are.

The converter-row change alone is insufficient: a Django model attribute for a
file column returns a falsy `FieldFile` / `ImageFieldFile` descriptor even when
no file is attached, and accessing `url` / `path` / `size` on an empty
descriptor raises. So this card adds a small generated **file-column read
resolver** (wired in [`types/base.py`][types-base], bodied in
[`types/resolvers.py`][types-resolvers] alongside the relation resolvers):
`return None if not value else value`, then Strawberry resolves the subfields
off the `FieldFile`. Consumer-authored annotations / `strawberry.field`
assignments still win (the standing override short-circuit,
[Scalar field override semantics][glossary-scalar-field-override-semantics]);
the generated resolver is attached only to auto-synthesized file/image fields.

Changing `FileField` / `ImageField` from `str` to an object type is a **breaking
wire-format change** — parallel to the
[`PositiveBigIntegerField → BigInt`][glossary-specialized-scalar-conversions]
(`0.0.6`) and model-anchored `GlobalID` (`0.0.9`) precedents — acceptable
pre-`1.0.0`, recorded in the glossary, with the consumer-annotation override
(`attachment: str`,
[Scalar field override semantics][glossary-scalar-field-override-semantics]) as
the one-line opt-out. No in-repo example breaks (no fakeshop model uses a file
column).

Justification: structured output is the read-side parity goal and the lossy
`str` was always a placeholder; mirroring upstream's field names lets a
migrating consumer's selection port unchanged. Two distinct types keep dimension
fields off non-image files.

Alternatives considered (and rejected):

- **Leave output as `str` and ship only `Upload`.** Rejected: fails the
  read-side DoD and leaves consumers hand-rolling file metadata.
- **Map output to `str | None` but document custom resolvers for metadata.**
  Rejected: preserves the weak contract and ignores the upstream parity target.
- **One `DjangoFileType` with nullable `width` / `height`.** Rejected: a
  non-image `FileField` has no dimensions; the `DjangoImageType` subclass scopes
  them to images, matching upstream.
- **Add a settings flag to keep `str` globally.** Rejected: a settings key for a
  one-line per-field override is over-engineering ([`AGENTS.md`][agents]); the
  annotation override is the finer-grained opt-out.

### Decision 4 — Read-side resolution: empty file as `null` and storage-safe subfield nullability

Two nullability rules layer on the
[Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)
mapping:

- **Object-field nullability** widens to `DjangoFileType | None` when the column
  is `null=True` **or** `blank=True` — not just `field.null`. A `blank=True`
  file column stores `""` (an empty `FieldFile`) for "no file", which the
  resolver maps to `None`, so the GraphQL field must be nullable to represent
  it. This composes with the
  [`Meta.nullable_overrides`][glossary-metanullable-overrides] /
  [`Meta.required_overrides`][glossary-metarequired-overrides] `force_nullable`
  tri-state — `required_overrides` can force `DjangoFileType!` when the consumer
  guarantees a file is always present (the "contract, not data" caveat the
  override entry documents).
- **Subfield nullability** makes `path` / `size` / `url` (and `width` / `height`
  on images) **nullable**, while `name` stays non-null. This is a deliberate
  divergence from upstream's all-non-null `path: str`: a non-filesystem storage
  backend (S3) raises `NotImplementedError` from `FieldFile.path`, and a file
  deleted out from under the row raises on `.url` / `.size`. Rather than 500 the
  whole request, the read resolver guards each storage-touching subfield with a
  **narrow** exception catch (`ValueError` / `OSError` / storage
  `NotImplementedError` → `None`); a present file with healthy storage resolves
  every subfield normally.

Justification: a file field with no file must resolve to `null`, not raise; and
a storage quirk on one property must not take down the query. The narrow catch
list keeps the guard from swallowing genuine resolver bugs. `name` is reliably
present whenever the object exists (the object is `null` for an absent file), so
it stays non-null.

Alternatives considered (and rejected):

- **No resolver; rely on Strawberry's default attribute access.** Rejected: an
  empty `FieldFile` is returned but raises on `.url` / `.size`, so a blank file
  column would 500 on selection.
- **Match upstream's all-non-null subfields and document the `path` caveat.**
  Rejected: it leaves a latent 500 on non-filesystem storage / vanished files;
  the nullable-subfield contract is the safer engineering choice and the SDL
  divergence is small and documented.
- **Widen the object on `field.null` only.** Rejected: a
  `blank=True, null=False` file column (Django's common shape) would render
  non-null while the resolver returns `None` — a guaranteed non-null violation;
  `blank` must widen too.
- **Catch a broad `Exception` in the subfield guard.** Rejected: it would hide
  real bugs; the catch list is narrowed to storage-shaped errors.

### Decision 5 — `Upload` scalar registration mirrors the `BigInt` precedent

[`scalars.py`][scalars] re-exports `Upload` (and `UploadDefinition`) from
`strawberry.file_uploads.scalars` and adds `Upload: UploadDefinition` to
`_PACKAGE_SCALAR_MAP`, so the [`strawberry_config`][glossary-strawberry-config]
factory binds it into every consumer schema exactly as it binds
[`BigInt`][glossary-bigint-scalar]. Strawberry's `Upload` is
`NewType("Upload", bytes)` paired with a `scalar(...)` `ScalarDefinition` —
byte-for-byte the same shape as `BigInt = NewType("BigInt", int)` +
`_BIGINT_SCALAR_DEFINITION`, so it **is** a `scalar_map` entry, not an
already-resolvable annotation: without the map entry an `Upload`-annotated field
would not resolve to the scalar.

Justification: [`spec-025`][spec-025] Decision 3 established the `NewType` +
`ScalarDefinition` registration pattern, and the `strawberry_config` glossary
entry already names `Upload` as the next scalar to land here; `Upload` slots in
with one map entry and no new machinery. Re-using Strawberry's scalar keeps
multipart-request parsing on the engine.

Alternatives considered (and rejected):

- **Ask consumers to import Strawberry's `Upload` and pass an
  `extra_scalar_map`.** Rejected: generated inputs reference `Upload`; the
  package must register its own generated scalar dependencies.
- **Define a wrapper `NewType` instead of re-exporting Strawberry's `Upload`.**
  Rejected: a second upload scalar would be incompatible with the engine's
  built-in multipart conventions and force clients to special-case it.
- **Skip the `_PACKAGE_SCALAR_MAP` entry and rely on auto-registration.**
  Rejected: `Upload` is a `NewType`, not a pre-registered scalar — the map entry
  binds the `NewType` to its `ScalarDefinition` (the same reason `BigInt` must
  be in the map).

### Decision 6 — Write-side input mapping: the mutation seam becomes `Upload`

The [`spec-036`][spec-036] fail-loud branch in
[`mutations/inputs.py`][mutations-inputs] #"Upload staged seam
(TODO-ALPHA-037-0.0.11)" is removed and replaced with a real mapping:
`FileField` / `ImageField` → `Upload`, required per the shipped per-field rule
(a `blank=False` / `null=False` / no-default file column is required in the
create `<Model>Input`, optional with `strawberry.UNSET` otherwise and in
`<Model>PartialInput`), widened to `Upload | None` on `blank` / `null`.
File/image fields are **scalar** input fields for naming: the Python attribute
is the model field name (`attachment`, not `attachment_id`), and the GraphQL
name follows the normal camel-case converter. The generator continues to own
requiredness, `UNSET`, partial-update omission, `Meta.fields` / `Meta.exclude`
narrowing, and custom-input merge. The write resolver
([`mutations/resolvers.py`][mutations-resolvers]) assigns a provided `Upload` to
the model file attribute before `full_clean()` / `save()`.

**The `036` file-column merge-override exception is lifted.**
[`spec-036`][spec-036] CR-6 pinned that file columns were "the one exception to
the merge override" because the `NotImplementedError` ran *before* the
`Meta.input_class` override skip. With `Upload` wired, the file-column branch
emits a valid field, so a file column now participates in the
[`Meta.input_class`][glossary-input-type-generation] /
`Meta.partial_input_class` merge override like any scalar; Slice 2 removes the
CR-6 carve-out and updates its `test_inputs.py` coverage.

Justification: the seam was built for exactly this card; reusing the generator
prevents a second write-input path just for uploads and keeps custom-input merge
consistent with every other scalar.

Alternatives considered (and rejected):

- **Keep the `NotImplementedError` and require `Meta.exclude`.** Rejected: that
  was the staging guard before `037`; after this card it would make the card a
  no-op for generated mutation inputs.
- **Require a consumer-authored `input_class` for upload fields.** Rejected:
  violates the generated-input goal and creates a bespoke escape hatch where the
  core package should know the mapping.
- **Represent uploads as `str` paths.** Rejected: unsafe and not a GraphQL
  upload contract; the client sends multipart upload values, not server paths.

### Decision 7 — Public surface: three net-new root-exported symbols

[`__init__.py`][init] re-exports and adds to `__all__`: `Upload` (the scalar,
from [`scalars.py`][scalars]), `DjangoFileType`, and `DjangoImageType` (from
[`types/converters.py`][types-converters]). All three already have
[`docs/GLOSSARY.md`][glossary] entries (`planned for 0.0.11`), so Slice 4
promotes the existing entries to `shipped (0.0.11)` and adds the three to the
glossary **Public exports** list; no net-new glossary *heading* is created by
this card.

Justification: root export matches the audience — `Upload` is referenced
wherever a consumer hand-writes an input field, and the two output types are the
field types a consumer names in custom resolvers / `strawberry.field`
annotations; all belong at the root alongside [`BigInt`][glossary-bigint-scalar]
/ [`DjangoType`][glossary-djangotype], parallel to how
[`BigInt`][glossary-bigint-scalar] ([`spec-017`][spec-017]) is root-exported.

Alternatives considered (and rejected):

- **Export only from a `scalars` / `types` namespace.** Rejected: the symbols
  are referenced inside schema modules alongside root-exported types; the
  package's settled posture is to root-export consumer-facing scalars and types.
- **Do not export the output types (auto-generated, never named).** Rejected: a
  consumer overriding a file field's resolver, or annotating a computed file
  field, must be able to name them; the glossary already lists them as public.

### Decision 8 — No new `Meta` key, no new setting, no dynamic storage policy

This card changes existing conversion behavior; it adds no new `DjangoType`
`Meta` key and no `DJANGO_STRAWBERRY_FRAMEWORK` setting.
[`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]
remain the opt-in / opt-out selectors;
[`Meta.nullable_overrides`][glossary-metanullable-overrides] /
[`Meta.required_overrides`][glossary-metarequired-overrides] remain the
nullability overrides; consumer-authored scalar overrides still bypass generated
conversion.

Justification: the repository rule is explicit — add settings keys only when the
feature needs them ([`AGENTS.md`][agents]). The file/image mapping has no
project-wide policy knob; the existing scalar-override semantics already provide
the escape hatch.

### Decision 9 — Test placement: package tests own synthetic file/image models

No fakeshop model has a file/image field, and adding one solely for this card
would be example-app churn, not a real acceptance path. Therefore:

- converter and generated-output behavior live in [`tests/types/`][test-types];
- generated mutation input behavior lives in
  [`tests/mutations/`][test-mutations];
- scalar registration and root-export pins live in
  [`tests/test_scalars.py`][test-scalars] /
  [`tests/base/test_init.py`][test-base-init];
- live `/graphql/` tests are added **only** if implementation naturally exposes
  a file/image field through an existing fakeshop app.

Coverage uses **synthetic models** (a test-only model with `FileField` /
`ImageField` columns over a `tmp_path` storage) — the [`spec-017`][spec-017]
converter-table precedent. Per the
[`examples/fakeshop/test_query/README.md`][test-query-readme] rule, a line
reachable through a real fakeshop query belongs in live HTTP; a synthetic
file/image model that exists only for a converter branch belongs in package
tests. Per the [`docs/SPECS/NEXT.md`][next] "prefer the card" rule (the card DoD
scopes to synthetic-model tests), the synthetic-model strategy wins and a live
fakeshop file-upload surface is deferred to fakeshop activation
([`TODO-BETA-051-0.1.5`][kanban]); the tension is recorded, not silently
resolved.

Alternatives considered (and rejected):

- **Add a live fakeshop file model + multipart HTTP test now.** Rejected: out of
  scope for an S converter card.
- **Mock the storage backend instead of a real `tmp_path` storage.** Rejected: a
  real temp-dir storage exercises `FieldFile.path` / `.size` / `.url` honestly;
  mock only the non-filesystem-`path` case, where a real backend is impractical,
  to cover the
  [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)
  guard.

### Decision 10 — This card owns the final `0.0.11` version bump

Unlike [`spec-036`][spec-036] (which shared `0.0.11` with this then-unstarted
sibling and so deferred the bump to "the joint cut"), **this card is the joint
cut.** [`docs/SPECS/NEXT.md`][next] Step 3 scopes "multiple WIP cards share the
patch" to the `## In progress` column; `036` is already `DONE` and `037` is the
**lone** `## In progress` entry on `0.0.11`, so the deferral condition is not
met for `037`. Leaving the version at `0.0.10` after `037` ships would make the
docs and public exports claim `0.0.11` behavior under a `0.0.10` identity, and
nobody would ever bump it (both cards would have deferred). Slice 4 therefore
aligns the version quintet:

- [`pyproject.toml`][pyproject]
- `__version__` in [`__init__.py`][init]
- [`tests/base/test_init.py::test_version`][test-base-init]
- the [`docs/GLOSSARY.md`][glossary] package-version line
- `uv.lock` if it carries the package version

Justification: `037` closes the `0.0.11` feature set, so it owns the cut —
exactly the card `036` Decision 13 deferred to. The bump moves only after the
mapping, tests, and docs are complete (Slice 4), never in Slice 1.

Alternatives considered (and rejected):

- **Defer again to a separate release-alignment card.** Rejected: no such WIP
  card exists, and `036` already deferred to this joint cut; a second deferral
  would orphan the bump.
- **Treat `036` (DONE) as a co-WIP card and defer per the multi-card rule.**
  Rejected: the NEXT.md rule keys on the `## In progress` column, where `037`
  stands alone; a DONE card is not a WIP co-owner.
- **Bump in Slice 1.** Rejected: the version should move only after the feature
  and docs are complete.

## Implementation plan

Four slices. Slices 1–2 are independent (read vs write modules); Slice 3 depends
on both; Slice 4 is doc + version-cut only. Line deltas are planning estimates.

| Slice | Files touched | New / changed tests | Approx. delta |
| --- | --- | --- | --- |
| 1 — read output objects + `SCALAR_MAP` + empty-file/storage resolver | [`types/converters.py`][types-converters] (`DjangoFileType` / `DjangoImageType` + two rows), [`types/base.py`][types-base] (resolver wiring + `blank`-aware nullability), [`types/resolvers.py`][types-resolvers] (empty-file + narrow storage guard) | [`tests/types/test_converters.py`][test-types] (~10) + [`tests/types/test_resolvers.py`][test-types] (~6 — empty→null, populated subfields, storage-failure→null subfield, image dims) + [`tests/types/test_base.py`][test-types] (~2 — `attachment: str` override) | `+170 / -10` |
| 2 — `Upload` scalar + mutation input + file assignment | [`scalars.py`][scalars] (re-export + `_PACKAGE_SCALAR_MAP` + docstring fix), [`mutations/inputs.py`][mutations-inputs] (seam → `Upload`), [`mutations/resolvers.py`][mutations-resolvers] (file assignment) | [`tests/test_scalars.py`][test-scalars] (~3) + [`tests/mutations/test_inputs.py`][test-mutations] (~6 — file→`Upload` required/optional, `| None`, lifted CR-6) + [`tests/mutations/test_resolvers.py`][test-mutations] (~5 — create/partial assignment, no `NotImplementedError`) | `+130 / -40` |
| 3 — public exports + coverage hardening | [`__init__.py`][init] (3 exports + `__all__`) | [`tests/base/test_init.py`][test-base-init] (~3 exports) + storage/null/dimension hardening | `+50 / -0` |
| 4 — docs + `0.0.11` version cut + card wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`README.md`][readme], [`GOAL.md`][goal], [`TODAY.md`][today], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban], version files ([`pyproject.toml`][pyproject], [`__init__.py`][init], [`tests/base/test_init.py`][test-base-init]) | `test_version` → `0.0.11` | `+90 / -45` |

Total expected delta: ~`+440 / -95` — an S–M cut (the version cut and
storage-safe resolver add a little over the bare table change), matching the
card's relative size. Staged `spec-036` TODO anchors naming the upload seam are
removed in the change that ships Slice 2; the [`scalars.py`][scalars]
docstring's stale `TODO-ALPHA-035-0.0.11` reference is corrected in the same
slice. New source comments should be minimal — only the empty-file /
storage-failure resolver guard and the nullable-subfield rationale need
explanatory comments.

## Edge cases and constraints

- **Empty file descriptor.** A `FieldFile` is falsy when no file name is stored;
  the generated output returns `None` for the whole field, so selecting
  `attachment { url }` on an empty file does not raise.
- **`blank=True` but `null=False`.** File columns can be empty while storing
  `""`. Object nullability treats `blank=True` as nullable for file/image
  output, unless [`Meta.required_overrides`][glossary-metarequired-overrides]
  forces the stricter contract.
- **`Meta.required_overrides` on a blank file field.** Allowed, but the consumer
  owns the invariant; if the row contains an empty value, Strawberry's ordinary
  non-null violation is the correct signal ("contract, not data").
- **Storage without local `path`.** `path` is nullable; a backend that cannot
  provide a filesystem path degrades that subfield to `null`, not a top-level
  failure.
- **Missing file in storage.** `size` / `url` / `width` / `height` are nullable
  so a storage lookup failure degrades to a `null` subfield via the narrow catch
  (`ValueError` / `OSError` / storage `NotImplementedError`) rather than a 500.
- **Image dimensions without Pillow / corrupt image files.** `width` / `height`
  are nullable and are not forced to validate the image during schema
  resolution.
- **Consumer scalar override.** A consumer annotation / `strawberry.field` on a
  file/image column bypasses generated output conversion and the generated
  empty-file resolver, exactly like every other scalar override; on the write
  side, a consumer `Meta.input_class` field for a file column is now honored via
  the merge override (lifted CR-6 exception,
  [Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).
- **MRO precedence (`ImageField` is a `FileField`).** Both rows are explicit;
  the MRO walk hits `ImageField`'s own row before `FileField`, so an
  `ImageField` (and a consumer subclass) resolves to `DjangoImageType`.
- **Mutation partial update.** Omitted upload fields stay `UNSET` and leave the
  stored file unchanged; a provided upload replaces the file through Django's
  normal assignment path. Clearing with `null` is not guaranteed by this card
  unless the model field accepts it and the shipped pipeline handles it
  consistently ([Risks](#risks-and-open-questions)).
- **Multipart transport.** The package exposes `Upload` without shipping a
  test-client helper; consumers use Strawberry/Django's existing multipart
  request handling until the `0.0.14` [`TestClient`][glossary-testclient] helper
  lands.
- **`Upload` requires the config factory.** A schema that does not pass
  `config=strawberry_config()` will not resolve `Upload` (a `NewType` needs its
  `scalar_map` entry) — the same constraint [`BigInt`][glossary-bigint-scalar]
  carries.
- **`Upload` scalar collision.** A consumer passing
  `extra_scalar_map={Upload: ...}` to `strawberry_config()` gets the existing
  collision `ValueError`, now naming `Upload` — consistent with the `BigInt`
  collision contract.
- **No `DjangoType` `Meta` key added.** [`DEFERRED_META_KEYS`][types-base] /
  `ALLOWED_META_KEYS` are byte-unchanged; the conversion is automatic from the
  column type.

## Test plan

Test placement follows the [`AGENTS.md`][agents] mirror rule; coverage uses
**synthetic models** (a test-only model with `FileField` / `ImageField` columns
over a `tmp_path` storage), with no live fakeshop surface
([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).

- **Converter tests** ([`tests/types/test_converters.py`][test-types]):
  `FileField` → `DjangoFileType`, `ImageField` → `DjangoImageType`, MRO
  precedence (incl. a consumer `ImageField` subclass), `null=True` /
  `blank=True` widen the object field, `Meta.nullable_overrides` /
  `Meta.required_overrides` still win, `Meta.exclude` remains the opt-out.
- **Generated output resolver tests**
  ([`tests/types/test_resolvers.py`][test-types]): a synthetic model with
  non-empty file/image values resolves `name` / `path` / `size` / `url` (+
  `width` / `height`) through schema execution; an empty file resolves the
  object as `null`; a storage-property failure degrades to a `null` subfield
  (not an uncaught exception); the consumer-annotation override
  (`attachment: str`) bypasses the converter and resolver.
- **Mutation input tests** ([`tests/mutations/test_inputs.py`][test-mutations]):
  replace the staged `NotImplementedError` tests with positive `Upload`
  annotation tests for create and partial inputs; requiredness follows `default`
  / `blank` / `null`; `Meta.fields` / `Meta.exclude` narrowing includes/excludes
  file/image fields; the custom-input merge honors an overridden upload field by
  generated field name (lifted CR-6).
- **Mutation resolver tests**
  ([`tests/mutations/test_resolvers.py`][test-mutations]): a provided `Upload`
  is assigned on create; an `UNSET` leaves the file unchanged on partial update;
  the previously-`NotImplementedError` path now succeeds.
- **Scalar config tests** ([`tests/test_scalars.py`][test-scalars]):
  `strawberry_config()` includes both `BigInt` and `Upload`; an
  `extra_scalar_map` collision with `Upload` raises the existing `ValueError`;
  every call returns a fresh scalar-map dict.
- **Public export / version tests**
  ([`tests/base/test_init.py`][test-base-init]): `__all__` includes
  `DjangoFileType` / `DjangoImageType` / `Upload`; `test_version` moves to
  `0.0.11`
  ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).
- **Live HTTP tests.** None required unless implementation adds or discovers a
  genuine fakeshop file/image field; do not add a fake upload domain solely for
  coverage.
- **Cross-cutting — no regression.** The full suite is green at the 100%
  coverage gate (`fail_under = 100`); `ruff format` + `ruff check` are clean; no
  other converter row changes and no read-side regression for non-file scalars.

## Doc updates

Each slice owns its doc edits. [`AGENTS.md`][agents] #"Do not update
CHANGELOG.md unless explicitly instructed" requires `CHANGELOG.md` edits to be
explicitly instructed — and a standing design doc cannot itself grant that
permission. This spec only *describes* the release-note work; the **Slice 4
maintainer prompt must explicitly include the `CHANGELOG.md` edit** for it to be
authorized.

- **Slice 4 — version cut**
  ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)):
  align [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init],
  [`tests/base/test_init.py::test_version`][test-base-init], the
  [`docs/GLOSSARY.md`][glossary] package-version line, and `uv.lock` (if
  applicable) on `0.0.11`.
- **Slice 4 — GLOSSARY** ([`docs/GLOSSARY.md`][glossary]): promote
  [`Upload` scalar][glossary-upload-scalar] /
  [`DjangoFileType`][glossary-djangofiletype] /
  [`DjangoImageType`][glossary-djangoimagetype] to `shipped (0.0.11)` (updating
  each body to the shipped contract — the output fields, the `Upload`
  registration, the empty-file → null resolution, the nullable-subfield
  rationale); rewrite the `FileField` / `ImageField` rows in
  [Scalar field conversion][glossary-scalar-field-conversion] /
  [Specialized scalar conversions][glossary-specialized-scalar-conversions] from
  "→ `str`" to the structured output objects (read) / `Upload` (mutation input),
  recording the read-side **breaking wire-format change** alongside the
  [`PositiveBigIntegerField → BigInt`][glossary-specialized-scalar-conversions]
  precedent; add the three symbols to **Public exports** and update the
  **Index** + **File / image uploads** browse-by-category row; flip the
  [`strawberry_config`][glossary-strawberry-config] entry's "next: `Upload`" to
  "`BigInt` + `Upload`".
- **Slice 4 — package docs**: [`docs/README.md`][docs-readme] /
  [`README.md`][readme] move the `Upload` scalar + file/image mapping from
  "Coming next (`0.0.11`)" to "Shipped today" and move the README **Status**
  line from `0.0.10` to `0.0.11`; [`GOAL.md`][goal] success-criterion 6's
  `Upload` reference now ships; [`TODAY.md`][today] rewrites the
  scalar-conversion table's `FileField` / `ImageField` → `str` row to the
  structured output objects and notes upload mutation inputs as a package
  capability not exercised by products; [`CHANGELOG.md`][changelog] carries the
  `[Unreleased]` → `0.0.11` bullets **only when the Slice 4 maintainer prompt
  explicitly requests it**.
- **Slice 4 — card wrap**: [`KANBAN.md`][kanban] moves
  [`TODO-ALPHA-037-0.0.11`][kanban] to Done with the next `DONE-NNN-0.0.11` id,
  keeping its `SpecDoc` pointing at the canonical card spec (a `SpecDoc` DB edit
  re-rendered via `scripts/build_kanban_md.py`, never a hand-edit).

## Risks and open questions

Each item names a preferred answer for the `0.0.11` cut and a fallback if
implementation reveals it is wrong.

- **Clearing an existing file via mutation input.** Preferred answer
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)):
  omitted upload leaves unchanged; provided upload replaces; clearing is not
  promised unless a nullable field plus `null` assignment already works through
  the shipped mutation pipeline. Fallback: add an explicit clear-file sentinel
  in a future form/serializer flavor if real users need it — do not overload
  empty upload values in this card.
- **Output subfield nullability vs upstream parity.** Preferred answer
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)):
  `path` / `size` / `url` / `width` / `height` nullable (storage-safe), `name`
  non-null — a deliberate, documented divergence from upstream's all-non-null
  `path: str`. Fallback: if nullable subfields prove awkward in
  Strawberry/Django, keep `path` nullable at minimum and document
  local-storage-only behavior for the others, but never let an empty/unreadable
  file descriptor raise.
- **Where to define `DjangoFileType` / `DjangoImageType`.** Preferred answer
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)):
  define them in [`types/converters.py`][types-converters], where the
  field-class mapping lives, and root-export them. Fallback: a tiny
  `types/files.py` module if importing them from `converters.py` creates a cycle
  — do not create a broad `fields/` package that collides conceptually with the
  planned `FieldSet`.
- **Image dimension reliability.** Preferred answer: nullable `width` / `height`
  resolved from Django's image field object when available. Fallback: ship only
  the file fields on `DjangoImageType` and record dimensions as a follow-up if
  the implementation would need heavy Pillow/storage coupling — use only if
  tests prove dimensions are not robust.
- **Card conflict — stale `"Pairs with 028"` note.** The card's "Other" section
  says "Pairs with 028", but `028` is the
  [ordering subsystem][glossary-orderset] (`DONE-028-0.0.8`), unrelated to
  uploads. Preferred reading: the genuine pairing is with the mutations card
  [`DONE-036-0.0.11`][kanban] (whose input seam this card fills) — the `028`
  reference is a stale copy-paste. Recorded per the [`docs/SPECS/NEXT.md`][next]
  "prefer the card, surface the conflict" rule.
- **Card conflict — stale `mutations/ (planned)` predicted file.** The card's
  "Predicted files" annotates
  `django_strawberry_framework/mutations/ (planned)`, but `mutations/` shipped
  with [`DONE-036-0.0.11`][kanban]. Preferred reading: the directory exists;
  this card edits [`mutations/inputs.py`][mutations-inputs] /
  [`mutations/resolvers.py`][mutations-resolvers] in place.
- **Card conflict — stale `TODO-ALPHA-035-0.0.11` in the `scalars.py`
  docstring.** [`scalars.py`][scalars] #"Future scalars (e.g. ``Upload`` per
  TODO-ALPHA-035-0.0.11) land here." names `035`, but `035` is the
  optimizer-hardening card; the real `Upload` owner is this card, `037`.
  Preferred reading: a stale number — Slice 2 corrects the docstring to
  `TODO-ALPHA-037-0.0.11`. (The [`mutations/inputs.py`][mutations-inputs] seam
  already names `037` correctly.)

## Out of scope (explicitly tracked elsewhere)

- **Multipart request helper** — [`TestClient`][glossary-testclient]
  (`TODO-ALPHA-043-0.0.14`); depends on this scalar existing but is not
  implemented here.
- **Form-based mutations** ([`DjangoFormMutation`][glossary-djangoformmutation])
  — `0.0.12` (`TODO-ALPHA-038-0.0.12`); reuses `Upload` through the same
  scalar-map helper where form fields need it.
- **DRF serializer mutations + auth mutations**
  ([`SerializerMutation`][glossary-serializermutation]) — `0.0.13`; serializer
  upload handling builds on this scalar.
- **A live fakeshop file-upload surface** — deferred to fakeshop activation
  ([`TODO-BETA-051-0.1.5`][kanban]); this card covers both directions with
  synthetic-model tests
  ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).
- **Field-level read gates** — `FieldSet` / per-field permission hooks in
  `0.1.1`; file-metadata permissions are not special-cased here.
- **Remote-storage adapters, thumbnailing, image validation, and signed-URL
  policies** — consumer/storage concerns beyond a model-field conversion card.

## Definition of done

The completion contract the card is built against. Items map onto the card's own
DoD bullets: item 1 (read converter), 2 (write input mapping), 3
(synthetic-model tests), 4 (glossary) — plus the spec / exports / version-cut
the [`docs/SPECS/NEXT.md`][next] flow adds.

**Spec + companion CSV**

1. `docs/spec-037-upload_file_image_mapping-0_0_11.md` (the canonical card spec)
   and its companion `spec-037-upload_file_image_mapping-0_0_11-terms.csv`
   exist;
   `uv run python scripts/check_spec_glossary.py --spec docs/spec-037-upload_file_image_mapping-0_0_11.md`
   reports `OK: <N> terms`.

**Slice 1 — read output objects**

2. [`types/converters.py`][types-converters] defines `DjangoFileType` (`name`
   non-null; `path` / `size` / `url` nullable) and
   `DjangoImageType(DjangoFileType)` (+ nullable `width` / `height`) and maps
   [`SCALAR_MAP`][types-converters] `FileField` → `DjangoFileType` /
   `ImageField` → `DjangoImageType`
   ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream));
   a file column resolves to `DjangoFileType | None` on `blank` / `null`, the
   generated resolver returns `None` for an empty `FieldFile`, and
   storage-property failures degrade to `null` subfields via the narrow catch
   ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability));
   the consumer-annotation override still wins.

**Slice 2 — write `Upload` input**

3. [`scalars.py`][scalars] re-exports `Upload` and registers it in
   `_PACKAGE_SCALAR_MAP` so [`strawberry_config`][glossary-strawberry-config]
   binds it
   ([Decision 5](#decision-5--upload-scalar-registration-mirrors-the-bigint-precedent));
   [`mutations/inputs.py`][mutations-inputs] maps `FileField` / `ImageField` to
   `Upload` (required per the shipped per-field rule, `| None` on `blank` /
   `null`), the `NotImplementedError` seam and its tests are removed, and file
   columns participate in the
   [`Meta.input_class`][glossary-input-type-generation] merge override (CR-6
   exception lifted); [`mutations/resolvers.py`][mutations-resolvers] assigns
   the uploaded file before `full_clean()` / `save()`
   ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).

**Slice 3 — public exports + coverage**

4. [`__init__.py`][init] re-exports `Upload` / `DjangoFileType` /
   `DjangoImageType` and adds all three to `__all__`
   ([Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols));
   [`tests/base/test_init.py`][test-base-init] pins them; synthetic-model tests
   cover the read converter / resolver (incl. storage-failure → null subfield),
   the `Upload` registration, and the write mapping
   ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).

**Cross-cutting — no regression**

5. The full suite is green at the 100% coverage gate (`fail_under = 100`);
   `ruff format` + `ruff check` are clean; no other converter row changes and no
   read-side regression for non-file scalars.

**Slice 4 — docs + the `0.0.11` cut + card wrap**

6. [`docs/GLOSSARY.md`][glossary] promotes
   [`Upload` scalar][glossary-upload-scalar] /
   [`DjangoFileType`][glossary-djangofiletype] /
   [`DjangoImageType`][glossary-djangoimagetype] to `shipped (0.0.11)`, rewrites
   the [Scalar field conversion][glossary-scalar-field-conversion] /
   [Specialized scalar conversions][glossary-specialized-scalar-conversions]
   file/image rows, adds the three to Public exports, records the read-side
   breaking-wire-format change, and moves the package-version line to `0.0.11`;
   [`docs/README.md`][docs-readme] / [`README.md`][readme] move the `Upload`
   scalar to "Shipped today" and the Status to `0.0.11`; [`GOAL.md`][goal] /
   [`TODAY.md`][today] reflect the shipped upload capability and the rewritten
   scalar table; [`CHANGELOG.md`][changelog] carries the bullets **only when the
   Slice 4 maintainer prompt explicitly requests the edit**;
   [`KANBAN.md`][kanban] records the card `DONE-NNN-0.0.11` with the `SpecDoc`
   reference at the canonical card spec (kanban DB + re-render).
7. **The `0.0.11` version bump lands in this card**
   ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)):
   [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init],
   [`tests/base/test_init.py::test_version`][test-base-init], the
   [`docs/GLOSSARY.md`][glossary] package-version line, and `uv.lock` (if
   applicable) align on `0.0.11`. The three net-new public symbols (`Upload`,
   `DjangoFileType`, `DjangoImageType`) are added to `__all__` and the export
   pin updated accordingly.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[pyproject]: ../pyproject.toml
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-auto-typed-annotations]: GLOSSARY.md#auto-typed-annotations
[glossary-bigint-scalar]: GLOSSARY.md#bigint-scalar
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-djangofiletype]: GLOSSARY.md#djangofiletype
[glossary-djangoformmutation]: GLOSSARY.md#djangoformmutation
[glossary-djangoimagetype]: GLOSSARY.md#djangoimagetype
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: GLOSSARY.md#djangomutationfield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: GLOSSARY.md#fielderror-envelope
[glossary-input-type-generation]: GLOSSARY.md#input-type-generation
[glossary-metaexclude]: GLOSSARY.md#metaexclude
[glossary-metafields]: GLOSSARY.md#metafields
[glossary-metamodel]: GLOSSARY.md#metamodel
[glossary-metanullable-overrides]: GLOSSARY.md#metanullable_overrides
[glossary-metarequired-overrides]: GLOSSARY.md#metarequired_overrides
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-scalar-field-conversion]: GLOSSARY.md#scalar-field-conversion
[glossary-scalar-field-override-semantics]: GLOSSARY.md#scalar-field-override-semantics
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-specialized-scalar-conversions]: GLOSSARY.md#specialized-scalar-conversions
[glossary-strawberry-config]: GLOSSARY.md#strawberry_config
[glossary-testclient]: GLOSSARY.md#testclient
[glossary-upload-scalar]: GLOSSARY.md#upload-scalar
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-001]: SPECS/spec-001-django_types-0_0_1.md
[spec-017]: SPECS/spec-017-deferred_scalars-0_0_6.md
[spec-025]: SPECS/spec-025-scalar_map_helper-0_0_7.md
[spec-026]: SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md
[spec-036]: SPECS/spec-036-mutations-0_0_11.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[init]: ../django_strawberry_framework/__init__.py
[mutations-inputs]: ../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../django_strawberry_framework/mutations/resolvers.py
[scalars]: ../django_strawberry_framework/scalars.py
[types-base]: ../django_strawberry_framework/types/base.py
[types-converters]: ../django_strawberry_framework/types/converters.py
[types-resolvers]: ../django_strawberry_framework/types/resolvers.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-mutations]: ../tests/mutations/
[test-scalars]: ../tests/test_scalars.py
[test-types]: ../tests/types/

<!-- examples/ -->
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-field-types]: https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/fields/types.py