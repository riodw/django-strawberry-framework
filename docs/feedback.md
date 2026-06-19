# Review feedback: spec-037 upload/file image mapping

Review target: [`docs/spec-037-upload_file_image_mapping-0_0_11.md`][spec-037].

Verdict: **do not implement the spec exactly as written yet.** The broad product
direction is right: structured read objects for file/image fields, `Upload` on
generated mutation inputs, no new consumer `Meta` key, and no fakeshop app churn.
The spec also correctly identifies the current repo state: read conversion still
maps file/image fields to `str`, the mutation input seam still raises for
file/image columns, `Upload` is not package-exported, and the patch version still
needs the final `0.0.11` cut.

The blockers are integration details. As written, the spec can leak output types
into filter inputs, cannot actually enforce its promised per-subfield storage
guard, and overstates the `Upload` scalar registration requirement.

## Findings

### P0 - `SCALAR_MAP` cannot safely become an output-object map without a filter-input split

The spec says to rewrite `SCALAR_MAP` from `FileField: str` /
`ImageField: str` to `DjangoFileType` / `DjangoImageType`. That is unsafe with
the current architecture because [`types.converters.scalar_for_field`][types-converters]
is shared by read-side `convert_scalar` **and** filter input conversion through
[`filters.inputs._scalar_from_model_field`][filters-inputs]. If `SCALAR_MAP`
starts returning `DjangoFileType` for a `FileField`, a `FilterSet` over a file
column can generate a GraphQL input field typed as an output object. That is an
invalid schema shape and a regression outside the stated file-output surface.

Recommended spec update: split the concepts before implementation. Keep a true
scalar map for scalar-valued inputs/filters and add a read-output field-type map
for object-valued file/image outputs, or add an explicit filter-side file/image
policy. The higher-quality fix is a small architectural split: `convert_scalar`
or a renamed read converter can consult a `FIELD_OUTPUT_TYPE_MAP` for
`FileField` / `ImageField`, while filter inputs continue to use scalar values
or fail loudly with a `ConfigurationError` for file filters until file filtering
has a deliberate contract. Add package tests for `FilterSet.Meta.fields` over a
synthetic `FileField` so this does not regress silently.

### P0 - The promised per-subfield storage guard is not implementable by the parent resolver alone

The spec says the generated file-column resolver returns `None` for an empty
`FieldFile` and otherwise returns the bound `FieldFile`, after which Strawberry
reads `name` / `path` / `size` / `url` / dimensions from it. That only solves
the empty-object case. It does **not** guard subfield access: Strawberry's
default resolver will still touch `FieldFile.path`, `.size`, `.url`, `.width`,
or `.height` later, outside the parent resolver, and those property accesses can
raise.

Recommended spec update: make the subfield safety mechanism explicit. Either
define `DjangoFileType` / `DjangoImageType` with resolver-backed Strawberry
fields that call a shared `_safe_file_attr(root, attr)` helper, or have the
parent resolver return a wrapper object whose properties perform the narrow
catch. The parent resolver should only decide object nullability (`not value`
→ `None`); the subfield resolver/wrapper should own `ValueError` / `OSError` /
storage `NotImplementedError` handling. Add tests that select only `url`,
only `path`, and multiple subfields, because each subfield must be guarded
independently.

### P1 - The `Upload` scalar registration rationale is inaccurate for the installed Strawberry version

The spec repeatedly says `Upload` is structurally identical to `BigInt` and
therefore must be added to `_PACKAGE_SCALAR_MAP`; it also says schemas without
`config=strawberry_config()` will not resolve `Upload`. I verified the installed
Strawberry package builds a schema containing `Upload` **without** the package
config factory. That makes the BigInt analogy too strong: `BigInt` is a
package-defined scalar that needs package registration; `Upload` is a
Strawberry-provided scalar that Strawberry already knows how to expose.

Recommended spec update: choose one contract and document it accurately. My
recommendation is to re-export Strawberry's `Upload` from the package root but
not claim package scalar-map registration is required. If the implementation
still adds `Upload` to `_PACKAGE_SCALAR_MAP` for consistency, describe it as a
package-pinning/centralization choice, not a resolver requirement, and be aware
that it creates a new collision case for `extra_scalar_map={Upload: ...}` that
does not exist today. Tests should pin the actual desired behavior, including
whether a generated upload schema works without `strawberry_config()`.

### P1 - The consumer override escape hatch needs exact resolver-skip wiring

The spec promises that a consumer annotation like `attachment: str` bypasses the
generated file mapping and the generated empty-file resolver. That is the right
contract, but the implementation plan only says "wired in `types/base.py` /
`types/resolvers.py`" and does not name the finalizer skip source. The registry
already stores `DjangoTypeDefinition.consumer_authored_fields`; the file
resolver attachment must skip those names, not only assigned
`strawberry.field(...)` overrides. Otherwise an annotation-only opt-out can be
silently clobbered by a generated resolver.

Recommended spec update: add a concrete finalizer step: attach generated
file-field resolvers in the same phase as relation resolvers, but skip
`definition.consumer_authored_fields` for scalar file/image fields. Add a test
where `attachment: str` is selected via `Meta.fields` and no generated resolver
or object type is installed for that field.

### P2 - The storage exception list should explicitly account for Django storage/path safety errors

The current catch list names `ValueError` / `OSError` / storage
`NotImplementedError`. That covers common empty/missing-file paths, but
filesystem-backed storage can also raise Django path-safety exceptions such as
`SuspiciousFileOperation` for corrupted or hostile stored names. The spec's own
goal is "corrupt/vanished rows degrade to nullable subfields, not GraphQL 500s";
the exception policy should explicitly decide whether those Django storage
exceptions degrade to `null` or remain top-level errors.

Recommended spec update: add a small "safe storage exceptions" helper or named
tuple in the spec and tests, and include a corrupted-name/path-traversal case.
If the decision is to let `SuspiciousFileOperation` propagate for security
visibility, document that exception as intentional rather than leaving it as an
accidental gap.

### P2 - The write-resolver production change may already be satisfied by the existing scalar path

The spec says [`mutations.resolvers`][mutations-resolvers] must assign a
provided `Upload` before `full_clean()` / `save()`. The existing create/update
pipeline already passes scalar attributes into `model(**attrs)` and
`setattr(instance, attr, value)` before validation. That likely handles
`UploadedFile` values without a dedicated file branch. A new special case should
only be added if tests prove the existing scalar assignment path fails.

Recommended spec update: reword Slice 2 from "add file assignment code" to
"verify the existing scalar assignment path handles `UploadedFile`; add a file
branch only for a tested gap." This keeps the implementation smaller and avoids
inventing a divergent write path for files.

### P2 - Test plan is missing the highest-risk regression points

The planned tests cover many direct file/image cases, but they miss the two
riskiest integration seams:

- filter input generation for a model `FileField` after the output-type mapping
  change;
- `Upload` behavior with and without `strawberry_config()`, so the docs do not
  assert a false config requirement.

Recommended spec update: add these to the Slice 1 / Slice 2 test plan. Also add
one override test that confirms `attachment: str` does not receive the generated
file resolver, and one subfield-isolation test where `path` fails but `url` or
`name` still resolves.

### P3 - The companion glossary CSV probably needs a few implementation terms

The spec uses `FieldFile`, `ImageFieldFile`, `SCALAR_MAP`, and `FilterSet` as
load-bearing implementation concepts, but the companion CSV only lists the
higher-level public concepts. A new developer implementing this card would need
the `FieldFile` and shared-converter/filter interaction vocabulary in front of
them.

Recommended spec update: add glossary coverage or at least CSV rows for
`FieldFile`, `SCALAR_MAP`, and `FilterSet` if those entries exist or are being
introduced. If `SCALAR_MAP` is split per the P0 finding, name the new output map
in the glossary/CSV as well.

## Proposed spec corrections before implementation

1. Replace the blanket "`SCALAR_MAP` rows become object types" instruction with
   an explicit read-output map vs scalar-input map design, or explicitly reject
   file/image filters with tests.
2. Define the subfield guard mechanism at the `DjangoFileType` /
   `DjangoImageType` field level, not only at the parent model-field resolver.
3. Correct the `Upload` registration section: Strawberry already resolves
   `Upload`; package registration is optional policy, not a technical
   requirement like `BigInt`.
4. Specify finalizer resolver attachment and skip behavior using
   `DjangoTypeDefinition.consumer_authored_fields`.
5. Add tests for filter generation, no-config upload schema behavior, subfield
   failure isolation, annotation-only override bypass, and the chosen
   Django-storage exception policy.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-037]: spec-037-upload_file_image_mapping-0_0_11.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filters-inputs]: ../django_strawberry_framework/filters/inputs.py
[mutations-resolvers]: ../django_strawberry_framework/mutations/resolvers.py
[types-converters]: ../django_strawberry_framework/types/converters.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
