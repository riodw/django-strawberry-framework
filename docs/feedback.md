# Critical review: spec-037 upload/file image mapping

Review target: [`docs/spec-037-upload_file_image_mapping-0_0_11.md`][spec-037].

Verdict: **revise before production implementation.** The updated spec has
absorbed the earlier major architecture concerns: it preserves `SCALAR_MAP` for
filter/scalar inputs, introduces a separate read-output map, puts the storage
guard on file-object subfields, treats `Upload` as Strawberry-owned rather than
package-registered, and avoids a new setting. Those are the right directions.

The remaining issues are narrower but still worth fixing before code lands.
Most are contract-precision problems: where the resolver hook actually belongs,
what model-driven mutations can honestly validate, how optional upload nulls
behave, and how synthetic file/image tests can be implemented without accidental
dependency or database churn.

## Findings

### P1 - `convert_scalar` becoming object-output aware blurs an existing abstraction

The spec keeps `SCALAR_MAP` scalar-only, but still says the read converter should
consult `FIELD_OUTPUT_TYPE_MAP` inside the same converter path that today is
named and documented as `convert_scalar`. That avoids the filter-input P0, but
it leaves a smaller architecture debt: a function named `convert_scalar` would
return `DjangoFileType` / `DjangoImageType`, which are output object types, not
scalars.

Recommended spec update: introduce a tiny read-side wrapper such as
`convert_field_output(field, type_name, *, force_nullable=None)` and call that
from `types/base.py::_build_annotations`. It can check `FIELD_OUTPUT_TYPE_MAP`
first, then delegate to `convert_scalar` for true scalar columns. Keep
`scalar_for_field` and `convert_scalar` scalar-shaped. This preserves the new
split without teaching future maintainers that "scalar conversion" may emit an
object type.

### P1 - The implementation plan omits the actual finalizer wiring file

The prose says file-column resolvers attach "in the same finalizer phase as the
relation resolvers," but the slice file list names `types/base.py` and
`types/resolvers.py`, not `types/finalizer.py`. In the current architecture,
`finalize_django_types()` is the only place relation resolvers are attached
before `strawberry.type(...)` freezes the class.

Recommended spec update: list [`types/finalizer.py`][types-finalizer] explicitly
in Slice 1. The finalizer call should pass
`definition.consumer_authored_fields`, not only
`definition.consumer_assigned_relation_fields`, so annotation-only overrides like
`attachment: str` are not clobbered.

### P1 - The spec over-promises model-level `ImageField` validation

The error-shape section says a `full_clean()` failure such as an `ImageField`
validator rejecting a non-image upload should become a `FieldError`. That is not
a safe model-driven promise. Django model `ImageField` does not provide the same
content validation as `forms.ImageField`; model `full_clean()` mainly runs model
field validation, custom validators, and constraints. The form/serializer cards
are the natural home for file-content validation.

Recommended spec update: reword the example. Promise that model validation
errors and custom validators surface through `FieldError`, but do not claim
generated `DjangoMutation` rejects arbitrary non-image bytes unless the model
declares a validator that does so. Move rich upload/content validation language
to the future `DjangoFormMutation` / serializer specs.

### P1 - Image dimension support needs a dependency/test strategy

The spec requires `DjangoImageType.width` / `height` and tests around image
dimensions, but this project currently does not declare Pillow in runtime or dev
dependencies. That matters because real image-dimension behavior depends on
Django's image stack and the Pillow-backed image file path.

Recommended spec update: choose one path before implementation:

- add Pillow as a dev/test dependency and use a tiny valid in-memory image in
  tests; or
- keep production fields nullable and unit-test the resolver logic with a
  lightweight object exposing `width` / `height`, leaving real image parsing out
  of scope.

Do not write tests that silently skip dimension coverage when Pillow is absent;
with `fail_under = 100`, skipped branches can hide missing behavior.

### P2 - Optional upload fields need explicit-null semantics stated

The spec says file/image inputs widen to `Upload | None` on `blank` / `null` and
all partial inputs are optional. That matches the existing generator pattern:
optional means the field may be omitted (`UNSET`). But in the current resolver
pipeline, an explicit `null` for a `null=False` scalar column is still an input
error, even if the field is optional because `blank=True` or has a default.

Recommended spec update: separate "omittable" from "nullable." For
`blank=True, null=False` file columns, generated GraphQL may accept `null`
because the optional-input machinery widens the annotation, but the resolver
should return a field error for explicit `null` unless the existing pipeline is
changed to coerce file clears to `""`. The spec currently hints that clearing is
out of scope; make that a concrete contract in Decision 6 and the test plan.

### P2 - Synthetic-model tests need a concrete table/storage fixture plan

The spec says package tests should use synthetic models with `FileField` /
`ImageField` and `tmp_path` storage. Converter-only tests can use unmanaged
models without tables, but resolver and mutation tests need real rows and real
storage side effects. The repo already has a pattern for this:
`managed = False` models plus `connection.schema_editor().create_model(...)`.

Recommended spec update: add the fixture shape explicitly. Use a unique
`app_label`, `managed = False`, manual `schema_editor` create/delete, and
`override_settings(MEDIA_ROOT=tmp_path)` or a field-level temp storage. This
keeps the tests local to `tests/` without migrations or fakeshop app churn.

### P2 - Storage-backed subfields can be expensive at list scale

The resolver-backed `path` / `size` / `url` fields are selection-gated, which is
good. Still, `size` and sometimes `url` can hit remote storage per row. The
optimizer cannot prefetch object-store metadata, and file columns are correctly
not relation-planned.

Recommended spec update: document this as a read-side performance caveat. The
contract should be: selecting metadata asks Django storage for metadata per
selected object/subfield; the framework guards storage-shaped failures, but it
does not cache or batch storage calls in this card.

### P2 - The settings-anchor question is not a spec-037 issue, but the rule should be explicit

The current 037 spec adds **no** setting and explicitly rejects a new setting
key. The setting-read concern instead matches the existing
`RELAY_GLOBALID_STRATEGY` design in [`types/relay.py`][types-relay]. That code
reads the setting during finalization, validates it with the same validator as
`Meta.globalid_strategy`, stamps `definition.effective_globalid_strategy`, and
does not re-read it per query. Under that shape, there is no meaningful query
runtime overhead, no repeated validation during execution, and no new request
thread-safety concern beyond the existing `conf.Settings` lazy-load contract.

The architectural line should be kept:

- [`conf.py`][conf] owns top-level settings-dict normalization and reload wiring.
- Domain modules own key-specific validation when validation needs local domain
  concepts and would otherwise create import cycles.
- Any setting that affects request behavior must be resolved/stamped at schema
  build/finalization time, not read repeatedly inside resolvers.

Recommended spec update: if a future spec mentions a settings read in
`types/relay.py`, state "finalization-time read and stamp" explicitly. If it
means query-time lazy evaluation, move the validation/stamping earlier; do not
validate settings during each query.

### P3 - Documentation DoD should avoid implying multipart support

The doc-update section mostly gets this right, but several completion bullets
still say "upload capability" broadly. Because multipart HTTP ergonomics belong
to the future `TestClient` card, the docs should consistently say this card
ships the scalar symbol and generated mutation field typing, not the test client
or a new fakeshop upload endpoint.

Recommended spec update: mirror the precise wording already present in the
better doc-update paragraph: "Upload scalar and generated file/image
mutation-field typing; full multipart HTTP test-client ergonomics remain
0.0.14."

## Proposed Spec Edits

1. Add a read-output conversion helper name rather than expanding
   `convert_scalar` to emit object types.
2. Add `types/finalizer.py` to Slice 1 files touched and specify the exact
   `consumer_authored_fields` skip.
3. Replace the non-image-upload validation example with a custom-validator or
   model-validation example.
4. Decide and document how image-dimension tests work without an implicit Pillow
   dependency.
5. State explicit-null behavior for optional upload fields, especially
   `blank=True, null=False`.
6. Specify the synthetic-model DB/storage fixture pattern.
7. Add the storage-metadata performance caveat.
8. Keep settings validation stamped at finalization; do not introduce query-time
   setting validation.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-037]: spec-037-upload_file_image_mapping-0_0_11.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../django_strawberry_framework/conf.py
[types-finalizer]: ../django_strawberry_framework/types/finalizer.py
[types-relay]: ../django_strawberry_framework/types/relay.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
