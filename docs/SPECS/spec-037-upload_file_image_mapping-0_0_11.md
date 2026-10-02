# Spec: Upload scalar and file / image field mapping — `FileField` / `ImageField` output objects and mutation `Upload` inputs

The package's file/image contract in both directions of the wire. On the **read**
side a `FileField` / `ImageField` column converts to a structured output object,
[`DjangoFileType`][glossary-djangofiletype] / [`DjangoImageType`][glossary-djangoimagetype]
(`name` / `size` / `url`, plus `width` / `height` for images), selected by a
read-only `FIELD_OUTPUT_TYPE_MAP` that stays off the shared scalar / filter-input
[`SCALAR_MAP`][types-converters]. On the **write** side the
[auto-generated mutation `Input` types][glossary-input-type-generation]
([`spec-036`][spec-036]) map the same columns to Strawberry's
[`Upload` scalar][glossary-upload-scalar] through
`django_strawberry_framework/mutations/inputs.py::model_column_write_annotation`. It is a
Required [`strawberry-graphql-django`][upstream-field-types] parity item: upstream's
`field_type_map` maps `files.FileField` → `DjangoFileType`, `files.ImageField` →
`DjangoImageType`, and both → `Upload` in `input_field_type_map`. `Upload` itself
needs no registration: it is a Strawberry built-in (`NewType("Upload", bytes)` + a
`ScalarDefinition`) already in Strawberry's `DEFAULT_SCALAR_REGISTRY`, so an
`Upload`-annotated field resolves in any schema and the package only **re-exports**
it — the contrast with the package-custom [`BigInt`][glossary-bigint-scalar] scalar,
which is absent from the default registry and is bound through
[`strawberry_config`][glossary-strawberry-config].

Status: **SHIPPED (`0.0.11`)** — card [`DONE-037-0.0.11`][kanban], released under the
[`CHANGELOG.md`][changelog] `## [0.0.11]` heading. The
[Slice checklist](#slice-checklist) stays unticked; the `Status:` line is the
completion source of truth.

Owner: package maintainer.

Related specs: [`spec-036-mutations-0_0_11.md`][spec-036] (the mutation input
generator whose per-column annotation this card fills for file columns, its
Decision 6, and the [`FieldError` envelope][glossary-fielderror-envelope], its
Decision 7); [`spec-048-secure_output_defaults-0_0_14.md`][spec-048] (the server's
absolute filesystem `path` is off the default file/image output and published only
through the per-column [`Meta.filesystem_path_fields`][glossary-metafilesystem-path-fields]
opt-in, which swaps the column onto [`DjangoFilePathType`][glossary-djangofilepathtype]
/ [`DjangoImagePathType`][glossary-djangoimagepathtype]);
[`spec-025-scalar_map_helper-0_0_7.md`][spec-025] (the
[`strawberry_config`][glossary-strawberry-config] / `_PACKAGE_SCALAR_MAP`
registration path `BigInt` needs and `Upload` does not);
[`spec-017-deferred_scalars-0_0_6.md`][spec-017] (the converter-table rows beside
which the file/image rows sit); [`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026]
(the `scalars` fakeshop app that carries the live file/image surface); and
[`spec-001-django_types-0_0_1.md`][spec-001] (the `DjangoType` conversion pipeline).

This spec's justifications and the alternatives each Decision rejected live in the
rationale companion
[`docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md`][spec-037-rationale].

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [`Upload` scalar][glossary-upload-scalar] — the write-side subject: Strawberry's
  built-in scalar, re-exported from the package root, typing a `FileField` /
  `ImageField` column on generated mutation inputs.
- [`DjangoFileType`][glossary-djangofiletype] /
  [`DjangoImageType`][glossary-djangoimagetype] — the read-side subjects.
  `DjangoFileType` carries `name` / `size` / `url`; `DjangoImageType` adds `width` /
  `height`. The server's absolute filesystem `path` is not a default subfield — a
  deployment that serves it opts in per column through
  [`Meta.filesystem_path_fields`][glossary-metafilesystem-path-fields], which swaps the
  column onto [`DjangoFilePathType`][glossary-djangofilepathtype] /
  [`DjangoImagePathType`][glossary-djangoimagepathtype]
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream) /
  [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
- [Scalar field conversion][glossary-scalar-field-conversion] /
  [Specialized scalar conversions][glossary-specialized-scalar-conversions] — the
  converter tables. The file/image row is a three-way split: **read** output → the
  structured objects (via `FIELD_OUTPUT_TYPE_MAP`), **filter / scalar-input** value →
  `str` in `SCALAR_MAP`, **mutation input** → `Upload`; the read-side change from the
  earlier `str` mapping is recorded there as a breaking wire-format change.
- [`BigInt` scalar][glossary-bigint-scalar] /
  [`strawberry_config`][glossary-strawberry-config] — the contrast case: `BigInt` is
  package-custom and bound through the factory; `Upload` is already in Strawberry's
  `DEFAULT_SCALAR_REGISTRY` and needs no `_PACKAGE_SCALAR_MAP` entry
  ([Decision 5](#decision-5--re-export-upload-rather-than-register-it)).
- [`DjangoMutation`][glossary-djangomutation] /
  [Input type generation][glossary-input-type-generation] /
  [`DjangoMutationField`][glossary-djangomutationfield] /
  [`FieldError` envelope][glossary-fielderror-envelope] — the [`spec-036`][spec-036]
  write side; its input generator produces `<Model>Input` / `<Model>PartialInput` and
  maps a file/image column to `Upload`
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).
- [Scalar field override semantics][glossary-scalar-field-override-semantics] /
  [`auto`-typed annotations][glossary-auto-typed-annotations] — the consumer opt-out:
  a concrete annotation override (`attachment: str`) keeps a `str` read shape and
  bypasses generated conversion
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)).
- [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]
  / [`DjangoType`][glossary-djangotype] / [`Meta.model`][glossary-metamodel] — the
  type-system surface the conversions ride; a file column is selected / excluded by
  the same rules as any column, and the input generator narrows by the mutation's own
  `Meta.fields` / `Meta.exclude` ([`spec-036`][spec-036] Decision 6).
- [`Meta.nullable_overrides`][glossary-metanullable-overrides] /
  [`Meta.required_overrides`][glossary-metarequired-overrides] — the
  `force_nullable` tri-state the default-nullable file output composes with
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
- [`ConfigurationError`][glossary-configurationerror] — raised for an unsupported
  field class on the read path; `FileField` / `ImageField` are supported on both read
  and write.
- [`DjangoFormMutation`][glossary-djangoformmutation] /
  [`SerializerMutation`][glossary-serializermutation] — the form and serializer
  flavors; each types its own file fields as `Upload` and reuses the same
  [`FieldError` envelope][glossary-fielderror-envelope].
- [`TestClient`][glossary-testclient] — the package test client whose path-keyed
  `files=` builder sends GraphQL multipart requests; the live upload tests drive
  through it ([Non-goals](#non-goals)).
- [relation handling][glossary-relation-handling] /
  [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — a file column is a
  **scalar** column, not a relation: it carries no FK and needs no optimizer planning,
  and its generated read resolver is a thin scalar-column wrapper.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (a line reachable through a real
  fakeshop query is covered in `examples/fakeshop/test_query/`; the package trees
  [`tests/types/`][test-types] / [`tests/`][test-scalars] /
  [`tests/mutations/`][test-mutations] keep what a live request cannot express —
  [Decision 9](#decision-9--test-placement-the-live-tier-owns-the-fileimage-wire-contract));
  the settings-keys-only-when-needed rule (the file/image conversion reads no setting).
- [`START.md`][start] — "behavior from `strawberry-graphql-django`, surface from
  `django-graphene-filters` + DRF" (the file/image output shapes and `Upload` mapping
  are borrowed at the *outcome* level); the "do both libraries provide it? →
  foundational" test; the reference-style markdown link convention.
- [`CONTRIBUTING.md`][contributing] — the 100% coverage gate on
  `django_strawberry_framework`; every converter branch, the read resolver, the
  per-subfield guard, the `Upload` re-export and the write-input mapping are covered.
- [`docs/TREE.md`][tree] — the module map; the file/image surface lives in
  [`types/converters.py`][types-converters] (read), [`types/resolvers.py`][types-resolvers]
  (parent resolver), [`scalars.py`][scalars] (the `Upload` re-export) and
  [`mutations/inputs.py`][mutations-inputs] (write).
- [`GOAL.md`][goal] — success criterion 6 names "`Upload` for `FileField` /
  `ImageField`" across the write flavors; this card supplies the scalar and the
  generated-input mapping.

## Slice checklist

Each top-level item maps to one commit / PR. **Four slices: read output objects
(Slice 1), write `Upload` input (Slice 2), exports + coverage (Slice 3), docs + the
`0.0.11` cut (Slice 4).**

- [ ] Slice 1: read-side output objects + the `FIELD_OUTPUT_TYPE_MAP` read map + the
  file-column resolver (per
  [Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)
  /
  [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability))
  - [ ] [`types/converters.py`][types-converters]: `DjangoFileType` (`@strawberry.type`
    with **resolver-backed** fields `name: str`, `size: int | None`, `url: str | None`)
    and `DjangoImageType(DjangoFileType)` (adds `width: int | None`,
    `height: int | None`); every nullable subfield delegates to the shared
    `django_strawberry_framework/types/converters.py::_safe_file_attr` guard
    ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
    `FIELD_OUTPUT_TYPE_MAP` (`models.ImageField → DjangoImageType`,
    `models.FileField → DjangoFileType`) is walked by
    `django_strawberry_framework/types/converters.py::_field_output_type_for` and consulted by
    `convert_field_output(field, type_name, *, force_nullable=None, expose_filesystem_path=False)`,
    which delegates every non-file column to `convert_scalar`, so `convert_scalar` /
    `scalar_for_field` stay scalar-only and no output object reaches the filter-input
    path. [`SCALAR_MAP`][types-converters]'s `FileField: str` / `ImageField: str` rows
    stay `str` for that path
    ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)).
    The MRO walk tests `type(field).__mro__`, where `ImageField` precedes `FileField`,
    so an `ImageField` (and a consumer subclass) resolves to `DjangoImageType`.
  - [ ] [`types/base.py`][types-base]: `_build_annotations` calls
    `convert_field_output` for every non-relation column not in
    `consumer_authored_fields`, threading the `nullable_overrides` /
    `required_overrides` tri-state as `force_nullable` and
    `field.name in filesystem_path_fields` as `expose_filesystem_path`. The
    default-nullable object shape (`<object> | None` independent of `blank` / `null`)
    is applied inside `convert_field_output`'s file branch.
  - [ ] [`types/resolvers.py`][types-resolvers] / [`types/finalizer.py`][types-finalizer]:
    `django_strawberry_framework/types/resolvers.py::_attach_file_resolvers` attaches
    `django_strawberry_framework/types/resolvers.py::_make_file_resolver` to every
    selected non-relation column that resolves through `FIELD_OUTPUT_TYPE_MAP`; the
    finalizer calls it in the same Phase-2 loop as `_attach_relation_resolvers` (the
    only place resolvers attach before `strawberry.type(...)` freezes the class). The
    parent resolver returns `None` for an empty / falsy `FieldFile` and otherwise the
    bound `FieldFile` (**object nullability only**); the per-subfield exception guard
    lives on the output types' own resolvers
    ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
    The attachment's skip set is **`definition.consumer_authored_fields`** (annotation
    *and* assigned-`strawberry.field` overrides — broader than the relation pass's
    `consumer_assigned_relation_fields`), so a consumer `attachment: str` keeps the
    `str` shape and gets no generated resolver or object type
    ([Scalar field override semantics][glossary-scalar-field-override-semantics]).
  - [ ] Output object nullability: a file/image column maps to `DjangoFileType | None`
    **by default**, independent of `null` / `blank`, composing with the
    [`Meta.nullable_overrides`][glossary-metanullable-overrides] /
    [`Meta.required_overrides`][glossary-metarequired-overrides] `force_nullable`
    tri-state — `required_overrides` (`force_nullable=False`) is the opt-in to the
    stricter `DjangoFileType!` contract.
  - [ ] Package coverage: [`tests/types/test_converters.py`][test-types] —
    `FileField` → `DjangoFileType`, `ImageField` → `DjangoImageType`, MRO precedence
    over a consumer `ImageField` subclass, default `| None`, the `force_nullable`
    compose, and the filter-input pin
    (`tests/types/test_converters.py::test_file_columns_stay_scalar_on_the_filter_input_path`:
    `scalar_for_field` and [`filters/inputs.py`][filters-inputs]
    `_scalar_from_model_field` return `str` and the `SCALAR_MAP` rows stay `str`);
    [`tests/types/test_base.py`][test-types] — the consumer-annotation and
    assigned-resolver overrides get no generated resolver or object type, an
    un-overridden file column does, and `Meta.*_overrides` reach the file branch.
- [ ] Slice 2: write-side `Upload` input + the `Upload` re-export (per
  [Decision 5](#decision-5--re-export-upload-rather-than-register-it)
  /
  [Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload))
  - [ ] [`scalars.py`][scalars]: re-exports `Upload` and `UploadDefinition` from
    `strawberry.file_uploads.scalars` and lists both in its `__all__`; `Upload` has no
    `_PACKAGE_SCALAR_MAP` entry
    ([Decision 5](#decision-5--re-export-upload-rather-than-register-it)).
  - [ ] [`mutations/inputs.py`][mutations-inputs]:
    `django_strawberry_framework/mutations/inputs.py::model_column_write_kind` classifies
    a `FileField` / `ImageField` as `FILE`, and
    `django_strawberry_framework/mutations/inputs.py::model_column_write_annotation` returns
    `Upload` for it. Requiredness follows the per-field rule (a `blank=False` /
    `null=False` / no-default file column is required in the create `<Model>Input`,
    optional with `UNSET` otherwise and in `<Model>PartialInput`), and a non-required
    field widens to `Upload | None`. The Python attribute is the model field name
    (`attachment`, not `attachment_id`). File columns take the
    [`Meta.input_class`][glossary-input-type-generation] /
    `Meta.partial_input_class` merge override like any scalar.
  - [ ] [`mutations/resolvers.py`][mutations-resolvers]:
    `django_strawberry_framework/mutations/resolvers.py::_decode_relations` routes `FILE` to
    the scalar handler, so an uploaded file reaches `model(**attrs)` (create) /
    `setattr` (update) before `full_clean()` / `save()` with no file-specific branch;
    Django's `FileField` descriptor accepts the `UploadedFile` directly. An omitted
    field (`UNSET`) leaves the file unchanged on partial update; an explicit `null` on
    a `null=False` file column is a `FieldError` from
    `django_strawberry_framework/mutations/resolvers.py::_explicit_null_error`
    (omittable ≠ nullable — never a silent clear).
  - [ ] Package coverage: [`tests/test_scalars.py`][test-scalars] — `Upload` is
    Strawberry's object, importable from `scalars`, absent from
    `strawberry_config().scalar_map`, and an `Upload`-typed field builds under a plain
    `StrawberryConfig`; [`tests/mutations/test_inputs.py`][test-mutations] — the
    `FILE` kind, the `Upload` annotation, the optional-column `UNSET` default,
    `Meta.fields` / `Meta.exclude` narrowing, and the consumer override skipping the
    generated `Upload` field. File assignment on create / update is live
    ([Decision 9](#decision-9--test-placement-the-live-tier-owns-the-fileimage-wire-contract)).
- [ ] Slice 3: public exports + coverage hardening (per
  [Decision 7](#decision-7--public-surface-upload-djangofiletype-and-djangoimagetype-root-exported)
  /
  [Decision 9](#decision-9--test-placement-the-live-tier-owns-the-fileimage-wire-contract))
  - [ ] [`__init__.py`][init]: re-exports `Upload` (from [`scalars.py`][scalars]) and
    `DjangoFileType` / `DjangoImageType` (from [`types/converters.py`][types-converters])
    and lists them in `__all__`.
  - [ ] Package coverage:
    `tests/base/test_init.py::test_file_upload_exports_resolve_to_their_source_definitions`
    pins the three as re-exports by identity. The live tier
    (`examples/fakeshop/test_query/test_uploads_api.py`) carries the storage-failure,
    empty-file and image-dimension rows.
- [ ] Slice 4: docs + the `0.0.11` release + card wrap (per [Doc updates](#doc-updates)
  / [Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump))
  - [ ] The `0.0.11` release
    ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).
  - [ ] [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme],
    [`README.md`][readme], [`GOAL.md`][goal], [`TODAY.md`][today] and
    [`KANBAN.md`][kanban] carry the shipped contract ([Doc updates](#doc-updates)).

## Problem statement

Upload fields are ordinary Django model fields, and a package that claims DRF-shaped
model-to-GraphQL generation cannot make every user-upload model hand-roll both its
output object fields and its mutation input scalars:

- A `str`-typed file field serializes to the stored name (`str(FieldFile)`),
  discarding the `url` a client needs to fetch the file, its `size`, and — for images
  — its dimensions. [`strawberry-graphql-django`][upstream-field-types] returns a
  `DjangoFileType` / `DjangoImageType`, so a migrating consumer's
  `{ avatar { url width } }` selection needs the same object shape here.
- A generated mutation input over a model with an editable file/image column needs an
  upload type for that column; inheriting the read-side `str` would be a wrong write
  contract (the client sends multipart file values, not server paths).
- A consumer hand-writing an upload field reaches for `Upload` at the package root
  beside [`BigInt`][glossary-bigint-scalar].

This is a Required `strawberry-graphql-django` parity item, foundational by the
[`START.md`][start] "do both libraries provide it?" test — both upstreams map
file/image fields, but only `strawberry-graphql-django` ships the structured output
object; `graphene-django` maps `FileField` to a bare `String`, the weaker form this
card does not copy.

## Current state

- **Read side** ([`types/converters.py`][types-converters]): `DjangoFileType`,
  `DjangoImageType`, the opt-in `DjangoFilePathType` / `DjangoImagePathType` (composed
  with the private `_FileSystemPathFields` mixin, [`spec-048`][spec-048]),
  `FIELD_OUTPUT_TYPE_MAP`, the output-type-keyed `FILESYSTEM_PATH_OUTPUT_TYPE_MAP`,
  `_field_output_type_for`, `convert_field_output` and `_safe_file_attr`.
  `SCALAR_MAP` keeps `FileField: str` / `ImageField: str` for the shared
  scalar/filter-input lookup. [`types/base.py`][types-base] `_build_annotations` calls
  `convert_field_output`; [`types/resolvers.py`][types-resolvers] carries
  `_make_file_resolver` / `_attach_file_resolvers`, called from
  [`types/finalizer.py`][types-finalizer]'s Phase-2 loop.
- **Write side** ([`mutations/inputs.py`][mutations-inputs]):
  `model_column_write_kind` returns `FILE` for a `FileField` / `ImageField` and
  `model_column_write_annotation` returns `Upload`; the column then rides the same
  override-skip / requiredness / `| None`-widening tail as any scalar in
  `build_mutation_input`. [`mutations/resolvers.py`][mutations-resolvers] routes
  `FILE` to the scalar handler, behind `_explicit_null_error`.
- **Scalar** ([`scalars.py`][scalars]): `Upload` and `UploadDefinition` re-exported
  from `strawberry.file_uploads.scalars`; `_PACKAGE_SCALAR_MAP` holds `BigInt` alone.
  The package root ([`__init__.py`][init]) exports `Upload`, `DjangoFileType`,
  `DjangoImageType`, `DjangoFilePathType` and `DjangoImagePathType` (not
  `UploadDefinition`).
- **Fakeshop.** The `scalars` app's `MediaSpecimen` carries `attachment`
  (`FileField`, required), `image` (`ImageField`, required), `optional_attachment`
  (`FileField`, `blank=True`) and `spare_image` (`ImageField`, `null=True`), exposed by
  `MediaSpecimenType`, the opt-in `MediaSpecimenWithPathType`
  (`filesystem_path_fields = ("attachment",)`) and the `createMediaSpecimen` /
  `updateMediaSpecimen` mutations. The products `Item.attachment` (`FileField`,
  `null=True, blank=True`) carries the form and serializer upload paths. The
  fakeshop `/graphql/` mount is the package's
  [`DjangoGraphQLView`][glossary-djangographqlview] with
  `multipart_uploads_enabled=True`.

## Goals

1. **Expose file/image output as structured objects.** The read converter returns
   [`DjangoFileType`][glossary-djangofiletype] /
   [`DjangoImageType`][glossary-djangoimagetype] via `FIELD_OUTPUT_TYPE_MAP` (kept off
   the shared `SCALAR_MAP` / filter-input path), so a client gets `name` / `size` /
   `url` (+ `width` / `height`) in one selection, and the server's absolute filesystem
   `path` only where a deployment opts the column into `Meta.filesystem_path_fields`
   ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)).
2. **Handle empty / unreadable files deliberately.** An absent file resolves the whole
   object to `null`; a storage property that cannot be produced degrades to a `null`
   subfield (guarded on the subfield resolver, not the parent) — never a
   `FieldFile.url` / `.path` exception surfacing as a request failure
   ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
3. **Re-export `Upload` from the package root** without registering it in
   `_PACKAGE_SCALAR_MAP`
   ([Decision 5](#decision-5--re-export-upload-rather-than-register-it)).
4. **Map `FileField` / `ImageField` to `Upload` on generated mutation inputs**, with
   the generic scalar-assignment path carrying the uploaded file
   ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).
5. **Keep read and write contracts distinct.** Output is an object type; input is
   `Upload`; neither side leaks the other's representation.
6. **Export `Upload` / `DjangoFileType` / `DjangoImageType` from the package root**
   ([Decision 7](#decision-7--public-surface-upload-djangofiletype-and-djangoimagetype-root-exported)).
7. **Close the `0.0.11` release**
   ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).

## Non-goals

- **Multipart transport helpers.** The [`TestClient`][glossary-testclient] owns
  multipart request building; this card ships the scalar it sends
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **A dedicated upload app.** The live file/image surface is `MediaSpecimen` on the
  existing `scalars` app, not a new fakeshop domain
  ([Decision 9](#decision-9--test-placement-the-live-tier-owns-the-fileimage-wire-contract)).
- **Nested writes / file-replacement policy beyond the direct field.** A provided
  value sets the field and an omitted value leaves it alone on partial update; no
  replace/delete semantics beyond that
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Storage abstraction / signed URLs / image processing.** The package exposes safe
  nullable subfields where storage properties may be unavailable and lets Django's
  storage object answer `url` / `size` (and the opted-in `path`)
  ([Edge cases](#edge-cases-and-constraints)).
- **`DurationField` / `BinaryField` and other unmapped scalars.** They stay absent
  from [`SCALAR_MAP`][types-converters] with their documented custom-scalar plugs.
- **A settings key or storage policy**
  ([Decision 8](#decision-8--no-setting-and-no-storage-policy-the-conversion-keys-on-the-column-type)).

## Borrowing posture

File/image mapping is **Required `strawberry-graphql-django` parity**, and
`graphene-django` provides a weaker form. *Behaviorally* the package copies
`strawberry-graphql-django`'s output shapes and `Upload` mapping; *surface-wise* it
keeps automatic `class Meta`-driven conversion (no decorator, no upload helper — a file
column is converted by the same `Meta.fields` / `Meta.exclude` selection as any
column). `graphene-django` maps `FileField` to a `String` output; the package follows
the richer Strawberry output object because the engine is Strawberry.

### Reference-package parity checkpoint

| Upstream | `django-strawberry-framework` | Status |
| --- | --- | --- |
| [`strawberry_django.fields.types.DjangoFileType`][upstream-field-types] (`name` / `path` / `size` / `url`) | [`DjangoFileType`][glossary-djangofiletype] public output type (`name` / `size` / `url`; `path` on the opt-in `DjangoFilePathType`); `FIELD_OUTPUT_TYPE_MAP[models.FileField]` read row ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)) | required parity (subfields widened nullable, `path` behind an opt-in, [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)) |
| [`strawberry_django.fields.types.DjangoImageType`][upstream-field-types] (file fields + dimensions) | [`DjangoImageType`][glossary-djangoimagetype] public output type; `FIELD_OUTPUT_TYPE_MAP[models.ImageField]` read row ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)) | required parity (subfields widened nullable, field-level guard, [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)) |
| [`strawberry_django` `input_field_type_map` maps file/image → `Upload`][upstream-field-types] | the [`mutations/inputs.py`][mutations-inputs] generator maps both to [`Upload`][glossary-upload-scalar] ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)) | required parity |
| `strawberry.file_uploads.scalars.Upload` | re-exported from the package root; resolves via Strawberry's built-in default registry — no `_PACKAGE_SCALAR_MAP` entry ([Decision 5](#decision-5--re-export-upload-rather-than-register-it)) | adopted upstream scalar; like upstream, relies on the built-in registry |
| `graphene_django.converter.convert_field_to_string` for `FileField` | rejected as too weak for this package's Strawberry output shape | deliberately not borrowed |

### From `strawberry-graphql-django` — borrow the output shapes and the input mapping

- **Output types.** `DjangoFileType` (`name` / `size` / `url`) and
  `DjangoImageType(DjangoFileType)` (+ `width` / `height`) — upstream's type names and
  field names, so a migrating consumer's `{ avatar { url width } }` selection ports
  unchanged. Two deliberate divergences: subfield nullability
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)),
  and the server's absolute filesystem `path`, which is not a default subfield — a
  deployment opts a column into it through `Meta.filesystem_path_fields`
  ([`spec-048`][spec-048]).
- **Input mapping.** `FileField` / `ImageField` → `Upload` on the mutation input;
  the empty-file / partial-update write semantics are the package's own
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).

### From `graphene-django` / DRF — borrow the user-facing shape

- **Automatic, `Meta`-driven conversion.** No `Upload` helper, no decorator, no
  per-field declaration — a file column is converted because it is in the type's
  `Meta.fields` selection, exactly as every other column.
- **Editable / `blank` / `null` / `default` metadata** drives whether an upload input
  is required (the DRF `required=False`-from-metadata rule the generator uses for
  every column).

### Explicitly do not borrow

- **A single flagged file type with an `is_image` runtime check.** Two distinct types
  (`DjangoFileType` / `DjangoImageType`) is the upstream shape, keeps dimension fields
  off non-image files, and the MRO walk selects the right one automatically.
- **A bespoke package-defined `Upload` scalar.** Strawberry ships `Upload`; re-using it
  keeps multipart parsing on the engine
  ([Decision 5](#decision-5--re-export-upload-rather-than-register-it)).
- **`graphene-django`'s `FileField` → `String` output.** Too weak.
- **Storage-backend abstraction / signed-URL generation.** Out of scope
  ([Non-goals](#non-goals)).

## User-facing API

No constructor argument — a file/image column is converted automatically by being in
the type's `Meta.fields` selection. The one file-specific `Meta` key on the read side
is the per-column `Meta.filesystem_path_fields` opt-in ([`spec-048`][spec-048]).

Read side — a `DjangoType` over a model with file/image columns:

```python
from django.db import models

from django_strawberry_framework import DjangoFileType, DjangoImageType, DjangoType, finalize_django_types


class Asset(models.Model):
    attachment = models.FileField(upload_to="files/")          # required column, but output is nullable by default
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
  attachment: DjangoFileType
  preview: DjangoImageType
}

type DjangoFileType {
  name: String!
  size: Int
  url: String
}

type DjangoImageType {
  name: String!
  size: Int
  url: String
  width: Int
  height: Int
}
```

Naming a column in `Meta.filesystem_path_fields` swaps it onto `DjangoFilePathType` /
`DjangoImagePathType`, which carry the same subfields plus `path: String` — the
server's absolute filesystem path, deployment metadata a client never needs to render
a file, and so opt-in per column rather than a default.

The object field is **nullable by default**, regardless of `null` / `blank`: the
generated parent resolver returns `None` for an empty / falsy `FieldFile`, and an
empty value is reachable even on a `null=False, blank=False` column (legacy rows,
direct `Model.objects.create()`, fixtures, and manual SQL all store `""`), so the SDL
must be nullable to represent it.
[`Meta.required_overrides`][glossary-metarequired-overrides] is the explicit opt-in
for a caller asserting a stronger non-empty contract (`DjangoFileType!`). `name` is
non-null for a present file; `size` / `url` / `width` / `height` (and the opted-in
`path`) are **nullable** because storage backends and corrupt/vanished rows can make
individual properties unavailable even when a file name exists
([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
A missing/empty file resolves the whole object as `null`, never a `FieldFile.url`
`ValueError`. A consumer who wants a `str` (name) shape keeps it with a concrete
annotation override (`attachment: str`), which bypasses generated field conversion
(`convert_field_output`) per
[Scalar field override semantics][glossary-scalar-field-override-semantics].

Write side — a [`DjangoMutation`][glossary-djangomutation] over the same model generates
an `Upload`-typed input field:

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

The per-field requiredness rule applies (a create-input field is required only when
the model field has no `default`, is not `null=True`, and is not `blank=True`);
partial inputs are all-optional `UNSET`. A provided upload is assigned through
Django's normal model-field path before `full_clean()` / `save()`; an omitted upload on
update leaves the current file untouched. An explicit `null` on a `null=False` file
column is a field-keyed `FieldError` (`"This field cannot be null."`), **not** a silent
clear ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).
The schema uses the package's standard `strawberry_config()` (required by `BigInt`);
`Upload` itself needs no binding — Strawberry resolves it from its built-in default
scalar registry:

```python
schema = strawberry.Schema(query=Query, mutation=Mutation, config=strawberry_config())
```

A real upload reaches the resolver only through a view that accepts GraphQL multipart
requests (`multipart_uploads_enabled=True` on the mounted view).

### Error shapes

- An unsupported field class with no supported ancestor raises
  [`ConfigurationError`][glossary-configurationerror] at type creation
  (`scalar_for_field`'s `Unsupported Django field type`); every `FileField` /
  `ImageField` subclass resolves through its ancestor.
- On write, a missing required `Upload` is rejected by GraphQL validation as a missing
  required input field; a model `full_clean()` failure — a declared field validator or
  a model-field / `constraints` violation — populates the
  [`FieldError` envelope][glossary-fielderror-envelope] keyed to the file field with a
  null object, not a top-level `GraphQLError` ([`spec-036`][spec-036] Decision 7). The
  generated `DjangoMutation` does **not** itself reject non-image bytes: Django's
  *model* `ImageField` runs model-field validation and any declared validators, **not**
  the image content sniffing `forms.ImageField` performs, so upload content validation
  is a model-validator concern on this flavor (the form flavor's `forms.ImageField`
  does sniff).
- Reading a populated file whose storage cannot produce a property (a non-filesystem
  `path`, a vanished file) degrades that **subfield** to `null` via the per-subfield
  guard ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability))
  — not a top-level error and not a swallowed resolver bug (the catch list is
  `ValueError` / `OSError` / `NotImplementedError`). `SuspiciousFileOperation` is not
  caught and is reported as an error.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file is `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md`, with its
`-terms.csv` and `-rationale.md` companions under `docs/SPECS/appx/`.

Rationale companion: [Decision 1][rationale-d1].

### Decision 2 — Card-scope boundary: file/image conversion only, not transport or storage abstraction

This card owns three related artifacts: (1) the `FileField` / `ImageField` output
object types; (2) the `Upload` re-export and the generated-input mapping; (3) the
`0.0.11` release wrap. It does **not** own multipart test helpers, a dedicated upload
app, remote-storage policies, image processing, or nested upload writes — each named
in [Non-goals](#non-goals) /
[Out of scope](#out-of-scope-explicitly-tracked-elsewhere).

Rationale companion: [Decision 2][rationale-d2].

### Decision 3 — Read-side output types: `DjangoFileType` / `DjangoImageType` mirroring upstream

[`types/converters.py`][types-converters] defines the file/image `@strawberry.type`
output types and the **read-output field-type map** that selects among them, kept
separate from [`SCALAR_MAP`][types-converters]:

- `DjangoFileType` — `name`, `size`, `url`, as **resolver-backed** Strawberry fields
  (Decision 4 explains why). Each resolver's `root` is the bound `FieldFile` the parent
  resolver returned, not an instance of the type.
- `DjangoImageType(DjangoFileType)` — adds `width`, `height`.
- `DjangoFilePathType` / `DjangoImagePathType` — the same subfields plus `path`,
  reached only by naming the column in `Meta.filesystem_path_fields`
  ([`spec-048`][spec-048] Decision 1 / Decision 2).
- `FIELD_OUTPUT_TYPE_MAP = {models.ImageField: DjangoImageType, models.FileField: DjangoFileType}`
  — the module-level map the **read** converter consults; *not* a `SCALAR_MAP` row.
  `FILESYSTEM_PATH_OUTPUT_TYPE_MAP` substitutes the path-bearing sibling, keyed on the
  already-resolved output type, so the MRO walk is never repeated.

**Why a separate map, not a `SCALAR_MAP` rewrite.**
[`SCALAR_MAP`][types-converters] is shared: the read path
([`convert_scalar`][types-converters]) *and* the **filter-input** path
([`filters/inputs.py`][filters-inputs] `_scalar_from_model_field`, which delegates to
[`scalar_for_field`][types-converters]) both walk it. If `SCALAR_MAP[models.FileField]`
returned `DjangoFileType`, a [`FilterSet`][glossary-filterset] input typed from a file
column would carry an **output** object as a GraphQL **input** — an invalid schema. So
`SCALAR_MAP[models.FileField]` / `[models.ImageField]` stay `str`, and the
output-object lookup lives in `FIELD_OUTPUT_TYPE_MAP`, owned by a dedicated read-only
wrapper.

**The read-side lookup is a thin wrapper, not an expansion of `convert_scalar`.**
[`convert_scalar`][types-converters] and [`scalar_for_field`][types-converters] stay
scalar-shaped. `convert_field_output(field, type_name, *, force_nullable=None, expose_filesystem_path=False)`
owns the `FIELD_OUTPUT_TYPE_MAP` lookup (through `_field_output_type_for`): for a
file/image column it returns the matching output object (nullable by default as
`<object> | None`, per
[Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)),
and otherwise delegates to `convert_scalar`. `expose_filesystem_path` carries the
per-column `Meta.filesystem_path_fields` opt-in and is read only inside the file
branch, so it can never change a scalar column's annotation.
[`types/base.py`][types-base] `_build_annotations` calls `convert_field_output` for
non-relation columns, so "scalar conversion" never emits an object type.

`ImageField` is a `FileField` subclass, so the MRO walk matters: it tests
`type(field).__mro__`, and `ImageField` appears in its own MRO *before* `FileField`, so
an `ImageField` (and a consumer `ImageField` subclass) resolves to `DjangoImageType`,
never falling through to `DjangoFileType`.

The map lookup alone is insufficient: a Django model attribute for a file column
returns a falsy `FieldFile` / `ImageFieldFile` even when no file is attached, and
reading `url` / `path` / `size` on it raises. So a generated **file-column read
resolver** is attached at `DjangoType` finalization in the **same phase as the
relation resolvers**: [`types/finalizer.py`][types-finalizer] calls
`_attach_file_resolvers` ([`types/resolvers.py`][types-resolvers]) inside the Phase-2
loop that runs `_attach_relation_resolvers` (the only place resolvers attach before
`strawberry.type(...)` freezes the class), immediately after the relation pass and
before interface injection. The parent resolver does object nullability only —
`value if value else None` — and Strawberry resolves the subfields off the returned
`FieldFile` through the output type's own **resolver-backed** fields (the per-subfield
guard, [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
The attachment **skips `definition.consumer_authored_fields`** (the override union —
annotation-only *and* assigned-`strawberry.field` overrides — that `_build_annotations`
honors, stored on [`DjangoTypeDefinition`][types-definition]). This skip is deliberately
**broader** than the relation pass's `consumer_assigned_relation_fields` (assigned
relation overrides only), so a consumer annotation *or* `strawberry.field` for a file
column — e.g. `attachment: str`
([Scalar field override semantics][glossary-scalar-field-override-semantics]) — keeps
its own shape and receives **no** generated resolver and no object type. Skipping only
assigned overrides would silently clobber an annotation opt-out.

The object-typed **read** output is a wire-format break from a `str` mapping,
recorded in the glossary alongside the
[`PositiveBigIntegerField → BigInt`][glossary-specialized-scalar-conversions]
precedent, with the consumer-annotation override (`attachment: str`) as the one-line
opt-out. The **filter** input shape for a file column is a scalar `str`.

Rationale companion: [Decision 3][rationale-d3].

### Decision 4 — Read-side resolution: empty file as `null` and storage-safe subfield nullability

Two layers, at two different levels:

- **Object-field nullability (parent level).** A file/image column maps to
  `DjangoFileType | None` **by default**, independent of `null` / `blank`. The
  generated parent resolver
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream))
  returns `None` for an empty / falsy `FieldFile`, and an empty value is reachable even
  on a `null=False, blank=False` column — Django stores `""` for "no file", and legacy
  rows, direct `Model.objects.create()`, fixtures, and manual SQL can all leave it empty
  (a `blank=False` column is a form-validation constraint, **not** a database non-empty
  invariant). A non-null SDL would turn that `None` into a
  `Cannot return null for non-nullable field` error, so the field is nullable to
  represent what the resolver can return. This composes with the
  [`Meta.nullable_overrides`][glossary-metanullable-overrides] /
  [`Meta.required_overrides`][glossary-metarequired-overrides] `force_nullable`
  tri-state — `required_overrides` (`force_nullable=False`) is the explicit opt-in to
  the stricter `DjangoFileType!` contract, for a consumer that guarantees a file is
  always present (the "contract, not data" caveat the override entry documents).
- **Subfield nullability (field level).** `size` / `url` (and `width` / `height` on
  images, and `path` on the opt-in path-bearing siblings) are **nullable**, while
  `name` stays non-null — a deliberate divergence from upstream's all-non-null
  subfields.

**The guard lives on the subfields, not the parent resolver.** The parent resolver
returns the bound `FieldFile`; Strawberry then resolves each *selected* subfield
**after** and **outside** the parent resolver — and those property reads are exactly
what raise on a non-filesystem backend (S3 `FieldFile.path` → `NotImplementedError`)
or a vanished file (`.size` → `OSError`; `.url` on local storage is string-built from
`MEDIA_URL` and does *not* raise). A `try/except` in the parent resolver cannot reach
them. So each nullable subfield resolver passes its one property read to
`_safe_file_attr(read)`, which runs the zero-argument callable and performs the
**narrow** catch (`ValueError` / `OSError` / `NotImplementedError` → `None`). Each
subfield owns its own guard, so selecting only `{ url }`, only `{ path }` on an
opted-in column, or several subfields each degrade **independently**. `name` is read
without the guard (`str(root)`, the stored name, always present whenever the object is
non-null). Unparseable image bytes reach the same nullable `width` / `height`
differently: Django answers the dimension read with `None` rather than raising, and the
nullable declaration carries it.

**Django path-safety exceptions are *not* silently nulled.** A corrupt or hostile
stored name can make storage raise `django.core.exceptions.SuspiciousFileOperation` —
a `SuspiciousOperation` subclass, **not** a `ValueError` / `OSError`, so the narrow
catch does not cover it. `_safe_file_attr` deliberately lets it propagate: a
path-traversal / escaped-name condition is a security signal that surfaces as a
reported error, not a `null` subfield.

Rationale companion: [Decision 4][rationale-d4].

### Decision 5 — Re-export `Upload` rather than register it

`Upload` is a Strawberry **built-in**: Strawberry registers `Upload: UploadDefinition`
in its `DEFAULT_SCALAR_REGISTRY`, and the schema converter seeds that registry into
every schema (`{**DEFAULT_SCALAR_REGISTRY}`) *before* merging any package `scalar_map`.
So an `Upload`-annotated field resolves in **any** schema — with or without
[`strawberry_config`][glossary-strawberry-config]. [`scalars.py`][scalars] therefore
only **re-exports** `Upload` and its `UploadDefinition` from
`strawberry.file_uploads.scalars` (both in its `__all__`), the package root
([`__init__.py`][init]) re-exports `Upload` alone, and the package adds **no**
`_PACKAGE_SCALAR_MAP` entry for it.

This is the deliberate contrast with [`BigInt`][glossary-bigint-scalar]:
`BigInt = NewType("BigInt", int)` is a package-custom scalar **absent** from
`DEFAULT_SCALAR_REGISTRY`, so it needs its `_PACKAGE_SCALAR_MAP` entry to resolve.
`Upload` shares BigInt's structural shape (a `NewType` paired with a `ScalarDefinition`)
but **not** its registration need.

Rationale companion: [Decision 5][rationale-d5].

### Decision 6 — Write-side input mapping: the mutation seam becomes `Upload`

`django_strawberry_framework/mutations/inputs.py::model_column_write_kind` classifies a
`FileField` / `ImageField` as `FILE`, and
`django_strawberry_framework/mutations/inputs.py::model_column_write_annotation` returns
`Upload` for that kind. The column then rides `build_mutation_input`'s scalar tail:
required per the per-field rule (a `blank=False` / `null=False` / no-default file column
is required in the create `<Model>Input`, optional with `strawberry.UNSET` otherwise and
in `<Model>PartialInput`), widened to `Upload | None` when not required. File/image
fields are **scalar** input fields for naming: the Python attribute is the model field
name (`attachment`, not `attachment_id`), and the GraphQL name follows the normal
camel-case converter. The generator owns requiredness, `UNSET`, partial-update
omission, `Meta.fields` / `Meta.exclude` narrowing, and the custom-input merge: a file
column whose attr a consumer [`Meta.input_class`][glossary-input-type-generation] /
`Meta.partial_input_class` supplies is skipped like any scalar, so the consumer's field
is honored. The form and serializer flavors type their model-backed file columns
through the same `model_column_write_kind` / `model_column_write_annotation` pair.

**No file-specific resolver code.** `_decode_relations`
([`mutations/resolvers.py`][mutations-resolvers]) routes `FILE` to the scalar handler,
which passes the value into `model(**attrs)` (create) / `setattr` (update) before
`full_clean()` / `save()`; Django's `FileField` descriptor accepts an `UploadedFile`
directly.

**Omittable is not nullable — explicit `null` is a field error, not a file clear.** A
non-required file column widens to `Upload | None` and may be **omitted**
(`strawberry.UNSET` → the stored file is left unchanged). The widening does **not**
make an explicit `null` a clear instruction. Because `FILE` rides the scalar handler,
`_explicit_null_error` returns a [`FieldError`][glossary-fielderror-envelope]
(`"This field cannot be null."`) for a provided `None` on a `null=False` file column —
including the `blank=True, null=False` shape, which `full_clean()` alone would let slip
to a `save()`-time `IntegrityError` — before any DB work. A `null=True` file column
accepts `None` as a value; clearing is otherwise out of scope
([Risks and open questions][rationale-risks]).

Rationale companion: [Decision 6][rationale-d6].

### Decision 7 — Public surface: `Upload`, `DjangoFileType` and `DjangoImageType` root-exported

[`__init__.py`][init] re-exports and lists in `__all__`: `Upload` (the scalar, from
[`scalars.py`][scalars]), `DjangoFileType` and `DjangoImageType` (from
[`types/converters.py`][types-converters]). The path-bearing siblings
`DjangoFilePathType` / `DjangoImagePathType` are root-exported beside them
([`spec-048`][spec-048]). Each has a [`docs/GLOSSARY.md`][glossary] entry and a
**Public exports** row.

Rationale companion: [Decision 7][rationale-d7].

### Decision 8 — No setting and no storage policy; the conversion keys on the column type

The conversion is driven by the column type and the existing selectors:
[`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] select
columns; [`Meta.nullable_overrides`][glossary-metanullable-overrides] /
[`Meta.required_overrides`][glossary-metarequired-overrides] override nullability;
consumer-authored overrides bypass generated conversion; and
[`Meta.filesystem_path_fields`][glossary-metafilesystem-path-fields]
([`spec-048`][spec-048] Decision 2) is the one file-specific `Meta` key, a per-column
output-shape opt-in that selects which output object a column resolves to. No
`DJANGO_STRAWBERRY_FRAMEWORK` setting is read, so there is no settings-read or
per-query validation overhead.

Should a future file/image feature need a setting, the standing line is the
[`RELAY_GLOBALID_STRATEGY`][types-relay] shape: [`conf.py`][conf] owns top-level
settings-dict normalization and reload wiring; a domain module owns key-specific
validation where it needs local domain concepts (avoiding import cycles); and any
setting that affects request behavior is **resolved / validated / stamped once at
schema build / finalization** — as [`types/relay.py`][types-relay] reads
`RELAY_GLOBALID_STRATEGY` and stamps `definition.effective_globalid_strategy`, which
per-query resolvers then read without re-reading the setting. A query-time settings
read is rejected.

Rationale companion: [Decision 8][rationale-d8].

### Decision 9 — Test placement: the live tier owns the file/image wire contract

A `FileField` / `ImageField` stores its relative name as `TEXT`, so it is
SQLite-reachable and the [`examples/fakeshop/test_query/README.md`][test-query-readme]
rule applies in full: a line a real fakeshop query reaches is covered over HTTP.

- **Live `/graphql/` tests** ([`test_uploads_api.py`][test-uploads-api], against
  `MediaSpecimen`) own the public contract: the default-nullable SDL (a *required*
  column renders nullable), no `path` on the default objects and its presence under
  `MediaSpecimenWithPathType`'s opt-in, populated subfields (incl. `width` / `height`
  from a real PNG), the empty-file object-`null` case, every degradation row (a
  backend whose `path` raises `NotImplementedError` nulls only `path`; a vanished file
  nulls `size`; unparseable image bytes null `width` / `height`; a
  `SuspiciousFileOperation` is reported, not nulled — storage faults injected with
  `override_settings(MEDIA_ROOT=...)` and a patched `FileSystemStorage.path`), the
  `Upload` input SDL, a **real multipart** create (and the form-flavor `ImageField`
  create), and the update path (omit keeps the file, a new upload replaces it,
  explicit `null` on the required file is a `FieldError`). The requests drive through
  the package [`TestClient`][glossary-testclient].
- **Package tests** own what a live request cannot express, reading real
  `MediaSpecimen` columns as fixtures: the converter seam
  ([`tests/types/test_converters.py`][test-types] — map rows, MRO precedence over a
  consumer `ImageField` subclass, which no fakeshop model declares, default
  nullability, the `force_nullable` compose, the filter-input pin), the `Meta` seam
  ([`tests/types/test_base.py`][test-types] — consumer overrides,
  `Meta.*_overrides` on file / image columns), the input generator
  ([`tests/mutations/test_inputs.py`][test-mutations]), scalar registration
  ([`tests/test_scalars.py`][test-scalars]) and the export identities
  ([`tests/base/test_init.py`][test-base-init]).

Rationale companion: [Decision 9][rationale-d9].

### Decision 10 — This card owns the final `0.0.11` version bump

`037` was the last card on the `0.0.11` patch line, so the `0.0.11` release closed with
it (the [`CHANGELOG.md`][changelog] `## [0.0.11]` heading). The release is
single-sourced in `__version__` in [`__init__.py`][init]
([`AGENTS.md`][agents] #"The release is single-sourced"); [`pyproject.toml`][pyproject]
derives its packaging metadata from it via `[tool.hatch.version]`.

Rationale companion: [Decision 10][rationale-d10].

## Implementation plan

| Slice | Files | Tests |
| --- | --- | --- |
| 1 — read output objects + `FIELD_OUTPUT_TYPE_MAP` + file-column resolver | [`types/converters.py`][types-converters] (resolver-backed `DjangoFileType` / `DjangoImageType`, `_safe_file_attr`, `FIELD_OUTPUT_TYPE_MAP`, `_field_output_type_for`, `convert_field_output`; `SCALAR_MAP` file rows stay `str`), [`types/base.py`][types-base] (`_build_annotations` calls `convert_field_output`), [`types/resolvers.py`][types-resolvers] (`_make_file_resolver`, `_attach_file_resolvers`), [`types/finalizer.py`][types-finalizer] (Phase-2 call passing `consumer_authored_fields`), [`pyproject.toml`][pyproject] (`pillow` in the `dev` dependency group) | [`tests/types/test_converters.py`][test-types], [`tests/types/test_base.py`][test-types] |
| 2 — `Upload` re-export + mutation input | [`scalars.py`][scalars] (re-export), [`mutations/inputs.py`][mutations-inputs] (`FILE` kind → `Upload`), [`mutations/resolvers.py`][mutations-resolvers] (`FILE` → scalar handler) | [`tests/test_scalars.py`][test-scalars], [`tests/mutations/test_inputs.py`][test-mutations] |
| 3 — public exports + coverage | [`__init__.py`][init] (three exports + `__all__`), the `scalars` app's `MediaSpecimen` + its types and mutations | [`tests/base/test_init.py`][test-base-init], [`test_uploads_api.py`][test-uploads-api] |
| 4 — docs + `0.0.11` release + card wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`README.md`][readme], [`GOAL.md`][goal], [`TODAY.md`][today], [`KANBAN.md`][kanban] | — |

## Edge cases and constraints

- **Empty file descriptor.** A `FieldFile` is falsy when no file name is stored; the
  generated output returns `None` for the whole field, so selecting
  `attachment { url }` on an empty file does not raise.
- **Empty value on a `null=False, blank=False` column.** File columns store `""` for
  "no file", reachable even when neither `null` nor `blank` is set. File/image output is
  therefore **nullable by default**, independent of `null` / `blank`, unless
  [`Meta.required_overrides`][glossary-metarequired-overrides] forces the stricter
  contract.
- **Nullability overrides on a file/image column.**
  [`Meta.required_overrides`][glossary-metarequired-overrides] on a file column is
  allowed, forcing the bare non-null object; the consumer owns the invariant, and an
  empty value then surfaces as Strawberry's ordinary non-null violation ("contract, not
  data"). [`Meta.nullable_overrides`][glossary-metanullable-overrides] on a file column
  is a redundant declaration the validator **accepts** and the annotation ignores. Both
  directions are pinned through the public `Meta` surface by
  `tests/types/test_base.py::test_meta_required_overrides_forces_non_null_file_output`,
  `tests/types/test_base.py::test_meta_required_overrides_forces_non_null_image_output`
  and `tests/types/test_base.py::test_meta_nullable_overrides_on_a_file_column_is_a_no_op`;
  the two `required_overrides` rows carry an un-overridden sibling file/image column in
  the same type as their control.
- **Storage without local `path`.** The absolute filesystem `path` is not a default
  subfield; on the opt-in `DjangoFilePathType` / `DjangoImagePathType` it is nullable,
  so a backend that cannot provide a filesystem path degrades that subfield to `null`.
- **Missing file in storage.** `size` / `width` / `height` read storage and are
  nullable, so a lookup failure degrades to a `null` subfield via the narrow catch
  (`ValueError` / `OSError` / `NotImplementedError`) on each subfield resolver.
- **Storage-metadata cost at list scale.** Resolving `size` (and sometimes `url` /
  `width` / `height`) asks Django storage for per-object metadata, which can hit a
  remote backend once per selected object and subfield. The subfields are
  selection-gated, but the optimizer **cannot** prefetch object-store metadata and file
  columns are not relation-planned. The package does **not** cache or batch storage
  calls; selecting file metadata over a large connection is a read-side cost the
  consumer weighs.
- **Path-safety errors are not nulled.**
  `django.core.exceptions.SuspiciousFileOperation` from a corrupt / hostile stored name
  is **not** caught by `_safe_file_attr` (it is a `SuspiciousOperation`, not a
  `ValueError` / `OSError`); it is reported as an error, by design
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
- **Image dimensions at read time.** `width` / `height` are nullable and are not forced
  to validate the image during schema resolution: unparseable bytes read as `None` from
  Django, and a storage failure on the read is guarded. A consumer using `ImageField`
  already has Pillow (Django requires it for the field); [`pyproject.toml`][pyproject]
  declares `pillow>=10.0.0` in the `dev` dependency group so the dimension rows run
  unconditionally.
- **Consumer scalar override.** A consumer annotation *or* `strawberry.field` on a
  file/image column lands in `consumer_authored_fields`, which the file-resolver
  attachment skips — so `attachment: str` bypasses both the `FIELD_OUTPUT_TYPE_MAP`
  output mapping and the generated resolver, like every other scalar override; on the
  write side, a consumer `Meta.input_class` field for a file column is honored via the
  merge override
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).
- **MRO precedence (`ImageField` is a `FileField`).** The MRO walk hits `ImageField`'s
  own row before `FileField`'s, so an `ImageField` (and a consumer subclass) resolves to
  `DjangoImageType`.
- **File-column filter input.** A filter input the package types from a file column's
  model field (`_scalar_from_model_field` → `scalar_for_field`) is a **scalar** `str`:
  the output-object mapping lives in `FIELD_OUTPUT_TYPE_MAP`, which `scalar_for_field`
  never reads. Such a filter compares the **stored file
  name string**, not file metadata (`url` / `size` / `width` / `height`). django-filter's
  own `Meta.fields` generation has no default filter for a `FileField` (an
  `AssertionError` under the default `unknown_field_behavior`; skipped under `WARN` /
  `IGNORE`).
- **Mutation partial update.** Omitted upload fields stay `UNSET` and leave the stored
  file unchanged; a provided upload replaces the file through Django's normal
  assignment path. An explicit `null` on a `null=False` file column is rejected with a
  field-keyed `FieldError` by `_explicit_null_error` (omittable ≠ nullable).
- **Multipart transport.** A real upload needs a view with
  `multipart_uploads_enabled=True`; the package's view-side upload bounds belong to
  [`DjangoGraphQLView`][glossary-djangographqlview], and the
  [`TestClient`][glossary-testclient] builds multipart requests for tests.
- **`Upload` resolves without extra config.** `Upload` is in Strawberry's built-in
  `DEFAULT_SCALAR_REGISTRY`, so an `Upload`-annotated field resolves in any schema,
  with or without `config=strawberry_config()`. The config factory is still required
  by the package-custom [`BigInt`][glossary-bigint-scalar] scalar.
- **`Meta` keys.** The file/image conversion is automatic from the column type and adds
  nothing to [`DEFERRED_META_KEYS`][types-base]; the one file-specific key in
  `ALLOWED_META_KEYS`, `filesystem_path_fields`, selects the output object for an
  opted-in column and changes no conversion rule stated here.

## Test plan

Placement follows the [`AGENTS.md`][agents] live-first rule and the two-tier split of
[Decision 9](#decision-9--test-placement-the-live-tier-owns-the-fileimage-wire-contract):
the public wire contract is earned over live `/graphql/` against the `scalars` app's
`MediaSpecimen`; the package trees keep the converter, `Meta` and generator seams,
reading the same real columns.

- **Converter / map tests** ([`tests/types/test_converters.py`][test-types]):
  `FileField` → `DjangoFileType`, `ImageField` → `DjangoImageType` via
  `FIELD_OUTPUT_TYPE_MAP`, MRO precedence (a consumer `ImageField` subclass), file/image
  output is `| None` by default across the required, `blank`-only and `null`-only
  columns, the `force_nullable` tri-state wins when passed to `convert_field_output`
  directly, the path-bearing sibling swap, and the filter-input pin —
  `scalar_for_field`, [`filters/inputs.py`][filters-inputs] `_scalar_from_model_field`
  and the [`SCALAR_MAP`][types-converters] rows are all `str`, never `DjangoFileType`.
  The pin is the package's delegation path rather than a materialized
  [`FilterSet`][glossary-filterset], because django-filter's auto `Meta.fields` filter
  for a bare `FileField` raises before package code runs.
- **`Meta`-level tests** ([`tests/types/test_base.py`][test-types]):
  `Meta.nullable_overrides` / `Meta.required_overrides` reach the file/image branch
  through the **public `Meta` surface** (the three rows named in
  [Edge cases](#edge-cases-and-constraints)); a consumer `attachment: str` annotation and
  a consumer-assigned resolver each get no generated resolver or object type, and an
  un-overridden file column does.
- **Mutation input tests** ([`tests/mutations/test_inputs.py`][test-mutations]): the
  `FILE` kind, `Upload` annotations for file and image columns, the optional-column
  `UNSET` default (`blank=True` and `null=True` arms), `Meta.fields` / `Meta.exclude`
  narrowing, and the custom-input merge skipping an overridden upload field.
- **Scalar config tests** ([`tests/test_scalars.py`][test-scalars]): `Upload` is
  Strawberry's object and importable from `scalars`; `strawberry_config().scalar_map`
  includes `BigInt` and not `Upload`; an `Upload`-typed field builds under a plain
  `StrawberryConfig`.
- **Public export tests** ([`tests/base/test_init.py`][test-base-init]): `__all__`
  includes `DjangoFileType` / `DjangoImageType` / `Upload`, and each resolves to its
  source definition by identity.
- **Live HTTP tests** ([`test_uploads_api.py`][test-uploads-api]): the rows listed in
  [Decision 9](#decision-9--test-placement-the-live-tier-owns-the-fileimage-wire-contract).
- **Cross-cutting.** The suite is green at the 100% coverage gate
  (`fail_under = 100`).

## Doc updates

- **GLOSSARY** ([`docs/GLOSSARY.md`][glossary]):
  [`Upload` scalar][glossary-upload-scalar] /
  [`DjangoFileType`][glossary-djangofiletype] /
  [`DjangoImageType`][glossary-djangoimagetype] carry the shipped contract (the output
  fields, the `Upload` re-export, empty-file → `null`, the nullable-subfield guard); the
  [Scalar field conversion][glossary-scalar-field-conversion] file/image row states the
  read / filter / input split; [Specialized scalar conversions][glossary-specialized-scalar-conversions]
  carries the file/image row and the read-side wire-format break; the three symbols are
  in **Public exports**, the **Index** and the **File / image uploads** browse-by-category
  row.
- **Package docs**: [`docs/README.md`][docs-readme] documents the structured read
  objects (and their default-nullable shape) and the `FileField` / `ImageField` →
  `Upload` input mapping; [`README.md`][readme]'s production-defaults bullet names the
  path-free file output; [`GOAL.md`][goal] criterion 6 names `Upload` for `FileField` /
  `ImageField`; [`TODAY.md`][today]'s scalars line names the structured file and image
  output and its criterion-6 row cites [`test_uploads_api.py`][test-uploads-api];
  [`docs/TREE.md`][tree] carries the
  [`scalars.py`][scalars] / [`types/converters.py`][types-converters] /
  [`types/resolvers.py`][types-resolvers] summary lines (rendered from the module
  docstrings).
- **Card**: [`KANBAN.md`][kanban] records [`DONE-037-0.0.11`][kanban] with its `SpecDoc`
  at this spec (kanban DB + re-render).

## Risks and open questions

Every question this card opened is answered by a Decision above; the open follow-ups
(clearing a file through mutation input, a file-filter contract, storage-metadata
batching) are recorded in the rationale companion under
[Risks and open questions][rationale-risks].

## Out of scope (explicitly tracked elsewhere)

- **Multipart request helper** — [`TestClient`][glossary-testclient] (card
  [`DONE-043-0.0.14`][kanban]).
- **Form-based mutations** ([`DjangoFormMutation`][glossary-djangoformmutation]) —
  `DONE-038-0.0.12`; a form's `forms.FileField` / `forms.ImageField` maps to `Upload`.
- **DRF serializer mutations** ([`SerializerMutation`][glossary-serializermutation]) —
  `DONE-039-0.0.13`; a serializer `FileField` maps to `Upload`.
- **The broader products/fakeshop activation** — [`TODO-BETA-066-0.1.5`][kanban]. The
  file/image surface's own live coverage is not part of it
  ([Decision 9](#decision-9--test-placement-the-live-tier-owns-the-fileimage-wire-contract)).
- **Field-level read gates** — `FieldSet` / per-field permission hooks; file-metadata
  permissions are not special-cased here.
- **Remote-storage adapters, thumbnailing, image validation, and signed-URL policies** —
  consumer/storage concerns beyond a model-field conversion card.

## Definition of done

**Spec + companion CSV**

1. `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` and its companions
   `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-terms.csv` and
   `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` exist;
   `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md`
   reports `OK: <N> terms`.

**Slice 1 — read output objects**

2. [`types/converters.py`][types-converters] defines `DjangoFileType` (`name` non-null;
   `size` / `url` nullable, **resolver-backed**; no default `path`) and
   `DjangoImageType(DjangoFileType)` (+ nullable `width` / `height`), and
   `FIELD_OUTPUT_TYPE_MAP` (`ImageField` → `DjangoImageType`, `FileField` →
   `DjangoFileType`) consulted by the read-only `convert_field_output` (called from
   [`types/base.py`][types-base] `_build_annotations`; `convert_scalar` /
   `scalar_for_field` stay scalar-only), **leaving** the shared
   [`SCALAR_MAP`][types-converters] file rows as `str`
   ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream));
   a file column resolves to `<object> | None` by default, the parent resolver returns
   `None` for an empty `FieldFile`, and each subfield's own `_safe_file_attr` guard
   degrades storage failures to `null`
   ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability));
   the file-resolver attachment in [`types/finalizer.py`][types-finalizer]'s Phase-2
   loop skips `consumer_authored_fields` (broader than the relation pass's
   `consumer_assigned_relation_fields`), so a consumer `attachment: str` override wins
   (no resolver, no object type); a package test pins that the filter-input scalar
   lookup over a file column yields `str`, not `DjangoFileType`.

**Slice 2 — write `Upload` input**

3. [`scalars.py`][scalars] re-exports `Upload` (no `_PACKAGE_SCALAR_MAP` entry)
   ([Decision 5](#decision-5--re-export-upload-rather-than-register-it));
   [`mutations/inputs.py`][mutations-inputs] maps `FileField` / `ImageField` to `Upload`
   (required per the per-field rule, `| None` when not required) and file columns take
   the [`Meta.input_class`][glossary-input-type-generation] merge override; the generic
   scalar-assignment path in [`mutations/resolvers.py`][mutations-resolvers] assigns the
   uploaded file before `full_clean()` / `save()` with no file-specific branch
   ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).

**Slice 3 — public exports + coverage**

4. [`__init__.py`][init] re-exports `Upload` / `DjangoFileType` / `DjangoImageType` and
   lists them in `__all__`
   ([Decision 7](#decision-7--public-surface-upload-djangofiletype-and-djangoimagetype-root-exported));
   [`tests/base/test_init.py`][test-base-init] pins them; the live tier and the package
   trees cover the read converter / resolver (incl. storage-failure → `null` subfield),
   the `Upload` re-export and resolution, and the write mapping
   ([Decision 9](#decision-9--test-placement-the-live-tier-owns-the-fileimage-wire-contract)).

**Cross-cutting — no regression**

5. The suite is green at the 100% coverage gate (`fail_under = 100`); `ruff format` +
   `ruff check` are clean; no non-file converter row changes.

**Slice 4 — docs + the `0.0.11` release + card wrap**

6. [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme] /
   [`README.md`][readme], [`GOAL.md`][goal] / [`TODAY.md`][today] and
   [`KANBAN.md`][kanban] carry the contract listed in [Doc updates](#doc-updates).
7. **The `0.0.11` release closes with this card**
   ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)), under the
   [`CHANGELOG.md`][changelog] `## [0.0.11]` heading.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[readme]: ../../README.md
[start]: ../../START.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-auto-typed-annotations]: ../GLOSSARY.md#auto-typed-annotations
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-djangofilepathtype]: ../GLOSSARY.md#djangofilepathtype
[glossary-djangofiletype]: ../GLOSSARY.md#djangofiletype
[glossary-djangoformmutation]: ../GLOSSARY.md#djangoformmutation
[glossary-djangographqlview]: ../GLOSSARY.md#djangographqlview
[glossary-djangoimagepathtype]: ../GLOSSARY.md#djangoimagepathtype
[glossary-djangoimagetype]: ../GLOSSARY.md#djangoimagetype
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: ../GLOSSARY.md#djangomutationfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: ../GLOSSARY.md#fielderror-envelope
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-input-type-generation]: ../GLOSSARY.md#input-type-generation
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metafilesystem-path-fields]: ../GLOSSARY.md#metafilesystem_path_fields
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metanullable-overrides]: ../GLOSSARY.md#metanullable_overrides
[glossary-metarequired-overrides]: ../GLOSSARY.md#metarequired_overrides
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[glossary-scalar-field-override-semantics]: ../GLOSSARY.md#scalar-field-override-semantics
[glossary-serializermutation]: ../GLOSSARY.md#serializermutation
[glossary-specialized-scalar-conversions]: ../GLOSSARY.md#specialized-scalar-conversions
[glossary-strawberry-config]: ../GLOSSARY.md#strawberry_config
[glossary-testclient]: ../GLOSSARY.md#testclient
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[rationale-d10]: appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md#decision-10--this-card-owns-the-final-0011-version-bump
[rationale-d1]: appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md#decision-2--card-scope-boundary-fileimage-conversion-only-not-transport-or-storage-abstraction
[rationale-d3]: appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream
[rationale-d4]: appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability
[rationale-d5]: appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md#decision-5--re-export-upload-rather-than-register-it
[rationale-d6]: appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload
[rationale-d7]: appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md#decision-7--public-surface-upload-djangofiletype-and-djangoimagetype-root-exported
[rationale-d8]: appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md#decision-8--no-setting-and-no-storage-policy-the-conversion-keys-on-the-column-type
[rationale-d9]: appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md#decision-9--test-placement-the-live-tier-owns-the-fileimage-wire-contract
[rationale-risks]: appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md#risks-and-open-questions
[spec-001]: spec-001-django_types-0_0_1.md
[spec-017]: spec-017-deferred_scalars-0_0_6.md
[spec-025]: spec-025-scalar_map_helper-0_0_7.md
[spec-026]: spec-026-scalar_conversion_fakeshop-0_0_7.md
[spec-036]: spec-036-mutations-0_0_11.md
[spec-037-rationale]: appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
[spec-048]: spec-048-secure_output_defaults-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[init]: ../../django_strawberry_framework/__init__.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[scalars]: ../../django_strawberry_framework/scalars.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-mutations]: ../../tests/mutations/
[test-scalars]: ../../tests/test_scalars.py
[test-types]: ../../tests/types/

<!-- examples/ -->
[test-query-readme]: ../../examples/fakeshop/test_query/README.md
[test-uploads-api]: ../../examples/fakeshop/test_query/test_uploads_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-field-types]: https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/fields/types.py
