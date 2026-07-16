# DRY review: `django_strawberry_framework/rest_framework/inputs.py`

Status: verified

## System trace

`rest_framework/inputs.py` owns DRF-serializer-derived `@strawberry.input`
generation (spec-039 Slice 1): schema-time field discovery (loud `.fields`
materialization), writable drop + `Meta.fields` / `Meta.exclude` narrowing,
descriptor-keyed create/partial shapes (annotations / descriptions /
requiredness / nested reverse maps), opt-in nested recursion
(`NestedSerializerConfig`), determinism fingerprinting for the schema hook,
create-required + collision aggregation, materialize/clear of the
serializer-only lazy namespace, and the writable/runtime field helpers the bind
and resolver reuse for source / star / injected agreement.

Public / bind-facing surface:

- namespace lifecycle — `SERIALIZER_INPUTS_MODULE_PATH`,
  `materialize_serializer_input_class`, `clear_serializer_input_namespace`
  (via `make_input_namespace` + shape debug registry); registered
  `rest_framework.input_namespace` / `rest_framework.shape_cache` pre-bind clears
- discovery + narrowing — `get_serializer_for_schema`,
  `writable_serializer_fields`, `resolve_effective_serializer_fields`,
  `resolve_optional_fields`, `resolve_injected_field_specs`
- fingerprint / identity — `serializer_schema_fingerprint`,
  `SerializerInputShape`, `serializer_input_type_name`,
  `describe_serializer_input`
- nested — `NestedSerializerConfig`, recursive `build_serializer_input_class`
- builders / guards — `build_serializer_input_class`, `build_serializer_inputs`,
  `guard_create_required_serializer_fields`
- runtime field helpers (consumed by sets/resolvers) —
  `runtime_validated_data_fields`, `writable_source_collisions`,
  `writable_star_sources`

Connected behavior examined:

- `utils/inputs.py` — already-shared spine (`InputFieldSpec`,
  `resolve_effective_fields`, `guard_dropped_required`,
  `iter_input_field_collisions` incl. `source_of`, `optional_input_field`,
  `make_input_namespace`, `make_shape_build_cache`, `generated_input_type_name`,
  `pascalize_token`)
- `forms/inputs.py` — sibling form generator (name-set identity, raise-on-first
  collisions, partial column-less required guard); already on `InputFieldSpec` /
  `guard_dropped_required`
- `mutations/inputs.py` — sibling model-column generator; shares `CREATE` /
  `PARTIAL`; distinct lazy module path so `<X>Input` families never collide
- `serializer_converter.py` — per-field conversion + `InputFieldSpec`
  construction; rejects unopted nested / star / dotted sources before the walk
- `sets.py` — bind cache, fingerprint drift guard, injected specs, runtime
  source/star checks via the helpers owned here
- `resolvers.py` — decode via bind-stashed `InputFieldSpec`; reuses runtime
  source/star helpers
- `hook_context.py` — frozen hook context only (no input-generation overlap;
  evidence that runtime write policy lives elsewhere)
- soft-dep — `rest_framework/__init__.py::require_drf` gates the package; this
  module is never imported on a DRF-absent build
- tests — `tests/rest_framework/test_inputs.py` (generator / fingerprint /
  collisions); live nested / serializer mutations under
  `examples/fakeshop/test_query/` (wire). Internal reverse-map / fingerprint /
  collision aggregation are not live GraphQL surfaces.

ITEM_BASELINE `1eb83b086b258513cecd74f6653994276aa7d999`: target unmodified at
review start; post-implementation item-scoped diff is only this file.

## Verification

Searches: `InputFieldSpec`, `guard_dropped_required`, `writable_serializer_fields`,
`writable_source_collisions`, `source_of`, `iter_input_field_collisions`,
`serializer_schema_fingerprint`, `read_only` / `HiddenField`,
`resolve_effective_fields`, `NestedSerializerConfig`,
`_aggregate_field_problems`, `resolve_optional_fields`,
`FormInputFieldSpec`, `MutationInputShape` across package + tests.

Static audit (`export_dry_review.py audit --target …/inputs.py`) oriented
importers; findings reconciled against behavior.

Focused pytest (15 passed, incl. source-collision, fingerprint, aggregate
schema-time problems, utils `source_of` walker). Coverage gate fails on partial
run as expected — not the final gate.

Rejected / deferred candidates:

1. **Merge flavor builders** (`build_serializer_input_class` ↔
   `build_form_input_class` / `build_mutation_input`) — already share
   `utils/inputs` mechanics; remaining loops encode serializer declared fields +
   descriptor identity + nested opt-in vs form `base_fields` / column-less
   requiredness vs model editable columns. Further merge needs mode flags.
   Reject.
2. **`_model_less_relation_annotation` ↔ `serializer_only_relation_annotation`**
   — forms DRY already rejected; different queryset discovery, naming, primary
   policy. Reject (converter / forms ownership).
3. **Form raise-on-first vs serializer aggregate collisions** — intentional
   reporting contracts (rev6 #5 aggregate vs form first-fail); consumption
   policy stays at call sites of `iter_input_field_collisions`. Reject unifying
   policy.
4. **Promote `_aggregate_field_problems` to `utils/inputs`** — single serializer
   consumer; forms do not want it. Reject.
5. **Descriptor `SerializerInputShape` ↔ name-set `MutationInputShape` /
   form naming** — serializer needs annotations / descriptions / requiredness /
   nested_specs because the schema hook can vary same-named fields; forms /
   model mutations key on name sets. Correct separation. Reject.
6. **Thin `materialize_*` / `clear_*` wrappers + distinct module path** —
   intentional family API / lazy `__dict__` isolation. Reject.
7. **`writable_source_collisions` / `writable_star_sources` /
   `runtime_validated_data_fields` relocate out of this file** — reorganization,
   not duplicated responsibility; sets + resolvers correctly import the
   schema-time field basis owner. Forward to folder pass only if ownership
   clarity becomes an issue. Defer.
8. **Double `resolve_effective_serializer_fields` in `build_serializer_inputs`
   → `build_serializer_input_class`** — redundant work, not cross-owner
   duplication. Out of scope micro-opt. Reject.
9. **`hook_context.py` overlap** — no shared generation responsibility.
   Reject.
10. **Partial column-less required guard for serializers** — forms need it
    because partial reconstructs model columns and cannot reconstruct extras;
    serializer partial is all-optional and DRF validates what is supplied. No
    parallel responsibility. Reject.

## Opportunities

### 1. Schema-time source collisions use `iter_input_field_collisions(..., source_of=…)` (accepted)

- **Repeated responsibility:** detect two writable generated-input fields that
  write the same one-segment model attribute (`source or declared name`).
- **Sites:** `utils/inputs.py::iter_input_field_collisions` (`source_of` arm,
  already tested); `_collect_input_attr_collision_messages` (docstring claimed
  the third arm but still hand-appended messages via
  `writable_source_collisions`); `writable_source_collisions` remains the
  runtime owner for sets/resolvers (star exclusion + non-`InputFieldSpec` maps).
- **Evidence:** docstring already named the `source_of` arm; message wording is
  byte-identical when `subject` is
  `SerializerMutation for {name!r}` and
  `source_of = lambda spec: spec.source or spec.target_name` (same `source or
  name` rule). Star sources never appear in successful schema-time specs
  (converter rejects them). Same contract, same change axis as input-attr /
  GraphQL-name collisions.
- **Owner:** `utils/inputs.py::iter_input_field_collisions` (walk + wording);
  this file collects for aggregation.
- **Consolidation:** pass `source_of`; drop the post-walk
  `writable_source_collisions` append (keep the helper for runtime).
- **Proof:** `tests/rest_framework/test_inputs.py::test_two_writable_fields_sharing_one_source_raise`;
  `tests/utils/test_inputs.py::test_input_collision_walker_reports_shared_write_sources`.
  Not earnable via live `/graphql` (bind-time configuration error).
- **Risks / non-goals:** do not delete `writable_source_collisions` (runtime
  star exclusion + HiddenField / narrowed maps); do not change form raise-first
  policy.

### 2. Fingerprint writable filter reuses `writable_serializer_fields` (accepted)

- **Repeated responsibility:** which schema-time serializer fields can affect
  the generated input / SDL (drop `read_only` + `HiddenField`).
- **Sites:** `writable_serializer_fields` (named owner; used by
  `resolve_effective_serializer_fields` / create-required basis / sets);
  `_fingerprint_field_map` (inlined the same predicate).
- **Evidence:** identical filter; fingerprint docstring already says it scopes
  to the writable set the builder uses. A drifted predicate would let
  fingerprint / build disagree on nested descent.
- **Owner:** `writable_serializer_fields`.
- **Consolidation:** iterate `writable_serializer_fields(field_map).items()`.
- **Proof:** existing fingerprint tests that distinguish writable vs read-only /
  nested opt-in shapes (`tests/rest_framework/test_inputs.py` fingerprint
  cases). Internal determinism contract — not a live GraphQL surface.
- **Risks / non-goals:** do not fold runtime `runtime_validated_data_fields`
  (includes defaulted HiddenField contributors) into this writable basis.

## Judgment

This file is the serializer write-input generator over an already-mature
`utils/inputs` spine (`InputFieldSpec`, effective-fields, dropped-required,
collision walker, namespace / shape-cache factories). The remaining real
duplication was unfinished wiring: schema-time source collisions still
re-spelled a walk the shared `source_of` arm already owns, and the fingerprint
re-inlined the writable predicate. Both now point at their owners. Flavor-level
builders, descriptor identity, nested opt-in, and runtime source/star helpers
stay correctly separate. Ready for Worker 2.

## Implementation (Worker 1)

**Owner chosen:** `utils/inputs.py::iter_input_field_collisions` for schema-time
source collisions; `writable_serializer_fields` for the fingerprint writable
basis.

**Migrated sites:**

- `rest_framework/inputs.py::_collect_input_attr_collision_messages` — pass
  `source_of=lambda spec: spec.source or spec.target_name`; remove post-walk
  `writable_source_collisions` message append
- `rest_framework/inputs.py::_fingerprint_field_map` — iterate
  `writable_serializer_fields(field_map)`

**Kept separate:** `writable_source_collisions` / `writable_star_sources` /
`runtime_validated_data_fields` for sets + resolvers; form raise-first
collision policy; flavor builder loops; descriptor vs name-set identity;
distinct serializer lazy module path.

**Validation:** focused tests above (15 passed); `uv run ruff format .` +
`uv run ruff check --fix .` clean. No full pytest. Changelog: not warranted
(internal wiring onto already-public helpers; no consumer API change).

## Independent verification (Worker 2)

Re-traced `rest_framework/inputs.py` as the serializer write-input generator over
`utils/inputs` (`InputFieldSpec`, effective-fields, collision walker, namespace /
shape-cache). Item-scoped diff vs `ITEM_BASELINE` is only the two claimed
wirings (plus docstring notes). No production edits by Worker 2.

### Challenge: Opportunity 1 (`source_of` on `iter_input_field_collisions`)

**Holds.** Baseline docstring already claimed the three arms lived in
`utils/inputs.py::iter_input_field_collisions`, but `_collect_input_attr_collision_messages`
still omitted `source_of` and re-appended via `writable_source_collisions`. That
was unfinished wiring, not a second owner.

Byte-stable wording for the two-writable-field case was re-derived independently:
`subject=f"SerializerMutation for {name!r}"` + walker template matches the old
hand-built sentence exactly (including `source or target_name` for bare declared
names vs aliases). End-to-end proof:
`tests/rest_framework/test_inputs.py::test_two_writable_fields_sharing_one_source_raise`
(name + `alias`/`source="name"`). Walker arm proof:
`tests/utils/test_inputs.py::test_input_collision_walker_reports_shared_write_sources`.

Disposed edge deltas (not revision-needed):

1. **N>2 owners of one source** — old helper emitted one message naming only
   `owners[0]`/`owners[1]`; the walker yields pairwise as it walks (strictly
   better for rev6 #5 aggregation). Exotic; two-field contract unchanged.
2. **`source="*"` exclusion** — `writable_source_collisions` skips `*`; the
   walker does not. Unreachable at this call site: converter /
   `_resolve_nested_field` reject dotted/star before a spec is appended
   (`_walk_serializer_fields` collects those as field errors and `continue`s).
3. **Interleaved vs appended order** — source messages now arise during the same
   walk as attr/GraphQL arms instead of after. Aggregate tests assert membership /
   counts, not mixed-arm bullet order; forms still leave `source_of=None`.

`writable_source_collisions` correctly remains for sets/resolvers (star exclusion
+ non-`InputFieldSpec` maps). Do not delete it.

### Challenge: Opportunity 2 (fingerprint → `writable_serializer_fields`)

**Holds.** Inlined predicate was identical to
`writable_serializer_fields` (`not read_only and not isinstance(..., HiddenField)`).
Returning a new dict preserves insertion order of survivors, so fingerprint tuple
order is unchanged. Same basis already used by
`resolve_effective_serializer_fields` / create-required / sets — a drifted
predicate would disagree on nested descent. Proof:
`test_fingerprint_skips_read_only_nested_serializer` plus other fingerprint cases
in `tests/rest_framework/test_inputs.py`. Correctly not folded into
`runtime_validated_data_fields` (defaulted HiddenField contributors).

### Rejected candidates (re-challenged)

1–10 in the artifact stand. Flavor builders still encode distinct field bases /
requiredness / nested opt-in; form raise-first vs serializer aggregate is
consumption policy at walker call sites; `_aggregate_field_problems` stays
serializer-local; descriptor vs name-set identity and distinct lazy module paths
remain intentional; double `resolve_effective_serializer_fields` is redundant
work, not cross-owner DRY; `hook_context.py` has no generation overlap; partial
column-less required guard is form-only.

### Missed opportunities

None that clear the consolidate bar. Runtime source/star helpers staying in this
file is reorganization, not duplicated responsibility (folder-pass deferral is
appropriate). No second inlined writable filter left under
`django_strawberry_framework/` besides the body of `writable_serializer_fields`
itself.

### Proof commands (Worker 2)

```shell
uv run pytest tests/rest_framework/test_inputs.py::test_two_writable_fields_sharing_one_source_raise \
  tests/rest_framework/test_inputs.py::test_read_only_field_sharing_source_with_writable_is_accepted \
  tests/rest_framework/test_inputs.py::test_writable_source_collisions_excludes_star_and_flags_duplicates \
  tests/rest_framework/test_inputs.py::test_fingerprint_skips_read_only_nested_serializer \
  tests/rest_framework/test_inputs.py::test_schema_fingerprint_sensitive_to_choices_and_help_text \
  tests/rest_framework/test_inputs.py::test_recursive_fingerprint_sensitive_to_nested_shape_change \
  tests/utils/test_inputs.py::test_input_collision_walker_reports_shared_write_sources \
  -q --no-cov
# 7 passed

uv run pytest tests/rest_framework/test_inputs.py \
  -k 'fingerprint or collision or source or HiddenField or read_only' \
  -q --no-cov
# 20 passed
```

**Disposition:** verified. Plan item checked.
