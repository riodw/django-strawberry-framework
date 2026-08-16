# DRY review: `django_strawberry_framework/types/converters.py`

Status: verified

## System trace

This module owns Django **model-field → Strawberry read-output** conversion and
the shared pieces write/filter paths must reuse for wire symmetry:

| Surface | Role |
| --- | --- |
| `SCALAR_MAP` + `scalar_for_field` | `models.Field` class → scalar; MRO walk; mutable extension hook |
| `convert_scalar` | Scalar + choice enum + `force_nullable` widening; ArrayField / HStoreField |
| `FIELD_OUTPUT_TYPE_MAP` + `_field_output_type_for` + `convert_field_output` | Read-only file/image object routing (kept off the scalar/filter path) |
| `DjangoFileType` / `DjangoImageType` (+ path siblings) + `_safe_file_attr` | Structured file read-output + storage-failure guard |
| `build_enum_from_choices` / `convert_choices_to_enum` | Choices → Strawberry enum (build core + model-keyed registry cache) |
| `resolved_relation_annotation` | Read-side relation annotation from `FieldMeta` (list / nullable / bare) |

Call / reuse graph (evidence only; siblings not absorbed):

- **Read orchestration:** `types/base.py::_build_annotations` →
  `convert_field_output` (non-relations); `types/finalizer.py` →
  `resolved_relation_annotation`; `types/resolvers.py::_attach_file_resolvers`
  → `_field_output_type_for` (same map walk as annotations).
- **Shared scalar / enum:** `filters/inputs.py::_scalar_from_model_field` /
  `_choice_enum_from_filter` → `scalar_for_field` / `convert_choices_to_enum`
  (local imports for cycle safety). Model-backed form / mutation / serializer
  inputs call `convert_scalar(..., force_nullable=False)` so choice enums match
  the read `DjangoType`.
- **Enum build core:** `rest_framework/serializer_converter.py` →
  `build_enum_from_choices` for serializer-only `ChoiceField` (separate
  name-keyed cache; same sanitization / grouped-form / collision rules).
- **Write-side registries (different key spaces):** `forms/converter.py`
  (`forms.Field` + `utils/converters.convert_with_mro`) and
  `rest_framework/serializer_converter.py` (`serializers.Field`). Model-backed
  columns still re-enter this module; model-less fields never do.
- **Scalars vs maps:** `scalars.py` owns `BigInt` / `Upload` definitions and
  `_PACKAGE_SCALAR_MAP` for schema config. This module maps field classes *to*
  those scalars (`BigInt` in `SCALAR_MAP`; `Upload` only on write build sites).
- **Inspect:** `management/commands/inspect_django_type.py` names which map /
  converter fired; does not own a second policy.

Item-scoped baseline
`d416f6f841f7d2342693c07de02ef968225d4deb`:
`git diff … -- django_strawberry_framework/types/converters.py` empty at review
start; no production edits in this item.

## Verification

Searches (package-wide): `SCALAR_MAP`, `FIELD_OUTPUT_TYPE_MAP`,
`FILESYSTEM_PATH_OUTPUT_TYPE_MAP`, `convert_field_output`, `convert_scalar`,
`scalar_for_field`, `build_enum_from_choices`, `convert_choices_to_enum`,
`_sanitize_member_name`, `_safe_file_attr`, `DjangoFileType` / `DjangoImageType`,
`__mro__` walks, `| None if` / `force_nullable` widening, `Upload` / file
branches in forms + serializer converters.

Optional `export_dry_review.py audit --target …/types/converters.py`: confirms
definitions and reverse imports; used as orientation only.

Contract comparisons that disproved consolidation:

1. **Three file representations** — `SCALAR_MAP[FileField/ImageField] = str`
   (filter / shared scalar), `FIELD_OUTPUT_TYPE_MAP` →
   `DjangoFileType`/`DjangoImageType` (read object), write sites → `Upload`.
   Docstring and map comments encode the split (spec-037). Merging would leak
   output objects into inputs or flatten read files back to `str`.

2. **Three scalar registries** — `SCALAR_MAP` (`models.Field`),
   `_SCALAR_FORM_FIELDS` (`forms.Field`), `_SERIALIZER_FIELD_CONVERTERS`
   (`serializers.Field`). Same *idea* (class → annotation), different class
   hierarchies, requiredness rules, and extension hooks. Form/serializer
   docs state they are not parallel copies of the read table; model-backed
   paths already call into this module.

3. **MRO walk idiom** — `scalar_for_field` (raise on miss),
   `_field_output_type_for` (None on miss), `utils/converters.convert_with_mro`
   (isinstance prechecks + raise). Same loop shape; different miss semantics
   and write-side precheck contract. Routing read lookups through
   `convert_with_mro` would add empty prechecks and blunt the tailored
   `ConfigurationError` text. A micro `_mro_lookup` helper would shrink two
   three-line loops without a shared change axis.

4. **Null widening defaults** — `convert_scalar`: default follows `field.null`.
   `convert_field_output` file branch: default always nullable (empty
   `FieldFile` → `None` even on `null=False`). Same `force_nullable` tri-state
   API, intentionally different defaults; unifying would need a mode flag.

5. **`resolved_relation_annotation` vs `relation_input_annotation`** — Read:
   `list[T]` / `T | None` / `T` from `FieldMeta`. Write (`mutations/inputs.py`):
   `GlobalID`/pk naming and attr remaps. Cardinality source (`FieldMeta` /
   `is_many_side`) is already shared; annotation *shape* must stay separate.

6. **Filter form-field fallback** — `filters/inputs.py` isinstance chain over
   django-filter *form* fields when `model_field is None` (method filters). Not
   a second `SCALAR_MAP`; model-backed path already delegates to
   `scalar_for_field`.

7. **`DurationField` / `BinaryField`** — Absent from default `SCALAR_MAP`
   (consumer registration). Serializer maps `DurationField` → `str`. Different
   key spaces; not drift.

Already single-sited (no further work): enum build/sanitize core; file storage
guard + path mixin; `_field_output_type_for` shared with resolvers; filter/
form/mutation/serializer reuse of `scalar_for_field` / `convert_scalar` /
`convert_choices_to_enum` / `build_enum_from_choices`.

## Opportunities

None — present-day ownership already places each invariant once. Apparent
duplicates are intentional read-output vs filter-scalar vs write-input
boundaries, or shared callers of this module's APIs. Strongest rejected
candidates are in Verification (1)–(4).

## Judgment

Zero-edit. `types/converters.py` is the true owner of model-field read
conversion, shared scalar/enum lookup, and file read-output types. Parallel
maps and MRO walks elsewhere encode different field-class spaces or different
null/miss contracts and should not be collapsed. Ready for Worker 2.

**Scoped diff statement:** relative to item baseline
`d416f6f841f7d2342693c07de02ef968225d4deb`, only this artifact is added
(`docs/dry/dry-file-types__converters.md`). No edits under
`django_strawberry_framework/`. Plan checkbox left for Worker 2.

**Deferred pytest:** none (no production change). No permanent tests added.

## Independent verification (Worker 2)

**Scoped diff:**
`git diff d416f6f841f7d2342693c07de02ef968225d4deb -- django_strawberry_framework/types/converters.py`
empty (726 lines match baseline). Zero-edit claim holds for production.

**Re-trace:** Read complete `types/converters.py`; followed `convert_field_output` /
`scalar_for_field` / `convert_scalar` / `build_enum_from_choices` /
`_field_output_type_for` / `_safe_file_attr` into `types/base.py`,
`types/resolvers.py`, `types/finalizer.py`, `filters/inputs.py`,
`forms/converter.py` + `forms/inputs.py`, `mutations/inputs.py`,
`rest_framework/serializer_converter.py`, `utils/converters.py`,
`scalars.py`, `inspect_django_type.py`. Independently grepped the same
symbol set plus `__mro__` walks and Upload/file branches.

**Challenged rejected candidates (source evidence):**

1. **FileField three ways** — Confirmed intentional. `SCALAR_MAP` keeps
   `FileField`/`ImageField` → `str`; `FIELD_OUTPUT_TYPE_MAP` →
   `DjangoFileType`/`DjangoImageType`; write build sites assign `Upload`
   (`mutations/inputs.py`, `forms/inputs.py`,
   `serializer_converter.py`) and never re-enter `convert_field_output`.
   Merging would leak output objects into inputs or flatten read files.

2. **Three scalar registries** — `_SCALAR_FORM_FIELDS` keys `forms.Field`;
   `_SERIALIZER_FIELD_CONVERTERS` keys `serializers.Field`; both ride
   `convert_with_mro` with isinstance prechecks. Model-backed write paths
   already call `convert_scalar` / `scalar_for_field` /
   `build_enum_from_choices`. Different hierarchies and miss/requiredness
   contracts.

3. **MRO idiom** — `scalar_for_field` raises `ConfigurationError`;
   `_field_output_type_for` returns `None`; `convert_with_mro` adds
   prechecks then raises via caller factory. Same loop shape, different
   miss semantics. A shared `_mro_lookup` would not own a shared change axis.

4. **Null defaults** — `convert_scalar` defaults from `field.null`;
   `convert_field_output` file branch defaults always-nullable
   (`file_effective_null = True if force_nullable is None else …`) to match
   empty-`FieldFile` → `None` resolvers. Same tri-state API, different
   defaults; unifying needs a mode flag.

5. **Write-site `Upload` isinstance ×3** — Independently considered as a
   missed consolidation (model `FileField`/`ImageField` → `Upload` in
   mutations / forms / serializer build sites). Rejected: each site wraps
   flavor-specific naming, kind, and requiredness; the shared rule is
   deliberately *not* in this module so `Upload` cannot enter
   `SCALAR_MAP` / filter inputs. A one-line helper would only shrink
   isinstance checks.

6. **Filter form-field fallback** — `_scalar_from_form_field` soft-falls to
   `str` and maps `NullBooleanField` → `bool`; form converter raises and
   maps `NullBooleanField` → `bool | None`. Not a second `SCALAR_MAP`.

**Already single-sited (confirmed):** enum sanitize/build core; file storage
guard + `_FileSystemPathFields` mixin; `_field_output_type_for` shared with
resolvers; filter/form/mutation/serializer reuse of scalar/enum APIs.

**Missed consolidations:** none found. Zero-edit verified.
