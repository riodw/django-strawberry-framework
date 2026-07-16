# DRY review: `django_strawberry_framework/forms/converter.py`

Status: verified

## System trace

`forms/converter.py` owns the **model-less** Django `forms.Field` → Strawberry
annotation + decode-kind registry (spec-038 Decision 7):

- `convert_form_field` — fail-loud MRO dispatch over `_SCALAR_FORM_FIELDS` plus
  ordered relation / file / multi-choice / bare-`Field` prechecks; returns
  `FormFieldConversion` (`annotation`, `kind`, `required`).
- `form_field_required` — the single NullBoolean / column-backed requiredness
  rule shared with `forms/inputs.py` build + create-required discovery.
- Re-exports of `SCALAR` / `RELATION_*` / `FILE` from `utils/inputs.py` (A7).

The form-flavor reverse-map record `FormInputFieldSpec` **was** defined here;
this pass deletes it. The reverse map is now single-sited on
`utils/inputs.py::InputFieldSpec` (`target_name` = form field name), constructed
by `forms/inputs.py` — so this module owns only the kind constants +
`convert_form_field`.

Connected behavior examined:

- `forms/inputs.py` — sole production caller of `convert_form_field` (column-less
  arm only). Column-backed `ModelForm` fields route through read-side
  `convert_scalar` / `relation_input_annotation` / `Upload` keyed on
  `models.Field`. Both arms share `form_field_required` and emit
  `FormInputFieldSpec`.
- `forms/resolvers.py` — decode kind-split imports kind constants; keys form
  payloads by `spec.form_field_name`.
- `forms/sets.py` — bind-stashes the reverse-map list; does not convert.
- `utils/converters.py::convert_with_mro` — shared precheck → MRO → raise
  skeleton (already extracted with the serializer converter).
- `utils/inputs.py` — `FieldConversionBase`, decode-kind vocabulary,
  `InputFieldSpec` (the unified reverse map; the form path now constructs it with
  `target_name` = form field name, completing spec-039 D1's deferred migration).
- `rest_framework/serializer_converter.py` — parallel `serializers.Field`-keyed
  registry over the same skeleton; consumer `register_serializer_field_converter`
  and nested kinds are serializer-only.
- `types/converters.py` — `models.Field`-keyed read / column-backed write path;
  intentionally a different key space from this module.
- `filters/inputs.py::_scalar_from_form_field` — filter-input typing for
  django-filter form subclasses; looks similar, different contract (below).
- `scalars.py` — `Upload` finalized at the form build site, not in this table;
  JSON uses `strawberry.scalars.JSON` here.
- Tests — `tests/forms/test_converter.py` (unit registry / fail-loud /
  NullBoolean); `tests/forms/test_inputs.py` (build-site wiring including JSON /
  relation id types). Live form mutations under `examples/fakeshop/test_query/`
  exercise the converter only through generated inputs, not as a direct
  surface.

ITEM_BASELINE `e04fd8f79e01a741ff6475f9e14f92282744920e`:
`git diff … -- django_strawberry_framework/forms/converter.py` at review start was
empty; the accepted migration (owned by the `forms/inputs.py` item) now deletes
`FormInputFieldSpec` and its `from dataclasses import dataclass` import from this
file and repoints the module docstring at `utils/inputs.py::InputFieldSpec`.

## Verification

Searches: `convert_form_field`, `_SCALAR_FORM_FIELDS`, `form_field_required`,
`FormInputFieldSpec`, `_scalar_from_form_field`, `convert_with_mro`,
`FieldConversionBase`, `InputFieldSpec` across package + tests.

Scratch (`DJANGO_SETTINGS_MODULE=config.settings`, `PYTHONPATH=examples/fakeshop`):

| Input | `convert_form_field` | `_scalar_from_form_field` |
| --- | --- | --- |
| `NullBooleanField` | `bool \| None`, `required=False` | bare `bool` |
| `JSONField` | `strawberry.scalars.JSON` | `str` (catch-all) |
| custom `forms.Field` subclass | `ConfigurationError` | `str` (catch-all) |

Rejected / deferred candidates:

1. **`_scalar_from_form_field` ↔ `_SCALAR_FORM_FIELDS`** — same key type
   (`forms.Field`), but different responsibilities: mutation input is fail-loud
   + write decode kinds + `bool | None` NullBoolean; filter input is permissive
   isinstance chain with silent `str` fallthrough and outer `| None` for
   optionality. Unifying would either soften mutation fail-loud or harden
   filters incorrectly. This file owns the write table; filters own theirs.
2. **Serializer scalar table / `convert_serializer_field`** — parallel by design
   (DRF field classes, registerable converters, nested kinds). Shared mechanics
   already live in `convert_with_mro` + `FieldConversionBase` + kind constants.
   Further merge needs mode flags across key spaces.
3. **`types/converters.py` / `SCALAR_MAP`** — `models.Field` key space; column-
   backed form fields already reuse it at `forms/inputs.py`. This module’s
   table is only for column-less form fields. Not a parallel copy.
4. **`FormInputFieldSpec` → `InputFieldSpec`** — same reverse-map idea
   (`form_field_name` ≈ `target_name`). ACCEPTED and now done: the unified type
   is `utils/inputs.py::InputFieldSpec`, and the `forms/inputs.py` item drove the
   migration (construct `InputFieldSpec(target_name=…)`; unused `source` /
   `nested_specs` default `None`). This file is not the destination-type owner,
   so it only sheds the deleted `FormInputFieldSpec` definition + its `dataclass`
   import; the decision and cross-site edits live on the `forms/inputs.py` item.
5. **Fallthrough error factories (form vs serializer)** — parallel wording over
   different field APIs (`field` repr vs `field.field_name`); flavor-owned
   messages are correct.
6. **Empty `FormFieldConversion` subclass of `FieldConversionBase`** — naming /
   typing flavor marker; base already holds the shape.
7. **Missing `register_form_field_converter`** — asymmetry with the serializer
   register hook is a capability gap, not duplicated responsibility.

## Opportunities

None owned here — prior cross-flavor extractions (`convert_with_mro`, kind
vocabulary, `FieldConversionBase`) already sit at their true owners, and the
`FormInputFieldSpec` → `InputFieldSpec` unification (the one real reverse-map
duplication) is owned and driven by the `forms/inputs.py` item; this module only
sheds the deleted definition. Remaining lookalikes are intentional key-space or
contract boundaries.

## Judgment

`forms/converter.py` is the sole authoritative `forms.Field`-keyed, fail-loud
mutation-input converter. Callers already route column-backed fields through
the read-side `models.Field` converters. The only in-file change is shedding the
migrated-away `FormInputFieldSpec` definition (owned by the `forms/inputs.py`
item); no converter policy changed. Ready for Worker 2.

## Independent verification (Worker 2)

Scoped diff vs ITEM_BASELINE
`e04fd8f79e01a741ff6475f9e14f92282744920e` for
`django_strawberry_framework/forms/converter.py` is the `FormInputFieldSpec`
deletion + `dataclass` import removal + docstring repoint only, all driven by
the `forms/inputs.py` item's accepted migration (confirmed). No converter
policy edit.

Re-trace: sole production call of `convert_form_field` is
`forms/inputs.py` column-less arm; column-backed path uses
`convert_scalar` / `relation_input_annotation` / `Upload`.
`form_field_required` is the single requiredness site (converter + build +
create-required discovery). Kind constants already live in `utils/inputs.py`
and are re-exported here. Dispatch skeleton already lives in
`utils/converters.py::convert_with_mro`.

Challenged rejected candidates:

1. **Filters `_scalar_from_form_field`** — same `forms.Field` key type, different
   contract. Scratch: `NullBooleanField` → mutation `bool | None` /
   `required=False` vs filter bare `bool`; `JSONField` → `JSON` vs `str`;
   `MultipleChoiceField` → `list[str]` vs `str`; custom `forms.Field` subclass →
   `ConfigurationError` vs silent `str`. Unifying needs a fail-loud vs
   catch-all mode flag across write vs filter optionality. Reject stands.
2. **Serializer scalar table / `convert_serializer_field`** — parallel by design
   over DRF field classes (registerable converters, nested kinds,
   `DurationField`→`str` where form `DurationField` still fail-louds). Shared
   mechanics already extracted; further merge would couple key spaces. Reject
   stands.
3. **`FormInputFieldSpec` → `InputFieldSpec`** — shapes are mechanically
   compatible (`form_field_name` ↔ `target_name`, unused `source` /
   `nested_specs` stay `None`), and `utils/inputs.py::InputFieldSpec` docstring
   names itself the unified owner. ACCEPTED and landed by the `forms/inputs.py`
   item: it rewrote `forms/inputs.py` construction, `forms/resolvers.py`
   (`spec.target_name`), and form tests, and deleted `FormInputFieldSpec` here.
   Confirmed: zero remaining `FormInputFieldSpec` / `.form_field_name` references
   under `django_strawberry_framework/` or `examples/`. This file correctly
   contributes only the deletion, not the destination-type ownership.
4. **`types/converters.py` / empty `FormFieldConversion` / missing
   `register_form_field_converter` / fallthrough message factories** — key-space
   separation, flavor naming marker, capability gap, and flavor-owned wording
   respectively. None encode a duplicated responsibility this file owns twice.

Missed opportunities searched (imports, bypasses, duplicate policy, tests):
none that share contract + change axis with this module beyond the landed
`FormInputFieldSpec` deletion. Disposition: verified.
