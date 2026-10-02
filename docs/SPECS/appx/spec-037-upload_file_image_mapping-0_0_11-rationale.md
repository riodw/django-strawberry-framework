# Rationale: spec-037 — Upload scalar and file / image field mapping (justifications and rejected alternatives)

Deliberative companion to [`spec-037-upload_file_image_mapping-0_0_11.md`][spec-037]. The
spec is the contract; this file holds why each Decision is shaped the way it is and the
alternatives it rejected. A reader looking for what the package *does* wants the spec.

## Decision 1 — Spec filename and canonical naming

[Spec decision.][spec-037-d1] The topic slug `upload_file_image_mapping` names **both**
halves of the card — the write-side `Upload` scalar *and* the read-side file/image
output objects. Rejected:

- **`upload_scalar` / `uploads`.** Narrows the name to the write half, while the
  read-side `DjangoFileType` / `DjangoImageType` change is equally the card's.
- **`files`.** Too vague; it does not name the `Upload` scalar.

## Decision 2 — Card-scope boundary: file/image conversion only, not transport or storage abstraction

[Spec decision.][spec-037-d2] The deliverable is a converter-table change, a
mutation-input mapping, and their tests and docs. Multipart request ergonomics belong to
the [`TestClient`][glossary-testclient], which depends on this card's scalar rather than
the reverse; keeping transport and storage policy out stops a file-upload transport
design from holding up the foundational mapping ([`START.md`][start] scope-creep rule).
Rejected:

- **Ship only the read side, write later.** The read and write halves describe one
  column type; splitting them leaves a half-mapped field type and a generated input that
  cannot cover a model with an editable file column.

## Decision 3 — Read-side output types: `DjangoFileType` / `DjangoImageType` mirroring upstream

[Spec decision.][spec-037-d3] Structured output is the read-side parity goal; mirroring
upstream's type and field names lets a migrating consumer's selection port unchanged. Two
distinct types keep dimension fields off non-image files. A separate output map keeps the
read change off the shared scalar / filter-input surface. The types live in
[`types/converters.py`][types-converters], beside the field-class mapping that selects
them, rather than in a new module. Rejected:

- **Put the object types directly in `SCALAR_MAP`.** A filter input typed from a file
  column would carry an output object as a GraphQL input — an invalid schema.
  `tests/types/test_converters.py::test_file_columns_stay_scalar_on_the_filter_input_path`
  pins the delegation path the filter-input generator uses (`scalar_for_field` and
  `_scalar_from_model_field` both return `str`, `SCALAR_MAP` rows stay `str`) rather than a
  materialized `FilterSet`, because django-filter raises an `AssertionError` on an
  auto-generated bare-`FileField` filter before any package code runs; the scalar-lookup
  pin is equally distinguishing.
- **Reject file/image filters with `ConfigurationError` and route reads through a renamed
  converter.** Cleaner once file filtering has a deliberate contract, but a behavior
  change for any consumer filtering on a file column's stored name. File columns keep
  their scalar `str` filter mapping ([Risks and open questions](#risks-and-open-questions)).
- **Keep `str` output and ship only `Upload`.** Leaves consumers hand-rolling file
  metadata.
- **Map output to `str | None` and document custom resolvers for metadata.** Preserves
  the weak contract and ignores the upstream parity target.
- **One `DjangoFileType` with nullable `width` / `height`.** A non-image `FileField` has
  no dimensions; the `DjangoImageType` subclass scopes them to images, matching upstream.
- **A settings flag to keep `str` globally.** A settings key for what a one-line
  per-field annotation override already does ([`AGENTS.md`][agents]: add settings keys
  only when the feature needs them); the override is finer-grained.

## Decision 4 — Read-side resolution: empty file as `null` and storage-safe subfield nullability

[Spec decision.][spec-037-d4] A file field with no file resolves to `null`, not an error;
a storage quirk on one property does not take down the query; and the guard sits where
the raising read happens (the subfield), which the parent resolver cannot reach. The
narrow catch list keeps the guard from swallowing genuine resolver bugs and from masking
security-relevant path errors. `name` is present whenever the object exists (the object
is `null` for an absent file), so it stays non-null. Rejected:

- **Guard only in the parent resolver (return the `FieldFile`, catch there).** Subfield
  reads happen later, in Strawberry's per-field resolution, outside the parent's
  `try/except`; a vanished-file selection of `{ size }` would still fail the request.
- **A wrapper object whose properties perform the catch.** Equivalent; resolver-backed
  `@strawberry.field`s on the two types are chosen because they keep the guard in the
  type definition and need no extra wrapper class.
- **Match upstream's all-non-null subfields and document the caveat.** Leaves a latent
  failure on non-filesystem storage and vanished files; the nullable-subfield SDL
  divergence is small and documented.
- **Widen the object on `field.null` only — or on `null` / `blank`.** The resolver returns
  `None` for *any* empty `FieldFile`, including on a `null=False, blank=False` column, so
  keying nullability on the column flags leaves a guaranteed non-null violation. The
  object is nullable by default; `required_overrides` is the explicit opt-in to non-null.
- **Catch a broad `Exception` (or fold `SuspiciousFileOperation` into the guard).** Hides
  real bugs and masks path-traversal signals; the catch list is narrowed to
  storage-shaped errors.

## Decision 5 — Re-export `Upload` rather than register it

[Spec decision.][spec-037-d5] Registering `Upload` in `_PACKAGE_SCALAR_MAP` would be
redundant (it already resolves) and misleading (it would imply a binding requirement that
does not exist). [`strawberry-graphql-django`][upstream-field-types] does the same: its
`input_field_type_map` maps `FileField` / `ImageField` to the bare `Upload` `NewType` with
no custom registration. Re-using Strawberry's scalar keeps multipart-request parsing on
the engine. Rejected:

- **Add `Upload` to `_PACKAGE_SCALAR_MAP` for symmetry with `BigInt`.** Redundant and
  misleading; it would also manufacture an `extra_scalar_map={Upload: ...}` collision
  contract for a scalar the package does not own.
- **A wrapper `NewType` instead of re-exporting Strawberry's `Upload`.** A second upload
  scalar would be incompatible with the engine's built-in multipart conventions and force
  clients to special-case it.
- **Do not export `Upload`; let consumers import it from Strawberry.** Generated inputs
  reference `Upload`, and a consumer hand-writing an upload field should find it at the
  package root beside [`BigInt`][glossary-bigint-scalar]
  ([Decision 7](#decision-7--public-surface-upload-djangofiletype-and-djangoimagetype-root-exported)).

## Decision 6 — Write-side input mapping: the mutation seam becomes `Upload`

[Spec decision.][spec-037-d6] Reusing the [`spec-036`][spec-036] input generator avoids a
second write-input path for uploads and keeps requiredness, narrowing and the
custom-input merge identical to every other scalar. Rejected:

- **Reject file columns and require `Meta.exclude`.** Makes generated mutation inputs
  unusable for any model with an editable file column.
- **Require a consumer-authored `input_class` for upload fields.** Defeats the
  generated-input goal and creates a bespoke escape hatch where the package should know
  the mapping.
- **Represent uploads as `str` paths.** Unsafe and not a GraphQL upload contract; the
  client sends multipart upload values, not server paths.
- **A dedicated file-assignment branch in the write resolver.** The scalar handler's
  `model(**attrs)` / `setattr` path already assigns an `UploadedFile`, and riding it is
  also what puts `_explicit_null_error` in front of a file column; a separate branch would
  be a divergent write path for files.

## Decision 7 — Public surface: `Upload`, `DjangoFileType` and `DjangoImageType` root-exported

[Spec decision.][spec-037-d7] Root export matches the audience: `Upload` is referenced
wherever a consumer hand-writes an input field, and the two output types are the field
types a consumer names in custom resolvers / `strawberry.field` annotations — all beside
[`BigInt`][glossary-bigint-scalar] / [`DjangoType`][glossary-djangotype], as
[`spec-017`][spec-017] root-exports `BigInt`. They are framework-provided output types,
not a decorator-first consumer API, so they stay within the package's `class Meta`-driven
posture ([`GOAL.md`][goal]). Rejected:

- **Export only from a `scalars` / `types` namespace.** The symbols are used in schema
  modules beside root-exported types; the package root-exports consumer-facing scalars and
  types.
- **Do not export the output types (auto-generated, never named).** A consumer overriding
  a file field's resolver, or annotating a computed file field, must be able to name them.

## Decision 8 — No setting and no storage policy; the conversion keys on the column type

[Spec decision.][spec-037-d8] Settings keys land only when a feature needs one
([`AGENTS.md`][agents]). The file/image mapping has no project-wide policy knob: the
scalar-override semantics already give the per-field escape hatch, and the one
file-specific choice, publishing the filesystem path, is a per-column `Meta` opt-in
([`spec-048`][spec-048]) rather than a global switch.

## Decision 9 — Test placement: the live tier owns the file/image wire contract

[Spec decision.][spec-037-d9] A file column is SQLite-reachable, so the live-first rule
([`examples/fakeshop/test_query/README.md`][test-query-readme]) puts every
consumer-visible row — SDL shapes, subfields, empty-file `null`, the degradation rows,
multipart create and update — on `/graphql/`. Storage faults are injectable live:
`override_settings(MEDIA_ROOT=...)` gives real temp-dir storage, a deleted file gives
the vanished case, raw bytes saved with `save=False` give the corrupt image, and a
patched `FileSystemStorage.path` gives the non-filesystem and `SuspiciousFileOperation`
cases. Rejected:

- **Synthetic file/image models in `tests/`.** `MediaSpecimen` carries every column shape
  the converter and generator branch on (required, `blank`-only, `null`-only, file and
  image), so a synthetic model would duplicate a fixture; the one shape no fakeshop model
  declares, a consumer `ImageField` subclass, stays a synthetic owner in
  `tests/types/test_converters.py`.
- **Mock the whole storage backend.** Real temp-dir storage exercises `FieldFile.path` /
  `.size` / `.url` honestly; only `path` is patched, for the two cases a local backend
  cannot produce.
- **A Pillow-conditional `skip` for the dimension rows.** Under `fail_under = 100` a
  conditional skip would let the gate pass over uncovered dimension branches; Pillow is a
  `dev`-group dependency instead (the package itself never imports it).

## Decision 10 — This card owns the final `0.0.11` version bump

[Spec decision.][spec-037-d10] `037` was the last card on the `0.0.11` patch line, so the
release closed with it; the version moves only after the mapping, tests and docs are
complete.

## Risks and open questions

Follow-ups this card leaves open, each a separate card if real users need it:

- **Clearing an existing file via mutation input.** An omitted upload leaves the file
  unchanged and a provided upload replaces it; an explicit `null` on a `null=False` file
  column is a field-keyed `FieldError` (`_explicit_null_error`), so it is never an
  accidental clear. No clear-file sentinel exists, and empty upload values are not
  overloaded as one.
- **File-column filtering contract.** File columns keep their scalar `str` filter mapping
  in `SCALAR_MAP` — a filter compares the stored **name** string, not file metadata
  (`url` / `size` / `width` / `height`). If string-filtering a file column proves
  meaningless, the alternative is rejecting file/image filters with a
  [`ConfigurationError`][glossary-configurationerror] once a deliberate file-filter
  contract is designed.
- **Storage-metadata read cost.** Selecting `size` / `url` / `width` / `height` asks
  Django storage for metadata per selected object and subfield; the package guards
  storage-shaped failures but does not cache or batch storage calls, and the optimizer
  cannot prefetch object-store metadata. A batching / caching layer is a follow-up if
  profiling shows it matters.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[goal]: ../../../GOAL.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary-bigint-scalar]: ../../GLOSSARY.md#bigint-scalar
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-djangotype]: ../../GLOSSARY.md#djangotype
[glossary-testclient]: ../../GLOSSARY.md#testclient

<!-- docs/SPECS/ -->
[spec-017]: ../spec-017-deferred_scalars-0_0_6.md
[spec-036]: ../spec-036-mutations-0_0_11.md
[spec-037-d10]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-10--this-card-owns-the-final-0011-version-bump
[spec-037-d1]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-1--spec-filename-and-canonical-naming
[spec-037-d2]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-2--card-scope-boundary-fileimage-conversion-only-not-transport-or-storage-abstraction
[spec-037-d3]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream
[spec-037-d4]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability
[spec-037-d5]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-5--re-export-upload-rather-than-register-it
[spec-037-d6]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload
[spec-037-d7]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-7--public-surface-upload-djangofiletype-and-djangoimagetype-root-exported
[spec-037-d8]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-8--no-setting-and-no-storage-policy-the-conversion-keys-on-the-column-type
[spec-037-d9]: ../spec-037-upload_file_image_mapping-0_0_11.md#decision-9--test-placement-the-live-tier-owns-the-fileimage-wire-contract
[spec-037]: ../spec-037-upload_file_image_mapping-0_0_11.md
[spec-048]: ../spec-048-secure_output_defaults-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[types-converters]: ../../../django_strawberry_framework/types/converters.py

<!-- tests/ -->

<!-- examples/ -->
[test-query-readme]: ../../../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-field-types]: https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/fields/types.py
