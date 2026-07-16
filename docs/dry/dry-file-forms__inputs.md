# DRY review: `django_strawberry_framework/forms/inputs.py`

Status: verified

## System trace

`forms/inputs.py` owns form-derived `@strawberry.input` generation (spec-038
Slice 1): discover `base_fields` without instantiation, narrow via
`Meta.fields` / `Meta.exclude`, emit create-shaped and partial inputs, materialize
into a form-only lazy module namespace, and produce the per-field reverse map the
Slice-3 decode stashes on the mutation.

Public / bind-facing surface:

- namespace lifecycle — `INPUTS_MODULE_PATH`, `materialize_form_input_class`,
  `clear_form_input_namespace` (via `make_input_namespace`); registered
  `forms.input_namespace` pre-bind clear
- kind vocabulary — `FORM`, re-exported `CREATE` / `PARTIAL`, `CREATE_SHAPED_KINDS`
- discovery + narrowing — `get_form_fields`, `resolve_effective_form_fields`
- naming — `form_input_type_name`
- builders — `build_form_input_class`, `build_form_inputs`
- guards — `guard_create_required_fields`,
  `guard_partial_required_column_less_fields`

Connected behavior examined:

- `forms/converter.py` — model-less `convert_form_field` + `form_field_required`;
  previously also defined `FormInputFieldSpec` (sole production constructor was
  here)
- `forms/sets.py` — `_cached_build_form_input` / bind stash of `_input_field_specs`
- `forms/resolvers.py` — decode keys reverse map by form field name + kind
- `utils/inputs.py` — materialize/build/optional/collision/guard spine;
  `InputFieldSpec` (already the serializer reverse map)
- `mutations/inputs.py` — sibling model-column generator; shares
  `relation_input_annotation`, `CREATE` / `PARTIAL`, materialize helpers; keeps a
  distinct module path so `<Model>Input` and `<FormClass>Input` never collide
- `rest_framework/inputs.py` + `serializer_converter.py` — sibling serializer
  generator; `serializer_only_relation_annotation` parallels
  `_model_less_relation_annotation` with stricter primary-required policy and
  different naming
- tests — `tests/forms/test_inputs.py` (generator contract); live form mutations
  under `examples/fakeshop/test_query/` exercise wire behavior through bind +
  resolve (internal reverse-map type is not a live surface)

ITEM_BASELINE `84f665a4b13979b9bfa5d83fb7b08040f2748fee`: target was unmodified at
review start; post-implementation item-scoped diffs cover the migration sites
below.

## Verification

Searches: `FormInputFieldSpec`, `InputFieldSpec`, `form_field_name`,
`target_name`, `build_form_input`, `guard_dropped_required`,
`_model_less_relation_annotation`, `serializer_only_relation_annotation`,
`relation_input_annotation`, `make_input_namespace`, `optional_input_field`,
`resolve_effective_fields` across package + tests.

Scratch (`DJANGO_SETTINGS_MODULE=config.settings`, `PYTHONPATH=examples/fakeshop`):

- `build_form_inputs` on a plain `Form` returns `InputFieldSpec` rows with
  `target_name` set and `source` / `nested_specs` left `None`;
  `converter.FormInputFieldSpec` is gone.
- `guard_partial_required_column_less_fields` still fail-louds on a dropped
  required column-less extra (`confirm`) with the pinned wording.

Rejected / deferred candidates:

1. **`_model_less_relation_annotation` ↔ `serializer_only_relation_annotation`** —
   shared Relay-vs-raw-pk id-scalar rule (two lines via `implements_relay_node` +
   `scalar_for_field`), but different queryset discovery, naming
   (`<name>_id` vs serializer graphql-name helper), and primary policy (form
   allows raw-pk fallback; serializer requires a registered primary). Merging
   needs mode flags across intentional contract differences. Reject.
2. **`build_form_input_class` ↔ `build_mutation_input` / serializer builders** —
   already share `utils/inputs` mechanics; remaining loops encode flavor field
   bases (form `base_fields` + column-backed vs column-less routing, model
   editable columns, serializer declared fields). Further merge would obscure
   ownership. Reject.
3. **Thin `materialize_*` / `clear_*` wrappers** — intentional family API over
   `make_input_namespace`; callers + tests address form-named entry points.
   Reject.
4. **Double `resolve_effective_form_fields` inside `build_form_inputs` →
   `build_form_input_class`** — redundant work, not duplicated responsibility
   across owners. Out of scope micro-opt. Reject.
5. **`mutations/inputs.py` namespace sibling** — must stay a distinct module
   `__dict__` (lazy path + name collision). Correct separation. Reject.

## Opportunities

### 1. Form reverse map uses `InputFieldSpec` (accepted)

- **Repeated responsibility:** per-generated-input-field reverse map for write
  decode (`input_attr`, `graphql_name`, decode key, `kind`, `related_model`).
- **Sites:** `forms/converter.py::FormInputFieldSpec` (definition);
  `forms/inputs.py::_field_triple_and_spec` (sole production constructor);
  `forms/resolvers.py::_decode_form_data` (`spec.form_field_name`);
  `utils/inputs.py::InputFieldSpec` (serializer owner, already generalized).
- **Evidence:** `InputFieldSpec` docstring already names itself the `038`
  form record + serializer axes; `form_field_name` ≡ `target_name`; form never
  needs `source` / `nested_specs` (defaults `None`). Spec-039 D1 left the form
  record untouched for blast radius — a pragmatic split, not a distinct
  contract. This file is the true construction owner; destination type already
  lives in `utils/inputs.py`.
- **Owner:** `utils/inputs.py::InputFieldSpec` (type);
  `forms/inputs.py` (form construction).
- **Consolidation:** construct `InputFieldSpec(target_name=form_field_name, …)`;
  delete `FormInputFieldSpec`; resolvers/tests read `.target_name`.
- **Proof:** `tests/forms/test_inputs.py` asserts `isinstance(..., InputFieldSpec)`
  + `target_name` / unused-axis defaults; converter unit test of the deleted
  dataclass removed. Live form mutations unchanged (wire contract identical).
- **Risks / non-goals:** do not invent a form-only alias; do not merge
  model-mutation naming records (`_GeneratedInputFieldName`) into
  `InputFieldSpec`.

### 2. Partial column-less required guard reuses `guard_dropped_required` (accepted)

- **Repeated responsibility:** `required − effective − waived` drop detection.
- **Sites:** `guard_create_required_fields` (already uses
  `guard_dropped_required`); `guard_partial_required_column_less_fields`
  (hand-rolled sorted drop).
- **Evidence:** same arithmetic; only the required-set filter (column-less only)
  and pinned error wording differ.
- **Owner:** `utils/inputs.py::guard_dropped_required`.
- **Consolidation:** filter `_required_form_field_names` to column-less, then
  call `guard_dropped_required` with the existing partial message factory.
- **Proof:** scratch + existing
  `guard_partial_required_column_less_fields` tests (message unchanged).
- **Risks / non-goals:** must not reuse the create required set wholesale (would
  wrongly reject reconstructable model-backed drops on update).

## Judgment

This file is the form write-input generator wrapper over already-shared
`utils/inputs` mechanics. The unfinished form/serializer reverse-map split was
the real duplication: one decode-record responsibility with two dataclasses.
Migrating form construction onto `InputFieldSpec` completes that ownership;
routing the partial guard through `guard_dropped_required` removes a second
copy of the same drop arithmetic. Sibling generators stay separate. Ready for
Worker 2.

## Implementation (Worker 1)

**Owner chosen:** `utils/inputs.py::InputFieldSpec` for the reverse-map type;
`forms/inputs.py` for form construction + partial-guard filter.

**Migrated sites:**

- `forms/inputs.py` — construct `InputFieldSpec(target_name=…)`; collision
  `name_of` → `.target_name`; partial guard → `guard_dropped_required`
- `forms/converter.py` — delete `FormInputFieldSpec`; docstring points at
  `InputFieldSpec`
- `forms/resolvers.py` — decode keys `.target_name`
- `forms/sets.py`, `forms/__init__.py` — comment/docstring ownership updates
- `utils/inputs.py` — `InputFieldSpec` docstring now covers form + serializer
- `tests/forms/test_inputs.py` — `target_name` + `InputFieldSpec` assertions
- `tests/forms/test_converter.py` — remove deleted-dataclass unit test

**Kept separate:** model-less vs serializer-only relation annotation helpers;
form vs model vs serializer builder loops; distinct form input module path.

**Validation:** `uv run ruff format .` + `uv run ruff check --fix .` clean;
scratch import/build + partial-guard checks above. No full pytest (per cycle
rules). Changelog: not warranted without maintainer ask (internal type unify,
no public consumer API change — `FormInputFieldSpec` was never package-root
exported).

## Independent verification (Worker 2)

Re-traced `forms/inputs.py` through converter / sets / resolvers / `utils/inputs`
and the item-scoped baseline diff. Confirmed both accepted consolidations and
disposed the rejected list.

**1. `FormInputFieldSpec` → `InputFieldSpec` — shared contract holds.**

Baseline `FormInputFieldSpec` axes were `input_attr`, `graphql_name`,
`form_field_name`, `kind`, `related_model`. `InputFieldSpec` is the same reverse-
map role with `target_name` as the neutral decode key; form construction sets
`target_name=name` (declared form field name, never the `<name>_id` relation
attr). Serializer-only `source` / `nested_specs` default `None` and are unused
on the form path — no mode flags. Decode in
`forms/resolvers.py::_decode_form_data` keys `provided_data` / `provided_files`
and `form_fields[...]` via `spec.target_name`, matching the old
`form_field_name` semantics. Spec-039 D1's "leave form untouched" was blast-
radius deferral, not a distinct contract; this migration completes that ownership.

**2. Call sites / deletion — complete.**

`FormInputFieldSpec` is gone from `forms/converter.py`. Zero remaining
references under `django_strawberry_framework/` or `examples/`. Migrated:
construction + collision `name_of` in `forms/inputs.py`, decode in
`forms/resolvers.py`, ownership comments in `forms/sets.py` /
`forms/__init__.py` / `utils/inputs.py`, tests in `tests/forms/test_inputs.py`
(`isinstance(..., InputFieldSpec)`, `target_name`, unused-axis defaults).
Deleted-dataclass unit test removed from `tests/forms/test_converter.py`. Never
package-root exported.

**3. `guard_partial_required_column_less_fields` → `guard_dropped_required` —
equivalent.**

Old: `sorted(name for name in required if name not in effective and
column_less)`. New: filter required to column-less, then
`guard_dropped_required` → `sorted(column_less_required - effective - ())`.
Same set arithmetic; pinned partial message factory preserved. Column-less
filter remains load-bearing (must not reuse the create required set wholesale).
`tests/forms/test_inputs.py::test_partial_guard_rejects_dropping_required_column_less_field`
and `::test_partial_guard_allows_dropping_model_backed_required_field` cover both
arms.

**4. Rejected candidates — independently affirmed.**

- `_model_less_relation_annotation` ↔ `serializer_only_relation_annotation`:
  shared Relay-vs-raw-pk id-scalar rule only; queryset discovery, naming
  (`<name>_id` vs serializer graphql-name helper), and primary policy
  (`registry.get` + raw-pk fallback vs `_require_relation_primary`) differ.
  Merge would need mode flags. Reject stands.
- Flavor builder loops / thin `materialize_*` wrappers / distinct
  `mutations.inputs` module path: intentional ownership boundaries. Reject
  stands.
- Double `resolve_effective_form_fields` in `build_form_inputs` →
  `build_form_input_class`: redundant work, not duplicated responsibility.
  Out of scope. Reject stands.

**5. Missed opportunities / blockers.**

None material. One cosmetic issue found and fixed in this commit:
`utils/inputs.py::iter_input_field_collisions` docstring had extra whitespace
before ``name_of`` from the edit; collapsed to a single space (not a
consolidation defect). No commit by Worker 2.

**Verdict:** Status → `verified`; plan item checked.
