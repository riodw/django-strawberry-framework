# Second-Pass Feedback

## Findings

1. **[P1] Converter tests still assert the pre-fix non-null file/image output.**
   [`tests/types/test_converters.py`][test-types-converters] still has direct
   mapping tests asserting `convert_field_output(field, "OwnerType") is
   DjangoFileType` / `is DjangoImageType` in
   `test_convert_field_output_filefield_to_djangofiletype`,
   `test_convert_field_output_imagefield_to_djangoimagetype`, and
   `test_field_output_map_mro_precedence_image_subclass_wins`. That contradicts
   the current implementation in
   [`types/converters.py`][types-converters]::convert_field_output, where unset
   `force_nullable` now returns `DjangoFileType | None` /
   `DjangoImageType | None` by default, and it also contradicts the newer
   `test_convert_field_output_file_image_nullable_by_default` test in the same
   file. This will fail as soon as the suite is run. Root fix: keep
   `_field_output_type_for(...) is DjangoFileType` / `DjangoImageType` for
   testing map identity, but change the `convert_field_output(...)` assertions in
   those three tests to the default nullable union. Leave the existing
   `force_nullable=False` assertion as the opt-in bare-object contract.

2. **[P2] The nullability-override scope still says scalar-only even though
   file/image output objects now participate.** The shipped code accepts
   `Meta.required_overrides = ("attachment",)` on a `FileField`: the validator in
   [`types/base.py`][types-base]::_validate_nullability_override_targets rejects
   relations but not file/image columns, and
   [`types/base.py`][types-base]::_build_annotations threads the same
   `force_nullable` tri-state into the file/image branch. That is now the
   documented spec-037 contract. However, the public relation-field
   `ConfigurationError` text still says "nullability overrides are scalar-only
   for now", `_build_annotations` comments still say the sets are validated
   scalar-only, and current docs in
   [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], and
   [`TODAY.md`][today] still describe `Meta.nullable_overrides` /
   `Meta.required_overrides` as scalar-only. Root fix: rename this scope to
   "non-relation model fields" or "column output fields" everywhere, and reserve
   "scalar-only" for the `convert_scalar` / `SCALAR_MAP` / filter-input path.

3. **[P3] Standing file/image docs do not fully carry the default-nullable
   object contract.** [`docs/spec-037-upload_file_image_mapping-0_0_11.md`][spec-037]
   and [`TODAY.md`][today] now say the output object itself is nullable by
   default independent of `null` / `blank`, with `required_overrides` as the
   explicit opt-in to `DjangoFileType!`. The broader current docs only partially
   say that: [`docs/GLOSSARY.md`][glossary] mentions empty / absent files
   resolving to `null`, while its scalar-conversion rows and
   `Meta.required_overrides` entry still do not name the default-nullable
   file/image object case; [`docs/README.md`][docs-readme], [`README.md`][readme],
   and the `0.0.11` file/image bullets in [`CHANGELOG.md`][changelog] likewise
   describe structured objects without explicitly stating that generated SDL is
   nullable by default regardless of the Django column. Root fix: add the same
   one-sentence contract to the current public summary rows; do not rewrite the
   older historical `0.0.9` changelog entry.

## Notes

I did not run pytest, per the repository instruction not to run it unless
explicitly asked. This pass was a static review of the latest source and docs
after the follow-up fixes.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[changelog]: ../CHANGELOG.md
[readme]: ../README.md
[today]: ../TODAY.md

<!-- docs/ -->

[docs-readme]: README.md
[glossary]: GLOSSARY.md
[spec-037]: spec-037-upload_file_image_mapping-0_0_11.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[types-base]: ../django_strawberry_framework/types/base.py
[types-converters]: ../django_strawberry_framework/types/converters.py

<!-- tests/ -->

[test-types-converters]: ../tests/types/test_converters.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
