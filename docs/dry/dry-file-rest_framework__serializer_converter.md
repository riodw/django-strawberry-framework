# DRY review: `django_strawberry_framework/rest_framework/serializer_converter.py`

Status: verified

## System trace

`rest_framework/serializer_converter.py` owns the DRF `serializers.Field` →
Strawberry annotation + decode-kind registry (spec-039) and the per-field
resolve path that emits `utils/inputs.py::InputFieldSpec`:

- `convert_serializer_field` — fail-loud `convert_with_mro` dispatch over
  `_SERIALIZER_FIELD_CONVERTERS` plus ordered nested / relation / file / list /
  multi-choice prechecks; returns `SerializerFieldConversion`.
- `register_serializer_field_converter` — sanctioned consumer extension of the
  live registry (mutable module dict; not cleared by `registry.clear()`).
- Nested helpers — `is_nested_serializer_field`, `nested_serializer_child`,
  `_reject_nested_serializer` (opt-in-only nested writes; recursion owned by
  `inputs.py`).
- Relation / source policy — `_reject_unsupported_relation_field` (PK-only),
  `backing_model_field` (one-segment `source`), `_require_relation_primary`
  (M3 stricter than form/model fallback), `serializer_only_relation_annotation`.
- Naming / docs — `serializer_field_graphql_name` (id-like-suffix rule),
  `serializer_field_description` (help_text + constraint summary).
- Choice enums — `_SERIALIZER_CHOICE_ENUMS` cache + `clear_serializer_choice_enums`
  over shared `types/converters.py::build_enum_from_choices`.
- Type-override policy — `_model_backed_scalar_annotation` (rev6 #8) + consumer-
  declared choice override (rev6 rev2 P2).
- `resolve_serializer_field` — column-backed vs column-less resolve that builds
  the reverse-map `InputFieldSpec` (`target_name` = declared name, optional
  `source`).

Connected behavior examined:

- `forms/converter.py` — sibling `forms.Field`-keyed registry over the same
  `convert_with_mro` + `FieldConversionBase` + kind vocabulary; thinner (no
  resolve / register / nested / source / choice-enum cache). Verified zero-edit
  in its own item.
- `utils/converters.py::convert_with_mro` — already-extracted shared dispatch
  skeleton (spec-039 P1.4).
- `utils/inputs.py` — `FieldConversionBase`, decode kinds, `InputFieldSpec`
  (serializer reverse map including `source` / `nested_specs`).
- `types/converters.py` — `models.Field`-keyed `SCALAR_MAP` / `scalar_for_field`
  / `convert_scalar` / `build_enum_from_choices`; column-backed serializer
  scalars and `ModelField` already route here. Distinct key space.
- `mutations/inputs.py::relation_input_annotation` — model-backed relation id
  type + `<column>_id` attr; serializer model-backed relations call it after
  M3 primary check.
- `forms/inputs.py::_field_triple_and_spec` / `_model_less_relation_annotation`
  — parallel resolve ownership lives in the form *inputs* module; serializer
  keeps resolve in this converter (source / type-override / choice-enum tightly
  coupled). Concurrent dirty on `forms/inputs.py` — not edited.
- `rest_framework/inputs.py` — sole production caller of
  `resolve_serializer_field` / `serializer_field_description`; owns class
  generation, nested opt-in recursion, and a nested-path `source_attrs`
  reject parallel to `backing_model_field`. Concurrent dirty — not edited.
- `rest_framework/sets.py` / `resolvers.py` — nested child helpers + decode via
  bind-stashed specs; do not re-implement conversion.
- `scalars.py` — `Upload` finalized at resolve (file kind), not in the scalar
  registry.
- Tests — `tests/rest_framework/test_converter.py` (unit registry / fail-loud /
  source / choice / register / description); live serializer mutations under
  `examples/fakeshop/test_query/` exercise the converter only through generated
  inputs. Converter internals are not a live GraphQL surface.

ITEM_BASELINE `6ebb7f14f75878623ff901f22b976bbc6421cbf0`:
`git diff … -- django_strawberry_framework/rest_framework/serializer_converter.py`
is empty.

## Verification

Searches: `convert_serializer_field`, `convert_with_mro`, `FieldConversionBase`,
`register_serializer_field_converter`, `build_enum_from_choices`,
`serializer_field_graphql_name`, `backing_model_field`, `source_attrs`,
`serializer_only_relation_annotation`, `_model_less_relation_annotation`,
`relation_input_annotation`, `implements_relay_node`, `SCALAR_MAP`,
`_SCALAR_FORM_FIELDS` across package + tests.

Static audit (`export_dry_review.py audit --target …/serializer_converter.py
--stdout`) oriented importers / definition graph; findings reconciled against
behavior (not treated as a verdict).

Scratch (`DJANGO_SETTINGS_MODULE=config.settings`, `PYTHONPATH=examples/fakeshop`):

| Probe | Result |
| --- | --- |
| `DurationField` | serializer → `str` (forms table has no duration row) |
| `DictField` | serializer → `JSON` (forms N/A) |
| `NullBooleanField` | form → `bool \| None`, `required=False` (serializer has no twin) |
| custom `forms.Field` / `serializers.Field` | both `ConfigurationError` (no silent `String`) |
| id-like-suffix | `category`→`category_id`/`categoryId`; `category_id` keeps; `category_pk`→`categoryPk` |

Rejected / deferred candidates:

1. **Merge serializer scalar table with `forms/converter._SCALAR_FORM_FIELDS`** —
   parallel by design (DRF vs Django forms key spaces). Serializer stores
   converter callables (uniform with `ModelField` + consumer registration);
   forms store bare annotations and wrap after MRO. Capability matrix differs
   (`DictField` / `DurationField` / `IPAddressField` / `FilePathField` /
   `ModelField` vs `NullBooleanField` / bare `forms.Field` exact-type). Shared
   mechanics already live in `convert_with_mro` + `FieldConversionBase` + kinds.
   Further merge needs mode flags. Reject.
2. **Merge with `types/converters.SCALAR_MAP`** — `models.Field` key space;
   column-backed and `ModelField` paths already reuse `convert_scalar` /
   `scalar_for_field` / `build_enum_from_choices`. This module's table is only
   for DRF field classes (column-less + kind prechecks). Not a parallel copy.
   Reject.
3. **`serializer_only_relation_annotation` ↔
   `forms/inputs._model_less_relation_annotation`** — same Relay-vs-raw-pk
   *sub*-rule, different overall contracts: serializer requires a registered
   primary (M3), uses id-like-suffix naming, discovers related model via
   `queryset` / `child_relation.queryset`; form allows missing-primary → raw
   pk, always `f"{name}_id"`, uses `field.queryset`. Full merge rejected (also
   by forms + inputs DRY). Extracting only
   `relation_id_scalar(related_model, primary)` would touch concurrently dirty
   `forms/inputs.py` to migrate every site — incomplete migration worse than
   leaving the documented parallel. Defer to a forms-clean project pass.
4. **`resolve_serializer_field` → move into `rest_framework/inputs.py`** (mirror
   forms ownership where resolve lives in inputs) — architectural alignment,
   not duplicated responsibility. Resolve is tightly coupled to source /
   type-override / choice-enum owned here; move would reshuffle without
   removing a second implementation. Concurrent dirty on `inputs.py`. Defer to
   folder pass only if ownership clarity becomes an issue.
5. **Nested `source_attrs` reject in `inputs.py` ↔ `backing_model_field`** —
   same mechanical `len(source_attrs) != 1` check, different nouns / messages
   (nested write-back vs model column). True shared predicate could live here,
   but the second site is on concurrently dirty `inputs.py` and the nested path
   cannot call `backing_model_field` (no model column). Defer to folder pass.
6. **Fallthrough error factories (form vs serializer)** — parallel wording over
   different field APIs (`field` repr vs `field.field_name`); flavor-owned
   messages are correct. Reject.
7. **Empty `SerializerFieldConversion` subclass of `FieldConversionBase`** —
   naming / typing flavor marker; base already holds the shape. Reject.
8. **`_scalar_name` ↔ `inspect_django_type._scalar_name`** — diagnostic
   `__name__`/`repr` vs full SDL renderer; different contracts. Reject.
9. **Choice-enum cache ↔ `registry` model-choice cache** —
   `build_enum_from_choices` already single-sites build rules; key spaces
   (`enum_name` vs `(model, field_name)`) and the serializer name-collision
   guard are intentionally separate. Reject further merge.
10. **`serializer_field_description` ↔ form help_text** — serializer-only DRF
    metadata → SDL docs (rev6 #9); forms have no parallel constraint summary
    builder. Reject.
11. **Id-like-suffix rule → `utils/inputs`** — serializer-declared names can be
    `*_id` / `*_pk`; form fields are not named that way before remap. Promoting
    without a second consumer is premature. Reject.

## Opportunities

None — prior cross-flavor extractions (`convert_with_mro`, kind vocabulary,
`FieldConversionBase`, `InputFieldSpec`, `build_enum_from_choices`) already sit
at their true owners. Remaining lookalikes are intentional key-space or
contract boundaries; the strongest deferred items (narrow `relation_id_scalar`
helper; nested/`backing_model_field` `source_attrs` predicate) require
migrating concurrently dirty sibling files and belong to a forms-clean folder
or project pass, not this item alone.

## Judgment

`serializer_converter.py` is the sole authoritative `serializers.Field`-keyed,
fail-loud mutation-input converter and per-field resolve owner. Column-backed
fields already reuse the read-side `models.Field` converters and
`relation_input_annotation`; enum construction reuses `build_enum_from_choices`;
dispatch and conversion value-objects are already shared with the form flavor.
No source change is warranted; item-scoped diff remains empty. Ready for
Worker 2.

## Independent verification (Worker 2)

Re-traced ownership through `convert_serializer_field` / `resolve_serializer_field`,
callers in `rest_framework/inputs.py` + `resolvers.py`, siblings
`forms/converter.py` + `forms/inputs.py::_model_less_relation_annotation`,
shared `convert_with_mro` / `FieldConversionBase` / `build_enum_from_choices` /
`relation_input_annotation`, and unit + live-query test surfaces. ITEM_BASELINE
scoped diff for this file is empty (confirmed). Concurrent dirty on
`rest_framework/inputs.py`, `forms/inputs.py`, `utils/inputs.py`, and related
siblings left untouched.

Independent probes (`DJANGO_SETTINGS_MODULE=config.settings`,
`PYTHONPATH=examples/fakeshop`):

| Claim | Result |
| --- | --- |
| `DurationField` / `DictField` serializer-only | `str` / `JSON` |
| `NullBooleanField` form-only | `bool \| None`, `required=False` |
| unregistered custom ser/form field | both `ConfigurationError` |
| bare `forms.Field` | `str` (exact-type; no serializer twin) |
| id-like-suffix | `category`→`category_id`/`categoryId`; `category_id` keeps; `category_pk`→`categoryPk` |
| M3 vs form fallback | serializer raises without registered primary; form → `cat_id` + raw `int` |

Disposition of Worker 1 candidates:

1. Merge scalar tables with forms / `SCALAR_MAP` — **reject upheld** (distinct key
   spaces + capability matrix; shared mechanics already extracted).
2. Full merge `serializer_only_relation_annotation` ↔
   `_model_less_relation_annotation` — **reject upheld** (M3 vs raw-pk fallback,
   naming, queryset discovery). Aligns with verified forms/inputs DRY.
3. Narrow `relation_id_scalar` extract — **defer upheld** (would require migrating
   concurrently dirty `forms/inputs.py`; incomplete migration worse than
   documented parallel). Folder/project pass when forms are clean.
4. Move `resolve_serializer_field` into `inputs.py` — **defer upheld**
   (ownership reshuffle, not a second implementation; `inputs.py` dirty).
5. Shared `source_attrs != 1` predicate with nested reject in `inputs.py` —
   **defer upheld** (same mechanical check, different nouns/messages; second
   site on dirty `inputs.py`; nested path cannot call `backing_model_field`).
6. Fallthrough factories / empty `SerializerFieldConversion` /
   `_scalar_name` vs inspect / choice-enum caches / description / id-like-suffix
   promotion — **reject upheld** (flavor messages, typing marker, SDL vs
   diagnostic naming, separate key spaces, serializer-only metadata, no second
   consumer).

No missed production bypass of the registry (sole callers are
`rest_framework/inputs.py` for resolve/description/nested helpers;
`resolvers.py` only uses `nested_serializer_child`). No source change required.

Verdict: zero-edit verified.
