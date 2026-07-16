# DRY review: `django_strawberry_framework/rest_framework/sets.py`

Status: verified

## System trace

`rest_framework/sets.py` owns the DRF-serializer write **declaration** surface
(spec-039 Slice 2 + Slice 3 seams):

- **`SerializerMutation(DjangoMutation)`** — rides the model metaclass,
  `_mutation_registry`, and `bind_mutations()` unchanged (Decision 6). Overrides
  `_resolve_model` (`Meta.serializer_class.Meta.model`), `_validate_meta`
  (serializer Meta matrix), `build_input` / `input_type_name` /
  `input_module_path` (serializer-input namespace), and `resolve_*` (serializer
  pipeline via `resolver_seams`).
- **Module-local helpers** — `_checked_schema_field_map` (schema-hook
  determinism fingerprint), `_serializer_input_shape_for` (descriptor-keyed
  shape cache), `_validate_serializer_nested_fields` (nested opt-in + write-method
  override gate), `_assert_schema_source_ownership` (root + nested schema-time
  writable-source ownership).
- **Consumer hooks** — `get_serializer_for_schema`, `get_serializer_kwargs`
  (constructor-only), `get_serializer_injected_data`, `get_serializer_save_kwargs`.
  Deliberately **no** coarse `get_serializer` constructor (H3 /
  Medium-7): `partial` / `context["request"]` stay framework-owned.

Already-promoted owners (not re-owned here): `mutations/sets.py`
(`reject_unknown_meta_keys`, `require_backing_class`,
`resolve_meta_model` / `resolve_backed_model_or_raise`, `NON_DELETE_*`,
`non_delete_operation_error`, `build_and_stash_input`, `construction_kwargs`,
`resolver_seams`, `_validate_permission_classes`, `validate_select_for_update`,
`_ValidatedMutationMeta`); `rest_framework/inputs.py` (generator, narrowing,
fingerprint, `runtime_validated_data_fields`, star/collision detection + raise);
`utils/inputs.py::normalize_field_name_sequence`.

Connected behavior examined:

- `forms/sets.py` — ModelForm sibling (same `DjangoMutation` ride; construction
  waiver via `get_form_kwargs` / `get_form`; pre-build `cached_build_input` key)
- `mutations/sets.py` — shared Meta / build / metaclass primitives
- `rest_framework/resolvers.py` — runtime ownership / agreement / write pipeline
- `rest_framework/inputs.py` / `serializer_converter.py` — Slice-1 generator +
  nested field helpers
- `filters/sets.py` / `orders/sets.py` / `sets_mixins.py` — FilterSet / OrderSet
  families; declaration lifecycle only (no write-Meta overlap)
- Tests — `tests/rest_framework/test_sets.py` (Meta / nested / ownership);
  live products / library serializer mutations under
  `examples/fakeshop/test_query/`

ITEM_BASELINE `80a98a6113bf330e7790ca5d45c78d7cbd712bfa`: target matched baseline
at review start. Concurrent dirty on `inputs.py` / `resolvers.py` /
`test_inputs.py` from prior verified DRY items left intact; this pass only
appends the ownership-raise helper and migrates call sites.

## Verification

Searches: every definition in the target; sibling form / model Meta +
`build_input` / construction hooks; `writable_star_sources` /
`writable_source_collisions` / `raise_writable_source_ownership_errors` /
`construction_kwargs` / `resolver_seams` / `_assert_runtime_write_source_ownership`
package-wide; FilterSet / OrderSet / `sets_mixins` for false lookalikes.

Compared contracts:

- **Form vs serializer `build_input` / cache** — form keys shape pre-build and
  uses `cached_build_input`; serializer keys post-build `SerializerInputShape`
  (P1.7 partial reuse, documented). Same change axis would force a double build.
- **Form vs serializer construction waiver** — form waives create-required via
  hook override; serializer never does (`injected_fields` only). Distinct
  Decision-7 contracts.
- **Schema-time vs runtime source ownership** — same detection rule (star +
  collision), different timing (class creation vs pre-`is_valid` for
  context-dependent `get_fields()`). Raise wording shares one owner; walkers
  stay phase-local.
- **Root vs nested schema ownership** — same rule, previously two raise copies
  that had already drifted in explanatory text. Confirmed consolidation.
- **`get_serializer_kwargs` default vs `construction_kwargs`** — Md7 docstring
  already named the serializer default as a consumer; body still inlined
  `{"data": data}`. Confirmed unfinished wiring.
- **FilterSet / OrderSet / `sets_mixins`** — related-declaration collect / naming
  / lazy target; not Meta-validate-and-register write flavors. Reject fold.
- **`_SERIALIZER_OPERATION_NESTED_WRITE_METHOD`** — create/update -> method name
  identity map local to nested write-method gate; not the
  `NON_DELETE_OPERATION_INPUT_KIND` generator map. Reject merge.

Optional audit (`export_dry_review.py audit --target …/sets.py --stdout`) used
for orientation only. No scratch under `docs/dry/temp-tests/`.

Focused proof (`--no-cov`, 7 passed):

- `tests/rest_framework/test_inputs.py::test_raise_writable_source_ownership_errors_star_and_collision`
- `tests/rest_framework/test_sets.py` star / duplicate / nested ownership cases
- `tests/rest_framework/test_resolvers.py::test_runtime_context_field_source_collision_fails_before_validation`

Class-creation / helper ownership is not earnable via live `/graphql`
(configuration errors before schema wire). Live serializer mutations remain the
runtime surface for resolvers.

Rejected / deferred candidates:

1. **Force serializer through `cached_build_input`** — wrong key timing (P1.7).
   Reject.
2. **Unify form / serializer Meta matrices** — would need mode flags for
   backing key, operation rules, injected/optional/nested keys, permission
   defaults. Reject.
3. **Promote `_checked_schema_field_map` / fingerprint guard** — serializer-only
   schema-hook determinism; no second consumer. Keep local. Reject.
4. **Share nested-fields validator with form nested** — forms have no
   `Meta.nested_fields` / DRF write-method override gate. Reject.
5. **Absorb FilterSet / OrderSet metaclasses** — related-declaration collection,
   not write Meta. Reject (already proved on mutations / sets_mixins items).
6. **Fold runtime ownership walker into schema walker** — runtime needs live
   serializer instance + nested specs from bind; schema needs NestedSerializerConfig
   tree + field_map. Shared raise is enough; walker merge would need mode flags.
   Reject.
7. **Derive `_ALLOWED_SERIALIZER_META_KEYS` from model / form sets** — keys must
   change independently (Decision 6 add/drop). Reject.

## Opportunities

### O1 — One raise path for writable-source ownership (accepted)

- **Repeated responsibility:** reject writable `source='*'` and multi-field
  single-source ownership with one `ConfigurationError` contract.
- **Sites:** `sets.py` root `_validate_meta` inline raise; former
  `_assert_nested_schema_source_ownership` raise copy;
  `resolvers.py::_assert_runtime_write_source_ownership` raise copy;
  detection already in `inputs.py::writable_star_sources` /
  `writable_source_collisions`.
- **Evidence:** three raise bodies with drifted explanations for the same DRF
  last-write-wins / whole-object merge hazard; tests pin substrings
  (`source='*'`, `bind one serializer source`, `nested serializer path`,
  `runtime serializer path '<root>'`).
- **Owner:** `rest_framework/inputs.py::raise_writable_source_ownership_errors`
  beside the detection helpers.
- **Consolidation:** add the raise helper; replace root + nested schema raises
  with one recursive `_assert_schema_source_ownership`; migrate the runtime
  raise site.
- **Proof:** focused tests listed above (package-internal; class-creation /
  helper path not live GraphQL).
- **Risks / non-goals:** do not merge schema vs runtime *walkers*; do not change
  the injected/effective supplied-field sets each phase computes.

### O2 — Wire `get_serializer_kwargs` through `construction_kwargs` (accepted)

- **Repeated responsibility:** default construction-hook kwargs shape
  (`{...base}` + optional `instance` only when non-`None`).
- **Sites:** `mutations/sets.py::construction_kwargs` (owner; form default
  already uses it; docstring already names serializer); serializer
  `get_serializer_kwargs` returned `{"data": data}` inline.
- **Evidence:** Md7 unfinished wiring — documented consumer missing the call.
- **Owner:** `construction_kwargs`.
- **Consolidation:** `return construction_kwargs(data=data)`.
- **Proof:** existing resolver hook tests that call
  `super().get_serializer_kwargs(...)` and assert framework-owned `data`
  identity; behavior unchanged for create (no `instance` key).
- **Risks / non-goals:** do not move framework merge / `partial` /
  `context["request"]` into the consumer hook.

## Judgment

`SerializerMutation` already rides the promoted mutation seams correctly.
Remaining duplication was unfinished ownership of the writable-source *raise*
(detection lived in inputs; three callers re-spelled the error) and the Md7
`construction_kwargs` default. Both now point at their owners. Form/model cache
timing, construction waiver, nested write-method gate, and FilterSet/OrderSet
families stay correctly separate. Ready for Worker 2.

## Implementation (Worker 1)

**Owner chosen:**

- `rest_framework/inputs.py::raise_writable_source_ownership_errors` for the
  ownership raise
- `sets.py::_assert_schema_source_ownership` for the schema-time recursive walk
- `mutations/sets.py::construction_kwargs` for the default construction kwargs

**Migrated sites:**

- `rest_framework/sets.py` — unified schema ownership walker; deleted nested-only
  raise twin; `get_serializer_kwargs` -> `construction_kwargs(data=data)`
- `rest_framework/resolvers.py::_assert_runtime_write_source_ownership` — raise
  via the inputs helper
- `rest_framework/inputs.py` — new raise helper
- `tests/rest_framework/test_inputs.py` — permanent helper coverage

**Kept separate:** schema vs runtime walkers; form construction waiver;
`cached_build_input` vs post-build descriptor cache; nested write-method map;
FilterSet / OrderSet / `sets_mixins`.

**Validation:** 7 focused tests passed; `uv run ruff format` +
`uv run ruff check --fix` + trailing-comma ASCII check clean on edited paths.
No full pytest. Changelog: not warranted (internal wiring onto already-public /
documented helpers; no consumer API change).

**Concurrent work preserved:** prior WIP on `inputs.py` / `resolvers.py` /
`test_inputs.py` from verified inputs/resolvers DRY items untouched except the
ownership-raise migration above. Plan checkbox left unchecked.

## Independent verification (Worker 2)

Re-traced `SerializerMutation` declaration ownership (Meta matrix → schema
ownership → `build_input` / hooks → resolver pipeline) against forms sibling,
`mutations/sets.py` seams, and `inputs` / `resolvers` detection+raise sites.
Did not rely on W1 private notes beyond this artifact + item-scoped diff.

**O1 — accepted.** Package-wide search shows no remaining inline star/collision
raise copies in `sets.py` / `resolvers.py`; both call
`raise_writable_source_ownership_errors`. Schema walker
`_assert_schema_source_ownership` correctly covers root (`location=None`) then
opted-in nested paths; runtime walker stays separate (live serializer +
request `data` + bind `specs`) and only shares the raise. Converter
`source='*'` / dotted-source rejections remain a different contract (input
generation), correctly not folded. Substring pins in
`test_sets` / `test_resolvers` / new helper test still match the unified
wording (`source='*'`, `bind one serializer source`, `nested serializer path`,
`runtime serializer path '<root>'`).

**O2 — accepted.** `get_serializer_kwargs` → `construction_kwargs(data=data)`
matches the Md7 owner already used by form `_default_get_form_kwargs`; with
default `instance=None` the return is still exactly `{"data": data}` (update
`instance` remains framework-merge-owned).

**Rejected candidates (re-challenged):** form/serializer cache timing and
construction waiver; FilterSet/OrderSet/sets_mixins; nesting write-method map
vs `NON_DELETE_OPERATION_INPUT_KIND`; merging schema+runtime walkers — still
distinct contracts / would need mode flags. No missed same-responsibility
duplicate found.

**Proof re-run (`--no-cov`, 9 passed):** helper star/collision/location test;
six `test_sets` class-creation star/collision/nested cases; runtime collision
before validation.

**Concurrent WIP:** left untouched — prior dirty on `inputs.py` /
`resolvers.py` / `test_inputs.py` / `test_resolvers.py` (resolvers-item
agreement helpers) outside this item's exclusive sets migration. No commit.
No full pytest.
