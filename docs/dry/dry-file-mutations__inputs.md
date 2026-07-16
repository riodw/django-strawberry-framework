# DRY review: `django_strawberry_framework/mutations/inputs.py`

Status: verified

## System trace

`mutations/inputs.py` owns the model write-input generation substrate (spec-036
Slice 1): editable-column selection, create/partial requiredness, relation /
Upload / scalar annotation mapping, shape identity + naming, namespace
materialize/clear, the public `FieldError` envelope, and the shared
`<Name>Payload` builder.

Public / bind-facing surface:

- namespace lifecycle — `INPUTS_MODULE_PATH`, `materialize_mutation_input_class`,
  `clear_mutation_input_namespace` (via `make_input_namespace`); registered
  `mutations.input_namespace` pre-bind clear; post-merge GraphQL-name audit in
  `_audit_mutation_input_surface`
- kind vocabulary — `CREATE` / `PARTIAL`, `NON_FIELD_ERROR_KEY`
- selection + requiredness — `editable_input_fields`, `input_field_required`
- relation / scalar mapping — `relation_input_annotation`,
  `_scalar_input_annotation` (Upload branch in `build_mutation_input`)
- shape + naming — `MutationInputShape`, `mutation_input_shape`,
  `mutation_input_type_name` (token via `pascalize_token`)
- builders — `build_mutation_input`, `build_payload_type`, `payload_object_slot`
- public envelope — `FieldError` (package-root re-export)

Connected behavior examined:

- `mutations/sets.py` — bind cache / merge path / `DjangoMutation.input_type_name`
  seam (lazy `data:` name); Meta validation walks `editable_input_fields`
- `mutations/fields.py` — consumes the overridable `input_type_name` seam only
  (fields DRY already forwarded seam-vs-shape here)
- `mutations/resolvers.py` — `FieldError`, `payload_object_slot`
- `forms/inputs.py` / `rest_framework/inputs.py` — sibling generators; reuse
  `CREATE` / `PARTIAL`, `relation_input_annotation`, `build_payload_type`;
  already on `InputFieldSpec` / `guard_dropped_required` / `resolve_effective_fields`
- `utils/inputs.py` — materialize/build/optional/collision/name spine
- `auth/mutations.py` — pins `RegisterInput` via `mutation_input_shape` +
  `_replace(type_name=...)`; overrides the name seam to a fixed string
- tests — `tests/mutations/test_inputs.py` (generator); live model mutations under
  `examples/fakeshop/test_query/` (wire / `FieldError`); seam↔shape contract is
  package-internal (not earnable via live GraphQL)

ITEM_BASELINE `2eb34db605c9800edf9eeadacd78ac8493172bf0`: target unmodified at
review start; post-implementation item-scoped diffs cover the sites below.

## Verification

Searches: `mutation_input_shape`, `MutationInputShape`, `input_type_name`,
`mutation_input_type_name`, `editable_input_fields`, `_GeneratedInputFieldName`,
`InputFieldSpec`, `guard_dropped_required`, `resolve_effective_fields`,
`FieldError`, `_audit_mutation_input_surface`, `_pascalize_token`,
`build_payload_type`, `relation_input_annotation` across package + tests.

Compared `DjangoMutation.input_type_name` to `mutation_input_shape(...).type_name`
and to the bind path in `_materialize_input_for` / `_materialize_merged_input`.
Pre-fix seam body re-walked `editable_input_fields` twice and called
`mutation_input_type_name` independently while the docstring already claimed
DRY-1 single-sourcing via `mutation_input_shape`.

Rejected / deferred candidates:

1. **`_GeneratedInputFieldName` → `InputFieldSpec`** — naming record for collision
   walks only (`input_attr` / `graphql_name` / `model_field_name`). Model
   mutations do not produce a form/serializer reverse-map decode ledger; forcing
   `kind` / `target_name` / `related_model` would invent unused axes. Forms DRY
   already kept this split. Reject.
2. **`editable_input_fields` narrowing → `resolve_effective_fields`** — shared
   fields/exclude/unknown spine, but empty-set policy differs: forms/serializers
   reject empty at resolve; mutations allow an empty selected set through to
   `build_mutation_input` so a consumer `overrides` merge can still supply
   fields, and unknown wording is `"non-editable or unknown"`. Merging needs a
   skip-empty mode flag. Reject.
3. **`_audit_mutation_input_surface` ↔ `types/finalizer._audit_field_surface`** —
   both reject GraphQL-name collisions; read-type audit also owns empty surfaces
   and a different name provenance (annotations / selected / consumer fields).
   Mutation audit runs at materialize on the post-merge input surface. Reject.
4. **`build_mutation_input` ↔ form/serializer builders** — already share
   `utils/inputs` mechanics; remaining loops encode model editable columns +
   M2M-always-optional + override skip. Further merge obscures ownership. Reject.
5. **`FieldError` relocation** — intentional freeze site (spec-036 Decision 7);
   package-root + every flavor import it from here. Correct owner. Reject.
6. **Thin `materialize_*` / `clear_*` wrappers + `_pascalize_token` alias** —
   family API / historical import path; no remaining production `_pascalize_token`
   importers (forms/serializer use `pascalize_token`). Alias cleanup is unrelated
   hygiene. Reject.
7. **`_shape_build_cache` → `make_shape_build_cache`** — lives in `sets.py`, not
   this file; forward to the `mutations/` folder / `sets.py` item. Reject here.

## Opportunities

### 1. Model `input_type_name` seam reads `mutation_input_shape(...).type_name` (accepted)

- **Repeated responsibility:** derived GraphQL/class name for a model mutation
  input shape `(model, operation_kind, frozenset(effective field names))`.
- **Sites:** `mutations/inputs.py::mutation_input_shape` (owner; bind +
  `build_mutation_input` already consume it); `mutations/sets.py::DjangoMutation.input_type_name`
  (re-derived via `editable_input_fields` ×2 + `mutation_input_type_name`);
  `mutations/fields.py` (consumer of the seam only).
- **Evidence:** DRY-1 exists specifically so name / cache key / identity cannot
  drift; the seam docstring claimed that single-sourcing but still re-spelled the
  walk. Auth already builds through `mutation_input_shape` when pinning
  `RegisterInput`. Same contract, same change axis (narrowing / naming rule).
- **Owner:** `mutations/inputs.py::mutation_input_shape` (computation);
  `DjangoMutation.input_type_name` (overridable seam returning `.type_name`).
- **Consolidation:** seam body becomes
  `return mutation_input_shape(model, kind, fields=..., exclude=...).type_name`;
  drop the unused `mutation_input_type_name` import from `sets.py`; document the
  seam as a shape consumer on `mutation_input_shape`.
- **Proof:** `tests/mutations/test_sets.py::test_model_flavor_input_seams_produce_today_defaults`
  asserts seam == `mutation_input_shape(...).type_name` for full create and
  narrowed update (and that the narrowed name is not the canonical
  `ItemPartialInput`). Live `/graphql` already covers wire names; the seam↔shape
  equality is not a live surface.
- **Risks / non-goals:** do not collapse form/serializer name seams onto
  `MutationInputShape` (different bases / descriptors); do not delete
  `mutation_input_type_name` (still the naming primitive shape + unit tests use).

## Judgment

This file is already the thin model-domain wrapper over `utils/inputs` that
sibling flavors mirror. The unfinished DRY-1 consumer was the model name seam:
it advertised shape single-sourcing while re-deriving the name. Routing the seam
through `mutation_input_shape(...).type_name` completes that ownership.
Everything else examined is intentional separation or belongs to `sets.py` /
folder pass. Ready for Worker 2.

## Implementation (Worker 1)

**Owner chosen:** `mutations/inputs.py::mutation_input_shape` for the derived
name; `mutations/sets.py::DjangoMutation.input_type_name` as the seam that reads
it.

**Migrated sites:**

- `mutations/sets.py` — `input_type_name` → `mutation_input_shape(...).type_name`;
  drop unused `mutation_input_type_name` import; `_shape_build_cache` comment
  names the shape descriptor (not the bare naming primitive)
- `mutations/inputs.py` — `mutation_input_shape` docstring lists the seam consumer
- `tests/mutations/test_sets.py` — full + narrowed seam↔shape equality assertions

**Kept separate:** `_GeneratedInputFieldName` vs `InputFieldSpec`; editable-column
narrowing vs `resolve_effective_fields`; materialize surface audit vs read-type
audit; `FieldError` home; form/serializer builder loops; `_shape_build_cache`
plumbing (sets item).

**Validation:** `uv run ruff format .` + `uv run ruff check --fix .` after edits.
No full pytest (per cycle rules). Changelog: not warranted (internal seam
ownership; no public API change).

## Independent verification (Worker 2)

Re-traced the derived model-input name through `mutation_input_shape` (owner),
`build_mutation_input`, `_materialize_input_for` / `_materialize_merged_input`,
`DjangoMutation.input_type_name`, and `fields.py::_synthesized_mutation_signature`
(lazy `data:` consumer). Compared baseline seam body
(`editable_input_fields` ×2 + `mutation_input_type_name`) to the post-fix
`mutation_input_shape(...).type_name` path against the same Meta
`fields` / `exclude` knobs and `NON_DELETE_OPERATION_INPUT_KIND` mapping.

**Shared-contract challenge (accepted):** The seam and
`mutation_input_shape.type_name` encode one rule — GraphQL/class name for
identity `(model, operation_kind, frozenset(effective editable names))` under
Meta narrowing. Pre-fix docstring already claimed DRY-1 via the shape while
the body re-derived; bind + generator already consumed the shape. Auth pins
`RegisterInput` through `mutation_input_shape` + `_replace(type_name=...)`.
Form/serializer name seams stay on different bases — correctly out of scope.

**Migration:** Complete. Seam has no leftover editable-field re-walk;
`mutation_input_type_name` import gone from `sets.py`. Remaining
`editable_input_fields` uses in `sets.py` are Meta validation / relation
override walks, not name re-derivation. Docstring + `_shape_build_cache`
comment name the shape descriptor.

**Rejected candidates (disposed):**
1. `_GeneratedInputFieldName` vs `InputFieldSpec` — collision naming only; no
   reverse-map decode ledger on model mutations. Keep.
2. `editable_input_fields` vs `resolve_effective_fields` — empty-set policy
   differs (mutations allow empty through for override merge; shared helper
   raises) and unknown wording differs. Keep.
3. `_audit_mutation_input_surface` vs `_audit_field_surface` — different
   phases / empty-surface ownership. Keep.
4. Builder loop merge with form/serializer — already share `utils/inputs`;
   remaining loops are model-domain. Keep.
5. `FieldError` home — intentional freeze site. Keep.
6. Thin wrappers / `_pascalize_token` alias — family API; unrelated hygiene.
   Keep.
7. `_shape_build_cache` → `make_shape_build_cache` — lives in `sets.py`;
   correctly deferred. Keep.

**Tests:** `tests/mutations/test_sets.py::test_model_flavor_input_seams_produce_today_defaults`
passed (focused run; coverage gate failed as expected for a single test).
Asserts full `ItemInput`, narrowed ≠ `ItemPartialInput`, and seam ==
`mutation_input_shape(...).type_name` for create + fields-narrowed update;
finalize pins materialized `ItemInput`. Seam↔shape equality is by-construction
after the fix (proves coupling); behavior anchors are the canonical / narrowed
name asserts + materialize check.

**Missed opportunities:** None material. Exclude-narrowed equality is the same
`mutation_input_shape(..., exclude=)` path already covered by fields-narrowing.
No production edits by Worker 2.
